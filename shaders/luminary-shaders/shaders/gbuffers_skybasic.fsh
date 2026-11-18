#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_skybasic.fsh
 * Gradiente atmosferico sferico uniforme a 360° senza righe o stacchi netti (stile BSL / Photon).
 */

uniform vec3 sunPosition;
uniform vec3 upPosition;
uniform int worldTime;

in vec4 vColor;
in vec3 vWorldDir;

/* RENDERTARGETS: 0,1 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outData;

void main() {
    // Se è la luna/sole o stella disegnata da vanilla (colore solido brillante), rispettala
    if (vColor.r > 0.95 && vColor.g > 0.95 && vColor.b > 0.95 && vColor.a > 0.8) {
        outColor = vColor;
        outData = vec4(0.0);
        return;
    }

    vec3 dir = normalize(vWorldDir);
    vec3 up = normalize(upPosition);
    vec3 sunDir = normalize(sunPosition);

    // Quota verticale della vista (-1.0 sotto i piedi, 0.0 orizzonte, +1.0 zenit)
    float altitude = clamp(dot(dir, up), -0.2, 1.0);
    float horizonMix = clamp(1.0 - altitude * 1.8, 0.0, 1.0);

    // Giorno vs Notte (sunPosition.y > 0 = giorno)
    float isDay = clamp(sunDir.y * 3.0 + 0.3, 0.0, 1.0);
    float isSunset = clamp(1.0 - abs(sunDir.y) * 4.0, 0.0, 1.0) * (1.0 - isDay * 0.8);

    // Palette atmosferica pulita
    vec3 zenitDay = vec3(0.24, 0.50, 0.92);      // Blu cielo pulito
    vec3 horizonDay = vec3(0.70, 0.84, 0.98);    // Orizzonte celeste chiaro
    vec3 sunsetColor = vec3(0.96, 0.52, 0.22);   // Alba/tramonto arancio
    vec3 nightZenith = vec3(0.02, 0.03, 0.07);   // Notte profonda
    vec3 nightHorizon = vec3(0.05, 0.07, 0.12);  // Notte orizzonte

    // Gradiente sferico morbido continuo
    vec3 daySky = mix(zenitDay, horizonDay, horizonMix * 0.75);
    vec3 nightSky = mix(nightZenith, nightHorizon, horizonMix * 0.7);

    vec3 finalSky = mix(nightSky, daySky, isDay);
    finalSky = mix(finalSky, sunsetColor, isSunset * horizonMix * 0.8);

    outColor = vec4(finalSky, 1.0);
    outData = vec4(0.0);
}
