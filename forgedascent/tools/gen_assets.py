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
# Apotheosis world tier -> gear tier needed to unlock it (PLAN.md section 8).
WORLD_TIER_GEAR = {"frontier": 4, "ascent": 6, "summit": 7, "pinnacle": 8}
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


def gen_ingots():
    for ingot in TABLE["ingots"]:
        iid, color, style = ingot["id"], ingot["color"], ingot["style"]
        save_png(f"assets/{NS}/textures/item/{iid}_ingot.png",
                 source_or_fallback(f"alltheores:item/{style}_ingot", color, "minecraft:item/iron_ingot"))
        save_png(f"assets/{NS}/textures/block/{iid}_block.png",
                 source_or_fallback(f"alltheores:block/{style}_block", color, "minecraft:block/iron_block"))
        item_model(f"{iid}_ingot", "minecraft:item/generated", f"{iid}_ingot")
        cube_block(f"{iid}_block")
        self_drop(f"{iid}_block")
        LANG[f"item.{NS}.{iid}_ingot"] = f"{ingot['name']} Ingot"
        LANG[f"block.{NS}.{iid}_block"] = f"Block of {ingot['name']}"
        shaped(f"{iid}_block", f"{NS}:{iid}_block", ["XXX", "XXX", "XXX"], {"X": ing(iid)}, "building")
        shapeless(f"{iid}_ingot_from_block", [{"tag": f"c:storage_blocks/{iid}"}], f"{NS}:{iid}_ingot", 9)
        tag("item", f"c:ingots/{iid}", f"{NS}:{iid}_ingot")
        tag("item", "c:ingots", f"#c:ingots/{iid}")
        for reg in ("item", "block"):
            tag(reg, f"c:storage_blocks/{iid}", f"{NS}:{iid}_block")
            tag(reg, "c:storage_blocks", f"#c:storage_blocks/{iid}")
        tag("block", "minecraft:mineable/pickaxe", f"{NS}:{iid}_block")
        tag("block", "minecraft:needs_stone_tool", f"{NS}:{iid}_block")


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


def gen_gear():
    for m in TABLE["gear"]:
        mid, name, color, tier = m["id"], m["name"], m["color"], m["tier"]
        TIER_MATERIALS.setdefault(tier, []).append(m["repair"])
        for unlock in WORLD_TIER_GEAR.values():
            if tier >= unlock:
                for kind in ("pickaxe", "sword", "chestplate"):
                    tag("item", f"{NS}:gear/tier_{unlock}", f"{NS}:{mid}_{kind}")
        key_tool = {"X": {"tag": m["repair"]}, "#": {"tag": "c:rods/wooden"}}
        tns, tprefix = m["tools_from"].split(":")
        for kind in TOOL_KINDS:
            item = f"{mid}_{kind}"
            if kind == "sword":
                img = draw_sprite(SHAPES["sword"], color)
            else:
                img = source_or_fallback(f"{tns}:item/{tprefix}_{kind}", color, f"minecraft:item/iron_{kind}", tool=True)
            save_png(f"assets/{NS}/textures/item/{item}.png", img)
            item_model(item, "minecraft:item/handheld", item)
            shaped(item, f"{NS}:{item}", TOOL_PATTERNS[kind], key_tool)
            tag("item", f"minecraft:{TOOL_TAGS[kind]}", f"{NS}:{item}")
            LANG[f"item.{NS}.{item}"] = f"{name} {kind.capitalize()}"
        ans, aprefix = m["armor_from"].split(":")
        for kind in ARMOR_KINDS:
            item = f"{mid}_{kind}"
            save_png(f"assets/{NS}/textures/item/{item}.png",
                     source_or_fallback(f"{ans}:item/{aprefix}_{kind}", color, f"minecraft:item/iron_{kind}"))
            item_model(item, "minecraft:item/generated", item)
            shaped(item, f"{NS}:{item}", ARMOR_PATTERNS[kind], {"X": {"tag": m["repair"]}})
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
            for world_tier, gear_tier in WORLD_TIER_GEAR.items():
                adv = json.loads(z.read(f"data/apotheosis/advancement/progression/{world_tier}.json"))
                adv["criteria"]["forgedascent_gear"] = {
                    "trigger": "minecraft:inventory_changed",
                    "conditions": {"items": [{"items": f"#{NS}:gear/tier_{gear_tier}"}]}}
                adv["requirements"].append(["forgedascent_gear"])
                adv["display"]["description"] = {"translate": f"advancements.{NS}.{world_tier}.desc"}
                LANG[f"advancements.{NS}.{world_tier}.desc"] = (
                    f"Equip affixed gear in every slot and own tier-{gear_tier} gear from Forged Ascent "
                    f"(or something as strong)")
                write_json(f"kubejs/data/apotheosis/advancement/progression/{world_tier}.json", adv, base=PROFILE_OUT)
    else:
        print("WARNING: Apotheosis jar not found; world tier unlocks not generated")

    lines = ["// Generated by forgedascent/tools/gen_assets.py. Gates tier-less mining tools behind",
             "// Forged Ascent tiers: the listed ingredient becomes 'any ingot of tier N'.",
             "ServerEvents.recipes(event => {"]
    for output, old, tier in GATING:
        lines.append(f"  event.replaceInput({{ output: '{output}' }}, '{old}', '#{NS}:tier_materials/{tier}')")
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


LANG = {"itemGroup.forgedascent": "Forged Ascent"}


def main():
    global SRC
    for sub in (f"assets/{NS}", f"data/{NS}", "data/c", "data/minecraft", "data/neoforge"):
        shutil.rmtree(OUT / sub, ignore_errors=True)
    SRC = Sources()
    gen_ingots()
    gen_ores()
    gen_gems()
    gen_gear()
    gen_tiers()
    gen_alloys()
    gen_elites()
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
