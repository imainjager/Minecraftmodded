package com.imainjager.forgedascent.mobs;

import java.util.Locale;

/** Elite variants (PLAN.md section 8). Multipliers apply on top of world-tier scaling. */
public enum EliteType {
    //        minWorldTier scale  health damage speed  knockback weight lootTier tint
    RUNNER(0, 0.90F, 0.9, 0.75, 1.25, 0.0, 3, 3, 0xDCEBFF),
    BRUTE(0, 1.25F, 2.0, 1.50, 0.85, 0.5, 3, 3, 0x6B5A48),
    ARMORED(2, 1.00F, 1.3, 1.10, 0.95, 0.3, 2, 5, 0x9AA0A6),
    MOLTEN(2, 1.00F, 1.3, 1.20, 1.00, 0.0, 3, 5, 0xFF8A2A),
    FROST(2, 1.00F, 1.3, 1.20, 1.00, 0.0, 3, 5, 0x8FD6FF),
    VENOMOUS(2, 1.00F, 1.3, 1.20, 1.00, 0.0, 3, 5, 0x6FD94A),
    DREAD(4, 1.15F, 4.0, 2.00, 1.05, 0.6, 1, 7, 0x4A2060);

    public final int minWorldTier;
    public final float scale;
    public final double health;
    public final double damage;
    public final double speed;
    public final double knockback;
    public final int weight;
    public final int lootTier;
    public final int tint;

    EliteType(int minWorldTier, float scale, double health, double damage, double speed, double knockback,
              int weight, int lootTier, int tint) {
        this.minWorldTier = minWorldTier;
        this.scale = scale;
        this.health = health;
        this.damage = damage;
        this.speed = speed;
        this.knockback = knockback;
        this.weight = weight;
        this.lootTier = lootTier;
        this.tint = tint;
    }

    public String id() {
        return name().toLowerCase(Locale.ROOT);
    }

    public static EliteType byId(String id) {
        for (EliteType t : values()) {
            if (t.id().equals(id)) return t;
        }
        return null;
    }
}
