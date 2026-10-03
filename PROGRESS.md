# Progress

Read [`PLAN.md`](PLAN.md) first. This file says where the build stopped and how to continue.

## Current state (2026-10-03)

**Phase 1: built and installed in the `Claude` profile. Waiting for the player's in-game test.**

| Done | Detail |
|---|---|
| Mod project | `forgedascent/` (NeoForge 21.1.251, MC 1.21.1, mod version 0.1.0) |
| Tier system | Block tags `forgedascent:needs_tier_1..8`, `forgedascent:incorrect_for_tier_0..9`. Vanilla wood/gold → 0, stone → 1, iron → 3, diamond → 6 |
| Ore gating | Existing ores tiered via `c:ores/*` tags (`tools/gen_assets.py`, `ORE_TIERS`) |
| Gear sets | Tin, zinc, lead, nickel, aluminum, pewter, brass, invar, constantan (sword, pickaxe, axe, shovel, hoe, 4 armor). Stat traits: lead/aluminum/tin move speed, lead knockback, constantan burning time |
| New items | Pewter ingot + block |
| Alloys | Shapeless crafting: pewter, bronze, brass, invar, constantan, electrum, steel (outputs All the Ores ingots) |
| Tier item tags | `forgedascent:tier_materials/2..5` (unused until later phases) |
| Vanilla nerfs | Iron armor 15 → 13; diamond armor 20 → 18, toughness 8 → 4; diamond tools 1000 durability |
| Existing gear re-tiered | Everything is Copper → 2, Mekanism bronze → 4, Mekanism/IE steel → 5, Mekanism osmium → 5 (KubeJS tag overrides in `profile/`) |
| Mekanism stats | Bronze/steel/osmium tool + armor stats lowered (`tools/install.py`, `MEKANISM_TOOLS`) |
| Osmium | Veins 16 → 9 blocks, no raw osmium blocks (new chunks only) |

## How to work on it

| Task | Command (from repo root unless noted) |
|---|---|
| Change gear stats/colors, add a gear material | Edit `forgedascent/src/main/resources/forgedascent/materials.json` |
| Regenerate textures, models, recipes, tags, names | `cd forgedascent` then `python tools/gen_assets.py` |
| Build the jar | `cd forgedascent` then `gradlew.bat build` (JAVA_HOME = the JDK 21 in `C:\Program Files\Microsoft`) |
| Quick crash check (only our mod) | `cd forgedascent` then `python tools/smoke_test.py` |
| Install into the `Claude` profile | `python tools/install.py` (Minecraft must be closed; backs up anything it replaces) |
| Pack-side overrides | Files under `profile/` are copied into the profile as-is |

## Next

1. Player tests Phase 1 in game (checklist in [`docs/PHASE1_TEST.md`](docs/PHASE1_TEST.md)) and reports problems/feel.
2. Fix anything found, then Phase 2 (rest of the metal gear sets, 7 new ores, machine/tool gating).

## Known gaps / to verify in game

- Whether our tag overrides beat each mod's own tags (KubeJS data should win)
- Silent Gear, Ice and Fire copper/silver gear and other dimensions' gear are not re-tiered yet
- Diamond ore currently needs a tier-5 pickaxe (steel/osmium), but no tier-5 gear set of ours exists yet. Mekanism steel/osmium or IE steel tools are the route for now
- Several silvery materials (tin, aluminum, nickel, invar) look alike
