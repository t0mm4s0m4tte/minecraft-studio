package com.luminary.ambientluminescence;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.minecraft.Util;

import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Pure Java client configuration for Ambient Luminescence.
 * Handles async file IO and safe fallbacks for corrupted/missing config files.
 */
public final class LuminescenceConfig {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static volatile LuminescenceConfig INSTANCE = new LuminescenceConfig();
    private static final AtomicBoolean INITIALIZED = new AtomicBoolean(false);

    public boolean enabled = true;
    public int maxRadius = 12; // Clamped between 4 and 14
    public boolean underwaterFlameExtinguish = true;
    public boolean lightEntities = true;
    public boolean lightDroppedItems = true;
    public boolean lightFireEntities = true;

    public LuminescenceConfig() {}

    public static LuminescenceConfig get() {
        return INSTANCE;
    }

    public static LuminescenceConfig loadFromPath(Path path) {
        if (path == null) {
            INSTANCE = new LuminescenceConfig();
            return INSTANCE;
        }

        try {
            if (Files.isRegularFile(path)) {
                try (Reader reader = Files.newBufferedReader(path)) {
                    LuminescenceConfig parsed = GSON.fromJson(reader, LuminescenceConfig.class);
                    if (parsed != null) {
                        parsed.maxRadius = Math.max(4, Math.min(14, parsed.maxRadius));
                        INSTANCE = parsed;
                        return parsed;
                    }
                }
            }
        } catch (Throwable ignored) {
            // Corrupted or unreadable JSON: fallback safely to default config
        }

        LuminescenceConfig defaults = new LuminescenceConfig();
        defaults.maxRadius = Math.max(4, Math.min(14, defaults.maxRadius));
        INSTANCE = defaults;
        saveToPath(path, defaults);
        return defaults;
    }

    public static void saveToPath(Path path, LuminescenceConfig cfg) {
        if (path == null || cfg == null) return;
        try {
            Path parent = path.getParent();
            if (parent != null && !Files.exists(parent)) {
                Files.createDirectories(parent);
            }
            try (Writer writer = Files.newBufferedWriter(path)) {
                GSON.toJson(cfg, writer);
            }
        } catch (Throwable ignored) {}
    }

    public static void initAsync(Path configDir) {
        if (configDir == null) return;
        if (INITIALIZED.compareAndSet(false, true)) {
            Util.ioPool().execute(() -> {
                loadFromPath(configDir.resolve("ambient_luminescence.json"));
            });
        }
    }
}
