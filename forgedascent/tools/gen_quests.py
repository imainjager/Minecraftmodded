"""Generates the "Forged Ascent" FTB Quests chapters (one per age) into ../profile/config/ftbquests/quests/chapters.

Text is written inline (title/subtitle/description); FTB Quests moves it into its lang files on load.
tools/install.py adds the chapter group to ATM10's chapter_groups.snbt. Run from forgedascent/:

    python tools/gen_quests.py
"""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "profile/config/ftbquests/quests/chapters"
NS = "forgedascent"
GROUP_ID = "F0A6ED5A5CE47001"


def qid(*parts):
    """Stable 16-hex-digit FTB Quests id."""
    return hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:16].upper()


def snbt(value, indent=0):
    pad = "\t" * indent
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value}d"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if not value:
            return "[ ]"
        inner = "\n".join(pad + "\t" + snbt(v, indent + 1) for v in value)
        return "[\n" + inner + "\n" + pad + "]"
    if isinstance(value, dict):
        inner = "\n".join(f"{pad}\t{k}: {snbt(v, indent + 1)}" for k, v in value.items())
        return "{\n" + inner + "\n" + pad + "}"
    raise TypeError(value)


class Chapter:
    def __init__(self, key, order, title, icon, subtitle):
        self.key, self.order, self.title, self.icon, self.subtitle = key, order, title, icon, subtitle
        self.quests = []
        self.last = None

    def quest(self, key, title, x, y, *, item=None, count=1, kill=None, check=False, desc=(), subtitle=None,
              icon=None, deps=None, rewards=(), xp=0, shape=None, size=None, optional=False):
        q = {"id": qid(self.key, key), "title": title, "x": float(x), "y": float(y)}
        if subtitle:
            q["subtitle"] = subtitle
        if desc:
            q["description"] = list(desc)
        if icon:
            q["icon"] = {"id": icon}
        if deps is None:
            deps = [self.last] if self.last else []
        if deps:
            q["dependencies"] = [qid(self.key, d) if not d.startswith("#") else d[1:] for d in deps]
        if shape:
            q["shape"] = shape
        if size:
            q["size"] = float(size)
        if optional:
            q["optional"] = True
        tasks = []
        if item:
            tasks.append({"id": qid(self.key, key, "task"), "type": "item", "item": {"count": 1, "id": item}, "count": count})
        if kill:
            tasks.append({"id": qid(self.key, key, "kill"), "type": "kill", "entity": kill, "value": 1})
        if check or not tasks:
            tasks.append({"id": qid(self.key, key, "check"), "type": "checkmark"})
        q["tasks"] = tasks
        rew = [{"id": qid(self.key, key, "reward", r), "type": "item", "item": {"count": 1, "id": r}, "count": c}
               for r, c in rewards]
        if xp:
            rew.append({"id": qid(self.key, key, "xp"), "type": "xp", "xp": xp})
        if rew:
            q["rewards"] = rew
        self.quests.append(q)
        if not optional:
            self.last = key
        return key

    def write(self):
        data = {"default_hide_dependency_lines": False, "default_quest_shape": "circle",
                "filename": self.key, "group": GROUP_ID, "icon": {"id": self.icon},
                "id": qid("chapter", self.key), "order_index": self.order, "quest_links": [],
                "subtitle": [self.subtitle], "title": self.title, "quests": self.quests}
        (OUT / f"{self.key}.snbt").write_text(snbt(data) + "\n", encoding="utf-8")


