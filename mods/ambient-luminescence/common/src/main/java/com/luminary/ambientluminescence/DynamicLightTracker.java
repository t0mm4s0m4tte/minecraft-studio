package com.luminary.ambientluminescence;

import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

/**
 * Tracciamento spaziale a coordinate discretizzate (BlockPos hash).
 * Gestisce il throttling degli aggiornamenti per prevenire lag spike
 * e ricalcoli multipli sulla pipeline di rendering chunk Sodium/Iris.
 */
public final class DynamicLightTracker {
    public static final class LightNode {
        public final long packedPos;
        public final int luminance;
        public long lastTickUpdated;

        public LightNode(long packedPos, int luminance, long tick) {
            this.packedPos = packedPos;
            this.luminance = luminance;
            this.lastTickUpdated = tick;
        }
    }

    private static final Map<Integer, LightNode> ACTIVE_ENTITIES = new ConcurrentHashMap<>();
    private static long currentClientTick = 0;

    private DynamicLightTracker() {}

    public static void onClientTick() {
        currentClientTick++;
        // Pulizia nodi obsoleti/morti ogni 100 tick
        if (currentClientTick % 100 == 0) {
            ACTIVE_ENTITIES.entrySet().removeIf(entry -> (currentClientTick - entry.getValue().lastTickUpdated) > 20);
        }
    }

    /**
     * Aggiorna o rimuove la sorgente luminosa associata all'ID entità.
     * Ritorna true se la sorgente si è spostata di blocco o ha variato intensità,
     * richiedendo un refresh della sezione chunk.
     */
    public static boolean updateEntitySource(int entityId, int blockX, int blockY, int blockZ, int luminance) {
        if (luminance <= 0) {
            return ACTIVE_ENTITIES.remove(entityId) != null;
        }

        long packed = packPos(blockX, blockY, blockZ);
        LightNode existing = ACTIVE_ENTITIES.get(entityId);

        if (existing == null) {
            ACTIVE_ENTITIES.put(entityId, new LightNode(packed, luminance, currentClientTick));
            return true;
        }

        existing.lastTickUpdated = currentClientTick;
        if (existing.packedPos != packed || existing.luminance != luminance) {
            ACTIVE_ENTITIES.put(entityId, new LightNode(packed, luminance, currentClientTick));
            return true;
        }

        return false;
    }

    public static void removeEntitySource(int entityId) {
        ACTIVE_ENTITIES.remove(entityId);
    }

    public static int getLuminanceAt(int blockX, int blockY, int blockZ) {
        long target = packPos(blockX, blockY, blockZ);
        int maxLuminance = 0;
        for (LightNode node : ACTIVE_ENTITIES.values()) {
            if (node.packedPos == target) {
                if (node.luminance > maxLuminance) {
                    maxLuminance = node.luminance;
                }
            }
        }
        return maxLuminance;
    }

    public static long packPos(int x, int y, int z) {
        return (((long) x & 0x3FFFFFF) << 38) | (((long) y & 0xFFF) << 26) | ((long) z & 0x3FFFFFF);
    }
}
