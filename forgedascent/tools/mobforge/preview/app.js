// mobforge preview: renders a GeckoLib .geo.json + .animation.json with its texture, the way GeckoLib does
// (same cube/UV/pivot/rotation rules, read from GeckoLib 4.8 source), so what you see here is what the game draws.
// Everything is plain WebGL, no libraries. Open index.html?model=eye_of_cthulhu&anim=idle_p1&view=front
'use strict';

const DEG = Math.PI / 180;
const qs = new URLSearchParams(location.search);

// ------------------------------------------------------------------ small matrix library (column-major)
const M = {
  ident() { return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]); },
  mul(a, b) {
    const o = new Float32Array(16);
    for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
      let s = 0; for (let k = 0; k < 4; k++) s += a[k*4 + r] * b[c*4 + k];
      o[c*4 + r] = s;
    }
    return o;
  },
  translate(x, y, z) { const m = M.ident(); m[12] = x; m[13] = y; m[14] = z; return m; },
  scale(x, y, z) { const m = M.ident(); m[0] = x; m[5] = y; m[10] = z; return m; },
  rotX(a) { const c = Math.cos(a), s = Math.sin(a), m = M.ident(); m[5] = c; m[6] = s; m[9] = -s; m[10] = c; return m; },
  rotY(a) { const c = Math.cos(a), s = Math.sin(a), m = M.ident(); m[0] = c; m[2] = -s; m[8] = s; m[10] = c; return m; },
  rotZ(a) { const c = Math.cos(a), s = Math.sin(a), m = M.ident(); m[0] = c; m[1] = s; m[4] = -s; m[5] = c; return m; },
  // GeckoLib: poseStack.mulPose(Rz); mulPose(Ry); mulPose(Rx)  => M = Rz * Ry * Rx
  rzyx(x, y, z) { return M.mul(M.rotZ(z), M.mul(M.rotY(y), M.rotX(x))); },
  perspective(fovy, aspect, near, far) {
    const f = 1 / Math.tan(fovy / 2), m = new Float32Array(16);
    m[0] = f / aspect; m[5] = f; m[10] = (far + near) / (near - far); m[11] = -1; m[14] = 2 * far * near / (near - far);
    return m;
  },
  lookAt(e, t, u) {
    let zx = e[0]-t[0], zy = e[1]-t[1], zz = e[2]-t[2], zl = Math.hypot(zx, zy, zz); zx/=zl; zy/=zl; zz/=zl;
    let xx = u[1]*zz - u[2]*zy, xy = u[2]*zx - u[0]*zz, xz = u[0]*zy - u[1]*zx, xl = Math.hypot(xx, xy, xz); xx/=xl; xy/=xl; xz/=xl;
    const yx = zy*xz - zz*xy, yy = zz*xx - zx*xz, yz = zx*xy - zy*xx;
    return new Float32Array([xx,yx,zx,0, xy,yy,zy,0, xz,yz,zz,0, -(xx*e[0]+xy*e[1]+xz*e[2]), -(yx*e[0]+yy*e[1]+yz*e[2]), -(zx*e[0]+zy*e[1]+zz*e[2]), 1]);
  },
  point(m, x, y, z) { return [m[0]*x + m[4]*y + m[8]*z + m[12], m[1]*x + m[5]*y + m[9]*z + m[13], m[2]*x + m[6]*y + m[10]*z + m[14]]; },
  dir(m, x, y, z) { return [m[0]*x + m[4]*y + m[8]*z, m[1]*x + m[5]*y + m[9]*z, m[2]*x + m[6]*y + m[10]*z]; },
};

