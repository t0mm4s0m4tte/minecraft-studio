#version 330 compatibility

/*
 * Luminary Shaders - composite.fsh
 * Passaggio composito: bloom leggero su pixel emissivi (colortex1.a > 0)
 * ed esaltazione micro-specular metalli nel rispetto del budget GPU <= 3.8 ms
 */

uniform sampler2D colortex0; // Shaded Albedo
uniform sampler2D colortex1; // Data buffer (Smoothness, Metalness, AO, Emissive)
uniform sampler2D depthtex0; // Depth buffer
uniform vec2 texelSize;

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
    
    // Bloom selettivo sui pixel emissivi LabPBR 1.3 (copper_bulb_lit, torch, lantern)
    // Campionamento cruciforme a 4-tap a costo computazionale trascurabile
    if (emissive > 0.05) {
        vec2 stepCoord = vec2(0.002, 0.002);
        vec3 bloomSample = (
            texture(colortex0, vTexCoord + vec2(stepCoord.x, 0.0)).rgb +
            texture(colortex0, vTexCoord - vec2(stepCoord.x, 0.0)).rgb +
            texture(colortex0, vTexCoord + vec2(0.0, stepCoord.y)).rgb +
            texture(colortex0, vTexCoord - vec2(0.0, stepCoord.y)).rgb
        ) * 0.25;
        
        color += bloomSample * (emissive * 0.6);
    }
    
    // Accentuazione lucentezza e fresnel dei metalli
    if (isMetal > 0.5) {
        color *= (1.0 + smoothness * 0.2);
    }
    
    outColor = vec4(color, baseColor.a);
}
