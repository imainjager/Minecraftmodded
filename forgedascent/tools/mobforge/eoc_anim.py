"""Animations for the Eye of Cthulhu (GeckoLib animation.json). Loops use Molang sine waves (smooth, tiny files);
one-shots are sampled keyframes so every move is exactly what the preview shows."""
import math

from forge import keys, ease_in_out, ease_out, ease_in

N = "animation.eye_of_cthulhu."
NERVE = [f"nerve_{i}" for i in range(1, 10)]
TEND_A = [f"tendril_a_{i}" for i in range(1, 6)]
TEND_B = [f"tendril_b_{i}" for i in range(1, 6)]


def wave(period, amp, phase=0.0, off=0.0):
    """Molang sine: amplitude amp, one cycle per `period` seconds, phase in degrees."""
    k = 360.0 / period
    ph = f"+{phase:.1f}" if phase >= 0 else f"{phase:.1f}"
    base = f"math.sin(query.anim_time*{k:.3f}{ph})*{amp:.3f}"
    return base if off == 0 else f"{base}+{off:.3f}"


class Anim:
    def __init__(self, length, loop):
        self.d = {"loop": loop, "animation_length": length, "bones": {}}

    def set(self, bone, **ch):
        b = self.d["bones"].setdefault(bone, {})
        for k, v in ch.items():
            b[k] = v
        return self

    def const(self, bone, **ch):
        """Loop channels: each value is a 3-list of numbers or Molang strings."""
        return self.set(bone, **{k: {"0.0": list(v)} for k, v in ch.items()})


def tails(a, period, amp, lag, tip_gain=1.6, bias=0.0):
    """Wave travelling down the optic nerve and the two tendrils."""
    n = len(NERVE)
    for i, name in enumerate(NERVE):
        g = 1 + (tip_gain - 1) * i / (n - 1)
        a.const(name, rotation=[wave(period, amp * g, -lag * i, bias), wave(period * 1.3, amp * 0.9 * g, -lag * i + 80),
                                wave(period * 0.9, amp * 0.3 * g, -lag * i + 30)])
    for chain, side in ((TEND_A, -1), (TEND_B, 1)):
        for i, name in enumerate(chain):
            g = 1 + 2.0 * i / 4
            a.const(name, rotation=[wave(period * 0.8, amp * 1.6 * g, -lag * 1.4 * i + (0 if side < 0 else 90)),
                                    wave(period * 1.1, amp * 2.2 * g, -lag * 1.4 * i + (40 if side < 0 else 150)), 0])


def jaws(a, open_deg):
    """open_deg: Molang string (degrees), positive = mouth open."""
    a.const("jaw_upper", rotation=[f"-({open_deg})", 0, 0])
    a.const("jaw_lower", rotation=[open_deg, 0, 0])


def idle_p1():
    a = Anim(4.0, True)
    a.const("body", position=[0, wave(4.0, 1.1), 0],
            rotation=[wave(2.0, 1.4, 20), wave(4.0, 2.5, 60), wave(4.0, 2.4, 90)])
    a.const("front", scale=[f"1+{wave(2.0, 0.018, 0)}"] * 3)
    tails(a, 2.0, 5.5, 32)
    return a


def move_p1():
    a = Anim(1.6, True)
    a.const("body", position=[0, wave(0.8, 1.3), wave(1.6, 0.6)],
            rotation=[wave(0.8, 1.6, 20, -5.0), wave(1.6, 3.5), wave(1.6, 3.0, 90)])
    a.const("front", scale=[f"1+{wave(0.8, 0.02)}"] * 3)
    tails(a, 0.8, 7.0, 30, bias=-8.0)
    return a


