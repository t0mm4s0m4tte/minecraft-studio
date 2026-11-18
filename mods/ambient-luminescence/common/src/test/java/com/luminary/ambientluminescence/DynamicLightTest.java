package com.luminary.ambientluminescence;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class DynamicLightTest {
    @BeforeEach
    public void setup() {
        DynamicLightTracker.clear();
    }

    @Test
    public void testRegistryLookup() {
        assertEquals(14, DynamicLightRegistry.getLuminance("minecraft:torch"));
        assertEquals(15, DynamicLightRegistry.getLuminance("minecraft:lantern"));
        assertEquals(15, DynamicLightRegistry.getLuminance("minecraft:copper_bulb"));
        assertEquals(0, DynamicLightRegistry.getLuminance("minecraft:stone"));
    }

    @Test
    public void testSpatialTrackingAndSnapshotSwap() {
        DynamicLightTracker.updateEntitySource(100, 10, 64, 10, 15);
        DynamicLightTracker.onClientTick();
        
        assertEquals(15, DynamicLightTracker.getLuminanceAt(10, 64, 10));
        assertTrue(DynamicLightTracker.getLuminanceAt(11, 64, 10) >= 13);
        assertEquals(0, DynamicLightTracker.getLuminanceAt(50, 64, 50));
    }
}
