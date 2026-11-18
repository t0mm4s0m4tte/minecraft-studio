package com.luminary.ambientluminescence.neoforge;

import com.luminary.ambientluminescence.AmbientLuminescenceClient;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.ClientTickEvent;

@Mod(value = AmbientLuminescenceClient.MOD_ID, dist = Dist.CLIENT)
public final class AmbientLuminescenceNeoForgeClient {
    public AmbientLuminescenceNeoForgeClient() {
        AmbientLuminescenceClient.init();
    }

    @EventBusSubscriber(modid = AmbientLuminescenceClient.MOD_ID, value = Dist.CLIENT)
    public static class ClientEvents {
        @SubscribeEvent
        public static void onClientTick(ClientTickEvent.Post event) {
            AmbientLuminescenceClient.onClientTick(Minecraft.getInstance());
        }
    }
}
