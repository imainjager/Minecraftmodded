"""mobforge: builds GeckoLib models (geo.json), baked textures and animations from Python.

Why: hand-placing hundreds of cubes and painting a texture that wraps over them is not practical.
Instead we describe the creature as shapes (sphere shells made of thin plates, teeth, tube segments),
write a "shader" function that says what colour every point of the creature's surface should be,
and mobforge bakes that into a texture atlas with a per-face UV map.

Coordinates here are GAME space (x is mirrored to GeckoLib file space on export). One unit = 1/16 block.
The creature's front is -Z (what GeckoLib models call north). Rotations are radians, matrix = Rz*Ry*Rx,
exactly how GeckoLib applies cube rotations (checked against its source).
"""
import json
import math

# ------------------------------------------------------------------ vectors / matrices (tuples, no numpy)


def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def v_len(a): return math.sqrt(v_dot(a, a))


def v_norm(a):
    l = v_len(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-12 else (0.0, 0.0, 0.0)


def m_mul_v(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def m_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def euler_to_m(rx, ry, rz):
    """GeckoLib order: vertex is rotated by X first, then Y, then Z."""
    return m_mul(rot_z(rz), m_mul(rot_y(ry), rot_x(rx)))


def m_to_euler(m):
    """Inverse of euler_to_m."""
    sy = -m[2][0]
    sy = max(-1.0, min(1.0, sy))
    ry = math.asin(sy)
    if abs(sy) < 0.999999:
        rx = math.atan2(m[2][1], m[2][2])
        rz = math.atan2(m[1][0], m[0][0])
    else:  # gimbal lock
        rz = 0.0
        rx = math.atan2(-m[1][2], m[1][1])
    return rx, ry, rz


def frame_to_m(x_axis, y_axis, z_axis):
    """Rotation matrix whose columns are the given local axes (must be right-handed)."""
    return [[x_axis[0], y_axis[0], z_axis[0]],
            [x_axis[1], y_axis[1], z_axis[1]],
            [x_axis[2], y_axis[2], z_axis[2]]]


# ------------------------------------------------------------------ noise (value noise, deterministic)


def _h(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1442695041 + seed * 1274126177) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def noise3(x, y, z, seed=0):
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    c = lambda dx, dy, dz: _h(ix + dx, iy + dy, iz + dz, seed)
    x00 = c(0, 0, 0) + (c(1, 0, 0) - c(0, 0, 0)) * fx
    x10 = c(0, 1, 0) + (c(1, 1, 0) - c(0, 1, 0)) * fx
    x01 = c(0, 0, 1) + (c(1, 0, 1) - c(0, 0, 1)) * fx
    x11 = c(0, 1, 1) + (c(1, 1, 1) - c(0, 1, 1)) * fx
    y0 = x00 + (x10 - x00) * fy
    y1 = x01 + (x11 - x01) * fy
    return y0 + (y1 - y0) * fz


def fbm3(x, y, z, octaves=4, seed=0):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += amp * noise3(x * freq, y * freq, z * freq, seed + o * 17)
        norm += amp
        amp *= 0.5
        freq *= 2.03
    return total / norm


def ridge3(x, y, z, octaves=3, seed=0):
    """1 on thin winding lines, 0 away from them. Good for veins and cracks."""
    return 1.0 - abs(2.0 * fbm3(x, y, z, octaves, seed) - 1.0)


def worley3(x, y, z, seed=0):
    """Distance to the nearest random point (cellular noise). Returns (d1, d2)."""
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    best1 = best2 = 9.0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cx, cy, cz = ix + dx, iy + dy, iz + dz
                px = cx + _h(cx, cy, cz, seed)
                py = cy + _h(cx, cy, cz, seed + 101)
                pz = cz + _h(cx, cy, cz, seed + 202)
                d = (px - x) ** 2 + (py - y) ** 2 + (pz - z) ** 2
                if d < best1:
                    best1, best2 = d, best1
                elif d < best2:
                    best2 = d
    return math.sqrt(best1), math.sqrt(best2)


def clamp(x, lo=0.0, hi=1.0): return lo if x < lo else hi if x > hi else x
def smooth(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0)) if e1 != e0 else (1.0 if x >= e1 else 0.0)
    return t * t * (3 - 2 * t)
def mix(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))
def mixf(a, b, t): return a + (b - a) * t


