#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.vsh
 * Passaggio vertici per terreno con calcolo TBN e bounds atlas per POM LabPBR 1.3
 */

attribute vec4 at_tangent;
attribute vec4 mc_midTexCoord;

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vNormal;
out vec3 vTangent;
out vec3 vBitangent;
out vec3 vViewPos;
flat out vec4 vAtlasBounds; // xy = minUV, zw = sizeUV

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;

    // Calcolo bounds sprite nell'atlas per evitare bleeding durante POM
    vec2 midUV = mc_midTexCoord.xy;
    vec2 halfExtent = abs(vTexCoord - midUV);
    vAtlasBounds = vec4(midUV - halfExtent, halfExtent * 2.0);

    // Vettore normale e tangente nello spazio di vista
    vNormal = normalize(gl_NormalMatrix * gl_Normal);

    if (abs(at_tangent.w) > 0.001) {
        vTangent = normalize(gl_NormalMatrix * at_tangent.xyz);
        vBitangent = normalize(cross(vNormal, vTangent) * at_tangent.w);
    } else {
        vTangent = vec3(1.0, 0.0, 0.0);
        vBitangent = cross(vNormal, vTangent);
    }

    vec4 viewPos = gl_ModelViewMatrix * gl_Vertex;
    vViewPos = viewPos.xyz;

    gl_Position = gl_ProjectionMatrix * viewPos;
}
