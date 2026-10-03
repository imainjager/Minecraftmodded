package com.imainjager.forgedascent;

import com.google.common.base.Suppliers;
import net.minecraft.core.Holder;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.component.ItemAttributeModifiers;

import java.util.function.Supplier;

/** Armor piece that adds the material's stat traits (movement speed, burning time) on top of normal armor stats. */
public class TraitArmorItem extends ArmorItem {
    private final Supplier<ItemAttributeModifiers> modifiers;

    public TraitArmorItem(Holder<ArmorMaterial> material, Type type, Properties properties, Materials.ArmorStats stats) {
        super(material, type, properties);
        this.modifiers = Suppliers.memoize(() -> {
            ItemAttributeModifiers mods = super.getDefaultAttributeModifiers();
            EquipmentSlotGroup slot = EquipmentSlotGroup.bySlot(type.getSlot());
            if (stats.moveSpeed() != 0) {
                mods = mods.withModifierAdded(Attributes.MOVEMENT_SPEED,
                        new AttributeModifier(ForgedAscent.id("armor_speed." + type.getName()), stats.moveSpeed(),
                                AttributeModifier.Operation.ADD_MULTIPLIED_BASE), slot);
            }
            if (stats.burningTime() != 0) {
                mods = mods.withModifierAdded(Attributes.BURNING_TIME,
                        new AttributeModifier(ForgedAscent.id("armor_burning." + type.getName()), stats.burningTime(),
                                AttributeModifier.Operation.ADD_MULTIPLIED_BASE), slot);
            }
            return mods;
        });
    }

    @Override
    public ItemAttributeModifiers getDefaultAttributeModifiers() {
        return modifiers.get();
    }
}
