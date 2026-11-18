#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_skybasic.vsh
 * Passaggio coordinate della volta celeste per gradiente sferico continuo senza tagli.
 */

out vec4 vColor;
out vec3 vWorldDir;

void main() {
    vColor = gl_Color;
    // Calcola il vettore di direzione della sfera celeste nello spazio mondo
    vWorldDir = normalize((gl_ModelViewMatrixInverse * (gl_ModelViewMatrix * gl_Vertex)).xyz);
    gl_Position = ftransform();
}
