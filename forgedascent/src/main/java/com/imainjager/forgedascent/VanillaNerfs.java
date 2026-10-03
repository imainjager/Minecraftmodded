package com.imainjager.forgedascent;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.neoforged.neoforge.event.ItemAttributeModifierEvent;
import net.neoforged.neoforge.event.ModifyDefaultComponentsEvent;

import java.util.List;
import java.util.Map;

/**
 * Moves vanilla iron to tier 3 and diamond to tier 6 stats (PLAN.md section 7).
 * Iron armor 15 -> 13. Diamond armor 20 -> 18, toughness 8 -> 4, tools 1561 -> 1000 durability.
 */
public final class VanillaNerfs {
    private static final Map<Item, Integer> ARMOR = Map.of(
            Items.IRON_CHESTPLATE, 5,
            Items.IRON_LEGGINGS, 4,
            Items.DIAMOND_CHESTPLATE, 7,
            Items.DIAMOND_LEGGINGS, 5);

    private static final List<Item> DIAMOND_ARMOR = List.of(
            Items.DIAMOND_HELMET, Items.DIAMOND_CHESTPLATE, Items.DIAMOND_LEGGINGS, Items.DIAMOND_BOOTS);

    private static final List<Item> DIAMOND_TOOLS = List.of(
            Items.DIAMOND_SWORD, Items.DIAMOND_PICKAXE, Items.DIAMOND_AXE, Items.DIAMOND_SHOVEL, Items.DIAMOND_HOE);

    private VanillaNerfs() {}

    public static void modifyDefaultComponents(ModifyDefaultComponentsEvent event) {
        for (Item tool : DIAMOND_TOOLS) {
            event.modify(tool, builder -> builder.set(DataComponents.MAX_DAMAGE, 1000));
        }
    }

    public static void modifyAttributes(ItemAttributeModifierEvent event) {
        Item item = event.getItemStack().getItem();
        if (!(item instanceof ArmorItem armor)) return;

        EquipmentSlotGroup slot = EquipmentSlotGroup.bySlot(armor.getEquipmentSlot());
        // Vanilla uses this id for an armor piece's armor and toughness modifiers.
        ResourceLocation vanillaId = ResourceLocation.withDefaultNamespace("armor." + armor.getType().getName());

        Integer armorValue = ARMOR.get(item);
        if (armorValue != null) {
            event.replaceModifier(Attributes.ARMOR,
                    new AttributeModifier(vanillaId, armorValue, AttributeModifier.Operation.ADD_VALUE), slot);
        }
        if (DIAMOND_ARMOR.contains(item)) {
            event.replaceModifier(Attributes.ARMOR_TOUGHNESS,
                    new AttributeModifier(vanillaId, 1.0, AttributeModifier.Operation.ADD_VALUE), slot);
        }
    }
}
