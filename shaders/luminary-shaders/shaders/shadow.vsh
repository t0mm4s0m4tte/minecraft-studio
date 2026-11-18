#version 330 compatibility

/*
 * Luminary Shaders - shadow.vsh
 * Generazione coordinate d'ombra per luce solare/lunare diretta.
 */

out vec4 vTexCoord;
out vec4 vColor;

void main() {
    vColor = gl_Color;
    vTexCoord = gl_TextureMatrix[0] * gl_MultiTexCoord0;
    gl_Position = ftransform();
}
