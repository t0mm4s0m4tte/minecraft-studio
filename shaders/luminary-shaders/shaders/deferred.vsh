#version 330 compatibility

/*
 * Luminary Shaders - deferred.vsh
 * Fullscreen quad vertex pass per deferred stage
 */

out vec2 vTexCoord;

void main() {
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    gl_Position = ftransform();
}
