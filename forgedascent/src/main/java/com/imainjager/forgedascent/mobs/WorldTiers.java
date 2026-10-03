package com.imainjager.forgedascent.mobs;

import com.imainjager.forgedascent.ForgedAscent;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.lang.reflect.Method;

/**
 * Reads the player's Apotheosis world tier (0 = Haven ... 4 = Pinnacle) through reflection,
 * so the mod still loads without Apotheosis (everything is then Haven).
 */
public final class WorldTiers {
    private static final int SEARCH_RADIUS = 128;
    private static Method getTier;
    private static boolean looked;

    private WorldTiers() {}

    public static int of(@Nullable Player player) {
        if (player == null) return 0;
        Method m = method();
        if (m == null) return 0;
        try {
            Object tier = m.invoke(null, player);
            return tier instanceof Enum<?> e ? e.ordinal() : 0;
        } catch (ReflectiveOperationException | RuntimeException e) {
            return 0;
        }
    }

    /** World tier of the nearest player, used for mobs and chests that have no player of their own. */
    public static int near(Level level, Vec3 pos) {
        return of(level.getNearestPlayer(pos.x, pos.y, pos.z, SEARCH_RADIUS, false));
    }

    private static Method method() {
        if (!looked) {
            looked = true;
            try {
                Class<?> c = Class.forName("dev.shadowsoffire.apotheosis.tiers.WorldTier");
                getTier = c.getMethod("getTier", Player.class);
            } catch (ReflectiveOperationException e) {
                ForgedAscent.LOGGER.info("Apotheosis world tiers not found; mob and loot scaling uses Haven");
            }
        }
        return getTier;
    }
}
