// The player scan redesign, backtested against today's (2026-11-20, C7; a test, the operator decides). On a saved night:
//  - today's scan: a forced batch per player projected 15+ minutes (at least 1 of him, PERP lineups), each lineup alone
//    in every contest the build entered, entries-weighted, on the slate's nights; his top-1% gain over a plain batch and
//    the Read by the noise bar (core / leverage strong; fade / skip weak; even);
//  - the redesign: ONE neutral batch (NEUTRAL lineups at the bank's settings, no rules), each lineup's sim ROI and top-1%
//    rate on the same nights, and a ridge regression of them on player indicators (lambda LAMBDA), a bootstrap band per
//    player (BOOT resamples); players ranked by their ROI coefficient (top-1% breaking ties); the top FOCUS as the focus
//    list, core where field ownership is at or above the slate's median, leverage below.
// Judged on real results in the night's main contest: for each list's players, the share of real entries holding him
// that reached the real top 10% / top 1%, and his real points less his projection; beside every player's average.
//
//   node scripts/dk_scan_study.js <night.json> <build.json> <standings dir> <slate csv> [--perp 40] [--neutral 3000] [--focus 12]
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const PERP = opt("perp", 40), NEUTRAL = opt("neutral", 3000), FOCUS = opt("focus", 12), SIMS = opt("sims", 2000), LAMBDA = opt("lambda", 20), BOOT = opt("boot", 40);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const gpMax = {}, outTeam = {};
rows.forEach(r => { gpMax[r.team] = Math.max(gpMax[r.team] || 0, r.gp || 0); if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => {
  const deep = (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < gpMax[r.team] / 2);
  const punt = (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg);
  r.deepOut = r.status !== "Out" && (deep || punt);
});
const byId = {}; rows.forEach(r => { byId[r.id] = r; });
const seed = B.nights_seed || 1405393094;
const ctxOf = rand => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, solver: sb.self.solver, random: rand, state: { lock: {}, excl: {}, cap: {}, floor: {} } });
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }));
const baseO = { n: 1, maxExpo: 1, minUnique: 1, z: N.z, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [], nightS: 0.35 };

