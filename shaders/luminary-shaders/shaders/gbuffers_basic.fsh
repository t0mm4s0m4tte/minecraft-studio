#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_basic.fsh
 */

in vec4 vColor;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData;

void main() {
    outColor = vColor;
    outData = vec4(0.0);
}
