package com.imainjager.forgedascent.smithy;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.Materials;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/** Cutting a rough gem has a small chance to also produce a Flawless gem (PLAN.md "Update 5 plan"). */
public final class GemCutting {
    private static final float FLAWLESS_CHANCE = 0.06F;

    private GemCutting() {}

    public static void register() {
        NeoForge.EVENT_BUS.addListener(GemCutting::onCrafted);
    }

    private static void onCrafted(PlayerEvent.ItemCraftedEvent event) {
        if (event.getEntity().level().isClientSide()) return;
        ResourceLocation crafted = BuiltInRegistries.ITEM.getKey(event.getCrafting().getItem());
        for (Materials.Gem gem : Materials.GEMS) {
            if (!crafted.toString().equals(gem.item())) continue;
            var rough = BuiltInRegistries.ITEM.get(ForgedAscent.id("rough_" + gem.id()));
            boolean cut = false;
            for (int i = 0; i < event.getInventory().getContainerSize(); i++) {
                if (event.getInventory().getItem(i).is(rough)) cut = true;
            }
            if (cut && event.getEntity().getRandom().nextFloat() < FLAWLESS_CHANCE) {
                ItemStack flawless = new ItemStack(BuiltInRegistries.ITEM.get(ForgedAscent.id("flawless_" + gem.id())));
                if (!event.getEntity().getInventory().add(flawless)) event.getEntity().drop(flawless, false);
                event.getEntity().displayClientMessage(Component.translatable("message.forgedascent.flawless",
                        flawless.getHoverName()).withStyle(ChatFormatting.AQUA), true);
            }
            return;
        }
    }
}
