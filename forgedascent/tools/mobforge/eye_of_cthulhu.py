"""Eye of Cthulhu: model, two skins (phase 1 eyeball, phase 2 toothy maw) and animations.

Run `python tools/mobforge/build.py` from forgedascent/ to write everything. Layout of the creature:
sphere of plates (the eyeball), optic nerve tail behind it (+Z), and in phase 2 a ring of teeth around a painted maw.
The same model and UV layout is used for both phases; only the texture differs, and the phase 2 parts are hidden
in phase 1 by the game (see HIDE).
"""
import math

from forge import (Cube, Model, v_add, v_sub, v_mul, v_norm, v_len, v_dot, v_cross, noise3, fbm3, ridge3, worley3,
                   smooth, mix, mixf, clamp, plate_on_sphere, sphere_shell, tube_segment, oriented_box)

C = (0.0, 22.0, 0.0)          # eyeball centre (units; entity feet are y=0)
R = 21.0                       # eyeball radius
MOUTH_LAT0 = -0.10             # phase 2 mouth centre (radians below/above the equator)
MOUTH_A, MOUTH_B = 0.82, 0.40  # mouth half width / half height as angles on the sphere
PAINT_B = 0.50                 # painted opening is a little taller than the closed teeth ring
NERVE_N = 9
TENDRIL_N = 5


def sph(lat, lon, radius=R):
    n = (math.cos(lat) * math.sin(lon), math.sin(lat), -math.cos(lat) * math.cos(lon))
    return v_add(C, v_mul(n, radius)), n


