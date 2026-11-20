// Why the bank sat under the field (2026-11-20, the operator's 11-20 early slate): on a saved build's lock-time slate,
// the simulated field against the whole bank, the kept pool, the bank's top K by sim, tier A and the picks: mean
// projection (the build's gate), mean summed field ownership and its percentile among the field's lineups, and the
// entries-weighted sim ROI of each lineup alone in every contest the build entered (the cut study's value, one seed).
//
//   node scripts/dk_bank_gap_study.js <night.json> <build.json> [--sims 2000] [--no-sim]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const SIMS = opt("sims", 2000);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf)), gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r)), by = {};
rows.forEach(r => { by[r.id] = r; });
const own = id => N.field.own[id] || 0, pj = id => by[id] ? S.gatedProj(by[id], gate) : 0;
const seed = B.nights_seed || 1405393094;
const ctxOf = r => ({ rows, proj: x => S.gatedProj(x, gate), own: x => own(x.id), state: { lock: {}, excl: {}, cap: {}, floor: {} }, random: r });
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }));
const pool = B.pool.map(ids => ({ ids: ids.map(String) }));
function roi(P) {
  const K = P.length, v = new Float64Array(K); let w = 0, fee = 0;
  for (const c of cs) {
    for (let c0 = 0; c0 < K; c0 += 2000) {
      const part = P.slice(c0, c0 + 2000), st = S.aloneStats(S.simulate(ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0)), part, N.field.field, N.z, c, c.n, SIMS), c);
      for (let j = 0; j < part.length; j++) v[c0 + j] += c.n * (st.odd[j] + st.even[j]) / 2;
    }
    w += c.n; fee += c.n * (c.entry_fee || 0);
  }
  const fw = fee / w;
  return Array.from(v, x => (x / w - fw) / fw);
}
const sumOwn = L => L.reduce((t, id) => t + own(id), 0), sumPj = L => L.reduce((t, id) => t + pj(id), 0);
const fieldOwn = N.field.field.map(sumOwn).sort((a, b) => a - b), pct = x => 100 * fieldOwn.filter(y => y < x).length / fieldOwn.length;
const mean = a => a.reduce((t, x) => t + x, 0) / Math.max(1, a.length);
const NOSIM = process.argv.includes("--no-sim");      // projection and ownership only (every night, quickly)
const R = NOSIM ? pool.map(() => 0) : roi(pool);
const fieldR = NOSIM ? [0] : roi(N.field.field.map(ids => ({ ids: ids.map(String) })));
const order = R.map((x, i) => i).sort((a, b) => R[b] - R[a]);
const keep = B.final || [], kv = keep.map(i => R[i]), tr = S.tiers(kv, kv, kv), tierA = keep.filter((_, k) => tr.tier[k] === "A");
const picks = [...new Set(Object.values(B.portfolios || {}).flat())];
const row = (name, ix, L) => { L = L || ix.map(i => pool[i].ids); const o = mean(L.map(sumOwn));
  return { group: name, n: L.length, proj: +mean(L.map(sumPj)).toFixed(1), own: +o.toFixed(0), own_pct: +pct(o).toFixed(0), sim_roi: ix ? +(100 * mean(ix.map(i => R[i]))).toFixed(1) : null }; };
const out = { night: N.date, draft_group: N.g, games: new Set(rows.map(r => r.game)).size, contests: cs.map(c => c.name + " x" + c.n), rows: [
  Object.assign(row("field", null, N.field.field), { sim_roi: +(100 * mean(fieldR)).toFixed(1) }),
  row("whole bank", pool.map((_, i) => i)), row("kept", keep), row("bank top " + keep.length + " by sim", order.slice(0, keep.length)), row("tier A (of kept)", tierA),
  row("picks", picks), row("bank bottom half by sim", order.slice(Math.floor(pool.length / 2))) ] };
console.log(JSON.stringify(out, null, 1));
