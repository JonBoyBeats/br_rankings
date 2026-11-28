# DraftKings CBB: the projection pair backtest (2026-11-28)

The operator approved this study. It is analysis only, and **the HOLD stands.** Tags follow the tiered bar ([process.md](process.md), rule 5).

- **Code:** [projection_pair_backtest_2026-11-28/ppb.py](projection_pair_backtest_2026-11-28/ppb.py)
- **Output:** [ppb.out](projection_pair_backtest_2026-11-28/ppb.out)
- **Asked:** why only 4 slates? Back-test on every graded slate instead.

## Verdict

**On all 18 graded slates, the 4-slate wins don't hold. Nothing in the pair is PROVEN on its arm's headline.**

1. **The minutes switch: NOISE.** On the 4 logged slates it was +0.256 ± 0.119 (4 of 4). On all 18 it is **+0.039 ± 0.094 (12 of 18)** on rotation minutes. On the 14 replayed slates alone it is **−0.023 ± 0.113 (8 of 14)**. It also makes ROTATION points worse: −0.085 ± 0.047 (ahead on only 7 of 18).
   - Rebuilt against old minutes over all 18 slates is a wash: +0.018 ± 0.104 (8 of 18).
   - The old minutes win only for ordinary players we project 20+ minutes: 30+ by 0.72 ± 0.31 (old better on 13 of 17), 20–30 by 0.32 ± 0.13 (15 of 17).
   - The rebuild wins on the fringe (+0.13 ± 0.14, 11 of 17) and on ordinary 10–20 (+0.12 ± 0.11, 12 of 17).
2. **The per-minute level factor alone: NOISE on its own headline.**
   - The fitted factor is ×0.94 (folds 0.94–0.95).
   - It cuts ROTATION points error by **+0.095 ± 0.035 (14 of 18).** That clears 2×SE on that measure.
   - But its arm's headline, STARS points, gets **−0.102 ± 0.114 (7 of 18)** worse. Within noise, but the wrong way on 11 of 18.
3. **The pair together: NOISE.**
   - The fitted factor is ×0.90.
   - **Rotation minutes +0.039 ± 0.094 (12 of 18), STARS points +0.082 ± 0.141 (8 of 18), ROTATION points +0.064 ± 0.046 (14 of 18).**
   - On the 4 logged slates the pair is excellent: STARS +0.570 ± 0.069 (4 of 4), ROTATION points +0.199 ± 0.018. On the 14 replayed slates it isn't: STARS −0.057 ± 0.162 (4 of 14).
   - Stars ahead on only 8 of 18 is not "clearly more slates than not".
4. **Stars in blowouts, by pregame spread: the hypothesis is rejected (NOISE).**
   - Stars' per-minute shortfall does **not** grow with the pregame spread. Per 10 points of |spread|, its slope is **+0.144 ± 0.131 (positive on 14 of 18)**, so the shortfall shrinks.
   - The adjustment held out: **−0.017 ± 0.027 on STARS points (6 of 18).**
5. **What the 4 slates were seeing is a close-game effect for stars, not an ordinary-vs-fringe one.** **DIRECTIONAL (finding).**
   - In pregame |spread| < 5, stars play **+3.0 ± 0.5 minutes more** than the rebuild projects (16 of 16 slates) and score **−0.073 ± 0.019 DK points a minute less** (2 of 16).
   - So the minutes-low / per-minute-high cancellation the operator described is real, but it lives in close games.
   - A held-out +3.5-minute bump for close-game stars with the level factor didn't help STARS points: −0.084 ± 0.105 (9 of 18).
   - Not a fix yet.

**Plain answer:** the minutes model can't be made better on ordinary games by the switch. Measured on every slate, the old minutes beat the rebuild only for 20+ minute ordinary players, and swapping them in costs rotation points elsewhere. The per-minute level is real for rotation players (×0.91–0.94) but not for stars.

**Nothing is proposed. For the operator's review (HELD):** a rotation-only per-minute level has no effect on stars by construction:
- **rotation points +0.090 ± 0.052, ahead on 13 of 18:** 72%, but 1.7 SE;
- **DIRECTIONAL**, exploratory, because its band was chosen after seeing that stars didn't want the level.

---

## 1. The replay: what was re-run, from what

| Slates | Old minutes | Rebuilt minutes | Rebuilt per-minute |
|---|---|---|---|
| 11-16 … 11-24 (14) | **(b) SIMPLE replayed**: the model live just before the rebuild, i.e. `min_old`'s model. It is the QMIN study's held-out replay ([quality_minutes_2026-11-25.md](quality_minutes_2026-11-25.md)). | **The shipped rebuild replayed**: steep 0.18, FORM 0.5, base parameters chosen on the other slates. | **The per-minute rebuild replayed**: `dk_ppm_study.project()` with each slate's held-out final parameters. |
| 11-25 … 11-26 (4) | `min_old` as logged at lock | `min_proj` as logged at lock | `ppm_parts.ppm` as logged at lock |

