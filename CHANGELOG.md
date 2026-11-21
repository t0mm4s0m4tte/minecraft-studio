# Changelog

All notable changes to the **Minecraft Studio — Synergic Triptych** suite (`ambient-luminescence`, `aetheria-labpbr-32x`, `luminary-shaders`) are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-11-21

### Added
- **Absolute World-Space Foliage Waving & Vector Direction Sync (`gbuffers_terrain.vsh`, `shadow.vsh`)**: Anchored foliage micro-waving to Absolute World-Space coordinates (`worldPos.xyz + cameraPosition`) before applying model-view matrices (`gbufferModelView` and `shadowModelView`), eliminating camera motion jitter and ensuring shadow pass waves at identical phase and direction as the geometry pass.
- **World-Space Water Caustic Solar Projection (`gbuffers_water.fsh`)**: Transformed `sunPosition` from view-space into world-space coordinates via `gbufferModelViewInverse`, stabilizing seabed caustic projection coordinates and preventing rotation during player camera pitch and yaw movements.
- **View-Invariant Hand & Entity Environment IBL (`gbuffers_hand.fsh`, `gbuffers_entities.fsh`)**: Replaced camera-relative `R.y` with view-invariant celestial reflection factor `dot(R, normalize(upPosition))` for ambient IBL reflections on held items and living entities.
- **Exact LabPBR 1.3 Emissive Decoding (`gbuffers_hand.fsh`, `gbuffers_entities.fsh`)**: Implemented strict specification-compliant LabPBR 1.3 emissive scale `rawEmissive / 254.0` for specular alpha values in range `1..254`.
- **True 8-Tap Screen-Space Cavity AO for Cinematic Profile (`deferred.fsh`)**: Added 4 diagonal depth samples (`px * 0.7071`) when `AO_QUALITY >= 2`, delivering smooth high-fidelity screen-space cavity ambient occlusion.
- **1.21.1 `block.properties` Cleanup**: Removed non-vanilla `copper_bulb_lit` identifier and registered `soul_wall_torch`, `redstone_torch`, `redstone_wall_torch`, `trial_spawner`, `vault`, `sculk_catalyst`, `sculk_sensor`, and `calibrated_sculk_sensor` under `block.1`.
- **Java 21 Mod Hardening (`AmbientLuminescenceClient.java`, `DynamicLightRegistry.java`)**:
  - Differentiated underwater immersion logic between dropped items/projectiles (`entity.isInWater()`) and living entities (`living.isUnderWater()`).
  - Added inspection of `BlockItemStateProperties` for `charges=0` (`respawn_anchor` discharged) and `waterlogged=false` on `minecraft:sea_pickle` to prevent false dynamic illumination.
  - Added dynamic light emission for `DragonFireball`, `WitherSkull` (luminance 12), and `FireworkRocketEntity` (luminance 11).
  - Extended dynamic light registry with `nether_star` (12), `fire_charge` (10), `brewing_stand` (1), `sculk_sensor` (1), and `calibrated_sculk_sensor` (1).
  - Ensured `lastHeldLuminance = 0`, tracker tick update, section flush, and tracker clear on world-unload.
- **Automated QA & Package Suite Expansion (`tests/test_shaders_static.py`, `scripts/package_release.py`)**:
  - Added 14th static GLSL test `test_absolute_world_waving_water_caustics_and_cavity_ao`.
  - Updated release packaging script default version target to `2.2.0`.

---

## [2.1.0] - 2026-11-21

### Added
- **World-Space Volumetric Light & Caustic Shafts Alignment (`composite.fsh`)**: Transformed raymarching `sampleView` points from camera view-space to player-centered world-space via `gbufferModelViewInverse` prior to `shadowModelView` projection, resolving pitch-dependent volumetric light swimming and aligning sun shafts and underwater caustic beams to true world orientation.
- **View-Invariant SSR Sky Fallback Solar Elevation (`composite.fsh`)**: Replaced camera-pitch dependent `normalize(sunDir).y` with view-invariant solar elevation `dot(normalize(sunDir), normalize(upDir))` in `computeSSRSkyFallback`, ensuring rock-solid celestial zenith and horizon color gradients during camera tilt.
- **Hot-Reload Deactivation Dirty-Section Flush (`AmbientLuminescenceClient.java`)**: Added `flushDirtySections(Minecraft client)` helper called immediately when `cfg.enabled` is toggled off at runtime or world state resets, scheduling Sodium/Vanilla chunk rebuilds on all illuminated sections before clearing trackers and eliminating ghost light artifacts.
- **Subaqueous Flame Extinguishment for Candles (`AmbientLuminescenceClient.java`)**: Extended underwater flame extinguishment rule to all candle variants (`itemId.endsWith("candle")`), properly extinguishing held candles when submerged.
- **Expanded MC 1.21.1 Dynamic Light Registry (`DynamicLightRegistry.java`)**: Added out-of-the-box dynamic light registrations for Trial Chambers blocks, sculk components, aquatic flora, and candles (`trial_spawner`, `vault`, `sea_pickle`, `sculk_catalyst`, `glow_lichen`, `spectral_arrow`, `ender_eye`, `dragon_egg`, `brown_mushroom`, and all 16 colored candle variants).
- **Automated Regression Test Suite (`tests/test_shaders_static.py`, `tests/test_package_release.py`)**: Added static verification for volumetric world-space transformation and view-invariant sky dot product, and regression test validating cleanup of stale archives in `dist/`.