// ------------------------------------------------------------------ Molang subset
const molangMath = {
  sin: d => Math.sin(d * DEG), cos: d => Math.cos(d * DEG), abs: Math.abs, sqrt: Math.sqrt, pow: Math.pow,
  min: Math.min, max: Math.max, floor: Math.floor, ceil: Math.ceil, round: Math.round, pi: Math.PI,
  clamp: (v, lo, hi) => Math.min(hi, Math.max(lo, v)), lerp: (a, b, t) => a + (b - a) * t,
  mod: (a, b) => a % b, exp: Math.exp, ln: Math.log, asin: v => Math.asin(v) / DEG, acos: v => Math.acos(v) / DEG,
  atan2: (y, x) => Math.atan2(y, x) / DEG, random: Math.random, trunc: Math.trunc,
};
const exprCache = new Map();
function evalValue(v, env) {
  if (typeof v === 'number') return v;
  if (typeof v === 'string') {
    let f = exprCache.get(v);
    if (!f) {
      const src = v.replace(/query\.anim_time|query\.life_time/g, 'q.t').replace(/query\.([a-z_]+)/g, 'q.$1')
                   .replace(/variable\.([a-z_]+)/g, 'q.$1').replace(/\bmath\./g, 'math.');
      f = new Function('q', 'math', 'return (' + src + ');');
      exprCache.set(v, f);
    }
    return f(env, molangMath);
  }
  return 0;
}

// ------------------------------------------------------------------ model loading
class Model {
  constructor(geo, anims) {
    const g = geo['minecraft:geometry'][0];
    this.tw = g.description.texture_width; this.th = g.description.texture_height;
    this.bones = new Map();
    this.order = [];
    for (const b of g.bones) {
      const bone = {
        name: b.name, parent: b.parent || null, children: [],
        pivot: [-(b.pivot?.[0] ?? 0) / 16, (b.pivot?.[1] ?? 0) / 16, (b.pivot?.[2] ?? 0) / 16],
        rot: [-(b.rotation?.[0] ?? 0) * DEG, -(b.rotation?.[1] ?? 0) * DEG, (b.rotation?.[2] ?? 0) * DEG],
        cubes: [], hidden: false,
      };
      this.bones.set(b.name, bone);
      for (const c of (b.cubes || [])) bone.cubes.push(this.buildCube(c));
    }
    // topological order (parents first)
    const seen = new Set();
    const visit = b => {
      if (seen.has(b.name)) return; if (b.parent) visit(this.bones.get(b.parent));
      seen.add(b.name); this.order.push(b); if (b.parent) this.bones.get(b.parent).children.push(b);
    };
    for (const b of this.bones.values()) visit(b);
    this.anims = anims ? anims.animations : {};
    this.cubeCount = 0; this.quadCount = 0;
    for (const b of this.order) for (const c of b.cubes) { this.cubeCount++; this.quadCount += 6; }
    this.buildBuffers();
  }

  buildCube(c) {
    const s = c.size, o = c.origin;
    const x0 = -(o[0] + s[0]) / 16, y0 = o[1] / 16, z0 = o[2] / 16;
    const x1 = x0 + s[0] / 16, y1 = y0 + s[1] / 16, z1 = z0 + s[2] / 16;
    const P = {
      blb: [x0,y0,z0], brb: [x0,y0,z1], tlb: [x0,y1,z0], trb: [x0,y1,z1],
      tlf: [x1,y1,z0], trf: [x1,y1,z1], blf: [x1,y0,z0], brf: [x1,y0,z1],
    };
    const order = {
      west: ['trb','tlb','blb','brb'], east: ['tlf','trf','brf','blf'], north: ['tlb','tlf','blf','blb'],
      south: ['trf','trb','brb','brf'], up: ['trb','trf','tlf','tlb'], down: ['blb','blf','brf','brb'],
    };
    const normals = { west: [-1,0,0], east: [1,0,0], north: [0,0,-1], south: [0,0,1], up: [0,1,0], down: [0,-1,0] };
    const pivot = c.pivot ? [-c.pivot[0] / 16, c.pivot[1] / 16, c.pivot[2] / 16] : [0, 0, 0];
    const rot = c.rotation ? [-c.rotation[0] * DEG, -c.rotation[1] * DEG, c.rotation[2] * DEG] : [0, 0, 0];
    const quads = [];
    for (const f of Object.keys(order)) {
      const uvd = c.uv[f]; if (!uvd) continue;
      const [u, v] = uvd.uv, [uw, vh] = uvd.uv_size;
      const uL = u / this.tw, uR = (u + uw) / this.tw, vT = v / this.th, vB = (v + vh) / this.th;
      quads.push({
        verts: order[f].map(k => P[k]),
        uvs: [[uR, vT], [uL, vT], [uL, vB], [uR, vB]],
        normal: normals[f],
      });
    }
    return { quads, pivot, rot };
  }

