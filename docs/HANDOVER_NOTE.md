# Release Engineering & Architecture Status — minecraft-studio (v2.2.0)

---

## 1. Repository & Release Status
- **Branch**: `master`
- **Current Release**: **v2.2.0 LTS ("Absolute World-Space Waving & Caustics, View-Invariant Hand/Entity IBL, 8-Tap Cavity AO & BlockState Light Precision")**
- **Distribution Artifacts (`dist/`)**:
  - `dist/ambient_luminescence-fabric-2.2.0.jar`
  - `dist/ambient_luminescence-neoforge-2.2.0.jar`
  - `dist/Aetheria-LabPBR-32x-2.2.0.zip`
  - `dist/Luminary-Shaders-2.2.0.zip`

---

## 2. Key Engineering Deliverables (v2.2.0)

### A. Multi-Loader Mod (`mods/ambient-luminescence`)
- **Zero-Allocation Spatial Engine**: Double-buffered primitive maps (`MAP_A`/`MAP_B`, `DIRTY_A`/`DIRTY_B`), `Long2IntMaps.fastIterable`, precomputed Euclidean LUT (`double[][][] DIST_LEN`), and `O(1)` lazy identity cache in `DynamicLightRegistry`.
- **World-Unload & Deactivation Flush**: Immediate `lastHeldLuminance = 0`, tracker tick update, section flush, and tracker clear on world-unload or disabled state.
- **Living vs Dropped Immersion Logic**: Strict differentiation between `entity.isInWater()` (items/projectiles) and `living.isUnderWater()` (players/mobs).
- **BlockItemStateProperties Precision**: Handled `charges=0` (`respawn_anchor` discharged) and `waterlogged=false` on `sea_pickle`.
- **Extended Entity & Item Light Catalog**: Added `DragonFireball`, `WitherSkull`, `FireworkRocketEntity`, plus `nether_star`, `fire_charge`, `brewing_stand`, `sculk_sensor`, and `calibrated_sculk_sensor`.

### B. LabPBR 1.3 Resource Pack (`packs/aetheria-labpbr-32x`)
- **Full Vanilla Coverage**: 1,620 asset sets (1,015 blocks + 605 items = 4,860 RGBA PNGs) passing `--strict --all` validation.
- **54 Anti-Tiling Blockstates**: 4-way weighted rotation variants across 54 cubical blocks, validated syntactically and structurally by `validate_labpbr.py`.
- **Visual QA Contact Sheets**: Automated generation of `docs/branding/contact_sheet_3x3.png` and `docs/branding/contact_sheet_lit.png`.

### C. Iris Shader Pack (`shaders/luminary-shaders`)
- **Absolute World-Space Foliage Waving**: Waving anchored to `worldPos.xyz + cameraPosition` before view re-projection in both `gbuffers_terrain.vsh` and `shadow.vsh`.
- **World-Space Water Caustic Solar Projection**: Sun vector transformed into world-space coordinates via `gbufferModelViewInverse` in `gbuffers_water.fsh`.
- **View-Invariant Hand & Entity Environment IBL**: Ambient reflections driven by `dot(R, normalize(upPosition))` and exact LabPBR 1.3 `1..254` emissive decoding in `gbuffers_hand.fsh` and `gbuffers_entities.fsh`.
- **8-Tap Screen-Space Cavity AO**: 4 additional diagonal depth samples for `AO_QUALITY >= 2` in `deferred.fsh`.
- **1.21.1 `block.properties` Cleanup**: Pruned legacy entries and registered all vanilla 1.21.1 light blocks under `block.1`.

---

## 3. Verification & Build Pipeline
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict --all
python packs/aetheria-labpbr-32x/scripts/generate_contact_sheets.py
python -m unittest discover -s tests -v
cd mods/ambient-luminescence && ./gradlew build --console=plain
python scripts/package_release.py --version 2.2.0 --skip-gradle
```


