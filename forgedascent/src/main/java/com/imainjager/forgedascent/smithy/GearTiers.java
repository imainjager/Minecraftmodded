package com.imainjager.forgedascent.smithy;

import com.imainjager.forgedascent.ForgedAscent;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.ItemAttributeModifierEvent;
import net.neoforged.neoforge.event.TagsUpdatedEvent;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;

import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/**
 * Works out the Forged Ascent tier (0–9) of any tool or armor, boosts other mods' gear to the gear curve
 * (PLAN.md "Update 4 design"), and applies the Reinforced bonus.
 */
public final class GearTiers {
    /** Set armor total and sword damage per tier. */
    private static final int[] ARMOR_CURVE = {7, 9, 10, 14, 18, 23, 29, 36, 45, 52};
    private static final double[] SWORD_CURVE = {4, 5, 6, 7, 9, 10.5, 13, 18, 24, 26};

    /** Our own gear: item path -> tier. Filled during registration. */
    public static final Map<String, Integer> OWN = new HashMap<>();

    /** Gear from other mods whose tier is known exactly (item id prefix -> tier). */
    private static final Map<String, Integer> KNOWN = Map.ofEntries(
            Map.entry("minecraft:wooden_", 0), Map.entry("minecraft:leather_", 1), Map.entry("minecraft:stone_", 1),
            Map.entry("minecraft:golden_", 2), Map.entry("minecraft:chainmail_", 2), Map.entry("minecraft:turtle_", 2),
            Map.entry("minecraft:iron_", 3), Map.entry("minecraft:diamond_", 6), Map.entry("minecraft:netherite_", 9),
            Map.entry("everythingcopper:", 2), Map.entry("iceandfire:armor_copper", 2), Map.entry("iceandfire:copper_", 2),
            Map.entry("iceandfire:armor_silver", 4), Map.entry("iceandfire:silver_", 4),
            Map.entry("mekanismtools:lapis_lazuli_", 3), Map.entry("mekanismtools:bronze_", 4),
            Map.entry("mekanismtools:steel_", 5), Map.entry("mekanismtools:osmium_", 5),
            Map.entry("mekanismtools:refined_glowstone_", 6), Map.entry("mekanismtools:refined_obsidian_", 8),
            Map.entry("immersiveengineering:armor_steel", 5), Map.entry("immersiveengineering:pickaxe_steel", 5),
            Map.entry("immersiveengineering:sword_steel", 5), Map.entry("immersiveengineering:axe_steel", 5),
            Map.entry("immersiveengineering:shovel_steel", 5), Map.entry("immersiveengineering:hoe_steel", 5));

    private static final ResourceLocation REINFORCED_ID = ForgedAscent.id("reinforced");
    private static final ResourceLocation BOOST_ID = ForgedAscent.id("tier_boost");
    private static final Map<Item, Integer> CACHE = new IdentityHashMap<>();

    private GearTiers() {}

    public static void register() {
        NeoForge.EVENT_BUS.addListener(GearTiers::onAttributes);
        NeoForge.EVENT_BUS.addListener((TagsUpdatedEvent e) -> CACHE.clear());
        NeoForge.EVENT_BUS.addListener(GearTiers::onTooltip);
    }

    /** Tier of a piece of gear, or 0 if unknown. */
    public static int of(ItemStack stack) {
        return of(stack.getItem());
    }

    public static int of(Item item) {
        return CACHE.computeIfAbsent(item, GearTiers::compute);
    }

    private static int compute(Item item) {
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(item);
        if (id.getNamespace().equals(ForgedAscent.MOD_ID)) return OWN.getOrDefault(id.getPath(), 0);
        String full = id.toString();
        for (var entry : KNOWN.entrySet()) {
            if (full.startsWith(entry.getKey())) return entry.getValue();
        }
        if (item instanceof TieredItem tiered) return toolTier(tiered);
        if (item instanceof ArmorItem armor) return armorTier(armor);
        return 0;
    }

    /** Highest ore tier the tool can harvest, checked against Forged Ascent's needs_tier_N block tags. */
    private static int toolTier(TieredItem tool) {
        TagKey<Block> incorrect = tool.getTier().getIncorrectBlocksForDrops();
        int best = 0;
        for (int n = 1; n <= 8; n++) {
            TagKey<Block> needs = TagKey.create(Registries.BLOCK, ForgedAscent.id("needs_tier_" + n));
            var blocks = BuiltInRegistries.BLOCK.getTag(needs);
            if (blocks.isEmpty()) continue;
            boolean canMine = false;
            for (Holder<Block> block : blocks.get()) {
                if (!block.is(incorrect)) {
                    canMine = true;
                    break;
                }
            }
            if (!canMine) break;
            best = n;
        }
        if (best == 8 && tool.getTier().getAttackDamageBonus() >= 4) best = 9;
        return best;
    }

