# Monday lock review, 2026-11-23: projections

Every number below is computed by the scripts named (sections 1-3: `scripts/dk_lock_review_proj.py`; section 4: `scripts/dk_minutes_steep_study.py`, `scripts/dk_outhand_study.py` at the old threshold, and `scripts/dk_gate_study.py` + `.js`). 11 graded slates, 11-16 to 11-22; banks on the 9 nights with standings. Thin: a slate is the unit.

**Headline from 2026-11-25: the projection grade by band** (`scripts/dk_proj_grade.py`, `dk_eval.py projgrade`, full tables in `review_projections_bands_2026-11-25.md`). Two bands by our projected DK points at lock: ROTATION 10-25 (8.1 points MAE, -0.4 bias, 33% off by 10+, minutes MAE 6.9; 635 player-nights) and STARS 25+ (9.5, -0.6, 40%, 6.0; 142). Projected under 10 is a secondary line (3.3 MAE). **The rule:** a projection change counts as an improvement only if it lowers the ROTATION band's minutes MAE or the STARS band's points MAE, held out by slate, without worsening the other band beyond noise, nor the banded proxy lenses (A1 `projaudit`: ownership agreement, salary gaps, minutes rank and top-5 hit for ROTATION and STARS) beyond theirs.

## Summary

**LOCK (keep as is)**
- **Steeper minutes, cal-4 m^1.12 (STEEP 0.12).** On the 7 slates before adoption, held-out steepening improves the minutes lens on 6 (g chosen 0.22-0.34). On the 4 slates since (already at 0.12), more steepening helps 2 and hurts 2. 0.12 holds; no case for more.
- **Out hand-off at 15 minutes (OUT_REG_MIN 15).** 5 team cases (an Out projected 15-20 minutes): teammates' minutes better in 4, pooled 4.738 -> 4.599 minutes MAE, 5.763 -> 5.656 points (68 teammate-nights). Thin but consistent.
- **Questionable factor (0.333 on 34 player-nights).** Held out by slate it beats x1 on 8 of 11 slates.
- **Zero-games cut (factor 0.0571 on 59 player-slates, 6 played).** The held-out factor beats no cut on 11 of 11 slates.
- **EvanMiya blend.** Pooled points MAE 5.551 with it vs 5.622 without (1,396 player-nights); better on 6 of 11 slates. Keep; on watch (small edge).
- **Sit flag (display).** Held-out Brier 0.0694 vs 0.268 current (1,417 players, 11 slates). No flag logged at lock yet: the 11-22 lock card's three flagged players were also zero-games players, scaled out of the pool, so none showed. The two-week review stays as planned.

**CHANGE (for the operator: the gate at the freeze)**
- The 50/50 blend with DraftKings' average was the calibration-week hedge "until the owner's choice at the freeze" (versions.csv cal-1). On all the data ours beats the blend under $6,000 (the blend wins 0 of 11 slates under $4k, 3 of 11 at $4-6k; pooled best weight 1.0 in both) and the two are level at $6,000+ (6 of 11, best weight 0.7).
- **Candidate: close the gate under $6,000 (ours alone there), keep the blend at $6,000+.** Points MAE 5.630 -> 5.421, better on 10 of 11 slates; the Vegas slope 1.50 -> 2.09 (real ~2.15-2.3); same-seed banks better on top 10% 7 / worse 2, cash 6 / 3, percentile 7 / 2 of 9 nights (pooled top 10% 9.2% -> 11.4%, cash 18.4% -> 22.0%, percentile 44.2 -> 47.3). Against it: the shape lens (|top-2 vs recent| 0.007 -> 0.020, larger on 8 of 11) and unexplained salary gaps (+10). Both lenses measure closeness to recent share and to the salary line, which DraftKings' season average carries, so the blend scores well on them by construction. **Strictly, A2 as written flags it** (two lenses worse); the operator's call.
- The alternative the gate's code offers at the freeze, the gate closed in every band (its own rule), also improves points (better on 8 of 11) and the banks less (top 10% 6 / 3, cash 5 / 4, percentile 4 / 5), with the same shape and gaps cost.

**WATCH**
- Ours runs slightly steep against recent shares (mean +0.008 top-2; the 11-20 to 11-22 slates +0.013 to +0.042), and cheap players come in under projection (bias -0.98 under $4k) while $6k+ come in over (+1.00).
- Salary gaps: 43 of 71 unexplained; the biggest misses are mostly salary-value spots and newcomers (below).
- The misses that dominate and are knowable before lock: newcomers / few games (26 minutes misses), salary-value spots (48 salary, 27 ownership), Q status. The rest (blowouts, late scratches, unexplained) aren't knowable before lock.


