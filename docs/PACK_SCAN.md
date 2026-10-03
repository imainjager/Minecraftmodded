# ATM10 Pack Scan (Phase 0)

Scanned on 2026-10-03 from the **Claude** CurseForge profile
(`C:\Users\spwel\curseforge\minecraft\Instances\Claude`), a copy of the main
ATM10 profile. ATM10 10.8.2, NeoForge 21.1.251, 491 mods. The scan only read
files and changed nothing.

Raw data is in [`pack-scan/`](pack-scan/):

| File | What's in it |
|---|---|
| `mod_list.txt` | Every installed mod and its file name |
| `materials.txt` | Ore, ingot, plate, gem, raw, nugget and dust items, per mod jar |
| `tools.txt` | Tool and armor items, per mod jar |
| `ctags.txt` | Common `c:` tags (ores/ingots/gems/plates/raw) and which jar defines them |
| `tiertags.txt` | Mining-tier block tags (`needs_*` / `incorrect_for_*`) and which jar defines them |

## Work rules

- **Only edit the `Claude` profile.** The main `All the Mods 10 - ATM10` profile is the player's real game and stays untouched.
- Backup zip: `Instances\Claude-backup-2026-10-03.zip` (everything except `simplebackups/`).

## Scripting tools

| Tool | Installed? |
|---|---|
| KubeJS (`kubejs-neoforge-2101.7.2`) | **Yes**, with ATM10's own scripts under `kubejs/server_scripts` |
| LootJS | **No.** Loot changes go in our mod's data (loot modifiers) or KubeJS instead |
| Almost Unified | Yes. Priority: minecraft > **alltheores** > allthemodium > kubejs > mekanism > modern_industrialization > ... |

## Which ores actually generate

ATM10 turns off most duplicate ores with `neoforge:none` biome modifiers in
`kubejs/data/`. All the Ores (ATO) provides almost every metal ore.

| Ore | Source that spawns | Notes |
|---|---|---|
| Copper, iron, gold, diamond, lapis, redstone, emerald | Vanilla | |
| Tin, zinc, lead, nickel, aluminum, silver | **ATO** | Mekanism/MI/Create/Ice and Fire copies disabled |
| Osmium | **ATO** | Mekanism osmium gen disabled. ATO's osmium vein also places **raw osmium blocks** (3% chance in deepslate) |
| Platinum, iridium | **ATO** | ATM10 overrides iridium placement |
| Uranium | ATO | **Don't touch** |
| Ruby, sapphire, peridot | **ATO** | Silent's Gems ores removed |
| Fluorite, cinnabar, salt, sulfur | ATO | |
| **Tungsten**, antimony, monazite | **Modern Industrialization** | Not disabled, so they still spawn |
| **Titanium** | **None** | MI has `titanium_ore` but no world generation |
| **Chromium** | **None** | Only an MI ingot/plate (made by processing) |
| Cobalt | **Not in the pack** | |
| Allthemodium / vibranium / unobtainium | Allthemodium | ATM end-game, stays above us |
| Possibly also: XyCraft aluminum, Oritech nickel/platinum, Railcraft ores | *(verify in game)* | Not disabled by a KubeJS file; may have their own config |

Other dimensions (Twilight Forest, Aether, Undergarden, Eternal Starlight, Deeper
and Darker, Ad Astra, Ice and Fire) have their own ores and gear. We leave
them as side content for now.

## Ingots and plates for our ladder

All of these already exist as items (mostly from ATO), so **we don't need to add new ingots**:

- Base metals: tin, zinc, lead, nickel, aluminum, silver, platinum, iridium, osmium
- Alloys (ATO): bronze, brass, steel, invar, constantan, electrum
- MI: titanium, tungsten, chromium, stainless steel, kanthal, cupronickel
- Plates for all of the above via ATO/MI (`c:plates/<metal>`), including copper, iron, gold, diamond, netherite

## Gear that already exists for ladder materials

| Material | Existing tools / armor | Source |
|---|---|---|
| **Copper** | Full tool + armor set (oxidizes over time) | **Everything is Copper** |
| Copper | Tools + armor | Ice and Fire |
| **Bronze** | Tools + paxel + armor | Mekanism Tools |
| **Steel** | Tools + paxel + armor | Mekanism Tools (ATM10 merged Railcraft/IE steel into these) |
| Osmium | Tools + paxel + armor | Mekanism Tools |
| Silver | Tools + armor | Ice and Fire |
| Lapis, refined glowstone, refined obsidian | Tools + armor | Mekanism Tools |
| Gems (ruby, sapphire, etc.) | Tools via Silent Gear / Silent's Gems parts | Silent Gear (modular) |
| None for: tin, zinc, lead, nickel, aluminum, brass, invar, constantan, electrum, platinum, iridium, titanium, tungsten | | **These are ours to add** |

Every mod in 1.21 defines its own `incorrect_for_<material>_tool(s)` block
tag (see `tiertags.txt`), and most copy a vanilla tier into it. When our mod
adds a tier, we must also edit the tags of existing tools we slot onto our
rungs (e.g. Mekanism bronze), or they'll keep their old mining level.

## Tier-less mining and ore without mining

Machines and items that skip pickaxe tiers. Phase 3 has to gate their **recipes**:

| Category | Things to gate |
|---|---|
| Mining tools with own rules | Actually Additions drills + AIOTs, IE drill, MI steam/electric mining drills, Extended Industrialization electric drill + ultimate laser drill, Mekanism Atomic Disassembler + Meka-Tool, Mining Gadgets, Draconic tools, IF infinity drill, Oritech hand drill, Just Dire Things tools, PneumaticCraft jackhammer, FTB Ultimine (follows tool tier, OK) |
| Block-breaking machines | Create mechanical drill, IE excavator, MI quarries, Oritech deep drill / laser arm, Steve's Carts drills, Mekanism Digital Miner, RFTools Builder quarry, QuarryPlus / Additional Enchanted Miner, Building Gadgets destruction, PneumaticCraft drones |
| Ore from nothing | IF laser drill, Occultism miner spirits, Mystical Agriculture seeds, Productive Bees / Modular Bees, Hostile Neural Networks, Botany Pots |
| Other | ATM10 **mining dimension** (`miningDim.js`), Actually Additions atomic reconstructor |

Gating everything at once is a lot. Phase 3 should start with the cheap early
skips (Create drill, Mining Gadgets, AA drills/AIOTs, quarries) and leave
late-game automation (bees, MA seeds, IF laser drill) at roughly its current
place.

## Mob scaling hooks

- Apotheosis 8.8.0 + Apothic Attributes 2.10.1 installed, config in `config/apotheosis/`
- In Control! 10.3.0 is installed and can also tweak mob spawns and stats from config
