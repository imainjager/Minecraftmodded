package com.imainjager.forgedascent.cthulhu;

import com.imainjager.forgedascent.ForgedAscent;
import com.imainjager.forgedascent.mobs.MobConfig;
import com.imainjager.forgedascent.world.ForgedWorldData;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;
import org.joml.Vector3f;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Eye of Cthulhu, a Terraria-style Gate I boss. Phase 1 is a huge bloodshot eyeball that hovers over you, then
 * dashes at you in threes and calls Servants. At half health it transforms into a fanged maw (phase 2) that
 * dashes faster in fours and ends each round with a roar that throws everyone nearby back.
 *
 * It flies through blocks (no hiding in a hole), is not scaled by world tier (it is a gate boss), and drops the
 * Gate I Treasure Bag through {@code BossGates}. Look and animation: tools/mobforge (GeckoLib model).
 */
public class EyeOfCthulhu extends Monster implements GeoEntity {
    public static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(EyeOfCthulhu.class, EntityDataSerializers.INT);
    public static final EntityDataAccessor<Integer> STATE = SynchedEntityData.defineId(EyeOfCthulhu.class, EntityDataSerializers.INT);

    public enum State { HOVER, WINDUP, CHARGE, RECOVER, SUMMON, TRANSFORM, ROAR }

    private record Step(State state, int ticks) {}

    private static final int TRANSFORM_TICKS = 70;
    private static final int TRANSFORM_SWAP_AT = 36;
    private static final int DEATH_TICKS = 70;

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final ServerBossEvent bossEvent = new ServerBossEvent(Component.translatable("entity.forgedascent.eye_of_cthulhu"),
            BossEvent.BossBarColor.RED, BossEvent.BossBarOverlay.NOTCHED_10);

    // server-side fight state
    private final ArrayDeque<Step> plan = new ArrayDeque<>();
    private Step current = new Step(State.HOVER, 60);
    private int ticksInState;
    private Vec3 dashDir = Vec3.ZERO;
    private final Set<UUID> hitThisDash = new HashSet<>();
    private double hoverAngle;
    private int hoverSign = 1;
    private int targetCooldown;
    private UUID targetId;
    private boolean fleesAtDawn;
    private int fleeTicks = -1;
    private int idleTicks;
    private boolean tookPartInFight;

    // death
    private DamageSource deathSource;
    private Player deathKiller;

    // client-side movement measure for the walk/idle animation choice
    public double movedSq;

    public EyeOfCthulhu(EntityType<? extends EyeOfCthulhu> type, Level level) {
        super(type, level);
        this.xpReward = 500;
        this.noPhysics = true;
        this.setNoGravity(true);
        this.setPersistenceRequired();
        this.hoverAngle = level.random.nextDouble() * Math.PI * 2;
        this.hoverSign = level.random.nextBoolean() ? 1 : -1;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 400.0)
                .add(Attributes.ATTACK_DAMAGE, 14.0)
                .add(Attributes.ARMOR, 6.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0)
                .add(Attributes.FOLLOW_RANGE, 96.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(PHASE, 1);
        builder.define(STATE, 0);
    }

    public int phase() {
        return this.entityData.get(PHASE);
    }

    public State state() {
        return State.values()[Mth.clamp(this.entityData.get(STATE), 0, State.values().length - 1)];
    }

    private void setState(State state) {
        this.entityData.set(STATE, state.ordinal());
    }

    /** Called by the spawner: this Eye leaves when the sun rises, like the Terraria one. */
    public void setFleesAtDawn(boolean flees) {
        this.fleesAtDawn = flees && MobConfig.EYE_FLEES.get();
    }

