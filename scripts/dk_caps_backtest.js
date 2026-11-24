// Caps backtest (2026-11-24, the operator via the coordinator; analysis only, nothing adopted): the fill already scores
// each lineup by its added value to the set, so do the caps help or just cost money? Each graded night's saved build's
// final pool is refilled into that night's real contests (as the DK page's Fill all contests: the largest stake first,
// DKSim.pick on each contest's seeded nights, the night cap as each player's Max% from what earlier contests used, a
// lineup in at most MAX contests) under five settings, and each set is scored on real points against the contest's real
// entries (the owner's own left out, ties split):
//   a  current: contest exposure 60%, night 60%, min unique 3, max core 15%
//   b  contest and night at 80%, the rest as a
//   c  no exposure caps (contest, night, core off), min unique 3 kept
//   d  no caps at all (min unique 1, a lineup in any number of contests)
//   e  a, then each contest's stranded seats topped up by added value with the caps off (as "Add best" does, one at a
//      time from the lineups breaking the caps)
// Out: one JSON line per night (each setting's fees, real dollars, ROI, entries at the real top 1% / top 10% lines, the
// largest single-player share of the night's entries, stranded seats) and, for the concentration question, each
// player's share of setting d's entries (the model left alone) beside his real DK points less his projection.
//
//   node scripts/dk_caps_backtest.js <night.json> <build.json> <standings dir> <graded slate csv> [--sims 1000]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const SIMS = opt("sims", 1000), MAX = 3;
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = (r, cap) => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: cap || {}, floor: {} }, random: r });
const pool = (B.final || B.pool.map((_, i) => i)).map(i => ({ ids: B.pool[i].map(String) }));
const supF = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json");
const sup = fs.existsSync(supF) ? JSON.parse(fs.readFileSync(supF)).contests || {} : {};
Object.keys(B.portfolios || {}).forEach(id => {
  if (sup[id] && !N.slate.contests.some(c => String(c.id) === id && c.payouts)) N.slate.contests = N.slate.contests.filter(c => String(c.id) !== id).concat([sup[id]]);
});
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }))
  .sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n || (b.entry_fee || 0) - (a.entry_fee || 0));
const total = cs.reduce((a, c) => a + c.n, 0);
const SET = {
  a: { expo: 60, night: 60, unique: 3, core: 15, max: MAX },
  b: { expo: 80, night: 80, unique: 3, core: 15, max: MAX },
  c: { expo: 100, night: 100, unique: 3, core: null, max: MAX },
  d: { expo: 100, night: 100, unique: 1, core: null, max: 1e9 },
  e: { expo: 60, night: 60, unique: 3, core: 15, max: MAX, topup: true }
};
const sims = {};
function simOf(c, idx) {      // each contest's seeded nights for the whole pool, once (the candidates are always a subset)
  if (!sims[c.id]) sims[c.id] = S.simulate(ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0)), pool, N.field.field, N.z, c, c.n, SIMS);
  return sims[c.id];
}
function sub(sim, idx) {      // the pool sim restricted to candidates idx: per-lineup arrays (length K) and per-lineup-night blocks (K x S)
  const o = Object.assign({}, sim), K = sim.K, Sn = sim.S;
  Object.keys(sim).forEach(k => {
    const v = sim[k]; if (!v || typeof v.length !== "number" || typeof v === "string") return;
    if (v.length === K * Sn && K * Sn !== K) { const a = new v.constructor(idx.length * Sn); idx.forEach((i, j) => a.set(v.subarray ? v.subarray(i * Sn, (i + 1) * Sn) : v.slice(i * Sn, (i + 1) * Sn), j * Sn)); o[k] = a; }
    else if (v.length === K) o[k] = Array.isArray(v) ? idx.map(i => v[i]) : v.constructor.from(idx, i => v[i]);
  });
  o.K = idx.length;
  return o;
}
function fill(st) {
  const used = {}, out = {}, nightCount = {}, nightLim = Math.max(1, Math.floor(st.night / 100 * total + 1e-9));
  let stranded = 0;
  for (const c of cs) {
    const idx = pool.map((_, i) => i).filter(i => (used[i] || 0) < st.max), P = idx.map(i => pool[i]);
    const cap = {};
    if (st.night < 100) Object.keys(nightCount).forEach(id => { const room = Math.max(0, nightLim - nightCount[id]); if (room < c.n) cap[id] = 100 * (room + 1e-6) / c.n; });
    const cx = ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0), cap), sim = sub(simOf(c), idx);
    const o = { n: c.n, maxExpo: Math.max(st.expo / 100, 1 / c.n), minUnique: Math.max(1, st.unique), conds: [], maxCore: st.core ? st.core / 100 : null, objective: "roi" };
    let ch = S.pick(cx, o, P, sim, c, c.n).chosen.slice();
    if (ch.length < c.n && st.topup) {      // the stranded seats: the caps off, the set so far kept, the next best by added value
      const cx2 = ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0), {});
      ch = S.pick(cx2, { n: c.n, maxExpo: 1, minUnique: 1, conds: [], maxCore: null, objective: "roi", preset: ch }, P, sim, c, c.n).chosen.slice();
    }
    stranded += c.n - ch.length;
    out[c.id] = ch.map(k => idx[k]);
    out[c.id].forEach(i => { used[i] = (used[i] || 0) + 1; pool[i].ids.forEach(id => { nightCount[id] = (nightCount[id] || 0) + 1; }); });
  }
  return { out, stranded };
}
const act = {}, prj = {};
{ const L = fs.readFileSync(actf, "utf8").split("\n"), h = L[0].split(","), iId = h.indexOf("dk_id"), iA = h.indexOf("actual_dk");
  L.slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iA] || 0; }); }
