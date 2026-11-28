# DraftKings CBB: ownership uncertainty in the sim (2026-11-28)

The operator asked for this study as the anchor experiment for the walkthrough. It is analysis only, and **the HOLD stands.** Tags follow rule 5 ([process.md](process.md)).

- **Code and outputs:** [own_uncertainty_sim_2026-11-28/](own_uncertainty_sim_2026-11-28/)
  - `ous.js`: the sim and the picks;
  - `ous.py`: the driver and the grade;
  - `sizes.json`: the measured uncertainty sizes;
  - `ous.out`: the results;
  - `picks.json`: every pick.
- **Data:** 14 saved builds with a lock-time slate and simulated field on the mirror, and graded standings. That's 68 entered contests: 31 flagship, 31 main, 6 qualifier/small.
- **Sims:** 500 nights per contest, on the page's own player draws (Proj + z × miss, seeded).

**The premise.** Our ownership misses the chalk (chalk-band MAE 10.5 on 100+ entry contests, after the 11-28 grade fix) and the field's concentration (its top 8 sum **+22.6 ± 7.1** over ours; per-slate SD 28.4). The sim builds one field from our point ownership, and our picks exploit that exact field. Is that why our entries finish 7.5 points under their simulated mean?

## Verdict

**No.**

1. **An uncertain field doesn't improve our picks overall:** **−1.92 ± 2.08 finish pct (7 of 14 slates ahead), +$0.38 ± $12.23 per lineup (4 of 14).** **NOISE.**
   - **Main contests** pick a little better under it, at every size tested: +1.3 to +2.0 finish pct, ahead on 8–10 of 12. **DIRECTIONAL.**
   - **Flagships and the qualifiers** pick worse: flagship −2.8 ± 3.3; qualifier −10.4 ± 10.4, one contest flipping.
2. **It doesn't fix the calibration; it makes it worse.**
   - Re-scored under the uncertain field, the same lineups' stated expected payout *rises* 8–10% and their stated top-1% rate rises: 0.246 → 0.263, against a real 0.132.
   - A more concentrated, noisier field is easier for leverage to beat in the sim. So the sim grows more confident, not less.
3. **The 7.5-point shortfall can't come from the field.** It is our entries' own *points* against their simulated mean, and the field doesn't score our lineups. The likely source is the projection: our lineups are picked on the projections the sim draws from, and the per-minute level runs high (Friday review sections 2 and 10).

**Nothing is proposed.** Main-contest picking under an uncertain field goes on the watch list.

---

## 1. The uncertainty model, and its sizes

**Measured** on the fixed `own_eval` (100+ entry contests, players with max(ours, real) ≥ 1; `sizes.json`):

| Tier | log((real + 1) / (ours + 1)): SD | mean | players |
|---|---|---|---|
| < $5k | **0.891** | −0.016 | 1,436 |
| $5–7k | **0.661** | −0.012 | 1,932 |
| $7k+ | **0.633** | −0.035 | 1,222 |

