# Project Plan: Custom ATM10 Progression Overhaul (v3)

Status: **final draft, waiting for go-ahead.** Built from the Phase 0 scan
([`docs/PACK_SCAN.md`](docs/PACK_SCAN.md)) and the planning conversation of
2026-10-03. All numbers are first guesses, tuned by playtesting. Items marked
*(verify)* are checked in game or in code before they're built.

## Decisions

| Question | Answer |
|---|---|
| Modpack | All the Mods 10 **10.8.2**, Minecraft **1.21.1**, NeoForge **21.1.251** |
| Play mode | **Single player only**, Windows 11, CurseForge |
| Profile Claude edits | **`Claude`** (copy). The main ATM10 profile is never touched |
| Pack updates | Never. Existing mods can be changed freely |
| Uranium | Leave alone |
| Mod name | **Forged Ascent** (id `forgedascent`) |
| Models | Flat item icons, simple block models, mobs reuse vanilla bodies (recolored/scaled). No new 3D mob models |
| Reinforced gear | **Smithing upgrade on the existing item**, stats only, never raises mining tier |
| Gems | **In**, with hardness-based tiers and a Lapidary Bench cutting system |
| Elite Essence | **No** |
| Way of working | **Live:** player plays the `Claude` profile, asks for changes, Claude rebuilds and updates it |

## Update 5 plan (agreed 2026-10-03, in progress: player still reviewing)

| Yes | No |
|---|---|
| **Quest fixes:** gear quests accept any item of the tier ("any tier-5 sword") via FTB Filter System smart filters on item tags like `forgedascent:tier_gear/5/swords`; check the "Forged Ascent" group shows as its own category | Prospector's Pick |
| **Scavenged early armors** (weaker than copper, some about equal; one perk each, doubled with a full set): Leaf (camouflage), Bark (knockback resist, fire weakness), Flint (thorns-like), Bone (skeletons notice later, bonus vs undead), Chitin (cobweb immunity, climbing, poison resist), Feather (no fall damage to 8 blocks), Shell (breath + swim speed), Slime (less fall damage, higher jump), Rotten (zombies ignore you until hit, costs hunger) | |
| **Distinct perk for every metal/gem set**, small like the current traits (e.g. aluminum +2.5% speed per piece). Every set gets its own unique thing; nothing overpowered | |

**Silent Gear integration (agreed):**
- Cause of the foundry requirement: the add-on **Silent Gear Metalworks** tags metals as "casting" and overrides Silent Gear's 68
  part recipes (`data/silentgear/recipe/gear/*`) with `"not_categories": ["casting"]`, so metal heads must be cast in the
  Productive Metalworks foundry. Fix pack-side (KubeJS data overrides): allow metals again. Foundry stays as an optional route.
