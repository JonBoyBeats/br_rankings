// QMIN study's same-seed bank check (2026-11-25): one rule-free bank at bank noise 0.35 with today's minutes and one
// with the candidate's, the same seed, on a graded night's lock-time slate (dk_bank_noise_study.py extract), the pool
// as the DK page has it (deep bench and punts out, as dk_minutes_cause_study.js), projections through gate.json. The
// candidate's points: today's x (candidate minutes / today's minutes), from the study's minutes file.
//
//   node scripts/dk_qmin_bank.js DIR/<night>.json MINS.json SLATE TOTAL OUT.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, minsFile, slate, total, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const M = JSON.parse(fs.readFileSync(minsFile))[slate] || {};
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const base = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
const cand = Object.assign({}, base); let moved = 0;
rows.forEach(r => { const m = M[r.id]; if (m && m[0] != null && m[1]) { cand[r.id] = base[r.id] * m[0] / m[1]; if (Math.abs(m[0] - m[1]) >= 1) moved++; } });
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const res = { banks: {}, moved: { cur: 0, cand: moved } };
  for (const [v, pts] of [["cur", base], ["cand", cand]]) {
    const ctx = { rows, proj: r => pts[r.id], own: r => N.field.own[r.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, solver: sb.self.solver, random: S.seeded(+N.g * 7 + 35) };
    res.banks[v] = (await S.poolDraw(ctx, Object.assign({}, plain, { z: N.z, nightS: 0.35 }), +total)).lineups.map(l => l.ids);
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