That's 2,772 player rows on 18 slates: 1,932 replayed and 840 logged. 11-27 isn't graded yet.

**I didn't use the ruler as "old minutes".** It is the 11-23 lock model, one version older than PREVIOUS. Its code reads tonight's fetched inputs (career and game logs, EvanMiya files, lines), which aren't stored per slate before 11-25, so it can't be run faithfully on early slates. PREVIOUS's model (b) is the right "old" for the switch, and its replay exists.

**What the replay can't reconstruct, and the bias:**
- **Play-by-play and box scores** were fetched on 2026-11-25 and filtered to games before each slate's first tip.
  - A game whose play-by-play was missing or late on ESPN drops out of that player's history. It would have dropped out at lock too.
  - Later stat corrections on ESPN are in. Small; it favours the replay slightly.
- **Statuses, Outs, lines, salaries:** the lock file's (stored per slate). Faithful.
- **News between projection and lock:** not stored. Neither model used a news read after 11-23, so the comparison is even.
- **EvanMiya:** the rebuilt per-minute doesn't use it, and (b) uses the lock model's per-minute, so nothing is missing.
- **Fix selection:** the rebuild's fix set (steep, FORM) and the per-minute fix set were chosen on all 14 early slates. Only their parameters were fitted per fold. That's a small selection leak in the rebuild's favour on the 14 replayed slates. It works against the switch and the level factor, so read their replayed numbers as slightly conservative.
- **Logged vs replayed:** the 4 logged slates are what really ran. The replayed 14 are a model run after the fact. Every table shows both, and they disagree in the same direction everywhere: the 4 logged slates favour the fixes. That could be the slates or the source; it can't be told apart yet.

## 2. The pair, and each alone

**Baseline** (rebuilt minutes × rebuilt per-minute), per-slate means over 18 slates:

| | Value |
|---|---|
| ROTATION minutes MAE | 6.280 |
| STARS points MAE | 8.806 |
| ROTATION points MAE | 7.658 |
| Spearman (points, projected 10+) | 0.522 |
| top-10 value overlap | 0.272 |

**Gains** are baseline − candidate, held out by slate, as mean ± SE (slates), with the number of slates ahead.
- Every fitted piece is leave-one-slate-out.
- Ordinary and fringe are defined before lock: |spread| ≥ 15, ≤ 2 games, a rotation teammate Out, or Questionable / P(play) < 0.9.