BOSS_TIPS = {
    "twilightforest:naga": ("Naga", "Twilight Forest: the big stone courtyard in the forest. Easiest gate boss."),
    "aether:slider": ("Slider", "The Aether: the Bronze Dungeon. A sliding stone block; hit it with a pickaxe."),
    "minecraft:elder_guardian": ("Elder Guardian", "Ocean Monuments. Bring Water Breathing and milk."),
    "twilightforest:lich": ("Lich", "Twilight Forest: the Lich Tower (after the Naga)."),
    "aether:valkyrie_queen": ("Valkyrie Queen", "The Aether: the Silver Dungeon."),
    "undergarden:forgotten_guardian": ("Forgotten Guardian", "The Undergarden: deep in the Catacombs."),
    "irons_spellbooks:dead_king": ("Dead King", "Iron's Spells: the Ancient Battleground / Dead King's crypt."),
    "twilightforest:minoshroom": ("Minoshroom", "Twilight Forest: the bottom of the Labyrinth in the swamp."),
    "twilightforest:hydra": ("Hydra", "Twilight Forest: the Fire Swamp lair. Fire resistance helps."),
    "cataclysm:netherite_monstrosity": ("Netherite Monstrosity", "Cataclysm: the Soul Black Smith in the Nether."),
    "eternal_starlight:starlight_golem": ("Starlight Golem", "Eternal Starlight: the Golem Forge."),
    "minecraft:wither": ("Wither", "Build it yourself from soul sand and wither skeleton skulls. Fight it underground."),
    "twilightforest:knight_phantom": ("Knight Phantoms", "Twilight Forest: the Stronghold (Dark Forest)."),
    "cataclysm:ender_guardian": ("Ender Guardian", "Cataclysm: the Ruined Citadel in the End."),
    "aether:sun_spirit": ("Sun Spirit", "The Aether: the Gold Dungeon."),
    "minecraft:ender_dragon": ("Ender Dragon", "The End. Bring a bow and blocks."),
    "cataclysm:ignis": ("Ignis", "Cataclysm: the Burning Arena in the Nether."),
    "twilightforest:ur_ghast": ("Ur-Ghast", "Twilight Forest: the Dark Tower."),
    "cataclysm:the_leviathan": ("Leviathan", "Cataclysm: the Sunken City in deep oceans."),
    "minecraft:warden": ("Warden", "Ancient Cities in the Deep Dark. Keep quiet... or don't."),
    "twilightforest:snow_queen": ("Snow Queen", "Twilight Forest: the Aurora Palace on the glacier."),
    "cataclysm:the_harbinger": ("Harbinger", "Cataclysm: the Wither Lab ruins."),
    "cataclysm:ancient_remnant": ("Ancient Remnant", "Cataclysm: the Cursed Pyramid in deserts."),
    "cataclysm:maledictus": ("Maledictus", "Cataclysm: the Frosted Prison in snowy biomes."),
    "cataclysm:scylla": ("Scylla", "Cataclysm: the Acropolis in the ocean."),
    "eternal_starlight:lunar_monstrosity": ("Lunar Monstrosity", "Eternal Starlight: the Cursed Garden."),
    "irons_spellbooks:fire_boss": ("Tyros", "Iron's Spells: the Ancient Fire Temple in the Nether."),
}

