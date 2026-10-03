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

    static {
        ModConfigSpec.Builder b = new ModConfigSpec.Builder();
        b.comment("Forged Ascent mob scaling. Each list has 5 values: Haven, Frontier, Ascent, Summit, Pinnacle.").push("mobs");
        HEALTH = b.comment("Hostile mob max-health multiplier").defineList("healthMultiplier",
                List.of(1.5, 2.0, 3.0, 4.5, 6.0), () -> 1.0, MobConfig::isNumber);
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
