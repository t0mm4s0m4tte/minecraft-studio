# Release Engineering & Architecture Status — minecraft-studio (v1.9.0)

---

## 1. Repository & Release Status
- **Branch**: `master`
- **Current Release**: **v1.9.0 ("Precision Shading, Hot-Reload Config, 54 Anti-Tiling & Full QA Gate")**
- **Distribution Artifacts (`dist/`)**:
  - `dist/ambient_luminescence-fabric-1.9.0.jar`
  - `dist/ambient_luminescence-neoforge-1.9.0.jar`
  - `dist/Aetheria-LabPBR-32x-1.9.0.zip`
  - `dist/Luminary-Shaders-1.9.0.zip`

---

## 2. Key Engineering Deliverables (v1.9.0)

### A. Multi-Loader Mod (`mods/ambient-luminescence`)
- **Zero-Allocation Spatial Engine**: Double-buffered primitive maps (`MAP_A`/`MAP_B`, `DIRTY_A`/`DIRTY_B`), `Long2IntMaps.fastIterable`, and `O(1)` lazy identity cache in `DynamicLightRegistry`.
- **Calibrated Radial Falloff**: Dynamic slope `Math.max(0.85, (double) clampedLum / (radius + 0.8))` supporting full light propagation up to `maxRadius = 14`.
- **Asynchronous Hot-Reload Config**: Non-blocking JSON configuration (`config/ambient_luminescence.json`) on `Util.ioPool()` with 100-tick last-modified polling (`pollReloadAsync()`).
- **Multi-Loader & Sodium Hooks**: Verified builds for Fabric (`0.16.5+`) and NeoForge (`21.1.65+`) with multi-target `SodiumLightDataAccessMixin` (Sodium 0.5.11+ and 0.6+).

### B. LabPBR 1.3 Resource Pack (`packs/aetheria-labpbr-32x`)
- **Full Vanilla Coverage**: 1,620 asset sets (1,015 blocks + 605 items = 4,860 RGBA PNGs) passing `--strict --all` validation.
- **54 Anti-Tiling Blockstates**: 4-way weighted rotation variants across 54 cubical blocks, validated syntactically and structurally by `validate_labpbr.py`.
- **Visual QA Contact Sheets**: Automated generation of `docs/branding/contact_sheet_3x3.png` and `docs/branding/contact_sheet_lit.png`.

### C. Iris Shader Pack (`shaders/luminary-shaders`)
- **Cotangent 3D Normal Mapping**: Full `_n.png` normal perturbation on held items (`gbuffers_hand.fsh`) and entities (`gbuffers_entities.fsh`).
- **Precision Shading Fixes**: `vBlockId` initialized across all profiles including `Potato`, linear view-space Z water depth (`-vViewPos.z`), smoothstep SSR sky fallback with underwater guard (`isEyeInWater == 0`), 5-tap Tent bloom, and deduplicated `block.properties`.
- **Static GLSL Gate**: 8 unit tests in `tests/test_shaders_static.py` enforcing directive integrity, render target parity, include resolution, localization key parity, and loop safety.

---

## 3. Verification & Build Pipeline
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict --all
python packs/aetheria-labpbr-32x/scripts/generate_contact_sheets.py
python -m unittest discover -s tests -v
cd mods/ambient-luminescence && ./gradlew build --console=plain
python scripts/package_release.py --version 1.9.0 --skip-gradle
```
