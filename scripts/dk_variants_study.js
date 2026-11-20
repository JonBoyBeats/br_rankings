// Variants of the top: backtest (2026-11-19). On a saved build: variants around the top N kept lineups (cut rank
// order), M each keeping K of the parent's 8 players, the rest redrawn under the parent's idea's rules (the build's
// tag_settings), the bank noise (0.35) and tonight's pool rules (deep bench and punts out, rebuilt from the slate rows);
// near-duplicates (7+ shared with a kept lineup, or another variant) dropped. Kept and variants re-simmed together on
// the page's nights (each contest's seed), each alone in every contest the build entered, weighted by its entries:
// a variant is appended when its value reaches the kept pool's median. Reported: (a) the best variant against its
// parent, (b) tier A (DKSim.tiers) before and after, (c) real top-10% / cash rates of the appended variants and of the
// kept pool in the night's main contest, as color.
//
//   node scripts/dk_variants_study.js <night.json> <build.json> <standings dir> <slate csv> [--n 15] [--m 25] [--k 5,6] [--sims 2000] [--winner IDX] [--rounds 2]
// --rounds 2 (2026-11-20): a second round on the first K, around the top N of the kept pool with round one's appended
// variants in it (a variant's idea is its first parent's), appended the same way; tier A after each round, and the
// second round's appended variants' real rates beside the first's.
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [nf, bf, sdir, actf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
const TOP = +opt("n", 15), M = +opt("m", 25), KS = String(opt("k", "5,6")).split(",").map(Number), SIMS = +opt("sims", 2000), WIN = opt("winner", null), ROUNDS = +opt("rounds", 1);
const SYSTEMATIC = process.argv.includes("--systematic");   // C3: cycle through every K-of-8 keep-set (shuffled once) instead of a random one each draw
const combos = (n, k) => { const out = []; const go = (s, a) => { if (a.length === k) { out.push(a.slice()); return; } for (let i = s; i < n; i++) { a.push(i); go(i + 1, a); a.pop(); } }; go(0, []); return out; };
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const games = {}, outTeam = {};
rows.forEach(r => { games[r.team] = Math.max(games[r.team] || 0, r.gp || 0); if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => {
  const deep = (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < games[r.team] / 2);
  const punt = (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg);
  r.deepOut = r.status !== "Out" && (deep || punt);
});
const seed = B.nights_seed || 1405393094;
const ctxOf = (rand, st) => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, solver: sb.self.solver, random: rand,
                               state: st || { lock: {}, excl: {}, cap: {}, floor: {} } });
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }));
const kept = B.final.map(i => ({ ids: B.pool[i].map(String), bi: i }));
const tagOf = i => { const t = B.tags[i]; return Array.isArray(t) ? t.join(" + ") : t; };

function value(pool, fresh) {       // each lineup alone in every entered contest, entries-weighted (the idea scoreboard's value)
  const K = pool.length, v = new Float64Array(K), odd = new Float64Array(K), even = new Float64Array(K); let w = 0;
  for (const c of cs) {                // fresh: another set of nights, for the out-of-sample check
    const sd = ((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0) + (fresh ? 99991 : 0);
    const sim = S.simulate(ctxOf(S.seeded(sd >>> 0)), pool, N.field.field, N.z, c, c.n, SIMS), st = S.aloneStats(sim, c);
    for (let k = 0; k < K; k++) { v[k] += c.n * (st.odd[k] + st.even[k]) / 2; odd[k] += c.n * st.odd[k]; even[k] += c.n * st.even[k]; }
    w += c.n;
  }
  return { v: Array.from(v, x => x / w), odd: Array.from(odd, x => x / w), even: Array.from(even, x => x / w) };
}
const tierA = val => S.tiers(val.v, val.odd, val.even).tier.filter(t => t === "A").length;
const shared = (a, b) => a.filter(id => b.includes(id)).length;

// real points and the main contest's lines (the night's contest in night.json)
const head = fs.readFileSync(actf, "utf8").split("\n")[0].split(","), iId = head.indexOf("dk_id"), iAct = head.indexOf("actual_dk"), act = {};
fs.readFileSync(actf, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iAct] || 0; });
const pts = fs.readFileSync(path.join(sdir, `contest-standings-${N.cid}.csv`), "utf8").split("\n").slice(1).map(l => l.split(",")).filter(v => v[1] && v[4] !== undefined && v[4] !== "").map(v => +v[4]).sort((a, b) => b - a);
const t10 = pts[Math.ceil(0.1 * pts.length) - 1], cashLine = pts[Math.min(S.payTable(N.contest).length - 1, pts.length) - 1];
const realOf = L => L.ids.reduce((t, id) => t + (act[id] || 0), 0);
const rates = L => L.length ? { top10: +(100 * L.filter(x => realOf(x) >= t10).length / L.length).toFixed(1), cash: +(100 * L.filter(x => realOf(x) >= cashLine).length / L.length).toFixed(1) } : null;

