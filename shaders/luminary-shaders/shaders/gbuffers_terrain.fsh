#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.fsh
 * G-Buffer stage: linearizzazione sRGB -> Linear, TBN mapping LabPBR 1.3,
 * Parallax Occlusion Mapping (POM) 3D + POM Self-Shadowing,
 * Rain Wetness & Dynamic Puddles con Porosità LabPBR 1.3 (0..64),
 * Cook-Torrance GGX, Subsurface Scattering (B: 65..255),
 * Shadow Map non-lineare simmetrica 9-tap Poisson + shadowcolor0 per ombre colorate,
 * Environment IBL (riflessione emisferica cielo/suolo + sole riflesso su metalli e superfici bagnate).
 */

#include "/lib/settings.glsl"

uniform sampler2D gtexture;     // Albedo sRGB
uniform sampler2D normals;      // Normal map (_n: RG=Normal, B=AO, A=Height)
uniform sampler2D specular;     // Specular map (_s: R=Smoothness, G=F0/Metal, B=Porosity/SSS, A=Emissive)
uniform sampler2D lightmap;     // Vanilla / Mod Lightmap
uniform sampler2D shadowtex0;   // Shadow Map completa (opachi + traslucidi)
uniform sampler2D shadowtex1;   // Shadow Map solo opachi
uniform sampler2D shadowcolor0; // Colore filtro traslucido (vetro colorato, acqua)

uniform vec3 shadowLightPosition;
uniform vec3 upPosition;
uniform vec3 cameraPosition;
uniform int heldBlockLightValue;
uniform int heldBlockLightValue2;
uniform int shadowMapResolution;
uniform float wetness;
uniform float rainStrength;
uniform int isEyeInWater;
uniform float frameTimeCounter;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;
in vec3 vTangent;
in vec3 vBitangent;
in vec3 vViewPos;
in vec3 vWorldNormal;
in vec3 vWorldPos;
in vec4 vShadowPos;
flat in vec4 vAtlasBounds;
flat in int vBlockId;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;   // Linear RGB HDR + Alpha
layout(location = 1) out vec4 outNormal;  // View-Space Normal (XYZ) + Material AO (W)
layout(location = 2) out vec4 outData;    // R=Smoothness, G=Metalness/F0, B=Porosity/SSS, A=Emissive