  buildBuffers() {
    let n = 0;
    for (const b of this.order) for (const c of b.cubes) n += c.quads.length;
    this.nQuads = n;
    this.uv = new Float32Array(n * 8);
    this.idx = new Uint16Array(n * 6);
    this.pos = new Float32Array(n * 12);
    this.shade = new Float32Array(n * 4);
    let q = 0;
    for (const b of this.order) for (const c of b.cubes) for (const quad of c.quads) {
      for (let i = 0; i < 4; i++) { this.uv[q*8 + i*2] = quad.uvs[i][0]; this.uv[q*8 + i*2 + 1] = quad.uvs[i][1]; }
      const base = q * 4;
      this.idx.set([base, base+1, base+2, base, base+2, base+3], q * 6);
      quad.index = q++;
    }
  }

  clip(name) { return this.anims[name]; }

  // evaluate an animation at time t (seconds): fills bone.anim = {rot, pos, scale}
  pose(animName, t, loopOverride) {
    for (const b of this.order) b.anim = { rot: [0,0,0], pos: [0,0,0], scale: [1,1,1] };
    const a = animName ? this.anims[animName] : null;
    if (!a) return 0;
    const len = a.animation_length || 1;
    let time = t;
    const loop = loopOverride ?? a.loop;
    if (loop === true) time = ((t % len) + len) % len;
    else time = Math.min(t, len);
    const env = { t: time };
    for (const [bn, chans] of Object.entries(a.bones || {})) {
      const bone = this.bones.get(bn); if (!bone) continue;
      if (chans.rotation) { const v = sample(chans.rotation, time, env); bone.anim.rot = [-v[0] * DEG, -v[1] * DEG, v[2] * DEG]; }
      if (chans.position) { bone.anim.pos = sample(chans.position, time, env); }
      if (chans.scale) { bone.anim.scale = sample(chans.scale, time, env, true); }
    }
    return len;
  }

  // transforms every vertex into world space (model space) for the current pose
  update(hidden) {
    const world = new Map();
    const shade = this.shade;
    for (const b of this.order) {
      const parent = b.parent ? world.get(b.parent) : M.ident();
      const px = b.pivot[0], py = b.pivot[1], pz = b.pivot[2];
      let m = M.mul(parent, M.translate(-b.anim.pos[0] / 16, b.anim.pos[1] / 16, b.anim.pos[2] / 16));
      m = M.mul(m, M.translate(px, py, pz));
      m = M.mul(m, M.rzyx(b.rot[0] + b.anim.rot[0], b.rot[1] + b.anim.rot[1], b.rot[2] + b.anim.rot[2]));
      m = M.mul(m, M.scale(b.anim.scale[0], b.anim.scale[1], b.anim.scale[2]));
      m = M.mul(m, M.translate(-px, -py, -pz));
      world.set(b.name, m);
      const hide = hidden && hidden.has(b.name);
      b.hiddenNow = hide || (b.parent && this.bones.get(b.parent).hiddenNow);
      for (const c of b.cubes) {
        let cm = M.mul(m, M.translate(c.pivot[0], c.pivot[1], c.pivot[2]));
        cm = M.mul(cm, M.rzyx(c.rot[0], c.rot[1], c.rot[2]));
        cm = M.mul(cm, M.translate(-c.pivot[0], -c.pivot[1], -c.pivot[2]));
        for (const quad of c.quads) {
          const qi = quad.index;
          for (let i = 0; i < 4; i++) {
            const v = quad.verts[i];
            const p = b.hiddenNow ? [0, -100, 0] : M.point(cm, v[0], v[1], v[2]);
            this.pos[qi*12 + i*3] = p[0]; this.pos[qi*12 + i*3 + 1] = p[1]; this.pos[qi*12 + i*3 + 2] = p[2];
          }
          const n = M.dir(cm, quad.normal[0], quad.normal[1], quad.normal[2]);
          const nl = Math.hypot(n[0], n[1], n[2]) || 1;
          const nx = n[0]/nl, ny = n[1]/nl, nz = n[2]/nl;
          // Minecraft entity lighting (Lighting.setupForEntityInInventory-style two lights)
          const L0 = [0.2, 1.0, -0.7], L1 = [-0.2, 1.0, 0.7];
          const l0 = Math.hypot(...L0), l1 = Math.hypot(...L1);
          const d0 = Math.max(0, (nx*L0[0] + ny*L0[1] + nz*L0[2]) / l0);
          const d1 = Math.max(0, (nx*L1[0] + ny*L1[1] + nz*L1[2]) / l1);
          const sh = Math.min(1, 0.4 + 0.6 * (d0 + d1));
          shade[qi*4] = shade[qi*4+1] = shade[qi*4+2] = shade[qi*4+3] = sh;
        }
      }
    }
  }
}

