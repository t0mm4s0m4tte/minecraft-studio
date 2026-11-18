"""
Generatore organico completo e tileable per Aetheria LabPBR 32x (60/60 blocchi).
Sostituisce i pattern sinusoidali regolari con noise organico toroidale (fBm + Worley),
hue-shifting cromatico stile vanilla enhanced e Micro-Roughness Breakup LabPBR 1.3.
"""

import os
import math
import json
import random
from generate_vertical_slice import clamp, compute_normal_from_height, write_png_rgba
from organic_noise import (
    SIZE, block_rng, create_toroidal_grid, sample_fbm, sample_toroidal_noise,
    sample_toroidal_worley, apply_pixelart_hueshift
)

def emit_texture_set(output_dir: str, name: str, albedo, height_grid, spec, normal_strength: float = 1.8):
    sanitized_spec = [(r, g, b, min(a, 254)) for (r, g, b, a) in spec]
    normal = compute_normal_from_height(height_grid, SIZE, SIZE, normal_strength)
    write_png_rgba(os.path.join(output_dir, f"{name}.png"), SIZE, SIZE, albedo)
    write_png_rgba(os.path.join(output_dir, f"{name}_n.png"), SIZE, SIZE, normal)
    write_png_rgba(os.path.join(output_dir, f"{name}_s.png"), SIZE, SIZE, sanitized_spec)

# ---------------------------------------------------------------------------
# 1. LEGNI ORGANICI (Corteccia asimmetrica tileable, no righe parallele)
# ---------------------------------------------------------------------------
def gen_organic_log_side(output_dir: str, name: str, bark_rgb: tuple, furrow_rgb: tuple, lenticels: bool = False):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 4)
    g2 = create_toroidal_grid(rng, 8)
    g3 = create_toroidal_grid(rng, 16)
    
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    
    for y in range(SIZE):
        for x in range(SIZE):
            # Solchi verticali organici distorciti dal rumore 2D toroidale
            warp = sample_toroidal_noise(x, y, g1, 4) * 4.5
            grain = sample_fbm(x + warp, y, [g1, g2, g3], octaves=3)
            ridge = math.sin((x + warp) * 0.9 + grain * 2.2)
            
            is_lenticel = lenticels and (abs(sample_toroidal_noise(x * 2, y * 3, g2, 8)) > 0.6)
            
            if is_lenticel:
                ht = 155
                r, g, b = clamp(bark_rgb[0] + 55), clamp(bark_rgb[1] + 45), clamp(bark_rgb[2] + 45)
                sm = 45
            elif ridge < -0.2:
                # Fessura corteccia
                ht = clamp(75 + grain * 20)
                depth_ratio = (ht - 128) / 60.0
                r, g, b = apply_pixelart_hueshift(furrow_rgb, depth_ratio, hue_shift_deg=10.0)
                sm = clamp(26 + grain * 8)
            else:
                # Rilievo corteccia
                ht = clamp(135 + ridge * 22 + grain * 14)
                shade = (ht - 128) / 50.0
                r, g, b = apply_pixelart_hueshift(bark_rgb, shade, hue_shift_deg=12.0)
                sm = clamp(38 + ridge * 12 + grain * 10)
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0)) # Dielettrico
            
    emit_texture_set(output_dir, name, albedo, height, spec, normal_strength=2.2)

def gen_organic_log_top(output_dir: str, name: str, bark_rgb: tuple, wood_rgb: tuple):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 8)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    
    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = abs(x - 15.5), abs(y - 15.5)
            cheb = max(dx, dy)
            rad = math.hypot(dx, dy)
            noise = sample_toroidal_noise(x, y, g1, 8) * 2.5
            
            if cheb >= 13.0:
                ht = clamp(116 + noise * 6)
                r, g, b = apply_pixelart_hueshift(bark_rgb, (ht - 128) / 50.0)
                sm = 30
            else:
                ring = math.sin((rad + noise) * 1.8)
                ht = clamp(132 + ring * 12)
                r, g, b = apply_pixelart_hueshift(wood_rgb, (ht - 128) / 45.0, hue_shift_deg=14.0)
                sm = clamp(58 + ring * 12)
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 1.8)

