# Changelog

All notable changes to the Minecraft Studio suite are documented in this file.
The format is based on Keep a Changelog and adheres to Semantic Versioning.

## [1.9.0] - 2026-11-21
### Added & Fixed
- **Mod `ambient-luminescence` (v1.9.0)**: Added asynchronous hot-reload polling (`pollReloadAsync()`) triggered every 100 ticks checking `Files.getLastModifiedTime(...)` on `ambient_luminescence.json`. Calibrated dynamic light falloff slope `Math.max(0.85, (double) clampedLum / (radius + 0.8))` allowing dynamic lights to fully illuminate up to `maxRadius = 14`.
- **Resource Pack `aetheria-labpbr-32x`**: Expanded seamless multi-rotation anti-tiling blockstates from 29 to 54 cubical blocks (adding tuff bricks, prismarine variants, nether bricks, end stone bricks, polished blackstone variants, calcite, terracotta, dripstone, obsidian variants, mud variants, coarse/rooted dirt, cracked deepslate variants, purpur, snow and ice). Integrated strict JSON validation of `pack.mcmeta` and all `blockstates/*.json` in `validate_labpbr.py`.
- **Shaders `luminary-shaders`**: Fixed `vBlockId` scoping outside `#ifdef FOLIAGE_WAVING` in `gbuffers_terrain.vsh` (fixing Potato profile foliage bug); purged dead `blockId == 5` references from `gbuffers_terrain.vsh`, `shadow.vsh`, and `gbuffers_terrain.fsh`; fixed underwater column depth linear comparison `-vViewPos.z` in `gbuffers_water.fsh`; replaced binary step with smooth sky transition and water-eye check `smoothstep(0.01, 0.12, ssrLen) * float(isEyeInWater == 0)` in `composite.fsh`; updated `block.properties` with MC 1.21.1 emissive IDs and zero duplicates; updated `shaders.properties` release header.
- **Extended Static GLSL QA Suite**: Added 4 new tests in `tests/test_shaders_static.py` (RENDERTARGETS match layout outputs count, shader `#include` target existence, `en_us.lang` / `it_it.lang` key parity, and no unbounded `while(true)` loops).
- **CI & Release Tooling**: Added Pillow installation and contact sheet generation step to `.github/workflows/build.yml`; updated default version in `package_release.py` to `1.9.0`.

## [1.8.0] - 2026-11-21
### Added
- **Asynchronous JSON Client Configuration (`LuminescenceConfig.java`)**: Pure Java non-blocking configuration loader reading `config/ambient_luminescence.json` via `Util.ioPool()`. Configurable max radius (clamped `4..14`), toggles for entity lighting, dropped items, and fire entity lighting with resilient JSON fallback on parse errors.
- **Expanded MC 1.21.1 Dynamic Light Sources**: Added missing registry entries in `DynamicLightRegistry` for `beacon`, `conduit`, `end_rod`, `jack_o_lantern`, `campfire`, `soul_campfire`, `ochre_froglight`, `verdant_froglight`, `pearlescent_froglight`, `respawn_anchor`, `enchanting_table`, `ender_chest`, `blaze_rod`, `blaze_powder`, `magma_cream`, `prismarine_crystals`, plus dynamic entity lighting for `Allay` (8), `EndCrystal` (12), and fireballs (12).
- **Automated Visual QA Contact Sheet Generator (`generate_contact_sheets.py`)**: Generates 3x3 albedo seamless tiling preview (`contact_sheet_3x3.png`) and synthetic LabPBR lit preview (`contact_sheet_lit.png`) for visual validation.
- **12 New Anti-Tiling Blockstates**: Added weighted multi-rotation definitions (`0°/90°/180°/270°`) for `stone_bricks`, `cracked_stone_bricks`, `mossy_stone_bricks`, `mossy_cobblestone`, `deepslate_bricks`, `deepslate_tiles`, `moss_block`, `mud`, `clay`, `soul_sand`, `soul_soil`, and `blackstone` (total anti-tiling blockstates expanded to 29).
- **Energy-Preserving SSR with Sky Fallback (`composite.fsh`)**: Added `computeSSRSkyFallback` blending horizon and zenith lighting on missed/edge SSR rays, and enforced energy-conserving composition `color = color * (1.0 - F * reflectionStrength * 0.55) + ssrColor * F * reflectionStrength;`.
- **5-Tap Tent Bloom Filter (`final.fsh`)**: Replaced single-tap bloom sampling with a 5-tap cross Tent filter on `colortex3` for smoother highlight rolloff without edge halos.
- **GLSL Static QA Suite (`tests/test_shaders_static.py`)**: Unit tests enforcing `#version 330 compatibility`, `/* RENDERTARGETS: ... */` annotations, `srgbToLinear` in `gbuffers_*.fsh`, and no duplicate block mappings in `block.properties`.
- **Modrinth & Marketplace Documentation (`docs/MODRINTH_PAGE.md`)**: Complete release sheet ready for public publishing on Modrinth and CurseForge.

