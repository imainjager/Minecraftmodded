# Eye of Cthulhu: what to test (mod 0.8.0, update 7)

A Terraria-style Gate I boss with a fully custom 3D model, skins and animations (GeckoLib). Pictures: [`docs/eye_of_cthulhu/`](eye_of_cthulhu/).

## How to meet it

| Way | What happens |
|---|---|
| **Suspicious Looking Eye** | Craft 6 spider eyes (shapeless). Right-click **at night, in the Overworld**. The Eye flies in from about 30 blocks away. One at a time. |
| **On its own** | Until it has been beaten once: each night there is a 1-in-3 chance (config) after world day 3. Needs a player with 8+ armor standing under open sky. You get *"You feel an evil presence watching you..."* first, then it arrives 30 to 150 seconds later. |
| **Spawn egg** | Creative tab "Forged Ascent". Always works, never leaves at dawn, even after it has been beaten. |

After the first kill (by a player) it stops coming on its own. Natural and item-summoned Eyes retreat when the sun rises (`fleesAtDawn` in `config/forgedascent-common.toml`, section `[eye_of_cthulhu]`).

## The fight

- **Phase 1** (400 HP, armor 6): hovers over you, winds up (shakes, pulls back), then dashes at you. Three dashes, then it calls 2 to 3 **Servants of Cthulhu** (small flying eyes, 14 HP, they drop spider eyes). Dash hits for about 14.
- **Half health**: roars and transforms (invulnerable for about 3.5 seconds). Boss bar turns purple.
- **Phase 2**: fanged maw, faster and spinning dashes, four in a row, then a roar that throws everyone within 14 blocks back and calls more Servants.
- It flies through blocks, so digging a hole doesn't save you.
- Not scaled by world tier (it is a gate boss).

## Drops

- Gate I **Treasure Bag** (Sigil, materials, rough gems, plate, accessory) and the gate counts as cleared, like Naga / Slider / Elder Guardian.
- **Raw Demonite** 18 to 34 (more with Looting). Smelt for **Demonite Ingots**; a new tier-4 metal with a full gear set (sword, tools, armor; armor perk: +3% attack damage per piece). Crafted at a Bronze Anvil.
- 2 to 5 spider eyes (so you can make another Suspicious Looking Eye), 25% chance of 1 to 2 ender pearls.

## Please check in game

1. The model: iris looks at you, nerve tail wiggles, phase 2 mouth and teeth, the glow of the iris in the dark.
2. The fight feels fair (dash damage, speed, Servants not overwhelming). All numbers are in `EyeOfCthulhu.java` and easy to tune.
3. Dawn retreat, the warning message at night, only one Eye at a time.
4. Quests: Stone Age chapter has *Suspicious Looking Eye* and *Demonite*; the Gate I boss list has the Eye.
5. Loot and the Treasure Bag after the death animation (about 3.5 seconds after the last hit).

## Not done / ideas

Shield of Cthulhu style accessory, trophy and mask blocks, music, a second Terraria boss with the same tools (Eater of Worlds / Brain of Cthulhu are good candidates).