## 1. The A2 lenses, as the projection stood at lock

| Slate | Minutes MAE | Points MAE | Shape top-2 ours-recent | Vegas slope (ours) | Vegas slope (real) | Salary gaps (unexplained / all) |
|---|---|---|---|---|---|---|
| 2026-11-16_156660 | 4.17 | 5.72 | – | 2.85 | 2.66 | 0 / 6 |
| 2026-11-17_156662 | 5.10 | 5.64 | -0.029 | 1.73 | 2.1 | 3 / 3 |
| 2026-11-17_156663 | 4.64 | 5.97 | +0.002 | 2.60 | 2.47 | 5 / 8 |
| 2026-11-18_157032 | 5.58 | 5.30 | -0.017 | 1.91 | 11.88 | 4 / 4 |
| 2026-11-18_157033 | 5.07 | 6.01 | -0.008 | 1.39 | 2.16 | 1 / 3 |
| 2026-11-19_157138 | 4.26 | 5.39 | +0.012 | 0.07 | 3.8 | 3 / 4 |
| 2026-11-19_157139 | 4.79 | 5.62 | +0.006 | 1.31 | 1.39 | 3 / 5 |
| 2026-11-20_157013 | 4.49 | 5.15 | +0.013 | 2.92 | 4.42 | 3 / 6 |
| 2026-11-20_157015 | 4.78 | 5.26 | +0.031 | 1.54 | 1.02 | 9 / 16 |
| 2026-11-21_157017 | 4.71 | 5.23 | +0.028 | 3.07 | 0.67 | 2 / 4 |
| 2026-11-22_157019 | 3.89 | 5.52 | +0.042 | 2.86 | 1.51 | 10 / 12 |
| **mean** | **4.68** | **5.53** | **+0.008** | **2.02** | | **43 / 71** |

### DraftKings points MAE and bias (actual - projected), players not Out

| Group | n | MAE ours | bias ours | MAE page (gated) | bias page | slates where the page beats ours (MAE) |
|---|---|---|---|---|---|---|
| under $4k | 697 | 3.37 | -0.98 | 3.55 | -1.46 | 3 of 11 |
| $4-6k | 423 | 7.06 | +0.37 | 7.31 | -0.96 | 4 of 11 |
| $6k+ | 297 | 8.47 | +1.00 | 8.38 | -0.36 | 5 of 11 |
| G | 757 | 5.62 | -0.03 | 5.78 | -0.86 | 4 of 11 |
| F | 616 | 5.43 | -0.26 | 5.54 | -1.25 | 4 of 11 |
| G/F | 44 | 5.79 | -1.02 | 6.08 | -2.42 | 4 of 11 |
| all | 1417 | 5.54 | -0.16 | 5.69 | -1.08 | 3 of 11 |

## 2. The misses log by reason tag (264 rows, 11 slates)

Knowable before lock: a tag the card carries at lock (an Out teammate, a Q, few games, a salary-value spot, a role change seen in the last games); the rest (blowout, foul trouble, unexplained) show only after.

| Lens | Tag | Misses | Mean size | Knowable pre-lock |
|---|---|---|---|---|
| Vegas | unexplained | 15 | 27.5 | no |
| Vegas | blowout | 10 | 37.8 | no |
| Vegas | late news / scratch | 9 | 29.4 | no |
| Vegas | Q status | 9 | 34.6 | yes |
| minutes | newcomer / few games | 26 | 16.8 | yes |
| minutes | unexplained | 17 | 15.1 | no |
| minutes | late news / scratch | 16 | 19.7 | no |
| minutes | blowout | 15 | 17.8 | no |
| minutes | Q status | 14 | 17.3 | yes |
| minutes | teammate out | 7 | 15.7 | yes |
| minutes | minutes role change | 6 | 16.8 | yes |
| own team | Q status | 12 | 46.9 | yes |
| own team | late news / scratch | 9 | 59.5 | no |
| own team | blowout | 9 | 41.8 | no |
| own team | unexplained | 9 | 36.9 | no |
| ownership | salary-value spot | 27 | 24.5 | yes |
| ownership | chalk concentration | 22 | 26.1 | no |
| ownership | blowout | 14 | 23.7 | no |
| ownership | newcomer / few games | 11 | 26.4 | yes |
| ownership | teammate out | 11 | 24.7 | yes |
| ownership | unexplained | 6 | 21.2 | no |
| salary | salary-value spot | 48 | 10.3 | yes |
| salary | newcomer / few games | 25 | 9.3 | yes |
| salary | chalk concentration | 22 | 9.2 | no |
| salary | blowout | 19 | 10.2 | no |
| salary | unexplained | 12 | 8.2 | no |
| salary | teammate out | 8 | 8.5 | yes |
| salary | late news / scratch | 6 | 16.7 | no |
| salary | Q status | 4 | 16.0 | yes |
| salary | minutes role change | 3 | 8.9 | yes |
| shape | unexplained | 15 | 15.8 | no |
| shape | blowout | 11 | 16.7 | no |
| shape | Q status | 8 | 15.9 | yes |
| shape | late news / scratch | 7 | 17.8 | no |
| shape | teammate out | 3 | 17.2 | yes |

