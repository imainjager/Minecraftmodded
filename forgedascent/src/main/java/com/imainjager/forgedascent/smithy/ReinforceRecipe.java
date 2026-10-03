package com.imainjager.forgedascent.smithy;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.util.Unit;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;

/**
 * Smithy Anvil: any damageable gear + a reinforced plate of at least the gear's tier → the same gear, marked
 * Reinforced (+1 armor or +1 attack damage, +25% durability). PLAN.md section 6.
 */
public final class ReinforceRecipe implements AnvilRecipe {
    public static final ReinforceRecipe INSTANCE = new ReinforceRecipe();
    public static final MapCodec<ReinforceRecipe> CODEC = MapCodec.unit(INSTANCE);
    public static final StreamCodec<RegistryFriendlyByteBuf, ReinforceRecipe> STREAM_CODEC = StreamCodec.unit(INSTANCE);

    private ReinforceRecipe() {}

    @Override
    public int tier() {
        return 0;
    }

    private record Parts(ItemStack gear, ItemStack plate) {}

    private static Parts find(CraftingInput input) {
        ItemStack gear = ItemStack.EMPTY;
        ItemStack plate = ItemStack.EMPTY;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty()) continue;
            if (stack.getItem() instanceof ReinforcedPlateItem) {
                if (!plate.isEmpty()) return null;
                plate = stack;
            } else {
                if (!gear.isEmpty()) return null;
                gear = stack;
            }
        }
        if (gear.isEmpty() || plate.isEmpty() || !gear.isDamageableItem() || gear.has(SmithyRegistries.REINFORCED.get())) {
            return null;
        }
        if (((ReinforcedPlateItem) plate.getItem()).tier() < GearTiers.of(gear)) return null;
        return new Parts(gear, plate);
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        return find(input) != null;
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        Parts parts = find(input);
        if (parts == null) return ItemStack.EMPTY;
        ItemStack result = parts.gear().copyWithCount(1);
        result.set(SmithyRegistries.REINFORCED.get(), Unit.INSTANCE);
        result.set(DataComponents.MAX_DAMAGE, Math.round(result.getMaxDamage() * 1.25F));
        return result;
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= 2;
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return ItemStack.EMPTY;
    }

    @Override
    public boolean isSpecial() {
        return true;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return SmithyRegistries.ANVIL_REINFORCE.get();
    }

    @Override
    public RecipeType<?> getType() {
        return SmithyRegistries.ANVIL_TYPE.get();
    }
}
