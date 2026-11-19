// Bank noise backtest (2026-11-19, versions.csv): draw banks at several Bank noise settings s (dk_sim.js nightPoints'
// s, the DK page's Bank noise) on a graded night's lock-time slate, for scripts/dk_bank_noise_study.py to score.
//
//   python3 scripts/dk_bank_noise_study.py extract --mirror ../br-adp-mirror --out DIR        (lock-time slates)
//   node scripts/dk_bank_noise_study.js DIR/<date>.json 2000 1,0.75,0.5,0.35 DIR/banks_<date>.json
//   node scripts/dk_bank_noise_study.js DIR/<date>.json 2000 1,0.5,0.35 DIR/rep_<date>.json --ideas analysis/cbb/dk/builds/<the night's build>
//   python3 scripts/dk_bank_noise_study.py score --dir DIR
//   (--no-punts on either draw: the punt test, players projected under 15 minutes left out unless his minutes rose on news)
//
// Without --ideas: a "No extra rules" bank (drawRules' defaults) of K lineups at each s. With it: the night's own ideas
// (the build's tag_settings, locks and excludes), each redrawn in proportion to its share of that night's bank. The
// deep bench is left out as the DK page does tonight (the team card's rule, rebuilt from the slate rows: projected
// under 12 minutes and under 8 a game or in fewer than half the team's games). Projections through today's gate.json.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [file, total, ss, out] = process.argv.slice(2), ii = process.argv.indexOf("--ideas");
const N = JSON.parse(fs.readFileSync(file)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const B = ii > 0 ? JSON.parse(fs.readFileSync(process.argv[ii + 1])) : null;
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
// --no-punts (the punt test, 2026-11-19): also leave out every player projected under 15 minutes, unless his minutes
// rose on news (a teammate Out at lock and his projection above his season average)
if (process.argv.includes("--no-punts")) {
  const outTeam = {}; rows.forEach(r => { if (r.status === "Out") outTeam[r.team] = 1; });
  rows.forEach(r => { if (r.status !== "Out" && (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg)) r.deepOut = true; });
}
const plain = { "No extra rules": { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [] } };
const count = {}; if (B) B.tags.forEach(t => { const k = Array.isArray(t) ? t.join(" + ") : t; count[k] = (count[k] || 0) + 1; });
(async () => {
  const res = { deep: rows.filter(r => r.deepOut).length, banks: {} };
  for (const s of ss.split(",").map(Number)) {
    const L = []; let i = 0;
    for (const [tag, o0] of Object.entries(B ? B.tag_settings : plain)) {
      if (B && !count[tag]) continue;
      const k = B ? Math.max(1, Math.round(+total * count[tag] / B.tags.length)) : +total;
      const st = { lock: Object.fromEntries((o0.lock || []).map(x => [x, 1])), excl: Object.fromEntries((o0.excl || []).map(x => [x, 1])), cap: {}, floor: {} };
      const ctx = { rows, proj: r => S.gatedProj(r, gate), own: r => N.field.own[r.id] || 0, state: st, solver: sb.self.solver,
                    random: S.seeded(+N.g * (B ? 13 : 7) + (B ? i++ : 0) + Math.round(s * 100)) };
      (await S.poolDraw(ctx, Object.assign({}, o0, { z: N.z, nightS: s }), k)).lineups.forEach(l => L.push(l.ids));
    }
    res.banks[s] = L; console.error(N.date, "s", s, L.length, "lineups");
  }
  res.proj = Object.fromEntries(rows.map(r => [r.id, S.gatedProj(r, gate)]));
  fs.writeFileSync(out, JSON.stringify(res));
})();