function sample(track, time, env, isScale) {
  // track: {"0.0": [x,y,z] | {vector:[..]} | number} or a direct vector array/number
  if (Array.isArray(track) || typeof track === 'number' || typeof track === 'string') {
    return vec(track, env, isScale);
  }
  const ks = Object.keys(track).map(Number).sort((a, b) => a - b);
  const raw = k => track[Object.keys(track).find(x => Number(x) === k)];
  const val = k => {
    let v = raw(k);
    if (v && !Array.isArray(v) && typeof v === 'object') v = v.vector ?? v.post ?? v.pre;
    return vec(v, env, isScale);
  };
  if (!ks.length) return isScale ? [1,1,1] : [0,0,0];
  if (time <= ks[0]) return val(ks[0]);
  if (time >= ks[ks.length - 1]) return val(ks[ks.length - 1]);
  let i = 0; while (ks[i + 1] < time) i++;
  const a = val(ks[i]), b = val(ks[i + 1]), f = (time - ks[i]) / (ks[i + 1] - ks[i]);
  return [a[0] + (b[0]-a[0]) * f, a[1] + (b[1]-a[1]) * f, a[2] + (b[2]-a[2]) * f];
}
function vec(v, env, isScale) {
  if (Array.isArray(v)) return [evalValue(v[0], env), evalValue(v[1], env), evalValue(v[2], env)];
  const n = evalValue(v, env);
  return isScale ? [n, n, n] : [n, n, n];
}

// ------------------------------------------------------------------ GL
let gl, prog, floorProg, texture, model, canvas;
const state = { anim: qs.get('anim') || '', t: parseFloat(qs.get('t') || '0'), phase: qs.get('phase') || '1',
  view: qs.get('view') || 'q1', playing: qs.get('play') !== '0', speed: 1, mode: qs.get('mode') || 'live',
  ref: qs.get('ref') !== '0', bg: qs.get('bg') || 'dusk', dist: parseFloat(qs.get('dist') || '0'), az: null, el: null };
let manifest, entry, atlasImg;
const VIEWS = {
  front: [0, 8], back: [180, 8], left: [-90, 8], right: [90, 8], top: [0, 85], bottom: [0, -60],
  q1: [35, 20], q2: [-40, 15], q3: [150, 25], low: [20, -12],
};

const VS = `attribute vec3 aPos; attribute vec2 aUv; attribute float aShade; uniform mat4 uVP; varying vec2 vUv; varying float vShade;
void main(){ vUv=aUv; vShade=aShade; gl_Position=uVP*vec4(aPos,1.0); }`;
const FS = `precision mediump float; uniform sampler2D uTex; varying vec2 vUv; varying float vShade; uniform float uFlash;
void main(){ vec4 c=texture2D(uTex,vUv); if(c.a<0.1) discard; gl_FragColor=vec4(c.rgb*vShade+vec3(uFlash,0.0,0.0)*0.5,1.0); }`;
const FVS = `attribute vec3 aPos; attribute vec3 aCol; uniform mat4 uVP; varying vec3 vCol; void main(){ vCol=aCol; gl_Position=uVP*vec4(aPos,1.0);} `;
const FFS = `precision mediump float; varying vec3 vCol; void main(){ gl_FragColor=vec4(vCol,1.0);} `;

