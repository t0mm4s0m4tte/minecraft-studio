# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.6.0)
*Ultimo aggiornamento: 19 Novembre 2026, 15:33 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master` (pulito, sincronizzato con `origin/master`).
- **Milestone Ufficiale**: **v1.6.0 ("Dynamic Weather Splashes, Volumetric Rain Illumination & Underwater Caustic Shafts")** completata, validata e taggata (`v1.6.0`).
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.6.0.zip`.
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.6.0.zip`.
  - Mod multi-loader in dist: `dist/ambient_luminescence-fabric-1.6.0.jar` e `dist/ambient_luminescence-neoforge-1.6.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.6.0)

### A. Volumetric Weather Particle Lighting & Handheld Torch Scatter (`gbuffers_weather.fsh`)
- Inclusione di `settings.glsl` e calcolo dello scattering solare/lunare anisotropo in avanti sulle gocce di pioggia e i fiocchi di neve (`shadowLightPosition`).
- Introduzione dell'illuminazione dinamica portatile (`heldBlockLightValue`, `heldBlockLightValue2`) sulle particelle di pioggia/neve ravvicinate con attenuazione quadratica morbida e raggio calibrato.

### B. Procedural Rain Splash Ripples on Dynamic Puddles (`gbuffers_terrain.fsh`)
- Aggiunta di `uniform float frameTimeCounter;` e algoritmo analitico `computeRainRipples` basato su onde circolari concentriche ad alta frequenza.
- Perturbazione fisica della normale delle pozzanghere dinamiche (`#ifdef DYNAMIC_PUDDLES`) durante precipitazioni attive (`rainStrength > 0.05`), creando anelli di riverbero realistici su tutte le superfici orizzontali.

### C. Underwater Volumetric Caustic Light Shafts (`composite.fsh`)
- Aggiunta di `uniform int isEyeInWater;` per distinguere l'osservatore emerso da quello immerso.
- Adattamento dello spettro cromatico dei godrays a tonalità ciano-smeraldo marina (`vec3(0.18, 0.78, 0.95)`), con boost volumetrico per simulare fasci di luce caustica sottomarini realistici.

### D. Release Packaging v1.6.0, Test & Deploy Client
- Validazione LabPBR 1.3: `60/60 PASS` in modalità strict su tutti i blocchi core.
- Test automatici `unittest`: 2/2 passati (`100% OK`).
- Pacchetti compilati in `dist/` e copiati in `.minecraft/shaderpacks/` e `.minecraft/resourcepacks/`.

---

## 3. Comandi di Ripresa Rapida
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict
python -m unittest discover -s tests -v
python scripts/package_release.py --version 1.6.0 --skip-gradle
```