## 3. Changes adopted since 11-16, re-checked on every slate

### Questionable factor (gate.json 0.333)

34 Questionable player-nights on 11 slates. Held out by slate: each slate's Q players at actual / projected over the other slates, against x1 and the current factor:

| Slate | n | actual / projected | factor (others) | MAE x1 | MAE x factor |
|---|---|---|---|---|---|
| 2026-11-16_156660 | 4 | 0.00 | 0.373 | 9.97 | 3.72 |
| 2026-11-17_156662 | 1 | 0.05 | 0.349 | 18.90 | 5.94 |
| 2026-11-17_156663 | 5 | 0.31 | 0.340 | 12.66 | 4.90 |
| 2026-11-18_157032 | 1 | 1.37 | 0.295 | 4.75 | 13.91 |
| 2026-11-18_157033 | 5 | 0.00 | 0.403 | 12.98 | 5.23 |
| 2026-11-19_157138 | 1 | 0.00 | 0.343 | 11.50 | 3.95 |
| 2026-11-19_157139 | 4 | 0.93 | 0.204 | 9.26 | 14.08 |
| 2026-11-20_157013 | 2 | 0.43 | 0.328 | 5.70 | 3.48 |
| 2026-11-20_157015 | 1 | 0.68 | 0.323 | 3.25 | 3.52 |
| 2026-11-21_157017 | 5 | 0.00 | 0.366 | 6.66 | 2.43 |
| 2026-11-22_157019 | 5 | 0.00 | 0.334 | 0.32 | 0.11 |

The factor beats x1 on 8 of 11 slates with Q players.

### EvanMiya blend (fp_dk with it, fp_base_dk without; players with both, not Out)

| Slate | n | MAE with | MAE without |
|---|---|---|---|
| 2026-11-16_156660 | 163 | 5.723 | 5.673 |
| 2026-11-17_156662 | 58 | 5.567 | 5.509 |
| 2026-11-17_156663 | 194 | 5.986 | 6.157 |
| 2026-11-18_157032 | 58 | 5.363 | 5.182 |
| 2026-11-18_157033 | 109 | 5.977 | 5.973 |
| 2026-11-19_157138 | 86 | 5.395 | 5.275 |
| 2026-11-19_157139 | 167 | 5.616 | 5.737 |
| 2026-11-20_157013 | 80 | 4.994 | 5.196 |
| 2026-11-20_157015 | 227 | 5.277 | 5.377 |
| 2026-11-21_157017 | 113 | 5.186 | 5.462 |
| 2026-11-22_157019 | 141 | 5.562 | 5.620 |
| **pooled** | 1396 | **5.551** | **5.622** |

With EvanMiya better on 6 of 11 slates.

### The gate's weight (w $6000-99999 0.50, $4000-5999 0.50, $0-3999 0.50: ours x w + DK's average x (1 - w), players with a DK average)

| Band | n | MAE ours | MAE DK avg | MAE at w 0.5 | best w (grid, pooled) | slates the 0.5 blend beats ours |
|---|---|---|---|---|---|---|
| under $4k | 576 | 3.415 | 4.367 | 3.846 | 1.0 | 0 of 11 |
| $4-6k | 422 | 7.025 | 7.894 | 7.263 | 1.0 | 3 of 11 |
| $6k+ | 297 | 8.470 | 8.878 | 8.477 | 0.7 | 6 of 11 |

### Zero-games factor (sit_model.json 0.0571; the group: 0 games, team 3+, not Out)

