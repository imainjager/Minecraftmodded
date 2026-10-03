# Project Plan: Custom ATM10 Progression Overhaul (v2)

Status: **draft v2, waiting for player approval.** Built from the Phase 0 scan
([`docs/PACK_SCAN.md`](docs/PACK_SCAN.md)). Every number here is a first guess
and gets tuned by playtesting.

## Decisions so far

| Question | Answer |
|---|---|
| Modpack | All the Mods 10, version **10.8.2** |
| Minecraft / loader | **1.21.1**, **NeoForge** 21.1.251 |
| Single player or server | **Single player only** |
| Profile Claude works in | CurseForge profile **`Claude`** (copy). The main ATM10 profile is never touched |
| Reinforced gear | **Stats only** (does not raise mining tier) |
| Pack updates | Never: the copy is frozen, so existing mods can be changed freely |
| Uranium | Leave alone |
| Cobalt | **Wanted**: add it as a new ore |
| Breadth | **Several materials per tier**, each with its own strengths, so there are different routes up |

## Goal

1. A **long, wide gear ladder**: 10 tiers, 3–5 materials per tier, so you can
   climb through whatever you find instead of one fixed path.
2. **Every useful ingot gets a job**: tools, armor, an alloy, or a key recipe.
3. **No skipping**: ore gates, plus machines that ignore pickaxe tiers get
   locked behind the right tier.
4. **Stronger mobs** that scale with Apotheosis world tiers.

---

## 1. How tiers work (the idea behind everything)

**Mining tier.** Every ore gets a tier number. A pickaxe can mine an ore if its
tier is at least that number. Tier N ore → makes tier N+1 gear → which mines
tier N+1 ore.

**Different routes ("any wood makes a chest").** Each tier has a **tier
tag** such as `tier_metals/4` that lists every ingot or gem of that tier.
Progression recipes ask for *any* item from the tag, not one specific
metal. Examples:
- The Alloy Forge upgrade needs "any 4 tier-5 ingots".
- The Create Mechanical Drill needs "any tier-4 plate".
- Reinforced plates accept any tier's plates.

So if you found cobalt but no osmium, you still move up. Like planks for
a chest, the material changes the stats, not whether you can progress.

**Each material has a personality.** Materials in the same tier have about the
same overall strength but trade off differently (see **Traits** below). That's
what makes the routes feel different and not just recolors.

**Existing gear lands automatically.** Tools from other mods that copy a vanilla
tier (iron, diamond, netherite) get moved with that vanilla tier. Tools we put on
a specific rung (Mekanism bronze, steel and osmium; Everything is Copper; Ice and
Fire silver) get their tier tags edited one by one.

---

## 2. The tier ladder

**Legend:** ✅ = already in the pack, reused · 🆕 = we add it · 🔧 = existing, we change it

| Tier | Name | Gear made from | Pickaxe can newly mine |
|---|---|---|---|
| 0 | Wood | Wood ✅ (+ wooden armor 🆕, optional) | Stone, coal, salt, sulfur |
| 1 | Stone | Stone ✅, flint 🆕 (optional) | **Copper, tin, zinc** |
| 2 | **Soft metals** | Copper ✅ (Everything is Copper), **Tin** 🆕, **Zinc** 🆕 | **Iron, lead, nickel, aluminum**, nether quartz |
| 3 | **Common metals** | Iron 🔧 (nerfed), **Lead** 🆕, **Nickel** 🆕, **Aluminum** 🆕, **Pewter** 🆕 (alloy) | **Gold, silver, redstone, lapis**, fluorite, cinnabar |
| 4 | **First alloys** | Bronze ✅ (Mekanism), **Brass** 🆕, **Invar** 🆕, **Constantan** 🆕, Silver ✅ (Ice and Fire) | **Cobalt** 🆕, **osmium** 🔧, antimony, emerald |
| 5 | **Hardened** | Steel ✅ (Mekanism), **Cobalt** 🆕, Osmium 🔧 (Mekanism, nerfed), **Cobalt Bronze** 🆕 (alloy) | **Diamond** 🔧, **ruby, sapphire, peridot**, **platinum**, monazite |
| 6 | **Precious** | Diamond 🔧 (nerfed), **Ruby** 🆕, **Sapphire** 🆕, **Peridot** 🆕, **Platinum** 🆕, refined glowstone ✅ (Mekanism) | **Titanium** 🆕, **chromite** 🆕 |
| 7 | **Refractory** | **Titanium** 🆕, **Chromium** 🆕, **Stainless steel** 🆕 (alloy) | **Tungsten**, **iridium** |
| 8 | **Superalloys** | **Tungsten** 🆕, **Tungsten steel** 🆕 (alloy), **Iridium** 🆕, **Osmiridium** 🆕 (alloy), refined obsidian ✅ (Mekanism) | **Ancient debris** |
| 9 | Netherite | Netherite ✅ (recipe 🔧: needs a tier-8 alloy) | ATM ores (allthemodium, etc.) |
| 10+ | ATM end-game | Allthemodium → vibranium → unobtainium ✅ (unchanged) | |

