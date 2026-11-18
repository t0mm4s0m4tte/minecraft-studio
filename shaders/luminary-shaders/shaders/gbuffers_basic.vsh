#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_basic.vsh
 */

out vec4 vColor;

void main() {
    vColor = gl_Color;
    gl_Position = ftransform();
}
