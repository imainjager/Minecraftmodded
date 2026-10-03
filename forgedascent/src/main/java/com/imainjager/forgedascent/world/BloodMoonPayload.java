package com.imainjager.forgedascent.world;

import com.imainjager.forgedascent.ForgedAscent;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Tells clients whether a blood moon is active (for the red fog). */
public record BloodMoonPayload(boolean active) implements CustomPacketPayload {
    public static final Type<BloodMoonPayload> TYPE = new Type<>(ForgedAscent.id("blood_moon"));
    public static final StreamCodec<ByteBuf, BloodMoonPayload> STREAM_CODEC =
            ByteBufCodecs.BOOL.map(BloodMoonPayload::new, BloodMoonPayload::active);

    /** Client-side copy of the state. */
    public static volatile boolean clientActive;

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