**Side materials** (off the main ladder, special traits):
- **Gold** ✅: very fast, very enchantable, fragile. Usable early as a "glass cannon"
- **Electrum** 🆕 (tier 4): enchantability king, low durability
- **Rose gold** 🆕 (tier 4, gold + copper): bonus luck/looting, soft
- **Lapis** ✅ (Mekanism, tier 3): enchantable support set
- **Lead** (tier 3) doubles as the heavy-tank set (see traits)

Other dimensions' gear (Twilight Forest, Aether, Undergarden, Eternal Starlight,
Ice and Fire dragon gear, Mystical Agriculture...) **stays as-is**. It lands where
its vanilla tier puts it. Fixing each one is optional polish later.

### Rough stat curve (first guesses, per tier average)

| Tier | Tool durability | Mining speed | Bonus attack | Armor (full set) | Toughness (set) |
|---|---|---|---|---|---|
| 1 | 131 | 4 | +1 | — | — |
| 2 | 180 | 5 | +1.5 | 11 | 0 |
| 3 | 250 | 6 | +2 | 13 (iron nerfed from 15) | 0 |
| 4 | 400 | 6.5 | +2.5 | 15 | 0 |
| 5 | 650 | 7 | +3 | 16 | 2 |
| 6 | 1000 | 8 | +3 | 18 (diamond nerfed from 20) | 4 (diamond nerfed from 8) |
| 7 | 1400 | 8.5 | +3.5 | 19 | 6 |
| 8 | 1800 | 9 | +4 | 20 | 9 |
| 9 | 2031 | 9 | +4 | 20 | 12 (vanilla netherite) |

### Traits (what makes same-tier materials different)

| Material | Trait |
|---|---|
| Tin | Cheap, light, low durability |
| Zinc | Resists rust: high durability for the tier, slower |
| Copper | Everything is Copper's oxidation, kept as-is |
| Iron | Balanced (baseline) |
| Lead | **Heavy:** high knockback resistance + armor, slower movement |
| Nickel | Balanced, slightly better durability than iron |
| Aluminum | **Light:** small movement-speed bonus, low armor |
| Pewter | Cheap alloy, good enchantability |
| Bronze | Balanced alloy, durable |
| Brass | Faster mining, less durability |
| Invar | Very durable, slow |
| Constantan | Fire-resistant gear (less fire/lava damage) |
| Silver | Bonus damage vs undead |
| Steel | Balanced, high durability |
| Cobalt | **Fast:** highest mining speed of its tier |
| Osmium | Heavy hitter, slow (nerfed) |
| Cobalt bronze | Mix of cobalt speed and bronze durability |
| Diamond / ruby / sapphire / peridot | Gems: diamond balanced, ruby more damage, sapphire more armor, peridot more durability |
| Platinum | Very enchantable precious metal |
| Titanium | Light + strong: armor without a speed penalty |
| Chromium | Hard: armor toughness |
| Stainless steel | Balanced, never-ending durability for the tier |
| Tungsten | Heaviest: huge damage, slow, knockback resistance |
| Tungsten steel | Balanced top tier |
| Iridium | Toughest armor, very slow to wear down |
| Osmiridium | Mining speed + durability |

---

## 3. Ores

### Carried over (already spawn, we only change mining tier / rarity)

| Ore | From | Mining tier | Change |
|---|---|---|---|
| Coal | Vanilla | 0 | — |
| Copper | Vanilla | 1 | Tier only |
| Tin, zinc | All the Ores | 1 | Tier only |
| Iron | Vanilla | 2 | Tier only (was stone-level) |
| Lead, nickel, aluminum | All the Ores | 2 | Tier only |
| Gold, redstone, lapis | Vanilla | 3 | — |
| Silver, fluorite, cinnabar | All the Ores | 3 | — |
| Osmium | All the Ores | 4 | **Rarer veins, no raw osmium blocks in veins** |
| Antimony | Modern Industrialization | 4 | — |
| Emerald | Vanilla | 4 | — |
| Diamond | Vanilla | 5 | **Less in chest loot** |
| Ruby, sapphire, peridot, platinum | All the Ores | 5 | — |
| Monazite | Modern Industrialization | 5 | — |
| Tungsten | Modern Industrialization | 7 | — |
| Iridium | All the Ores | 7 | — |
| Ancient debris | Vanilla | 8 | — |
| Uranium | All the Ores | — | **Don't touch** |