    // ------------------------------------------------------------------ boss bar

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        bossEvent.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bossEvent.removePlayer(player);
    }

    @Override
    public void setCustomName(@Nullable Component name) {
        super.setCustomName(name);
        bossEvent.setName(this.getDisplayName());
    }

    // ------------------------------------------------------------------ rules of the body

    @Override
    public boolean canBeLeashed() {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return false;
    }

    @Override
    protected void checkFallDamage(double y, boolean onGround, net.minecraft.world.level.block.state.BlockState state, net.minecraft.core.BlockPos pos) {
    }

    @Override
    public boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public boolean isInvulnerableTo(DamageSource source) {
        return source.is(DamageTypes.IN_WALL) || source.is(DamageTypes.DROWN) || source.is(DamageTypes.FALL)
                || source.is(DamageTypes.FLY_INTO_WALL) || super.isInvulnerableTo(source);
    }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        if (!level().isClientSide && state() == State.TRANSFORM && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return false;  // it is busy being reborn
        }
        boolean hurt = super.hurt(source, amount);
        if (hurt && !level().isClientSide) tookPartInFight = true;
        return hurt;
    }

    @Override
    public void travel(Vec3 input) {
        // the fight code sets the velocity; just move and slow down a little
        this.move(MoverType.SELF, this.getDeltaMovement());
        this.setDeltaMovement(this.getDeltaMovement().scale(0.98));
    }

    // ------------------------------------------------------------------ ticking

    @Override
    public void tick() {
        double ox = getX(), oy = getY(), oz = getZ();
        super.tick();
        movedSq = (getX() - ox) * (getX() - ox) + (getY() - oy) * (getY() - oy) + (getZ() - oz) * (getZ() - oz);
        this.yBodyRot = getYRot();
        this.yHeadRot = getYRot();
        if (level().isClientSide) {
            clientEffects();
            return;
        }
        if (isDeadOrDying() || isNoAi()) return;
        serverFight();
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        bossEvent.setProgress(getHealth() / getMaxHealth());
        bossEvent.setColor(phase() == 1 ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.PURPLE);
    }

    private void clientEffects() {
        if (isDeadOrDying()) {
            if (deathTime % 2 == 0) {
                for (int i = 0; i < 3; i++) {
                    level().addParticle(new DustParticleOptions(new Vector3f(0.75f, 0.05f, 0.1f), 1.6f),
                            getX() + (random.nextDouble() - 0.5) * 3, getY() + 1.3 + (random.nextDouble() - 0.5) * 3,
                            getZ() + (random.nextDouble() - 0.5) * 3, 0, 0.05, 0);
                }
            }
            return;
        }
        State s = state();
        if (s == State.CHARGE && tickCount % 2 == 0) {
            level().addParticle(new DustParticleOptions(new Vector3f(0.7f, 0.05f, 0.1f), 1.4f),
                    getX() + (random.nextDouble() - 0.5), getY() + 1.3 + (random.nextDouble() - 0.5), getZ() + (random.nextDouble() - 0.5), 0, 0, 0);
        }
        if (s == State.TRANSFORM && tickCount % 2 == 0) {
            level().addParticle(ParticleTypes.CRIMSON_SPORE, getX() + (random.nextDouble() - 0.5) * 3, getY() + 1.3 + (random.nextDouble() - 0.5) * 3,
                    getZ() + (random.nextDouble() - 0.5) * 3, 0, 0.1, 0);
        }
    }

    private Player findTarget() {
        Player keep = null;
        if (targetId != null && level() instanceof ServerLevel sl) {
            var e = sl.getEntity(targetId);
            if (e instanceof Player p && p.isAlive() && !p.isCreative() && !p.isSpectator() && p.distanceToSqr(this) < 110 * 110) keep = p;
        }
        if (keep != null && targetCooldown-- > 0) return keep;
        targetCooldown = 20;
        Player nearest = level().getNearestPlayer(getX(), getY(), getZ(), 96.0, EntitySelector.NO_CREATIVE_OR_SPECTATOR);
        targetId = nearest == null ? null : nearest.getUUID();
        return nearest;
    }

    private void serverFight() {
        ServerLevel level = (ServerLevel) level();
        Player target = findTarget();
        setTarget(target);

        // leaves at sunrise when summoned the Terraria way
        if (fleesAtDawn && fleeTicks < 0 && level.isDay() && state() != State.TRANSFORM && level.dimension() == Level.OVERWORLD) {
            fleeTicks = 0;
            broadcastNear(Component.translatable("message.forgedascent.eye_retreats").withStyle(ChatFormatting.LIGHT_PURPLE));
        }
        if (fleeTicks >= 0) {
            fleeTicks++;
            setDeltaMovement(getDeltaMovement().add(0, 0.04, 0).scale(1.04));
            if (fleeTicks > 70) {
                level.sendParticles(ParticleTypes.POOF, getX(), getY() + 1.3, getZ(), 40, 1, 1, 1, 0.05);
                discard();
            }
            return;
        }

        if (target == null) {
            idleTicks++;
            setState(State.HOVER);
            setDeltaMovement(getDeltaMovement().add(Math.cos(tickCount * 0.04) * 0.004, Math.sin(tickCount * 0.05) * 0.004, Math.sin(tickCount * 0.04) * 0.004));
            if (idleTicks > 20 * 60 * 3 && fleesAtDawn) discard();
            return;
        }
        idleTicks = 0;

        // transformation at half health
        if (phase() == 1 && getHealth() <= getMaxHealth() * 0.5f && state() != State.TRANSFORM) {
            enter(new Step(State.TRANSFORM, TRANSFORM_TICKS), target);
            plan.clear();
        }

        ticksInState++;
        switch (current.state()) {
            case HOVER -> tickHover(target);
            case WINDUP -> tickWindup(target);
            case CHARGE -> tickCharge(target);
            case RECOVER -> tickRecover(target);
            case SUMMON -> tickSummon(target);
            case ROAR -> tickRoar(target);
            case TRANSFORM -> tickTransform(target);
        }
        if (ticksInState >= current.ticks()) {
            advance(target);
        }
    }

    // ------------------------------------------------------------------ plan of attack

    private void buildPlan() {
        plan.clear();
        if (phase() == 1) {
            plan.add(new Step(State.HOVER, 50 + random.nextInt(40)));
            for (int i = 0; i < 3; i++) {
                plan.add(new Step(State.WINDUP, i == 0 ? 18 : 12));
                plan.add(new Step(State.CHARGE, 24));
                plan.add(new Step(State.HOVER, 18));
            }
            plan.add(new Step(State.SUMMON, 30));
            plan.add(new Step(State.HOVER, 50));
        } else {
            plan.add(new Step(State.HOVER, 24 + random.nextInt(24)));
            for (int i = 0; i < 4; i++) {
                plan.add(new Step(State.WINDUP, i == 0 ? 14 : 9));
                plan.add(new Step(State.CHARGE, 20));
                plan.add(new Step(State.RECOVER, 14));
            }
            plan.add(new Step(State.ROAR, 40));
            plan.add(new Step(State.HOVER, 30));
        }
    }

    private void advance(Player target) {
        if (plan.isEmpty()) buildPlan();
        enter(plan.poll(), target);
    }

    private void enter(Step step, Player target) {
        current = step;
        ticksInState = 0;
        setState(step.state());
        switch (step.state()) {
            case WINDUP -> {
                playSound(SoundEvents.PHANTOM_SWOOP, 2.0F, phase() == 1 ? 0.6F : 0.45F);
                if (random.nextInt(3) == 0) hoverSign = -hoverSign;
            }
            case CHARGE -> {
                Vec3 aim = target.getBoundingBox().getCenter().add(target.getDeltaMovement().scale(4));
                dashDir = aim.subtract(position().add(0, getBbHeight() / 2, 0)).normalize();
                hitThisDash.clear();
                playSound(SoundEvents.ENDER_DRAGON_FLAP, 3.0F, 0.6F);
                playSound(phase() == 1 ? SoundEvents.RAVAGER_ROAR : SoundEvents.ENDER_DRAGON_GROWL, 2.0F, phase() == 1 ? 1.4F : 1.1F);
            }
            case ROAR -> playSound(SoundEvents.ENDER_DRAGON_GROWL, 4.0F, 0.7F);
            case SUMMON -> playSound(SoundEvents.RAVAGER_ROAR, 3.0F, 0.6F);
            case TRANSFORM -> {
                playSound(SoundEvents.WITHER_SPAWN, 3.0F, 0.6F);
                broadcastNear(Component.translatable("message.forgedascent.eye_enraged").withStyle(ChatFormatting.DARK_RED));
            }
            default -> { }
        }
    }

    // ------------------------------------------------------------------ the moves

    private void steer(Vec3 goal, double maxSpeed, double accel) {
        Vec3 to = goal.subtract(position());
        double speed = Math.min(maxSpeed, to.length() * 0.16);
        Vec3 desired = to.lengthSqr() < 1.0E-4 ? Vec3.ZERO : to.normalize().scale(speed);
        setDeltaMovement(getDeltaMovement().lerp(desired, accel));
    }

    private void face(Vec3 point, float maxTurn) {
        Vec3 to = point.subtract(position().add(0, getBbHeight() / 2, 0));
        float yaw = (float) (Mth.atan2(-to.x, to.z) * Mth.RAD_TO_DEG);
        float pitch = (float) (-Mth.atan2(to.y, Math.sqrt(to.x * to.x + to.z * to.z)) * Mth.RAD_TO_DEG);
        setYRot(Mth.approachDegrees(getYRot(), yaw, maxTurn));
        setXRot(Mth.approachDegrees(getXRot(), pitch, maxTurn));
    }

    private void tickHover(Player target) {
        boolean p1 = phase() == 1;
        hoverAngle += (p1 ? 0.035 : 0.065) * hoverSign;
        double radius = p1 ? 8.0 : 5.5;
        Vec3 goal = target.position().add(Math.cos(hoverAngle) * radius, 5.5 + (p1 ? 1.0 : 0.0), Math.sin(hoverAngle) * radius);
        steer(goal, p1 ? 0.5 : 0.7, p1 ? 0.12 : 0.16);
        face(target.getEyePosition(), 14f);
    }

    private void tickWindup(Player target) {
        setDeltaMovement(getDeltaMovement().scale(0.78));
        face(target.getBoundingBox().getCenter(), 45f);
        if (ticksInState % 6 == 0) {
            ((ServerLevel) level()).sendParticles(new DustParticleOptions(new Vector3f(0.8f, 0.1f, 0.1f), 1.5f),
                    getX(), getY() + 1.3, getZ(), 6, 0.8, 0.8, 0.8, 0.01);
        }
    }

    private void tickCharge(Player target) {
        boolean p1 = phase() == 1;
        double speed = p1 ? 1.05 : 1.4;
        setDeltaMovement(dashDir.scale(speed));
        float yaw = (float) (Mth.atan2(-dashDir.x, dashDir.z) * Mth.RAD_TO_DEG);
        float pitch = (float) (-Mth.atan2(dashDir.y, Math.sqrt(dashDir.x * dashDir.x + dashDir.z * dashDir.z)) * Mth.RAD_TO_DEG);
        setYRot(Mth.approachDegrees(getYRot(), yaw, 60f));
        setXRot(Mth.approachDegrees(getXRot(), pitch, 60f));
        double damage = getAttributeValue(Attributes.ATTACK_DAMAGE) * (p1 ? 1.0 : 1.35);
        AABB box = getBoundingBox().inflate(0.35);
        for (Player p : level().getEntitiesOfClass(Player.class, box, EntitySelector.NO_CREATIVE_OR_SPECTATOR)) {
            if (hitThisDash.add(p.getUUID())) {
                if (p.hurt(damageSources().mobAttack(this), (float) damage)) {
                    p.knockback(1.4, -dashDir.x, -dashDir.z);
                    p.setDeltaMovement(p.getDeltaMovement().add(0, 0.35, 0));
                    p.hurtMarked = true;
                    playSound(SoundEvents.GENERIC_EXPLODE.value(), 0.8F, 1.6F);
                }
            }
        }
    }

    private void tickRecover(Player target) {
        setDeltaMovement(getDeltaMovement().scale(0.8));
        face(target.getEyePosition(), 30f);
        if (ticksInState == 1) playSound(SoundEvents.PLAYER_ATTACK_CRIT, 1.5F, 0.5F);
    }

    private void tickSummon(Player target) {
        setDeltaMovement(getDeltaMovement().scale(0.85).add(0, 0.01, 0));
        face(target.getEyePosition(), 20f);
        if (ticksInState == 14) spawnServants(phase() == 1 ? 2 + random.nextInt(2) : 3);
    }

    private void tickRoar(Player target) {
        setDeltaMovement(getDeltaMovement().scale(0.85).add(0, 0.012, 0));
        face(target.getEyePosition(), 20f);
        if (ticksInState == 16) {
            ServerLevel level = (ServerLevel) level();
            double radius = 14;
            for (Player p : level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(radius), EntitySelector.NO_CREATIVE_OR_SPECTATOR)) {
                Vec3 away = p.position().subtract(position()).multiply(1, 0, 1);
                if (away.lengthSqr() < 1.0E-4) away = new Vec3(1, 0, 0);
                away = away.normalize();
                if (p.hurt(damageSources().mobAttack(this), (float) (getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.6))) {
                    p.setDeltaMovement(away.x * 1.6, 0.6, away.z * 1.6);
                    p.hurtMarked = true;
                }
            }
            for (int ring = 0; ring < 3; ring++) {
                for (int i = 0; i < 48; i++) {
                    double a = i / 48.0 * Math.PI * 2;
                    double r = 2.5 + ring * 3.5;
                    level.sendParticles(new DustParticleOptions(new Vector3f(0.8f, 0.05f, 0.1f), 2.0f),
                            getX() + Math.cos(a) * r, getY() + 1.0, getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0);
                }
            }
            level.sendParticles(ParticleTypes.SONIC_BOOM, getX(), getY() + 1.3, getZ(), 1, 0, 0, 0, 0);
            playSound(SoundEvents.GENERIC_EXPLODE.value(), 3.0F, 0.6F);
            spawnServants(2);
        }
    }

    private void tickTransform(Player target) {
        // spiral up gently while the body rebuilds itself
        setDeltaMovement(getDeltaMovement().scale(0.9).add(0, ticksInState < 40 ? 0.012 : -0.004, 0));
        face(target.getEyePosition(), 6f);
        if (ticksInState == TRANSFORM_SWAP_AT) {
            this.entityData.set(PHASE, 2);
            bossEvent.setColor(BossEvent.BossBarColor.PURPLE);
            ServerLevel level = (ServerLevel) level();
            level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, getX(), getY() + 1.3, getZ(), 1, 0, 0, 0, 0);
            level.sendParticles(new DustParticleOptions(new Vector3f(0.7f, 0.0f, 0.1f), 3f), getX(), getY() + 1.3, getZ(), 80, 1.5, 1.5, 1.5, 0.05);
            playSound(SoundEvents.ENDER_DRAGON_GROWL, 5.0F, 0.6F);
        }
    }

    private void spawnServants(int count) {
        ServerLevel level = (ServerLevel) level();
        List<EyeServant> alive = level.getEntitiesOfClass(EyeServant.class, getBoundingBox().inflate(48), s -> getUUID().equals(s.ownerId()));
        int room = 6 - alive.size();
        for (int i = 0; i < Math.min(count, room); i++) {
            EyeServant servant = CthulhuRegistries.SERVANT.get().create(level);
            if (servant == null) continue;
            double a = random.nextDouble() * Math.PI * 2;
            servant.moveTo(getX() + Math.cos(a) * 2.2, getY() + 1.0 + random.nextDouble(), getZ() + Math.sin(a) * 2.2, getYRot(), 0);
            servant.setOwner(this, phase() == 2);
            level.addFreshEntity(servant);
            level.sendParticles(ParticleTypes.POOF, servant.getX(), servant.getY(), servant.getZ(), 8, 0.2, 0.2, 0.2, 0.02);
        }
    }

    private void broadcastNear(Component message) {
        if (level() instanceof ServerLevel sl) {
            for (ServerPlayer p : sl.players()) {
                if (p.distanceToSqr(this) < 160 * 160) p.sendSystemMessage(message);
            }
        }
    }

    // ------------------------------------------------------------------ death

    @Override
    protected void dropAllDeathLoot(ServerLevel level, DamageSource source) {
        // hold the loot back until the death animation has finished
        this.deathSource = source;
        this.deathKiller = this.lastHurtByPlayer;
    }

    @Override
    protected void tickDeath() {
        this.deathTime++;
        setDeltaMovement(getDeltaMovement().scale(0.9));
        if (level() instanceof ServerLevel level) {
            if (deathTime == 1) {
                setState(State.TRANSFORM);   // keeps the state frozen; the death animation is chosen by isDeadOrDying
                playSound(SoundEvents.WITHER_DEATH, 4.0F, 0.5F);
                // servants fall with their master
                for (EyeServant s : level.getEntitiesOfClass(EyeServant.class, getBoundingBox().inflate(96), s -> getUUID().equals(s.ownerId()))) {
                    s.kill();
                }
                ForgedWorldData data = ForgedWorldData.get(level.getServer());
                if (deathKiller != null && !data.eyeDefeated()) {
                    data.setEyeDefeated(true);
                    level.getServer().getPlayerList().broadcastSystemMessage(
                            Component.translatable("message.forgedascent.eye_defeated").withStyle(ChatFormatting.LIGHT_PURPLE), false);
                }
            }
            if (deathTime >= DEATH_TICKS && !isRemoved()) {
                level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, getX(), getY() + 1.3, getZ(), 1, 0, 0, 0, 0);
                level.sendParticles(new DustParticleOptions(new Vector3f(0.8f, 0.05f, 0.1f), 3f), getX(), getY() + 1.3, getZ(), 120, 1.5, 1.5, 1.5, 0.12);
                playSound(SoundEvents.GENERIC_EXPLODE.value(), 4.0F, 0.7F);
                if (deathSource != null) {
                    this.lastHurtByPlayer = deathKiller;
                    this.lastHurtByPlayerTime = 100;
                    super.dropAllDeathLoot(level, deathSource);
                }
                remove(RemovalReason.KILLED);
                bossEvent.removeAllPlayers();
            }
        }
    }

    // ------------------------------------------------------------------ sound

    @Override
    protected SoundEvent getAmbientSound() {
        return SoundEvents.ELDER_GUARDIAN_AMBIENT;
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.RAVAGER_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return null;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 160;
    }

    @Override
    protected float getSoundVolume() {
        return 3.0f;
    }

    @Override
    public float getVoicePitch() {
        return phase() == 1 ? 0.55f : 0.4f;
    }

    // ------------------------------------------------------------------ save

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("phase", phase());
        tag.putBoolean("flees", fleesAtDawn);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("phase")) this.entityData.set(PHASE, Mth.clamp(tag.getInt("phase"), 1, 2));
        fleesAtDawn = tag.getBoolean("flees");
        if (hasCustomName()) bossEvent.setName(getDisplayName());
        plan.clear();
        current = new Step(State.HOVER, 40);
    }

    @Override
    public boolean shouldDropExperience() {
        return true;
    }

    // ------------------------------------------------------------------ GeckoLib

    private static final String A = "animation.eye_of_cthulhu.";

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 3, this::animate));
    }

    private PlayState animate(AnimationState<EyeOfCthulhu> animState) {
        int p = phase();
        boolean moving = movedSq > 0.0036;
        if (isDeadOrDying()) return animState.setAndContinue(RawAnimation.begin().thenPlayAndHold(A + "death"));
        return animState.setAndContinue(switch (state()) {
            case TRANSFORM -> RawAnimation.begin().thenPlayAndHold(A + "transform");
            case WINDUP -> RawAnimation.begin().thenPlayAndHold(A + "windup_p" + p);
            case CHARGE -> RawAnimation.begin().thenLoop(A + "charge_p" + p);
            case RECOVER -> p == 2 ? RawAnimation.begin().thenPlayAndHold(A + "recover_p2")
                    : RawAnimation.begin().thenLoop(A + (moving ? "move_p1" : "idle_p1"));
            case SUMMON -> p == 1 ? RawAnimation.begin().thenPlayAndHold(A + "summon_p1") : RawAnimation.begin().thenPlayAndHold(A + "special_p2");
            case ROAR -> RawAnimation.begin().thenPlayAndHold(A + "special_p2");
            default -> RawAnimation.begin().thenLoop(A + (moving ? "move_p" : "idle_p") + p);
        });
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public AABB getBoundingBoxForCulling() {
        return getBoundingBox().inflate(3.0, 2.0, 3.0);
    }
}
