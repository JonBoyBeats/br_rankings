# DraftKings CBB: the ownership disagreement test (2026-11-28)

The operator approved this test. It is **analysis only**: nothing on the page, in the projections or in the config changes.

**The operator has put all proposals on hold.** That includes the Friday review's flagship fill and its ownership Q term. Nothing in this write-up is proposed. Where a candidate is named, it is for the operator's review and marked held.

**The question.** When our projected ownership and the field's real ownership disagree about a player, who was right about the result? Should we lean harder into our numbers, or is the field's disagreement information we lack?

**Data.**
- 16 graded slates, 2026-11-16_156660 to 2026-11-26_157382.
- One row per slate and player:
  - *ours* is our projected ownership at lock (`own_eval.csv`'s own_proj, the page's number; `own_raw` beside it);
  - *real* is the field's real ownership, entries-weighted over the slate's 100+ entry contests;
  - **d = real − ours**;
  - projection = `fp_dk`, result = `actual_dk`;
  - value = DK points per $1k;
  - 5x = 5 × salary in thousands or more.
- **The analysis set** is the players at 5%+ on either side: n = 675. The coordinator's first pass had 668.
- **The slate is the unit.** Every figure is a per-slate statistic, then the mean ± SE over slates, with a 90% bootstrap band over slates and the number of slates positive.
- **Code and outputs:** [ownership_disagreement_2026-11-28/](ownership_disagreement_2026-11-28/), which holds `od.py`, `od2.py` and `od3.py` and their `.out` files.

## Verdict

1. **The field knew something we didn't, but mostly where it bought players, and mostly in the rotation band.**
   - Players the field owned 10+ points above us beat our projection by **+3.31 ± 1.32**, compared within the same slate with players we agreed on (12 of 15 slates).
   - Players it faded by 10+ came in −1.44 ± 1.44, which is noise.
   - In the rotation band (we projected 10–25), it splits cleanly. Loved players: **+6.05 ± 1.49** against our projection. Faded: **−4.32 ± 1.89**.
   - **Among stars (25+) it reverses.** Faded stars beat our projection by **+5.51 ± 2.13** (10 of 12 slates), and loved stars only +1.26 ± 2.20. On stars, leaning away from the field paid.
2. **Overall, neither side ranks outcomes better.** Per-slate Spearman with actual value: our projected value 0.185 ± 0.040, field real ownership 0.187 ± 0.045. The field beat us on 7 of 16 slates. A rank blend (weight about 0.5, fitted held out) gets 0.199, only +0.015 ± 0.027 better: noise.
3. **The disagreement is real but small as a linear signal.** r(d, actual − projection) is **+0.126 ± 0.057, positive on 11 of 16.** Even knowing real ownership exactly, with a hindsight correction fitted leave-one-slate-out, cuts projection MAE by only +0.02 ± 0.06. The information sits in the tails (the 10+ buckets), not in a line through every player.
4. **One pre-lock signal predicts both where the field disagrees and where it's right: our own projected value (fp per $1k).**
   - When we call a player a big value, the field owns him *less* than we project (r −0.115 ± 0.040, 3 of 16 slates positive) and he comes in *under* our projection (r −0.121 ± 0.035, 2 of 16).
   - Held out, the sign is right on both for 11 of 16 slates.
   - In plain terms: our value spread is too wide, and the field shrinks it.
   - The next best signal is recent minutes above our projected minutes (`min_gap`): both up, 8 of 14 held out.
   - **Neither improves the projection held out beyond noise:** +0.025 ± 0.055 and +0.019 ± 0.024 MAE.
5. **Our "leverage away" behaviour cost us on these slates.** Per lineup, our entries held **0.57 fewer** field-loved players and **0.60 more** field-faded players than the field (16 slates, loved fewer on 15). Priced at each slate's own residual gaps, that is **−3.98 ± 1.75 DK points per lineup** (5 of 16 slates positive).
   - Our lineups holding 1+ loved players finished **+6.1 ± 3.9 percentile points** above our lineups holding none (10 of 13 slates). That comparison is confounded by lineup construction, so it is colour.
6. **Should field disagreement feed the projection, the ownership model, both or neither? Neither, today.** No pre-lock signal passes the Lab bar for the projection (MAE gain under 2×SE) or for our ownership (the best combination is +0.185 ± 0.096 on the chalk band but worse on all players). The projection arms are settling anyway (process.md rule 4).
   - **What it does say is a construction point.** Our bank leans away from players the field loves in the rotation band and under $7k, and that lean lost about 4 points a lineup. On stars it's the reverse.
   - That points at our value calls (finding 4), not at the field's ownership as an input.

