package com.imainjager.forgedascent.mobs;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Skeleton;
import net.minecraft.world.entity.monster.Spider;
import net.minecraft.world.entity.monster.Witch;
import net.minecraft.world.entity.monster.WitherSkeleton;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.monster.piglin.Piglin;
import net.minecraft.world.level.Level;

/** Elite mob classes: vanilla mobs with extra XP. Stats, look and effects come from EliteMobs/MobEvents. */
public final class EliteEntities {
    private EliteEntities() {}

    private static int xp(EntityType<?> type, int base) {
        EliteType elite = EliteMobs.eliteOf(type);
        return elite == null ? base : (int) Math.round(base * (1 + elite.health));
    }

    public static class EliteZombie extends Zombie {
        public EliteZombie(EntityType<? extends Zombie> type, Level level) {
            super(type, level);
            this.xpReward = xp(type, this.xpReward);
        }
    }

    public static class EliteSkeleton extends Skeleton {
        public EliteSkeleton(EntityType<? extends Skeleton> type, Level level) {
            super(type, level);
            this.xpReward = xp(type, this.xpReward);
        }
    }

    public static class EliteSpider extends Spider {
        public EliteSpider(EntityType<? extends Spider> type, Level level) {
            super(type, level);
            this.xpReward = xp(type, this.xpReward);
        }
    }

    public static class EliteWitherSkeleton extends WitherSkeleton {
        public EliteWitherSkeleton(EntityType<? extends WitherSkeleton> type, Level level) {
            super(type, level);
            this.xpReward = xp(type, this.xpReward);
        }
    }

    public static class ElitePiglin extends Piglin {
        public ElitePiglin(EntityType<? extends AbstractPiglin> type, Level level) {
            super(type, level);
            this.xpReward = xp(type, this.xpReward);
        }
    }

    public static class EliteWitch extends Witch {
        public EliteWitch(EntityType<? extends Witch> type, Level level) {
            super(type, level);
            this.xpReward = xp(type, this.xpReward);
        }
    }
}
