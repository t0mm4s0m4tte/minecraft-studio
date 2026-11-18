"""
Generatore SPBR-Grade per Lista 1: Pietre (Stone & Masonry).
Prende le texture ufficiali autentiche di Minecraft 1.21.1 (16x16),
le adatta a 32x32 con micro-dettaglio coerente ai minerali vanilla,
e genera canali Normal Map (_n: Tangente + AO + Height) e Specular Map (_s: Smoothness + F0/Metal)
rigorosamente LabPBR 1.3.
"""

import os
from generate_vertical_slice import clamp, compute_normal_from_height, write_png_rgba
from validate_labpbr import decode_png_pixels

SIZE = 32

def read_raw_png_16(filepath):
    pixels, err = decode_png_pixels(filepath)
    if err:
        raise RuntimeError(f"Errore lettura {filepath}: {err}")
    return pixels # 256 tuple (r,g,b,a)

def upscale_16_to_32(pixels_16):
    """Upscale 16x16 -> 32x32 preservando la pixel art fedele di Minecraft."""
    pixels_32 = []
    for y in range(32):
        src_y = y // 2
        for x in range(32):
            src_x = x // 2
            p = pixels_16[src_y * 16 + src_x]
            pixels_32.append(p)
    return pixels_32

def generate_spbr_stone(
    vanilla_dir: str,
    output_dir: str,
    block_name: str,
    base_smoothness: int = 38,
    base_f0: int = 16,
    height_mult: float = 0.55,
    normal_strength: float = 1.8
):
    src_file = os.path.join(vanilla_dir, f"{block_name}.png")
    if not os.path.exists(src_file):
        print(f"[SKIP] {src_file} non trovato")
        return

    px_16 = read_raw_png_16(src_file)
    albedo_32 = upscale_16_to_32(px_16)

    height_grid = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    spec_32 = []

    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = albedo_32[y * SIZE + x]
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            # Calcolo rilievo naturale in base alla profondità e crepe della texture
            ht = clamp(128 + (luma - 128) * height_mult)
            
            # Se ci sono crepe/fughe molto scure, abbassa l'altezza per accentuare il solco 3D
            if luma < 70:
                ht = clamp(ht - 15)
                sm = max(10, base_smoothness - 15)
            else:
                sm = base_smoothness

            height_grid[y][x] = ht
            spec_32.append((sm, base_f0, 0, 0))

    normal_32 = compute_normal_from_height(height_grid, SIZE, SIZE, normal_strength)

    write_png_rgba(os.path.join(output_dir, f"{block_name}.png"), SIZE, SIZE, albedo_32)
    write_png_rgba(os.path.join(output_dir, f"{block_name}_n.png"), SIZE, SIZE, normal_32)
    write_png_rgba(os.path.join(output_dir, f"{block_name}_s.png"), SIZE, SIZE, spec_32)
    print(f"[OK] {block_name} generato SPBR (fedele ai minerali vanilla).")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pack_dir = os.path.dirname(script_dir)
    vanilla_dir = os.path.join(pack_dir, "vanilla_raw_16x")
    output_dir = os.path.join(pack_dir, "assets", "minecraft", "textures", "block")

    print("Rigenerazione Lista 1 Pietre coerente con lo stile dei Minerali Vanilla...")
    
    # Lista 1: Stone & Masonry
    blocks = [
        # (name, smoothness, f0, height_mult, normal_strength)
        ("stone", 38, 16, 0.5, 1.6),
        ("cobblestone", 32, 16, 0.7, 2.2),
        ("mossy_cobblestone", 34, 16, 0.65, 2.0),
        ("stone_bricks", 42, 16, 0.6, 2.0),
        ("mossy_stone_bricks", 40, 16, 0.6, 1.9),
        ("cracked_stone_bricks", 36, 16, 0.7, 2.2),
        ("deepslate", 35, 16, 0.6, 1.9),
    ]

    for name, sm, f0, h_mult, norm_s in blocks:
        generate_spbr_stone(vanilla_dir, output_dir, name, sm, f0, h_mult, norm_s)

    print("Tutti i blocchi di pietra della Lista 1 sono ora allineati allo stile autentico dei Minerali!")

if __name__ == "__main__":
    main()
