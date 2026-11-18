# CLAUDE.md — minecraft-studio (Trittico Sinergico)

Studio grafico e modding Minecraft per la pipeline ad alte prestazioni basata su Iris + Sodium.

## Stack Tecnologico
- **Minecraft**: 1.21.1 (Java Edition LTS)
- **Java**: 21 (Temurin-21)
- **Mod Framework**: Architectury Loom (Multi-loader: Fabric 1.21.1 + NeoForge 1.21.1)
- **Shaders Pipeline**: Iris / Sodium GLSL (`#version 330 compatibility`)
- **PBR Standard**: LabPBR 1.3 (`pbr.format = lab_pbr_1_3`)
- **Performance Budget**: `<= 3.8 ms` frame time GPU sul profilo `Balanced` (default)

## Architettura del Trittico
1. **`mods/ambient-luminescence`**: Mod multi-loader per illuminazione dinamica per-entity e held-item con propagazione lag-free e zero allocazioni per-frame.
2. **`packs/aetheria-labpbr-32x`**: Resource pack texture 32x32 RGBA con canali normali, AO, roughness, metallic, emission conformi a LabPBR 1.3.
3. **`shaders/luminary-shaders`**: Shader pack Iris nativo con normal mapping TBN, BRDF dielettrico/metallico, bloom emissivo e profili prestazionali (`Potato`, `Balanced`, `Cinematic`).

## Comandi Operativi
```bash
# Validazione Asset LabPBR (Strict subset)
python packs/aetheria-labpbr-32x/scripts/validate_labpbr.py --strict

# Compilazione Mod (Fabric + NeoForge)
cd mods/ambient-luminescence
./gradlew build
# Su Windows se necessario:
.\gradlew.bat build
```

## Riferimento Agenti Specialisti
Per la guida stilistica, architetturale e review dei ruoli specialistici, fare riferimento ai prompt di studio in:
`C:\Users\tommy\OneDrive\Documenti\Claude\my-office\prompts\` (es. `game-designer.md`, `engineering-software-architect.md`, `technical-artist.md`).
