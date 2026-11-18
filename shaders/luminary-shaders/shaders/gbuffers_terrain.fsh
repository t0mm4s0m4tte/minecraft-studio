#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.fsh
 * Standard LabPBR 1.3 + Dynamic Light Support
 * Profili gestiti via macro (#ifdef PBR_ENABLED, DYNAMIC_LIGHTS, POM_ENABLED, AO_QUALITY)
 */

uniform sampler2D gtexture;    // Albedo
uniform sampler2D normals;     // Normal map (_n)
uniform sampler2D specular;    // Specular map (_s)
uniform sampler2D lightmap;    // Vanilla Lightmap

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

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData; // R=Smoothness, G=Metalness, B=AO, A=Emissive

#define PBR_ENABLED
#define DYNAMIC_LIGHTS

// Microfacet GGX Distribution (Normal Distribution Function)
float D_GGX(float NdotH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (3.14159265 * denom * denom);
}

// Schlick-GGX Geometric Attenuation
float G_SchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

float G_Smith(float NdotV, float NdotL, float roughness) {
    return G_SchlickGGX(NdotV, roughness) * G_SchlickGGX(NdotL, roughness);
}

// Fresnel-Schlick Approximation
vec3 F_Schlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

void main() {
    vec2 coord = vTexCoord;
    vec4 albedo = texture(gtexture, coord) * vColor;
    if (albedo.a < 0.1) {
        discard;
    }
    
    vec3 N = normalize(vNormal);
    float ao = 1.0;
    float smoothness = 0.0;
    float isMetal = 0.0;
    float emissive = 0.0;
    vec3 F0 = vec3(0.04); // Base dielectric reflectance

#ifdef PBR_ENABLED
    vec4 normalSample = texture(normals, coord);
    vec4 specSample = texture(specular, coord);

    // LabPBR 1.3: _n.rg = tangent normal
    vec2 normalXY = normalSample.xy * 2.0 - 1.0;
    float normalZ = sqrt(max(0.0, 1.0 - dot(normalXY, normalXY)));
    vec3 tNormal = normalize(vec3(normalXY, normalZ));

    // Costruzione matrice TBN
    mat3 tbn = mat3(normalize(vTangent), normalize(vBitangent), N);
    N = normalize(tbn * tNormal);

    ao = normalSample.b; // LabPBR: B = Ambient Occlusion

    smoothness = specSample.r;
    float f0_metal = specSample.g;
    
    // LabPBR 1.3: G >= 230/255 -> Metallic; < 230 -> Dielectric F0 (0.00 .. 0.04)
    if (f0_metal >= (229.5 / 255.0)) {
        isMetal = 1.0;
        F0 = albedo.rgb; // Metalli usano il colore albedo come F0
    } else {
        isMetal = 0.0;
        F0 = vec3(f0_metal * (255.0 / 229.0) * 0.04);
        F0 = max(F0, vec3(0.04));
    }

    // LabPBR 1.3: Alpha emissivo 0..254 (255 riservato)
    float rawEmissive = specSample.a * 255.0;
    if (rawEmissive > 0.5 && rawEmissive < 254.5) {
        emissive = rawEmissive / 254.0;
    }
#endif

    // Lightmap base vanilla
    vec2 lm = vLmCoord;

#ifdef DYNAMIC_LIGHTS
    // Illuminazione dinamica integrata per player/item tenuto in mano
    int maxHeldLight = max(heldBlockLightValue, heldBlockLightValue2);
    if (maxHeldLight > 0) {
        float distToPlayer = length(vViewPos);
        float dynFalloff = clamp(1.0 - (distToPlayer / 15.0), 0.0, 1.0);
        float dynIntensity = (float(maxHeldLight) / 15.0) * dynFalloff * dynFalloff;
        lm.x = max(lm.x, dynIntensity);
    }
#endif

    vec3 lightColor = texture(lightmap, lm).rgb;

    // Vettore vista e luce solare nello spazio di vista
    vec3 V = normalize(-vViewPos);
    vec3 L = normalize(shadowLightPosition.xyz);
    vec3 H = normalize(V + L);

    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.001);
    float NdotH = max(dot(N, H), 0.0);
    float VdotH = max(dot(V, H), 0.0);

    // Specular GGX / Cook-Torrance leggero (Target <= 3.8ms)
    vec3 specularColor = vec3(0.0);
#ifdef PBR_ENABLED
    if (smoothness > 0.05 && NdotL > 0.0) {
        float roughness = max(pow(1.0 - smoothness, 2.0), 0.02);
        float NDF = D_GGX(NdotH, roughness);
        float G = G_Smith(NdotV, NdotL, roughness);
        vec3 F = F_Schlick(VdotH, F0);

        vec3 numerator = NDF * G * F;
        float denominator = 4.0 * NdotV * NdotL + 0.0001;
        specularColor = (numerator / denominator) * NdotL * lightColor;
    }
#endif

    // Luce diffusa con AO
    vec3 diffuse = albedo.rgb * lightColor * ao * (1.0 - isMetal);

    // Contributo emissivo puro
    vec3 emissiveLight = albedo.rgb * (emissive * 2.2);

    vec3 finalRgb = diffuse + specularColor + emissiveLight;

    outColor = vec4(finalRgb, albedo.a);
    outData = vec4(smoothness, isMetal, ao, emissive);
}
