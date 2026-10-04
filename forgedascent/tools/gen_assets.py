"""Generates Forged Ascent textures, models, recipes, tags, loot tables, worldgen and English names,
plus the pack-side files under ../profile (All the Ores depth overrides, KubeJS gating script).

Reads src/main/resources/forgedascent/materials.json (the same table the Java code reads).
Textures are recolored from the vanilla jar and the mods installed in the CurseForge "Claude"
profile, so they are generated locally and NOT committed (see .gitignore). Run from forgedascent/:

    python tools/gen_assets.py
"""
import colorsys
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
TABLE = json.loads((ROOT / "src/main/resources/forgedascent/materials.json").read_text(encoding="utf-8"))
OUT = ROOT / "src/generated/resources"
PROFILE_OUT = REPO / "profile"
NS = "forgedascent"

PACK_MODS = Path.home() / "curseforge/minecraft/Instances/Claude/mods"
VANILLA_JAR = Path.home() / "curseforge/minecraft/Install/versions/1.21.1/1.21.1.jar"

# ---------------------------------------------------------------- source textures


class Sources:
    """Index of every texture in the vanilla jar and the pack's mod jars (Silent mods excluded)."""

    def __init__(self):
        self.index = {}
        jars = [VANILLA_JAR] + sorted(j for j in PACK_MODS.glob("*.jar")
                                      if "silent" not in j.name.lower() and not j.name.startswith("forgedascent"))
        for jar in jars:
            with zipfile.ZipFile(jar) as z:
                for n in z.namelist():
                    if n.startswith("assets/") and "/textures/" in n and n.endswith(".png"):
                        self.index.setdefault(n, jar)
        self.cache = {}

    def get(self, ref):
        """ref like 'alltheores:item/tin_ingot' -> RGBA image, or None."""
        ns, path = ref.split(":", 1)
        key = f"assets/{ns}/textures/{path}.png"
        if key not in self.index:
            return None
        if key not in self.cache:
            with zipfile.ZipFile(self.index[key]) as z:
                self.cache[key] = Image.open(io.BytesIO(z.read(key))).convert("RGBA")
        return self.cache[key].copy()


SRC = None
MISSING = []

# ---------------------------------------------------------------- colors


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(rgb, f):
    if f >= 0:
        return tuple(round(c + (255 - c) * f) for c in rgb)
    return tuple(round(c * (1 + f)) for c in rgb)


def gradient(hex_color):
    base = hex_rgb(hex_color)
    if lum(base) > 0.75:
        # Near-white metals: pull the midtone down so the sprite keeps its shading.
        base = shade(base, -0.18)
    return [(0.0, shade(base, -0.70)), (0.30, shade(base, -0.35)), (0.60, base),
            (0.85, shade(base, 0.30)), (1.0, shade(base, 0.60))]


def lookup(stops, t):
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
    return stops[-1][1]


def lum(rgb):
    r, g, b = rgb[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def recolor(img, hex_color, mask=None):
    """Gradient-maps every opaque pixel (or only those where mask(x, y, rgba) is True) to the color."""
    px = img.load()
    w, h = img.size
    pts = [(x, y) for y in range(h) for x in range(w)
           if px[x, y][3] > 0 and (mask is None or mask(x, y, px[x, y]))]
    if not pts:
        return img
    ls = sorted(lum(px[x, y]) for x, y in pts)
    lo, hi = ls[int(len(ls) * 0.05)], ls[min(len(ls) - 1, int(len(ls) * 0.95))]
    span = max(hi - lo, 0.15)
    stops = gradient(hex_color)
    for x, y in pts:
        a = px[x, y][3]
        px[x, y] = (*lookup(stops, (lum(px[x, y]) - lo) / span), a)
    return img


def is_handle(x, y, rgba, size):
    """Wooden handle pixels: brownish, in the lower-left part of a diagonal tool sprite."""
    s = size / 16
    if x > 8 * s or y < 7 * s:
        return False
    r, g, b = (c / 255 for c in rgba[:3])
    hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
    return 0.03 <= hh <= 0.14 and ss >= 0.25 and 0.10 <= vv <= 0.85 and r > b


def recolor_tool(img, hex_color):
    w = img.size[0]
    return recolor(img, hex_color, mask=lambda x, y, p: not is_handle(x, y, p, w))


def recolor_spots(ore, base, hex_color):
    """Recolors the pixels where an ore texture differs from its plain stone background."""
    if base.size != ore.size:
        base = base.resize(ore.size, Image.NEAREST)
    bp = base.load()

    def diff(x, y, p):
        q = bp[x, y]
        return sum(abs(p[i] - q[i]) for i in range(3)) > 40

    return recolor(ore, hex_color, mask=diff)

# ---------------------------------------------------------------- fallback sprites (our own drawings)

SHAPES = {
    "sword": """
................
.............XX.
............XXX.
...........XXX..
..........XXX...
.........XXX....
........XXX.....
.......XXX......
..D...XXX.......
...D.XXX........
....DXX.........
....HDD.........
...H...D........
..H.............
.H..............
................""",
}
WOOD = {"hi": (150, 104, 56), "base": (122, 82, 44), "lo": (92, 60, 30), "line": (46, 30, 14)}


def palette(hex_color):
    base = hex_rgb(hex_color)
    return {"hi": shade(base, 0.30), "base": base, "lo": shade(base, -0.25), "line": shade(base, -0.60)}


def draw_sprite(shape, hex_color):
    pal = palette(hex_color)
    rows = shape.strip("\n").split("\n")
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()

    def filled(x, y):
        return 0 <= x < 16 and 0 <= y < 16 and rows[y][x] != "."

    for y in range(16):
        for x in range(16):
            c = rows[y][x]
            if c == ".":
                near = [rows[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= x + dx < 16 and 0 <= y + dy < 16 and rows[y + dy][x + dx] != "."]
                if near:
                    px[x, y] = (*(WOOD["line"] if all(n == "H" for n in near) else pal["line"]), 255)
                continue
            p = WOOD if c == "H" else pal
            if c == "D":
                color = p["lo"]
            elif not filled(x, y - 1) or not filled(x - 1, y):
                color = p["hi"]
            elif not filled(x, y + 1) or not filled(x + 1, y):
                color = p["lo"]
            else:
                color = p["base"]
            px[x, y] = (*color, 255)
    return img


ARMOR_ALIASES = {"_chestplate": "_chest", "_leggings": "_pants", "_boots": "_shoes"}


def source_or_fallback(ref, hex_color, fallback_ref, tool=False):
    img = SRC.get(ref)
    for kind, alias in ARMOR_ALIASES.items():
        if img is None and ref.endswith(kind):
            img = SRC.get(ref[: -len(kind)] + alias)
    if img is None:
        MISSING.append(ref)
        img = SRC.get(fallback_ref)
    return recolor_tool(img, hex_color) if tool else recolor(img, hex_color)

# ---------------------------------------------------------------- data helpers


def write_json(rel, data, base=None):
    path = (base or OUT) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def save_png(rel, img):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def opt(tag_or_id):
    return {"id": tag_or_id, "required": False}


TAGS = {}


def tag(registry, name, *entries):
    TAGS.setdefault((registry, name), []).extend(entries)


def item_model(name, parent, texture):
    write_json(f"assets/{NS}/models/item/{name}.json",
               {"parent": parent, "textures": {"layer0": f"{NS}:item/{texture}"}})


def cube_block(name, texture=None):
    texture = texture or name
    write_json(f"assets/{NS}/models/block/{name}.json",
               {"parent": "minecraft:block/cube_all", "textures": {"all": f"{NS}:block/{texture}"}})
    write_json(f"assets/{NS}/models/item/{name}.json", {"parent": f"{NS}:block/{name}"})
    write_json(f"assets/{NS}/blockstates/{name}.json", {"variants": {"": {"model": f"{NS}:block/{name}"}}})


def self_drop(name):
    write_json(f"data/{NS}/loot_table/blocks/{name}.json", {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                   "entries": [{"type": "minecraft:item", "name": f"{NS}:{name}"}]}]})


def ore_drop(name, raw):
    silk = {"condition": "minecraft:match_tool", "predicate": {"predicates": {"minecraft:enchantments": [
        {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}
    write_json(f"data/{NS}/loot_table/blocks/{name}.json", {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:alternatives", "children": [
            {"type": "minecraft:item", "name": f"{NS}:{name}", "conditions": [silk]},
            {"type": "minecraft:item", "name": f"{NS}:{raw}", "functions": [
                {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                 "formula": "minecraft:ore_drops"},
                {"function": "minecraft:explosion_decay"}]}]}]}]})


def shaped(name, result, pattern, key, category="equipment", count=1):
    write_json(f"data/{NS}/recipe/{name}.json", {
        "type": "minecraft:crafting_shaped", "category": category,
        "key": key, "pattern": pattern, "result": {"count": count, "id": result}})


def shapeless(name, ingredients, result, count, needs_mod=None):
    data = {"type": "minecraft:crafting_shapeless", "category": "misc",
            "ingredients": ingredients, "result": {"count": count, "id": result}}
    if needs_mod:
        data["neoforge:conditions"] = [{"type": "neoforge:mod_loaded", "modid": needs_mod}]
    write_json(f"data/{NS}/recipe/{name}.json", data)


def cooking(name, kind, ingredient, result, xp, time):
    write_json(f"data/{NS}/recipe/{name}.json", {
        "type": f"minecraft:{kind}", "category": "misc", "cookingtime": time, "experience": xp,
        "ingredient": ingredient, "result": {"count": 1, "id": result}})


def ing(name):
    return {"tag": f"c:ingots/{name}"}