def windup(length, p2):
    a = Anim(length, "hold_on_last_frame")

    def f_(t):
        return ease_out(min(1, t / (length * 0.8)))

    def body_pos(t):
        shake = (t / length) ** 1.5
        return [math.sin(t * 95) * 0.5 * shake, math.sin(t * 77) * 0.5 * shake, 7.0 * f_(t) + math.sin(t * 61) * 0.4 * shake]

    def body_rot(t):
        shake = (t / length) ** 1.5
        return [-12.0 * f_(t) + math.sin(t * 83) * 2.6 * shake, math.sin(t * 71) * 2.2 * shake,
                math.sin(t * 91) * 3.5 * shake]

    a.set("body", position=keys(body_pos, length, 0.03), rotation=keys(body_rot, length, 0.03),
          scale=keys(lambda t: [1 - 0.08 * f_(t), 1 - 0.08 * f_(t), 1 + 0.10 * f_(t)], length, 0.05))
    a.set("front", scale=keys(lambda t: [1 + 0.1 * ease_in_out(t / length)] * 3, length, 0.1))
    for i, name in enumerate(NERVE):
        a.set(name, rotation=keys(lambda t, i=i: [14.0 * ease_out(min(1, t / length)) * (1 + i * 0.1)
                                                  + math.sin(t * 40 - i) * 3 * (t / length),
                                                  math.sin(t * 22 + i) * 6 * (t / length), 0], length, 0.05))
    if p2:
        for chain, side in ((TEND_A, -1), (TEND_B, 1)):
            for i, name in enumerate(chain):
                a.set(name, rotation=keys(lambda t, i=i, side=side: [
                    -8 * ease_out(min(1, t / length)),
                    side * 30 * ease_out(min(1, t / length)) * (1 + i * 0.2) + math.sin(t * 35 + i) * 6, 0], length, 0.05))
        a.set("jaw_upper", rotation=keys(lambda t: [-34 * ease_out(min(1, t / (length * 0.7))) - math.sin(t * 70) * 1.5, 0, 0], length, 0.04))
        a.set("jaw_lower", rotation=keys(lambda t: [34 * ease_out(min(1, t / (length * 0.7))) + math.sin(t * 70) * 1.5, 0, 0], length, 0.04))
    return a


def charge(p2):
    a = Anim(0.5, True)
    spin = 720.0 if p2 else 360.0
    a.const("body", position=[0, 0, -4.0], rotation=[0, 0, f"query.anim_time*{spin:.0f}"], scale=[0.9, 0.9, 1.2])
    for i, name in enumerate(NERVE):
        a.const(name, rotation=[wave(0.25, 2.5 + i * 0.6, -25 * i, 6.0), wave(0.25, 3.0 + i * 0.5, -25 * i + 90), 0])
    if p2:
        for chain, side in ((TEND_A, -1), (TEND_B, 1)):
            for i, name in enumerate(chain):
                a.const(name, rotation=[wave(0.25, 4 + i * 2, -30 * i),
                                        f"{side * 18}+{wave(0.25, 5 + i * 2, -30 * i + 90)}", 0])
        jaws(a, f"30+{wave(0.125, 4)}")
    return a


def summon():
    L = 1.4
    a = Anim(L, "hold_on_last_frame")

    def f(t):
        f0 = math.sin(min(1, t / 0.5) * math.pi / 2)
        return f0 if t < 0.9 else f0 * (1 - ease_in_out((t - 0.9) / 0.5))

    a.set("body", position=keys(lambda t: [math.sin(t * 60) * 0.4, 2.0 * f(t), 5.0 * f(t)], L, 0.03),
          rotation=keys(lambda t: [-18.0 * f(t), math.sin(t * 50) * 3 * f(t), math.sin(t * 66) * 3 * f(t)], L, 0.03),
          scale=keys(lambda t: [1 + 0.16 * (max(0.0, math.sin((t - 0.45) / 0.45 * math.pi)) if 0.45 < t < 0.9 else 0.0)] * 3, L, 0.03))
    a.set("front", scale=keys(lambda t: [1 + 0.12 * (math.sin((t - 0.4) / 0.5 * math.pi) if 0.4 < t < 0.9 else 0)] * 3, L, 0.04))
    for i, name in enumerate(NERVE):
        a.set(name, rotation=keys(lambda t, i=i: [18 * math.sin(min(1, t / 0.6) * math.pi / 2) + math.sin(t * 30 - i) * 4,
                                                  math.sin(t * 20 + i * 0.8) * 8, 0], L, 0.05))
    return a


