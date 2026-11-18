"""
Generatore deterministico ad alta fedeltà di texture Vertical Slice 32x32 per Aetheria LabPBR 1.3.
Produce 10 set completi (albedo.png, _n.png, _s.png) per:
stone, cobblestone, oak_planks, deepslate, iron_ore,
copper_block, copper_bulb, copper_bulb_lit, torch, lantern.

Specifiche LabPBR 1.3:
- Albedo: Colore base RGBA 8-bit con micro-variazione realistica.
- Normal map (_n):
  - R: Tangent Normal X (128 = 0.0)
  - G: Tangent Normal Y (128 = 0.0)
  - B: Ambient Occlusion (0..255, tipicamente 180..255 nelle fessure)
  - A: Height Map (0..255, 128 = livello zero, 255 = rilievo max, 0 = solco profondo)
- Specular map (_s):
  - R: Smoothness (0..255) -> Perceptual Roughness = (1.0 - Smoothness)^2
  - G: Metallic / Reflectance F0 (0..229 = Dielettrico F0 0.00..0.04; 230..255 = Metallo)
  - B: Porosity / SSS (0 = non poroso, non trans-illuminato)
  - A: Emissività (0 = non emissivo, 1..254 = emissivo; 255 è RISERVATO e vietato!)
"""

import os
import math
import struct
import zlib
import random

def write_png_rgba(filepath, width, height, pixels):
    """Scrive un file PNG RGBA a 8-bit senza alcuna dipendenza esterna."""
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

    raw_data = bytearray()
    for y in range(height):
        raw_data.append(0) # Filtro None
        for x in range(width):
            r, g, b, a = pixels[y * width + x]
            raw_data.extend((r, g, b, a))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw_data))) + chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(png)

def clamp(val, min_v=0, max_v=255):
    return max(min_v, min(max_v, int(round(val))))

def compute_normal_from_height(height_grid, w=32, h=32, strength=1.5):
    """Calcola la normale tangente (R, G, B=AO, A=Height) tramite sobel filter su height_grid."""
    normal_pixels = []
    for y in range(h):
        for x in range(w):
            left = height_grid[y][(x - 1) % w]
            right = height_grid[y][(x + 1) % w]
            up = height_grid[(y - 1) % h][x]
            down = height_grid[(y + 1) % h][x]
            center = height_grid[y][x]

            # Differenze spaziali (dx, dy)
            dx = (right - left) / 255.0 * strength
            dy = (down - up) / 255.0 * strength
            dz = 1.0

            # Normalizzazione
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            nx = dx / length
            ny = dy / length
            nz = dz / length

            # Mappatura su 0..255 per R e G (128 = 0)
            r = clamp((nx * 0.5 + 0.5) * 255.0)
            g = clamp((ny * 0.5 + 0.5) * 255.0)

            # AO calcolata in base alla depressione locale
            curvature = (left + right + up + down) / 4.0 - center
            ao_factor = max(0.0, min(1.0, 1.0 - curvature / 60.0))
            ao = clamp(180 + ao_factor * 75)

            height_val = clamp(center)
            normal_pixels.append((r, g, ao, height_val))

    return normal_pixels