# ---------------------------------------------------------------- tables

TOOL_KINDS = ["sword", "pickaxe", "axe", "shovel", "hoe"]
ARMOR_KINDS = ["helmet", "chestplate", "leggings", "boots"]
TOOL_PATTERNS = {
    "sword": ["X", "X", "#"],
    "pickaxe": ["XXX", " # ", " # "],
    "axe": ["XX", "X#", " #"],
    "shovel": ["X", "#", "#"],
    "hoe": ["XX", " #", " #"],
}
ARMOR_PATTERNS = {
    "helmet": ["XXX", "X X"],
    "chestplate": ["X X", "XXX", "XXX"],
    "leggings": ["XXX", "X X", "X X"],
    "boots": ["X X", "X X"],
}
ARMOR_TAGS = {"helmet": "head_armor", "chestplate": "chest_armor", "leggings": "leg_armor", "boots": "foot_armor"}
TOOL_TAGS = {"sword": "swords", "pickaxe": "pickaxes", "axe": "axes", "shovel": "shovels", "hoe": "hoes"}

# Armor icon prefix -> worn-armor layer name, where they differ.
ARMOR_LAYERS = {
    "minecraft:golden": "minecraft:gold",
    "everythingcopper:copper": "everythingcopper:unaffected_copper",
    "iceandfire:armor_copper_metal": "iceandfire:copper",
    "iceandfire:armor_silver_metal": "iceandfire:silver",
    "immersiveengineering:armor_steel": "immersiveengineering:steel",
}

# Ore mining tiers (PLAN.md section 3). Ore tier N needs a tier-N pickaxe. New ores are added from the table.
ORE_TIERS = {
    1: ["c:ores/copper", "c:ores/tin", "c:ores/zinc"],
    2: ["c:ores/iron", "c:ores/lead", "c:ores/nickel", "c:ores/aluminum", "c:ores/quartz"],
    3: ["c:ores/gold", "c:ores/silver", "c:ores/redstone", "c:ores/lapis", "c:ores/fluorite", "c:ores/cinnabar"],
    4: ["c:ores/osmium", "c:ores/antimony", "c:ores/emerald", "c:ores/peridot"],
    5: ["c:ores/diamond", "c:ores/platinum", "c:ores/monazite"],
    6: ["c:ores/ruby", "c:ores/sapphire"],
    7: ["c:ores/tungsten", "c:ores/iridium"],
    8: ["c:ores/netherite_scrap", "minecraft:ancient_debris"],
}
MAX_TIER = 9

# "Any material of this tier" item tags (PLAN.md section 1), as ingot/gem tags. Gear materials are added from the table.
TIER_MATERIALS = {2: ["c:ingots/copper"], 3: ["c:ingots/iron"], 4: ["c:ingots/bronze", "c:ingots/silver"],
                  5: ["c:ingots/steel", "c:ingots/osmium"], 6: ["c:gems/diamond"]}

# Gear counted as "tier N or better" for Apotheosis world tier unlocks (besides our own gear).
EXTRA_GEAR = {
    4: ["mekanismtools:bronze_pickaxe", "mekanismtools:bronze_sword"],
    5: ["mekanismtools:steel_pickaxe", "mekanismtools:steel_sword", "mekanismtools:osmium_pickaxe",
        "mekanismtools:osmium_sword", "immersiveengineering:pickaxe_steel", "immersiveengineering:sword_steel"],
    6: ["minecraft:diamond_pickaxe", "minecraft:diamond_sword", "minecraft:diamond_chestplate"],
    8: ["minecraft:netherite_pickaxe", "minecraft:netherite_sword", "minecraft:netherite_chestplate"],
}
# Apotheosis world tier -> gear tier counted for forgedascent:gear/tier_N tags.
WORLD_TIER_GEAR = {"frontier": 4, "ascent": 6, "summit": 7, "pinnacle": 8}
# Apotheosis world tier -> boss gate Sigil needed to unlock it (PLAN.md "Update 4 design").
WORLD_TIER_SIGIL = {"frontier": 2, "ascent": 3, "summit": 5, "pinnacle": 6}

# Smithy anvils (must match smithy/SmithyRegistries.java): (id, tier, color, display name)
FIRST_ANVIL_TIER = 4
ANVILS = [("stone", 3, "#8A8A8A", "Stone"), ("bronze", 4, "#C08A4A", "Bronze"), ("steel", 5, "#8A949C", "Steel"), ("gemstone", 6, "#3FB8B0", "Gemstone"),
          ("titanium", 7, "#B7B4C7", "Titanium"), ("tungsten", 8, "#5C5F66", "Tungsten"),
          ("netherite", 9, "#4A3C3E", "Netherite")]
PLATE_GRADES = {2: ("Copper", "#C87C4A"), 3: ("Iron", "#D8D8D8"), 4: ("Bronze", "#C08A4A"), 5: ("Steel", "#8A949C"),
                6: ("Gem", "#3FB8B0"), 7: ("Titanium", "#B7B4C7"), 8: ("Tungsten", "#5C5F66"),
                9: ("Netherite", "#4A3C3E")}
# Plates per tier, for reinforced plates and anvils. Our gear metals are added from the table.
TIER_PLATES = {2: ["c:plates/copper"], 3: ["c:plates/iron"], 4: ["c:plates/bronze", "c:plates/silver"],
               5: ["c:plates/steel", "c:plates/osmium"], 9: ["c:plates/netherite"]}

# Other gear moved onto anvils: (item id prefix, item kinds, tier). Their crafting recipes are converted.
GEAR_KINDS = ["sword", "pickaxe", "axe", "shovel", "hoe", "helmet", "chestplate", "leggings", "boots"]
MOVED_GEAR = (
    [(f"minecraft:diamond_{k}", 6) for k in GEAR_KINDS]
    + [(f"mekanismtools:{m}_{k}", t) for m, t in (("bronze", 4), ("steel", 5), ("osmium", 5),
                                                     ("refined_glowstone", 6), ("refined_obsidian", 8))
       for k in GEAR_KINDS + ["paxel"]]
    + [(f"immersiveengineering:{k}_steel", 5) for k in ("sword", "pickaxe", "axe", "shovel", "hoe")]
    + [(f"immersiveengineering:armor_steel_{k}", 5) for k in ("helmet", "chestplate", "leggings", "boots")]
)
APOTHEOSIS_JAR_GLOB = "Apotheosis-*.jar"

# Elite mobs (must match mobs/EliteType.java and mobs/EliteMobs.java).
ELITE_TYPES = {  # id: (tint, strength, loot tier, display name)
    "runner": ("#DCEBFF", 0.50, 3, "Runner"),
    "brute": ("#6B5A48", 0.60, 3, "Brute"),
    "armored": ("#9AA0A6", 0.70, 5, "Armored"),
    "molten": ("#FF8A2A", 0.70, 5, "Molten"),
    "frost": ("#8FD6FF", 0.70, 5, "Frost"),
    "venomous": ("#6FD94A", 0.70, 5, "Venomous"),
    "dread": ("#4A2060", 0.80, 7, "Dread"),
}
ELITE_BASES = {  # id: (vanilla texture, display name, vanilla loot table)
    "zombie": ("minecraft:entity/zombie/zombie", "Zombie", "minecraft:entities/zombie"),
    "skeleton": ("minecraft:entity/skeleton/skeleton", "Skeleton", "minecraft:entities/skeleton"),
    "spider": ("minecraft:entity/spider/spider", "Spider", "minecraft:entities/spider"),
    "wither_skeleton": ("minecraft:entity/skeleton/wither_skeleton", "Wither Skeleton",
                        "minecraft:entities/wither_skeleton"),
    "piglin": ("minecraft:entity/piglin/piglin", "Piglin", "minecraft:entities/piglin"),
    "witch": ("minecraft:entity/witch", "Witch", "minecraft:entities/witch"),
}

# Temporary crafting-table alloys (PLAN.md scope changes): (name, [(metal, count)], result, count, needs mod)
ALLOYS = [
    ("pewter", [("tin", 3), ("lead", 1)], f"{NS}:pewter_ingot", 4, None),
    ("bronze", [("copper", 3), ("tin", 1)], "alltheores:bronze_ingot", 4, "alltheores"),
    ("brass", [("copper", 3), ("zinc", 1)], "alltheores:brass_ingot", 4, "alltheores"),
    ("invar", [("iron", 2), ("nickel", 1)], "alltheores:invar_ingot", 3, "alltheores"),
    ("constantan", [("copper", 1), ("nickel", 1)], "alltheores:constantan_ingot", 2, "alltheores"),
    ("electrum", [("gold", 1), ("silver", 1)], "alltheores:electrum_ingot", 2, "alltheores"),
    ("bismuth_bronze", [("copper", 2), ("tin", 1), ("bismuth", 1)], f"{NS}:bismuth_bronze_ingot", 4, None),
    ("duralumin", [("aluminum", 3), ("copper", 1), ("manganese", 1)], f"{NS}:duralumin_ingot", 5, None),
    ("rose_gold", [("gold", 3), ("copper", 1)], f"{NS}:rose_gold_ingot", 4, None),
    ("manganese_steel", [("steel", 3), ("manganese", 1)], f"{NS}:manganese_steel_ingot", 4, None),
    ("alnico", [("aluminum", 1), ("nickel", 1), ("cobalt", 1)], f"{NS}:alnico_ingot", 3, None),
    ("vanadium_steel", [("steel", 3), ("vanadium", 1)], f"{NS}:vanadium_steel_ingot", 4, None),
    ("white_gold", [("gold", 3), ("platinum", 1)], f"{NS}:white_gold_ingot", 4, None),
    ("stainless_steel", [("steel", 4), ("chromium", 1), ("nickel", 1)],
     "modern_industrialization:stainless_steel_ingot", 6, "modern_industrialization"),
    ("chromoly", [("steel", 4), ("chromium", 1), ("molybdenum", 1)], f"{NS}:chromoly_ingot", 6, None),
    ("titanium_alloy", [("titanium", 4), ("aluminum", 1), ("vanadium", 1)], f"{NS}:titanium_alloy_ingot", 6, None),
    ("high_speed_steel", [("steel", 4), ("tungsten", 1), ("molybdenum", 1), ("chromium", 1)],
     f"{NS}:high_speed_steel_ingot", 6, None),
    ("stellite", [("cobalt", 2), ("chromium", 1), ("tungsten", 1)], f"{NS}:stellite_ingot", 4, None),
    ("inconel", [("nickel", 3), ("chromium", 1), ("iron", 1)], f"{NS}:inconel_ingot", 5, None),
    ("osmiridium", [("osmium", 1), ("iridium", 1)], f"{NS}:osmiridium_ingot", 2, None),
    ("nichrome", [("nickel", 4), ("chromium", 1)], f"{NS}:nichrome_ingot", 5, None),
]

