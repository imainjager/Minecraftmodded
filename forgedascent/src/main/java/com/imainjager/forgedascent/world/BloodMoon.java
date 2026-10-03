package com.imainjager.forgedascent.world;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.mobs.MobConfig;
import com.imainjager.forgedascent.mobs.WorldTiers;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Drowned;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.EventHooks;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.player.CanPlayerSleepEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.event.tick.LevelTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;

import java.util.Map;
import java.util.WeakHashMap;

/**
 * Blood moon (PLAN.md "Update 4 design"): after Gate I is cleared, 1 in 8 nights is a blood moon. Double spawns,
 * more elites, better drops, no sleeping, and zombies / Brutes / Dread elites dig toward players they can't reach.
 * Diggers never break blocks with block entities (machines, chests, storage) or obsidian-tier blocks.
 */
public final class BloodMoon {
    private static final TagKey<Block> SIEGE_PROOF = TagKey.create(Registries.BLOCK, ForgedAscent.id("siege_proof"));
    private static final float MAX_HARDNESS = 50.0F;
    private static final int STUCK_TICKS = 40;

    private static boolean active;
    private static final Map<Mob, Dig> DIGGERS = new WeakHashMap<>();

    private static final class Dig {
        double lastDistance = Double.MAX_VALUE;
        int stuckTicks;
        BlockPos pos;
        float progress;
    }

    private BloodMoon() {}

    public static void register() {
        NeoForge.EVENT_BUS.addListener(BloodMoon::onLevelTick);
        NeoForge.EVENT_BUS.addListener(BloodMoon::onEntityTick);
        NeoForge.EVENT_BUS.addListener(BloodMoon::onSleep);
        NeoForge.EVENT_BUS.addListener(BloodMoon::onDrops);
        NeoForge.EVENT_BUS.addListener((ServerStartedEvent e) -> active = ForgedWorldData.get(e.getServer()).bloodMoon());
        NeoForge.EVENT_BUS.addListener((PlayerEvent.PlayerLoggedInEvent e) -> {
            if (e.getEntity() instanceof ServerPlayer player) PacketDistributor.sendToPlayer(player, new BloodMoonPayload(active));
        });
    }

    public static boolean active() {
        return active;
    }

    public static boolean activeIn(Level level) {
        return active && level.dimension() == Level.OVERWORLD;
    }

    // ------------------------------------------------------------------ night cycle

    private static void onLevelTick(LevelTickEvent.Post event) {
        if (!(event.getLevel() instanceof ServerLevel level) || level.dimension() != Level.OVERWORLD) return;
        if (level.getGameTime() % 20 != 0) return;
        ForgedWorldData data = ForgedWorldData.get(level.getServer());
        long time = level.getDayTime() % 24000;
        long day = level.getDayTime() / 24000;

        if (!data.bloodMoon() && time >= 12500 && time < 13500 && data.lastRolledDay() != day) {
            data.setLastRolledDay(day);
            if (MobConfig.BLOOD_MOON.get() && data.gateCleared(1) && day >= 3
                    && level.getRandom().nextDouble() < MobConfig.BLOOD_MOON_CHANCE.get()) {
                setActive(level, data, true);
            }
        } else if (data.bloodMoon() && (time >= 23000 || time < 12500)) {
            setActive(level, data, false);
        }
    }

    private static void setActive(ServerLevel level, ForgedWorldData data, boolean on) {
        active = on;
        data.setBloodMoon(on);
        DIGGERS.clear();
        if (!on && MobConfig.RESTORE_AT_DAWN.get()) {
            for (ForgedWorldData.Broken b : data.takeBroken()) {
                if (level.isEmptyBlock(b.pos())) level.setBlockAndUpdate(b.pos(), b.state());
            }
        }
        level.getServer().getPlayerList().broadcastSystemMessage(Component.translatable(
                on ? "message.forgedascent.blood_moon_rise" : "message.forgedascent.blood_moon_set")
                .withStyle(on ? ChatFormatting.DARK_RED : ChatFormatting.GOLD), false);
        PacketDistributor.sendToAllPlayers(new BloodMoonPayload(on));
    }

    private static void onSleep(CanPlayerSleepEvent event) {
        if (activeIn(event.getLevel())) event.setProblem(Player.BedSleepingProblem.NOT_SAFE);
    }

    // ------------------------------------------------------------------ spawns and drops

    /** Elite chance bonus while a blood moon is up. */
    public static double eliteBonus(Level level) {
        return activeIn(level) ? 0.15 : 0.0;
    }

    /** Whether to add one extra copy of a naturally spawned monster (keeps it light near crowded players). */
    public static boolean shouldDouble(ServerLevel level, Mob mob) {
        if (!activeIn(level) || !(mob instanceof Monster)) return false;
        if (level.getRandom().nextDouble() >= MobConfig.BLOOD_MOON_SPAWNS.get() - 1.0) return false;
        Player player = level.getNearestPlayer(mob, 64);
        return player != null && level.getEntitiesOfClass(Monster.class, player.getBoundingBox().inflate(48)).size() < 40;
    }

