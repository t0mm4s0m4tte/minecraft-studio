#version 330 compatibility

/*
 * Luminary Shaders - composite.fsh
 * Compositing pass:
 * 1. Screen-Space Reflections (SSR) e Fresnel ambientale sull'acqua e sui metalli lucidi (smoothness > 0.72)
 * 2. Bloom gaussiano a 9-tap multi-scala su sorgenti emissive e riflessi speculari HDR
 */

#include "/lib/settings.glsl"

uniform sampler2D colortex0; // HDR Linear Scene Color
uniform sampler2D colortex1; // View-Space Normal + AO
uniform sampler2D colortex2; // LabPBR Data (R=Smoothness, G=Metal, B=Porosity/SSS, A=Emissive)
uniform sampler2D depthtex0;
uniform float viewWidth;
uniform float viewHeight;

in vec2 vTexCoord;

/* RENDERTARGETS: 0,3 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outBloom;

void main() {
    vec4 baseColor = texture(colortex0, vTexCoord);
    vec4 pbrData = texture(colortex2, vTexCoord);

    float smoothness = pbrData.r;
    float isMetal = pbrData.g;
    float emissive = pbrData.a;

    vec3 color = baseColor.rgb;
    vec2 px = vec2(1.0 / max(viewWidth, 1280.0), 1.0 / max(viewHeight, 720.0));

    // Isolamento Bloom Gaussiano 9-tap su pixel emissivi e highlight speculari HDR (> 1.15)
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
