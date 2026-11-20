// Max ROI vs Balanced fills (2026-11-20, for the operator; nothing adopted): a saved build's final pool filled both ways
// as the DK page's Fill all contests does (the largest stake first; DKSim.pick on each contest's seeded nights at the
// build's settings, a lineup in at most MAX contests, the night cap: no player in more than NIGHT% of the night's
// entries, locks capped like the rest), then both judged on the same fresh nights for every contest (one seed, so a
// player has the same night in each contest): expected net dollars, its spread (sd, 5th / 95th percentile), the share of
// nights where one of the night's entries reaches a contest's top 1%; and on real points where the standings exist.
//
//   node scripts/dk_fill_study.js <night.json> <build.json> <standings dir> <slate csv> [--max 3] [--night 60] [--sims 2000]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const MAX = opt("max", 3), NIGHT = opt("night", 60), SIMS = opt("sims", 2000);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = (r, cap) => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: cap || {}, floor: {} }, random: r });
const pool = (B.final || B.pool.map((_, i) => i)).map(i => ({ ids: B.pool[i].map(String) }));
const pk = Object.assign({ maxExpo: 40, minUnique: 3, maxCore: 15 }, B.pick || {});
const supF = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json");
const sup = fs.existsSync(supF) ? JSON.parse(fs.readFileSync(supF)).contests || {} : {};
Object.keys(B.portfolios || {}).forEach(id => {
  if (sup[id] && !N.slate.contests.some(c => String(c.id) === id && c.payouts)) N.slate.contests = N.slate.contests.filter(c => String(c.id) !== id).concat([sup[id]]);
});
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }))
  .sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n || (b.entry_fee || 0) - (a.entry_fee || 0));
const total = cs.reduce((a, c) => a + c.n, 0), nightLim = Math.max(1, Math.floor(NIGHT / 100 * total + 1e-9));

function fill(objective) {
  const used = {}, out = {}, nightCount = {};
  for (const c of cs) {
    const idx = pool.map((_, i) => i).filter(i => (used[i] || 0) < MAX), P = idx.map(i => pool[i]);
    const cap = {};                                       // the night cap as each player's Max% in this contest
    Object.keys(nightCount).forEach(id => { const room = Math.max(0, nightLim - nightCount[id]); if (room < c.n) cap[id] = 100 * (room + 1e-6) / c.n; });
    const cx = ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0), cap);
    const sim = S.simulate(cx, P, N.field.field, N.z, c, c.n, SIMS);
    const o = { n: c.n, maxExpo: Math.max(pk.maxExpo / 100, 1 / c.n), minUnique: Math.max(1, pk.minUnique), conds: [], maxCore: pk.maxCore ? pk.maxCore / 100 : null, objective };
    out[c.id] = S.pick(cx, o, P, sim, c, c.n).chosen.map(k => idx[k]);
    out[c.id].forEach(i => { used[i] = (used[i] || 0) + 1; pool[i].ids.forEach(id => { nightCount[id] = (nightCount[id] || 0) + 1; }); });
  }
  return out;
}

// each night's dollars back for a contest's set, and whether one of them reached the top 1%
function nightly(sim, c, K) {
  const pay = S.payTable(c), paid = pay.length - 1, tie = sim.tieSplit && sim.tie ? sim.tie : new Float32Array(K), out = new Float64Array(sim.S), top = new Uint8Array(sim.S);
  const T1 = Math.max(1, Math.ceil(0.01 * (c.size || 0)));
  const at = (pl, t) => { if (t >= 0.5) return S.placePay(pay, pl, t); const q = Math.round(pl); return q >= 1 && q <= paid ? pay[q] : 0; };
  for (let s = 0; s < sim.S; s++) for (let i = 0; i < K; i++) {
    let mine = 0;
    for (let j = 0; j < K; j++) if (sim.cs[j * sim.S + s] > sim.cs[i * sim.S + s]) mine++;
    const pl = 1 + sim.fa[i * sim.S + s] + mine;
    out[s] += at(pl, tie[i]);
    if (Math.round(pl) <= T1) top[s] = 1;
  }
  return { d: out, top };
}

const act = {}, graded = actf && fs.existsSync(actf);      // a night not graded yet: no real points, no real dollars
if (graded) {
  const head = fs.readFileSync(actf, "utf8").split("\n")[0].split(","), iId = head.indexOf("dk_id"), iAct = head.indexOf("actual_dk");
  fs.readFileSync(actf, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iAct] || 0; });
}
function real(c, sets) {          // real dollars: placed among the contest's real entries (the owner's own left out), ties split
  const f = path.join(sdir, `contest-standings-${c.id}.csv`);
  if (!graded || !fs.existsSync(f)) return null;
  const pts = [];
  fs.readFileSync(f, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[1] && v[4] !== undefined && v[4] !== "" && !/^jonboyjackson/i.test(v[2] || "")) pts.push(+v[4]); });
  const pay = S.payTable(c), ours = sets.map(L => L.reduce((t, id) => t + (act[id] || 0), 0));
  let tot = 0;
  ours.forEach(x => {
    const above = pts.filter(p => p > x).length + ours.filter(y => y > x).length, tied = pts.filter(p => p === x).length + ours.filter(y => y === x).length - 1;
    let w = 0; for (let k = above + 1; k <= above + 1 + tied; k++) w += pay[k] || 0;
    tot += w / (tied + 1);
  });
  return tot;
}

const res = {};
for (const [name, F] of [["Max ROI", fill("roi")], ["Balanced", fill("balanced")]]) {
  const tot = new Float64Array(SIMS), any1 = new Uint8Array(SIMS), use = {};
  let fees = 0, realD = 0, realOk = true;
  for (const c of cs) {
    const L = F[c.id].map(i => pool[i]);
    F[c.id].forEach(i => { use[i] = 1; });
    const sim = S.simulate(ctxOf(S.seeded(seed + 7777)), L, N.field.field, N.z, c, L.length, SIMS), r = nightly(sim, c, L.length);
    for (let s = 0; s < SIMS; s++) { tot[s] += r.d[s]; if (r.top[s]) any1[s] = 1; }
    fees += (c.entry_fee || 0) * L.length;
    const rd = real(c, L.map(x => x.ids));
    if (rd == null) realOk = false; else realD += rd;
  }
  const net = Array.from(tot, x => x - fees).sort((a, b) => a - b), mean = net.reduce((a, b) => a + b, 0) / SIMS;
  res[name] = { entries: Object.values(F).reduce((a, v) => a + v.length, 0), distinct: Object.keys(use).length, fees: +fees.toFixed(2),
                expected_net: +mean.toFixed(2), sd: +Math.sqrt(net.reduce((a, b) => a + (b - mean) ** 2, 0) / SIMS).toFixed(2),
                p5: +net[Math.floor(0.05 * SIMS)].toFixed(2), p95: +net[Math.floor(0.95 * SIMS)].toFixed(2),
                top1_nights: +(100 * any1.reduce((a, b) => a + b, 0) / SIMS).toFixed(1), real_net: realOk ? +(realD - fees).toFixed(2) : null };
}
console.log(JSON.stringify({ night: N.date, contests: cs.map(c => c.name + " x" + c.n + " $" + c.entry_fee), night_limit: nightLim, res }, null, 1));
