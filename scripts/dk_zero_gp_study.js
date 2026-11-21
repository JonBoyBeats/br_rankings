// Zero-games players, the lineup part (2026-11-21; scripts/dk_zero_gp_study.py has the variants and scores the banks).
// One rule-free bank at bank noise 0.35 per variant on a graded night's lock-time slate, every variant on the same seed,
// the pool as scripts/dk_dnp_study.js has it (deep bench and punts left out), projections through today's gate.json:
//   cur      our projection, Questionable x the gate's factor (as the page)
//   zero_*   the zero-games group: our projection before the Q factor x the variant's factor (zf_<night>.json); the rest as cur
//
//   node scripts/dk_zero_gp_study.js DIR/<night>.json K DIR/zf_<night>.json DIR/zero_<night>.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, total, ffile, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const FX = JSON.parse(fs.readFileSync(ffile));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const VARIANTS = ["cur", "zero_q", "zero_f", "zero_p"];
const base = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
const noQ = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(Object.assign({}, r, { status: r.status === "Questionable" ? "" : r.status }), gate)]));
function alt(v) {
  if (v === "cur") return base;
  const f = FX[v] || {}, pts = {};
  rows.forEach(r => { pts[r.id] = f[r.id] != null ? noQ[r.id] * f[r.id] : base[r.id]; });
  return pts;
}
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const res = { banks: {}, group: Object.keys(FX.zero_q || {}).length, inPool: Object.keys(FX.zero_q || {}).filter(id => { const r = rows.find(x => x.id === id); return r && !r.deepOut; }).length };
  for (const v of VARIANTS) {
    const pts = alt(v), st = { lock: {}, excl: {}, cap: {}, floor: {} };
    const ctx = { rows, proj: r => pts[r.id], own: r => N.field.own[r.id] || 0, state: st, solver: sb.self.solver, random: S.seeded(+N.g * 7 + 35) };
    res.banks[v] = (await S.poolDraw(ctx, Object.assign({}, plain, { z: N.z, nightS: 0.35 }), +total)).lineups.map(l => l.ids);
    console.error(N.date, N.g, v, res.banks[v].length, "lineups");
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
