package com.imainjager.forgedascent.cthulhu;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Suspicious Looking Eye: use it at night to call the Eye of Cthulhu. */
public class SuspiciousEyeItem extends Item {
    public SuspiciousEyeItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel server)) {
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide());
        }
        if (level.dimension() != Level.OVERWORLD || !EyeSpawner.isNight(server)) {
            player.displayClientMessage(Component.translatable("message.forgedascent.eye_night_only"), true);
            return InteractionResultHolder.fail(stack);
        }
        if (EyeSpawner.alive(server)) {
            player.displayClientMessage(Component.translatable("message.forgedascent.eye_already_awake"), true);
            return InteractionResultHolder.fail(stack);
        }
        EyeSpawner.spawnNear(server, player, true);
        if (!player.getAbilities().instabuild) stack.shrink(1);
        player.getCooldowns().addCooldown(this, 40);
        return InteractionResultHolder.sidedSuccess(stack, false);
    }
}
