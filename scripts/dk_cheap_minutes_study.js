// "Minutes is king" for cheap players, the lineup part (2026-11-21; scripts/dk_cheap_minutes_study.py has the variants
// and scores the banks). One rule-free bank ("No extra rules", drawRules' defaults) at bank noise 0.35 per projection
// variant on a graded night's lock-time slate (scripts/dk_bank_noise_study.py extract), every variant on the same seed,
// the pool as the DK page has it tonight: the deep bench and the punts (projected under 15 minutes without news) left
// out (dk_bank_noise_study.js --no-punts), projections through today's gate.json.
//
//   node scripts/dk_cheap_minutes_study.js DIR/<night>.json K DIR/cheap_<night>.json
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, total, out] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
const VARIANTS = ["cur", "flat_5k", "flatpos_5k", "flatgrp_5k", "shrink_5k", "flat_third", "flatpos_third", "flatgrp_third", "shrink_third"];
const base = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
// the variants, as alt_points in the .py
function alt(v) {
  if (v === "cur") return { pts: Object.assign({}, base), cheap: [] };
  const [mode, line] = v.split("_"), live = rows.filter(r => r.status !== "Out" && (r.min || 0) > 0);
  const rate = L => L.reduce((t, r) => t + base[r.id], 0) / L.reduce((t, r) => t + r.min, 0), flat = rate(live), fpos = {};
  ["G", "F"].forEach(g => { const L = live.filter(r => (r.position || "?")[0] === g); fpos[g] = L.length ? rate(L) : flat; });
  const cheap = new Set(line === "5k" ? live.filter(r => r.salary < 5000).map(r => r.id)
    : live.slice().sort((a, b) => a.salary - b.salary).slice(0, Math.ceil(live.length / 3)).map(r => r.id));
  const grp = live.filter(r => cheap.has(r.id)), fgrp = grp.length ? rate(grp) : flat, pts = {};
  rows.forEach(r => {
    if (!cheap.has(r.id)) { pts[r.id] = base[r.id]; return; }
    const f = mode === "flatpos" ? (fpos[(r.position || "?")[0]] || flat) : mode === "flatgrp" ? fgrp : flat;
    pts[r.id] = mode === "shrink" ? 0.5 * base[r.id] + 0.5 * r.min * f : r.min * f;
  });
  return { pts, cheap: [...cheap] };
}
const plain = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] };
(async () => {
  const res = { deep: rows.filter(r => r.deepOut).length, banks: {}, cheap: {}, proj: { cur: base } };
  for (const v of VARIANTS) {
    const a = alt(v), st = { lock: {}, excl: {}, cap: {}, floor: {} };
    const ctx = { rows, proj: r => a.pts[r.id], own: r => N.field.own[r.id] || 0, state: st, solver: sb.self.solver, random: S.seeded(+N.g * 7 + 35) };
    res.banks[v] = (await S.poolDraw(ctx, Object.assign({}, plain, { z: N.z, nightS: 0.35 }), +total)).lineups.map(l => l.ids);
    res.cheap[v] = a.cheap;
    console.error(N.date, N.g, v, res.banks[v].length, "lineups");
  }
  fs.writeFileSync(out, JSON.stringify(res));
})();
