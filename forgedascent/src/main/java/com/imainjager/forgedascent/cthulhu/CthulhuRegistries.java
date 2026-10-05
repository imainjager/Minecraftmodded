package com.imainjager.forgedascent.cthulhu;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.ModRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.DeferredSpawnEggItem;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Entity types and items for the Eye of Cthulhu fight. */
public final class CthulhuRegistries {
    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(Registries.ENTITY_TYPE, ForgedAscent.MOD_ID);

    public static final DeferredHolder<EntityType<?>, EntityType<EyeOfCthulhu>> EYE = ENTITY_TYPES.register("eye_of_cthulhu",
            () -> EntityType.Builder.of(EyeOfCthulhu::new, MobCategory.MONSTER)
                    .sized(2.6F, 2.6F).eyeHeight(1.3F).fireImmune().clientTrackingRange(10).updateInterval(1)
                    .build(ForgedAscent.id("eye_of_cthulhu").toString()));

    public static final DeferredHolder<EntityType<?>, EntityType<EyeServant>> SERVANT = ENTITY_TYPES.register("servant_of_cthulhu",
            () -> EntityType.Builder.of(EyeServant::new, MobCategory.MONSTER)
                    .sized(0.8F, 0.8F).eyeHeight(0.45F).fireImmune().clientTrackingRange(8).updateInterval(1)
                    .build(ForgedAscent.id("servant_of_cthulhu").toString()));

    public static DeferredItem<Item> SUSPICIOUS_EYE;
    public static DeferredItem<Item> EYE_EGG;
    public static DeferredItem<Item> SERVANT_EGG;

    private CthulhuRegistries() {}

    public static void register(IEventBus modBus) {
        SUSPICIOUS_EYE = ModRegistries.ITEMS.register("suspicious_looking_eye",
                () -> new SuspiciousEyeItem(new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON)));
        EYE_EGG = ModRegistries.ITEMS.register("eye_of_cthulhu_spawn_egg",
                () -> new DeferredSpawnEggItem(EYE, 0xEBDDCB, 0xA8142A, new Item.Properties()));
        SERVANT_EGG = ModRegistries.ITEMS.register("servant_of_cthulhu_spawn_egg",
                () -> new DeferredSpawnEggItem(SERVANT, 0xEBDDCB, 0x3E8A4C, new Item.Properties()));
        ModRegistries.addToTab(SUSPICIOUS_EYE);
        ModRegistries.addToTab(EYE_EGG);
        ModRegistries.addToTab(SERVANT_EGG);
        ENTITY_TYPES.register(modBus);
        modBus.addListener((EntityAttributeCreationEvent e) -> {
            e.put(EYE.get(), EyeOfCthulhu.createAttributes().build());
            e.put(SERVANT.get(), EyeServant.createAttributes().build());
        });
        EyeSpawner.register();
    }
}
