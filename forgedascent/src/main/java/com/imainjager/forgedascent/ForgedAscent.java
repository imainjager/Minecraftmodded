package com.imainjager.forgedascent;

import com.mojang.logging.LogUtils;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import org.slf4j.Logger;

@Mod(ForgedAscent.MOD_ID)
public class ForgedAscent {
    public static final String MOD_ID = "forgedascent";
    public static final Logger LOGGER = LogUtils.getLogger();

    public ForgedAscent(IEventBus modBus) {
        Materials.load();
        ModRegistries.register(modBus);
        modBus.addListener(VanillaNerfs::modifyDefaultComponents);
        NeoForge.EVENT_BUS.addListener(VanillaNerfs::modifyAttributes);
    }

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }
}
