#version 330 compatibility

/*
 * Luminary Shaders - deferred.fsh
 * Passaggio Deferred:
 * 1. Scattering Atmosferico Fisico Rayleigh + Mie per il cielo (depthtex0 == 1.0)
 * 2. Screen-Space Ambient Occlusion (SSAO) + Material AO per la geometria solida
 * 3. Foschia atmosferica (Aerial Perspective) sulla distanza
 */

#include "/lib/settings.glsl"

uniform sampler2D colortex0; // Linear HDR Scene Color
uniform sampler2D colortex1; // View-Space Normal (RGB) + Material AO (A)
uniform sampler2D colortex2; // LabPBR Data (R=Smoothness, G=Metal, B=Porosity/SSS, A=Emissive)
uniform sampler2D depthtex0;

uniform mat4 gbufferProjectionInverse;
uniform mat4 gbufferModelViewInverse;
uniform vec3 sunPosition;
uniform vec3 upPosition;
uniform float viewWidth;
uniform float viewHeight;
uniform float near;
uniform float far;
uniform float wetness;
uniform float rainStrength;
uniform int moonPhase;
uniform int worldTime;
uniform int isEyeInWater;
uniform vec3 cameraPosition;

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outColor;

float linearizeDepth(float d) {
    float z_n = 2.0 * d - 1.0;
    return (2.0 * near * far) / max(far + near - z_n * (far - near), 0.0001);
}

float cloudHash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float cloudNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(cloudHash(i + vec2(0.0, 0.0)), cloudHash(i + vec2(1.0, 0.0)), u.x),
        mix(cloudHash(i + vec2(0.0, 1.0)), cloudHash(i + vec2(1.0, 1.0)), u.x),
        u.y
    );
}

float cloudFBM(vec2 p) {
    float v = 0.0;
    v += 0.550 * cloudNoise(p); p *= 2.03;
    v += 0.285 * cloudNoise(p); p *= 2.07;
    v += 0.165 * cloudNoise(p);
    return v;
}

