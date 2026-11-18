"""
Generatore deterministico completo delle 50 texture mancanti dell'MVP (60/60)
per Aetheria LabPBR 32x (Minecraft 1.21.1).

Riutilizza le primitive PNG/Sobel di `generate_vertical_slice.py` e produce
set LabPBR 1.3 completi (<block>.png, <block>_n.png, <block>_s.png) 32x32 RGBA 8-bit.
"""

import argparse
import hashlib
import json
import math
import os
import random

from generate_vertical_slice import clamp, compute_normal_from_height, write_png_rgba

SIZE = 32


def block_rng(name: str) -> random.Random:
    """Restituisce un PRNG deterministico indipendente dall'ordine di esecuzione."""
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def emit_texture_set(output_dir: str, name: str, albedo, height_grid, spec, normal_strength: float = 1.8):
    """Calcola la normal map Sobel con AO e salva Albedo, _n e _s in RGBA 8-bit."""
    sanitized_spec = [(r, g, b, min(a, 254)) for (r, g, b, a) in spec]
    normal = compute_normal_from_height(height_grid, SIZE, SIZE, normal_strength)
    write_png_rgba(os.path.join(output_dir, f"{name}.png"), SIZE, SIZE, albedo)
    write_png_rgba(os.path.join(output_dir, f"{name}_n.png"), SIZE, SIZE, normal)
    write_png_rgba(os.path.join(output_dir, f"{name}_s.png"), SIZE, SIZE, sanitized_spec)


def _noise_grid(rng: random.Random, amplitude: float, base: int = 128):
    return [[clamp(base + rng.uniform(-amplitude, amplitude)) for _ in range(SIZE)] for _ in range(SIZE)]


def _host_stone_pixel(x: int, y: int, rng: random.Random):
    wave = 10 * math.sin(x * 0.55) * math.cos(y * 0.55)
    ht = clamp(128 + wave + rng.uniform(-6, 6))
    c = clamp(124 + (ht - 128) * 0.75)
    return ht, (c, c, c, 255), (clamp(45 + (ht - 128) * 0.25), 16, 0, 0)


