# Player stability from our own history: bias vs volatility (2026-11-28)

Analysis only. Nothing ships; no page, projection, bank or sim change. Asked by the operator through the coordinator
on 2026-11-28.

## Pre-registration (committed before any result was computed)

Earlier "fragile" tests (hot-value cap, greens, source disagreement) asked "do we miss by more?", which mixes two
things this study keeps apart:

- **BIAS** — we over-project (actual − proj below zero): bad, own less.
- **VOLATILITY** — a wide outcome range around an unbiased centre: not bad in top-heavy contests, but it should set
  the width of the noise the bank and the sim use for that player.

The bank's Projection noise (batch item 2, live, settling) uses one σ per salary tier. The sim already uses a
per-player spread: `miss_dk` (scripts/cbb_nightly.py `miss()`: a + b·fp plus early-season, minutes-CV, bench and
transfer terms) times the outcome shape SIM_Z (SD 1.25, 10th/90th percentile −1.42 / +1.71). This study asks whether
our own history predicts either the bias or the volatility better than those.

### Data

- **Rows**: every graded DK slate night record in `analysis/cbb/dk/<date>_<draft group>.csv` (20 slate files from
  2026-11-16 to 2026-11-27). Players with status not "Out" at lock and a lock projection `fp_dk` ≥ 5 (the
  projection logged at lock in the night record). A player who didn't play counts at actual 0 points and 0 minutes.
- **Projection**: `fp_dk` (lock-time DK points); `min_proj` (lock-time minutes).
- **Actuals**: `actual_dk`, `min`.
- **Game logs at lock**: rebuilt from battle-royale-research `data/cbb/box/2026-27/*.json`, using only games dated
  before the slate's date. Matching is by ESPN athlete id.

### Features (all computable at lock)

| Feature | Definition |
|---|---|
| min_sd5, min_mean5 | SD and mean of minutes over the last 5 games played |
| min_sd10, min_mean10 | the same over the last 10 |
| min_trend | mean minutes of the last 3 games − mean of the 7 before those (needs 5+ games, else missing) |
| starter_share | share of this season's games started (`st` in the box cache) |
| gp | games played this season before the slate |
| role_change | 1 if \|mean of last 3 games' minutes − season mean minutes\| ≥ 6, else 0 |
| abs_spread | \|pregame spread\| (night record `spread`) |
| total | pregame total (`ou`) |
| questionable | 1 if status is Q (or "Questionable") at lock |
| tier | salary < $5k / $5–7k / $7k+ |
| proj | `fp_dk` |
| ppm_sd10 | SD of DK points per minute over the last 10 games with 5+ minutes |

Not reconstructable: **fouls per 40** (the box cache has no fouls) — dropped. Missing values (too few games) are
reported as their own bin in A and filled with the fit slates' median plus a missing flag in B and C.

### Targets

1. **BIAS** e = actual_dk − fp_dk.
2. **VOLATILITY** v = |e − b̂|, with b̂ the bias predicted for that player by model C fitted without his slate. In
   test A, b̂ is the bin's mean bias on the fit slates.
3. **Minutes miss** m = actual min − min_proj.

### Split

- Fit set: the first 14 slate files (2026-11-16 to 2026-11-24). Out of sample: the last 6 (11-25, 11-26, 11-27;
  two slate files each).
- Leave-one-slate-out (LOSO) across all 20 for B and C as well, each slate file held out in turn.
- Every number is a mean over slate files, ± SE over slate files, with k of n slates.

### Tests

- **A, descriptive.** For each continuous feature, quintile cut points fixed on the fit set's pooled rows (applied
  unchanged to the last 6); binary features by level; tier by its 3 levels; missing as its own bin. Per bin: mean
  bias e, mean volatility v (around the bin's fit-set mean bias) and mean minutes miss m, ± SE over slates, on the fit
  set and on the last 6 separately. A bin needs 3+ players on a slate to count that slate.
- **B, volatility model.** Linear regression of v on the standardized features (plus missing flags), fit LOSO.
  Predicted σ̂ = √(π/2) × predicted v, floored at 1.0 point. Scored on the held-out slate's residuals r = e − b̂ by the
  mean Gaussian log-likelihood log N(r; 0, σ̂²), against:
  - (i) the per-tier σ: √(π/2) × the tier's mean v on the other slates (the bank's current structure);
  - (ii) the sim's σ: 1.25 × `miss_dk`.
  Also the 10/90 band coverage (target 80%) and the coverage gap |coverage − 0.80|.
