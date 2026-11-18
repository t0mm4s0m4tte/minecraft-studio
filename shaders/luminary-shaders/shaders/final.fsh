#version 330 compatibility

/*
 * Luminary Shaders - final.fsh
 * Khronos PBR Neutral / AgX Tone Mapping, bloom upsampling,
 * dithering triangolare anti-banding e conversione finale Linear -> sRGB.
 */

uniform sampler2D colortex0; // HDR Linear Scene Color
uniform sampler2D colortex3; // Bloom highlights
uniform float viewWidth;
uniform float viewHeight;

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 finalColor;

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
    vec3 sceneHdr = texture(colortex0, vTexCoord).rgb;
    vec3 bloomHdr = texture(colortex3, vTexCoord).rgb;
    
    // 1. Accrescimento bloom con curva morbida
    vec3 hdrColor = sceneHdr + bloomHdr * 0.25;
    
    // 2. Khronos PBR Neutral Tone Mapping (HDR -> LDR)
    vec3 tonemapped = PBRNeutralToneMapping(hdrColor);
    
    // 3. Conversione Linear -> sRGB
    vec3 srgbColor = linearToSrgb(tonemapped);
    
    // 4. Dithering 8-bit anti-banding
    vec2 screenCoord = vTexCoord * vec2(max(viewWidth, 1920.0), max(viewHeight, 1080.0));
    float dither = bayer4x4(screenCoord) / 255.0;
    srgbColor += vec3(dither);
    
    finalColor = vec4(clamp(srgbColor, 0.0, 1.0), 1.0);
}
