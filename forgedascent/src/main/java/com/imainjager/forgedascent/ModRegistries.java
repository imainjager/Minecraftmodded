package com.imainjager.forgedascent;

import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.DiggerItem;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.SimpleTier;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;

public final class ModRegistries {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(ForgedAscent.MOD_ID);
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(ForgedAscent.MOD_ID);
    public static final DeferredRegister<ArmorMaterial> ARMOR_MATERIALS =
            DeferredRegister.create(Registries.ARMOR_MATERIAL, ForgedAscent.MOD_ID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, ForgedAscent.MOD_ID);

    /** Everything shown in the creative tab, in registration order. */
    private static final List<DeferredItem<? extends Item>> TAB_ITEMS = new ArrayList<>();

    private ModRegistries() {}

    public static void register(IEventBus modBus) {
        for (Materials.Ingot ingot : Materials.INGOTS) {
            TAB_ITEMS.add(ITEMS.registerSimpleItem(ingot.id() + "_ingot"));
            DeferredBlock<Block> block = BLOCKS.registerSimpleBlock(ingot.id() + "_block",
                    BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_BLOCK));
            TAB_ITEMS.add(ITEMS.registerSimpleBlockItem(block));
        }
        for (Materials.Gear gear : Materials.GEAR) {
            registerGear(gear);
        }

        TABS.register("main", () -> CreativeModeTab.builder()
                .title(Component.translatable("itemGroup.forgedascent"))
                .icon(() -> new ItemStack(TAB_ITEMS.get(0).get()))
                .displayItems((params, output) -> TAB_ITEMS.forEach(item -> output.accept(item.get())))
                .build());

        ITEMS.register(modBus);
        BLOCKS.register(modBus);
        ARMOR_MATERIALS.register(modBus);
        TABS.register(modBus);
    }

    private static void registerGear(Materials.Gear gear) {
        String name = gear.id();
        TagKey<Item> repairTag = TagKey.create(Registries.ITEM, ResourceLocation.parse(gear.repair()));

        Materials.ToolStats t = gear.tool();
        TagKey<Block> incorrect = TagKey.create(Registries.BLOCK, ForgedAscent.id("incorrect_for_tier_" + gear.tier()));
        Tier tier = new SimpleTier(incorrect, t.uses(), t.speed(), t.attack(), t.enchant(), () -> Ingredient.of(repairTag));

        TAB_ITEMS.add(ITEMS.register(name + "_sword", () -> new SwordItem(tier,
                new Item.Properties().attributes(SwordItem.createAttributes(tier, 3, -2.4F)))));
        TAB_ITEMS.add(ITEMS.register(name + "_pickaxe", () -> new PickaxeItem(tier,
                new Item.Properties().attributes(DiggerItem.createAttributes(tier, 1.0F, -2.8F)))));
        TAB_ITEMS.add(ITEMS.register(name + "_axe", () -> new AxeItem(tier,
                new Item.Properties().attributes(DiggerItem.createAttributes(tier, 6.0F, -3.1F)))));
        TAB_ITEMS.add(ITEMS.register(name + "_shovel", () -> new ShovelItem(tier,
                new Item.Properties().attributes(DiggerItem.createAttributes(tier, 1.5F, -3.0F)))));
        TAB_ITEMS.add(ITEMS.register(name + "_hoe", () -> new HoeItem(tier,
                new Item.Properties().attributes(DiggerItem.createAttributes(tier, -Math.round(t.attack()), -1.0F)))));

        Materials.ArmorStats a = gear.armor();
        EnumMap<ArmorItem.Type, Integer> defense = new EnumMap<>(ArmorItem.Type.class);
        defense.put(ArmorItem.Type.HELMET, a.helmet());
        defense.put(ArmorItem.Type.CHESTPLATE, a.chestplate());
        defense.put(ArmorItem.Type.LEGGINGS, a.leggings());
        defense.put(ArmorItem.Type.BOOTS, a.boots());
        defense.put(ArmorItem.Type.BODY, a.chestplate());
        DeferredHolder<ArmorMaterial, ArmorMaterial> material = ARMOR_MATERIALS.register(name, () -> new ArmorMaterial(
                defense, a.enchant(), SoundEvents.ARMOR_EQUIP_IRON, () -> Ingredient.of(repairTag),
                List.of(new ArmorMaterial.Layer(ForgedAscent.id(name))), a.toughness(), a.knockback()));

        for (ArmorItem.Type type : List.of(ArmorItem.Type.HELMET, ArmorItem.Type.CHESTPLATE,
                ArmorItem.Type.LEGGINGS, ArmorItem.Type.BOOTS)) {
            Holder<ArmorMaterial> holder = material;
            TAB_ITEMS.add(ITEMS.register(name + "_" + type.getName(), () -> new TraitArmorItem(holder, type,
                    new Item.Properties().durability(type.getDurability(a.durability())), a)));
        }
    }
}
