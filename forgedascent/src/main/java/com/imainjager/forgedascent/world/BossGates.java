package com.imainjager.forgedascent.world;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.imainjager.forgedascent.ForgedAscent;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * Terraria-style boss gates (PLAN.md "Update 4 design"): a gate boss killed by a player drops that gate's
 * Treasure Bag (Sigil + loot) and marks the gate cleared for the world. Bosses per gate are in materials.json.
 */
public final class BossGates {
    private static final Map<ResourceLocation, Integer> GATE_OF = new HashMap<>();

    private BossGates() {}

    public static void register() {
        try (var in = BossGates.class.getResourceAsStream("/forgedascent/materials.json")) {
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            for (JsonElement e : root.getAsJsonArray("gates")) {
                JsonObject o = e.getAsJsonObject();
                int gate = o.get("gate").getAsInt();
                o.getAsJsonArray("bosses").forEach(b -> GATE_OF.put(ResourceLocation.parse(b.getAsString()), gate));
            }
        } catch (Exception ex) {
            throw new RuntimeException("Forged Ascent could not read boss gates", ex);
        }
        NeoForge.EVENT_BUS.addListener(BossGates::onDrops);
    }

    private static void onDrops(LivingDropsEvent event) {
        if (!(event.getEntity().level() instanceof ServerLevel level)) return;
        if (!(event.getSource().getEntity() instanceof Player player)) return;
        Integer gate = GATE_OF.get(BuiltInRegistries.ENTITY_TYPE.getKey(event.getEntity().getType()));
        if (gate == null) return;

        ItemStack bag = new ItemStack(BuiltInRegistries.ITEM.get(ForgedAscent.id("treasure_bag_" + gate)));
        var pos = event.getEntity().position();
        event.getDrops().add(new ItemEntity(level, pos.x, pos.y, pos.z, bag));

        ForgedWorldData data = ForgedWorldData.get(level.getServer());
        if (!data.gateCleared(gate)) {
            data.clearGate(gate);
            level.getServer().getPlayerList().broadcastSystemMessage(
                    Component.translatable("message.forgedascent.gate_cleared", player.getDisplayName(),
                            Component.translatable("gate.forgedascent." + gate)).withStyle(ChatFormatting.GOLD), false);
        }
    }
}
