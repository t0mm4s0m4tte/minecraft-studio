"""
Contact sheet generator for visual QA - Aetheria LabPBR 32x.
Generates:
1. contact_sheet_3x3.png: 3x2 grid of panels repeating albedo 32x32 in a 3x3 mosaic (96x96 px scaled 2x -> 192x192 px)
   with text label on top over background #16181D to check for seamless tiling.
2. contact_sheet_lit.png: 3x2 grid of panels synthetically lit by light direction
   normalize((0.65, 0.70, 0.55)) using _n.png (normals X/Y, reconstructed Z, AO in B) and
   _s.png (smoothness + specular highlights on metals), scaled 4x (-> 128x128 px per panel)
   over background #16181D.
"""

import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw

CORE_BLOCKS = [
    "stone",
    "cobblestone",
    "deepslate",
    "oak_planks",
    "tuff_bricks",
    "copper_block"
]

BG_COLOR = (22, 24, 29, 255) # #16181D
TEXT_COLOR = (220, 224, 230, 255)
PANEL_BORDER_COLOR = (45, 50, 60, 255)

def render_lit_texture(base_img: Image.Image, norm_img: Image.Image, spec_img: Image.Image) -> Image.Image:
    base = base_img.convert("RGBA")
    norm = norm_img.convert("RGBA")
    spec = spec_img.convert("RGBA")

    w, h = base.size
    # Light direction: normalize((0.65, 0.70, 0.55))
    lx, ly, lz = 0.65, 0.70, 0.55
    l_len = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / l_len, ly / l_len, lz / l_len

    # View direction: (0, 0, 1) pointing straight towards screen
    vx, vy, vz = 0.0, 0.0, 1.0

    # Halfway vector H = normalize(L + V)
    hx, hy, hz = lx + vx, ly + vy, lz + vz
    h_len = math.sqrt(hx * hx + hy * hy + hz * hz)
    hx, hy, hz = hx / h_len, hy / h_len, hz / h_len

    lit_out = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    base_pix = base.load()
    norm_pix = norm.load()
    spec_pix = spec.load()
    out_pix = lit_out.load()

    for y in range(h):
        for x in range(w):
            br, bg, bb, ba = base_pix[x, y]
            nr, ng, nb, na = norm_pix[x, y]
            sr, sg, sb, sa = spec_pix[x, y]

            # LabPBR normal map: R = nx [-1..1], G = ny [-1..1], B = AO [0..1]
            nx = (nr / 255.0) * 2.0 - 1.0
            ny = (ng / 255.0) * 2.0 - 1.0
            # LabPBR Y axis is up or inverted depending on conventions; in MC OpenGL Y+ is up
            nz_sq = max(0.0, 1.0 - nx * nx - ny * ny)
            nz = math.sqrt(nz_sq)
            ao = nb / 255.0

            # LabPBR specular map: R = smoothness, G = f0 / metalness, B = porosity / sss
            smoothness = sr / 255.0
            metalness_raw = sg / 255.0
            is_metal = 1.0 if metalness_raw >= 0.9 else (metalness_raw if metalness_raw > 0.05 else 0.0)

            # N dot L (diffuse)
            ndotl = max(0.0, nx * lx + ny * ly + nz * lz)
            # N dot H (specular)
            ndoth = max(0.0, nx * hx + ny * hy + nz * hz)

            # Ambient + Diffuse
            ambient = 0.20 * ao
            diffuse = 0.80 * ndotl * ao

            # Specular power and highlight
            roughness = max(0.04, 1.0 - smoothness)
            spec_power = max(2.0, 2.0 / (roughness * roughness))
            spec_term = math.pow(ndoth, spec_power) * smoothness

            # Final RGB composition
            albedo_r = br / 255.0
            albedo_g = bg / 255.0
            albedo_b = bb / 255.0

            # Metalness colors specular with albedo
            spec_color_r = (1.0 - is_metal) + is_metal * albedo_r
            spec_color_g = (1.0 - is_metal) + is_metal * albedo_g
            spec_color_b = (1.0 - is_metal) + is_metal * albedo_b

            diff_multiplier = (ambient + diffuse) * (1.0 - is_metal * 0.85)

            out_r = min(1.0, albedo_r * diff_multiplier + spec_term * spec_color_r * 1.5)
            out_g = min(1.0, albedo_g * diff_multiplier + spec_term * spec_color_g * 1.5)
            out_b = min(1.0, albedo_b * diff_multiplier + spec_term * spec_color_b * 1.5)

            out_pix[x, y] = (int(out_r * 255), int(out_g * 255), int(out_b * 255), ba)

    return lit_out

