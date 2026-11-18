package com.luminary.ambientluminescence;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.resources.ResourceLocation;

/**
 * Core client logic for Ambient Luminescence (Platform-agnostic).
 * Scans local player equipment and nearby entities (ItemEntities, mobs, players)
 * to feed DynamicLightTracker without heap allocation during regular ticks.
 */
public final class AmbientLuminescenceClient {
    public static final String MOD_ID = "ambient_luminescence";
    private static int lastHeldLuminance = 0;

    private AmbientLuminescenceClient() {}

    public static void init() {
        // Initialization hook common across Fabric & NeoForge
    }

    public static void onClientTick(Minecraft client) {
        if (client == null) return;
        DynamicLightTracker.onClientTick();

        Player player = client.player;
        ClientLevel level = client.level;
        if (player == null || level == null) return;

        // 1. Process player main-hand and off-hand light
        int mainHandLum = getStackLuminance(player.getMainHandItem());
        int offHandLum = getStackLuminance(player.getOffhandItem());
        int playerLum = Math.max(mainHandLum, offHandLum);

        lastHeldLuminance = playerLum;
        DynamicLightTracker.updateEntitySource(
            player.getId(),
            player.getBlockX(),
            player.getBlockY(),
            player.getBlockZ(),
            playerLum
        );

        // 2. Scan nearby entities within render radius (e.g. 16 blocks)
        for (Entity entity : level.entitiesForRendering()) {
            if (entity == null || entity == player) continue;

            if (entity instanceof ItemEntity itemEntity) {
                int itemLum = getStackLuminance(itemEntity.getItem());
                DynamicLightTracker.updateEntitySource(
                    itemEntity.getId(),
                    itemEntity.getBlockX(),
                    itemEntity.getBlockY(),
                    itemEntity.getBlockZ(),
                    itemLum
                );
            } else if (entity instanceof Player otherPlayer) {
                int mLum = getStackLuminance(otherPlayer.getMainHandItem());
                int oLum = getStackLuminance(otherPlayer.getOffhandItem());
                int oPlayerLum = Math.max(mLum, oLum);
                DynamicLightTracker.updateEntitySource(
                    otherPlayer.getId(),
                    otherPlayer.getBlockX(),
                    otherPlayer.getBlockY(),
                    otherPlayer.getBlockZ(),
                    oPlayerLum
                );
            }
        }
    }

    public static int getStackLuminance(ItemStack stack) {
        if (stack == null || stack.isEmpty()) return 0;
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(stack.getItem());
        if (id == null) return 0;
        return DynamicLightRegistry.getLuminance(id.toString());
    }

    public static int getLastHeldLuminance() {
        return lastHeldLuminance;
    }
}
