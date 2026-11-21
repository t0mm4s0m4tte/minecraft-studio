package com.luminary.ambientluminescence;

import it.unimi.dsi.fastutil.longs.LongIterator;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.boss.enderdragon.EndCrystal;
import net.minecraft.world.entity.animal.allay.Allay;
import net.minecraft.world.entity.projectile.LargeFireball;
import net.minecraft.world.entity.projectile.SmallFireball;
import net.minecraft.world.entity.GlowSquid;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Blaze;
import net.minecraft.world.entity.monster.MagmaCube;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.SpectralArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.BlockItemStateProperties;

/**
 * Core client logic for Ambient Luminescence (Platform-agnostic).
 * Scans local player equipment and nearby entities (ItemEntities, mobs, projectiles, players),
 * evaluates 1.21.1 DataComponents & underwater flame rules, updates DynamicLightTracker,
 * and triggers chunk light rebuilds on dirty sections so dropped torches glow immediately!
 */
public final class AmbientLuminescenceClient {
    public static final String MOD_ID = "ambient_luminescence";
    private static int lastHeldLuminance = 0;
    private static int configPollTicks = 0;

    private AmbientLuminescenceClient() {}

    public static void init() {
        // Common initialization hook across Fabric & NeoForge
    }

    public static void onClientTick(Minecraft client) {
        if (client == null) return;

        LuminescenceConfig.initAsync(client.gameDirectory.toPath().resolve("config"));
        configPollTicks++;
        if (configPollTicks >= 100) {
            configPollTicks = 0;
            LuminescenceConfig.pollReloadAsync();
        }

        LuminescenceConfig cfg = LuminescenceConfig.get();
        if (!cfg.enabled) {
            DynamicLightTracker.clear();
            return;
        }

        Player player = client.player;
        ClientLevel level = client.level;
        if (player == null || level == null) {
            DynamicLightTracker.clear();
            return;
        }

        // 1. Process local player main-hand, off-hand, and helmet light (with underwater flame rule)
        boolean playerUnderwater = player.isUnderWater();
        int mainHandLum = getStackLuminance(player.getMainHandItem(), playerUnderwater && cfg.underwaterFlameExtinguish);
        int offHandLum = getStackLuminance(player.getOffhandItem(), playerUnderwater && cfg.underwaterFlameExtinguish);
        int headLum = getStackLuminance(player.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.HEAD), playerUnderwater && cfg.underwaterFlameExtinguish);
        int playerLum = Math.max(Math.max(mainHandLum, offHandLum), headLum);
        if (cfg.lightFireEntities && player.isOnFire()) {
            playerLum = Math.max(playerLum, 15);
        }

        lastHeldLuminance = playerLum;
        if (playerLum > 0) {
            DynamicLightTracker.updateEntitySource(
                player.getId(),
                player.getBlockX(),
                player.getBlockY(),
                player.getBlockZ(),
                playerLum
            );
        }

        // 2. Scan nearby entities (dropped ItemEntity torches, mobs, glowing projectiles, other players)
        for (Entity entity : level.entitiesForRendering()) {
            if (entity == null || entity == player) continue;
            if (entity.distanceToSqr(player) > 64.0 * 64.0) continue;

            int entityLum = 0;
            boolean underwater = entity.isInWater();

            if (entity instanceof ItemEntity itemEntity) {
                if (cfg.lightDroppedItems) {
                    entityLum = getStackLuminance(itemEntity.getItem(), underwater && cfg.underwaterFlameExtinguish);
                }
            } else if (entity instanceof Player otherPlayer) {
                if (cfg.lightEntities) {
                    int mLum = getStackLuminance(otherPlayer.getMainHandItem(), otherPlayer.isUnderWater() && cfg.underwaterFlameExtinguish);
                    int oLum = getStackLuminance(otherPlayer.getOffhandItem(), otherPlayer.isUnderWater() && cfg.underwaterFlameExtinguish);
                    entityLum = Math.max(mLum, oLum);
                }
            } else if (cfg.lightEntities) {
                if (entity instanceof Blaze || entity instanceof MagmaCube) {
                    entityLum = 12;
                } else if (entity instanceof GlowSquid) {
                    entityLum = 10;
                } else if (entity instanceof SpectralArrow) {
                    entityLum = 10;
                } else if (entity instanceof Allay) {
                    entityLum = 8;
                } else if (entity instanceof EndCrystal) {
                    entityLum = 12;
                } else if (entity instanceof SmallFireball || entity instanceof LargeFireball) {
                    entityLum = 12;
                }
                if (entity instanceof net.minecraft.world.entity.LivingEntity living) {
                    int heldLum = Math.max(
                        getStackLuminance(living.getMainHandItem(), underwater && cfg.underwaterFlameExtinguish),
                        getStackLuminance(living.getOffhandItem(), underwater && cfg.underwaterFlameExtinguish)
                    );
                    entityLum = Math.max(entityLum, heldLum);
                }
            }

            if (cfg.lightFireEntities && entity.isOnFire() && !underwater) {
                entityLum = Math.max(entityLum, 15);
            }

            if (entityLum > 0) {
                DynamicLightTracker.updateEntitySource(
                    entity.getId(),
                    entity.getBlockX(),
                    entity.getBlockY(),
                    entity.getBlockZ(),
                    entityLum
                );
            }
        }

        // 3. Swap double-buffered snapshot & schedule chunk rebuilds on dirty sections
        DynamicLightTracker.onClientTick();
        LongOpenHashSet dirty = DynamicLightTracker.consumeDirtySections();
        if (dirty != null && client.levelRenderer != null) {
            LongIterator it = dirty.iterator();
            while (it.hasNext()) {
                long sec = it.nextLong();
                int sx = DynamicLightTracker.unpackX(sec);
                int sy = DynamicLightTracker.unpackY(sec);
                int sz = DynamicLightTracker.unpackZ(sec);
                client.levelRenderer.setSectionDirty(sx, sy, sz);
            }
        }
    }

    public static int getStackLuminance(ItemStack stack) {
        return getStackLuminance(stack, false);
    }

    public static int getStackLuminance(ItemStack stack, boolean underwater) {
        if (stack == null || stack.isEmpty()) return 0;
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(stack.getItem());
        if (id == null) return 0;
        String itemId = id.toString();

        // Underwater flame extinguishment rule: open-flame torches turn off underwater
        if (underwater && (itemId.equals("minecraft:torch")
                || itemId.equals("minecraft:soul_torch")
                || itemId.equals("minecraft:redstone_torch")
                || itemId.equals("minecraft:campfire")
                || itemId.equals("minecraft:soul_campfire"))) {
            return 0;
        }

        // Check 1.21.1 DataComponents.BLOCK_STATE (e.g. light block level, copper_bulb lit state)
        try {
            BlockItemStateProperties stateProps = stack.get(DataComponents.BLOCK_STATE);
            if (stateProps != null && !stateProps.isEmpty()) {
                String levelVal = stateProps.properties().get("level");
                if (levelVal != null) {
                    int parsed = Integer.parseInt(levelVal);
                    if (parsed >= 0 && parsed <= 15) return parsed;
                }
                String litVal = stateProps.properties().get("lit");
                if ("false".equalsIgnoreCase(litVal)) {
                    return 0;
                }
            }
        } catch (Throwable ignored) {}

        int fastLum = DynamicLightRegistry.getLuminance(stack.getItem());
        return fastLum > 0 ? fastLum : DynamicLightRegistry.getLuminance(itemId);
    }

    public static int getLastHeldLuminance() {
        return lastHeldLuminance;
    }
}