Gating uses the common ore tags (`c:ores/tin` and so on). Stone, deepslate,
nether and end variants, and any duplicate ore from another mod, get the same
tier automatically.

### New ores 🆕

| Ore | Where it spawns | Mining tier | Drops | Why |
|---|---|---|---|---|
| **Cobalt** | **Nether** (common) + deep deepslate (rare) | 4 | Raw cobalt | Your request. Makes a Nether trip a real route to tier 5 |
| **Titanium** | Deep deepslate, mountains (more common under mountain biomes) | 6 | Raw titanium | Has no ore in the pack today |
| **Chromite** | Deep deepslate + basalt deltas (Nether) | 6 | Raw chromite → chromium ingot | Chromium has no ore today |

All three get ore, deepslate ore, raw item, raw block, ingot, nugget, plate and
storage block. All three join the common tags (`c:ores/cobalt`, `c:ingots/cobalt`...),
so other mods' machines (crushers, Mekanism ore processing) can use them where the
mods support tags. We reuse the existing MI titanium and chromium ingots
instead of adding duplicates, if Almost Unified allows (*verify*).

---

## 4. Ingots

**Reused (exist already, no new items):** copper, tin, zinc, iron, lead, nickel,
aluminum, gold, silver, osmium, platinum, iridium, titanium (MI), chromium (MI),
tungsten (MI), bronze, brass, invar, constantan, electrum, steel, stainless steel (MI).

**New 🆕:** cobalt, pewter, rose gold, cobalt bronze, tungsten steel, osmiridium.
Plus nuggets, plates and storage blocks for each where missing.

---

## 5. Alloys (Alloy Forge recipes)

| Alloy | Recipe (ingots) | Output | Tier | Forge needed |
|---|---|---|---|---|
| Pewter 🆕 | 3 tin + 1 lead | 4 | 3 | Alloy Forge |
| Bronze | 3 copper + 1 tin | 4 | 4 | Alloy Forge |
| Brass | 3 copper + 1 zinc | 4 | 4 | Alloy Forge |
| Invar | 2 iron + 1 nickel | 3 | 4 | Alloy Forge |
| Constantan | 1 copper + 1 nickel | 2 | 4 | Alloy Forge |
| Electrum | 1 gold + 1 silver | 2 | 4 (side) | Alloy Forge |
| Rose gold 🆕 | 3 gold + 1 copper | 4 | 4 (side) | Alloy Forge |
| Steel | 1 iron + 2 coal/coke | 1 | 5 | Alloy Forge |
| Cobalt bronze 🆕 | 2 cobalt + 1 bronze | 3 | 5 | Alloy Forge |
| Stainless steel | 4 steel + 1 chromium + 1 nickel | 6 | 7 | **Blast Alloy Forge** |
| Tungsten steel 🆕 | 1 tungsten + 2 steel | 2 | 8 | **Blast Alloy Forge** |
| Osmiridium 🆕 | 1 osmium + 1 iridium | 2 | 8 | **Blast Alloy Forge** |

Other mods' alloy recipes (Create brass, Mekanism, Modern Industrialization,
Immersive Engineering) **stay**. They become the automated way to get the same alloys later.

**Possible extras (not in the plan unless you want them):** nichrome (nickel +
chromium), titanium-aluminide (titanium + aluminum), black bronze, white gold.
Each extra alloy is one more set to balance, so I'd hold these back for later.

### The two forges 🆕

| Block | Made from | Can make |
|---|---|---|
| **Alloy Forge** | Bricks + any tier-3 metal | Tier 3–5 alloys. 2–3 input slots + fuel slot, burns furnace fuel |
| **Blast Alloy Forge** | Upgrade the Alloy Forge with any 4 tier-6 ingots + blaze items | Everything above, plus the hot alloys (tier 7–8). Faster |

---

## 6. Reinforced gear

**Change from plan v1 (my recommendation):** instead of a separate "Reinforced
Bronze Pickaxe" item for every material (that would double the item count to
~350), reinforcing is an **upgrade applied to the item you already have**:

- 4 plates of the item's tier (any material in that tier's tag) → 1 **reinforced plate**
- **Smithing table:** your tool or armor + reinforced plate → the same item, now marked
  **"Reinforced"**: +1 armor per piece, +1 attack damage, +25% durability
