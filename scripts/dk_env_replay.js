// Game factor replay (2026-11-19, for the operator's decision; nothing adopted): the slate scan and the cut on a saved
// night valued twice on the same nights, with the sim's correlation off (today) and with a game factor b on each
// team's top 3 by projected minutes only (scripts/cbb_env_study.py in battle-royale-research: on 2025-26 those
// players' opponents correlate +0.015, b = sqrt = 0.12; teammates and bench players don't). The draws are the same
// for both (drawn once, at today's settings); only the valuation changes.
//
//   Scan: the page's batches (plain 5 x PER, each team 3+ / 4+ and game 3+ / 4+ / 5+ stack PER, each player at 15+
//   minutes PERP), each lineup alone in every contest the build entered, entries-weighted; gains in top-1% rate over
//   the plain batch, Read by the page's noise test. Reported: rank correlation of the gains between the two settings,
//   the top stacks each way, and how many Reads change.
//   Cut: the build's whole pool valued both ways; the top len(final) by value kept (an approximation of the page's cut:
//   no per-idea split or spread caps); the overlap, tier A (DKSim.tiers) and, where the night's standings exist, the
//   real top-10% and top-1% rates of the lineups the factor brings in and drops (in the night's main contest).
//
//   node scripts/dk_env_replay.js <night.json> <build.json> [--b 0.12] [--per 60] [--perp 40] [--sims 2000]
const fs = require("fs"), path = require("path"), vm = require("vm");
const ROOT = path.join(__dirname, ".."), S = require(path.join(ROOT, "dk_sim.js"));
const sb = { self: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, "vendor", "lp_solver.js"), "utf8"), sb);
const [nf, bf] = process.argv.slice(2);
const opt = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? +process.argv[i + 1] : d; };
const B0 = opt("b", 0.12), PER = opt("per", 60), PERP = opt("perp", 40), SIMS = opt("sims", 2000);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf)), gate = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const DK = path.join(ROOT, "analysis/cbb/dk");
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
// the pool's rules as the page has them tonight: deep bench and punts out
const gpMax = {}, outTeam = {};
rows.forEach(r => { gpMax[r.team] = Math.max(gpMax[r.team] || 0, r.gp || 0); if (r.status === "Out") outTeam[r.team] = 1; });
rows.forEach(r => {
  const deep = (r.min || 0) < 12 && (r.min_avg == null || r.min_avg < 8 || (r.gp || 0) < gpMax[r.team] / 2);
  const punt = (r.min || 0) < 15 && !(outTeam[r.team] && r.min_avg != null && r.min > r.min_avg);
  r.deepOut = r.status !== "Out" && (deep || punt);
});
// each team's top 3 by projected minutes (not Out)
const top3 = {}, byTeam = {};
rows.filter(r => r.status !== "Out").forEach(r => (byTeam[r.team] = byTeam[r.team] || []).push(r));
Object.values(byTeam).forEach(L => L.sort((a, b) => (b.min || 0) - (a.min || 0)).slice(0, 3).forEach(r => { top3[r.id] = 1; }));
const OFF = { team: 0, game: 0 }, ON = { team: 0, game: B0, gameIds: top3 };
// contests: the build's, with the owner's supplement where the lobby file missed the payouts
const supF = path.join(DK, "contests_supplement.json"), sup = fs.existsSync(supF) ? JSON.parse(fs.readFileSync(supF)).contests || {} : {};
Object.keys(B.portfolios || {}).forEach(id => {
  if (sup[id] && !N.slate.contests.some(c => String(c.id) === id && c.payouts)) N.slate.contests = N.slate.contests.filter(c => String(c.id) !== id).concat([sup[id]]);
});
const cs = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(c => String(c.id) === id)).filter(c => c && c.payouts)
  .map(c => Object.assign({}, c, { n: Math.min(B.portfolios[String(c.id)].length, c.max_per_user || 1) }));
const seed = B.nights_seed || 1405393094;
const ctxOf = (rand, corr) => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, solver: sb.self.solver, random: rand,
                                 corr, state: { lock: {}, excl: {}, cap: {}, floor: {} } });

// each lineup alone in every contest, entries-weighted: value, top-1% rate, and the top-1% rate on odd / even nights
function value(pool, corr, fresh) {      // fresh: other nights (the same setting again, for the noise baseline)
  const K = pool.length, v = new Float64Array(K), t1 = new Float64Array(K), o1 = new Float64Array(K), e1 = new Float64Array(K), odd = new Float64Array(K), even = new Float64Array(K);
  let w = 0;
  for (const c of cs) {
    const T1 = Math.max(1, Math.ceil(0.01 * (c.size || 0)));
    for (let c0 = 0; c0 < K; c0 += 2000) {
      const part = pool.slice(c0, c0 + 2000);
      const sim = S.simulate(ctxOf(S.seeded((((seed ^ Math.imul(+c.id || 0, 2654435761)) >>> 0) + (fresh ? 99991 : 0)) >>> 0), corr), part, N.field.field, N.z, c, c.n, SIMS), st = S.aloneStats(sim, c);
      for (let j = 0; j < part.length; j++) {
        const k = c0 + j;
        v[k] += c.n * (st.odd[j] + st.even[j]) / 2; odd[k] += c.n * st.odd[j]; even[k] += c.n * st.even[j]; t1[k] += c.n * st.top1[j];
        let ho = 0, he = 0;
        for (let s = 0; s < SIMS; s++) if (Math.round(1 + sim.fa[j * SIMS + s]) <= T1) { if (s % 2) ho++; else he++; }
        o1[k] += c.n * ho / Math.floor(SIMS / 2); e1[k] += c.n * he / Math.ceil(SIMS / 2);
      }
    }
    w += c.n;
  }
  const f = a => Array.from(a, x => x / w);
  return { v: f(v), t1: f(t1), o1: f(o1), e1: f(e1), odd: f(odd), even: f(even) };
}