function value(pool) {             // per lineup: entries-weighted ROI, top-1% rate, and the top-1% rate on odd / even nights
  const K = pool.length, v = new Float64Array(K), t1 = new Float64Array(K), o1 = new Float64Array(K), e1 = new Float64Array(K); let w = 0, fee = 0;
  for (const c of cs) {
    const T1 = Math.max(1, Math.ceil(0.01 * (c.size || 0)));
    for (let c0 = 0; c0 < K; c0 += 2000) {
      const part = pool.slice(c0, c0 + 2000), sim = S.simulate(ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0)), part, N.field.field, N.z, c, c.n, SIMS), st = S.aloneStats(sim, c);
      for (let j = 0; j < part.length; j++) {
        v[c0 + j] += c.n * (st.odd[j] + st.even[j]) / 2; t1[c0 + j] += c.n * st.top1[j];
        let ho = 0, he = 0; for (let s = 0; s < SIMS; s++) if (Math.round(1 + sim.fa[j * SIMS + s]) <= T1) { if (s % 2) ho++; else he++; }
        o1[c0 + j] += c.n * ho / Math.floor(SIMS / 2); e1[c0 + j] += c.n * he / Math.ceil(SIMS / 2);
      }
    }
    w += c.n; fee += c.n * (c.entry_fee || 0);
  }
  const fw = fee / w;
  return { roi: Array.from(v, x => (x / w - fw) / fw), t1: Array.from(t1, x => x / w), o1: Array.from(o1, x => x / w), e1: Array.from(e1, x => x / w) };
}
function ridge(pool, y, players, idx) {      // coefficients on player indicators, centred, lambda LAMBDA (Gauss-Jordan on P x P)
  const P = players.length, col = {}; players.forEach((id, j) => { col[id] = j; });
  const A = Array.from({ length: P }, () => new Float64Array(P)), b = new Float64Array(P), ix = idx || pool.map((_, i) => i);
  const my = ix.reduce((t, i) => t + y[i], 0) / ix.length, mx = new Float64Array(P);
  ix.forEach(i => pool[i].ids.forEach(id => { if (col[id] != null) mx[col[id]] += 1 / ix.length; }));
  ix.forEach(i => {
    const js = pool[i].ids.map(id => col[id]).filter(j => j != null);
    js.forEach(a => { b[a] += y[i] - my; js.forEach(c => { A[a][c] += 1; }); });
  });
  for (let a = 0; a < P; a++) { for (let c = 0; c < P; c++) A[a][c] -= ix.length * mx[a] * mx[c]; A[a][a] += LAMBDA; }
  const M = A.map((r, i) => Array.from(r).concat([b[i]]));
  for (let i = 0; i < P; i++) {
    let p = i; for (let r = i + 1; r < P; r++) if (Math.abs(M[r][i]) > Math.abs(M[p][i])) p = r;
    [M[i], M[p]] = [M[p], M[i]]; const d = M[i][i] || 1e-12;
    for (let c = i; c <= P; c++) M[i][c] /= d;
    for (let r = 0; r < P; r++) if (r !== i && M[r][i]) { const f = M[r][i]; for (let c = i; c <= P; c++) M[r][c] -= f * M[i][c]; }
  }
  return M.map(r => r[P]);
}
// real results: the night's main contest's entries, each lineup's names to DK ids
function lineupNames(s) { const parts = (" " + s.trim()).split(/(?:^|\s)(G|F|UTIL)\s/); const out = []; for (let i = 2; i < parts.length; i += 2) if (parts[i] && parts[i].trim()) out.push(parts[i].trim()); return out; }
function realRates() {
  const f = path.join(sdir, `contest-standings-${N.cid}.csv`);
  if (!fs.existsSync(f)) return null;
  const nameId = {}; rows.forEach(r => { nameId[r.name] = nameId[r.name] ? "dup" : r.id; });
  const lines = fs.readFileSync(f, "utf8").split("\n").slice(1).map(l => { const m = l.match(/^(\d+),[^,]*,[^,]*,[^,]*,([\d.]+),([^,]*)/); return m ? { rank: +m[1], ids: lineupNames(m[3]).map(n => nameId[n]).filter(x => x && x !== "dup") } : null; }).filter(x => x && x.ids.length === 8);
  const n = lines.length, t10 = Math.ceil(0.1 * n), t1 = Math.max(1, Math.ceil(0.01 * n)), by = {};
  lines.forEach(L => L.ids.forEach(id => { const b = by[id] = by[id] || [0, 0, 0]; b[0]++; if (L.rank <= t10) b[1]++; if (L.rank <= t1) b[2]++; }));
  return { by, n, all10: lines.filter(L => L.rank <= t10).length / n, all1: lines.filter(L => L.rank <= t1).length / n };
}
const act = {};
if (fs.existsSync(actf)) { const h = fs.readFileSync(actf, "utf8").split("\n")[0].split(","), iId = h.indexOf("dk_id"), iA = h.indexOf("actual_dk");
  fs.readFileSync(actf, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iA] || 0; }); }
function judge(list, R) {          // a list's players: real top-10% / top-1% rate of entries holding them, real less projected points
  if (!R || !list.length) return null;
  let e = 0, a = 0, b = 0, d = 0;
  list.forEach(id => { const x = R.by[id] || [0, 0, 0]; e += x[0]; a += x[1]; b += x[2]; d += (act[id] || 0) - S.gatedProj(byId[id], gate); });
  return { players: list.length, entries: e, top10: e ? +(100 * a / e).toFixed(1) : null, top1: e ? +(100 * b / e).toFixed(2) : null, pts_vs_proj: +(d / list.length).toFixed(1) };
}