**Proposals: none pass, and all are held.** Two candidates are named for the operator's review (held) on the watch list at the end.

---

## 1. The proper test

### (a) Buckets and continuous versions (`od.py`)

| d = real − ours | n | actual − projection | Value (pts/$1k) | 5x rate |
|---|---|---|---|---|
| field 10+ above us (mean d +17.6) | 74 | **+3.41 ± 1.26 (15) [+1.48, +5.45], +12** | 4.54 ± 0.22 | 0.332 ± 0.069 |
| within 10 | 537 | +0.19 ± 0.39 (16) [−0.47, +0.78], +11 | 3.65 ± 0.09 | 0.207 ± 0.018 |
| field 10+ below us (mean d −17.2) | 64 | −1.25 ± 1.26 (16) [−3.32, +0.69], +6 | 3.60 ± 0.22 | 0.239 ± 0.056 |

Paired within slate, against "within 10":

| | actual − projection | Value | 5x rate |
|---|---|---|---|
| loved | **+3.31 ± 1.32 (15) [+1.17, +5.39], +12** | **+0.90 ± 0.26, +12** | +0.13 ± 0.07, +10 |
| faded | −1.44 ± 1.44 (16) [−3.72, +0.90], +5 | −0.05 ± 0.23, +9 | +0.03 ± 0.06, +9 |

Continuous (per-slate Pearson r, then over slates):

| Measure | Value |
|---|---|
| d vs actual − projection | +0.126 ± 0.057 (16) [+0.037, +0.214], +11 |
| d vs value | +0.128 ± 0.062 [+0.029, +0.230], +11 |
| d vs 5x | +0.081 ± 0.048 [+0.010, +0.164], +11 |
| slope | +1.43 ± 0.69 DK points per 10 points of d, +11 |
| d against `own_raw` instead (before the ownership correction) | +0.128 ± 0.057, +11, the same |

The coordinator's first pass reproduces: r +0.13 on 11 of 16; loved +2.65 / 5x 0.35, within +0.37 / 0.22, faded −1.84 / 0.25. My figures are slate-weighted, which is why they differ a little.

### (b) Both directions, by band and position

Per-slate r(d, actual − projection), and the loved / faded mean of actual − projection:

| Split | n | r | Loved (n): act − proj | Faded (n): act − proj |
|---|---|---|---|---|
| salary < $5k | 156 | +0.19 ± 0.12, +11 | (24) **+6.24 ± 2.65** | (27) **−4.99 ± 2.23** |
| salary $5–7k | 307 | +0.10 ± 0.07, +10 | (29) +3.24 ± 1.80 | (20) **−5.03 ± 2.45** |
| salary $7k+ | 212 | +0.02 ± 0.08, +9 | (21) +2.84 ± 2.37 | (17) **+6.02 ± 2.52** |
| rotation 10–25 | 430 | **+0.19 ± 0.08, +11** | (43) **+6.05 ± 1.49** | (41) **−4.32 ± 1.89** |
| stars 25+ | 238 | +0.02 ± 0.07, +8 | (30) +1.26 ± 2.20 | (23) **+5.51 ± 2.13** |
| guards | 398 | +0.13 ± 0.05, +12 | (40) +4.44 ± 1.19 | (43) +0.97 ± 2.37 |
| forwards | 277 | +0.10 ± 0.08, +11 | (34) +1.72 ± 2.39 | (21) −5.21 ± 2.27 |

The field is right in both directions on cheap and rotation players. On $7k+ stars the field's fades are wrong: they beat our projection by about 6 points. Cell sizes are 17–43 players, so read the bands as directional.

### (c) Leave one slate out

Fitting projection' = projection + b × d on 15 slates and scoring the 16th:
- b sits in a narrow 0.127–0.165 points per point of d;
- the held-out slate's own correlation has the fitted sign on 11 of 16;
- **the held-out MAE gain is +0.020 ± 0.058.** This is hindsight (real ownership is only known after lock), so it is the *upper bound* on what any ownership-based projection fix could buy. It is close to nothing in MAE. The disagreement matters in the tails, not on average.

