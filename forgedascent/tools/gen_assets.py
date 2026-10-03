"""Generates Forged Ascent textures, models, recipes, tags, loot tables and English names.

Reads src/main/resources/forgedascent/materials.json (the same table the Java code reads)
and writes everything into src/generated/resources. Run from the forgedascent folder:

    python tools/gen_assets.py
"""
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TABLE = json.loads((ROOT / "src/main/resources/forgedascent/materials.json").read_text(encoding="utf-8"))
OUT = ROOT / "src/generated/resources"
NS = "forgedascent"

# ---------------------------------------------------------------- colors

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(rgb, f):
    """f > 0 lightens toward white, f < 0 darkens toward black."""
    if f >= 0:
        return tuple(round(c + (255 - c) * f) for c in rgb)
    return tuple(round(c * (1 + f)) for c in rgb)


def palette(hex_color):
    base = hex_rgb(hex_color)
    return {"hi": shade(base, 0.30), "base": base, "lo": shade(base, -0.25), "line": shade(base, -0.60)}


WOOD = {"hi": (150, 104, 56), "base": (122, 82, 44), "lo": (92, 60, 30), "line": (46, 30, 14)}

# ---------------------------------------------------------------- item sprites
# X = material, D = dark material (guards), H = wooden handle. Outlines and shading are added automatically.

SHAPES = {
    "pickaxe": """
................
....XXXXXX......
..XXXXXXXXXX....
.XXX.....XXXX...
.XX......HXXXX..
.X......H..XXX..
.......H....XXX.
......H......XX.
.....H.......XX.
....H.........X.
...H............
..H.............
.H..............
................
................
................""",
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
    "axe": """
.............H..
......XXXXX.H...
.....XXXXXXXH...
....XXXXXXXH....
....XXXXXXH.....
....XXXXXH......
.....XXXH.......
.......H........
......H.........
.....H..........
....H...........
...H............
..H.............
.H..............
................
................""",
    "shovel": """
................
..........XXX...
.........XXXXX..
.........XXXXXX.
..........XXXXX.
.........H.XXX..
........H.......
.......H........
......H.........
.....H..........
....H...........
...H............
..H.............
.H..............
................
................""",
    "hoe": """
.............H..
......XXXXXXXH..
.....XX.....H...
.....X.....H....
..........H.....
.........H......
........H.......
.......H........
......H.........
.....H..........
....H...........
...H............
..H.............
.H..............
................
................""",
    "helmet": """
................
................
................
....XXXXXXXX....
...XXXXXXXXXX...
...XXXXXXXXXX...
...XXX....XXX...
...XXX....XXX...
...XX......XX...
................
................
................
................
................
................
................""",
    "chestplate": """
................
................
..XXX......XXX..
.XXXXX....XXXXX.
.XXXXXXXXXXXXXX.
.XXXXXXXXXXXXXX.
..XX.XXXXXX.XX..
.....XXXXXX.....
.....XXXXXX.....
.....XXXXXX.....
.....XXXXXX.....
.....XXXXXX.....
................
................
................
................""",
    "leggings": """
................
................
....XXXXXXXX....
....XXXXXXXX....
....XXXXXXXX....
....XXX..XXX....
....XXX..XXX....
....XXX..XXX....
....XXX..XXX....
....XXX..XXX....
....XXX..XXX....
....XXX..XXX....
................
................
................
................""",
    "boots": """
................
................
................
................
................
................
...XXX....XXX...
...XXX....XXX...
...XXX....XXX...
..XXXX....XXXX..
..XXXX....XXXX..
................
................
................
................
................""",
    "ingot": """
................
................
................
................
................
................
.....XXXXXXXX...
...XXXXXXXXXX...
..XXXXXXXXXXX...
..XXXXXXXXXX....
..XXXXXXXX......
................
................
................
................
................""",
}


def parse(shape):
    rows = [r for r in shape.strip("\n").split("\n")]
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), shape
    return rows


