# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.1.0)
*Ultimo aggiornamento: 19 Novembre 2026, 00:08 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master` (pulito, sincronizzato con `origin/master`).
- **Ultimo Commit**: `647a4c0` — `fix(shaders): implement gbuffers_weather with near camera fade and rain godray suppression`.
- **Milestone Ufficiale**: **v1.1.0** rilasciata e taggata (`v1.1.0`).
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.1.0.zip` (aggiornato con fix meteo).
  - Resourcepack in dist: `dist/Aetheria-LabPBR-32x-1.1.0.zip` (100% copertura 1.21.1: 1.015 blocchi, 605 item).
  - Mod multi-loader in dist: `dist/ambient_luminescence-fabric-1.1.0.jar` e `dist/ambient_luminescence-neoforge-1.1.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.1.0)

### A. Sinergia LabPBR & Rain Wetness (`gbuffers_terrain.fsh`)
- Lettura canale **Porosità LabPBR 1.3** (`_s.b` in `0..64`).
- Oscuramento realistico dell'albedo per assorbimento d'acqua nei materiali porosi.
- Incremento di smoothness superficiale per film d'acqua.
- **Dynamic Puddles**: Formazione di micro-pozzanghere organiche guidate da noise 2D su superfici orizzontali rivolte verso l'alto (`vWorldNormal.y > 0.80`), con appiattimento della normale verso `(0, 1, 0)` e F0 calibrato.

### B. Riflessi Screen-Space (SSR) & Luce Volumetrica (`composite.fsh`)
- **SSR in View-Space**: Raymarching ottimizzato con binary refinement (2–3 iterazioni) e vignette edge fade per evitare hard-cut sui bordi dello schermo.
- **Volumetric Godrays**: Crepuscular rays campionando la shadow map con dither Bayer 4x4 e scattering Henyey-Greenstein ($g = 0.58$), scalato tra i profili `Balanced` (8 step) e `Cinematic` (16 step).

### C. Acqua Avanzata & Cielo Notturno
- **Water Caustics & Snell Refraction**:
  - Caustiche solari/lunari procedurali 2D in world-space sul fondale sommerso (`gbuffers_water.fsh`).
  - Micro-rifrazione screen-space di Snell sul fondale con clamp di sicurezza per azzerare il clipping (`depthtex0 < depthtex1`).
- **Atmospheric Night Sky & Stars (`deferred.fsh`)**:
  - Volta stellata procedurale ancorata a `worldDir` (nessun shimmer sub-pixel).
  - Modulazione luce spettrale e contrasto in base alla fase lunare (`moonPhase`).
  - Flash atmosferici temporaleschi durante i temporali (`rainStrength > 0.85`).

### D. Fix Rifinitura Meteo & Risoluzione Bug Segnalato (`gbuffers_weather`)
- **Problema rilevato nel video utente**: Righe della pioggia a raggiera attorno al campo visivo ("raggi attorno a me") causati dalla prospettiva dei billboard vanilla a ridosso degli occhi.
- **Soluzione applicata**:
  - Creati `gbuffers_weather.vsh` e `gbuffers_weather.fsh` con **Soft Camera Near-Fade** (`smoothstep(0.8, 2.5, dist)`).
  - Tonalità atmosferica morbida e trasparenza cinematografica calibrata.
  - Soppressione dei godrays direzionali della shadow map durante pioggia forte (`effectiveRain > 0.85`).

---

## 3. Punti di Partenza per la Prossima Sessione
1. **Verifica visiva in-game con pioggia**:
   - Ricarica shader con `F3 + R` e controlla la morbidezza delle gocce e l'assenza di raggi/aloni parassiti con `/weather rain`.
2. **Eventuali Texture Misting su Resource Pack**:
   - Opzionale: se si desidera una grana delle gocce ancora più fine, valutare una texture custom 32x per `assets/minecraft/textures/environment/rain.png` in `aetheria-labpbr-32x`.
3. **Ottimizzazioni & Prossime Feature (v1.2.0 Roadmap)**:
   - Sfumatura orizzonte nebbia avanzata con biomi umidi/paludi.
   - Subsurface Scattering (SSS) avanzato per foglie e piante (`rawB > 64`).
   - Sottopassi di denoiser temporale per SSR ad altissima risoluzione.

---

## 4. Comandi Utili per Riprendere
```bash
# Validazione asset
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict

# Test unitari
python -m unittest discover -s tests -v

# Rigenerazione release e copia automatica
python scripts/package_release.py --skip-gradle
```
