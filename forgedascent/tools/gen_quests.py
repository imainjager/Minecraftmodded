"""Generates the "Forged Ascent" FTB Quests chapters into ../profile/config/ftbquests/quests/chapters.

One chapter per age, each a linear path: arrival -> mine the new ores -> alloys -> pattern-welded metals ->
plates & reinforcing -> gear up -> side branches (gems, Silent Gear) -> prepare -> boss gate -> Sigil.
Text is written inline; FTB Quests moves it into its lang files on load. tools/install.py adds the chapter group.
Run from forgedascent/:

    python tools/gen_quests.py
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_assets as ga  # noqa: E402  (material tables: alloys, gems, gates)

OUT = ROOT.parent / "profile/config/ftbquests/quests/chapters"
NS = "forgedascent"
GROUP_ID = "70A6ED5A5CE47001"
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def qid(*parts):
    """Stable 16-hex-digit FTB Quests id. FTB Quests ids are positive longs, so the first digit must be 0-7."""
    value = int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF
    return f"{value:016X}"


def snbt_key(key):
    # Keys with characters like ':' must be quoted (e.g. "ftbfiltersystem:filter").
    return key if re.fullmatch(r"[A-Za-z0-9_]+", key) else json.dumps(key)


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
        return "[\n" + "\n".join(pad + "\t" + snbt(v, indent + 1) for v in value) + "\n" + pad + "]"
    if isinstance(value, dict):
        inner = "\n".join(f"{pad}\t{snbt_key(k)}: {snbt(v, indent + 1)}" for k, v in value.items())
        return "{\n" + inner + "\n" + pad + "}"
    raise TypeError(value)


class Chapter:
    def __init__(self, key, order, title, icon, subtitle):
        self.key, self.order, self.title, self.icon, self.subtitle = key, order, title, icon, subtitle
        self.quests, self.last, self.x = [], None, 0.0

    def quest(self, key, title, *, x=None, y=0.0, item=None, count=1, kill=None, check=False, desc=(),
              subtitle=None, icon=None, deps=None, rewards=(), xp=0, shape=None, size=None, optional=False, step=True):
        if x is None:
            x = self.x
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
            q["dependencies"] = [qid(self.key, d) for d in deps]
        if shape:
            q["shape"] = shape
        if size:
            q["size"] = float(size)
        if optional:
            q["optional"] = True
        tasks = []
        if item and item.startswith("#"):
            tasks.append({"id": qid(self.key, key, "task"), "type": "item", "count": count, "item": {
                "count": 1, "id": "ftbfiltersystem:smart_filter",
                "components": {"ftbfiltersystem:filter": f"item_tag({item[1:]})"}}})
        elif item:
            tasks.append({"id": qid(self.key, key, "task"), "type": "item", "count": count,
                          "item": {"count": 1, "id": item}})
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
        if step:
            self.x = x + 1.25
        return key

    def write(self):
        data = {"default_hide_dependency_lines": False, "default_quest_shape": "circle", "filename": self.key,
                "group": GROUP_ID, "icon": {"id": self.icon}, "id": qid("chapter", self.key),
                "order_index": self.order, "quest_links": [], "subtitle": [self.subtitle], "title": self.title,
                "quests": self.quests}
        (OUT / f"{self.key}.snbt").write_text(snbt(data) + "\n", encoding="utf-8")


# Ores by the pickaxe tier that mines them: (item, name, where to find it)
ORES = {
    1: [("minecraft:raw_copper", "Copper", "Everywhere, mid heights."),
        ("alltheores:raw_tin", "Tin", "Shallow stone, y 0 to 160."),
        ("alltheores:raw_zinc", "Zinc", "Stone, y 0 to 128."),
        (f"{NS}:raw_bismuth", "Bismuth", "Near the surface, y 0 to 128 (pink-purple ore).")],
    2: [("minecraft:raw_iron", "Iron", "Everywhere. Needs a copper, tin or zinc pickaxe now."),
        ("alltheores:raw_lead", "Lead", "Middle depths, y -40 to 80."),
        ("alltheores:raw_nickel", "Nickel", "Middle depths, y -40 to 80."),
        ("alltheores:raw_aluminum", "Aluminum", "y -16 to 128.")],
    3: [("minecraft:raw_gold", "Gold", "Deep stone and the Nether."),
        ("alltheores:raw_silver", "Silver", "Deep, below y 56."),
        (f"{NS}:raw_manganese", "Manganese", "y -24 to 72 (brown-grey ore)."),
        ("minecraft:redstone", "Redstone", "Deep, near bedrock."),
        ("minecraft:amethyst_shard", "Amethyst", "Amethyst geodes underground.")],
    4: [(f"{NS}:raw_cobalt", "Cobalt", "Common in the &cNether&r, rare in deep deepslate."),
        ("alltheores:raw_osmium", "Osmium", "Deep, y -64 to 24 (smaller veins now)."),
        (f"{NS}:raw_molybdenum", "Molybdenum", "Under &amountain&r biomes."),
        (f"{NS}:rough_emerald", "Emerald", "Mountains. Drops rough: cut it with an emery wheel."),
        (f"{NS}:rough_garnet", "Garnet", "Silent's Gems ore. Drops rough."),
        (f"{NS}:rough_peridot", "Peridot", "Drops rough.")],
    5: [(f"{NS}:rough_diamond", "Diamond", "Deep. Drops rough: cut it with a diamond-grit wheel."),
        ("alltheores:raw_platinum", "Platinum", "Deep, y -64 to 0."),
        (f"{NS}:raw_vanadium", "Vanadium", "Under &edeserts and badlands&r (red ore)."),
        (f"{NS}:rough_topaz", "Topaz", "Drops rough.")],
    6: [(f"{NS}:raw_titanium", "Titanium", "Deep deepslate; more under mountains."),
        (f"{NS}:raw_chromium", "Chromium", "Deep deepslate and the Nether's basalt deltas."),
        (f"{NS}:rough_ruby", "Ruby", "Drops rough."), (f"{NS}:rough_sapphire", "Sapphire", "Drops rough."),
        (f"{NS}:rough_alexandrite", "Alexandrite", "Drops rough.")],
    7: [("modern_industrialization:raw_tungsten", "Tungsten", "Deep stone."),
        ("alltheores:raw_iridium", "Iridium", "Very deep, y -64 to -24."),
        (f"{NS}:rough_black_diamond", "Black Diamond", "Drops rough. The toughest gem.")],
    8: [("minecraft:ancient_debris", "Ancient Debris", "Low in the Nether.")],
}
EXTRA_ALLOY_TIERS = {"electrum": 4, "steel": 5, "stainless_steel": 7, "nichrome": 6, "tungsten_carbide": 8}
# (chapter key, title, icon, gear tier, ore tiers unlocked in this chapter, subtitle)
AGES = [
    ("forged_ascent_1_stone", "Stone Age", "minecraft:stone_pickaxe", 3, [1, 2, 3],
     "Tiers 1-3: stone, copper/tin/zinc, then iron"),
    ("forged_ascent_2_bronze", "Bronze Age", f"{NS}:brass_pickaxe", 4, [4], "Tier 4: the first alloys"),
    ("forged_ascent_3_steel", "Steel Age", f"{NS}:cobalt_pickaxe", 5, [5], "Tier 5: steel, cobalt, diamonds"),
    ("forged_ascent_4_gem", "Gem Age", f"{NS}:emerald_pickaxe", 6, [6], "Tier 6: precious metals and gems"),
    ("forged_ascent_5_titanium", "Titanium Age", f"{NS}:titanium_pickaxe", 7, [7], "Tier 7: refractory metals"),
    ("forged_ascent_6_tungsten", "Tungsten Age", f"{NS}:tungsten_carbide_pickaxe", 8, [8], "Tier 8: superalloys"),
    ("forged_ascent_7_netherite", "Netherite Age", "minecraft:netherite_pickaxe", 9, [], "Tier 9: netherite"),
]
ANVIL_OF_TIER = {3: "stone", 4: "bronze", 5: "steel", 6: "gemstone", 7: "titanium", 8: "tungsten", 9: "netherite"}
WORLD_TIER_AFTER_GATE = {2: "Frontier", 3: "Ascent", 5: "Summit", 6: "Pinnacle"}
BOSS_TIPS = {
    "forgedascent:eye_of_cthulhu": ("Eye of Cthulhu", "It may find you on its own at night, or craft a Suspicious Looking Eye "
                                    "(6 spider eyes) and use it at night. It dashes at you: keep moving and hit it as it hovers. "
                                    "At half health it grows a maw and turns nasty."),
    "twilightforest:naga": ("Naga", "Twilight Forest: the stone courtyard in the forest. The easiest gate boss."),
    "aether:slider": ("Slider", "The Aether: Bronze Dungeon. Hit the sliding block with a pickaxe."),
    "minecraft:elder_guardian": ("Elder Guardian", "Ocean Monuments. Bring Water Breathing and milk."),
    "twilightforest:lich": ("Lich", "Twilight Forest: the Lich Tower."),
    "aether:valkyrie_queen": ("Valkyrie Queen", "The Aether: Silver Dungeon."),
    "undergarden:forgotten_guardian": ("Forgotten Guardian", "The Undergarden: deep in the Catacombs."),
    "irons_spellbooks:dead_king": ("Dead King", "Iron's Spells: the Dead King's crypt."),
    "twilightforest:minoshroom": ("Minoshroom", "Twilight Forest: bottom of the Labyrinth in the swamp."),
    "twilightforest:hydra": ("Hydra", "Twilight Forest: the Fire Swamp lair. Fire resistance helps."),
    "cataclysm:netherite_monstrosity": ("Netherite Monstrosity", "Cataclysm: the Soul Black Smith in the Nether."),
    "eternal_starlight:starlight_golem": ("Starlight Golem", "Eternal Starlight: the Golem Forge."),
    "minecraft:wither": ("Wither", "Build it from soul sand and wither skeleton skulls. Fight it underground."),
    "twilightforest:knight_phantom": ("Knight Phantoms", "Twilight Forest: the Stronghold (Dark Forest)."),
    "cataclysm:ender_guardian": ("Ender Guardian", "Cataclysm: the Ruined Citadel in the End."),
    "aether:sun_spirit": ("Sun Spirit", "The Aether: Gold Dungeon."),
    "minecraft:ender_dragon": ("Ender Dragon", "The End. Bring a bow and blocks."),
    "cataclysm:ignis": ("Ignis", "Cataclysm: the Burning Arena in the Nether."),
    "twilightforest:ur_ghast": ("Ur-Ghast", "Twilight Forest: the Dark Tower."),
    "cataclysm:the_leviathan": ("Leviathan", "Cataclysm: the Sunken City in deep oceans."),
    "minecraft:warden": ("Warden", "Ancient Cities in the Deep Dark."),
    "twilightforest:snow_queen": ("Snow Queen", "Twilight Forest: the Aurora Palace on the glacier."),
    "cataclysm:the_harbinger": ("Harbinger", "Cataclysm: the Wither Lab ruins."),
    "cataclysm:ancient_remnant": ("Ancient Remnant", "Cataclysm: the Cursed Pyramid in deserts."),
    "cataclysm:maledictus": ("Maledictus", "Cataclysm: the Frosted Prison in snowy biomes."),
    "cataclysm:scylla": ("Scylla", "Cataclysm: the Acropolis in the ocean."),
    "eternal_starlight:lunar_monstrosity": ("Lunar Monstrosity", "Eternal Starlight: the Cursed Garden."),
    "irons_spellbooks:fire_boss": ("Tyros", "Iron's Spells: the Ancient Fire Temple in the Nether."),
}


def pretty(item):
    return item.split(":")[1].replace("_", " ").title()


def alloys_by_tier():
    gear_tiers = {g["id"]: g["tier"] for g in ga.TABLE["gear"]}
    out = {}
    for name, parts, result, count, _ in ga.ALLOYS:
        tier = gear_tiers.get(name, EXTRA_ALLOY_TIERS.get(name, 3))
        ratio = " + ".join(f"{n} {m.replace('_', ' ')}" for m, n in parts)
        out.setdefault(tier, []).append((result, name.replace("_", " ").title(), f"{ratio} -> {count}"))
    out.setdefault(5, []).append(("alltheores:steel_ingot", "Steel", "1 iron + 2 coal -> 1"))
    out.setdefault(8, []).append((f"{NS}:tungsten_carbide_ingot", "Tungsten Carbide", "2 tungsten + 2 coal + 1 cobalt -> 2"))
    return out


def age_chapter(order, key, title, icon, tier, ore_tiers, subtitle, alloys, gates):
    ch = Chapter(key, order, title, icon, subtitle)
    gate_no = order + 1
    # 1. Arrival
    if order == 0:
        ch.quest("arrival", "Welcome to Forged Ascent", icon=f"{NS}:tin_pickaxe", size=1.5, shape="gear",
                 subtitle="Read me first", xp=50, rewards=[("alltheores:tin_ingot", 4)],
                 desc=["This world has a long gear ladder: &etiers 1 to 9&r. Every ore needs a pickaxe of its tier: "
                       "a &6stone&r pickaxe can't mine iron any more.",
                       "Tier 4+ gear is forged at &bSmithy Anvils&r. Each new anvil needs a &dSigil&r from a "
                       "&cboss gate&r, Terraria style. Follow these chapters in order.",
                       "Mobs grow stronger with your Apotheosis world tier, deep underground and in other "
                       "dimensions. Elites (Brutes, Runners, Dread...) appear more as you climb."])
    else:
        anvil = f"{NS}:{ANVIL_OF_TIER[tier]}_anvil"
        ch.quest("arrival", f"Forge the {pretty(anvil)}", item=anvil, size=1.5, shape="gear",
                 subtitle=f"Unlocks tier-{tier} gear", xp=150,
                 rewards=[(f"{NS}:reinforced_plate_{tier}", 1)],
                 desc=[f"Craft the &b{pretty(anvil)}&r: the previous anvil, your Sigil and tier-{min(tier, 8)} plates.",
                       f"It forges every recipe up to &etier {tier}&r (JEI: 'Smithy Anvil' tab), folds pattern-welded "
                       "metals, reinforces and repairs gear."])
    # 2. Mining
    for ore_tier in ore_tiers:
        for i, (item, name, where) in enumerate(ORES[ore_tier]):
            ch.quest(f"ore_{ore_tier}_{i}", f"Mine {name}", item=item, y=-1.0 if i % 2 == 0 else 1.0,
                     subtitle=f"Needs a tier-{ore_tier} pickaxe", desc=[where])
        if order == 0 and ore_tier < 3:
            nxt = ore_tier + 1
            ch.quest(f"pickaxe_{nxt}", f"A tier-{nxt} pickaxe", item=f"#{NS}:tier_gear/{nxt}/pickaxe",
                     icon={2: f"{NS}:tin_pickaxe", 3: "minecraft:iron_pickaxe"}[nxt], shape="square",
                     desc=[f"Any tier-{nxt} pickaxe opens the next ores." + (
                         " Copper, tin or zinc all work: pick the one whose stats you like." if nxt == 2 else
                         " Iron, lead, nickel, aluminum or pewter.")])
    # 3. Alloys
    for i, (item, name, ratio) in enumerate(alloys.get(tier, [])):
        ch.quest(f"alloy_{i}", f"Alloy: {name}", item=item, y=-1.0 if i % 2 == 0 else 1.0,
                 subtitle=ratio, desc=["Alloys are mixed in a crafting table. The ratio is the real-world one."])
    # 4. Pattern-welded metals
    folds = [i for i in ga.TABLE["ingots"] if i.get("pattern") and i["tier"] == tier]
    for i, fold in enumerate(folds):
        a, b = fold["folded_from"]
        ch.quest(f"fold_{i}", f"Fold {fold['name']}", item=f"{NS}:{fold['id']}_ingot", y=-1.0 if i % 2 == 0 else 1.0,
                 subtitle=f"{a.replace('_', ' ')} + {b.replace('_', ' ')}", shape="diamond",
                 desc=["At your anvil, lay 5 and 4 ingots in a checker pattern to fold a &dpattern-welded&r metal. "
                       "It's a slightly stronger Silent Gear material with a wavy look."])
    # 5. Plates and reinforcing
    ch.quest("plates", "Hammer plates", item=f"#c:plates", icon="alltheores:iron_plate" if order == 0 else None,
             desc=["Plates: All the Ores hammer + 2 ingots, the IE Metal Press, Create's press or the MI compressor."])
    ch.quest("reinforced_plate", f"Tier-{tier} reinforced plate", item=f"{NS}:reinforced_plate_{tier}",
             desc=["4 plates of a tier (2x2) make that tier's reinforced plate."])
    ch.quest("reinforce", "Reinforce your gear", check=True, icon=f"{NS}:reinforced_plate_{tier}",
             desc=["At an anvil: gear + reinforced plate -> &bReinforced I&r (+1 armor or damage, +25% durability).",
                   "You can go to &bII&r and &bIII&r: each needs a plate one grade higher than the last."])
    # 6. Gear up
    for kind, kind_icon in (("pickaxe", "pickaxe"), ("chestplate", "chestplate"), ("helmet", "helmet"),
                            ("leggings", "leggings"), ("boots", "boots"), ("sword", "sword")):
        ch.quest(f"gear_{kind}", f"Any tier-{tier} {kind}", item=f"#{NS}:tier_gear/{tier}/{kind}",
                 y=-1.0 if kind in ("pickaxe", "helmet", "boots") else 1.0, rewards=[("minecraft:experience_bottle", 2)],
                 desc=[f"Any tier-{tier} {kind} counts. Each material has its own small perk: check the tooltips."])
    # 7. Side branches (optional)
    spine = ch.last
    if order == 0:
        ch.quest("scavenged", "Scavenger's armor", item=f"#{NS}:tier_gear/1/chestplate", icon=f"{NS}:leaf_chestplate",
                 y=-2.5, deps=[spine], optional=True, step=False,
                 desc=["Leaf (camouflage), Bark, Flint (thorns), Bone, Chitin (no poison), Feather (no fall "
                       "damage), Shell (breathing), Slime (bouncy), Rotten (zombies ignore you). A full set doubles the perk."])
        ch.quest("stone_anvil", "Build a Stone Anvil", item=f"{NS}:stone_anvil", y=2.5, deps=[spine], optional=True,
                 step=False, desc=["Smooth stone and iron. It forges and reinforces tier 1-3 gear and Silent Gear "
                                   "parts, and it's the base of the Bronze Anvil."])
    if order == 0:
        ch.quest("eye_summon", "Suspicious Looking Eye", item=f"{NS}:suspicious_looking_eye", y=-4.0, deps=[spine],
                 optional=True, step=False,
                 desc=["Six spider eyes make one. Use it at night to call the &dEye of Cthulhu&r, a Gate I boss.",
                       "Once you beat it, it stops visiting on its own, but you can always call it again. "
                       "Servants of Cthulhu drop spider eyes."])
        ch.quest("demonite", "Demonite", item=f"{NS}:raw_demonite", y=4.0, deps=[spine], optional=True, step=False,
                 desc=["The Eye of Cthulhu drops raw Demonite. Smelt it into ingots. Demonite is a tier-4 metal with "
                       "its own armor perk: a little extra damage."])
    if order in (1, 2):
        wheel = f"{NS}:emery_wheel" if order == 1 else f"{NS}:diamond_grit_wheel"
        ch.quest("cutting", "Cut gems", item=wheel, y=-2.5, deps=[spine], optional=True, step=False,
                 desc=["Rough gem + cutting wheel in a crafting grid. Emery cuts up to hardness 8; diamond grit "
                       "(crushed rough diamonds) cuts everything. 6% of cuts also give a &bFlawless&r gem."])
    if order >= 1:
        ch.quest("silent_gear", f"Silent Gear at tier {tier}", check=True, icon="silentgear:pickaxe", y=2.5,
                 deps=[spine], optional=True, step=False,
                 desc=[f"Tier-{tier} materials make Silent Gear parts at your anvil (blueprint + materials). "
                       "See the Silent Gear Smithing chapter."])
    # 8. Prepare + 9. boss gate
    gate = gates[gate_no]
    ch.quest("prepare", f"Prepare for {gate['name']}", check=True, icon="minecraft:shield", shape="square",
             desc=["Before a gate boss: wear a full set of this tier, reinforce it, bring food and healing.",
                   "Gate bosses aren't scaled by world tier, but the mobs around them are."], deps=[spine])
    before = ch.last
    bx = ch.x
    for i, boss in enumerate(gate["bosses"]):
        bname, tip = BOSS_TIPS.get(boss, (pretty(boss), ""))
        ch.quest(f"boss_{i}", f"Defeat: {bname}", x=bx, y=-2.0 + i * 1.3, kill=boss, deps=[before],
                 subtitle=f"{gate['name']} boss", shape="hexagon", optional=True, step=False,
                 desc=[tip, "Any one boss of this gate is enough."])
    ch.x = bx + 1.75
    if gate_no <= 6:
        ch.quest("sigil", f"{gate['name']} Sigil", item=f"{NS}:sigil_{gate_no}", deps=[before], size=1.75,
                 shape="gear", subtitle="Beat any boss of the gate", xp=300,
                 desc=[f"Every {gate['name']} boss drops a &dTreasure Bag&r: this Sigil, tier materials, rough gems, "
                       "a reinforced plate and an accessory.", "Use the Sigil to forge the next Smithy Anvil."]
                 + ([f"It also unlocks the Apotheosis world tier &e{WORLD_TIER_AFTER_GATE[gate_no]}&r."]
                    if gate_no in WORLD_TIER_AFTER_GATE else []))
    else:
        ch.quest("final", "Conquer the Final Gate", check=True, deps=[before], size=1.75, shape="gear", xp=600,
                 desc=["Beat any final boss above for the Final Treasure Bag. Beyond this lies ATM's own "
                       "Allthemodium ladder."])
    ch.write()


def silent_gear_chapter(order):
    sg = Chapter("forged_ascent_8_silent_gear", order, "Silent Gear Smithing", "silentgear:pickaxe",
                 "Mix and match parts at your anvils")
    sg.quest("intro", "Silent Gear, the Forged Ascent way", check=True, size=1.5, shape="gear",
             icon="silentgear:pickaxe_blueprint", xp=50,
             desc=["Silent Gear builds tools from parts: a &ehead&r, a &erod&r (handle), and optional &etip&r, "
                   "&ebinding&r, &egrip&r and &ecoating&r.",
                   "No foundry: blueprint + materials in a grid. Tier 1-3 materials work in a crafting table; "
                   "&btier 4+ materials need a Smithy Anvil of that tier&r. Blueprints are kept.",
                   "Every Forged Ascent metal, alloy, pattern-welded metal and gem is a Silent Gear material."])
    sg.quest("blueprint", "Draw a blueprint", item="silentgear:pickaxe_blueprint",
             desc=["Blueprints are crafted; rarer ones (katana, mace, spear...) also turn up in chests."])
    sg.quest("head", "Forge a head", item="silentgear:pickaxe_head",
             desc=["Blueprint + 3 materials. Mixing materials mixes their stats and traits."])
    sg.quest("rod", "Make a handle", item="silentgear:rod",
             desc=["Every Forged Ascent metal makes rods. Light metals swing faster, heavy ones hit harder, tough "
                   "ones last longer, gem rods mine faster."])
    sg.quest("tool", "Assemble a tool", item="silentgear:pickaxe", desc=["Head + rod in a crafting table."])
    sg.quest("tip", "Tip it with a gem", item="silentgear:tip", y=-1.0,
             desc=["Gem tips add damage and durability: ruby, sapphire, topaz, black diamond..."])
    sg.quest("folded", "Pattern-welded parts", item=f"#{NS}:pattern_welded", y=1.0,
             desc=["Folded metals (Damascus Steel, Mokume-gane, Timascus...) are extra-sharp Silent Gear materials."])
    sg.quest("flawless", "Flawless tips", item=f"#{NS}:flawless_gems", rewards=[(f"{NS}:diamond_grit", 4)],
             desc=["6% of gem cuts also give a &bFlawless&r gem: the strongest tips and coatings."])
    sg.quest("coating", "Coat it in superalloy", item="silentgear:coating",
             desc=["Stellite, inconel, osmiridium, tungsten carbide and high-speed steel make coatings."])
    sg.quest("salvage", "Recycle loot", item="silentgear:salvager",
             desc=["The Salvager breaks gear (including Forged Ascent gear) back into materials."])
    sg.write()


def main():
    gates = {g["gate"]: g for g in ga.TABLE["gates"]}
    alloys = alloys_by_tier()
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for order, (key, title, icon, tier, ore_tiers, subtitle) in enumerate(AGES):
        age_chapter(order, key, title, icon, tier, ore_tiers, subtitle, alloys, gates)
    silent_gear_chapter(len(AGES))
    total = sum(1 for f in OUT.glob("*.snbt") for line in f.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith("title:"))
    print(f"Wrote {len(AGES) + 1} chapters ({total} titled entries) to {OUT}")


if __name__ == "__main__":
    main()
