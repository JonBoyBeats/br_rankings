// Shadow portfolios: before each DraftKings CBB slate locks, the 20-lineup portfolio each of the five frozen rule
// sets (dk_sim.js RULESETS, on BASE) would have entered (with its candidate pool, for the random-set benchmark, and
// for No extra rules also the pool's top 20 by expected payout alone), built by the same code as the DK page's Sim & pick, on our
// projection through the projection gate, with no locks, excludes or overrides. Graded after the slate against the
// real contest standings (scripts/cbb_daily.py): top-10% and cash rates first, each rule set against "No extra rules"
// slate by slate. Run hourly by battle-royale-research's NBA ADP poll workflow until the first game.
//
//   node scripts/dk_shadow.js --mirror <dir with dk_cbb_morning.json, dk_cbb_field.json> --out <file>
//                             [--gate analysis/cbb/dk/gate.json] [--save-dir <dir>] [--sims 3000]
//
// The contest each slate's portfolios are built for: the biggest field taking BASE.n entries a user, with a payout
// table. Draws are seeded by draft group and rule set, so a run can be rebuilt exactly.
const fs = require("fs"), path = require("path"), vm = require("vm");

const ROOT = path.join(__dirname, "..");
const S = require(path.join(ROOT, "dk_sim.js"));
const sandbox = { self: {} };
vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sandbox);
const solver = sandbox.self.solver;
// the code this run is on: this repo (the sim, rule sets, pick) and the one running it (projections, field), when git can say
function sha(dir) { try { return require("child_process").execSync("git -C " + JSON.stringify(dir) + " rev-parse --short HEAD", { stdio: ["ignore", "pipe", "ignore"] }).toString().trim(); } catch (e) { return "?"; } }
const VERSION = "br_rankings " + sha(ROOT) + ", battle-royale-research " + sha(process.cwd());

function arg(name, dflt) { const i = process.argv.indexOf("--" + name); return i > 0 ? process.argv[i + 1] : dflt; }

(async () => {
  const mirror = arg("mirror"), out = arg("out"), saveDir = arg("save-dir"), sims = +arg("sims", S.BASE.sims);
  const gatePath = arg("gate", path.join(ROOT, "analysis", "cbb", "dk", "gate.json"));
  const morning = JSON.parse(fs.readFileSync(path.join(mirror, "dk_cbb_morning.json")));
  const field = JSON.parse(fs.readFileSync(path.join(mirror, "dk_cbb_field.json")));
  const gate = fs.existsSync(gatePath) ? JSON.parse(fs.readFileSync(gatePath)) : null;
  const doc = { generated_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"), version: VERSION, base: S.BASE, cand: { unique: S.CAND_UNIQUE, rand: S.CAND_RAND },
                gate: gate, slates: {} };
  for (const sl of morning.slates) {
    if (sl.locked || new Date(sl.start) <= new Date()) continue;
    const F = field.slates[String(sl.draft_group_id)];
    const contest = (sl.contests || []).filter(c => c.payouts && (c.max_per_user || 1) >= S.BASE.n).sort((a, b) => (b.size || 0) - (a.size || 0))[0];
    if (!F || !F.field || !F.field.length || !contest) {
      console.log(`[shadow ${sl.draft_group_id}] skipped: ${!contest ? "no contest taking " + S.BASE.n + " entries with a payout table" : "no simulated field"}`);
      continue;
    }
    const rows = Object.entries(sl.players).map(([id, r]) => Object.assign({ id }, r));
    const entry = { start: sl.start, day: sl.day, contest: { id: contest.id, name: contest.name, size: contest.size, entry_fee: contest.entry_fee },
                    nights: sims, rulesets: {} };
    for (let i = 0; i < S.RULESETS.length; i++) {
      const set = S.RULESETS[i], t = Date.now();
      const ctx = { rows, proj: r => S.gatedProj(r, gate), own: r => F.own[r.id] || 0, state: { lock: {}, excl: {}, cap: {} }, solver,
                    random: S.seeded(sl.draft_group_id * 31 + i) };
      const o = S.rulesFor(set, F.field, F.own);
      const res = await S.simPick(ctx, o, contest, F.field, field.z, S.BASE.candidates, sims);
      entry.rulesets[set.key] = res.error ? { name: set.name, rules: o, error: res.error } : {
        name: set.name, rules: o, lineups: res.lineups.map(l => ({ ids: l.ids, slots: l.slots, sim: l.sim })), expected: res.total,
        fee: res.fee, any_first: res.anyFirst, coverage: res.coverage, diversity: res.diversity, cut: res.cut, stability: res.stability,
        candidates: res.candidates, why: res.why,
        pool: res.cand.map(l => l.ids) };          // the candidate pool, for the random-set benchmark
      if (set.key === "none" && !res.error) {
        // the top 20 of the same pool by expected payout alone (no self-competition, no caps), to set beside the pick
        const top = S.topAlone(res.sim, contest, S.BASE.n);
        entry.top20_alone = { lineups: top.map(k => ({ ids: res.cand[k].ids, slots: res.cand[k].slots })),
                              expected: S.value(res.sim, contest, top), diversity: S.diversity(ctx, top.map(k => res.cand[k])) };
      }
      console.log(`[shadow ${sl.draft_group_id}] ${set.key}: ${res.error || res.lineups.length + " lineups, expected $" + res.total.toFixed(2) +
                  " on $" + res.fee.toFixed(2) + ", stability " + Math.round(100 * res.stability.kept) + "%"} (${((Date.now() - t) / 1000).toFixed(0)}s)`);
    }
    doc.slates[sl.draft_group_id] = entry;
    if (saveDir) fs.writeFileSync(path.join(saveDir, `${sl.day}_${sl.draft_group_id}_shadow.json`), JSON.stringify(entry) + "\n");
  }
  fs.writeFileSync(out, JSON.stringify(doc) + "\n");
  console.log(`dk_cbb_shadow.json: ${Object.keys(doc.slates).length} slate(s)`);
})().catch(e => { console.error(e); process.exit(1); });
