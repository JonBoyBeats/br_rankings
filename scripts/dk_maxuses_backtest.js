// Max-contests-per-lineup backtest (2026-11-24, the operator via the coordinator; analysis only, nothing adopted): with
// the current settings (contest exposure 60%, night cap 60%, min unique 3, max core 15%, auto top-up on), does letting a
// lineup sit in more contests earn more, and at what swing? Each graded night's saved build's final pool is refilled into
// that night's real contests as the DK page does it on main:
//   1. Fill all contests: the largest stake first; DKSim.pick on each contest's seeded nights from the lineups not yet in
//      MAX contests, the night cap as each player's Max% from what earlier contests used; a short set relaxes one cap a
//      step (max core 20%, 25%, then max exposure 70%; objective cover, what it picked kept), as pickPortfolios does;
//   2. stranded seats counted here (before the top-up);
//   3. Auto top-up: in slate order, each open seat takes the final-pool lineup not in that contest and under MAX uses
//      that breaks the caps least (fewest caps broken, then the fewest entries over, then the best value), one seat at a
//      time, as strandFor / autoTopUp do. Value: the page uses the cut board's value, which builds don't save; here it is
//      the lineup's expected payout alone in that contest on the same sim nights (DKSim builder.alone).
// Only MAX varies: 3 (now), 5, unlimited. Each set is scored on real points against the contest's real entries (the
// owner's own left out, ties split), with the top 1% / top 10% lines.
//
//   node scripts/dk_maxuses_backtest.js <night.json> <build.json> <standings dir> <graded slate csv> [--sims 1000]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const SIMS = opt("sims", 1000), EXPO = 0.6, NIGHT = 0.6, UNIQUE = 3, CORE = 0.15;
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = (r, cap) => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: cap || {}, floor: {} }, random: r });
const rng = c => S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0);
const pool = (B.final || B.pool.map((_, i) => i)).map(i => ({ ids: B.pool[i].map(String) }));
const supF = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json");
const sup = fs.existsSync(supF) ? JSON.parse(fs.readFileSync(supF)).contests || {} : {};
Object.keys(B.portfolios || {}).forEach(id => {
  if (sup[id] && !N.slate.contests.some(c => String(c.id) === id && c.payouts)) N.slate.contests = N.slate.contests.filter(c => String(c.id) !== id).concat([sup[id]]);
});
// slate order (nbContests, the top-up's order); the fill's order is the largest stake first
const slateCs = N.slate.contests.filter(c => c.payouts && B.portfolios && B.portfolios[String(c.id)])
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }));
const cs = slateCs.slice().sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n || (b.entry_fee || 0) - (a.entry_fee || 0));
const total = cs.reduce((a, c) => a + c.n, 0), nightLim = Math.max(1, Math.floor(NIGHT * total + 1e-9));
const sims = {}, alone = {};
function simOf(c) {           // each contest's seeded nights for the whole pool, once (the candidates are always a subset)
  if (!sims[c.id]) {
    sims[c.id] = S.simulate(ctxOf(rng(c)), pool, N.field.field, N.z, c, c.n, SIMS);
    const b = S.builder(sims[c.id], c); alone[c.id] = pool.map((_, k) => b.alone(k));
  }
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
function fill(MAX) {
  const used = {}, out = {}, nightCount = {}, relaxed = [];
  let stranded = 0;
  for (const c of cs) {
    const idx = pool.map((_, i) => i).filter(i => (used[i] || 0) < MAX), P = idx.map(i => pool[i]);
    const cap = {};
    Object.keys(nightCount).forEach(id => { const room = Math.max(0, nightLim - nightCount[id]); if (room < c.n) cap[id] = 100 * (room + 1e-6) / c.n; });
    const cx = ctxOf(rng(c), cap), sim = sub(simOf(c), idx);
    const po = { n: c.n, maxExpo: Math.max(EXPO, 1 / c.n), minUnique: UNIQUE, conds: [], maxCore: CORE, objective: "roi" };
    let r = S.pick(cx, po, P, sim, c, c.n);
    if (r.chosen.length < c.n) {     // C4: relax one cap a step, what it picked kept, the rest by coverage
      const steps = [];
      if (po.maxCore < 0.2) steps.push(["core20", { maxCore: 0.2 }]);
      if (po.maxCore < 0.25) steps.push(["core25", { maxCore: 0.25 }]);
      if (po.maxExpo < 0.7) steps.push(["expo70", { maxCore: Math.max(po.maxCore, 0.25), maxExpo: 0.7 }]);
      for (let si = 0; si < steps.length && r.chosen.length < c.n; si++) {
        const had = r.chosen.length, r2 = S.pick(cx, Object.assign({}, po, steps[si][1], { objective: "cover", preset: r.chosen }), P, sim, c, c.n);
        if (r2.chosen.length > had) { r = r2; relaxed.push(c.id + ":" + steps[si][0] + "+" + (r2.chosen.length - had)); }
      }
    }
    stranded += c.n - r.chosen.length;
    out[c.id] = r.chosen.map(k => idx[k]);
    out[c.id].forEach(i => { used[i] = (used[i] || 0) + 1; pool[i].ids.forEach(id => { nightCount[id] = (nightCount[id] || 0) + 1; }); });
  }
  // Auto top-up (strandFor's Add best, one seat at a time, slate order)
  let topped = 0, broke = 0;
  for (const c of slateCs) {
    while (out[c.id].length < c.n) {
      const have = out[c.id], cnt = {}, lim = S.expoLimit(EXPO, c.n);
      have.forEach(i => pool[i].ids.forEach(id => { cnt[id] = (cnt[id] || 0) + 1; }));
      let best = null;
      pool.forEach((L, i) => {
        if (have.indexOf(i) >= 0 || (used[i] || 0) >= MAX) return;
        let over = 0, ex = 0;
        L.ids.forEach(id => {
          if ((nightCount[id] || 0) + 1 > nightLim) { over++; ex += (nightCount[id] || 0) + 1 - nightLim; }
          if ((cnt[id] || 0) + 1 > lim) { over++; ex += (cnt[id] || 0) + 1 - lim; }
        });
        const close = have.filter(j => pool[j].ids.filter(id => L.ids.indexOf(id) >= 0).length > 8 - UNIQUE).length;
        if (close) { over++; ex += close; }
        const k = [over, ex, -alone[c.id][i]];
        if (!best || k[0] < best.k[0] || (k[0] === best.k[0] && (k[1] < best.k[1] || (k[1] === best.k[1] && k[2] < best.k[2])))) best = { i, k };
      });
      if (!best) break;
      have.push(best.i); topped++; if (best.k[0]) broke++;
      used[best.i] = (used[best.i] || 0) + 1; pool[best.i].ids.forEach(id => { nightCount[id] = (nightCount[id] || 0) + 1; });
    }
  }
  return { out, stranded, topped, broke, relaxed, used };
}
const act = {};
{ const L = fs.readFileSync(actf, "utf8").split("\n"), h = L[0].split(","), iId = h.indexOf("dk_id"), iA = h.indexOf("actual_dk");
  L.slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iA] || 0; }); }
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
const res = {};
for (const [k, MAX] of [["m3", 3], ["m5", 5], ["unl", 1e9]]) {
  const F = fill(MAX); let fees = 0, dol = 0, t1 = 0, t10 = 0, n = 0, cov = 0;
  for (const c of cs) {
    const L = F.out[c.id].map(i => pool[i].ids); n += L.length;
    const r = real(c, L); if (!r) continue;
    cov += L.length; fees += (c.entry_fee || 0) * L.length; dol += r.d; t1 += r.t1; t10 += r.t10;
  }
  const u = Object.values(F.used).filter(x => x > 0);
  res[k] = { entries: n, graded: cov, fees: +fees.toFixed(2), real: +dol.toFixed(2), net: +(dol - fees).toFixed(2), roi: fees ? +(100 * (dol - fees) / fees).toFixed(1) : null,
             top1: t1, top10: t10, distinct: u.length, in3: u.filter(x => x >= 3).length, in4: u.filter(x => x >= 4).length, seats4: u.filter(x => x >= 4).reduce((a, x) => a + x, 0), most: Math.max(0, ...u),
             stranded: F.stranded, topped: F.topped, topped_breaking: F.broke, relaxed: F.relaxed };
}
console.log(JSON.stringify({ night: N.date, g: N.g, contests: cs.length, entries: total, pool: pool.length, res }));