| Slate | n | played | actual / projected | factor (others) | MAE unscaled | MAE x factor |
|---|---|---|---|---|---|---|
| 2026-11-16_156660 | 13 | 3 | 0.124 | 0.037 | 6.65 | 1.10 |
| 2026-11-17_156662 | 1 | 0 | 0.000 | 0.058 | 3.30 | 0.19 |
| 2026-11-17_156663 | 9 | 2 | 0.000 | 0.067 | 6.57 | 0.44 |
| 2026-11-18_157032 | 1 | 0 | 0.000 | 0.058 | 2.60 | 0.15 |
| 2026-11-18_157033 | 3 | 0 | 0.000 | 0.065 | 15.47 | 1.00 |
| 2026-11-19_157138 | 2 | 0 | 0.000 | 0.059 | 6.20 | 0.37 |
| 2026-11-19_157139 | 3 | 0 | 0.000 | 0.062 | 10.77 | 0.67 |
| 2026-11-20_157013 | 5 | 0 | 0.000 | 0.060 | 3.38 | 0.20 |
| 2026-11-20_157015 | 3 | 0 | 0.000 | 0.058 | 1.60 | 0.09 |
| 2026-11-21_157017 | 6 | 0 | 0.000 | 0.061 | 4.55 | 0.28 |
| 2026-11-22_157019 | 13 | 1 | 0.118 | 0.037 | 6.47 | 1.07 |

The held-out factor beats no cut on 11 of 11 slates (59 player-slates, 6 played).

### Sit model and flag

Fitted on 1417 players, 11 slates; held-out Brier 0.0694 (model) vs 0.268 (the current implied chance) over 1417 players. Flags logged at lock: 0.

## 4. Re-runs and the gate candidate

### Steeper minutes (scripts/dk_minutes_steep_study.py: extra steepening g held out by slate, on top of the projection as it stood at lock; slates from 11-20 on already carry 0.12)

```
Held out by slate (g chosen on the others): minutes MAE, points MAE, shape top-2 ours-recent, Vegas slope, salary gaps unexplained/all
  2026-11-16_156660 g 0.28: minutes 4.171 -> 3.987; points 5.722 -> 5.549; shape - -> -; Vegas 2.846 -> 2.846; gaps 0/6 -> 0/7
  2026-11-17_156662 g 0.26: minutes 5.100 -> 4.548; points 5.642 -> 5.411; shape -0.029 -> -0.007; Vegas 1.731 -> 1.737; gaps 3/3 -> 4/4
  2026-11-17_156663 g 0.30: minutes 4.642 -> 4.289; points 5.967 -> 6.021; shape 0.002 -> 0.032; Vegas 2.604 -> 2.574; gaps 5/8 -> 5/10
  2026-11-18_157032 g 0.22: minutes 5.580 -> 4.632; points 5.298 -> 4.900; shape -0.017 -> 0.009; Vegas 1.914 -> 2.072; gaps 4/4 -> 4/5
  2026-11-18_157033 g 0.28: minutes 5.068 -> 4.621; points 6.012 -> 5.729; shape -0.008 -> 0.020; Vegas 1.388 -> 1.341; gaps 1/3 -> 1/4
  2026-11-19_157138 g 0.34: minutes 4.261 -> 4.275; points 5.395 -> 5.483; shape 0.012 -> 0.048; Vegas 0.072 -> 0.081; gaps 3/4 -> 5/7
  2026-11-19_157139 g 0.28: minutes 4.789 -> 4.253; points 5.616 -> 5.331; shape 0.006 -> 0.033; Vegas 1.309 -> 1.344; gaps 3/5 -> 4/7
  2026-11-20_157013 g 0.38: minutes 4.489 -> 5.430; points 5.146 -> 5.412; shape 0.013 -> 0.053; Vegas 2.923 -> 3.034; gaps 3/6 -> 1/7
  2026-11-20_157015 g 0.32: minutes 4.780 -> 4.641; points 5.258 -> 5.140; shape 0.031 -> 0.069; Vegas 1.542 -> 1.660; gaps 9/16 -> 4/13
  2026-11-21_157017 g 0.32: minutes 4.706 -> 4.452; points 5.227 -> 4.999; shape 0.028 -> 0.059; Vegas 3.073 -> 3.038; gaps 2/4 -> 2/5
  2026-11-22_157019 g 0.36: minutes 3.890 -> 4.317; points 5.516 -> 5.444; shape 0.042 -> 0.087; Vegas 2.862 -> 2.931; gaps 10/12 -> 8/13
Minutes lens better on 8 of 11 held-out slates
```

