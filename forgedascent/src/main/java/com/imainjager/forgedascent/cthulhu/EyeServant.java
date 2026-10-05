package com.imainjager.forgedascent.cthulhu;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
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
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.animation.AnimatableManager;
import software.bernie.geckolib.animation.AnimationController;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.animation.PlayState;
import software.bernie.geckolib.animation.RawAnimation;
import software.bernie.geckolib.util.GeckoLibUtil;

import java.util.UUID;

/** Servant of Cthulhu: a small flying eye the boss throws at you. Drops a spider eye now and then (the "lens"). */
public class EyeServant extends Monster implements GeoEntity {
    public static final EntityDataAccessor<Boolean> ANGRY = SynchedEntityData.defineId(EyeServant.class, EntityDataSerializers.BOOLEAN);
    public static final EntityDataAccessor<Boolean> CHARGING = SynchedEntityData.defineId(EyeServant.class, EntityDataSerializers.BOOLEAN);

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private UUID owner;
    private int orphanTicks;
    private int nextCharge = 50;
    private int windup;
    private int chargeLeft;
    private Vec3 dashDir = Vec3.ZERO;
    private boolean hitThisDash;
    private double angle;
    public double movedSq;

    public EyeServant(EntityType<? extends EyeServant> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        this.setNoGravity(true);
        this.xpReward = 3;
        this.angle = level.random.nextDouble() * Math.PI * 2;
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 14.0)
                .add(Attributes.ATTACK_DAMAGE, 5.0)
                .add(Attributes.FOLLOW_RANGE, 64.0)
                .add(Attributes.MOVEMENT_SPEED, 0.3)
                .add(Attributes.FLYING_SPEED, 0.5);
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(ANGRY, false);
        builder.define(CHARGING, false);
    }

    public void setOwner(EyeOfCthulhu boss, boolean angry) {
        this.owner = boss.getUUID();
        this.entityData.set(ANGRY, angry);
        if (angry) {
            getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(7.0);
        }
    }

    public UUID ownerId() {
        return owner;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return false;
    }

    @Override
    public boolean isInvulnerableTo(DamageSource source) {
        return source.is(DamageTypes.IN_WALL) || source.is(DamageTypes.FALL) || source.is(DamageTypes.DROWN) || super.isInvulnerableTo(source);
    }

    @Override
    public boolean isPushedByFluid() {
        return false;
    }

    @Override
    public void travel(Vec3 input) {
        this.move(MoverType.SELF, this.getDeltaMovement());
        this.setDeltaMovement(this.getDeltaMovement().scale(0.97));
    }

    @Override
    public void tick() {
        double ox = getX(), oy = getY(), oz = getZ();
        super.tick();
        movedSq = (getX() - ox) * (getX() - ox) + (getY() - oy) * (getY() - oy) + (getZ() - oz) * (getZ() - oz);
        this.yBodyRot = getYRot();
        this.yHeadRot = getYRot();
        if (level().isClientSide || isDeadOrDying() || isNoAi()) return;
        serverBrain();
    }

    private void serverBrain() {
        ServerLevel level = (ServerLevel) level();
        if (owner != null) {
            var boss = level.getEntity(owner);
            if (boss == null || !boss.isAlive()) {
                if (++orphanTicks > 100) {
                    discard();
                    return;
                }
            } else {
                orphanTicks = 0;
            }
        }
        Player target = level.getNearestPlayer(getX(), getY(), getZ(), 64, EntitySelector.NO_CREATIVE_OR_SPECTATOR);
        setTarget(target);
        if (target == null) {
            setDeltaMovement(getDeltaMovement().scale(0.9));
            return;
        }
        Vec3 eye = target.getEyePosition();
        boolean charging = chargeLeft > 0;
        this.entityData.set(CHARGING, charging || windup > 0);
        if (charging) {
            chargeLeft--;
            setDeltaMovement(dashDir.scale(entityData.get(ANGRY) ? 0.95 : 0.8));
            if (!hitThisDash) {
                AABB box = getBoundingBox().inflate(0.25);
                for (Player p : level.getEntitiesOfClass(Player.class, box, EntitySelector.NO_CREATIVE_OR_SPECTATOR)) {
                    if (p.hurt(damageSources().mobAttack(this), (float) getAttributeValue(Attributes.ATTACK_DAMAGE))) {
                        p.knockback(0.8, -dashDir.x, -dashDir.z);
                        hitThisDash = true;
                    }
                }
            }
            lookAlong(dashDir, 60f);
            return;
        }
        if (windup > 0) {
            windup--;
            setDeltaMovement(getDeltaMovement().scale(0.7));
            lookAt(eye, 40f);
            if (windup == 0) {
                dashDir = target.getBoundingBox().getCenter().subtract(position().add(0, getBbHeight() / 2, 0)).normalize();
                chargeLeft = 14;
                hitThisDash = false;
                playSound(SoundEvents.PHANTOM_SWOOP, 1.0F, 1.6F);
            }
            return;
        }
        angle += 0.07;
        Vec3 goal = target.position().add(Math.cos(angle) * 4.0, 2.4 + Math.sin(angle * 1.7) * 0.8, Math.sin(angle) * 4.0);
        Vec3 to = goal.subtract(position());
        Vec3 desired = to.normalize().scale(Math.min(0.5, to.length() * 0.15));
        setDeltaMovement(getDeltaMovement().lerp(desired, 0.12));
        lookAt(eye, 25f);
        if (--nextCharge <= 0) {
            nextCharge = 45 + random.nextInt(50);
            windup = 9;
        }
    }

    private void lookAt(Vec3 point, float turn) {
        Vec3 to = point.subtract(position().add(0, getBbHeight() / 2, 0));
        lookAlong(to, turn);
    }

    private void lookAlong(Vec3 to, float turn) {
        float yaw = (float) (Mth.atan2(-to.x, to.z) * Mth.RAD_TO_DEG);
        float pitch = (float) (-Mth.atan2(to.y, Math.sqrt(to.x * to.x + to.z * to.z)) * Mth.RAD_TO_DEG);
        setYRot(Mth.approachDegrees(getYRot(), yaw, turn));
        setXRot(Mth.approachDegrees(getXRot(), pitch, turn));
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.PHANTOM_HURT;
    }

    @Override
    protected SoundEvent getDeathSound() {
        return SoundEvents.PHANTOM_DEATH;
    }

    @Override
    public float getVoicePitch() {
        return 1.6f;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        if (owner != null) tag.putUUID("owner", owner);
        tag.putBoolean("angry", entityData.get(ANGRY));
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.hasUUID("owner")) owner = tag.getUUID("owner");
        entityData.set(ANGRY, tag.getBoolean("angry"));
    }

    // ------------------------------------------------------------------ GeckoLib

    private static final String A = "animation.servant_of_cthulhu.";

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        controllers.add(new AnimationController<>(this, "main", 2, this::animate));
    }

    private PlayState animate(AnimationState<EyeServant> state) {
        if (isDeadOrDying()) return state.setAndContinue(RawAnimation.begin().thenPlayAndHold(A + "death"));
        return state.setAndContinue(RawAnimation.begin().thenLoop(A + (entityData.get(CHARGING) ? "charge" : "idle")));
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }
}