---

## [2.0.0] - 2026-11-21

### Added
- **Multi-Scatter GGX Energy Compensation (Turquin)**: Implemented `energyComp = vec3(1.0) + F0 * (roughness * 0.65)` in `gbuffers_terrain.fsh`, `gbuffers_hand.fsh`, and `gbuffers_entities.fsh`. Compensates for multiple inter-microfacet scattering loss on rough metals and rough dielectrics, eliminating energy loss darkening at high roughness angles.
- **World-Space Foliage Shadow Synchronization (`shadow.vsh`)**: Foliage wind waving in shadow pass transformed via `shadowModelViewInverse * shadowViewPos` to match the exact world-space wave phase and frequency of `gbuffers_terrain.vsh`, completely eliminating leaf shadow swimming and phase drift.
- **Proportional Euclidean LUT in DynamicLightTracker (`double[][][] DIST_LEN`)**: Precomputed 3D Euclidean distances in a static table combined with dynamic `stepCost = Math.max(0.85, (double) clampedLum / (radius + 0.8))` without runtime `Math.sqrt` calls, ensuring zero-allocation performance with exact radial light bounds.
- **Head/Helmet Dynamic Luminescence Support (`AmbientLuminescenceClient.java`)**: Added `EquipmentSlot.HEAD` inspection on other multiplayer players (`Player otherPlayer`) and all living entities (`LivingEntity living`), allowing mining helmets and illuminated headgear to cast dynamic light across all nearby entities.
- **Distribution Hygiene in `scripts/package_release.py`**: Automated cleanup of legacy version archives in `dist/` upon building, strictly retaining only the 4 release artifacts for `2.0.0`.
- **Static GLSL QA Verification (`tests/test_shaders_static.py`)**: Added `test_multiscatter_ggx_and_shadow_world_sync` verifying Multi-Scatter GGX presence across all geometry stages and shadow world-space inverse transform.

---

## [1.9.0] - Production Release (MC 1.21.1 LTS)

### Added
- **Asynchronous Hot-Reload Client Config (`LuminescenceConfig.java`)**: Pure Java non-blocking configuration (`config/ambient_luminescence.json`) running on `Util.ioPool()` with automatic timestamp polling every 100 client ticks (`pollReloadAsync()`), configurable radius clamping (`4..14`), feature toggles, and resilient fallback on malformed JSON.
- **Expanded MC 1.21.1 Dynamic Light Registry**: Full support for copper bulbs (all oxidation states), froglights, end rods, campfires, soul campfires, beacons, conduits, respawn anchors, enchanting tables, helmet light sources, and living entities (`Allay`, `EndCrystal`, `Blaze`, `MagmaCube`, fireballs, spectral arrows).
- **54 Multi-Rotation Anti-Tiling Blockstates**: Weighted 4-way rotation variants (`0° / 90° / 180° / 270°`) across 54 natural and architectural cubical blocks (stone, deepslate, tuff bricks, prismarine variants, nether bricks, end stone bricks, blackstone variants, calcite, terracotta, dripstone, obsidian, mud bricks, dirt variants, purpur, snow, and ice).
- **Strict JSON & Full-Pack Asset Validator (`validate_labpbr.py`)**: Integrated JSON schema and syntax validation for `pack.mcmeta` and all 54 `blockstates/*.json` alongside strict pixel-level verification of all 1,620 LabPBR 1.3 texture sets (4,860 RGBA PNGs).
- **Automated Visual QA Contact Sheets (`generate_contact_sheets.py`)**: Automated generation of 3x3 seamless tiling mosaics (`contact_sheet_3x3.png`) and synthetic LabPBR lit previews (`contact_sheet_lit.png`) in CI and local builds.
- **Cotangent 3D Normal Mapping on Held Items & Entities (`gbuffers_hand.fsh`, `gbuffers_entities.fsh`)**: Analytic screen-space cotangent frame (`perturbNormalCotangent`) decoding `_n.png` normal maps on all 605 first-person items, tools, weapons, and entity armors.
- **Extended Static GLSL QA Suite (`tests/test_shaders_static.py`)**: 8 automated static analysis checks verifying `#version 330 compatibility`, `RENDERTARGETS` vs `layout(location)` output parity, `#include` resolution, `srgbToLinear` conversion, `block.properties` uniqueness, `en_us.lang` / `it_it.lang` key parity, and absence of unbounded `while(true)` loops.
- **Open-Source & Marketplace Packaging**: MIT License with Mojang asset notice (`LICENSE`), complete Modrinth/CurseForge documentation (`docs/MODRINTH_PAGE.md`), and automated GitHub Release workflow (`.github/workflows/build.yml`).

