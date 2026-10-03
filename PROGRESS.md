# Progress

Read [`PLAN.md`](PLAN.md) first. This file says where the build stopped and how to continue.

## Current state (2026-10-03)

**Phases 3–5 (gems, mobs, loot): built and installed in the `Claude` profile (mod version 0.3.0). Waiting for the player's in-game test** ([`docs/PHASE3-5_TEST.md`](docs/PHASE3-5_TEST.md)). Phase 2 was installed but not yet tested in game when 3–5 were built.
Phase 1 was tested in game by the player: worked; only complaint was texture quality (fixed in Phase 2, see "Texture rule").

### Phases 3–5 (0.3.0)

| Done | Detail |
|---|---|
| Rough gems | Diamond, emerald, peridot, garnet, topaz, ruby, sapphire, alexandrite, black diamond ores drop `rough_<gem>` (KubeJS loot tables in `profile/`, from `gems` in `materials.json`) |
| Cutting (basic) | Crafting: rough gem + cutting wheel → gem. Emery wheel (32 uses, cuts hardness ≤ 8), diamond-grit wheel (64 uses, ≤ 10). Rough diamond → 2 diamond grit |
| Gem gear (9 sets) | Amethyst (t4), garnet, peridot (t5), emerald, topaz (t6), alexandrite, ruby, sapphire (t7), black diamond (t8). **Jade dropped: not in the pack** |
| Mob scaling | All hostile mobs (incl. modded, not bosses): health/damage × world tier × place (deepslate, deep, Nether, other dims). Projectile damage scaled too. Numbers in `config/forgedascent-common.toml` |
| Armor on mobs | Zombies/skeletons/piglins, chance per world tier, gear from the matching tier band, 5% drop |
| Elites | 42 mob types `forgedascent:<runner|brute|armored|molten|frost|venomous|dread>_<zombie|skeleton|spider|wither_skeleton|piglin|witch>`, swapped in at spawn. Recolored vanilla skins, size via scale attribute, on-hit fire/slow/poison, Dread speed aura, bonus loot |
| In-place elites | Creepers (short fuse / big blast / charged), endermen (stats), pillagers (Quick Charge + Piercing crossbow), vindicators/evokers/ravagers (stats). Patrol captains get the aura from Ascent up |
| Hardened/Ancient | Stat-only (+25% / +50% health) for 30% of normal mobs from Ascent / Pinnacle. **No reskin yet** |
| Chest loot | Global loot modifier on every `chests/*` table: tier-band ingots, rough gems, wheels, occasional gear piece. Fewer diamonds in Haven/Frontier chests |
| World tier unlocks | Apotheosis Frontier/Ascent/Summit/Pinnacle also need tier 4/6/7/8 gear (`forgedascent:gear/tier_N`). Advancement files copied from the Apotheosis jar (git-ignored) |
| Testing | `tools/smoke_test.py "command" ...` runs server commands over RCON and prints replies |

Not done from the plan (deferred): flawless gems, inlays, heat treatment, synthetic gems, Automatic Lapidary, raid extra wave, bigger underground groups, better skeleton aim, Hardened/Ancient reskins, blood moon, web-shooting spiders.