- Works on **any** tool or armor, including other mods' gear, as long as its tier is known
- Stats only: it does **not** raise the mining tier

Fewer textures, works on everything, and the item keeps its enchantments.

---

## 7. Closing loopholes

**Nerfs**
- **Diamond:** ore needs tier 5, gear stats lowered to tier 6, less diamond in chest loot
- **Osmium:** rarer ore, no raw osmium blocks in veins, Mekanism osmium tool stats lowered (Mekanism Tools config)
- **Iron:** armor 15 → 13 (tier 3 baseline)
- **Netherite:** the netherite upgrade also needs a tier-8 alloy ingot

**Tier-less mining:** these get their recipes gated to a sensible tier. All
recipes use the tier tags, so any material of that tier works:

| Tier needed | Machines / tools |
|---|---|
| 4 | Create Mechanical Drill, PneumaticCraft jackhammer, Actually Additions AIOTs |
| 5 | Mining Gadgets (tier 1), IE drill, MI steam mining drill, Actually Additions drill, Oritech hand drill |
| 6 | IE excavator, MI quarries, Steve's Carts drills, QuarryPlus / Additional Enchanted Miner, Building Gadgets destruction |
| 7 | Mekanism Atomic Disassembler + Digital Miner, RFTools Builder quarry, Oritech deep drill, MI electric drill |
| 8 | Meka-Tool, IF laser drill, Extended Industrialization laser drill, Draconic tools |

**Recommendation: don't** try to gate every "ore from nothing" system
(Mystical Agriculture seeds, ore bees, Hostile Neural Networks, Occultism miners).
They're already late-game in ATM10 and gating them all is a lot of work for
little gain. Raise the cheap early ones (first MA ore seeds, first ore bees) to
tier 5–6 only if they turn out to skip the ladder in practice.

**The ATM mining dimension:** its portal recipe gets gated to tier 5.

**Quests:** ATM10's quest book will mention items in the old order. Ignore for now.

---

## 8. Mob difficulty

- **Base buff** for all hostile mobs: +50% health, +30% damage, +2 armor (config file)
- **Per Apotheosis world tier** (Haven → Frontier → Ascent → Summit → Pinnacle *(verify names)*):
  health ×1 / ×1.5 / ×2.25 / ×3.5 / ×5, damage ×1 / ×1.3 / ×1.7 / ×2.2 / ×3
- If reading the Apotheosis tier from code turns out hard, the fallback is to scale
  by the **best gear tier the player has reached** (we already track that through
  the tier tags)
- **Elites (later):** tougher variants of existing mobs (vanilla models with new
  colors, glow, size and gear) at Ascent and above

---

## 9. Build order

| Phase | Work | Test in game |
|---|---|---|
| 0 ✅ | Setup, backup, pack scan | — |
| 1 | Mod skeleton + **tier system** (tags, tier tags) + **one new material end to end (tin)** + re-tier copper and iron | Tin gear works, iron needs a copper/tin pickaxe |
| 2 | All new gear sets (~20 materials × 9 items), traits | All gear craftable, stats feel right |
| 3 | New ores (cobalt, titanium, chromite) + all ore gating + diamond/osmium/iron nerfs | Can't skip tiers, new ores spawn |
| 4 | Alloy Forge + Blast Alloy Forge + new alloys | Alloying loop is fun |
| 5 | Reinforcement upgrade + machine/tool recipe gating | Can't skip with drills/quarries |
| 6 | Mob scaling | Fights get harder per world tier |
| 7 | Elite mobs, Silent Gear materials, other-dimension gear fixes, polish | — |

## How it's built

| Part | Where | Why |
|---|---|---|
| New items, blocks, ores, forges, traits, mob scaling | **Our mod (`.jar`)**, Java | Only code can add items and blocks |
| Tier tags, ore gating, new recipes, loot changes | **Inside our mod** as data | Version-controlled, one file to install |
| Changing/removing other mods' recipes | **KubeJS scripts** in `kubejs/server_scripts/zz_progression/` (copies kept in this repo) | ATM10 already uses KubeJS for this |
| Mekanism tool stats, ore rarity, Apotheosis | **Config file edits** in the `Claude` profile (copies + notes kept in this repo) | That's where those settings live |

## Known limits

- **Textures:** made by recoloring template sprites per material. Consistent but simple. Can be replaced with hand-drawn ones any time
- **~20 new gear sets** is a lot of balancing. Built in batches and tuned from playtesting
- **Claude can't see the game.** Testing relies on you describing what happened, screenshots, and log/crash files
- Some mods' tools may still behave oddly with the new tiers. We fix them as we find them
