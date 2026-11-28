// Step 2 grading: the sim's cut lines (dk_sim.js simulate, the shadow's own call: N = BASE.n, BASE.sims nights, our
// projection through the gate) for PREVIOUS (the field saved at lock) and the candidate field of the contest's type,
// with the same seeded nights; and, as context, our entered lineups' sim expected payout and top-1% under each field.
//   node grade.js <data dir> <out json> [_cand_r4.json]
const fs = require("fs"), path = require("path");
const S = require(path.join(__dirname, "..", "..", "..", "..", "dk_sim.js"));
const [dir, out, suffix] = process.argv.slice(2);             // suffix: _cand.json (R1-R3, default) or _cand_r4.json
const res = [];
for (const f of fs.readdirSync(dir).filter(f => /^20\d\d-\d\d-\d\d_\d+\.json$/.test(f)).sort()) {
  const s = JSON.parse(fs.readFileSync(path.join(dir, f)));
  const cf = path.join(dir, f.replace(".json", suffix || "_cand.json"));
  if (!fs.existsSync(cf)) continue;
  const C = JSON.parse(fs.readFileSync(cf));
  const rows = Object.entries(s.players).map(([id, r]) => Object.assign({ id }, r));
  for (const c of s.contests) {
    if (!c.payouts || !c.size) continue;
    const contest = { id: c.id, size: c.size, payouts: c.payouts, entry_fee: c.fee };
    const cand = (c.mine || []).map(m => ({ ids: m.ids.map(String) }));
    const one = (field) => {
      const ctx = { rows, proj: r => (r.fp_gate != null ? r.fp_gate * (r.status === "Questionable" && s.gate && s.gate.questionable && s.gate.questionable.factor != null && !r.zero_gp ? s.gate.questionable.factor : 1) : S.gatedProj(r, s.gate)), random: S.seeded(+c.id % 2147483647) };
      const sim = S.simulate(ctx, cand, field.map(L => L.map(String)), s.z, contest, S.BASE.n, S.BASE.sims);
      const o = { cash: sim.cut.cash, top10: sim.cut.top10, win: sim.cut.win };
      if (cand.length) {
        const T1 = Math.max(1, Math.ceil(0.01 * contest.size));
        let t1 = 0;
        for (let k = 0; k < sim.K; k++) for (let n = 0; n < sim.S; n++) if (1 + sim.fa[k * sim.S + n] <= T1) t1++;
        o.mine_expected = S.value(sim, contest, cand.map((_, k) => k));
        o.mine_top1 = t1 / (sim.K * sim.S);
        o.mine_dups = Array.from(sim.dup).reduce((a, b) => a + b, 0) / sim.K;
      }
      return o;
    };
    const prev = one(s.prev_field), cnd = one(C.fields[c.type] || C.fields.main);
    const T1r = Math.max(1, Math.ceil(0.01 * c.entries));
    res.push({ slate: f.slice(0, -5), date: s.date, cid: c.id, type: c.type, entries: c.entries, size: c.size, fee: c.fee,
               shadow: c.id === s.shadow_contest, sim_cash_logged: c.sim_cash_logged, sim_top10_logged: c.sim_top10_logged,
               field_cash: c.field_cash, field_top10: c.field_top10, field_avg: c.field_avg, prev, cand: cnd,
               mine_n: cand.length, mine_won: (c.mine || []).reduce((a, m) => a + m.won, 0),
               mine_top1_real: cand.length ? (c.mine || []).filter(m => m.rank <= T1r).length / cand.length : null });
  }
  console.log("graded", f);
}
fs.writeFileSync(out, JSON.stringify(res, null, 0));
