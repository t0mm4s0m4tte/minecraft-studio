#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_weather.vsh
 * Stage vertex per pioggia e neve con calcolo della posizione in view-space.
 */

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vViewPos;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;

    vec4 viewPos = gl_ModelViewMatrix * gl_Vertex;
    vViewPos = viewPos.xyz;

    gl_Position = gl_ProjectionMatrix * viewPos;
}
