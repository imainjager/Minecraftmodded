package com.imainjager.forgedascent.loot;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.Materials;
import com.imainjager.forgedascent.mobs.WorldTiers;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.level.storage.loot.predicates.LootItemCondition;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.loot.IGlobalLootModifier;
import net.neoforged.neoforge.common.loot.LootModifier;

import java.util.List;
import java.util.Set;

/**
 * Adds Forged Ascent materials to every chest loot table, scaled by the opening player's Apotheosis
 * world tier (PLAN.md section 9). Lootr rolls the same tables per player, so it applies there too.
 */
public class TieredChestLoot extends LootModifier {
    public static final MapCodec<TieredChestLoot> CODEC =
            RecordCodecBuilder.mapCodec(inst -> codecStart(inst).apply(inst, TieredChestLoot::new));

    /** Material tier band per loot tier (world tier, +1 outside the Overworld). */
    private static final int[][] BAND = {{2, 3}, {3, 5}, {5, 7}, {6, 8}, {7, 8}};

    /** Removed from early chests (Haven/Frontier) so diamond gear can't be skipped to. */
    private static final Set<Item> ANTI_SKIP = Set.of(Items.DIAMOND, Items.DIAMOND_BLOCK,
            Items.DIAMOND_SWORD, Items.DIAMOND_PICKAXE, Items.DIAMOND_AXE, Items.DIAMOND_SHOVEL, Items.DIAMOND_HOE,
            Items.DIAMOND_HELMET, Items.DIAMOND_CHESTPLATE, Items.DIAMOND_LEGGINGS, Items.DIAMOND_BOOTS);

    public TieredChestLoot(LootItemCondition[] conditions) {
        super(conditions);
    }

    @Override
    public MapCodec<? extends IGlobalLootModifier> codec() {
        return CODEC;
    }

    @Override
    protected ObjectArrayList<ItemStack> doApply(ObjectArrayList<ItemStack> loot, LootContext context) {
        ResourceLocation table = context.getQueriedLootTableId();
        if (table == null || !table.getPath().startsWith("chests/")) return loot;

        Level level = context.getLevel();
        Entity opener = context.getParamOrNull(LootContextParams.THIS_ENTITY);
        int tier;
        if (opener instanceof Player player) {
            tier = WorldTiers.of(player);
        } else {
            Vec3 origin = context.getParamOrNull(LootContextParams.ORIGIN);
            tier = origin == null ? 0 : WorldTiers.near(level, origin);
        }
        if (level.dimension() != Level.OVERWORLD) tier = Math.min(tier + 1, BAND.length - 1);

        RandomSource random = context.getRandom();
        if (tier <= 1) {
            loot.removeIf(stack -> ANTI_SKIP.contains(stack.getItem()) && random.nextFloat() < 0.6F);
        }

        int[] band = BAND[tier];
        int extras = 1 + (random.nextFloat() < 0.5F ? 1 : 0);
        for (int i = 0; i < extras; i++) {
            float roll = random.nextFloat();
            ItemStack stack;
            if (roll < 0.65F) {
                stack = fromTag(random, ForgedAscent.id("tier_materials/" + (band[0] + random.nextInt(band[1] - band[0] + 1))),
                        1 + random.nextInt(4));
            } else if (roll < 0.85F) {
                stack = roughGem(random, band);
            } else if (roll < 0.93F || tier < 2) {
                stack = new ItemStack(item(tier >= 3 ? "diamond_grit_wheel" : "emery_wheel"));
            } else {
                stack = gearPiece(random, band);
            }
            if (!stack.isEmpty()) loot.add(stack);
        }
        if (random.nextFloat() < 0.06F) {
            String type = BLUEPRINTS[random.nextInt(BLUEPRINTS.length)];
            BuiltInRegistries.ITEM.getOptional(ResourceLocation.fromNamespaceAndPath("silentgear", type + "_blueprint"))
                    .ifPresent(item -> loot.add(new ItemStack(item)));
        }
        return loot;
    }

    /** Silent Gear blueprints that can turn up in chests (they stay craftable too). */
    private static final String[] BLUEPRINTS = {"katana", "dagger", "knife", "machete", "mace", "spear", "hammer",
            "excavator", "mattock", "paxel", "saw", "sickle", "prospector_hammer", "shield", "bow", "crossbow",
            "slingshot", "trident"};

    private static ItemStack fromTag(RandomSource random, ResourceLocation tag, int count) {
        return BuiltInRegistries.ITEM.getTag(TagKey.create(Registries.ITEM, tag))
                .flatMap(set -> set.getRandomElement(random))
                .map(Holder::value)
                .map(item -> new ItemStack(item, count))
                .orElse(ItemStack.EMPTY);
    }

    private static ItemStack roughGem(RandomSource random, int[] band) {
        List<Materials.Gem> gems = Materials.GEMS.stream()
                .filter(g -> g.tier() >= band[0] - 1 && g.tier() <= band[1] - 1).toList();
        if (gems.isEmpty()) return ItemStack.EMPTY;
        return new ItemStack(item("rough_" + gems.get(random.nextInt(gems.size())).id()), 1 + random.nextInt(2));
    }

    private static ItemStack gearPiece(RandomSource random, int[] band) {
        List<Materials.Gear> gear = Materials.GEAR.stream()
                .filter(g -> g.tier() >= band[0] && g.tier() <= band[1]).toList();
        if (gear.isEmpty()) return ItemStack.EMPTY;
        String[] kinds = {"sword", "pickaxe", "axe", "helmet", "chestplate", "leggings", "boots"};
        Materials.Gear g = gear.get(random.nextInt(gear.size()));
        return new ItemStack(item(g.id() + "_" + kinds[random.nextInt(kinds.length)]));
    }

    private static Item item(String path) {
        return BuiltInRegistries.ITEM.get(ForgedAscent.id(path));
    }
}
