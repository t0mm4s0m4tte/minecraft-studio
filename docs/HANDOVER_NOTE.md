# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.4.0)
*Ultimo aggiornamento: 19 Novembre 2026, 10:05 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master` (pulito, sincronizzato con `origin/master`).
- **Milestone Ufficiale**: **v1.4.0 ("Dimensional Overhaul, Edge-AA/CAS & Camera Motion Blur")** completata, validata e taggata (`v1.4.0`).
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.4.0.zip`.
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.4.0.zip`.
  - Mod multi-loader in dist: `dist/ambient_luminescence-fabric-1.4.0.jar` e `dist/ambient_luminescence-neoforge-1.4.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.4.0)

### A. Luma-Guided Edge-AA & Contrast Adaptive Sharpening (`final.fsh` + `lib/settings.glsl`)
- Filtro spaziale guidato dal gradiente di luminanza cardinale (`nN`, `nS`, `nE`, `nW`) combinato con Contrast Adaptive Sharpening (CAS, `#ifdef AA_SHARPEN`).
- Attivo di default sui profili `Balanced` e `Cinematic`, disabilitato su `Potato`.
- Attenua l'aliasing sui bordi ad alto contrasto preservando e valorizzando la nitidezza delle texture LabPBR 32x.

### B. Analytical Camera Velocity Motion Blur (`final.fsh`)
- Ricostruzione screen-space della velocità di camera tramite reproiezione analitica con matrici inverse e matrici del frame precedente (`gbufferProjectionInverse`, `gbufferModelViewInverse`, `gbufferPreviousModelView`, `gbufferPreviousProjection`).
- Esclusione della mano/primo piano (`rawDepth > 0.56` e `rawDepth < 0.9999`) e campionamento direzionale a 4-tap clampato per azzerare artefatti visivi sulle rotazioni rapide.
- Attivo di default sul profilo `Cinematic`, disabilitato su `Potato` e `Balanced`.

### C. Nether & End Dimensional Atmosphere & Emissive Rim-Light (`deferred.fsh` + `gbuffers_terrain.fsh`)
- In `deferred.fsh`: rilevamento delle profondità sotterranee e dimensioni chiuse (`absoluteWorldY < 32.0`) con potenziamento della foschia calda/magmatica e perforazione della nebbia proporzionale all'emissività LabPBR del frammento (`fogFactor *= (1.0 - emissive * 0.75)`).
- In `gbuffers_terrain.fsh`: rim-light fresnel emissivo (`emissiveRim = pow(1.0 - NdotV, 3.0) * emissive * 1.25`) per i blocchi incandescenti (lava, shroomlight, crying obsidian, soul fire).

### D. Release Packaging v1.4.0, Test & Deploy Client
- Validazione LabPBR 1.3: `60/60 PASS` in modalità strict.
- Test automatici `unittest`: 2/2 passati (`100% OK`).
- Pacchetti compilati in `dist/` e copiati in `.minecraft/shaderpacks/` e `.minecraft/resourcepacks/`.

---

## 3. Comandi di Ripresa Rapida
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict
python -m unittest discover -s tests -v
python scripts/package_release.py --version 1.4.0 --skip-gradle
```