# All the Ores ore heights reshaped so early metals sit high and late metals sit deep.
ATO_DEPTHS = {
    "tin": (0, 160, 4), "zinc": (0, 128, 3), "aluminum": (-16, 128, 4),
    "lead": (-40, 80, 3), "nickel": (-40, 80, 3),
    "osmium": (-64, 24, 2), "platinum": (-64, 0, 2), "iridium": (-64, -24, 2),
}

# Recipe gating for tier-less mining (PLAN.md section 7): (output, ingredient to replace, tier).
# Most other drills/quarries already need diamonds, which now need a tier-5 pickaxe.
GATING = [
    ("create:mechanical_drill", "#c:ingots/iron", 4),
    ("immersiveengineering:drillhead_iron", "#c:ingots/iron", 4),
    ("stevescarts:module_iron_drill", "minecraft:iron_ingot", 4),
    ("buildinggadgets2:gadget_destruction", "#c:ingots/iron", 5),
    ("mekanism:atomic_disassembler", "#mekanism:alloys/infused", 7),
    ("industrialforegoing:laser_drill", "#c:gears/gold", 8),
]

ORE_TARGETS = {
    "stone": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"},
    "deepslate": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"},
    "nether": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:base_stone_nether"},
}
ORE_BASES = {"stone": "minecraft:block/stone", "deepslate": "minecraft:block/deepslate",
             "nether": "minecraft:block/netherrack"}
ORE_PREFIX = {"stone": "", "deepslate": "deepslate_", "nether": "nether_"}
STONE_TAG = {"stone": "c:ores_in_ground/stone", "deepslate": "c:ores_in_ground/deepslate",
             "nether": "c:ores_in_ground/netherrack"}

# ---------------------------------------------------------------- generation


def pattern_weld(img, color_a, color_b):
    """Two-tone wavy 'Damascus' look: each pixel takes one metal's gradient, chosen by a folded wave pattern."""
    import math
    px = img.load()
    w, h = img.size
    pts = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 0]
    if not pts:
        return img
    ls = sorted(lum(px[x, y]) for x, y in pts)
    lo, hi = ls[int(len(ls) * 0.05)], ls[min(len(ls) - 1, int(len(ls) * 0.95))]
    span = max(hi - lo, 0.15)
    stops_a, stops_b = gradient(color_a), gradient(color_b)
    s = 16 / w
    for x, y in pts:
        wave = math.sin((x * s) * 0.9 + (y * s) * 1.7 + 2.2 * math.sin((x * s) * 0.45))
        stops = stops_a if wave > 0 else stops_b
        px[x, y] = (*lookup(stops, (lum(px[x, y]) - lo) / span), px[x, y][3])
    return img


def gen_ingots():
    for ingot in TABLE["ingots"]:
        iid, color, style = ingot["id"], ingot["color"], ingot["style"]
        if "pattern" in ingot:
            a, b = ingot["pattern"]
            save_png(f"assets/{NS}/textures/item/{iid}_ingot.png",
                     pattern_weld(SRC.get(f"alltheores:item/{style}_ingot"), a, b))
            save_png(f"assets/{NS}/textures/block/{iid}_block.png",
                     pattern_weld(SRC.get(f"alltheores:block/{style}_block"), a, b))
            PATTERN_PLATES[iid] = (a, b)
        else:
            save_png(f"assets/{NS}/textures/item/{iid}_ingot.png",
                     source_or_fallback(f"alltheores:item/{style}_ingot", color, "minecraft:item/iron_ingot"))
            save_png(f"assets/{NS}/textures/block/{iid}_block.png",
                     source_or_fallback(f"alltheores:block/{style}_block", color, "minecraft:block/iron_block"))
        item_model(f"{iid}_ingot", "minecraft:item/generated", f"{iid}_ingot")
        cube_block(f"{iid}_block")
        self_drop(f"{iid}_block")
        LANG[f"item.{NS}.{iid}_ingot"] = f"{ingot['name']} Ingot"
        LANG[f"block.{NS}.{iid}_block"] = f"Block of {ingot['name']}"
        gen_plate(iid, ingot["name"], color, style)
        shaped(f"{iid}_block", f"{NS}:{iid}_block", ["XXX", "XXX", "XXX"], {"X": ing(iid)}, "building")
        shapeless(f"{iid}_ingot_from_block", [{"tag": f"c:storage_blocks/{iid}"}], f"{NS}:{iid}_ingot", 9)
        tag("item", f"c:ingots/{iid}", f"{NS}:{iid}_ingot")
        tag("item", "c:ingots", f"#c:ingots/{iid}")
        for reg in ("item", "block"):
            tag(reg, f"c:storage_blocks/{iid}", f"{NS}:{iid}_block")
            tag(reg, "c:storage_blocks", f"#c:storage_blocks/{iid}")
        tag("block", "minecraft:mineable/pickaxe", f"{NS}:{iid}_block")
        tag("block", "minecraft:needs_stone_tool", f"{NS}:{iid}_block")


PATTERN_PLATES = {}


def gen_damascus():
    """Pattern-welded metals (PLAN.md "Update 6"): folded at a Smithy Anvil, tier materials, Silent Gear materials."""
    sg_cond = [{"type": "neoforge:mod_loaded", "modid": "silentgear"}]
    for ingot in TABLE["ingots"]:
        if "pattern" not in ingot:
            continue
        iid, tier, (a, b) = ingot["id"], ingot["tier"], ingot["folded_from"]
        write_json(f"data/{NS}/recipe/folding/{iid}.json", {
            "type": f"{NS}:anvil_shaped", "tier": tier, "key": {"A": ing(a), "B": ing(b)},
            "pattern": ["ABA", "BAB", "ABA"], "result": {"count": 6, "id": f"{NS}:{iid}_ingot"}})
        TIER_MATERIALS.setdefault(tier, []).append(f"c:ingots/{iid}")
        TIER_PLATES.setdefault(tier, []).append(f"c:plates/{iid}")
        tag("item", f"{NS}:pattern_welded", f"{NS}:{iid}_ingot")
        # Silent Gear: a bit stronger than the tier's normal metals, extra sharp.
        sword, armor = SWORD_CURVE[tier] - 4, ARMOR_CURVE[tier]
        pieces = {"helmet": round(armor * 0.15), "chestplate": round(armor * 0.4), "boots": round(armor * 0.15)}
        pieces["leggings"] = armor - sum(pieces.values())
        mat = {"id": iid, "color": ingot["color"], "repair": f"c:ingots/{iid}",
               "tool": {"uses": int(250 * tier * 1.1), "speed": 5.0 + tier * 0.6, "attack": round(sword * 1.08, 2),
                        "enchant": 16},
               "armor": {"durability": int(5 * tier * 1.1), **pieces, "toughness": tier * 0.2, "enchant": 16}}
        data = sg_material(mat, tier, {"tag": f"c:ingots/{iid}"}, ["metal"] + tier_categories(tier),
                           f"material.{NS}.{iid}")
        data["properties"]["silentgear:main"]["traits"] = [{"conditions": [], "level": 2, "trait": "silentgear:sharp"}]
        data["neoforge:conditions"] = sg_cond
        write_json(f"data/{NS}/silentgear_materials/{iid}.json", data)
        LANG[f"material.{NS}.{iid}"] = ingot["name"]
        SG_EXTRA_TIERS[f"{NS}:{iid}"] = tier


SG_EXTRA_TIERS = {}