def generate_sheets(pack_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    pack_dir = Path(pack_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    block_dir = pack_dir / "assets" / "minecraft" / "textures" / "block"
    if not block_dir.exists():
        raise FileNotFoundError(f"Texture block directory not found at {block_dir}")

    # Layout for 3x3 seamless sheet:
    # 3 columns, 2 rows
    # Panel inner size: 3x3 repetition of 32x32 -> 96x96 px, nearest scaled 2x -> 192x192 px
    # Header per panel: 24 px
    # Padding: 16 px between panels and borders
    cols, rows = 3, 2
    cell_w, cell_h = 192, 192
    header_h = 24
    pad = 16

    sheet1_w = pad + cols * (cell_w + pad)
    sheet1_h = pad + rows * (cell_h + header_h + pad)

    sheet_seamless = Image.new("RGBA", (sheet1_w, sheet1_h), BG_COLOR)
    draw_seamless = ImageDraw.Draw(sheet_seamless)

    for idx, bname in enumerate(CORE_BLOCKS):
        col = idx % cols
        row = idx // cols
        x0 = pad + col * (cell_w + pad)
        y0 = pad + row * (cell_h + header_h + pad)

        draw_seamless.text((x0 + 4, y0 + 4), bname, fill=TEXT_COLOR)

        base_path = block_dir / f"{bname}.png"
        img = Image.open(base_path).convert("RGBA").crop((0, 0, 32, 32))

        # Create 3x3 repetition (96x96)
        mosaic = Image.new("RGBA", (96, 96))
        for my in range(3):
            for mx in range(3):
                mosaic.paste(img, (mx * 32, my * 32))

        # Scale 2x nearest
        mosaic_scaled = mosaic.resize((cell_w, cell_h), Image.Resampling.NEAREST)
        sheet_seamless.paste(mosaic_scaled, (x0, y0 + header_h))
        draw_seamless.rectangle(
            [x0 - 1, y0 + header_h - 1, x0 + cell_w, y0 + header_h + cell_h],
            outline=PANEL_BORDER_COLOR
        )

    out1 = output_dir / "contact_sheet_3x3.png"
    sheet_seamless.save(out1, "PNG")

    # Layout for lit preview sheet:
    # 3 columns, 2 rows
    # Scaled 4x: 32x32 -> 128x128 px per panel
    # Header per panel: 22 px
    lit_cell_w, lit_cell_h = 128, 128
    lit_header_h = 22
    lit_pad = 16

    sheet2_w = lit_pad + cols * (lit_cell_w + lit_pad)
    sheet2_h = lit_pad + rows * (lit_cell_h + lit_header_h + lit_pad)

    sheet_lit = Image.new("RGBA", (sheet2_w, sheet2_h), BG_COLOR)
    draw_lit = ImageDraw.Draw(sheet_lit)

    for idx, bname in enumerate(CORE_BLOCKS):
        col = idx % cols
        row = idx // cols
        x0 = lit_pad + col * (lit_cell_w + lit_pad)
        y0 = lit_pad + row * (lit_cell_h + lit_header_h + lit_pad)

        draw_lit.text((x0 + 4, y0 + 3), bname, fill=TEXT_COLOR)

        base_path = block_dir / f"{bname}.png"
        norm_path = block_dir / f"{bname}_n.png"
        spec_path = block_dir / f"{bname}_s.png"

        b_img = Image.open(base_path).crop((0, 0, 32, 32))
        n_img = Image.open(norm_path).crop((0, 0, 32, 32))
        s_img = Image.open(spec_path).crop((0, 0, 32, 32))

        lit_panel = render_lit_texture(b_img, n_img, s_img)
        lit_scaled = lit_panel.resize((lit_cell_w, lit_cell_h), Image.Resampling.NEAREST)

        sheet_lit.paste(lit_scaled, (x0, y0 + lit_header_h))
        draw_lit.rectangle(
            [x0 - 1, y0 + lit_header_h - 1, x0 + lit_cell_w, y0 + lit_header_h + lit_cell_h],
            outline=PANEL_BORDER_COLOR
        )

    out2 = output_dir / "contact_sheet_lit.png"
    sheet_lit.save(out2, "PNG")

    return out1, out2

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent.parent
    pack_dir = repo_root / "packs" / "aetheria-labpbr-32x"
    output_dir = repo_root / "docs" / "branding"

    p1, p2 = generate_sheets(pack_dir, output_dir)
    print(f"Generated sheets:")
    print(f" - {p1} ({p1.stat().st_size} bytes)")
    print(f" - {p2} ({p2.stat().st_size} bytes)")
