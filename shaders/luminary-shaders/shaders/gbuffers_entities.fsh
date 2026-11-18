#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_entities.fsh
 */

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform vec4 entityColor;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vNormal;
in vec3 vViewPos;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData;

void main() {
    vec4 tex = texture(gtexture, vTexCoord) * vColor;
    if (tex.a < 0.1) discard;

    // Flash del danno entità
    tex.rgb = mix(tex.rgb, entityColor.rgb, entityColor.a);

    vec3 light = texture(lightmap, vLmCoord).rgb;
    outColor = vec4(tex.rgb * light, tex.a);
    outData = vec4(0.0);
}