The concentration miss (the field's top-8 sum minus ours, 200+ entry contests) is **+22.6, SD 28.4 over 16 slates.**

**How each simulated night's field is drawn.** Each field lineup is weighted by exp(Σ ε_p over its players + κ × c_L):
- ε_p ~ N(0, the SD of the player's tier) × τ;
- c_L is the number of our 8 most-owned players in the lineup;
- κ ~ N(μ, sd), set per slate so the field's top-8 ownership moves by N(+22.6, 28.4) points.

Players are scored on the same draws as today's fixed field, so the field is the only difference.

**What a 1,000-lineup field can carry.** Independent per-player noise at the full measured size (log SD 0.63–0.89) concentrates a 1,000-lineup field onto a handful of lineups. The effective field size is about F × exp(−8σ²), roughly 2. So the per-player noise is scaled by τ until the expected effective size is a third of the field, and the noise actually carried is measured:

| Size | ESS | Field top-8 vs ours (mean ± SD over nights) | Per-player log SD carried | τ |
|---|---|---|---|---|
| × 0.5 | 509 of 1,000 | +4.5 ± 26.5 | 0.29 | 1.00 |
| **× 1** | 470 | **+14.9 ± 36.2** | 0.31 | 0.52 |
| × 2 | 420 | +36.6 ± 58.9 | 0.35 | 0.26 |
| concentration only (× 1, no ε) | 926 | **+22.6 ± 28.6** | 0.09 | 0 |

**The model under-carries per-player noise.** It reaches about half the measured per-player error. Fully representing it needs a field rebuilt each night by the optimizer, which a replay can't do. The concentration-only run carries the measured concentration miss exactly.

## 2. Picks under the uncertain field, on real results

Three pick sets per contest, all with the page's pick (`DKSim.pick`: Max ROI for main and qualifier contests, Max coverage for flagships, each contest on its own, the build's caps):
- **A:** today's fixed field, picked from the kept pool;
- **B:** the uncertain field, picked from the kept pool (a re-fill);
- **C:** a re-cut under the uncertain field, then the same pick. The re-cut takes the kept pool plus 2,000 other bank lineups, ranked by entries-weighted expected payout, and keeps the top |kept|. It replaced 13–30% of the kept pool.

**R** is random fills of the same size from the kept pool (300 draws).

Real finish percentile and payout per lineup, per contest, averaged within each slate, then mean ± SE over slates (slates ahead):

| Size | Type | B − A, finish pct | C − A, finish pct | A − R | B − A, $ per lineup |
|---|---|---|---|---|---|
| **× 1** | all (68 contests, 14 slates) | **−1.92 ± 2.08, 7** | −2.22 ± 2.12, 7 | +3.96 ± 2.69, 8 | +0.38 ± 12.23, 4 |
| × 1 | flagship (31) | −2.82 ± 3.28, 8 | −3.03 ± 3.29, 8 | +2.22 ± 3.86, 9 | +0.27 ± 24.53, 3 |
| × 1 | **main (31, 12 slates)** | **+1.78 ± 0.81, 9 of 12** | +1.54 ± 1.07, 8 | +2.97 ± 1.98, 9 | +0.157 ± 0.113, 6 |
| × 1 | qualifier/small (6) | −10.42 ± 10.42, 0 | −10.42 ± 10.42, 0 | +13.32 ± 7.47, 4 | 0 |
| × 0.5 | all | −3.83 ± 2.04, 3 | −4.21 ± 2.18, 5 | +4.07 ± 2.57, 9 | −8.52 ± 7.85, 5 |
| × 0.5 | main | +1.32 ± 0.73, 8 | +0.75 ± 1.06, 6 | | +0.158 ± 0.111, 7 |
| × 2 | all | −2.78 ± 1.95, 6 | −3.12 ± 1.94, 5 | +3.81 ± 2.76, 9 | −8.42 ± 7.87, 3 |
| × 2 | main | +1.45 ± 0.87, 9 | +0.65 ± 1.02, 6 | | +0.161 ± 0.114, 6 |
| concentration only | all | −0.21 ± 0.76, 8 | −1.14 ± 1.01, 6 | +3.89 ± 2.65, 10 | −0.39 ± 0.22, 4 |
| concentration only | main | +2.04 ± 1.30, 10 of 12 | +1.30 ± 0.74, 9 | | +0.054 ± 0.036, 6 |
| concentration only | flagship | −1.78 ± 1.99, 5 | −3.02 ± 2.14, 5 | | −0.93 ± 0.49, 2 |

**Reading it:**
- **Payout differences are dominated by one or two big flagship cashes.** One set catching a $1k first and the other missing it moves the mean by $10–25 a lineup. Finish percentile is the steadier measure.
- **On finish percentile:**
  - **main** gains under every size: 8–10 of 12 slates, +1.3 to +2.0;
  - **flagships** lose: −1.8 to −6.1;
  - **the qualifiers** have one contest flip, 1 entry a night.
- **The re-cut (C) adds nothing over the re-fill (B).**

**Tags:**
- uncertain field overall: **NOISE**;
- main contests re-filled under it: **DIRECTIONAL** (+1.78 ± 0.81, 9 of 12 at × 1; ahead at every size; dollars +$0.16 ± $0.11, 6 of 12);
- flagships and qualifiers under it: **NOISE**, leaning worse.

## 3. Calibration

Summed over the 68 contests. Stated means the expected payout and top-1% coverage the sim gave the set; real means what the set paid.

| Set, scored by | Stated payout | Real payout | Stated ÷ real | Stated top-1% | Real top-1% |
|---|---|---|---|---|---|
| A, fixed sim | $2,186 | $2,971 | 0.74 | 0.246 | 0.132 |
| A's same lineups, uncertain sim (× 1) | $2,408 | $2,971 | 0.81 | 0.263 | 0.132 |
| B, uncertain sim (× 1) | $2,428 | $1,955 | 1.24 | 0.272 | 0.118 |
| A's lineups, concentration-only sim | $2,200 | $2,971 | 0.74 | 0.251 | 0.132 |

Fees were $969.

- **The uncertain field raises what the sim states for the same lineups,** by 1–10% in payout and in top-1% coverage. It moves away from the real top-1% rate (0.132), not toward it. **NOISE** as a calibration fix.
- **The stated payout of these re-picked sets reads low against real ($2,186 vs $2,971).** The late-swap calibration found our real entries stated 2.1× too high. Two reasons for the difference:
  - these are replay picks, not the entries;
  - one or two big real cashes carry the real total.
- **The top-1% rate, which isn't hostage to one cash, says the sim is overconfident by about 2×** (0.25 stated vs 0.13 real). That agrees with the late-swap calibration.

## What could and couldn't be replayed

**Replayed:**
- the slate (projections, miss sizes) and the simulated field as they stood at lock, from the mirror;
- the page's player draws and its pick (`DKSim.pick`), with each build's caps;
- the build's kept pool and bank;
- the real standings.

**Not replayed:**
- **The page's actual fill.** The flagship joint pick (`pickJoint`), the qualifiers' chalk batch, the night cap across contests, and the operator's hand edits are not in this replay. Set A is today's fill *model* run alone per contest, not the entries that were made.
- **The merit cut by idea.** The re-cut ranks by plain expected payout.
- **Ties:** prize splits with duplicates are off in every set.
- **A field rebuilt per night.** Uncertainty is a reweighting of the lock-time field, so the per-player ownership noise is under-carried (0.31 vs 0.63–0.89).

## Watch list (HELD)

| Item | Tag | Next |
|---|---|---|
| Main contests filled under an uncertain (concentrated) field | DIRECTIONAL | Re-run with the page's actual fill (cross-contest caps) once the fill replay can run it; 10+ more slates |
| The sim's top-1% overconfidence (about 2×) | finding (agrees with the late-swap calibration) | It lives in the projection, our lineups' own points, not the field. Test the selection haircut and the per-minute level there. |

**Note, 2026-11-28 (unified contest types):** the by-type tables above came from `ous.py`, which used a by-size rule (under 800 entries = flagship). The pick itself (`ous.js`) already used the page's flagship rule.

Re-graded on the DK page's profile (`scripts/dk_contest_type.py`; `ous.py --grade-only`, output `ous_recut.out`). The types now split into 20 flagship, 43 main and 5 qualifier contests (were 31 / 31 / 6). At × 1:

| Type | B − A finish pct, before | After |
|---|---|---|
| Main | +1.78 ± 0.81, 9 of 12 | +1.73 ± 0.74, 9 of 12 |
| Flagship | −2.82 ± 3.28, 8 of 14 | −4.07 ± 3.61, 6 of 13 |

Main stays positive at every size, ahead on 6 to 12 of 12 (was 8–10). Tags are unchanged: overall NOISE, mains DIRECTIONAL, flagships NOISE.
