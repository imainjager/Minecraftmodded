package com.imainjager.forgedascent.smithy;

import com.imainjager.forgedascent.ForgedAscent;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;

import java.util.List;

/** Boss Treasure Bag: right-click to open; contents come from loot table forgedascent:bags/gate_N. */
public class TreasureBagItem extends Item {
    private final int gate;

    public TreasureBagItem(int gate, Properties properties) {
        super(properties);
        this.gate = gate;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack bag = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            ResourceKey<LootTable> key = ResourceKey.create(Registries.LOOT_TABLE, ForgedAscent.id("bags/gate_" + gate));
            LootTable table = server.getServer().reloadableRegistries().getLootTable(key);
            LootParams params = new LootParams.Builder(server)
                    .withParameter(LootContextParams.ORIGIN, player.position())
                    .withParameter(LootContextParams.THIS_ENTITY, player)
                    .withLuck(player.getLuck())
                    .create(LootContextParamSets.GIFT);
            for (ItemStack loot : table.getRandomItems(params)) {
                if (!player.getInventory().add(loot)) player.drop(loot, false);
            }
            level.playSound(null, player.blockPosition(), SoundEvents.ARMOR_EQUIP_LEATHER.value(), SoundSource.PLAYERS, 1.0F, 0.8F);
            bag.consume(1, player);
        }
        return InteractionResultHolder.sidedSuccess(bag, level.isClientSide());
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("tooltip.forgedascent.treasure_bag").withStyle(ChatFormatting.GRAY));
    }
}