- **C, bias model.** Linear regression of e on the same features, LOSO. Scored by held-out MAE of (fp_dk + ê)
  against fp_dk alone, per slate. Secondary: the same for the minutes miss m against min_proj. Plus the last-6 view
  from fitting on the first 14 only.
- **D, sim calibration by bucket.** Buckets: quintiles of the held-out σ̂ from B, and separately quintiles of the
  sim's own `miss_dk`/`fp_dk`, plus bench (min_proj < 20) vs not. Per bucket: realised SD of e and the 10/90 coverage
  of the sim's band (fp_dk − 1.42·miss_dk, fp_dk + 1.71·miss_dk, floored at 0), against the sim's stated spread
  (1.25·miss_dk). The overall ratio was 0.93x.

### Pass bars (process.md rule 5)

- **B passes (PROVEN)** if the per-player σ beats the per-tier σ on held-out log-likelihood by more than 2×SE over
  slates, ahead on most slates, and is also ahead on the last 6 (fit on the first 14). **DIRECTIONAL**: right
  direction on 13+ of 20 slates (65%) and on the last 6, mean positive. Otherwise **NOISE**. The comparison with the
  sim's σ is reported the same way, as context.
- **C passes (PROVEN)** if the corrected projection's held-out MAE beats fp_dk by more than 2×SE, ahead on most
  slates, and ahead on the last 6. DIRECTIONAL / NOISE as for B. A single feature in A counts as a "fragile" signal
  only if its top-vs-bottom bin bias difference has the same sign on the fit set and the last 6 and clears 2×SE on
  the fit set.
- **D** is descriptive: a bucket is "too tight" if its realised SD exceeds the sim's stated spread by more than 2×SE
  (bootstrap over slates).

### What follows

- If B passes: a written proposal for per-player σ in the bank's Projection noise, as a future change. Item 2 stays
  as it is while it settles.
- If C passes: a projection-correction proposal with its arm and its PREVIOUS column.
- Nothing else.

## Results

(Appended after the run; nothing below this line existed at the pre-registration commit c3961c8.)

### Plain summary

- **Volatility (B): NOISE.** Our own history doesn't predict a player's outcome range better than one σ per
  salary tier (+0.01 ± 0.01 log-likelihood per player, 11 of 20; out of sample −0.06 ± 0.07). It also doesn't beat
  the sim's existing per-player spread (1.25 × miss_dk: −0.00 ± 0.01). Keep the bank's per-tier noise; per-player σ
  isn't worth building.
- **Bias (C): DIRECTIONAL, and it is sit-risk, not on-court over-projection.**
  - The bias model's held-out gain is small but real on leave-one-slate-out: points +0.15 ± 0.06 MAE (13 of 20,
    past 2×SE), minutes +0.28 ± 0.08 (16 of 20). Out of sample (fit on 14, last 6) it's +0.03 ± 0.03 on points (3 of
    6) and +0.15 ± 0.08 on minutes (5 of 6).
  - The only two single-feature signals that pass the pre-registered check are **few games played (≤3)** and
    **Questionable at lock**. Both are carried by players who then didn't play: 23% of the ≤3-game players and 58% of
    the Q players sat. When they did play, they beat our projection (≤3 games +0.39, Q +2.58).
  - So the "true fragile" in our history is "may not play", which belongs to the sit-risk flag (task pending, the
    2-week review), not to a points discount for players who take the floor.
- **Sim calibration (D): the sim's spread is about 10% too tight overall**, and most so for the players we think are
  steadiest. Realised SD / stated is 1.10 overall; 1.15 in the lowest predicted-σ fifth (15 of 20 slates above 1, 10/90
  coverage 0.70 against 0.80). Bench players (1.11) aren't notably tighter than starters (1.07). The sim's 10/90 band
  covers 0.746 overall.

### Data

2,098 player rows on 20 slate files (2026-11-16 to 11-27): fit set 14 files (1,266 rows), last 6 (832 rows). Mean
bias −0.28 (fit −0.18, last 6 −0.44). Not reconstructable: fouls per 40 (not in the box cache), dropped as
pre-registered. One mechanical note: on discrete features (starter share, games played, |spread|) tied quintile cut
points collapse some bins, so the fragile check compares the lowest and highest bins present.

### A. Descriptive (full tables in `player_stability_2026-11-28/ps.out`)

Fragile check, top bin minus bottom bin bias, per slate:

