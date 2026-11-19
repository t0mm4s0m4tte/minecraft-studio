# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.3.0)
*Ultimo aggiornamento: 19 Novembre 2026, 09:49 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master` (pulito, sincronizzato con `origin/master`).
- **Milestone Ufficiale**: **v1.3.0 ("Cinematic Optics, Auto-Exposure & Atmosphere LUTs")** completata, validata e taggata (`v1.3.0`).
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.3.0.zip`.
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.3.0.zip`.
  - Mod multi-loader in dist: `dist/ambient_luminescence-fabric-1.3.0.jar` e `dist/ambient_luminescence-neoforge-1.3.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.3.0)

### A. Dynamic Auto-Exposure & Eye Adaptation (`composite.fsh` -> `final.fsh`)
- Stima multi-point della luminanza media della scena campionando 5 punti cardinali in `composite.fsh` e memorizzandola nel canale alpha di `outBloom` (`colortex3.a`).
- Funzione di guadagno morbido in `final.fsh` (`#ifdef AUTO_EXPOSURE`) con adattamento della risposta oculare (`exposureGain = clamp(0.42 / pow(sceneLuma, 0.35), 0.78, 1.45)`).

### B. Cinematic Bokeh Depth of Field (`final.fsh`)
- Sfocatura ottica a 6 tap su anello esagonale (`#ifdef DOF_ENABLED`), disattivata di default su `Potato` e `Balanced`, abilitata su `Cinematic`.
- Calcolo Circle of Confusion (`CoC`) basato sul delta tra profondità al centro schermo (`depthtex0(vec2(0.5))`) e frammento corrente.

### C. Atmospheric Color Grading LUT & Aberrazione Cromatica (`final.fsh`)
- Selettore `TONEMAP_PRESET`:
  - `0`: Natural AgX (neutro senza distorsione di colore).
  - `1`: Warm Golden Hour (riscaldamento ambrato e contrasto morbido).
  - `2`: Nordic Cold (tonalità fredde artiche e micro-desaturazione).
- Aberrazione cromatica radiale (`#ifdef CHROMATIC_ABERRATION`) sui bordi dello schermo proporzionale alla distanza quadratica dal centro.

### D. Packaging, Test & Deploy Client
- Validazione LabPBR 1.3: `60/60 PASS` in modalità strict.
- Test automatici `unittest`: 2/2 passati (`100% OK`).
- Pacchetti compilati in `dist/` e copiati in `.minecraft/shaderpacks/` e `.minecraft/resourcepacks/`.

---

## 3. Comandi di Ripresa Rapida
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict
python -m unittest discover -s tests -v
python scripts/package_release.py --version 1.3.0 --skip-gradle
```
