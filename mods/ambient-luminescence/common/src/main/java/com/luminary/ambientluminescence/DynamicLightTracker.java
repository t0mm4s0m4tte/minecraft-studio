package com.luminary.ambientluminescence;

import it.unimi.dsi.fastutil.longs.Long2IntOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongIterator;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Spatial light tracking engine with radial 3D block light falloff (radius 14)
 * and dirty-chunk tracking for Sodium + Iris + Vanilla chunk light rebuilds.
 * Uses zero-allocation double-buffering during client render/tick loops.
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

    private static final Long2IntOpenHashMap MAP_A = new Long2IntOpenHashMap();
    private static final Long2IntOpenHashMap MAP_B = new Long2IntOpenHashMap();
    private static final LongOpenHashSet DIRTY_A = new LongOpenHashSet();
    private static final LongOpenHashSet DIRTY_B = new LongOpenHashSet();

    private static final Long2IntOpenHashMap PREV_SOURCES = new Long2IntOpenHashMap();
    private static final Long2IntOpenHashMap CURR_SOURCES = new Long2IntOpenHashMap();

    private static Long2IntOpenHashMap activeWorkingMap;
    private static LongOpenHashSet activeDirtySet;

    private static final AtomicReference<Long2IntOpenHashMap> LIGHT_MAP_SNAPSHOT;
    private static long currentClientTick = 0;

    static {
        MAP_A.defaultReturnValue(0);
        MAP_B.defaultReturnValue(0);
        PREV_SOURCES.defaultReturnValue(0);
        CURR_SOURCES.defaultReturnValue(0);

        activeWorkingMap = MAP_A;
        activeDirtySet = DIRTY_A;
        LIGHT_MAP_SNAPSHOT = new AtomicReference<>(MAP_B);
    }

    private DynamicLightTracker() {}

    public static void onClientTick() {
        currentClientTick++;
        synchronized (MAP_A) {
            // Detect which light sources moved, appeared, or disappeared since last tick
            activeDirtySet.clear();
            for (Long2IntOpenHashMap.Entry entry : CURR_SOURCES.long2IntEntrySet()) {
                long pos = entry.getLongKey();
                int lum = entry.getIntValue();
                if (PREV_SOURCES.get(pos) != lum) {
                    markSectionsAround(unpackX(pos), unpackY(pos), unpackZ(pos), lum);
                }
            }
            for (Long2IntOpenHashMap.Entry entry : PREV_SOURCES.long2IntEntrySet()) {
                long pos = entry.getLongKey();
                int prevLum = entry.getIntValue();
                if (CURR_SOURCES.get(pos) != prevLum) {
                    markSectionsAround(unpackX(pos), unpackY(pos), unpackZ(pos), prevLum);
                }
            }

            PREV_SOURCES.clear();
            PREV_SOURCES.putAll(CURR_SOURCES);
            CURR_SOURCES.clear();

            // Swap working map with published snapshot with zero allocations
            Long2IntOpenHashMap publishedMap = activeWorkingMap;
            LIGHT_MAP_SNAPSHOT.set(publishedMap);

            Long2IntOpenHashMap nextWorkingMap = (activeWorkingMap == MAP_A) ? MAP_B : MAP_A;
            nextWorkingMap.clear();
            activeWorkingMap = nextWorkingMap;
        }
    }

    private static void markSectionsAround(int bx, int by, int bz, int radius) {
        int r = Math.min(Math.max(radius, 1), 15);
        int minSecX = (bx - r) >> 4;
        int maxSecX = (bx + r) >> 4;
        int minSecY = (by - r) >> 4;
        int maxSecY = (by + r) >> 4;
        int minSecZ = (bz - r) >> 4;
        int maxSecZ = (bz + r) >> 4;
        for (int sx = minSecX; sx <= maxSecX; sx++) {
            for (int sy = minSecY; sy <= maxSecY; sy++) {
                for (int sz = minSecZ; sz <= maxSecZ; sz++) {
                    activeDirtySet.add(packPos(sx, sy, sz));
                }
            }
        }
    }

    public static LongOpenHashSet consumeDirtySections() {
        synchronized (MAP_A) {
            if (activeDirtySet.isEmpty()) return null;
            LongOpenHashSet toReturn = activeDirtySet;
            activeDirtySet = (activeDirtySet == DIRTY_A) ? DIRTY_B : DIRTY_A;
            activeDirtySet.clear();
            return toReturn;
        }
    }

    /**
     * Registers a dynamic light source and propagates radial falloff into surrounding blocks
     * so dropped torches, items, and entities illuminate a smooth 3D sphere of blocks!
     */
    public static boolean updateEntitySource(int entityId, int blockX, int blockY, int blockZ, int luminance) {
        if (luminance <= 0) return false;
        int clampedLum = Math.min(luminance, 15);
        long centerPacked = packPos(blockX, blockY, blockZ);

        synchronized (MAP_A) {
            int prevSrc = CURR_SOURCES.get(centerPacked);
            if (clampedLum > prevSrc) {
                CURR_SOURCES.put(centerPacked, clampedLum);
            }

            // Ensure center block always has exact source luminance
            if (clampedLum > activeWorkingMap.get(centerPacked)) {
                activeWorkingMap.put(centerPacked, clampedLum);
            }

            // Radial Euclidean falloff across nearby blocks
            int radius = Math.min(clampedLum - 1, 12);
            for (int dx = -radius; dx <= radius; dx++) {
                int maxDy = radius - Math.abs(dx);
                for (int dy = -maxDy; dy <= maxDy; dy++) {
                    int maxDz = maxDy - Math.abs(dy);
                    for (int dz = -maxDz; dz <= maxDz; dz++) {
                        if (dx == 0 && dy == 0 && dz == 0) continue;
                        double dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
                        int falloffLum = (int) Math.round(clampedLum - dist * 1.25);
                        if (falloffLum > 0) {
                            long p = packPos(blockX + dx, blockY + dy, blockZ + dz);
                            int cur = activeWorkingMap.get(p);
                            if (falloffLum > cur) {
                                activeWorkingMap.put(p, falloffLum);
                            }
                        }
                    }
                }
            }
        }
        return true;
    }

    public static void removeEntitySource(int entityId) {
        // Handled automatically by tick double-buffering
    }

    public static int getLuminanceAt(int blockX, int blockY, int blockZ) {
        long target = packPos(blockX, blockY, blockZ);
        return LIGHT_MAP_SNAPSHOT.get().get(target);
    }

    public static long packPos(int x, int y, int z) {
        return (((long) x & 0x3FFFFFFL) << 38) | (((long) z & 0x3FFFFFFL) << 12) | ((long) y & 0xFFFL);
    }

    public static int unpackX(long packed) {
        return (int) (packed >> 38);
    }

    public static int unpackY(long packed) {
        return (int) ((packed << 52) >> 52);
    }

    public static int unpackZ(long packed) {
        return (int) ((packed << 26) >> 38);
    }

    public static void clear() {
        synchronized (MAP_A) {
            MAP_A.clear();
            MAP_B.clear();
            DIRTY_A.clear();
            DIRTY_B.clear();
            PREV_SOURCES.clear();
            CURR_SOURCES.clear();
            activeWorkingMap = MAP_A;
            activeDirtySet = DIRTY_A;
            LIGHT_MAP_SNAPSHOT.set(MAP_B);
        }
    }
}