function batches() {
  const live = rows.filter(r => r.status !== "Out" && !r.deepOut), teams = {}, games = {}, out = [{ key: "plain", kind: "plain", conds: [] }];
  live.forEach(r => { (teams[r.team] = teams[r.team] || []).push(r.id); if (r.game) (games[r.game] = games[r.game] || []).push(r.id); });
  Object.keys(teams).sort().forEach(t => [3, 4].forEach(n => out.push({ key: t + " " + n + "+", kind: "team", conds: [{ type: "min", ids: teams[t], n }] })));
  Object.keys(games).sort().forEach(g => {
    const two = g.split("@"); if (two.length !== 2 || !teams[two[0]] || !teams[two[1]]) return;
    [3, 4, 5].forEach(n => out.push({ key: g + " " + n + "+", kind: "game", conds: [{ type: "min", ids: games[g], n }, { type: "min", ids: teams[two[0]], n: 1 }, { type: "min", ids: teams[two[1]], n: 1 }] }));
  });
  live.filter(r => (r.min || 0) >= 15).forEach(r => out.push({ key: r.name, kind: "player", id: r.id, top3: !!top3[r.id], conds: [{ type: "min", ids: [r.id], n: 1 }] }));
  return out;
}
function reads(rowsB, val, plain) {
  const gain = rowsB.map(b => mean(val.t1, b.idx) - mean(val.t1, plain.idx));
  const dd = rowsB.map(b => (mean(val.o1, b.idx) - mean(val.o1, plain.idx)) - (mean(val.e1, b.idx) - mean(val.e1, plain.idx)));
  const m = dd.reduce((a, x) => a + x, 0) / dd.length, sig = Math.sqrt(dd.reduce((a, x) => a + (x - m) * (x - m), 0) / Math.max(1, dd.length - 1)) / 2, bar = 2 * Math.SQRT2 * sig;
  return { gain, bar, read: gain.map(g => g > bar ? "strong" : g < -bar ? "weak" : "even") };
}
const mean = (a, ix) => ix.reduce((t, k) => t + a[k], 0) / Math.max(1, ix.length);
function spearman(a, b) {
  const rk = x => { const o = x.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]), r = new Array(x.length); o.forEach(([, i], j) => { r[i] = j; }); return r; };
  const ra = rk(a), rb = rk(b), n = a.length, ma = (n - 1) / 2;
  let s = 0, sa = 0, sb2 = 0; for (let i = 0; i < n; i++) { s += (ra[i] - ma) * (rb[i] - ma); sa += (ra[i] - ma) ** 2; sb2 += (rb[i] - ma) ** 2; }
  return s / Math.sqrt(sa * sb2);
}

// real points and the main contest's lines, where the standings exist
function realLines() {
  const sf = path.join(DK, "standings", `contest-standings-${N.cid}.csv`), af = path.join(DK, `${N.date}_${N.g}.csv`);
  if (!fs.existsSync(sf) || !fs.existsSync(af)) return null;
  const head = fs.readFileSync(af, "utf8").split("\n")[0].split(","), iId = head.indexOf("dk_id"), iAct = head.indexOf("actual_dk"), act = {};
  fs.readFileSync(af, "utf8").split("\n").slice(1).forEach(l => { const v = l.split(","); if (v[iId]) act[v[iId]] = +v[iAct] || 0; });
  const pts = fs.readFileSync(sf, "utf8").split("\n").slice(1).map(l => l.split(",")).filter(v => v[1] && v[4] !== undefined && v[4] !== "").map(v => +v[4]).sort((a, b) => b - a);
  return { act, t10: pts[Math.ceil(0.1 * pts.length) - 1], t1: pts[Math.ceil(0.01 * pts.length) - 1] };
}