# ------------------------------------------------------------------ model


FACES = ("north", "south", "east", "west", "up", "down")


class Cube:
    """A box in game space. `center` is also its rotation pivot; `rot` = (rx, ry, rz) radians."""

    def __init__(self, center, size, rot=(0.0, 0.0, 0.0), tag="", data=None):
        self.center = tuple(center)
        self.size = tuple(size)
        self.rot = tuple(rot)
        self.tag = tag
        self.data = data or {}
        self.uv = {}  # face -> (u, v, w, h) in texels, filled by Atlas

    def matrix(self):
        return euler_to_m(*self.rot)

    def corners(self):
        """The 8 named corners of GeckoLib's VertexSet, in cube-local coordinates relative to the centre."""
        hx, hy, hz = self.size[0] / 2, self.size[1] / 2, self.size[2] / 2
        return {
            "blb": (-hx, -hy, -hz), "brb": (-hx, -hy, hz), "tlb": (-hx, hy, -hz), "trb": (-hx, hy, hz),
            "tlf": (hx, hy, -hz), "trf": (hx, hy, hz), "blf": (hx, -hy, -hz), "brf": (hx, -hy, hz),
        }

    def face_vertices(self, face):
        """v0..v3 in cube-local coords, same order as GeckoLib's VertexSet quadXxx()."""
        c = self.corners()
        order = {
            "west": ("trb", "tlb", "blb", "brb"),
            "east": ("tlf", "trf", "brf", "blf"),
            "north": ("tlb", "tlf", "blf", "blb"),
            "south": ("trf", "trb", "brb", "brf"),
            "up": ("trb", "trf", "tlf", "tlb"),
            "down": ("blb", "blf", "brf", "brb"),
        }[face]
        return [c[k] for k in order]

    FACE_NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0),
                   "up": (0, 1, 0), "down": (0, -1, 0)}

    def face_size(self, face):
        """World size (u-direction length, v-direction length) of the face, in units."""
        v = self.face_vertices(face)
        # v0->v1 runs along texture -u, v1->v2 along +v
        return v_len(v_sub(v[0], v[1])), v_len(v_sub(v[2], v[1]))

    def point_on_face(self, face, s, t):
        """Model-space point for texture fractions s (0 = left edge of the texture rect) and t (0 = top)."""
        v = self.face_vertices(face)
        # texture corners: v1=(0,0) v0=(1,0) v3=(1,1) v2=(0,1)
        p = tuple((1 - s) * (1 - t) * v[1][i] + s * (1 - t) * v[0][i] + s * t * v[3][i] + (1 - s) * t * v[2][i]
                  for i in range(3))
        return v_add(self.center, m_mul_v(self.matrix(), p))

    def world_normal(self, face):
        return m_mul_v(self.matrix(), self.FACE_NORMAL[face])


class Bone:
    def __init__(self, name, pivot=(0.0, 0.0, 0.0), parent=None, rot=(0.0, 0.0, 0.0)):
        self.name, self.pivot, self.parent, self.rot = name, tuple(pivot), parent, tuple(rot)
        self.cubes = []


