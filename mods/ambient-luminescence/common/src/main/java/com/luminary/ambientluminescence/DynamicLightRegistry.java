package com.luminary.ambientluminescence;

import it.unimi.dsi.fastutil.objects.Reference2IntOpenHashMap;
import it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;

/**
 * High-efficiency item luminance registry.
 * Uses FastUtil Reference2IntOpenHashMap for runtime item identity lookup O(1)
 * and an Object2IntOpenHashMap for string-based lookup, avoiding un-bootstrapped Items.* clinit.
 */
public final class DynamicLightRegistry {
    private static final Reference2IntOpenHashMap<Item> ITEM_LIGHTS = new Reference2IntOpenHashMap<>();
    private static final Object2IntOpenHashMap<String> STRING_LIGHTS = new Object2IntOpenHashMap<>();

    static {
        ITEM_LIGHTS.defaultReturnValue(0);
        STRING_LIGHTS.defaultReturnValue(0);

        // Core vanilla light sources registered by ResourceLocation string
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

        // Trial Chambers 1.21 light blocks
        register("minecraft:copper_bulb", 15);
        register("minecraft:exposed_copper_bulb", 12);
        register("minecraft:weathered_copper_bulb", 8);
        register("minecraft:oxidized_copper_bulb", 4);

        // Additional MC 1.21.1 dynamic light sources
        register("minecraft:beacon", 15);
        register("minecraft:conduit", 15);
        register("minecraft:end_rod", 14);
        register("minecraft:jack_o_lantern", 15);
        register("minecraft:campfire", 15);
        register("minecraft:soul_campfire", 10);
        register("minecraft:ochre_froglight", 15);
        register("minecraft:verdant_froglight", 15);
        register("minecraft:pearlescent_froglight", 15);
        register("minecraft:respawn_anchor", 15);
        register("minecraft:enchanting_table", 7);
        register("minecraft:ender_chest", 7);
        register("minecraft:blaze_rod", 10);
        register("minecraft:blaze_powder", 6);
        register("minecraft:magma_cream", 6);
        register("minecraft:prismarine_crystals", 6);

        // Extended 1.21.1 Trial Chambers, Sculk, Aquatic & Candles
        register("minecraft:trial_spawner", 8);
        register("minecraft:vault", 12);
        register("minecraft:sea_pickle", 12);
        register("minecraft:sculk_catalyst", 6);
        register("minecraft:glow_lichen", 7);
        register("minecraft:spectral_arrow", 10);
        register("minecraft:ender_eye", 8);
        register("minecraft:dragon_egg", 1);
        register("minecraft:brown_mushroom", 1);
        register("minecraft:candle", 6);
        register("minecraft:white_candle", 6);
        register("minecraft:orange_candle", 6);
        register("minecraft:magenta_candle", 6);
        register("minecraft:light_blue_candle", 6);
        register("minecraft:yellow_candle", 6);
        register("minecraft:lime_candle", 6);
        register("minecraft:pink_candle", 6);
        register("minecraft:gray_candle", 6);
        register("minecraft:light_gray_candle", 6);
        register("minecraft:cyan_candle", 6);
        register("minecraft:purple_candle", 6);
        register("minecraft:blue_candle", 6);
        register("minecraft:brown_candle", 6);
        register("minecraft:green_candle", 6);
        register("minecraft:red_candle", 6);
        register("minecraft:black_candle", 6);
        register("minecraft:nether_star", 12);
        register("minecraft:fire_charge", 10);
        register("minecraft:brewing_stand", 1);
        register("minecraft:sculk_sensor", 1);
        register("minecraft:calibrated_sculk_sensor", 1);
    }

    private DynamicLightRegistry() {}

    public static void register(String itemId, int luminance) {
        if (itemId != null && luminance >= 1 && luminance <= 15) {
            STRING_LIGHTS.put(itemId, luminance);
            try {
                ResourceLocation rl = ResourceLocation.tryParse(itemId);
                if (rl != null && BuiltInRegistries.ITEM != null) {
                    Item item = BuiltInRegistries.ITEM.get(rl);
                    if (item != null) {
                        ITEM_LIGHTS.put(item, luminance);
                    }
                }
            } catch (Throwable ignored) {
                // Allows running in unbootstrapped unit test environments
            }
        }
    }

    public static void register(Item item, int luminance) {
        if (item != null && luminance >= 1 && luminance <= 15) {
            ITEM_LIGHTS.put(item, luminance);
        }
    }

    public static int getLuminance(Item item) {
        if (item == null) return 0;
        int lum = ITEM_LIGHTS.getInt(item);
        if (lum > 0) return lum;
        try {
            ResourceLocation key = BuiltInRegistries.ITEM.getKey(item);
            if (key != null) {
                int found = STRING_LIGHTS.getInt(key.toString());
                if (found > 0) {
                    ITEM_LIGHTS.put(item, found);
                }
                return found;
            }
        } catch (Throwable ignored) {}
        return 0;
    }

    public static int getLuminance(String itemId) {
        if (itemId == null) return 0;
        return STRING_LIGHTS.getInt(itemId);
    }

    public static boolean isLightSource(Item item) {
        return getLuminance(item) > 0;
    }

    public static boolean isLightSource(String itemId) {
        return getLuminance(itemId) > 0;
    }
}
