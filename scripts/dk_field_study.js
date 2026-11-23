// The field study's banks (2026-11-23; scripts/dk_field_study.py banks writes the inputs and scores the output). One
// rule-free bank at bank noise 0.35 on a graded night's lock-time projections (every field on the same seed), the pool
// as the page has it (deep bench and punts left out), then the cut (DKSim.cutPool, by merit) against each field given:
// which lineups it keeps when the simulated field is the current one, and when it is the calibrated one.
//
//   node scripts/dk_field_study.js IN.json OUT.json
//   IN:  {players: {id: card}, z, contest: {size, entry_fee, payouts}, fields: {label: [[ids]...]}, bank, keep, cut, nights, seed}
//   OUT: {bank: [[ids]...], keep: {label: [bank index...]}}
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [inp, out] = process.argv.slice(2), A = JSON.parse(fs.readFileSync(inp, "utf8"));
const gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(A.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const pts = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const st = { lock: {}, excl: {}, cap: {}, floor: {} };
  const ctx = { rows, proj: r => pts[r.id], own: r => 0, state: st, solver: sb.self.solver, random: S.seeded(A.seed || 1) };
  const bank = (await S.poolDraw(ctx, Object.assign({}, plain, { z: A.z, nightS: 0.35 }), A.bank)).lineups;
  const res = { bank: bank.map(l => l.ids), keep: {} };
  for (const [label, F] of Object.entries(A.fields)) {
    const cx = { rows, proj: r => pts[r.id], own: r => 0, state: st, solver: sb.self.solver, random: S.seeded((A.seed || 1) + 99) };
    const c = await S.cutPool(cx, bank, [{ contest: A.contest, n: 1 }], F, A.z, A.keep, A.cut || 0.1, A.nights, null, null, { mode: "merit" });
    res.keep[label] = c.keep;
    console.error(label, "kept", c.keep.length, "of", bank.length);
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
