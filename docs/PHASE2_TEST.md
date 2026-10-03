# Phase 2 test checklist

Use the **Claude** profile. Tell Claude what happened plus anything that felt off. If it crashes,
just say so: Claude can read `crash-reports/` and `logs/latest.log` itself.

## 1. It loads
- [ ] Game reaches the main menu and a world loads
- [ ] The **Forged Ascent** creative tab now has 31 gear sets, 7 ores (with deepslate/nether versions), raw ores and lots of ingots/blocks

## 2. Looks
- [ ] New tool and armor icons look decent (they're recolors of other mods' textures now)
- [ ] Wear a few sets (F5): worn armor looks right and matches its color
- [ ] Ores look like ores (colored spots on stone/deepslate/netherrack)

## 3. New ores in a NEW world (creative is fine)
Ores only appear in newly generated land. Spectator mode (`/gamemode spectator`) lets you fly through stone.
- [ ] **Bismuth** (pink-purple): common near the surface
- [ ] **Cobalt** (blue): common in the **Nether**
- [ ] **Vanadium** (red): under **deserts/badlands**
- [ ] **Molybdenum** (blue-grey): under **mountains**
- [ ] **Titanium / Chromium**: deep (below y=0)

## 4. Mining tiers
- [ ] Brass pickaxe (tier 4) mines cobalt ore; tin pickaxe can't
- [ ] Cobalt pickaxe (tier 5) mines diamond and vanadium
- [ ] Platinum pickaxe (tier 6) mines titanium and chromium
- [ ] Titanium pickaxe (tier 7) mines tungsten (`modern_industrialization:tungsten_ore`)
- [ ] Tungsten pickaxe (tier 8) mines ancient debris; titanium pickaxe can't

## 5. Crafting (JEI)
- [ ] Raw ores smelt into ingots
- [ ] A few alloys: 3 steel + 1 manganese → manganese steel; cobalt + chromium + tungsten → stellite; 3 gold + 1 copper → rose gold
- [ ] **Create Mechanical Drill** recipe now asks for a tier-4 ingot (bronze, brass, invar...) instead of iron

## 6. Traits
- [ ] Inconel full set: you stop burning almost instantly after leaving fire
- [ ] Tungsten armor slows you a little; duralumin armor speeds you up a little
