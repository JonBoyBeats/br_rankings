/* DraftKings college basketball: the optimizer, the contest sim and the portfolio pick, shared by the DK page
 * (dk.html) and the nightly shadow portfolios (scripts/dk_shadow.js), so the lineups graded are the lineups the page
 * builds. No page code here: the caller passes a context:
 *
 *   ctx = { rows: [{id, name, team, game, home, roster, salary, status, fp_dk, dk_avg, miss_dk, ...}],
 *           proj(r): his Proj (the page's override, else the gated projection: gatedProj),
 *           own(r): his projected ownership %, state: {lock, excl, cap}, solver: javascript-lp-solver,
 *           random(): a uniform draw (Math.random on the page, a seeded one for the shadow portfolios),
 *           progress(msg): optional; awaited every few lineups so a page can repaint }
 *
 * RULESETS are the five shadow rule sets, frozen 2026-11-16 for the 30-slate test: no new ones and no changes
 * until that decision. BASE is the settings all five share.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DKSim = factory();
})(this, function () {
  var CAP = 50000, SLOTS = ["G", "G", "G", "F", "F", "F", "UTIL", "UTIL"];
  var MIN_PROJ = 6;   // players projected under this are left out of the optimizer (none is in a top lineup), unless locked
  // Sim & pick's candidates: each differs from every earlier one by CAND_UNIQUE+ players, under CAND_RAND noise (its
  // own, apart from the page's Randomness, which is Build's). On the 2026-11-16 slate (Jukebox, 20 lineups, 2,000
  // nights): differing by 1 at 15% noise filled 16 of 20 lineups (expected back $7.02); by 2 at 20%, all 20 ($7.74);
  // by 1 at 25%, 20 ($7.31); by 3 at 15%, 17 ($7.17). One slate: rechecked on the first graded slates.
  var CAND_UNIQUE = 2, CAND_RAND = 0.20;

  var BASE = { n: 20, maxExpo: 0.6, minUnique: 3, rand: 0.15, minSal: 48500, maxTeam: 5, candidates: 150, sims: 3000 };
  var RULESETS = [
    { key: "none", name: "No extra rules", rules: {} },
    { key: "stack", name: "Game stack: 3+ from one game, both teams", rules: { stackN: 3, stackBoth: true } },
    { key: "owncap", name: "Ownership cap: total own at most the field's 25th percentile lineup", rules: { maxOwnPctile: 25 } },
    { key: "lowown", name: "Low-owned: 2+ players under 10% owned", rules: { lowN: 2, lowPct: 10 } },
    { key: "all", name: "All three together", rules: { stackN: 3, stackBoth: true, maxOwnPctile: 25, lowN: 2, lowPct: 10 } }
  ];

  function isG(r) { return /(^|\/)G(\/|$)/.test(r.roster); }
  function isF(r) { return /(^|\/)F(\/|$)/.test(r.roster); }

  // a seeded uniform draw (mulberry32), for shadow portfolios that rebuild the same way
  function seeded(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(random) { var u = 1 - random(), v = random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }

  // The projection gate (analysis/cbb/dk/gate.json, scripts/cbb_daily.py): where DraftKings' season average has beaten
  // ours over the graded nights in a salary band, Proj there is w x ours + (1 - w) x DraftKings' average.
  function gatedProj(r, gate) {
    var b = gate && (gate.bands || []).find(function (x) { return x.open && r.salary >= x.lo && r.salary <= x.hi; });
    if (!b || !r.dk_avg) return r.fp_dk;
    return b.w * r.fp_dk + (1 - b.w) * r.dk_avg;
  }

  // The field's lineup ownership at a percentile (for the ownership-cap rule set)
  function fieldOwnPctile(field, own, pct) {
    var t = field.map(function (L) { return L.reduce(function (s, id) { return s + (own[id] || 0); }, 0); }).sort(function (a, b) { return a - b; });
    return t.length ? t[Math.min(t.length - 1, Math.floor(pct / 100 * t.length))] : null;
  }

  function usable(ctx, r) { return r.status !== "Out" && !ctx.state.excl[r.id]; }

  // G slots from guards first, F slots from forwards first, G/F players where needed, the rest to UTIL
  function assign(ctx, ids) {
    var by = {}; ctx.rows.forEach(function (r) { by[r.id] = r; });
    var ps = ids.map(function (id) { return by[id]; }).sort(function (a, b) { return b.salary - a.salary; });
    var g = ps.filter(function (r) { return isG(r) && !isF(r); }), f = ps.filter(function (r) { return isF(r) && !isG(r); }), gf = ps.filter(function (r) { return isG(r) && isF(r); });
    var G = g.splice(0, 3), F = f.splice(0, 3);
    while (G.length < 3) G.push(gf.shift());
    while (F.length < 3) F.push(gf.shift());
    return G.concat(F, g, f, gf).slice(0, 8).map(function (r) { return r.id; });
  }

  // Up to o.n lineups under the rules: each the best under that lineup's randomized Proj. o.noCaps: no exposure caps.
  async function solve(ctx, o) {
    var st = ctx.state, proj = ctx.proj, own = ctx.own;
    var pool = ctx.rows.filter(function (r) { return usable(ctx, r) && (proj(r) >= MIN_PROJ || st.lock[r.id]); });
    var locks = pool.filter(function (r) { return st.lock[r.id]; });
    var limit = {};
    pool.forEach(function (r) {
      var cap = o.noCaps ? 1 : Math.min(o.maxExpo, st.cap[r.id] != null && st.cap[r.id] !== "" ? +st.cap[r.id] / 100 : 1);
      limit[r.id] = st.lock[r.id] || o.noCaps ? o.n : Math.floor(cap * o.n + 1e-9);
    });
    var games = Array.from(new Set(pool.map(function (r) { return r.game; })));
    var count = {}, out = [], teams = Array.from(new Set(pool.map(function (r) { return r.team; }))), why = "";
    for (var k = 0; k < o.n; k++) {
      if (k % 5 === 4 && ctx.progress) await ctx.progress((o.label || "Building") + "… " + k + " of " + o.n);
      var cons = { n: { equal: 8 }, g: { min: 3 }, f: { min: 3 }, sal: { max: CAP, min: o.minSal } }, vars = {}, ints = {};
      teams.forEach(function (t) { cons["t_" + t] = { max: o.maxTeam }; });
      out.forEach(function (L, i) { cons["u" + i] = { max: 8 - o.minUnique }; });
      if (o.maxOwn != null) cons.own = { max: o.maxOwn };
      if (o.lowN) cons.low = { min: o.lowN };
      if (o.stackN) {
        // y_game = 1 marks the stacked game: at least stackN from it (and one from each side with stackBoth)
        cons.stack = { min: 1 };
        games.forEach(function (gm, i) {
          var y = { score: 0, stack: 1 };
          y["gs" + i] = -o.stackN; cons["gs" + i] = { min: 0 };
          if (o.stackBoth) { y["ga" + i] = -1; y["gh" + i] = -1; cons["ga" + i] = { min: 0 }; cons["gh" + i] = { min: 0 }; }
          vars["y" + i] = y; ints["y" + i] = 1; cons["yb" + i] = { max: 1 }; y["yb" + i] = 1;
        });
      }
      pool.forEach(function (r) {
        if ((count[r.id] || 0) >= limit[r.id]) return;
        var v = { score: proj(r) * (1 + o.rand * gauss(ctx.random)), n: 1, sal: r.salary };
        v["t_" + r.team] = 1;
        if (isG(r)) v.g = 1;
        if (isF(r)) v.f = 1;
        if (o.maxOwn != null) v.own = own(r);
        if (o.lowN && own(r) < o.lowPct) v.low = 1;
        if (o.stackN) {
          var gi = games.indexOf(r.game);
          v["gs" + gi] = 1;
          if (o.stackBoth) v[(r.home ? "gh" : "ga") + gi] = 1;
        }
        if (st.lock[r.id]) { v["lk_" + r.id] = 1; cons["lk_" + r.id] = { equal: 1 }; }
        else { v["b_" + r.id] = 1; cons["b_" + r.id] = { max: 1 }; }
        out.forEach(function (L, i) { if (L.ids.indexOf(r.id) >= 0) v["u" + i] = 1; });
        vars[r.id] = v; ints[r.id] = 1;
      });
      if (locks.some(function (r) { return !vars[r.id]; })) { why = "a locked player is out of the pool"; break; }
      var res = ctx.solver.Solve({ optimize: "score", opType: "max", constraints: cons, variables: vars, ints: ints });
      if (!res.feasible) { why = "no lineup left fits the rules (loosen Min unique, Max exposure, the stack or ownership rules, Min salary or the locks)"; break; }
      var ids = Object.keys(vars).filter(function (id) { return id.charAt(0) !== "y" && res[id] > 0.5; });
      if (ids.length !== 8) { why = "the solver returned " + ids.length + " players"; break; }
      ids.forEach(function (id) { count[id] = (count[id] || 0) + 1; });
      out.push({ ids: ids, slots: assign(ctx, ids) });
    }
    return { lineups: out, why: why };
  }

  function payTable(c) {     // place -> dollars, from [[first, last, dollars], ...]
    var t = [0];
    (c.payouts || []).forEach(function (p) { for (var i = p[0]; i <= p[1]; i++) t[i] = p[2]; });
    for (var i = 1; i < t.length; i++) t[i] = t[i] || 0;
    return t;
  }

  // S simulated nights: each player's points drawn from his Proj and his ±, in z's shape; the candidates' and the
  // field's lineups scored. Returns each candidate's score and the field entries above it, by night, and the
  // simulated field's cut lines (winning score, top 10%, the last paid place), averaged over the nights.
  function simulate(ctx, cand, field, z, contest, N, S) {
    var by = {}; ctx.rows.forEach(function (r) { by[r.id] = r; });
    var ix = {}, mean = [], err = [];
    function idx(id) {
      if (ix[id] == null) {
        var r = by[id] || {}, m = r.status === "Out" ? 0 : (by[id] ? ctx.proj(r) : 0);
        ix[id] = mean.length; mean.push(m); err.push(r.miss_dk || 0.35 * m);
      }
      return ix[id];
    }
    var candIx = cand.map(function (L) { return L.ids.map(idx); });
    var fieldIx = field.map(function (L) { return L.map(idx); });
    var P = mean.length, size = contest.size || 0, paid = payTable(contest).length - 1;
    var w = Math.max(0, size - N) / fieldIx.length;               // each field lineup stands for w entries
    var pts = new Float32Array(P), cs = [], fa = [], cut = { win: 0, top10: 0, cash: 0 };
    var fsc = new Float64Array(fieldIx.length);
    function scoreAtPlace(place) {                                // the field's score at a place (1 = best)
      var i = fsc.length - Math.min(fsc.length, Math.max(1, Math.ceil(place / w)));
      return fsc[i];
    }
    for (var s = 0; s < S; s++) {
      for (var p = 0; p < P; p++) pts[p] = Math.max(0, mean[p] + z[(ctx.random() * z.length) | 0] * err[p]);
      for (var f = 0; f < fieldIx.length; f++) { var t = 0, L = fieldIx[f]; for (var j = 0; j < 8; j++) t += pts[L[j]]; fsc[f] = t; }
      fsc.sort();                                                  // ascending
      cut.win += scoreAtPlace(1) / S; cut.top10 += scoreAtPlace(Math.ceil(0.1 * size)) / S; cut.cash += scoreAtPlace(paid) / S;
      var row = new Float32Array(cand.length), above = new Float32Array(cand.length);
      for (var k = 0; k < cand.length; k++) {
        var t2 = 0, L2 = candIx[k]; for (var j2 = 0; j2 < 8; j2++) t2 += pts[L2[j2]];
        row[k] = t2;
        var lo = 0, hi = fsc.length;                               // field lineups scoring above t2
        while (lo < hi) { var mid = (lo + hi) >> 1; if (fsc[mid] <= t2) lo = mid + 1; else hi = mid; }
        above[k] = (fsc.length - lo) * w;
      }
      cs.push(row); fa.push(above);
    }
    return { cs: cs, fa: fa, cut: cut };
  }

  // Greedy: add the candidate that adds the most expected payout to what's chosen (ours push each other down too),
  // within the exposure caps and Min unique, over the given nights.
  function pick(ctx, o, cand, sim, contest, N, nights) {
    var st = ctx.state, pay = payTable(contest), paid = pay.length - 1;
    function payAt(place) { var q = Math.round(place); return q >= 1 && q <= paid ? pay[q] : 0; }
    var chosen = [], count = {}, limit = {}, place = nights.map(function () { return []; });
    ctx.rows.forEach(function (r) {
      var cap = Math.min(o.maxExpo, st.cap[r.id] != null && st.cap[r.id] !== "" ? +st.cap[r.id] / 100 : 1);
      limit[r.id] = st.lock[r.id] ? N : Math.floor(cap * N + 1e-9);
    });
    while (chosen.length < N) {
      var best = -1, bestV = -Infinity;
      for (var k = 0; k < cand.length; k++) {
        if (chosen.indexOf(k) >= 0) continue;
        var ids = cand[k].ids;
        if (ids.some(function (id) { return (count[id] || 0) + 1 > limit[id]; })) continue;
        if (chosen.some(function (q) { return cand[q].ids.filter(function (id) { return ids.indexOf(id) >= 0; }).length > 8 - o.minUnique; })) continue;
        var v = 0;
        for (var a = 0; a < nights.length; a++) {
          var s = nights[a], me = sim.cs[s][k], mine = 0, delta = 0;
          for (var i = 0; i < chosen.length; i++) {
            if (sim.cs[s][chosen[i]] > me) mine++;
            else { var pl = place[a][i]; delta += payAt(pl + 1) - payAt(pl); }
          }
          v += payAt(1 + sim.fa[s][k] + mine) + delta;
        }
        if (v > bestV) { bestV = v; best = k; }
      }
      if (best < 0) break;
      for (var b = 0; b < nights.length; b++) {                    // add it: everyone of ours below it moves down a place
        var s2 = nights[b], me2 = sim.cs[s2][best], mine2 = 0;
        for (var i2 = 0; i2 < chosen.length; i2++) {
          if (sim.cs[s2][chosen[i2]] > me2) mine2++; else place[b][i2] += 1;
        }
        place[b].push(1 + sim.fa[s2][best] + mine2);
      }
      chosen.push(best);
      cand[best].ids.forEach(function (id) { count[id] = (count[id] || 0) + 1; });
    }
    return { chosen: chosen, place: place, payAt: payAt, paid: paid };
  }

  // A fixed portfolio's mean payout over the given nights (ours placed among the field and each other)
  function value(sim, contest, chosen, nights) {
    var pay = payTable(contest), paid = pay.length - 1, total = 0;
    function payAt(place) { var q = Math.round(place); return q >= 1 && q <= paid ? pay[q] : 0; }
    nights.forEach(function (s) {
      chosen.forEach(function (k) {
        var mine = 0;
        chosen.forEach(function (j) { if (j !== k && sim.cs[s][j] > sim.cs[s][k]) mine++; });
        total += payAt(1 + sim.fa[s][k] + mine);
      });
    });
    return nights.length ? total / nights.length : 0;
  }

  // Candidates under the rules, the sim, the pick, and its stability: the same pick made on each half of the nights
  // apart, and how many lineups both halves chose.
  async function simPick(ctx, o, contest, field, z, K, S) {
    var N = o.n;
    var pool = await solve(ctx, Object.assign({}, o, { n: Math.max(N, K), minUnique: CAND_UNIQUE, rand: CAND_RAND, noCaps: true,
                                                       label: "Building candidates" }));
    var cand = pool.lineups;
    if (cand.length < N) return { error: "only " + cand.length + " candidates fit the rules" + (pool.why ? " (" + pool.why + ")" : "") };
    if (ctx.progress) await ctx.progress("Simulating " + S + " nights…");
    var sim = simulate(ctx, cand, field, z, contest, N, S);
    var all = [], h1 = [], h2 = [];
    for (var s = 0; s < S; s++) { all.push(s); (s < S / 2 ? h1 : h2).push(s); }
    if (ctx.progress) await ctx.progress("Picking " + N + " lineups, and checking the pick on each half of the nights…");
    var full = pick(ctx, o, cand, sim, contest, N, all);
    // stability: the pick made on each half of the nights, scored on the other half against the pick made there.
    // Many candidates are worth nearly the same, so which ones get picked moves with the draw; what matters is
    // whether a pick made on one set of nights keeps its value on another.
    var a = pick(ctx, o, cand, sim, contest, N, h1).chosen, b = pick(ctx, o, cand, sim, contest, N, h2).chosen;
    var both = a.filter(function (k) { return b.indexOf(k) >= 0; }).length;
    var kept = (value(sim, contest, a, h2) / (value(sim, contest, b, h2) || 1) + value(sim, contest, b, h1) / (value(sim, contest, a, h1) || 1)) / 2;
    var total = 0, anyFirst = 0, size = contest.size || 0;
    var lineups = full.chosen.map(function (k, i) {
      var e = 0, cash = 0, top10 = 0, first = 0;
      for (var n = 0; n < S; n++) {
        var pl = full.place[n][i], q = Math.round(pl);
        e += full.payAt(pl); if (q <= full.paid) cash++; if (q <= Math.ceil(0.1 * size)) top10++; if (q <= 1) first++;
      }
      total += e / S;
      return Object.assign({}, cand[k], { sim: { e: e / S, cash: cash / S, top10: top10 / S, first: first / S } });
    });
    for (var n2 = 0; n2 < S; n2++) if (full.place[n2].some(function (pl) { return Math.round(pl) <= 1; })) anyFirst++;
    return { lineups: lineups, candidates: cand.length, nights: S, total: total, fee: (contest.entry_fee || 0) * lineups.length,
             anyFirst: anyFirst / S, cut: sim.cut, stability: { halves: both, kept: kept, n: lineups.length }, why: pool.why };
  }

  // A frozen rule set's rules as solve() takes them, on top of BASE
  function rulesFor(set, field, own) {
    var o = Object.assign({}, BASE, set.rules);
    if (set.rules.maxOwnPctile != null) o.maxOwn = fieldOwnPctile(field, own, set.rules.maxOwnPctile);
    delete o.maxOwnPctile;
    return o;
  }

  return { CAP: CAP, SLOTS: SLOTS, MIN_PROJ: MIN_PROJ, BASE: BASE, RULESETS: RULESETS, isG: isG, isF: isF, seeded: seeded,
           gatedProj: gatedProj, fieldOwnPctile: fieldOwnPctile, assign: assign, solve: solve, payTable: payTable,
           simulate: simulate, pick: pick, value: value, simPick: simPick, rulesFor: rulesFor, CAND_UNIQUE: CAND_UNIQUE, CAND_RAND: CAND_RAND };
});