| Done | Detail |
|---|---|
| Mod project | `forgedascent/` (NeoForge 21.1.251, MC 1.21.1) |
| Tier system | Block tags `forgedascent:needs_tier_1..8`, `forgedascent:incorrect_for_tier_0..9`. Vanilla wood/gold → 0, stone → 1, iron → 3, diamond → 6 |
| Ore gating | All ores tiered via `c:ores/*` tags (`ORE_TIERS` in `tools/gen_assets.py` + `tier` of each new ore) |
| Gear sets (31) | Tier 2: tin, zinc · 3: lead, nickel, aluminum, pewter · 4: brass, invar, constantan, bismuth bronze, duralumin, electrum, rose gold · 5: cobalt, manganese steel, alnico · 6: platinum, vanadium steel, white gold · 7: titanium, chromium, stainless steel, chromoly, titanium alloy · 8: tungsten, tungsten carbide, high-speed steel, stellite, inconel, iridium, osmiridium |
| Stat traits | Move speed (tin, aluminum, duralumin, titanium, chromoly, titanium alloy +; lead, tungsten −), knockback (lead, manganese steel, tungsten), burning time (constantan, inconel), luck (rose gold) |
| New ores (7) | Bismuth (t1, shallow), manganese (t3), cobalt (t4, Nether + deep), molybdenum (t4, mountains), vanadium (t5, desert/badlands), titanium (t6, deep + mountains), chromium (t6, deep + basalt deltas). Ore, raw, raw block, ingot, block, smelting/blasting |
| New ingots | 23 (ore metals + alloys + nichrome) with storage blocks |
| Alloys | Shapeless crafting (see `ALLOYS` in `tools/gen_assets.py`) |
| Ore depths | All the Ores tin/zinc shallow, lead/nickel/aluminum mid, osmium/platinum/iridium deep (`ATO_DEPTHS`, KubeJS data in `profile/`) |
| Tool gating | Create drill, IE iron drill head, Steve's Carts iron drill → tier 4; destruction gadget → 5; Atomic Disassembler → 7; IF laser drill → 8 (`GATING`, KubeJS script in `profile/`). Most other drills/quarries need diamonds, which need tier 5 |
| Vanilla/Mekanism nerfs | Iron/diamond armor, diamond tools, Mekanism bronze/steel/osmium, osmium veins (from Phase 1) |

## Texture rule (player's request, 2026-10-03)

- **Tools and armor are recolored from existing pack textures**, not drawn from scratch. Each material picks a
  source set (`tools_from`, `armor_from` in `materials.json`), using **different sources per material** so sets look distinct.
- **The sword is our own sprite** (player liked it).
- **Never use Silent Gear / Silent's Gems textures.**
- Ingots, ores, raw items and blocks are recolored from All the Ores (`style` in `materials.json`).
- Recolored textures come from other mods, so they are **generated locally and git-ignored**. `tools/gen_assets.py`
  needs the `Claude` profile's mods and the vanilla 1.21.1 jar on this PC.
- Check results with a preview sheet before installing. Swap sources that look busy or blown out.

## How to work on it

| Task | Command (from repo root unless noted) |
|---|---|
| Change stats/colors/texture sources, add a material or ore | Edit `forgedascent/src/main/resources/forgedascent/materials.json` |
| Regenerate textures, models, recipes, tags, worldgen, names, `profile/` files | `cd forgedascent` then `python tools/gen_assets.py` |
| Build the jar | `cd forgedascent` then `gradlew.bat build` (JAVA_HOME = the JDK 21 in `C:\Program Files\Microsoft`) |
| Quick crash check (only our mod) | `cd forgedascent` then `python tools/smoke_test.py` |
| Install into the `Claude` profile | `python tools/install.py` (Minecraft must be closed; backs up anything it replaces) |
| Pack-side overrides | Files under `profile/` are copied into the profile as-is |

## Next

1. Player tests Phases 2–5 in game ([`docs/PHASE2_TEST.md`](docs/PHASE2_TEST.md), [`docs/PHASE3-5_TEST.md`](docs/PHASE3-5_TEST.md)) and reports problems/feel.
2. Tune numbers from feedback, then pick from the deferred list above.

## Known gaps / to verify in game

- New ores and changed ore depths only appear in **new chunks**
- Almost Unified may swap our titanium/chromium ingots for Modern Industrialization's in recipe outputs (fine, same tag)
- Silent Gear, Ice and Fire copper/silver gear and other dimensions' gear are not re-tiered yet
- Tool gating via KubeJS `replaceInput` is unverified in game (check JEI recipes)
- ATM mining dimension is not gated yet
