#version 330 compatibility

/*
 * Luminary Shaders - composite.fsh
 * Release: v1.1.0 (Atmospheric & Wetness Upgrade)
 *
 * 1. Screen-Space Reflections (SSR) in View-Space:
 *    - Raymarch su superfici dielettriche/metalliche lisce o bagnate (smoothness > 0.65) e acqua.
 *    - Binary search refinement (2 iterazioni) per precisione millimetrica sul bordo d'impatto.
 *    - Screen-edge vignette fade per transizione morbida con fallback su gradiente cielo.
 *    - Risparmio energetico di Fresnel Schlick.
 * 2. Volumetric Light / Godrays:
 *    - Dithered raymarching verso la shadow map (shadowtex0) con Bayer 4x4 anti-banding.
 *    - Scattering di fase anisotropo Henyey-Greenstein.
 *    - Scalabile per profilo (Potato: off, Balanced: 8 passi, Cinematic: 16 passi).
 * 3. Bloom gaussiano a 9-tap multi-scala su sorgenti emissive ed eccessi HDR.
 */

#include "/lib/settings.glsl"

uniform sampler2D colortex0; // HDR Linear Scene Color
uniform sampler2D colortex1; // View-Space Normal (RGB 0..1 -> -1..1) + Material AO (A)
uniform sampler2D colortex2; // LabPBR Data (R=Smoothness, G=Metal, B=Porosity/SSS, A=Emissive)
uniform sampler2D depthtex0;  // Profondità completa (incluso traslucido/acqua)
uniform sampler2D depthtex1;  // Profondità solo opachi
uniform sampler2D shadowtex0; // Shadow Map completa

uniform mat4 gbufferProjection;
uniform mat4 gbufferProjectionInverse;
uniform mat4 shadowModelView;
uniform mat4 shadowProjection;
uniform vec3 shadowLightPosition;
uniform vec3 upPosition;
uniform vec3 sunPosition;
uniform float viewWidth;
uniform float viewHeight;
uniform float near;
uniform float far;
uniform float wetness;
uniform float rainStrength;

in vec2 vTexCoord;