def gen_plate(iid, name, color, style):
    """A plate for one of our ingots, made the ways the pack already makes plates (PLAN.md "Update 4 design")."""
    plate = f"{iid}_plate"
    if iid in PATTERN_PLATES:
        save_png(f"assets/{NS}/textures/item/{plate}.png",
                 pattern_weld(SRC.get(f"alltheores:item/{style}_plate"), *PATTERN_PLATES[iid]))
    else:
        save_png(f"assets/{NS}/textures/item/{plate}.png",
                 source_or_fallback(f"alltheores:item/{style}_plate", color, "minecraft:item/iron_ingot"))
    item_model(plate, "minecraft:item/generated", plate)
    LANG[f"item.{NS}.{plate}"] = f"{name} Plate"
    tag("item", f"c:plates/{iid}", f"{NS}:{plate}")
    tag("item", "c:plates", f"#c:plates/{iid}")
    out = {"count": 1, "id": f"{NS}:{plate}"}
    cond = lambda mod: [{"type": "neoforge:mod_loaded", "modid": mod}]
    write_json(f"data/{NS}/recipe/plates/{iid}_hammer.json", {
        "neoforge:conditions": cond("alltheores"), "type": "minecraft:crafting_shaped", "category": "misc",
        "key": {"a": ing(iid), "h": {"tag": "alltheores:ore_hammers"}}, "pattern": ["   ", "ha ", "a  "], "result": out})
    write_json(f"data/{NS}/recipe/plates/{iid}_metal_press.json", {
        "neoforge:conditions": cond("immersiveengineering"), "type": "immersiveengineering:metal_press",
        "energy": 51200, "input": ing(iid), "mold": "immersiveengineering:mold_plate", "result": {"item": f"{NS}:{plate}"}})
    write_json(f"data/{NS}/recipe/plates/{iid}_pressing.json", {
        "neoforge:conditions": cond("create"), "type": "create:pressing",
        "ingredients": [ing(iid)], "results": [{"id": f"{NS}:{plate}"}]})
    write_json(f"data/{NS}/recipe/plates/{iid}_compressor.json", {
        "neoforge:conditions": cond("modern_industrialization"), "type": "modern_industrialization:compressor",
        "duration": 100, "eu": 2, "item_inputs": [{"amount": 1, "tag": f"c:ingots/{iid}"}],
        "item_outputs": [{"amount": 1, "item": f"{NS}:{plate}"}]})


def anvil_shaped(name, result, pattern, key, tier, needs_mod=None):
    data = {"type": f"{NS}:anvil_shaped", "tier": tier, "key": key, "pattern": pattern,
            "result": {"count": 1, "id": result}}
    if needs_mod:
        data["neoforge:conditions"] = [{"type": "neoforge:mod_loaded", "modid": needs_mod}]
    write_json(f"data/{NS}/recipe/{name}.json", data)


def gen_ores():
    for ore in TABLE["ores"]:
        oid, color, style = ore["id"], ore["color"], ore["style"]
        ORE_TIERS.setdefault(ore["tier"], []).append(f"c:ores/{oid}")
        for variant in ore["variants"]:
            name = f"{ORE_PREFIX[variant]}{oid}_ore"
            src = SRC.get(f"alltheores:block/{ORE_PREFIX[variant]}{style}_ore")
            base = SRC.get(ORE_BASES[variant])
            if src is None:
                MISSING.append(f"alltheores:block/{ORE_PREFIX[variant]}{style}_ore")
                src = SRC.get("minecraft:block/" + {"stone": "iron_ore", "deepslate": "deepslate_iron_ore",
                                                     "nether": "nether_gold_ore"}[variant])
            save_png(f"assets/{NS}/textures/block/{name}.png", recolor_spots(src, base, color))
            cube_block(name)
            ore_drop(name, f"raw_{oid}")
            LANG[f"block.{NS}.{name}"] = f"{'Deepslate ' if variant == 'deepslate' else 'Nether ' if variant == 'nether' else ''}{ore['name']} Ore"
            for reg in ("item", "block"):
                tag(reg, f"c:ores/{oid}", f"{NS}:{name}")
                tag(reg, STONE_TAG[variant], f"{NS}:{name}")
            tag("block", "minecraft:mineable/pickaxe", f"{NS}:{name}")
            cooking(f"smelting/{oid}_ingot_from_{name}", "smelting", {"item": f"{NS}:{name}"},
                    f"{NS}:{oid}_ingot", 0.7, 200)
            cooking(f"blasting/{oid}_ingot_from_{name}", "blasting", {"item": f"{NS}:{name}"},
                    f"{NS}:{oid}_ingot", 0.7, 100)
        for reg in ("item", "block"):
            tag(reg, "c:ores", f"#c:ores/{oid}")

        raw, raw_block = f"raw_{oid}", f"raw_{oid}_block"
        save_png(f"assets/{NS}/textures/item/{raw}.png",
                 source_or_fallback(f"alltheores:item/raw_{style}", color, "minecraft:item/raw_iron"))
        save_png(f"assets/{NS}/textures/block/{raw_block}.png",
                 source_or_fallback(f"alltheores:block/raw_{style}_block", color, "minecraft:block/raw_iron_block"))
        item_model(raw, "minecraft:item/generated", raw)
        cube_block(raw_block)
        self_drop(raw_block)
        LANG[f"item.{NS}.{raw}"] = f"Raw {ore['name']}"
        LANG[f"block.{NS}.{raw_block}"] = f"Block of Raw {ore['name']}"
        tag("item", f"c:raw_materials/{oid}", f"{NS}:{raw}")
        tag("item", "c:raw_materials", f"#c:raw_materials/{oid}")
        for reg in ("item", "block"):
            tag(reg, f"c:storage_blocks/raw_{oid}", f"{NS}:{raw_block}")
            tag(reg, "c:storage_blocks", f"#c:storage_blocks/raw_{oid}")
        tag("block", "minecraft:mineable/pickaxe", f"{NS}:{raw_block}")
        shaped(raw_block, f"{NS}:{raw_block}", ["XXX", "XXX", "XXX"], {"X": {"item": f"{NS}:{raw}"}}, "building")
        shapeless(f"{raw}_from_block", [{"item": f"{NS}:{raw_block}"}], f"{NS}:{raw}", 9)
        cooking(f"smelting/{oid}_ingot", "smelting", {"tag": f"c:raw_materials/{oid}"}, f"{NS}:{oid}_ingot", 0.7, 200)
        cooking(f"blasting/{oid}_ingot", "blasting", {"tag": f"c:raw_materials/{oid}"}, f"{NS}:{oid}_ingot", 0.7, 100)

        for wg in ore["worldgen"]:
            fid = f"ore_{wg['name']}"
            targets = [{"state": {"Name": f"{NS}:{ORE_PREFIX[v]}{oid}_ore"}, "target": ORE_TARGETS[v]}
                       for v in wg["variants"]]
            write_json(f"data/{NS}/worldgen/configured_feature/{fid}.json", {
                "type": "minecraft:ore",
                "config": {"discard_chance_on_air_exposure": 0.0, "size": wg["size"], "targets": targets}})
            write_json(f"data/{NS}/worldgen/placed_feature/{fid}.json", {
                "feature": f"{NS}:{fid}",
                "placement": [
                    {"type": "minecraft:count", "count": wg["count"]},
                    {"type": "minecraft:in_square"},
                    {"type": "minecraft:height_range", "height": {
                        "type": f"minecraft:{wg['shape']}",
                        "min_inclusive": {"absolute": wg["min"]}, "max_inclusive": {"absolute": wg["max"]}}},
                    {"type": "minecraft:biome"}]})
            write_json(f"data/{NS}/neoforge/biome_modifier/{fid}.json", {
                "type": "neoforge:add_features", "biomes": wg["biomes"],
                "features": f"{NS}:{fid}", "step": "underground_ores"})


def gear_recipe(item, pattern, key, tier):
    """Tier 1-3 gear is made in a crafting table; tier 4+ needs a Smithy Anvil of that tier."""
    if tier >= FIRST_ANVIL_TIER:
        anvil_shaped(item, f"{NS}:{item}", pattern, key, tier)
    else:
        shaped(item, f"{NS}:{item}", pattern, key)


def gen_gear():
    for m in TABLE["gear"]:
        mid, name, color, tier = m["id"], m["name"], m["color"], m["tier"]
        armor_only = m.get("armor_only", False)
        if armor_only:
            tag("item", m["repair"], *[e if not e.startswith("#") else e for e in TABLE["scavenged"][mid]])
        else:
            TIER_MATERIALS.setdefault(tier, []).append(m["repair"])
        for kind in ("sword", "pickaxe", "helmet", "chestplate", "leggings", "boots"):
            if not (armor_only and kind in ("sword", "pickaxe")):
                tag("item", f"{NS}:tier_gear/{tier}/{kind}", f"{NS}:{mid}_{kind}")
        for unlock in WORLD_TIER_GEAR.values():
            if armor_only:
                break
            if tier >= unlock:
                for kind in ("pickaxe", "sword", "chestplate"):
                    tag("item", f"{NS}:gear/tier_{unlock}", f"{NS}:{mid}_{kind}")
        key_tool = {"X": {"tag": m["repair"]}, "#": {"tag": "c:rods/wooden"}}
        tns, tprefix = m["tools_from"].split(":")
        for kind in ([] if armor_only else TOOL_KINDS):
            item = f"{mid}_{kind}"
            if kind == "sword":
                img = draw_sprite(SHAPES["sword"], color)
            else:
                img = source_or_fallback(f"{tns}:item/{tprefix}_{kind}", color, f"minecraft:item/iron_{kind}", tool=True)
            save_png(f"assets/{NS}/textures/item/{item}.png", img)
            item_model(item, "minecraft:item/handheld", item)
            gear_recipe(item, TOOL_PATTERNS[kind], key_tool, tier)
            tag("item", f"minecraft:{TOOL_TAGS[kind]}", f"{NS}:{item}")
            LANG[f"item.{NS}.{item}"] = f"{name} {kind.capitalize()}"
        ans, aprefix = m["armor_from"].split(":")
        for kind in ARMOR_KINDS:
            item = f"{mid}_{kind}"
            save_png(f"assets/{NS}/textures/item/{item}.png",
                     source_or_fallback(f"{ans}:item/{aprefix}_{kind}", color, f"minecraft:item/iron_{kind}"))
            item_model(item, "minecraft:item/generated", item)
            gear_recipe(item, ARMOR_PATTERNS[kind], {"X": {"tag": m["repair"]}}, tier)
            tag("item", f"minecraft:{ARMOR_TAGS[kind]}", f"{NS}:{item}")
            tag("item", "minecraft:trimmable_armor", f"{NS}:{item}")
            LANG[f"item.{NS}.{item}"] = f"{name} {kind.capitalize()}"
        lns, lname = ARMOR_LAYERS.get(m["armor_from"], m["armor_from"]).split(":")
        lname = lname.split("/")[-1]  # icons may live in a subfolder (gear/, armor/); layers don't
        for layer in (1, 2):
            save_png(f"assets/{NS}/textures/models/armor/{mid}_layer_{layer}.png",
                     source_or_fallback(f"{lns}:models/armor/{lname}_layer_{layer}", color,
                                        f"minecraft:models/armor/iron_layer_{layer}"))


