package com.imainjager.forgedascent.smithy;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.core.component.TypedDataComponent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Runs another mod's crafting recipe (Silent Gear part recipes) in a Smithy Anvil. The anvil's tier is checked
 * against the tier of the Silent Gear materials in the crafted part (PLAN.md "Update 5 plan").
 */
@SuppressWarnings("unchecked")
public record AnvilDelegateRecipe(Recipe<?> recipe) implements AnvilRecipe {
    public static final MapCodec<AnvilDelegateRecipe> CODEC =
            Recipe.CODEC.fieldOf("recipe").xmap(AnvilDelegateRecipe::new, AnvilDelegateRecipe::recipe);
    public static final StreamCodec<RegistryFriendlyByteBuf, AnvilDelegateRecipe> STREAM_CODEC =
            Recipe.STREAM_CODEC.map(AnvilDelegateRecipe::new, AnvilDelegateRecipe::recipe);

    private static final Pattern ID = Pattern.compile("[a-z0-9_.-]+:[a-z0-9_./-]+");
    private static Map<String, Integer> materialTiers;

    private Recipe<CraftingInput> inner() {
        return (Recipe<CraftingInput>) recipe;
    }

    @Override
    public int tier() {
        return 0;
    }

    @Override
    public boolean matches(CraftingInput input, Level level) {
        return inner().matches(input, level);
    }

    @Override
    public ItemStack assemble(CraftingInput input, HolderLookup.Provider registries) {
        return inner().assemble(input, registries);
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return inner().canCraftInDimensions(width, height);
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return inner().getResultItem(registries);
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return inner().getIngredients();
    }

    @Override
    public boolean isSpecial() {
        return true;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return SmithyRegistries.ANVIL_DELEGATE.get();
    }

    @Override
    public RecipeType<?> getType() {
        return SmithyRegistries.ANVIL_TYPE.get();
    }

    /** Highest tier of any Silent Gear material stored on the crafted part (0 if none is known). */
    public static int craftedTier(ItemStack stack, HolderLookup.Provider registries) {
        Map<String, Integer> tiers = tiers();
        int best = 0;
        for (TypedDataComponent<?> component : stack.getComponents()) {
            var key = BuiltInRegistries.DATA_COMPONENT_TYPE.getKey(component.type());
            if (key == null || !key.getNamespace().equals("silentgear")) continue;
            var encoded = component.encodeValue(registries.createSerializationContext(JsonOps.INSTANCE));
            if (encoded.result().isEmpty()) continue;
            Matcher m = ID.matcher(encoded.result().get().toString());
            while (m.find()) best = Math.max(best, tiers.getOrDefault(m.group(), 0));
        }
        return best;
    }

    private static Map<String, Integer> tiers() {
        if (materialTiers == null) {
            Map<String, Integer> map = new HashMap<>();
            try (var in = AnvilDelegateRecipe.class.getResourceAsStream("/forgedascent/sg_material_tiers.json")) {
                if (in != null) {
                    JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
                    for (Map.Entry<String, JsonElement> e : root.entrySet()) map.put(e.getKey(), e.getValue().getAsInt());
                }
            } catch (Exception ignored) {
                // No table: every part counts as tier 0.
            }
            materialTiers = map;
        }
        return materialTiers;
    }
}