(async () => {
  const t0 = Date.now(), live = rows.filter(r => r.status !== "Out" && !r.deepOut), scanP = live.filter(r => (r.min || 0) >= 15);
  const own = id => N.field.own[id] || 0, medOwn = scanP.map(r => own(r.id)).sort((a, b) => a - b)[Math.floor(scanP.length / 2)];
  // today's scan
  const pool = [], at = {}, add = (L) => { const k = L.ids.slice().sort().join(","); if (at[k] == null) { at[k] = pool.length; pool.push({ ids: L.ids.map(String) }); } return at[k]; };
  const plain = (await S.pool(ctxOf(S.seeded(7919 + (+N.g || 0))), baseO, 5 * PERP)).lineups.map(add), batches = [];
  for (let i = 0; i < scanP.length; i++) batches.push({ id: scanP[i].id, idx: (await S.pool(ctxOf(S.seeded(7919 * (i + 2) + (+N.g || 0))), Object.assign({}, baseO, { conds: [{ type: "min", ids: [scanP[i].id], n: 1 }] }), PERP)).lineups.map(add) });
  const neutral = (await S.pool(ctxOf(S.seeded(31337 + (+N.g || 0))), baseO, NEUTRAL)).lineups.map(add);
  const val = value(pool), mean = (a, ix) => ix.reduce((t, k) => t + a[k], 0) / Math.max(1, ix.length);
  const gains = batches.map(b => ({ id: b.id, g: mean(val.t1, b.idx) - mean(val.t1, plain), d: (mean(val.o1, b.idx) - mean(val.o1, plain)) - (mean(val.e1, b.idx) - mean(val.e1, plain)) }));
  const dm = gains.reduce((t, x) => t + x.d, 0) / gains.length, bar = 2 * Math.SQRT2 * Math.sqrt(gains.reduce((t, x) => t + (x.d - dm) ** 2, 0) / Math.max(1, gains.length - 1)) / 2;
  const read = x => x.g > bar ? (own(x.id) >= medOwn ? "core" : "leverage") : x.g < -bar ? (own(x.id) >= medOwn ? "fade" : "skip") : "even";
  gains.forEach(x => { x.read = read(x); });
  // the redesign: ridge on the neutral batch
  const nPool = neutral.map(i => pool[i]), players = [...new Set(nPool.flatMap(L => L.ids))].filter(id => byId[id]);
  const yR = neutral.map(i => val.roi[i]), yT = neutral.map(i => val.t1[i]);
  const bR = ridge(nPool, yR, players), bT = ridge(nPool, yT, players);
  const rnd = S.seeded(99), boots = players.map(() => []);
  for (let k = 0; k < BOOT; k++) { const ix = nPool.map(() => (rnd() * nPool.length) | 0), bb = ridge(nPool, yR, players, ix); bb.forEach((x, j) => boots[j].push(x)); }
  const band = boots.map(a => { const m = a.reduce((t, x) => t + x, 0) / a.length; return Math.sqrt(a.reduce((t, x) => t + (x - m) ** 2, 0) / Math.max(1, a.length - 1)); });
  const ranked = players.map((id, j) => ({ id, name: byId[id].name, roi: bR[j], top1: bT[j], band: band[j], own: own(id), held: nPool.filter(L => L.ids.includes(id)).length }))
    .filter(x => (byId[x.id].min || 0) >= 15).sort((a, b) => b.roi - a.roi || b.top1 - a.top1);
  const focus = ranked.slice(0, FOCUS).map(x => Object.assign(x, { read: x.own >= medOwn ? "core" : "leverage" }));
  const R = realRates();
  const all = judge(scanP.map(r => r.id), R);
  const out = { night: N.date, draft_group: N.g, players_scanned: scanP.length, neutral: nPool.length, own_median: +medOwn.toFixed(1), noise_bar: +(100 * bar).toFixed(3),
    current: { core: gains.filter(x => x.read === "core").length, leverage: gains.filter(x => x.read === "leverage").length, even: gains.filter(x => x.read === "even").length,
               fade: gains.filter(x => x.read === "fade").length, skip: gains.filter(x => x.read === "skip").length,
               core_leverage_real: judge(gains.filter(x => /core|leverage/.test(x.read)).map(x => x.id), R), fade_skip_real: judge(gains.filter(x => /fade|skip/.test(x.read)).map(x => x.id), R) },
    ridge: { focus: focus.map(x => ({ name: x.name, read: x.read, roi: +(100 * x.roi).toFixed(1), band: +(100 * x.band).toFixed(1), top1: +(100 * x.top1).toFixed(2), own: +x.own.toFixed(1), held: x.held })),
             focus_real: judge(focus.map(x => x.id), R), bottom_real: judge(ranked.slice(-FOCUS).map(x => x.id), R),
             chalk_held: ranked.filter(x => x.own >= 25).length, chalk_in_focus: focus.filter(x => x.own >= 25).length },
    all_real: all, field_rates: R ? { top10: +(100 * R.all10).toFixed(1), top1: +(100 * R.all1).toFixed(2) } : null, seconds: Math.round((Date.now() - t0) / 1000) };
  console.log(JSON.stringify(out, null, 1));
})();
