// Ownership uncertainty in the sim (2026-11-28, analysis only). For one saved build, on the slate and the simulated
// field as they stood at lock, the same player draws (the page's: Proj + z x miss_dk, independent, seeded) scored
// against the field two ways:
//   fixed      today: the one field from our point ownership, every field lineup standing for (size - n) / F entries
//   uncertain  each night the field's ownership drawn around ours: each field lineup weighted by
//              exp(sum over its players of eps_p + kappa x c_L), eps_p ~ N(0, sigma of his salary tier), c_L the number
//              of our top-8 owned players in it, kappa ~ N(mu, sd) set so the field's top-8 ownership moves by
//              N(conc_mean, conc_sd) points (the measured concentration miss); all sizes x SCALE
// Then the page's pick (DKSim.pick: Max ROI for main and qualifier contests, Max coverage for flagships, each contest
// on its own, the build's caps) fills every contest the build entered, from
//   A  the kept pool under the fixed field (today's cut, today's fill model)
//   B  the kept pool under the uncertain field (re-fill)
//   C  a re-cut under the uncertain field (the kept pool and up to RECUT_EXTRA other bank lineups ranked by their
//      entries-weighted expected payout, the top |kept| kept), then the fill as B
// Output (stdout, JSON): per contest the chosen lineups (player ids) for A / B / C and each set's stated expected
// payout and top-1% coverage under the fixed and the uncertain sims.
//   node ous.js <night.json> <build.json> <params.json>
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..", "..", "..", ".."), S = require(path.join(ROOT, "dk_sim.js"));
const [nf, bf, pf] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(nf)), B = JSON.parse(fs.readFileSync(bf)), PR = JSON.parse(fs.readFileSync(pf));
const SIMS = PR.sims || 500, SCALE = PR.scale == null ? 1 : PR.scale, RECUT_EXTRA = PR.recut_extra || 2000;
const gate = B.gate || JSON.parse(fs.readFileSync(path.join(ROOT, "analysis/cbb/dk/gate.json")));
const rows = Object.entries(N.slate.players).map(([id, r]) => Object.assign({ id }, r));
const by = {}; rows.forEach(r => { by[r.id] = r; });
const seed = B.nights_seed || 1405393094;
const ctxOf = rnd => ({ rows, proj: x => S.gatedProj(x, gate), own: x => N.field.own[x.id] || 0, state: { lock: {}, excl: {}, cap: {}, floor: {} }, random: rnd });
const sup = (() => { const f = path.join(ROOT, "analysis/cbb/dk/contests_supplement.json"); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f)).contests || {} : {}; })();
const flagship = c => /pull up jumper/i.test(c.name || "") || (!/dime time|and-one|quarter jukebox|qualifier|satellite/i.test(c.name || "") && (c.size || 0) >= 100 && (c.size || 0) < 800);
const contests = Object.keys(B.portfolios || {}).map(id => N.slate.contests.find(x => String(x.id) === id && x.payouts) || sup[id])
  .filter(c => c && c.payouts).map(c => Object.assign({}, c, { n: B.portfolios[String(c.id)].length })).filter(c => c.n > 0);
if (!contests.length) { console.log(JSON.stringify({ day: B.day, draft_group: B.draft_group, contests: [] })); process.exit(0); }

// ---- the candidates: the kept pool, then up to RECUT_EXTRA other bank lineups (for the re-cut)
const kept = (B.final && B.final.length ? B.final : B.pool.map((_, i) => i));
const keptSet = new Set(kept);
const rngX = S.seeded(seed ^ 0x51ce);
const others = B.pool.map((_, i) => i).filter(i => !keptSet.has(i));
for (let i = others.length - 1; i > 0; i--) { const j = (rngX() * (i + 1)) | 0; [others[i], others[j]] = [others[j], others[i]]; }
const candIdx = kept.concat(others.slice(0, RECUT_EXTRA));
const cand = candIdx.map(i => ({ ids: B.pool[i].map(String) }));
const K = cand.length, KK = kept.length;

// ---- players, in the page's fixed order
const ix = {}, mean = [], err = [], tier = [];
rows.forEach(r => { ix[r.id] = mean.length; const m = r.status === "Out" ? 0 : S.gatedProj(r, gate); mean.push(m); err.push(r.miss_dk || 0.35 * m);
  const s = r.salary || 0; tier.push(s < 5000 ? PR.sigma_lt5 : s < 7000 ? PR.sigma_5to7 : PR.sigma_7plus); });