### Out hand-off (scripts/dk_outhand_study.py, run with the pre-change threshold 20 so the 15-20 cases show)

```
2026-11-16 UCLA without Xavier Booker (16.7): teammates' minutes MAE 4.762 -> 4.853, DK points 5.269 -> 5.383; starters' minutes 
2026-11-18 UCONN without Nik Khamenia (17.8): teammates' minutes MAE 4.292 -> 4.063, DK points 4.942 -> 4.749; starters' minutes Jr. 29->29 (played 38), Mullins 29->29 (played 36), Landrew 26->27 (played 37), Ross 32->32 (played 27)
2026-11-19 SHU without Terry Copeland Jr. (15.9): teammates' minutes MAE 4.414 -> 4.216, DK points 5.450 -> 5.437; starters' minutes Fisher 30->31 (played 32), Wilcher 25->25 (played 30)
2026-11-19 TA&M without Cade Phillips (17.8): teammates' minutes MAE 6.767 -> 6.512, DK points 8.410 -> 8.135; starters' minutes Haggerty 26->26 (played 39)
2026-11-20 MINN without Kai Shinholster (19.4): teammates' minutes MAE 3.169 -> 3.089, DK points 4.358 -> 4.213; starters' minutes Asuma 34->35 (played 32), Evans 34->35 (played 36), Crocker-Johnson 26->27 (played 31), Durkin 31->32 (played 27)
All: teammates' minutes MAE 4.738 -> 4.599, DK points 5.763 -> 5.656 (68 teammate-nights)
```

### The gate (scripts/dk_gate_study.py: ours = closed everywhere, part = closed under $6k, against today's blend)

