/* The late-swap study's simulated nights (scripts/dk_lateswap_study.py): each player's points on S nights from the DK
 * page's own outcome model (dk_sim.js DKSim.nightPoints: projection + his expected miss x the field's outcome shape z,
 * with the team and game draws), seeded so a rerun repeats. Games are independent of each other in that model, so a
 * started game's real result carries nothing into the draws of the games still to tip.
 *
 *   node scripts/dk_lateswap_study.js IN.json OUT.json
 *   IN:  {rows: [{id, team, game, proj, miss_dk, status}], z: [...], S, seed}
 *   OUT: {ids: [...], nights: [[points per id], ...]}   (S rows)
 */
const fs = require("fs"), path = require("path");
const DKSim = require(path.join(__dirname, "..", "dk_sim.js"));
const [inp, out] = process.argv.slice(2);
const a = JSON.parse(fs.readFileSync(inp, "utf8"));
const rows = a.rows.map(r => Object.assign({}, r));
const ctx = { rows, proj: r => r.proj || 0, random: DKSim.seeded(a.seed || 1) };
const ids = rows.map(r => r.id), nights = [];
for (let s = 0; s < a.S; s++) {
  const p = DKSim.nightPoints(ctx, a.z, 1);
  nights.push(ids.map(id => Math.round(100 * (p[id] || 0)) / 100));
}
fs.writeFileSync(out, JSON.stringify({ ids, nights }));