def gen_tiers():
    for tier, ores in ORE_TIERS.items():
        tag("block", f"{NS}:needs_tier_{tier}", *[opt(("#" + o) if o.startswith("c:") else o) for o in ores])
    for t in range(0, MAX_TIER + 1):
        entries = []
        if t + 1 <= max(ORE_TIERS):
            entries.append(f"#{NS}:needs_tier_{t + 1}")
        if t < MAX_TIER:
            entries.append(f"#{NS}:incorrect_for_tier_{t + 1}")
        if t == 0:
            entries.append("#minecraft:needs_stone_tool")
        if t <= 2:
            entries.append("#minecraft:needs_iron_tool")
        if t <= 5:
            entries.append("#minecraft:needs_diamond_tool")
        tag("block", f"{NS}:incorrect_for_tier_{t}", *entries)
    for vanilla, t in (("wooden", 0), ("gold", 0), ("stone", 1), ("iron", 3), ("diamond", 6)):
        tag("block", f"minecraft:incorrect_for_{vanilla}_tool", f"#{NS}:incorrect_for_tier_{t}")
    for tier, mats in TIER_MATERIALS.items():
        tag("item", f"{NS}:tier_materials/{tier}", *[opt(f"#{x}") for x in dict.fromkeys(mats)])
    for unlock in sorted(set(WORLD_TIER_GEAR.values())):
        extra = [i for t, items in EXTRA_GEAR.items() if t >= unlock for i in items]
        tag("item", f"{NS}:gear/tier_{unlock}", *[opt(i) for i in extra])


def gen_gems():
    for gem in TABLE["gems"]:
        gid, color = gem["id"], gem["color"]
        ORE_TIERS.setdefault(gem["tier"], []).append(f"c:ores/{gid}")
        rough = f"rough_{gid}"
        save_png(f"assets/{NS}/textures/item/{rough}.png",
                 source_or_fallback("alltheores:item/raw_silver", color, "minecraft:item/raw_iron"))
        item_model(rough, "minecraft:item/generated", rough)
        LANG[f"item.{NS}.{rough}"] = f"Rough {gem['name']}"
        tag("item", f"{NS}:rough_gems", f"{NS}:{rough}")
        wheels = f"{NS}:cutting_wheels/{8 if gem['hardness'] <= 8 else 10}"
        shapeless(f"cutting/{gid}", [{"item": f"{NS}:{rough}"}, {"tag": wheels}], gem["item"], 1,
                  gem["item"].split(":")[0] if not gem["item"].startswith("minecraft:") else None)
    tag("item", f"{NS}:cutting_wheels/8", f"{NS}:emery_wheel", f"{NS}:diamond_grit_wheel")
    tag("item", f"{NS}:cutting_wheels/10", f"{NS}:diamond_grit_wheel")
    save_png(f"assets/{NS}/textures/item/diamond_grit.png",
             source_or_fallback("minecraft:item/sugar", "#7FE8E4", "minecraft:item/gunpowder"))
    save_png(f"assets/{NS}/textures/item/emery_wheel.png",
             source_or_fallback("create:item/sand_paper", "#8A5A4A", "minecraft:item/flint"))
    save_png(f"assets/{NS}/textures/item/diamond_grit_wheel.png",
             source_or_fallback("create:item/sand_paper", "#6FD8D4", "minecraft:item/flint"))
    for item, name in (("diamond_grit", "Diamond Grit"), ("emery_wheel", "Emery Cutting Wheel"),
                       ("diamond_grit_wheel", "Diamond-Grit Cutting Wheel")):
        item_model(item, "minecraft:item/generated", item)
        LANG[f"item.{NS}.{item}"] = name
    shapeless("diamond_grit", [{"item": f"{NS}:rough_diamond"}], f"{NS}:diamond_grit", 2)
    shaped("emery_wheel", f"{NS}:emery_wheel", ["FFF", "FIF", "FFF"],
           {"F": {"item": "minecraft:flint"}, "I": {"tag": f"{NS}:tier_materials/4"}}, "misc")
    shaped("diamond_grit_wheel", f"{NS}:diamond_grit_wheel", ["GGG", "GIG", "GGG"],
           {"G": {"item": f"{NS}:diamond_grit"}, "I": {"tag": f"{NS}:tier_materials/6"}}, "misc")


def gen_elites():
    for base, (texture, base_name, loot) in ELITE_BASES.items():
        src = SRC.get(texture)
        for elite, (tint, strength, loot_tier, name) in ELITE_TYPES.items():
            eid = f"{elite}_{base}"
            img = src.copy()
            px = img.load()
            t = hex_rgb(tint)
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    r, g, b, a = px[x, y]
                    if a == 0:
                        continue
                    l = lum((r, g, b))
                    tinted = tuple(min(255, round(l * c * 1.35)) for c in t)
                    px[x, y] = (*(round(o + (n - o) * strength) for o, n in zip((r, g, b), tinted)), a)
            save_png(f"assets/{NS}/textures/entity/elite/{eid}.png", img)
            LANG[f"entity.{NS}.{eid}"] = f"{name} {base_name}"
            LANG[f"item.{NS}.{eid}_spawn_egg"] = f"{name} {base_name} Spawn Egg"
            write_json(f"assets/{NS}/models/item/{eid}_spawn_egg.json", {"parent": "minecraft:item/template_spawn_egg"})
            write_json(f"data/{NS}/loot_table/entities/{eid}.json", {
                "type": "minecraft:entity",
                "pools": [
                    {"rolls": 1, "entries": [{"type": "minecraft:loot_table", "value": loot}]},
                    {"rolls": 1, "conditions": [{"condition": "minecraft:random_chance", "chance": 0.35}],
                     "entries": [{"type": "minecraft:tag", "name": f"{NS}:tier_materials/{loot_tier}",
                                  "expand": True}]}]})