def generate_textures(output_dir):
    random.seed(42) # Riproducibilità assoluta deterministica
    w, h = 32, 32

    # 1. STONE
    print("Generating stone...")
    height_stone = [[128 + int(14 * math.sin(x*0.6) * math.cos(y*0.6) + random.uniform(-6, 6)) for x in range(w)] for y in range(h)]
    albedo_stone = []
    spec_stone = []
    for y in range(h):
        for x in range(w):
            var = height_stone[y][x] - 128
            c = clamp(125 + var * 0.8)
            albedo_stone.append((c, c, c, 255))
            # Pietra: Smoothness bassa (ruvida ~45), Dielettrico F0 tipico (G=16 ~ 0.04), no emissivo
            smooth = clamp(45 + var * 0.3)
            spec_stone.append((smooth, 16, 0, 0))
    normal_stone = compute_normal_from_height(height_stone, w, h, 1.8)
    write_png_rgba(os.path.join(output_dir, "stone.png"), w, h, albedo_stone)
    write_png_rgba(os.path.join(output_dir, "stone_n.png"), w, h, normal_stone)
    write_png_rgba(os.path.join(output_dir, "stone_s.png"), w, h, spec_stone)

    # 2. COBBLESTONE
    print("Generating cobblestone...")
    # Matrice a ciottoli con solchi marcati
    height_cobble = [[128 for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            cell_x = (x // 8) * 8 + 4
            cell_y = (y // 8) * 8 + 4
            dist = math.sqrt((x - cell_x)**2 + (y - cell_y)**2)
            noise = random.uniform(-8, 8)
            if dist > 3.8:
                height_cobble[y][x] = clamp(60 + noise) # Fessura profonda
            else:
                height_cobble[y][x] = clamp(160 - dist * 8 + noise) # Rilievo sasso

    albedo_cobble = []
    spec_cobble = []
    for y in range(h):
        for x in range(w):
            ht = height_cobble[y][x]
            if ht < 90:
                c = clamp(65 + random.uniform(-5, 5))
            else:
                c = clamp(110 + (ht - 128) * 0.7 + random.uniform(-6, 6))
            albedo_cobble.append((c, c, c, 255))
            smooth = clamp(35 if ht < 90 else 55)
            spec_cobble.append((smooth, 16, 0, 0))
    normal_cobble = compute_normal_from_height(height_cobble, w, h, 2.5)
    write_png_rgba(os.path.join(output_dir, "cobblestone.png"), w, h, albedo_cobble)
    write_png_rgba(os.path.join(output_dir, "cobblestone_n.png"), w, h, normal_cobble)
    write_png_rgba(os.path.join(output_dir, "cobblestone_s.png"), w, h, spec_cobble)

    # 3. OAK_PLANKS
    print("Generating oak_planks...")
    height_planks = [[128 for _ in range(w)] for _ in range(h)]
    albedo_planks = []
    spec_planks = []
    for y in range(h):
        plank_idx = y // 8
        is_seam = (y % 8 == 0 or y % 8 == 7)
        for x in range(w):
            grain = int(8 * math.sin(x * 0.4 + plank_idx * 1.5) + random.uniform(-3, 3))
            if is_seam:
                height_planks[y][x] = 70
                albedo_planks.append((90, 60, 30, 255))
                spec_planks.append((25, 16, 0, 0))
            else:
                height_planks[y][x] = clamp(130 + grain)
                r = clamp(165 + grain * 0.8)
                g = clamp(125 + grain * 0.6)
                b = clamp(75 + grain * 0.4)
                albedo_planks.append((r, g, b, 255))
                smooth = clamp(65 + grain * 0.5)
                spec_planks.append((smooth, 16, 0, 0)) # Legno: F0 dielettrico 16, no metallico, no emissivo
    normal_planks = compute_normal_from_height(height_planks, w, h, 1.8)
    write_png_rgba(os.path.join(output_dir, "oak_planks.png"), w, h, albedo_planks)
    write_png_rgba(os.path.join(output_dir, "oak_planks_n.png"), w, h, normal_planks)
    write_png_rgba(os.path.join(output_dir, "oak_planks_s.png"), w, h, spec_planks)

    # 4. DEEPSLATE
    print("Generating deepslate...")
    height_deep = [[128 for _ in range(w)] for _ in range(h)]
    albedo_deep = []
    spec_deep = []
    for y in range(h):
        layer = (y // 4) % 2
        for x in range(w):
            wave = int(12 * math.cos((x + y*0.5) * 0.4) + random.uniform(-4, 4))
            ht = clamp(120 + (15 if layer == 0 else -15) + wave)
            height_deep[y][x] = ht
            c = clamp(55 + (ht - 128) * 0.5)
            albedo_deep.append((c, c + 2, c + 4, 255))
            spec_deep.append((50, 16, 0, 0))
    normal_deep = compute_normal_from_height(height_deep, w, h, 2.0)
    write_png_rgba(os.path.join(output_dir, "deepslate.png"), w, h, albedo_deep)
    write_png_rgba(os.path.join(output_dir, "deepslate_n.png"), w, h, normal_deep)
    write_png_rgba(os.path.join(output_dir, "deepslate_s.png"), w, h, spec_deep)

    # 5. IRON_ORE
    print("Generating iron_ore...")
    height_iron = [[128 + int(random.uniform(-6, 6)) for _ in range(w)] for _ in range(h)]
    # Aggiungi vene di ferro
    iron_mask = [[False for _ in range(w)] for _ in range(h)]
    vein_centers = [(10, 10), (12, 11), (22, 18), (20, 20), (14, 24)]
    for y in range(h):
        for x in range(w):
            for vx, vy in vein_centers:
                if math.sqrt((x - vx)**2 + (y - vy)**2) < 3.2:
                    iron_mask[y][x] = True
                    height_iron[y][x] = 150 + int(random.uniform(-3, 6))

    albedo_iron = []
    spec_iron = []
    for y in range(h):
        for x in range(w):
            if iron_mask[y][x]:
                # Vena minerale ferro grezzo / metallo
                r = clamp(210 + random.uniform(-8, 8))
                g = clamp(170 + random.uniform(-8, 8))
                b = clamp(140 + random.uniform(-8, 8))
                albedo_iron.append((r, g, b, 255))
                # Metallo puro: G >= 230 (245 = Iron Specular F0), Smoothness alta (150)
                spec_iron.append((150, 245, 0, 0))
            else:
                # Pietra circostante
                c = clamp(120 + random.uniform(-6, 6))
                albedo_iron.append((c, c, c, 255))
                spec_iron.append((45, 16, 0, 0))
    normal_iron = compute_normal_from_height(height_iron, w, h, 2.2)
    write_png_rgba(os.path.join(output_dir, "iron_ore.png"), w, h, albedo_iron)
    write_png_rgba(os.path.join(output_dir, "iron_ore_n.png"), w, h, normal_iron)
    write_png_rgba(os.path.join(output_dir, "iron_ore_s.png"), w, h, spec_iron)

    # 6. COPPER_BLOCK
    print("Generating copper_block...")
    height_copper = [[128 + int(8 * math.sin(x*0.4) + random.uniform(-3, 3)) for x in range(w)] for y in range(h)]
    albedo_copper = []
    spec_copper = []
    for y in range(h):
        for x in range(w):
            # Tonalità rame metallico lucido
            r = clamp(195 + random.uniform(-5, 5))
            g = clamp(105 + random.uniform(-5, 5))
            b = clamp(80 + random.uniform(-5, 5))
            albedo_copper.append((r, g, b, 255))
            # Blocco di rame: Smoothness medio-alta (140), Metallic totale (G=250), Emissivo=0
            spec_copper.append((140, 250, 0, 0))
    normal_copper = compute_normal_from_height(height_copper, w, h, 1.4)
    write_png_rgba(os.path.join(output_dir, "copper_block.png"), w, h, albedo_copper)
    write_png_rgba(os.path.join(output_dir, "copper_block_n.png"), w, h, normal_copper)
    write_png_rgba(os.path.join(output_dir, "copper_block_s.png"), w, h, spec_copper)

    # 7. COPPER_BULB (spento)
    print("Generating copper_bulb...")
    height_cbulb = [[128 for _ in range(w)] for _ in range(h)]
    albedo_cbulb = []
    spec_cbulb = []
    for y in range(h):
        for x in range(w):
            is_frame = (x < 4 or x >= 28 or y < 4 or y >= 28)
            dist_core = math.sqrt((x - 16)**2 + (y - 16)**2)
            if is_frame:
                height_cbulb[y][x] = 160
                albedo_cbulb.append((190, 100, 75, 255))
                spec_cbulb.append((130, 245, 0, 0)) # Telaio rame
            elif dist_core < 9:
                height_cbulb[y][x] = 110 # Rientranza bulbo
                # Filamento/vetro spento
                albedo_cbulb.append((85, 70, 50, 255))
                spec_cbulb.append((180, 20, 0, 0)) # Vetro spento (Smooth=180, Dielettrico, Emissivo=0)
            else:
                height_cbulb[y][x] = 140
                albedo_cbulb.append((160, 90, 65, 255))
                spec_cbulb.append((120, 240, 0, 0))
    normal_cbulb = compute_normal_from_height(height_cbulb, w, h, 2.0)
    write_png_rgba(os.path.join(output_dir, "copper_bulb.png"), w, h, albedo_cbulb)
    write_png_rgba(os.path.join(output_dir, "copper_bulb_n.png"), w, h, normal_cbulb)
    write_png_rgba(os.path.join(output_dir, "copper_bulb_s.png"), w, h, spec_cbulb)

    # 8. COPPER_BULB_LIT (acceso)
    print("Generating copper_bulb_lit...")
    height_cbulb_lit = [row[:] for row in height_cbulb]
    albedo_cbulb_lit = []
    spec_cbulb_lit = []
    for y in range(h):
        for x in range(w):
            is_frame = (x < 4 or x >= 28 or y < 4 or y >= 28)
            dist_core = math.sqrt((x - 16)**2 + (y - 16)**2)
            if is_frame:
                albedo_cbulb_lit.append((205, 115, 85, 255))
                spec_cbulb_lit.append((130, 245, 0, 0))
            elif dist_core < 9:
                # Bulbo acceso: albedo brillante arancio-ambra
                albedo_cbulb_lit.append((255, 220, 140, 255))
                # Emissivo LabPBR 1.3: A = 220 (valido 0..254!)
                spec_cbulb_lit.append((200, 20, 0, 220))
            else:
                albedo_cbulb_lit.append((185, 105, 75, 255))
                # Luce di riflesso sul bordo interno
                spec_cbulb_lit.append((140, 240, 0, 40))
    normal_cbulb_lit = compute_normal_from_height(height_cbulb_lit, w, h, 2.0)
    write_png_rgba(os.path.join(output_dir, "copper_bulb_lit.png"), w, h, albedo_cbulb_lit)
    write_png_rgba(os.path.join(output_dir, "copper_bulb_lit_n.png"), w, h, normal_cbulb_lit)
    write_png_rgba(os.path.join(output_dir, "copper_bulb_lit_s.png"), w, h, spec_cbulb_lit)

    # 9. TORCH
    print("Generating torch...")
    height_torch = [[0 for _ in range(w)] for _ in range(h)]
    albedo_torch = []
    spec_torch = []
    for y in range(h):
        for x in range(w):
            is_stick = (13 <= x <= 18 and 10 <= y <= 31)
            is_head = (12 <= x <= 19 and 4 <= y <= 9)
            is_flame = (11 <= x <= 20 and 0 <= y <= 7)

            if is_flame:
                height_torch[y][x] = 160
                albedo_torch.append((255, 200, 50, 255))
                # Fiamma: Emissività alta (240), dielettrico, A <= 254
                spec_torch.append((100, 16, 0, 240))
            elif is_head:
                height_torch[y][x] = 145
                albedo_torch.append((50, 40, 30, 255)) # Carbone
                spec_torch.append((30, 16, 0, 80)) # Brace parzialmente emissiva
            elif is_stick:
                height_torch[y][x] = 135
                albedo_torch.append((130, 95, 55, 255)) # Legno
                spec_torch.append((45, 16, 0, 0))
            else:
                # Pixel trasparente esterno (torch è un modello 3D / cross)
                height_torch[y][x] = 0
                albedo_torch.append((0, 0, 0, 0))
                spec_torch.append((0, 0, 0, 0))
    normal_torch = compute_normal_from_height(height_torch, w, h, 1.5)
    write_png_rgba(os.path.join(output_dir, "torch.png"), w, h, albedo_torch)
    write_png_rgba(os.path.join(output_dir, "torch_n.png"), w, h, normal_torch)
    write_png_rgba(os.path.join(output_dir, "torch_s.png"), w, h, spec_torch)

    # 10. LANTERN
    print("Generating lantern...")
    height_lantern = [[0 for _ in range(w)] for _ in range(h)]
    albedo_lantern = []
    spec_lantern = []
    for y in range(h):
        for x in range(w):
            is_chain_hook = (14 <= x <= 17 and y <= 4)
            is_top_roof = (8 <= x <= 23 and 5 <= y <= 9)
            is_bottom = (8 <= x <= 23 and 25 <= y <= 29)
            is_posts = ((8 <= x <= 10 or 21 <= x <= 23) and 10 <= y <= 24)
            is_metal = is_chain_hook or is_top_roof or is_bottom or is_posts

            is_core_flame = (13 <= x <= 18 and 14 <= y <= 20)
            is_glass = (11 <= x <= 20 and 10 <= y <= 24)

            if is_metal:
                height_lantern[y][x] = 170
                c = clamp(45 + random.uniform(-4, 4))
                albedo_lantern.append((c, c, c, 255))
                # Ferro battuto: G = 235 (Metallo), Smoothness = 90
                spec_lantern.append((90, 235, 0, 0))
            elif is_core_flame:
                height_lantern[y][x] = 140
                albedo_lantern.append((255, 235, 170, 255))
                # Cuore fiamma lanterna: A = 245 emissivo (LabPBR <= 254)
                spec_lantern.append((120, 20, 0, 245))
            elif is_glass:
                height_lantern[y][x] = 120
                albedo_lantern.append((220, 180, 120, 200)) # Vetro illuminato
                spec_lantern.append((210, 20, 0, 70)) # Bagliore diffuso sul vetro
            else:
                height_lantern[y][x] = 0
                albedo_lantern.append((0, 0, 0, 0))
                spec_lantern.append((0, 0, 0, 0))
    normal_lantern = compute_normal_from_height(height_lantern, w, h, 2.0)
    write_png_rgba(os.path.join(output_dir, "lantern.png"), w, h, albedo_lantern)
    write_png_rgba(os.path.join(output_dir, "lantern_n.png"), w, h, normal_lantern)
    write_png_rgba(os.path.join(output_dir, "lantern_s.png"), w, h, spec_lantern)

    print("Vertical slice textures generation complete!")

if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\tommy\OneDrive\Documenti\Claude\gaming\minecraft-studio\packs\aetheria-labpbr-32x\assets\minecraft\textures\block"
    generate_textures(out_dir)