function compile(vs, fs) {
  const mk = (t, s) => { const sh = gl.createShader(t); gl.shaderSource(sh, s); gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh)); return sh; };
  const p = gl.createProgram(); gl.attachShader(p, mk(gl.VERTEX_SHADER, vs)); gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); return p;
}

let buf = {};
function setupGL() {
  canvas = document.getElementById('c');
  gl = canvas.getContext('webgl', { antialias: true, preserveDrawingBuffer: true });
  prog = compile(VS, FS); floorProg = compile(FVS, FFS);
  buf.pos = gl.createBuffer(); buf.uv = gl.createBuffer(); buf.shade = gl.createBuffer(); buf.idx = gl.createBuffer();
  buf.fpos = gl.createBuffer(); buf.fcol = gl.createBuffer();
}

function loadImage(url) {
  return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error('no ' + url)); i.src = url + '?' + Date.now(); });
}

function setTexture(img) {
  if (!texture) texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  atlasImg = img;
}

// reference scenery: floor grid, a 1-block cube and a 1.8 block "player"
function sceneryGeometry() {
  const P = [], C = [];
  const box = (x0,y0,z0,x1,y1,z1,col) => {
    const f = (a,b,c,d,sh) => { for (const i of [a,b,c,a,c,d]) { P.push(...i); C.push(col[0]*sh, col[1]*sh, col[2]*sh); } };
    const v = [[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]];
    f(v[0],v[1],v[2],v[3],0.75); f(v[5],v[4],v[7],v[6],0.75); f(v[4],v[0],v[3],v[7],0.6); f(v[1],v[5],v[6],v[2],0.6); f(v[3],v[2],v[6],v[7],1.0); f(v[4],v[5],v[1],v[0],0.5);
  };
  // floor tiles (checker, 1 block each)
  for (let x = -8; x < 8; x++) for (let z = -8; z < 8; z++) {
    const c = ((x + z) & 1) ? [0.28,0.32,0.26] : [0.24,0.28,0.22];
    box(x, -0.05, z, x+1, 0, z+1, c);
  }
  if (state.ref) {
    // player reference (0.6 x 1.8 x 0.6) and one-block cube
    box(3.2, 0, -0.3, 3.8, 0.7, 0.3, [0.2,0.25,0.7]);          // legs/body
    box(3.2, 0.7, -0.3, 3.8, 1.4, 0.3, [0.2,0.55,0.6]);
    box(3.275, 1.4, -0.25, 3.725, 1.85, 0.25, [0.78,0.6,0.45]);  // head
    box(-4.5, 0, -0.5, -3.5, 1, 0.5, [0.5,0.5,0.5]);             // 1 block
  }
  return { P: new Float32Array(P), C: new Float32Array(C) };
}
let scenery;

function bgColor() {
  return { dusk: [0.16, 0.18, 0.28], day: [0.55, 0.72, 0.92], night: [0.04, 0.05, 0.10], dark: [0.07, 0.07, 0.08], light: [0.85, 0.85, 0.88] }[state.bg] || [0.16, 0.18, 0.28];
}

