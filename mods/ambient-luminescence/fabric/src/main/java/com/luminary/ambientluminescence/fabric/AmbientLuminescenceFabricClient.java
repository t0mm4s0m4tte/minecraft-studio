package com.luminary.ambientluminescence.fabric;

import com.luminary.ambientluminescence.AmbientLuminescenceClient;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;

public final class AmbientLuminescenceFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        AmbientLuminescenceClient.init();
        ClientTickEvents.END_CLIENT_TICK.register(AmbientLuminescenceClient::onClientTick);
    }
}
