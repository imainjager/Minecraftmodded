package com.imainjager.forgedascent.world;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.nbt.Tag;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.ArrayList;
import java.util.List;

/** World-wide Forged Ascent state, stored with the Overworld: cleared boss gates and blood moon progress. */
public class ForgedWorldData extends SavedData {
    private static final String NAME = "forgedascent";

    public record Broken(BlockPos pos, BlockState state) {}

    private int gatesCleared;
    private boolean bloodMoon;
    private long lastRolledDay = -1;
    private int brokenTonight;
    private boolean eyeDefeated;
    private long eyeLastRollDay = -1;
    private long eyePendingAt = -1;
    private final List<Broken> broken = new ArrayList<>();

    public static ForgedWorldData get(MinecraftServer server) {
        return server.overworld().getDataStorage().computeIfAbsent(
                new Factory<>(ForgedWorldData::new, ForgedWorldData::load), NAME);
    }

    private static ForgedWorldData load(CompoundTag tag, HolderLookup.Provider registries) {
        ForgedWorldData data = new ForgedWorldData();
        data.gatesCleared = tag.getInt("gates");
        data.bloodMoon = tag.getBoolean("blood_moon");
        data.lastRolledDay = tag.getLong("last_rolled_day");
        data.brokenTonight = tag.getInt("broken_tonight");
        data.eyeDefeated = tag.getBoolean("eye_defeated");
        data.eyeLastRollDay = tag.contains("eye_last_roll") ? tag.getLong("eye_last_roll") : -1;
        data.eyePendingAt = tag.contains("eye_pending") ? tag.getLong("eye_pending") : -1;
        var blocks = registries.lookupOrThrow(Registries.BLOCK);
        for (Tag t : tag.getList("broken", Tag.TAG_COMPOUND)) {
            CompoundTag c = (CompoundTag) t;
            data.broken.add(new Broken(BlockPos.of(c.getLong("pos")), NbtUtils.readBlockState(blocks, c.getCompound("state"))));
        }
        return data;
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        tag.putInt("gates", gatesCleared);
        tag.putBoolean("blood_moon", bloodMoon);
        tag.putLong("last_rolled_day", lastRolledDay);
        tag.putInt("broken_tonight", brokenTonight);
        tag.putBoolean("eye_defeated", eyeDefeated);
        tag.putLong("eye_last_roll", eyeLastRollDay);
        tag.putLong("eye_pending", eyePendingAt);
        ListTag list = new ListTag();
        for (Broken b : broken) {
            CompoundTag c = new CompoundTag();
            c.putLong("pos", b.pos().asLong());
            c.put("state", NbtUtils.writeBlockState(b.state()));
            list.add(c);
        }
        tag.put("broken", list);
        return tag;
    }

    public boolean gateCleared(int gate) {
        return (gatesCleared & (1 << gate)) != 0;
    }

    public void clearGate(int gate) {
        gatesCleared |= 1 << gate;
        setDirty();
    }

    /** Eye of Cthulhu: once beaten it stops appearing on its own (the summoning item and spawn egg still work). */
    public boolean eyeDefeated() {
        return eyeDefeated;
    }

    public void setEyeDefeated(boolean defeated) {
        eyeDefeated = defeated;
        setDirty();
    }

    public long eyeLastRollDay() {
        return eyeLastRollDay;
    }

    public void setEyeLastRollDay(long day) {
        eyeLastRollDay = day;
        setDirty();
    }

    /** Time of day (ticks) when a rolled natural spawn should appear tonight, or -1. */
    public long eyePendingAt() {
        return eyePendingAt;
    }

    public void setEyePendingAt(long time) {
        eyePendingAt = time;
        setDirty();
    }

    public boolean bloodMoon() {
        return bloodMoon;
    }

    public void setBloodMoon(boolean active) {
        bloodMoon = active;
        if (active) brokenTonight = 0;
        setDirty();
    }

    public long lastRolledDay() {
        return lastRolledDay;
    }

    public void setLastRolledDay(long day) {
        lastRolledDay = day;
        setDirty();
    }

    public int brokenTonight() {
        return brokenTonight;
    }

    public void recordBroken(BlockPos pos, BlockState state, boolean remember) {
        brokenTonight++;
        if (remember) broken.add(new Broken(pos, state));
        setDirty();
    }

    public List<Broken> takeBroken() {
        List<Broken> copy = new ArrayList<>(broken);
        broken.clear();
        setDirty();
        return copy;
    }
}