| Candidate | ROTATION minutes | STARS points | ROTATION points | Lenses: Spearman / top-10 | Tag |
|---|---|---|---|---|---|
| switch (old minutes on ordinary rows) | +0.039 ± 0.094, 12 of 18 | −0.013 ± 0.118, 9 | **−0.085 ± 0.047, 7** | +0.003 / +0.006 | **NOISE** |
| level (per-minute × L, L 0.94) | 0 | **−0.102 ± 0.114, 7** | **+0.095 ± 0.035, 14** | 0 / 0 | **NOISE** on its headline (STARS) |
| **pair** (switch + level, L 0.90) | +0.039 ± 0.094, 12 | +0.082 ± 0.141, 8 | +0.064 ± 0.046, 14 | +0.003 / +0.006 | **NOISE** |
| blowout (stars' per-minute by pregame spread, c 0.02) | 0 | −0.017 ± 0.027, 6 | 0 | 0 / +0.006 | **NOISE** |
| pair + blowout | +0.039 ± 0.094, 12 | −0.015 ± 0.162, 8 | +0.063 ± 0.046, 14 | +0.003 / +0.022 | **NOISE** |
| *exploratory:* level on ROTATION only (L 0.91) | 0 | 0 | +0.090 ± 0.052, 13 | 0 / +0.006 | **DIRECTIONAL (exploratory)** |
| *exploratory:* switch only at 20+ minutes (threshold held out: 20) | −0.004 ± 0.088, 11 | −0.013 ± 0.118, 9 | −0.096 ± 0.045, 6 | +0.007 / +0.006 | **NOISE** |
| *exploratory:* that switch + level | −0.004 ± 0.088, 11 | +0.084 ± 0.141, 8 | +0.054 ± 0.046, 14 | +0.007 / +0.006 | **NOISE** |
| *exploratory:* close-game stars +3.5 min + level | 0 | −0.084 ± 0.105, 9 | +0.093 ± 0.052, 13 | +0.001 / +0.006 | **NOISE** |

**By source:**

| Candidate | Logged 4 slates | Replayed 14 slates |
|---|---|---|
| switch | rotation minutes +0.256 ± 0.119 (4 of 4) | −0.023 ± 0.113 (8 of 14) |
| pair | STARS +0.570 ± 0.069 (4 of 4), ROTATION points +0.199 ± 0.018 (4 of 4) | STARS −0.057 ± 0.162 (4 of 14), ROTATION points +0.025 ± 0.055 (10 of 14) |
| level | ROTATION points +0.171 ± 0.065 (4 of 4) | +0.073 ± 0.041 (10 of 14) |

**Ordinary vs fringe for the pair:**
- ordinary STARS points +0.209 ± 0.133 (10 of 17);
- fringe STARS −0.220 ± 0.435 (6 of 15).

So the pair helps ordinary stars a little and hurts fringe stars. That's the cancellation, but not enough to call it.

**Rebuilt against old minutes, every slate** (ROTATION minutes; positive means the rebuild is better):

| Rows | Rebuilt − old | Rebuild better on |
|---|---|---|
| all | +0.018 ± 0.104 | 8 of 18 |
| ordinary | −0.131 ± 0.131 | 5 of 17 |
| fringe | +0.128 ± 0.138 | 11 of 17 |
| ordinary, projected 30+ | **−0.717 ± 0.310** | 4 of 17 |
| ordinary, projected 20–30 | **−0.315 ± 0.125** | 2 of 17 |
| ordinary, projected 10–20 | +0.116 ± 0.108 | 12 of 17 |
| ordinary, projected < 10 | +0.044 ± 0.195 | 8 of 17 |

**The old minutes are better for ordinary 20+ minute players. DIRECTIONAL (finding): 15 of 17 at 20–30, 13 of 17 at 30+.** Swapping them in still doesn't pay, for two reasons:
- **The minutes gain is small next to the rebuild's own gains** at 10–20 and on the fringe.
- **The rebuilt per-minute was fitted on the rebuilt minutes,** so mixing old minutes with it costs rotation points (−0.085).

## 3. Stars in blowouts, pregame only

Stars are players projected 25+, with 10+ actual minutes. Per slate, then over slates; "ahead" counts slates where the residual is positive (actual above projection).

| Pregame \|spread\| | n | Per-minute: actual − ours | Minutes: actual − ours | Points: actual − ours |
|---|---|---|---|---|
| 0–5 | 188 | **−0.073 ± 0.019, 2 of 16** | **+3.025 ± 0.487, 16 of 16** | +1.08 ± 0.82 |
| 5–10 | 63 | −0.098 ± 0.040, 3 of 12 | +2.254 ± 0.746, 10 of 12 | −0.33 ± 1.20 |
| 10–15 | 28 | −0.051 ± 0.072, 4 of 7 | +0.053 ± 0.726 | −1.45 ± 1.62 |
| 15–20 | 29 | +0.032 ± 0.052, 4 of 6 | −1.02 ± 1.82 | −0.46 ± 2.89 |
| 20+ | 14 | −0.039 (2 slates) | +2.29 ± 3.51 | +1.94 ± 4.32 |

- Per 10 points of |spread|, the per-minute residual's slope is **+0.144 ± 0.131 (18), positive on 14.** So the shortfall *shrinks* as the spread grows.
- After the minutes model's state weighting, stars in pregame blowouts don't fall short on per-minute. The adjustment (c 0.01–0.10 across folds) gains −0.017 ± 0.027 on STARS. **NOISE.**

**Diagnostic only, the final margin** (known after the game, never usable before lock):

| Final margin | n | Per-minute | Minutes |
|---|---|---|---|
| 0–10 | 149 | −0.101 ± 0.032 | +2.52 ± 0.64 (14 of 15) |
| 10–20 | 112 | −0.052 ± 0.040 | +1.41 ± 0.57 |
| 20+ | 61 | −0.069 ± 0.039 | −0.55 ± 0.77 |

The minutes do fall away in real blowouts, but the per-minute shortfall doesn't grow there either.

## Watch list (for the operator's review, HELD)

| Item | Tag | Now | Next |
|---|---|---|---|
| Per-minute level on ROTATION players only (×0.91) | DIRECTIONAL (exploratory) | +0.090 ± 0.052, 13 of 18; stars untouched | re-test with 11-27 and the next week's slates; pre-register the band |
| Close-game stars: minutes +3.0 short, per-minute −0.07 high (pregame \|spread\| < 5) | DIRECTIONAL (finding) | 16 of 16 and 14 of 16 slates | a minutes-side fix for close-game stars refit with its per-minute together (a +3.5-minute bump alone didn't help STARS points) |
| Old minutes better for ordinary 20+ minute players | DIRECTIONAL (finding) | 15 of 17 (20–30), 13 of 17 (30+) | only worth revisiting with the per-minute refit on the same minutes |
| Minutes switch, the pair, the blowout adjustment | NOISE | see section 2 | none |

---

## Time trend (follow-up, 2026-11-28)

**The operator's point.** The early slates had little in-season data, so the in-season pieces (QMIN states, context, form, per-category rates) were starved there. Maybe the 4 recent slates favoured the candidates because of a time trend, not noise.

**Code:**
- [ppb_trend.py / ppb_trend.out](projection_pair_backtest_2026-11-28/ppb_trend.out): each candidate's held-out gain per slate and per row;
- `ppb.py` re-run with `MIN_GP=5` / `MIN_GP=7`: [ppb_gp5.out](projection_pair_backtest_2026-11-28/ppb_gp5.out), [ppb_gp7.out](projection_pair_backtest_2026-11-28/ppb_gp7.out).

Games played at lock comes from each slate's lock file. Gains are positive when the candidate beats the live baseline; for "rebuilt vs old minutes", positive means the rebuild is better.

**The data limit first.** **No early slate has a 7+ game player.** The rotation rows with 7+ games at lock are 0% on every slate through 11-24 and 14–17% on 11-25 and 11-26. So "games played" and "slate order" are almost the same variable for 7+, and 7+ exists on only 4 slates (101 rows).

### 1. Trends

**Against slate order** (OLS slope of the per-slate gain on slate order, per 10 slates ± SE over 18 slates; then the first and second 9 slates):

| Candidate | Headline | Slope per 10 slates | First 9 | Second 9 |
|---|---|---|---|---|
| rebuilt vs old minutes | ROTATION minutes | −0.251 ± 0.196 | +0.179 ± 0.181 (rebuild ahead 6) | **−0.143 ± 0.080 (rebuild ahead 2)** |
| switch | ROTATION minutes | +0.205 ± 0.180 | −0.103 ± 0.161 (4) | **+0.181 ± 0.083 (8 of 9)** |
| switch | ROTATION points | +0.003 ± 0.093 | −0.101 ± 0.080 (4) | −0.069 ± 0.054 (3) |
| level, ROTATION only | ROTATION points | +0.112 ± 0.100 | +0.083 ± 0.073 (6) | +0.097 ± 0.079 (7) |
| pair | STARS points | +0.146 ± 0.278 | −0.061 ± 0.242 (2) | +0.225 ± 0.144 (6) |
| pair | ROTATION points | **+0.171 ± 0.082** | +0.022 ± 0.068 (7) | +0.105 ± 0.064 (7) |
| pair | ROTATION minutes | +0.205 ± 0.180 | as the switch | as the switch |

**Against games played at lock** (per-slate bucket means, then over slates; the row-level slope per game played, capped at 10, has a cluster-robust SE by slate):

| Candidate | Headline | ≤ 3 games | 4–6 games | 7+ games (4 slates) | Row slope per game |
|---|---|---|---|---|---|
| rebuilt vs old minutes | ROTATION minutes | +0.038 ± 0.131 (17) | −0.119 ± 0.136 (18) | +0.027 ± 0.330 | −0.045 ± 0.034 |
| switch | ROTATION minutes | +0.052 ± 0.091 | +0.077 ± 0.102 (13 of 18) | −0.027 ± 0.330 | +0.018 ± 0.032 |
| switch | ROTATION points | +0.148 ± 0.142 | −0.107 ± 0.052 | +0.138 ± 0.299 | +0.002 ± 0.020 |
| level, ROTATION only | ROTATION points | **+0.349 ± 0.229 (12 of 17)** | +0.042 ± 0.066 | +0.012 ± 0.238 | −0.058 ± 0.042 |
| pair | STARS points | +0.889 ± 0.657 (8 slates) | +0.021 ± 0.120 | +0.265 ± 0.366 | −0.154 ± 0.111 |
| pair | ROTATION points | +0.547 ± 0.308 | −0.011 ± 0.064 | +0.173 ± 0.077 (4 of 4) | −0.068 ± 0.042 |

**What it says:**
- **There is a time trend, and it points the operator's way.** The switch's minutes gain went from −0.10 (first 9 slates) to **+0.18 ± 0.08, ahead on 8 of 9** (second 9). The rebuild's edge over the old minutes went from +0.18 to **−0.14 ± 0.08**: the rebuild was better on only 2 of the last 9. The pair's rotation-points slope is **+0.171 ± 0.082 per 10 slates** (2.1 SE).
- **But it isn't explained by games played.** Within a slate, players with more games don't show bigger gains. Every row-level slope on games played is flat or *negative*: the switch +0.018 ± 0.032, the pair −0.068 ± 0.042 and −0.154 ± 0.111.
  - The level factor's gain sits in the starved rows (≤ 3 games: +0.349), the opposite of "improves as data fills in".
  - So the trend is in *time* (the slates, the schedule, the logged-vs-replayed source), not in the player's own sample size.
- **The second half includes the 4 logged slates.** The time trend and the logged-vs-replayed difference can't yet be told apart.

### 2. Restricted to experienced players, on all slates

| Restricted to | Slates | Switch: ROTATION minutes | Level, ROTATION only: ROTATION points | Pair: STARS / ROTATION points | Rebuilt vs old minutes |
|---|---|---|---|---|---|
| 5+ games at lock | 14 (1,218 rows) | −0.075 ± 0.147 (8 of 14) | +0.061 ± 0.067 (10 of 14) | −0.181 ± 0.140 (6) / +0.020 ± 0.055 (10) | +0.140 ± 0.171 (7) |
| 7+ games at lock | 4 (101 rows, logged only) | −0.028 ± 0.330 (2 of 4) | −0.236 ± 0.107 (0 of 4) | +0.249 ± 0.312 (2) / +0.110 ± 0.150 (3) | +0.027 ± 0.330 (2) |

**Restricting to players with a full in-season sample doesn't make any candidate better.** With 5+ games the rebuild beats the old minutes (+0.14), and the switch loses. The starvation hypothesis predicts the opposite.

On 7+ games the old minutes still win at 30+ projected minutes, by 1.72 ± 0.46 (0 of 4), and the rebuild wins at 10–20 (+0.77 ± 0.28, 4 of 4). That's 16 and 27 rows.

### 3. Tags, and what would settle each

| Finding | Tag | What settles it |
|---|---|---|
| A time trend favouring the switch and the pair (second 9 slates: switch +0.18 ± 0.08, 8 of 9; pair rotation-points slope +0.17 ± 0.08 per 10 slates) | **DIRECTIONAL** (the split was chosen after seeing it) | **The next 10 graded slates, scored prospectively** at the standing re-run (due at 28 graded slates). If the switch's rotation-minutes gain clears 2×SE and is ahead on 7+ of those 10, it is PROVEN; if it flips, NOISE. |
| The trend is driven by games played (starved in-season pieces) | **NOISE** | Row slopes are flat or negative, and the 5+ game restriction doesn't help. It could only reverse once 7+ game players exist on 10+ slates: about 2 more weeks of slates (7+ games appears from 11-25). Re-test at the 28-slate re-run with `MIN_GP=7`. |
| Old minutes better for 30+ minute ordinary players | DIRECTIONAL (finding) | It holds at 7+ games (1.72, 0 of 4). Recheck at 10 slates with 7+ game rows. |
| The switch, the level, the pair on all rows | NOISE (unchanged) | The 28-slate re-run. |

### 4. Scorecard addition (tooling and report only, allowed under the HOLD)

- **`scorecard.md` gains "Minutes and per-minute by games played at lock".** The two headlines, ROTATION minutes MAE and STARS points MAE, are split into ≤ 3 / 4–6 / 7+ games, with LIVE, LIVE − PREV, LIVE − RULER and the season's rows.
  - The code is `scripts/dk_scorecard.py` (`gp_lines`); `python3 scripts/dk_eval.py scorecard` writes it nightly as before.
  - Games played comes from a new `gp` column in the night record (`scripts/cbb_daily.py`, from the next record on).
  - Records written before the column read it from `analysis/cbb/dk/gp_at_lock.csv`, written by `scripts/dk_gp_backfill.py` from the lock files (2,843 rows, 18 slates).
- **A standing re-run trigger.** The scorecard prints "Projection pair backtest …: last run 2026-11-28 at 18 graded slates; next re-run due at 28 graded slates (now N)", and adds DUE NOW when reached.
  - The run log is [pair_backtest_runs.json](pair_backtest_runs.json).
  - The rule is in [process.md](process.md) under "Standing re-runs".
  - No CI job was added.
- **`ppb.py` is rerunnable:** paths are relative to the checkout (override with `BRR=<path>`), and `MIN_GP` restricts by games played.
- **Test:** `tests/dk_scorecard.py` checks the `gp` column and the split (22 passed).
