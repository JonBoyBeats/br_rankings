// Middle band and tighter cores (2026-11-28, analysis only; HELD). For one saved build, on the slate and the simulated
// field as they stood at lock (the page's fixed field, the same player draws as ous.js variant A), the page's pick
// (DKSim.pick: Max ROI for mains and qualifiers, Max coverage for flagships, each contest on its own, the build's caps)
// fills every contest the build entered from each candidate subset python hands it:
//   variants: [{name, set: [kept-pool positions], maxCore: % or null (the build's)}]
// Output (stdout, JSON): per contest, per variant, the chosen lineups (player ids).
//   node mb.js <night.json> <build.json> <params.json>
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..", "..", "..", ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, pf] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf)), PR = JSON.parse(fs.readFileSync(pf));
const SIMS = PR.sims || 500;
const gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = rnd => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, random: rnd });
const sup = (() => { const f = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json"); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f)).contests || {} : {}; })();
const flagship = c => /pull up jumper/i.test(c.name || "") || (!/dime time|and-one|quarter jukebox|qualifier|satellite/i.test(c.name || "") && (c.size || 0) >= 100 && (c.size || 0) < 800);
const contests = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(x => String(x.id) === id && x.payouts) || sup[id])
  .filter(c => c && c.payouts).map(c => Object.assign({}, c, { n: B.portfolios[String(c.id)].length })).filter(c => c.n > 0);
const kept = (B.final && B.final.length ? B.final : B.pool.map((_, i) => i));
const cand = kept.map(i => ({ ids: B.pool[i].map(String) })), K = cand.length;
const ix = {}, mean = [], err = [];
rows.forEach(r => { ix[r.id] = mean.length; const m = r.status === "Out" ? 0 : S.gatedProj(r, gate); mean.push(m); err.push(r.miss_dk || 0.35 * m); });
const idx = id => { if (ix[id] == null) { ix[id] = mean.length; mean.push(0); err.push(0); } return ix[id]; };
const candIx = cand.map(L => L.ids.map(idx));
const field = N.field.field, F = field.length, fieldIx = field.map(L => L.map(idx)), P = mean.length, z = N.z;
function simA(contest) {         // ous.js simPair, the fixed field only (same seeds, so the same draws as its variant A)
  const size = contest.size || 0, n = contest.n, wEach = Math.max(0, size - n);
  const rnd = S.seeded((seed ^ Math.imul(+contest.id || 0, 2654435761)) >>> 0);
  const cs = new Float32Array(K * SIMS), fa = new Float32Array(K * SIMS), pts = new Float32Array(P), fsc = new Float64Array(F);
  for (let s = 0; s < SIMS; s++) {
    for (let p = 0; p < P; p++) pts[p] = Math.max(0, mean[p] + z[(rnd() * z.length) | 0] * err[p]);
    for (let f = 0; f < F; f++) { let t = 0; const L = fieldIx[f]; for (let j = 0; j < 8; j++) t += pts[L[j]]; fsc[f] = t; }
    const sorted = Float64Array.from(fsc).sort();
    for (let k = 0; k < K; k++) {
      let t2 = 0; const L2 = candIx[k]; for (let j = 0; j < 8; j++) t2 += pts[L2[j]];
      let lo = 0, hi = F; const t2e = t2 + 1e-6;
      while (lo < hi) { const mid = (lo + hi) >> 1; if (sorted[mid] <= t2e) lo = mid + 1; else hi = mid; }
      cs[k * SIMS + s] = t2; fa[k * SIMS + s] = (F - lo) * wEach / F;
    }
  }
  return { cs, fa, K, S: SIMS, cut: { win: 0, top10: 0, cash: 0 }, quality: new Float32Array(K), core: new Float32Array(K), rate: 0,
           dup: new Float32Array(K), tie: new Float32Array(K), tieSplit: false };
}
const restrict = (sim, keep) => {
  const out = { K: keep.length, S: sim.S, cs: new Float32Array(keep.length * sim.S), fa: new Float32Array(keep.length * sim.S), cut: sim.cut,
                quality: new Float32Array(keep.length), core: new Float32Array(keep.length), rate: 0, dup: new Float32Array(keep.length), tie: new Float32Array(keep.length), tieSplit: false };
  keep.forEach((k, i) => { out.cs.set(sim.cs.subarray(k * sim.S, (k + 1) * sim.S), i * sim.S); out.fa.set(sim.fa.subarray(k * sim.S, (k + 1) * sim.S), i * sim.S); });
  return out;
};
const pk = B.pick || { maxExpo: 60, minUnique: 2, maxCore: 15 };
const opts = (c, n, maxCore) => ({ n, maxExpo: Math.max(pk.maxExpo / 100, 1 / n), minUnique: pk.minUnique || 1, conds: [],
  maxCore: (maxCore == null ? (pk.maxCore || 0) : maxCore) / 100, objective: flagship(c) ? "cover" : "roi" });
const cx = ctxOf(S.seeded(1));
const out = { day: B.day, draft_group: B.draft_group, kept: K, pick: pk, contests: [] };
contests.forEach(c => {
  const sim = simA(c);
  const row = { id: String(c.id), name: c.name, size: c.size, fee: c.entry_fee, n: c.n, sets: {} };
  for (const v of PR.variants) {
    const set = v.set.filter(k => k < K);
    if (set.length < c.n) { row.sets[v.name] = null; continue; }
    const ch = S.pick(cx, opts(c, c.n, v.maxCore), set.map(k => cand[k]), restrict(sim, set), c, c.n).chosen;
    row.sets[v.name] = ch.map(i => cand[set[i]].ids);
  }
  out.contests.push(row);
});
console.log(JSON.stringify(out));