def gen_organic_planks(output_dir: str, name: str, wood_rgb: tuple, seam_rgb: tuple, smoothness: int):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 8)
    g2 = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    
    for y in range(SIZE):
        plank_idx = y // 8
        ly = y % 8
        v_joint = (plank_idx * 13 + 5) % SIZE
        for x in range(SIZE):
            grain = sample_fbm(x, y, [g1, g2], octaves=2)
            is_seam = (ly == 0 or ly == 7 or x == v_joint)
            
            if is_seam:
                ht = 68
                r, g, b = apply_pixelart_hueshift(seam_rgb, -0.6)
                sm = 22
            else:
                ht = clamp(134 + grain * 16)
                shade = (ht - 128) / 40.0
                r, g, b = apply_pixelart_hueshift(wood_rgb, shade, hue_shift_deg=10.0)
                sm = clamp(smoothness + grain * 12)
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 1.9)

# ---------------------------------------------------------------------------
# 2. PIETRE, DEEPSLATE & TUFF (Voronoi naturale, zero artefatti)
# ---------------------------------------------------------------------------
def gen_organic_stone(output_dir: str, name: str):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 8)
    g2 = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    base_rgb = (126, 126, 126)
    
    for y in range(SIZE):
        for x in range(SIZE):
            fbm = sample_fbm(x, y, [g1, g2], octaves=2)
            ht = clamp(128 + fbm * 26)
            shade = (ht - 128) / 45.0
            r, g, b = apply_pixelart_hueshift(base_rgb, shade, hue_shift_deg=8.0)
            sm = clamp(44 + fbm * 14) # Micro-Roughness Breakup
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 1.7)

def gen_organic_cobblestone(output_dir: str, name: str, mossy: bool = False):
    rng = block_rng(name)
    stones = [(rng.uniform(0, 32), rng.uniform(0, 32)) for _ in range(16)]
    g_detail = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    base_stone = (118, 118, 118)
    moss_color = (78, 118, 54)
    
    for y in range(SIZE):
        for x in range(SIZE):
            d = sample_toroidal_worley(x, y, stones)
            detail = sample_toroidal_noise(x, y, g_detail, 16) * 12
            is_crevice = d > 3.6
            is_moss = mossy and (is_crevice or d < 1.4 and rng.random() > 0.45)
            
            if is_moss:
                ht = clamp(140 + detail)
                r, g, b = apply_pixelart_hueshift(moss_color, (ht - 128) / 45.0, hue_shift_deg=12.0)
                sm = 24
            elif is_crevice:
                ht = clamp(64 + detail * 0.5)
                r, g, b = apply_pixelart_hueshift(base_stone, -0.65)
                sm = 30
            else:
                ht = clamp(165 - d * 18 + detail)
                r, g, b = apply_pixelart_hueshift(base_stone, (ht - 128) / 40.0)
                sm = clamp(52 + detail * 0.6)
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 2.4)

def gen_organic_deepslate(output_dir: str, name: str):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 4)
    g2 = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    base_rgb = (54, 56, 62)
    
    for y in range(SIZE):
        for x in range(SIZE):
            layer = math.sin(y * 0.45 + sample_toroidal_noise(x, y, g1, 4) * 1.5)
            detail = sample_toroidal_noise(x, y, g2, 16) * 12
            ht = clamp(128 + layer * 22 + detail)
            shade = (ht - 128) / 40.0
            r, g, b = apply_pixelart_hueshift(base_rgb, shade, hue_shift_deg=10.0)
            sm = clamp(52 + detail * 0.5)
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 2.1)

