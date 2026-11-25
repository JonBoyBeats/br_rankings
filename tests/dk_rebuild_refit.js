// The DK page's Mark out on the rebuilt minutes (2026-11-25): DKSim.refitTeam on the pipeline's min_pre / min_ctx gives
// the minutes battle-royale-research cbb_nightly.rebuilt_minutes gives the same availability (the fixture is written by
// that repo's tests/cbb_pbp.py: a team, its star ruled out, the pipeline's minutes with him out). node tests/dk_rebuild_refit.js
const D = require("../dk_sim.js"), f = require("./dk_fixture/rebuild_refit.json");
let ok = 0, bad = 0;
const check = (name, cond, info) => { console.log((cond ? "PASS " : "FAIL ") + name + (cond || !info ? "" : "  " + JSON.stringify(info))); cond ? ok++ : bad++; };
const cards = Object.entries(f.rows).filter(([k, r]) => r.status !== "Out" && !f.out.includes(k)).map(([k, r]) => ({ id: k, min_pre: r.min_pre, min_ctx: r.min_ctx }));
const m = D.refitTeam(cards, f.out);
const worst = Math.max(...Object.keys(f.want).map(k => Math.abs(m[k] - f.want[k])));
check("refitTeam: the star ruled out gives the pipeline's minutes (within rounding)", worst < 0.06, { worst, m, want: f.want });
check("refitTeam: the team at 200", Math.abs(Object.values(m).reduce((a, x) => a + x, 0) - 200) < 1e-6);
check("fitShare: proportional to 200, none over 40", (v => Math.abs(v.reduce((a, x) => a + x, 0) - 200) < 1e-6 && Math.max(...v) <= 40 + 1e-9)(D.fitShare([30, 30, 30, 30, 30, 20, 10, 5], 200)));
const none = D.refitTeam(cards, []);
check("refitTeam: nothing flipped leaves the context alone (the star's teammates without his min_ctx)", Object.keys(none).every(k => Math.abs(none[k] - m[k]) > 0 || !(f.rows[k].min_ctx || {}).dkstar));
console.log(ok + " passed, " + bad + " failed");
process.exit(bad ? 1 : 0);
