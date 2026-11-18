"""
Fusione perfetta Lista 2 (Minerali) sulla roccia esatta della Lista 1 (Stone & Deepslate).
Garantisce coerenza cromatica e materica al 100%: il fondo dei minerali e' generato
usando la stessa identica formula e grana della pietra e dell'ardesia della Lista 1.
"""

import os
import math
import random
from generate_vertical_slice import clamp, compute_normal_from_height, write_png_rgba
from organic_noise import (
    SIZE, block_rng, create_toroidal_grid, sample_toroidal_noise, apply_pixelart_hueshift
)
from refine_ores_pack import create_ore_clusters

def emit_texture_set(output_dir: str, name: str, albedo, height_grid, spec, normal_strength: float = 2.1):
    sanitized_spec = [(r, g, b, min(a, 254)) for (r, g, b, a) in spec]
    normal = compute_normal_from_height(height_grid, SIZE, SIZE, normal_strength)
    write_png_rgba(os.path.join(output_dir, f"{name}.png"), SIZE, SIZE, albedo)
    write_png_rgba(os.path.join(output_dir, f"{name}_n.png"), SIZE, SIZE, normal)
    write_png_rgba(os.path.join(output_dir, f"{name}_s.png"), SIZE, SIZE, sanitized_spec)

def gen_coherent_ore(
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
    
    # BASI ESATTE DELLA LISTA 1:
    # Stone della Lista 1: (124, 124, 124) con micro-variazione d'ombra
    # Deepslate della Lista 1: (58, 60, 68) con onde orizzontali y
    base_stone_rgb = (124, 124, 124)
    base_deepslate_rgb = (58, 60, 68)
    
    for y in range(SIZE):
        for x in range(SIZE):
            detail = sample_toroidal_noise(x, y, g2, 16) * 8
            is_gem = (x, y) in gem_pixels
            is_core = (x, y) in core_pixels
            
            if is_gem:
                if is_core:
                    # Cuore sfaccettato del minerale
                    ht = clamp(170 + detail)
                    r, g, b = apply_pixelart_hueshift(vein_highlight_rgb, 0.32, hue_shift_deg=8.0)
                    sm = clamp(smoothness + 18)
                else:
                    # Bordo del filone incastonato
                    ht = clamp(152 + detail)
                    r, g, b = apply_pixelart_hueshift(vein_rgb, (ht - 140) / 32.0, hue_shift_deg=8.0)
                    sm = smoothness
                f0 = f0_metal
                em = emissive if emissive > 0 else 0
            else:
                # STESSA IDENTICA FORMULA DI ROCCIA OSPITE DELLA LISTA 1
                if deepslate:
                    # Sedimentazione orizzontale coerente con il deepslate Lista 1
                    warp_x = sample_toroidal_noise(x, y, g1, 4) * 3.5
                    layer_val = math.sin((y + warp_x) * 0.8) * 18
                    ht = clamp(128 + layer_val + detail)
                    shade = (ht - 128) / 38.0
                    r, g, b = apply_pixelart_hueshift(base_deepslate_rgb, shade, hue_shift_deg=8.0)
                else:
                    # Pietra coerente con stone Lista 1
                    ht = clamp(128 + detail * 1.5)
                    shade = (ht - 128) / 42.0
                    r, g, b = apply_pixelart_hueshift(base_stone_rgb, shade, hue_shift_deg=8.0)
                sm = 44
                f0 = 16
                em = 0
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, f0, 0, em))
            
    emit_texture_set(output_dir, name, albedo, height, spec, normal_strength=2.1)

def main():
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r"packs\aetheria-labpbr-32x\assets\minecraft\textures\block"
    print("Rigenerazione coerente Lista 2 Minerali sulla base della Lista 1...")

    ores = [
        ("coal_ore", False, (38, 38, 42), (68, 68, 76), 85, 20, 0),
        ("deepslate_coal_ore", True, (38, 38, 42), (68, 68, 76), 88, 20, 0),
        ("iron_ore", False, (215, 175, 142), (245, 215, 185), 160, 246, 0),
        ("deepslate_iron_ore", True, (215, 175, 142), (245, 215, 185), 160, 246, 0),
        ("copper_ore", False, (210, 115, 80), (250, 155, 110), 155, 250, 0),
        ("deepslate_copper_ore", True, (210, 115, 80), (250, 155, 110), 155, 250, 0),
        ("gold_ore", False, (252, 210, 50), (255, 240, 120), 200, 252, 0),
        ("deepslate_gold_ore", True, (252, 210, 50), (255, 240, 120), 200, 252, 0),
        ("redstone_ore", False, (225, 25, 25), (255, 75, 75), 170, 40, 160),
        ("deepslate_redstone_ore", True, (225, 25, 25), (255, 75, 75), 170, 40, 160),
        ("diamond_ore", False, (88, 242, 238), (175, 255, 252), 240, 140, 0),
        ("deepslate_diamond_ore", True, (88, 242, 238), (175, 255, 252), 240, 140, 0),
    ]

    for name, ds, v_rgb, vh_rgb, sm, f0, em in ores:
        gen_coherent_ore(out, name, ds, v_rgb, vh_rgb, sm, f0, em)

    print("Lista 2 Minerali perfettamente allineata alla Lista 1!")

if __name__ == "__main__":
    main()