vec3 srgbToLinear(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

vec2 wrapAtlasCoord(vec2 uv, vec4 bounds) {
    if (bounds.z <= 0.00001 || bounds.w <= 0.00001) return uv;
    vec2 local = mod(uv - bounds.xy, bounds.zw);
    return bounds.xy + local;
}

#ifdef POM_ENABLED
vec2 computeParallaxCoord(vec2 startUV, vec3 viewDirTS, float viewDist, vec4 bounds, vec2 ddx, vec2 ddy, out float outPomDepth) {
    outPomDepth = 0.0;
    if (viewDist > 24.0 || abs(viewDirTS.z) < 0.15 || bounds.z <= 0.00001) return startUV;

    float baseAlpha = textureGrad(gtexture, startUV, ddx, ddy).a;
    if (baseAlpha < 0.99) return startUV;
    float hSample = textureGrad(normals, startUV, ddx, ddy).a;
    if (hSample < 0.02 || hSample > 0.995) return startUV;

    float fade = clamp(1.0 - (viewDist / 24.0), 0.0, 1.0);
    float layerCount = float(POM_STEPS);
    float layerDepth = 1.0 / layerCount;
    vec2 rawOffset = (viewDirTS.xy / max(abs(viewDirTS.z), 0.35)) * (POM_DEPTH * 0.65 * fade) * bounds.zw;
    vec2 maxOffset = clamp(rawOffset, -bounds.zw * 0.22, bounds.zw * 0.22);
    vec2 deltaUV = maxOffset / layerCount;

    vec2 currUV = startUV;
    float currLayerDepth = 0.0;
    float currHeight = 1.0 - hSample;

    for (int i = 0; i < POM_STEPS; i++) {
        if (currLayerDepth >= currHeight) break;
        currUV -= deltaUV;
        currLayerDepth += layerDepth;
        currHeight = 1.0 - (textureGrad(normals, wrapAtlasCoord(currUV, bounds), ddx, ddy).a);
    }

    vec2 prevUV = currUV + deltaUV;
    float afterDepth = currHeight - currLayerDepth;
    float beforeDepth = (1.0 - textureGrad(normals, wrapAtlasCoord(prevUV, bounds), ddx, ddy).a) - (currLayerDepth - layerDepth);
    float weight = clamp(afterDepth / max(afterDepth - beforeDepth, 0.0001), 0.0, 1.0);

    outPomDepth = mix(currHeight, currLayerDepth, weight);
    return wrapAtlasCoord(mix(currUV, prevUV, weight), bounds);
}

float computePomSelfShadow(vec2 pomUV, float surfaceDepth, vec3 lightDirTS, float viewDist, vec4 bounds, vec2 ddx, vec2 ddy) {
    if (viewDist > 20.0 || lightDirTS.z <= 0.05 || surfaceDepth <= 0.04 || bounds.z <= 0.00001) return 1.0;

    float fade = clamp(1.0 - (viewDist / 20.0), 0.0, 1.0);
    const int SHADOW_STEPS = 4;
    float stepDepth = surfaceDepth / float(SHADOW_STEPS);
    vec2 stepUV = (lightDirTS.xy / max(lightDirTS.z, 0.25)) * (POM_DEPTH * fade) * bounds.zw * (stepDepth);

    vec2 currUV = pomUV;
    float currDepth = surfaceDepth;
    float occlusion = 0.0;

    for (int i = 0; i < SHADOW_STEPS; i++) {
        currUV += stepUV;
        currDepth -= stepDepth;
        float sampleDepth = 1.0 - textureGrad(normals, wrapAtlasCoord(currUV, bounds), ddx, ddy).a;
        if (sampleDepth < currDepth - 0.03) {
            occlusion += (currDepth - sampleDepth);
        }
    }
    return clamp(1.0 - occlusion * 1.45 * fade, 0.28, 1.0);
}
#endif

// Microfacet GGX Distribution
float D_GGX(float NdotH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (3.14159265 * denom * denom);
}

float G_SchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

float G_Smith(float NdotV, float NdotL, float roughness) {
    return G_SchlickGGX(NdotV, roughness) * G_SchlickGGX(NdotL, roughness);
}

vec3 F_Schlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

vec3 distortShadowClipPos(vec3 clipPos) {
    float dist = length(clipPos.xy);
    float distortFactor = dist * 0.85 + 0.15;
    clipPos.xy /= distortFactor;
    clipPos.z *= 0.5;
    return clipPos;
}

vec3 sampleColoredShadowMap(vec4 shadowPos, float NdotL) {
#ifdef SHADOW_ENABLED
    if (NdotL <= 0.001) return vec3(0.0);
    vec3 clipPos = shadowPos.xyz / shadowPos.w;
    float distFromCenter = length(clipPos.xy);
    if (distFromCenter > 0.98) return vec3(1.0);

    vec3 distorted = distortShadowClipPos(clipPos);
    vec3 sp = distorted * 0.5 + 0.5;
    if (sp.x < 0.0 || sp.x > 1.0 || sp.y < 0.0 || sp.y > 1.0 || sp.z < 0.0 || sp.z > 1.0) {
        return vec3(1.0);
    }

    float distortFactor = distFromCenter * 0.85 + 0.15;
    float bias = max(0.00075 * (1.0 - NdotL), 0.00025) * (distortFactor * 1.4 + 0.4);
    float currentDepth = sp.z - bias;

    vec2 texelSize = vec2(1.0 / float(max(shadowMapResolution, 512)));
    const vec2 poissonDisk[9] = vec2[9](
        vec2( 0.0,   0.0),
        vec2(-0.75, -0.45),
        vec2( 0.75, -0.45),
        vec2(-0.45,  0.75),
        vec2( 0.45,  0.75),
        vec2(-0.95,  0.15),
        vec2( 0.95, -0.15),
        vec2( 0.15, -0.95),
        vec2(-0.15,  0.95)
    );

    vec3 accumShadow = vec3(0.0);
    for (int i = 0; i < 9; i++) {
        vec2 sampleUV = sp.xy + poissonDisk[i] * texelSize * 1.35;
        float depthAll = texture(shadowtex0, sampleUV).r;
        if (currentDepth <= depthAll) {
            accumShadow += vec3(1.0);
        } else {
            float depthOpaque = texture(shadowtex1, sampleUV).r;
            if (currentDepth <= depthOpaque) {
                vec4 sc = texture(shadowcolor0, sampleUV);
                vec3 tint = srgbToLinear(sc.rgb);
                accumShadow += mix(vec3(1.0), tint, sc.a);
            }
        }
    }
    return accumShadow / 9.0;
#else
    return vec3(1.0);
#endif
}

// Noise procedurale leggero 2D per micro-pozzanghere organiche
float hash2D(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise2D(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash2D(i);
    float b = hash2D(i + vec2(1.0, 0.0));
    float c = hash2D(i + vec2(0.0, 1.0));
    float d = hash2D(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

vec2 computeRainRipples(vec2 worldXZ, float time) {
    vec2 cell = floor(worldXZ * 2.5);
    vec2 local = fract(worldXZ * 2.5) - 0.5;
    float h = hash2D(cell);
    float cycle = fract(time * 1.85 + h);
    float dist = length(local);
    float ringRadius = cycle * 0.42;
    float wave = sin((dist - ringRadius) * 42.0) * smoothstep(0.18, 0.0, abs(dist - ringRadius));
    float fade = (1.0 - cycle) * smoothstep(0.45, 0.10, dist);
    vec2 dir = local / max(dist, 0.001);
    return dir * (wave * fade * 0.14);
}

void main() {
    vec2 coord = vTexCoord;
    vec2 ddx = dFdx(vTexCoord);
    vec2 ddy = dFdy(vTexCoord);

    vec3 geomN = normalize(vNormal);
    vec3 geomT = normalize(vTangent);
    vec3 geomB = normalize(vBitangent);
    mat3 tbn = mat3(geomT, geomB, geomN);
    mat3 tbnInv = transpose(tbn);

    float viewDist = length(vViewPos);
    vec3 V = normalize(-vViewPos);
    vec3 L = normalize(shadowLightPosition.xyz);

    float pomSelfShadow = 1.0;

#if defined(PBR_ENABLED) && defined(POM_ENABLED)
    vec3 viewDirTS = normalize(tbnInv * V);
    vec3 lightDirTS = normalize(tbnInv * L);
    float pomDepth = 0.0;
    coord = computeParallaxCoord(coord, viewDirTS, viewDist, vAtlasBounds, ddx, ddy, pomDepth);
    pomSelfShadow = computePomSelfShadow(coord, pomDepth, lightDirTS, viewDist, vAtlasBounds, ddx, ddy);
#endif

    vec4 rawAlbedo = textureGrad(gtexture, coord, ddx, ddy) * vColor;
    if (rawAlbedo.a < 0.1) discard;

    vec3 linearAlbedo = srgbToLinear(rawAlbedo.rgb);

    vec3 N = geomN;
    float ao = 1.0;
    float smoothness = 0.0;
    float isMetal = 0.0;
    vec3 F0 = vec3(0.04);
    float porosity = 0.0;
    float sss = 0.0;
    float emissive = 0.0;

#ifdef PBR_ENABLED
    vec4 normalSample = textureGrad(normals, coord, ddx, ddy);
    vec4 specSample = textureGrad(specular, coord, ddx, ddy);

    if (normalSample.r > 0.004 || normalSample.g > 0.004) {
        vec2 normalXY = normalSample.xy * 2.0 - 1.0;
        normalXY *= 1.35;
        float normalZ = sqrt(max(0.02, 1.0 - dot(normalXY, normalXY)));
        vec3 tNormal = normalize(vec3(normalXY, normalZ));
        N = normalize(tbn * tNormal);
        ao = clamp(pow(normalSample.b, 1.35), 0.18, 1.0);
    }

    smoothness = specSample.r;
    float rawG = specSample.g * 255.0;

    if (rawG <= 229.5) {
        float f0_scalar = max(pow(specSample.g, 2.0), 0.02);
        F0 = vec3(f0_scalar);
        isMetal = 0.0;
    } else {
        isMetal = 1.0;
        int mCode = int(floor(rawG + 0.5));
        if (mCode == 230)      F0 = vec3(0.56, 0.57, 0.58); // Ferro (Fe)
        else if (mCode == 231) F0 = vec3(0.91, 0.92, 0.92); // Alluminio (Al)
        else if (mCode == 232) F0 = vec3(0.55, 0.56, 0.55); // Cromo (Cr)
        else if (mCode == 233) F0 = vec3(0.95, 0.64, 0.54); // Rame (Cu)
        else if (mCode == 234) F0 = vec3(1.00, 0.71, 0.29); // Oro (Au)
        else if (mCode == 235) F0 = vec3(0.68, 0.66, 0.63); // Platino (Pt)
        else if (mCode == 236) F0 = vec3(0.66, 0.61, 0.53); // Nichel (Ni)
        else if (mCode == 237) F0 = vec3(0.97, 0.96, 0.91); // Argento (Ag)
        else                   F0 = linearAlbedo;            // Custom Metal (255)
    }

    float rawB = specSample.b * 255.0;
    if (rawB <= 64.0) {
        porosity = rawB / 64.0;
        sss = 0.0;
    } else {
        porosity = 0.0;
        sss = (rawB - 65.0) / 190.0;
    }

    float rawEmissive = specSample.a * 255.0;
    if (rawEmissive >= 1.0 && rawEmissive <= 254.0) {
        emissive = rawEmissive / 254.0;
    }

    // Fallback Integrated PBR (IPBR) via block.properties se specular non definita/neutra
    if (specSample.r < 0.01 && specSample.g < 0.01 && specSample.a < 0.01) {
        if (vBlockId == 1) {
            emissive = max(emissive, 0.75);
        } else if (vBlockId == 2) {
            isMetal = 1.0;
            F0 = vec3(0.56, 0.57, 0.58);
            smoothness = 0.55;
        } else if (vBlockId == 3) {
            isMetal = 1.0;
            F0 = vec3(1.00, 0.71, 0.29);
            smoothness = 0.65;
        } else if (vBlockId == 4) {
            isMetal = 1.0;
            F0 = vec3(0.95, 0.64, 0.54);
            smoothness = 0.50;
        } else if (vBlockId == 10018 || vBlockId == 5) {
            sss = max(sss, 0.65);
        }
    }
#endif

    // =========================================================================
    // RAIN WETNESS & DYNAMIC PUDDLES (Atmospheric Upgrade v1.1.0)
    // =========================================================================
    float effectiveRain = max(wetness, rainStrength);
    float skyExposure = clamp((vLmCoord.y - 0.70) / 0.28, 0.0, 1.0);
    float wetFactor = effectiveRain * skyExposure * float(isEyeInWater == 0);

#ifdef RAIN_WETNESS
    if (wetFactor > 0.001) {
        // 1. Oscuramento fisico albedo per assorbimento d'acqua nei materiali porosi
        // I materiali con porosità alta assorbono più acqua e si scuriscono significativamente
        float absorbDarken = mix(1.0, 0.58, porosity * wetFactor);
        linearAlbedo *= absorbDarken;

        // 2. Incremento smoothness superficiale dovuto al velo d'acqua (film sottile)
        float wetSmoothness = mix(smoothness, 0.88, wetFactor * (0.35 + 0.65 * (1.0 - porosity)));
        smoothness = max(smoothness, wetSmoothness);
        if (isMetal < 0.5) {
            F0 = mix(F0, vec3(0.04), wetFactor * 0.5); // F0 acqua ~ 0.02..0.04
        }
    }
#endif

#ifdef DYNAMIC_PUDDLES
    if (wetFactor > 0.05 && vWorldNormal.y > 0.80) {
        // Micro-pozzanghere organiche su superfici orizzontali rivolte al cielo
        vec3 worldAbsPos = vWorldPos + cameraPosition;
        float puddleNoise = noise2D(worldAbsPos.xz * 0.65);
        puddleNoise = puddleNoise * 0.7 + noise2D(worldAbsPos.xz * 1.85) * 0.3;

        // Soglia di accumulo guidata da intensità pioggia e porosità (materiali impermeabili formano pozzanghere prima)
        float accumulationThreshold = mix(0.70, 0.35, wetFactor * (1.0 - porosity * 0.45));
        float puddleMask = smoothstep(accumulationThreshold, accumulationThreshold + 0.15, puddleNoise);

        if (puddleMask > 0.01) {
            // Appiattimento normale verso l'alto con anelli d'impatto procedurali durante pioggia
            vec2 rippleOffset = vec2(0.0);
            if (rainStrength > 0.05) {
                rippleOffset = computeRainRipples(worldAbsPos.xz, frameTimeCounter) * rainStrength * puddleMask;
            }
            vec3 puddleWorldUp = normalize(vec3(rippleOffset.x, 1.0, rippleOffset.y));
            vec3 flatViewUp = normalize(gl_NormalMatrix * puddleWorldUp);
            N = normalize(mix(N, flatViewUp, puddleMask * 0.92));
            smoothness = mix(smoothness, 0.95, puddleMask);
            if (isMetal < 0.5) {
                F0 = mix(F0, vec3(0.025), puddleMask);
            }
            // Scurimento fondale pozzanghera per rifrazione/accumulo
            linearAlbedo *= mix(1.0, 0.72, puddleMask);
        }
    }
#endif

    vec2 lm = vLmCoord;
    vec3 dynamicTorchLight = vec3(0.0);
#ifdef DYNAMIC_LIGHTS
    int maxHeldLight = max(heldBlockLightValue, heldBlockLightValue2);
    if (maxHeldLight > 0) {
        vec3 handLightPos = vec3(0.25, 0.15, -0.35);
        vec3 toLight = handLightPos - vViewPos;
        float lightDist = length(toLight);
        vec3 L_dyn = toLight / max(lightDist, 0.001);
        float radius = float(maxHeldLight) * 1.05;
        float atten = clamp(1.0 - (lightDist / max(radius, 1.0)), 0.0, 1.0);
        atten = smoothstep(0.0, 1.0, atten);
        float NdotL_dyn = mix(0.45, 1.0, max(dot(N, L_dyn), 0.0));
        float dynIntensity = (float(maxHeldLight) / 15.0) * atten * atten;
        lm.x = max(lm.x, dynIntensity * 0.92);
        dynamicTorchLight = vec3(1.35, 0.85, 0.42) * dynIntensity * NdotL_dyn * 0.95;
    }
#endif

    vec3 totalLightMap = srgbToLinear(texture(lightmap, lm).rgb);
    vec3 skyOnlyLight  = srgbToLinear(texture(lightmap, vec2(0.03125, lm.y)).rgb);
    vec3 blockLight    = max(totalLightMap - skyOnlyLight, vec3(0.0));

    vec3 upDir = normalize(upPosition);
    vec3 H = normalize(V + L);

    float NdotL = max(dot(N, L), 0.0);
    float geomNdotL = max(dot(geomN, L), 0.0);
    float NdotV = max(dot(N, V), 0.001);
    float NdotH = max(dot(N, H), 0.0);
    float VdotH = max(dot(V, H), 0.0);

    vec3 specularColor = vec3(0.0);
    vec3 shadowColor = vec3(1.0);
    vec3 sssLight = vec3(0.0);

#ifdef SHADOW_ENABLED
    shadowColor = sampleColoredShadowMap(vShadowPos, max(NdotL, geomNdotL));
#endif

    shadowColor *= pomSelfShadow;

    if (sss > 0.01) {
        float wrapNdotL = max((dot(N, L) + 0.50) / 1.50, 0.0);
        // Mie forward-scattering solare/lunare attraverso il fogliame (trasmissione back-lit)
        float forwardScatter = pow(clamp(dot(V, -L), 0.0, 1.0), 3.0) * 1.25;
        // Tonalità calda smeraldo/oro di trasmissione fogliame
        vec3 foliageTint = mix(linearAlbedo, vec3(0.55, 0.85, 0.35), 0.40);
        vec3 sssShadow = mix(vec3(0.35), vec3(1.0), shadowColor);
        sssLight = foliageTint * (skyOnlyLight * 1.35 + blockLight * 0.8) * (wrapNdotL * 0.45 + forwardScatter) * sss * sssShadow;
    }

    vec3 celestialIlluminance = mix(vec3(0.48, 0.52, 0.62), vec3(1.50, 1.45, 1.36), NdotL * shadowColor);
    vec3 directSkyLight = skyOnlyLight * celestialIlluminance;
    vec3 totalLight = directSkyLight + blockLight + dynamicTorchLight;

#ifdef PBR_ENABLED
    float roughness = max(pow(1.0 - smoothness, 2.0), 0.02);
    vec3 F = F_Schlick(VdotH, F0);

    if (smoothness > 0.02 && NdotL > 0.0) {
        float NDF = D_GGX(NdotH, roughness);
        float G = G_Smith(NdotV, NdotL, roughness);
        vec3 numerator = NDF * G * F;
        float denominator = 4.0 * NdotV * NdotL + 0.0001;
        specularColor += (numerator / denominator) * NdotL * skyOnlyLight * shadowColor * 2.1;
    }

    // Riflesso Speculare Ambientale per metalli, gemme e superfici bagnate/pozzanghere
    if (smoothness > 0.18 || isMetal > 0.5) {
        vec3 R = reflect(-V, N);
        float skyFactor = clamp(dot(R, upDir) * 0.5 + 0.5, 0.0, 1.0);
        float skyVis = clamp(lm.y * 1.15, 0.15, 1.0);
        vec3 envSky = mix(vec3(0.12, 0.14, 0.18), vec3(0.62, 0.84, 1.18), skyFactor) * skyVis;

        float rDotSun = clamp(dot(R, L), 0.0, 1.0);
        float glintPower = mix(8.0, 48.0, smoothness);
        float rainGlintMod = mix(1.0, 0.40, wetFactor); // Attenua il riverbero del sole diretto durante pioggia (luce diffusa)
        envSky += vec3(1.55, 1.42, 1.18) * pow(rDotSun, glintPower) * (0.35 + 0.65 * shadowColor) * skyVis * rainGlintMod;
        envSky += vec3(1.25, 0.78, 0.35) * (lm.x * lm.x * 1.05);

        vec3 F_env = F_Schlick(NdotV, F0);
        vec3 metalTint = mix(vec3(1.0), linearAlbedo * 1.15, isMetal);
        float envStrength = pow(smoothness, 1.6) * mix(0.48, 1.10, isMetal);
        specularColor += envSky * F_env * metalTint * envStrength * ao;
    }
#endif

    float kD = 1.0 - isMetal * 0.72;
    vec3 diffuse = linearAlbedo * totalLight * ao * kD;
    // Rim-light e glow emissivo LabPBR per blocchi incandescenti (lava, shroomlight, crying obsidian, soul fire)
    float emissiveRim = pow(1.0 - NdotV, 3.0) * emissive * 1.25;
    vec3 emissiveLight = linearAlbedo * (pow(emissive, 1.35) * 2.15 + emissiveRim);
    vec3 finalLinearRgb = diffuse + specularColor + sssLight + emissiveLight;

    outColor = vec4(finalLinearRgb, rawAlbedo.a);
    outNormal = vec4(N * 0.5 + 0.5, ao);
    outData = vec4(smoothness, isMetal, max(porosity, sss), emissive);
}
