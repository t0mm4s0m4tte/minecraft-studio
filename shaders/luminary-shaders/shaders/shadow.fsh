#version 330 compatibility

/*
 * Luminary Shaders - shadow.fsh
 * Scrittura mappa di profondità con scarto trasparenze per ombre fogliame/vetro.
 */

uniform sampler2D gtexture;

in vec4 vTexCoord;
in vec4 vColor;

void main() {
    vec4 tex = texture(gtexture, vTexCoord.xy) * vColor;
    if (tex.a < 0.1) discard;
}
