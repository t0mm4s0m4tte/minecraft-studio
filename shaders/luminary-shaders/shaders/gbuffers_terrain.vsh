#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.vsh
 * Passaggio vertici per terreno con calcolo TBN, proiezione shadow map e bounds atlas.
 */

attribute vec4 at_tangent;
attribute vec4 mc_midTexCoord;

uniform mat4 shadowModelView;
uniform mat4 shadowProjection;

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vNormal;
out vec3 vTangent;
out vec3 vBitangent;
out vec3 vViewPos;
out vec4 vShadowPos;
flat out vec4 vAtlasBounds;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;

    vec2 midUV = mc_midTexCoord.xy;
    vec2 halfExtent = abs(vTexCoord - midUV);
    vAtlasBounds = vec4(midUV - halfExtent, halfExtent * 2.0);

    vNormal = normalize(gl_NormalMatrix * gl_Normal);

    if (abs(at_tangent.w) > 0.001) {
        vTangent = normalize(gl_NormalMatrix * at_tangent.xyz);
        vBitangent = normalize(cross(vTangent, vNormal) * at_tangent.w);
    } else {
        vTangent = vec3(1.0, 0.0, 0.0);
        vBitangent = cross(vNormal, vTangent);
    }

    vec4 viewPos = gl_ModelViewMatrix * gl_Vertex;
    vViewPos = viewPos.xyz;

    // Coordinate per campionamento ombra diretta
    vec4 shadowView = shadowModelView * (gl_ModelViewMatrixInverse * viewPos);
    vShadowPos = shadowProjection * shadowView;

    gl_Position = gl_ProjectionMatrix * viewPos;
}