def build():
    m = Model("geometry.eye_of_cthulhu", texel_per_unit=3.0)
    m.bone("root", C)
    m.bone("look", C, "root")
    m.bone("body", C, "look")
    m.bone("eyeball", C, "body")
    m.bone("front", C, "body")
    # mouth hinge: a horizontal line through the corners of the mouth
    hinge_lat = MOUTH_LAT0
    hinge, _ = sph(hinge_lat, MOUTH_A * 0.92, R)
    hinge = (0.0, hinge[1], hinge[2] + 1.0)
    m.bone("jaw_upper", hinge, "body")
    m.bone("jaw_lower", hinge, "body")
    m.bone("maw_fixed", C, "body")

    # ---- eyeball: odd ring count so a plate sits exactly at the front (iris centre)
    for cube, lat, lon in sphere_shell(C, R, rings=19, seg=42, thick=1.2, tag="eye", oversize=1.07):
        n = (math.cos(lat) * math.sin(lon), math.sin(lat), -math.cos(lat) * math.cos(lon))
        ang = math.acos(clamp(-n[2], -1, 1))
        m.add("front" if ang < 0.45 else "eyeball", cube)

    # ---- phase 2 mouth: lips and teeth hinge on the two jaw bones
    mid, _ = sph(MOUTH_LAT0, 0.0, R)
    for bone, sign, count, shift in (("jaw_upper", 1, 8, 0.5), ("jaw_lower", -1, 7, 1.0)):
        for k in range(count):
            f = (k + shift) / (8.0 if sign > 0 else 8.0)
            ph = math.pi * (0.07 + 0.86 * f)
            lon = MOUTH_A * math.cos(ph)
            lat = MOUTH_LAT0 + sign * MOUTH_B * math.sin(ph)
            pt, nrm = sph(lat, lon, R)
            inward = v_sub(mid, pt)
            inward = v_norm(v_sub(inward, v_mul(nrm, v_dot(inward, nrm))))
            centre_f = math.exp(-((f - 0.5) / 0.22) ** 2)
            fang = 0.8 + 0.7 * centre_f
            fang *= 0.9 + 0.25 * (((k * 5 + (3 if sign < 0 else 0)) % 4) / 3.0)
            base = v_sub(pt, v_mul(nrm, 0.9))
            parts = ((3.4 * fang, 3.6, 3.2), (3.2 * fang, 2.4, 2.1), (2.8 * fang, 1.1, 1.0))
            off = 0.0
            pos = base
            total = sum(p[0] for p in parts)
            for pi_, (length, wdt, dep) in enumerate(parts):
                # fangs curve inward the closer they get to the tip
                bend = 0.18 * pi_
                axis = v_norm(v_add(v_mul(nrm, 0.62 - bend * 2.0), v_mul(inward, 0.78 + bend * 2.0)))
                tangent = v_norm(v_cross(axis, nrm)) if abs(v_dot(axis, nrm)) < 0.99 else (1, 0, 0)
                centre = v_add(pos, v_mul(axis, length / 2 * 0.98))
                cube = oriented_box(centre, (wdt, length * 1.06, dep), tangent, axis, "tooth",
                                    {"base": base, "axis": v_norm(v_sub(v_add(pos, v_mul(axis, length)), base)), "len": total, "idx": pi_})
                m.add(bone, cube)
                pos = v_add(pos, v_mul(axis, length * 0.96))
            m.add(bone, plate_on_sphere(C, R + 1.0, lat + sign * 0.04, lon, 6.2, 4.2, 2.4, "lip"))
    # lips at the corners stay with the body
    for s_ in (-1, 1):
        for step in (0, 1):
            lon = s_ * (MOUTH_A + 0.02 + step * 0.1)
            m.add("maw_fixed", plate_on_sphere(C, R + 0.9, MOUTH_LAT0, lon, 5.0, 5.0, 2.2, "lip"))

    # ---- optic nerve: chain of short octagonal tubes curving down and back
    def chain(prefix, parent, start, dir_fn, radii, seglen, sides, tag, pivot_bone_parent, cap_at=()):
        pos = start
        par = parent
        for i, radius in enumerate(radii):
            axis = v_norm(dir_fn(i))
            name = f"{prefix}_{i + 1}"
            m.bone(name, pos, par)
            centre = v_add(pos, v_mul(axis, seglen / 2))
            for cube in tube_segment(centre, axis, seglen * 1.1, radius, sides, 1.3, tag,
                                     twist=math.pi / sides, data={"seg": i, "chain": prefix}):
                m.add(name, cube)
            end = v_add(pos, v_mul(axis, seglen))
            if i in cap_at or i == len(radii) - 1:
                # close the open tube end with two crossed slabs (an octagon-ish cap)
                helper = (0, 1, 0) if abs(axis[1]) < 0.9 else (1, 0, 0)
                ex = v_norm(v_cross(helper, axis))
                ey = v_cross(axis, ex)
                rr = radius * 0.94
                for ang in (0.0, math.pi / 4):
                    xa = v_add(v_mul(ex, math.cos(ang)), v_mul(ey, math.sin(ang)))
                    m.add(name, oriented_box(v_sub(end, v_mul(axis, 0.3)), (rr * 2 * 0.86, 1.3, rr * 2 * 0.86), xa, axis, tag,
                                             {"seg": i, "chain": prefix}))
            pos = end
            par = name

    radii = [6.4, 5.0, 4.3, 3.7, 3.2, 2.7, 2.3, 1.9, 1.6]
    # slow S-curve: sweeps down first, then back up a little
    chain("nerve", "body", (0.0, C[1] - 1.5, R - 3.0),
          lambda i: (0.18 * math.sin(i * 0.7), -0.30 + 0.07 * i, 1.0), radii, 7.0, 8, "nerve", "body", cap_at=(3,))
    for sgn, name in ((-1, "tendril_a"), (1, "tendril_b")):
        start = (sgn * 9.0, C[1] + 2.0, R * 0.93)
        chain(name, "body", start,
              lambda i, sgn=sgn: (sgn * (0.55 - 0.08 * i), 0.12 - 0.12 * i, 1.0),
              [mixf(2.6, 0.9, i / (TENDRIL_N - 1)) for i in range(TENDRIL_N)], 6.0, 6, "tendril", "body")
    return m


# ------------------------------------------------------------------ shaders


def polar(n):
    """angle from the front axis, angle around it."""
    fa = -n[2]
    return math.acos(clamp(fa, -1, 1)), math.atan2(n[1], n[0]), fa


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _vein_dist(theta, psi, j, n_main):
    """Distance (in radians of arc) from this point to vein j, plus how far along it (0..1)."""
    base = 2 * math.pi * (j + 0.35 * math.sin(j * 12.9898)) / n_main
    t0, t1 = 0.47, 1.9 + 0.5 * math.sin(j * 4.1)
    if theta < t0 - 0.02 or theta > t1:
        return 9.0, 0.0
    u = (theta - t0) / (t1 - t0)
    path = base + 0.20 * math.sin(u * 3.2 + j * 1.7) * u + 0.045 * math.sin(u * 9 + j)
    d = abs(_wrap(psi - path)) * math.sin(max(theta, 0.05))
    best, along = d, u
    # a pair of branches splitting off partway along the vein
    for sgn in (-1, 1):
        for split in (0.3, 0.55):
            if u > split:
                uu = u - split
                bp = path + sgn * (0.42 * uu + 0.25 * uu * uu) * (1.0 + 0.3 * math.sin(j * 3.3 + split))
                db = abs(_wrap(psi - bp)) * math.sin(max(theta, 0.05))
                if db < best:
                    best, along = db + uu * 0.012, u
    return best, along


