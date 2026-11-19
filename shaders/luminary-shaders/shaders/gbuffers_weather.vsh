#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_weather.vsh
 * Stage vertex per pioggia e neve con calcolo della posizione in view-space
 * e inclinazione dinamica da vento leggero.
 */

uniform float frameTimeCounter;
uniform mat4 gbufferModelViewInverse;

out vec4 vColor;
out vec2 vTexCoord;
out vec2 vLmCoord;
out vec3 vViewPos;

void main() {
    vColor = gl_Color;
    vTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    vLmCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;

    vec4 vertex = gl_Vertex;

    // Inclinazione dinamica da vento: inclina leggermente le particelle di pioggia/neve
    // in direzione orizzontale in base all'altezza locale e a un'oscillazione sinusoidale morbida.
    float windTime = frameTimeCounter * 1.5;
    float windStrength = 0.22 + 0.08 * sin(windTime * 0.7);
    float windGust = sin(windTime + vertex.y * 0.15) * 0.06;
    vertex.x += (windStrength + windGust) * (vertex.y * 0.12);
    vertex.z += (windStrength * 0.5) * (vertex.y * 0.08);

    vec4 viewPos = gl_ModelViewMatrix * vertex;
    vViewPos = viewPos.xyz;

    gl_Position = gl_ProjectionMatrix * viewPos;
}