def gen_smithy():
    """Plates per tier, reinforced plates, Smithy Anvils, Sigils, Treasure Bags, moved recipes (PLAN.md "Update 4 design")."""
    for m in TABLE["gear"]:
        if m["repair"].startswith("c:ingots/"):
            TIER_PLATES.setdefault(m["tier"], []).append("c:plates/" + m["repair"].split("/", 1)[1])
    for tier, plates in TIER_PLATES.items():
        tag("item", f"{NS}:tier_plates/{tier}", *[opt("#" + p) for p in dict.fromkeys(plates)])

    # Reinforced plates: 4 plates of a tier -> 1 reinforced plate of that tier.
    for tier, (grade, color) in PLATE_GRADES.items():
        item = f"reinforced_plate_{tier}"
        save_png(f"assets/{NS}/textures/item/{item}.png",
                 source_or_fallback("immersiveengineering:item/plate_steel", color, "alltheores:item/steel_plate"))
        item_model(item, "minecraft:item/generated", item)
        LANG[f"item.{NS}.{item}"] = f"{grade}-Grade Reinforced Plate"
        shaped(item, f"{NS}:{item}", ["PP", "PP"], {"P": {"tag": f"{NS}:tier_plates/{tier}"}}, "misc")
    write_json(f"data/{NS}/recipe/anvil_reinforce.json", {"type": f"{NS}:anvil_reinforce"})
    write_json(f"data/{NS}/recipe/anvil_repair.json", {"type": f"{NS}:anvil_repair"})
    LANG["message.forgedascent.flawless"] = "A flawless cut! You found a %s."
    for gem in TABLE["gems"]:
        item = f"flawless_{gem['id']}"
        img = source_or_fallback(f"{gem['item'].split(':')[0]}:item/{gem['item'].split(':')[1]}", gem["color"],
                                 "minecraft:item/diamond")
        save_png(f"assets/{NS}/textures/item/{item}.png", img)
        write_json(f"assets/{NS}/models/item/{item}.json", {"parent": "minecraft:item/generated",
                                                             "textures": {"layer0": f"{NS}:item/{item}"}})
        LANG[f"item.{NS}.{item}"] = f"Flawless {gem['name']}"
        tag("item", f"{NS}:flawless_gems", f"{NS}:{item}")
    # Quest helper tags: any tier-N gear of a kind (vanilla/other mods added below).
    kinds = ("sword", "pickaxe", "helmet", "chestplate", "leggings", "boots")
    for prefix, t in (("minecraft:stone_", 1), ("minecraft:iron_", 3), ("minecraft:diamond_", 6),
                      ("minecraft:netherite_", 9), ("everythingcopper:copper_", 2)):
        for kind in kinds:
            if prefix == "minecraft:stone_" and kind not in ("sword", "pickaxe"):
                continue
            tag("item", f"{NS}:tier_gear/{t}/{kind}", opt(prefix + kind))
    for prefix, t in (("mekanismtools:bronze_", 4), ("mekanismtools:steel_", 5), ("mekanismtools:osmium_", 5)):
        for kind in kinds:
            tag("item", f"{NS}:tier_gear/{t}/{kind}", opt(prefix + kind))

    # Sigils and Treasure Bags per gate.
    for gate in TABLE["gates"]:
        n, color, gname = gate["gate"], gate["color"], gate["name"]
        LANG[f"gate.{NS}.{n}"] = gname
        if n <= 6:
            sigil = f"sigil_{n}"
            save_png(f"assets/{NS}/textures/item/{sigil}.png",
                     source_or_fallback("minecraft:item/nether_star", color, "minecraft:item/emerald"))
            item_model(sigil, "minecraft:item/generated", sigil)
            LANG[f"item.{NS}.{sigil}"] = f"{gname} Sigil"
        bag = f"treasure_bag_{n}"
        save_png(f"assets/{NS}/textures/item/{bag}.png",
                 source_or_fallback("minecraft:item/bundle", color, "minecraft:item/leather"))
        item_model(bag, "minecraft:item/generated", bag)
        LANG[f"item.{NS}.{bag}"] = f"{gname} Treasure Bag"
        tier = min(8, n + 3)
        pools = []
        if n <= 6:
            pools.append({"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"{NS}:sigil_{n}"}]})
        pools += [
            {"rolls": 3, "entries": [{"type": "minecraft:tag", "name": f"{NS}:tier_materials/{tier}", "expand": True,
                                      "functions": [{"function": "minecraft:set_count",
                                                     "count": {"type": "minecraft:uniform", "min": 2, "max": 4}}]}]},
            {"rolls": {"type": "minecraft:uniform", "min": 1, "max": 2},
             "entries": [{"type": "minecraft:tag", "name": f"{NS}:rough_gems", "expand": True}]},
            {"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"{NS}:reinforced_plate_{min(9, n + 3)}"}]},
            {"rolls": 1, "entries": [{"type": "minecraft:loot_table", "value": f"{NS}:bags/accessories_{n}"}]},
        ]
        write_json(f"data/{NS}/loot_table/bags/gate_{n}.json", {"type": "minecraft:gift", "pools": pools})
        # Accessories live in their own table that only loads when their mods are installed.
        mods = sorted({a.split(":")[0] for a in gate["accessories"]})
        write_json(f"data/{NS}/loot_table/bags/accessories_{n}.json", {
            "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": m} for m in mods],
            "type": "minecraft:gift",
            "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": a} for a in gate["accessories"]]}]})

    # Smithy Anvils: crafted (in a crafting table) from the previous anvil, a Sigil and plates of the new tier.
    vanilla_anvil, vanilla_top = SRC.get("minecraft:block/anvil"), SRC.get("minecraft:block/anvil_top")
    for i, (aid, tier, color, name) in enumerate(ANVILS):
        block = f"{aid}_anvil"
        save_png(f"assets/{NS}/textures/block/{block}.png", recolor(vanilla_anvil.copy(), color))
        save_png(f"assets/{NS}/textures/block/{block}_top.png", recolor(vanilla_top.copy(), color))
        write_json(f"assets/{NS}/models/block/{block}.json", {
            "parent": "minecraft:block/template_anvil",
            "textures": {"top": f"{NS}:block/{block}_top", "body": f"{NS}:block/{block}",
                         "particle": f"{NS}:block/{block}"}})
        write_json(f"assets/{NS}/models/item/{block}.json", {"parent": f"{NS}:block/{block}"})
        write_json(f"assets/{NS}/blockstates/{block}.json", {"variants": {
            f"facing={d}": {"model": f"{NS}:block/{block}", "y": y}
            for d, y in (("north", 90), ("east", 180), ("south", 270), ("west", 0))}})
        self_drop(block)
        tag("block", "minecraft:mineable/pickaxe", f"{NS}:{block}")
        LANG[f"block.{NS}.{block}"] = f"{name} Anvil"
        plates = {"tag": f"{NS}:tier_plates/{min(tier, 8)}"}
        sigil = {"item": f"{NS}:sigil_{i}"}
        if i == 0:
            shaped(block, f"{NS}:{block}", ["III", " S ", "SSS"],
                   {"I": {"tag": "c:ingots/iron"}, "S": {"item": "minecraft:smooth_stone"}}, "misc")
        elif i == 1:
            shaped(block, f"{NS}:{block}", ["PPP", "PAP", "PSP"],
                   {"P": plates, "S": sigil, "A": {"item": f"{NS}:stone_anvil"}}, "misc")
        else:
            prev = {"item": f"{NS}:{ANVILS[i - 1][0]}_anvil"}
            top = {"tag": "c:ingots/netherite"} if aid == "netherite" else plates
            shaped(block, f"{NS}:{block}", ["TTT", "PAP", "PSP"], {"T": top, "P": plates, "A": prev, "S": sigil}, "misc")

    # Vanilla diamond/netherite and major mods' tier 4+ gear move onto anvils.
    targets = dict(MOVED_GEAR)
    found = set()
    jars = [VANILLA_JAR] + sorted(PACK_MODS.glob("*.jar"))
    for jar in jars:
        with zipfile.ZipFile(jar) as z:
            for n in z.namelist():
                if not (n.startswith("data/") and "/recipe" in n and n.endswith(".json")):
                    continue
                try:
                    data = json.loads(z.read(n))
                except Exception:
                    continue
                result = data.get("result")
                rid = result.get("id") if isinstance(result, dict) else None
                if rid not in targets or rid in found or "pattern" not in data or "key" not in data:
                    continue
                found.add(rid)
                ns, path = rid.split(":")
                anvil_shaped(f"moved/{ns}/{path}", rid, data["pattern"], data["key"], targets[rid],
                             None if ns == "minecraft" else ns)
    for k in GEAR_KINDS:
        write_json(f"data/{NS}/recipe/moved/minecraft/netherite_{k}.json", {
            "type": f"{NS}:anvil_shapeless", "tier": 9, "copy_components": True,
            "ingredients": [{"item": f"minecraft:diamond_{k}"}, {"tag": "c:ingots/netherite"},
                            {"tag": f"{NS}:tier_materials/8"}],
            "result": {"count": 1, "id": f"minecraft:netherite_{k}"}})
        found.add(f"minecraft:netherite_{k}")
    MOVED.extend(sorted(found))
    tag("block", f"{NS}:siege_proof", opt("#c:obsidians"), "minecraft:obsidian", "minecraft:crying_obsidian",
        "minecraft:reinforced_deepslate", "minecraft:netherite_block", "minecraft:respawn_anchor")


MOVED = []

# ---------------------------------------------------------------- Silent Gear (PLAN.md "Update 5 plan")

SWORD_CURVE = [4, 5, 6, 7, 9, 10.5, 13, 18, 24, 26]
ARMOR_CURVE = [5, 7, 10, 14, 18, 23, 29, 36, 45, 52]
VANILLA_ATTACK = [0, 1, 1.5, 2, 2.5, 3, 3, 3.5, 4, 4]
VANILLA_ARMOR = [5, 7, 11, 15, 15, 16, 20, 20, 20, 20]
# Tier of Silent Gear's own materials (Silent Gear, Silent's Gems, Metalworks), by material name.
SG_TIERS = {
    "wood": 0, "netherwood": 0, "bamboo": 0, "paper": 0, "leather": 0, "wool": 0, "sinew": 0, "fine_silk": 0,
    "string": 0, "flax": 0, "fluffy_string": 0, "slime": 0, "meat": 0, "stone": 1, "basalt": 1, "blackstone": 1,
    "end_stone": 1, "netherrack": 1, "terracotta": 1, "flint": 1, "bone": 1, "glass": 1, "prismarine": 2,
    "copper": 2, "tin": 2, "zinc": 2, "gold": 2, "iron": 3, "lead": 3, "nickel": 3, "aluminum": 3, "lapis_lazuli": 3,
    "redstone": 3, "opal": 3, "pearl": 3, "turquoise": 3, "moldavite": 3, "ammolite": 3, "silver": 4, "bronze": 4,
    "brass": 4, "invar": 4, "electrum": 4, "constantan": 4, "amethyst": 4, "quartz": 4, "glowstone": 4, "kyanite": 4,
    "citrine": 4, "carnelian": 4, "rose_quartz": 4, "steel": 5, "osmium": 5, "crimson_iron": 5, "azure_silver": 5,
    "uranium": 5, "garnet": 5, "peridot": 5, "iolite": 5, "tanzanite": 5, "emerald": 6, "diamond": 6, "platinum": 6,
    "refined_glowstone": 6, "blaze_gold": 6, "obsidian": 6, "topaz": 6, "aquamarine": 6, "heliodor": 6,
    "white_diamond": 6, "crimson_steel": 7, "azure_electrum": 7, "lumium": 7, "signalum": 7, "ruby": 7, "sapphire": 7,
    "alexandrite": 7, "enderium": 8, "refined_obsidian": 8, "black_diamond": 8, "netherite": 9, "tyrian_steel": 9,
    "uru_metal": 9,
}
# Every one of our materials makes Silent Gear rods (handles); the handle's bonus follows the material's personality.
SG_ROD_LIGHT = {"aluminum", "duralumin", "titanium", "chromoly", "titanium_alloy", "tin", "electrum", "rose_gold"}
SG_ROD_HEAVY = {"lead", "tungsten", "tungsten_carbide", "manganese_steel", "iridium", "osmiridium"}
SG_ROD_TOUGH = {"zinc", "nickel", "invar", "bismuth_bronze", "vanadium_steel", "stainless_steel", "stellite"}


