package com.imainjager.forgedascent;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/** Gem cutting wheel: stays in the crafting grid after a cut, losing one durability (PLAN.md section 5). */
public class CuttingWheelItem extends Item {
    public CuttingWheelItem(Properties properties) {
        super(properties);
    }

    @Override
    public boolean hasCraftingRemainingItem(ItemStack stack) {
        return true;
    }

    @Override
    public ItemStack getCraftingRemainingItem(ItemStack stack) {
        ItemStack worn = stack.copyWithCount(1);
        worn.setDamageValue(worn.getDamageValue() + 1);
        return worn.getDamageValue() >= worn.getMaxDamage() ? ItemStack.EMPTY : worn;
    }
}
