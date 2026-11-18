#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_textured.fsh
 */

uniform sampler2D gtexture;
uniform sampler2D lightmap;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData;

void main() {
    vec4 tex = texture(gtexture, vTexCoord) * vColor;
    if (tex.a < 0.1) discard;
    vec3 light = texture(lightmap, vLmCoord).rgb;
    outColor = vec4(tex.rgb * light, tex.a);
    outData = vec4(0.0);
}
