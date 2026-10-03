# Start Here: Setting Up on Your Windows PC

This guide gets Claude Code working on your own computer so it can build the mod
and edit your ATM10 copy directly. The full project plan is in [`PLAN.md`](PLAN.md).

## How the pieces fit

- **Your PC** is where the work happens. Claude Code runs there, builds the mod,
  and puts it in your CurseForge profile.
- **This GitHub repository** stores the mod's code. It's a backup and a history of
  every change, so nothing is lost.
- **CurseForge** runs the game like normal. You just press Play.

## Step 1: Open Claude Code on your PC

Use it the same way you did before (the Claude desktop app's **Code** tab, or the terminal).
If it asks which folder to work in, pick or create an empty one, for example
`Documents\Minecraftmodded`.

## Step 2: Close Minecraft

Make sure the game isn't running while Claude copies files around.

## Step 3: Paste this prompt

Copy everything in the box below and send it to Claude Code on your PC.

```text
Hi Claude! I'm a complete beginner (no coding or modding experience), so please
explain things simply and ask before doing anything risky. Please walk me through
each step.

PROJECT: I'm making my own custom mod(s) for my personal copy of the "All the Mods 10"
modpack, and also tweaking the mods already in it. The full plan is in my GitHub
repository: https://github.com/imainjager/Minecraftmodded on the branch
"claude/eager-clarke-85t16h". Read PLAN.md there first. It has all the decisions
and the build order.

KEY FACTS:
- Windows 11 PC, single player only.
- Modpack: All the Mods 10, version 10.8.2, Minecraft 1.21.1, NeoForge.
- I use the CurseForge app. My ATM10 copy is my own frozen profile: it will never be
  updated, so changing existing mods' configs/recipes/etc. is fine.
- Main idea: a much longer ore/gear tier ladder (copper -> iron -> bronze/brass ->
  steel -> gems/diamond -> titanium -> tungsten -> netherite), tools and armor for
  the pack's unused ingots, an Alloy Forge, reinforced gear (stats only), nerfs to
  diamond and osmium, and much stronger mobs that scale with Apotheosis tiers.
- Don't touch uranium.

WHAT I'D LIKE YOU TO DO TODAY (Phase 0 in PLAN.md):
1. Check what's installed (Git, Java 21 JDK) and help me install anything missing.
2. Clone my repository into this folder and switch to the branch above.
3. Find my ATM10 profile folder. CurseForge usually keeps profiles in
   C:\Users\<my name>\curseforge\minecraft\Instances\ . If there's more than one
   ATM10 profile, ask me which one is my copy.
4. Make a full BACKUP of that profile folder (a zip next to it with today's date)
   before changing anything.
5. Scan the profile WITHOUT changing it: list the mods in the mods folder, find the
   ores/ingots/plates/gems (All the Ores, Mekanism, Modern Industrialization, etc.),
   check which mods have their own tools or tier-less mining (Create drills,
   quarries, mining lasers, etc.), and check whether KubeJS and LootJS are installed.
   Save what you find to a file in the repo so future sessions can use it.
6. Then suggest any changes to the tier table in PLAN.md based on what's actually
   in the pack, and ask me to approve before starting Phase 1.

Commit and push your work to the same branch when you finish something.
```

## Step 4: Approve things as it asks

Claude Code will ask permission before running commands or installing things.
Read what it says, and approve if it matches what's in the prompt. If something
looks confusing, just ask it "what does this do?"

## Good to know

- **Where your profile lives:** in CurseForge, right-click your ATM10 copy → **Open Folder**.
- **If the game crashes:** the details are in that folder under `crash-reports\` and
  `logs\latest.log`. Tell Claude and it can read them.
- **Screenshots help:** you can paste or drag screenshots into Claude Code.
