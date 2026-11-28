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

(To be appended after the run; nothing below this line existed at the pre-registration commit.)
