/* Late-swap calibration (2026-11-24, the coordinator's request; analysis only): the stated cash %, top-1 % and expected
 * payout the Swap step shows for an entry, rebuilt at each tip break of a saved night with the page's own machinery
 * (dk_sim.js DKSim.nightPoints for the nights, dk_swap.js hiddenMass / hiddenOwn / fieldDraw / board, the field's chalk
 * fitted as dk.html swapChalkFit), for our entries and a sample of field entries, with the simulated spread of each
 * entry's remaining points and of the contest's cash line. scripts/dk_lateswap_calib.py writes IN and reads OUT.
 *
 *   node scripts/dk_lateswap_calib.js IN.json OUT.json
 *   IN:  {rows, cards: {id: card}, own, z, S, seed, variants: [{name, s, corr}], contests: [{id, table, fee, entries:
 *        [{slots: [[slot, id] x 8], ours, sample, rank, points}]}], breaks: [{k, at, started: [ids], base, left}]}
 *   OUT: [{variant, cid, k, e, kind, top1, cash, ev, now, sim_mean, sim_sd, pit, rank, points, cl_pit, cl_mean, cl_sd}]
 */
const fs = require("fs"), path = require("path");
const DKSim = require(path.join(__dirname, "..", "dk_sim.js"));
const DKSwap = require(path.join(__dirname, "..", "dk_swap.js"));
const [inp, outp] = process.argv.slice(2);
const a = JSON.parse(fs.readFileSync(inp, "utf8"));
const by = a.cards, ids = a.rows.map(r => r.id), col = {};
ids.forEach((id, j) => { col[id] = j; });
const FIT_MIN = 5;     // dk.html SWAP_FIT_MIN

// the nights per variant: the page's draw (S nights, projection + expected miss x z, independent draws by default),
// s scaling each player's deviation (the variance multiplier) and corr the team / game draws (ctx.corr)
const NIGHTS = {};
a.variants.forEach(v => {
  const ctx = { rows: a.rows.map(r => Object.assign({}, r)), proj: r => r.proj || 0, random: DKSim.seeded(a.seed), corr: v.corr || undefined };
  const n = [];
  for (let s = 0; s < a.S; s++) { const p = DKSim.nightPoints(ctx, a.z, v.s); n.push(ids.map(id => p[id] || 0)); }
  NIGHTS[v.name] = n;
});

function chalkFit(entries, own) {       // dk.html swapChalkFit, on ids (the saved standings are matched to cards already)
  const cnt = {}; let tot = 0;
  entries.forEach(e => e.lu.forEach(x => { if (x[1]) { cnt[x[1]] = (cnt[x[1]] || 0) + 1; tot++; } }));
  const pairs = Object.keys(cnt).filter(id => (own[id] || 0) > 0).map(id => ({ real: cnt[id], o: own[id] }));
  if (pairs.length < FIT_MIN || !tot) return 1;
  const rs = pairs.reduce((t, x) => t + x.real, 0);
  const err = pw => { const ps = pairs.reduce((t, x) => t + Math.pow(x.o, pw), 0); return pairs.reduce((t, x) => t + Math.abs(x.real / rs - Math.pow(x.o, pw) / ps), 0); };
  return err(2) < err(1) ? 2 : 1;
}

