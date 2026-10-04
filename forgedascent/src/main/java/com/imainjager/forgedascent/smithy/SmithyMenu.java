package com.imainjager.forgedascent.smithy;

import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.inventory.ResultContainer;
import net.minecraft.world.inventory.ResultSlot;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.inventory.TransientCraftingContainer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.Level;

/** 3x3 crafting grid for Smithy Anvil recipes (layout and shift-click rules copied from the vanilla crafting table). */
public class SmithyMenu extends AbstractContainerMenu {
    private final CraftingContainer craftSlots = new TransientCraftingContainer(this, 3, 3);
    private final ResultContainer resultSlots = new ResultContainer();
    private final ContainerLevelAccess access;
    private final Player player;
    private final int tier;

    public SmithyMenu(int id, Inventory inventory, int tier) {
        this(id, inventory, ContainerLevelAccess.NULL, tier);
    }

    public SmithyMenu(int id, Inventory inventory, ContainerLevelAccess access, int tier) {
        super(SmithyRegistries.SMITHY_MENU.get(), id);
        this.access = access;
        this.player = inventory.player;
        this.tier = tier;
        addSlot(new ResultSlot(player, craftSlots, resultSlots, 0, 124, 35));
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 3; col++) {
                addSlot(new Slot(craftSlots, col + row * 3, 30 + col * 18, 17 + row * 18));
            }
        }
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                addSlot(new Slot(inventory, col + row * 9 + 9, 8 + col * 18, 84 + row * 18));
            }
        }
        for (int col = 0; col < 9; col++) {
            addSlot(new Slot(inventory, col, 8 + col * 18, 142));
        }
    }

    public int tier() {
        return tier;
    }

    @Override
    public void slotsChanged(Container container) {
        access.execute((level, pos) -> updateResult(level));
    }

    private void updateResult(Level level) {
        if (level.isClientSide() || !(player instanceof ServerPlayer serverPlayer)) return;
        CraftingInput input = craftSlots.asCraftInput();
        ItemStack result = ItemStack.EMPTY;
        for (RecipeHolder<AnvilRecipe> holder : level.getRecipeManager().getRecipesFor(SmithyRegistries.ANVIL_TYPE.get(), input, level)) {
            if (holder.value().tier() > tier) continue;
            if (resultSlots.setRecipeUsed(level, serverPlayer, holder)) {
                ItemStack crafted = holder.value().assemble(input, level.registryAccess());
                if (holder.value() instanceof AnvilDelegateRecipe
                        && AnvilDelegateRecipe.craftedTier(crafted, level.registryAccess()) > tier) {
                    continue;
                }
                if (!crafted.isEmpty()) {
                    result = crafted;
                    break;
                }
            }
        }
        resultSlots.setItem(0, result);
        setRemoteSlot(0, result);
        serverPlayer.connection.send(new ClientboundContainerSetSlotPacket(containerId, incrementStateId(), 0, result));
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        access.execute((level, pos) -> clearContainer(player, craftSlots));
    }

    @Override
    public boolean stillValid(Player player) {
        return access.evaluate((level, pos) -> level.getBlockState(pos).getBlock() instanceof SmithyAnvilBlock
                && player.distanceToSqr(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5) <= 64.0, true);
    }

    @Override
    public boolean canTakeItemForPickAll(ItemStack stack, Slot slot) {
        return slot.container != resultSlots && super.canTakeItemForPickAll(stack, slot);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        ItemStack copy = ItemStack.EMPTY;
        Slot slot = slots.get(index);
        if (slot.hasItem()) {
            ItemStack stack = slot.getItem();
            copy = stack.copy();
            if (index == 0) {
                access.execute((level, pos) -> stack.getItem().onCraftedBy(stack, level, player));
                if (!moveItemStackTo(stack, 10, 46, true)) return ItemStack.EMPTY;
                slot.onQuickCraft(stack, copy);
            } else if (index >= 10 && index < 46) {
                if (!moveItemStackTo(stack, 1, 10, false)) {
                    if (index < 37) {
                        if (!moveItemStackTo(stack, 37, 46, false)) return ItemStack.EMPTY;
                    } else if (!moveItemStackTo(stack, 10, 37, false)) {
                        return ItemStack.EMPTY;
                    }
                }
            } else if (!moveItemStackTo(stack, 10, 46, false)) {
                return ItemStack.EMPTY;
            }
            if (stack.isEmpty()) {
                slot.setByPlayer(ItemStack.EMPTY);
            } else {
                slot.setChanged();
            }
            if (stack.getCount() == copy.getCount()) return ItemStack.EMPTY;
            slot.onTake(player, stack);
            if (index == 0) player.drop(stack, false);
        }
        return copy;
    }
}