function drawScene(vp, x, y, w, h) {
  gl.viewport(x, y, w, h); gl.enable(gl.SCISSOR_TEST); gl.scissor(x, y, w, h);
  const bg = bgColor(); gl.clearColor(bg[0], bg[1], bg[2], 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);
  // scenery
  gl.useProgram(floorProg);
  gl.uniformMatrix4fv(gl.getUniformLocation(floorProg, 'uVP'), false, vp);
  attr(floorProg, 'aPos', buf.fpos, 3, scenery.P); attr(floorProg, 'aCol', buf.fcol, 3, scenery.C);
  gl.drawArrays(gl.TRIANGLES, 0, scenery.P.length / 3);
  // model
  gl.useProgram(prog);
  gl.uniformMatrix4fv(gl.getUniformLocation(prog, 'uVP'), false, vp);
  gl.uniform1f(gl.getUniformLocation(prog, 'uFlash'), parseFloat(qs.get('flash') || '0'));
  attr(prog, 'aPos', buf.pos, 3, model.pos); attr(prog, 'aUv', buf.uv, 2, model.uv); attr(prog, 'aShade', buf.shade, 1, expandShade());
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, buf.idx); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, model.idx, gl.DYNAMIC_DRAW);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.uniform1i(gl.getUniformLocation(prog, 'uTex'), 0);
  gl.drawElements(gl.TRIANGLES, model.idx.length, gl.UNSIGNED_SHORT, 0);
  gl.disable(gl.SCISSOR_TEST);
}
function expandShade() { return model.shade; }
function attr(p, name, b, size, data) {
  const loc = gl.getAttribLocation(p, name);
  gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW);
  gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
}

function camera(view, aspect, extra) {
  let [az, el] = VIEWS[view] || VIEWS.q1;
  if (state.az !== null) az = state.az; if (state.el !== null) el = state.el;
  const dist = state.dist || (entry.camDist || 7.5) * (extra || 1);
  const tgt = entry.camTarget || [0, 1.4, 0];
  const a = az * DEG, e = el * DEG;
  const eye = [tgt[0] + dist * Math.sin(a) * Math.cos(e), tgt[1] + dist * Math.sin(e), tgt[2] - dist * Math.cos(a) * Math.cos(e)];
  const proj = M.perspective(40 * DEG, aspect, 0.1, 100);
  return M.mul(proj, M.lookAt(eye, tgt, [0, 1, 0]));
}

function hiddenSet() { return new Set((entry.hide || {})[state.phase] || []); }

function render() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  gl.disable(gl.SCISSOR_TEST);
  const hidden = hiddenSet();
  if (state.mode === 'sheet') {
    const views = (qs.get('views') || 'front,back,left,right,top,q1').split(',');
    model.pose(state.anim, state.t); model.update(hidden);
    const cols = Math.min(3, views.length), rows = Math.ceil(views.length / cols);
    const tw = Math.floor(w / cols), th = Math.floor(h / rows);
    views.forEach((v, i) => {
      const cx = (i % cols) * tw, cy = h - (Math.floor(i / cols) + 1) * th;
      drawScene(camera(v, tw / th, parseFloat(qs.get('zoom') || '1')), cx, cy, tw, th);
    });
    return;
  }
  if (state.mode === 'film') {
    const frames = parseInt(qs.get('frames') || '8');
    const len = model.pose(state.anim, 0) || 1;
    const cols = Math.min(4, frames), rows = Math.ceil(frames / cols);
    const tw = Math.floor(w / cols), th = Math.floor(h / rows);
    for (let i = 0; i < frames; i++) {
      model.pose(state.anim, len * i / frames, true); model.update(hidden);
      const cx = (i % cols) * tw, cy = h - (Math.floor(i / cols) + 1) * th;
      drawScene(camera(state.view, tw / th, parseFloat(qs.get('zoom') || '1')), cx, cy, tw, th);
    }
    return;
  }
  model.pose(state.anim, state.t); model.update(hidden);
  drawScene(camera(state.view, w / h), 0, 0, w, h);
}

let last = 0;
function tick(ts) {
  if (!last) last = ts;
  const dt = Math.min(0.1, (ts - last) / 1000); last = ts;
  if (state.playing && state.mode === 'live') {
    state.t += dt * state.speed;
    const slider = document.getElementById('t'); if (slider) slider.value = state.t;
  }
  render();
  requestAnimationFrame(tick);
}

