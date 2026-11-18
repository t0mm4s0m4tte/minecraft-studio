#version 330 compatibility

/*
 * Luminary Shaders - shadow.vsh
 * Shadow map pass con distorsione non-lineare (0.85) simmetrica
 * per triplicare la risoluzione effettiva vicino al giocatore senza slittamenti.
 */

out vec4 vTexCoord;
out vec4 vColor;

vec3 distortShadowClipPos(vec3 clipPos) {
    float dist = length(clipPos.xy);
    float distortFactor = dist * 0.85 + 0.15;
    clipPos.xy /= distortFactor;
    clipPos.z *= 0.5;
    return clipPos;
}

void main() {
    vColor = gl_Color;
    vTexCoord = gl_TextureMatrix[0] * gl_MultiTexCoord0;

    vec4 clipPos = ftransform();
    clipPos.xyz = distortShadowClipPos(clipPos.xyz);
    gl_Position = clipPos;
}
