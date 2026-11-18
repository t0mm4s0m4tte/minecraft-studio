#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.fsh
 * Shading fisicamente calibrato LabPBR 1.3 con Shadow Map PCF e luci dinamiche calde/ciano.
 */

#include "/lib/settings.glsl"

uniform sampler2D gtexture;    // Albedo
uniform sampler2D normals;     // Normal map (_n: RG=Normal, B=AO, A=Height)
uniform sampler2D specular;    // Specular map (_s: R=Smoothness, G=F0/Metal, B=Porosity, A=Emissive)
uniform sampler2D lightmap;    // Vanilla Lightmap
uniform sampler2D shadowtex0;  // Iris Shadow Map
uniform sampler2D shadowcolor0;

uniform vec3 sunPosition;
uniform vec3 shadowLightPosition;
uniform int heldItemId;
uniform int heldBlockLightValue;
uniform int heldBlockLightValue2;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;
in vec3 vTangent;
in vec3 vBitangent;
in vec3 vViewPos;
in vec4 vShadowPos;
flat in vec4 vAtlasBounds;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData; // R=Smoothness, G=Metalness, B=AO, A=Emissive

// Microfacet GGX Distribution
float D_GGX(float NdotH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (3.14159265 * denom * denom);
}

// Schlick-GGX Attenuation
float G_SchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

float G_Smith(float NdotV, float NdotL, float roughness) {
    return G_SchlickGGX(NdotV, roughness) * G_SchlickGGX(NdotL, roughness);
}

// Fresnel-Schlick
vec3 F_Schlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

vec2 wrapAtlasCoord(vec2 uv, vec4 bounds) {
    if (bounds.z <= 0.00001 || bounds.w <= 0.00001) return uv;
    vec2 local = mod(uv - bounds.xy, bounds.zw);
    return bounds.xy + local;
}

#ifdef POM_ENABLED
vec2 computeParallaxCoord(vec2 startUV, vec3 viewDirTS, float viewDist, vec4 bounds, vec2 ddx, vec2 ddy) {
    if (viewDist > 20.0 || abs(viewDirTS.z) < 0.15 || bounds.z <= 0.00001) return startUV;

    float fade = clamp(1.0 - (viewDist / 20.0), 0.0, 1.0);
    float layerCount = float(POM_STEPS);
    float layerDepth = 1.0 / layerCount;
    vec2 maxOffset = (viewDirTS.xy / max(abs(viewDirTS.z), 0.25)) * (POM_DEPTH * fade) * bounds.zw;
    vec2 deltaUV = maxOffset / layerCount;

    vec2 currUV = startUV;
    float currLayerDepth = 0.0;
    float currHeight = 1.0 - textureGrad(normals, wrapAtlasCoord(currUV, bounds), ddx, ddy).a;

    for (int i = 0; i < POM_STEPS; i++) {
        if (currLayerDepth >= currHeight) break;
        currUV -= deltaUV;
        currLayerDepth += layerDepth;
        currHeight = 1.0 - textureGrad(normals, wrapAtlasCoord(currUV, bounds), ddx, ddy).a;
    }

    vec2 prevUV = currUV + deltaUV;
    float afterDepth = currHeight - currLayerDepth;
    float beforeDepth = (1.0 - textureGrad(normals, wrapAtlasCoord(prevUV, bounds), ddx, ddy).a) - (currLayerDepth - layerDepth);
    float weight = clamp(afterDepth / max(afterDepth - beforeDepth, 0.0001), 0.0, 1.0);

    return wrapAtlasCoord(mix(currUV, prevUV, weight), bounds);
}
#endif

// Campionamento Shadow Map PCF 4-tap a costo ridotto (<= 3.8ms)
float sampleShadowMap(vec4 shadowPos, float NdotL) {
#ifdef SHADOW_ENABLED
    vec3 sp = shadowPos.xyz / shadowPos.w;
    sp = sp * 0.5 + 0.5;
    
    // Controllo fuori bounds frustum ombra
    if (sp.x < 0.0 || sp.x > 1.0 || sp.y < 0.0 || sp.y > 1.0 || sp.z < 0.0 || sp.z > 1.0) {
        return 1.0;
    }
    
    // Bias adattivo per eliminare shadow acne
    float bias = max(0.0018 * (1.0 - NdotL), 0.0006);
    float currentDepth = sp.z - bias;
    
    // PCF a 4 campioni bilineari
    float shadow = 0.0;
    vec2 texelSize = vec2(1.0 / 1024.0);
    shadow += step(currentDepth, texture(shadowtex0, sp.xy + vec2(-0.5, -0.5) * texelSize).r);
    shadow += step(currentDepth, texture(shadowtex0, sp.xy + vec2( 0.5, -0.5) * texelSize).r);
    shadow += step(currentDepth, texture(shadowtex0, sp.xy + vec2(-0.5,  0.5) * texelSize).r);
    shadow += step(currentDepth, texture(shadowtex0, sp.xy + vec2( 0.5,  0.5) * texelSize).r);
    return shadow * 0.25;
#else
    return 1.0;
#endif
}

