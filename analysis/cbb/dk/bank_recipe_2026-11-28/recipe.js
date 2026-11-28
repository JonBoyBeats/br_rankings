// Section 7 replays (2026-11-28, analysis only): for one graded slate, on the slate and the simulated field as they
// stood at lock (extract.py), draw banks with the page's draw (DKSim.poolDraw: each lineup the best one for one
// simulated night at Bank noise 0.35, less levW x projected ownership; Under: lowN players under 10% owned; the deep
// bench left out as the team card does), one seed policy for all recipes, then (with a build) cut by merit
// (DKSim.cutPool, each batch its own idea, floors max(5, 1%)) and fill every contest the build entered as the fill
// studies do (largest stake first, a lineup in at most 3 contests, night cap 60%, DKSim.pick: Max coverage for
// flagships, Max ROI otherwise, the build's pick settings). Output: every recipe's bank, kept and picks (player ids).
//
//   node recipe.js <night.json> <greens.json> <out.json> [--build build.json] [--total 1500] [--keepfrac 0.3] [--jk 0.5]
//   recipes: d9 (the 9 cells L{0,.1,.2} x U{0,1,2}, equal shares), plain (L0 U0), greencore (a third under "at least
//   n of the slate's greens", n = 3 with 5+ greens else 2, the rest plain), jitter (plain, each draw's projections
//   multiplied by exp(sigma_t Z - sigma_t^2/2), sigma_t = JK x the tier's measured miss / its mean projection),
//   light (half plain, half L0.1 U0); and for 1b: greens600 vs plain600 (the GREENS rule vs plain, 600 each).
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, "..", "..", "..", ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [nf, gf, outf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
const T = +opt("total", 1500), KF = +opt("keepfrac", 0.3), JK = +opt("jk", 0.5), bf = opt("build", null), ONLY = opt("only", null);
const N = JSON.parse(fs.readFileSync(nf)), G = JSON.parse(fs.readFileSync(gf))[N.date + "_" + N.g] || [];
const gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}; rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); });
rows.forEach(r => { r.deepOut = r.status !== "Out" && (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2); });
const live = new Set(rows.filter(r => r.status !== "Out" && !r.deepOut).map(r => r.id));
const greens = G.filter(id => live.has(id));
const base = { n: 1, maxExpo: 1, minUnique: 1, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: [], z: N.z, nightS: 0.35 };
// the jitter's tier sizes: the graded slates' measured miss (MAE of fp_dk vs actual, played, projected 5+) over the mean projection
const TIER = JSON.parse(opt("tiers", '{"lt5":[6.09,10.6],"5to7":[7.92,19.0],"7p":[8.33,29.0]}'));
const sig = r => { const s = r.salary || 0, t = s < 5000 ? TIER.lt5 : s < 7000 ? TIER["5to7"] : TIER["7p"]; return JK * t[0] / t[1]; };
const projOf = r => S.gatedProj(r, gate);
const ctxOf = (rnd, pj) => ({ rows, proj: pj || projOf, own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, solver: sb.self.solver, random: rnd });
function normal(r) { const u = 1 - r(), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
const seedOf = (label, k) => ((+N.g * 7919) ^ (k * 104729) ^ [...label].reduce((t, c) => (t * 31 + c.charCodeAt(0)) >>> 0, 7)) >>> 0;
async function batch(label, o, K, seen) {
  const L = [];
  if (o.jitter) {                   // one draw per lineup, its own jittered projections
    const rj = S.seeded(seedOf(label, 1)), rd = S.seeded(seedOf(label, 2));
    let tries = 0;
    while (L.length < K && tries < 3 * K) {
      tries++;
      const m = {}; rows.forEach(r => { const s = sig(r); m[r.id] = projOf(r) * Math.exp(s * normal(rj) - s * s / 2); });
      const res = await S.poolDraw(ctxOf(rd, r => m[r.id]), Object.assign({}, base, o), 1);
      const x = res.lineups[0]; if (!x) break;
      const key = x.ids.slice().sort().join(","); if (seen[key]) continue; seen[key] = 1; L.push(x.ids.map(String));
    }
    return L;
  }
  const res = await S.poolDraw(ctxOf(S.seeded(seedOf(label, 0))), Object.assign({}, base, o), K + 50);
  for (const x of res.lineups) { const key = x.ids.slice().sort().join(","); if (seen[key]) continue; seen[key] = 1; L.push(x.ids.map(String)); if (L.length >= K) break; }
  return L;
}
const gn = greens.length >= 5 ? 3 : 2;
const grule = greens.length >= 2 ? [{ type: "min", ids: greens, n: Math.min(gn, greens.length) }] : null;
const RECIPES = {
  d9: [0, 0.1, 0.2].flatMap(l => [0, 1, 2].map(u => ["L" + l + " U" + u, { levW: l, lowN: u }, T / 9])),
  plain: [["L0 U0", {}, T]],
  greencore: grule ? [["GREEN core", { conds: grule }, Math.round(T / 3)], ["L0 U0", {}, T - Math.round(T / 3)]] : null,
  jitter: [["jitter", { jitter: 1 }, T]],
  light: [["L0 U0", {}, T / 2], ["L0.1 U0", { levW: 0.1 }, T / 2]],
  greens600: grule ? [["GREENS rule", { conds: grule }, 600]] : null,
  plain600: [["L0 U0 (1b)", {}, 600]]
};
// cut and fill (with a build)
const B = bf ? JSON.parse(fs.readFileSync(bf)) : null;
let cs = [];
if (B) {
  const sup = (() => { const f = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json"); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f)).contests || {} : {}; })();
  cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id && c.payouts) || sup[id]).filter(c => c && c.payouts)
    .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) })).filter(c => c.n > 0)
    .sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n || (b.entry_fee || 0) - (a.entry_fee || 0));
}
const flagship = c => /pull up jumper/i.test(c.name || "") || (!/dime time|and-one|quarter jukebox|qualifier|satellite/i.test(c.name || "") && (c.size || 0) >= 100 && (c.size || 0) < 800);
const pk = Object.assign({ maxExpo: 60, minUnique: 3, maxCore: 15 }, (B && B.pick) || {});
const seed = (B && B.nights_seed) || 1405393094, CN = 1000, SIMS = 1000, MAXC = 3, NIGHT = 60;
const fieldL = N.field.field;
async function cutFill(bank, tags) {
  const keep = Math.max(100, Math.round(KF * bank.length));
  const total = cs.reduce((a, c) => a + c.n, 0), nightLim = Math.max(1, Math.floor(NIGHT / 100 * total + 1e-9));
  const L = bank.map(ids => ({ ids }));
  const res = await S.cutPool(ctxOf(S.seeded(seed + 1)), L, cs.map(c => ({ contest: c, n: c.n })), fieldL, N.z, keep, 0.1, CN, null, tags, { mode: "merit" });
  const pool = res.keep.map(i => L[i]);
  const used = {}, picks = {}, nightCount = {};
  for (const c of cs) {
    const idx = pool.map((_, i) => i).filter(i => (used[i] || 0) < MAXC), P = idx.map(i => pool[i]), cap = {};
    Object.keys(nightCount).forEach(id => { const room = Math.max(0, nightLim - nightCount[id]); if (room < c.n) cap[id] = 100 * (room + 1e-6) / c.n; });
    const cx = Object.assign(ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0)), { state: { lock: {}, excl: {}, cap, floor: {} } });
    const sim = S.simulate(cx, P, fieldL, N.z, c, c.n, SIMS);
    const o = { n: c.n, maxExpo: Math.max(pk.maxExpo / 100, 1 / c.n), minUnique: Math.max(1, pk.minUnique || 1), conds: [], maxCore: pk.maxCore ? pk.maxCore / 100 : null, objective: flagship(c) ? "cover" : "roi" };
    picks[c.id] = S.pick(cx, o, P, sim, c, c.n).chosen.map(k => idx[k]);
    picks[c.id].forEach(i => { used[i] = (used[i] || 0) + 1; pool[i].ids.forEach(id => { nightCount[id] = (nightCount[id] || 0) + 1; }); });
  }
  return { kept: res.keep, picks };
}
(async () => {
  const out = { date: N.date, g: N.g, greens: greens.length, green_n: grule ? grule[0].n : 0, contests: cs.map(c => ({ id: String(c.id), name: c.name, size: c.size, fee: c.entry_fee, n: c.n, payouts: c.payouts })), recipes: {} };
  for (const [name, spec] of Object.entries(RECIPES)) {
    if (!spec || (ONLY && !ONLY.split(",").includes(name))) continue;
    const t0 = Date.now(), seen = {}, bank = [], tags = [];
    for (const [label, o, k] of spec) { const L = await batch(name + "|" + label, o, Math.round(k), seen); L.forEach(x => { bank.push(x); tags.push(label); }); }
    const r = { bank, tags };
    if (B && cs.length && !/600$/.test(name)) Object.assign(r, await cutFill(bank, tags));
    r.seconds = Math.round((Date.now() - t0) / 1000);
    out.recipes[name] = r;
    console.error(N.date, N.g, name, bank.length, "drawn", r.kept ? r.kept.length + " kept" : "", r.seconds + "s");
  }
  fs.writeFileSync(outf, JSON.stringify(out));
})();