def sclera(n, theta, psi, fa, blood):
    """The white of the eye with branching veins. blood 0..1 = how bloodshot."""
    base = (243.0, 235.0, 224.0)
    mott = fbm3(n[0] * 6, n[1] * 6, n[2] * 6, 3, 3)
    col = mix(base, (222.0, 205.0, 188.0), clamp(mott * 1.4 - 0.2) * 0.7)
    col = mix(col, (236.0, 190.0, 160.0), smooth(0.9, 0.45, theta) * 0.0)
    col = mix(col, (222.0, 150.0, 146.0), smooth(0.3, -0.9, fa) * 0.55)
    # veins: ~16 trunks leaving the iris, each branching twice
    best, along = 9.0, 0.0
    if theta < 2.5:
        n_main = 16
        for j in range(n_main):
            d, al = _vein_dist(theta, psi, j, n_main)
            if d < best:
                best, along = d, al
    width = 0.026 * (1 - along) ** 1.2 + 0.0105
    wob = noise3(psi * 7, theta * 9, 2.0, 71) - 0.5
    d = best + wob * 0.006
    core = smooth(width, width * 0.35, d)
    halo = smooth(width * 3.2, width * 0.5, d) * 0.35
    k = (0.55 + 0.6 * blood)
    col = mix(col, (236.0, 150.0, 146.0), halo * k * (1 - along * 0.6))
    col = mix(col, (160.0, 20.0, 32.0), clamp(core * k * 1.4))
    # fine capillary net everywhere
    w = fbm3(n[0] * 3.0 + 9, n[1] * 3.0, n[2] * 3.0, 2, 11)
    net = ridge3(n[0] * 11 + w, n[1] * 11 - w, n[2] * 11 + w, 2, 31)
    col = mix(col, (206.0, 96.0, 100.0), smooth(0.972, 0.992, net) * smooth(0.8, -0.3, fa) * 0.7 * k)
    # redder rim around the iris
    col = mix(col, (230.0, 170.0, 150.0), smooth(0.75, 0.47, theta) * 0.35)
    return col


def iris(n, theta, psi, ir, pupil, hues, slit=False):
    fib = noise3(psi * 4.0, theta * 18, 0.5, 9)
    fib2 = noise3(psi * 11.0, theta * 6, 1.5, 4)
    rr = clamp(theta / ir)
    inner, mid, outer = hues
    col = mix(inner, mid, smooth(0.28, 0.55, rr))
    col = mix(col, outer, smooth(0.62, 0.92, rr))
    col = mix(col, tuple(c * 0.55 for c in col), (fib2 - 0.5) * 0.9 + 0.25)
    col = mix(col, tuple(min(255, c * 1.35) for c in col), clamp(fib - 0.45) * 0.9)
    col = mix(col, tuple(c * 0.25 for c in outer), smooth(0.86, 1.0, rr))     # limbal ring
    return col


def eyeball_p1(p, center=C, red=False):
    n = v_norm(v_sub(p, center))
    theta, psi, fa = polar(n)
    col = sclera(n, theta, psi, fa, 1.0 if red else 0.8)
    ir = 0.46
    if theta < ir + 0.05:
        hues = ((255.0, 200.0, 40.0), (214.0, 70.0, 30.0), (92.0, 16.0, 24.0)) if red else ((238.0, 172.0, 40.0), (92.0, 152.0, 56.0), (18.0, 84.0, 112.0))
        i_col = iris(n, theta, psi, ir, 0.2, hues)
        pupil = 0.20
        i_col = mix(i_col, (6.0, 4.0, 8.0), smooth(pupil + 0.025, pupil - 0.01, theta))
        col = mix(col, i_col, smooth(ir + 0.04, ir - 0.01, theta))
        for hx, hy, hr, hs in ((-0.24, 0.27, 0.09, 1.0), (0.18, -0.21, 0.042, 0.6)):
            hn = v_norm((hx, hy, -1.0))
            d = math.acos(clamp(v_dot(n, hn), -1, 1))
            col = mix(col, (255.0, 255.0, 255.0), smooth(hr, hr * 0.45, d) * hs)
    if fa < -0.80:
        col = mix(col, (150.0, 40.0, 56.0), smooth(-0.80, -0.97, fa))
    return col


