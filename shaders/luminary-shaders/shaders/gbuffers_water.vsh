#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_water.vsh
 * Passaggio vertici per acqua trasparente con calcolo coordinate World-Space.
 */

uniform mat4 gbufferModelViewInverse;

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vNormal;
out vec3 vViewPos;
out vec3 vWorldPos;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    vNormal = normalize(gl_NormalMatrix * gl_Normal);

    vec4 viewPos = gl_ModelViewMatrix * gl_Vertex;
    vViewPos = viewPos.xyz;

    // Coordinate in spazio mondo per onde analitiche continue
    vec4 worldPos = gbufferModelViewInverse * viewPos;
    vWorldPos = worldPos.xyz;

    gl_Position = gl_ProjectionMatrix * viewPos;
}