def _host_deepslate_pixel(x: int, y: int, rng: random.Random):
    band = 14 if ((y // 4) % 2 == 0) else -14
    wave = 10 * math.cos((x + y * 0.5) * 0.4) + rng.uniform(-4, 4)
    ht = clamp(122 + band + wave)
    c = clamp(54 + (ht - 128) * 0.45)
    return ht, (c, c + 2, c + 5, 255), (50, 16, 0, 0)


# ---------------------------------------------------------------------------
# 1. TERRAIN & STONE
# ---------------------------------------------------------------------------

def gen_mossy_cobblestone(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            cx, cy = (x // 8) * 8 + 4, (y // 8) * 8 + 4
            dist = math.hypot(x - cx, y - cy)
            moss_signal = math.sin(x * 0.45 + 0.8) * math.cos(y * 0.45 - 0.5) + rng.uniform(-0.25, 0.25)
            is_moss = (dist > 3.2 and moss_signal > -0.1) or moss_signal > 0.52
            if is_moss:
                ht = clamp(142 + rng.uniform(-8, 10))
                height[y][x] = ht
                r = clamp(68 + rng.uniform(-8, 8))
                g = clamp(112 + rng.uniform(-10, 12))
                b = clamp(52 + rng.uniform(-6, 6))
                albedo.append((r, g, b, 255))
                spec.append((22, 12, 8, 0))
            elif dist > 3.8:
                ht = clamp(62 + rng.uniform(-6, 6))
                height[y][x] = ht
                c = clamp(66 + rng.uniform(-5, 5))
                albedo.append((c, c, c, 255))
                spec.append((35, 16, 0, 0))
            else:
                ht = clamp(160 - dist * 8 + rng.uniform(-7, 7))
                height[y][x] = ht
                c = clamp(112 + (ht - 128) * 0.7 + rng.uniform(-5, 5))
                albedo.append((c, c, c, 255))
                spec.append((55, 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 2.4)


def gen_smooth_stone(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            border = (x == 0 or x == SIZE - 1 or y == 0 or y == SIZE - 1)
            inner_bevel = (x == 1 or x == SIZE - 2 or y == 1 or y == SIZE - 2)
            speck = rng.uniform(-4, 4)
            if border:
                ht = 104
                c = clamp(118 + speck)
            elif inner_bevel:
                ht = 142
                c = clamp(162 + speck)
            else:
                ht = clamp(134 + 3 * math.sin(x * 0.3 + y * 0.2) + speck)
                c = clamp(148 + speck)
            height[y][x] = ht
            albedo.append((c, c, c, 255))
            spec.append((72, 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.4)


def gen_brick_block(
    output_dir: str,
    name: str,
    base_rgb: tuple,
    mortar_rgb: tuple,
    smoothness: int,
    rows: int = 2,
    cols: int = 2,
    mossy: bool = False,
    cracked: bool = False,
    normal_strength: float = 2.0,
):
    rng = block_rng(name)
    row_h = SIZE // rows
    col_w = SIZE // cols
    height = [[138 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []

    crack_pixels = set()
    if cracked:
        for t in range(18):
            cx = clamp(6 + t + int(math.sin(t * 0.9) * 2), 1, SIZE - 2)
            cy = clamp(4 + int(t * 1.3), 1, SIZE - 2)
            crack_pixels.add((cx, cy))
            crack_pixels.add((min(SIZE - 1, cx + 1), cy))

    for y in range(SIZE):
        row_idx = y // row_h
        ly = y % row_h
        x_shift = (col_w // 2) if (row_idx % 2 == 1) else 0
        for x in range(SIZE):
            lx = (x + x_shift) % col_w
            is_mortar = (ly == 0 or lx == 0)
            is_bevel = (ly == 1 or ly == row_h - 1 or lx == 1 or lx == col_w - 1)
            is_crack = (x, y) in crack_pixels
            moss_hit = mossy and (is_mortar or is_bevel) and (math.sin(x * 0.5 + y * 0.4) + rng.uniform(-0.3, 0.3) > 0.15)

            if moss_hit:
                ht = clamp(134 + rng.uniform(-6, 8))
                r, g, b = clamp(64 + rng.uniform(-6, 6)), clamp(108 + rng.uniform(-8, 10)), clamp(48 + rng.uniform(-5, 5))
                sm, f0 = 24, 12
            elif is_crack:
                ht = 52
                r, g, b = [clamp(v * 0.45) for v in mortar_rgb]
                sm, f0 = 20, 16
            elif is_mortar:
                ht = clamp(76 + rng.uniform(-4, 4))
                delta = rng.uniform(-5, 5)
                r, g, b = [clamp(v + delta) for v in mortar_rgb]
                sm, f0 = max(18, smoothness - 25), 16
            else:
                noise = rng.uniform(-6, 6)
                ht = clamp((146 if is_bevel else 138) + noise)
                shade = (6 if is_bevel else 0) + noise * 0.9
                r, g, b = [clamp(v + shade) for v in base_rgb]
                sm, f0 = clamp(smoothness + noise * 0.4), 16

            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, f0, 0, 0))

    emit_texture_set(output_dir, name, albedo, height, spec, normal_strength)


def gen_gravel(output_dir: str, name: str):
    rng = block_rng(name)
    palette = [(118, 114, 110), (138, 134, 128), (102, 98, 95), (128, 120, 112), (92, 90, 92)]
    pebbles = [(rng.randint(0, SIZE - 1), rng.randint(0, SIZE - 1), rng.choice(palette)) for _ in range(42)]
    height = [[120 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            best_d = 999.0
            best_col = palette[0]
            for px, py, col in pebbles:
                dx = min(abs(x - px), SIZE - abs(x - px))
                dy = min(abs(y - py), SIZE - abs(y - py))
                d = math.hypot(dx, dy)
                if d < best_d:
                    best_d = d
                    best_col = col
            ht = clamp(160 - best_d * 18 + rng.uniform(-6, 6))
            height[y][x] = ht
            shade = (ht - 128) * 0.55
            albedo.append(tuple(clamp(c + shade) for c in best_col) + (255,))
            spec.append((clamp(30 + rng.uniform(-5, 10)), 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 2.3)


# ---------------------------------------------------------------------------
# 2. ORES & RAW METALS
# ---------------------------------------------------------------------------

def gen_ore(
    output_dir: str,
    name: str,
    deepslate: bool,
    vein_rgb: tuple,
    smoothness: int,
    f0_metal: int,
    emissive: int = 0,
    porosity: int = 0,
    malachite_flecks: bool = False,
):
    rng = block_rng(name)
    vein_centers = [
        (rng.randint(5, 11), rng.randint(5, 11)),
        (rng.randint(18, 26), rng.randint(6, 13)),
        (rng.randint(12, 20), rng.randint(15, 22)),
        (rng.randint(6, 13), rng.randint(20, 27)),
        (rng.randint(20, 27), rng.randint(21, 27)),
    ]
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []

    for y in range(SIZE):
        for x in range(SIZE):
            min_d = min(math.hypot(x - vx, y - vy) for vx, vy in vein_centers)
            jitter = rng.uniform(-0.45, 0.45)
            if min_d + jitter < 2.6:
                ht = clamp(168 - min_d * 10 + rng.uniform(-4, 6))
                height[y][x] = ht
                if malachite_flecks and rng.random() < 0.34:
                    r = clamp(68 + rng.uniform(-8, 8))
                    g = clamp(162 + rng.uniform(-10, 10))
                    b = clamp(138 + rng.uniform(-8, 8))
                    albedo.append((r, g, b, 255))
                    spec.append((85, 18, 0, 0))
                else:
                    delta = rng.uniform(-10, 10)
                    r, g, b = [clamp(c + delta) for c in vein_rgb]
                    albedo.append((r, g, b, 255))
                    em = clamp(emissive * (1.0 - min_d * 0.12), 0, 254) if emissive > 0 else 0
                    spec.append((smoothness, f0_metal, porosity, em))
            else:
                ht, host_rgb, host_spec = (
                    _host_deepslate_pixel(x, y, rng) if deepslate else _host_stone_pixel(x, y, rng)
                )
                height[y][x] = ht
                albedo.append(host_rgb)
                spec.append(host_spec)

    emit_texture_set(output_dir, name, albedo, height, spec, 2.2)


# ---------------------------------------------------------------------------
# 3. WOODS & CONSTRUCTION
# ---------------------------------------------------------------------------

def gen_log_side(output_dir: str, name: str, bark_rgb: tuple, furrow_rgb: tuple, lenticels: bool = False):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            ridge = math.sin(x * 1.15 + math.sin(y * 0.25) * 1.4)
            is_lenticel = lenticels and (y % 6 == 2) and (3 <= (x + y * 5) % 13 <= 7)
            if is_lenticel:
                ht = 148
                r, g, b = clamp(bark_rgb[0] + 68), clamp(bark_rgb[1] + 52), clamp(bark_rgb[2] + 52)
                sm = 40
            elif ridge < -0.35:
                ht = clamp(82 + rng.uniform(-6, 6))
                delta = rng.uniform(-5, 5)
                r, g, b = [clamp(c + delta) for c in furrow_rgb]
                sm = 22
            else:
                ht = clamp(138 + ridge * 18 + rng.uniform(-6, 6))
                delta = ridge * 10 + rng.uniform(-6, 6)
                r, g, b = [clamp(c + delta) for c in bark_rgb]
                sm = 32
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 2.1)


def gen_log_top(output_dir: str, name: str, bark_rgb: tuple, wood_rgb: tuple):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = abs(x - 15.5), abs(y - 15.5)
            cheb = max(dx, dy)
            rad = math.hypot(dx, dy)
            if cheb >= 13.0:
                ht = clamp(118 + rng.uniform(-12, 12))
                delta = rng.uniform(-8, 8)
                r, g, b = [clamp(c + delta) for c in bark_rgb]
                sm = 28
            else:
                ring = math.sin(rad * 1.9 + rng.uniform(-0.15, 0.15))
                ht = clamp(132 + ring * 10 + rng.uniform(-3, 3))
                delta = ring * 12 + rng.uniform(-4, 4)
                r, g, b = [clamp(c + delta) for c in wood_rgb]
                sm = clamp(58 + ring * 8)
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.7)


def gen_planks(output_dir: str, name: str, wood_rgb: tuple, seam_rgb: tuple, smoothness: int):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        plank_idx = y // 8
        ly = y % 8
        v_joint = (plank_idx * 11 + 7) % SIZE
        for x in range(SIZE):
            is_seam = (ly == 0 or ly == 7 or x == v_joint)
            if is_seam:
                ht = 72
                r, g, b = [clamp(c + rng.uniform(-4, 4)) for c in seam_rgb]
                sm = 24
            else:
                grain = 7 * math.sin(x * 0.42 + plank_idx * 1.7) + rng.uniform(-3, 3)
                ht = clamp(132 + grain)
                r, g, b = [clamp(c + grain * 0.9) for c in wood_rgb]
                sm = clamp(smoothness + grain * 0.5)
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.8)


# ---------------------------------------------------------------------------
# 4. TRIAL CHAMBERS & COPPER 1.21
# ---------------------------------------------------------------------------

def gen_weathered_copper_stage(output_dir: str, name: str, patina_ratio: float, smoothness_copper: int):
    rng = block_rng(name)
    copper_rgb = (182, 110, 82)
    patina_rgb = (78, 162, 134)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            patch = 0.5 + 0.5 * math.sin(x * 0.35 + 0.6) * math.cos(y * 0.35 - 0.4) + rng.uniform(-0.18, 0.18)
            is_patina = patch < patina_ratio
            border = (x == 0 or y == 0 or x == SIZE - 1 or y == SIZE - 1)
            ht = clamp((112 if border else 132) + (6 if is_patina else -2) + rng.uniform(-4, 4))
            height[y][x] = ht
            if is_patina:
                delta = rng.uniform(-8, 8)
                albedo.append(tuple(clamp(c + delta) for c in patina_rgb) + (255,))
                spec.append((46, 18, 0, 0))
            else:
                delta = rng.uniform(-7, 7)
                albedo.append(tuple(clamp(c + delta) for c in copper_rgb) + (255,))
                spec.append((smoothness_copper, 246, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.6)


def gen_cut_copper(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[140 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            seam = (x in (0, 15, 16, 31) or y in (0, 15, 16, 31))
            bevel = (x in (1, 14, 17, 30) or y in (1, 14, 17, 30))
            noise = rng.uniform(-4, 4)
            if seam:
                ht = 74
                r, g, b = clamp(128 + noise), clamp(66 + noise), clamp(48 + noise)
                sm = 85
            elif bevel:
                ht = 160
                r, g, b = clamp(218 + noise), clamp(128 + noise), clamp(92 + noise)
                sm = 168
            else:
                ht = clamp(140 + noise)
                r, g, b = clamp(195 + noise), clamp(108 + noise), clamp(78 + noise)
                sm = 152
            height[y][x] = ht
            albedo.append((r, g, b, 255))
            spec.append((sm, 250, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 2.0)


def gen_copper_grate(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            outer_frame = (x < 3 or x >= SIZE - 3 or y < 3 or y >= SIZE - 3)
            inner_cross = (14 <= x <= 17 or 14 <= y <= 17)
            diag_bar = (abs(x - y) <= 1 or abs((SIZE - 1 - x) - y) <= 1)
            if outer_frame or inner_cross or diag_bar:
                ht = 168 if outer_frame else 150
                noise = rng.uniform(-5, 5)
                albedo.append((clamp(192 + noise), clamp(106 + noise), clamp(76 + noise), 255))
                spec.append((145, 250, 0, 0))
            else:
                ht = 0
                albedo.append((0, 0, 0, 0))
                spec.append((0, 0, 0, 0))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 2.1)


def gen_chiseled_copper(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            cheb = max(abs(x - 15.5), abs(y - 15.5))
            is_groove = (3.5 <= cheb <= 5.0) or (9.5 <= cheb <= 11.0)
            is_center = (cheb < 3.0)
            noise = rng.uniform(-4, 4)
            if is_groove:
                ht = 82
                albedo.append((clamp(132 + noise), clamp(70 + noise), clamp(50 + noise), 255))
                spec.append((95, 242, 0, 0))
            elif is_center:
                ht = 168
                albedo.append((clamp(215 + noise), clamp(128 + noise), clamp(90 + noise), 255))
                spec.append((165, 250, 0, 0))
            else:
                ht = clamp(144 + noise)
                albedo.append((clamp(194 + noise), clamp(108 + noise), clamp(78 + noise), 255))
                spec.append((148, 250, 0, 0))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 2.0)


def gen_tuff(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            pit = math.sin(x * 0.7) * math.cos(y * 0.7) * 14 + rng.uniform(-8, 8)
            ht = clamp(128 + pit)
            height[y][x] = ht
            r = clamp(104 + pit * 0.55)
            g = clamp(107 + pit * 0.55)
            b = clamp(97 + pit * 0.50)
            albedo.append((r, g, b, 255))
            spec.append((clamp(36 + pit * 0.3), 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.9)


def gen_chiseled_tuff(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[136 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            cheb = max(abs(x - 15.5), abs(y - 15.5))
            manh = abs(x - 15.5) + abs(y - 15.5)
            groove = (4.0 <= cheb <= 5.5) or (11.0 <= cheb <= 12.5) or (7.5 <= manh <= 9.0)
            noise = rng.uniform(-4, 4)
            ht = clamp((76 if groove else 146) + noise)
            height[y][x] = ht
            shift = (-22 if groove else 6) + noise
            albedo.append((clamp(104 + shift), clamp(107 + shift), clamp(98 + shift), 255))
            spec.append((clamp(48 if not groove else 26), 16, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 2.1)


def gen_crafter_top(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[140 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            is_outer = (x < 4 or x >= SIZE - 4 or y < 4 or y >= SIZE - 4)
            is_rivet = (x in (2, SIZE - 3) and y in (2, SIZE - 3))
            in_grid = (5 <= x <= 26 and 5 <= y <= 26)
            slot_x = (x - 5) % 8
            slot_y = (y - 5) % 8
            is_slot_hole = in_grid and (slot_x < 6 and slot_y < 6)
            noise = rng.uniform(-3, 3)

            if is_rivet:
                ht = 172
                albedo.append((210, 52, 42, 255))
                spec.append((130, 240, 0, 75))
            elif is_outer:
                ht = clamp(154 + noise)
                c = clamp(82 + noise)
                albedo.append((c, c + 3, c + 6, 255))
                spec.append((120, 240, 0, 0))
            elif is_slot_hole:
                ht = 84
                c = clamp(44 + noise)
                albedo.append((c, c - 2, c - 4, 255))
                spec.append((35, 16, 0, 0))
            else:
                ht = clamp(144 + noise)
                albedo.append((clamp(158 + noise), clamp(112 + noise), clamp(72 + noise), 255))
                spec.append((68, 16, 0, 0))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 2.2)


# ---------------------------------------------------------------------------
# 5. LIGHT SOURCES & DYNAMIC EMITTERS
# ---------------------------------------------------------------------------

def gen_torch_variant(output_dir: str, name: str, flame_rgb: tuple, tilted: bool = False):
    rng = block_rng(name)
    height = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            sx = x - int(round((28 - y) * 0.25)) if tilted else x
            is_stick = (13 <= sx <= 18 and 10 <= y <= 31)
            is_head = (12 <= sx <= 19 and 4 <= y <= 9)
            is_flame = (11 <= sx <= 20 and 0 <= y <= 7)

            if is_flame:
                height[y][x] = 162
                albedo.append(flame_rgb + (255,))
                spec.append((105, 16, 0, 240))
            elif is_head:
                height[y][x] = 146
                albedo.append((48, 38, 32, 255))
                spec.append((30, 16, 0, 85))
            elif is_stick:
                height[y][x] = 134
                n = rng.uniform(-5, 5)
                albedo.append((clamp(128 + n), clamp(92 + n), clamp(52 + n), 255))
                spec.append((45, 16, 0, 0))
            else:
                height[y][x] = 0
                albedo.append((0, 0, 0, 0))
                spec.append((0, 0, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.5)


def gen_soul_lantern(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            is_metal = (
                (14 <= x <= 17 and y <= 4)
                or (8 <= x <= 23 and 5 <= y <= 9)
                or (8 <= x <= 23 and 25 <= y <= 29)
                or ((8 <= x <= 10 or 21 <= x <= 23) and 10 <= y <= 24)
            )
            is_core = (13 <= x <= 18 and 14 <= y <= 20)
            is_glass = (11 <= x <= 20 and 10 <= y <= 24)

            if is_metal:
                height[y][x] = 170
                c = clamp(44 + rng.uniform(-4, 4))
                albedo.append((c, c + 3, c + 6, 255))
                spec.append((95, 236, 0, 0))
            elif is_core:
                height[y][x] = 142
                albedo.append((120, 245, 255, 255))
                spec.append((130, 20, 0, 245))
            elif is_glass:
                height[y][x] = 120
                albedo.append((85, 195, 225, 205))
                spec.append((210, 20, 0, 82))
            else:
                height[y][x] = 0
                albedo.append((0, 0, 0, 0))
                spec.append((0, 0, 0, 0))
    emit_texture_set(output_dir, name, albedo, height, spec, 2.0)


def gen_glowstone(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            crystal = math.sin(x * 0.65) * math.cos(y * 0.65) + rng.uniform(-0.35, 0.35)
            if crystal > 0.05:
                ht = clamp(152 + crystal * 35)
                albedo.append((clamp(248 + rng.uniform(-6, 6)), clamp(205 + rng.uniform(-12, 12)), clamp(102 + rng.uniform(-10, 10)), 255))
                spec.append((120, 24, 0, clamp(185 + crystal * 55, 120, 242)))
            else:
                ht = clamp(96 + rng.uniform(-8, 8))
                albedo.append((clamp(138 + rng.uniform(-8, 8)), clamp(96 + rng.uniform(-6, 6)), clamp(48 + rng.uniform(-6, 6)), 255))
                spec.append((42, 16, 0, 24))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 2.1)


def gen_sea_lantern(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            cheb = max(abs(x - 15.5), abs(y - 15.5))
            noise = rng.uniform(-5, 5)
            if cheb >= 11.0:
                ht = clamp(156 + noise)
                albedo.append((clamp(165 + noise), clamp(208 + noise), clamp(198 + noise), 255))
                spec.append((115, 22, 0, 32))
            elif cheb >= 7.5:
                ht = clamp(134 + noise)
                albedo.append((clamp(198 + noise), clamp(238 + noise), clamp(230 + noise), 255))
                spec.append((165, 26, 0, 155))
            else:
                ht = clamp(122 + noise)
                albedo.append((clamp(232 + noise), clamp(252 + noise), 250, 255))
                spec.append((195, 30, 0, 235))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 1.6)


def gen_shroomlight(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            bump = math.sin(x * 0.55 + 0.4) * math.sin(y * 0.55 - 0.3) + rng.uniform(-0.22, 0.22)
            ht = clamp(132 + bump * 32)
            height[y][x] = ht
            if bump > -0.1:
                albedo.append((clamp(245 + bump * 10), clamp(162 + bump * 30), clamp(66 + bump * 20), 255))
                spec.append((70, 18, 120, clamp(195 + bump * 40, 140, 238)))
            else:
                albedo.append((clamp(196 + rng.uniform(-6, 6)), clamp(96 + rng.uniform(-6, 6)), clamp(38 + rng.uniform(-4, 4)), 255))
                spec.append((55, 16, 95, 95))
    emit_texture_set(output_dir, name, albedo, height, spec, 1.8)


def gen_crying_obsidian(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[132 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            tear_wave = math.sin(x * 0.8 + math.cos(y * 0.35)) + math.cos(y * 0.65) * 0.6 + rng.uniform(-0.2, 0.2)
            if tear_wave > 0.95:
                ht = 104
                albedo.append((clamp(185 + rng.uniform(-10, 10)), clamp(72 + rng.uniform(-8, 8)), 250, 255))
                spec.append((180, 32, 70, 215))
            else:
                ht = clamp(138 + rng.uniform(-10, 10))
                r = clamp(24 + rng.uniform(-4, 6))
                g = clamp(16 + rng.uniform(-3, 5))
                b = clamp(38 + rng.uniform(-5, 8))
                albedo.append((r, g, b, 255))
                spec.append((192, 24, 0, 0))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 2.0)


def gen_trial_spawner_side(output_dir: str, name: str):
    rng = block_rng(name)
    height = [[128 for _ in range(SIZE)] for _ in range(SIZE)]
    albedo, spec = [], []
    for y in range(SIZE):
        for x in range(SIZE):
            is_frame = (x < 4 or x >= SIZE - 4 or y < 4 or y >= SIZE - 4)
            is_bar = (x in (10, 11, 20, 21) or y in (10, 11, 20, 21))
            is_copper_trim = (x in (3, SIZE - 4) or y in (3, SIZE - 4))
            noise = rng.uniform(-4, 4)

            if is_copper_trim:
                ht = 168
                albedo.append((clamp(192 + noise), clamp(106 + noise), clamp(76 + noise), 255))
                spec.append((145, 250, 0, 0))
            elif is_frame or is_bar:
                ht = clamp(156 + noise)
                c = clamp(48 + noise)
                albedo.append((c, c + 12, c + 18, 255))
                spec.append((110, 238, 0, 0))
            else:
                ht = 88
                glow = 1.0 - math.hypot(x - 15.5, y - 15.5) / 16.0
                r = clamp(248)
                g = clamp(110 + glow * 105)
                b = clamp(28 + glow * 45)
                albedo.append((r, g, b, 255))
                spec.append((95, 20, 0, clamp(160 + glow * 75, 130, 235)))
            height[y][x] = ht
    emit_texture_set(output_dir, name, albedo, height, spec, 2.2)


# ---------------------------------------------------------------------------
# TABELLA DISPATCH COMPLETA DEI 50 BLOCCHI MANCANTI
# ---------------------------------------------------------------------------

GENERATORS = {
    # Terrain & Stone (9)
    "mossy_cobblestone": gen_mossy_cobblestone,
    "smooth_stone": gen_smooth_stone,
    "stone_bricks": lambda d, n: gen_brick_block(d, n, (124, 124, 124), (82, 82, 82), 54),
    "mossy_stone_bricks": lambda d, n: gen_brick_block(d, n, (122, 124, 120), (80, 82, 80), 52, mossy=True),
    "cracked_stone_bricks": lambda d, n: gen_brick_block(d, n, (118, 118, 118), (74, 74, 74), 50, cracked=True),
    "cobbled_deepslate": lambda d, n: gen_brick_block(d, n, (62, 64, 68), (34, 36, 40), 58, rows=4, cols=4, normal_strength=2.5),
    "deepslate_bricks": lambda d, n: gen_brick_block(d, n, (58, 60, 65), (32, 34, 38), 66),
    "deepslate_tiles": lambda d, n: gen_brick_block(d, n, (52, 54, 60), (28, 30, 34), 76, rows=4, cols=4),
    "gravel": gen_gravel,
    # Ores & Raw Metals (11)
    "coal_ore": lambda d, n: gen_ore(d, n, False, (36, 36, 38), 86, 20),
    "deepslate_coal_ore": lambda d, n: gen_ore(d, n, True, (34, 34, 36), 88, 20),
    "deepslate_iron_ore": lambda d, n: gen_ore(d, n, True, (210, 170, 140), 150, 245),
    "copper_ore": lambda d, n: gen_ore(d, n, False, (206, 110, 74), 145, 250, malachite_flecks=True),
    "deepslate_copper_ore": lambda d, n: gen_ore(d, n, True, (206, 110, 74), 145, 250, malachite_flecks=True),
    "gold_ore": lambda d, n: gen_ore(d, n, False, (248, 206, 56), 196, 252),
    "deepslate_gold_ore": lambda d, n: gen_ore(d, n, True, (248, 206, 56), 196, 252),
    "redstone_ore": lambda d, n: gen_ore(d, n, False, (220, 28, 28), 162, 40, emissive=145),
    "deepslate_redstone_ore": lambda d, n: gen_ore(d, n, True, (220, 28, 28), 162, 40, emissive=145),
    "diamond_ore": lambda d, n: gen_ore(d, n, False, (84, 236, 232), 232, 130),
    "deepslate_diamond_ore": lambda d, n: gen_ore(d, n, True, (84, 236, 232), 232, 130),
    # Woods & Construction (11)
    "oak_log": lambda d, n: gen_log_side(d, n, (106, 82, 50), (72, 54, 32)),
    "oak_log_top": lambda d, n: gen_log_top(d, n, (102, 78, 48), (168, 132, 82)),
    "spruce_log": lambda d, n: gen_log_side(d, n, (62, 42, 24), (38, 24, 14)),
    "spruce_log_top": lambda d, n: gen_log_top(d, n, (58, 40, 24), (118, 84, 50)),
    "spruce_planks": lambda d, n: gen_planks(d, n, (116, 84, 48), (68, 46, 24), 62),
    "dark_oak_log": lambda d, n: gen_log_side(d, n, (54, 38, 24), (32, 22, 14)),
    "dark_oak_log_top": lambda d, n: gen_log_top(d, n, (50, 36, 22), (84, 58, 34)),
    "dark_oak_planks": lambda d, n: gen_planks(d, n, (68, 44, 24), (38, 24, 12), 70),
    "cherry_log": lambda d, n: gen_log_side(d, n, (58, 36, 44), (36, 22, 28), lenticels=True),
    "cherry_log_top": lambda d, n: gen_log_top(d, n, (56, 36, 44), (218, 148, 158)),
    "cherry_planks": lambda d, n: gen_planks(d, n, (226, 178, 172), (166, 118, 116), 74),
    # Trial Chambers & Copper 1.21 (11)
    "exposed_copper": lambda d, n: gen_weathered_copper_stage(d, n, 0.36, 116),
    "weathered_copper": lambda d, n: gen_weathered_copper_stage(d, n, 0.72, 92),
    "oxidized_copper": lambda d, n: gen_weathered_copper_stage(d, n, 1.05, 65),
    "cut_copper": gen_cut_copper,
    "copper_grate": gen_copper_grate,
    "chiseled_copper": gen_chiseled_copper,
    "tuff": gen_tuff,
    "chiseled_tuff": gen_chiseled_tuff,
    "tuff_bricks": lambda d, n: gen_brick_block(d, n, (98, 102, 92), (62, 65, 58), 46),
    "tuff_tiles": lambda d, n: gen_brick_block(d, n, (96, 100, 90), (58, 62, 55), 54, rows=4, cols=4),
    "crafter_top": gen_crafter_top,
    # Light Sources & Dynamic Emitters (8)
    "wall_torch": lambda d, n: gen_torch_variant(d, n, (255, 200, 50), tilted=True),
    "soul_torch": lambda d, n: gen_torch_variant(d, n, (80, 232, 255), tilted=False),
    "soul_lantern": gen_soul_lantern,
    "glowstone": gen_glowstone,
    "sea_lantern": gen_sea_lantern,
    "shroomlight": gen_shroomlight,
    "crying_obsidian": gen_crying_obsidian,
    "trial_spawner_side": gen_trial_spawner_side,
}


def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_out = os.path.join(root_dir, "assets", "minecraft", "textures", "block")
    manifest_path = os.path.join(root_dir, "mvp-60-blocks.json")

    parser = argparse.ArgumentParser(description="Genera tutte le texture mancanti MVP 60/60 per Aetheria LabPBR 32x")
    parser.add_argument("--output-dir", default=default_out, help="Cartella di destinazione delle texture")
    parser.add_argument("--overwrite", action="store_true", help="Rigenera anche le texture dei 50 blocchi già presenti")
    args = parser.parse_args()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_blocks = [b for blocks in manifest["categories"].values() for b in blocks]
    generated = 0
    skipped = 0

    for block in manifest_blocks:
        if block not in GENERATORS:
            continue
        base_path = os.path.join(args.output_dir, f"{block}.png")
        if os.path.exists(base_path) and not args.overwrite:
            skipped += 1
            continue
        GENERATORS[block](args.output_dir, block)
        generated += 1

    print(f"Completato: {generated} blocchi generati, {skipped} già esistenti saltati.")


if __name__ == "__main__":
    main()
