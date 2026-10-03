# Phase 1 test checklist

Use the **Claude** profile in CurseForge. A **new creative world** is quickest for checks 1–6.
Tell Claude what happened for each, plus anything that felt off. If the game crashes,
say so and Claude can read `crash-reports/` and `logs/latest.log` itself.

## 1. It loads
- [ ] The game reaches the main menu
- [ ] A world loads
- [ ] In the creative inventory there's a **Forged Ascent** tab with tin, zinc, lead, nickel, aluminum, pewter, brass, invar and constantan gear, plus a pewter ingot and block

## 2. Looks
- [ ] Tools and armor icons show up (no purple-black squares)
- [ ] Wearing a full set shows colored armor on your character (F5 to look)

## 3. Mining tiers (survival mode, `/gamemode survival`)
Give yourself pickaxes with `/give @s <item>`, and place ores to test. Try:
- [ ] **Stone pickaxe on iron ore**: breaks slowly and drops **nothing**
- [ ] **Tin pickaxe** (`forgedascent:tin_pickaxe`) **on iron ore**: drops raw iron
- [ ] **Tin pickaxe on gold ore**: drops nothing
- [ ] **Iron pickaxe on diamond ore**: drops nothing
- [ ] **Brass pickaxe** (tier 4) **on osmium ore** (`alltheores:osmium_ore`): drops raw osmium
- [ ] **Mekanism steel pickaxe** (`mekanismtools:steel_pickaxe`) **on diamond ore**: drops a diamond
- [ ] **Everything is Copper pickaxe** (`everythingcopper:copper_pickaxe`) **on iron ore**: drops raw iron

## 4. Crafting (JEI: search the item, press R for recipes)
- [ ] Tin pickaxe: 3 tin ingots + 2 sticks
- [ ] Alloys in a crafting table: 3 tin + 1 lead → 4 pewter; 3 copper + 1 tin → 4 bronze; 3 copper + 1 zinc → 4 brass; 2 iron + 1 nickel → 3 invar; 1 copper + 1 nickel → 2 constantan; gold + silver → 2 electrum; iron + 2 coal → steel

## 5. Stats (hover over items, F3+H shows more detail)
- [ ] Iron chestplate shows +5 armor (was +6)
- [ ] Diamond pickaxe durability 1000
- [ ] Aluminum armor gives a little speed, lead armor slows you a little

## 6. Enchanting
- [ ] Our tools and armor can be enchanted at an enchanting table

## 7. Survival feel (later, optional)
- [ ] Start a survival world: does stone → copper/tin/zinc → iron feel right, or too slow/grindy?