(async () => {
  const t0 = Date.now(), out = { night: N.date, draft_group: N.g, contests: cs.map(c => c.name + " x" + c.n), b: B0, top3_players: Object.keys(top3).length };
  // --- the scan ---
  const bt = batches(), pool = [], at = {};
  for (let i = 0; i < bt.length; i++) {
    const b = bt[i], cx = ctxOf(S.seeded(7919 * (i + 1) + (+N.g || 0)), OFF);
    const o = { n: 1, maxExpo: 1, minUnique: 1, z: N.z, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, stackBoth: false, maxOwn: null, lowN: 0, lowPct: 10, conds: b.conds, nightS: 0.35 };
    const res = await S.pool(cx, o, b.kind === "plain" ? 5 * PER : b.kind === "player" ? PERP : PER);
    b.idx = res.lineups.map(L => { const k = L.ids.slice().sort().join(","); if (at[k] == null) { at[k] = pool.length; pool.push({ ids: L.ids }); } return at[k]; });
  }
  out.scan_draw_s = Math.round((Date.now() - t0) / 1000);
  const plain = bt[0], stk = bt.filter(b => b.kind === "team" || b.kind === "game"), pls = bt.filter(b => b.kind === "player");
  const v0 = value(pool, OFF), v1 = value(pool, ON), vf = value(pool, OFF, true);
  for (const [name, L] of [["stacks", stk], ["players", pls]]) {
    const r0 = reads(L, v0, plain), r1 = reads(L, v1, plain), rf = reads(L, vf, plain), top = (r, n) => r.gain.map((g, i) => [g, i]).sort((a, b) => b[0] - a[0]).slice(0, n).map(([g, i]) => L[i].key + " " + (100 * g).toFixed(2));
    const o = { n: L.length, rank_corr: +spearman(r0.gain, r1.gain).toFixed(3), rank_corr_noise: +spearman(r0.gain, rf.gain).toFixed(3),
                reads_changed_noise: r0.read.filter((x, i) => x !== rf.read[i]).length, bar_off: +(100 * r0.bar).toFixed(3), bar_on: +(100 * r1.bar).toFixed(3),
                reads_changed: r0.read.filter((x, i) => x !== r1.read[i]).length, strong_off: r0.read.filter(x => x === "strong").length, strong_on: r1.read.filter(x => x === "strong").length,
                top5_off: top(r0, 5), top5_on: top(r1, 5) };
    if (name === "stacks") ["team", "game"].forEach(k => {
      const ix = L.map((b, i) => i).filter(i => L[i].kind === k);
      o["mean_gain_change_" + k] = +(100 * ix.reduce((t, i) => t + r1.gain[i] - r0.gain[i], 0) / ix.length).toFixed(3);
    });
    else [true, false].forEach(k => {
      const ix = L.map((b, i) => i).filter(i => L[i].top3 === k);
      o["mean_gain_change_" + (k ? "top3" : "others")] = +(100 * ix.reduce((t, i) => t + r1.gain[i] - r0.gain[i], 0) / Math.max(1, ix.length)).toFixed(3);
    });
    out["scan_" + name] = o;
  }
  // --- the cut ---
  const P = B.pool.map(ids => ({ ids: ids.map(String) })), keepN = (B.final || []).length || 1500;
  const c0 = value(P, OFF), c1 = value(P, ON), cf = value(P, OFF, true);
  const keep = val => val.v.map((x, i) => [x, i]).sort((a, b) => b[0] - a[0]).slice(0, keepN).map(([, i]) => i);
  const k0 = keep(c0), k1 = keep(c1), s0 = new Set(k0), s1 = new Set(k1), inn = k1.filter(i => !s0.has(i)), outk = k0.filter(i => !s1.has(i));
  const tierA = (val, k) => S.tiers(k.map(i => val.v[i]), k.map(i => val.odd[i]), k.map(i => val.even[i])).tier.filter(t => t === "A").length;
  const stackOf = ids => { const g = {}; ids.forEach(id => { const r = N.slate.players[id]; if (r && top3[id]) g[r.game] = (g[r.game] || 0) + 1; }); return Math.max(0, ...Object.values(g)); };
  const kf = new Set(keep(cf));
  out.cut = { pool: P.length, kept: keepN, overlap: +(k0.filter(i => s1.has(i)).length / keepN).toFixed(3), overlap_noise: +(k0.filter(i => kf.has(i)).length / keepN).toFixed(3), brought_in: inn.length,
              tierA_off: tierA(c0, k0), tierA_on: tierA(c1, k1),
              mean_top3_same_game_in: +(inn.reduce((t, i) => t + stackOf(P[i].ids), 0) / Math.max(1, inn.length)).toFixed(2),
              mean_top3_same_game_dropped: +(outk.reduce((t, i) => t + stackOf(P[i].ids), 0) / Math.max(1, outk.length)).toFixed(2) };
  const R = realLines();
  if (R) {
    const rate = (ix, line) => ix.length ? +(100 * ix.filter(i => P[i].ids.reduce((t, id) => t + (R.act[id] || 0), 0) >= line).length / ix.length).toFixed(1) : null;
    out.cut.real = { kept_off_top10: rate(k0, R.t10), kept_on_top10: rate(k1, R.t10), kept_off_top1: rate(k0, R.t1), kept_on_top1: rate(k1, R.t1),
                     brought_in_top10: rate(inn, R.t10), dropped_top10: rate(outk, R.t10), brought_in_top1: rate(inn, R.t1), dropped_top1: rate(outk, R.t1) };
  }
  out.seconds = Math.round((Date.now() - t0) / 1000);
  console.log(JSON.stringify(out, null, 1));
})();
