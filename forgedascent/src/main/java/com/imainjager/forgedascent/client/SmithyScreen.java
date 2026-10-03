package com.imainjager.forgedascent.client;

import com.imainjager.forgedascent.smithy.SmithyMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;

/** Smithy Anvil screen: the vanilla crafting table layout plus the anvil's tier. */
public class SmithyScreen extends AbstractContainerScreen<SmithyMenu> {
    private static final ResourceLocation BACKGROUND =
            ResourceLocation.withDefaultNamespace("textures/gui/container/crafting_table.png");

    public SmithyScreen(SmithyMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        titleLabelX = 29;
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        renderTooltip(graphics, mouseX, mouseY);
    }

    @Override
    protected void renderBg(GuiGraphics graphics, float partialTick, int mouseX, int mouseY) {
        graphics.blit(BACKGROUND, leftPos, topPos, 0, 0, imageWidth, imageHeight);
    }

    @Override
    protected void renderLabels(GuiGraphics graphics, int mouseX, int mouseY) {
        super.renderLabels(graphics, mouseX, mouseY);
        graphics.drawString(font, Component.translatable("gui.forgedascent.anvil_tier", menu.tier()),
                imageWidth - 8 - font.width(Component.translatable("gui.forgedascent.anvil_tier", menu.tier())),
                inventoryLabelY, 0x404040, false);
    }
}
