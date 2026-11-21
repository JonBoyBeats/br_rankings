// Who sits, the lineup part (2026-11-21; scripts/dk_dnp_study.py fits the chances and scores the banks). One rule-free
// bank at bank noise 0.35 per projection on a graded night's lock-time slate, every variant on the same seed, the pool
// as scripts/dk_cheap_minutes_study.js has it (deep bench and punts left out), projections through today's gate.json:
//   cur        our projection, Questionable x the gate's factor (as the page)
//   dnp_cheap  under $5,000: the held-out chance to play x our projection (the Q factor replaced); the rest as cur
//   dnp_all    every player: chance x our projection
//
//   node scripts/dk_dnp_study.js DIR/<night>.json K DIR/p_<night>.json DIR/dnp_<night>.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, total, pfile, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const P = JSON.parse(fs.readFileSync(pfile));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const VARIANTS = ["cur", "dnp_cheap", "dnp_all"];
const base = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
const noQ = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(Object.assign({}, r, { status: r.status === "Questionable" ? "" : r.status }), gate)]));
function alt(v) {
  if (v === "cur") return base;
  const pts = {};
  rows.forEach(r => { pts[r.id] = P[r.id] != null && (v === "dnp_all" || r.salary < 5000) ? noQ[r.id] * P[r.id] : base[r.id]; });
  return pts;
}
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const res = { deep: rows.filter(r => r.deepOut).length, banks: {}, matched: rows.filter(r => P[r.id] != null).length };
  for (const v of VARIANTS) {
    const pts = alt(v), st = { lock: {}, excl: {}, cap: {}, floor: {} };
    const ctx = { rows, proj: r => pts[r.id], own: r => N.field.own[r.id] || 0, state: st, solver: sb.self.solver, random: S.seeded(+N.g * 7 + 35) };
    res.banks[v] = (await S.poolDraw(ctx, Object.assign({}, plain, { z: N.z, nightS: 0.35 }), +total)).lineups.map(l => l.ids);
    console.error(N.date, N.g, v, res.banks[v].length, "lineups");
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
