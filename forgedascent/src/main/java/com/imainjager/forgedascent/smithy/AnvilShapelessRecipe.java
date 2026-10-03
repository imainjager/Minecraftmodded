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
import net.minecraft.world.level.Level;

/**
 * Shapeless Smithy Anvil recipe. With {@code copy_components} the result keeps the enchantments, damage and
 * name of the item matching the first ingredient (used for netherite upgrades).
 */
public record AnvilShapelessRecipe(int tier, NonNullList<Ingredient> ingredients, ItemStack result, boolean copyComponents)
        implements AnvilRecipe {
    public static final MapCodec<AnvilShapelessRecipe> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Codec.INT.fieldOf("tier").forGetter(AnvilShapelessRecipe::tier),
            Ingredient.CODEC_NONEMPTY.listOf().fieldOf("ingredients")
                    .xmap(list -> NonNullList.of(Ingredient.EMPTY, list.toArray(Ingredient[]::new)), l -> l)
                    .forGetter(AnvilShapelessRecipe::ingredients),
            ItemStack.STRICT_CODEC.fieldOf("result").forGetter(AnvilShapelessRecipe::result),
            Codec.BOOL.optionalFieldOf("copy_components", false).forGetter(AnvilShapelessRecipe::copyComponents)
    ).apply(i, AnvilShapelessRecipe::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, AnvilShapelessRecipe> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, AnvilShapelessRecipe::tier,
            Ingredient.CONTENTS_STREAM_CODEC.apply(ByteBufCodecs.list())
                    .map(list -> NonNullList.of(Ingredient.EMPTY, list.toArray(Ingredient[]::new)), l -> l),
            AnvilShapelessRecipe::ingredients,
            ItemStack.STREAM_CODEC, AnvilShapelessRecipe::result,
            ByteBufCodecs.BOOL, AnvilShapelessRecipe::copyComponents,
            AnvilShapelessRecipe::new);

    @Override
    public boolean matches(CraftingInput input, Level level) {
        if (input.ingredientCount() != ingredients.size()) return false;
        return input.stackedContents().canCraft(this, null);
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        if (copyComponents) {
            for (int i = 0; i < input.size(); i++) {
                ItemStack stack = input.getItem(i);
                if (!stack.isEmpty() && ingredients.get(0).test(stack)) {
                    return stack.transmuteCopy(result.getItem(), result.getCount());
                }
            }
        }
        return result.copy();
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return width * height >= ingredients.size();
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return result;
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return ingredients;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return SmithyRegistries.ANVIL_SHAPELESS.get();
    }

    @Override
    public RecipeType<?> getType() {
        return SmithyRegistries.ANVIL_TYPE.get();
    }
}
