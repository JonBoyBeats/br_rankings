// The cut by merit with a floor vs today's equal share per idea (2026-11-20, C2; a test, the operator decides): a saved
// build's whole bank cut both ways at the build's own settings (Keep, Cut % a round, nights a round) on the same nights
// (DKSim.cutPool, mode "merit": each round ranks every lineup together and keeps the best overall, each idea keeping
// its best max(5, 1% of its bank)). Each kept pool is then judged on fresh nights in every contest the build entered,
// entries-weighted: tier A (DKSim.tiers) and its ideas, the best lineup's value, the Max ROI fill's expected net (as
// Fill all contests: largest stake first, a lineup in at most 3 contests, the night cap 60%) and how many entries it
// left short; and on real points where the standings exist: random fills from each kept pool.
//
//   node scripts/dk_cut_study.js <night.json> <build.json> <standings dir> <slate csv> [--sims 2000] [--fills 200]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const SIMS = opt("sims", 2000), FILLS = opt("fills", 200), MAX = 3, NIGHT = 60;
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = (r, cap) => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: cap || {}, floor: {} }, random: r });
const bank = B.pool.map(ids => ({ ids: ids.map(String) }));
const tag = i => { const t = B.tags[i]; return Array.isArray(t) ? t[0] : t; };
const group = i => (B.groups || {})[tag(i)] || tag(i);
const supF = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json"), sup = fs.existsSync(supF) ? JSON.parse(fs.readFileSync(supF)).contests || {} : {};
Object.keys(B.portfolios || {}).forEach(id => {
  if (sup[id] && !N.slate.contests.some(c => String(c.id) === id && c.payouts)) N.slate.contests = N.slate.contests.filter(c => String(c.id) !== id).concat([sup[id]]);
});
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }))
  .sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n || (b.entry_fee || 0) - (a.entry_fee || 0));
const total = cs.reduce((a, c) => a + c.n, 0), nightLim = Math.max(1, Math.floor(NIGHT / 100 * total + 1e-9));
const pk = Object.assign({ maxExpo: 60, minUnique: 3, maxCore: 15 }, B.pick || {});
const cut = B.cut || {}, KEEP = cut.keep || 2000, PCT = (cut.pct || 10) / 100, CN = cut.nights || 2000;

function value(pool, fresh) {       // each lineup alone in every contest, entries-weighted
  const K = pool.length, v = new Float64Array(K), odd = new Float64Array(K), even = new Float64Array(K); let w = 0;
  for (const c of cs) {
    for (let c0 = 0; c0 < K; c0 += 2000) {
      const part = pool.slice(c0, c0 + 2000);
      const sim = S.simulate(ctxOf(S.seeded((((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0) + (fresh ? 99991 : 0)) >>> 0)), part, N.field.field, N.z, c, c.n, SIMS), st = S.aloneStats(sim, c);
      for (let j = 0; j < part.length; j++) { v[c0 + j] += c.n * (st.odd[j] + st.even[j]) / 2; odd[c0 + j] += c.n * st.odd[j]; even[c0 + j] += c.n * st.even[j]; }
    }
    w += c.n;
  }
  return { v: Array.from(v, x => x / w), odd: Array.from(odd, x => x / w), even: Array.from(even, x => x / w) };
}
function fill(pool) {               // Fill all contests at Max ROI
  const used = {}, out = {}, nightCount = {};
  for (const c of cs) {
    const idx = pool.map((_, i) => i).filter(i => (used[i] || 0) < MAX), P = idx.map(i => pool[i]), cap = {};
    Object.keys(nightCount).forEach(id => { const room = Math.max(0, nightLim - nightCount[id]); if (room < c.n) cap[id] = 100 * (room + 1e-6) / c.n; });
    const cx = ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0), cap);
    const sim = S.simulate(cx, P, N.field.field, N.z, c, c.n, SIMS);
    const o = { n: c.n, maxExpo: Math.max(pk.maxExpo / 100, 1 / c.n), minUnique: Math.max(1, pk.minUnique), conds: [], maxCore: pk.maxCore ? pk.maxCore / 100 : null, objective: "roi" };
    out[c.id] = S.pick(cx, o, P, sim, c, c.n).chosen.map(k => idx[k]);
    out[c.id].forEach(i => { used[i] = (used[i] || 0) + 1; pool[i].ids.forEach(id => { nightCount[id] = (nightCount[id] || 0) + 1; }); });
  }
  return out;
}
function fillNet(pool, F) {         // the fill's expected net on fresh nights (the builder's places)
  const tot = new Float64Array(SIMS); let fees = 0, n = 0;
  for (const c of cs) {
    const L = F[c.id].map(i => pool[i]); n += L.length; fees += (c.entry_fee || 0) * L.length;
    if (!L.length) continue;
    const sim = S.simulate(ctxOf(S.seeded(seed + 7777)), L, N.field.field, N.z, c, L.length, SIMS), pay = S.payTable(c), paid = pay.length - 1;
    for (let s = 0; s < SIMS; s++) for (let i = 0; i < L.length; i++) {
      let mine = 0; for (let j = 0; j < L.length; j++) if (sim.cs[j * SIMS + s] > sim.cs[i * SIMS + s]) mine++;
      const q = Math.round(1 + sim.fa[i * SIMS + s] + mine); tot[s] += q >= 1 && q <= paid ? pay[q] : 0;
    }
  }
  return { net: tot.reduce((a, b) => a + b, 0) / SIMS - fees, filled: n };
}
const act = {}, graded = actf && fs.existsSync(actf);
if (graded) {
  const head = fs.readFileSync(actf, "utf8").split("\n")[0].split(","), iId = head.indexOf("dk_id"), iAct = head.indexOf("actual_dk");
  fs.readFileSync(actf, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iAct] || 0; });
}
const fields = {};
cs.forEach(c => { const f = path.join(sdir, `contest-standings-${c.id}.csv`); if (graded && fs.existsSync(f)) {
  fields[c.id] = fs.readFileSync(f, "utf8").split("\n").slice(1).map(l => l.split(",")).filter(v => v[1] && v[4] !== undefined && v[4] !== "" && !/^jonboyjackson/i.test(v[2] || "")).map(v => +v[4]); } });
