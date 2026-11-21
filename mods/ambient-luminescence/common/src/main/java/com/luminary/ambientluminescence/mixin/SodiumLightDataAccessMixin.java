package com.luminary.ambientluminescence.mixin;

import com.luminary.ambientluminescence.DynamicLightTracker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Compatibilità diretta con Sodium 0.6+ / 0.8+:
 * Inietta la luce dinamica di DynamicLightTracker (torce droppate, ItemEntity, entità luminose)
 * direttamente nel metodo LightDataAccess.compute(int x, int y, int z) di Sodium!
 *
 * In LightDataAccess di Sodium:
 * - i bit 0..3 sono BlockLight (BL)
 * - i bit 4..7 sono SkyLight (SL)
 * - i bit 8..11 sono Luminance (LU)
 */
@Pseudo
@Mixin(targets = {"net.caffeinemc.mods.sodium.client.model.light.data.LightDataAccess", "me.jellysquid.mods.sodium.client.model.light.data.LightDataAccess"}, remap = false)
public class SodiumLightDataAccessMixin {
    @Inject(method = "compute(III)I", at = @At("RETURN"), cancellable = true, remap = false, require = 0)
    private void ambientLuminescence$injectSodiumDynamicLight(int x, int y, int z, CallbackInfoReturnable<Integer> cir) {
        int dyn = DynamicLightTracker.getLuminanceAt(x, y, z);
        if (dyn > 0) {
            int word = cir.getReturnValue();
            int currentBL = word & 15;
            if (dyn > currentBL) {
                word = (word & ~15) | (dyn & 15);
                cir.setReturnValue(word);
            }
        }
    }
}
