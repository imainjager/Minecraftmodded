package com.imainjager.forgedascent.mobs;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.Materials;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BiomeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.AbstractSkeleton;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.EnderMan;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.Evoker;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.PatrollingMonster;
import net.minecraft.world.entity.monster.Pillager;
import net.minecraft.world.entity.monster.Ravager;
import net.minecraft.world.entity.monster.Vindicator;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.FinalizeSpawnEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

import java.util.ArrayList;
import java.util.List;

/**
 * Mob difficulty (PLAN.md section 8). Spawn decisions are made in FinalizeSpawnEvent and stored on the mob;
 * they're applied in EntityJoinLevelEvent, after vanilla has finished equipping the mob.
 */
public final class MobEvents {
    private static final String PENDING = "forgedascent_pending";
    private static final String ELITE = "forgedascent_elite";
    private static final String DAMAGE = "forgedascent_damage";
    private static final String AURA = "forgedascent_aura";
    private static final ResourceLocation MOD_ID = ForgedAscent.id("difficulty");

    /** Gear tier band of the armor mobs wear, per world tier. */
    private static final int[][] ARMOR_BAND = {{2, 3}, {3, 4}, {4, 6}, {6, 7}, {7, 8}};

    private record Place(double stat, double elite) {
        static Place of(ServerLevel level, BlockPos pos) {
            if (level.dimension() == Level.NETHER) return new Place(0.40, 0.20);
            if (level.dimension() != Level.OVERWORLD) return new Place(0.75, 0.25);
            if (pos.getY() < -32) return new Place(0.50, 0.20);
            if (pos.getY() < 0) return new Place(0.25, 0.15);
            return new Place(0, 0);
        }
    }

    private MobEvents() {}

    public static void register() {
        NeoForge.EVENT_BUS.addListener(MobEvents::onFinalizeSpawn);
        NeoForge.EVENT_BUS.addListener(MobEvents::onJoin);
        NeoForge.EVENT_BUS.addListener(MobEvents::onIncomingDamage);
        NeoForge.EVENT_BUS.addListener(MobEvents::onTick);
    }

    // ------------------------------------------------------------------ spawning

    private static void onFinalizeSpawn(FinalizeSpawnEvent event) {
        Mob mob = event.getEntity();
        if (!(mob instanceof Enemy) || mob.getType().is(Tags.EntityTypes.BOSSES)) return;
        ServerLevelAccessor accessor = event.getLevel();
        ServerLevel level = accessor.getLevel();
        Vec3 pos = new Vec3(event.getX(), event.getY(), event.getZ());
        BlockPos block = BlockPos.containing(pos);
        RandomSource random = mob.getRandom();
        MobSpawnType spawnType = event.getSpawnType();
        boolean natural = spawnType != MobSpawnType.COMMAND && spawnType != MobSpawnType.SPAWN_EGG;

        int tier = WorldTiers.near(level, pos);
        Place place = Place.of(level, block);
        double eliteChance = Math.min(MobConfig.ELITE_CAP.get(), MobConfig.pick(MobConfig.ELITE_CHANCE, tier) + place.elite());
        EliteType own = EliteMobs.eliteOf(mob.getType());

        // Swap the mob for an elite version of itself.
        EliteMobs.Base base = EliteMobs.baseFor(mob.getType());
        if (own == null && natural && base != null && random.nextDouble() < eliteChance) {
            EliteType elite = pickElite(random, tier, level, block, true);
            Mob replacement = EliteMobs.type(base, elite).create(level);
            if (replacement != null) {
                replacement.moveTo(pos.x, pos.y, pos.z, mob.getYRot(), mob.getXRot());
                replacement.finalizeSpawn(accessor, event.getDifficulty(), spawnType, null);
                replacement.getPersistentData().put(PENDING, pending(tier, place, elite.id(), 1.0, false));
                accessor.addFreshEntityWithPassengers(replacement);
                event.setSpawnCancelled(true);
                return;
            }
        }

        String elite = own != null ? own.id() : "";
        double hardened = 1.0;
        if (own == null && natural && upgradesInPlace(mob) && random.nextDouble() < eliteChance) {
            elite = pickElite(random, tier, level, block, false).id();
        } else if (own == null && tier >= 2 && random.nextDouble() < MobConfig.HARDENED_CHANCE.get()) {
            hardened = tier >= 4 ? 1.5 : 1.25;
        }
        boolean armor = natural && wearsArmor(mob) && random.nextDouble() < MobConfig.pick(MobConfig.ARMOR_CHANCE, tier);
        mob.getPersistentData().put(PENDING, pending(tier, place, elite, hardened, armor));
    }

