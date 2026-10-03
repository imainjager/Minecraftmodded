# Project Plan: Custom ATM10 Progression Overhaul

Status: **planning**. Nothing here is final. Details marked *(verify)* need to be
checked against the real ATM10 install before we build them.

## Goal

Play my own copy of All the Mods 10 (Minecraft 1.21.1, NeoForge) with:

1. A **longer, harder gear progression** where you mine ores, alloy them, and
   step up through many tool and armor tiers instead of jumping straight to diamond.
2. **Useful ores and ingots.** Most of the "useless" ingots in ATM10 (tin, lead,
   nickel, aluminum, zinc, iridium, invar, electrum, constantan, ...) get a
   place in the progression with their own tools and armor.
3. **Stronger mobs** that scale as the game goes on, building on Apotheosis world tiers.
4. **Tweaks to existing ATM10 mods** (configs, recipes, loot, ore rarity) so the
   new progression can't be skipped.

The pack copy will not be updated, so we can change existing mods freely.

## The pieces

| Piece | What it is | How it gets built |
|---|---|---|
| Custom mod (`.jar`) | New tiers, tools, armor, alloy forge, mob scaling | Java code (NeoForge 1.21.1) |
| Data changes | Which pickaxe mines which ore, recipes, loot tables | Tags/datapack inside our mod + KubeJS scripts |
| Config changes | Ore rarity, Mekanism tool stats, Apotheosis settings | Editing files in the instance's `config/` folder |

## 1. Harvest tier ladder (first draft)

Minecraft 1.21 decides what a pickaxe can mine using **block tags** (lists of
blocks). Our mod adds new tiers *between* the vanilla ones and puts ores into
the right lists. Tools from every other mod keep their vanilla tier, so they
automatically land at the matching rung without being changed one by one.

| Tier | Gear at this tier | Can now mine | Notes |
|---|---|---|---|
| 0 | Wood (tools + new wooden armor) | Stone, coal | |
| 1 | Stone | Copper, tin, zinc | |
| 2 | **Copper** (new tools + armor) | Iron, lead, aluminum, nickel | Vanilla 1.21.1 has no copper tools, so we add them *(verify none in pack)* |
| 3 | Iron (**nerfed**) | Gold, silver, redstone, lapis, **deepslate** | Iron sits where vanilla iron does |
| 4 | **Bronze / Brass** (alloys) | Deepslate ores, osmium?, cobalt? | Brass is a slight upgrade over bronze |
| 5 | **Steel** | Gems: ruby, sapphire, peridot, amethyst ore, **diamond** | Diamond becomes mid-tier |
| 6 | **Gem tier** (diamond, ruby, sapphire...) | Platinum, titanium, osmium | Vanilla diamond tools land here |
| 7 | **Titanium / Invar / Constantan** | Tungsten, iridium, chromium | |
| 8 | **Tungsten steel / Iridium** | Ancient debris | |
| 9 | Netherite | ATM end-game ores (Allthemodium etc.) | ATM's own end-game stays above us |

Uranium: **don't touch**.

Side materials that don't sit on the main ladder but get gear with special traits:
- **Electrum** (gold + silver): high enchantability, low durability
- **Lead**: heavy armor, high knockback resistance, slow
- More can be added later

## 2. Reinforced gear (the second path upward)

- Ingot → plate (All the Ores already has plates *(verify)*)
- 4 plates → 1 **reinforced plate**
- Reinforced plates craft **Reinforced [Material]** tools and armor:
  **+1 armor per piece, +1 attack damage, more durability**
- Open question: does reinforcing also raise the *mining* tier, or only stats?
  (Recommendation: stats only, so the ore gates still mean something.)

## 3. Alloying

- An **Alloy Forge** block from our mod: put in 2–3 ingredients and fuel, get an alloy.
  Simple, no tech-mod chains.
- Recipes: bronze (copper + tin), brass (copper + zinc), steel (iron + coal),
  invar (iron + nickel), constantan (copper + nickel), electrum (gold + silver),
  tungsten steel (tungsten + steel), and more later.
- Ingots that are currently stuck behind tech mods (titanium, chromium, tungsten
  from Modern Industrialization) get furnace/forge recipes so they're reachable
  without the tech mod.
- We reuse the pack's existing ingots through common tags (`c:ingots/tin`, etc.)
  instead of making duplicates. New ores only where something is missing.

## 4. Closing loopholes in the existing pack

- **Diamonds:** fewer in chest loot and harder to mine (tier 5)
- **Osmium (Mekanism):** rarer ore (Mekanism world config), needs tier 4–6 pickaxe,
  weaker tools (Mekanism Tools config)
- **Tier-less mining:** machines like Create drills, quarries, mining lasers
  and the Atomic Disassembler ignore pickaxe tiers. Gate their recipes behind
  the right tier materials
- **Silent Gear:** add our materials so it fits the same ladder (low priority)
- **Quests:** ATM10's quest book may point at items in the "old" order. Fine to ignore at first

## 5. Mob difficulty

- **Base buff** for all hostile mobs (more health, more damage, some armor). Numbers in a config file
- **Per-tier scaling:** much bigger jumps per Apotheosis world tier than Apotheosis
  gives now. Read the player's Apotheosis tier if possible *(verify API)*,
  otherwise track progress ourselves
- **Elite variants (later):** tougher versions of existing mobs that reuse vanilla
  models with new textures/size/glow/gear. These appear at higher tiers.
  Brand-new mob models are possible but come last (art is the hard part)

## 6. Build order

| Phase | Work | Test in game |
|---|---|---|
| 0 | Set up Claude Code on the PC, back up the instance, install Java 21, scan the pack's mod list, item IDs and configs | — |
| 1 | Mod skeleton + tier system + **one** material (copper) all the way through | Copper gear shows up and mining gates work |
| 2 | Full material table: tools + armor for every tier | All gear craftable, stats feel right |
| 3 | Ore gating tags, diamond/osmium nerfs, loot changes | Can't skip tiers |
| 4 | Alloy Forge + reinforced gear | Alloying loop is fun |
| 5 | Mob scaling | Fights feel harder per tier |
| 6 | Elite mobs, Silent Gear, polish | — |

## Known limits

- **Textures:** generated by recoloring template sprites per material. They'll look
  consistent but simple. They can be swapped for hand-drawn ones any time.
- **Balance needs playtesting:** first numbers will be guesses, then tuned from feedback.
- **Claude can't see the game:** testing relies on the player describing what happened,
  screenshots, and the game's log/crash files (`logs/latest.log`, `crash-reports/`).
- **ATM10 has 400+ mods:** some will have their own tools, ores or mining methods we
  have to find and slot in. Scanning the installed mod files helps catch these early.
