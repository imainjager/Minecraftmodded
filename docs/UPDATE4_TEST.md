# Update 4 test checklist (anvils, boss gates, blood moon, quest book)

Use the **Claude** profile (mod 0.5.0). Tell Claude what happened; if it crashes, just say so.

## Quest book
- [ ] Open the quest book: there's a new **Forged Ascent** group at the top with 7 chapters (Stone Age → Netherite Age)
- [ ] Quests show text, icons and rewards; ATM's own chapters still look normal

## Gear curve
- [ ] Iron chestplate +5, diamond chestplate +12, netherite chestplate +21 (hover, F3+H)
- [ ] Other mods' gear got stronger too (e.g. Mekanism steel pickaxe damage, Twilight Forest armor)
- [ ] Mobs at Summit/Pinnacle feel beatable with matching-tier gear

## Plates and reinforcing
- [ ] Our plates (e.g. Cobalt Plate) can be made with an All the Ores hammer + 2 ingots, and in Create/IE presses
- [ ] 4 tier plates (2x2) → a reinforced plate of that tier
- [ ] At an anvil: gear + reinforced plate (same tier or higher) → same gear with "Reinforced" in the tooltip, +1 armor/damage

## Anvils (creative is fine)
- [ ] Bronze/Steel/Gemstone/Titanium/Tungsten/Netherite Anvils are in the Forged Ascent tab and place like anvils
- [ ] Right-click opens a crafting grid titled with the anvil name and its tier
- [ ] JEI has a **Smithy Anvil** tab; e.g. Brass Pickaxe shows "Needs: Bronze Anvil or better"
- [ ] A Bronze Anvil can't craft tier-5 gear (cobalt); a Steel Anvil can
- [ ] Diamond and netherite gear and Mekanism/IE steel tools can no longer be made in a crafting table (netherite = diamond item + netherite ingot + tier-8 ingot at a Netherite Anvil)
- [ ] Tier 1–3 gear (tin, lead, iron...) still works in a normal crafting table

## Boss gates
- [ ] Kill a gate boss, e.g. `/summon minecraft:elder_guardian` (in water) or the Naga: a **Gate I Treasure Bag** drops and chat says the gate is cleared
- [ ] Right-click the bag: Sigil + ingots + rough gems + a reinforced plate + an Artifacts accessory
- [ ] Bronze Anvil recipe: 3 tier-4 plates, Gate I Sigil, 3 iron blocks
- [ ] Note: Twilight Forest Knight Phantoms are several mobs, so each may drop a bag. Tell Claude if that's too generous

## Blood moon
- [ ] After a Gate I boss is cleared, nights can turn into blood moons (force one for testing by waiting, or ask Claude for a test command)
- [ ] Chat warning at dusk, reddish fog, can't sleep, more mobs
- [ ] Zombies that can't reach you break blocks toward you (with crack animation); they never break chests/machines or obsidian
- [ ] Damage is permanent (`restoreAtDawn = false` in `config/forgedascent-common.toml`)
- [ ] No noticeable lag during a blood moon