| Feature | Fit (14) | Last 6 | Passes |
|---|---|---|---|
| games played, 5+ vs ≤3 | +3.56 ± 0.92 (8 of 9) | +4.24 ± 2.71 (4 of 5) | yes |
| Questionable vs not | −8.04 ± 2.64 (6 of 7 negative) | −4.25 ± 6.95 | yes |
| starter share, high vs low | +1.86 ± 0.74 (12 of 14) | −0.12 ± 0.43 | no (flips) |
| projection, top vs bottom fifth | +2.33 ± 1.01 (10 of 14) | −1.10 ± 0.72 | no (flips) |
| salary tier, $7k+ vs <$5k | +1.71 ± 0.81 (10 of 14) | −0.24 ± 1.21 | no (flips) |
| minutes SD (5 / 10), minutes mean (5 / 10), trend, spread, total, ppm SD | inside noise | — | no |
| role change (3-game vs season ≥ 6 min) | only 20 rows, none in the fit set | — | can't test |

Volatility per bin rises with minutes, projection and tier (bigger players have wider outcomes in points), which is
what the per-tier σ already captures.

Context (not pre-registered), the two signals with non-players removed:

| Group | n | Didn't play | Bias, all | Bias, played only |
|---|---|---|---|---|
| ≤3 games | 280 | 23% | −1.95 | +0.39 |
| 4 games | 449 | 4% | +0.76 | +1.30 |
| 5+ games | 1,369 | 4% | −0.28 | +0.24 |
| Questionable | 52 | 58% | −7.42 | +2.58 |
| not Questionable | 2,046 | 5% | −0.10 | +0.47 |

### B. Volatility model

| Held-out log-likelihood gain per player | Mean ± SE | Slates ahead | Tag |
|---|---|---|---|
| per-player σ vs per-tier σ, LOSO 20 | +0.01 ± 0.01 (2×SE 0.014) | 11 of 20 | NOISE |
| per-player σ vs per-tier σ, fit 14 → last 6 | −0.06 ± 0.07 | 4 of 6 | |
| per-player σ vs sim σ (1.25 × miss_dk), LOSO 20 | −0.00 ± 0.01 | 11 of 20 | NOISE |

10/90 coverage (target 0.80): per-player 0.812, per-tier 0.819, the sim's band 0.746.

### C. Bias model

| Held-out MAE gain (fp_dk alone − fp_dk + predicted bias) | Mean ± SE | Slates ahead | Tag |
|---|---|---|---|
| points, LOSO 20 | +0.15 ± 0.06 (2×SE 0.12) | 13 of 20 | |
| points, fit 14 → last 6 | +0.03 ± 0.03 | 3 of 6 | DIRECTIONAL (past 2×SE on LOSO, but the out-of-sample gain is inside noise) |
| minutes, LOSO 20 | +0.28 ± 0.08 (2×SE 0.16) | 16 of 20 | |
| minutes, fit 14 → last 6 | +0.15 ± 0.08 | 5 of 6 | DIRECTIONAL |

### D. Sim calibration by bucket

Realised SD of (actual − proj) against the sim's stated spread (1.25 × miss_dk), and the sim's 10/90 band coverage:

| Bucket | n | Realised / stated | Coverage |
|---|---|---|---|
| held-out σ̂ fifth 1 (steadiest) | 419 | 1.15 (above 1 on 15 of 20 slates; too tight beyond 2×SE) | 0.704 |
| σ̂ fifths 2–5 | 420 each | 1.05–1.08 | 0.74–0.77 |
| sim miss_dk/fp fifths 1–5 | 419–420 | 1.06–1.10 (fifths 2, 4, 5 flagged too tight) | 0.72–0.78 |
| bench (min_proj < 20) | 999 | 1.11 | 0.741 |
| not bench | 1,099 | 1.07 | 0.753 |
| all | 2,098 | 1.10 | 0.746 |

This differs from the late-swap calibration's 0.93x, which measured the spread of whole lineups at the first break;
here it is single players at lock.

### Proposals

- **B (per-player σ in the bank): none.** It failed; the bank's per-tier noise stays.
- **C: no projection correction for players who play.** The bias signal is sit-risk. Proposed instead, for the
  operator's review alongside the pending sit-risk flag review: test a play-probability discount for (a) players with ≤3
  games this season and (b) Questionable players, on the minutes/projection arm, with PREVIOUS = fp_dk without it, under
  rule 5. This is a proposal only; nothing changes.
- **D (context, not a rule-5 item):** the sim's per-player spread runs about 10% tight, most for the steadiest fifth.
  A uniform widening of miss_dk would be the natural test, with the calibration and the over-trust gauge as its
  measures; not proposed here.
