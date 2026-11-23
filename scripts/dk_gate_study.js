// The projection gate at the freeze (2026-11-23 lock review): one rule-free bank at bank noise 0.35 per variant on a
// graded night's lock-time slate (scripts/dk_bank_noise_study.py extract), both on the same seed, the pool as the DK page
// has it (deep bench and punts left out, as scripts/dk_zero_gp_study.js):
//   cur   today's gate.json (the calibration blend: ours x 0.5 + DraftKings' average x 0.5 in every band), Q x its factor
//   ours  the gate closed (ours alone), Q x its factor (the gate's own rule: DK's average beats ours in no band)
//   part  closed under $6,000 only (ours alone there), the blend kept at $6,000+ (where the two are level)
//
//   node scripts/dk_gate_study.js DIR/<night>.json K DIR/gate_<night>.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, total, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const closed = Object.assign({}, gate, { bands: (gate.bands || []).map(b => Object.assign({}, b, { open: false })) });
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const part = Object.assign({}, gate, { bands: (gate.bands || []).map(b => Object.assign({}, b, { open: b.lo >= 6000 ? b.open : false })) });
const VARIANTS = { cur: gate, ours: closed, part };
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const res = { banks: {} };
  for (const v of Object.keys(VARIANTS)) {
    const pts = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, VARIANTS[v])])), st = { lock: {}, excl: {}, cap: {}, floor: {} };
    const ctx = { rows, proj: r => pts[r.id], own: r => N.field.own[r.id] || 0, state: st, solver: sb.self.solver, random: S.seeded(+N.g * 7 + 35) };
    res.banks[v] = (await S.poolDraw(ctx, Object.assign({}, plain, { z: N.z, nightS: 0.35 }), +total)).lineups.map(l => l.ids);
    console.error(N.date, N.g, v, res.banks[v].length, "lineups");
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