const idx = id => { if (ix[id] == null) { ix[id] = mean.length; mean.push(0); err.push(0); tier.push(PR.sigma_lt5); } return ix[id]; };
const candIx = cand.map(L => L.ids.map(idx));
const field = N.field.field, F = field.length;
const fieldIx = field.map(L => L.map(idx));
const P = mean.length, z = N.z;
// our top 8 by projected ownership, and c_L
const own = N.field.own || {};
const top8 = Object.keys(own).sort((a, b) => own[b] - own[a]).slice(0, 8).map(idx);
const isTop = new Uint8Array(P); top8.forEach(p => { isTop[p] = 1; });
const cL = fieldIx.map(L => L.reduce((t, p) => t + isTop[p], 0));
// kappa's scale: the field's top-8 ownership (points) as a function of kappa, its slope at 0
const top8Own = k => { let W = 0; const hold = new Float64Array(P); for (let f = 0; f < F; f++) { const w = Math.exp(k * cL[f]); W += w; fieldIx[f].forEach(p => { hold[p] += w; }); }
  return top8.reduce((t, p) => t + 100 * hold[p] / W, 0); };
const slope = (top8Own(0.05) - top8Own(0)) / 0.05;
const kMu = SCALE * PR.conc_mean / slope, kSd = SCALE * PR.conc_sd / slope;
// Tempering: independent per-player noise at the measured size (log SD 0.63-0.89) tilts a 1,000-lineup field so hard
// that a handful of lineups carry it (effective size F x exp(-sum of the lineup's variances)); the noise is scaled down
// (TAU) until the expected effective field size is F / 3, and the per-player noise actually carried is reported.
const sigL = fieldIx.reduce((t, L) => t + L.reduce((u, p) => u + Math.pow(SCALE * tier[p], 2), 0), 0) / F;
const TAU = PR.kappa_only ? 0 : Math.min(1, Math.sqrt(Math.log(3) / Math.max(1e-9, sigL)));

