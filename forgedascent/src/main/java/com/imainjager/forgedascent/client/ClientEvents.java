package com.imainjager.forgedascent.client;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.smithy.SmithyRegistries;
import com.imainjager.forgedascent.world.BloodMoonPayload;
import net.minecraft.client.Minecraft;
import net.minecraft.world.level.Level;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;
import net.neoforged.neoforge.client.event.ViewportEvent;

@EventBusSubscriber(modid = ForgedAscent.MOD_ID, value = Dist.CLIENT)
public final class ClientEvents {
    private ClientEvents() {}

    @SubscribeEvent
    public static void registerScreens(RegisterMenuScreensEvent event) {
        event.register(SmithyRegistries.SMITHY_MENU.get(), SmithyScreen::new);
    }

    /** Blood moon: tint the Overworld's fog (and so the horizon) red at night. */
    @SubscribeEvent
    public static void fogColor(ViewportEvent.ComputeFogColor event) {
        Minecraft mc = Minecraft.getInstance();
        if (!BloodMoonPayload.clientActive || mc.level == null || mc.level.dimension() != Level.OVERWORLD) return;
        float blend = 0.55F;
        event.setRed(event.getRed() + (0.55F - event.getRed()) * blend);
        event.setGreen(event.getGreen() * (1 - blend));
        event.setBlue(event.getBlue() * (1 - blend));
    }
}
