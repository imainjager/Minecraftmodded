package com.imainjager.forgedascent;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/** Loads the gear table from forgedascent/materials.json (also read by tools/gen_assets.py). */
public final class Materials {
    public record Ingot(String id, String name) {}

    public record ToolStats(int uses, float speed, float attack, int enchant) {}

    public record ArmorStats(int durability, int helmet, int chestplate, int leggings, int boots,
                             float toughness, float knockback, int enchant, double moveSpeed, double burningTime) {}

    public record Gear(String id, String name, int tier, String repair, ToolStats tool, ArmorStats armor) {}

    public static final List<Ingot> INGOTS = new ArrayList<>();
    public static final List<Gear> GEAR = new ArrayList<>();

    private Materials() {}

    public static void load() {
        try (InputStream in = Materials.class.getResourceAsStream("/forgedascent/materials.json")) {
            if (in == null) throw new IllegalStateException("forgedascent/materials.json is missing from the jar");
            JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();

            for (JsonElement e : root.getAsJsonArray("ingots")) {
                JsonObject o = e.getAsJsonObject();
                INGOTS.add(new Ingot(o.get("id").getAsString(), o.get("name").getAsString()));
            }

            JsonArray gear = root.getAsJsonArray("gear");
            for (JsonElement e : gear) {
                JsonObject o = e.getAsJsonObject();
                JsonObject t = o.getAsJsonObject("tool");
                JsonObject a = o.getAsJsonObject("armor");
                GEAR.add(new Gear(
                        o.get("id").getAsString(),
                        o.get("name").getAsString(),
                        o.get("tier").getAsInt(),
                        o.get("repair").getAsString(),
                        new ToolStats(t.get("uses").getAsInt(), t.get("speed").getAsFloat(),
                                t.get("attack").getAsFloat(), t.get("enchant").getAsInt()),
                        new ArmorStats(a.get("durability").getAsInt(), a.get("helmet").getAsInt(),
                                a.get("chestplate").getAsInt(), a.get("leggings").getAsInt(), a.get("boots").getAsInt(),
                                a.get("toughness").getAsFloat(), a.get("knockback").getAsFloat(), a.get("enchant").getAsInt(),
                                a.get("move_speed").getAsDouble(), a.get("burning_time").getAsDouble())));
            }
        } catch (Exception ex) {
            throw new RuntimeException("Forged Ascent could not read materials.json", ex);
        }
        ForgedAscent.LOGGER.info("Forged Ascent loaded {} ingots and {} gear materials", INGOTS.size(), GEAR.size());
    }
}
