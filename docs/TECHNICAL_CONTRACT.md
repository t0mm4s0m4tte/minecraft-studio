# TECHNICAL ARCHITECTURE CONTRACT (TAC) — MINECRAFT STUDIO SUITE
**Target**: Minecraft Java Edition 1.21.1 (LTS)  
**Spec Version**: 2.2.0-RELEASE  
**Status**: APPROVED & LOCKED (Single Source of Truth - SSoT)  
**Maintainers**: Minecraft Studio Core Engineering

---

## 1. Runtime & Toolchain Compatibility Matrix
- **Minecraft**: 1.21.1 Java Edition
- **Java Virtual Machine**: JDK 21 (Temurin-21 / GraalVM CE 21, toolchain enforced)
- **Mod Architecture**: Architectury Loom multi-loader (`:common`, `:fabric`, `:neoforge`)
- **Fabric Loader**: `>= 0.16.5` (Fabric API `>= 0.100.0+1.21.1`)
- **NeoForge**: `21.1.65+`
- **Graphics Framework**: Sodium `0.6.x` (or `0.5.11+`) + Iris `1.8.x` (or `1.7.x`)
- **PBR Standard**: LabPBR 1.3 Strict (`pbr.format = lab_pbr_1_3`)

---

## 2. Cross-Layer Triptych Contract (Mod ↔ Resource Pack ↔ Shader Pack)

### 2.1. Iris Rendering Buffers & HDR Formats (`shaders.properties`)
```properties
pbr.format = lab_pbr_1_3
colortex0.format = RGBA16F
colortex1.format = RGBA16F
colortex2.format = RGBA8
colortex3.format = RGBA16F
```
- **`colortex0`**:
  - G-Buffers stage: Linearized Albedo `sRGB -> Linear` (`pow(rgb, 2.2)`), Alpha cutout/transparency.
  - Deferred & Composite stage: Accumulated HDR Linear Light scene (Direct + Ambient + Specular + Dynamic Light).
- **`colortex1`**:
  - G-Buffers stage: Normal Vector (RGB in view/tangent space mapped `[-1..1]`) + Material AO in Alpha channel (or Packed Normal + AO encoding).
- **`colortex2`**:
  - G-Buffers stage: LabPBR 1.3 physical channels:
    - `R`: Smoothness (`0..255`, $Roughness = (1.0 - S/255.0)^2$)
    - `G`: Reflectance / Dielectric F0 or hardcoded metal table ID (`0..229` $\rightarrow F_0 = (G/255)^2$; `230..237` metals; `255` custom metal)
    - `B`: Porosity / SSS (`0..64` rain porosity; `65..255` Subsurface Scattering)
    - `A`: Emissive (`1..254` linear scale, `0` and `255` disabled)
- **`colortex3`**:
  - Isolated Bloom highlights (pre-downsampling mipmap pyramid) + lightmap auxiliary data.

### 2.2. Dynamic Lighting Bridge Protocol (`ambient-luminescence` ↔ `luminary-shaders`)
- **Primary Channel (Vanilla & Sodium Pipeline)**:
  - `ambient-luminescence` injects dynamic luminance directly into `LightDataAccess` (Sodium) and `LevelRenderer.getLightColor` (Vanilla fallback).
  - Coordinates are evaluated lock-free using an immutable atomic snapshot with selective chunk section dirtying (`SectionPos`).
- **Secondary Channel (Shader Pack Iris Uniforms)**:
  - Iris natively provides `heldBlockLightValue` and `heldBlockLightValue2`.
  - The shader pack samples both the mod-driven lightmap (illuminating dropped items, mobs, and surrounding players) and applies a subtle local falloff for near-camera pixels without dual-energy compounding.

### 2.3. Canonical MC 1.21.1 Texture Naming & IPBR Fallback
All textures match the actual vanilla MC 1.21.1 jar names:
- `tuff_bricks.png`, `chiseled_tuff.png`, `polished_tuff.png`, `chiseled_tuff_bricks.png` (replaces non-existent `tuff_tiles`).
- `torch.png` and `soul_torch.png` (used for both ground and wall torches; `wall_torch` removed).
- `trial_spawner_side_inactive.png`, `trial_spawner_side_active.png` (replaces `trial_spawner_side`).
- `crafter_top.png`, `crafter_top_triggered.png`, `crafter_side.png`, `crafter_bottom.png`.
- `copper_bulb.png`, `copper_bulb_lit.png`, `copper_bulb_powered.png`, `copper_bulb_lit_powered.png`.

Mapping in `shaders/block.properties`:
- Assigns unique IDs for IPBR fallback to torches, lanterns, metals (iron, gold, copper) and foliage when texture pack is partial or absent.

---

## 3. Hardware & Performance Budget
- **GPU Frame Time (`Balanced` profile at 1080p on midrange hardware)**:
  - `shadow`: `<= 0.8 ms`
  - `gbuffers_*`: `<= 0.8 ms`
  - `deferred` (BRDF + Shadow Sampling + Sky): `<= 1.2 ms`
  - `composite*` (World-Space Water, SSR, Godrays, Bloom downsample): `<= 0.6 ms`
  - `final` (Bloom upsample, Tone Mapping, Dithering): `<= 0.4 ms`
  - **Total GPU Budget**: `<= 3.8 ms` ($> 144\text{ fps}$).
- **CPU Render Loop**:
  - **Zero Per-Frame Allocations**: strict prohibition of `new BlockPos`, `new Vec3`, stream lambdas, or Integer boxing inside the tick/render loop.
  - Exclusive use of FastUtil primitive maps (`Reference2IntOpenHashMap`, `Long2IntOpenHashMap`) or thread-safe pools.

---

## 4. Module Acceptance & Release Gate Criteria
1. **Multi-Loader Mod (`ambient-luminescence`)**: `./gradlew build test` (JDK 21) passes across `:common`, `:fabric`, and `:neoforge`, zero loader-specific or client-only leaks in common logic, active Mixin hooks on `LevelRenderer` and Sodium `LightDataAccess`, asynchronous config hot-reload, and zero per-frame heap allocations.
2. **LabPBR 1.3 Resource Pack (`aetheria-labpbr-32x`)**: Valid `texture.properties` (`format=lab-pbr`), strict compliance across all 1,620 texture sets (4,860 RGBA PNGs) and 54 anti-tiling blockstate JSONs verified via `validate_labpbr.py --strict --all`, plus automated 3x3 and lit contact sheets.
3. **Deferred Iris Shader Pack (`luminary-shaders` v2.2.0)**: `#version 330 compatibility` pipeline (`shadow` -> `gbuffers_*` -> `deferred` -> `composite` -> `final`), sRGB-to-Linear conversion, LabPBR 1.3 + IPBR fallback, Multi-Scatter GGX energy compensation, absolute world-space foliage shadow synchronization, world-space water caustic solar projection, view-invariant hand and entity environment IBL (`dot(R, normalize(upPosition))`), 8-tap screen cavity AO (`AO_QUALITY >= 2`), cotangent 3D normal mapping on hand/entities, rain wetness & splash ripples, world-space Beer-Lambert water with linear depth `-vViewPos.z`, smooth energy-conserving SSR, volumetric clouds & godrays, 5-tap Tent bloom, and AgX / Khronos PBR Neutral tone mapping.
4. **Automated Static & Packaging Gate**: 100% pass rate on `python -m unittest discover -s tests -v` (`test_shaders_static`, `test_contact_sheets`, `test_package_release`) and deterministic archive generation in `dist/`.


