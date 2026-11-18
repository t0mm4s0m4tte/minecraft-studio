"""
Modulo di generazione procedurale per texture 32x32 organiche tileable (toroidali)
con supporto fBm multi-ottava, Worley cell noise e Hue-Shifting pixel-art per LabPBR 1.3.
"""

import math
import random
import hashlib

SIZE = 32

def clamp(val, min_v=0, max_v=255):
    return max(min_v, min(max_v, int(round(val))))

def block_rng(name: str) -> random.Random:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))

def create_toroidal_grid(rng: random.Random, scale: int = 8):
    """Crea una griglia di gradiente casuale periodica per garantire seamless tiling a 32x32."""
    grid = {}
    for y in range(scale):
        for x in range(scale):
            angle = rng.uniform(0, math.pi * 2)
            grid[(x, y)] = (math.cos(angle), math.sin(angle))
    return grid

def _fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

def sample_toroidal_noise(x: float, y: float, grid, scale: int = 8):
    """Campiona rumore perlin tileable."""
    gx = (x / SIZE) * scale
    gy = (y / SIZE) * scale

    x0 = int(math.floor(gx)) % scale
    y0 = int(math.floor(gy)) % scale
    x1 = (x0 + 1) % scale
    y1 = (y0 + 1) % scale

    fx = gx - math.floor(gx)
    fy = gy - math.floor(gy)

    u = _fade(fx)
    v = _fade(fy)

    def dot_grad(ix, iy, rx, ry):
        gx_val, gy_val = grid[(ix, iy)]
        return gx_val * rx + gy_val * ry

    n00 = dot_grad(x0, y0, fx, fy)
    n10 = dot_grad(x1, y0, fx - 1.0, fy)
    n01 = dot_grad(x0, y1, fx, fy - 1.0)
    n11 = dot_grad(x1, y1, fx - 1.0, fy - 1.0)

    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    return nx0 + v * (nx1 - nx0)

def sample_fbm(x: float, y: float, grids, octaves=3, lacunarity=2.0, gain=0.5):
    """Fractional Brownian Motion multi-ottava periodico."""
    total = 0.0
    amp = 1.0
    max_amp = 0.0
    for i in range(octaves):
        g = grids[i]
        scale = len(g) ** 0.5
        total += sample_toroidal_noise(x * (lacunarity ** i), y * (lacunarity ** i), g, int(scale)) * amp
        max_amp += amp
        amp *= gain
    return total / max_amp

def sample_toroidal_worley(x: float, y: float, points, period=32):
    """Cellular / Worley noise periodico (distanza euclidea toroidale minima)."""
    min_dist = 999.0
    for px, py in points:
        dx = abs(x - px)
        dy = abs(y - py)
        dx = min(dx, period - dx)
        dy = min(dy, period - dy)
        d = math.hypot(dx, dy)
        if d < min_dist:
            min_dist = d
    return min_dist

def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    h = 0.0
    if mx == mn:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    s = 0.0 if mx == 0 else df / mx
    v = mx
    return h, s, v

def hsv_to_rgb(h, s, v):
    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2.0 - 1.0))
    m = v - c
    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return clamp((r + m) * 255), clamp((g + m) * 255), clamp((b + m) * 255)

def apply_pixelart_hueshift(base_rgb, shade_factor, hue_shift_deg=12.0, sat_boost=0.15):
    """Applica ombreggiature d'artista: ombre più fredde/sature, luci più calde/chiare."""
    h, s, v = rgb_to_hsv(*base_rgb)
    # Ombre (shade < 0) -> shift verso blu/viola (-H), più saturate (+S)
    # Luci (shade > 0) -> shift verso giallo/ambra (+H), leggermente desaturate (-S)
    shift = clamp(shade_factor, -1.0, 1.0)
    if shift < 0:
        new_h = (h - hue_shift_deg * abs(shift)) % 360
        new_s = min(1.0, s + sat_boost * abs(shift))
        new_v = max(0.0, v * (1.0 + shift * 0.45))
    else:
        new_h = (h + hue_shift_deg * shift) % 360
        new_s = max(0.0, s * (1.0 - sat_boost * 0.5 * shift))
        new_v = min(1.0, v * (1.0 + shift * 0.35))
    return hsv_to_rgb(new_h, new_s, new_v)
