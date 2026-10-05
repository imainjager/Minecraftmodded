package com.imainjager.forgedascent.mobs;

import net.neoforged.neoforge.common.ModConfigSpec;

import java.util.List;

/** Mob difficulty numbers (PLAN.md section 8), editable in config/forgedascent-common.toml. Lists are per world tier: Haven, Frontier, Ascent, Summit, Pinnacle. */
public final class MobConfig {
    public static final ModConfigSpec SPEC;
    public static final ModConfigSpec.ConfigValue<List<? extends Double>> HEALTH;
    public static final ModConfigSpec.ConfigValue<List<? extends Double>> DAMAGE;
    public static final ModConfigSpec.ConfigValue<List<? extends Double>> ARMOR_CHANCE;
    public static final ModConfigSpec.ConfigValue<List<? extends Double>> ELITE_CHANCE;
    public static final ModConfigSpec.DoubleValue ELITE_CAP;
    public static final ModConfigSpec.DoubleValue HARDENED_CHANCE;
    public static final ModConfigSpec.BooleanValue BLOOD_MOON;
    public static final ModConfigSpec.DoubleValue BLOOD_MOON_CHANCE;
    public static final ModConfigSpec.DoubleValue BLOOD_MOON_SPAWNS;
    public static final ModConfigSpec.BooleanValue DIGGING;
    public static final ModConfigSpec.BooleanValue RESTORE_AT_DAWN;
    public static final ModConfigSpec.IntValue MAX_DIGGERS;
    public static final ModConfigSpec.IntValue MAX_BROKEN;
    public static final ModConfigSpec.BooleanValue EYE_NATURAL;
    public static final ModConfigSpec.DoubleValue EYE_CHANCE;
    public static final ModConfigSpec.IntValue EYE_MIN_ARMOR;
    public static final ModConfigSpec.IntValue EYE_MIN_DAY;
    public static final ModConfigSpec.BooleanValue EYE_FLEES;

    static {
        ModConfigSpec.Builder b = new ModConfigSpec.Builder();
        b.comment("Forged Ascent mob scaling. Each list has 5 values: Haven, Frontier, Ascent, Summit, Pinnacle.").push("mobs");
        HEALTH = b.comment("Hostile mob max-health multiplier").defineList("healthMultiplier",
                List.of(1.5, 2.0, 3.0, 4.0, 5.0), () -> 1.0, MobConfig::isNumber);
        DAMAGE = b.comment("Hostile mob damage multiplier").defineList("damageMultiplier",
                List.of(1.3, 1.5, 1.8, 2.2, 2.8), () -> 1.0, MobConfig::isNumber);
        ARMOR_CHANCE = b.comment("Chance a zombie/skeleton/piglin spawns wearing Forged Ascent armor").defineList("armorChance",
                List.of(0.0, 0.10, 0.20, 0.25, 0.33), () -> 0.0, MobConfig::isNumber);
        ELITE_CHANCE = b.comment("Base chance a mob spawns as an elite (place bonuses are added on top)").defineList("eliteChance",
                List.of(0.05, 0.12, 0.20, 0.27, 0.35), () -> 0.0, MobConfig::isNumber);
        ELITE_CAP = b.comment("Maximum elite chance after place bonuses").defineInRange("eliteCap", 0.5, 0.0, 1.0);
        HARDENED_CHANCE = b.comment("Chance a normal mob is Hardened (Ascent and up) or Ancient (Pinnacle)")
                .defineInRange("hardenedChance", 0.3, 0.0, 1.0);
        b.pop();
        b.comment("Blood moon (starts after a Gate I boss is beaten)").push("blood_moon");
        BLOOD_MOON = b.define("enabled", true);
        BLOOD_MOON_CHANCE = b.comment("Chance each night").defineInRange("chance", 0.125, 0.0, 1.0);
        BLOOD_MOON_SPAWNS = b.comment("Monster spawn multiplier during a blood moon").defineInRange("spawnMultiplier", 2.0, 1.0, 4.0);
        DIGGING = b.comment("Zombies, husks, Brutes and Dread elites dig toward players they can't reach").define("digging", true);
        RESTORE_AT_DAWN = b.comment("Put broken blocks back at sunrise (false = permanent damage, blocks drop as items)")
                .define("restoreAtDawn", false);
        MAX_DIGGERS = b.comment("Most mobs digging at the same time").defineInRange("maxDiggers", 6, 0, 64);
        MAX_BROKEN = b.comment("Most blocks broken per blood moon").defineInRange("maxBrokenBlocks", 150, 0, 10000);
        b.pop();
        b.comment("Eye of Cthulhu (Gate I boss)").push("eye_of_cthulhu");
        EYE_NATURAL = b.comment("The Eye can appear on its own at night until it has been defeated once").define("naturalSpawn", true);
        EYE_CHANCE = b.comment("Chance per night that it appears (while not yet defeated)").defineInRange("chance", 0.33, 0.0, 1.0);
        EYE_MIN_ARMOR = b.comment("A player needs at least this much armor before the Eye will pick them").defineInRange("minArmor", 8, 0, 100);
        EYE_MIN_DAY = b.comment("The Eye never appears on its own before this world day").defineInRange("minDay", 3, 0, 100000);
        EYE_FLEES = b.comment("Natural and item-summoned Eyes retreat when the sun rises").define("fleesAtDawn", true);
        b.pop();
        SPEC = b.build();
    }

    private MobConfig() {}

    private static boolean isNumber(Object o) {
        return o instanceof Number;
    }

    static double pick(ModConfigSpec.ConfigValue<List<? extends Double>> list, int tier) {
        List<? extends Double> values = list.get();
        if (values.isEmpty()) return 0;
        return ((Number) values.get(Math.min(tier, values.size() - 1))).doubleValue();
    }
}
