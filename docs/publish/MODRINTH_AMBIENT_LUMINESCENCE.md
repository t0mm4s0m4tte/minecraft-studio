# Metadata Table

| Field | Value |
|---|---|
| **Project Type** | Mod |
| **Title** | Ambient Luminescence |
| **Slug** | `ambient-luminescence` |
| **Summary** | Zero-allocation Euclidean dynamic lights with underwater flame rules and async hot-reload config for Fabric & NeoForge 1.21.1. |
| **Categories** | Optimization, Technology, Utility |
| **Loaders** | Fabric, NeoForge |
| **Minecraft Versions** | 1.21.1 |
| **License** | MIT |

---

# Ambient Luminescence — Dynamic Lights Engine

**Ambient Luminescence** è il motore di illuminazione dinamica ad altissima efficienza e zero allocazioni a runtime per **Minecraft 1.21.1**, sviluppato per architetture **Fabric** e **NeoForge**.

Progettato da zero per eliminare il garbage collection overhead e le latenze tipiche delle mod di luce dinamica convenzionali, Ambient Luminescence precalcola una Look-Up Table (LUT) euclidea tridimensionale ed esegue il calcolo fotometrico direttamente sul thread di rendering o sul loop asincrono.

---

## ⚡ Caratteristiche Architetturali Chiave

- **Zero-Allocation Euclidean Distance LUT**: Niente istanziazioni di oggetti `Vec3d` o iterazioni di heap durante l'aggiornamento luminoso dei chunk. Calcolo deterministico della propagazione della luce.
- **Supporto Nativo Biloader (Fabric & NeoForge)**: Codice sorgente core condiviso, con bridge dedicati compilati con Java 21 su Fabric Loader 0.16.5+ e NeoForge 21.1.65+.
- **Trial Chambers & 1.21.1 Full Registry**: Riconoscimento immediato di tutte le sorgenti luminose introdotte in Minecraft 1.21.1:
  - Copper Bulbs (tutti i 4 stadi di ossidazione: Unaffected, Exposed, Weathered, Oxidized)
  - Vault e Ominous Vault (stati di idle, attivazione ed emissione ricompense)
  - Crafter in stato di alimentazione redstone
  - Proiettili infiammati (frecce spettrali, proiettili di Breeze accesi)
- **Underwater Flame Rules**: Rilevamento volumetrico dell'immersione in fluidi con spegnimento o attenuazione della luce di torce e lanterne in acqua, compatibile con le convenzioni realistiche dei modpack moderni.
- **Async Hot-Reload JSON Config**: File di configurazione modificabile a caldo senza riavviare il client (`/ambientluminescence reload`).

---

## 🔗 Il Trittico Grafico di Minecraft Studio

Ambient Luminescence è il componente logico del **Trittico di Minecraft Studio**, progettato per interoperare nativamente con:

1. **[Aetheria LabPBR 32x](https://github.com/t0mm4s0m4tte/minecraft-studio/blob/master/docs/publish/MODRINTH_AETHERIA_LABPBR.md)**: Resource pack LabPBR 1.3 ad alta risoluzione con normali e canali emissivi al pixel.
2. **[Luminary Shaders](https://github.com/t0mm4s0m4tte/minecraft-studio/blob/master/docs/publish/MODRINTH_LUMINARY_SHADERS.md)**: Shader pack Iris deferred con campionamento Multi-Scatter GGX e volumetria atmosferica.

Se utilizzi **Prism Launcher** o **Modrinth App**, puoi scaricare direttamente il pacchetto 1-click **`Minecraft-Studio-Triptych-2.2.0.mrpack`** dalla [GitHub Release v2.2.0](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/tag/v2.2.0).

---

## 📥 Installazione & Requisiti

1. Installa Minecraft 1.21.1 con **Fabric Loader** (e Fabric API) oppure **NeoForge**.
2. Scarica il file JAR corrispondente al tuo loader:
   - `ambient_luminescence-fabric-2.2.0.jar`
   - `ambient_luminescence-neoforge-2.2.0.jar`
3. Posiziona il JAR nella cartella `.minecraft/mods/`.
4. (Opzionale) Associa Iris Shaders per abilitare il passaggio dei dati di illuminazione dinamica agli shader deferred.

---

## 📄 Licenza

Rilasciato sotto licenza Open Source **MIT License**.

