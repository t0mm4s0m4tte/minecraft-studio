#version 330 compatibility

/*
 * Luminary Shaders - gbuffers_weather.fsh
 * Rendering avanzato di pioggia e neve:
 * 1. Soft camera near-fade (elimina il taglio brusco e le righe a raggiera a ridosso degli occhi)
 * 2. Ammorbidimento della texture con curva di trasparenza cinematografica
 * 3. Tonalità azzurro-nebbia atmosferica coerente con il cielo piovoso
 * 4. Forward-scattering solare/lunare e luce dinamica portatile nel raggio della mano
 */

#include "/lib/settings.glsl"

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform float wetness;
uniform float rainStrength;

uniform vec3 shadowLightPosition;
uniform int heldBlockLightValue;
uniform int heldBlockLightValue2;

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

    vec3 dynamicTorchLight = vec3(0.0);
#ifdef DYNAMIC_LIGHTS
    int maxHeldLight = max(heldBlockLightValue, heldBlockLightValue2);
    if (maxHeldLight > 0) {
        float radius = float(maxHeldLight) * 0.90;
        float atten = clamp(1.0 - (dist / max(radius, 1.0)), 0.0, 1.0);
        atten = smoothstep(0.0, 1.0, atten);
        float dynIntensity = (float(maxHeldLight) / 15.0) * atten * atten;
        dynamicTorchLight = vec3(1.40, 0.88, 0.44) * dynIntensity * 1.15;
    }
#endif

    vec3 V = normalize(vViewPos);
    vec3 L = normalize(shadowLightPosition);
    float forwardScatter = pow(clamp(dot(V, L), 0.0, 1.0), 4.0) * 0.65;
    vec3 totalLight = light * (1.15 + forwardScatter) + dynamicTorchLight;

    outColor = vec4(rainTint * totalLight, alpha);
    outNormal = vec4(0.5, 0.5, 1.0, 1.0);
    outData = vec4(0.0);
}
