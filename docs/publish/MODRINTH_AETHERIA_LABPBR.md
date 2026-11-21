# Metadata Table

| Field | Value |
|---|---|
| **Project Type** | Resource Pack |
| **Title** | Aetheria LabPBR 32x |
| **Slug** | `aetheria-labpbr-32x` |
| **Summary** | Complete LabPBR 1.3 32x resource pack with 100% 1.21.1 coverage, strict normal/height maps, subsurface scattering, and anti-tiling. |
| **Categories** | Realistic, Modern, 32x |
| **Loaders** | Vanilla, Fabric, NeoForge, Iris, OptiFine |
| **Minecraft Versions** | 1.21.1 |
| **License** | MIT |

---

# Aetheria LabPBR 32x — Physically Based Materials

**Aetheria LabPBR 32x** è un pacchetto di risorse ad alta fedeltà a 32 pixel per blocco conforme al protocollo standard **LabPBR 1.3**, progettato specificamente per le pipeline shader fisicamente corrette (PBR) di Minecraft 1.21.1.

Ogni singola texture è stata generata e validata su tre canali cromatici e fisici distinti (Albedo RGBA, Normal/Height `_n.png`, Specular/Roughness/F0/SSS `_s.png`), garantendo un'interazione fotometrica impeccabile sotto qualsiasi condizione di luce o inclinazione solare.

---

## 🎨 Caratteristiche dei Materiali

- **Copertura Completa 1.21.1 (1.620 Asset Sets / 4.860 File PNG)**:
  - Tutti i blocchi minerali, pietre, legni, fogliami e vegetazione.
  - Copertura integrale delle strutture *Trial Chambers*: tuff chisel/bricks, rame ossidabile in tutti gli stadi, trial spawner, vault e grate di rame.
- **Conformità Rigorosa LabPBR 1.3**:
  - `_n.png` (Canale Normale + Altezza/Parallasse): Red = $Normal_X$, Green = $Normal_Y$, Blue = Occlusione Ambientale (AO), Alpha = Height Map (POM).
  - `_s.png` (Canale Proprietà Materiali): Red = Perceptual Smoothness ($1 - Roughness$), Green = Riflettanza di base $F_0$ (Metalli dielettrici vs conduttori), Blue = Porosità / Subsurface Scattering (SSS), Alpha = Emissione LabPBR.
- **54 Blockstates Anti-Tiling**: Rotazioni pesate casuali per pietre naturali, ghiaia, sabbia e terra, eliminando l'effetto griglia ripetitiva su grandi distanze.
- **Zero Artefatti di Compressione**: Tutte le texture sono esportate a 32x32 RGBA senza dithering distruttivo o perdite di bit depth.

---

## 🔗 Il Trittico Grafico di Minecraft Studio

Aetheria LabPBR 32x dà il massimo se abbinato agli altri due componenti del **Trittico di Minecraft Studio**:

1. **[Luminary Shaders](https://github.com/t0mm4s0m4tte/minecraft-studio/blob/master/docs/publish/MODRINTH_LUMINARY_SHADERS.md)**: La pipeline shader progettata su misura per interpretare le altezze POM, la rugosità GGX e le proprietà metalliche di Aetheria senza clipping o sfarfallio.
2. **[Ambient Luminescence](https://github.com/t0mm4s0m4tte/minecraft-studio/blob/master/docs/publish/MODRINTH_AMBIENT_LUMINESCENCE.md)**: Mod di illuminazione dinamica per torce ed entità che fa risaltare i riflessi LabPBR in tempo reale nelle caverne.

Installazione rapida 1-click disponibile con **`Minecraft-Studio-Triptych-2.2.0.mrpack`** tramite la [GitHub Release v2.2.0](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/tag/v2.2.0).

---

## 📥 Installazione

1. Scarica `Aetheria-LabPBR-32x-2.2.0.zip`.
2. Posizionalo nella cartella `.minecraft/resourcepacks/`.
3. In Minecraft, apri **Opzioni $\to$ Pacchetti di risorse**, sposta *Aetheria LabPBR 32x* nella colonna di destra e clicca su *Fatto*.
4. Per visualizzare le normali 3D e i riflessi metallici, attiva uno shader pack compatibile con LabPBR 1.3 (come **Luminary Shaders** o qualunque shader Iris/OptiFine PBR).

---

## 📄 Licenza

Rilasciato sotto licenza Open Source **MIT License**.

