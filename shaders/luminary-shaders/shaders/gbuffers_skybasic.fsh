#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_skybasic.fsh
 * Gradiente atmosferico naturale con sole morbido ed eliminazione nebbia grigia.
 */

uniform vec3 sunPosition;
uniform vec3 upPosition;
uniform int worldTime;

in vec4 vColor;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData;

void main() {
    // Vettore vista normalizzato da colore o interpolazione
    vec3 up = normalize(upPosition);
    vec3 sun = normalize(sunPosition);
    
    // Calcolo ora del giorno (0..24000)
    float timeFrac = float(worldTime % 24000) / 24000.0;
    float isDay = clamp(sin(timeFrac * 3.14159265 * 2.0), 0.0, 1.0);
    float isSunset = clamp(1.0 - abs(isDay - 0.5) * 4.0, 0.0, 1.0);
    
    // Gradienti cielo
    vec3 zenithDay = vec3(0.24, 0.48, 0.88);
    vec3 horizonDay = vec3(0.68, 0.82, 0.96);
    vec3 sunsetColor = vec3(0.96, 0.48, 0.22);
    vec3 nightZenith = vec3(0.02, 0.03, 0.08);
    vec3 nightHorizon = vec3(0.06, 0.08, 0.14);
    
    vec3 daySky = mix(horizonDay, zenithDay, 0.5);
    vec3 finalSky = mix(nightHorizon, daySky, isDay);
    finalSky = mix(finalSky, sunsetColor, isSunset * 0.65);
    
    outColor = vec4(finalSky, 1.0);
    outData = vec4(0.0);
}
