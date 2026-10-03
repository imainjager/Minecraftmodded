# Phases 3–5 test checklist (gems, mobs, loot)

Use the **Claude** profile, ideally a **new world** on **Hard** difficulty. Tell Claude what happened plus anything
that felt off or too hard/easy. If it crashes, just say so: Claude can read `crash-reports/` and `logs/latest.log`.

## Gems
- [ ] Mining diamond ore (with a tier-5 pickaxe) drops **Rough Diamond**, not a diamond. Fortune gives more
- [ ] Rough Diamond alone in a crafting grid → 2 Diamond Grit
- [ ] Emery Cutting Wheel: 8 flint around any tier-4 ingot (bronze, brass, invar...)
- [ ] Rough emerald + emery wheel → emerald, and the wheel stays in the grid with less durability
- [ ] Rough diamond needs the **Diamond-Grit** wheel (grit around a tier-6 ingot/diamond), the emery wheel won't work
- [ ] Gem gear (amethyst, garnet, peridot, emerald, topaz, alexandrite, ruby, sapphire, black diamond) is craftable and looks OK

## Mobs (survival)
- [ ] Normal mobs feel tougher (Haven: 1.5× health, 1.3× damage). Deeper underground and in the Nether they're tougher still
- [ ] Sometimes an elite spawns, e.g. a **Brute Zombie** (bigger, darker), a **Runner Skeleton** (fast, pale). Their names show in the death message / Jade tooltip
- [ ] Elites drop normal loot plus sometimes a Forged Ascent ingot
- [ ] Spawn eggs aren't added; test with `/summon forgedascent:brute_zombie`, `/summon forgedascent:dread_skeleton` etc.
- [ ] **Molten** elites (Nether) set you on fire, **Frost** (snowy biomes) slow you, **Venomous** (jungle/swamp) poison you
- [ ] With Apotheosis world tier set higher (Ascent and up), some zombies/skeletons wear Forged Ascent armor

## Loot
- [ ] Chests (dungeons, mineshafts, structure mods, Lootr chests) now also contain Forged Ascent ingots, rough gems, or a cutting wheel
- [ ] Early (Haven/Frontier) chests have fewer diamonds

## World tiers
- [ ] The Apotheosis **Frontier** unlock now also needs tier-4 gear (e.g. a brass pickaxe) on top of Apotheosis's own requirement. The advancement description says so

## Settings
- [ ] `config/forgedascent-common.toml` exists. Mob health/damage/elite numbers can be changed there (restart after editing)
