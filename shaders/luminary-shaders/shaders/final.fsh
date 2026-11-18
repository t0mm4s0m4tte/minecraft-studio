#version 330 compatibility

/*
 * Luminary Shaders - final.fsh
 * Passaggio a schermo: tonemapping ACES calibrato, correzione gamma e dithering anti-banding
 */

uniform sampler2D colortex0;
uniform float viewWidth;
uniform float viewHeight;

in vec2 vTexCoord;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 finalColor;

// Tonemapping ACES Film Curve rapido
vec3 ACESFilm(vec3 x) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// Dithering triangolare anti-banding 8-bit
float bayer4x4(vec2 coord) {
    int x = int(mod(coord.x, 4.0));
    int y = int(mod(coord.y, 4.0));
    int index = x + y * 4;
    
    // Matrice di Bayer 4x4
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
    
    // 1. Tonemapping ACES
    color = ACESFilm(color);
    
    // 2. Correzione gamma da linear a sRGB (pow 1/2.2)
    color = pow(color, vec3(1.0 / 2.2));
    
    // 3. Dithering 8-bit per eliminare gradient banding
    vec2 screenCoord = vTexCoord * vec2(max(viewWidth, 1920.0), max(viewHeight, 1080.0));
    float dither = bayer4x4(screenCoord) / 255.0;
    color += vec3(dither);
    
    finalColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
