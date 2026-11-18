#version 330 compatibility

/*
 * Luminary Shaders - final.fsh
 * Tonemapping naturale ad alta vivacità, correzione gamma sRGB e dithering anti-banding.
 * Evita lo sbiancamento di erba/foglie e mantiene i colori vanilla ricchi e caldi.
 */

uniform sampler2D colortex0;
uniform float viewWidth;
uniform float viewHeight;

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 finalColor;

// Curva filmica Reinhard-Jodie morbida: preserva la saturazione naturale e le tinte del fogliame
vec3 FilmToneMap(vec3 color) {
    float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
    vec3 tc = color / (color + vec3(1.0));
    return mix(color / (1.0 + luma), tc, tc);
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
    vec3 color = texture(colortex0, vTexCoord).rgb;
    
    // 1. Tonemapping calibrato morbido (non brucia i verdi dell'erba)
    color = FilmToneMap(color * 1.08);
    
    // 2. Leggero boost di contrasto e saturazione naturale
    float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
    color = mix(vec3(luma), color, 1.12);
    
    // 3. Dithering 8-bit anti-banding
    vec2 screenCoord = vTexCoord * vec2(max(viewWidth, 1920.0), max(viewHeight, 1080.0));
    float dither = bayer4x4(screenCoord) / 255.0;
    color += vec3(dither);
    
    finalColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
