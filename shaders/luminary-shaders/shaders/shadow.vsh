#version 330 compatibility

/*
 * Luminary Shaders - shadow.vsh
 * Shadow map pass con distorsione non-lineare (0.85) simmetrica
 * per triplicare la risoluzione effettiva vicino al giocatore senza slittamenti,
 * e foliage waving coerente (#ifdef FOLIAGE_WAVING).
 */

#include "/lib/settings.glsl"

attribute vec4 mc_Entity;
uniform float frameTimeCounter;
uniform vec3 cameraPosition;
uniform mat4 shadowModelView;
uniform mat4 shadowModelViewInverse;

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

    vec4 shadowViewPos = gl_ModelViewMatrix * gl_Vertex;

#ifdef FOLIAGE_WAVING
    int blockId = int(mc_Entity.x + 0.5);
    if (blockId == 10018) {
        vec4 worldPos = shadowModelViewInverse * shadowViewPos;
        vec3 worldAbs = worldPos.xyz + cameraPosition;
        float waveSpeed = frameTimeCounter * 2.2;
        float wave = sin(waveSpeed + worldAbs.x * 1.5 + worldAbs.z * 1.2) * 0.035
                   + cos(waveSpeed * 1.4 + worldAbs.y * 2.0) * 0.02;
        worldPos.x += wave * 0.75;
        worldPos.z += wave * 0.50;
        shadowViewPos = shadowModelView * worldPos;
    }
#endif

    vec4 clipPos = gl_ProjectionMatrix * shadowViewPos;
    clipPos.xyz = distortShadowClipPos(clipPos.xyz);
    gl_Position = clipPos;
}