(async () => {
  const base = value(kept.map(x => ({ ids: x.ids }))), sortedBase = base.v.slice().sort((a, b) => a - b);
  const out = { night: N.date, kept: kept.length, contests: cs.map(c => c.name + " x" + c.n), tierA_before: tierA(base), kept_real: rates(kept), runs: {} };
  for (const K of KS) {
    const vars = [], parentOf = [];
    for (let p = 0; p < Math.min(TOP, kept.length); p++) {
      const o0 = B.tag_settings[tagOf(kept[p].bi)] || {};
      const st = { lock: Object.fromEntries((o0.lock || []).map(x => [x, 1])), excl: Object.fromEntries((o0.excl || []).map(x => [x, 1])), cap: {}, floor: {} };
      const cx = ctxOf(S.seeded(seed + 1000 * K + p), st);
      const o = Object.assign({ n: 1, maxExpo: 1, minUnique: 1, maxTeam: 8, conds: [] }, o0, { z: N.z, nightS: 0.35 });
      if (SYSTEMATIC) { const r0 = S.seeded(seed + 31 * p), cb = combos(8, K); for (let i = cb.length - 1; i > 0; i--) { const j = (r0() * (i + 1)) | 0; [cb[i], cb[j]] = [cb[j], cb[i]]; } o.keepSets = cb; }
      for (const L of await S.variants(cx, o, kept[p].ids, K, M)) {
        if (kept.some(x => shared(x.ids, L.ids) >= 7) || vars.some(x => shared(x.ids, L.ids) >= 7)) continue;
        vars.push({ ids: L.ids.map(String) }); parentOf.push(p);
      }
    }
    const all = value(kept.map(x => ({ ids: x.ids })).concat(vars)), kv = all.v.slice(0, kept.length), vv = all.v.slice(kept.length);
    const med = kv.slice().sort((a, b) => a - b)[Math.floor(kept.length / 2)];
    const app = vars.filter((_, i) => vv[i] >= med);
    const after = { v: kv.concat(vv.filter(x => x >= med)), odd: all.odd.slice(0, kept.length).concat(all.odd.slice(kept.length).filter((_, i) => vv[i] >= med)),
                    even: all.even.slice(0, kept.length).concat(all.even.slice(kept.length).filter((_, i) => vv[i] >= med)) };
    let better = 0, gap = 0, parents = 0, better2 = 0, gap2 = 0;
    const bestOf = [], top = Math.min(TOP, kept.length);
    for (let p = 0; p < top; p++) {
      const mine = vv.map((x, i) => [x, i]).filter(([, i]) => parentOf[i] === p); if (!mine.length) continue;
      parents++; const [best, bi] = mine.reduce((a, b) => (b[0] > a[0] ? b : a)); gap += best - kv[p]; if (best > kv[p]) better++;
      bestOf.push([p, bi]);
    }
    // out of sample: each parent and the variant chosen as its best, on fresh nights
    const fresh = value(bestOf.map(([p]) => ({ ids: kept[p].ids })).concat(bestOf.map(([, i]) => vars[i])), true), q = bestOf.length;
    for (let j = 0; j < q; j++) { const d = fresh.v[q + j] - fresh.v[j]; gap2 += d; if (d > 0) better2++; }
    const r = { drawn: vars.length, appended: app.length, parents_with_variants: parents, parents_beaten: better, mean_best_minus_parent: +(gap / Math.max(1, parents)).toFixed(3),
                fresh_parents_beaten: better2, fresh_mean_best_minus_parent: +(gap2 / Math.max(1, q)).toFixed(3),
                tierA_after: tierA(after), appended_real: rates(app), variants_real: rates(vars), median_value: +med.toFixed(3), parent_value_mean: +(kv.slice(0, TOP).reduce((a, b) => a + b, 0) / TOP).toFixed(3) };
    if (WIN != null) {                // color: cousins of a given pool lineup (11-18's 283.5 winner) among the variants
      const w = B.pool[+WIN].map(String);
      r.winner_cousins = { "7of8": vars.filter(x => shared(x.ids, w) >= 7).length, "6of8": vars.filter(x => shared(x.ids, w) === 6).length,
                           kept_rank: B.final.indexOf(+WIN) + 1, best_cousin_real: Math.max(0, ...vars.filter(x => shared(x.ids, w) >= 6).map(realOf)) };
    }
    if (ROUNDS >= 2 && K === KS[0]) {       // round two around the new top (kept + round one's appended)
      const pool1 = kept.map(x => ({ ids: x.ids, bi: x.bi })).concat(vars.map((x, i) => ({ ids: x.ids, bi: kept[parentOf[i]].bi })).filter((_, i) => vv[i] >= med));
      const v1 = value(pool1.map(x => ({ ids: x.ids }))), order = v1.v.map((x, i) => [x, i]).sort((a, b) => b[0] - a[0]).map(([, i]) => i);
      const vars2 = [];
      for (let q = 0; q < Math.min(TOP, order.length); q++) {
        const par = pool1[order[q]], o0 = B.tag_settings[tagOf(par.bi)] || {};
        const st = { lock: Object.fromEntries((o0.lock || []).map(x => [x, 1])), excl: Object.fromEntries((o0.excl || []).map(x => [x, 1])), cap: {}, floor: {} };
        const cx = ctxOf(S.seeded(seed + 50000 + 1000 * K + q), st);
        const o = Object.assign({ n: 1, maxExpo: 1, minUnique: 1, maxTeam: 8, conds: [] }, o0, { z: N.z, nightS: 0.35 });
        for (const L of await S.variants(cx, o, par.ids, K, M)) {
          if (pool1.some(x => shared(x.ids, L.ids) >= 7) || vars2.some(x => shared(x.ids, L.ids) >= 7)) continue;
          vars2.push({ ids: L.ids.map(String) });
        }
      }
      const all2 = value(pool1.map(x => ({ ids: x.ids })).concat(vars2)), k1 = pool1.length, kv2 = all2.v.slice(0, k1), vv2 = all2.v.slice(k1);
      const med2 = kv2.slice().sort((a, b) => a - b)[Math.floor(k1 / 2)], keep2 = vv2.map((x, i) => i).filter(i => vv2[i] >= med2);
      const after2 = { v: kv2.concat(keep2.map(i => vv2[i])), odd: all2.odd.slice(0, k1).concat(keep2.map(i => all2.odd[k1 + i])), even: all2.even.slice(0, k1).concat(keep2.map(i => all2.even[k1 + i])) };
      const top2 = after2.v.slice().sort((a, b) => b - a).slice(0, TOP), top1 = v1.v.slice().sort((a, b) => b - a).slice(0, TOP);
      r.round2 = { pool_after_round1: k1, tierA_after_round1: tierA(v1), drawn: vars2.length, appended: keep2.length, tierA_after_round2: tierA(after2),
                   top_mean_after_round1: +(top1.reduce((a, b) => a + b, 0) / top1.length).toFixed(3), top_mean_after_round2: +(top2.reduce((a, b) => a + b, 0) / top2.length).toFixed(3),
                   appended_real: rates(keep2.map(i => vars2[i])) };
    }
    out.runs["K=" + K] = r;
  }
  console.log(JSON.stringify(out, null, 1));
})();
