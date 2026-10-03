package com.imainjager.forgedascent.smithy;

import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Recipe;

/** A recipe crafted in a Smithy Anvil. Anvils accept recipes whose tier is at most their own. */
public interface AnvilRecipe extends Recipe<CraftingInput> {
    int tier();
}
