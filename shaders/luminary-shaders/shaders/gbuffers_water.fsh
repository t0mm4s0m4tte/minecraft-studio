#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_water.fsh
 * Acqua con increspature procedurali, Fresnel dielettrico e riflesso cielo.
 */

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform float frameTimeCounter;
uniform vec3 upPosition;

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
    
    // Onde procedurali animate nel tangent space
    float t = frameTimeCounter * 2.2;
    float wave1 = sin(vTexCoord.x * 24.0 + t) * cos(vTexCoord.y * 24.0 + t * 0.8);
    float wave2 = sin((vTexCoord.x + vTexCoord.y) * 36.0 - t * 1.2) * 0.5;
    vec3 waveNormal = normalize(vNormal + vec3(wave1 * 0.08, wave2 * 0.08, 0.0));
    
    // Fresnel dielettrico
    vec3 V = normalize(-vViewPos);
    float NdotV = max(dot(waveNormal, V), 0.0);
    float fresnel = 0.03 + 0.97 * pow(clamp(1.0 - NdotV, 0.0, 1.0), 5.0);
    
    // Riflesso cielo azzurro
    vec3 skyReflect = mix(vec3(0.55, 0.72, 0.95), vec3(0.85, 0.92, 1.0), fresnel);
    
    vec3 waterBase = mix(vec3(0.12, 0.38, 0.58), tex.rgb, 0.45);
    vec3 col = waterBase * light + skyReflect * (fresnel * 0.65);
    
    outColor = vec4(col, clamp(tex.a * 0.82, 0.55, 0.9));
    outData = vec4(0.96, 0.0, 1.0, 0.0); // Smoothness 0.96 per riflessi speculari
}
