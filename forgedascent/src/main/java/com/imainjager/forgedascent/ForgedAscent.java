package com.imainjager.forgedascent;

import com.imainjager.forgedascent.loot.TieredChestLoot;
import com.imainjager.forgedascent.mobs.EliteMobs;
import com.imainjager.forgedascent.mobs.MobConfig;
import com.imainjager.forgedascent.mobs.MobEvents;
import com.imainjager.forgedascent.smithy.GearTiers;
import com.imainjager.forgedascent.smithy.SmithyRegistries;
import com.imainjager.forgedascent.world.BloodMoon;
import com.imainjager.forgedascent.world.BloodMoonPayload;
import com.imainjager.forgedascent.world.BossGates;
import com.mojang.logging.LogUtils;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import com.mojang.serialization.MapCodec;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;
import org.slf4j.Logger;

@Mod(ForgedAscent.MOD_ID)
public class ForgedAscent {
    public static final String MOD_ID = "forgedascent";
    public static final Logger LOGGER = LogUtils.getLogger();

    private static final DeferredRegister<MapCodec<? extends IGlobalLootModifier>> LOOT_MODIFIERS =
            DeferredRegister.create(NeoForgeRegistries.Keys.GLOBAL_LOOT_MODIFIER_SERIALIZERS, MOD_ID);

    public ForgedAscent(IEventBus modBus, ModContainer container) {
        Materials.load();
        ModRegistries.register(modBus);
        SmithyRegistries.register(modBus);
        EliteMobs.register(modBus);
        com.imainjager.forgedascent.cthulhu.CthulhuRegistries.register(modBus);
        GearTiers.register();
        ArmorPerks.register();
        com.imainjager.forgedascent.smithy.GemCutting.register();
        BossGates.register();
        BloodMoon.register();
        modBus.addListener((RegisterPayloadHandlersEvent e) -> e.registrar("1").playToClient(
                BloodMoonPayload.TYPE, BloodMoonPayload.STREAM_CODEC,
                (payload, context) -> BloodMoonPayload.clientActive = payload.active()));
        LOOT_MODIFIERS.register("tiered_chest_loot", () -> TieredChestLoot.CODEC);
        LOOT_MODIFIERS.register(modBus);
        container.registerConfig(ModConfig.Type.COMMON, MobConfig.SPEC);
        modBus.addListener(VanillaNerfs::modifyDefaultComponents);
        NeoForge.EVENT_BUS.addListener(VanillaNerfs::modifyAttributes);
        MobEvents.register();
    }

    public static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }
}