def draw_sprite(shape, pal):
    rows = parse(shape)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()

    def filled(x, y):
        return 0 <= x < 16 and 0 <= y < 16 and rows[y][x] != "."

    for y in range(16):
        for x in range(16):
            c = rows[y][x]
            if c == ".":
                if any(filled(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[x, y] = (*(WOOD["line"] if _near_only_handle(rows, x, y) else pal["line"]), 255)
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


def _near_only_handle(rows, x, y):
    near = [rows[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= x + dx < 16 and 0 <= y + dy < 16 and rows[y + dy][x + dx] != "."]
    return bool(near) and all(c == "H" for c in near)


def draw_block(pal):
    img = Image.new("RGBA", (16, 16))
    px = img.load()
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                c = pal["line"]
            elif x == 1 or y == 1:
                c = pal["hi"]
            elif x == 14 or y == 14:
                c = pal["lo"]
            elif (x + y) % 7 == 0 and 3 < x < 12:
                c = pal["hi"]
            else:
                c = pal["base"]
            px[x, y] = (*c, 255)
    return img

# ---------------------------------------------------------------- worn armor (64x32 humanoid layout)


def faces(u, v, w, h, d):
    """UV rectangles of a model cuboid: name -> (x, y, width, height)."""
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h),
        "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h),
        "back": (u + d + w + d, v + d, w, h),
    }


def paint_face(px, rect, pal, rows=None):
    x0, y0, w, h = rect
    for dy in range(h):
        if rows is not None and dy not in rows:
            continue
        for dx in range(w):
            if dy == 0 or (rows is not None and dy == min(rows)):
                c = pal["hi"]
            elif dy == h - 1 or dx == w - 1 or (rows is not None and dy == max(rows)):
                c = pal["lo"]
            elif dx == 0:
                c = pal["hi"]
            else:
                c = pal["base"] if (dx * 3 + dy * 5) % 11 else pal["lo"]
            px[x0 + dx, y0 + dy] = (*c, 255)


def draw_armor_layers(pal):
    one = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    p1 = one.load()
    # Helmet: whole head except the bottom, with an open visor on the front.
    for name, rect in faces(0, 0, 8, 8, 8).items():
        if name == "bottom":
            continue
        if name == "front":
            x0, y0, w, h = rect
            paint_face(p1, rect, pal, rows=range(0, 3))
            for dy in range(3, h):
                for dx in (0, w - 1):
                    p1[x0 + dx, y0 + dy] = (*pal["lo"], 255)
            continue
        paint_face(p1, rect, pal)
    # Chestplate: body + both arms (arms share one UV in armor layers).
    for rect in faces(16, 16, 8, 12, 4).values():
        paint_face(p1, rect, pal)
    for name, rect in faces(40, 16, 4, 12, 4).items():
        if name != "bottom":
            paint_face(p1, rect, pal)
    # Boots: lower 5 rows of the legs plus the soles.
    for name, rect in faces(0, 16, 4, 12, 4).items():
        if name == "top":
            continue
        if name == "bottom":
            paint_face(p1, rect, pal)
        else:
            paint_face(p1, rect, pal, rows=range(rect[3] - 5, rect[3]))

    two = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    p2 = two.load()
    # Leggings: legs down to the shins, plus the lower body as a belt.
    for name, rect in faces(0, 16, 4, 12, 4).items():
        if name == "bottom":
            continue
        paint_face(p2, rect, pal, rows=None if name == "top" else range(0, 9))
    for name, rect in faces(16, 16, 8, 12, 4).items():
        if name in ("top", "bottom"):
            continue
        paint_face(p2, rect, pal, rows=range(rect[3] - 4, rect[3]))
    return one, two

# ---------------------------------------------------------------- data helpers


def write_json(rel, data):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def save_png(rel, img):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def opt(tag_or_id):
    return {"id": tag_or_id, "required": False}


TAGS = {}  # (registry, "ns:path") -> list of entries


def tag(registry, name, *entries):
    TAGS.setdefault((registry, name), []).extend(entries)


def item_model(name, parent, texture):
    write_json(f"assets/{NS}/models/item/{name}.json",
               {"parent": parent, "textures": {"layer0": f"{NS}:item/{texture}"}})


def shaped(name, result, pattern, key, category="equipment"):
    write_json(f"data/{NS}/recipe/{name}.json", {
        "type": "minecraft:crafting_shaped", "category": category,
        "key": key, "pattern": pattern, "result": {"count": 1, "id": result}})


def shapeless(name, ingredients, result, count, needs_mod=None):
    data = {"type": "minecraft:crafting_shapeless", "category": "misc",
            "ingredients": ingredients, "result": {"count": count, "id": result}}
    if needs_mod:
        data["neoforge:conditions"] = [{"type": "neoforge:mod_loaded", "modid": needs_mod}]
    write_json(f"data/{NS}/recipe/{name}.json", data)


def ing(name):
    return {"tag": f"c:ingots/{name}"}

# ---------------------------------------------------------------- generation

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

# Ore mining tiers (PLAN.md section 3). Ore tier N needs a tier-N pickaxe.
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

# Ingots/gems per tier for "any material of this tier" recipes (PLAN.md section 1).
TIER_MATERIALS = {
    2: ["copper", "tin", "zinc"],
    3: ["iron", "lead", "nickel", "aluminum", "pewter"],
    4: ["bronze", "brass", "invar", "constantan", "silver", "electrum"],
    5: ["steel", "osmium"],
}

# Temporary crafting-table alloys (PLAN.md scope changes). Output comes from All the Ores unless ours.
ALLOYS = [
    ("pewter", [("tin", 3), ("lead", 1)], f"{NS}:pewter_ingot", 4, None),
    ("bronze", [("copper", 3), ("tin", 1)], "alltheores:bronze_ingot", 4, "alltheores"),
    ("brass", [("copper", 3), ("zinc", 1)], "alltheores:brass_ingot", 4, "alltheores"),
    ("invar", [("iron", 2), ("nickel", 1)], "alltheores:invar_ingot", 3, "alltheores"),
    ("constantan", [("copper", 1), ("nickel", 1)], "alltheores:constantan_ingot", 2, "alltheores"),
    ("electrum", [("gold", 1), ("silver", 1)], "alltheores:electrum_ingot", 2, "alltheores"),
]


def main():
    for sub in (f"assets/{NS}", f"data/{NS}", "data/c", "data/minecraft"):
        shutil.rmtree(OUT / sub, ignore_errors=True)

    lang = {"itemGroup.forgedascent": "Forged Ascent"}
    colors = {m["id"]: m["color"] for m in TABLE["gear"]}
    colors.update({i["id"]: i["color"] for i in TABLE["ingots"]})

    # New ingots + storage blocks
    for ingot in TABLE["ingots"]:
        iid, name, pal = ingot["id"], ingot["name"], palette(ingot["color"])
        save_png(f"assets/{NS}/textures/item/{iid}_ingot.png", draw_sprite(SHAPES["ingot"], pal))
        save_png(f"assets/{NS}/textures/block/{iid}_block.png", draw_block(pal))
        item_model(f"{iid}_ingot", "minecraft:item/generated", f"{iid}_ingot")
        write_json(f"assets/{NS}/models/block/{iid}_block.json",
                   {"parent": "minecraft:block/cube_all", "textures": {"all": f"{NS}:block/{iid}_block"}})
        write_json(f"assets/{NS}/models/item/{iid}_block.json", {"parent": f"{NS}:block/{iid}_block"})
        write_json(f"assets/{NS}/blockstates/{iid}_block.json",
                   {"variants": {"": {"model": f"{NS}:block/{iid}_block"}}})
        write_json(f"data/{NS}/loot_table/blocks/{iid}_block.json", {
            "type": "minecraft:block",
            "pools": [{"rolls": 1, "bonus_rolls": 0, "conditions": [{"condition": "minecraft:survives_explosion"}],
                       "entries": [{"type": "minecraft:item", "name": f"{NS}:{iid}_block"}]}]})
        lang[f"item.{NS}.{iid}_ingot"] = f"{name} Ingot"
        lang[f"block.{NS}.{iid}_block"] = f"Block of {name}"
        shaped(f"{iid}_block", f"{NS}:{iid}_block", ["XXX", "XXX", "XXX"], {"X": ing(iid)}, "building")
        shapeless(f"{iid}_ingot_from_block", [{"tag": f"c:storage_blocks/{iid}"}], f"{NS}:{iid}_ingot", 9)
        tag("item", f"c:ingots/{iid}", f"{NS}:{iid}_ingot")
        tag("item", "c:ingots", f"#c:ingots/{iid}")
        tag("item", f"c:storage_blocks/{iid}", f"{NS}:{iid}_block")
        tag("item", "c:storage_blocks", f"#c:storage_blocks/{iid}")
        tag("block", f"c:storage_blocks/{iid}", f"{NS}:{iid}_block")
        tag("block", "c:storage_blocks", f"#c:storage_blocks/{iid}")
        tag("block", "minecraft:mineable/pickaxe", f"{NS}:{iid}_block")
        tag("block", "minecraft:needs_stone_tool", f"{NS}:{iid}_block")

    # Gear sets
    for m in TABLE["gear"]:
        mid, name, pal = m["id"], m["name"], palette(m["color"])
        key_tool = {"X": {"tag": m["repair"]}, "#": {"tag": "c:rods/wooden"}}
        for kind, pattern in TOOL_PATTERNS.items():
            item = f"{mid}_{kind}"
            save_png(f"assets/{NS}/textures/item/{item}.png", draw_sprite(SHAPES[kind], pal))
            item_model(item, "minecraft:item/handheld", item)
            shaped(item, f"{NS}:{item}", pattern, key_tool)
            tag("item", f"minecraft:{TOOL_TAGS[kind]}", f"{NS}:{item}")
            lang[f"item.{NS}.{item}"] = f"{name} {kind.capitalize()}"
        for kind, pattern in ARMOR_PATTERNS.items():
            item = f"{mid}_{kind}"
            save_png(f"assets/{NS}/textures/item/{item}.png", draw_sprite(SHAPES[kind], pal))
            item_model(item, "minecraft:item/generated", item)
            shaped(item, f"{NS}:{item}", pattern, {"X": {"tag": m["repair"]}})
            tag("item", f"minecraft:{ARMOR_TAGS[kind]}", f"{NS}:{item}")
            tag("item", "minecraft:trimmable_armor", f"{NS}:{item}")
            lang[f"item.{NS}.{item}"] = f"{name} {kind.capitalize()}"
        one, two = draw_armor_layers(pal)
        save_png(f"assets/{NS}/textures/models/armor/{mid}_layer_1.png", one)
        save_png(f"assets/{NS}/textures/models/armor/{mid}_layer_2.png", two)

    # Mining tiers
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
    # Vanilla tool tiers land on our ladder: wood 0, gold 0, stone 1, iron 3, diamond 6.
    for vanilla, t in (("wooden", 0), ("gold", 0), ("stone", 1), ("iron", 3), ("diamond", 6)):
        tag("block", f"minecraft:incorrect_for_{vanilla}_tool", f"#{NS}:incorrect_for_tier_{t}")

    # "Any material of this tier" item tags
    for tier, mats in TIER_MATERIALS.items():
        tag("item", f"{NS}:tier_materials/{tier}", *[opt(f"#c:ingots/{x}") for x in mats])

    # Crafting-table alloys
    for name, parts, result, count, needs in ALLOYS:
        ingredients = [ing(metal) for metal, n in parts for _ in range(n)]
        shapeless(f"alloy/{name}", ingredients, result, count, needs)
    shapeless("alloy/steel", [ing("iron"), {"tag": "minecraft:coals"}, {"tag": "minecraft:coals"}],
              "alltheores:steel_ingot", 1, "alltheores")

    # Write tags
    for (registry, full), entries in TAGS.items():
        ns, path = full.split(":", 1)
        folder = "item" if registry == "item" else "block"
        seen, values = set(), []
        for e in entries:
            k = json.dumps(e, sort_keys=True)
            if k not in seen:
                seen.add(k)
                values.append(e)
        write_json(f"data/{ns}/tags/{folder}/{path}.json", {"values": values})

    write_json(f"assets/{NS}/lang/en_us.json", dict(sorted(lang.items())))
    print(f"Generated {len(TABLE['gear'])} gear sets, {len(TABLE['ingots'])} ingots, {len(TAGS)} tags into {OUT}")


if __name__ == "__main__":
    main()
