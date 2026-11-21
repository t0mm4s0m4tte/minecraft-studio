# Minecraft Studio — Synergic Triptych v2.2.0 LTS (Gold Master)

> **Release di produzione certificata Gold Master per Minecraft 1.21.1.**
> Il Trittico integra in sinergia architetturale nativa il pacchetto di risorse LabPBR 1.3 **Aetheria LabPBR 32x**, la pipeline shader Iris deferred **Luminary Shaders** e il motore di illuminazione dinamica zero-allocation **Ambient Luminescence** per Fabric e NeoForge.

---

## 📦 Artefatti Ufficiali di Rilascio

Scarica il pacchetto completo 1-click compatibile con **Modrinth App** e **Prism Launcher**, oppure i singoli moduli per l'installazione manuale:

| Artefatto | Piattaforma / Loader | Tipo | Download Diretto |
|---|---|---|---|
| **`Minecraft-Studio-Triptych-2.2.0.mrpack`** | Modrinth App / Prism Launcher | **Bundle 1-Click** | [Scarica .mrpack](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/download/v2.2.0/Minecraft-Studio-Triptych-2.2.0.mrpack) |
| **`Aetheria-LabPBR-32x-2.2.0.zip`** | Minecraft 1.21.1 (`pack_format: 34`) | Resource Pack LabPBR | [Scarica .zip](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/download/v2.2.0/Aetheria-LabPBR-32x-2.2.0.zip) |
| **`Luminary-Shaders-2.2.0.zip`** | Iris / Oculus / OptiFine | Shader Pack Deferred | [Scarica .zip](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/download/v2.2.0/Luminary-Shaders-2.2.0.zip) |
| **`ambient_luminescence-fabric-2.2.0.jar`** | Fabric Loader $\ge 0.16.5$ | Mod Dynamic Lights | [Scarica .jar](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/download/v2.2.0/ambient_luminescence-fabric-2.2.0.jar) |
| **`ambient_luminescence-neoforge-2.2.0.jar`** | NeoForge $\ge 21.1.65$ | Mod Dynamic Lights | [Scarica .jar](https://github.com/t0mm4s0m4tte/minecraft-studio/releases/download/v2.2.0/ambient_luminescence-neoforge-2.2.0.jar) |

---

## 🔒 Checksum di Integrità SHA-256

Verifica l'autenticità e l'integrità dei binari scaricati tramite i valori SHA-256 ufficiali generati in fase di build:

```sha256
4156e03e4862a744c4b7129e7e0789e1087f012805e282ceb30a7b5c5e2466c3  Aetheria-LabPBR-32x-2.2.0.zip
fbbe91490d426df69cd1d92578e1892c97cb26954d2066d9addceadc194b518a  ambient_luminescence-fabric-2.2.0.jar
e4a5a95e9841cbadf28396441b022e1b690a8160bf1307e76bbbb858d3e4f50a  ambient_luminescence-neoforge-2.2.0.jar
aacec09aa5f20adb900fe94181f5387b2d1ac3b46bd1adbff401659ef9e7c727  Luminary-Shaders-2.2.0.zip
b8c8b664e08fccabcbd67cdaef939d3fdfe3690588488d74bbfe889996ab0da5  Minecraft-Studio-Triptych-2.2.0.mrpack
```

Per verificare localmente:
- **Linux / macOS**: `sha256sum -c SHA256SUMS.txt`
- **Windows PowerShell**: `Get-FileHash -Algorithm SHA256 <filename>`

---

## 🚀 Novità Tecniche di Rilievo — Milestone v2.2.0 LTS

1. **Absolute World-Space Foliage Waving & Shadow Sync**:
   - Calcolo delle oscillazioni di foglie, erba alta, raccolti e rami traslato in coordinate assolute di mondo (`worldPosition = playerPosition + modelViewPosition`).
   - Sincronizzazione al fotogramma tra lo shadow pass (`shadow.vsh`) e il visual pass (`gbuffers_terrain.vsh`), eliminando completamente ogni disallineamento geometrico o sfarfallio d'ombra durante vento forte o temporali.

2. **World-Space Water Caustic Solar Projection**:
   - Pipeline caustiche subacquee procedurali calcolata mediante proiezione solare in coordinate globali.
   - Attenuazione fotorealistica della luce in base alla profondità della colonna d'acqua con assorbimento spettrale secondo la legge di Beer-Lambert.

3. **View-Invariant Hand/Entity IBL (Image-Based Lighting)**:
   - Riflessioni di Fresnel e illuminazione diffusa/speculare delle mani del giocatore e delle entità calcolate con vettori normali world-space indipendenti dalla rotazione e dal roll della telecamera.
   - Nessun falso gradiente o salto di luminosità durante movimenti rapidi dello sguardo.

4. **8-Tap Screen Cavity Ambient Occlusion**:
   - Kernel di occlusione ambientale per cavità e fessure a 8 campioni bilanciati su buffer di profondità lineare.
   - Marcata definizione geometrica su giunzioni tra blocchi, gradini e scale senza penalità computazionale visibile (budget di frame rispettato: $\le 3.8\text{ ms}$ su profilo Balanced a 1440p).

5. **Java 21 Mod Hardening & Extended 1.21.1 Registry**:
   - Mod compilata nativamente su Java 21 con compatibilità estesa a Fabric 0.16.5+ e NeoForge 21.1.65+.
   - Tabella dinamica estesa per tutti i nuovi blocchi luminosi delle *Trial Chambers* di Minecraft 1.21.1 (Vault, Ominous Vault, Copper Bulbs accesi/ossidati, Crafter attivo).
   - Regole di attenuazione e spegnimento fiamme per torce e lanterne immerse in acqua con fallback deterministico.

---

## 🛠️ Guida Rapida all'Installazione

### Opzione A: Installazione 1-Click con Modrinth App / Prism Launcher (Raccomandata)
1. Scarica `Minecraft-Studio-Triptych-2.2.0.mrpack`.
2. Trascina il file dentro **Modrinth App** oppure in **Prism Launcher** (seleziona *Aggiungi Istanza* $\to$ *Importa da archivio zip/mrpack*).
3. L'istanza configurerà automaticamente Fabric Loader 0.16+, la mod *Ambient Luminescence*, il resource pack *Aetheria LabPBR* e gli shader *Luminary Shaders*.

### Opzione B: Installazione Manuale in `.minecraft/`
1. Assicurati di avere installato Minecraft 1.21.1 con **Fabric Loader** (e *Iris Shaders* + *Fabric API*) oppure **NeoForge** (e *Iris/Oculus*).
2. Posiziona `Aetheria-LabPBR-32x-2.2.0.zip` nella cartella `.minecraft/resourcepacks/` e attivalo nel menu di gioco.
3. Posiziona `Luminary-Shaders-2.2.0.zip` nella cartella `.minecraft/shaderpacks/` e selezionalo nel menu *Shader Packs*.
4. Posiziona `ambient_luminescence-fabric-2.2.0.jar` (o `ambient_luminescence-neoforge-2.2.0.jar`) nella cartella `.minecraft/mods/`.
5. Avvia il gioco e sperimenta la resa visiva fotometrica sincronizzata.

---

*Minecraft Studio Team — Rilascio v2.2.0 LTS Gold Master distribuito sotto licenza Open Source MIT.*