def sg_rod(mid, tier, gem):
    def mul(stat, value):
        return {stat: {"operation": "MULTIPLY_TOTAL", "value": round(value, 3)}}
    if mid in SG_ROD_LIGHT:
        return {"attack_speed": {"operation": "ADD", "value": 0.15}, **mul("durability", 0.03 * tier)}
    if mid in SG_ROD_HEAVY:
        return {"attack_speed": {"operation": "ADD", "value": -0.05}, **mul("attack_damage", 0.04 + 0.01 * tier)}
    if mid in SG_ROD_TOUGH:
        return mul("durability", 0.1 + 0.02 * tier)
    if gem:
        return {**mul("harvest_speed", 0.03 + 0.01 * tier), **mul("durability", 0.05)}
    return {**mul("attack_damage", 0.03), **mul("durability", 0.05)}
SG_COATING_ALLOYS = {"stellite", "inconel", "osmiridium", "tungsten_carbide", "high_speed_steel"}
SG_TRAITS = {"tin": "malleable", "lead": "heavy", "aluminum": "light", "duralumin": "light", "cobalt": "accelerate",
             "alnico": "magnetic", "titanium": "light", "chromium": "hard", "stainless_steel": "sturdy",
             "tungsten": "heavy", "tungsten_carbide": "hard", "high_speed_steel": "accelerate", "stellite": "sturdy",
             "inconel": "fireproof", "constantan": "heat_resistant", "rose_gold": "lucky", "white_gold": "lustrous",
             "ruby": "sharp", "emerald": "lucky", "platinum": "lustrous"}


def sg_scale(value, factor):
    return round(value * factor, 2) if isinstance(value, (int, float)) else value


def sg_material(m, tier, ingredient, categories, name_key, main=True):
    a, t = m["armor"], m["tool"]
    total = a["helmet"] + a["chestplate"] + a["leggings"] + a["boots"]
    props = {}
    if main:
        props["silentgear:main"] = {
            "armor": float(total), "armor/helmet": float(a["helmet"]), "armor/chestplate": float(a["chestplate"]),
            "armor/leggings": float(a["leggings"]), "armor/boots": float(a["boots"]),
            "armor_durability": float(a["durability"]), "armor_toughness": float(a["toughness"] * 4),
            "attack_damage": float(t["attack"]), "attack_speed": 0.0, "charging_value": 1.0, "draw_speed": 0.0,
            "durability": float(t["uses"]), "enchantment_value": float(t["enchant"]),
            "harvest_speed": float(t["speed"]),
            "harvest_tier": {"incorrect_blocks_for_tool": f"{NS}:incorrect_for_tier_{tier}",
                             "level_hint": str(tier), "name": m["id"]},
            "magic_armor": round(total * 0.4, 1), "magic_damage": 1.0, "ranged_damage": round(t["attack"] * 0.5, 2),
            "rarity": float(tier * 10), "repair_value": 0.15,
            "traits": ([{"conditions": [], "level": 1, "trait": f"silentgear:{SG_TRAITS[m['id']]}"}]
                       if m["id"] in SG_TRAITS else []),
        }
    props["silentgear:rod"] = sg_rod(m["id"], tier, m["repair"].startswith("c:gems/"))
    if m["id"] in SG_COATING_ALLOYS:
        props["silentgear:coating"] = {"durability": {"operation": "MULTIPLY_TOTAL", "value": 0.25},
                                       "attack_damage": {"operation": "MULTIPLY_TOTAL", "value": 0.1}}
    if m.get("gem_tip"):
        props["silentgear:tip"] = m["gem_tip"]
    return {"type": "silentgear:simple", "parent": "silentgear:empty",
            "crafting": {"can_salvage": True, "categories": categories, "gear_type_blacklist": [],
                         "ingredient": ingredient, "part_substitutes": {}},
            "display": {"color": "#FF" + m["color"].lstrip("#").upper(), "main_texture_type": "HIGH_CONTRAST",
                        "name": {"translate": name_key}, "name_prefix": ""},
            "properties": props}


def tier_categories(tier):
    return [f"{NS}_tier_{tier}"] + ([f"{NS}_low"] if tier <= 3 else [])


def gen_silentgear():
    tiers = {}
    gem_items = {g["id"]: g for g in TABLE["gems"]}
    sg_cond = [{"type": "neoforge:mod_loaded", "modid": "silentgear"}]
    # Our materials as Silent Gear materials.
    for m in TABLE["gear"]:
        if m.get("armor_only"):
            continue
        mid, tier = m["id"], m["tier"]
        kind = "gem" if m["repair"].startswith("c:gems/") else "metal"
        gem = gem_items.get(mid)
        if gem:
            m = dict(m, gem_tip={"attack_damage": {"operation": "ADD", "value": round(0.5 + tier * 0.25, 2)},
                                 "durability": {"operation": "ADD", "value": 50 * tier}})
        data = sg_material(m, tier, {"tag": m["repair"]}, [kind] + tier_categories(tier), f"material.{NS}.{mid}")
        data["neoforge:conditions"] = sg_cond
        write_json(f"data/{NS}/silentgear_materials/{mid}.json", data)
        LANG[f"material.{NS}.{mid}"] = m["name"]
        tiers[f"{NS}:{mid}"] = tier
    # Flawless gems: strong tips and coatings only.
    for gem in TABLE["gems"]:
        gid, tier = gem["id"], gem["tier"] + 1
        props = {"silentgear:tip": {"attack_damage": {"operation": "ADD", "value": round(1.5 + tier * 0.5, 2)},
                                    "durability": {"operation": "ADD", "value": 150 * tier},
                                    "harvest_speed": {"operation": "ADD", "value": 0.5 * tier}},
                 "silentgear:coating": {"durability": {"operation": "MULTIPLY_TOTAL", "value": 0.35},
                                        "attack_damage": {"operation": "MULTIPLY_TOTAL", "value": 0.15},
                                        "enchantment_value": {"operation": "ADD", "value": 5.0}}}
        write_json(f"data/{NS}/silentgear_materials/flawless_{gid}.json", {
            "neoforge:conditions": sg_cond, "type": "silentgear:simple", "parent": "silentgear:empty",
            "crafting": {"can_salvage": False, "categories": ["gem"] + tier_categories(tier), "gear_type_blacklist": [],
                         "ingredient": {"item": f"{NS}:flawless_{gid}"}, "part_substitutes": {}},
            "display": {"color": "#FF" + gem["color"].lstrip("#").upper(), "main_texture_type": "HIGH_CONTRAST",
                        "name": {"translate": f"material.{NS}.flawless_{gid}"}, "name_prefix": ""},
            "properties": props})
        LANG[f"material.{NS}.flawless_{gid}"] = f"Flawless {gem['name']}"
        tiers[f"{NS}:flawless_{gid}"] = tier

    # Rebalance Silent Gear's own materials (Metalworks' versions win over the originals). Git-ignored copies.
    jars = {j.name: j for j in PACK_MODS.glob("*.jar")}
    sources = [j for n, j in jars.items() if n.startswith(("silent-gear-", "silentgems-"))] + \
              [j for n, j in jars.items() if n.startswith("sgearmetalworks")]
    materials = {}
    for jar in sources:
        with zipfile.ZipFile(jar) as z:
            for n in z.namelist():
                mm = re.match(r"data/([a-z_]+)/silentgear_materials/([a-z0-9_/]+)\.json$", n)
                if mm:
                    materials[(mm.group(1), mm.group(2))] = json.loads(z.read(n))
    shutil.rmtree(PROFILE_OUT / "kubejs/data/silentgear/silentgear_materials", ignore_errors=True)
    shutil.rmtree(PROFILE_OUT / "kubejs/data/silentgems/silentgear_materials", ignore_errors=True)
    shutil.rmtree(PROFILE_OUT / "kubejs/data/sgearmetalworks/silentgear_materials", ignore_errors=True)
    for (ns, path), data in materials.items():
        tier = SG_TIERS.get(path.split("/")[-1])
        if tier is None:
            continue
        tiers[f"{ns}:{path}"] = tier
        crafting = data.setdefault("crafting", {})
        crafting["categories"] = [c for c in crafting.get("categories", []) if not c.startswith(NS)] + tier_categories(tier)
        main = data.get("properties", {}).get("silentgear:main")
        if isinstance(main, dict):
            ht = main.get("harvest_tier")
            if isinstance(ht, dict):
                ht["incorrect_blocks_for_tool"] = f"{NS}:incorrect_for_tier_{tier}"
                ht["level_hint"] = str(tier)
            if isinstance(main.get("attack_damage"), (int, float)) and main["attack_damage"] > 0:
                ratio = max(0.75, min(1.25, main["attack_damage"] / max(0.5, VANILLA_ATTACK[tier])))
                main["attack_damage"] = round((SWORD_CURVE[tier] - 4) * ratio, 2)
            if isinstance(main.get("armor"), (int, float)) and main["armor"] > 0:
                ratio = max(0.75, min(1.25, main["armor"] / VANILLA_ARMOR[tier]))
                factor = ARMOR_CURVE[tier] * ratio / main["armor"]
                for key in [k for k in main if k == "armor" or k.startswith("armor/")]:
                    main[key] = sg_scale(main[key], factor)
        write_json(f"kubejs/data/{ns}/silentgear_materials/{path}.json", data, base=PROFILE_OUT)
    tiers.update(SG_EXTRA_TIERS)
    write_json(f"{NS}/sg_material_tiers.json", dict(sorted(tiers.items())))

    # Part recipes: crafting table for tier 1-3 materials, any Smithy Anvil up to its tier for all materials.
    shutil.rmtree(PROFILE_OUT / "kubejs/data/silentgear/recipe", ignore_errors=True)
    mw = next((j for n, j in jars.items() if n.startswith("sgearmetalworks")), None)
    if mw:
        with zipfile.ZipFile(mw) as z:
            for n in z.namelist():
                mm = re.match(r"data/silentgear/recipe/(gear/[a-z0-9_]+)\.json$", n)
                if not mm:
                    continue
                recipe = json.loads(z.read(n))
                text = json.dumps(recipe)
                if "not_categories" not in text:
                    continue
                anvil = json.loads(text.replace('"not_categories": ["casting"], ', '').replace('"not_categories": ["casting"]', ''))
                table = json.loads(text.replace('"not_categories": ["casting"]', f'"categories": ["{NS}_low"]'))
                write_json(f"kubejs/data/silentgear/recipe/{mm.group(1)}.json", table, base=PROFILE_OUT)
                anvil.pop("neoforge:conditions", None)
                write_json(f"data/{NS}/recipe/sg/{mm.group(1).split('/')[-1]}.json",
                           {"neoforge:conditions": sg_cond, "type": f"{NS}:anvil_delegate", "recipe": anvil})

    # Salvaging our gear back into materials.
    piece_returns = {"sword": 1, "pickaxe": 2, "axe": 2, "shovel": 1, "hoe": 1,
                     "helmet": 3, "chestplate": 5, "leggings": 4, "boots": 2}
    own_ingots = {i["id"] for i in TABLE["ingots"]}
    for m in TABLE["gear"]:
        mid = m["id"]
        if m.get("armor_only"):
            base = TABLE["scavenged"][mid][0]
            if base.startswith("#"):
                continue
            result = base
        elif mid in gem_items:
            result = gem_items[mid]["item"]
        elif mid in own_ingots:
            result = f"{NS}:{mid}_ingot"
        elif mid in ("tungsten", "stainless_steel"):
            result = f"modern_industrialization:{mid}_ingot"
        else:
            result = f"alltheores:{mid}_ingot"
        if mid == "amethyst":
            result = "minecraft:amethyst_shard"
        for kind, count in piece_returns.items():
            if m.get("armor_only") and kind in TOOL_KINDS:
                continue
            mods = sorted({"silentgear", result.split(":")[0]} - {"minecraft", NS})
            write_json(f"data/{NS}/recipe/salvage/{mid}_{kind}.json", {
                "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": x} for x in mods],
                "type": "silentgear:salvaging", "ingredient": {"item": f"{NS}:{mid}_{kind}"},
                "results": [{"count": count, "id": result}]})


