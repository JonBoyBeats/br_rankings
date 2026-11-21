// Tier signal study (2026-11-21, the coordinator's question 1): rebuild the Cut step's idea board for a night's kept
// lineups, as the DK page's ideaBoard does (dk.html): each kept lineup simmed alone in every contest the night was entered
// in, on the slate's nights (the build's nights_seed mixed with the contest id, the page's nightsCtx), S nights; its
// value = sum over contests of entries x its mean payout alone; tiers A / B / C by DKSim.tiers on those values and their
// odd / even halves. Input from scripts/dk_tier_signal_study.py extract; output for its score step.
//
//   node scripts/dk_tier_signal_study.js DIR/<key>.json [S]   -> DIR/<key>_board.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), D = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const file = process.argv[2], S = +(process.argv[3] || 3000), N = JSON.parse(fs.readFileSync(file));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const pool = N.keep.map(ids => ({ ids }));
const K = pool.length, ret = new Float64Array(K), odd = new Float64Array(K), even = new Float64Array(K);
let w = 0;
for (const x of N.contests) {
  const c = x.contest, n = x.n;
  const ctx = { rows, proj: r => D.gatedProj(r, N.gate), own: r => N.field.own[r.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} },
                solver: sb.self.solver, random: D.seeded((N.seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0) };
  const sim = D.simulate(ctx, pool, N.field.field, N.z, c, n, S), st = D.aloneStats(sim, c);
  for (let k = 0; k < K; k++) { ret[k] += n * (st.odd[k] + st.even[k]) / 2; odd[k] += n * st.odd[k]; even[k] += n * st.even[k]; }
  w += n;
  console.error(N.key, c.name, "n", n, "simmed", K);
}
const tr = D.tiers(Array.from(ret), Array.from(odd), Array.from(even));
fs.writeFileSync(file.replace(/\.json$/, "_board.json"), JSON.stringify({ key: N.key, w, S, sigma: tr.sigma, tier: tr.tier,
  values: Array.from(ret, v => v / Math.max(1, w)) }));
