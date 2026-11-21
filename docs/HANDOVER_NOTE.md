# Stato dei Lavori & Diario di Bordo — minecraft-studio (v1.8.0)
*Ultimo aggiornamento: 21 Novembre 2026, 14:45 CET*

---

## 1. Stato Attuale della Repository
- **Branch**: `master`.
- **Milestone Ufficiale**: **v1.8.0 ("Client Config, Visual LabPBR QA, GLSL Static Gate & Modrinth Readiness")** completata, validata e pacchettizzata.
- **Pacchetti Generati & Deployati**:
  - Shaderpack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\shaderpacks\Luminary-Shaders-1.8.0.zip`.
  - Resourcepack in client: `C:\Users\tommy\AppData\Roaming\.minecraft\resourcepacks\Aetheria-LabPBR-32x-1.8.0.zip`.
  - Mod multi-loader in client e dist:
    - Client: `C:\Users\tommy\AppData\Roaming\.minecraft\mods\ambient_luminescence-fabric-1.8.0.jar` (rimosso il vecchio `1.7.0.jar`).
    - Dist: `dist/ambient_luminescence-fabric-1.8.0.jar` e `dist/ambient_luminescence-neoforge-1.8.0.jar`.

---

## 2. Sintesi Lavori Svolti nella Sessione (Milestone v1.8.0)

### A. Mod `ambient-luminescence`
- Versione sincronizzata a `1.8.0` in `gradle.properties`.
- Nuova classe pure Java `LuminescenceConfig.java` per configurazione client asincrona (`ambient_luminescence.json`) con pool IO di Minecraft, raggio dinamico clampato (`4..14`) e gestione fail-safe di JSON corrotto.
- Copertura 1.21.1 completata in `DynamicLightRegistry.java` (campfires, froglights, end rods, beacon, conduit, ecc.) e supporto entità per `Allay`, `EndCrystal`, e fireballs.
- Test unitario completo per salvataggio/caricamento configurazione e clamp raggio in `DynamicLightTest.java`.
- Compilazione riuscita per Fabric e NeoForge con JDK 21.

### B. Resource Pack `aetheria-labpbr-32x`
- Generatore contact sheet `generate_contact_sheets.py` per QA visuale: seamless 3x3 albedo (`contact_sheet_3x3.png`) e synthetic lit preview (`contact_sheet_lit.png`).
- 12 nuovi blockstates anti-tiling (totale 29 blockstate variant a 4 rotazioni pesate).
- Validazione `--strict --all` con 1620/1620 asset set conformi.

### C. Shader Pack `luminary-shaders`
- SSR energy-preserving in `composite.fsh` con fallback su gradiente cielo lungo `reflect(viewDir, N)`.
- Bloom highlights potenziato in `final.fsh` con filtro a 5 tap Tent/Karis su `colortex3`.
- Suite di test statici GLSL in `tests/test_shaders_static.py`.

### D. QA, CI & Packaging
- Scheda di pubblicazione Modrinth/CurseForge in `docs/MODRINTH_PAGE.md`.
- Aggiornato `scripts/package_release.py` con default `1.8.0`.
- Documentazione `README.md`, `CHANGELOG.md` e `docs/TECHNICAL_CONTRACT.md` sincronizzata su `1.8.0-RELEASE`.

---

## 3. Comandi di Verifica Rapida
```powershell
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict --all
python packs/aetheria-labpbr-32x/scripts/generate_contact_sheets.py
python -m unittest discover -s tests -v
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
Push-Location mods/ambient-luminescence; .\gradlew.bat build --console=plain; Pop-Location
python scripts/package_release.py --version 1.8.0 --skip-gradle
```
