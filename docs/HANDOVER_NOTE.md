# Release Engineering & Architecture Status — minecraft-studio (v2.1.0)

---

## 1. Repository & Release Status
- **Branch**: `master`
- **Current Release**: **v2.1.0 LTS ("Volumetric World-Space Alignment, Ghost-Light Flush & Full 1.21.1 Registry")**
- **Distribution Artifacts (`dist/`)**:
  - `dist/ambient_luminescence-fabric-2.1.0.jar`
  - `dist/ambient_luminescence-neoforge-2.1.0.jar`
  - `dist/Aetheria-LabPBR-32x-2.1.0.zip`
  - `dist/Luminary-Shaders-2.1.0.zip`

---

## 2. Key Engineering Deliverables (v2.1.0)

### A. Multi-Loader Mod (`mods/ambient-luminescence`)
- **Zero-Allocation Spatial Engine**: Double-buffered primitive maps (`MAP_A`/`MAP_B`, `DIRTY_A`/`DIRTY_B`), `Long2IntMaps.fastIterable`, precomputed Euclidean LUT (`double[][][] DIST_LEN`), and `O(1)` lazy identity cache in `DynamicLightRegistry`.
- **Hot-Reload Deactivation Dirty-Section Flush**: `flushDirtySections(Minecraft client)` schedules chunk section rebuilds in Sodium/Vanilla on disable or world reset before emptying trackers, fully eliminating ghost light remnants.
- **Extended MC 1.21.1 Catalog**: Out-of-the-box dynamic lighting for trial spawners, vaults, sea pickles, sculk catalysts, glow lichen, candles (all 16 colors), spectral arrows, ender eyes, dragon eggs, and brown mushrooms.
- **Subaqueous Candle Flame Extinguishment**: Held candles reliably extinguish when submerged underwater alongside torches and campfires.

### B. LabPBR 1.3 Resource Pack (`packs/aetheria-labpbr-32x`)
- **Full Vanilla Coverage**: 1,620 asset sets (1,015 blocks + 605 items = 4,860 RGBA PNGs) passing `--strict --all` validation.
- **54 Anti-Tiling Blockstates**: 4-way weighted rotation variants across 54 cubical blocks, validated syntactically and structurally by `validate_labpbr.py`.
- **Visual QA Contact Sheets**: Automated generation of `docs/branding/contact_sheet_3x3.png` and `docs/branding/contact_sheet_lit.png`.

### C. Iris Shader Pack (`shaders/luminary-shaders`)
- **World-Space Volumetric Light & Caustic Shafts Alignment**: Raymarching sample points transformed via `gbufferModelViewInverse` before `shadowModelView` projection, resolving pitch-dependent volumetric light swimming.
- **View-Invariant SSR Sky Fallback**: Solar elevation computed via `dot(sunN, upN)` rather than view-space `sunDir.y`, ensuring consistent horizon/zenith transitions independent of camera pitch.
- **Multi-Scatter GGX Energy Compensation & World-Space Foliage Shadow Sync**: Physical Turquin multi-scatter microfacet compensation and world-space shadow foliage wave synchronization (`shadowModelViewInverse`).
- **Cotangent 3D Normal Mapping**: Full `_n.png` normal perturbation on held items (`gbuffers_hand.fsh`) and entities (`gbuffers_entities.fsh`).

---

## 3. Verification & Build Pipeline
```bash
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict --all
python packs/aetheria-labpbr-32x/scripts/generate_contact_sheets.py
python -m unittest discover -s tests -v
cd mods/ambient-luminescence && ./gradlew build --console=plain
python scripts/package_release.py --version 2.1.0 --skip-gradle
```

