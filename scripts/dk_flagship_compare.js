// Flagships together or apart (2026-11-24, contest profiles; in-sim only). On a saved build's final pool (and the
// lineups it entered), the night's flagship contests (the Pull Up Jumper, and by size 100-800 the High Five; the page's
// profileAuto) filled two ways under contest exposure 60%, Max core 15%, Min unique off, a lineup in up to 3 contests:
//   separate  each flagship by its own Max coverage (DKSim.pick "cover": the added nights one of its set reaches its
//             top 1%, added value breaking ties), the largest stake first, as the fill did before 2026-11-24
//   joint     all flagships at once (DKSim.pickJoint): the added nights one of the flagships' lineups reaches the top
//             1% of its own contest, added value breaking ties (the flagship profile)
// a short set relaxed as the page's Fill relaxes it. Every flagship is simulated on the same nights (one seed), and
// each set is scored on those (in-sample) and on a second, independent draw (fresh nights): each contest's top-1%
// coverage and expected payout, and the joint coverage (nights one of all the flagship lineups is in its top 1%).
// (The earlier comparison of a "win" objective against Max ROI and Max coverage, which led to this, is the version of
// this script at commit 577892c.)
//
//   node scripts/dk_flagship_compare.js <night.json> <build.json> [--sims 3000]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const SIMS = opt("sims", 3000), MAXUSE = 3;
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = r => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, random: r });
const supF = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json");
const sup = fs.existsSync(supF) ? JSON.parse(fs.readFileSync(supF)).contests || {} : {};
const flagship = c => /pull up jumper/i.test(c.name || "") || (!/dime time|and-one|quarter jukebox|qualifier|satellite/i.test(c.name || "") && (c.size || 0) >= 100 && (c.size || 0) < 800);
const fc = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(x => String(x.id) === id && x.payouts) || sup[id]).filter(c => c && c.payouts && flagship(c))
  .map(c => Object.assign({}, c, { n: B.portfolios[String(c.id)].length })).filter(c => c.n > 0)
  .sort((a, b) => (b.entry_fee || 0) * b.n - (a.entry_fee || 0) * a.n);
if (!fc.length) process.exit(0);
const keep = B.final || B.pool.map((_, i) => i), ent = [].concat(...fc.map(c => B.portfolios[String(c.id)]));
const idx = keep.concat(ent.filter((bi, i) => keep.indexOf(bi) < 0 && ent.indexOf(bi) === i)), pool = idx.map(i => ({ ids: B.pool[i].map(String) }));
const seedJ = (seed ^ Math.imul(+fc[0].id || 0, 2654435761)) >>> 0, seedF = (seedJ ^ 0x5eed0b5) >>> 0;
const simsIn = fc.map(c => S.simulate(ctxOf(S.seeded(seedJ)), pool, N.field.field, N.z, c, c.n, SIMS));
const simsOut = fc.map(c => S.simulate(ctxOf(S.seeded(seedF)), pool, N.field.field, N.z, c, c.n, SIMS));
const cx = ctxOf(S.seeded(1)), base = n => ({ n, maxExpo: Math.max(0.6, 1 / n), minUnique: 1, conds: [], maxCore: 0.15 });
const relax = (sim, c, ch) => {        // the page's relax steps for a short set, by top-1% coverage
  [{ maxCore: 0.2 }, { maxCore: 0.25 }, { maxCore: 0.25, maxExpo: 0.7 }].forEach(x => {
    if (ch.length < c.n) ch = S.pick(cx, Object.assign(base(c.n), x, { objective: "cover", preset: ch }), pool, sim, c, c.n).chosen;
  });
  return ch;
};
// separate: each by its own coverage, the largest stake first (a night's two or three flagships keep every lineup
// within MAXUSE contests)
const sep = fc.map((c, ci) => relax(simsIn[ci], c, S.pick(cx, Object.assign(base(c.n), { objective: "cover" }), pool, simsIn[ci], c, c.n).chosen));
// joint
const rj = S.pickJoint(cx, Object.assign(base(Math.max(...fc.map(c => c.n))), { uses: {}, maxUse: MAXUSE }), pool, simsIn, fc, fc.map(c => c.n));
const joint = rj.into.map((ch, ci) => relax(simsIn[ci], fc[ci], ch.slice()));
const score = (sims, sets) => {
  const per = sets.map((ks, ci) => { const b = S.builder(sims[ci], fc[ci]); b.set(ks); return { top1: b.coverage().top1, ev: b.total(), n: ks.length, mask: b.cover1() }; });
  const M = sims[0].S; let j = 0;
  for (let a = 0; a < M; a++) if (per.some(p => p.mask[a])) j++;
  return { joint: j / M, ev: per.reduce((t, p) => t + p.ev, 0), contests: per.map(p => ({ top1: p.top1, ev: p.ev, n: p.n })) };
};
const out = { day: B.day, draft_group: B.draft_group, contests: fc.map(c => ({ id: String(c.id), name: c.name, size: c.size, fee: c.entry_fee, n: c.n })), sims: SIMS, pool: pool.length,
  separate: { in: score(simsIn, sep), out: score(simsOut, sep) }, joint: { in: score(simsIn, joint), out: score(simsOut, joint) },
  entered: { out: score(simsOut, fc.map(c => B.portfolios[String(c.id)].map(bi => idx.indexOf(bi)))) } };
console.log(JSON.stringify(out));
