package com.imainjager.forgedascent;

import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.Tiers;
import net.neoforged.neoforge.event.ItemAttributeModifierEvent;
import net.neoforged.neoforge.event.ModifyDefaultComponentsEvent;

import java.util.List;
import java.util.Map;

/**
 * Puts vanilla iron (tier 3), diamond (tier 6) and netherite (tier 9) gear on the Forged Ascent gear curve
 * (PLAN.md "Update 4 design"). Armor sets: iron 14, diamond 29, netherite 52. Sword damage: iron 7, diamond 13, netherite 26.
 */
public final class VanillaNerfs {
    private static final Map<Item, Integer> ARMOR = Map.ofEntries(
            Map.entry(Items.IRON_HELMET, 2), Map.entry(Items.IRON_CHESTPLATE, 5),
            Map.entry(Items.IRON_LEGGINGS, 5), Map.entry(Items.IRON_BOOTS, 2),
            Map.entry(Items.DIAMOND_HELMET, 4), Map.entry(Items.DIAMOND_CHESTPLATE, 12),
            Map.entry(Items.DIAMOND_LEGGINGS, 9), Map.entry(Items.DIAMOND_BOOTS, 4),
            Map.entry(Items.NETHERITE_HELMET, 7), Map.entry(Items.NETHERITE_CHESTPLATE, 21),
            Map.entry(Items.NETHERITE_LEGGINGS, 16), Map.entry(Items.NETHERITE_BOOTS, 8));

    private static final List<Item> DIAMOND_ARMOR = List.of(
            Items.DIAMOND_HELMET, Items.DIAMOND_CHESTPLATE, Items.DIAMOND_LEGGINGS, Items.DIAMOND_BOOTS);

    private static final List<Item> DIAMOND_TOOLS = List.of(
            Items.DIAMOND_SWORD, Items.DIAMOND_PICKAXE, Items.DIAMOND_AXE, Items.DIAMOND_SHOVEL, Items.DIAMOND_HOE);

    /** Extra attack damage for vanilla tools of a tier, so their swords hit 7 / 13 / 26. */
    private static final Map<Tiers, Double> TOOL_DAMAGE = Map.of(Tiers.IRON, 1.0, Tiers.DIAMOND, 6.0, Tiers.NETHERITE, 18.0);

    private VanillaNerfs() {}

    public static void modifyDefaultComponents(ModifyDefaultComponentsEvent event) {
        for (Item tool : DIAMOND_TOOLS) {
            event.modify(tool, builder -> builder.set(DataComponents.MAX_DAMAGE, 1000));
        }
    }

    public static void modifyAttributes(ItemAttributeModifierEvent event) {
        Item item = event.getItemStack().getItem();
        if (item instanceof ArmorItem armor) {
            Integer armorValue = ARMOR.get(item);
            if (armorValue == null) return;
            EquipmentSlotGroup slot = EquipmentSlotGroup.bySlot(armor.getEquipmentSlot());
            // Vanilla uses this id for an armor piece's armor and toughness modifiers.
            ResourceLocation vanillaId = ResourceLocation.withDefaultNamespace("armor." + armor.getType().getName());
            event.replaceModifier(Attributes.ARMOR,
                    new AttributeModifier(vanillaId, armorValue, AttributeModifier.Operation.ADD_VALUE), slot);
            if (DIAMOND_ARMOR.contains(item)) {
                event.replaceModifier(Attributes.ARMOR_TOUGHNESS,
                        new AttributeModifier(vanillaId, 1.0, AttributeModifier.Operation.ADD_VALUE), slot);
            }
        } else if (item instanceof TieredItem tiered && tiered.getTier() instanceof Tiers tier) {
            Double extra = TOOL_DAMAGE.get(tier);
            if (extra != null) addToBaseDamage(event, extra);
        }
    }

    /** Raises a tool's base attack damage modifier by {@code extra}. Also used for other mods' gear. */
    static void addToBaseDamage(ItemAttributeModifierEvent event, double extra) {
        Holder<Attribute> attack = Attributes.ATTACK_DAMAGE;
        for (var entry : event.getModifiers()) {
            if (entry.attribute().equals(attack) && entry.modifier().id().equals(Item.BASE_ATTACK_DAMAGE_ID)) {
                event.replaceModifier(attack, new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID,
                        entry.modifier().amount() + extra, entry.modifier().operation()), entry.slot());
                return;
            }
        }
    }
}
