package com.imainjager.forgedascent;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.EntityTypeTags;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.monster.AbstractSkeleton;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.living.LivingChangeTargetEvent;
import net.neoforged.neoforge.event.entity.living.LivingEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

import java.util.List;

/**
 * Perks of the scavenged armors that aren't plain stats (PLAN.md "Update 5 plan"), plus their full-set bonus:
 * wearing all four pieces of a scavenged set doubles its perk.
 */
public final class ArmorPerks {
    private static final List<EquipmentSlot> SLOTS =
            List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET);

    private ArmorPerks() {}

    public static void register() {
        NeoForge.EVENT_BUS.addListener(ArmorPerks::onVisibility);
        NeoForge.EVENT_BUS.addListener(ArmorPerks::onDamage);
        NeoForge.EVENT_BUS.addListener(ArmorPerks::onEffect);
        NeoForge.EVENT_BUS.addListener(ArmorPerks::onTarget);
        NeoForge.EVENT_BUS.addListener(ArmorPerks::onPlayerTick);
    }

    /** Pieces of a Forged Ascent armor set worn, counted twice for a full set (the full-set bonus). */
    static int strength(LivingEntity entity, String set) {
        int pieces = 0;
        for (EquipmentSlot slot : SLOTS) {
            ResourceLocation id = BuiltInRegistries.ITEM.getKey(entity.getItemBySlot(slot).getItem());
            if (id.getNamespace().equals(ForgedAscent.MOD_ID) && id.getPath().startsWith(set + "_")) pieces++;
        }
        return pieces == 4 ? 8 : pieces;
    }

    private static void onVisibility(LivingEvent.LivingVisibilityEvent event) {
        LivingEntity entity = event.getEntity();
        int leaf = strength(entity, "leaf");
        if (leaf > 0) event.modifyVisibility(Math.max(0.2, 1 - 0.1 * leaf));
        int bone = strength(entity, "bone");
        if (bone > 0 && event.getLookingEntity() instanceof AbstractSkeleton) event.modifyVisibility(Math.max(0.3, 1 - 0.1 * bone));
        int rotten = strength(entity, "rotten");
        if (rotten > 0 && event.getLookingEntity() instanceof Zombie) event.modifyVisibility(Math.max(0.3, 1 - 0.1 * rotten));
    }

    private static void onDamage(LivingIncomingDamageEvent event) {
        LivingEntity victim = event.getEntity();
        if (event.getSource().getEntity() instanceof LivingEntity attacker && event.getSource().getDirectEntity() == attacker) {
            int flint = strength(victim, "flint");
            if (flint > 0 && attacker != victim) {
                attacker.hurt(victim.damageSources().thorns(victim), 0.25F * flint);
            }
        }
        if (event.getSource().getEntity() instanceof Player player && victim.getType().is(EntityTypeTags.UNDEAD)) {
            int bone = strength(player, "bone");
            if (bone > 0) event.setAmount(event.getAmount() * (1 + 0.04F * bone));
        }
    }

    private static void onEffect(MobEffectEvent.Applicable event) {
        if (event.getEffectInstance().getEffect().equals(MobEffects.POISON) && strength(event.getEntity(), "chitin") >= 2) {
            event.setResult(MobEffectEvent.Applicable.Result.DO_NOT_APPLY);
        }
    }

    /** A full Rotten set makes zombies ignore you unless you hit them first. */
    private static void onTarget(LivingChangeTargetEvent event) {
        if (event.getEntity() instanceof Zombie zombie && event.getNewAboutToBeSetTarget() instanceof Player player
                && strength(player, "rotten") == 8 && zombie.getLastHurtByMob() != player) {
            event.setCanceled(true);
        }
    }

    /** Full-set bonus for stat perks: adds the set's per-piece perks once more; Rotten costs hunger. */
    private static void onPlayerTick(PlayerTickEvent.Post event) {
        Player player = event.getEntity();
        if (player.level().isClientSide() || player.tickCount % 20 != 0) return;
        for (Materials.Gear gear : Materials.GEAR) {
            if (!gear.armorOnly()) continue;
            boolean full = strength(player, gear.id()) == 8;
            for (Materials.Perk perk : gear.armor().perks()) {
                var attribute = BuiltInRegistries.ATTRIBUTE.getHolder(ResourceLocation.parse(perk.attribute()));
                if (attribute.isEmpty()) continue;
                AttributeInstance instance = player.getAttribute(attribute.get());
                if (instance == null) continue;
                ResourceLocation id = ForgedAscent.id("full_set." + gear.id() + "." + ResourceLocation.parse(perk.attribute()).getPath());
                if (full && !instance.hasModifier(id)) {
                    AttributeModifier.Operation op = switch (perk.op()) {
                        case "add_multiplied_base" -> AttributeModifier.Operation.ADD_MULTIPLIED_BASE;
                        case "add_multiplied_total" -> AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL;
                        default -> AttributeModifier.Operation.ADD_VALUE;
                    };
                    instance.addTransientModifier(new AttributeModifier(id, perk.amount() * 4, op));
                } else if (!full && instance.hasModifier(id)) {
                    instance.removeModifier(id);
                }
            }
        }
        if (strength(player, "rotten") == 8) player.causeFoodExhaustion(0.4F);
    }
}
