"""
Modulo dedicato per la generazione fotorealistica/vanilla-enhanced della Lista 1 (Pietre & Rocce).
Elimina le righe verticali del deepslate, ammorbidisce i cobblestone e crea mattoni con fughe naturali.
"""

import os
import math
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

# 1. COBBLESTONE (Ciottoli morbidi ad incastro naturale)
def gen_refined_cobblestone(output_dir: str, name: str, mossy: bool = False):
    rng = block_rng(name)
    # 24 ciottoli di varie dimensioni sparsi naturalmente
    stones = [(rng.uniform(0, 32), rng.uniform(0, 32)) for _ in range(24)]
    g1 = create_toroidal_grid(rng, 16)
    
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    base_stone = (122, 122, 122)
    moss_base = (84, 128, 58)
    
    for y in range(SIZE):
        for x in range(SIZE):
            d = sample_toroidal_worley(x, y, stones)
            grain = sample_toroidal_noise(x, y, g1, 16) * 10
            is_crevice = d > 2.8
            is_moss = mossy and (is_crevice or (d < 1.8 and rng.random() > 0.5))
            
            if is_moss:
                ht = clamp(138 + grain)
                r, g, b = apply_pixelart_hueshift(moss_base, (ht - 128) / 45.0, hue_shift_deg=12.0)
                sm = 28
            elif is_crevice:
                ht = clamp(72 + grain * 0.4)
                r, g, b = apply_pixelart_hueshift(base_stone, -0.45)
                sm = 32
            else:
                ht = clamp(155 - d * 14 + grain)
                r, g, b = apply_pixelart_hueshift(base_stone, (ht - 128) / 40.0)
                sm = clamp(50 + grain * 0.5)
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 2.0)

# 2. STONE BRICKS (Mattoni con fughe morbide e crepe organiche)
def gen_refined_stone_bricks(output_dir: str, name: str, mossy: bool = False, cracked: bool = False):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    base_rgb = (124, 124, 124)
    moss_rgb = (82, 126, 56)
    
    # Mappa crepe frastagliata
    crack_map = set()
    if cracked:
        cx, cy = 16, 4
        for _ in range(35):
            crack_map.add((cx % SIZE, cy % SIZE))
            crack_map.add(((cx + 1) % SIZE, cy % SIZE))
            cx += rng.choice([-1, 0, 1])
            cy += rng.choice([0, 1, 1, 2])
            
    for y in range(SIZE):
        row = y // 8
        is_h_seam = (y % 8 == 0)
        v_offset = 8 if (row % 2 == 1) else 0
        
        for x in range(SIZE):
            is_v_seam_pixel = ((x + v_offset) % 16 == 0)
            is_mortar = is_h_seam or is_v_seam_pixel
            grain = sample_toroidal_noise(x, y, g1, 16) * 12
            is_crack = (x, y) in crack_map
            is_moss = mossy and (is_mortar or abs(grain) > 6)
            
            if is_crack:
                ht = 55
                r, g, b = apply_pixelart_hueshift(base_rgb, -0.65)
                sm = 20
            elif is_moss:
                ht = clamp(134 + grain)
                r, g, b = apply_pixelart_hueshift(moss_rgb, (ht - 128) / 45.0)
                sm = 26
            elif is_mortar:
                ht = 78
                r, g, b = apply_pixelart_hueshift(base_rgb, -0.38) # Fuga morbida, non nera
                sm = 30
            else:
                ht = clamp(142 + grain)
                r, g, b = apply_pixelart_hueshift(base_rgb, (ht - 128) / 42.0)
                sm = clamp(54 + grain * 0.4)
                
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 1.9)

# 3. DEEPSLATE (Stratificazione orizzontale di ardesia, no righe verticali)
def gen_refined_deepslate(output_dir: str, name: str):
    rng = block_rng(name)
    g1 = create_toroidal_grid(rng, 4)
    g2 = create_toroidal_grid(rng, 16)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    base_rgb = (58, 60, 68) # Ardesia con riflesso grigio-bluastro
    
    for y in range(SIZE):
        for x in range(SIZE):
            warp_x = sample_toroidal_noise(x, y, g1, 4) * 3.5
            layer_val = math.sin((y + warp_x) * 0.8) * 18
            detail = sample_toroidal_noise(x, y, g2, 16) * 8
            ht = clamp(128 + layer_val + detail)
            shade = (ht - 128) / 38.0
            r, g, b = apply_pixelart_hueshift(base_rgb, shade, hue_shift_deg=8.0)
            sm = clamp(52 + detail * 0.4)
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
            
    emit_texture_set(output_dir, name, albedo, height, spec, 2.0)

def main():
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\tommy\OneDrive\Documenti\Claude\gaming\minecraft-studio\packs\aetheria-labpbr-32x\assets\minecraft\textures\block"
    print("Rifinitura Lista 1 Pietre in corso...")
    gen_refined_cobblestone(out, "cobblestone", mossy=False)
    gen_refined_cobblestone(out, "mossy_cobblestone", mossy=True)
    gen_refined_stone_bricks(out, "stone_bricks", mossy=False, cracked=False)
    gen_refined_stone_bricks(out, "mossy_stone_bricks", mossy=True, cracked=False)
    gen_refined_stone_bricks(out, "cracked_stone_bricks", mossy=False, cracked=True)
    gen_refined_deepslate(out, "deepslate")
    print("Lista 1 Pietre rigenerata!")

if __name__ == "__main__":
    main()