let essT = 0; const top8T = [], lr = [];
const base0 = (() => { const h = new Float64Array(P); for (let f = 0; f < F; f++) fieldIx[f].forEach(p => { h[p] += 100 / F; }); return h; })();
const chalkP = [...Array(P).keys()].filter(p => base0[p] >= 1);
function normal(r) { const u = 1 - r(), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
// one sim per contest: cs (lineup scores), fa (field entries above), on the SAME player draws for both field modes
function simPair(contest) {
  const size = contest.size || 0, n = contest.n, wEach = Math.max(0, size - n);
  const rnd = S.seeded((seed ^ Math.imul(+contest.id || 0, 2654435761)) >>> 0), rU = S.seeded((seed ^ 0xa11ce ^ (+contest.id || 0)) >>> 0);
  const csA = new Float32Array(K * SIMS), faA = new Float32Array(K * SIMS), faB = new Float32Array(K * SIMS);
  const pts = new Float32Array(P), fsc = new Float64Array(F), eps = new Float64Array(P), lw = new Float64Array(F), order = new Uint32Array(F);
  const sortedS = new Float64Array(F), cumW = new Float64Array(F + 1);
  for (let s = 0; s < SIMS; s++) {
    for (let p = 0; p < P; p++) pts[p] = Math.max(0, mean[p] + z[(rnd() * z.length) | 0] * err[p]);
    for (let f = 0; f < F; f++) { let t = 0; const L = fieldIx[f]; for (let j = 0; j < 8; j++) t += pts[L[j]]; fsc[f] = t; order[f] = f; }
    // the uncertain field's weights this night
    for (let p = 0; p < P; p++) eps[p] = TAU * SCALE * tier[p] * normal(rU);
    const kap = kMu + kSd * normal(rU);
    let mx = -Infinity;
    for (let f = 0; f < F; f++) { let t = kap * cL[f]; const L = fieldIx[f]; for (let j = 0; j < 8; j++) t += eps[L[j]]; lw[f] = t; if (t > mx) mx = t; }
    order.sort((a, b) => fsc[a] - fsc[b]);                         // ascending
    let W = 0;
    for (let i = 0; i < F; i++) sortedS[i] = fsc[order[i]];
    cumW[F] = 0;
    for (let i = F - 1; i >= 0; i--) { const w = Math.exp(lw[order[i]] - mx); cumW[i] = cumW[i + 1] + w; }
    W = cumW[0];
    if (contest === contests[0]) {
      let W2 = 0; for (let f = 0; f < F; f++) W2 += Math.exp(2 * (lw[f] - mx));
      essT += W * W / W2 / SIMS;
      const hold = new Float64Array(P); for (let f = 0; f < F; f++) { const w = Math.exp(lw[f] - mx) / W; fieldIx[f].forEach(p => { hold[p] += w; }); }
      let t8 = 0; top8.forEach(p => { t8 += 100 * hold[p]; }); top8T.push(t8);
      for (const p of chalkP) { const o0 = base0[p], o1 = 100 * hold[p]; if (o0 >= 1) { lr.push(Math.log((o1 + 1) / (o0 + 1))); } }
    }
    for (let k = 0; k < K; k++) {
      let t2 = 0; const L2 = candIx[k]; for (let j = 0; j < 8; j++) t2 += pts[L2[j]];
      let lo = 0, hi = F; const t2e = t2 + 1e-6;
      while (lo < hi) { const mid = (lo + hi) >> 1; if (sortedS[mid] <= t2e) lo = mid + 1; else hi = mid; }
      csA[k * SIMS + s] = t2; faA[k * SIMS + s] = (F - lo) * wEach / F; faB[k * SIMS + s] = cumW[lo] / W * wEach;
    }
  }
  const mk = fa => ({ cs: csA, fa, K, S: SIMS, cut: { win: 0, top10: 0, cash: 0 }, quality: new Float32Array(K), core: new Float32Array(K), rate: 0,
                      dup: new Float32Array(K), tie: new Float32Array(K), tieSplit: false });
  return { A: mk(faA), B: mk(faB) };
}
const evOf = (sim, contest) => { const pay = (() => { const t = [0]; (contest.payouts || []).forEach(p => { for (let i = p[0]; i <= p[1]; i++) t[i] = p[2]; }); return t; })();
  const e = new Float64Array(sim.K); for (let k = 0; k < sim.K; k++) { let t = 0; for (let s = 0; s < sim.S; s++) { const q = Math.round(sim.fa[k * sim.S + s] + 1); t += q >= 1 && q < pay.length ? pay[q] || 0 : 0; } e[k] = t / sim.S; } return e; };
const sims = contests.map(simPair);
const pk = B.pick || { maxExpo: 60, minUnique: 2, maxCore: 15 };
const opts = (c, n) => ({ n, maxExpo: Math.max(pk.maxExpo / 100, 1 / n), minUnique: pk.minUnique || 1, conds: [], maxCore: (pk.maxCore || 0) / 100, objective: flagship(c) ? "cover" : "roi" });
const cx = ctxOf(S.seeded(1));
const restrict = (sim, keep) => {          // a sim over a subset of candidates (indexes into cand)
  const out = { K: keep.length, S: sim.S, cs: new Float32Array(keep.length * sim.S), fa: new Float32Array(keep.length * sim.S), cut: sim.cut,
                quality: new Float32Array(keep.length), core: new Float32Array(keep.length), rate: 0, dup: new Float32Array(keep.length), tie: new Float32Array(keep.length), tieSplit: false };
  keep.forEach((k, i) => { out.cs.set(sim.cs.subarray(k * sim.S, (k + 1) * sim.S), i * sim.S); out.fa.set(sim.fa.subarray(k * sim.S, (k + 1) * sim.S), i * sim.S); });
  return out;
};
const keptI = [...Array(KK).keys()];
// the re-cut under the uncertain field: entries-weighted expected payout per lineup over the night's contests
const wev = new Float64Array(K);
contests.forEach((c, ci) => { const e = evOf(sims[ci].B, c); for (let k = 0; k < K; k++) wev[k] += c.n * e[k]; });
const recut = [...Array(K).keys()].sort((a, b) => wev[b] - wev[a]).slice(0, KK).sort((a, b) => a - b);
const recutChanged = recut.filter(k => k >= KK).length;
const sd = v => { const m = v.reduce((a, b) => a + b, 0) / v.length; return Math.sqrt(v.reduce((a, b) => a + (b - m) * (b - m), 0) / v.length); };
const out = { day: B.day, draft_group: B.draft_group, sims: SIMS, scale: SCALE, kappa_only: !!PR.kappa_only, kappa: { mu: kMu, sd: kSd, slope_pts_per_unit: slope }, tau: TAU,
  achieved: { ess: essT, field: F, top8_base: top8Own(0), top8_mean: top8T.reduce((a, b) => a + b, 0) / top8T.length, top8_sd: sd(top8T), player_log_sd: sd(lr) },
  kept: KK, recut_new: recutChanged, contests: [] };
contests.forEach((c, ci) => {
  const variants = { A: { sim: restrict(sims[ci].A, keptI), set: keptI }, B: { sim: restrict(sims[ci].B, keptI), set: keptI }, C: { sim: restrict(sims[ci].B, recut), set: recut } };
  const row = { id: String(c.id), name: c.name, size: c.size, fee: c.entry_fee, n: c.n, flagship: flagship(c), sets: {} };
  for (const [v, x] of Object.entries(variants)) {
    const ch = S.pick(cx, opts(c, c.n), x.set.map(k => cand[k]), x.sim, c, c.n).chosen;
    const glob = ch.map(i => x.set[i]);
    const stat = sim => { const b = S.builder(restrict(sim, glob), c); b.set([...Array(glob.length).keys()]); return { ev: b.total(), top1: b.coverage().top1 }; };
    row.sets[v] = { lineups: glob.map(k => cand[k].ids), stated_fixed: stat(sims[ci].A), stated_uncertain: stat(sims[ci].B) };
  }
  out.contests.push(row);
});
console.log(JSON.stringify(out));
