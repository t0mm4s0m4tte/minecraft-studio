# CLAUDE.md — minecraft-studio (Synergic Triptych)

High-performance graphics and modding studio for Minecraft built on the Iris + Sodium pipeline.

## Tech Stack
- **Minecraft**: 1.21.1 (Java Edition LTS)
- **Java**: 21 (Temurin-21)
- **Mod Framework**: Architectury Loom (Multi-loader: Fabric 1.21.1 + NeoForge 1.21.1)
- **Shaders Pipeline**: Iris / Sodium GLSL (`#version 330 compatibility`)
- **PBR Standard**: LabPBR 1.3 (`pbr.format = lab_pbr_1_3`)
- **Performance Budget**: `<= 3.8 ms` GPU frame time on `Balanced` profile (default)

## Triptych Architecture
1. **`mods/ambient-luminescence`**: Multi-loader mod for per-entity and held-item dynamic lighting with zero per-frame allocations.
2. **`packs/aetheria-labpbr-32x`**: 32x32 RGBA texture pack with normals, AO, roughness, metallic, and emission channels strictly compliant with LabPBR 1.3.
3. **`shaders/luminary-shaders`**: Native Iris shader pack with TBN normal mapping, dielectric/metallic BRDF, emissive bloom, SSR, volumetric godrays, and 3 performance profiles (`Potato`, `Balanced`, `Cinematic`).

## Operational Commands
```bash
# Validate LabPBR Assets (Strict full 1,620 asset sets --strict --all)
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict --all

# Compile Mod (Fabric + NeoForge)
cd mods/ambient-luminescence
./gradlew build
# On Windows PowerShell if needed:
.\gradlew.bat build

# Run Packager Unit Tests
python -m unittest discover -s tests -v

# Build Release Distribution (.zip / .jar in dist/)
python scripts/package_release.py --skip-gradle
```

## Architecture & Specialized Guidelines
For technical contracts and design specifications, refer to:
- `docs/TECHNICAL_CONTRACT.md` (SSoT Architecture Contract)
- `CHANGELOG.md` (Release history and changelog)