## [1.7.0] - 2026-11-20
### Added
- **Zero-Allocation Double-Buffering Engine (`DynamicLightTracker.java`)**: Pre-allocated dual map buffers (`MAP_A`, `MAP_B`) and dual dirty set buffers (`DIRTY_A`, `DIRTY_B`), eliminating all per-tick heap allocations during dynamic light propagation and dirty chunk discovery.
- **Full-Pack Strict Validator Mode (`validate_labpbr.py --all`)**: Automated validation over all 1,620 texture sets (1,015 blocks and 605 items = 4,860 PNGs) with custom handling for vanilla 64x flowing fluid textures (`lava_flow`, `water_flow`).
- **Extended Anti-Tiling Blockstates**: Added 10 multi-variant weighted rotation blockstates (`deepslate`, `cobbled_deepslate`, `dirt`, `sand`, `netherrack`, `end_stone`, `granite`, `diorite`, `andesite`, `bricks`) bringing the total to 17.
- **Integrated PBR (IPBR) Shader Fallback (`gbuffers_terrain.vsh`, `gbuffers_terrain.fsh`)**: Real-time pass-through of `vBlockId` via `mc_Entity.x` to assign physically-based fallback metallic and emissive properties when specular maps are unassigned.
- **Dynamic Shadow Texel Resolution**: `texelSize` in `gbuffers_terrain.fsh` Poisson filter is now dynamically scaled from Iris `shadowMapResolution`.
- **Packaging & CI Alignment**: Mod version bumped to `1.7.0`, GitHub Actions CI updated to execute `--strict --all` validation, and release packager default set to `1.7.0`.

## [1.6.0] - 2026-11-19
### Added
- **Volumetric Weather Particle Lighting & Dynamic Torch Scatter (`gbuffers_weather.fsh`)**: Physical forward-scattering Mie on rain and snow particles driven by sun/moon vector (`shadowLightPosition`), combined with quadratic handheld dynamic torchlight falloff (`heldBlockLightValue`, `heldBlockLightValue2`).
- **Procedural Rain Splash Ripples on Dynamic Puddles (`gbuffers_terrain.fsh`)**: Procedural concentric wave propagation rings (*rain splash ripples*) perturbing the surface normal of dynamic puddles (`#ifdef DYNAMIC_PUDDLES`) during rain (`rainStrength > 0.05`).
- **Underwater Volumetric Caustic Light Shafts (`composite.fsh`)**: Submerged crepuscular light shafts adapted to marine cyan-emerald spectrum (`vec3(0.18, 0.78, 0.95)`) with boosted volumetric depth transmission when `isEyeInWater == 1`.

