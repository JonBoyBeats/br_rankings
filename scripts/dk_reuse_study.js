// Cross-contest reuse test (2026-11-19, for the owner's decision; nothing adopted): a saved build's final pool filled
// two ways, as the DK page's Fill all contests does (the largest stake first, DKSim.pick at the build's settings on
// each contest's seeded nights): (A) each lineup in one contest only, today's rule; (B) each contest from the whole
// final pool, unique within a contest, a lineup in at most MAX contests. Both are then judged on the same fresh nights
// for every contest (one seed, so a player has the same night in each contest), and on real points.
//
//   node scripts/dk_reuse_study.js <night.json> <build.json> <standings dir> <slate csv> [--max 3] [--sims 2000]
//   (night.json: scripts/dk_bank_noise_study.py extract's lock-time slate and field; slate csv: analysis/cbb/dk/<date>_<g>.csv)
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const MAX = opt("max", 3), SIMS = opt("sims", 2000);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = r => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, random: r });
const pool = (B.final || B.pool.map((_, i) => i)).map(i => ({ ids: B.pool[i].map(String) }));
const pk = Object.assign({ maxExpo: 40, minUnique: 3, maxCore: 15 }, B.pick || {});
const missing = Object.keys(B.portfolios || {}).filter(id => !N.slate.contests.some(c => String(c.id) === id && c.payouts));
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }))
  .sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n || (b.entry_fee || 0) - (a.entry_fee || 0));

function fill(reuse) {
  const used = {}, out = {};
  for (const c of cs) {
    const idx = pool.map((_, i) => i).filter(i => reuse ? (used[i] || 0) < MAX : !used[i]), P = idx.map(i => pool[i]);
    const cx = ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0));
    const sim = S.simulate(cx, P, N.field.field, N.z, c, c.n, SIMS);
    const o = { n: c.n, maxExpo: Math.max(pk.maxExpo / 100, 1 / c.n), minUnique: Math.max(1, pk.minUnique), conds: [],
                maxCore: pk.maxCore ? pk.maxCore / 100 : null, objective: "roi" };
    out[c.id] = S.pick(cx, o, P, sim, c, c.n).chosen.map(k => idx[k]);
    out[c.id].forEach(i => { used[i] = (used[i] || 0) + 1; });
  }
  return out;
}

// each night's dollars back for a contest's set on the given sim (the builder's places: field above + ours above)
function nightly(sim, c, K) {
  const pay = S.payTable(c), paid = pay.length - 1, tie = sim.tieSplit && sim.tie ? sim.tie : new Float32Array(K), out = new Float64Array(sim.S);
  const at = (pl, t) => { if (t >= 0.5) return S.placePay(pay, pl, t); const q = Math.round(pl); return q >= 1 && q <= paid ? pay[q] : 0; };
  for (let s = 0; s < sim.S; s++) for (let i = 0; i < K; i++) {
    let mine = 0;
    for (let j = 0; j < K; j++) if (sim.cs[j * sim.S + s] > sim.cs[i * sim.S + s]) mine++;
    out[s] += at(1 + sim.fa[i * sim.S + s] + mine, tie[i]);
  }
  return out;
}

// real points: the slate csv's actual_dk by dk_id
const head = fs.readFileSync(actf, "utf8").split("\n")[0].split(","), iId = head.indexOf("dk_id"), iAct = head.indexOf("actual_dk");
const act = {};
fs.readFileSync(actf, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iAct] || 0; });
// real dollars: placed among the contest's real entries (the owner's own left out), ties split
function real(c, sets) {
  const f = path.join(sdir, `contest-standings-${c.id}.csv`);
  if (!fs.existsSync(f)) return null;
  const pts = [];
  fs.readFileSync(f, "utf8").split("\n").slice(1).forEach(l => {
    const v = l.split(",");
    if (v[1] && v[4] !== undefined && v[4] !== "" && !/^jonboyjackson/i.test(v[2] || "")) pts.push(+v[4]);
  });
  const pay = S.payTable(c), ours = sets.map(L => L.reduce((t, id) => t + (act[id] || 0), 0));
  let tot = 0;
  ours.forEach(x => {
    const above = pts.filter(p => p > x).length + ours.filter(y => y > x).length;
    const tied = pts.filter(p => p === x).length + ours.filter(y => y === x).length - 1;
    let w = 0;
    for (let k = above + 1; k <= above + 1 + tied; k++) w += pay[k] || 0;
    tot += w / (tied + 1);
  });
  return tot;
}

const res = {};
for (const [name, F] of [["one contest only", fill(false)], ["reuse, max " + MAX, fill(true)]]) {
  const tot = new Float64Array(SIMS), use = {};
  let fees = 0, realD = 0, realOk = true, maxUse = 0;
  for (const c of cs) {
    const L = F[c.id].map(i => pool[i]);
    F[c.id].forEach(i => { use[i] = (use[i] || 0) + 1; maxUse = Math.max(maxUse, use[i]); });
    const sim = S.simulate(ctxOf(S.seeded(seed + 7777)), L, N.field.field, N.z, c, L.length, SIMS), d = nightly(sim, c, L.length);
    for (let s = 0; s < SIMS; s++) tot[s] += d[s];
    fees += (c.entry_fee || 0) * L.length;
    const r = real(c, L.map(x => x.ids));
    if (r == null) realOk = false; else realD += r;
  }
  const net = Array.from(tot, x => x - fees).sort((a, b) => a - b), mean = net.reduce((a, b) => a + b, 0) / SIMS;
  const sd = Math.sqrt(net.reduce((a, b) => a + (b - mean) * (b - mean), 0) / SIMS);
  res[name] = { entries: Object.values(F).reduce((a, v) => a + v.length, 0), distinct: Object.keys(use).length, max_use: maxUse,
                fees: +fees.toFixed(2), expected_net: +mean.toFixed(2), sd: +sd.toFixed(2), p5: +net[Math.floor(0.05 * SIMS)].toFixed(2),
                p95: +net[Math.floor(0.95 * SIMS)].toFixed(2), real_net: realOk ? +(realD - fees).toFixed(2) : null };
}
console.log(JSON.stringify({ night: N.date, contests: cs.map(c => c.name + " x" + c.n + " $" + c.entry_fee), missing, res }, null, 1));
