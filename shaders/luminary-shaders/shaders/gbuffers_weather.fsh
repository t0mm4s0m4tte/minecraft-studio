#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_weather.fsh
 * Rendering avanzato di pioggia e neve:
 * 1. Soft camera near-fade (elimina il taglio brusco e le righe a raggiera a ridosso degli occhi)
 * 2. Ammorbidimento della texture con curva di trasparenza cinematografica
 * 3. Tonalità azzurro-nebbia atmosferica coerente con il cielo piovoso
 */

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform float wetness;
uniform float rainStrength;

in vec4 vColor;
in vec2 vTexCoord;
in vec2 vLmCoord;
in vec3 vViewPos;

/* RENDERTARGETS: 0,1,2 */
layout(location = 0) out vec4 outColor;
layout(location = 1) out vec4 outNormal;
layout(location = 2) out vec4 outData;

vec3 srgbToLinear(vec3 c) {
    return pow(max(c, vec3(0.0)), vec3(2.2));
}

void main() {
    vec4 tex = texture(gtexture, vTexCoord) * vColor;
    if (tex.a < 0.05) discard;

    // Distanza dalla telecamera in View-Space
    float dist = length(vViewPos);

    // 1. Soft Camera Near-Fade:
    // Dissolve gradualmente le gocce che si trovano a meno di 3.0 blocchi dagli occhi,
    // eliminando l'effetto "raggi sparati in faccia" / distorsione a tunnel prospettica.
    float nearFade = smoothstep(1.0, 3.0, dist);

    // 2. Far Fade delicato per integrare la pioggia nella foschia lontana
    float farFade = 1.0 - smoothstep(16.0, 32.0, dist) * 0.45;

    float alpha = tex.a * nearFade * farFade * 0.72;
    if (alpha < 0.02) discard;

    // Luce ambientale dalla lightmap
    vec3 light = srgbToLinear(texture(lightmap, vLmCoord).rgb);

    // Tinta soffusa atmosferica: ammorbidisce il blu elettrico vanilla verso una goccia d'acqua realistica
    vec3 linearTex = srgbToLinear(tex.rgb);
    vec3 rainTint = mix(linearTex, vec3(0.45, 0.55, 0.68), 0.35);

    outColor = vec4(rainTint * light * 1.15, alpha);
    outNormal = vec4(0.5, 0.5, 1.0, 1.0);
    outData = vec4(0.0);
}