const out = [];
a.contests.forEach(c => {
  const N = c.entries.length;
  const paid = Object.keys(c.table).length ? Math.max(...Object.keys(c.table).map(Number)) : Math.max(1, Math.floor(0.2 * N));
  const byRank = c.entries.map(e => e.points).sort((x, y) => y - x);
  const realLine = byRank[Math.min(paid, N) - 1];                       // the real cash line: the paid place's points
  a.breaks.forEach(b => {
    const st = {}; b.started.forEach(id => { st[id] = 1; });
    const at = (s, id, NT) => { const j = col[id]; return j == null ? 0 : NT[s][j]; };
    // the standings at this break, as the file would read: started games' players shown, the rest hidden
    const ent = c.entries.map(e => ({ lu: e.slots.map(x => [x[0], st[x[1]] ? x[1] : null]) }));
    const mass = DKSwap.hiddenMass(ent.map(e => ({ slots: e.lu.map(x => ({ slot: x[0], name: x[1] })) })));
    const revGames = {}; ent.forEach(e => e.lu.forEach(x => { if (x[1]) revGames[by[x[1]].event || by[x[1]].game] = 1; }));
    const rows = Object.keys(by).map(id => Object.assign({ id }, by[id]));
    const fieldPool = rows.filter(r => !revGames[r.event || r.game] && r.status !== "Out");
    const chalk = chalkFit(ent, a.own);
    const w = DKSwap.hiddenOwn(a.own, fieldPool.map(r => r.id), mass);
    if (chalk !== 1) Object.keys(w).forEach(id => { w[id] = Math.pow(w[id], chalk); });
    // two scorings: as the page (ours known, every other entry drawn) and the field sample (also known)
    [["ours", e => c.entries[e].ours], ["field", e => c.entries[e].ours || c.entries[e].sample]].forEach(([kind, known]) => {
      const random = DKSim.seeded(20261121 + 97 * b.k), lineups = [], mine = [], draws = {};
      c.entries.forEach((e, i) => {
        if (known(i)) { mine.push(i); lineups.push(e.slots.map(x => [x[0], x[1]])); return; }
        const lu = ent[i].lu; lineups.push(lu);
        const open = lu.filter(x => !x[1]).map(x => x[0]);
        if (!open.length) return;
        const left = DKSwap.CAP - lu.reduce((t, x) => t + (x[1] ? by[x[1]].salary || 0 : 0), 0), d = [];
        for (let m = 0; m < 6; m++) { const x = DKSwap.fieldDraw(random, open, left, fieldPool, w, {}); if (x) d.push(x); }
        draws[i] = d;
      });
      const mineSet = {}; mine.forEach(e => { mineSet[e] = 1; });
      const want = c.entries.map((e, i) => i).filter(i => kind === "ours" ? c.entries[i].ours : c.entries[i].sample);
      if (!want.length) return;
      a.variants.forEach(v => {
        const NT = NIGHTS[v.name];
        const B = DKSwap.board({ ids, nights: NT, started: st, base: b.base, left: b.left, lineups, mine, draws, table: c.table });
        // the simulated cash line per night: a second pass over the board's totals is not exposed, so rebuilt here the
        // same way (started at base + rest x share left, hidden full; a field entry's hidden part cycled by night)
        const lines = [];
        if (kind === "ours") {
          for (let s = 0; s < a.S; s++) {
            const tot = new Float64Array(N);
            lineups.forEach((lu, e) => {
              let x = 0;
              lu.forEach(q => { if (q[1] && st[q[1]]) x += (b.base[q[1]] || 0) + at(s, q[1], NT) * (b.left[q[1]] != null ? b.left[q[1]] : 1); });
              const isMine = mineSet[e], opts = isMine || !(draws[e] && draws[e].length) ? [lu.filter(q => q[1] && !st[q[1]]).map(q => q[1])] : draws[e];
              opts[s % opts.length].forEach(id => { x += st[id] && !isMine ? (b.base[id] || 0) + at(s, id, NT) * (b.left[id] != null ? b.left[id] : 1) : at(s, id, NT); });
              tot[e] = x;
            });
            const srt = Array.from(tot).sort((x, y) => y - x); lines.push(srt[Math.min(paid, N) - 1]);
          }
        }
        const lm = lines.length ? lines.reduce((t, x) => t + x, 0) / lines.length : null;
        const lsd = lines.length ? Math.sqrt(lines.reduce((t, x) => t + (x - lm) * (x - lm), 0) / lines.length) : null;
        const lpit = lines.length ? (lines.filter(x => x < realLine).length + 0.5 * lines.filter(x => x === realLine).length) / lines.length : null;
        want.forEach(e => {
          const lu = c.entries[e].slots, idsE = lu.map(x => x[1]), sc = B.score(e, idsE);
          const now = idsE.reduce((t, id) => t + (st[id] ? b.base[id] || 0 : 0), 0), tots = [];
          for (let s = 0; s < a.S; s++) {
            let x = 0; idsE.forEach(id => { x += st[id] ? (b.base[id] || 0) + at(s, id, NT) * (b.left[id] != null ? b.left[id] : 1) : at(s, id, NT); });
            tots.push(x);
          }
          const m = tots.reduce((t, x) => t + x, 0) / a.S, sd = Math.sqrt(tots.reduce((t, x) => t + (x - m) * (x - m), 0) / a.S), real = c.entries[e].points;
          const pit = (tots.filter(x => x < real).length + 0.5 * tots.filter(x => x === real).length) / a.S;
          out.push({ variant: v.name, cid: c.id, k: b.k, e, kind, chalk, top1: sc.top1, cash: sc.cash, ev: sc.ev, now: Math.round(100 * now) / 100,
                     sim_mean: m, sim_sd: sd, pit, rank: c.entries[e].rank, points: real, cl_pit: lpit, cl_mean: lm, cl_sd: lsd, real_line: realLine });
        });
      });
    });
  });
});
fs.writeFileSync(outp, JSON.stringify(out));
