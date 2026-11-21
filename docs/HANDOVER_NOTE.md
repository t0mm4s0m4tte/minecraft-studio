# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.7.0)
*Ultimo aggiornamento: 21 Novembre 2026, 14:10 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master`.
- **Milestone Ufficiale**: **v1.7.0 ("Cross-Layer Hardening, Zero-Alloc Sync & Release QA")** completata, validata e pacchettizzata.
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.7.0.zip`.
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.7.0.zip`.
  - Mod multi-loader in client e dist:
    - Client: `C:\Users\tommy\AppData\Roaming\.minecraft\mods\ambient_luminescence-fabric-1.7.0.jar` (rimosso il vecchio `1.0.0.jar`).
    - Dist: `dist/ambient_luminescence-fabric-1.7.0.jar` e `dist/ambient_luminescence-neoforge-1.7.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.7.0)

### A. Mod `ambient-luminescence`
- Versione sincronizzata a `1.7.0` in `gradle.properties`.
- Refactoring `DynamicLightTracker.java` a double-buffering pre-allocato (`MAP_A`/`MAP_B` e `DIRTY_A`/`DIRTY_B`), azzerando le allocazioni per-tick nella pipeline di render.
- Test unitario `testZeroAllocDoubleBufferingAndDirtySections()` in `DynamicLightTest.java`.
- Compilazione riuscita per Fabric e NeoForge con JDK 21.

### B. Resource Pack `aetheria-labpbr-32x`
- Aggiunto flag `--all` in `validate_labpbr.py`: controllo di tutti i 1.620 set di texture (1.015 blocchi + 605 item = 4.860 PNG) con verifica `texture.properties` e gestione eccezioni fluidi 64x.
- Aggiunti 10 file blockstate anti-tiling in `assets/minecraft/blockstates/` (`deepslate`, `cobbled_deepslate`, `dirt`, `sand`, `netherrack`, `end_stone`, `granite`, `diorite`, `andesite`, `bricks`), portando il totale a 17.

### C. Shader Pack `luminary-shaders`
- Rimossa la sovrapposizione foglie tra `block.5` e `block.10018` in `block.properties`.
- Passaggio di `vBlockId` da `gbuffers_terrain.vsh` a `gbuffers_terrain.fsh` con fallback IPBR automatico se la texture non ha specular attiva.
- Calcolo dinamico di `texelSize` in base a `shadowMapResolution` in `gbuffers_terrain.fsh`.

### D. QA, CI & Packaging
- Aggiornato workflow GitHub Actions (`build.yml`) per eseguire la validazione `--strict --all`.
- Aggiornato `scripts/package_release.py` con default `1.7.0`.
- Rimosso link rotto `b2b-outreach.md` in `README.md`.

---

## 3. Comandi di Verifica Rapida
```powershell
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict --all
python -m unittest discover -s tests -v
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
Push-Location mods/ambient-luminescence; .\gradlew.bat build --console=plain; Pop-Location
python scripts/package_release.py --version 1.7.0
```