# (chapter key, title, icon, tier, subtitle, ore items, gear item, alloy items, extra (item, title, desc) quests)
AGES = [
    ("forged_ascent_1_stone", "Stone Age", "minecraft:stone_pickaxe", 3,
     "Tiers 1-3: copper, tin and zinc, then iron",
     ["minecraft:raw_copper", "alltheores:raw_tin", "alltheores:raw_zinc", "minecraft:raw_iron", "alltheores:raw_lead",
      "alltheores:raw_nickel", "alltheores:raw_aluminum", "forgedascent:raw_bismuth"],
     ["forgedascent:tin_pickaxe", "minecraft:iron_pickaxe", "forgedascent:lead_chestplate"],
     ["forgedascent:pewter_ingot"]),
    ("forged_ascent_2_bronze", "Bronze Age", "forgedascent:brass_pickaxe", 4,
     "Tier 4: the first alloys, cobalt and gem cutting",
     ["forgedascent:raw_manganese", "forgedascent:raw_cobalt", "forgedascent:raw_molybdenum", "alltheores:raw_osmium",
      "forgedascent:rough_emerald", "forgedascent:rough_garnet"],
     ["forgedascent:brass_pickaxe", "forgedascent:invar_chestplate", "forgedascent:amethyst_sword"],
     ["alltheores:bronze_ingot", "alltheores:brass_ingot", "forgedascent:duralumin_ingot"]),
    ("forged_ascent_3_steel", "Steel Age", "forgedascent:cobalt_pickaxe", 5,
     "Tier 5: steel, cobalt and the first diamonds",
     ["forgedascent:raw_vanadium", "forgedascent:rough_diamond", "alltheores:raw_platinum", "forgedascent:rough_topaz"],
     ["forgedascent:cobalt_pickaxe", "forgedascent:manganese_steel_chestplate", "forgedascent:garnet_sword"],
     ["alltheores:steel_ingot", "forgedascent:manganese_steel_ingot", "forgedascent:alnico_ingot"]),
    ("forged_ascent_4_gem", "Gem Age", "forgedascent:emerald_pickaxe", 6,
     "Tier 6: precious metals and cut gems",
     ["forgedascent:raw_titanium", "forgedascent:raw_chromium", "forgedascent:rough_ruby", "forgedascent:rough_sapphire",
      "forgedascent:rough_alexandrite"],
     ["forgedascent:platinum_pickaxe", "minecraft:diamond_chestplate", "forgedascent:topaz_sword"],
     ["forgedascent:vanadium_steel_ingot", "forgedascent:white_gold_ingot"]),
    ("forged_ascent_5_titanium", "Titanium Age", "forgedascent:titanium_pickaxe", 7,
     "Tier 7: refractory metals",
     ["modern_industrialization:raw_tungsten", "alltheores:raw_iridium", "forgedascent:rough_black_diamond"],
     ["forgedascent:titanium_pickaxe", "forgedascent:titanium_alloy_chestplate", "forgedascent:ruby_sword"],
     ["forgedascent:chromoly_ingot", "forgedascent:titanium_alloy_ingot", "modern_industrialization:stainless_steel_ingot"]),
    ("forged_ascent_6_tungsten", "Tungsten Age", "forgedascent:tungsten_carbide_pickaxe", 8,
     "Tier 8: superalloys",
     ["minecraft:ancient_debris"],
     ["forgedascent:tungsten_carbide_pickaxe", "forgedascent:iridium_chestplate", "forgedascent:black_diamond_sword"],
     ["forgedascent:tungsten_carbide_ingot", "forgedascent:high_speed_steel_ingot", "forgedascent:stellite_ingot",
      "forgedascent:inconel_ingot", "forgedascent:osmiridium_ingot"]),
    ("forged_ascent_7_netherite", "Netherite Age", "minecraft:netherite_pickaxe", 9,
     "Tier 9: netherite and the final bosses",
     ["minecraft:netherite_ingot"], ["minecraft:netherite_pickaxe", "minecraft:netherite_chestplate"], []),
]
ANVIL_OF_TIER = {4: "bronze", 5: "steel", 6: "gemstone", 7: "titanium", 8: "tungsten", 9: "netherite"}
WORLD_TIER_AFTER_GATE = {2: "Frontier", 3: "Ascent", 5: "Summit", 6: "Pinnacle"}


def name(item):
    return item.split(":")[1].replace("_", " ").title()


