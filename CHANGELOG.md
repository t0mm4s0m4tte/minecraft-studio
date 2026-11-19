# Changelog

All notable changes to the Minecraft Studio suite are documented in this file.
The format is based on Keep a Changelog and adheres to Semantic Versioning.

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
