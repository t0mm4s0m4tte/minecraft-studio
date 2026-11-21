# Changelog

All notable changes to the Minecraft Studio suite are documented in this file.
The format is based on Keep a Changelog and adheres to Semantic Versioning.

## [1.7.0] - 2026-11-21
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
