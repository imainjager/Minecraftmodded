package com.imainjager.forgedascent;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/** Loads the material table from forgedascent/materials.json (also read by tools/gen_assets.py). */
public final class Materials {
    public record Ingot(String id, String name) {}

    /** A new ore: ore blocks per stone variant ("stone", "deepslate", "nether"), raw item and raw block. */
    public record Ore(String id, String name, List<String> variants) {}

    /** A gem whose ores drop rough_&lt;id&gt; (PLAN.md section 5). */
    public record Gem(String id, String name, int tier, String item) {}

    public record ToolStats(int uses, float speed, float attack, int enchant) {}

    /** A per-piece attribute bonus ("op" is add_value, add_multiplied_base or add_multiplied_total). */
    public record Perk(String attribute, double amount, String op) {}

    public record ArmorStats(int durability, int helmet, int chestplate, int leggings, int boots,
                             float toughness, float knockback, int enchant,
                             double moveSpeed, double burningTime, double luck, List<Perk> perks) {}

    public record Gear(String id, String name, int tier, String repair, boolean armorOnly, ToolStats tool, ArmorStats armor) {}

    public static final List<Ingot> INGOTS = new ArrayList<>();
    public static final List<Ore> ORES = new ArrayList<>();
    public static final List<Gem> GEMS = new ArrayList<>();
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

            for (JsonElement e : root.getAsJsonArray("ores")) {
                JsonObject o = e.getAsJsonObject();
                List<String> variants = new ArrayList<>();
                o.getAsJsonArray("variants").forEach(v -> variants.add(v.getAsString()));
                ORES.add(new Ore(o.get("id").getAsString(), o.get("name").getAsString(), variants));
            }

            for (JsonElement e : root.getAsJsonArray("gems")) {
                JsonObject o = e.getAsJsonObject();
                GEMS.add(new Gem(o.get("id").getAsString(), o.get("name").getAsString(), o.get("tier").getAsInt(),
                        o.get("item").getAsString()));
            }

            for (JsonElement e : root.getAsJsonArray("gear")) {
                JsonObject o = e.getAsJsonObject();
                JsonObject t = o.getAsJsonObject("tool");
                JsonObject a = o.getAsJsonObject("armor");
                List<Perk> perks = new ArrayList<>();
                if (a.has("perks")) {
                    for (JsonElement p : a.getAsJsonArray("perks")) {
                        JsonObject po = p.getAsJsonObject();
                        perks.add(new Perk(po.get("attribute").getAsString(), po.get("amount").getAsDouble(), po.get("op").getAsString()));
                    }
                }
                GEAR.add(new Gear(
                        o.get("id").getAsString(),
                        o.get("name").getAsString(),
                        o.get("tier").getAsInt(),
                        o.get("repair").getAsString(),
                        o.has("armor_only") && o.get("armor_only").getAsBoolean(),
                        new ToolStats(t.get("uses").getAsInt(), t.get("speed").getAsFloat(),
                                t.get("attack").getAsFloat(), t.get("enchant").getAsInt()),
                        new ArmorStats(a.get("durability").getAsInt(), a.get("helmet").getAsInt(),
                                a.get("chestplate").getAsInt(), a.get("leggings").getAsInt(), a.get("boots").getAsInt(),
                                a.get("toughness").getAsFloat(), a.get("knockback").getAsFloat(), a.get("enchant").getAsInt(),
                                optional(a, "move_speed"), optional(a, "burning_time"), optional(a, "luck"), perks)));
            }
        } catch (Exception ex) {
            throw new RuntimeException("Forged Ascent could not read materials.json", ex);
        }
        ForgedAscent.LOGGER.info("Forged Ascent loaded {} ingots, {} ores, {} gems and {} gear materials",
                INGOTS.size(), ORES.size(), GEMS.size(), GEAR.size());
    }

    private static double optional(JsonObject o, String key) {
        return o.has(key) ? o.get(key).getAsDouble() : 0.0;
    }
}