    private static void onDrops(LivingDropsEvent event) {
        LivingEntity entity = event.getEntity();
        if (!(entity.level() instanceof ServerLevel level) || !activeIn(level) || !(entity instanceof Monster)) return;
        if (!(event.getSource().getEntity() instanceof Player player) || level.getRandom().nextFloat() >= 0.25F) return;
        int tier = Math.min(8, 3 + WorldTiers.of(player));
        var tag = TagKey.create(Registries.ITEM, ForgedAscent.id("tier_materials/" + tier));
        BuiltInRegistries.ITEM.getTag(tag).flatMap(set -> set.getRandomElement(level.getRandom())).ifPresent(item -> {
            ItemStack stack = new ItemStack((Item) item.value());
            event.getDrops().add(new ItemEntity(level, entity.getX(), entity.getY(), entity.getZ(), stack));
        });
    }

    // ------------------------------------------------------------------ digging

    private static boolean digger(Mob mob) {
        if (mob instanceof Zombie && !(mob instanceof Drowned)) return true;
        String elite = mob.getPersistentData().getString("forgedascent_elite");
        return elite.equals("brute") || elite.equals("dread");
    }

    private static void onEntityTick(EntityTickEvent.Post event) {
        if (!active || !(event.getEntity() instanceof Mob mob) || !(mob.level() instanceof ServerLevel level)) return;
        if (level.dimension() != Level.OVERWORLD || !MobConfig.DIGGING.get() || !digger(mob)) return;
        if (!(mob.getTarget() instanceof Player target) || mob.distanceTo(target) > 24) {
            stopDigging(level, mob);
            return;
        }
        Dig dig = DIGGERS.get(mob);
        if (dig != null && dig.pos != null) {
            continueDigging(level, mob, dig);
            return;
        }
        if (mob.tickCount % 10 != 0) return;
        if (dig == null) {
            dig = new Dig();
            DIGGERS.put(mob, dig);
        }
        double distance = mob.distanceTo(target);
        dig.stuckTicks = distance < dig.lastDistance - 0.5 ? 0 : dig.stuckTicks + 10;
        dig.lastDistance = distance;
        if (dig.stuckTicks < STUCK_TICKS || diggingCount() >= MobConfig.MAX_DIGGERS.get()) return;
        if (ForgedWorldData.get(level.getServer()).brokenTonight() >= MobConfig.MAX_BROKEN.get()) return;
        if (!EventHooks.canEntityGrief(level, mob)) return;
        dig.pos = pickBlock(level, mob, target);
        dig.progress = 0;
    }

    private static int diggingCount() {
        int n = 0;
        for (Dig d : DIGGERS.values()) if (d.pos != null) n++;
        return n;
    }

    private static BlockPos pickBlock(ServerLevel level, Mob mob, Player target) {
        Direction dir = Direction.getNearest(target.getX() - mob.getX(), 0, target.getZ() - mob.getZ());
        BlockPos feet = mob.blockPosition();
        BlockPos ahead = feet.relative(dir);
        BlockPos[] order;
        if (target.getY() > mob.getY() + 1.5) {
            order = new BlockPos[]{feet.above(2), ahead.above(), ahead.above(2)};
        } else if (target.getY() < mob.getY() - 1.5) {
            order = new BlockPos[]{ahead, ahead.below(), feet.below()};
        } else {
            order = new BlockPos[]{ahead.above(), ahead};
        }
        for (BlockPos pos : order) {
            if (breakable(level, pos)) return pos;
        }
        return null;
    }

    private static boolean breakable(ServerLevel level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (state.isAir() || !state.getFluidState().isEmpty() || state.hasBlockEntity() || state.is(SIEGE_PROOF)) return false;
        float hardness = state.getDestroySpeed(level, pos);
        return hardness >= 0 && hardness < MAX_HARDNESS;
    }

    private static void continueDigging(ServerLevel level, Mob mob, Dig dig) {
        if (!breakable(level, dig.pos)) {
            level.destroyBlockProgress(mob.getId(), dig.pos, -1);
            dig.pos = null;
            return;
        }
        BlockState state = level.getBlockState(dig.pos);
        float hardness = Math.max(0.2F, state.getDestroySpeed(level, dig.pos));
        boolean strong = !(mob instanceof Zombie) || !mob.getPersistentData().getString("forgedascent_elite").isEmpty();
        dig.progress += (strong ? 2.0F : 1.0F) / (hardness * 30.0F + 10.0F);
        mob.getLookControl().setLookAt(dig.pos.getX() + 0.5, dig.pos.getY() + 0.5, dig.pos.getZ() + 0.5);
        if (mob.tickCount % 5 == 0) {
            level.destroyBlockProgress(mob.getId(), dig.pos, Math.min(9, (int) (dig.progress * 10)));
            mob.swing(net.minecraft.world.InteractionHand.MAIN_HAND);
        }
        if (dig.progress >= 1.0F) {
            level.destroyBlockProgress(mob.getId(), dig.pos, -1);
            boolean restore = MobConfig.RESTORE_AT_DAWN.get();
            ForgedWorldData.get(level.getServer()).recordBroken(dig.pos, state, restore);
            level.destroyBlock(dig.pos, !restore, mob);
            dig.pos = null;
            dig.stuckTicks = 0;
        }
    }

    private static void stopDigging(ServerLevel level, Mob mob) {
        Dig dig = DIGGERS.remove(mob);
        if (dig != null && dig.pos != null) level.destroyBlockProgress(mob.getId(), dig.pos, -1);
    }
}
