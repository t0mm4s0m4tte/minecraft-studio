#version 330 compatibility

/*
 * Luminary Shaders - final.fsh
 * Khronos PBR Neutral Tone Mapping, bloom upsampling,
 * Auto-Exposure dinamica, Bokeh Depth of Field, Color Grading LUT,
 * Aberrazione Cromatica e dithering triangolare anti-banding 8-bit.
 */

#include "/lib/settings.glsl"

uniform sampler2D colortex0; // HDR Linear Scene Color
uniform sampler2D colortex3; // Bloom highlights (RGB) + Scene Average Luma (A)
uniform sampler2D depthtex0; // Depth buffer completo
uniform float viewWidth;
uniform float viewHeight;
uniform float near;
uniform float far;

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 finalColor;

float linearizeDepth(float d) {
    float z_n = 2.0 * d - 1.0;
    return (2.0 * near * far) / max(far + near - z_n * (far - near), 0.0001);
}

// Khronos PBR Neutral Tone Mapping (zero-clipping, preserva tinte e saturazione)
vec3 PBRNeutralToneMapping(vec3 color) {
    const float startCompression = 0.8 - 0.04;
    const float desaturation = 0.15;

    float x = min(color.r, min(color.g, color.b));
    float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
    color -= offset;

    float peak = max(color.r, max(color.g, color.b));
    if (peak < startCompression) return color;

    const float d = 1.0 - startCompression;
    float newPeak = 1.0 - d * d / (peak + d - startCompression);
    color *= newPeak / peak;

    float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);
    return mix(color, newPeak * vec3(1.0), g);
}

// Conversione finale Linear -> sRGB
vec3 linearToSrgb(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(1.0 / 2.2));
}

// Dithering triangolare anti-banding 8-bit
float bayer4x4(vec2 coord) {
    int x = int(mod(coord.x, 4.0));
    int y = int(mod(coord.y, 4.0));
    int index = x + y * 4;
    
    const float ditherTable[16] = float[16](
         0.0 / 16.0,  8.0 / 16.0,  2.0 / 16.0, 10.0 / 16.0,
        12.0 / 16.0,  4.0 / 16.0, 14.0 / 16.0,  6.0 / 16.0,
          3.0 / 16.0, 11.0 / 16.0,  1.0 / 16.0,  9.0 / 16.0,
        15.0 / 16.0,  7.0 / 16.0, 13.0 / 16.0,  5.0 / 16.0
    );
    return ditherTable[index] - 0.5;
}

void main() {
    vec2 uv = vTexCoord;
    vec2 px = vec2(1.0 / max(viewWidth, 1920.0), 1.0 / max(viewHeight, 1080.0));

    // 1. Aberrazione cromatica radiale sui bordi dello schermo
    vec3 sceneHdr = vec3(0.0);
#ifdef CHROMATIC_ABERRATION
    vec2 toCenter = uv - 0.5;
    float rDist2 = dot(toCenter, toCenter);
    vec2 caOffset = toCenter * (0.0018 * rDist2 * 4.0);
    sceneHdr.r = texture(colortex0, uv - caOffset).r;
    sceneHdr.g = texture(colortex0, uv).g;
    sceneHdr.b = texture(colortex0, uv + caOffset).b;
#else
    sceneHdr = texture(colortex0, uv).rgb;
#endif

    // 2. Cinematic Bokeh Depth of Field (anello esagonale a 6 tap)
#ifdef DOF_ENABLED
    float centerDepth = linearizeDepth(texture(depthtex0, vec2(0.5)).r);
    float pixelDepth = linearizeDepth(texture(depthtex0, uv).r);
    if (pixelDepth < far * 0.99) {
        float coc = clamp(abs(pixelDepth - centerDepth) / max(centerDepth * 1.6, 4.0), 0.0, 1.0) * 3.5;
        if (coc > 0.08) {
            vec2 dofRadius = coc * px;
            const vec2 hexTaps[6] = vec2[6](
                vec2( 1.0,  0.0),
                vec2( 0.5,  0.866),
                vec2(-0.5,  0.866),
                vec2(-1.0,  0.0),
                vec2(-0.5, -0.866),
                vec2( 0.5, -0.866)
            );
            vec3 dofAccum = sceneHdr * 0.40;
            for (int i = 0; i < 6; i++) {
                dofAccum += texture(colortex0, uv + hexTaps[i] * dofRadius).rgb * 0.10;
            }
            sceneHdr = dofAccum;
        }
    }
#endif

    // 3. Bloom highlights
    vec4 bloomSample = texture(colortex3, uv);
    vec3 bloomHdr = bloomSample.rgb;
    vec3 hdrColor = sceneHdr + bloomHdr * 0.25;

    // 4. Dynamic Auto-Exposure & Eye Adaptation
#ifdef AUTO_EXPOSURE
    float sceneLuma = max(texture(colortex3, vec2(0.5)).a, 0.05);
    float exposureGain = clamp(0.42 / pow(sceneLuma, 0.35), 0.78, 1.45);
    hdrColor *= exposureGain;
#endif

    // 5. Color Grading LUT Presets
#if TONEMAP_PRESET == 1
    // Warm Golden Hour: riscaldamento ambrato + contrasto morbido
    hdrColor *= vec3(1.08, 0.99, 0.88);
    hdrColor = pow(max(hdrColor, vec3(0.0)), vec3(1.04));
#elif TONEMAP_PRESET == 2
    // Nordic Cold: toni freddi artici + micro-desaturazione
    hdrColor *= vec3(0.91, 0.98, 1.09);
    float gray = dot(hdrColor, vec3(0.2126, 0.7152, 0.0722));
    hdrColor = mix(hdrColor, vec3(gray), 0.08);
#endif

    // 6. Khronos PBR Neutral Tone Mapping (HDR -> LDR)
    vec3 tonemapped = PBRNeutralToneMapping(hdrColor);

    // 7. Conversione Linear -> sRGB
    vec3 srgbColor = linearToSrgb(tonemapped);

    // 8. Dithering 8-bit anti-banding
    vec2 screenCoord = uv * vec2(max(viewWidth, 1920.0), max(viewHeight, 1080.0));
    float dither = bayer4x4(screenCoord) / 255.0;
    srgbColor += vec3(dither);

    finalColor = vec4(clamp(srgbColor, 0.0, 1.0), 1.0);
}

