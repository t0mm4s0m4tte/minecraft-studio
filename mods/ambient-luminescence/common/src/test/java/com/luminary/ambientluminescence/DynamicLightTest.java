package com.luminary.ambientluminescence;

import it.unimi.dsi.fastutil.longs.LongOpenHashSet;
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

    @Test
    public void testZeroAllocDoubleBufferingAndDirtySections() {
        // Tick 1: Aggiunta sorgente luminosa
        DynamicLightTracker.updateEntitySource(101, 20, 64, 20, 14);
        DynamicLightTracker.onClientTick();

        assertEquals(14, DynamicLightTracker.getLuminanceAt(20, 64, 20));
        LongOpenHashSet dirty1 = DynamicLightTracker.consumeDirtySections();
        assertNotNull(dirty1);
        assertFalse(dirty1.isEmpty());

        // Consumo successivo nello stesso tick o stato vuoto deve essere null
        assertNull(DynamicLightTracker.consumeDirtySections());

        // Tick 2: Sorgente mantenuta alla stessa posizione -> dirty sections null
        DynamicLightTracker.updateEntitySource(101, 20, 64, 20, 14);
        DynamicLightTracker.onClientTick();
        assertNull(DynamicLightTracker.consumeDirtySections());
        assertEquals(14, DynamicLightTracker.getLuminanceAt(20, 64, 20));

        // Tick 3: Nessun aggiornamento sorgente (sorgente rimossa/spenta) -> luce torna a 0 e notifica dirty
        DynamicLightTracker.onClientTick();
        assertEquals(0, DynamicLightTracker.getLuminanceAt(20, 64, 20));
        LongOpenHashSet dirtyRemoved = DynamicLightTracker.consumeDirtySections();
        assertNotNull(dirtyRemoved);
        assertFalse(dirtyRemoved.isEmpty());

        // Tick 4: Ancora spenta -> stabile, dirty sections null
        DynamicLightTracker.onClientTick();
        assertNull(DynamicLightTracker.consumeDirtySections());
        assertEquals(0, DynamicLightTracker.getLuminanceAt(20, 64, 20));
    }
}