def main():
    table = json.loads((ROOT / "src/main/resources/forgedascent/materials.json").read_text(encoding="utf-8"))
    gates = {g["gate"]: g for g in table["gates"]}
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)

    for order, (key, title, icon, tier, subtitle, ores, gear, alloys) in enumerate(AGES):
        ch = Chapter(key, order, title, icon, subtitle)
        y = 0
        if order == 0:
            ch.quest("welcome", "Welcome to Forged Ascent", 0, 0, icon="forgedascent:tin_pickaxe", size=1.5, shape="gear",
                     subtitle="Read me first",
                     desc=["This pack has a long gear ladder: &etiers 1 to 9&r.",
                           "Every ore needs a pickaxe of its tier. A &6stone&r pickaxe can't mine iron any more: "
                           "you need copper, tin or zinc first.",
                           "Tier 4+ gear is crafted at a &bSmithy Anvil&r. Each anvil is unlocked by beating a "
                           "&cboss gate&r and using its &dSigil&r, Terraria style.",
                           "Mobs get stronger with your Apotheosis world tier, deep underground and in other "
                           "dimensions. Watch out for &4blood moons&r."],
                     rewards=[("alltheores:tin_ingot", 4)], xp=50)
        else:
            anvil = f"{NS}:{ANVIL_OF_TIER[tier]}_anvil"
            ch.quest("anvil", f"Forge the {name(anvil)}", 0, 0, item=anvil, size=1.5, shape="gear",
                     subtitle=f"Unlocks tier-{tier} gear",
                     desc=[f"Craft the &b{name(anvil)}&r from the previous anvil, the Sigil you won and tier-{min(tier, 8)} plates.",
                           f"It crafts every gear recipe up to &etier {tier}&r (JEI: the 'Smithy Anvil' tab).",
                           "Anvils also &breinforce&r gear: put gear + a reinforced plate of the same tier or higher in the grid."],
                     deps=[], rewards=[(f"{NS}:reinforced_plate_{min(tier, 9)}", 1)], xp=100)
        x = 2
        for i, ore in enumerate(ores):
            ch.quest(f"ore_{i}", f"Find {name(ore)}", x, -1 if i % 2 == 0 else 1,
                     item=ore, deps=[ch.last] if i == 0 else [f"ore_{i - 1}"],
                     desc=[f"Needs a tier-{max(1, tier - 1)} pickaxe or better." if order else "Mine it with the right pickaxe tier."])
            x += 1.0
        for i, alloy in enumerate(alloys):
            ch.quest(f"alloy_{i}", f"Alloy: {name(alloy)}", x, 0, item=alloy,
                     desc=["Alloys are mixed in a crafting table for now (check JEI for the real-world ratios)."])
            x += 1.0
        plate_item = "alltheores:iron_plate" if order == 0 else f"{NS}:reinforced_plate_{min(tier, 9)}"
        ch.quest("plates", "Hammer some plates", x, -1, item=plate_item,
                 desc=["Plates come from an All the Ores hammer (2 ingots), the IE Metal Press, Create's press or "
                       "the MI compressor.", "4 plates of a tier make a &breinforced plate&r of that tier."] if order == 0
                 else ["4 plates of this tier make the reinforced plate. Reinforce your best gear at your anvil!"])
        x += 1.0
        for i, g in enumerate(gear):
            ch.quest(f"gear_{i}", f"Gear up: {name(g)}", x, 0, item=g,
                     desc=["Gear of this tier keeps up with the mobs. Armor matters a lot in this pack."],
                     rewards=[("minecraft:experience_bottle", 4)])
            x += 1.0
        if order == 1:
            ch.quest("cutting", "Cut your first gem", x, -1, item=f"{NS}:emery_wheel",
                     desc=["Gem ores drop &arough gems&r. Put a rough gem and a cutting wheel in a crafting grid to cut it.",
                           "Emery wheels cut gems up to hardness 8; diamond, ruby, sapphire and black diamond need a "
                           "diamond-grit wheel (crush rough diamonds into grit)."])
            x += 1.0
        if order == 0:
            ch.quest("blood_moon", "Beware the blood moon", x, 1, check=True, icon="minecraft:zombie_head",
                     desc=["After your first gate boss, roughly 1 night in 8 is a &4blood moon&r: twice the monsters, "
                           "more elites, no sleeping, better drops.",
                           "Zombies and Brutes &cdig through walls&r to reach you. They can't break machines, chests "
                           "or obsidian-tier blocks."], optional=True)
            x += 1.0

        # Boss gate
        gate_no = order + 1
        gate = gates[gate_no]
        before_gate = ch.last
        gx = x + 1
        for i, boss in enumerate(gate["bosses"]):
            bname, tip = BOSS_TIPS.get(boss, (name(boss), ""))
            ch.quest(f"boss_{i}", f"Defeat: {bname}", gx, -2 + i * 1.3, kill=boss, deps=[before_gate],
                     subtitle=gate["name"] + " boss", desc=[tip, "Any one boss of this gate is enough."],
                     shape="hexagon", optional=True)
        if gate_no <= 6:
            ch.quest("sigil", f"{gate['name']} Sigil", gx + 2, 0, item=f"{NS}:sigil_{gate_no}", deps=[before_gate],
                     size=1.5, shape="gear", subtitle="Beat any boss above",
                     desc=[f"Every {gate['name']} boss drops a &dTreasure Bag&r with this Sigil, tier materials, "
                           "rough gems and an accessory.",
                           f"Use the Sigil to forge the next Smithy Anvil."]
                     + ([f"It also unlocks the Apotheosis world tier &e{WORLD_TIER_AFTER_GATE[gate_no]}&r."]
                        if gate_no in WORLD_TIER_AFTER_GATE else []),
                     xp=250)
        else:
            ch.quest("final", "Conquer the Final Gate", gx + 2, 0, check=True, deps=[before_gate], size=1.5,
                     shape="gear", desc=["Beat any final boss above for the Final Treasure Bag. "
                                         "Beyond this lies ATM's own Allthemodium ladder."], xp=500)
        ch.write()

    print(f"Wrote {len(AGES)} chapters to {OUT}")


if __name__ == "__main__":
    main()
