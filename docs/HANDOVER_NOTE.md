# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.2.0)
*Ultimo aggiornamento: 19 Novembre 2026, 09:12 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master` (pulito, sincronizzato con `origin/master`).
- **Milestone Ufficiale**: **v1.2.0 ("Foliage SSS, Biome Atmosphere & Weather Misting")** completata, validata e taggata (`v1.2.0`).
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.2.0.zip` (30.151 bytes).
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.2.0.zip` (6.685.048 bytes).
  - Mod multi-loader in dist: `dist/ambient_luminescence-fabric-1.2.0.jar` e `dist/ambient_luminescence-neoforge-1.2.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.2.0)

### A. Weather Misting 32x & Inclinazione Dinamica Vento
- Generazione texture ad alta definizione 32x procedurale per `assets/minecraft/textures/environment/rain.png` e `snow.png` (128x512 RGBA):
  - Micro-gocce sottili con decadimento verticale sinusoidale, prive di artefatti blocchettati vanilla.
  - Fiocchi di neve microscopici con sfumatura radiale e densità atmosferica morbida.
- Pipeline riproducibile integrata in `packs/aetheria-labpbr-32x/scripts/build_full_pack_32x.py` (`generate_environment_textures`).
- Inclinazione dinamica da vento leggero su `gbuffers_weather.vsh` modulata da `frameTimeCounter` e quota dei vertici.
- Soft near/far camera fade (`smoothstep(1.0, 3.0, dist)` e far fade su 16–32 blocchi) in `gbuffers_weather.fsh`.

### B. Subsurface Scattering (SSS) Avanzato & Foliage Wind Waving
- Potenziamento Subsurface Scattering (`_s.b` in `65..255`) in `gbuffers_terrain.fsh`:
  - Mie forward-scattering solare/lunare (`pow(clamp(dot(V, -L), 0.0, 1.0), 3.0) * 1.25`) per illuminazione vibrante back-lit attraverso foglie e vegetazione.
  - Tonalità smeraldo/oro organica modulata da `shadowColor` e luce solare.
- Wind waving leggero (`#define FOLIAGE_WAVING`):
  - Oscillazione sinusoidale multi-frequenza in `gbuffers_terrain.vsh` guidata da `mc_Entity.x` per foliage (`10018` e blocco `5`).
  - Coerenza geometrica delle ombre proiettate in `shadow.vsh` con deformazione identica.
  - Mappatura completa in `block.properties` per foglie, erba alta, fiori, rampicanti e coltivazioni.
  - Configurazione completa con toggle in `lib/settings.glsl`, `shaders.properties`, `lang/en_us.lang` e `lang/it_it.lang`.

### C. Stratified Height Fog & Aerial Perspective
- Ricostruzione posizione assoluta in coordinate mondo `worldPos.y` e quota globale `cameraPosition.y + worldPos.y` in `deferred.fsh`.
- Foschia stratificata per altitudine (ground mist nelle valli a bassa quota `y < 85` e aumento durante la pioggia), preservando l'azzeramento sott'acqua (`isEyeInWater == 0`).
- Fusione volumetrica con il colore reale dell'orizzonte calcolato dallo scattering fisico Rayleigh/Mie (`computeAtmosphericSky`).

### D. SSR Roughness Filtering & Packaging Release v1.2.0
- Filtro spatial jitter-blur a 3-tap guidato da `roughness = 1.0 - smoothness` in `composite.fsh` per valori $0.65 < \text{smoothness} < 0.92$:
  - Riflessi nitidi speculari su acqua calma e vetro (`smoothness >= 0.92`).
  - Riflessi satinati fisicamente plausibili su metalli levigati e pietre bagnate.
- Aggiornamento della versione predefinita a `1.2.0` in `scripts/package_release.py`, `README.md` e `docs/TECHNICAL_CONTRACT.md`.
- Esecuzione test unitari (`100% PASS` su 2 test) e validazione LabPBR (`60/60 PASS` strict).
- Deploy dei pacchetti zip `1.2.0` in `.minecraft/shaderpacks/` e `.minecraft/resourcepacks/`.

---

## 3. Comandi di Verifica Rapida
```bash
# Validazione LabPBR 1.3 strict
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict

# Test unitari suite di packaging
python -m unittest discover -s tests -v

# Rigenerazione release
python scripts/package_release.py --version 1.2.0 --skip-gradle
```
