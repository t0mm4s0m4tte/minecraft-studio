#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_terrain.vsh
 * Passaggio vertici per terreno con calcolo TBN per normal mapping LabPBR 1.3
 */

attribute vec4 at_tangent;

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vNormal;
out vec3 vTangent;
out vec3 vBitangent;
out vec3 vViewPos;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    
    // Vettore normale e tangente nello spazio di vista
    vNormal = normalize(gl_NormalMatrix * gl_Normal);
    
    if (abs(at_tangent.w) > 0.001) {
        vTangent = normalize(gl_NormalMatrix * at_tangent.xyz);
        vBitangent = normalize(cross(vTangent, vNormal) * at_tangent.w);
    } else {
        // Fallback orizzontale se la tangente non è fornita
        vTangent = vec3(1.0, 0.0, 0.0);
        vBitangent = cross(vNormal, vTangent);
    }
    
    vec4 viewPos = gl_ModelViewMatrix * gl_Vertex;
    vViewPos = viewPos.xyz;
    
    gl_Position = gl_ProjectionMatrix * viewPos;
}