### (d) Who ranks outcomes better (per-slate Spearman with actual value)

| Ranker | Analysis set (5%+) | Projected 10+ | Whole slate |
|---|---|---|---|
| our projected value (fp / $1k) | 0.185 ± 0.040, +14 | 0.174 ± 0.040 | 0.505 ± 0.025 |
| field real ownership | 0.187 ± 0.045, +12 | 0.185 ± 0.045 | 0.511 ± 0.026 |
| our projected ownership | 0.141 ± 0.040, +14 | | |
| blend of ranks (LOSO weight 0.4–0.6) | 0.199 ± 0.036, +14 | | |
| field − ours | +0.002 ± 0.052, field ahead on 7 of 16 | +0.011 ± 0.052 | +0.006 ± 0.014 |

It's a tie. The blend's +0.015 ± 0.027 over ours is noise. Our projected *ownership* ranks outcomes worse than either our projection or the field's ownership.

### (e) Our entries (`od2.py`; our lineups from the public standings, labelled "us")

| Per lineup, us − field | Value |
|---|---|
| field-loved players held | **−0.574 ± 0.104 (16), fewer on 15** |
| field-faded players held | **+0.597 ± 0.166 (16), more on 12** |

| Our lineups holding | Lineups | Mean finish percentile |
|---|---|---|
| 0 loved | 167 | 50.2 ± 6.1 |
| 1 loved | 322 | 50.7 ± 4.3 |
| 2+ loved | 204 | 48.3 ± 5.3 |
| paired per slate, 1+ minus 0 | | +6.1 ± 3.9 (13), +10 |

The 2+ bucket finishing lower than the 1 bucket, and the paired difference, show the comparison is confounded by which slates and ideas carried the loved players. Read it as colour.

## 2. Before lock: which signals predict where the field disagrees and is right?

From the lock file (`<slate>_proj.json`), on the analysis set. For each signal:
- the per-slate r with d and with actual − projection;
- whether both point the same way;
- held out by slate: whether the sign fitted on the other slates holds for d, for the result, and for both;
- an ex-ante test: actual − projection regressed on the signal, leave-one-slate-out, as an MAE gain.