// ------------------------------------------------------------------ UI
function ui() {
  const sel = document.getElementById('anim'), ph = document.getElementById('phase');
  const fillAnims = () => {
    sel.innerHTML = '';
    const names = Object.keys(model.anims).filter(n => !entry.animPhase || !entry.animPhase[n] || entry.animPhase[n].includes(state.phase));
    for (const n of ['', ...names]) { const o = document.createElement('option'); o.value = n; o.textContent = n || '(rest pose)'; sel.appendChild(o); }
    if (!names.includes(state.anim) && state.anim) state.anim = names[0] || '';
    sel.value = state.anim;
  };
  ph.innerHTML = '';
  for (const p of Object.keys(entry.textures)) { const o = document.createElement('option'); o.value = p; o.textContent = 'phase ' + p; ph.appendChild(o); }
  ph.value = state.phase;
  fillAnims();
  sel.onchange = () => { state.anim = sel.value; state.t = 0; };
  ph.onchange = async () => { state.phase = ph.value; setTexture(await loadImage(entry.textures[state.phase])); fillAnims(); };
  document.getElementById('view').innerHTML = Object.keys(VIEWS).map(v => `<option>${v}</option>`).join('');
  document.getElementById('view').value = state.view;
  document.getElementById('view').onchange = e => { state.view = e.target.value; state.az = state.el = null; };
  document.getElementById('play').onclick = e => { state.playing = !state.playing; e.target.textContent = state.playing ? 'pause' : 'play'; };
  document.getElementById('speed').oninput = e => state.speed = parseFloat(e.target.value);
  document.getElementById('t').oninput = e => { state.t = parseFloat(e.target.value); state.playing = false; };
  document.getElementById('info').textContent = `${model.cubeCount} cubes, atlas ${model.tw}x${model.th}`;
  document.getElementById('atlas').onclick = () => { const a = document.getElementById('atlasview'); a.style.display = a.style.display === 'block' ? 'none' : 'block'; if (a.style.display === 'block') a.src = atlasImg.src; };
  let drag = null;
  canvas.onmousedown = e => { drag = [e.clientX, e.clientY, state.az ?? VIEWS[state.view][0], state.el ?? VIEWS[state.view][1]]; };
  window.onmouseup = () => drag = null;
  window.onmousemove = e => { if (!drag) return; state.az = drag[2] + (e.clientX - drag[0]) * 0.4; state.el = Math.max(-80, Math.min(88, drag[3] + (e.clientY - drag[1]) * 0.4)); };
  canvas.onwheel = e => { e.preventDefault(); state.dist = (state.dist || entry.camDist || 7.5) * (e.deltaY > 0 ? 1.08 : 0.92); };
  if (state.mode !== 'live') document.getElementById('bar').style.display = 'none';
}

async function main() {
  setupGL();
  scenery = sceneryGeometry();
  manifest = await (await fetch('manifest.json?' + Date.now())).json();
  entry = manifest.models.find(m => m.id === (qs.get('model') || manifest.models[0].id)) || manifest.models[0];
  const [geo, anims] = await Promise.all([fetch(entry.geo + '?' + Date.now()).then(r => r.json()),
    fetch(entry.animations + '?' + Date.now()).then(r => r.json())]);
  model = new Model(geo, anims);
  if (!qs.get('phase') && entry.defaultPhase) state.phase = entry.defaultPhase;
  const names = Object.keys(model.anims);
  if (state.anim && !model.anims[state.anim]) { const hit = names.find(n => n.endsWith('.' + state.anim)); if (hit) state.anim = hit; }
  if (!state.anim && names.length) state.anim = names[0];
  setTexture(await loadImage(entry.textures[state.phase]));
  ui();
  document.title = 'ready';
  requestAnimationFrame(tick);
}
main().catch(e => { document.body.insertAdjacentHTML('beforeend', '<pre style="color:#f66">' + e.stack + '</pre>'); document.title = 'error'; });
window.PREVIEW = { state, VIEWS };

// Saves the current canvas to tools/mobforge/shots/<name>.png through serve.py.
window.PREVIEW.snapshot = function (name) {
  return new Promise(res => {
    render();
    canvas.toBlob(async b => { await fetch('/save/' + name + '.png', { method: 'POST', body: b }); res(name); }, 'image/png');
  });
};