def transform():
    L = 3.2
    a = Anim(L, "hold_on_last_frame")

    def sc(t):
        if t < 1.5:
            s = 1 - 0.18 * ease_in_out(t / 1.5)
        elif t < 1.75:
            s = 0.82 + 0.58 * ease_out((t - 1.5) / 0.25)
        else:
            s = 1.40 - 0.40 * ease_in_out(min(1, (t - 1.75) / 1.1))
        return [s, s, s]

    def pos(t):
        k = min(1, t / 1.5)
        a_ = 1.8 * k * k if t < 1.7 else 0.5 * max(0, 1 - (t - 1.7) / 0.8)
        return [math.sin(t * 120) * a_, 2.5 * ease_in_out(min(1, t / 1.2)) + math.sin(t * 97) * a_, math.sin(t * 83) * a_]

    def rot(t):
        spin = 720 * ease_in_out(t / L) ** 1.2
        k = min(1, t / 1.5)
        shake = 6 * k * k if t < 1.7 else 6 * max(0, 1 - (t - 1.7) / 0.9)
        tilt = -8 * ease_in_out(min(1, t / 1.2)) * (1 if t < 2.2 else max(0, 1 - (t - 2.2)))
        return [tilt + math.sin(t * 90) * shake, spin, math.sin(t * 77) * shake]

    a.set("body", position=keys(pos, L, 0.025), rotation=keys(rot, L, 0.025), scale=keys(sc, L, 0.025))
    for i, name in enumerate(NERVE):
        a.set(name, rotation=keys(lambda t, i=i: [math.sin(t * 28 - i * 0.7) * (8 + i), math.sin(t * 19 + i * 0.9) * (10 + i * 1.5), 0], L, 0.04))
    for chain, side in ((TEND_A, -1), (TEND_B, 1)):
        for i, name in enumerate(chain):
            a.set(name, rotation=keys(lambda t, i=i, side=side: [
                math.sin(t * 25 + i) * 10, side * 20 * ease_in_out(min(1, t / 2)) + math.sin(t * 30 + i) * 12, 0], L, 0.04))

    def jaw(t):
        if t < 1.7:
            return 0.0
        return 40 * ease_out(min(1, (t - 1.7) / 0.5)) - 40 * ease_in_out(max(0, min(1, (t - 2.3) / 0.8)))
    a.set("jaw_upper", rotation=keys(lambda t: [-jaw(t), 0, 0], L, 0.04))
    a.set("jaw_lower", rotation=keys(lambda t: [jaw(t), 0, 0], L, 0.04))
    return a


def idle_p2():
    a = Anim(3.0, True)
    a.const("body", position=[wave(3.0, 0.6, 30), wave(1.5, 1.4), 0],
            rotation=[wave(1.5, 3.0, 40), wave(3.0, 4.0, 90), wave(3.0, 4.5)])
    a.const("front", scale=[f"1+{wave(1.0, 0.025)}"] * 3)
    tails(a, 1.5, 9.0, 36)
    jaws(a, f"10+{wave(1.0, 7.0)}")
    return a


def move_p2():
    a = Anim(1.2, True)
    a.const("body", position=[0, wave(0.6, 1.5), wave(1.2, 0.8)],
            rotation=[wave(0.6, 2.4, 20, -6.0), wave(1.2, 5.0), wave(1.2, 5.0, 90)])
    a.const("front", scale=[f"1+{wave(0.6, 0.03)}"] * 3)
    tails(a, 0.6, 10.0, 34, bias=-6.0)
    jaws(a, f"14+{wave(0.6, 8.0)}")
    return a


def recover_p2():
    """Jaws snap shut and the body recoils: played when a dash ends."""
    L = 0.9
    a = Anim(L, "hold_on_last_frame")
    a.set("body", position=keys(lambda t: [0, 0, -6.0 * math.exp(-t * 7) if t < 0.7 else 0.0], L, 0.03),
          rotation=keys(lambda t: [8 * math.sin(min(1, t / 0.9) * math.pi), 0, 0], L, 0.04),
          scale=keys(lambda t: [1 + 0.07 * math.exp(-t * 9)] * 3, L, 0.04))
    a.set("jaw_upper", rotation=keys(lambda t: [-30 * (1 - min(1, t / 0.14)), 0, 0], L, 0.02))
    a.set("jaw_lower", rotation=keys(lambda t: [30 * (1 - min(1, t / 0.14)), 0, 0], L, 0.02))
    for i, name in enumerate(NERVE):
        a.set(name, rotation=keys(lambda t, i=i: [-10 * math.exp(-t * 3) * math.cos(t * 12 - i * 0.6),
                                                  6 * math.exp(-t * 3) * math.sin(t * 10 - i * 0.5), 0], L, 0.04))
    return a


