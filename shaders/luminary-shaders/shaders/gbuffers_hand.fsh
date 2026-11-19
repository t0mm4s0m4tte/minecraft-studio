#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_hand.fsh
 * LabPBR 1.3 Hand & Held Items Shading:
 * Decodifica normals (_n) e specular (_s) per i 605 item ed armi PBR 32x.
 * Specular highlight GGX/Schlick, luce dinamica portatile, Fresnel rim-light ed emissione.
 */

#include "/lib/settings.glsl"

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform sampler2D normals;
uniform sampler2D specular;

uniform vec3 shadowLightPosition;
uniform int heldBlockLightValue;
uniform int heldBlockLightValue2;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;
in vec3 vViewPos;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outData;

vec3 srgbToLinear(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

float D_GGX(float NdotH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (3.14159265 * denom * denom);
}

float G_SchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

float G_Smith(float NdotV, float NdotL, float roughness) {
    return G_SchlickGGX(NdotV, roughness) * G_SchlickGGX(NdotL, roughness);
}

vec3 F_Schlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

void main() {
    vec4 tex = texture(gtexture, vTexCoord) * vColor;
    if (tex.a < 0.1) discard;

    vec3 linearAlbedo = srgbToLinear(tex.rgb);
    vec3 geomN = normalize(vNormal);
    vec3 N = geomN;
    float ao = 1.0;

    float smoothness = 0.0;
    float isMetal = 0.0;
    vec3 F0 = vec3(0.04);
    float emissive = 0.0;

#ifdef PBR_ENABLED
    vec4 normalSample = texture(normals, vTexCoord);
    vec4 specSample = texture(specular, vTexCoord);

    if (normalSample.r > 0.004 || normalSample.g > 0.004) {
        ao = clamp(pow(normalSample.b, 1.35), 0.20, 1.0);
    }

    smoothness = specSample.r;
    float rawG = specSample.g * 255.0;
    int rawF0 = int(floor(rawG + 0.5));

    if (rawF0 < 230) {
        float f0_scalar = max(pow(specSample.g, 2.0), 0.02);
        F0 = vec3(f0_scalar);
        isMetal = 0.0;
    } else {
        isMetal = 1.0;
        if (rawF0 == 230)      F0 = vec3(0.56, 0.57, 0.58); // Ferro
        else if (rawF0 == 231) F0 = vec3(0.91, 0.92, 0.92); // Alluminio
        else if (rawF0 == 232) F0 = vec3(0.55, 0.56, 0.55); // Cromo
        else if (rawF0 == 233) F0 = vec3(0.95, 0.64, 0.54); // Rame
        else if (rawF0 == 234) F0 = vec3(1.00, 0.71, 0.29); // Oro
        else if (rawF0 == 235) F0 = vec3(0.68, 0.66, 0.63); // Platino
        else if (rawF0 == 236) F0 = vec3(0.66, 0.61, 0.53); // Nichel
        else if (rawF0 == 237) F0 = vec3(0.97, 0.96, 0.91); // Argento
        else                   F0 = linearAlbedo;            // Custom Metal
    }

    if (specSample.a > 0.004 && specSample.a < 0.996) {
        emissive = specSample.a;
    }
#endif

    vec2 lm = vLmCoord;
    vec3 dynamicTorchLight = vec3(0.0);
#ifdef DYNAMIC_LIGHTS
    int maxHeldLight = max(heldBlockLightValue, heldBlockLightValue2);
    if (maxHeldLight > 0) {
        vec3 handLightPos = vec3(0.20, 0.10, -0.20);
        vec3 toLight = handLightPos - vViewPos;
        float lightDist = length(toLight);
        vec3 L_dyn = toLight / max(lightDist, 0.001);
        float radius = float(maxHeldLight) * 0.95;
        float atten = clamp(1.0 - (lightDist / max(radius, 1.0)), 0.0, 1.0);
        atten = smoothstep(0.0, 1.0, atten);
        float NdotL_dyn = mix(0.50, 1.0, max(dot(N, L_dyn), 0.0));
        float dynIntensity = (float(maxHeldLight) / 15.0) * atten * atten;
        lm.x = max(lm.x, dynIntensity * 0.90);
        dynamicTorchLight = vec3(1.35, 0.85, 0.42) * dynIntensity * NdotL_dyn;
    }
#endif

    vec3 light = srgbToLinear(texture(lightmap, lm).rgb);
    vec3 totalAmbient = light + dynamicTorchLight;

    vec3 V = normalize(-vViewPos);
    vec3 L = normalize(shadowLightPosition);
    vec3 H = normalize(V + L);

    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.001);
    float NdotH = max(dot(N, H), 0.0);
    float VdotH = max(dot(V, H), 0.0);

    vec3 specularColor = vec3(0.0);
#ifdef PBR_ENABLED
    if (smoothness > 0.02 && NdotL > 0.0) {
        float roughness = max(pow(1.0 - smoothness, 2.0), 0.02);
        float NDF = D_GGX(NdotH, roughness);
        float G = G_Smith(NdotV, NdotL, roughness);
        vec3 F = F_Schlick(VdotH, F0);
        vec3 specContrib = (NDF * G * F) / (4.0 * NdotV * NdotL + 0.0001);
        specularColor = specContrib * NdotL * light * 1.85;
    }

    if (smoothness > 0.20 || isMetal > 0.5) {
        vec3 R = reflect(-V, N);
        float skyVis = clamp(lm.y * 1.15, 0.20, 1.0);
        vec3 envSky = mix(vec3(0.15, 0.18, 0.22), vec3(0.70, 0.85, 1.10), clamp(R.y * 0.5 + 0.5, 0.0, 1.0)) * skyVis;
        vec3 F_env = F_Schlick(NdotV, F0);
        vec3 metalTint = mix(vec3(1.0), linearAlbedo * 1.15, isMetal);
        specularColor += envSky * F_env * metalTint * pow(smoothness, 1.5) * mix(0.5, 1.0, isMetal) * ao;
    }
#endif

    float directionalShade = mix(0.75, 1.15, NdotL);
    float kD = 1.0 - isMetal * 0.75;
    vec3 diffuse = linearAlbedo * totalAmbient * directionalShade * ao * kD;

    // Rim-light Fresnel ed emissione per oggetti infusi/incantati/torce
    float fresnelRim = pow(1.0 - NdotV, 3.0) * (0.12 + 0.35 * emissive);
    vec3 rimColor = mix(vec3(0.4, 0.6, 0.9), linearAlbedo, isMetal) * fresnelRim * light;

    vec3 emissiveLight = linearAlbedo * (pow(emissive, 1.25) * 2.5 + fresnelRim * emissive * 1.5);
    vec3 finalLinearRgb = diffuse + specularColor + rimColor + emissiveLight;

    outColor = vec4(finalLinearRgb, tex.a);
    outNormal = vec4(N * 0.5 + 0.5, ao);
    outData = vec4(smoothness, isMetal, 0.0, emissive);
}