rows.forEach(r => { prj[r.id] = S.gatedProj(r, gate); });
const stand = {};
function standOf(c) {            // the contest's real points (the owner's own entries left out), best first
  if (c.id in stand) return stand[c.id];
  const f = path.join(sdir, `contest-standings-${c.id}.csv`);
  if (!fs.existsSync(f)) return (stand[c.id] = null);
  const pts = [];
  fs.readFileSync(f, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[1] && /^\d+$/.test(v[1]) && v[4] !== undefined && v[4] !== "" && !/^jonboyjackson/i.test(v[2] || "")) pts.push(+v[4]); });
  return (stand[c.id] = pts.sort((a, b) => b - a));
}
function real(c, sets) {
  const pts = standOf(c); if (!pts || !pts.length) return null;
  const pay = S.payTable(c), ours = sets.map(L => L.reduce((t, id) => t + (act[id] || 0), 0));
  const N1 = pts.length + ours.length, l1 = pts[Math.max(0, Math.ceil(0.01 * N1) - 1)], l10 = pts[Math.max(0, Math.ceil(0.10 * N1) - 1)];
  let tot = 0, t1 = 0, t10 = 0;
  ours.forEach(x => {
    const above = pts.filter(p => p > x).length + ours.filter(y => y > x).length, tied = pts.filter(p => p === x).length + ours.filter(y => y === x).length - 1;
    let w = 0; for (let k = above + 1; k <= above + 1 + tied; k++) w += pay[k] || 0;
    tot += w / (tied + 1); if (x >= l1) t1++; if (x >= l10) t10++;
  });
  return { d: tot, t1, t10 };
}
const res = {}, expoD = {};
for (const k of Object.keys(SET)) {
  const F = fill(SET[k]); let fees = 0, dol = 0, t1 = 0, t10 = 0, n = 0, cov = 0;
  const cnt = {};
  for (const c of cs) {
    const L = F.out[c.id].map(i => pool[i].ids); n += L.length;
    L.forEach(ids => ids.forEach(id => { cnt[id] = (cnt[id] || 0) + 1; }));
    const r = real(c, L); if (!r) continue;
    cov += L.length; fees += (c.entry_fee || 0) * L.length; dol += r.d; t1 += r.t1; t10 += r.t10;
  }
  const top = Object.keys(cnt).sort((x, y) => cnt[y] - cnt[x])[0];
  res[k] = { entries: n, graded: cov, fees: +fees.toFixed(2), real: +dol.toFixed(2), net: +(dol - fees).toFixed(2), roi: fees ? +(100 * (dol - fees) / fees).toFixed(1) : null,
             top1: t1, top10: t10, max_player: top ? +(100 * cnt[top] / n).toFixed(1) : 0, max_name: top ? N.slate.players[top].name : "", stranded: F.stranded };
  if (k === "d") Object.keys(cnt).forEach(id => { expoD[id] = cnt[id] / n; });
}
// the concentration question: setting d's player shares (the model left alone) against each player's real points less
// his projection (did the players it leaned on beat what we projected?)
const conc = Object.keys(expoD).map(id => ({ id, name: N.slate.players[id].name, share: expoD[id], beat: (act[id] || 0) - (prj[id] || 0), act: act[id] || 0, proj: prj[id] || 0,
  own: N.field.own[id] || 0, salary: N.slate.players[id].salary }));
console.log(JSON.stringify({ night: N.date, g: N.g, contests: cs.length, entries: total, res, conc }));
