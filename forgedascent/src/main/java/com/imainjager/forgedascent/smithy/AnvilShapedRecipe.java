package com.imainjager.forgedascent.smithy;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.ShapedRecipePattern;
import net.minecraft.world.level.Level;

/** Shaped recipe that only works in a Smithy Anvil of at least {@code tier}. */
public record AnvilShapedRecipe(int tier, ShapedRecipePattern pattern, ItemStack result) implements AnvilRecipe {
    public static final MapCodec<AnvilShapedRecipe> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Codec.INT.fieldOf("tier").forGetter(AnvilShapedRecipe::tier),
            ShapedRecipePattern.MAP_CODEC.forGetter(AnvilShapedRecipe::pattern),
            ItemStack.STRICT_CODEC.fieldOf("result").forGetter(AnvilShapedRecipe::result)
    ).apply(i, AnvilShapedRecipe::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, AnvilShapedRecipe> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, AnvilShapedRecipe::tier,
            ShapedRecipePattern.STREAM_CODEC, AnvilShapedRecipe::pattern,
            ItemStack.STREAM_CODEC, AnvilShapedRecipe::result,
            AnvilShapedRecipe::new);

    @Override
    public boolean matches(CraftingInput input, Level level) {
        return pattern.matches(input);
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return result.copy();
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width >= pattern.width() && height >= pattern.height();
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return result;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return pattern.ingredients();
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return SmithyRegistries.ANVIL_SHAPED.get();
    }

    @Override
    public RecipeType<?> getType() {
        return SmithyRegistries.ANVIL_TYPE.get();
    }
}
