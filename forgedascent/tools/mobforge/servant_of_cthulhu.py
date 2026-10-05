"""Servant of Cthulhu: the little flying eyeball the boss spawns. Shares the eyeball shader with the boss."""
import math

from forge import Model, sphere_shell, tube_segment, oriented_box, v_add, v_mul, v_norm, v_sub, v_cross, clamp, mix
import eye_of_cthulhu as eoc

CS = (0.0, 7.0, 0.0)
RS = 6.0
PHASES = [1, 2]
TEXTURES = {1: "servant_of_cthulhu", 2: "servant_of_cthulhu_angry"}
ATLAS_WIDTH = 256
BOUNDS = (2, 2, (0, 0.5, 0))
CAM_DIST = 3.2
CAM_TARGET = [0, 0.45, 0.2]
HIDE = {}


def build():
    m = Model("geometry.servant_of_cthulhu", texel_per_unit=5.0)
    m.bone("root", CS)
    m.bone("look", CS, "root")
    m.bone("body", CS, "look")
    m.bone("eyeball", CS, "body")
    for cube, lat, lon in sphere_shell(CS, RS, rings=11, seg=20, thick=1.0, tag="eye", oversize=1.1):
        m.add("eyeball", cube)
    pos = (0.0, CS[1] - 0.5, RS - 1.0)
    par = "body"
    radii = [2.4, 1.9, 1.4, 1.0]
    for i, rad in enumerate(radii):
        axis = v_norm((0.0, -0.15 + 0.05 * i, 1.0))
        name = f"nerve_{i + 1}"
        m.bone(name, pos, par)
        centre = v_add(pos, v_mul(axis, 2.2))
        for cube in tube_segment(centre, axis, 4.6, rad, 6, 0.8, "nerve", twist=math.pi / 6, data={"seg": i}):
            m.add(name, cube)
        pos = v_add(pos, v_mul(axis, 4.4))
        par = name
    return m


def make_shader(phase):
    def shader(ctx):
        if ctx["tag"] == "eye":
            return eoc.eyeball_p1(ctx["p"], CS, red=(phase == 2))
        return eoc.nerve_color(ctx["p"], ctx, phase)
    return shader


def animations():
    from eoc_anim import Anim, wave
    N = "animation.servant_of_cthulhu."
    names = [f"nerve_{i}" for i in range(1, 5)]

    def tail(a, period, amp, lag):
        for i, n in enumerate(names):
            a.const(n, rotation=[wave(period, amp * (1 + i * 0.5), -lag * i), wave(period * 1.2, amp * (1 + i * 0.5), -lag * i + 90), 0])
    idle = Anim(2.0, True)
    idle.const("body", position=[0, wave(2.0, 0.9), 0], rotation=[wave(1.0, 3, 30), wave(2.0, 6), wave(2.0, 5, 90)])
    tail(idle, 1.0, 9, 40)
    charge = Anim(0.4, True)
    charge.const("body", position=[0, 0, -1.5], rotation=[0, 0, "query.anim_time*900"], scale=[0.9, 0.9, 1.2])
    tail(charge, 0.2, 5, 30)
    death = Anim(0.5, "hold_on_last_frame")
    from forge import keys
    death.set("body", scale=keys(lambda t: [max(0.001, 1 + 0.3 * math.sin(t / 0.5 * math.pi) - t / 0.5)] * 3, 0.5, 0.05),
              rotation=keys(lambda t: [0, 720 * t / 0.5, 0], 0.5, 0.05))
    tail(death, 0.2, 8, 30)
    out = {N + "idle": idle.d, N + "charge": charge.d, N + "death": death.d}
    return out, {}


def make_glow_shader(phase):
    return _servant_glow(phase)


def _servant_glow(phase):
    base = make_shader(phase)

    def shader(ctx):
        if ctx["tag"] != "eye":
            return (0, 0, 0, 0)
        n = v_norm(v_sub(ctx["p"], CS))
        theta, psi, fa = eoc.polar(n)
        if 0.215 < theta < 0.47:
            return (*base(ctx)[:3], 215)
        return (0, 0, 0, 0)
    return shader
