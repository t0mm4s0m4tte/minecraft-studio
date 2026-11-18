package com.luminary.ambientluminescence;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class DynamicLightTest {

    @BeforeEach
    void setup() {
        // Reset or verify baseline registry
    }

    @Test
    void testRegistryValues() {
        assertEquals(14, DynamicLightRegistry.getLuminance("minecraft:torch"));
        assertEquals(15, DynamicLightRegistry.getLuminance("minecraft:lantern"));
        assertEquals(15, DynamicLightRegistry.getLuminance("minecraft:copper_bulb"));
        assertEquals(10, DynamicLightRegistry.getLuminance("minecraft:soul_torch"));
        assertEquals(0, DynamicLightRegistry.getLuminance("minecraft:dirt"));
        assertTrue(DynamicLightRegistry.isLightSource("minecraft:torch"));
        assertFalse(DynamicLightRegistry.isLightSource("minecraft:stone"));
    }

    @Test
    void testTrackerSpatialTracking() {
        int entityId = 1001;
        // Initial placement
        boolean changed = DynamicLightTracker.updateEntitySource(entityId, 10, 64, 20, 14);
        assertTrue(changed, "First update should trigger a state change");
        assertEquals(14, DynamicLightTracker.getLuminanceAt(10, 64, 20));

        // Same position & intensity
        boolean redundant = DynamicLightTracker.updateEntitySource(entityId, 10, 64, 20, 14);
        assertFalse(redundant, "Identical position and luminance should not trigger state change");

        // Movement
        boolean moved = DynamicLightTracker.updateEntitySource(entityId, 11, 64, 20, 14);
        assertTrue(moved, "Moving to adjacent block must trigger change");
        assertEquals(14, DynamicLightTracker.getLuminanceAt(11, 64, 20));

        // Removal
        DynamicLightTracker.removeEntitySource(entityId);
        assertEquals(0, DynamicLightTracker.getLuminanceAt(11, 64, 20));
    }
}