def special_p2():
    """Roar: rears back, jaws wide, shockwave at ~0.8s."""
    L = 1.8
    a = Anim(L, "hold_on_last_frame")

    def f(t):
        up = ease_out(min(1, t / 0.7))
        down = 1 - ease_in_out(max(0, min(1, (t - 1.3) / 0.5)))
        return up * down

    a.set("body", position=keys(lambda t: [math.sin(t * 100) * 0.5 * f(t), 3 * f(t) + math.sin(t * 90) * 0.5 * f(t), 6 * f(t)], L, 0.025),
          rotation=keys(lambda t: [-26 * f(t) + math.sin(t * 80) * 2 * f(t), math.sin(t * 66) * 3 * f(t), math.sin(t * 77) * 3 * f(t)], L, 0.025),
          scale=keys(lambda t: [1 + (0.2 * max(0, math.sin((t - 0.7) / 0.5 * math.pi)) if 0.7 < t < 1.2 else 0.0)] * 3, L, 0.025))
    a.set("jaw_upper", rotation=keys(lambda t: [-46 * f(t) - math.sin(t * 60) * 2 * f(t), 0, 0], L, 0.025))
    a.set("jaw_lower", rotation=keys(lambda t: [46 * f(t) + math.sin(t * 60) * 2 * f(t), 0, 0], L, 0.025))
    a.set("front", scale=keys(lambda t: [1 + 0.1 * f(t) * math.sin(t * 24)] * 3, L, 0.04))
    for i, name in enumerate(NERVE):
        a.set(name, rotation=keys(lambda t, i=i: [20 * f(t) + math.sin(t * 22 - i) * 5 * f(t), math.sin(t * 16 + i) * 9 * f(t), 0], L, 0.04))
    for chain, side in ((TEND_A, -1), (TEND_B, 1)):
        for i, name in enumerate(chain):
            a.set(name, rotation=keys(lambda t, i=i, side=side: [
                -14 * f(t), side * (36 + i * 8) * f(t) + math.sin(t * 28 + i) * 8 * f(t), 0], L, 0.04))
    return a


def death():
    L = 3.2
    a = Anim(L, "hold_on_last_frame")

    def sc(t):
        if t < 2.6:
            return [1 + 0.10 * (t / 2.6) + 0.02 * math.sin(t * 40)] * 3
        k = ease_in((t - 2.6) / 0.6)
        return [1.1 * (1 - k) + 0.001] * 3

    def amp(t):
        return min(1, t / 2.5)

    a.set("body", position=keys(lambda t: [math.sin(t * 110) * 1.4 * amp(t),
                                          3 * ease_in_out(min(1, t / 1.5)) + math.sin(t * 95) * 1.2 * amp(t),
                                          math.sin(t * 88) * 1.2 * amp(t)], L, 0.025),
          rotation=keys(lambda t: [-15 * ease_in_out(min(1, t / 1.5)) + math.sin(t * 77) * 5 * amp(t),
                                   1440 * ease_in_out(t / L) ** 1.6, math.sin(t * 69) * 6 * amp(t)], L, 0.025),
          scale=keys(sc, L, 0.025))
    a.set("jaw_upper", rotation=keys(lambda t: [-(18 + 18 * math.sin(t * 25)) * min(1, t / 0.6), 0, 0], L, 0.03))
    a.set("jaw_lower", rotation=keys(lambda t: [(18 + 18 * math.sin(t * 25)) * min(1, t / 0.6), 0, 0], L, 0.03))
    for i, name in enumerate(NERVE):
        a.set(name, rotation=keys(lambda t, i=i: [math.sin(t * 24 - i * 0.7) * (10 + i * 1.5), math.sin(t * 17 + i) * (14 + i * 2), 0], L, 0.04))
    for chain, side in ((TEND_A, -1), (TEND_B, 1)):
        for i, name in enumerate(chain):
            a.set(name, rotation=keys(lambda t, i=i, side=side: [math.sin(t * 27 + i) * 12, side * 25 + math.sin(t * 33 + i) * 16, 0], L, 0.04))
    return a


def make():
    anims = {
        "idle_p1": idle_p1(), "move_p1": move_p1(), "windup_p1": windup(0.9, False), "charge_p1": charge(False),
        "summon_p1": summon(), "transform": transform(),
        "idle_p2": idle_p2(), "move_p2": move_p2(), "windup_p2": windup(0.9, True), "charge_p2": charge(True),
        "recover_p2": recover_p2(), "special_p2": special_p2(), "death": death(),
    }
    out = {N + k: v.d for k, v in anims.items()}
    phase_of = {N + k: ["1"] for k in ("idle_p1", "move_p1", "windup_p1", "charge_p1", "summon_p1")}
    phase_of.update({N + k: ["2"] for k in ("idle_p2", "move_p2", "windup_p2", "charge_p2", "recover_p2", "special_p2")})
    phase_of[N + "transform"] = ["1", "2"]
    phase_of[N + "death"] = ["1", "2"]
    return out, phase_of