```
== ours against the blend ==
Per slate (cur = the blend, ours = the gate closed): points MAE, |shape|, Vegas slope, unexplained gaps
  2026-11-16_156660  pts 5.441 -> 5.565  |shape| 0.000 -> 0.000  Vegas 1.75 -> 2.62  gaps 0 -> 0
  2026-11-17_156662  pts 5.359 -> 5.417  |shape| 0.006 -> 0.022  Vegas 0.90 -> 1.26  gaps 1 -> 1
  2026-11-17_156663  pts 6.103 -> 5.768  |shape| 0.002 -> 0.002  Vegas 1.87 -> 2.77  gaps 2 -> 4
  2026-11-18_157032  pts 5.502 -> 5.445  |shape| 0.003 -> 0.011  Vegas -1.03 -> 2.33  gaps 1 -> 1
  2026-11-18_157033  pts 5.565 -> 5.619  |shape| 0.003 -> 0.005  Vegas 0.88 -> 1.33  gaps 1 -> 1
  2026-11-19_157138  pts 5.434 -> 5.306  |shape| 0.006 -> 0.012  Vegas 1.15 -> 0.54  gaps 4 -> 4
  2026-11-19_157139  pts 6.165 -> 5.713  |shape| 0.006 -> 0.011  Vegas 2.19 -> 1.88  gaps 2 -> 3
  2026-11-20_157013  pts 5.362 -> 5.092  |shape| 0.009 -> 0.017  Vegas 3.36 -> 3.31  gaps 3 -> 3
  2026-11-20_157015  pts 5.589 -> 5.259  |shape| 0.015 -> 0.031  Vegas 1.16 -> 1.52  gaps 5 -> 9
  2026-11-21_157017  pts 5.545 -> 5.032  |shape| 0.012 -> 0.029  Vegas 2.00 -> 3.02  gaps 4 -> 2
  2026-11-22_157019  pts 5.867 -> 5.509  |shape| 0.018 -> 0.042  Vegas 2.23 -> 2.88  gaps 6 -> 10
Pooled: points MAE 5.630 -> 5.429 (better on 8 of 11); |shape| 0.007 -> 0.017 (larger on 10); Vegas slope 1.50 -> 2.13; unexplained gaps +9 in all
== part against the blend ==
Per slate (cur = the blend, ours = the gate closed): points MAE, |shape|, Vegas slope, unexplained gaps
  2026-11-16_156660  pts 5.441 -> 5.396  |shape| 0.000 -> 0.000  Vegas 1.75 -> 2.52  gaps 0 -> 0
  2026-11-17_156662  pts 5.359 -> 5.396  |shape| 0.006 -> 0.002  Vegas 0.90 -> 1.14  gaps 1 -> 3
  2026-11-17_156663  pts 6.103 -> 5.900  |shape| 0.002 -> 0.013  Vegas 1.87 -> 2.55  gaps 2 -> 3
  2026-11-18_157032  pts 5.502 -> 5.453  |shape| 0.003 -> 0.003  Vegas -1.03 -> 2.05  gaps 1 -> 1
  2026-11-18_157033  pts 5.565 -> 5.350  |shape| 0.003 -> 0.010  Vegas 0.88 -> 1.12  gaps 1 -> 2
  2026-11-19_157138  pts 5.434 -> 5.290  |shape| 0.006 -> 0.023  Vegas 1.15 -> 0.81  gaps 4 -> 4
  2026-11-19_157139  pts 6.165 -> 5.791  |shape| 0.006 -> 0.021  Vegas 2.19 -> 1.96  gaps 2 -> 2
  2026-11-20_157013  pts 5.362 -> 5.259  |shape| 0.009 -> 0.024  Vegas 3.36 -> 3.52  gaps 3 -> 3
  2026-11-20_157015  pts 5.589 -> 5.290  |shape| 0.015 -> 0.040  Vegas 1.16 -> 1.32  gaps 5 -> 8
  2026-11-21_157017  pts 5.545 -> 5.100  |shape| 0.012 -> 0.037  Vegas 2.00 -> 3.29  gaps 4 -> 5
  2026-11-22_157019  pts 5.867 -> 5.401  |shape| 0.018 -> 0.053  Vegas 2.23 -> 2.66  gaps 6 -> 8
Pooled: points MAE 5.630 -> 5.421 (better on 10 of 11); |shape| 0.007 -> 0.020 (larger on 8); Vegas slope 1.50 -> 2.09; unexplained gaps +10 in all

Rule-free banks at bank noise 0.35, the same seed under each gate, scored on real points (9 nights with standings: thin).
night       gate      n  top10%  cash%   pctl
2026-11-16  cur    2000    1.4%   4.0%  30.6%
2026-11-16  ours   2000    1.5%   3.4%  27.7%
2026-11-16  part   2000    1.4%   3.6%  29.8%
2026-11-17  cur    2000   16.4%  32.2%  56.1%
2026-11-17  ours   2000   12.6%  25.4%  50.9%
2026-11-17  part   2000   19.2%  35.7%  58.0%
2026-11-18  cur    2000    1.2%   2.8%  31.4%
2026-11-18  ours   2000    1.0%   2.1%  26.4%
2026-11-18  part   2000    1.4%   3.1%  33.6%
2026-11-19e cur    2000    2.9%  11.8%  42.0%
2026-11-19e ours   2000    4.4%  14.9%  45.6%
2026-11-19e part   2000    4.3%  15.0%  46.0%
2026-11-19  cur    2000    1.7%   5.1%  19.6%
2026-11-19  ours   2000    2.1%   5.7%  19.3%
2026-11-19  part   2000    1.9%   5.0%  20.2%
2026-11-20e cur    2000   16.2%  30.2%  59.3%
2026-11-20e ours   2000   19.6%  35.9%  63.1%
2026-11-20e part   2000   13.1%  25.9%  55.4%
2026-11-20  cur    2000   15.7%  30.4%  54.5%
2026-11-20  ours   2000   17.0%  34.2%  57.4%
2026-11-20  part   2000   20.9%  37.8%  60.5%
2026-11-21  cur    2000   16.7%  30.5%  54.8%
2026-11-21  ours   2000   23.8%  42.4%  62.7%
2026-11-21  part   2000   18.2%  36.4%  59.6%
2026-11-22  cur    2000   10.8%  19.1%  49.6%
2026-11-22  ours   2000    8.8%  16.4%  46.8%
2026-11-22  part   2000   22.6%  35.2%  62.3%
  pooled cur   top10 9.2% cash 18.4% pctl 44.2%   vs cur: top10 better 0 / worse 0, cash 0 / 0, pctl 0 / 0 of 9
  pooled ours  top10 10.1% cash 20.0% pctl 44.4%   vs cur: top10 better 6 / worse 3, cash 5 / 4, pctl 4 / 5 of 9
  pooled part  top10 11.4% cash 22.0% pctl 47.3%   vs cur: top10 better 7 / worse 2, cash 6 / 3, pctl 7 / 2 of 9
```