class Model:
    def __init__(self, identifier, texel_per_unit=3.0):
        self.identifier = identifier
        self.tpu = texel_per_unit
        self.bones = {}
        self.order = []

    def bone(self, name, pivot=(0, 0, 0), parent=None, rot=(0, 0, 0)):
        b = Bone(name, pivot, parent, rot)
        self.bones[name] = b
        self.order.append(name)
        return b

    def add(self, bone, cube):
        self.bones[bone].cubes.append(cube)
        return cube

    def all_cubes(self):
        for name in self.order:
            for c in self.bones[name].cubes:
                yield name, c

    # ---- atlas -------------------------------------------------------------------------

    def layout(self, width=1024, gutter=2, min_texels=1):
        """Gives every face of every cube a rectangle in the atlas (shelf packing)."""
        rects = []
        for _, c in self.all_cubes():
            for f in FACES:
                lw, lh = c.face_size(f)
                w = max(min_texels, round(lw * self.tpu))
                h = max(min_texels, round(lh * self.tpu))
                rects.append((c, f, w, h))
        rects.sort(key=lambda r: (-r[3], -r[2]))
        x = y = shelf = 0
        for c, f, w, h in rects:
            if x + w + gutter > width:
                x, y, shelf = 0, y + shelf + gutter, 0
            c.uv[f] = (x + gutter // 2, y + gutter // 2, w, h)
            x += w + gutter
            shelf = max(shelf, h)
        height = y + shelf + gutter
        h2 = 64
        while h2 < height:
            h2 *= 2
        self.tex_w, self.tex_h = width, h2
        return width, h2

    def bake(self, shader, fill=(255, 0, 255, 255)):
        """Paints the atlas. shader(ctx) -> (r, g, b) or (r, g, b, a) with 0..255 floats.
        ctx: dict(p=model-space point, n=surface normal, tag, cube, face, s, t)."""
        from PIL import Image
        img = Image.new("RGBA", (self.tex_w, self.tex_h), fill)
        px = img.load()
        for bname, c in self.all_cubes():
            for f in FACES:
                u, v, w, h = c.uv[f]
                n = c.world_normal(f)
                for j in range(h):
                    t = (j + 0.5) / h
                    for i in range(w):
                        s = (i + 0.5) / w
                        col = shader({"p": c.point_on_face(f, s, t), "n": n, "tag": c.tag, "cube": c,
                                      "face": f, "s": s, "t": t, "bone": bname})
                        px[u + i, v + j] = _rgba(col)
                # bleed 1 texel outwards so nearest-neighbour sampling never picks up magenta
                for k in (0, 1):
                    _bleed(px, u, v, w, h, k, self.tex_w, self.tex_h)
        return img

    # ---- export ------------------------------------------------------------------------

    def to_geo(self, bounds=(6, 6, (0, 1.5, 0))):
        bones = []
        for name in self.order:
            b = self.bones[name]
            jb = {"name": name, "pivot": [-b.pivot[0], b.pivot[1], b.pivot[2]]}
            if b.parent:
                jb["parent"] = b.parent
            if any(b.rot):
                jb["rotation"] = [-math.degrees(b.rot[0]), -math.degrees(b.rot[1]), math.degrees(b.rot[2])]
            cubes = []
            for c in b.cubes:
                cx, cy, cz = c.center
                sx, sy, sz = c.size
                jc = {"origin": [r(-(cx + sx / 2)), r(cy - sy / 2), r(cz - sz / 2)], "size": [r(sx), r(sy), r(sz)],
                      "uv": {f: {"uv": [c.uv[f][0], c.uv[f][1]], "uv_size": [c.uv[f][2], c.uv[f][3]]} for f in FACES}}
                if any(abs(a) > 1e-9 for a in c.rot):
                    jc["pivot"] = [r(-cx), r(cy), r(cz)]
                    jc["rotation"] = [r(-math.degrees(c.rot[0]), 4), r(-math.degrees(c.rot[1]), 4),
                                      r(math.degrees(c.rot[2]), 4)]
                cubes.append(jc)
            if cubes:
                jb["cubes"] = cubes
            bones.append(jb)
        return {"format_version": "1.12.0", "minecraft:geometry": [{
            "description": {"identifier": self.identifier, "texture_width": self.tex_w, "texture_height": self.tex_h,
                            "visible_bounds_width": bounds[0], "visible_bounds_height": bounds[1],
                            "visible_bounds_offset": list(bounds[2])},
            "bones": bones}]}


def r(x, nd=4):
    return round(x, nd)


def _rgba(col):
    if len(col) == 3:
        col = (*col, 255)
    return tuple(int(clamp(c, 0, 255)) for c in col)


def _bleed(px, u, v, w, h, k, tw, th):
    """Copies the outermost texels of a rect one texel outward (k=0) or two (k=1)."""
    k1 = k + 1
    for i in range(-k, w + k):
        for j, src in ((-k1, 0), (h + k, h - 1)):
            x, y = u + min(max(i, 0), w - 1), v + src
            if 0 <= u + i < tw and 0 <= v + j < th:
                px[u + i, v + j] = px[x, y]
    for j in range(-k1, h + k1):
        for i, src in ((-k1, 0), (w + k, w - 1)):
            x, y = u + src, v + min(max(j, 0), h - 1)
            if 0 <= u + i < tw and 0 <= v + j < th:
                px[u + i, v + j] = px[x, y]


# ------------------------------------------------------------------ shapes


def plate_on_sphere(center, radius, lat, lon, width, height, thick, tag, data=None):
    """A thin rectangular plate lying on a sphere at (lat, lon), outward face = cube north face.
    lat/lon radians; lon 0 faces -Z (the creature's front), +lon turns toward +X."""
    cl, sl = math.cos(lat), math.sin(lat)
    n = (cl * math.sin(lon), sl, -cl * math.cos(lon))  # outward normal
    east = (math.cos(lon), 0.0, math.sin(lon))
    north = (-sl * math.sin(lon), cl, sl * math.cos(lon))
    # right-handed local frame (x=east, y=north, z=-normal)
    m = frame_to_m(east, north, v_mul(n, -1))
    rx, ry, rz = m_to_euler(m)
    pos = v_add(center, v_mul(n, radius - thick / 2))
    return Cube(pos, (width, height, thick), (rx, ry, rz), tag, data)


def sphere_shell(center, radius, rings, seg, thick=1.5, tag="body", oversize=1.14, data_fn=None):
    """Yields (cube, lat, lon) plates covering a sphere. seg = plates around the equator."""
    out = []
    dlat = math.pi / rings
    for k in range(rings):
        lat = -math.pi / 2 + (k + 0.5) * dlat
        n = max(5, round(seg * math.cos(lat)))
        dlon = 2 * math.pi / n
        h = 2 * radius * math.tan(dlat / 2) * oversize
        # width at the wider (equator-side) edge so neighbouring plates overlap
        edge = min(abs(lat - dlat / 2), abs(lat + dlat / 2)) if abs(lat) > dlat / 2 else 0.0
        w = 2 * radius * math.cos(edge) * math.tan(dlon / 2) * oversize
        for j in range(n):
            lon = j * dlon  # lon 0 = the front (-Z); use an odd ring count so a plate sits exactly at the front
            cube = plate_on_sphere(center, radius, lat, lon, w, h, thick, tag, data_fn(lat, lon) if data_fn else None)
            out.append((cube, lat, lon))
    return out


def tube_segment(center, axis, length, radius, sides, thick, tag, twist=0.0, data=None):
    """Open polygonal tube made of `sides` plates around `axis` (a unit vector). Returns cubes."""
    axis = v_norm(axis)
    helper = (0, 1, 0) if abs(axis[1]) < 0.9 else (1, 0, 0)
    e1 = v_norm(v_cross(helper, axis))
    e2 = v_cross(axis, e1)
    out = []
    w = 2 * radius * math.tan(math.pi / sides) * 1.12
    for k in range(sides):
        a = twist + 2 * math.pi * k / sides
        n = v_add(v_mul(e1, math.cos(a)), v_mul(e2, math.sin(a)))  # outward
        # local frame: x = tangent, y = axis, z = -normal; right-handed => x = y cross z
        z = v_mul(n, -1)
        x = v_cross(axis, z)
        m = frame_to_m(x, axis, z)
        rx, ry, rz = m_to_euler(m)
        pos = v_add(center, v_mul(n, radius - thick / 2))
        out.append(Cube(pos, (w, length, thick), (rx, ry, rz), tag, dict(data or {}, ang=a)))
    return out


def oriented_box(center, size, x_axis, y_axis, tag, data=None):
    """Box with local x/y given (z is derived right-handed)."""
    x_axis, y_axis = v_norm(x_axis), v_norm(y_axis)
    z_axis = v_cross(x_axis, y_axis)
    m = frame_to_m(x_axis, y_axis, z_axis)
    return Cube(center, size, m_to_euler(m), tag, data)


# ------------------------------------------------------------------ animation helpers


def ease_in_out(t): return t * t * (3 - 2 * t)
def ease_out(t): return 1 - (1 - t) ** 3
def ease_in(t): return t ** 3


def keys(fn, length, step=0.05):
    """Samples fn(t) over [0, length] into a GeckoLib keyframe dict (linear interpolation)."""
    n = max(1, round(length / step))
    out = {}
    for i in range(n + 1):
        t = length * i / n
        out[fmt_time(t)] = [r(c, 3) if not isinstance(c, str) else c for c in fn(t)]
    return out


def fmt_time(t):
    s = f"{t:.3f}".rstrip("0").rstrip(".")
    return s if "." in s else s + ".0"


def write_json(path, data):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