### Changed & Fixed
- **Zero-Allocation Spatial Engine & Calibrated Radial Falloff (`DynamicLightTracker.java`)**: Double-buffered primitive maps (`MAP_A`/`MAP_B`, `DIRTY_A`/`DIRTY_B`), `Long2IntMaps.fastIterable(...)` tick diffing, `O(1)` lazy identity cache in `DynamicLightRegistry`, and proportional radial falloff slope `Math.max(0.85, (double) clampedLum / (radius + 0.8))` enabling full light reach up to `maxRadius = 14`.
- **Multi-Target Sodium Compatibility**: `SodiumLightDataAccessMixin` supporting both Sodium 0.5.11+ and Sodium 0.6+ package paths alongside 3-arg and 4-arg `LevelRendererMixin` hooks.
- **Terrain Block ID Scoping (`gbuffers_terrain.vsh`)**: Moved `vBlockId` assignment outside `#ifdef FOLIAGE_WAVING` so Integrated PBR (IPBR) material fallbacks remain active on the `Potato` profile; removed legacy `blockId == 5` dead branches across `gbuffers_terrain.vsh`, `gbuffers_terrain.fsh`, and `shadow.vsh`.
- **Linear Water Column Depth (`gbuffers_water.fsh`)**: Replaced Euclidean view distance `length(vViewPos)` with view-space Z depth `-vViewPos.z` for homogeneous Beer-Lambert absorption across wide fields of view.
- **Smooth SSR Sky Fallback & 5-Tap Tent Bloom (`composite.fsh`, `final.fsh`)**: Energy-conserving Screen-Space Reflections with `smoothstep(0.01, 0.12, ssrLen)` sky horizon fallback (disabled underwater via `isEyeInWater == 0`) and 5-tap cross Tent bloom filter on `colortex3`.
- **MC 1.21.1 `block.properties` Alignment**: Updated emissive (`block.1`), metallic (`block.2`, `block.3`, `block.4`), glass (`block.6`), and foliage (`block.10018`) mappings with zero duplicate block identifiers.

---

## [1.5.0 – 1.7.0] - Atmosphere, First-Person PBR & Zero-Alloc Pipeline

### Added
- **Volumetric FBM Procedural Clouds & Submersion Fog (`deferred.fsh`)**: Multi-octave fractional Brownian motion cloud layer with solar/lunar silver-lining scatter and exponential Beer-Lambert underwater/lava extinction.
- **First-Person Hand & Living Entity LabPBR Shading (`gbuffers_hand.*`, `gbuffers_entities.*`)**: Specular (`_s`) and normal (`_n`) decoding for held items and mobs with GGX microfacet highlights, handheld torchlight falloff, and Fresnel rim-lighting.
- **Weather Particle Scattering & Rain Splash Ripples (`gbuffers_weather.fsh`, `gbuffers_terrain.fsh`)**: Mie forward-scattering on rain/snow particles, concentric rain splash ripples on dynamic puddles, and underwater volumetric caustic shafts.
- **Integrated PBR (IPBR) Fallback & Dynamic Shadow Resolution**: Automatic material fallback via `mc_Entity.x` when specular textures are absent, and dynamic Poisson shadow filter scaling via `shadowMapResolution`.

---

## [1.1.0 – 1.4.0] - Deferred Optics, Dimensions & Post-Processing

### Added
- **LabPBR 1.3 Rain Wetness & Dynamic Puddles**: Porosity darkening (`_s.b` `0..64`) and procedural puddle reflection accumulation during rainfall.
- **View-Space SSR, Volumetric Godrays & Water Caustics**: Raymarched reflections with binary refinement, Bayer 4x4 dithered crepuscular rays, and Snell water refraction.
- **Cinematic Post-Processing & Camera Optics (`final.fsh`)**: Dynamic multi-point auto-exposure, 6-tap hexagonal bokeh Depth of Field, Luma-guided Edge AA with Contrast Adaptive Sharpening (CAS), 4-tap camera velocity motion blur, optional chromatic aberration, and selectable color grading LUT presets (`Natural AgX`, `Warm Golden Hour`, `Nordic Cold`).
- **Dimensional Atmosphere (Nether & The End)**: Automatic sky-lightmap dimensional detection driving volumetric Nether ember dust, End void mist, and deep-cave warm incandescent ambient lighting.

---

## [1.0.0] - Foundation Architecture

### Added
- Initial architecture of the Minecraft 1.21.1 Synergic Triptych (`ambient-luminescence` Architectury multi-loader mod, `aetheria-labpbr-32x` 32x32 resource pack, and `luminary-shaders` Iris deferred shader pipeline with GGX BRDF, distorted shadow mapping, and Parallax Occlusion Mapping).
