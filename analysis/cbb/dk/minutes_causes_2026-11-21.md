# Where our minutes go wrong (step C), 2026-11-21

Analysis only: nothing on the page or in the projections changed. Script: `scripts/dk_minutes_cause_study.py`
(`analyse`, `lenses`, `score`) and `scripts/dk_minutes_cause_study.js` (the banks). Every number below is the scripts'
output, pasted.

**The sample is thin:** 9 slates with box scores over five dates, 11-16 to 11-20, 841 players who played. The lineup
part uses the 5 nights with standings on file (11-16 to 11-19, the punt test's nights).

## Verdict

- **No pre-lock minutes correction passes A2.** Each was held out by slate and judged on the A1 minutes lens, points MAE,
  shape, Vegas slope and salary gaps.
  - Team-out boost ×2.3: minutes lens better on 0 of 9 slates.
  - Residual spread: better on 1 of 9.
  - Last-5 blend: better on 1 of 9.
- **Out boost ×2.3 on the banks:** top 10% 4.8% vs 4.7% and cash 11.1% vs 11.2% pooled. It's better on 11-18, worse on
  11-19 main, and changes nothing on two nights.
- **Where the error sits:**
  - Overtime is 16.1% of the squared minutes error and can't be known before lock.
  - Foul trouble isn't measured, because our box scores have no fouls column.
  - Blowouts (final margin 20+) hold 23.8% of the error on 23.5% of the players, no more than their share: the
    spread already in the projection (MIN_BY_SPREAD) takes care of them.
  - Players who played run +1.68 minutes above our projection on average. That's mostly the minutes we give to
    players who then sit. It's step B's question (who sits), not a minutes-rule fix.
- **The one real signal is too thin to act on:** teammates our hand-off boosted 2+ minutes played +5.31 more than we
  projected, but that's only 8 players. Re-check as nights come in.

## Raw output

### Causes (per slate, then pooled; held-out corrections)
```
Slates with box scores: 9 (2026-11-16_156660, 2026-11-17_156662, 2026-11-17_156663, 2026-11-18_157032, 2026-11-18_157033, 2026-11-19_157138, 2026-11-19_157139, 2026-11-20_157013, 2026-11-20_157015); players who played: 841. A thin sample: nine slates over five dates.

Per slate: n played, minutes MAE, bias, and the share of the slate's squared error in each group (out / spread 10+ / last-5 off 4+ / overtime / final 20+)
  2026-11-16_156660  n 140 MAE 5.09 bias +1.54 | out  0.0% spread 100.0% recent 32.5% OT 16.2% blowout 88.6%
  2026-11-17_156662  n  40 MAE 5.58 bias +1.43 | out  0.0% spread 100.0% recent  0.0% OT  0.0% blowout  0.0%
  2026-11-17_156663  n 144 MAE 5.54 bias +1.39 | out 11.1% spread 15.0% recent  9.0% OT  0.0% blowout 48.9%
  2026-11-18_157032  n  38 MAE 6.30 bias +3.39 | out  0.0% spread  0.0% recent  0.0% OT 60.6% blowout  0.0%
  2026-11-18_157033  n  75 MAE 5.37 bias +2.94 | out 31.2% spread  0.0% recent 11.5% OT  0.0% blowout  0.0%
  2026-11-19_157138  n  60 MAE 5.39 bias +1.26 | out  0.0% spread  0.0% recent  0.0% OT  0.0% blowout  0.0%
  2026-11-19_157139  n 116 MAE 5.60 bias +2.25 | out 39.7% spread  0.0% recent  9.4% OT 42.1% blowout 15.6%
  2026-11-20_157013  n  63 MAE 4.93 bias +0.73 | out  5.3% spread 24.5% recent 19.9% OT  0.0% blowout  0.0%
  2026-11-20_157015  n 165 MAE 5.64 bias +1.27 | out  0.0% spread 10.4% recent  4.8% OT 21.3% blowout  0.0%

Pooled: minutes MAE 5.46, RMSE 6.79, bias (real - ours) +1.68 over 841 players who played.

group                                     n share n share SE    bias knowable before lock
team had an Out regular                  79    9.4%    10.6%   +1.98 yes
  of them, boosted 2+ min                 8    1.0%     1.6%   +5.31 yes
final margin 20+ (diagnostic)           198   23.5%    23.8%   +1.72 no
pre-game spread 10+                     252   30.0%    26.0%   +1.26 yes
  starters (proj 25+), spread 10+        42    5.0%     4.8%   -0.78 yes
  bench (proj <15), spread 10+          111   13.2%     8.4%   +1.70 yes
last-5 off his projection by 4+          55    6.5%    11.0%   +5.84 yes
overtime game                            90   10.7%    16.1%   +3.85 no

Team out: 79 teammate-games; projected boost mean 1.11 min; their error (real - ours) +5.31 where boosted 2+ (n 8), +1.61 where boosted less (n 71).

Held-out corrections (parameter chosen on the other slates; squared error removed, share of the whole):
  out     removes 0.53% of the squared error (MAE 5.459 -> 5.455); better on 3 of 9 slates; parameters 2.30; 2.30; 2.20; 2.30; 2.20; 2.30; 2.30; 2.60; 2.30
      2026-11-16_156660  par 2.30           RMSE 6.404 -> 6.404   MAE 5.091 -> 5.091
      2026-11-17_156662  par 2.30           RMSE 6.908 -> 6.908   MAE 5.575 -> 5.575
      2026-11-17_156663  par 2.20           RMSE 6.836 -> 6.788   MAE 5.544 -> 5.474
      2026-11-18_157032  par 2.30           RMSE 7.323 -> 7.323   MAE 6.297 -> 6.297
      2026-11-18_157033  par 2.20           RMSE 6.751 -> 6.668   MAE 5.368 -> 5.376
      2026-11-19_157138  par 2.30           RMSE 6.799 -> 6.799   MAE 5.388 -> 5.388
      2026-11-19_157139  par 2.30           RMSE 6.904 -> 6.851   MAE 5.603 -> 5.630
      2026-11-20_157013  par 2.60           RMSE 6.141 -> 6.213   MAE 4.935 -> 4.985
      2026-11-20_157015  par 2.30           RMSE 7.098 -> 7.098   MAE 5.643 -> 5.643
  spread  removes -3.19% of the squared error (MAE 5.459 -> 5.579); better on 4 of 9 slates; parameters -0.31/0.43; 0.05/0.15; 0.15/0.12; 0.04/0.15; 0.04/0.15; 0.04/0.15; 0.04/0.15; 0.06/0.15; 0.00/0.15
      2026-11-16_156660  par -0.31/0.43     RMSE 6.404 -> 7.082   MAE 5.091 -> 5.813
      2026-11-17_156662  par 0.05/0.15      RMSE 6.908 -> 6.884   MAE 5.575 -> 5.570
      2026-11-17_156663  par 0.15/0.12      RMSE 6.836 -> 6.829   MAE 5.544 -> 5.540
      2026-11-18_157032  par 0.04/0.15      RMSE 7.323 -> 7.323   MAE 6.297 -> 6.297
      2026-11-18_157033  par 0.04/0.15      RMSE 6.751 -> 6.751   MAE 5.368 -> 5.368
      2026-11-19_157138  par 0.04/0.15      RMSE 6.799 -> 6.799   MAE 5.388 -> 5.388
      2026-11-19_157139  par 0.04/0.15      RMSE 6.904 -> 6.904   MAE 5.603 -> 5.603
      2026-11-20_157013  par 0.06/0.15      RMSE 6.141 -> 6.135   MAE 4.935 -> 4.916
      2026-11-20_157015  par 0.00/0.15      RMSE 7.098 -> 7.094   MAE 5.643 -> 5.655
  recent  removes 0.21% of the squared error (MAE 5.459 -> 5.499); better on 5 of 9 slates; parameters 0.30; 0.40; 0.45; 0.45; 0.40; 0.40; 0.55; 0.20; 0.40
      2026-11-16_156660  par 0.30           RMSE 6.404 -> 6.310   MAE 5.091 -> 5.012
      2026-11-17_156662  par 0.40           RMSE 6.908 -> 6.931   MAE 5.575 -> 5.618
      2026-11-17_156663  par 0.45           RMSE 6.836 -> 6.860   MAE 5.544 -> 5.584
      2026-11-18_157032  par 0.45           RMSE 7.323 -> 7.472   MAE 6.297 -> 6.453
      2026-11-18_157033  par 0.40           RMSE 6.751 -> 6.719   MAE 5.368 -> 5.358
      2026-11-19_157138  par 0.40           RMSE 6.799 -> 6.774   MAE 5.388 -> 5.474
      2026-11-19_157139  par 0.55           RMSE 6.904 -> 7.104   MAE 5.603 -> 5.870
      2026-11-20_157013  par 0.20           RMSE 6.141 -> 5.864   MAE 4.935 -> 4.679
      2026-11-20_157015  par 0.40           RMSE 7.098 -> 7.048   MAE 5.643 -> 5.716

Overtime: 16.1% of the squared error, not knowable before lock. Fouls: not in our box scores, not measured.
Largest held-out gain: out (0.53% of the squared error).
```

### A2 lenses per candidate (held out by slate)
```
Candidate recent, held out by slate: minutes MAE (A1's: no 20+ blowouts or news scratches), points MAE, shape top-2 ours-recent, Vegas slope, salary gaps unexplained/all
The correction runs on every player not Out (before lock no one knows who sits); it is fit on the errors of those who played.
  2026-11-16_156660  par 0.30       minutes 4.171 -> 4.185; points 5.722 -> 5.644; shape - -> -; Vegas 2.846 -> 2.869; gaps 0/6 -> 0/8
  2026-11-17_156662  par 0.40       minutes 5.100 -> 5.133; points 5.642 -> 5.676; shape -0.029 -> -0.028; Vegas 1.731 -> 1.723; gaps 3/3 -> 3/3
  2026-11-17_156663  par 0.45       minutes 4.642 -> 4.734; points 5.967 -> 5.975; shape 0.002 -> -0.005; Vegas 2.604 -> 2.601; gaps 5/8 -> 3/6
  2026-11-18_157032  par 0.45       minutes 5.580 -> 5.745; points 5.298 -> 5.383; shape -0.017 -> -0.023; Vegas 1.914 -> 2.016; gaps 4/4 -> 3/3
  2026-11-18_157033  par 0.40       minutes 5.068 -> 5.089; points 6.012 -> 6.041; shape -0.008 -> -0.014; Vegas 1.388 -> 1.431; gaps 1/3 -> 1/3
  2026-11-19_157138  par 0.40       minutes 4.261 -> 4.481; points 5.395 -> 5.532; shape 0.012 -> 0.001; Vegas 0.072 -> 0.100; gaps 3/4 -> 3/4
  2026-11-19_157139  par 0.55       minutes 4.789 -> 5.219; points 5.616 -> 5.816; shape 0.006 -> -0.006; Vegas 1.309 -> 1.300; gaps 3/5 -> 1/2
  2026-11-20_157013  par 0.20       minutes 4.489 -> 4.353; points 5.146 -> 5.094; shape 0.013 -> 0.005; Vegas 2.923 -> 2.931; gaps 3/6 -> 3/6
  2026-11-20_157015  par 0.40       minutes 4.780 -> 4.961; points 5.258 -> 5.352; shape 0.031 -> 0.015; Vegas 1.542 -> 1.521; gaps 9/16 -> 8/12
  pooled (mean of slates): minutes 4.764 -> 4.878 (better on 1 of 9); points 5.562 -> 5.613 (better on 2); |shape| 0.013 -> 0.011 (larger on 4); Vegas 1.814 -> 1.833; unexplained gaps 31 -> 25
  parameter on all slates: 0.40
Candidate out, held out by slate: minutes MAE (A1's: no 20+ blowouts or news scratches), points MAE, shape top-2 ours-recent, Vegas slope, salary gaps unexplained/all
The correction runs on every player not Out (before lock no one knows who sits); it is fit on the errors of those who played.
  2026-11-16_156660  par 2.30       minutes 4.171 -> 4.171; points 5.722 -> 5.722; shape - -> -; Vegas 2.846 -> 2.846; gaps 0/6 -> 0/6
  2026-11-17_156662  par 2.30       minutes 5.100 -> 5.100; points 5.642 -> 5.642; shape -0.029 -> -0.029; Vegas 1.731 -> 1.731; gaps 3/3 -> 3/3
  2026-11-17_156663  par 2.20       minutes 4.642 -> 4.642; points 5.967 -> 5.952; shape 0.002 -> -0.000; Vegas 2.604 -> 3.263; gaps 5/8 -> 4/8
  2026-11-18_157032  par 2.30       minutes 5.580 -> 5.580; points 5.298 -> 5.298; shape -0.017 -> -0.017; Vegas 1.914 -> 1.914; gaps 4/4 -> 4/4
  2026-11-18_157033  par 2.20       minutes 5.068 -> 5.259; points 6.012 -> 6.178; shape -0.008 -> -0.012; Vegas 1.388 -> 1.510; gaps 1/3 -> 2/4
  2026-11-19_157138  par 2.30       minutes 4.261 -> 4.261; points 5.395 -> 5.395; shape 0.012 -> 0.012; Vegas 0.072 -> 0.072; gaps 3/4 -> 3/4
  2026-11-19_157139  par 2.30       minutes 4.789 -> 4.966; points 5.616 -> 5.753; shape 0.006 -> 0.003; Vegas 1.309 -> 0.669; gaps 3/5 -> 2/4
  2026-11-20_157013  par 2.60       minutes 4.489 -> 4.638; points 5.146 -> 5.230; shape 0.013 -> 0.008; Vegas 2.923 -> 3.697; gaps 3/6 -> 3/6
  2026-11-20_157015  par 2.30       minutes 4.780 -> 4.780; points 5.258 -> 5.258; shape 0.031 -> 0.031; Vegas 1.542 -> 1.542; gaps 9/16 -> 9/16
  pooled (mean of slates): minutes 4.764 -> 4.822 (better on 0 of 9); points 5.562 -> 5.603 (better on 1); |shape| 0.013 -> 0.012 (larger on 1); Vegas 1.814 -> 1.916; unexplained gaps 31 -> 30
  parameter on all slates: 2.30
Candidate spread, held out by slate: minutes MAE (A1's: no 20+ blowouts or news scratches), points MAE, shape top-2 ours-recent, Vegas slope, salary gaps unexplained/all
The correction runs on every player not Out (before lock no one knows who sits); it is fit on the errors of those who played.
  2026-11-16_156660  par -0.31/0.43 minutes 4.171 -> 4.363; points 5.722 -> 6.517; shape - -> -; Vegas 2.846 -> 3.040; gaps 0/6 -> 0/7
  2026-11-17_156662  par 0.05/0.15  minutes 5.100 -> 5.377; points 5.642 -> 5.841; shape -0.029 -> -0.036; Vegas 1.731 -> 1.700; gaps 3/3 -> 3/3
  2026-11-17_156663  par 0.15/0.12  minutes 4.642 -> 4.642; points 5.967 -> 5.973; shape 0.002 -> 0.001; Vegas 2.604 -> 2.815; gaps 5/8 -> 4/7
  2026-11-18_157032  par 0.04/0.15  minutes 5.580 -> 5.580; points 5.298 -> 5.298; shape -0.017 -> -0.017; Vegas 1.914 -> 1.914; gaps 4/4 -> 4/4
  2026-11-18_157033  par 0.04/0.15  minutes 5.068 -> 5.068; points 6.012 -> 6.012; shape -0.008 -> -0.008; Vegas 1.388 -> 1.388; gaps 1/3 -> 1/3
  2026-11-19_157138  par 0.04/0.15  minutes 4.261 -> 4.261; points 5.395 -> 5.395; shape 0.012 -> 0.012; Vegas 0.072 -> 0.072; gaps 3/4 -> 3/4
  2026-11-19_157139  par 0.04/0.15  minutes 4.789 -> 4.789; points 5.616 -> 5.616; shape 0.006 -> 0.006; Vegas 1.309 -> 1.309; gaps 3/5 -> 3/5
  2026-11-20_157013  par 0.06/0.15  minutes 4.489 -> 4.474; points 5.146 -> 5.146; shape 0.013 -> 0.013; Vegas 2.923 -> 2.968; gaps 3/6 -> 3/6
  2026-11-20_157015  par 0.00/0.15  minutes 4.780 -> 4.814; points 5.258 -> 5.281; shape 0.031 -> 0.030; Vegas 1.542 -> 1.557; gaps 9/16 -> 9/14
  pooled (mean of slates): minutes 4.764 -> 4.818 (better on 1 of 9); points 5.562 -> 5.675 (better on 1); |shape| 0.013 -> 0.014 (larger on 1); Vegas 1.814 -> 1.863; unexplained gaps 31 -> 30
  parameter on all slates: 0.04/0.15
```

### Banks: current vs out boost x2.3, same seeds, real results
```
Rule-free banks at bank noise 0.35, the same seeds, current minutes vs the candidate (out), scored on real points (5 nights with standings: thin).
  2026-11-16  cur      n  2000 own  256% top10   1.4% cash   4.0% pctl  30.6%  (players moved 1+ min: 0)
  2026-11-16  out      n  2000 own  256% top10   1.4% cash   4.0% pctl  30.6%  (players moved 1+ min: 0)
  2026-11-17  cur      n  2000 own  212% top10  16.4% cash  32.2% pctl  56.1%  (players moved 1+ min: 0)
  2026-11-17  out      n  2000 own  210% top10  16.4% cash  32.0% pctl  55.9%  (players moved 1+ min: 10)
  2026-11-18  cur      n  2000 own  287% top10   1.3% cash   2.9% pctl  31.3%  (players moved 1+ min: 0)
  2026-11-18  out      n  2000 own  283% top10   2.1% cash   4.4% pctl  34.4%  (players moved 1+ min: 22)
  2026-11-19e cur      n  2000 own  309% top10   2.9% cash  11.8% pctl  42.0%  (players moved 1+ min: 0)
  2026-11-19e out      n  2000 own  309% top10   2.9% cash  11.8% pctl  42.0%  (players moved 1+ min: 0)
  2026-11-19  cur      n  2000 own  209% top10   1.7% cash   5.0% pctl  19.6%  (players moved 1+ min: 0)
  2026-11-19  out      n  2000 own  201% top10   1.1% cash   3.5% pctl  14.2%  (players moved 1+ min: 49)
Pooled (mean of nights), nights better than current:
  cur      top10 4.7% cash 11.2% pctl 35.9%   better: top10 0, cash 0, pctl 0 of 5
  out      top10 4.8% cash 11.1% pctl 35.4%   better: top10 2, cash 1, pctl 1 of 5
```
