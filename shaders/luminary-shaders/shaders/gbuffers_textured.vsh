#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_textured.vsh
 */

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    gl_Position = ftransform();
}