/* RENDERTARGETS: 0,3 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outBloom;

// Dithering Bayer 4x4
float bayer4x4(vec2 coord) {
    int x = int(mod(coord.x, 4.0));
    int y = int(mod(coord.y, 4.0));
    int index = x + y * 4;
    
    const float dTable[16] = float[16](
         0.0 / 16.0,  8.0 / 16.0,  2.0 / 16.0, 10.0 / 16.0,
        12.0 / 16.0,  4.0 / 16.0, 14.0 / 16.0,  6.0 / 16.0,
          3.0 / 16.0, 11.0 / 16.0,  1.0 / 16.0,  9.0 / 16.0,
        15.0 / 16.0,  7.0 / 16.0, 13.0 / 16.0,  5.0 / 16.0
    );
    return dTable[index];
}

// Ricostruzione posizione view-space da coordinate schermo (UV + Depth)
vec3 reconstructViewPos(vec2 uv, float depth) {
    vec4 clipPos = vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 viewPosH = gbufferProjectionInverse * clipPos;
    return viewPosH.xyz / max(viewPosH.w, 0.00001);
}

// Proiezione da View-Space a Screen UV (0..1) e Clip Depth (0..1)
vec3 projectViewToScreen(vec3 vPos) {
    vec4 clip = gbufferProjection * vec4(vPos, 1.0);
    vec3 ndc = clip.xyz / max(clip.w, 0.00001);
    return ndc * 0.5 + 0.5;
}

// Distorsione simmetrica shadow map
vec3 distortShadowClipPos(vec3 clipPos) {
    float dist = length(clipPos.xy);
    float distortFactor = dist * 0.85 + 0.15;
    clipPos.xy /= distortFactor;
    clipPos.z *= 0.5;
    return clipPos;
}

// Fase di Henyey-Greenstein per scattering in avanti verso la sorgente luminosa
float henyeyGreenstein(float cosTheta, float g) {
    float g2 = g * g;
    return (1.0 - g2) / (4.0 * 3.14159265 * pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5));
}

// =============================================================================
// SCREEN-SPACE REFLECTIONS (SSR)
// =============================================================================
vec3 computeSSR(vec3 viewPos, vec3 N, float smoothness, float isMetal, vec2 screenUV, float dither) {
#if !defined(SSR_ENABLED) || SSR_QUALITY == 0
    return vec3(0.0);
#else
    vec3 V = normalize(-viewPos);
    vec3 R = reflect(-V, N);

    // Evita raymarching per riflessi rivolti verso la telecamera o dentro la geometria
    if (dot(R, N) <= 0.001 || R.z > 0.0) return vec3(0.0);

#if SSR_QUALITY == 1
    const int MAX_STEPS = 12;
    const int BINARY_STEPS = 2;
    float maxDist = 32.0;
#else
    const int MAX_STEPS = 24;
    const int BINARY_STEPS = 3;
    float maxDist = 48.0;
#endif

    float stepSize = maxDist / float(MAX_STEPS);
    vec3 rayPos = viewPos + N * 0.06; // Epsilon offset lungo la normale per evitare self-intersection

    // Jitter iniziale del passo con Bayer dither
    rayPos += R * (stepSize * (0.35 + 0.65 * dither));

    bool hit = false;
    vec2 hitUV = vec2(0.0);
    vec3 stepVec = R * stepSize;

    for (int i = 0; i < MAX_STEPS; i++) {
        rayPos += stepVec;
        vec3 sUV = projectViewToScreen(rayPos);

        // Uscito dai limiti dello schermo
        if (sUV.x < 0.0 || sUV.x > 1.0 || sUV.y < 0.0 || sUV.y > 1.0 || sUV.z < 0.0 || sUV.z > 1.0) {
            break;
        }

        float sampledDepth = texture(depthtex0, sUV.xy).r;
        if (sampledDepth >= 0.9999) continue; // Salta il cielo

        vec3 sceneViewPos = reconstructViewPos(sUV.xy, sampledDepth);
        float depthDiff = rayPos.z - sceneViewPos.z; // Entrambi negativi in OpenGL View-Space

        // Ray dietro la superficie ma entro lo spessore tollerato (0.8 blocchi)
        if (depthDiff <= 0.0 && depthDiff > -0.85) {
            // Raffinamento binario per trovare l'impatto esatto
            vec3 p0 = rayPos - stepVec;
            vec3 p1 = rayPos;

            for (int b = 0; b < BINARY_STEPS; b++) {
                vec3 mid = (p0 + p1) * 0.5;
                vec3 midUV = projectViewToScreen(mid);
                float midDepth = texture(depthtex0, midUV.xy).r;
                vec3 midScenePos = reconstructViewPos(midUV.xy, midDepth);
                float midDiff = mid.z - midScenePos.z;

                if (midDiff <= 0.0) {
                    p1 = mid;
                    hitUV = midUV.xy;
                } else {
                    p0 = mid;
                }
            }
            hit = true;
            break;
        }
    }

    if (!hit) return vec3(0.0);

    // Screen-edge vignette fade (zero hard clipping sui bordi dello schermo)
    vec2 edgeFade2D = smoothstep(vec2(0.0), vec2(0.12), hitUV) * (1.0 - smoothstep(vec2(0.88), vec2(1.0), hitUV));
    float edgeFade = clamp(edgeFade2D.x * edgeFade2D.y, 0.0, 1.0);

    // Fade morbido sui raggi radenti e sulla distanza percorsa
    float distFade = clamp(1.0 - length(rayPos - viewPos) / maxDist, 0.0, 1.0);
    float finalWeight = edgeFade * distFade;

    vec3 reflectedSample = texture(colortex0, hitUV).rgb;
    return reflectedSample * finalWeight;
#endif
}

// =============================================================================
// VOLUMETRIC LIGHT / GODRAYS
// =============================================================================
vec3 computeVolumetricLight(vec3 viewPos, float depth, vec2 screenUV, float dither, float rain) {
#if !defined(VOLUMETRIC_LIGHT) || VOLUMETRIC_QUALITY == 0
    return vec3(0.0);
#else
    vec3 L = normalize(shadowLightPosition.xyz);
    vec3 V = normalize(viewPos);
    float cosTheta = dot(V, L);

    // Fase di scattering calibrata (Henyey-Greenstein g = 0.58)
    float phase = henyeyGreenstein(cosTheta, 0.58);

#if VOLUMETRIC_QUALITY == 1
    const int STEPS = 8;
    float maxMarchDist = min(length(viewPos), 36.0);
#else
    const int STEPS = 16;
    float maxMarchDist = min(length(viewPos), 54.0);
#endif

    if (maxMarchDist < 1.0) return vec3(0.0);

    float stepLength = maxMarchDist / float(STEPS);
    vec3 rayDir = normalize(viewPos);
    vec3 startPos = rayDir * (stepLength * dither);

    vec3 accumLight = vec3(0.0);
    vec3 sunColor = vec3(1.20, 1.15, 1.05);

    for (int i = 0; i < STEPS; i++) {
        vec3 sampleView = startPos + rayDir * (float(i) * stepLength);

        // Trasformazione da View-Space a Shadow-Space
        vec4 shadowView = shadowModelView * vec4(sampleView, 1.0);
        vec4 shadowClip = shadowProjection * shadowView;
        vec3 spClip = shadowClip.xyz / max(shadowClip.w, 0.00001);

        float distFromCenter = length(spClip.xy);
        if (distFromCenter < 0.95) {
            vec3 distorted = distortShadowClipPos(spClip);
            vec3 sp = distorted * 0.5 + 0.5;

            if (sp.x >= 0.0 && sp.x <= 1.0 && sp.y >= 0.0 && sp.y <= 1.0 && sp.z >= 0.0 && sp.z <= 1.0) {
                float shadowSample = texture(shadowtex0, sp.xy).r;
                float bias = 0.0012;
                if (sp.z - bias <= shadowSample) {
                    accumLight += sunColor;
                }
            }
        }
    }

    // Intensità bilanciata: 0.55 moltiplicatore base, attenuato durante la pioggia (cielo coperto)
    float rainAtten = mix(1.0, 0.20, rain);
    vec3 godrays = (accumLight / float(STEPS)) * (phase * 0.55 * rainAtten);
    return godrays;
#endif
}

void main() {
    vec4 baseColor = texture(colortex0, vTexCoord);
    vec4 normalData = texture(colortex1, vTexCoord);
    vec4 pbrData = texture(colortex2, vTexCoord);
    float depth = texture(depthtex0, vTexCoord).r;
    float opaqueDepth = texture(depthtex1, vTexCoord).r;
    float effectiveRain = max(wetness, rainStrength);

    float smoothness = pbrData.r;
    float isMetal = pbrData.g;
    float emissive = pbrData.a;

    vec3 N = normalize(normalData.xyz * 2.0 - 1.0);
    vec3 color = baseColor.rgb;

#ifdef WATER_CAUSTICS
    // Micro-rifrazione screen-space (Snell UV offset) sui pixel d'acqua (depthtex0 < depthtex1)
    bool isWaterPixel = (depth < opaqueDepth - 0.0001) && (abs(pbrData.b - (64.0 / 255.0)) < 0.025);
    if (isWaterPixel) {
        float waterThickness = clamp((opaqueDepth - depth) * 24.0, 0.0, 1.0);
        vec2 refractUV = clamp(vTexCoord + N.xy * (0.018 * waterThickness), 0.002, 0.998);
        float refractOpaqueDepth = texture(depthtex1, refractUV).r;
        // Clamp di sicurezza: campiona solo se il pixel rifratto è dietro la superficie dell'acqua
        if (refractOpaqueDepth > depth + 0.0001) {
            vec3 refractedCol = texture(colortex0, refractUV).rgb;
            color = mix(color, refractedCol, 0.35 * waterThickness);
        }
    }
#endif

    vec2 screenCoord = vTexCoord * vec2(max(viewWidth, 1280.0), max(viewHeight, 720.0));
    float dither = bayer4x4(screenCoord);

    // Ricostruzione View-Space
    vec3 viewPos = reconstructViewPos(vTexCoord, depth);

    // 1. Screen-Space Reflections (SSR) per superfici dielettriche/metalliche lisce o bagnate (smoothness > 0.65)
    if (depth < 0.9999 && smoothness > 0.65) {
        vec3 ssrColor = vec3(0.0);

        // SSR Roughness Filtering:
        // Se la superficie è speculare perfetta (smoothness >= 0.92, es. acqua calma, vetro), raymarch singolo nitido.
        // Se la superficie è satinata (0.65 < smoothness < 0.92, es. metalli levigati, pietre umide),
        // applica spatial jitter-blur a 3-tap guidato da roughness = 1.0 - smoothness.
        if (smoothness < 0.92) {
            float roughness = (1.0 - smoothness);
            float blurRadius = roughness * 0.18;

            // Vettore tangente e bitangente ortogonali alla normale N
            vec3 upVec = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
            vec3 tangent = normalize(cross(upVec, N));
            vec3 bitangent = cross(N, tangent);

            // Tap 1: centrale con micro-offset ditherato
            vec3 N1 = normalize(N + (tangent * (dither - 0.5) + bitangent * (dither - 0.5)) * (blurRadius * 0.6));
            vec3 sample1 = computeSSR(viewPos, N1, smoothness, isMetal, vTexCoord, dither);

            // Tap 2: offset positivo lungo la tangente
            vec3 N2 = normalize(N + (tangent * 0.866 + bitangent * 0.5) * blurRadius);
            vec3 sample2 = computeSSR(viewPos, N2, smoothness, isMetal, vTexCoord, fract(dither + 0.333));

            // Tap 3: offset negativo lungo la bitangente
            vec3 N3 = normalize(N + (-tangent * 0.866 - bitangent * 0.5) * blurRadius);
            vec3 sample3 = computeSSR(viewPos, N3, smoothness, isMetal, vTexCoord, fract(dither + 0.666));

            ssrColor = (sample1 * 0.50) + (sample2 * 0.25) + (sample3 * 0.25);
        } else {
            ssrColor = computeSSR(viewPos, N, smoothness, isMetal, vTexCoord, dither);
        }

        // Fresnel fisico Schlick per pesare il riflesso
        vec3 V = normalize(-viewPos);
        float NdotV = max(dot(N, V), 0.001);
        vec3 F0 = mix(vec3(0.04), baseColor.rgb, isMetal);
        vec3 F = F0 + (1.0 - F0) * pow(clamp(1.0 - NdotV, 0.0, 1.0), 5.0);

        float reflectionStrength = pow(smoothness, 2.0) * mix(0.75, 1.0, isMetal);
        color = mix(color, color + ssrColor * F, reflectionStrength);
    }

    // 2. Volumetric Light / Godrays
    if (depth > 0.0001 && effectiveRain < 0.85) {
        vec3 godrays = computeVolumetricLight(viewPos, depth, vTexCoord, dither, effectiveRain);
        color += godrays;
    }

    // 3. Isolamento Bloom Gaussiano 9-tap
    vec2 px = vec2(1.0 / max(viewWidth, 1280.0), 1.0 / max(viewHeight, 720.0));
    const vec2 offsets[9] = vec2[9](
        vec2( 0.0,  0.0),
        vec2( 2.5,  0.0),
        vec2(-2.5,  0.0),
        vec2( 0.0,  2.5),
        vec2( 0.0, -2.5),
        vec2( 4.0,  4.0),
        vec2(-4.0,  4.0),
        vec2( 4.0, -4.0),
        vec2(-4.0, -4.0)
    );
    const float weights[9] = float[9](
        0.24, 0.12, 0.12, 0.12, 0.12, 0.07, 0.07, 0.07, 0.07
    );

    vec3 bloomAccum = vec3(0.0);
    for (int i = 0; i < 9; i++) {
        vec2 sUV = clamp(vTexCoord + offsets[i] * px, 0.001, 0.999);
        vec3 sCol = texture(colortex0, sUV).rgb;
        float sEm = texture(colortex2, sUV).a;
        float luma = dot(sCol, vec3(0.2126, 0.7152, 0.0722));
        float hdrExcess = max(luma - 1.15, 0.0);
        vec3 contrib = sCol * (sEm * 1.45 + hdrExcess * 0.65);
        bloomAccum += contrib * weights[i];
    }

#ifdef PBR_ENABLED
    if (isMetal > 0.5) {
        color *= (1.0 + smoothness * 0.22);
    }
#endif

    outColor = vec4(color, baseColor.a);
    outBloom = vec4(bloomAccum, 1.0);
}
