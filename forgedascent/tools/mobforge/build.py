"""Builds mobforge creatures into the mod's resources and the preview manifest.

    python tools/mobforge/build.py [eye_of_cthulhu ...] [--phase N] [--meta]

--phase N  only bake skin N (so the skins can be baked in parallel, see ../../bake.sh)
--meta     only write the geo/animation files and the preview manifest (no texture baking)
"""
import importlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from forge import write_json  # noqa: E402

ROOT = HERE.parent.parent                      # forgedascent/
ASSETS = ROOT / "src/main/resources/assets/forgedascent"
PREVIEW = HERE / "preview"
MODS = ["eye_of_cthulhu", "servant_of_cthulhu"]


def rel_to_repo(path):
    return "/" + str(path.relative_to(ROOT.parent)).replace("\\", "/")


def build(name, only_phase=None, meta_only=False):
    mod = importlib.import_module(name)
    t0 = time.time()
    model = mod.build()
    w, h = model.layout(width=getattr(mod, "ATLAS_WIDTH", 1024))
    print(f"[{name}] {sum(1 for _ in model.all_cubes())} cubes, atlas {w}x{h}")
    textures = {}
    for phase in getattr(mod, "PHASES", [1]):
        out = ASSETS / "textures/entity" / f"{mod.TEXTURES[phase]}.png"
        textures[str(phase)] = rel_to_repo(out)
        if meta_only or (only_phase and phase != only_phase):
            continue
        img = model.bake(mod.make_shader(phase))
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
        print(f"  texture phase {phase}: {out.name} ({time.time() - t0:.1f}s)")
        if hasattr(mod, "make_glow_shader"):
            gout = out.with_name(out.stem + "_glowmask.png")
            model.bake(mod.make_glow_shader(phase), fill=(0, 0, 0, 0)).save(gout)
            print(f"  glow mask: {gout.name} ({time.time() - t0:.1f}s)")
    geo_path = ASSETS / "geo/entity" / f"{name}.geo.json"
    anim_path = ASSETS / "animations/entity" / f"{name}.animation.json"
    if only_phase is None:
        write_json(geo_path, model.to_geo(getattr(mod, "BOUNDS", (6, 6, (0, 1.5, 0)))))
        anims, phase_of = mod.animations()
        write_json(anim_path, {"format_version": "1.8.0", "animations": anims})
    else:
        phase_of = mod.animations()[1]
    return {"id": name, "geo": rel_to_repo(geo_path), "animations": rel_to_repo(anim_path), "textures": textures,
            "hide": getattr(mod, "HIDE", {}), "animPhase": phase_of, "camDist": getattr(mod, "CAM_DIST", 7.5),
            "camTarget": getattr(mod, "CAM_TARGET", [0, 1.4, 0]), "defaultPhase": "1"}


if __name__ == "__main__":
    args = sys.argv[1:]
    only = None
    meta = "--meta" in args
    args = [a for a in args if a != "--meta"]
    if "--phase" in args:
        i = args.index("--phase")
        only = int(args[i + 1])
        del args[i:i + 2]
    names = args or MODS
    existing = {}
    mpath = PREVIEW / "manifest.json"
    if mpath.exists():
        existing = {m["id"]: m for m in json.loads(mpath.read_text())["models"]}
    for n in names:
        if n in MODS:
            existing[n] = build(n, only, meta)
    if only is None:
        write_json(str(mpath), {"models": [existing[n] for n in MODS if n in existing]})
