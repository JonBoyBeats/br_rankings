// B.3, the shared-lineup cut credit (2026-11-23 lock review; held since 2026-11-20). The cut (DKSim.cutPool, merit mode)
// gives each lineup to one idea for its floor (max(5, 1% of the idea's bank)) and the 7-of-8 near-copy skip: today the
// idea that drew it first (dk.html lineupGroup). A lineup two or more ideas drew is credited to only that first one.
// The proposal: credit a shared lineup to the idea, among those that drew it, where it ranks best (its percentile among
// that idea's lineups by the first round's value). Both cuts run on the same nights (the build's seed, its Keep, Cut %
// and nights), and the kept pools go to scripts/dk_shared_credit_study.py to be scored on real results.
//
//   node scripts/dk_shared_credit_study.js <night.json from dk_tier_signal_study.py extract> <build.json> <out.json>
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), D = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [nf, bf, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const bank = B.pool.map(ids => ({ ids: ids.map(String) }));
const cut = B.cut || {}, keep = cut.keep || 2000, pct = (cut.pct || 10) / 100, nights = cut.nights || 2000;
const groupOf = t => (B.groups || {})[t] || t;
const tagsOf = i => { const t = B.tags[i]; return Array.isArray(t) ? t : [t]; };
const first = bank.map((_, i) => groupOf(tagsOf(i)[0]));
const all = bank.map((_, i) => [...new Set(tagsOf(i).map(groupOf))]);
const contests = N.contests.map(x => ({ contest: x.contest, n: x.n }));
const ctx = () => ({ rows, proj: r => D.gatedProj(r, N.gate), own: r => N.field.own[r.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} },
                     solver: sb.self.solver, random: D.seeded((N.seed || 1) >>> 0) });
(async () => {
  const t0 = Date.now();
  const A = await D.cutPool(ctx(), bank, contests, N.field.field, N.z, keep, pct, nights, null, first, { mode: "merit" });
  // each lineup's first-round value: its running mean payout alone per contest, entries-weighted (every lineup is in round 1)
  const w = contests.map(c => c.n), val = bank.map((_, i) => { const e = A.est(i); return e.reduce((t, v, j) => t + v * w[j], 0); });
  const members = {}; bank.forEach((_, i) => all[i].forEach(g => { (members[g] = members[g] || []).push(i); }));
  const sorted = {}; Object.keys(members).forEach(g => { sorted[g] = members[g].map(i => val[i]).sort((a, b) => b - a); });
  const rankIn = (g, v) => { const a = sorted[g]; let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] > v) lo = m + 1; else hi = m; } return lo / a.length; };
  let shared = 0, moved = 0;
  const best = bank.map((_, i) => {
    if (all[i].length < 2) return first[i];
    shared++;
    const g = all[i].slice().sort((a, b) => rankIn(a, val[i]) - rankIn(b, val[i]))[0];
    if (g !== first[i]) moved++;
    return g;
  });
  const Bc = await D.cutPool(ctx(), bank, contests, N.field.field, N.z, keep, pct, nights, null, best, { mode: "merit" });
  const inA = new Set(A.keep), both = Bc.keep.filter(i => inA.has(i)).length;
  fs.writeFileSync(out, JSON.stringify({ key: N.key, bank: bank.length, shared, moved, keepA: A.keep, keepB: Bc.keep, overlap: both, secs: (Date.now() - t0) / 1000 }));
  console.error(N.key, "bank", bank.length, "shared", shared, "moved", moved, "kept", A.keep.length, Bc.keep.length, "overlap", both, ((Date.now() - t0) / 1000).toFixed(0) + "s");
})();