    private static CompoundTag pending(int tier, Place place, String elite, double hardened, boolean armor) {
        CompoundTag tag = new CompoundTag();
        tag.putInt("tier", tier);
        tag.putDouble("place", place.stat());
        tag.putString("elite", elite);
        tag.putDouble("hardened", hardened);
        tag.putBoolean("armor", armor);
        return tag;
    }

    private static boolean upgradesInPlace(Mob mob) {
        return mob instanceof Creeper || mob instanceof EnderMan || mob instanceof Pillager
                || mob instanceof Vindicator || mob instanceof Evoker || mob instanceof Ravager;
    }

    private static boolean wearsArmor(Mob mob) {
        return mob instanceof Zombie || mob instanceof AbstractSkeleton || mob instanceof AbstractPiglin;
    }

    private static EliteType pickElite(RandomSource random, int tier, ServerLevel level, BlockPos pos, boolean fullSet) {
        List<EliteType> pool = new ArrayList<>();
        Holder<net.minecraft.world.level.biome.Biome> biome = level.getBiome(pos);
        for (EliteType t : EliteType.values()) {
            if (t.minWorldTier > tier) continue;
            if (!fullSet && t != EliteType.RUNNER && t != EliteType.BRUTE && t != EliteType.DREAD) continue;
            if (t == EliteType.MOLTEN && level.dimension() != Level.NETHER) continue;
            if (t == EliteType.FROST && !biome.value().coldEnoughToSnow(pos)) continue;
            if (t == EliteType.VENOMOUS && !(biome.is(BiomeTags.IS_JUNGLE) || biome.is(Tags.Biomes.IS_SWAMP))) continue;
            for (int i = 0; i < t.weight; i++) pool.add(t);
        }
        return pool.get(random.nextInt(pool.size()));
    }

    // ------------------------------------------------------------------ applying

    private static void onJoin(EntityJoinLevelEvent event) {
        if (event.getLevel().isClientSide() || !(event.getEntity() instanceof Mob mob)) return;
        CompoundTag data = mob.getPersistentData();
        if (!data.contains(PENDING)) return;
        CompoundTag p = data.getCompound(PENDING);
        data.remove(PENDING);
        apply(mob, p);
    }

