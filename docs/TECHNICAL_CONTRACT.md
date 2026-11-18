# TECHNICAL ARCHITECTURE CONTRACT (TAC) — MINECRAFT STUDIO SUITE
**Target**: Minecraft Java Edition 1.21.1 (LTS)  
**Spec Version**: 1.1.0-RELEASE  
**Status**: APPROVED & LOCKED (Single Source of Truth - SSoT)  
**Authors**: `mc-pipeline-architect` in collaborazione con `mc-mod-systems-engineer`, `mc-labpbr-texture-artist`, `mc-iris-shader-architect`, `mc-release-qa-gate`.

---

## 1. Matrix di Compatibilità Runtime & Toolchain
- **Minecraft**: 1.21.1 Java Edition
- **Java Virtual Machine**: JDK 21 (Temurin-21 / GraalVM CE 21, toolchain enforced)
- **Mod Architecture**: Architectury Loom multi-loader (`:common`, `:fabric`, `:neoforge`)
- **Fabric Loader**: `>= 0.16.5` (Fabric API `>= 0.100.0+1.21.1`)
- **NeoForge**: `21.1.65+`
- **Graphics Framework**: Sodium `0.6.x` (o `0.5.11+`) + Iris `1.8.x` (o `1.7.x`)
- **PBR Standard**: LabPBR 1.3 Strict (`pbr.format = lab_pbr_1_3`)

---

## 2. Contratto Cross-Layer Trittico (Mod ↔ Resource Pack ↔ Shader Pack)

### 2.1. Buffer di Rendering Iris & Formati HDR (`shaders.properties`)
```properties
pbr.format = lab_pbr_1_3
colortex0.format = RGBA16F
colortex1.format = RGBA16F
colortex2.format = RGBA8
colortex3.format = RGBA16F
```
- **`colortex0`**:
  - G-Buffers stage: Albedo linearizzata `sRGB -> Linear` (`pow(rgb, 2.2)`), Alpha cutout/transparency.
  - Deferred & Composite stage: Scena HDR Linear Light accumulata (Direct + Ambient + Specular + Dynamic Light).
- **`colortex1`**:
  - G-Buffers stage: Normal Vector (RGB in view/tangent space mappato `[-1..1]`) + Material AO nel canale Alpha (o codifica Packed Normal + AO).
- **`colortex2`**:
  - G-Buffers stage: Dati fisici LabPBR 1.3:
    - `R`: Smoothness (`0..255`, $Roughness = (1.0 - S/255.0)^2$)
    - `G`: Reflectance / F0 dielettrico o ID metallo tabellato (`0..229` $\rightarrow F_0 = (G/255)^2$; `230..237` metalli; `255` custom metal)
    - `B`: Porosità / SSS (`0..64` porosità pioggia; `65..255` Subsurface Scattering)
    - `A`: Emissività (`1..254` scala lineare, `0` e `255` spenta)
- **`colortex3`**:
  - Bloom highlights isolati (pre-downsampling mipmap pyramid) + dati ausiliari lightmap.

### 2.2. Protocollo Bridge Luci Dinamiche (`ambient-luminescence` ↔ `luminary-shaders`)
- **Canale Primario (Vanilla & Sodium Pipeline)**:
  - `ambient-luminescence` inietta la luminanza dinamica direttamente in `LightDataAccess` (Sodium) e `LevelRenderer.getLightColor` (Vanilla fallback).
  - Le coordinate sono calcolate in lock-free con snapshot immutabile atomico e dirtying selettivo delle sezioni chunk (`SectionPos`).
- **Canale Secondario (Shader Pack Iris Uniforms)**:
  - Iris espone nativamente `heldBlockLightValue` e `heldBlockLightValue2`.
  - Lo shader pack campiona sia la lightmap vanilla/sodium modulata dal mod (che illumina item a terra, mob e player circostanti), sia gestisce un falloff dinamico locale sui pixel vicini alla camera senza doppie somme di energia.

### 2.3. Nomi Canonici MC 1.21.1 & Mappatura Texture / IPBR
Tutte le texture devono corrispondere ai nomi effettivi del jar vanilla MC 1.21.1:
- `tuff_bricks.png`, `chiseled_tuff.png`, `polished_tuff.png`, `chiseled_tuff_bricks.png` (sostituisce il non-esistente `tuff_tiles`).
- `torch.png` e `soul_torch.png` (usati sia per torcia a terra che a parete; `wall_torch` rimosso).
- `trial_spawner_side_inactive.png`, `trial_spawner_side_active.png` (sostituisce `trial_spawner_side`).
- `crafter_top.png`, `crafter_top_triggered.png`, `crafter_side.png`, `crafter_bottom.png`.
- `copper_bulb.png`, `copper_bulb_lit.png`, `copper_bulb_powered.png`, `copper_bulb_lit_powered.png`.

Mappatura `shaders/block.properties`:
- Assegna ID univoci per fallback IPBR a torce, lanterne, metalli (ferro, oro, rame) e vegetazione quando il texture pack è parziale o assente.

---

## 3. Budget Hardware & Prestazioni
- **Frame time GPU (profilo `Balanced` a 1080p su GPU midrange)**:
  - `shadow`: `<= 0.8 ms`
  - `gbuffers_*`: `<= 0.8 ms`
  - `deferred` (BRDF + Shadow Sampling): `<= 1.2 ms`
  - `composite*` (Acqua world-space, SSR, Bloom downsample): `<= 0.6 ms`
  - `final` (Bloom upsample, AgX Tone Mapping, Dither): `<= 0.4 ms`
  - **Budget Totale GPU**: `<= 3.8 ms` ($> 144\text{ fps}$).
- **CPU Render Loop**:
  - **Zero Allocazioni per-frame**: divieto di `new BlockPos`, `new Vec3`, stream lambda o boxing Integer nel loop di tick/rendering.
  - Uso esclusivo di FastUtil primitive maps (`Reference2IntOpenHashMap`, `Long2IntOpenHashMap`) o pool thread-safe.

---

## 4. Criteri di Accettazione Stadio per Stadio
1. **Stadio 2 (Mod)**: `./gradlew build test` (JDK 21) verde su Fabric e NeoForge, zero riferimenti client in common, Mixin attivi su `LevelRenderer`/Sodium, zero codice morto.
2. **Stadio 3 (Pack)**: Zero sottocartelle spurie in `assets/`, `texture.properties` presente, canali LabPBR 1.3 conformi, `validate_labpbr.py --strict` 100% PASS, test unittari Python verdi.
3. **Stadio 4 (Shader v1.1.0)**: Pipeline Deferred (`deferred.fsh`), linearizzazione sRGB, LabPBR esatto con tabella metalli, Rain Wetness & Dynamic Puddles guidati da porosità `_s.b` (`0..64`), acqua world-space analitica con Beer-Lambert, caustiche subacquee & rifrazione Snell, SSR View-Space con binary refinement & edge fade, Volumetric Godrays con dithering Bayer 4x4, Starfield world-space & `moonPhase`, bloom mipmap + Khronos PBR Neutral tone mapping.
4. **Stadio 5 (QA Gate)**: Tutti e 6 gli assi `>= 8/10`, verdetto `PASS`.