def lonlat(n):
    return math.atan2(n[0], -n[2]), math.asin(clamp(n[1], -1, 1))


def eyeball_p2(p):
    n = v_norm(v_sub(p, C))
    lon, lat = lonlat(n)
    theta, psi, fa = polar(n)
    # raw, angry flesh: dark red with pale lumps and thick dark veins
    cell, cell2 = worley3(n[0] * 7, n[1] * 7, n[2] * 7, 4)
    lump = smooth(0.15, 0.55, cell2 - cell)
    mott = fbm3(n[0] * 5, n[1] * 5, n[2] * 5, 3, 8)
    col = mix((120.0, 22.0, 34.0), (176.0, 52.0, 58.0), mott)
    col = mix(col, (196.0, 96.0, 92.0), (1 - lump) * 0.35)
    w = fbm3(n[0] * 2.5, n[1] * 2.5, n[2] * 2.5, 2, 12)
    vein = ridge3(n[0] * 4.4 + w, n[1] * 4.4 - w, n[2] * 4.4 + w, 3, 15)
    col = mix(col, (52.0, 6.0, 22.0), smooth(0.90, 0.965, vein) * 0.9)
    vein2 = ridge3(n[0] * 10 - w, n[1] * 10 + w, n[2] * 10, 2, 33)
    col = mix(col, (80.0, 10.0, 30.0), smooth(0.95, 0.985, vein2) * 0.7)
    # the remains of the eye, glaring above the mouth
    elat, ev = 0.78, None
    ex, ey = lon, lat - elat
    d = math.sqrt((ex / 1.15) ** 2 + ey ** 2)
    if d < 0.34:
        lid = smooth(0.34, 0.30, d)
        white = mix((236.0, 214.0, 190.0), (205.0, 120.0, 110.0), smooth(0.1, 0.34, d))
        col = mix(col, white, lid)
        irr = d / 0.34
        if d < 0.20:
            ic = mix((255.0, 200.0, 30.0), (200.0, 40.0, 20.0), smooth(0.2, 0.9, d / 0.2))
            ic = mix(ic, (60.0, 8.0, 10.0), smooth(0.80, 1.0, d / 0.2))
            col = mix(col, ic, smooth(0.20, 0.17, d))
            # vertical slit pupil
            slit = smooth(0.045, 0.02, abs(ex / 1.15)) * smooth(0.19, 0.12, abs(ey))
            col = mix(col, (6.0, 2.0, 4.0), slit)
        # heavy brow shadow
        col = mix(col, (70.0, 10.0, 24.0), smooth(0.30, 0.38, d) * smooth(0.32, 0.46, d) * 0.6)
    # the maw
    mx, my = lon, lat - MOUTH_LAT0
    e = (mx / MOUTH_A) ** 2 + (my / PAINT_B) ** 2
    if e < 1.55:
        gum = mix((176.0, 60.0, 84.0), (214.0, 112.0, 124.0), fbm3(n[0] * 14, n[1] * 14, n[2] * 14, 2, 41))
        col = mix(col, gum, smooth(1.55, 1.15, e))
    if e < 1.12:
        depth = clamp(1.0 - e)
        inner = mix((120.0, 20.0, 44.0), (14.0, 0.0, 8.0), smooth(0.0, 0.55, depth))
        ridges = 0.5 + 0.5 * math.sin(e * 38.0 + fbm3(n[0] * 8, n[1] * 8, n[2] * 8, 2, 5) * 6.0)
        inner = mix(inner, tuple(c * 0.55 for c in inner), ridges * 0.5 * smooth(0.05, 0.4, depth))
        # tongue
        tx, ty = mx / 0.46, (my + 0.16) / 0.2
        tg = tx * tx + ty * ty
        if my < 0.05 and tg < 1.0:
            tongue = mix((200.0, 84.0, 112.0), (140.0, 36.0, 72.0), smooth(0.0, 1.0, tg))
            tongue = mix(tongue, (232.0, 130.0, 150.0), smooth(0.9, 0.0, abs(tx)) * 0.25)
            inner = mix(inner, tongue, smooth(1.0, 0.8, tg))
        col = mix(col, inner, smooth(1.12, 1.0, e))
    if fa < -0.80:
        col = mix(col, (90.0, 10.0, 28.0), smooth(-0.80, -0.97, fa))
    return col


