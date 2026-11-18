#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_water.fsh
 */

uniform sampler2D gtexture;
uniform sampler2D lightmap;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;
in vec3 vViewPos;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData;

void main() {
    vec4 tex = texture(gtexture, vTexCoord) * vColor;
    vec3 light = texture(lightmap, vLmCoord).rgb;
    
    // Fresnel dielettrico per acqua
    vec3 V = normalize(-vViewPos);
    vec3 N = normalize(vNormal);
    float NdotV = max(dot(N, V), 0.0);
    float fresnel = 0.02 + 0.98 * pow(clamp(1.0 - NdotV, 0.0, 1.0), 5.0);
    
    vec3 col = tex.rgb * light + fresnel * 0.15;
    outColor = vec4(col, tex.a);
    // R=Smoothness (0.95), G=Dielectric (0.0), B=AO (1.0), A=Emissive (0.0)
    outData = vec4(0.95, 0.0, 1.0, 0.0);
}