    /** Estimate from the armor material's set total (vanilla-like values). */
    private static int armorTier(ArmorItem armor) {
        ArmorMaterial material = armor.getMaterial().value();
        int total = 0;
        for (ArmorItem.Type type : List.of(ArmorItem.Type.HELMET, ArmorItem.Type.CHESTPLATE,
                ArmorItem.Type.LEGGINGS, ArmorItem.Type.BOOTS)) {
            total += material.getDefense(type);
        }
        if (total <= 9) return 1;
        if (material.toughness() >= 3) return 9;
        if (total <= 12) return 2;
        if (total <= 15) return 3;
        if (total <= 17) return 4;
        if (total <= 19) return 5;
        if (total <= 20) return 6;
        if (total <= 26) return 7;
        if (total <= 34) return 8;
        return 9;
    }

    private static void onAttributes(ItemAttributeModifierEvent event) {
        ItemStack stack = event.getItemStack();
        Item item = stack.getItem();
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(item);
        String ns = id.getNamespace();
        boolean boost = !ns.equals("minecraft") && !ns.equals(ForgedAscent.MOD_ID) && !ns.equals("silentgear");

        if (item instanceof ArmorItem armor) {
            EquipmentSlotGroup slot = EquipmentSlotGroup.bySlot(armor.getEquipmentSlot());
            if (boost) boostArmor(event, armor, slot);
            if (SmithyRegistries.reinforcement(stack) > 0) {
                event.addModifier(Attributes.ARMOR, new AttributeModifier(REINFORCED_ID, SmithyRegistries.reinforcement(stack),
                        AttributeModifier.Operation.ADD_VALUE), slot);
            }
        } else if (item instanceof TieredItem tool) {
            if (boost) {
                int tier = of(item);
                double wanted = SWORD_CURVE[tier] - 4;
                double extra = wanted - tool.getTier().getAttackDamageBonus();
                if (extra > 0.5) {
                    event.addModifier(Attributes.ATTACK_DAMAGE, new AttributeModifier(BOOST_ID, extra,
                            AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
                }
            }
            if (SmithyRegistries.reinforcement(stack) > 0) {
                event.addModifier(Attributes.ATTACK_DAMAGE, new AttributeModifier(REINFORCED_ID, SmithyRegistries.reinforcement(stack),
                        AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
            }
        } else if (SmithyRegistries.reinforcement(stack) > 0 && stack.isDamageableItem()) {
            event.addModifier(Attributes.ATTACK_DAMAGE, new AttributeModifier(REINFORCED_ID, SmithyRegistries.reinforcement(stack),
                    AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
        }
    }

    private static void boostArmor(ItemAttributeModifierEvent event, ArmorItem armor, EquipmentSlotGroup slot) {
        ArmorMaterial material = armor.getMaterial().value();
        int total = 0;
        for (ArmorItem.Type type : List.of(ArmorItem.Type.HELMET, ArmorItem.Type.CHESTPLATE,
                ArmorItem.Type.LEGGINGS, ArmorItem.Type.BOOTS)) {
            total += material.getDefense(type);
        }
        if (total <= 0) return;
        double factor = (double) ARMOR_CURVE[of(armor)] / total;
        if (factor < 1.05) return;
        ResourceLocation vanillaId = ResourceLocation.withDefaultNamespace("armor." + armor.getType().getName());
        for (var entry : event.getModifiers()) {
            if (entry.attribute().equals(Attributes.ARMOR) && entry.modifier().id().equals(vanillaId)) {
                event.replaceModifier(Attributes.ARMOR, new AttributeModifier(vanillaId,
                        Math.round(entry.modifier().amount() * factor), entry.modifier().operation()), entry.slot());
                return;
            }
        }
    }

    private static void onTooltip(ItemTooltipEvent event) {
        int level = SmithyRegistries.reinforcement(event.getItemStack());
        if (level > 0) {
            event.getToolTip().add(1, Component.translatable("tooltip.forgedascent.reinforced",
                    Component.translatable("enchantment.level." + level)).withStyle(ChatFormatting.AQUA));
        }
    }
}