| Signal | Rows | r with d | r with act − proj | Same way | Held-out sign right: d / result / both | Projection MAE gain, held out |
|---|---|---|---|---|---|---|
| **pval** (our projected value) | 675 | −0.115 ± 0.040, +3 | −0.121 ± 0.035, +2 | yes | 13 / 14 / **11 of 16** | +0.025 ± 0.055 |
| q (Questionable at lock) | 675 | −0.376 ± 0.132 (5), +1 | −0.149 ± 0.162, +2 | yes | 4 / 3 / 3 of 5 | +0.074 ± 0.145 |
| **min_gap** (last game's minutes − our projected minutes) | 577 | +0.127 ± 0.043, +10 | +0.069 ± 0.034, +10 | yes | 10 / 10 / **8 of 14** | +0.019 ± 0.024 |
| min_trend (last 3 minutes − season mpg) | 577 | +0.103 ± 0.036, +11 | +0.062 ± 0.060, +9 | yes | 11 / 9 / 7 of 14 | −0.033 ± 0.022 |
| last1 (last game's DK points − our projection) | 577 | +0.136 ± 0.033, +12 | +0.035 ± 0.041, +8 | yes | 12 / 8 / 6 of 14 | −0.015 ± 0.020 |
| last3 | 577 | +0.035 ± 0.048 | +0.042 ± 0.035 | yes | 10 / 8 / 6 of 14 | −0.049 ± 0.029 |
| cheap_min (under $5k, last game's minutes 5+ over ours) | 675 | +0.051 ± 0.046 (10) | +0.042 ± 0.059 | yes | 7 / 4 / 4 of 10 | −0.047 ± 0.022 |
| transfer | 675 | +0.016 ± 0.028 | +0.012 ± 0.028 | yes | 8 / 9 / 5 of 16 | −0.029 ± 0.017 |
| corr_res (our ownership correction, own − own_raw) | 675 | −0.097 ± 0.089 (5) | −0.035 ± 0.094 | yes | 4 / 1 / 1 of 5 | −0.073 ± 0.038 |
| miya (EvanMiya per-minute − ours) | 674 | +0.011 ± 0.064 | +0.050 ± 0.036 | yes | 4 / 9 / 3 of 16 | −0.032 ± 0.027 |
| sal_move (salary change, $k) | 271 | +0.068 ± 0.089 (11) | +0.034 ± 0.084 | yes | 8 / 3 / 2 of 11 | −0.031 ± 0.025 |
| dk_avg (DraftKings' average − our projection) | 675 | −0.100 ± 0.043, +4 | **+0.125 ± 0.029, +13** | **no** | 12 / 13 / 0 of 16 | +0.054 ± 0.053 |
| checks score | 675 | −0.137 ± 0.038, +3 | +0.033 ± 0.035, +8 | no | 13 / 8 / 0 of 16 | −0.036 ± 0.018 |

**Ranked by "both right, held out":**
1. pval: 11 of 16.
2. min_gap: 8 of 14.
3. min_trend: 7 of 14.
4. last1, last3: 6 of 14 each.
5. Everything else: under half.

**How to read them:**
- **pval** is the clean one. Where we see big value, the field doesn't buy it, and the result agrees with the field.
- **Recent minutes running above our projection** (min_gap, min_trend) moves the field, and the result follows a little.
- **dk_avg** predicts our *result* misses on its own (DK's average above ours → he beats our projection; 13 of 16) but not the field's disagreement. It is a projection signal, not a field signal.
- **The checks score** and **last game's points** move the field's ownership, but not the result.

**Can't be reconstructed from what's logged at lock:**
- news and status changes after our projection was set: only the status at lock is stored, not when it changed or which update the field saw;
- line and total movement: only the lock line is stored;
- any outside source beyond EvanMiya and DraftKings' average.

**As ownership corrections** (`od3.py`; d regressed on the signals leave-one-slate-out, ours + fitted d, scored against real):

| Signals | Chalk-band MAE gain | All-player MAE gain |
|---|---|---|
| min_gap | +0.046 ± 0.033 | +0.015 ± 0.011 |
| last1 | +0.031 ± 0.028 | +0.022 ± 0.012 |
| pval + last1 + checks + min_gap | +0.083 ± 0.069 | −0.007 ± 0.024 |
| the same + dk_avg | +0.185 ± 0.096 (10 of 14) | −0.046 ± 0.035 |

None passes 2×SE, and the best on the chalk band is worse on all players.

## 3. Implication

- **Projection, ownership model, both or neither? Neither, on this evidence.**
  - **Projection:** no pre-lock field signal improves MAE held out. The minutes and per-minute arms are settling 4 of 7 anyway.
  - **Ownership:** no combination passes. The ownership correction itself is settling 5 of 7.
  - The finding is about *our value calls*. Our biggest projected values run too hot, the field discounts them, and the field is right (pval, 11 of 16 both ways).
    - That belongs to the projection arm's per-minute level question in the Friday review (section 2: per-minute runs high by about 0.08 DK points a minute).
    - It is best tested there, as a shrink on extreme projected values held out, not as an ownership input.
- **The cost of "leverage away" on these 16 slates:** about **−4.0 ± 1.8 DK points per lineup** from holding fewer field-loved and more field-faded players than the field (2.3 SE, 5 of 16 slates positive).
  - It comes from cheap and rotation players. On $7k+ stars, fading with the field's fades would have *gained* (faded stars +6.0 against our projection).
  - It is a hindsight attribution, not a tested setting.
- **Lean harder into our numbers? Not in the rotation band.** There the field's disagreement carried information we lacked, in both directions. On stars, yes: the field's star fades were wrong.

## Watch list (both for the operator's review; HELD)

| Item | Arm | Now | Check at |
|---|---|---|---|
| Shrink extreme projected values toward salary-implied (the pval finding) | per-minute / projection | field and result both disagree with our top values, 11 of 16 held out; projection MAE gain +0.025 ± 0.055 | 7 settled slates, judged on the STARS / ROTATION band rule |
| Bank lean on field-loved rotation / cheap players (a cap on fading them) | bank / cut | −3.98 ± 1.75 pts per lineup on 16 slates; stars reverse | 20+ slates, tested as a setting on ROI and finish, held out |
| Recent minutes above our projected minutes (min_gap, min_trend) | minutes | both directions 8 of 14 / 7 of 14 held out | minutes arm at 7 slates |
| DK average − ours as a result signal | projection | r +0.125 ± 0.029 with our miss, 13 of 16; MAE gain +0.054 ± 0.053 | 7 slates |
