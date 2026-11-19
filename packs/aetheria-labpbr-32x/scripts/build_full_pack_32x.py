"""Build Full Pack 32x LabPBR 1.3 for Minecraft 1.21.1.

Processes all block and item textures from the vanilla 1.21.1 JAR,
upscaling them to 32x using Scale2x / EPX with sub-texel micro-detailing,
generating LabPBR 1.3 normal (_n.png) and specular (_s.png) maps,
and preserving existing hand-crafted assets.
"""

from concurrent.futures import ProcessPoolExecutor
import io
import json
import math
import os
import sys
import time
import zipfile

import numpy as np
from PIL import Image

VANILLA_JAR = r"C:\Users\tommy\AppData\Roaming\.minecraft\versions\1.21.1\1.21.1.jar"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK_TARGET_DIR = os.path.join(BASE_DIR, "assets", "minecraft", "textures", "block")
ITEM_TARGET_DIR = os.path.join(BASE_DIR, "assets", "minecraft", "textures", "item")
ENV_TARGET_DIR = os.path.join(BASE_DIR, "assets", "minecraft", "textures", "environment")


def generate_environment_textures():
    """Generates procedural high-definition 32x rain and snow textures."""
    import random
    os.makedirs(ENV_TARGET_DIR, exist_ok=True)
    width, height = 128, 512

    # 1. Rain Texture: fine semi-transparent raindrops with smooth vertical fade
    rain_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    random.seed(1337)
    for _ in range(60):
        cx = random.randint(0, width - 1)
        cy = random.randint(0, height - 1)
        streak_len = random.randint(14, 28)
        base_alpha = random.randint(90, 160)
        base_r, base_g, base_b = 180, 205, 235
        for dy in range(streak_len):
            py = (cy + dy) % height
            progress = dy / float(streak_len - 1)
            fade = math.sin(progress * math.pi) ** 1.2
            a = int(base_alpha * fade)
            if a > 0:
                rain_img.putpixel((cx, py), (base_r, base_g, base_b, a))
                halo_a = int(a * 0.25)
                if halo_a > 0:
                    rain_img.putpixel(((cx - 1) % width, py), (base_r, base_g, base_b, halo_a))
                    rain_img.putpixel(((cx + 1) % width, py), (base_r, base_g, base_b, halo_a))
    rain_path = os.path.join(ENV_TARGET_DIR, "rain.png")
    rain_img.save(rain_path)

    # 2. Snow Texture: soft circular microscopic snowflakes
    snow_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    random.seed(4242)
    for _ in range(90):
        fx = random.randint(0, width - 1)
        fy = random.randint(0, height - 1)
        flake_radius = random.choice([1, 2, 2, 3])
        max_alpha = random.randint(180, 240)
        for dy in range(-flake_radius, flake_radius + 1):
            for dx in range(-flake_radius, flake_radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= flake_radius:
                    px = (fx + dx) % width
                    py = (fy + dy) % height
                    falloff = max(0.0, 1.0 - (dist / float(flake_radius + 0.5)))
                    alpha = int(max_alpha * (falloff ** 1.3))
                    if alpha > 0:
                        cur_a = snow_img.getpixel((px, py))[3]
                        snow_img.putpixel((px, py), (245, 250, 255, min(255, cur_a + alpha)))
    snow_path = os.path.join(ENV_TARGET_DIR, "snow.png")
    snow_img.save(snow_path)
    print(f"Generated environment textures: rain.png, snow.png in {ENV_TARGET_DIR}")

POM_FLAT_KEYWORDS = {
    "flower", "sapling", "grass", "fern", "vine", "lily", "rail", "ladder", "pane",
    "door", "trapdoor", "torch", "lantern", "candle", "chain", "web", "crop", "wheat",
    "carrot", "potato", "beetroot", "stem", "kelp", "seagrass", "coral", "amethyst_bud",
    "cluster", "pointed_dripstone", "scaffolding", "bars", "grate", "spawner", "carpet",
    "snow", "bed", "cake", "comparator", "repeater", "redstone_dust", "lever", "button",
    "tripwire", "bamboo", "azalea", "dripleaf", "roots", "sprouts", "fungus", "mushroom",
    "sugar_cane", "cactus", "dead_bush", "fire", "campfire", "bell", "anvil", "grindstone",
    "lectern", "stonecutter", "brewing_stand", "cauldron", "hopper", "chorus", "end_rod",
    "lightning_rod", "heavy_core", "dragon_egg", "pink_petals", "pitcher", "torchflower",
    "sculk_vein", "sensor", "shrieker", "frogspawn", "hanging_sign", "sign"
}


def is_pom_flat(name_lower: str, is_item: bool, has_transparent_pixels: bool) -> bool:
    if is_item:
        return True
    if has_transparent_pixels:
        return True
    if "grass_block_top" in name_lower:
        return False
    for kw in POM_FLAT_KEYWORDS:
        if kw in name_lower:
            return True
    return False


def scale2x_epx(img_rgba: np.ndarray) -> np.ndarray:
    """Scale2x / EPX algorithm vectorized in NumPy on RGBA image (H, W, 4).

    Input: (H, W, 4) uint8
    Output: (2H, 2W, 4) uint8
    """
    h, w, c = img_rgba.shape
    p = img_rgba.astype(np.int32)

    # Shifted neighbors with clamp border
    a = np.pad(p[:-1, :, :], ((1, 0), (0, 0), (0, 0)), mode="edge")  # up
    d = np.pad(p[1:, :, :], ((0, 1), (0, 0), (0, 0)), mode="edge")  # down
    c_left = np.pad(p[:, :-1, :], ((0, 0), (1, 0), (0, 0)), mode="edge")  # left
    b = np.pad(p[:, 1:, :], ((0, 0), (0, 1), (0, 0)), mode="edge")  # right

    def is_equal(x, y):
        # Color distance on RGB < 18 and same alpha state (or difference < 18)
        rgb_diff = np.max(np.abs(x[..., :3] - y[..., :3]), axis=-1)
        a_diff = np.abs(x[..., 3] - y[..., 3])
        return (rgb_diff < 18) & (a_diff < 18)

    eq_c_a = is_equal(c_left, a)
    eq_c_d = is_equal(c_left, d)
    eq_a_b = is_equal(a, b)
    eq_b_d = is_equal(b, d)

    cond_e0 = eq_c_a & (~eq_c_d) & (~eq_a_b)
    cond_e1 = eq_a_b & (~eq_c_a) & (~eq_b_d)
    cond_e2 = eq_c_d & (~eq_b_d) & (~eq_c_a)
    cond_e3 = eq_b_d & (~eq_a_b) & (~eq_c_d)

    e0 = np.where(cond_e0[..., None], c_left, p)
    e1 = np.where(cond_e1[..., None], a, p)
    e2 = np.where(cond_e2[..., None], d, p)
    e3 = np.where(cond_e3[..., None], b, p)

    # Assemble into (2H, 2W, 4)
    out = np.empty((2 * h, 2 * w, c), dtype=np.int32)
    out[0::2, 0::2] = e0
    out[0::2, 1::2] = e1
    out[1::2, 0::2] = e2
    out[1::2, 1::2] = e3

    # Add micro-detail deterministic (+-3 sRGB checkerboard where alpha > 0)
    grid_y, grid_x = np.indices((2 * h, 2 * w))
    checker = ((grid_y + grid_x) % 2) * 2 - 1  # -1 or +1
    noise = checker[..., None] * 3

    alpha_mask = out[..., 3:4] > 0
    rgb = np.clip(out[..., :3] + noise * alpha_mask, 0, 255)
    out[..., :3] = rgb

    # Strictly preserve alpha without spurious partial alpha on cutouts
    # If original alpha was 0, keep 0. If 255, keep 255.
    return out.astype(np.uint8)


def generate_normal_map(albedo_rgb: np.ndarray, albedo_alpha: np.ndarray, pom_flat: bool, is_rock_or_metal: bool) -> np.ndarray:
    """Generates LabPBR 1.3 Normal + AO + Height (_n.png) from albedo.
    albedo_rgb: (H, W, 3) float 0..255
    albedo_alpha: (H, W) uint8
    """
    h, w, _ = albedo_rgb.shape
    l_lum = (0.299 * albedo_rgb[..., 0] + 0.587 * albedo_rgb[..., 1] + 0.114 * albedo_rgb[..., 2]) / 255.0

    strength = 2.2 if is_rock_or_metal else 1.4

    if not pom_flat:
        # Wrap periodic roll for solid cubic blocks
        l_up = np.roll(l_lum, 1, axis=0)
        l_down = np.roll(l_lum, -1, axis=0)
        l_left = np.roll(l_lum, 1, axis=1)
        l_right = np.roll(l_lum, -1, axis=1)
    else:
        # Clamp edge gradients for pom_flat / items / cutouts
        l_up = np.pad(l_lum[:-1, :], ((1, 0), (0, 0)), mode="edge")
        l_down = np.pad(l_lum[1:, :], ((0, 1), (0, 0)), mode="edge")
        l_left = np.pad(l_lum[:, :-1], ((0, 0), (1, 0)), mode="edge")
        l_right = np.pad(l_lum[:, 1:], ((0, 0), (0, 1)), mode="edge")

    dx = (l_left - l_right) * strength
    dy = (l_down - l_up) * strength

    len_xy = np.sqrt(dx * dx + dy * dy)
    # Clamp length so vector stays valid
    scale = np.where(len_xy > 0.99, 0.99 / np.maximum(len_xy, 1e-5), 1.0)
    nx = dx * scale
    ny = dy * scale
    nz = np.sqrt(np.maximum(1.0 - nx * nx - ny * ny, 0.01))

    # Red & Green: normal vector mapped to 0..255
    n_r = np.clip(128.0 + nx * 127.0, 0, 255).astype(np.uint8)
    n_g = np.clip(128.0 + ny * 127.0, 0, 255).astype(np.uint8)

    # Blue: Ambient Occlusion (AO)
    mean_l = np.mean(l_lum)
    ao = np.clip(215.0 + (l_lum - mean_l) * 90.0, 140, 255).astype(np.uint8)

    # Alpha: Height (POM)
    if pom_flat:
        height = np.full((h, w), 255, dtype=np.uint8)
    else:
        height = np.clip(150.0 + (l_lum - 0.5) * 160.0, 64, 254).astype(np.uint8)

    normal_rgba = np.stack([n_r, n_g, ao, height], axis=-1)

    # Where albedo alpha == 0, force _n = (128, 128, 255, 255)
    zero_mask = albedo_alpha == 0
    normal_rgba[zero_mask] = [128, 128, 255, 255]

    return normal_rgba


def generate_specular_map(name_lower: str, albedo_rgb: np.ndarray, albedo_alpha: np.ndarray) -> np.ndarray:
    """Generates LabPBR 1.3 Specular map (_s.png) based on material classification.
    R: Roughness (perceptual smoothness inverted: high R = smoother)
    G: F0 / Metalness (230..237 = metal, dielectric < 230)
    B: Porosity / Subsurface Scattering (SSS)
    A: Emissive (1..254)
    """
    h, w, _ = albedo_rgb.shape
    l_lum = (0.299 * albedo_rgb[..., 0] + 0.587 * albedo_rgb[..., 1] + 0.114 * albedo_rgb[..., 2]) / 255.0

    r_ch = np.zeros((h, w), dtype=np.uint8)
    g_ch = np.zeros((h, w), dtype=np.uint8)
    b_ch = np.zeros((h, w), dtype=np.uint8)
    a_ch = np.zeros((h, w), dtype=np.uint8)

    r_alb = albedo_rgb[..., 0]
    g_alb = albedo_rgb[..., 1]
    b_alb = albedo_rgb[..., 2]

    # Tool detection for per-pixel handle vs head
    is_tool = any(kw in name_lower for kw in [
        "_sword", "_pickaxe", "_axe", "_shovel", "_hoe", "trident", "arrow", "mace", "spyglass", "brush"
    ])
    tool_handle_mask = np.zeros((h, w), dtype=bool)
    if is_tool and not ("golden_" in name_lower or "copper_" in name_lower):
        tool_handle_mask = (r_alb > b_alb * 1.4) & (g_alb > b_alb * 1.1) & (albedo_alpha > 0)

    # Material categorization
    # A. Metals
    is_iron = any(k in name_lower for k in [
        "iron", "anvil", "chain", "minecart", "bucket", "shears", "compass",
        "piston", "hopper", "cauldron", "rail", "bars", "heavy_core", "mace", "shield"
    ]) and not ("gold" in name_lower or "golden" in name_lower)
    is_gold = any(k in name_lower for k in ["gold", "bell", "clock", "golden_"])
    is_copper = any(k in name_lower for k in ["copper", "lightning_rod", "spyglass", "brush"]) and not is_gold
    is_netherite = any(k in name_lower for k in ["netherite", "ancient_debris", "lodestone"])

    # B. Gems, Glass, Crystals
    is_gem = any(k in name_lower for k in [
        "diamond", "emerald", "amethyst", "ruby", "lapis", "prismarine_crystals",
        "heart_of_the_sea", "ender_pearl"
    ])
    is_glass_ice = any(k in name_lower for k in [
        "glass", "ice", "packed_ice", "blue_ice", "conduit", "potion", "bottle"
    ])
    is_mineral_crystal = any(k in name_lower for k in [
        "quartz", "calcite", "bone", "ivory", "shell", "turtle_scute", "armadillo"
    ])

    # C. Emissives
    is_emissive = any(k in name_lower for k in [
        "lava", "fire", "soul_fire", "magma", "glowstone", "sea_lantern", "shroomlight",
        "froglight", "jack_o_lantern", "beacon", "end_rod", "blaze", "glow_ink",
        "glow_berries", "glow_item_frame", "ender_eye", "nether_star", "experience_bottle",
        "dragon_breath", "crying_obsidian", "respawn_anchor", "sculk_catalyst",
        "sculk_sensor", "calibrated_sculk_sensor", "sculk_shrieker", "amethyst_cluster",
        "torchflower", "redstone_lamp_on", "powered", "lit"
    ])

    # D. Foliage, Plants, Organics
    is_organic = any(k in name_lower for k in [
        "leaves", "grass", "fern", "vine", "lily", "flower", "sapling", "azalea", "moss",
        "dripleaf", "kelp", "seagrass", "coral", "cactus", "sugar_cane", "bamboo", "melon",
        "pumpkin", "apple", "berry", "carrot", "potato", "beetroot", "chorus", "mushroom",
        "fungus", "wart", "slime", "honey", "wax", "sponge", "wool", "carpet", "bed",
        "banner", "leather", "meat", "beef", "porkchop", "chicken", "mutton", "rabbit",
        "cod", "salmon", "bread", "cookie", "cake", "pie", "stew", "soup", "egg",
        "feather", "string", "web", "paper", "book"
    ])

    # E. Woods & Barks
    is_wood = any(k in name_lower for k in [
        "log", "wood", "stem", "hyphae", "planks", "stripped", "door", "trapdoor",
        "fence", "gate", "sign", "boat", "chest", "barrel", "crafting_table", "bookshelf",
        "lectern", "composter", "note_block", "jukebox", "loom", "cartography",
        "fletching", "smithing", "stick", "bowl", "bow", "crossbow", "fishing_rod"
    ])

    # Mineral defaults
    is_smooth_mineral = any(k in name_lower for k in ["polished_", "smooth_", "glazed_", "obsidian", "tiles"])

    # Classification Assignment
    if is_iron:
        r_val = np.clip(185.0 + l_lum * 55.0, 160, 240).astype(np.uint8)
        r_ch[:] = r_val
        g_ch[:] = 230
        b_ch[:] = 0
    elif is_gold:
        r_val = np.clip(205.0 + l_lum * 45.0, 180, 248).astype(np.uint8)
        r_ch[:] = r_val
        g_ch[:] = 234
        b_ch[:] = 0
    elif is_copper:
        # Per-pixel oxidized patina check
        is_patina = g_alb > (r_alb * 1.08)
        r_ch[:] = np.where(is_patina, 75, 195)
        g_ch[:] = np.where(is_patina, 12, 233)
        b_ch[:] = np.where(is_patina, 45, 0)
    elif is_netherite:
        r_val = np.clip(170.0 + l_lum * 50.0, 145, 225).astype(np.uint8)
        r_ch[:] = r_val
        g_ch[:] = 235
        b_ch[:] = 0
    elif is_gem:
        r_ch[:] = 235
        g_ch[:] = 42
        b_ch[:] = 110
    elif is_glass_ice:
        r_ch[:] = 242
        g_ch[:] = 24
        b_ch[:] = 85
    elif is_mineral_crystal:
        r_ch[:] = 145
        g_ch[:] = 18
        b_ch[:] = 75
    elif is_organic:
        if "slime" in name_lower or "honey" in name_lower:
            r_ch[:] = 215
            g_ch[:] = 20
            b_ch[:] = 210
        else:
            r_val = np.clip(45.0 + l_lum * 45.0, 35, 110).astype(np.uint8)
            r_ch[:] = r_val
            g_ch[:] = 10
            b_ch[:] = 165
    elif is_wood:
        r_val = np.clip(55.0 + l_lum * 45.0, 40, 105).astype(np.uint8)
        r_ch[:] = r_val
        g_ch[:] = 10
        b_ch[:] = 32
    elif is_smooth_mineral:
        r_val = np.clip(135.0 + l_lum * 55.0, 115, 195).astype(np.uint8)
        r_ch[:] = r_val
        g_ch[:] = 16
        b_ch[:] = 20
    else:
        # Default rough rock / dirt
        r_val = np.clip(40.0 + l_lum * 45.0, 25, 95).astype(np.uint8)
        r_ch[:] = r_val
        g_ch[:] = 12
        b_ch[:] = 48

    # Tool handle override (wood)
    if is_tool:
        r_ch[tool_handle_mask] = 65
        g_ch[tool_handle_mask] = 10
        b_ch[tool_handle_mask] = 30
        if "diamond" in name_lower:
            blade_mask = ~tool_handle_mask
            r_ch[blade_mask] = 235
            g_ch[blade_mask] = 42
        elif "stone" in name_lower:
            blade_mask = ~tool_handle_mask
            r_ch[blade_mask] = 55
            g_ch[blade_mask] = 12

    # Emissive channel
    if is_emissive:
        # Bright or glowing pixels
        emissive_mask = (l_lum > 0.45) | (b_alb > 180) | ((r_alb > 200) & (g_alb > 100))
        emiss_val = np.clip(l_lum * 235.0, 90, 250).astype(np.uint8)
        a_ch[:] = np.where(emissive_mask, emiss_val, 0)

    specular_rgba = np.stack([r_ch, g_ch, b_ch, a_ch], axis=-1)

    # Where albedo alpha == 0, force _s = (0, 0, 0, 0)
    zero_mask = albedo_alpha == 0
    specular_rgba[zero_mask] = [0, 0, 0, 0]

    return specular_rgba


def process_texture_task(task: dict) -> dict:
    """Processes a single texture entry: upscaling and LabPBR map generation."""
    rel_path = task["rel_path"]  # e.g. "assets/minecraft/textures/block/stone.png"
    name = task["name"]          # e.g. "stone.png"
    target_dir = task["target_dir"]
    is_item = task["is_item"]
    image_bytes = task["image_bytes"]
    mcmeta_bytes = task.get("mcmeta_bytes")

    base_stem = os.path.splitext(name)[0]
    out_albedo_path = os.path.join(target_dir, f"{base_stem}.png")
    out_normal_path = os.path.join(target_dir, f"{base_stem}_n.png")
    out_specular_path = os.path.join(target_dir, f"{base_stem}_s.png")
    out_mcmeta_path = os.path.join(target_dir, f"{base_stem}.png.mcmeta")

    # If preserve lock applies
    if os.path.exists(out_albedo_path):
        # Already preserved! Copy mcmeta if present and missing
        if mcmeta_bytes and not os.path.exists(out_mcmeta_path):
            with open(out_mcmeta_path, "wb") as f:
                f.write(mcmeta_bytes)
        return {"status": "skipped", "name": name, "is_item": is_item}

    # Load source image
    with Image.open(io.BytesIO(image_bytes)) as src_img:
        src_img = src_img.convert("RGBA")
        src_np = np.array(src_img)

    h, w, _ = src_np.shape
    name_lower = base_stem.lower()
    is_rock_or_metal = not is_item and not any(k in name_lower for k in ["leaves", "flower", "grass", "plant", "wool", "wood", "planks"])

    # Handle vertical animation strips
    if h > w and (h % w == 0):
        n_frames = h // w
        frame_albedos = []
        frame_normals = []
        frame_speculars = []

        for f_idx in range(n_frames):
            frame_src = src_np[f_idx * w : (f_idx + 1) * w, :, :]
            frame_32x = scale2x_epx(frame_src)
            f_rgb = frame_32x[..., :3].astype(np.float32)
            f_alpha = frame_32x[..., 3]

            has_transp = np.any(f_alpha < 250)
            pom_flat = is_pom_flat(name_lower, is_item, has_transp)

            f_norm = generate_normal_map(f_rgb, f_alpha, pom_flat, is_rock_or_metal)
            f_spec = generate_specular_map(name_lower, f_rgb, f_alpha)

            frame_albedos.append(frame_32x)
            frame_normals.append(f_norm)
            frame_speculars.append(f_spec)

        albedo_out = np.vstack(frame_albedos)
        normal_out = np.vstack(frame_normals)
        specular_out = np.vstack(frame_speculars)
    else:
        # Single frame or arbitrary ratio
        albedo_out = scale2x_epx(src_np)
        f_rgb = albedo_out[..., :3].astype(np.float32)
        f_alpha = albedo_out[..., 3]

        has_transp = np.any(f_alpha < 250)
        pom_flat = is_pom_flat(name_lower, is_item, has_transp)

        normal_out = generate_normal_map(f_rgb, f_alpha, pom_flat, is_rock_or_metal)
        specular_out = generate_specular_map(name_lower, f_rgb, f_alpha)

    # Save images
    os.makedirs(target_dir, exist_ok=True)
    Image.fromarray(albedo_out, "RGBA").save(out_albedo_path, "PNG", optimize=False)
    Image.fromarray(normal_out, "RGBA").save(out_normal_path, "PNG", optimize=False)
    Image.fromarray(specular_out, "RGBA").save(out_specular_path, "PNG", optimize=False)

    # Handle .mcmeta
    mcmeta_copied = False
    if mcmeta_bytes:
        try:
            mcmeta_json = json.loads(mcmeta_bytes.decode("utf-8"))
            if "animation" in mcmeta_json:
                anim = mcmeta_json["animation"]
                if "width" in anim:
                    anim["width"] = anim["width"] * 2
                if "height" in anim:
                    anim["height"] = anim["height"] * 2
            with open(out_mcmeta_path, "w", encoding="utf-8") as f:
                json.dump(mcmeta_json, f, indent=2)
            mcmeta_copied = True
        except Exception:
            with open(out_mcmeta_path, "wb") as f:
                f.write(mcmeta_bytes)
            mcmeta_copied = True

    return {
        "status": "generated",
        "name": name,
        "is_item": is_item,
        "mcmeta": mcmeta_copied,
    }


def main():
    start_time = time.time()
    print("=" * 70)
    print("AETHERIA LABPBR 32X - FULL PACK 100% COVERAGE PIPELINE (MC 1.21.1)")
    print("=" * 70)

    if not os.path.exists(VANILLA_JAR):
        print(f"ERROR: Vanilla jar not found at {VANILLA_JAR}")
        sys.exit(1)

    os.makedirs(BLOCK_TARGET_DIR, exist_ok=True)
    os.makedirs(ITEM_TARGET_DIR, exist_ok=True)

    with zipfile.ZipFile(VANILLA_JAR, "r") as z:
        all_names = set(z.namelist())

        block_pngs = sorted([
            f for f in all_names
            if f.startswith("assets/minecraft/textures/block/")
            and f.endswith(".png")
            and not f.endswith("_n.png")
            and not f.endswith("_s.png")
            and "/" not in f[len("assets/minecraft/textures/block/"):]
        ])

        item_pngs = sorted([
            f for f in all_names
            if f.startswith("assets/minecraft/textures/item/")
            and f.endswith(".png")
            and not f.endswith("_n.png")
            and not f.endswith("_s.png")
            and "/" not in f[len("assets/minecraft/textures/item/"):]
        ])

        print(f"Vanilla JAR extracted: {len(block_pngs)} block textures, {len(item_pngs)} item textures.")

        tasks = []
        for p in block_pngs:
            fname = os.path.basename(p)
            img_data = z.read(p)
            meta_name = p + ".mcmeta"
            meta_data = z.read(meta_name) if meta_name in all_names else None
            tasks.append({
                "rel_path": p,
                "name": fname,
                "target_dir": BLOCK_TARGET_DIR,
                "is_item": False,
                "image_bytes": img_data,
                "mcmeta_bytes": meta_data,
            })

        for p in item_pngs:
            fname = os.path.basename(p)
            img_data = z.read(p)
            meta_name = p + ".mcmeta"
            meta_data = z.read(meta_name) if meta_name in all_names else None
            tasks.append({
                "rel_path": p,
                "name": fname,
                "target_dir": ITEM_TARGET_DIR,
                "is_item": True,
                "image_bytes": img_data,
                "mcmeta_bytes": meta_data,
            })

    print(f"Total tasks prepared: {len(tasks)} (Block: {len(block_pngs)}, Item: {len(item_pngs)})")

    skipped_count = 0
    generated_blocks = 0
    generated_items = 0
    mcmeta_count = 0

    max_workers = min(os.cpu_count() or 4, 16)
    print(f"Executing batch generation with ProcessPoolExecutor (workers={max_workers})...")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_texture_task, tasks, chunksize=16))

    for res in results:
        if res["status"] == "skipped":
            skipped_count += 1
        else:
            if res["is_item"]:
                generated_items += 1
            else:
                generated_blocks += 1
            if res.get("mcmeta"):
                mcmeta_count += 1

    # Count actual files in target directories
    generate_environment_textures()
    final_block_pngs = [f for f in os.listdir(BLOCK_TARGET_DIR) if f.endswith(".png")]
    final_block_albedos = [f for f in final_block_pngs if not f.endswith("_n.png") and not f.endswith("_s.png")]
    final_item_pngs = [f for f in os.listdir(ITEM_TARGET_DIR) if f.endswith(".png")]
    final_item_albedos = [f for f in final_item_pngs if not f.endswith("_n.png") and not f.endswith("_s.png")]

    final_block_mcmeta = [f for f in os.listdir(BLOCK_TARGET_DIR) if f.endswith(".png.mcmeta")]
    final_item_mcmeta = [f for f in os.listdir(ITEM_TARGET_DIR) if f.endswith(".png.mcmeta")]

    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"Pipeline executed in {elapsed:.2f} seconds!")
    print(f"Preserved pre-existing handcrafted blocks: {skipped_count}")
    print(f"Newly generated blocks: {generated_blocks} (3 files each = {generated_blocks * 3} PNGs)")
    print(f"Newly generated items: {generated_items} (3 files each = {generated_items * 3} PNGs)")
    print(f"Animation metadata copied/adapted: {mcmeta_count}")
    print("-" * 70)
    print("DIRECTORY STATUS:")
    print(f"  textures/block/ -> {len(final_block_albedos)} albedos, {len(final_block_pngs)} total PNGs, {len(final_block_mcmeta)} .mcmeta")
    print(f"  textures/item/  -> {len(final_item_albedos)} albedos, {len(final_item_pngs)} total PNGs, {len(final_item_mcmeta)} .mcmeta")
    print("=" * 70)


if __name__ == "__main__":
    main()