function realNet(sets, c) {         // a contest's set placed among its real entries, ties split
  const pts = fields[c.id], pay = S.payTable(c), ours = sets.map(L => L.ids.reduce((t, id) => t + (act[id] || 0), 0)); let tot = 0;
  ours.forEach(x => { const above = pts.filter(p => p > x).length + ours.filter(y => y > x).length, tied = pts.filter(p => p === x).length + ours.filter(y => y === x).length - 1;
    let w = 0; for (let k = above + 1; k <= above + 1 + tied; k++) w += pay[k] || 0; tot += w / (tied + 1); });
  return tot - (c.entry_fee || 0) * sets.length;
}
function randomFills(pool) {        // real net of random fills from the kept pool (distinct within a contest)
  if (!cs.every(c => fields[c.id])) return null;
  const r = S.seeded(424242), nets = [];
  for (let f = 0; f < FILLS; f++) {
    let net = 0;
    for (const c of cs) { const pick = new Set(); while (pick.size < Math.min(c.n, pool.length)) pick.add((r() * pool.length) | 0); net += realNet([...pick].map(i => pool[i]), c); }
    nets.push(net);
  }
  return { mean: +(nets.reduce((a, b) => a + b, 0) / FILLS).toFixed(2), positive: +(100 * nets.filter(x => x > 0).length / FILLS).toFixed(1) };
}

(async () => {
  const out = { night: N.date, draft_group: N.g, bank: bank.length, keep: KEEP, pct: PCT, nights: CN, contests: cs.map(c => c.name + " x" + c.n), runs: {} };
  for (const mode of ["equal", "merit"]) {
    const t0 = Date.now();
    const res = await S.cutPool(ctxOf(S.seeded(seed + 1)), bank, cs.map(c => ({ contest: c, n: c.n })), N.field.field, N.z, KEEP, PCT, CN, null, bank.map((_, i) => group(i)), { mode });
    const pool = res.keep.map(i => bank[i]), val = value(pool, true), tr = S.tiers(val.v, val.odd, val.even);
    const aIx = tr.tier.map((t, k) => t === "A" ? k : -1).filter(k => k >= 0), ideas = {};
    aIx.forEach(k => { const g = group(res.keep[k]); ideas[g] = (ideas[g] || 0) + 1; });
    const kept = {}; res.keep.forEach(i => { const g = group(i); kept[g] = (kept[g] || 0) + 1; });
    const F = fill(pool), fn = fillNet(pool, F);
    out.runs[mode] = { kept: pool.length, rounds: res.rounds.length, ideas_kept: Object.keys(kept).length, tierA: aIx.length, tierA_ideas: Object.keys(ideas).length,
                       tierA_by: ideas, best_value: +Math.max(...val.v).toFixed(3), fill_net: +fn.net.toFixed(2), fill_short: total - fn.filled, real_random_fills: randomFills(pool),
                       seconds: Math.round((Date.now() - t0) / 1000) };
  }
  console.log(JSON.stringify(out, null, 1));
})();