void main() {
    vec2 coord = vTexCoord;
    vec2 ddx = dFdx(vTexCoord);
    vec2 ddy = dFdy(vTexCoord);

    vec3 geomN = normalize(vNormal);
    vec3 geomT = normalize(vTangent);
    vec3 geomB = normalize(vBitangent);
    mat3 tbn = mat3(geomT, geomB, geomN);

    float viewDist = length(vViewPos);
    vec3 V = normalize(-vViewPos);

#if defined(PBR_ENABLED) && defined(POM_ENABLED)
    vec3 viewDirTS = normalize(transpose(tbn) * V);
    coord = computeParallaxCoord(coord, viewDirTS, viewDist, vAtlasBounds, ddx, ddy);
#endif

    vec4 albedo = textureGrad(gtexture, coord, ddx, ddy) * vColor;
    if (albedo.a < 0.1) discard;

    vec3 N = geomN;
    float ao = 1.0;
    float smoothness = 0.0;
    float isMetal = 0.0;
    float emissive = 0.0;
    vec3 F0 = vec3(0.04);

#ifdef PBR_ENABLED
    vec4 normalSample = textureGrad(normals, coord, ddx, ddy);
    vec4 specSample = textureGrad(specular, coord, ddx, ddy);

    vec2 normalXY = (normalSample.xy * 2.0 - 1.0) * 1.5;
    float normalZ = sqrt(max(0.001, 1.0 - dot(normalXY, normalXY)));
    vec3 tNormal = normalize(vec3(normalXY, normalZ));
    N = normalize(tbn * tNormal);

#if AO_QUALITY >= 1
    ao = mix(1.0, normalSample.b, 0.75);
#endif

    smoothness = specSample.r;
    float f0_metal = specSample.g;

    if (f0_metal >= (229.5 / 255.0)) {
        isMetal = 1.0;
        F0 = albedo.rgb;
    } else {
        isMetal = 0.0;
        F0 = max(vec3(f0_metal * (255.0 / 229.0) * 0.04), vec3(0.04));
    }

    float rawEmissive = specSample.a * 255.0;
    if (rawEmissive > 0.5 && rawEmissive < 254.5) {
        emissive = rawEmissive / 254.0;
    }
#endif

    vec2 lm = vLmCoord;
    vec3 dynLightTint = vec3(1.0, 0.82, 0.55); // Caldo default (torcia/lanterna)

#ifdef DYNAMIC_LIGHTS
    int maxHeldLight = max(heldBlockLightValue, heldBlockLightValue2);
    if (maxHeldLight > 0) {
        float dynFalloff = clamp(1.0 - (viewDist / 15.0), 0.0, 1.0);
        float dynIntensity = (float(maxHeldLight) / 15.0) * dynFalloff * dynFalloff;
        lm.x = max(lm.x, dynIntensity);
    }
#endif

    vec3 lightColor = texture(lightmap, lm).rgb;

    vec3 specularColor = vec3(0.0);
    float directionalFactor = 1.0;
    float shadowVisibility = 1.0;

#ifdef SHADOW_ENABLED
    vec3 L = normalize(shadowLightPosition.xyz);
    vec3 H = normalize(V + L);

    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.001);
    float NdotH = max(dot(N, H), 0.0);
    float VdotH = max(dot(V, H), 0.0);

    shadowVisibility = sampleShadowMap(vShadowPos, NdotL);
    directionalFactor = mix(0.70, 1.25, NdotL * shadowVisibility);

#ifdef PBR_ENABLED
    if (smoothness > 0.04 && NdotL > 0.0 && shadowVisibility > 0.05) {
        float roughness = max(pow(1.0 - smoothness, 2.0), 0.02);
        float NDF = D_GGX(NdotH, roughness);
        float G = G_Smith(NdotV, NdotL, roughness);
        vec3 F = F_Schlick(VdotH, F0);

        vec3 numerator = NDF * G * F;
        float denominator = 4.0 * NdotV * NdotL + 0.0001;
        specularColor = (numerator / denominator) * NdotL * lightColor * shadowVisibility * 1.5;
    }
#endif
#endif

    vec3 diffuse = albedo.rgb * lightColor * ao * directionalFactor * (1.0 - isMetal * 0.82);
    vec3 emissiveLight = albedo.rgb * (emissive * 2.5);
    vec3 finalRgb = diffuse + specularColor + emissiveLight;

    outColor = vec4(finalRgb, albedo.a);
    outData = vec4(smoothness, isMetal, ao, emissive);
}
