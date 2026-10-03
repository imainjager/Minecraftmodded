"""Installs Forged Ascent into the CurseForge "Claude" profile.

1. Copies the built mod jar into mods/ (older Forged Ascent jars are moved to the backup folder).
2. Copies everything under profile/ into the profile (e.g. KubeJS tag overrides).
3. Patches pack config/worldgen files in place (Mekanism tool stats, osmium veins).

Every file that gets replaced or patched is copied to
<profile>/forgedascent_backups/<timestamp>/ first. Never touches the main ATM10 profile.

    python tools/install.py
"""
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROFILE = Path.home() / "curseforge/minecraft/Instances/Claude"
BACKUP = PROFILE / "forgedascent_backups" / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Mekanism Tools stats (PLAN.md section 7): bronze -> tier 4, steel/osmium -> tier 5, osmium nerfed.
MEKANISM_TOOLS = {
    "bronzeToolDurability": 400, "bronzeToughness": 0.0,
    "bronzeHelmetArmor": 2, "bronzeChestplateArmor": 6, "bronzeLeggingArmor": 5, "bronzeBootArmor": 2,
    "steelToolDurability": 650, "steelEfficiency": 7.0, "steelPaxelDurability": 1300, "steelToughness": 0.5,
    "steelHelmetArmor": 3, "steelChestplateArmor": 6, "steelLeggingArmor": 5, "steelBootArmor": 2,
    "osmiumToolDurability": 650, "osmiumEfficiency": 4.5, "osmiumAttackDamage": 3.5, "osmiumEnchantability": 10,
    "osmiumPaxelDurability": 1300, "osmiumPaxelEfficiency": 4.5, "osmiumPaxelEnchantability": 10,
    "osmiumToughness": 0.5,
    "osmiumHelmetArmor": 3, "osmiumChestplateArmor": 6, "osmiumLeggingArmor": 5, "osmiumBootArmor": 2,
    "osmiumHelmetDurability": 220, "osmiumChestplateDurability": 320,
    "osmiumLeggingDurability": 300, "osmiumBootDurability": 260,
}

OSMIUM_FEATURE = "kubejs/data/alltheores/worldgen/configured_feature/ore_osmium.json"
OSMIUM_VEIN_SIZE = 9  # ATM10 default is 16


def backup(path: Path):
    if not path.exists():
        return
    dest = BACKUP / path.relative_to(PROFILE)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)


def minecraft_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq javaw.exe"], capture_output=True, text=True).stdout
        return "javaw.exe" in out
    except OSError:
        return False


def install_jar():
    jars = sorted((REPO / "forgedascent/build/libs").glob("forgedascent-*.jar"))
    jars = [j for j in jars if not j.name.endswith(("-sources.jar", "-javadoc.jar"))]
    if not jars:
        sys.exit("No built jar found. Run 'gradlew build' in forgedascent/ first.")
    jar = max(jars, key=lambda p: p.stat().st_mtime)
    mods = PROFILE / "mods"
    for old in mods.glob("forgedascent-*.jar"):
        backup(old)
        old.unlink()
    shutil.copy2(jar, mods / jar.name)
    print(f"  mod jar: {jar.name}")


def copy_overlay():
    src = REPO / "profile"
    count = 0
    for f in src.rglob("*"):
        if f.is_file():
            dest = PROFILE / f.relative_to(src)
            if dest.exists() and dest.read_bytes() == f.read_bytes():
                continue
            backup(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            count += 1
    print(f"  profile files updated: {count}")


def patch_mekanism():
    path = PROFILE / "config/Mekanism/tools-materials-startup.toml"
    text = path.read_text(encoding="utf-8")
    new = text
    for key, value in MEKANISM_TOOLS.items():
        new, n = re.subn(rf"^(\s*){key} = .*$", rf"\g<1>{key} = {value}", new, flags=re.M)
        if n != 1:
            print(f"  WARNING: Mekanism key {key} found {n} times")
    if new != text:
        backup(path)
        path.write_text(new, encoding="utf-8")
    print(f"  Mekanism tool stats: {'patched' if new != text else 'already up to date'}")


def patch_osmium():
    path = PROFILE / OSMIUM_FEATURE
    data = json.loads(path.read_text(encoding="utf-8"))
    config = data["config"]
    targets = [t for t in config["targets"] if t["state"]["Name"] != "alltheores:raw_osmium_block"]
    changed = targets != config["targets"] or config["size"] != OSMIUM_VEIN_SIZE
    if changed:
        backup(path)
        config["targets"] = targets
        config["size"] = OSMIUM_VEIN_SIZE
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"  osmium veins: {'patched' if changed else 'already up to date'}")


def main():
    if not PROFILE.exists():
        sys.exit(f"Profile not found: {PROFILE}")
    if minecraft_running():
        sys.exit("Minecraft (javaw.exe) is running. Close it before installing.")
    print(f"Installing Forged Ascent into {PROFILE}")
    install_jar()
    copy_overlay()
    patch_mekanism()
    patch_osmium()
    if BACKUP.exists():
        print(f"Backups of replaced files: {BACKUP}")
    print("Done.")


if __name__ == "__main__":
    main()
