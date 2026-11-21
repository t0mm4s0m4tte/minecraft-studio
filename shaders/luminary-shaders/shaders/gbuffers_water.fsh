#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_water.fsh
 * Acqua in World-Space a 3 ottave Gerstner/FBM, ricostruzione normale nel piano XZ del mondo,
 * lettura profondità fondale (depthtex1) per vera attenuazione esponenziale di Beer-Lambert,
 * caustiche solari subacquee animate in world-space,
 * Fresnel fisico di Schlick (F0 = 0.02) e riflesso speculare GGX del disco solare.
 */

#include "/lib/settings.glsl"

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform sampler2D depthtex0;
uniform sampler2D depthtex1;

uniform float frameTimeCounter;
uniform float viewWidth;
uniform float viewHeight;
uniform float near;
uniform float far;
uniform vec3 cameraPosition;
uniform vec3 upPosition;
uniform vec3 sunPosition;
uniform vec3 shadowLightPosition;
uniform mat4 gbufferModelViewInverse;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;
in vec3 vViewPos;
in vec3 vWorldPos;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outData;

vec3 srgbToLinear(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

float linearizeDepth(float d) {
    float z_n = 2.0 * d - 1.0;
    return (2.0 * near * far) / max(far + near - z_n * (far - near), 0.0001);
}

// Funzione d'onda analitica FBM a 3 ottave in coordinate World-Space XZ
float evaluateWaveHeight(vec2 xz, float t) {
    float w1 = sin(xz.x * 1.45 + xz.y * 0.65 + t * 1.75) * 0.48;
    float w2 = cos(xz.x * 0.85 - xz.y * 1.65 + t * 1.35) * 0.34;
    float w3 = sin((xz.x - xz.y) * 2.95 - t * 2.35) * 0.18;
    float w4 = cos((xz.x + xz.y * 1.3) * 4.6 + t * 3.1) * 0.08;
    return (w1 + w2 + w3 + w4) * 0.085;
}

#ifdef WATER_CAUSTICS
// Reticolo caustico procedurale 2D in World-Space (interferenza a 2 strati sfasati)
float evaluateCaustics(vec2 xz, float t) {
    vec2 p1 = xz * 1.85 + vec2(t * 0.38, -t * 0.27);
    vec2 p2 = xz * 2.15 + vec2(-t * 0.31, t * 0.42);
    float c1 = abs(sin(p1.x + sin(p1.y * 1.3 + t * 0.6)) + cos(p1.y + cos(p1.x * 1.1 - t * 0.5)));
    float c2 = abs(sin(p2.x * 1.2 - cos(p2.y * 1.4 - t * 0.4)) + cos(p2.y * 1.3 + sin(p2.x * 0.9 + t * 0.7)));
    float net = pow(clamp(1.0 - min(c1, c2) * 0.48, 0.0, 1.0), 3.2);
    return net;
}
#endif

void main() {
    vec4 rawAlbedo = texture(gtexture, vTexCoord) * vColor;
    if (rawAlbedo.a < 0.05) discard;

    vec3 linearAlbedo = srgbToLinear(rawAlbedo.rgb);
    vec3 light = srgbToLinear(texture(lightmap, vLmCoord).rgb);

    // 1. Onde analitiche in World-Space (Zero UV atlas artifacts)
    vec3 worldPos = vWorldPos + cameraPosition;
    float t = frameTimeCounter;
    float eps = 0.05;

    float h0 = evaluateWaveHeight(worldPos.xz, t);
    float hx = evaluateWaveHeight(worldPos.xz + vec2(eps, 0.0), t);
    float hz = evaluateWaveHeight(worldPos.xz + vec2(0.0, eps), t);

    // Gradiente orizzontale World-Space -> trasformato correttamente in View-Space tramite gl_NormalMatrix
    vec3 worldWaveOffset = vec3(-(hx - h0) / eps, 0.0, -(hz - h0) / eps);
    vec3 viewWaveOffset = gl_NormalMatrix * worldWaveOffset;
    vec3 waveNormal = normalize(vNormal + viewWaveOffset * 0.55);

    // 2. Profondità reale della colonna d'acqua tramite depthtex1 (terreno opaco sotto l'acqua)
    vec2 screenUV = gl_FragCoord.xy / vec2(max(viewWidth, 1.0), max(viewHeight, 1.0));
    float opaqueDepthSample = texture(depthtex1, screenUV).r;
    float floorDist = linearizeDepth(opaqueDepthSample);
    float surfaceDist = -vViewPos.z;
    float waterColumnDepth = clamp(floorDist - surfaceDist, 0.0, 24.0);

    // 3. Legge di Beer-Lambert: I(d) = exp(-sigma * d), il rosso viene assorbito per primo, poi il verde, infine il blu
    vec3 sigma = vec3(0.46, 0.17, 0.075);
    vec3 transmittance = exp(-sigma * waterColumnDepth);

    vec3 shallowColor = mix(vec3(0.06, 0.36, 0.44), linearAlbedo * 1.15, 0.45);
    vec3 deepColor    = vec3(0.012, 0.075, 0.17);
    vec3 waterBodyColor = mix(deepColor, shallowColor, transmittance) * light;

#ifdef WATER_CAUSTICS
    if (waterColumnDepth > 0.05 && waterColumnDepth < 18.0) {
        vec3 sunDirWorld = normalize((gbufferModelViewInverse * vec4(sunPosition, 0.0)).xyz);
        // Proiezione del fondale lungo la direzione della luce celeste in World-Space
        vec2 floorWorldXZ = worldPos.xz - sunDirWorld.xz * (waterColumnDepth / max(abs(sunDirWorld.y), 0.25));
        float caustics = evaluateCaustics(floorWorldXZ, t);
        float depthFade = smoothstep(0.05, 0.45, waterColumnDepth) * exp(-waterColumnDepth * 0.14);
        waterBodyColor += vec3(0.55, 0.85, 0.95) * caustics * depthFade * transmittance * vLmCoord.y * 0.65;
    }
#endif

    // 4. Fresnel Schlick per acqua (indice di rifrazione n=1.333 -> F0 = 0.02)
    vec3 V = normalize(-vViewPos);
    float NdotV = max(dot(waveNormal, V), 0.001);
    float fresnel = 0.02 + 0.98 * pow(clamp(1.0 - NdotV, 0.0, 1.0), 5.0);

    // 5. Riflessione atmosferica Rayleigh e Specular GGX del Sole (Sun Glint)
    vec3 upDir = normalize(upPosition);
    vec3 L = normalize(shadowLightPosition.xyz);
    vec3 H = normalize(V + L);
    float sunElevation = clamp(dot(upDir, normalize(sunPosition)) * 0.5 + 0.5, 0.0, 1.0);

    vec3 R = reflect(-V, waveNormal);
    float rUp = clamp(dot(R, upDir), 0.0, 1.0);
    vec3 horizonSky = mix(vec3(0.08, 0.12, 0.22), vec3(0.55, 0.78, 1.05), sunElevation);
    vec3 zenithSky  = mix(vec3(0.02, 0.04, 0.10), vec3(0.18, 0.42, 0.88), sunElevation);
    vec3 skyReflect = mix(horizonSky, zenithSky, pow(rUp, 0.65)) * max(vLmCoord.y, 0.15);

    // Riverbero speculare GGX del disco solare sulle creste d'onda
    float NdotH = max(dot(waveNormal, H), 0.0);
    float NdotL = max(dot(waveNormal, L), 0.0);
    float roughness = 0.035;
    float a2 = roughness * roughness;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    float sunGlint = (a2 / (3.14159265 * denom * denom)) * NdotL * fresnel;
    vec3 sunGlintColor = vec3(1.65, 1.52, 1.32) * clamp(sunGlint * 0.45, 0.0, 4.5) * vLmCoord.y;

    vec3 finalLinearRgb = mix(waterBodyColor, skyReflect, clamp(fresnel * 0.82, 0.04, 0.92)) + sunGlintColor;

    // Opacità fisica: più trasparente sui bordi bassi, più densa in profondità o ad angolo radente (Fresnel)
    float depthAlpha = 1.0 - exp(-waterColumnDepth * 0.45);
    float finalAlpha = clamp(mix(0.52, 0.90, max(depthAlpha, fresnel)), 0.50, 0.94);

    outColor = vec4(finalLinearRgb, finalAlpha);
    outNormal = vec4(waveNormal * 0.5 + 0.5, 1.0);
    outData = vec4(0.96, 0.0, 64.0 / 255.0, 0.0);
}
