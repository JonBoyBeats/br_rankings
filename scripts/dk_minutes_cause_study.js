// Where our minutes go wrong, the lineup part (2026-11-21; scripts/dk_minutes_cause_study.py has the causes and scores
// the banks). One rule-free bank at bank noise 0.35 for current minutes and one for the candidate, the same seed, on a
// graded night's lock-time slate (scripts/dk_bank_noise_study.py extract), the pool as the DK page has it tonight (deep
// bench and punts left out, as scripts/dk_cheap_minutes_study.js), projections through today's gate.json.
// The candidate "out": a teammate of an Out regular (season average 15+) gets his projected hand-off boost scaled by K
// (the boost: his minutes less the team fit with the Outs put back in, as the .py's prep; no steepen before 2026-11-20),
// his points moving with his minutes.
//
//   node scripts/dk_minutes_cause_study.js DIR/<night>.json K TOTAL DIR/mincause_<night>.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, K, total, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const base = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
// the candidate's points: the hand-off boost scaled by K
const cand = Object.assign({}, base); let moved = 0;
const teams = {}; rows.forEach(r => { (teams[r.team] = teams[r.team] || []).push(r); });
Object.values(teams).forEach(rs => {
  const live = rs.filter(r => r.status !== "Out" && r.min), outs = rs.filter(r => r.status === "Out" && (r.min_avg || 0) >= 15);
  if (!outs.length || live.length < 5) return;
  const m0 = live.map(r => r.min_raw || r.min), om = outs.map(r => r.min_raw || r.min || r.min_avg);
  const b = S.fitMinutes(m0.concat(om)).slice(0, live.length);
  live.forEach((r, i) => {
    const m = Math.max(0, r.min + (+K - 1) * (r.min - b[i]));
    if (Math.abs(m - r.min) >= 1) moved++;
    cand[r.id] = base[r.id] * (m / r.min);
  });
});
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const res = { banks: {}, moved: { cur: 0, out: moved } };
  for (const [v, pts] of [["cur", base], ["out", cand]]) {
    const ctx = { rows, proj: r => pts[r.id], own: r => N.field.own[r.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, solver: sb.self.solver, random: S.seeded(+N.g * 7 + 35) };
    res.banks[v] = (await S.poolDraw(ctx, Object.assign({}, plain, { z: N.z, nightS: 0.35 }), +total)).lineups.map(l => l.ids);
    console.error(N.date, N.g, v, res.banks[v].length, "lineups");
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
