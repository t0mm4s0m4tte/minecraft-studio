"""
Modulo dedicato per la generazione ad alta fedeltà della Lista 2: Minerali (Ores & Raw Metals).
Sostituisce i cerchietti tondi isolati con filoni e grappoli sfaccettati a cristallo incastonati nella roccia.
"""

import os
import math
import random
from generate_vertical_slice import clamp, compute_normal_from_height, write_png_rgba
from organic_noise import (
    SIZE, block_rng, create_toroidal_grid, sample_toroidal_noise, apply_pixelart_hueshift
)

def emit_texture_set(output_dir: str, name: str, albedo, height_grid, spec, normal_strength: float = 2.2):
    sanitized_spec = [(r, g, b, min(a, 254)) for (r, g, b, a) in spec]
    normal = compute_normal_from_height(height_grid, SIZE, SIZE, normal_strength)
    write_png_rgba(os.path.join(output_dir, f"{name}.png"), SIZE, SIZE, albedo)
    write_png_rgba(os.path.join(output_dir, f"{name}_n.png"), SIZE, SIZE, normal)
    write_png_rgba(os.path.join(output_dir, f"{name}_s.png"), SIZE, SIZE, sanitized_spec)

# Generatore cluster di cristalli spigolosi stile Minecraft autentico
def create_ore_clusters(rng: random.Random):
    # 3-4 grappoli di cristallo angolari (non sfere)
    clusters = []
    seeds = [(rng.randint(6, 26), rng.randint(6, 26)) for _ in range(3)]
    gem_pixels = set()
    core_pixels = set()
    
    for sx, sy in seeds:
        for ox in range(-3, 4):
            for oy in range(-3, 4):
                # Distanza Manhattan/Chebyshev per forme poligonali e spigoli vivi
                dist_m = abs(ox) + abs(oy)
                dist_c = max(abs(ox), abs(oy))
                if dist_m <= 3 and dist_c <= 2 and rng.random() > 0.15:
                    px = (sx + ox) % SIZE
                    py = (sy + oy) % SIZE
                    gem_pixels.add((px, py))
                    if dist_m <= 1:
                        core_pixels.add((px, py))
    return gem_pixels, core_pixels

def gen_refined_ore(
    output_dir: str,
    name: str,
    deepslate: bool,
    vein_rgb: tuple,
    vein_highlight_rgb: tuple,
    smoothness: int,
    f0_metal: int,
    emissive: int = 0
):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 4)
    g2 = create_toroidal_grid(rng, 16)
    
    gem_pixels, core_pixels = create_ore_clusters(rng)
    
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    host_base = (58, 60, 68) if deepslate else (124, 124, 124)
    
    for y in range(SIZE):
        for x in range(SIZE):
            detail = sample_toroidal_noise(x, y, g2, 16) * 8
            is_gem = (x, y) in gem_pixels
            is_core = (x, y) in core_pixels
            
            if is_gem:
                if is_core:
                    # Cuore brillante del cristallo/minerale
                    ht = clamp(175 + detail)
                    r, g, b = apply_pixelart_hueshift(vein_highlight_rgb, 0.35, hue_shift_deg=10.0)
                    sm = clamp(smoothness + 20)
                else:
                    # Bordo sfaccettato del cristallo
                    ht = clamp(155 + detail)
                    r, g, b = apply_pixelart_hueshift(vein_rgb, (ht - 140) / 30.0, hue_shift_deg=8.0)
                    sm = smoothness
                f0 = f0_metal
                em = emissive if emissive > 0 else 0
            else:
                # Roccia ospite: strati orizzontali naturali se deepslate, granulosa se pietra
                if deepslate:
                    warp_x = sample_toroidal_noise(x, y, g1, 4) * 3.5
                    layer_val = math.sin((y + warp_x) * 0.8) * 16
                    ht = clamp(128 + layer_val + detail)
                else:
                    ht = clamp(128 + detail * 1.5)
                shade = (ht - 128) / 40.0
                r, g, b = apply_pixelart_hueshift(host_base, shade, hue_shift_deg=8.0)
                sm = 40
                f0 = 16
                em = 0
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, f0, 0, em))
            
    emit_texture_set(output_dir, name, albedo, height, spec, normal_strength=2.3)

def main():
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\tommy\OneDrive\Documenti\Claude\gaming\minecraft-studio\packs\aetheria-labpbr-32x\assets\minecraft\textures\block"
    print("Rigenerazione Lista 2 Minerali in corso...")
    
    ores = [
        # Carbone: nero carbone sfaccettato opaco
        ("coal_ore", False, (40, 40, 44), (70, 70, 78), 85, 20, 0),
        ("deepslate_coal_ore", True, (38, 38, 42), (68, 68, 76), 88, 20, 0),
        # Ferro: metallo grezzo beige-dorato lucente
        ("iron_ore", False, (215, 175, 142), (245, 215, 185), 160, 246, 0),
        ("deepslate_iron_ore", True, (215, 175, 142), (245, 215, 185), 160, 246, 0),
        # Rame: arancio metallico con accenti brillanti
        ("copper_ore", False, (210, 115, 80), (250, 155, 110), 155, 250, 0),
        ("deepslate_copper_ore", True, (210, 115, 80), (250, 155, 110), 155, 250, 0),
        # Oro: giallo brillante puro con forte specularità metallica
        ("gold_ore", False, (252, 210, 50), (255, 240, 120), 200, 252, 0),
        ("deepslate_gold_ore", True, (252, 210, 50), (255, 240, 120), 200, 252, 0),
        # Redstone: cristallo rosso vivo emissivo
        ("redstone_ore", False, (225, 25, 25), (255, 75, 75), 170, 40, 160),
        ("deepslate_redstone_ore", True, (225, 25, 25), (255, 75, 75), 170, 40, 160),
        # Diamante: ciano gemma pura ad altissima lucentezza
        ("diamond_ore", False, (88, 242, 238), (175, 255, 252), 240, 140, 0),
        ("deepslate_diamond_ore", True, (88, 242, 238), (175, 255, 252), 240, 140, 0),
    ]
    
    for name, ds, v_rgb, vh_rgb, sm, f0, em in ores:
        gen_refined_ore(out, name, ds, v_rgb, vh_rgb, sm, f0, em)
        
    print("Tutti i 12 Minerali rigenerati con successo!")

if __name__ == "__main__":
    main()
