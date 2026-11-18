#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_basic.fsh
 */

in vec4 vColor;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outData;

vec3 srgbToLinear(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

void main() {
    outColor = vec4(srgbToLinear(vColor.rgb), vColor.a);
    outNormal = vec4(0.5, 0.5, 1.0, 1.0);
    outData = vec4(0.0);
}
