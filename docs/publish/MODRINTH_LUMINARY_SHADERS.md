# Metadata Table

| Field | Value |
|---|---|
| **Project Type** | Shader |
| **Title** | Luminary Shaders |
| **Slug** | `luminary-shaders` |
| **Summary** | High-performance Iris deferred shaders with Multi-Scatter GGX, Beer-Lambert caustics, and world-space synchronized foliage shadows. |
| **Categories** | Realistic, Performance, PBR |
| **Loaders** | Iris, Oculus, OptiFine |
| **Minecraft Versions** | 1.21.1 |
| **License** | MIT |

---

# Luminary Shaders — Physically Based Deferred Shaders

**Luminary Shaders** è una pipeline di rendering deferred per **Iris / Oculus / OptiFine** in **Minecraft 1.21.1**, architettata in GLSL `#version 330 compatibility` con un rigoroso target di frame rate competitivo ($\le 3.8\text{ ms}$ a 1440p sul profilo predefinito *Balanced*).

Sviluppato per offrire un'illuminazione cinematografica e fisicamente coerente senza sacrificare la fluidità di gioco, Luminary Shaders include calcoli ottici avanzati di riflessione, rifrazione, volumetria atmosferica e sincronizzazione delle ombre del mondo.

---

## ☀️ Funzionalità Tecniche Avanzate

- **Multi-Scatter GGX & LabPBR 1.3 Native**:
  - Conservazione dell'energia ottica sui materiali ruvidi ad alta riflessione, eliminando il classico scurimento innaturale dei metalli microfaccettati.
  - Pieno supporto a rugosità percettiva, $F_0$ conduttori/dielettrici, e Subsurface Scattering (SSS) su foglie, cera e marmo.
- **Absolute World-Space Foliage Waving & Shadow Sync**:
  - Il calcolo dell'oscillazione del vento è calcolato in coordinate globali di mondo assoluto.
  - Perfetta sincronizzazione fotometrica tra la mappa d'ombra (`shadow.vsh`) e la geometria del mondo (`gbuffers_terrain.vsh`): zero distaccamento, sfarfallio o ombre fantasma sulle foglie mosse dal vento.
- **World-Space Beer-Lambert Water & Caustic Solar Projection**:
  - Simulazione fisica della penetrazione della luce nell'acqua con coefficienti di assorbimento cromatico realistici.
  - Caustiche subacquee animate proiettate secondo il vettore solare astronomico.
- **View-Invariant Hand & Entity IBL**:
  - Calcolo dei vettori normali world-space isolato dal rollio o dalle rapide rotazioni della visuale in prima persona.
- **8-Tap Screen Cavity Ambient Occlusion**:
  - Filtro di occlusione su cavità a campionamento geometrico bilanciato per evidenziare interstizi, mattoni e crepature.
- **Profili Scalabili Integrati**:
  - *Potato*: Ottimizzato per GPU integrate ($\le 1.2\text{ ms}$).
  - *Balanced* (Predefinito): Bilanciamento ottimale tra fedeltà visiva PBR e frame rate competitivo ($\le 3.8\text{ ms}$).
  - *Cinematic*: Massima accuratezza con 16-step POM, 24-step SSR e 8-tap Cavity AO ($\le 6.5\text{ ms}$).

---

## 🔗 Il Trittico Grafico di Minecraft Studio

Luminary Shaders raggiunge il suo apice visivo combinato con gli altri due pilastri del **Trittico di Minecraft Studio**:

1. **[Aetheria LabPBR 32x](https://github.com/t0mm4s0m4tte/minecraft-studio/blob/master/docs/publish/MODRINTH_AETHERIA_LABPBR.md)**: Resource pack con materiali LabPBR 1.3 ottimizzati specificamente per la BRDF di Luminary Shaders.
2. **[Ambient Luminescence](https://github.com/t0mm4s0m4tte/minecraft-studio/blob/master/docs/publish/MODRINTH_AMBIENT_LUMINESCENCE.md)**: Luce dinamica per entità e oggetti tenuti in mano, iniettata in tempo reale nel deferred pipeline.

Puoi installare l'intero Trittico in 1 click con **`Minecraft-Studio-Triptych-2.2.0.mrpack`** scaricabile dalla [GitHub Release v2.2.0](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/tag/v2.2.0).

---

## 📥 Installazione

1. Installa Minecraft 1.21.1 con **Fabric** e **Iris Shaders** (oppure NeoForge con Iris/Oculus).
2. Scarica `Luminary-Shaders-2.2.0.zip`.
3. Posizionalo nella cartella `.minecraft/shaderpacks/`.
4. Nel menu di gioco, vai su **Opzioni $\to$ Impostazioni video $\to$ Shader Packs**, seleziona *Luminary Shaders* e applica.
5. Regola il profilo qualitativo preferito direttamente dalle impostazioni shader integrate.

---

## 📄 Licenza

Rilasciato sotto licenza Open Source **MIT License**.

