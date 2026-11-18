#version 330 compatibility

/*
 * Luminary Shaders - composite.vsh
 * Fullscreen quad pass per post-processing / shading composito
 */

out vec2 vTexCoord;

void main() {
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    gl_Position = ftransform();
}