## [1.5.0] - 2026-11-19
### Added
- **Volumetric Procedural FBM Clouds (`deferred.fsh`, `lib/settings.glsl`)**: Multi-octave fractional Brownian motion cloud deck in the sky dome (`#ifdef VOLUMETRIC_CLOUDS`), animated by `worldTime` wind vector, modulated by rain density, and highlighted with anisotropic solar/lunar silver-lining forward scatter.
- **Beer-Lambert Underwater & Lava Volumetric Fog (`deferred.fsh`)**: Physically based exponential distance absorption with deep cyan-blue marine extinction for water (`isEyeInWater == 1`) and dense fiery amber absorption for lava (`isEyeInWater == 2`).
- **LabPBR 1.3 First-Person Hand & Held Item Shading (`gbuffers_hand.vsh`, `gbuffers_hand.fsh`)**: Full normal (`_n`) and specular (`_s`) decoding for all 605 32x items and tools; microfacet GGX/Schlick highlights on metallic weapons, handheld dynamic torchlight falloff, Fresnel rim-lighting, and real emissive output to `colortex2` (`outData`).
- **LabPBR 1.3 Living Entity & Armor Shading (`gbuffers_entities.fsh`)**: Complete PBR metallic reflectance for iron, gold, diamond, and netherite armors, entity damage-tint blending, dynamic held light propagation, Fresnel edge rim-light, and emissive material data pass-through.
- **Iris Configuration & Localization**: Added `VOLUMETRIC_CLOUDS` option toggle to `shaders.properties` (enabled on `Balanced` and `Cinematic`, disabled on `Potato`) with full English and Italian descriptions.

## [1.4.0] - 2026-11-19
### Added
- **Dimensional Overhaul (Nether & The End)**: Dimensional detection via sky lightmap extinction in `composite.fsh`, volumetric Nether atmospheric dust and End void mist.
- **Underground Ambient Light Overhaul**: Deep cave warm fog and incandescent rim-light for glowing blocks in `deferred.fsh`.
- **Luma-Guided Edge Anti-Aliasing**: Spatial anti-aliasing pass combined with Contrast Adaptive Sharpening (CAS) in `final.fsh`.
- **Analytical Camera Velocity Motion Blur**: 4-tap clamped directional velocity blur with reverse reprojection in `final.fsh`.

## [1.3.0] - 2026-11-19
### Added
- **Dynamic Auto-Exposure**: Multi-point average luminance sampling stored in `colortex3.a` and smooth ocular gain adaptation in `final.fsh`.
- **Cinematic Bokeh Depth of Field**: 6-tap hexagonal bokeh blur in `final.fsh` driven by center crosshair depth delta.
- **Color Grading Presets**: Iris menu selectable LUTs (`Natural AgX`, `Warm Golden Hour`, `Nordic Cold`).
- **Chromatic Aberration**: Optional radial peripheral color fringing on screen borders.

## [1.2.0] - 2026-11-19
### Added
- **Procedural 32x Rain & Snow**: High-definition misting textures eliminating blocky streaks.
- **Foliage Wind Waving & SSS**: Organic waving in `gbuffers_terrain.vsh` and `shadow.vsh` with forward scattering.
- **Stratified Height Fog**: Altitude-based valley mist in `deferred.fsh`.
- **SSR Roughness Filtering**: 3-tap spatial jitter blur on satin surfaces.

## [1.1.0] - 2026-11-18
### Added
- **LabPBR 1.3 Rain Wetness & Puddles**: Porosity darkening and dynamic puddles on flat surfaces.
- **Screen-Space Reflections & Godrays**: Raymarched SSR and volumetric crepuscular rays.
- **Water Caustics & Snell Refraction**: Animated caustics and physically based refraction.

## [1.0.0] - 2026-11-18
### Added
- Initial release of the synergic triptych for Minecraft 1.21.1.
- Complete 32x LabPBR 1.3 resource pack across blocks and items.
- Multi-loader dynamic light client mod (Fabric + NeoForge).
- Deferred shader pack with PBR BRDF, shadows, and POM.
