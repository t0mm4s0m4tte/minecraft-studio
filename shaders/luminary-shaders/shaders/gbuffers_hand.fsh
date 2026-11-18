#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_hand.fsh
 */

uniform sampler2D gtexture;
uniform sampler2D lightmap;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outData;

vec3 srgbToLinear(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

void main() {
    vec4 tex = texture(gtexture, vTexCoord) * vColor;
    if (tex.a < 0.1) discard;
    vec3 light = srgbToLinear(texture(lightmap, vLmCoord).rgb);
    outColor = vec4(srgbToLinear(tex.rgb) * light, tex.a);
    outNormal = vec4(normalize(vNormal) * 0.5 + 0.5, 1.0);
    outData = vec4(0.0);
}
