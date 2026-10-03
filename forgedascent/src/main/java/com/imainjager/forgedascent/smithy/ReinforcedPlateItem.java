package com.imainjager.forgedascent.smithy;

import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;

import java.util.List;

/** Reinforces gear of up to its tier at a Smithy Anvil. */
public class ReinforcedPlateItem extends Item {
    private final int tier;

    public ReinforcedPlateItem(int tier, Properties properties) {
        super(properties);
        this.tier = tier;
    }

    public int tier() {
        return tier;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.forgedascent.reinforced_plate", tier).withStyle(net.minecraft.ChatFormatting.GRAY));
    }
}