- **Blueprint + ingots works without the foundry.** Tier 1–3 materials: crafting table *and* anvils. Tier 4+ materials: only at a
  Smithy Anvil of at least that tier (anvil checks the material's tier on the crafted part). Idea for the crafting-table limit:
  give each material a tier category and make the table recipes require low-tier categories.
- **New Stone Anvil (tier 3)**, no boss needed, craftable early (also reinforces early gear).
- **Rebalance all ~60 Silent Gear materials** (incl. Silent's Gems ones) onto our curve: attack = tier sword bonus, armor =
  tier set totals, durability like our gear, `harvest_tier` → `forgedascent:incorrect_for_tier_N`. Silent Gear's diamond is still
  vanilla (+3 attack, 20 armor, 1561 durability). Unique SG materials (crimson steel, azure electrum, tyrian steel, blaze gold...) get a tier.
- **Add all our metals, alloys and gems as Silent Gear materials** (stats from `materials.json`, fitting SG traits, SG tints its own textures).
- Gear assembly (head + rod) stays a normal crafting-table step.
- **Silent Gear parts per material:** heads = all metals/alloys/cut gems; rods = light/strong metals (aluminum, duralumin,
  titanium, chromoly, titanium alloy, steel...); tips = gems (ruby +damage, sapphire +durability, topaz +speed, black diamond);
  bindings/grips = scavenged materials (chitin, bone, bark...); coatings = late alloys (stellite, inconel, osmiridium).
  Silent Gear's own weapon types and shields then cover weapon variety.

**Also in update 5 (agreed):**
- **Flawless gems:** gem cutting has a rare Flawless result; flawless gems are stronger Silent Gear tips/coatings (this replaces "inlays")
- **Silent Gear Smithing chapter** inside the Forged Ascent quest tab (blueprints, parts, handles, tips, which anvil per tier)
- **Anvil repair with ingots:** gear + ingots of its material repairs it at a Smithy Anvil

- **Silent Gear loot (conditional):** legendary Silent Gear items in Treasure Bags (rare, named, strong trait, e.g. "Hydra's
  Fang": cobalt katana, ruby tip, chitin binding) **and** Silent Gear weapons in chests (Lootr), materials scaling with world
  tier. **Verify on the test server that generated tools have real parts and stats; if not, drop both.**
- **Salvaging:** Silent Gear Salvager recipes for our gear, scavenged armors and vanilla tier gear (recycle loot into materials)
- **Smith's journal quests:** "craft a tool from 3 different materials", "make a gem-tipped weapon", "reinforce a Silent Gear tool"

**Update 6 candidates:** blueprints as treasure (fancy weapon types found in loot), whetstones/gem oils, weapon types gated by
anvil tier, elite part drops, armor trims from our metals, Elite Hunter quest chain, gate maps, ruined forges.
Later (needs research): flawless gems auto-graded S in Silent Gear's grader, Bounty Board hooks.
Rejected: Prospector's Pick.

## Update 4 design (agreed 2026-10-03, overrides older sections where they differ)

Player's yes/no list:

| Yes | No |
|---|---|
| Gear curve (ours + vanilla iron/diamond/netherite) + mob trim (Summit health ×4, Pinnacle ×5) | Foundry / molten metals |
| Other mods' gear boosted to the curve by tier | Tier tooltips / colored names |
| Spawn eggs for the 42 elites | Elite abilities |
| Plates (made with other mods' hammers/presses) → reinforced gear (stats only) | Heart Canister integration, smithing ranks |
| Tiered anvils, each crafted with a boss Sigil | Locked dimensions, NPCs/traders, boss summons, Hardmode flag, boss-only bars, re-fighting bosses |
| Boss Sigils + Treasure Bags with Artifacts/Relics accessories | Machine yield bonuses, Tier Trials, Elite Trophies, side-material jobs, web spiders |
| **Quest book** ("Forged Ascent" chapters, the player's main progression guide) | |
| Blood moon with digging mobs | |
| Later: flawless gems + inlays | |

### Gear curve (full set armor / sword damage; Apothic Attributes armor: damage taken = 10/(10+armor))

| Tier | 2 | 3 (iron) | 4 | 5 | 6 (diamond) | 7 | 8 | 9 (netherite) |
|---|---|---|---|---|---|---|---|---|
| Armor | 10 | 14 | 18 | 23 | 29 | 36 | 45 | 52 |
| Sword damage | 6 | 7 | 9 | 10.5 | 13 | 18 | 24 | 26 |

Materials keep their personality as offsets around the curve. Other mods' gear: tools get the tier's damage (tier from the blocks
the tool can't mine), armor scaled to the tier's total (explicit tiers for Mekanism/IE/Everything is Copper/Ice and Fire, heuristic for the rest).

### Anvils (Terraria-style gates). Tier 1–3 gear stays in the crafting table.

| Anvil | Crafted from | Crafts gear tier ≤ |
|---|---|---|
| Bronze | Gate I Sigil + tier-4 plates | 4 |
| Steel | Bronze Anvil + Gate II Sigil + tier-5 plates | 5 |
| Gemstone | Steel Anvil + Gate III Sigil + tier-6 plates/gems | 6 |
| Titanium | Gemstone Anvil + Gate IV Sigil + tier-7 plates | 7 |
| Tungsten | Titanium Anvil + Gate V Sigil + tier-8 plates | 8 |
| Netherite | Tungsten Anvil + Gate VI Sigil + netherite | 9 |

Anvils open a 3x3 crafting screen with their own recipe type (tier field). Anvils drop themselves. Our tier 4+ gear,
vanilla diamond/netherite gear (netherite upgrade moves here) and major mods' tier 4+ gear (Mekanism Tools, IE steel) move onto anvils.
Reinforcing happens at an anvil: gear + reinforced plate (tier ≥ gear tier) → same gear, +1 armor per piece or +1 damage, +25% durability.

### Boss gates (bosses are NOT scaled by world tier). Any one boss of a gate drops that gate's Treasure Bag (Sigil + tier materials + rough gems + accessory).

| Gate | Unlocks anvil | Bosses |
|---|---|---|
| I | Bronze (t4) | Naga, Slider, Elder Guardian |
| II | Steel (t5) | Lich, Valkyrie Queen, Forgotten Guardian, Dead King |
| III | Gemstone (t6) | Minoshroom, Hydra, Netherite Monstrosity, Starlight Golem |
| IV | Titanium (t7) | Wither, Knight Phantoms, Ender Guardian, Sun Spirit |
| V | Tungsten (t8) | Ender Dragon, Ignis, Ur-Ghast, Leviathan, Warden |
| VI | Netherite (t9) | Snow Queen, Harbinger, Ancient Remnant, Maledictus |
| Final | — | Scylla, Lunar Monstrosity, Tyros (fire boss) |

Apotheosis world tiers follow gates: Frontier after II, Ascent after III, Summit after V, Pinnacle after VI.

### Blood moon
- Starts after Gate I is cleared; 1 in 8 nights; warning at dusk; red fog (red sky if possible); no sleeping
- 2× monster spawns (skipped when many monsters are already near the player, for lag), +15% elite chance, better drops
- **Digging:** zombies, husks, Brutes (any base) and Dread elites that can't reach their target break blocks toward it, with crack animation.
  They can break **everything except obsidian-tier blocks** (hardness ≥ 50, unbreakable, siege-proof tag) and **never** blocks with
  block entities (chests, machines, storage). Max ~6 diggers at once, ~150 blocks per night
- **Damage is permanent** (player's final choice): broken blocks drop as items. Config switch to restore them at dawn instead.
  Blocks with block entities (machines, chests, storage) are still never broken

### Quest book
New FTB Quests chapter group "Forged Ascent", one chapter per age (Stone, Bronze, Steel, Gem, Titanium, Tungsten, Netherite),
each: mine new ores → craft gear/plates → prepare (reinforce, cut gems, reforge) → boss gate (kill task per boss option, with how-to-find notes)
→ Sigil → next anvil. New files only; ATM's chapters are not edited (backup first). ATM10 uses split lang files under `quests/lang/en_us/`.

## Scope changes (agreed 2026-10-03, override the sections below)

| Topic | Change |
|---|---|
| Alloys | **Temporary: shapeless crafting-table recipes** (same ratios as section 4). No Alloy Forge / Blast Alloy Forge for now. "Blast-only" smelting of titanium/chromium/tungsten is dropped until a real alloying system is chosen |
| Gem cutting | **Very basic system**, no GUI and no Automatic Lapidary. Gems are **not in Phase 1** |
| Elites | **Stay as distinct mob types** (own names, recolored/scaled vanilla bodies) |
| New ores | **Plain veins first** (ordinary ore blobs in rock, with biome/dimension/depth rules). Ocean nodules and beach black sand come later |
| Deferred | Blood moon, web-shooting spiders, inlays, synthetic gems, PCD, special (non-stat) traits |
| Mod name | **Forged Ascent** (id `forgedascent`) |

### Phase 1 contents

Mod setup + gear-set generator, tier system + tier tags, ore gating for existing ores,
iron/diamond/osmium nerfs, gear sets for **tin, zinc, lead, nickel, aluminum, pewter,
brass, invar, constantan** (stat traits only), crafting-table alloy recipes, re-tier
copper (Everything is Copper) and Mekanism bronze/steel/osmium. Test in game before Phase 2.

---

## 1. How tiers work

- **Mining tier:** every ore has a tier number. A pickaxe mines an ore if its tier
  is at least that number. Tier N ore → tier N+1 gear → mines tier N+1 ore.
- **Tier tags ("any wood makes a chest"):** every tier has a tag listing all its
  ingots, gems and plates. Progression recipes take *any* item from the tier's tag, so
  any material in a tier keeps you moving. The material only changes stats and trait.
- **Personalities:** same-tier materials have similar total strength, with different trade-offs (traits).
- **Existing gear:** tools from other mods follow their vanilla tier (iron → 3, diamond → 6,
  netherite → 9). Gear we place on a rung (Everything is Copper, Mekanism bronze/steel/osmium,
  Ice and Fire silver) gets its tier tags edited one by one.
- **Same tier in every stone:** stone, deepslate, nether and end versions of an ore need the
  same tier, done through the common tags (`c:ores/<name>`).

## 2. The full ladder

Legend: ✅ exists in pack · 🆕 we add · 🔧 existing, changed · *(side)* off the main line

| Tier | Metal gear | Gem gear | Pickaxe newly mines |
|---|---|---|---|
| 0 | Wood ✅ | — | Stone, coal, salt, sulfur |
| 1 | Stone ✅ | — | Copper, tin, zinc, **bismuth** 🆕 |
| 2 | Copper ✅ (Everything is Copper), Tin 🆕, Zinc 🆕 | — | Iron, lead, nickel, aluminum, nether quartz |
| 3 | Iron 🔧, Lead 🆕, Nickel 🆕, Aluminum 🆕, Pewter 🆕, Lapis ✅ *(side)* | — | Gold, silver, redstone, lapis, fluorite, cinnabar, **manganese** 🆕, soft gems, amethyst |
| 4 | Bronze ✅, Brass 🆕, Bismuth bronze 🆕, Invar 🆕, Constantan 🆕, Duralumin 🆕, Silver ✅, Gold ✅ *(side)*, Electrum 🆕 *(side)*, Rose gold 🆕 *(side)* | Amethyst 🆕 | **Cobalt** 🆕, osmium 🔧, antimony, emerald, **molybdenum** 🆕, jade, garnet, peridot, iolite, tanzanite |
| 5 | Steel ✅, Cobalt 🆕, Osmium 🔧, Manganese steel 🆕, Alnico 🆕 *(side)* | Jade 🆕, Garnet 🆕, Peridot 🆕 | Diamond 🔧, platinum, monazite, **vanadium** 🆕, emerald-family, topaz |
| 6 | Platinum 🆕, Vanadium steel 🆕, Refined glowstone ✅, White gold 🆕 *(side)* | Diamond 🔧, Emerald 🆕, Topaz 🆕 | **Titanium** 🆕, **chromium** 🆕, ruby, sapphire, alexandrite |
| 7 | Titanium 🆕, Chromium 🆕, Stainless steel 🆕, Chromoly 🆕, Titanium alloy 🆕 | Ruby 🆕, Sapphire 🆕, Alexandrite 🆕 | Tungsten, iridium, black diamond |
| 8 | Tungsten 🆕, Tungsten carbide 🆕, High-speed steel 🆕, Stellite 🆕, Inconel 🆕, Iridium 🆕, Osmiridium 🆕, PCD 🆕, Refined obsidian ✅ | Black diamond 🆕 | Ancient debris |
| 9 | Netherite 🔧 (upgrade also needs a tier-8 alloy) | — | ATM ores (allthemodium etc.) |
| 10+ | Allthemodium → vibranium → unobtainium ✅ (unchanged) | — | — |

Other dimensions' gear (Twilight Forest, Aether, Undergarden, Eternal Starlight,
Ice and Fire dragon gear, Mystical Agriculture...) keeps its vanilla-matched tier.
Fixing individual ones is later polish.

### Stat curve (per-tier average, first guesses)

| Tier | Tool durability | Mining speed | Bonus attack | Armor (set) | Toughness (set) |
|---|---|---|---|---|---|
| 1 | 131 | 4 | +1 | — | — |
| 2 | 180 | 5 | +1.5 | 11 | 0 |
| 3 | 250 | 6 | +2 | 13 (iron nerfed from 15) | 0 |
| 4 | 400 | 6.5 | +2.5 | 15 | 0 |
| 5 | 650 | 7 | +3 | 16 | 2 |
| 6 | 1000 | 8 | +3 | 18 (diamond nerfed from 20) | 4 (diamond nerfed from 8) |
| 7 | 1400 | 8.5 | +3.5 | 19 | 6 |
| 8 | 1800 | 9 | +4 | 20 | 9 |
| 9 | 2031 | 9 | +4 | 20 | 12 |

### Traits

| Material | Trait |
|---|---|
| Tin | Cheap, light, low durability |
| Zinc | High durability for the tier, slower |
| Copper | Everything is Copper's oxidation, as-is |
| Iron | Baseline |
| Lead | Heavy: knockback resistance + armor, slower movement |
| Nickel | Slightly better durability than iron |
| Aluminum | Light: movement-speed bonus, low armor |
| Pewter | Cheap, enchantable |
| Bronze | Durable all-rounder |
| Brass | Faster mining, less durability |
| Bismuth bronze | Tougher bronze |
| Invar | Very durable, slow |
| Constantan | Less fire/lava damage |
| Duralumin | Light: speed bonus |
| Silver | Bonus damage vs undead |
| Gold *(side)* | Very fast, very enchantable, fragile |
| Electrum *(side)* | Top early enchantability, low durability |
| Rose gold *(side)* | Luck / looting bonus |
| Steel | Durable all-rounder |
| Cobalt | Fastest mining of its tier |
| Osmium | Heavy hitter, slow (nerfed) |
| Manganese steel | Huge durability, armor knockback resistance |
| Alnico *(side)* | Magnetic: nearby item drops fly to you |
| Platinum | Very enchantable |
| Vanadium steel | Strong all-rounder |
| White gold *(side)* | Highest enchantability |
| Titanium | Armor with no speed penalty |
| Chromium | Armor toughness |
| Stainless steel | Very high durability |
| Chromoly | Light and strong |
| Titanium alloy | Light, strong, no slowdown |
| Tungsten | Huge damage, slow, knockback resistance |
| Tungsten carbide | Best pickaxe material among metals |
| High-speed steel | Fastest mining |
| Stellite | Barely wears down |
| Inconel | Full set: fire and lava immunity |
| Iridium | Toughest armor, slow to wear |
| Osmiridium | Mining speed + durability |
| PCD | Ultimate pickaxe (tools only) |
| Amethyst | Enchantable early gem |
| Jade | Durability king of its tier |
| Garnet | More damage |
| Peridot | More durability |
| Diamond | Balanced |
| Emerald | Enchantable, villager-themed luck |
| Topaz | Mining speed |
| Ruby | More damage |
| Sapphire | More armor |
| Alexandrite | Different bonuses by day and by night |
| Black diamond | Toughest gem gear |

---

## 3. Ores

### Carried over (already spawn: we change tier/rarity only)

| Ore | From | Mining tier | Change |
|---|---|---|---|
| Coal, salt, sulfur | Vanilla / ATO | 0 | — |
| Copper | Vanilla | 1 | Tier |
| Tin, zinc | All the Ores | 1 | Tier |
| Iron | Vanilla | 2 | Tier (was stone-level) |
| Lead, nickel, aluminum | All the Ores | 2 | Tier |
| Nether quartz | Vanilla | 2 | — |
| Gold, redstone, lapis | Vanilla | 3 | — |
| Silver, fluorite, cinnabar | All the Ores | 3 | — |
| Osmium | All the Ores | 4 | **Rarer veins, no raw osmium blocks in veins** |
| Antimony | Modern Industrialization | 4 | — |
| Emerald | Vanilla | 4 | Drops rough emerald |
| Diamond | Vanilla | 5 | **Drops rough diamond**, less in chest loot |
| Platinum | All the Ores | 5 | — |
| Monazite | Modern Industrialization | 5 | — |
| Ruby, sapphire, peridot | All the Ores | per gem table | Drop rough gems |
| Silent's Gems ores | Silent's Gems *(verify they spawn)* | per gem table | Drop rough gems |
| Tungsten | Modern Industrialization | 7 | Smelts only in the Blast Alloy Forge |
| Iridium | All the Ores | 7 | — |
| Ancient debris | Vanilla | 8 | — |
| Uranium | All the Ores | — | **Don't touch** |

### New ores 🆕

| Ore | Real mineral | Where it spawns | Mining tier | Notes |
|---|---|---|---|---|
| Bismuth | Bismuthinite | Shallow stone, near copper | 1 | Ingredient (bismuth bronze) |
| Manganese | Pyrolusite + manganese nodules | Stone, **plus nodules on the deep ocean floor** | 3 | Ingredient (duralumin, manganese steel) |
| Cobalt | Cobaltite | **Nether** (common) + deep deepslate (rare) | 4 | Gear + ingredient |
| Molybdenum | Molybdenite | **Mountain** biomes, near copper | 4 | Ingredient (chromoly, high-speed steel) |
| Vanadium | Vanadinite | **Desert and badlands** | 5 | Ingredient (vanadium steel, titanium alloy) |
| Titanium | Rutile + **black sand** | Deep deepslate, **plus black sand on beaches** | 6 | Smelts only in the Blast Alloy Forge |
| Chromium | Chromite | Deep deepslate + Nether basalt deltas | 6 | Smelts only in the Blast Alloy Forge |

Each new ore comes with: ore + deepslate ore (plus the special forms above), raw item,
raw block, ingot, nugget, plate, storage block, and common tags. We reuse MI's titanium,
chromium and tungsten ingots instead of making duplicates, if Almost Unified allows *(verify)*.

**Ingredient-only metals** (no gear set): bismuth, manganese, molybdenum, vanadium.

---

## 4. Alloys

| Tier | Alloy | Recipe (ingots) | Output | Forge |
|---|---|---|---|---|
| 3 | Pewter 🆕 | 3 tin + 1 lead | 4 | Alloy Forge |
| 4 | Bronze | 3 copper + 1 tin | 4 | Alloy Forge |
| 4 | Brass | 3 copper + 1 zinc | 4 | Alloy Forge |
| 4 | Bismuth bronze 🆕 | 2 copper + 1 tin + 1 bismuth | 4 | Alloy Forge |
| 4 | Invar | 2 iron + 1 nickel | 3 | Alloy Forge |
| 4 | Constantan | 1 copper + 1 nickel | 2 | Alloy Forge |
| 4 | Duralumin 🆕 | 3 aluminum + 1 copper + 1 manganese | 5 | Alloy Forge |
| 4 *(side)* | Electrum | 1 gold + 1 silver | 2 | Alloy Forge |
| 4 *(side)* | Rose gold 🆕 | 3 gold + 1 copper | 4 | Alloy Forge |
| 5 | Steel | 1 iron + 2 coal/coke | 1 | Alloy Forge |
| 5 | Manganese steel 🆕 | 3 steel + 1 manganese | 4 | Alloy Forge |
| 5 *(side)* | Alnico 🆕 | 1 aluminum + 1 nickel + 1 cobalt | 3 | Alloy Forge |
| 6 | Vanadium steel 🆕 | 3 steel + 1 vanadium | 4 | Alloy Forge |
| 6 *(side)* | White gold 🆕 | 3 gold + 1 platinum | 4 | Alloy Forge |
| 7 | Stainless steel | 4 steel + 1 chromium + 1 nickel | 6 | Blast Alloy Forge |
| 7 | Chromoly 🆕 | 4 steel + 1 chromium + 1 molybdenum | 6 | Blast Alloy Forge |
| 7 | Titanium alloy 🆕 | 4 titanium + 1 aluminum + 1 vanadium | 6 | Blast Alloy Forge |
| 8 | Tungsten carbide 🆕 | 2 tungsten + 2 coke + 1 cobalt | 2 | Blast Alloy Forge |
| 8 | High-speed steel 🆕 | 4 steel + 1 tungsten + 1 molybdenum + 1 chromium | 6 | Blast Alloy Forge |
| 8 | Stellite 🆕 | 2 cobalt + 1 chromium + 1 tungsten | 4 | Blast Alloy Forge |
| 8 | Inconel 🆕 | 3 nickel + 1 chromium + 1 iron | 5 | Blast Alloy Forge |
| 8 | Osmiridium 🆕 | 1 osmium + 1 iridium | 2 | Blast Alloy Forge |
| 8 | PCD 🆕 | 4 diamond grit + 1 cobalt | 1 | Blast Alloy Forge |
| — | Nichrome 🆕 | 4 nickel + 1 chromium | 5 | Alloy Forge → crafting part for the Blast Alloy Forge |

Other mods' alloy recipes (Create, Mekanism, MI, IE) stay as the automated routes.

### Forges 🆕

| Block | Made from | Makes | Notes |
|---|---|---|---|
| **Alloy Forge** | Bricks + any tier-3 metal | Tier 3–6 alloys | 2–3 inputs + fuel, burns furnace fuel |
| **Blast Alloy Forge** | Upgrade the Alloy Forge: nichrome coils + any 4 tier-6 ingots + blaze rods | Everything, plus tier 7–8 alloys and smelting titanium/chromium/tungsten | Faster |

---

## 5. Gems

### Gem roster and tiers (by real hardness, Mohs scale)

| Gem | Hardness | Ore mining tier | Role |
|---|---|---|---|
| Pearl, ammolite, turquoise, opal, moldavite, lapis, fluorite | 2.5–6 | 3 | Inlay only |
| Kyanite | 4.5 / 7 | 3 | Inlay only |
| **Amethyst** (+ citrine, rose quartz, carnelian count as quartz family) | 7 | 3 | **Tier-4 gear** (amethyst) |
| **Jade** | 6–7, very tough | 4 | **Tier-5 gear** |
| **Garnet**, **peridot** | 6.5–7.5 | 4 | **Tier-5 gear** |
| Iolite, tanzanite | 6.5–7.5 | 4 | Inlay only |
| **Emerald** (+ aquamarine, heliodor = beryl family) | 7.5–8 | 4–5 | **Tier-6 gear** (emerald). Aquamarine/heliodor are inlays |
| **Topaz** | 8 | 5 | **Tier-6 gear** |
| **Diamond** (+ white diamond) | 10 | 5 | **Tier-6 gear**. Stays at 6 because ~100 other mods' tools are tied to diamond. Hardest to cut |
| **Alexandrite** | 8.5 | 6 | **Tier-7 gear** |
| **Ruby**, **sapphire** | 9 | 6 | **Tier-7 gear** |
| **Black diamond** (carbonado) | 10, tougher than diamond | 7 | **Tier-8 gear** |

11 gem gear sets. Tech gems (certus quartz, fluix, black quartz, xychorium) and
dimension gems stay as they are.

### Gem cutting

1. Gem ores drop **rough gems**. Fortune gives more rough gems.
2. **Lapidary Bench** 🆕: rough gem + **cutting wheel** → cut gem:

   | Wheel | Cuts up to hardness |
   |---|---|
   | Sandstone wheel | 6 |
   | Emery wheel (corundum abrasive) | 8 |
   | Diamond-grit wheel | 10 |

3. Every cut rolls a result: **Shattered** (→ gem dust), **Clean** (→ the normal gem item
   every mod uses), or **Flawless** (rare). Odds improve the harder the wheel is than the gem.
   Wheels have durability.
4. **Inlays:** at a smithing table, put one flawless gem into any tool or armor for a bonus
   by gem: ruby +damage, sapphire +armor, opal +enchant power, pearl water breathing,
   turquoise luck, etc. One inlay per item.
5. **Automatic Lapidary** 🆕 (tier 7): a machine that cuts gems automatically.
6. **Heat treatment:** amethyst in a furnace → citrine.
7. **Synthetic gems** (Blast Alloy Forge): gem dust + aluminum + trace metal → rough gem.
   Ruby = + chromium, sapphire = + iron and titanium, emerald = beryl dust + chromium or vanadium.
8. **Diamond grit:** from shattered diamonds. Used for diamond-grit wheels and PCD.

New items per gem: rough gem, flawless gem (and gem dust where missing).

---

## 6. Reinforced gear

- 4 plates of a tier (any material in that tier's tag) → 1 reinforced plate
- Smithing table: tool/armor + reinforced plate → same item, marked **Reinforced**:
  +1 armor per piece, +1 attack damage, +25% durability. Keeps enchantments
- Works on any gear, including other mods'. Stats only

---

## 7. Closing loopholes

**Nerfs:**
- **Diamond:** ore needs tier 5, drops rough diamonds that must be cut, gear stats lowered to tier 6, less in chests
- **Osmium:** rarer, no raw osmium blocks in veins, Mekanism osmium tool stats lowered (Mekanism Tools config)
- **Iron:** armor 15 → 13
- **Netherite:** upgrade also needs a tier-8 alloy ingot

**Tier-less mining:** recipes gated using the tier tags:

| Tier needed | Machines / tools |
|---|---|
| 4 | Create Mechanical Drill, PneumaticCraft jackhammer, Actually Additions AIOTs |
| 5 | Mining Gadgets (tier 1), IE drill, MI steam mining drill, Actually Additions drill, Oritech hand drill, ATM mining dimension portal |
| 6 | IE excavator, MI quarries, Steve's Carts drills, QuarryPlus / Additional Enchanted Miner, Building Gadgets destruction |
| 7 | Mekanism Atomic Disassembler + Digital Miner, RFTools Builder quarry, Oritech deep drill, MI electric drill |
| 8 | Meka-Tool, IF laser drill, Extended Industrialization laser drill, Draconic tools |

"Ore from nothing" systems (Mystical Agriculture, ore bees, Hostile Neural Networks,
Occultism miners) are **not** gated unless they turn out to skip the ladder in play.
Quests are ignored for now.

---

## 8. Mobs

### World tiers (Apotheosis)

Haven → Frontier → Ascent → Summit → Pinnacle. Unlocks are changed to need our gear tiers:

| World tier | Unlock needs |
|---|---|
| Frontier | Tier 4 gear |
| Ascent | Tier 6 gear |
| Summit | Tier 7 gear |
| Pinnacle | Tier 8 gear |

You can still pick a lower tier any time.

### Base scaling

Difficulty mostly comes from **health and damage**. Assumes **Hard** difficulty.

| World tier | Health | Damage | Mobs with some armor |
|---|---|---|---|
| Haven | ×1.5 | ×1.3 | 0% |
| Frontier | ×2 | ×1.5 | 10% |
| Ascent | ×3 | ×1.8 | 20% |
| Summit | ×4.5 | ×2.2 | 25% |
| Pinnacle | ×6 | ×2.8 | 33% |

Armor comes from the tier ladder that fits the world tier. Small drop chance.

### Danger by place (stacks with world tier)

| Where | Health / damage | Extra elite chance |
|---|---|---|
| Surface | — | — |
| Deepslate layer (below y=0) | +25% | +15% |
| Deep (below y=−32) | +50% | +20% |
| Nether | +40% | +20% |
| End and late dimensions | +75% | +25% |

Also: bigger groups underground at higher tiers (3–5 instead of 1), better skeleton aim at higher tiers.

### Elite spawn chance

| World tier | Base elite chance | New types unlocked |
|---|---|---|
| Haven | 5% | Runner, Brute |
| Frontier | 12% | — |
| Ascent | 20% | Armored, Molten, Frost, Venomous |
| Summit | 27% | — |
| Pinnacle | 35% | Dread |

Place bonuses are added on top, **capped at 50%**, so normal mobs are always the majority.
Normal mobs also get reskins: **Hardened** (Ascent+, darker, more health) and **Ancient**
(Pinnacle, pale/cracked, even more health).

### Elite types

| Elite | Look | Stats |
|---|---|---|
| Runner | Slimmer, lighter | Faster than normal, slower than a baby zombie. −25% damage, a bit less health |
| Brute | 25% bigger, darker | ×2 health, +50% damage, slower, knockback resistant |
| Armored | Grey | Always wears tier gear, high armor |
| Molten | Orange glow (Nether) | Sets you on fire |
| Frost | Icy blue (cold biomes) | Slows you |
| Venomous | Green (jungle/swamp) | Poisons |
| Dread | Glowing eyes, dark aura | ×4 health, ×2 damage, speeds up nearby mobs. Best drops |

**Which mobs:**
- **Full elite mobs (own mob types):** zombie (+ husk, drowned), skeleton (+ stray), spider (+ cave spider), wither skeleton, piglin, witch ("Coven": stronger potions)
- **Upgraded in place** (to keep Creeper Overhaul / Enderman Overhaul skins): creeper (Runner = short fuse, Brute = bigger blast, Dread = charged), enderman (stats only). Shown with a glow/particles
- **Illagers:** see below

### Illagers *(new)*

Pillagers, vindicators, evokers and ravagers come from outposts, patrols, raids,
mansions and structure mods (Illager Warship, When Dungeons Arise). Instead of
changing how they spawn, every illager gets **checked when it enters the world**,
whatever brought it in, and may be upgraded:

| Elite | Base | What it does |
|---|---|---|
| Marksman | Pillager | Faster reload, piercing bolts, longer range |
| Berserker | Vindicator | Brute stats, speeds up at low health |
| Archmage | Evoker | More vexes, faster fang attacks |
| Juggernaut | Ravager | Armored, knockback resistant |
| Captain upgrade | Patrol/raid captain | Leads with a Dread aura |

Raids scale with world tier: elite share rises, and an extra wave from Summit up. Raid
members are **upgraded in place** (not replaced) so raids keep working.

### Extras

- **Spider webs:** Venomous/Brute spiders (Ascent+) shoot a web projectile (flat sprite) that slows you or leaves a temporary cobweb
- **Blood moon** (Ascent+): rare night, chat warning, more and stronger spawns, no sleeping, red sky (fallback: red fog + red moon if shaders interfere)
- **Apotheosis invaders** get scaled by our system. No new bosses
- Torchmaster mega torches still stop spawns, so bases stay safe

---

## 9. Loot (Lootr-compatible)

Lootr gives each player a personal copy of a chest, rolled from the normal loot tables on
first open. Our mod **adds loot into chest loot tables** (vanilla + structure mods), based on
the world tier when the chest is first opened:

| World tier | Chest extras |
|---|---|
| Haven | Tier 1–3 ingots, raw ores, rough soft gems, sandstone wheels |
| Frontier | Tier 3–5 materials, rough gems, emery wheels, reinforced plates |
| Ascent | Tier 5–7 materials, rare flawless gems, the occasional tier-6 gear piece |
| Summit | Tier 6–8 materials, diamond-grit wheels, more flawless gems |
| Pinnacle | Tier 7–8 materials, black diamonds, the best flawless gems |

- Harder structures and dimensions give a bonus
- Diamonds and high-tier items reduced in early chests
- Apotheosis rolls affixes on our gear automatically
- Reading the world tier in code is *(verify)*. Fallback: track tier progress ourselves

---

## 10. Build order

| Phase | Work | Test in game |
|---|---|---|
| 0 ✅ | Setup, backup, pack scan | — |
| 1 | Mod skeleton, tier system + tier tags, **tin** end to end, re-tier copper and iron | Tin gear works, iron needs a tier-2 pickaxe |
| 2 | All metal gear sets + traits | Gear craftable, stats feel right |
| 3 | New ores + worldgen, all ore gating, diamond/osmium/iron nerfs | Can't skip tiers, new ores spawn |
| 4 | Alloy Forge, Blast Alloy Forge, all alloys | Alloying loop works |
| 5 | Gems: rough drops, Lapidary Bench, wheels, gem gear, heat treatment | Cutting feels fun, not tedious |
| 6 | Reinforcement, inlays, machine/tool recipe gating | Can't skip with drills/quarries |
| 7 | Mob scaling: world tier + place, armor, Hardened/Ancient reskins | Fights get harder per tier and depth |
| 8 | Elite mobs, illager elites, creeper/enderman upgrades | Elites feel distinct |
| 9 | Loot injection, world tier unlocks tied to gear | Chests feel rewarding per tier |
| 10 | Blood moon, web-shooting spiders, synthetic gems, Automatic Lapidary, polish | — |

## How it's built

| Part | Where |
|---|---|
| Items, blocks, ores, forges, lapidary, mobs, traits, scaling, blood moon | Our mod (`.jar`), Java |
| Tier tags, ore gating, recipes, worldgen, loot | Data inside our mod |
| Changing/removing other mods' recipes | KubeJS: `kubejs/server_scripts/zz_progression/` (copies in this repo) |
| Mekanism tool stats, ore rarity, Apotheosis settings | Config edits in the `Claude` profile (copies + notes in this repo) |

## Live workflow

1. Claude builds the mod and installs it into the `Claude` profile, backing up first.
2. The player plays, then asks for changes in plain words.
3. Recipe, loot and tag tweaks done through KubeJS/datapacks can often be reloaded in game
   (`/reload`). Code changes (new items, mobs) need a game restart.
4. New ores only appear in **chunks that haven't been generated yet**. Explore new areas, or use a new world.
5. **Removing** an item later deletes it from existing worlds, so removals are announced first.

## Known limits

- Textures are generated recolors. Simple but consistent
- ~36 gear sets and many mobs: built in batches, balanced by playtesting
- Claude can't see the game. Testing relies on descriptions, screenshots and logs
- Some other mods' tools or mobs may behave oddly. Fixed as found
