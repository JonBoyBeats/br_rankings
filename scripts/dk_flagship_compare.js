// Flagship comparison (2026-11-24, contest profiles; in-sim only): on a saved build's final pool, the flagship contest
// (the $15 Pull Up Jumper) filled as the page's Fill did before the profiles (Max ROI: added expected payout, Min unique
// 3) against the flagship profile's win objective (the added nights one of the set places 1st, weighted by the share of
// 1st's prize; added value breaking ties; Min unique off), both under contest exposure 60% and Max core 15%, on the
// contest's seeded nights (as scripts/dk_caps_backtest.js seeds them), a short set relaxed as the page's Fill relaxes it.
// Also the set actually entered. Each set scored in-sample (the nights it was picked on) and out-of-sample (a second,
// independent draw of nights). Each set's P(1st)
// (nights one of it places 1st) and expected payout, at the entered count and at 2, 3 and 4 lineups. No real results:
// P(1st) at these rates can't be checked on a dozen graded nights.
//
//   node scripts/dk_flagship_compare.js <night.json> <build.json> [--sims 3000]
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const SIMS = opt("sims", 3000);      // "cover" too: the top-1% coverage objective, a smoother proxy for the win
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf));
const gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const seed = B.nights_seed || 1405393094;
const ctxOf = r => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, random: r });
const out = [];
Object.keys(B.portfolios || {}).forEach(cid => {
  const c = N.slate.contests.find(x => String(x.id) === cid);
  if (!c || !c.payouts || !/pull up jumper/i.test(c.name || "")) return;
  const entered = B.portfolios[cid], keep = B.final || B.pool.map((_, i) => i);
  const idx = keep.concat(entered.filter(bi => keep.indexOf(bi) < 0)), pool = idx.map(i => ({ ids: B.pool[i].map(String) }));
  const n = entered.length, fee = c.entry_fee || 0;
  const sim = S.simulate(ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0)), pool, N.field.field, N.z, c, Math.max(n, 4), SIMS);
  // the sets are picked on the contest's seeded nights and scored on those (in-sample, what the page shows) and on a
  // second, independent draw of nights (out-of-sample: a greedy pick flatters itself on the nights it picked on)
  const simOut = S.simulate(ctxOf(S.seeded((seed ^ Math.imul(+c.id || 0, 2654435761) ^ 0x5eed0b5) >>> 0)), pool, N.field.field, N.z, c, Math.max(n, 4), SIMS);
  const cx = ctxOf(S.seeded(1));
  const one = (sm, ks) => { const b = S.builder(sm, c); b.set(ks); return { p1: b.coverage().first, ev: b.total() }; };
  const stats = ks => { const i = one(sim, ks), o = one(simOut, ks); return { p1: i.p1, ev: i.ev, p1_out: o.p1, ev_out: o.ev, n: ks.length }; };
  const base = { maxExpo: 0.6, minUnique: 3, conds: [], maxCore: 0.15 };
  // the page's Fill: a short set relaxes one cap a step at a time (Max core 20, 25%, then Max exposure 70%), topping up by
  // coverage (the win objective for the flagship)
  const run = (obj, m) => {
    const o = Object.assign({ n: m }, base, obj === "win" ? { minUnique: 1 } : {}, { maxExpo: Math.max(0.6, 1 / m), objective: obj });
    let ch = S.pick(cx, o, pool, sim, c, m).chosen;
    [{ maxCore: 0.2 }, { maxCore: 0.25 }, { maxCore: 0.25, maxExpo: 0.7 }].forEach(x => {
      if (ch.length < m) ch = S.pick(cx, Object.assign({}, o, x, { objective: obj === "win" ? "win" : "cover", preset: ch }), pool, sim, c, m).chosen;
    });
    return ch;
  };
  const row = { day: B.day, draft_group: B.draft_group, contest: c.name, contest_id: cid, size: c.size, fee, n, sims: SIMS, pool: pool.length };
  row.entered = stats(entered.map(bi => idx.indexOf(bi)));
  ["roi", "win", "cover"].forEach(obj => {
    row[obj] = stats(run(obj, n));
    row[obj + "_at"] = [2, 3, 4].map(m => stats(run(obj, m)));
  });
  out.push(row);
});
out.forEach(r => console.log(JSON.stringify(r)));
