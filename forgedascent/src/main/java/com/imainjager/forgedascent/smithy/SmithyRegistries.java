package com.imainjager.forgedascent.smithy;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.ModRegistries;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.util.Unit;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

import java.util.ArrayList;
import java.util.List;

/** Smithy anvils, their recipes and menu, reinforced plates, boss Sigils and Treasure Bags (PLAN.md "Update 4 design"). */
public final class SmithyRegistries {
    public static final DeferredRegister<RecipeType<?>> RECIPE_TYPES =
            DeferredRegister.create(Registries.RECIPE_TYPE, ForgedAscent.MOD_ID);
    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS =
            DeferredRegister.create(Registries.RECIPE_SERIALIZER, ForgedAscent.MOD_ID);
    public static final DeferredRegister<MenuType<?>> MENUS = DeferredRegister.create(Registries.MENU, ForgedAscent.MOD_ID);
    public static final DeferredRegister.DataComponents COMPONENTS =
            DeferredRegister.createDataComponents(Registries.DATA_COMPONENT_TYPE, ForgedAscent.MOD_ID);

    public static final DeferredHolder<RecipeType<?>, RecipeType<AnvilRecipe>> ANVIL_TYPE =
            RECIPE_TYPES.register("anvil", () -> RecipeType.simple(ForgedAscent.id("anvil")));
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<AnvilShapedRecipe>> ANVIL_SHAPED =
            RECIPE_SERIALIZERS.register("anvil_shaped", () -> new RecipeSerializer<>() {
                public com.mojang.serialization.MapCodec<AnvilShapedRecipe> codec() { return AnvilShapedRecipe.CODEC; }
                public StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, AnvilShapedRecipe> streamCodec() { return AnvilShapedRecipe.STREAM_CODEC; }
            });
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<AnvilShapelessRecipe>> ANVIL_SHAPELESS =
            RECIPE_SERIALIZERS.register("anvil_shapeless", () -> new RecipeSerializer<>() {
                public com.mojang.serialization.MapCodec<AnvilShapelessRecipe> codec() { return AnvilShapelessRecipe.CODEC; }
                public StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, AnvilShapelessRecipe> streamCodec() { return AnvilShapelessRecipe.STREAM_CODEC; }
            });
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<AnvilDelegateRecipe>> ANVIL_DELEGATE =
            RECIPE_SERIALIZERS.register("anvil_delegate", () -> new RecipeSerializer<>() {
                public com.mojang.serialization.MapCodec<AnvilDelegateRecipe> codec() { return AnvilDelegateRecipe.CODEC; }
                public StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, AnvilDelegateRecipe> streamCodec() { return AnvilDelegateRecipe.STREAM_CODEC; }
            });
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<RepairRecipe>> ANVIL_REPAIR =
            RECIPE_SERIALIZERS.register("anvil_repair", () -> new RecipeSerializer<>() {
                public com.mojang.serialization.MapCodec<RepairRecipe> codec() { return RepairRecipe.CODEC; }
                public StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, RepairRecipe> streamCodec() { return RepairRecipe.STREAM_CODEC; }
            });
    public static final DeferredHolder<RecipeSerializer<?>, RecipeSerializer<ReinforceRecipe>> ANVIL_REINFORCE =
            RECIPE_SERIALIZERS.register("anvil_reinforce", () -> new RecipeSerializer<>() {
                public com.mojang.serialization.MapCodec<ReinforceRecipe> codec() { return ReinforceRecipe.CODEC; }
                public StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, ReinforceRecipe> streamCodec() { return ReinforceRecipe.STREAM_CODEC; }
            });

    public static final DeferredHolder<MenuType<?>, MenuType<SmithyMenu>> SMITHY_MENU = MENUS.register("smithy_anvil",
            () -> IMenuTypeExtension.create((id, inventory, buf) -> new SmithyMenu(id, inventory, buf.readVarInt())));

    /** Reinforcement from 0.5.x: counts as level I. */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Unit>> REINFORCED =
            COMPONENTS.registerComponentType("reinforced", b -> b.persistent(Unit.CODEC)
                    .networkSynchronized(StreamCodec.unit(Unit.INSTANCE)));
    /** Reinforcement level I-III. */
    public static final DeferredHolder<DataComponentType<?>, DataComponentType<Integer>> REINFORCEMENT =
            COMPONENTS.registerComponentType("reinforcement", b -> b.persistent(com.mojang.serialization.Codec.intRange(1, 3))
                    .networkSynchronized(net.minecraft.network.codec.ByteBufCodecs.VAR_INT));

    public static int reinforcement(net.minecraft.world.item.ItemStack stack) {
        Integer level = stack.get(REINFORCEMENT.get());
        if (level != null) return level;
        return stack.has(REINFORCED.get()) ? 1 : 0;
    }

    /** Anvil names by tier; anvil N crafts anvil recipes of tier ≤ N. */
    public static final String[] ANVIL_NAMES = {"stone", "bronze", "steel", "gemstone", "titanium", "tungsten", "netherite"};
    public static final int FIRST_ANVIL_TIER = 3;
    public static final List<DeferredBlock<SmithyAnvilBlock>> ANVILS = new ArrayList<>();
    public static final List<DeferredItem<ReinforcedPlateItem>> REINFORCED_PLATES = new ArrayList<>();
    public static final int GATES = 6;

    private SmithyRegistries() {}

    public static void register(IEventBus modBus) {
        for (int i = 0; i < ANVIL_NAMES.length; i++) {
            int tier = FIRST_ANVIL_TIER + i;
            DeferredBlock<SmithyAnvilBlock> anvil = ModRegistries.BLOCKS.register(ANVIL_NAMES[i] + "_anvil",
                    () -> new SmithyAnvilBlock(tier, BlockBehaviour.Properties.ofFullCopy(Blocks.ANVIL)));
            ANVILS.add(anvil);
            ModRegistries.addToTab(ModRegistries.ITEMS.registerSimpleBlockItem(anvil));
        }
        for (int tier = 2; tier <= 9; tier++) {
            int t = tier;
            var plate = ModRegistries.ITEMS.register("reinforced_plate_" + tier,
                    () -> new ReinforcedPlateItem(t, new Item.Properties()));
            REINFORCED_PLATES.add(plate);
            ModRegistries.addToTab(plate);
        }
        for (var gem : com.imainjager.forgedascent.Materials.GEMS) {
            ModRegistries.addToTab(ModRegistries.ITEMS.registerSimpleItem("flawless_" + gem.id(),
                    new Item.Properties().rarity(Rarity.RARE)));
        }
        for (int gate = 1; gate <= GATES; gate++) {
            ModRegistries.addToTab(ModRegistries.ITEMS.registerSimpleItem("sigil_" + gate,
                    new Item.Properties().stacksTo(16).rarity(Rarity.EPIC).fireResistant()));
        }
        for (int gate = 1; gate <= GATES + 1; gate++) {
            int g = gate;
            ModRegistries.addToTab(ModRegistries.ITEMS.register("treasure_bag_" + gate,
                    () -> new TreasureBagItem(g, new Item.Properties().rarity(Rarity.EPIC).fireResistant())));
        }
        RECIPE_TYPES.register(modBus);
        RECIPE_SERIALIZERS.register(modBus);
        MENUS.register(modBus);
        COMPONENTS.register(modBus);
    }
}
