package com.luminary.ambientluminescence;

import it.unimi.dsi.fastutil.longs.Long2IntMap;
import it.unimi.dsi.fastutil.longs.Long2IntMaps;
import it.unimi.dsi.fastutil.longs.Long2IntOpenHashMap;
import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Spatial light tracking engine with precomputed 3D radial falloff (radius 4..14)
 * and dirty-chunk tracking for Sodium + Iris + Vanilla chunk light rebuilds.
 * Strictly zero-allocation double-buffering during client render/tick loops.
 */
public final class DynamicLightTracker {
    private static final Long2IntOpenHashMap MAP_A = new Long2IntOpenHashMap();
    private static final Long2IntOpenHashMap MAP_B = new Long2IntOpenHashMap();
    private static final LongOpenHashSet DIRTY_A = new LongOpenHashSet();
    private static final LongOpenHashSet DIRTY_B = new LongOpenHashSet();

    private static final Long2IntOpenHashMap PREV_SOURCES = new Long2IntOpenHashMap();
    private static final Long2IntOpenHashMap CURR_SOURCES = new Long2IntOpenHashMap();

    private static final int[][][] DIST_COST = new int[15][15][15];

    private static Long2IntOpenHashMap activeWorkingMap;
    private static LongOpenHashSet activeDirtySet;
    private static final AtomicReference<Long2IntOpenHashMap> LIGHT_MAP_SNAPSHOT;

    static {
        MAP_A.defaultReturnValue(0);
        MAP_B.defaultReturnValue(0);
        PREV_SOURCES.defaultReturnValue(0);
        CURR_SOURCES.defaultReturnValue(0);

        for (int x = 0; x <= 14; x++) {
            for (int y = 0; y <= 14; y++) {
                for (int z = 0; z <= 14; z++) {
                    double dist = Math.sqrt(x * x + y * y + z * z);
                    DIST_COST[x][y][z] = (int) Math.round(dist);
                }
            }
        }

        activeWorkingMap = MAP_A;
        activeDirtySet = DIRTY_A;
        LIGHT_MAP_SNAPSHOT = new AtomicReference<>(MAP_B);
    }

    private DynamicLightTracker() {}

    public static void onClientTick() {
        synchronized (MAP_A) {
            activeDirtySet.clear();
            for (Long2IntMap.Entry entry : Long2IntMaps.fastIterable(CURR_SOURCES)) {
                long pos = entry.getLongKey();
                int lum = entry.getIntValue();
                if (PREV_SOURCES.get(pos) != lum) {
                    markSectionsAround(unpackX(pos), unpackY(pos), unpackZ(pos), lum);
                }
            }
            for (Long2IntMap.Entry entry : Long2IntMaps.fastIterable(PREV_SOURCES)) {
                long pos = entry.getLongKey();
                int prevLum = entry.getIntValue();
                if (CURR_SOURCES.get(pos) != prevLum) {
                    markSectionsAround(unpackX(pos), unpackY(pos), unpackZ(pos), prevLum);
                }
            }

            PREV_SOURCES.clear();
            PREV_SOURCES.putAll(CURR_SOURCES);
            CURR_SOURCES.clear();

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

    public static boolean updateEntitySource(int entityId, int blockX, int blockY, int blockZ, int luminance) {
        if (luminance <= 0) return false;
        int clampedLum = Math.min(luminance, 15);
        long centerPacked = packPos(blockX, blockY, blockZ);

        synchronized (MAP_A) {
            int prevSrc = CURR_SOURCES.get(centerPacked);
            if (clampedLum > prevSrc) {
                CURR_SOURCES.put(centerPacked, clampedLum);
            }

            if (clampedLum > activeWorkingMap.get(centerPacked)) {
                activeWorkingMap.put(centerPacked, clampedLum);
            }

            int radius = Math.min(clampedLum - 1, Math.max(4, Math.min(LuminescenceConfig.get().maxRadius, 14)));
            for (int dx = -radius; dx <= radius; dx++) {
                int ax = Math.abs(dx);
                int maxDy = radius - ax;
                for (int dy = -maxDy; dy <= maxDy; dy++) {
                    int ay = Math.abs(dy);
                    int maxDz = maxDy - ay;
                    for (int dz = -maxDz; dz <= maxDz; dz++) {
                        if (dx == 0 && dy == 0 && dz == 0) continue;
                        int falloffLum = clampedLum - DIST_COST[ax][ay][Math.abs(dz)];
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
