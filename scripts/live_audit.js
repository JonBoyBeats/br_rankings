// Live page green audit: replays past nights (tests/live_audit/<date>.json) through nba_live.html's own
// grade() and checks what a night of greens looks like. Each player's points build up over his real
// stints (from the nightly box archive); games tip 30 minutes apart in ESPN's order and run 2h20m of
// wall clock. Every 15 minutes of the night it counts each round's dark and light greens.
//   node scripts/live_audit.js [-v] [tests/live_audit/2026-10-26.json ...]
// Fails (exit 1) when: anything is green before a game has started, a round has more than one dark
// green, or a round shows more than MAX_ROUND greens at once. Add a night with
// scripts/live_audit_fixture.py when one looks wrong.
const fs = require("fs"), path = require("path");
const MAX_ROUND = 4, WALL = 140, STEP = 15;
const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "nba_live.html"), "utf8");
function lift(name) {
  const i = html.indexOf("function " + name + "("), eol = html.indexOf("\n", i);
  if (i < 0) throw new Error("nba_live.html has no " + name + "()");
  if (html.slice(i, eol).trim().endsWith("}")) return html.slice(i, eol);     // a one-line function
  return html.slice(i, html.indexOf("\n}\n", i) + 2);
}
const state = { proj: {} };
eval([/var TEAMS = [^\n]+/, /var POOLS = [^\n]+/, /var ESPN_ALIASES = \{[^}]+\};/].map(re => html.match(re)[0])
  .concat(["roundOf", "normName", "played", "grade"].map(lift)).join("\n"));

const args = process.argv.slice(2), verbose = args.includes("-v");
let files = args.filter(a => a !== "-v");
if (!files.length) {
  const dir = path.join(root, "tests", "live_audit");
  files = fs.readdirSync(dir).filter(f => f.endsWith(".json")).sort().map(f => path.join(dir, f));
}
let failed = 0;
for (const f of files) {
  const fx = JSON.parse(fs.readFileSync(f, "utf8"));
  state.proj = {};
  fx.morning.forEach(r => { const k = normName(r.name); state.proj[ESPN_ALIASES[k] || k] = r.fp; });
  const tip = {}, game = {}, teamGame = {}, boxBy = {};
  fx.games.forEach((g, i) => { tip[g.id] = i * 30; game[g.id] = g; });
  fx.box.forEach(r => { const k = normName(r.name); boxBy[(ESPN_ALIASES[k] || k) + "|" + r.team] = r; teamGame[r.team] = r.gid; });
  const end = Math.max(...Object.values(tip)) + WALL, problems = [], lines = [];
  let snaps = 0, dark = 0, light = 0, most = 0;
  for (let t = 0; t <= end; t += STEP) {
    const rows = fx.players.map(p => {
      const k = normName(p.first_name + " " + p.last_name), b = boxBy[k + "|" + p.team], G = game[teamGame[p.team]];
      if (!G) return { p, b: null, g: null, fp: null };
      const len = G.len || 2880, el = t - tip[G.id];
      const sec = el <= 0 ? 0 : el >= WALL ? len : Math.round(el / WALL * len);
      const st = sec <= 0 ? "pre" : sec >= len ? "post" : "in";
      const per = sec >= 2880 ? 5 : Math.floor(sec / 720) + 1, left = per <= 4 ? per * 720 - sec : 0;
      const g = { state: st, period: per, clock: Math.floor(left / 60) + ":" + String(left % 60).padStart(2, "0"), status: "STATUS_IN_PROGRESS" };
      if (!b) return { p, b: null, g, fp: null };
      const on = (b.st || []).reduce((s, x) => s + Math.max(0, Math.min(x[1], sec) - x[0]), 0);
      const tot = (b.st || []).reduce((s, x) => s + x[1] - x[0], 0);
      return { p, b: { out: !!b.dnp }, g, fp: b.dnp || st === "pre" ? null : tot ? Math.round(b.fp * on / tot * 10) / 10 : 0 };
    });
    grade(rows);
    const per = {};
    rows.forEach(r => {
      if (!r.good) return;
      if (!(r.played > 0)) problems.push(`${t}m: ${r.p.last_name} green before his game started`);
      const x = per[r.round] = per[r.round] || [0, 0];
      x[r.good === 1 ? 0 : 1]++;
    });
    Object.keys(per).forEach(rd => {
      const [d, l] = per[rd];
      if (d > 1) problems.push(`${t}m: round ${rd} has ${d} dark greens`);
      if (d + l > MAX_ROUND) problems.push(`${t}m: round ${rd} has ${d + l} greens`);
      most = Math.max(most, d + l); dark += d; light += l;
    });
    snaps++;
    lines.push(`${String(t).padStart(4)}m  ` + [1, 2, 3, 4, 5, 6].map(rd => "R" + rd + " " + (per[rd] ? per[rd][0] + "/" + per[rd][1] : "-/-")).join("  "));
  }
  console.log(`${problems.length ? "FAIL" : "ok  "} ${fx.day} ${fx.label}: ${fx.players.length} players, ` +
              `${(dark / snaps).toFixed(1)} dark + ${(light / snaps).toFixed(1)} light green at a time, most in one round ${most}`);
  if (verbose) console.log(lines.join("\n"));
  problems.slice(0, 10).forEach(x => console.log("     " + x));
  failed += problems.length ? 1 : 0;
}
process.exit(failed ? 1 : 0);
