#version 330 compatibility

/*
 * Luminary Shaders - composite.fsh
 * Passaggio composito: bloom leggero su pixel emissivi (colortex1.a > 0),
 * micro-SSAO opzionale su profilo Cinematic (AO_QUALITY == 2) ed esaltazione metalli.
 */

#include "/lib/settings.glsl"

uniform sampler2D colortex0; // Shaded Albedo
uniform sampler2D colortex1; // Data buffer (Smoothness, Metalness, AO, Emissive)
uniform sampler2D depthtex0; // Depth buffer
uniform float viewWidth;
uniform float viewHeight;

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outColor;

void main() {
    vec4 baseColor = texture(colortex0, vTexCoord);
    vec4 pbrData = texture(colortex1, vTexCoord);

    float smoothness = pbrData.r;
    float isMetal = pbrData.g;
    float emissive = pbrData.a;

    vec3 color = baseColor.rgb;
    vec2 px = vec2(1.0 / max(viewWidth, 1280.0), 1.0 / max(viewHeight, 720.0));

#if AO_QUALITY >= 2
    // Micro-cavity SSAO a 4 tap su profondità per profilo Cinematic
    float centerDepth = texture(depthtex0, vTexCoord).r;
    if (centerDepth < 0.9999) {
        vec2 offset = px * 2.5;
        float d1 = texture(depthtex0, vTexCoord + vec2(offset.x, 0.0)).r;
        float d2 = texture(depthtex0, vTexCoord - vec2(offset.x, 0.0)).r;
        float d3 = texture(depthtex0, vTexCoord + vec2(0.0, offset.y)).r;
        float d4 = texture(depthtex0, vTexCoord - vec2(0.0, offset.y)).r;
        float avgDepth = (d1 + d2 + d3 + d4) * 0.25;
        float occlusion = clamp((centerDepth - avgDepth) * 900.0, 0.0, 0.28);
        color *= (1.0 - occlusion);
    }
#endif

    // Bloom selettivo sui pixel emissivi LabPBR 1.3 (copper_bulb_lit, torch, lantern)
    if (emissive > 0.05) {
        vec2 stepCoord = px * 3.0;
        vec3 bloomSample = (
            texture(colortex0, vTexCoord + vec2(stepCoord.x, 0.0)).rgb +
            texture(colortex0, vTexCoord - vec2(stepCoord.x, 0.0)).rgb +
            texture(colortex0, vTexCoord + vec2(0.0, stepCoord.y)).rgb +
            texture(colortex0, vTexCoord - vec2(0.0, stepCoord.y)).rgb
        ) * 0.25;

        color += bloomSample * (emissive * 0.6);
    }

#ifdef PBR_ENABLED
    // Accentuazione lucentezza e fresnel dei metalli
    if (isMetal > 0.5) {
        color *= (1.0 + smoothness * 0.2);
    }
#endif

    outColor = vec4(color, baseColor.a);
}
