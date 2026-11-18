package com.luminary.ambientluminescence;

import java.util.HashMap;
import java.util.Map;

/**
 * Registro statico ad alta efficienza per l'assegnazione dei valori di luminanza (0..15)
 * a item, blocchi tenuti in mano o entità cadute a terra.
 * Zero-allocation durante il tick loop tramite cache diretta O(1).
 */
public final class DynamicLightRegistry {
    private static final Map<String, Integer> LIGHT_LEVELS = new HashMap<>();

    static {
        // Fonti standard vanilla
        register("minecraft:torch", 14);
        register("minecraft:soul_torch", 10);
        register("minecraft:redstone_torch", 7);
        register("minecraft:lantern", 15);
        register("minecraft:soul_lantern", 10);
        register("minecraft:glowstone", 15);
        register("minecraft:glowstone_dust", 8);
        register("minecraft:sea_lantern", 15);
        register("minecraft:shroomlight", 15);
        register("minecraft:magma_block", 3);
        register("minecraft:crying_obsidian", 10);
        register("minecraft:lava_bucket", 15);
        register("minecraft:glow_berries", 14);
        register("minecraft:glow_ink_sac", 8);
        register("minecraft:glow_item_frame", 8);
        register("minecraft:amethyst_cluster", 5);
        register("minecraft:small_amethyst_bud", 1);
        register("minecraft:medium_amethyst_bud", 2);
        register("minecraft:large_amethyst_bud", 4);

        // Blocchi Trial Chambers & Update 1.21
        register("minecraft:copper_bulb", 15);
        register("minecraft:exposed_copper_bulb", 12);
        register("minecraft:weathered_copper_bulb", 8);
        register("minecraft:oxidized_copper_bulb", 4);
        register("minecraft:trial_spawner", 11);
        register("minecraft:vault", 6);
    }

    private DynamicLightRegistry() {}

    public static void register(String itemId, int luminance) {
        if (luminance >= 1 && luminance <= 15) {
            LIGHT_LEVELS.put(itemId, luminance);
        }
    }

    public static int getLuminance(String itemId) {
        return LIGHT_LEVELS.getOrDefault(itemId, 0);
    }

    public static boolean isLightSource(String itemId) {
        return LIGHT_LEVELS.containsKey(itemId);
    }
}