    private static void apply(Mob mob, CompoundTag p) {
        int tier = p.getInt("tier");
        double place = p.getDouble("place");
        EliteType elite = EliteType.byId(p.getString("elite"));
        double health = MobConfig.pick(MobConfig.HEALTH, tier) * (1 + place) * p.getDouble("hardened");
        double damage = MobConfig.pick(MobConfig.DAMAGE, tier) * (1 + place);
        CompoundTag data = mob.getPersistentData();

        if (elite != null) {
            health *= elite.health;
            damage *= elite.damage;
            modify(mob, Attributes.MOVEMENT_SPEED, elite.speed - 1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
            modify(mob, Attributes.KNOCKBACK_RESISTANCE, elite.knockback, AttributeModifier.Operation.ADD_VALUE);
            modify(mob, Attributes.SCALE, elite.scale - 1, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
            data.putString(ELITE, elite.id());
            if (elite == EliteType.DREAD) data.putBoolean(AURA, true);
            upgradeInPlace(mob, elite);
        }
        if (mob instanceof PatrollingMonster patrol && patrol.isPatrolLeader() && tier >= 2) {
            data.putBoolean(AURA, true);
        }
        modify(mob, Attributes.MAX_HEALTH, health - 1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        modify(mob, Attributes.ATTACK_DAMAGE, damage - 1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        data.putDouble(DAMAGE, damage);
        mob.setHealth(mob.getMaxHealth());

        if (p.getBoolean("armor") || (elite == EliteType.ARMORED && wearsArmor(mob))) {
            equipArmor(mob, tier, elite == EliteType.ARMORED);
        }
    }

    private static void modify(Mob mob, Holder<Attribute> attribute, double amount, AttributeModifier.Operation op) {
        AttributeInstance instance = mob.getAttribute(attribute);
        if (instance == null || amount == 0 || instance.hasModifier(MOD_ID)) return;
        instance.addPermanentModifier(new AttributeModifier(MOD_ID, amount, op));
    }

    /** Creepers, endermen and illagers keep their own type; elites change their behavior or gear instead. */
    private static void upgradeInPlace(Mob mob, EliteType elite) {
        if (mob instanceof Creeper creeper) {
            CompoundTag tag = new CompoundTag();
            creeper.addAdditionalSaveData(tag);
            switch (elite) {
                case RUNNER -> tag.putShort("Fuse", (short) 15);
                case BRUTE -> tag.putByte("ExplosionRadius", (byte) 4);
                case DREAD -> tag.putBoolean("powered", true);
                default -> { }
            }
            creeper.readAdditionalSaveData(tag);
        } else if (mob instanceof Pillager) {
            ItemStack crossbow = new ItemStack(Items.CROSSBOW);
            var enchantments = mob.level().registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
            crossbow.enchant(enchantments.getOrThrow(Enchantments.QUICK_CHARGE), 2);
            crossbow.enchant(enchantments.getOrThrow(Enchantments.PIERCING), 2);
            mob.setItemSlot(EquipmentSlot.MAINHAND, crossbow);
        }
    }

    private static void equipArmor(Mob mob, int tier, boolean fullSet) {
        int[] band = ARMOR_BAND[Math.min(tier, ARMOR_BAND.length - 1)];
        List<Materials.Gear> candidates = Materials.GEAR.stream()
                .filter(g -> g.tier() >= band[0] && g.tier() <= band[1]).toList();
        if (candidates.isEmpty()) return;
        RandomSource random = mob.getRandom();
        Materials.Gear gear = candidates.get(random.nextInt(candidates.size()));
        List<EquipmentSlot> slots = new ArrayList<>(List.of(
                EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET));
        int pieces = fullSet ? 4 : 2 + random.nextInt(3);
        for (int i = 0; i < pieces; i++) {
            EquipmentSlot slot = slots.remove(random.nextInt(slots.size()));
            String kind = switch (slot) {
                case HEAD -> "helmet";
                case CHEST -> "chestplate";
                case LEGS -> "leggings";
                default -> "boots";
            };
            Item item = BuiltInRegistries.ITEM.get(ForgedAscent.id(gear.id() + "_" + kind));
            mob.setItemSlot(slot, new ItemStack(item));
            mob.setDropChance(slot, 0.05F);
        }
    }

    // ------------------------------------------------------------------ combat

    private static void onIncomingDamage(LivingIncomingDamageEvent event) {
        DamageSource source = event.getSource();
        if (!(source.getEntity() instanceof Mob attacker)) return;
        CompoundTag data = attacker.getPersistentData();
        // Melee damage scales through the attack-damage attribute; projectiles need this.
        if (source.getDirectEntity() != attacker && data.contains(DAMAGE)) {
            event.setAmount((float) (event.getAmount() * data.getDouble(DAMAGE)));
        }
        LivingEntity victim = event.getEntity();
        switch (data.getString(ELITE)) {
            case "molten" -> victim.igniteForSeconds(4);
            case "frost" -> victim.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1), attacker);
            case "venomous" -> victim.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 0), attacker);
            default -> { }
        }
    }

    /** Dread elites and patrol captains speed up nearby monsters. */
    private static void onTick(EntityTickEvent.Post event) {
        Entity entity = event.getEntity();
        if (entity.tickCount % 40 != 0 || entity.level().isClientSide() || !(entity instanceof Mob mob)) return;
        if (!mob.getPersistentData().getBoolean(AURA)) return;
        for (Monster other : mob.level().getEntitiesOfClass(Monster.class, mob.getBoundingBox().inflate(8))) {
            if (other != mob) other.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 60, 0));
        }
    }
}
