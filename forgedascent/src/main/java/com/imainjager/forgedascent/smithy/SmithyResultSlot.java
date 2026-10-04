package com.imainjager.forgedascent.smithy;

import net.minecraft.core.NonNullList;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.inventory.ResultContainer;
import net.minecraft.world.inventory.ResultSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeType;
import net.neoforged.neoforge.common.CommonHooks;

/**
 * Output slot of a Smithy Anvil. Same as the crafting table's, except leftovers come from the anvil recipe that was
 * used, so Silent Gear part recipes keep their blueprint (vanilla only asks crafting-table recipes).
 */
public class SmithyResultSlot extends ResultSlot {
    private final CraftingContainer craftSlots;
    private final ResultContainer resultSlots;
    private final Player player;

    public SmithyResultSlot(Player player, CraftingContainer craftSlots, ResultContainer resultSlots, int x, int y) {
        super(player, craftSlots, resultSlots, 0, x, y);
        this.craftSlots = craftSlots;
        this.resultSlots = resultSlots;
        this.player = player;
    }

    @Override
    @SuppressWarnings("unchecked")
    public void onTake(Player taker, ItemStack stack) {
        checkTakeAchievements(stack);
        CraftingInput.Positioned positioned = craftSlots.asPositionedCraftInput();
        CraftingInput input = positioned.input();
        CommonHooks.setCraftingPlayer(taker);
        NonNullList<ItemStack> remaining;
        var used = resultSlots.getRecipeUsed();
        if (used != null && used.value().getType() == SmithyRegistries.ANVIL_TYPE.get()) {
            remaining = ((Recipe<CraftingInput>) used.value()).getRemainingItems(input);
        } else {
            remaining = taker.level().getRecipeManager().getRemainingItemsFor(RecipeType.CRAFTING, input, taker.level());
        }
        CommonHooks.setCraftingPlayer(null);

        for (int row = 0; row < input.height(); row++) {
            for (int col = 0; col < input.width(); col++) {
                int slot = col + positioned.left() + (row + positioned.top()) * craftSlots.getWidth();
                ItemStack current = craftSlots.getItem(slot);
                ItemStack leftover = remaining.get(col + row * input.width());
                if (!current.isEmpty()) {
                    craftSlots.removeItem(slot, 1);
                    current = craftSlots.getItem(slot);
                }
                if (!leftover.isEmpty()) {
                    if (current.isEmpty()) {
                        craftSlots.setItem(slot, leftover);
                    } else if (ItemStack.isSameItemSameComponents(current, leftover)) {
                        leftover.grow(current.getCount());
                        craftSlots.setItem(slot, leftover);
                    } else if (!player.getInventory().add(leftover)) {
                        player.drop(leftover, false);
                    }
                }
            }
        }
    }
}
