#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.vsh
 * G-Buffer vertex stage con calcolo TBN Gram-Schmidt sicuro, bounds atlas,
 * vettori mondo e wind waving del fogliame (#ifdef FOLIAGE_WAVING).
 */

#include "/lib/settings.glsl"

attribute vec4 at_tangent;
attribute vec4 mc_midTexCoord;
attribute vec4 mc_Entity;

uniform mat4 gbufferModelView;
uniform mat4 gbufferModelViewInverse;
uniform mat4 shadowModelView;
uniform mat4 shadowProjection;
uniform vec3 cameraPosition;
uniform float frameTimeCounter;

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vNormal;
out vec3 vTangent;
out vec3 vBitangent;
out vec3 vViewPos;
out vec3 vWorldNormal;
out vec3 vWorldPos;
out vec4 vShadowPos;
flat out vec4 vAtlasBounds;
flat out int vBlockId;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;

    vec2 midUV = mc_midTexCoord.xy;
    vec2 halfExtent = abs(vTexCoord - midUV);
    vAtlasBounds = vec4(midUV - halfExtent, halfExtent * 2.0);

    vNormal = normalize(gl_NormalMatrix * gl_Normal);
    vWorldNormal = normalize(gl_Normal);

    // Costruzione TBN Gram-Schmidt sicura contro NaN su normali asse X
    if (abs(at_tangent.w) > 0.001) {
        vec3 t = normalize(gl_NormalMatrix * at_tangent.xyz);
        t = normalize(t - dot(t, vNormal) * vNormal);
        vTangent = t;
        vBitangent = normalize(cross(vNormal, vTangent) * at_tangent.w);
    } else {
        vec3 c1 = cross(vNormal, vec3(0.0, 0.0, 1.0));
        vec3 c2 = cross(vNormal, vec3(0.0, 1.0, 0.0));
        vTangent = length(c1) > length(c2) ? normalize(c1) : normalize(c2);
        vBitangent = normalize(cross(vNormal, vTangent));
    }

    vec4 viewPos = gl_ModelViewMatrix * gl_Vertex;
    vec4 worldPos = gbufferModelViewInverse * viewPos;

    int blockId = int(mc_Entity.x + 0.5);
    vBlockId = blockId;

#ifdef FOLIAGE_WAVING
    // Micro-waving per foglie, erba e vegetazione organica (ID 10018) in Absolute World-Space
    if (blockId == 10018) {
        vec3 worldAbs = worldPos.xyz + cameraPosition;
        float waveSpeed = frameTimeCounter * 2.2;
        float wave = sin(waveSpeed + worldAbs.x * 1.5 + worldAbs.z * 1.2) * 0.035
                   + cos(waveSpeed * 1.4 + worldAbs.y * 2.0) * 0.02;
        worldPos.x += wave * 0.75;
        worldPos.z += wave * 0.50;
        viewPos = gbufferModelView * worldPos;
    }
#endif

    vViewPos = viewPos.xyz;
    vWorldPos = worldPos.xyz;

    vec4 shadowView = shadowModelView * worldPos;
    vShadowPos = shadowProjection * shadowView;

    gl_Position = gl_ProjectionMatrix * viewPos;
}