# ---------------------------------------------------------------------------
# 3. MINERALI FEDELI AL VANILLA (Vene organiche su pietra/deepslate)
# ---------------------------------------------------------------------------
def gen_organic_ore(
    output_dir: str,
    name: str,
    deepslate: bool,
    vein_rgb: tuple,
    smoothness: int,
    f0_metal: int,
    emissive: int = 0
):
    rng = block_rng(name)
    gems = [(rng.uniform(4, 28), rng.uniform(4, 28)) for _ in range(6)]
    g1 = create_toroidal_grid(rng, 8)
    g2 = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    host_base = (54, 56, 62) if deepslate else (124, 124, 124)
    
    for y in range(SIZE):
        for x in range(SIZE):
            d = sample_toroidal_worley(x, y, gems)
            is_gem = d < 2.5
            detail = sample_toroidal_noise(x, y, g2, 16) * 10
            
            if is_gem:
                ht = clamp(168 - d * 14 + detail)
                shade = (ht - 140) / 35.0
                r, g, b = apply_pixelart_hueshift(vein_rgb, shade, hue_shift_deg=14.0)
                sm = clamp(smoothness + detail * 0.5)
                f0 = f0_metal
                em = emissive if emissive > 0 else 0
            else:
                ht = clamp(126 + detail * 1.5)
                shade = (ht - 128) / 40.0
                r, g, b = apply_pixelart_hueshift(host_base, shade, hue_shift_deg=8.0)
                sm = 44
                f0 = 16
                em = 0
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, f0, 0, em))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 2.2)

# ---------------------------------------------------------------------------
# DISPATCH & REGENERAZIONE COMPLETA (Tutti i 60 blocchi)
# ---------------------------------------------------------------------------
def run_full_organic_regeneration(output_dir: str):
    import generate_mvp_60
    import generate_vertical_slice
    
    print("[ORGANIC REGEN] Inizio rigenerazione ad alta fedeltà LabPBR 1.3...")
    
    # Aggiorna Vertical Slice (10 blocchi hero)
    gen_organic_stone(output_dir, "stone")
    gen_organic_cobblestone(output_dir, "cobblestone", mossy=False)
    gen_organic_planks(output_dir, "oak_planks", (168, 130, 80), (105, 75, 42), 62)
    gen_organic_deepslate(output_dir, "deepslate")
    gen_organic_ore(output_dir, "iron_ore", False, (216, 178, 146), 154, 245)
    
    # 5 blocchi trial/lights da vertical slice
    generate_vertical_slice.generate_textures(output_dir)
    
    # Rigenera i blocchi mancanti col nuovo generatore organico
    gen_organic_cobblestone(output_dir, "mossy_cobblestone", mossy=True)
    
    # Legni organici
    woods = [
        ("spruce_log", (68, 48, 28), (42, 28, 16), False),
        ("dark_oak_log", (56, 40, 26), (34, 24, 14), False),
        ("cherry_log", (64, 40, 48), (40, 24, 30), True),
        ("oak_log", (112, 86, 54), (76, 56, 34), False),
    ]
    for wname, brgb, frgb, lent in woods:
        gen_organic_log_side(output_dir, wname, brgb, frgb, lent)
        
    tops = [
        ("oak_log_top", (106, 80, 50), (174, 138, 88)),
        ("spruce_log_top", (64, 44, 26), (124, 88, 54)),
        ("dark_oak_log_top", (54, 38, 24), (88, 62, 38)),
        ("cherry_log_top", (60, 38, 46), (224, 154, 164)),
    ]
    for tname, brgb, wrgb in tops:
        gen_organic_log_top(output_dir, tname, brgb, wrgb)
        
    planks = [
        ("spruce_planks", (122, 88, 52), (72, 48, 26), 64),
        ("dark_oak_planks", (72, 48, 26), (42, 26, 14), 72),
        ("cherry_planks", (230, 182, 176), (170, 122, 120), 76),
    ]
    for pname, wrgb, srgb, sm in planks:
        gen_organic_planks(output_dir, pname, wrgb, srgb, sm)
        
    # Rigenera tutti gli altri blocchi tramite generate_mvp_60
    generate_mvp_60.main()
    print("[ORGANIC REGEN] Rigenerazione completata con successo!")

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\tommy\OneDrive\Documenti\Claude\gaming\minecraft-studio\packs\aetheria-labpbr-32x\assets\minecraft\textures\block"
    run_full_organic_regeneration(out)