def nerve_color(p, ctx, phase):
    base = (222.0, 104.0, 112.0) if phase == 1 else (176.0, 44.0, 62.0)
    ring = 0.5 + 0.5 * math.sin(p[2] * 0.9 + p[1] * 0.4)
    col = mix(base, tuple(c * 0.72 for c in base), ring * 0.5)
    vein = ridge3(p[0] * 0.22, p[1] * 0.22, p[2] * 0.22, 3, 40)
    col = mix(col, (96.0, 14.0, 34.0), smooth(0.9, 0.98, vein))
    col = mix(col, tuple(c * 0.8 for c in col), fbm3(p[0] * 0.5, p[1] * 0.5, p[2] * 0.5, 2, 3) * 0.6)
    return col


def tooth_color(p, ctx):
    d = ctx["cube"].data
    t = clamp(v_dot(v_sub(p, d["base"]), d["axis"]) / d["len"])
    col = mix((150.0, 112.0, 86.0), (246.0, 238.0, 214.0), smooth(0.0, 0.5, t))
    col = mix(col, (255.0, 252.0, 240.0), smooth(0.6, 1.0, t) * 0.5)
    grain = fbm3(p[0] * 0.9, p[1] * 0.9, p[2] * 2.2, 2, 50)
    return mix(col, tuple(c * 0.86 for c in col), grain * 0.5)


def lip_color(p):
    n = fbm3(p[0] * 0.4, p[1] * 0.4, p[2] * 0.4, 3, 61)
    return mix((172.0, 48.0, 74.0), (222.0, 118.0, 134.0), n)


def make_shader(phase):
    def shader(ctx):
        tag = ctx["tag"]
        p = ctx["p"]
        if tag == "eye":
            return eyeball_p1(p) if phase == 1 else eyeball_p2(p)
        if tag in ("nerve", "tendril"):
            return nerve_color(p, ctx, phase)
        if tag == "tooth":
            return tooth_color(p, ctx)
        if tag == "lip":
            return lip_color(p)
        return (255, 0, 255)
    return shader


def make_glow_shader(phase, center=C):
    """Emissive layer: the parts that keep glowing in the dark (alpha = strength)."""
    base = make_shader(phase)

    def shader(ctx):
        if ctx["tag"] != "eye":
            return (0, 0, 0, 0)
        p = ctx["p"]
        n = v_norm(v_sub(p, center))
        theta, psi, fa = polar(n)
        if phase == 1:
            if 0.215 < theta < 0.47:
                return (*base(ctx)[:3], 215)
            return (0, 0, 0, 0)
        lon, lat = lonlat(n)
        ex, ey = lon / 1.15, lat - 0.78
        d = math.sqrt(ex * ex + ey * ey)
        if d < 0.20 and abs(ex) > 0.04:
            return (*base(ctx)[:3], 255)
        e = (lon / MOUTH_A) ** 2 + ((lat - MOUTH_LAT0) / PAINT_B) ** 2
        if e < 0.8:
            return (*base(ctx)[:3], int(150 * smooth(0.8, 0.2, e)))
        return (0, 0, 0, 0)
    return shader


PHASES = [1, 2]
TEXTURES = {1: "eye_of_cthulhu", 2: "eye_of_cthulhu_phase2"}
BOUNDS = (8, 8, (0, 1.5, 0))
CAM_DIST = 9.0
CAM_TARGET = [0, 1.4, 0.5]
JAWS = ["jaw_upper", "jaw_lower", "maw_fixed"]
TENDRILS = [f"tendril_{s}_{i}" for s in "ab" for i in range(1, TENDRIL_N + 1)]
HIDE = {"1": JAWS + TENDRILS + ["nerve_5"], "2": []}


def mixf(a, b, t):
    return a + (b - a) * t


def animations():
    from eoc_anim import make
    return make()
