# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.5.0)
*Ultimo aggiornamento: 19 Novembre 2026, 15:15 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master` (pulito, sincronizzato con `origin/master`).
- **Milestone Ufficiale**: **v1.5.0 ("Volumetric FBM Clouds, Underwater Fog & LabPBR Hand/Entity Shading")** completata, validata e taggata (`v1.5.0`).
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.5.0.zip`.
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.5.0.zip`.
  - Mod multi-loader in dist: `dist/ambient_luminescence-fabric-1.5.0.jar` e `dist/ambient_luminescence-neoforge-1.5.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.5.0)

### A. Procedural Volumetric FBM Clouds & Underwater/Lava Fog (`deferred.fsh` + `lib/settings.glsl`)
- Implementato strato di nuvole volumetriche procedurali FBM a 3 ottave nella cupola celeste (`#ifdef VOLUMETRIC_CLOUDS`), attivo su `Balanced` e `Cinematic`, disabilitato su `Potato`.
- Le nuvole sono animate da offset vento basato su `worldTime`, modulate in copertura e densità dall'intensità della pioggia (`rain`), integrate con attenuazione all'orizzonte e illuminate con *silver-lining* anisotropo solare/lunare.
- Aggiunta foschia volumetrica subacquea Beer-Lambert (`isEyeInWater == 1`) con assorbimento ciano-blu profondo ed estinzione esponenziale sulla distanza modulata dall'elevazione solare, e foschia densa infuocata per la lava (`isEyeInWater == 2`).

### B. LabPBR 1.3 First-Person Hand & Held Item Shading (`gbuffers_hand.vsh`, `gbuffers_hand.fsh`)
- Aggiornato vertex shader esponendo `vViewPos` dal model-view matrix.
- Decodifica completa LabPBR 1.3 in fragment shader: texture normals (`_n`) e specular (`_s`), tabella F0 dei metalli nativi (Ferro, Alluminio, Cromo, Rame, Oro, Platino, Nichel, Argento) ed emissivi reali.
- Specular highlight microfacet GGX/Schlick su armi ed attrezzi metallici, illuminazione dinamica portatile (`heldBlockLightValue`, `heldBlockLightValue2`), rim-light Fresnel e scrittura corretta del buffer PBR `outData` (`colortex2`).

### C. LabPBR 1.3 Living Entity & Armor Shading (`gbuffers_entities.fsh`)
- Decodifica LabPBR completa su entità viventi ed armature metalliche/diamante/netherite con supporto entity damage tint overlay (`entityColor`).
- Illuminazione dinamica portatile proiettata sulle entità vicine, rim-light Fresnel di silhouette e riflesso speculare GGX/Schlick con passthrough dati PBR in `colortex2`.

### D. Release Packaging v1.5.0, Test & Deploy Client
- Validazione LabPBR 1.3: `60/60 PASS` in modalità strict su tutti i blocchi core.
- Test automatici `unittest`: 2/2 passati (`100% OK`).
- Pacchetti compilati in `dist/` e copiati in `.minecraft/shaderpacks/` e `.minecraft/resourcepacks/`.

---

## 3. Comandi di Ripresa Rapida
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict
python -m unittest discover -s tests -v
python scripts/package_release.py --version 1.5.0 --skip-gradle
```
