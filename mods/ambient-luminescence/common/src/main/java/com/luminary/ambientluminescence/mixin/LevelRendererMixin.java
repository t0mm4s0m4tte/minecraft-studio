package com.luminary.ambientluminescence.mixin;

import com.luminary.ambientluminescence.DynamicLightTracker;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockAndTintGetter;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(LevelRenderer.class)
public class LevelRendererMixin {
    @Inject(method = "getLightColor(Lnet/minecraft/world/level/BlockAndTintGetter;Lnet/minecraft/core/BlockPos;)I", at = @At("RETURN"), cancellable = true)
    private static void ambientLuminescence$injectDynamicLight(BlockAndTintGetter level, BlockPos pos, CallbackInfoReturnable<Integer> cir) {
        int dynamicLight = DynamicLightTracker.getLuminanceAt(pos.getX(), pos.getY(), pos.getZ());
        if (dynamicLight > 0) {
            int original = cir.getReturnValue();
            int blockLight = original & 0xFFFF;
            int skyLight = (original >> 16) & 0xFFFF;
            int dynamicBlockLight = Math.max(blockLight, dynamicLight << 4);
            cir.setReturnValue(dynamicBlockLight | (skyLight << 16));
        }
    }
}
