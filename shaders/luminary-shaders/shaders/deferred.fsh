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

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outColor;

float linearizeDepth(float d) {
    float z_n = 2.0 * d - 1.0;
    return (2.0 * near * far) / max(far + near - z_n * (far - near), 0.0001);
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

    return sky;
}

void main() {
    vec4 baseColor = texture(colortex0, vTexCoord);
    vec4 normalData = texture(colortex1, vTexCoord);
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
    ssao = 1.0 - (occ * 0.08);
#endif

    vec3 sceneColor = baseColor.rgb * mix(0.88, 1.0, matAO) * ssao;

    // Foschia atmosferica morbida (Aerial Perspective) oltre i 90 blocchi (più densa durante pioggia)
    float dist = length(viewPos);
    float fogDensity = mix(0.0045, 0.012, effectiveRain);
    float fogStart = mix(48.0, 24.0, effectiveRain);
    float fogFactor = clamp(1.0 - exp(-max(dist - fogStart, 0.0) * fogDensity), 0.0, mix(0.65, 0.85, effectiveRain));
    if (fogFactor > 0.001) {
        vec3 horizonFogDir = normalize(vec3(viewDir.x, 0.05, viewDir.z));
        vec3 horizonWorldDir = normalize((gbufferModelViewInverse * vec4(horizonFogDir, 0.0)).xyz);
        vec3 horizonFog = computeAtmosphericSky(horizonFogDir, horizonWorldDir, upDir, sunDir, effectiveRain);
        sceneColor = mix(sceneColor, horizonFog, fogFactor);
    }

    outColor = vec4(sceneColor, baseColor.a);
}
