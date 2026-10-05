package com.imainjager.forgedascent.cthulhu;

import com.imainjager.forgedascent.mobs.MobConfig;
import com.imainjager.forgedascent.world.ForgedWorldData;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

import java.util.ArrayList;
import java.util.List;

/**
 * Calls the Eye of Cthulhu: with the Suspicious Looking Eye, or on its own at night (a warning first, then it
 * flies in from afar) until it has been beaten once.
 */
public final class EyeSpawner {
    private EyeSpawner() {}

    public static void register() {
        NeoForge.EVENT_BUS.addListener(EyeSpawner::onLevelTick);
    }

    public static boolean isNight(ServerLevel level) {
        long t = level.getDayTime() % 24000L;
        return t >= 13000L && t < 23000L;
    }

    public static boolean alive(ServerLevel level) {
        for (var e : level.getAllEntities()) {
            if (e instanceof EyeOfCthulhu eye && eye.isAlive()) return true;
        }
        return false;
    }

    /** Spawns the Eye 30 blocks away and high up, flying in. */
    public static EyeOfCthulhu spawnNear(ServerLevel level, Player player, boolean fleesAtDawn) {
        EyeOfCthulhu eye = CthulhuRegistries.EYE.get().create(level);
        if (eye == null) return null;
        double a = level.random.nextDouble() * Math.PI * 2;
        double dist = 30;
        double y = Mth.clamp(player.getY() + 14, level.getMinBuildHeight() + 8, level.getMaxBuildHeight() - 8);
        eye.moveTo(player.getX() + Math.cos(a) * dist, y, player.getZ() + Math.sin(a) * dist, 0, 0);
        eye.setFleesAtDawn(fleesAtDawn);
        level.addFreshEntity(eye);
        for (ServerPlayer p : level.players()) {
            p.sendSystemMessage(Component.translatable("message.forgedascent.eye_awoken").withStyle(ChatFormatting.LIGHT_PURPLE));
            level.playSound(null, p.blockPosition(), SoundEvents.ENDER_DRAGON_GROWL, SoundSource.HOSTILE, 1.5F, 0.6F);
        }
        return eye;
    }

    private static List<ServerPlayer> eligible(ServerLevel level) {
        List<ServerPlayer> out = new ArrayList<>();
        for (ServerPlayer p : level.players()) {
            if (p.isCreative() || p.isSpectator() || !p.isAlive()) continue;
            if (p.getArmorValue() < MobConfig.EYE_MIN_ARMOR.get()) continue;
            if (!level.canSeeSky(p.blockPosition())) continue;
            out.add(p);
        }
        return out;
    }

    private static void onLevelTick(LevelTickEvent.Post event) {
        if (!(event.getLevel() instanceof ServerLevel level) || level.dimension() != Level.OVERWORLD) return;
        if (level.getGameTime() % 20 != 0 || !MobConfig.EYE_NATURAL.get()) return;
        ForgedWorldData data = ForgedWorldData.get(level.getServer());
        if (data.eyeDefeated()) return;
        long time = level.getDayTime();
        long day = time / 24000L;
        long tod = time % 24000L;
        if (tod < 12000L && data.eyePendingAt() >= 0) {
            data.setEyePendingAt(-1);   // the night ended without it showing up
        }
        if (isNight(level) && data.eyeLastRollDay() != day) {
            data.setEyeLastRollDay(day);
            List<ServerPlayer> candidates = eligible(level);
            if (day >= MobConfig.EYE_MIN_DAY.get() && !candidates.isEmpty() && !alive(level)
                    && level.random.nextDouble() < MobConfig.EYE_CHANCE.get()) {
                long at = Math.min(22000L, Math.max(tod, 13500L) + 600L + level.random.nextInt(2400));
                data.setEyePendingAt(at);
                for (ServerPlayer p : candidates) {
                    p.sendSystemMessage(Component.translatable("message.forgedascent.eye_warning").withStyle(ChatFormatting.LIGHT_PURPLE));
                    level.playSound(null, p.blockPosition(), SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 0.8F, 0.6F);
                }
            }
        }
        if (data.eyePendingAt() >= 0 && tod >= data.eyePendingAt() && isNight(level)) {
            List<ServerPlayer> candidates = eligible(level);
            if (!candidates.isEmpty() && !alive(level)) {
                data.setEyePendingAt(-1);
                spawnNear(level, candidates.get(level.random.nextInt(candidates.size())), true);
            } else if (tod > 22500L) {
                data.setEyePendingAt(-1);
            }
        }
    }
}
