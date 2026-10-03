package com.imainjager.forgedascent.client.jei;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.smithy.AnvilRecipe;
import com.imainjager.forgedascent.smithy.AnvilShapedRecipe;
import com.imainjager.forgedascent.smithy.ReinforceRecipe;
import com.imainjager.forgedascent.smithy.SmithyRegistries;
import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.gui.builder.IRecipeLayoutBuilder;
import mezz.jei.api.gui.drawable.IDrawable;
import mezz.jei.api.gui.drawable.IDrawableStatic;
import mezz.jei.api.gui.ingredient.IRecipeSlotsView;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.IFocusGroup;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.recipe.RecipeType;
import mezz.jei.api.recipe.category.IRecipeCategory;
import mezz.jei.api.registration.IRecipeCatalystRegistration;
import mezz.jei.api.registration.IRecipeCategoryRegistration;
import mezz.jei.api.registration.IRecipeRegistration;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.NonNullList;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;

import java.util.List;

/** JEI tab "Smithy Anvil" showing anvil recipes and which anvils craft them. */
@JeiPlugin
public class ForgedAscentJei implements IModPlugin {
    private static final RecipeType<RecipeHolder<AnvilRecipe>> ANVIL =
            RecipeType.createRecipeHolderType(ForgedAscent.id("anvil"));

    @Override
    public ResourceLocation getPluginUid() {
        return ForgedAscent.id("jei");
    }

    @Override
    public void registerCategories(IRecipeCategoryRegistration registration) {
        registration.addRecipeCategories(new AnvilCategory(registration.getJeiHelpers().getGuiHelper()));
    }

    @Override
    public void registerRecipes(IRecipeRegistration registration) {
        var level = Minecraft.getInstance().level;
        if (level == null) return;
        List<RecipeHolder<AnvilRecipe>> recipes = level.getRecipeManager()
                .getAllRecipesFor(SmithyRegistries.ANVIL_TYPE.get()).stream()
                .filter(h -> !(h.value() instanceof ReinforceRecipe)).toList();
        registration.addRecipes(ANVIL, recipes);
        for (var plate : SmithyRegistries.REINFORCED_PLATES) {
            registration.addIngredientInfo(new ItemStack(plate.get()), VanillaTypes.ITEM_STACK,
                    Component.translatable("jei.forgedascent.reinforce"));
        }
    }

    @Override
    public void registerRecipeCatalysts(IRecipeCatalystRegistration registration) {
        for (var anvil : SmithyRegistries.ANVILS) {
            registration.addRecipeCatalyst(new ItemStack(anvil.get()), ANVIL);
        }
    }

    private static final class AnvilCategory implements IRecipeCategory<RecipeHolder<AnvilRecipe>> {
        private final IDrawableStatic background;
        private final IDrawable icon;

        AnvilCategory(IGuiHelper gui) {
            background = gui.createDrawable(
                    ResourceLocation.withDefaultNamespace("textures/gui/container/crafting_table.png"), 29, 16, 116, 54);
            icon = gui.createDrawableItemStack(new ItemStack(SmithyRegistries.ANVILS.get(0).get()));
        }

        @Override
        public RecipeType<RecipeHolder<AnvilRecipe>> getRecipeType() {
            return ANVIL;
        }

        @Override
        public Component getTitle() {
            return Component.translatable("jei.forgedascent.anvil");
        }

        @Override
        public int getWidth() {
            return 116;
        }

        @Override
        public int getHeight() {
            return 64;
        }

        @Override
        public IDrawable getIcon() {
            return icon;
        }

        @Override
        public void setRecipe(IRecipeLayoutBuilder builder, RecipeHolder<AnvilRecipe> holder, IFocusGroup focuses) {
            AnvilRecipe recipe = holder.value();
            NonNullList<Ingredient> ingredients = recipe.getIngredients();
            int width = recipe instanceof AnvilShapedRecipe shaped ? shaped.pattern().width() : 3;
            if (!(recipe instanceof AnvilShapedRecipe)) builder.setShapeless();
            for (int i = 0; i < ingredients.size(); i++) {
                builder.addSlot(RecipeIngredientRole.INPUT, 1 + (i % width) * 18, 1 + (i / width) * 18)
                        .addIngredients(ingredients.get(i));
            }
            var registries = Minecraft.getInstance().level.registryAccess();
            builder.addSlot(RecipeIngredientRole.OUTPUT, 95, 19).addItemStack(recipe.getResultItem(registries));
        }

        @Override
        public void draw(RecipeHolder<AnvilRecipe> holder, IRecipeSlotsView slots, GuiGraphics graphics, double mouseX, double mouseY) {
            background.draw(graphics);
            int tier = holder.value().tier();
            String anvil = SmithyRegistries.ANVIL_NAMES[Math.max(0, tier - SmithyRegistries.FIRST_ANVIL_TIER)];
            graphics.drawString(Minecraft.getInstance().font,
                    Component.translatable("jei.forgedascent.needs_anvil",
                            Component.translatable("block.forgedascent." + anvil + "_anvil")), 0, 56, 0x404040, false);
        }
    }
}
