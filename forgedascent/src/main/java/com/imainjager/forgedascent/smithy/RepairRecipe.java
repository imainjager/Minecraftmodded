package com.imainjager.forgedascent.smithy;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.HolderLookup;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;

/** Smithy Anvil: damaged gear + ingots it can be repaired with → repaired by 25% of its durability per ingot. */
public final class RepairRecipe implements AnvilRecipe {
    public static final RepairRecipe INSTANCE = new RepairRecipe();
    public static final MapCodec<RepairRecipe> CODEC = MapCodec.unit(INSTANCE);
    public static final StreamCodec<RegistryFriendlyByteBuf, RepairRecipe> STREAM_CODEC = StreamCodec.unit(INSTANCE);

    private RepairRecipe() {}

    @Override
    public int tier() {
        return 0;
    }

    private record Parts(ItemStack gear, int ingots) {}

    private static Parts find(CraftingInput input) {
        ItemStack gear = ItemStack.EMPTY;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (!stack.isEmpty() && stack.isDamageableItem()) {
                if (!gear.isEmpty()) return null;
                gear = stack;
            }
        }
        if (gear.isEmpty() || !gear.isDamaged()) return null;
        int ingots = 0;
        for (int i = 0; i < input.size(); i++) {
            ItemStack stack = input.getItem(i);
            if (stack.isEmpty() || stack == gear) continue;
            if (!gear.getItem().isValidRepairItem(gear, stack)) return null;
            ingots++;
        }
        return ingots == 0 ? null : new Parts(gear, ingots);
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
        int repair = Math.round(result.getMaxDamage() * 0.25F * parts.ingots());
        result.setDamageValue(Math.max(0, result.getDamageValue() - repair));
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
        return SmithyRegistries.ANVIL_REPAIR.get();
    }

    @Override
    public RecipeType<?> getType() {
        return SmithyRegistries.ANVIL_TYPE.get();
    }
}
