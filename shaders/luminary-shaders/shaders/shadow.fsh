#version 330 compatibility

/*
 * Luminary Shaders - shadow.fsh
 * Scrittura mappa di profondità + shadowcolor0 per ombre colorate (vetro/acqua).
 */

uniform sampler2D gtexture;

in vec4 vTexCoord;
in vec4 vColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 outShadowColor;

void main() {
    vec4 tex = texture(gtexture, vTexCoord.xy) * vColor;
    if (tex.a < 0.1) discard;
    outShadowColor = tex;
}