def gen_loot_modifiers():
    write_json(f"data/{NS}/loot_modifiers/tiered_chest_loot.json",
               {"type": f"{NS}:tiered_chest_loot", "conditions": []})
    write_json("data/neoforge/loot_modifiers/global_loot_modifiers.json",
               {"replace": False, "entries": [f"{NS}:tiered_chest_loot"]})


def gen_alloys():
    for name, parts, result, count, needs in ALLOYS:
        ingredients = [ing(metal) for metal, n in parts for _ in range(n)]
        shapeless(f"alloy/{name}", ingredients, result, count, needs)
    shapeless("alloy/steel", [ing("iron"), {"tag": "minecraft:coals"}, {"tag": "minecraft:coals"}],
              "alltheores:steel_ingot", 1, "alltheores")
    shapeless("alloy/tungsten_carbide", [ing("tungsten"), ing("tungsten"), {"tag": "minecraft:coals"},
                                         {"tag": "minecraft:coals"}, ing("cobalt")],
              f"{NS}:tungsten_carbide_ingot", 2)


def gen_profile():
    """Pack-side files copied into the Claude profile by tools/install.py."""
    shutil.rmtree(PROFILE_OUT / "kubejs/server_scripts/zz_forgedascent", ignore_errors=True)
    for metal, (lo, hi, count) in ATO_DEPTHS.items():
        write_json(f"kubejs/data/alltheores/worldgen/placed_feature/ore_{metal}_placed.json", {
            "feature": f"alltheores:ore_{metal}",
            "placement": [
                {"type": "minecraft:count", "count": count},
                {"type": "minecraft:in_square"},
                {"type": "minecraft:height_range", "height": {
                    "type": "minecraft:trapezoid",
                    "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
                {"type": "minecraft:biome"}]}, base=PROFILE_OUT)
    # Gem ores drop rough gems (PLAN.md section 5). KubeJS data beats each mod's own loot table.
    silk = {"condition": "minecraft:match_tool", "predicate": {"predicates": {"minecraft:enchantments": [
        {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}
    for gem in TABLE["gems"]:
        for ore in gem["ores"]:
            ns, path = ore.split(":")
            write_json(f"kubejs/data/{ns}/loot_table/blocks/{path}.json", {
                "type": "minecraft:block",
                "pools": [{"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:alternatives", "children": [
                    {"type": "minecraft:item", "name": ore, "conditions": [silk]},
                    {"type": "minecraft:item", "name": f"{NS}:rough_{gem['id']}", "functions": [
                        {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                         "formula": "minecraft:ore_drops"},
                        {"function": "minecraft:explosion_decay"}]}]}]}]}, base=PROFILE_OUT)

    # Apotheosis world tiers also need Forged Ascent gear (PLAN.md section 8). Copied from the
    # Apotheosis jar with one extra criterion, so these files are git-ignored.
    apoth = next(PACK_MODS.glob(APOTHEOSIS_JAR_GLOB), None)
    if apoth:
        with zipfile.ZipFile(apoth) as z:
            for world_tier, gate in WORLD_TIER_SIGIL.items():
                adv = json.loads(z.read(f"data/apotheosis/advancement/progression/{world_tier}.json"))
                adv["criteria"]["forgedascent_gate"] = {
                    "trigger": "minecraft:inventory_changed",
                    "conditions": {"items": [{"items": f"{NS}:sigil_{gate}"}]}}
                adv["requirements"].append(["forgedascent_gate"])
                adv["display"]["description"] = {"translate": f"advancements.{NS}.{world_tier}.desc"}
                gate_name = next(g["name"] for g in TABLE["gates"] if g["gate"] == gate)
                LANG[f"advancements.{NS}.{world_tier}.desc"] = (
                    f"Equip affixed gear in every slot and beat a {gate_name} boss (get its Sigil)")
                write_json(f"kubejs/data/apotheosis/advancement/progression/{world_tier}.json", adv, base=PROFILE_OUT)
    else:
        print("WARNING: Apotheosis jar not found; world tier unlocks not generated")

    lines = ["// Generated by forgedascent/tools/gen_assets.py. Gates tier-less mining tools behind",
             "// Forged Ascent tiers: the listed ingredient becomes 'any ingot of tier N'.",
             "ServerEvents.recipes(event => {"]
    for output, old, tier in GATING:
        lines.append(f"  event.replaceInput({{ output: '{output}' }}, '{old}', '#{NS}:tier_materials/{tier}')")
    lines.append("")
    lines.append("  // Gear moved onto Smithy Anvils: remove its crafting-table and smithing-table recipes.")
    lines.append("  const moved = " + json.dumps(MOVED))
    lines.append("  const tableTypes = ['minecraft:crafting_shaped', 'minecraft:crafting_shapeless', "
                 "'minecraft:smithing_transform', 'mekanism:mek_data']")
    lines.append("  moved.forEach(id => tableTypes.forEach(type => event.remove({ output: id, type: type })))")
    lines.append("})")
    path = PROFILE_OUT / "kubejs/server_scripts/zz_forgedascent/gating.js"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tags():
    for (registry, full), entries in TAGS.items():
        ns, path = full.split(":", 1)
        seen, values = set(), []
        for e in entries:
            k = json.dumps(e, sort_keys=True)
            if k not in seen:
                seen.add(k)
                values.append(e)
        write_json(f"data/{ns}/tags/{registry}/{path}.json", {"values": values})


LANG = {
    "itemGroup.forgedascent": "Forged Ascent",
    "tooltip.forgedascent.reinforced": "Reinforced %s",
    "tooltip.forgedascent.reinforced_plate": "Reinforces gear up to tier %s at a Smithy Anvil",
    "tooltip.forgedascent.treasure_bag": "Right-click to open",
    "gui.forgedascent.anvil_tier": "Tier %s",
    "jei.forgedascent.anvil": "Smithy Anvil",
    "jei.forgedascent.needs_anvil": "Needs: %s or better",
    "jei.forgedascent.reinforce": "Put this plate and a tool, weapon or armor piece into a Smithy Anvil to reinforce "
                                  "it: +1 armor or +1 attack damage, +25% durability per level, up to Reinforced III. Level I needs a plate of the gear's tier, level II one grade higher, level III two grades higher.",
    "message.forgedascent.gate_cleared": "%s cleared %s! A new Smithy Anvil can now be forged.",
    "message.forgedascent.blood_moon_rise": "The moon rises blood red... the dead are restless tonight.",
    "message.forgedascent.blood_moon_set": "The blood moon sets. You survived the night.",
}


def main():
    global SRC
    for sub in (f"assets/{NS}", f"data/{NS}", "data/c", "data/minecraft", "data/neoforge"):
        shutil.rmtree(OUT / sub, ignore_errors=True)
    SRC = Sources()
    gen_ingots()
    gen_damascus()
    gen_ores()
    gen_gems()
    gen_gear()
    gen_tiers()
    gen_alloys()
    gen_elites()
    gen_smithy()
    gen_silentgear()
    gen_loot_modifiers()
    gen_profile()
    write_tags()
    write_json(f"assets/{NS}/lang/en_us.json", dict(sorted(LANG.items())))
    print(f"Generated {len(TABLE['gear'])} gear sets, {len(TABLE['ores'])} ores, {len(TABLE['ingots'])} ingots, "
          f"{len(TAGS)} tags")
    if MISSING:
        print("Missing source textures (used fallbacks):")
        for m in sorted(set(MISSING)):
            print("  ", m)


if __name__ == "__main__":
    main()