vec3 computeAtmosphericSky(vec3 viewDir, vec3 worldDir, vec3 upDir, vec3 sunDir, float rain) {
    float vDotUp = dot(viewDir, upDir);
    float vDotSun = clamp(dot(viewDir, sunDir), 0.0, 1.0);
    float sunElevation = clamp(dot(sunDir, upDir) * 0.5 + 0.5, 0.0, 1.0);

    // Modulazione fase lunare (0 = luna piena, 4 = luna nuova)
    float moonPhaseFactor = 0.5 + 0.5 * cos(float(moonPhase) * 0.78539816);
    float moonBoost = mix(0.65, 1.35, moonPhaseFactor);

    // Scattering di Rayleigh (zenith blu profondo -> orizzonte azzurro latteo)
    vec3 zenithDay  = vec3(0.11, 0.30, 0.78);
    vec3 horizonDay = vec3(0.46, 0.70, 0.98);
    vec3 zenithNight  = vec3(0.01, 0.02, 0.06) * moonBoost;
    vec3 horizonNight = vec3(0.04, 0.07, 0.14) * moonBoost;

    vec3 zenith  = mix(zenithNight, zenithDay, sunElevation);
    vec3 horizon = mix(horizonNight, horizonDay, sunElevation);

    float horizonFactor = pow(1.0 - clamp(vDotUp, 0.0, 1.0), 2.4);
    vec3 sky = mix(zenith, horizon, horizonFactor);

    // Scattering di Mie (alone solare anisotropo):
    float mieGlow = pow(vDotSun, 32.0) * 0.18 + pow(vDotSun, 256.0) * 0.65;
    vec3 sunTint = mix(vec3(1.2, 0.45, 0.15), vec3(1.3, 1.25, 1.10), sunElevation);
    float sunVisibility = mix(1.0, 0.15, rain);
    sky += sunTint * (mieGlow * sunElevation * sunVisibility);

    // Volta stellata procedurale ancorata a worldDir (visibile di notte con cielo sereno)
    if (sunElevation < 0.35 && rain < 0.8 && vDotUp > 0.02) {
        float nightVis = smoothstep(0.35, 0.12, sunElevation) * (1.0 - smoothstep(0.35, 0.8, rain)) * smoothstep(0.02, 0.25, vDotUp);
        vec3 starGrid = floor(worldDir * 240.0);
        float starHash = fract(sin(dot(starGrid, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
        if (starHash > 0.9965) {
            vec3 starCellCenter = normalize(starGrid + 0.5);
            float distToStar = length(worldDir - starCellCenter) * 240.0;
            float starCore = smoothstep(0.45, 0.05, distToStar);
            float twinkle = 0.75 + 0.25 * sin(float(worldTime) * 0.06 + starHash * 62.83);
            vec3 starColor = mix(vec3(0.75, 0.85, 1.0), vec3(1.0, 0.92, 0.78), fract(starHash * 31.7));
            sky += starColor * (starCore * twinkle * nightVis * 1.4);
        }
    }

    // Cielo plumbeo/grigio desaturato durante la pioggia + bagliore freddo da temporale
    vec3 rainSky = mix(vec3(0.12, 0.14, 0.18), vec3(0.38, 0.42, 0.48), sunElevation);
    if (rainStrength > 0.85) {
        float stormFlash = pow(max(sin(float(worldTime) * 0.37) * cos(float(worldTime) * 0.19), 0.0), 18.0);
        rainSky += vec3(0.45, 0.58, 0.82) * stormFlash * 0.85;
    }
    sky = mix(sky, rainSky, rain * 0.85);

#ifdef VOLUMETRIC_CLOUDS
    if (vDotUp > 0.03) {
        float cloudPlaneDist = 1.0 / max(vDotUp + 0.12, 0.12);
        vec2 windOffset = vec2(float(worldTime) * 0.0018, float(worldTime) * 0.0007);
        vec2 cloudUV = worldDir.xz * cloudPlaneDist * 1.45 + cameraPosition.xz * 0.0015 + windOffset;
        float n = cloudFBM(cloudUV);
        float coverage = mix(0.46, 0.24, rain);
        float density = smoothstep(coverage, coverage + 0.32, n);
        float horizonFade = smoothstep(0.03, 0.22, vDotUp);
        float cloudAlpha = density * horizonFade * 0.88;

        if (cloudAlpha > 0.005) {
            float silverLining = pow(vDotSun, 12.0) * (1.0 - density * 0.65) * 0.85;
            vec3 cloudLit = mix(vec3(0.08, 0.11, 0.18) * moonBoost, vec3(0.96, 0.95, 0.92), sunElevation);
            vec3 cloudShadow = mix(vec3(0.03, 0.05, 0.09) * moonBoost, vec3(0.54, 0.60, 0.70), sunElevation);
            vec3 cloudColor = mix(cloudLit, cloudShadow, density * 0.65);
            cloudColor += sunTint * (silverLining * sunElevation * (1.0 - rain * 0.75));
            cloudColor = mix(cloudColor, rainSky * 0.90, rain * 0.80);
            sky = mix(sky, cloudColor, cloudAlpha);
        }
    }
#endif

    return sky;
}

void main() {
    vec4 baseColor = texture(colortex0, vTexCoord);
    vec4 normalData = texture(colortex1, vTexCoord);
    vec4 pbrData = texture(colortex2, vTexCoord);
    float emissive = pbrData.a;
    float depth = texture(depthtex0, vTexCoord).r;
    float effectiveRain = max(wetness, rainStrength);

    // Ricostruzione direzione del raggio in View-Space
    vec4 clipPos = vec4(vTexCoord * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 viewPosH = gbufferProjectionInverse * clipPos;
    vec3 viewPos = viewPosH.xyz / max(viewPosH.w, 0.00001);
    vec3 viewDir = normalize(viewPos);

    vec3 upDir = normalize(upPosition);
    vec3 sunDir = normalize(sunPosition);
    vec3 worldDir = normalize((gbufferModelViewInverse * vec4(viewDir, 0.0)).xyz);

    // Se è cielo (depth >= 0.9999), applica scattering Rayleigh + Mie preservando sole/stelle
    if (depth >= 0.9999) {
        vec3 atmoSky = computeAtmosphericSky(viewDir, worldDir, upDir, sunDir, effectiveRain);
        // Preserva eventuale disco solare / stelle già disegnati in baseColor
        float baseLuma = dot(baseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
        vec3 finalSky = mix(atmoSky, max(baseColor.rgb, atmoSky), clamp((baseLuma - 0.35) * 2.0, 0.0, 1.0) * (1.0 - effectiveRain * 0.75));
        outColor = vec4(finalSky, 1.0);
        return;
    }

    float matAO = clamp(normalData.a, 0.25, 1.0);
    float ssao = 1.0;

#if AO_QUALITY >= 1
    vec2 px = vec2(1.0 / max(viewWidth, 1280.0), 1.0 / max(viewHeight, 720.0)) * 2.5;
    float centerLin = linearizeDepth(depth);
    float d1 = linearizeDepth(texture(depthtex0, vTexCoord + vec2( px.x,  0.0)).r);
    float d2 = linearizeDepth(texture(depthtex0, vTexCoord + vec2(-px.x,  0.0)).r);
    float d3 = linearizeDepth(texture(depthtex0, vTexCoord + vec2( 0.0,  px.y)).r);
    float d4 = linearizeDepth(texture(depthtex0, vTexCoord + vec2( 0.0, -px.y)).r);

    float occ = 0.0;
    occ += clamp((centerLin - d1) * 1.5, 0.0, 1.0) * step(abs(centerLin - d1), 1.2);
    occ += clamp((centerLin - d2) * 1.5, 0.0, 1.0) * step(abs(centerLin - d2), 1.2);
    occ += clamp((centerLin - d3) * 1.5, 0.0, 1.0) * step(abs(centerLin - d3), 1.2);
    occ += clamp((centerLin - d4) * 1.5, 0.0, 1.0) * step(abs(centerLin - d4), 1.2);
#if AO_QUALITY >= 2
    vec2 pxDiag = px * 0.7071;
    float d5 = linearizeDepth(texture(depthtex0, vTexCoord + vec2( pxDiag.x,  pxDiag.y)).r);
    float d6 = linearizeDepth(texture(depthtex0, vTexCoord + vec2(-pxDiag.x,  pxDiag.y)).r);
    float d7 = linearizeDepth(texture(depthtex0, vTexCoord + vec2( pxDiag.x, -pxDiag.y)).r);
    float d8 = linearizeDepth(texture(depthtex0, vTexCoord + vec2(-pxDiag.x, -pxDiag.y)).r);
    occ += clamp((centerLin - d5) * 1.5, 0.0, 1.0) * step(abs(centerLin - d5), 1.2);
    occ += clamp((centerLin - d6) * 1.5, 0.0, 1.0) * step(abs(centerLin - d6), 1.2);
    occ += clamp((centerLin - d7) * 1.5, 0.0, 1.0) * step(abs(centerLin - d7), 1.2);
    occ += clamp((centerLin - d8) * 1.5, 0.0, 1.0) * step(abs(centerLin - d8), 1.2);
    ssao = 1.0 - (occ * 0.045);
#else
    ssao = 1.0 - (occ * 0.08);
#endif
#endif

    vec3 sceneColor = baseColor.rgb * mix(0.88, 1.0, matAO) * ssao;

    // Aerial Perspective & Stratified Height Fog
    // Disattivata completamente se il giocatore è sott'acqua (isEyeInWater > 0)
    if (isEyeInWater == 0) {
        float dist = length(viewPos);
        vec3 worldPos = (gbufferModelViewInverse * vec4(viewPos, 1.0)).xyz;
        float absoluteWorldY = cameraPosition.y + worldPos.y;

        // Ground mist stratificata nelle vallate (y < 85), più densa durante la pioggia o le prime ore del mattino
        float heightFactor = clamp((85.0 - absoluteWorldY) / 35.0, 0.0, 1.0);
        float baseFogDensity = mix(0.0035, 0.011, effectiveRain);
        float mistBoost = heightFactor * mix(0.005, 0.015, effectiveRain);
        float effectiveDensity = baseFogDensity + mistBoost;

        float fogStart = mix(32.0, 16.0, effectiveRain);
        float fogFactor = clamp(1.0 - exp(-max(dist - fogStart, 0.0) * effectiveDensity), 0.0, mix(0.72, 0.92, effectiveRain));

        // Nelle profondità sotterranee / dimensioni chiuse (y < 32) foschia calda/ambrata
        float deepRealmFactor = clamp((32.0 - absoluteWorldY) / 48.0, 0.0, 1.0);
        vec3 deepWarmTint = vec3(0.28, 0.12, 0.06);

        // Le superfici emissive (lava, lanterne, bulbi) perforano la foschia lontana
        fogFactor *= (1.0 - emissive * 0.75);

        if (fogFactor > 0.001) {
            vec3 horizonFogDir = normalize(vec3(viewDir.x, max(viewDir.y * 0.25, 0.02), viewDir.z));
            vec3 horizonWorldDir = normalize((gbufferModelViewInverse * vec4(horizonFogDir, 0.0)).xyz);
            vec3 horizonFog = computeAtmosphericSky(horizonFogDir, horizonWorldDir, upDir, sunDir, effectiveRain);
            horizonFog = mix(horizonFog, max(horizonFog, deepWarmTint), deepRealmFactor * 0.45);
            sceneColor = mix(sceneColor, horizonFog, fogFactor);
        }
    } else if (isEyeInWater == 1) {
        float dist = length(viewPos);
        float waterFogFactor = clamp(1.0 - exp(-dist * 0.065), 0.0, 0.94);
        float sunElev = clamp(dot(sunDir, upDir) * 0.5 + 0.5, 0.0, 1.0);
        vec3 underwaterFog = mix(vec3(0.008, 0.045, 0.095), vec3(0.025, 0.22, 0.34), sunElev);
        waterFogFactor *= (1.0 - emissive * 0.60);
        sceneColor = mix(sceneColor, underwaterFog, waterFogFactor);
    } else if (isEyeInWater == 2) {
        float dist = length(viewPos);
        float lavaFogFactor = clamp(1.0 - exp(-dist * 0.45), 0.0, 0.98);
        sceneColor = mix(sceneColor, vec3(0.85, 0.22, 0.03), lavaFogFactor);
    }

    outColor = vec4(sceneColor, baseColor.a);
}
