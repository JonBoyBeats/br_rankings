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
  // ... and a Questionable player at that x gate.questionable.factor (measured by dk_eval.py gate: actual / projected
  // over the graded Questionable player-nights; 1 until there are enough)
  // A team's projected minutes made to add up to exactly total (200): over it, the excess off each in proportion to
  // m x (40 - m), none under 0.5; under it, the shortfall on the same way, none over 40. The same rule as
  // battle-royale-research cbb_nightly.py fit_minutes (the owner's, 2026-11-19).
  function fitMinutes(mins, total) {
    total = total == null ? 200 : total;
    var m = mins.slice();
    for (var it = 0; it < 20; it++) {
      var gap = total - m.reduce(function (a, x) { return a + x; }, 0);
      if (Math.abs(gap) < 1e-6) break;
      var w = m.map(function (x) { return (gap > 0 ? x < 40 : x > 0.5) ? x * Math.max(1, 40 - x) : 0; });
      var W = w.reduce(function (a, x) { return a + x; }, 0);
      if (!W) break;
      m = m.map(function (x, i) { return Math.min(40, Math.max(0.5, x + gap * w[i] / W)); });
    }
    return m;
  }
  // A seeded random generator (mulberry32): the same seed, the same draws
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
  function gatedProj(r, gate) {
    var b = gate && (gate.bands || []).find(function (x) { return x.open && r.salary >= x.lo && r.salary <= x.hi; });
    var p = !b || !r.dk_avg ? r.fp_dk : b.w * r.fp_dk + (1 - b.w) * r.dk_avg;
    var q = gate && gate.questionable && gate.questionable.factor;
    return r.status === "Questionable" && q != null && p != null ? p * q : p;
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
    var inPool = {}; pool.forEach(function (r) { inPool[r.id] = 1; });
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
      var extra = {};                         // player id -> {constraint: coefficient}, from the rules (o.conds)
      var active = (o.conds || []).filter(function (rule) { return !isShare(rule); });
      if (!o.noCaps) (o.conds || []).filter(isShare).forEach(function (rule) {
        // at least: the first lineups meet it until enough do; at most: none more once the cap is reached
        var have = out.filter(function (L) { return meets(rule, L.ids); }).length;
        if (rule.share != null && have < Math.ceil(rule.share * o.n - 1e-9)) active.push({ type: "min", ids: rule.ids, n: rule.n });
        if (rule.maxShare != null && have >= Math.floor(rule.maxShare * o.n + 1e-9)) active.push({ type: "under", ids: rule.ids, n: rule.n });
      });
      active.forEach(function (rule, i) { ruleConstraints(rule, i, extra, cons); });
      pool.forEach(function (r) {
        if ((count[r.id] || 0) >= limit[r.id]) return;
        // the objective: a simulated night's points (o.night, the pool's sim-night draw) or the projection jiggled by
        // o.rand; less o.levW x his projected ownership in % points (the idea's Leverage weight)
        var v = { score: (o.night ? o.night[r.id] || 0 : proj(r) * (1 + o.rand * gauss(ctx.random))) - (o.levW ? o.levW * own(r) : 0), n: 1, sal: r.salary };
        var ex = extra[r.id];
        if (ex) for (var c in ex) v[c] = (v[c] || 0) + ex[c];
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
      var res = solveSplit(ctx.solver, cons, vars, ints, active, inPool);
      if (!res.feasible) { why = "no lineup left fits the rules (loosen Min unique, Max exposure, the stack or ownership rules, Min salary or the locks)"; break; }
      var ids = Object.keys(vars).filter(function (id) { return inPool[id] && res[id] > 0.5; });
      if (ids.length !== 8) { why = "the solver returned " + ids.length + " players"; break; }
      ids.forEach(function (id) { count[id] = (count[id] || 0) + 1; });
      out.push({ ids: ids, slots: assign(ctx, ids) });
    }
    return { lineups: out, why: why };
  }

  // --- rules: the team tiles' buttons and the four if/then templates ------------------------------------------
  //   {type: "min", ids, n}              at least n from ids (Min 2 / Min 3 from a team; Stack with opponent: two of them)
  //   {type: "none", ids}                none of ids (Exclude team)
  //   {type: "if", ids: [P], set, n}     1. if P, then at least n from set
  //   {type: "ifnot", ids: [P], set, n}  2. if not P, then at least n from set
  //   {type: "ifteam", set, n, set2, m}  3. if at least n from set (a team), then at least m from set2 (its opponent)
  //   {type: "never", ids: [P, Q]}       4. never P with Q
  //   a "min" rule with share: s          in at least ceil(s x N) of the N lineups (the rest free): the quadrant buttons'
  //                                       "2+ from the team in 75% / 25% of lineups"
  //   a "min" rule with maxShare: s       in at most floor(s x N) of them (a team exposure cap: "1+ from it in at most 50%")
  //   {type: "under", ids, n}             fewer than n from ids (what an exposure cap turns into once it's reached)
  // Each rule carries its own label (the page writes it). passes() checks a lineup; ruleConstraints() makes the
  // optimizer obey it exactly.
  function isShare(rule) { return rule.share != null || rule.maxShare != null; }
  function meets(rule, ids) { return rule.ids.filter(function (id) { return ids.indexOf(id) >= 0; }).length >= rule.n; }
  // a set's share rules: [{rule, have, need (at least) or cap (at most), ok}] for lineups out of N planned
  function shareStatus(rules, lineups, N) {
    return rules.filter(isShare).map(function (rule) {
      var have = lineups.filter(function (L) { return meets(rule, L.ids); }).length;
      if (rule.share != null) { var need = Math.ceil(rule.share * N - 1e-9); return { rule: rule, have: have, need: need, ok: have >= need }; }
      var cap = Math.floor(rule.maxShare * N + 1e-9);
      return { rule: rule, have: have, cap: cap, ok: have <= cap };
    });
  }
  // whether lineup k can join the picks and leave every share rule still reachable: an at-most rule takes no more
  // lineups that meet it once full; the at-least rules' outstanding lineups, counted as if no lineup met two of them,
  // must fit in the slots left after k (so their lineups are reserved early enough, whatever the overlap)
  function shareFits(rules, cand, picked, k, N) {
    var left = N - picked.length - 1, owed = 0;
    for (var i = 0; i < rules.length; i++) {
      var rule = rules[i];
      if (!isShare(rule)) continue;
      var m = meets(rule, cand[k].ids), have = picked.filter(function (j) { return meets(rule, cand[j].ids); }).length + (m ? 1 : 0);
      if (rule.maxShare != null && m && have > Math.floor(rule.maxShare * N + 1e-9)) return false;
      if (rule.share != null) owed += Math.max(0, Math.ceil(rule.share * N - 1e-9) - have);
    }
    return owed <= left;
  }

  function passes(rule, ids) {
    if (isShare(rule)) return true;           // a share rule is about the set, not one lineup (shareStatus)
    var has = function (id) { return ids.indexOf(id) >= 0; };
    var cnt = function (set) { return (set || []).filter(has).length; };
    switch (rule.type) {
      case "min": return cnt(rule.ids) >= rule.n;
      case "none": return cnt(rule.ids) === 0;
      case "if": return !has(rule.ids[0]) || cnt(rule.set) >= rule.n;
      case "ifnot": return has(rule.ids[0]) || cnt(rule.set) >= rule.n;
      case "ifteam": return cnt(rule.set) < rule.n || cnt(rule.set2) >= rule.m;
      case "never": return cnt(rule.ids) <= 1;
      case "under": return cnt(rule.ids) < rule.n;
    }
    return true;
  }

  function ruleConstraints(rule, i, extra, cons) {
    var k = "r" + i;
    var add = function (id, c, coef) { var e = extra[id] = extra[id] || {}; e[c] = (e[c] || 0) + coef; };
    switch (rule.type) {
      case "min": cons[k] = { min: rule.n }; rule.ids.forEach(function (id) { add(id, k, 1); }); break;
      case "none": cons[k] = { max: 0 }; rule.ids.forEach(function (id) { add(id, k, 1); }); break;
      case "never": cons[k] = { max: 1 }; rule.ids.forEach(function (id) { add(id, k, 1); }); break;
      case "under": cons[k] = { max: rule.n - 1 }; rule.ids.forEach(function (id) { add(id, k, 1); }); break;
      case "if":        // sum(set) - n x P >= 0
        cons[k] = { min: 0 }; rule.set.forEach(function (id) { add(id, k, 1); }); add(rule.ids[0], k, -rule.n); break;
      case "ifnot":     // sum(set) + n x P >= n
        cons[k] = { min: rule.n }; rule.set.forEach(function (id) { add(id, k, 1); }); add(rule.ids[0], k, rule.n); break;
      case "ifteam":
        // An either/or, which a binary switch made slow in this solver (5-13s for 3 lineups with a team minimum
        // alongside): only the counts go in here, unbounded; solve() splits on it when a lineup breaks it.
        rule.set.forEach(function (id) { add(id, k + "a", 1); });
        rule.set2.forEach(function (id) { add(id, k + "b", 1); });
        break;
    }
  }

  // K candidates under the rules, the way Sim & pick and the builder take them: drawn under the plain rules, each
  // if/then rule's pass count taken, the passing ones kept, and the pool topped back up to K with lineups drawn under
  // every rule. draw(o, n) gives up to n lineups under o.
  async function underRules(ctx, o, K, draw) {
    var all = o.conds || [], conds = all.filter(function (rule) { return !isShare(rule); });
    var base = (await draw(Object.assign({}, o, { conds: [] }), K)).lineups;
    var counts = all.map(function (rule) {
      var f = isShare(rule) ? function (L) { return meets(rule, L.ids); } : function (L) { return passes(rule, L.ids); };
      return { label: rule.label, pass: base.filter(f).length, of: base.length, share: isShare(rule) };
    });
    var keep = base.filter(function (L) { return conds.every(function (rule) { return passes(rule, L.ids); }); });
    var kept = keep.length, added = 0, why = "";
    if (conds.length && keep.length < K) {
      var seen = {}; keep.forEach(function (L) { seen[L.ids.slice().sort().join(",")] = 1; });
      var more = await draw(o, K - keep.length);
      more.lineups.forEach(function (L) {
        var key = L.ids.slice().sort().join(",");
        if (!seen[key]) { seen[key] = 1; keep.push(L); added++; }
      });
      why = more.why || "";
    }
    // an at-least share rule needs lineups that meet it: if fewer than three times what the set needs, draw more that do
    var shareMore = 0;
    for (var i = 0; i < all.length; i++) {
      var rule = all[i];
      if (rule.share == null) continue;
      var want = 3 * Math.ceil(rule.share * (o.n || 20) - 1e-9), have = keep.filter(function (L) { return meets(rule, L.ids); }).length;
      if (have < want) {
        var seen2 = {}; keep.forEach(function (L) { seen2[L.ids.slice().sort().join(",")] = 1; });
        var extra = await draw(Object.assign({}, o, { conds: conds.concat([{ type: "min", ids: rule.ids, n: rule.n }]) }), want - have);
        extra.lineups.forEach(function (L) {
          var key = L.ids.slice().sort().join(",");
          if (!seen2[key]) { seen2[key] = 1; keep.push(L); shareMore++; }
        });
      }
    }
    return { lineups: keep, counts: counts, kept: kept, of: base.length, added: added + shareMore, why: why, base: base };
  }

  // Solve; if the lineup breaks a template-3 rule (n+ from set without m+ from set2), solve its two cases apart (fewer
  // than n from set; n+ from set and m+ from set2) and keep the better: the same optimum the binary switch gives.
  function solveSplit(solver, cons, vars, ints, conds, inPool) {
    var res = solver.Solve({ optimize: "score", opType: "max", constraints: cons, variables: vars, ints: ints });
    if (!res.feasible) return res;
    var ids = Object.keys(vars).filter(function (id) { return inPool[id] && res[id] > 0.5; });
    for (var i = 0; i < conds.length; i++) {
      var rule = conds[i];
      if (rule.type !== "ifteam" || passes(rule, ids)) continue;
      var a = Object.assign({}, cons), b = Object.assign({}, cons);
      a["r" + i + "a"] = { max: rule.n - 1 };
      b["r" + i + "a"] = { min: rule.n }; b["r" + i + "b"] = { min: rule.m };
      var ra = solveSplit(solver, a, vars, ints, conds, inPool), rb = solveSplit(solver, b, vars, ints, conds, inPool);
      if (!ra.feasible) return rb;
      if (!rb.feasible) return ra;
      return ra.result >= rb.result ? ra : rb;
    }
    return res;
  }

  // The payout at a place with ties field entries tied there (DraftKings splits the prizes of the places a tie covers
  // evenly): the mean of the payouts from the place to the place + ties (both rounded)
  function placePay(pay, place, ties) {
    var q = Math.round(place), m = ties >= 0.5 ? Math.round(ties) : 0, t = 0;
    if (!m) return q >= 1 && q < pay.length ? pay[q] : 0;
    for (var i = q; i <= q + m; i++) t += i >= 1 && i < pay.length ? pay[i] : 0;
    return t / (m + 1);
  }

  function payTable(c) {     // place -> dollars, from [[first, last, dollars], ...]
    var t = [0];
    (c.payouts || []).forEach(function (p) { for (var i = p[0]; i <= p[1]; i++) t[i] = p[2]; });
    for (var i = 1; i < t.length; i++) t[i] = t[i] || 0;
    return t;
  }

  // S simulated nights: each player's points drawn from his Proj and his ±, in z's shape; the candidates' and the
  // field's lineups scored. Kept by lineup, for the builder's loops: cs[k * S + s] is lineup k's score on night s,
  // fa[k * S + s] the field entries above it. Also the simulated field's cut lines (winning score, top 10%, the last
  // paid place), averaged over the nights.
  // Shared draws in the sim: on each night a standard normal T per team and G per game (times the spread of the
  // outcome shape z), and each player's outcome is sqrt(1 - a^2 - b^2) x his own draw + a x T + b x G, so teammates
  // correlate a^2 + b^2 and opponents b^2. Sized on 2026-27's box scores (battle-royale-research
  // scripts/cbb_corr_study.py, games of 2026-11-03 to 11-15, 2,837 player-games of players with a usual of 10+ DK
  // points, misses against their usual in their other games with the line taken out): teammates -0.032 (90%: -0.048
  // to -0.012), opponents -0.003 (-0.021 to +0.015), a team's total swinging 0.82x what independent players would
  // make. A shared draw can only add correlation, and the data show none (slightly the reverse, minutes being shared),
  // so both are 0: the sim's draws stay independent. ctx.corr ({team, game}) overrides them, for checking.
  var CORR = { team: 0, game: 0 };
  // The prize split among exact ties with the simulated field (placePay). Off from 2026-11-17 while the simulated field
  // duplicated too little overall and too much of our own lineups; back on once the field was calibrated against the real
  // fields (battle-royale-research scripts/dk_field_calibrate.py: duplication with another user 7.1% simulated against
  // 6.8% real, salary used matched, the owner's entries duplicated 1 of 36). ctx.tieSplit overrides it, for checking.
  var TIE_SPLIT = true;

  function simulate(ctx, cand, field, z, contest, N, S) {
    var by = {}; ctx.rows.forEach(function (r) { by[r.id] = r; });
    var ix = {}, mean = [], err = [], tOf = [], gOf = [], teams = {}, games = {};
    function idx(id) {
      if (ix[id] == null) {
        var r = by[id] || {}, m = r.status === "Out" ? 0 : (by[id] ? ctx.proj(r) : 0);
        ix[id] = mean.length; mean.push(m); err.push(r.miss_dk || 0.35 * m);
        var t = r.team || "?", g = r.game || t;
        if (teams[t] == null) teams[t] = Object.keys(teams).length;
        if (games[g] == null) games[g] = Object.keys(games).length;
        tOf.push(teams[t]); gOf.push(games[g]);
      }
      return ix[id];
    }
    // every player on the slate first, in its fixed order: each night then takes the same draws for a player whatever
    // lineups are in the pool, so a seeded ctx.random gives the same nights to any pool (the DK page's fills, 2026-11-18)
    ctx.rows.forEach(function (r) { idx(r.id); });
    var candIx = cand.map(function (L) { return L.ids.map(idx); });
    var fieldIx = field.map(function (L) { return L.map(idx); });
    var P = mean.length, K = cand.length, size = contest.size || 0, paid = payTable(contest).length - 1;
    var w = Math.max(0, size - N) / fieldIx.length;               // each field lineup stands for w entries
    var pts = new Float32Array(P), cs = new Float32Array(K * S), fa = new Float32Array(K * S), cut = { win: 0, top10: 0, cash: 0 };
    var fsc = new Float64Array(fieldIx.length), fieldPts = 0;
    function scoreAtPlace(place) {                                // the field's score at a place (1 = best)
      var i = fsc.length - Math.min(fsc.length, Math.max(1, Math.ceil(place / w)));
      return fsc[i];
    }
    var corr = ctx.corr || CORR, ca = corr.team || 0, cb = corr.game || 0, shared = ca > 0 || cb > 0;
    var zm = 0, zsd = 0;
    if (shared) {
      z.forEach(function (v) { zm += v / z.length; });
      z.forEach(function (v) { zsd += (v - zm) * (v - zm) / z.length; });
      zsd = Math.sqrt(zsd);
    }
    var own = Math.sqrt(Math.max(0, 1 - ca * ca - cb * cb)), T = new Float64Array(Object.keys(teams).length), G = new Float64Array(Object.keys(games).length);
    function normal() { var u = 1 - ctx.random(), v = ctx.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
    for (var s = 0; s < S; s++) {
      if (!shared) for (var p = 0; p < P; p++) pts[p] = Math.max(0, mean[p] + z[(ctx.random() * z.length) | 0] * err[p]);
      else {
        for (var ti = 0; ti < T.length; ti++) T[ti] = normal();
        for (var gi = 0; gi < G.length; gi++) G[gi] = normal();
        for (var p3 = 0; p3 < P; p3++) {
          var d = z[(ctx.random() * z.length) | 0];
          pts[p3] = Math.max(0, mean[p3] + (zm + own * (d - zm) + zsd * (ca * T[tOf[p3]] + cb * G[gOf[p3]])) * err[p3]);
        }
      }
      for (var f = 0; f < fieldIx.length; f++) { var t = 0, L = fieldIx[f]; for (var j = 0; j < 8; j++) t += pts[L[j]]; fsc[f] = t; fieldPts += t / fieldIx.length / S; }
      fsc.sort();                                                  // ascending
      cut.win += scoreAtPlace(1) / S; cut.top10 += scoreAtPlace(Math.ceil(0.1 * size)) / S; cut.cash += scoreAtPlace(paid) / S;
      for (var k = 0; k < K; k++) {
        var t2 = 0, L2 = candIx[k]; for (var j2 = 0; j2 < 8; j2++) t2 += pts[L2[j2]];
        var lo = 0, hi = fsc.length, t2e = t2 + 1e-6;              // field lineups scoring above t2 (an identical one ties)
        while (lo < hi) { var mid = (lo + hi) >> 1; if (fsc[mid] <= t2e) lo = mid + 1; else hi = mid; }
        cs[k * S + s] = t2; fa[k * S + s] = (fsc.length - lo) * w;
      }
    }
    // each lineup's quality and leverage, beside its sim value: quality, its expected points less what its salary
    // buys at the simulated field's points per dollar; leverage, the share of the field holding its core (its three
    // highest-salaried players; lower is more leverage)
    var salOf = function (ids) { return ids.reduce(function (a, id) { return a + ((by[id] || {}).salary || 0); }, 0); };
    var fieldSal = field.reduce(function (a, L) { return a + salOf(L); }, 0) / Math.max(1, field.length), rate = fieldSal ? fieldPts / fieldSal : 0;
    var fieldSets = field.map(function (L) { var o = {}; L.forEach(function (id) { o[id] = 1; }); return o; });
    var quality = new Float32Array(K), core = new Float32Array(K);
    for (var k3 = 0; k3 < K; k3++) {
      var e = 0; for (var s3 = 0; s3 < S; s3++) e += cs[k3 * S + s3] / S;
      quality[k3] = e - salOf(cand[k3].ids) * rate;
      var top = cand[k3].ids.slice().sort(function (a, b) { return ((by[b] || {}).salary || 0) - ((by[a] || {}).salary || 0); }).slice(0, 3), hold = 0;
      for (var f3 = 0; f3 < fieldSets.length; f3++) if (fieldSets[f3][top[0]] && fieldSets[f3][top[1]] && fieldSets[f3][top[2]]) hold++;
      core[k3] = fieldSets.length ? hold / fieldSets.length : 0;
    }
    // duplication: each lineup's identical lineups in the simulated field (dup), and the field entries they stand for
    // in this contest (tie: dup x w), who tie with it every night and split the prizes there (placePay)
    var fkey = {};
    field.forEach(function (L) { var k = L.slice().sort().join(","); fkey[k] = (fkey[k] || 0) + 1; });
    var dup = new Float32Array(K), tie = new Float32Array(K);
    for (var k4 = 0; k4 < K; k4++) { dup[k4] = fkey[cand[k4].ids.slice().sort().join(",")] || 0; tie[k4] = dup[k4] * w; }
    return { cs: cs, fa: fa, K: K, S: S, cut: cut, quality: quality, core: core, rate: rate, dup: dup, tie: tie,
             tieSplit: ctx.tieSplit != null ? !!ctx.tieSplit : TIE_SPLIT };
  }

  // The portfolio builder: a set of picked lineups, and what each other lineup would ADD to it, on the given nights.
  // On every night our own lineups are ranked among the field and among each other, so a lineup that scores on the
  // same nights as one already picked mostly pushes ours down a place: its added value is small (self-competition),
  // and a lineup that hits on other nights adds more. Coverage: the share of nights where at least one picked lineup
  // reaches the top 1% (or cashes). The 20-pick (pick) and the DK page's builder both use this.
  function builder(sim, contest, nights) {
    var S = sim.S, K = sim.K, pay = payTable(contest), paid = pay.length - 1, size = contest.size || 0;
    var T1 = Math.max(1, Math.ceil(0.01 * size)), T10 = Math.max(1, Math.ceil(0.1 * size));
    if (!nights) { nights = []; for (var n0 = 0; n0 < S; n0++) nights.push(n0); }
    var M = nights.length, cs = sim.cs, fa = sim.fa;
    var payF = new Float64Array(Math.max(paid + 2, 2));
    for (var i0 = 1; i0 <= paid; i0++) payF[i0] = pay[i0];
    var tie = sim.tieSplit && sim.tie ? sim.tie : new Float32Array(K);
    function payAt(place, t) { if (t >= 0.5) return placePay(pay, place, t); var q = Math.round(place); return q >= 1 && q <= paid ? payF[q] : 0; }
    var picked = [], P = 0, ps = new Float32Array(0), pp = new Float32Array(0), dp = new Float32Array(0);
    var cov1 = new Uint8Array(M), covC = new Uint8Array(M), total = 0;
    function refresh() {
      P = picked.length;
      ps = new Float32Array(M * P); pp = new Float32Array(M * P); dp = new Float32Array(M * P); total = 0;
      for (var a = 0; a < M; a++) {
        var s = nights[a], c1 = 0, cc = 0;
        for (var i = 0; i < P; i++) ps[a * P + i] = cs[picked[i] * S + s];
        for (var i2 = 0; i2 < P; i2++) {
          var me = ps[a * P + i2], mine = 0;
          for (var j = 0; j < P; j++) if (ps[a * P + j] > me) mine++;
          var pl = 1 + fa[picked[i2] * S + s] + mine;
          var tt = tie[picked[i2]];
          pp[a * P + i2] = pl; dp[a * P + i2] = payAt(pl + 1, tt) - payAt(pl, tt); total += payAt(pl, tt);
          var q = Math.round(pl); if (q <= T1) c1 = 1; if (q <= paid) cc = 1;
        }
        cov1[a] = c1; covC[a] = cc;
      }
      total /= M;
    }
    // what lineup k adds: expected payout with it minus without, and the coverage it adds
    function score(k) {
      var v = 0, g1 = 0, gc = 0, base = k * S;
      for (var a = 0; a < M; a++) {
        var s = nights[a], me = cs[base + s], mine = 0, delta = 0, off = a * P;
        for (var i = 0; i < P; i++) { if (ps[off + i] > me) mine++; else delta += dp[off + i]; }
        var pl = 1 + fa[base + s] + mine, q = Math.round(pl);
        v += payAt(pl, tie[k]) + delta;
        if (!cov1[a] && q <= T1) g1++;
        if (!covC[a] && q <= paid) gc++;
      }
      return { value: v / M, top1: g1 / M, cash: gc / M };
    }
    function alone(k) {             // its expected payout by itself (no other lineup of ours in the contest)
      var v = 0, base = k * S;
      for (var a = 0; a < M; a++) v += payAt(1 + fa[base + nights[a]], tie[k]);
      return v / M;
    }
    function lineupStats(i) {       // picked lineup i's numbers in the portfolio as it stands
      var e = 0, cash = 0, top10 = 0, first = 0;
      for (var a = 0; a < M; a++) {
        var pl = pp[a * P + i], q = Math.round(pl);
        e += payAt(pl, tie[picked[i]]); if (q <= paid) cash++; if (q <= T10) top10++; if (q <= 1) first++;
      }
      return { e: e / M, cash: cash / M, top10: top10 / M, first: first / M };
    }
    function coverage() {
      var c1 = 0, cc = 0, f = 0;
      for (var a = 0; a < M; a++) {
        c1 += cov1[a]; cc += covC[a];
        for (var i = 0; i < P; i++) if (Math.round(pp[a * P + i]) <= 1) { f++; break; }
      }
      return { top1: c1 / M, cash: cc / M, first: f / M };
    }
    return { picked: picked, payAt: payAt, paid: paid, K: K,
             add: function (k) { if (picked.indexOf(k) < 0) { picked.push(k); refresh(); } },
             remove: function (k) { var i = picked.indexOf(k); if (i >= 0) { picked.splice(i, 1); refresh(); } },
             set: function (ks) { picked.length = 0; ks.forEach(function (k) { picked.push(k); }); refresh(); },
             score: score, alone: alone, lineupStats: lineupStats, coverage: coverage, total: function () { return total; } };
  }

  // The 20-pick: N times, add the lineup that raises the set's expected payout most given those already picked
  // (builder.score: self-competition in), within the exposure caps and Min unique.
  // A lineup's core: its three highest-salaried players (ties by id), as a key
  function cores(ctx, lineups) {
    var sal = {}; ctx.rows.forEach(function (r) { sal[r.id] = r.salary || 0; });
    return lineups.map(function (L) {
      return L.ids.slice().sort(function (a, b) { return (sal[b] || 0) - (sal[a] || 0) || (a < b ? -1 : 1); }).slice(0, 3).sort().join(",");
    });
  }
  // the most-used core in a set of lineups: {key, n, of, share}
  function topCore(ctx, lineups) {
    var c = {}, best = null;
    cores(ctx, lineups).forEach(function (k) { c[k] = (c[k] || 0) + 1; if (!best || c[k] > c[best]) best = k; });
    return best ? { key: best, n: c[best], of: lineups.length, share: c[best] / lineups.length } : null;
  }
  // Each lineup alone in a contest, from the sim's nights: how often it places in the top 1%, the top 10% and the
  // cash, and its payout alone on the odd and the even nights (for tiers). {top1, top10, cash, odd, even} arrays.
  function aloneStats(sim, contest) {
    var S = sim.S, K = sim.K, size = contest.size || 0, paid = payTable(contest).length - 1;
    var T1 = Math.max(1, Math.ceil(0.01 * size)), T10 = Math.max(1, Math.ceil(0.1 * size));
    var odd = [], even = [];
    for (var s = 0; s < S; s++) (s % 2 ? odd : even).push(s);
    var bo = builder(sim, contest, odd), be = builder(sim, contest, even);
    var out = { top1: new Float32Array(K), top10: new Float32Array(K), cash: new Float32Array(K), odd: new Float32Array(K), even: new Float32Array(K) };
    for (var k = 0; k < K; k++) {
      var a = 0, b = 0, c = 0;
      for (var s2 = 0; s2 < S; s2++) {
        var q = Math.round(1 + sim.fa[k * S + s2]);
        if (q <= T1) a++;
        if (q <= T10) b++;
        if (q <= paid) c++;
      }
      out.top1[k] = a / S; out.top10[k] = b / S; out.cash[k] = c / S; out.odd[k] = bo.alone(k); out.even[k] = be.alone(k);
    }
    return out;
  }
  // Tiers A / B / C by the sim's own noise: the spread of each lineup's odd-night less even-night value gives the
  // noise of one lineup's value (sigma = sd / 2: the full value is the halves' mean); two lineups differ by more than
  // noise when their values are 2 x sqrt(2) x sigma apart. Best first, a lineup starts the next tier once it falls that
  // far below the top of its own; C holds the rest. {tier: ["A", ...], sigma}
  function tiers(v, h1, h2) {
    var n = v.length, d = [], m = 0;
    for (var i = 0; i < n; i++) { d.push(h1[i] - h2[i]); m += (h1[i] - h2[i]) / n; }
    var sd = 0; d.forEach(function (x) { sd += (x - m) * (x - m) / Math.max(1, n - 1); });
    var sigma = Math.sqrt(sd) / 2, gap = 2 * Math.SQRT2 * sigma, order = [];
    for (var j = 0; j < n; j++) order.push(j);
    order.sort(function (a, b) { return v[b] - v[a]; });
    var out = new Array(n), t = 0, top = n ? v[order[0]] : 0;
    order.forEach(function (k) {
      if (t < 2 && v[k] < top - gap) { t++; top = v[k]; }
      out[k] = "ABC"[t];
    });
    return { tier: out, sigma: sigma };
  }
  // a lineup's 28 player pairs, as keys
  function pairs(ids) {
    var s = ids.slice().sort(), out = [];
    for (var i = 0; i < s.length; i++) for (var j = i + 1; j < s.length; j++) out.push(s[i] + "|" + s[j]);
    return out;
  }
  // o.maxCore (optional, a share): no core in more than max(1, floor(maxCore x N)) of the N lineups
  function coreLimit(o, N) { return o.maxCore ? Math.max(1, Math.floor(o.maxCore * N + 1e-9)) : 0; }

  function pick(ctx, o, cand, sim, contest, N, nights) {
    var st = ctx.state, b = builder(sim, contest, nights), count = {}, limit = {};
    var coreOf = o.maxCore ? cores(ctx, cand) : null, coreLim = coreLimit(o, N), coreN = {};
    // o.pairLimit with o.pairCount (shared across the night's contests): no two players together in more than pairLimit entries
    var pairsOf = o.pairLimit ? cand.map(function (L) { return pairs(L.ids); }) : null;
    ctx.rows.forEach(function (r) {
      var cap = Math.min(o.maxExpo, st.cap[r.id] != null && st.cap[r.id] !== "" ? +st.cap[r.id] / 100 : 1);
      limit[r.id] = st.lock[r.id] ? N : Math.floor(cap * N + 1e-9);
    });
    // the at-least share rules first, the one with the fewest qualifying candidates first (each lineup the best
    // addition among those that meet it), so the rarest requirement isn't left to lineups the caps have shut out;
    // then the rest of the set, by added value
    var conds = o.conds || [], perLine = conds.filter(function (rule) { return !isShare(rule); });
    var phases = conds.filter(function (rule) { return rule.share != null; }).map(function (rule) {
      return { rule: rule, n: cand.filter(function (L) { return meets(rule, L.ids); }).length };
    }).sort(function (x, y) { return x.n - y.n; }).map(function (x) { return x.rule; }).concat([null]);
    phases.forEach(function (rule) {
      var need = rule ? Math.ceil(rule.share * N - 1e-9) : N;
      while (b.picked.length < N && (!rule || b.picked.filter(function (j) { return meets(rule, cand[j].ids); }).length < need)) {
        var best = -1, bestV = -Infinity, ok = [];
        for (var k = 0; k < cand.length; k++) {
          if (b.picked.indexOf(k) >= 0 || (rule && !meets(rule, cand[k].ids)) ||
              (perLine.length && !perLine.every(function (r) { return passes(r, cand[k].ids); })) || !fits(cand, b.picked, k, count, limit, o.minUnique) ||
              !shareFits(conds, cand, b.picked, k, N) || (coreOf && (coreN[coreOf[k]] || 0) + 1 > coreLim) ||
              (pairsOf && pairsOf[k].some(function (pk) { return (o.pairCount[pk] || 0) + 1 > o.pairLimit; }))) continue;
          ok.push([k, b.score(k)]);
        }
        // o.objective: "roi" (the default: added value), "cover" (the rise in nights one of the set reaches the top
        // 1%, added value breaking ties), "balanced" (each, over the best of it among the candidates, weighted equally)
        var obj = o.objective || "roi", mv = 1e-12, mc = 1e-12;
        if (obj === "balanced") ok.forEach(function (x) { mv = Math.max(mv, x[1].value); mc = Math.max(mc, x[1].top1); });
        ok.forEach(function (x) {
          var sc = x[1], v = obj === "cover" ? sc.top1 * 1e6 + sc.value : obj === "balanced" ? 0.5 * Math.max(0, sc.value) / mv + 0.5 * sc.top1 / mc : sc.value;
          if (v > bestV) { bestV = v; best = x[0]; }
        });
        if (best < 0) break;
        b.add(best);
        cand[best].ids.forEach(function (id) { count[id] = (count[id] || 0) + 1; });
        if (coreOf) coreN[coreOf[best]] = (coreN[coreOf[best]] || 0) + 1;
        if (pairsOf) pairsOf[best].forEach(function (pk) { o.pairCount[pk] = (o.pairCount[pk] || 0) + 1; });
      }
    });
    return { chosen: b.picked.slice(), builder: b };
  }

  // whether lineup k can join the picks: no player past his cap, and Min unique against each picked lineup
  function fits(cand, picked, k, count, limit, minUnique) {
    var ids = cand[k].ids;
    for (var i = 0; i < ids.length; i++) if ((count[ids[i]] || 0) + 1 > limit[ids[i]]) return false;
    for (var j = 0; j < picked.length; j++) {
      var shared = 0, other = cand[picked[j]].ids;
      for (var m = 0; m < ids.length; m++) if (other.indexOf(ids[m]) >= 0) shared++;
      if (shared > 8 - minUnique) return false;
    }
    return true;
  }

  // A fixed portfolio's mean payout over the given nights (ours placed among the field and each other)
  function value(sim, contest, chosen, nights) {
    var b = builder(sim, contest, nights);
    b.set(chosen);
    return b.total();
  }

  // The top n lineups by their expected payout alone (no self-competition, no caps): for comparing with the pick
  function topAlone(sim, contest, n) {
    var b = builder(sim, contest), v = [];
    for (var k = 0; k < sim.K; k++) v.push([b.alone(k), k]);
    return v.sort(function (x, y) { return y[0] - x[0]; }).slice(0, n).map(function (x) { return x[1]; });
  }

  // A set of lineups' diversity: the most-used player's share, the mean players shared by two lineups, and the
  // distinct cores (a lineup's core: its three highest-salaried players)
  function diversity(ctx, lineups) {
    var by = {}; ctx.rows.forEach(function (r) { by[r.id] = r; });
    var count = {}, cores = {}, shared = 0, pairs = 0;
    lineups.forEach(function (L, i) {
      L.ids.forEach(function (id) { count[id] = (count[id] || 0) + 1; });
      cores[L.ids.slice().sort(function (a, b) { return (by[b] || {}).salary - (by[a] || {}).salary || (a < b ? -1 : 1); }).slice(0, 3).sort().join(",")] = 1;
      for (var j = 0; j < i; j++) { shared += L.ids.filter(function (id) { return lineups[j].ids.indexOf(id) >= 0; }).length; pairs++; }
    });
    var top = Object.keys(count).sort(function (a, b) { return count[b] - count[a]; })[0];
    return { most_used: top ? { id: top, name: (by[top] || {}).name, share: count[top] / lineups.length } : null,
             mean_shared: pairs ? shared / pairs : 0, cores: Object.keys(cores).length, n: lineups.length };
  }

  // A large pool for the builder: lineups drawn under the rules at CAND_RAND noise (o.poolRand: the DK page's draw sets its own), duplicates dropped (no
  // uniqueness constraints: at 1,000 lineups they make every solve slower; 1,000 distinct took 1,023 draws, 18s)
  async function pool(ctx, o, K) {
    var res = await underRules(ctx, o, K, function (o2, n) { return poolDraw(ctx, o2, n); });
    res.why = res.why || (res.lineups.length < K ? "only " + res.lineups.length + " distinct lineups fit the rules" : "");
    return res;
  }

  // One simulated night's points for every player, from the distribution simulate() draws them from: his projection
  // plus his expected miss x a draw from the outcome shape z (never below 0), with the team and game draws when CORR
  // (or ctx.corr) sets them
  function nightPoints(ctx, z) {
    var corr = ctx.corr || CORR, ca = corr.team || 0, cb = corr.game || 0, out = {}, T = {}, G = {}, zm = 0, zsd = 0;
    if (ca > 0 || cb > 0) {
      z.forEach(function (v) { zm += v / z.length; });
      z.forEach(function (v) { zsd += (v - zm) * (v - zm) / z.length; });
      zsd = Math.sqrt(zsd);
    }
    var own = Math.sqrt(Math.max(0, 1 - ca * ca - cb * cb));
    ctx.rows.forEach(function (r) {
      var m = r.status === "Out" ? 0 : ctx.proj(r), err = r.miss_dk || 0.35 * m, d = z[(ctx.random() * z.length) | 0];
      if (ca > 0 || cb > 0) {
        var t = r.team || "?", g = r.game || t;
        if (T[t] == null) T[t] = gauss(ctx.random);
        if (G[g] == null) G[g] = gauss(ctx.random);
        d = zm + own * (d - zm) + zsd * (ca * T[t] + cb * G[g]);
      }
      out[r.id] = Math.max(0, m + d * err);
    });
    return out;
  }

  // The pool's draw: with o.z (the sim's outcome shape), each lineup is the best one under the rules for one simulated
  // night (nightPoints), less the Leverage weight o.levW x projected ownership; without it, the projection jiggled by
  // o.poolRand / CAND_RAND. Duplicates dropped.
  async function poolDraw(ctx, o, K) {
    var seen = {}, out = [], tries = 0;
    while (out.length < K && tries < 3 * K) {
      if (tries % 25 === 24 && ctx.progress) await ctx.progress("Building the pool… " + out.length + " of " + K);
      var r = await solve(ctx, Object.assign({}, o, { n: 1, minUnique: 1, rand: o.poolRand != null ? o.poolRand : CAND_RAND, noCaps: true,
                                                      night: o.z ? nightPoints(ctx, o.z) : null }));
      tries++;
      if (!r.lineups.length) return { lineups: out, why: r.why };
      var key = r.lineups[0].ids.slice().sort().join(",");
      if (!seen[key]) { seen[key] = 1; out.push(r.lineups[0]); }
    }
    return { lineups: out, why: out.length < K ? "only " + out.length + " distinct lineups in " + tries + " draws" : "" };
  }

  // Candidates under the rules, the sim, the pick, and its stability: the same pick made on each half of the nights
  // apart, each scored on the other half against the pick made there.
  async function simPick(ctx, o, contest, field, z, K, S) {
    var N = o.n;
    var draw = function (o2, n) {
      return solve(ctx, Object.assign({}, o2, { n: n, minUnique: CAND_UNIQUE, rand: CAND_RAND, noCaps: true, label: "Building candidates" }));
    };
    var cp = await underRules(ctx, o, Math.max(N, K), draw);
    var cand = cp.lineups;
    if (cand.length < N) return { error: "only " + cand.length + " candidates fit the rules" + (cp.why ? " (" + cp.why + ")" : ""), rules: cp };
    if (ctx.progress) await ctx.progress("Simulating " + S + " nights…");
    var sim = simulate(ctx, cand, field, z, contest, N, S);
    var full = pick(ctx, o, cand, sim, contest, N);
    // too thin to fill N under the rules and the caps: draw more under the rules (and, for each at-least share rule
    // left short, more lineups that meet it), avoiding the players the pick already has at their exposure cap, and
    // pick again; twice at most
    for (var round = 0; round < 2 && full.chosen.length < N && (o.conds || []).length; round++) {
      if (ctx.progress) await ctx.progress("Only " + full.chosen.length + " of " + N + " fit: drawing more candidates under the rules…");
      var seen = {}; cand.forEach(function (L) { seen[L.ids.slice().sort().join(",")] = 1; });
      var plain = (o.conds || []).filter(function (rule) { return !isShare(rule); });
      var used = {}; full.chosen.forEach(function (k) { cand[k].ids.forEach(function (id) { used[id] = (used[id] || 0) + 1; }); });
      var capped = Object.keys(used).filter(function (id) { return used[id] >= Math.floor(o.maxExpo * N + 1e-9) && !ctx.state.lock[id]; });
      var avoid = capped.length ? [{ type: "none", ids: capped }] : [];
      var draws = [await draw(Object.assign({}, o, { conds: plain.concat(avoid).concat((o.conds || []).filter(isShare)) }), Math.max(N, K))];
      var short = shareStatus(o.conds || [], full.chosen.map(function (k) { return cand[k]; }), N).filter(function (x) { return x.need != null && !x.ok; });
      for (var q = 0; q < short.length; q++) {
        draws.push(await draw(Object.assign({}, o, { conds: plain.concat(avoid).concat([{ type: "min", ids: short[q].rule.ids, n: short[q].rule.n }]) }), Math.max(N, K)));
      }
      draws.forEach(function (more) {
        more.lineups.forEach(function (L) { var key = L.ids.slice().sort().join(","); if (!seen[key]) { seen[key] = 1; cand.push(L); cp.added++; } });
      });
      sim = simulate(ctx, cand, field, z, contest, N, S);
      full = pick(ctx, o, cand, sim, contest, N);
      cp.topped = true;
    }
    var h1 = [], h2 = [];
    for (var s = 0; s < S; s++) (s < S / 2 ? h1 : h2).push(s);
    if (ctx.progress) await ctx.progress("Checking the pick on each half of the nights…");
    // Many candidates are worth nearly the same, so which ones get picked moves with the draw; what matters is
    // whether a pick made on one set of nights keeps its value on another.
    var a = pick(ctx, o, cand, sim, contest, N, h1).chosen, b = pick(ctx, o, cand, sim, contest, N, h2).chosen;
    var both = a.filter(function (k) { return b.indexOf(k) >= 0; }).length;
    var kept = (value(sim, contest, a, h2) / (value(sim, contest, b, h2) || 1) + value(sim, contest, b, h1) / (value(sim, contest, a, h1) || 1)) / 2;
    var lineups = full.chosen.map(function (k, i) { return Object.assign({}, cand[k], { sim: full.builder.lineupStats(i) }); });
    var cov = full.builder.coverage();
    var cost = null;
    if ((o.conds || []).length) {
      // What the rules cost: the set picked with all of them, with none, and with each removed, on one pool (the
      // candidates under the rules and the plain ones drawn first) over the same nights, so only the rules differ
      if (ctx.progress) await ctx.progress("Pricing the rules: picking again without them…");
      var union = cand.slice(), seenU = {};
      union.forEach(function (L) { seenU[L.ids.slice().sort().join(",")] = 1; });
      (cp.base || []).forEach(function (L) { var key = L.ids.slice().sort().join(","); if (!seenU[key]) { seenU[key] = 1; union.push(L); } });
      var simU = simulate(ctx, union, field, z, contest, N, S);
      var ev = function (conds) {
        var r = pick(ctx, Object.assign({}, o, { conds: conds }), union, simU, contest, N);
        return { value: r.builder.total(), n: r.chosen.length };
      };
      var all = ev(o.conds), none = ev([]);
      cost = { pool: union.length, nights: S, all: all.value, all_n: all.n, none: none.value, none_n: none.n,
               per: o.conds.map(function (rule, i) {
                 var w = ev(o.conds.filter(function (x, j) { return j !== i; }));
                 return { label: rule.label, without: w.value, cost: w.value - all.value };
               }) };
    }
    return { lineups: lineups, chosen: full.chosen, cand: cand, sim: sim, candidates: cand.length, nights: S,
             total: full.builder.total(), fee: (contest.entry_fee || 0) * lineups.length, anyFirst: cov.first, coverage: cov,
             diversity: diversity(ctx, lineups), cut: sim.cut, stability: { halves: both, kept: kept, n: lineups.length }, why: cp.why, rules: cp,
             share: shareStatus(o.conds || [], lineups, N), cost: cost };
  }

  // The re-sim and cut: from a bank of lineups down to keep, a round at a time. Each round simulates the survivors over
  // fresh nights and adds each lineup's payout alone (no other lineup of ours) in every contest to its running totals,
  // so its estimate is the mean over every night of every round it has been in. Then each contest ranks the survivors
  // by that estimate, and a lineup stays if it ranks high enough in ANY contest: the threshold rank is the lowest that
  // keeps (1 - cut) of them (never fewer than keep). contests: [{contest, n: our entries in it}]. progress(round) gets
  // {round, survivors} after each round.
  // The cut, within each idea: tags[i] is bank lineup i's idea (the tag it was first drawn under). Each idea keeps the
  // same share of its own lineups, Keep / bank size (rounded, at least 1). Each round simulates the survivors over fresh
  // nights and adds each one's payout alone in every contest (prizes split among exact ties with the field: placePay)
  // to its running total, so a lineup's number is its mean over every night it has been through; a lineup's rank is its
  // best across the contests (top in ANY of them). Then each idea keeps its best-ranked, down by Cut % a round to its
  // share, skipping a lineup that shares 7+ of 8 players with a better-ranked one it has kept.
  async function cutPool(ctx, bank, contests, field, z, keep, cut, nights, progress, tags) {
    var F = field.length, idx = bank.map(function (L, i) { return i; });
    var tagOf = bank.map(function (L, i) { return (tags && tags[i]) || "all"; }), size = {}, quota = {};
    tagOf.forEach(function (t) { size[t] = (size[t] || 0) + 1; });
    Object.keys(size).forEach(function (t) { quota[t] = Math.max(1, Math.round(size[t] * Math.min(1, keep / bank.length))); });
    var sum = contests.map(function () { return new Float64Array(bank.length); }), seen = new Float64Array(bank.length);
    var raw = { size: F + 1, payouts: [] };               // a contest where each field lineup stands for one entry
    var rounds = [];
    var over = function () { var n = {}; idx.forEach(function (i) { n[tagOf[i]] = (n[tagOf[i]] || 0) + 1; }); return Object.keys(n).some(function (t) { return n[t] > quota[t]; }); };
    for (var round = 1; over() || round === 1; round++) {
      var lineups = idx.map(function (i) { return bank[i]; });
      var sim = simulate(ctx, lineups, field, z, raw, 1, nights);
      contests.forEach(function (c, ci) {
        var pay = payTable(c.contest), w = Math.max(0, (c.contest.size || 0) - c.n) / F;
        for (var k = 0; k < lineups.length; k++) {
          var t = 0, base = k * nights, ties = sim.tieSplit ? sim.dup[k] * w : 0;
          for (var s = 0; s < nights; s++) t += placePay(pay, 1 + sim.fa[base + s] * w, ties);
          sum[ci][idx[k]] += t;
        }
      });
      idx.forEach(function (i) { seen[i] += nights; });
      if (!over()) { rounds.push({ round: round, survivors: idx.length, ids: idx.slice() }); if (progress) await progress(rounds[rounds.length - 1]); break; }
      var best = {};                                       // each lineup's best rank across the contests
      idx.forEach(function (i) { best[i] = Infinity; });
      contests.forEach(function (c, ci) {
        idx.slice().sort(function (a, b) { return sum[ci][b] / seen[b] - sum[ci][a] / seen[a]; })
          .forEach(function (i, r) { if (r + 1 < best[i]) best[i] = r + 1; });
      });
      var byTag = {};
      idx.slice().sort(function (a, b) { return best[a] - best[b]; }).forEach(function (i) { (byTag[tagOf[i]] = byTag[tagOf[i]] || []).push(i); });
      var before = idx.length, next = [];
      Object.keys(byTag).forEach(function (t) {
        var alive = byTag[t], target = Math.max(quota[t], Math.ceil(alive.length * (1 - cut))), kept = [];
        for (var a = 0; a < alive.length && kept.length < target; a++) {
          var ids = bank[alive[a]].ids, near = kept.some(function (j) { return bank[j].ids.filter(function (id) { return ids.indexOf(id) >= 0; }).length >= 7; });
          if (!near) kept.push(alive[a]);
        }
        next = next.concat(kept);
      });
      idx = next.sort(function (a, b) { return best[a] - best[b]; });
      rounds.push({ round: round, survivors: idx.length, ids: idx.slice() });
      if (progress) await progress(rounds[rounds.length - 1]);
      if (idx.length >= before) break;                     // nothing left to cut (every idea at its share)
    }
    var est = function (i) { return contests.map(function (c, ci) { return sum[ci][i] / seen[i]; }); };
    return { keep: idx, rounds: rounds, est: est, nights: seen, quota: quota, size: size, tagOf: tagOf };
  }

  // A frozen rule set's rules as solve() takes them, on top of BASE
  function rulesFor(set, field, own) {
    var o = Object.assign({}, BASE, set.rules);
    if (set.rules.maxOwnPctile != null) o.maxOwn = fieldOwnPctile(field, own, set.rules.maxOwnPctile);
    delete o.maxOwnPctile;
    return o;
  }

  return { CAP: CAP, SLOTS: SLOTS, MIN_PROJ: MIN_PROJ, BASE: BASE, RULESETS: RULESETS, isG: isG, isF: isF, seeded: seeded,
           gatedProj: gatedProj, seeded: seeded, fitMinutes: fitMinutes, aloneStats: aloneStats, tiers: tiers, fieldOwnPctile: fieldOwnPctile, assign: assign, solve: solve, payTable: payTable,
           simulate: simulate, builder: builder, pick: pick, fits: fits, value: value, topAlone: topAlone, diversity: diversity,
           pool: pool, poolDraw: poolDraw, simPick: simPick, rulesFor: rulesFor, passes: passes, underRules: underRules,
           CORR: CORR, TIE_SPLIT: TIE_SPLIT, nightPoints: nightPoints, placePay: placePay, pairs: pairs, cores: cores, topCore: topCore, coreLimit: coreLimit, isShare: isShare, meets: meets, shareStatus: shareStatus, shareFits: shareFits, cutPool: cutPool,
           CAND_UNIQUE: CAND_UNIQUE, CAND_RAND: CAND_RAND };
});
