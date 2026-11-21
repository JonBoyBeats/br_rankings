# "Minutes is king" for cheap players: study, 2026-11-21

Analysis only: nothing on the page or in the projections changed. Scripts: `scripts/dk_cheap_minutes_study.py` (the
variants, accuracy, A2 lenses, scoring) and `scripts/dk_cheap_minutes_study.js` (the rule-free banks). **A thin sample:**
9 slates with box scores (11-16 to 11-20, early and main) for accuracy; 5 nights with standings on file (11-16 to 11-19,
the punt test's nights and contests) for the lineup part. The 11-20 standings and the 11-17 / 11-18 early slates' contests
aren't on file.

## The question and the variants

Players below a salary line get projected minutes x a flat rate; everyone above keeps our projection.

- Lines: salary under $5,000; and the bottom third of each slate by salary (players not Out).
- `flat`: the slate's projected DK points per minute (sum of projections / sum of projected minutes, players not Out:
  knowable at lock). `flatpos`: the same by position (G / F). `flatgrp`: the cheap group's own projected rate, added
  after the first run showed the slate rate (0.80) sits far above what cheap players score (0.58-0.62), so the test of
  dropping the per-player rate isn't only a test of raising the level. `shrink`: our per-player rate halfway to the
  slate's flat rate (0.5 x ours + 0.5 x minutes x flat).
- Accuracy uses each slate's banked `fp_dk` and `min_proj`; the banks use the lock-time slate through today's gate.json,
  as the punt and bank-noise tests did.

## Verdict

**No variant passes the A2 rule.** Dropping (or halving) our per-player rate for cheap players makes them less accurate
on every slate, and the lineups drawn from it do worse on real results. The one near-tie, the cheap group's own rate on
the bottom third (`flatgrp_third`), matches ours on accuracy (MAE 2.72 vs 2.73, better on 6 of 9 slates) but its banks are
worse pooled (top 10% 4.0% vs 4.7%, cash 9.9% vs 11.2%, better on 1 of 5 nights). The minutes half of the idea is right
(minutes drive at least half our cheap-player miss) but the fix is better minutes, not a flat rate: our per-player rate
carries real signal (cheap players' real rate is 0.58-0.62 a minute, ours 0.66-0.72, the slate's 0.80).

## Output

```
Slates with box scores: 9 (2026-11-16_156660, 2026-11-17_156662, 2026-11-17_156663, 2026-11-18_157032, 2026-11-18_157033, 2026-11-19_157138, 2026-11-19_157139, 2026-11-20_157013, 2026-11-20_157015). A thin sample: about ten nights.

== Cheap players: salary under $5,000 ==
  2026-11-16_156660  n 115  MAE cur 4.87 | flat 5.13 | flat by pos 5.13 | flat of the cheap group 4.90 | shrink 4.96
  2026-11-17_156662  n  39  MAE cur 4.28 | flat 4.84 | flat by pos 4.93 | flat of the cheap group 4.28 | shrink 4.54
  2026-11-17_156663  n 127  MAE cur 4.62 | flat 4.99 | flat by pos 5.01 | flat of the cheap group 4.85 | shrink 4.77
  2026-11-18_157032  n  40  MAE cur 3.79 | flat 4.14 | flat by pos 4.13 | flat of the cheap group 3.79 | shrink 3.96
  2026-11-18_157033  n  71  MAE cur 5.01 | flat 5.49 | flat by pos 5.46 | flat of the cheap group 5.18 | shrink 5.21
  2026-11-19_157138  n  58  MAE cur 4.08 | flat 4.42 | flat by pos 4.38 | flat of the cheap group 4.14 | shrink 4.20
  2026-11-19_157139  n 108  MAE cur 4.20 | flat 4.55 | flat by pos 4.51 | flat of the cheap group 4.18 | shrink 4.33
  2026-11-20_157013  n  55  MAE cur 3.90 | flat 4.23 | flat by pos 4.23 | flat of the cheap group 3.96 | shrink 4.07
  2026-11-20_157015  n 157  MAE cur 3.98 | flat 4.31 | flat by pos 4.29 | flat of the cheap group 4.14 | shrink 4.12
  slates where the variant's MAE beats ours: flat_5k 0 of 9, flatpos_5k 0 of 9, flatgrp_5k 2 of 9, shrink_5k 0 of 9
  pooled (770 player-games over 9 slates):
    cur            MAE 4.35  corr 0.646  bias (actual-proj) -0.78   played only: MAE 5.46 bias +0.54 (n 458)
    flat_5k        MAE 4.71  corr 0.623  bias (actual-proj) -1.63   played only: MAE 5.73 bias -0.55 (n 458)
    flatpos_5k     MAE 4.70  corr 0.622  bias (actual-proj) -1.63   played only: MAE 5.71 bias -0.55 (n 458)
    flatgrp_5k     MAE 4.45  corr 0.623  bias (actual-proj) -0.78   played only: MAE 5.55 bias +0.61 (n 458)
    shrink_5k      MAE 4.50  corr 0.641  bias (actual-proj) -1.20   played only: MAE 5.54 bias -0.01 (n 458)
  our misses on the cheap players who played (n 458): squared error from minutes 45%, from rate 42%, the cross term +12%
  their real points per minute 0.620 (median 0.608) vs our rate 0.715 vs the slates' flat rate 0.801 (mean); DNPs 312, our miss on them 2.72 a player
  our biggest misses:
    2026-11-18_157033  Keanu Dawes              $ 4200  ours  14.5  flat  12.4  actual  41.0  min 15.2 proj / 31.0 real
    2026-11-19_157139  Trey Parker              $ 4800  ours  13.5  flat  14.8  actual  38.2  min 17.9 proj / 23.0 real
    2026-11-20_157015  Terry Copeland Jr.       $ 4600  ours  10.8  flat  11.5  actual  34.8  min 14.6 proj / 25.0 real
    2026-11-18_157033  Ryan Agarwal             $ 4700  ours  13.9  flat  14.9  actual  36.0  min 18.3 proj / 28.0 real
    2026-11-17_156663  Davion Thompson          $ 3800  ours  17.1  flat  19.9  actual  39.0  min 23.9 proj / 34.0 real
    2026-11-19_157138  Owen Freeman             $ 3900  ours  11.9  flat   9.2  actual  33.8  min 11.4 proj / 22.0 real
    2026-11-19_157139  Darin Smith Jr.          $ 4000  ours  12.7  flat  13.0  actual  34.2  min 15.7 proj / 26.0 real
    2026-11-16_156660  Dennis Johnson III       $ 4500  ours   9.3  flat  15.5  actual  30.8  min 19.8 proj / 36.0 real
  the flat variant's biggest misses:
    2026-11-18_157033  Keanu Dawes              $ 4200  ours  14.5  flat  12.4  actual  41.0  min 15.2 proj / 31.0 real
    2026-11-19_157138  Owen Freeman             $ 3900  ours  11.9  flat   9.2  actual  33.8  min 11.4 proj / 22.0 real
    2026-11-19_157139  Trey Parker              $ 4800  ours  13.5  flat  14.8  actual  38.2  min 17.9 proj / 23.0 real
    2026-11-20_157015  Terry Copeland Jr.       $ 4600  ours  10.8  flat  11.5  actual  34.8  min 14.6 proj / 25.0 real
    2026-11-16_156660  Isaiah Miranda           $ 4900  ours  14.4  flat  12.1  actual  34.2  min 15.4 proj / 27.0 real
    2026-11-20_157015  Simeon Wilcher           $ 4600  ours  16.0  flat  21.4  actual  -0.5  min 27.2 proj /  5.0 real
    2026-11-19_157139  Darin Smith Jr.          $ 4000  ours  12.7  flat  13.0  actual  34.2  min 15.7 proj / 26.0 real
    2026-11-18_157033  Ryan Agarwal             $ 4700  ours  13.9  flat  14.9  actual  36.0  min 18.3 proj / 28.0 real

== Cheap players: the bottom third of each slate by salary ==
  2026-11-16_156660  n  57  MAE cur 3.87 | flat 4.51 | flat by pos 4.50 | flat of the cheap group 4.11 | shrink 4.18
  2026-11-17_156662  n  20  MAE cur 2.63 | flat 3.24 | flat by pos 3.21 | flat of the cheap group 2.66 | shrink 2.94
  2026-11-17_156663  n  65  MAE cur 2.81 | flat 3.16 | flat by pos 3.19 | flat of the cheap group 2.74 | shrink 2.98
  2026-11-18_157032  n  20  MAE cur 3.00 | flat 3.65 | flat by pos 3.55 | flat of the cheap group 3.09 | shrink 3.33
  2026-11-18_157033  n  37  MAE cur 3.49 | flat 4.04 | flat by pos 4.07 | flat of the cheap group 3.34 | shrink 3.75
  2026-11-19_157138  n  29  MAE cur 2.00 | flat 2.21 | flat by pos 2.20 | flat of the cheap group 1.92 | shrink 2.10
  2026-11-19_157139  n  56  MAE cur 2.40 | flat 2.78 | flat by pos 2.77 | flat of the cheap group 2.38 | shrink 2.59
  2026-11-20_157013  n  28  MAE cur 2.64 | flat 2.82 | flat by pos 2.82 | flat of the cheap group 2.61 | shrink 2.73
  2026-11-20_157015  n  76  MAE cur 1.93 | flat 2.20 | flat by pos 2.21 | flat of the cheap group 1.90 | shrink 2.06
  slates where the variant's MAE beats ours: flat_third 0 of 9, flatpos_third 0 of 9, flatgrp_third 6 of 9, shrink_third 0 of 9
  pooled (388 player-games over 9 slates):
    cur            MAE 2.73  corr 0.249  bias (actual-proj) -1.51   played only: MAE 3.52 bias +0.72 (n 111)
    flat_third     MAE 3.13  corr 0.253  bias (actual-proj) -2.12   played only: MAE 3.70 bias -0.17 (n 111)
    flatpos_third  MAE 3.13  corr 0.252  bias (actual-proj) -2.13   played only: MAE 3.69 bias -0.17 (n 111)
    flatgrp_third  MAE 2.72  corr 0.252  bias (actual-proj) -1.51   played only: MAE 3.56 bias +0.67 (n 111)
    shrink_third   MAE 2.93  corr 0.253  bias (actual-proj) -1.82   played only: MAE 3.60 bias +0.28 (n 111)
  our misses on the cheap players who played (n 111): squared error from minutes 55%, from rate 44%, the cross term +1%
  their real points per minute 0.579 (median 0.500) vs our rate 0.662 vs the slates' flat rate 0.801 (mean); DNPs 277, our miss on them 2.41 a player
  our biggest misses:
    2026-11-19_157139  Tyler Harris             $ 3000  ours  19.5  flat  19.2  actual   0.0  min 23.3 proj /  0.0 real
    2026-11-18_157033  Eddie Ricks III          $ 3000  ours  17.5  flat  18.8  actual   0.0  min 23.1 proj /  0.0 real
    2026-11-18_157033  Tyler Harris             $ 3000  ours  17.3  flat  17.6  actual   0.0  min 21.7 proj /  0.0 real
    2026-11-17_156663  Tyler Harris             $ 3000  ours  15.7  flat  16.9  actual   0.0  min 20.3 proj /  0.0 real
    2026-11-19_157138  Jones Lay                $ 3000  ours   0.3  flat   0.5  actual  14.8  min  0.6 proj / 18.0 real
    2026-11-16_156660  Donovan Williams Jr.     $ 3000  ours   5.5  flat   6.9  actual  19.8  min  8.8 proj / 14.0 real
    2026-11-20_157015  Jackson Ball             $ 3100  ours   3.2  flat   4.9  actual  16.5  min  6.3 proj / 22.0 real
    2026-11-17_156663  Kohl Rosario             $ 3000  ours  12.4  flat  14.2  actual   0.0  min 17.0 proj /  3.0 real
  the flat variant's biggest misses:
    2026-11-19_157139  Tyler Harris             $ 3000  ours  19.5  flat  19.2  actual   0.0  min 23.3 proj /  0.0 real
    2026-11-18_157033  Eddie Ricks III          $ 3000  ours  17.5  flat  18.8  actual   0.0  min 23.1 proj /  0.0 real
    2026-11-18_157033  Tyler Harris             $ 3000  ours  17.3  flat  17.6  actual   0.0  min 21.7 proj /  0.0 real
    2026-11-17_156663  Tyler Harris             $ 3000  ours  15.7  flat  16.9  actual   0.0  min 20.3 proj /  0.0 real
    2026-11-19_157138  Jones Lay                $ 3000  ours   0.3  flat   0.5  actual  14.8  min  0.6 proj / 18.0 real
    2026-11-17_156663  Amir Jenkins             $ 3000  ours  11.9  flat  14.3  actual   0.0  min 17.1 proj /  0.0 real
    2026-11-17_156663  Kohl Rosario             $ 3000  ours  12.4  flat  14.2  actual   0.0  min 17.0 proj /  3.0 real
    2026-11-16_156660  Andrew Osasuyi           $ 3300  ours   8.8  flat   6.0  actual  20.0  min  7.7 proj / 10.0 real

== A2 lenses, every slate (points MAE all players; |shape| top-2 ours-recent; Vegas slope of team points on implied totals; 2 sd salary gaps unexplained). Minutes are untouched, so the minutes lens can't move ==
  flat_5k        points MAE 5.562 -> 5.810 (better on 0 of 9); |shape| 0.013 -> 0.017 (larger on 4); Vegas slope 1.814 -> 1.070; unexplained gaps +0 in all
  flatpos_5k     points MAE 5.562 -> 5.808 (better on 0 of 9); |shape| 0.013 -> 0.016 (larger on 5); Vegas slope 1.814 -> 1.091; unexplained gaps -2 in all
  flatgrp_5k     points MAE 5.562 -> 5.612 (better on 2 of 9); |shape| 0.013 -> 0.013 (larger on 3); Vegas slope 1.814 -> 1.212; unexplained gaps +4 in all
  shrink_5k      points MAE 5.562 -> 5.667 (better on 0 of 9); |shape| 0.013 -> 0.013 (larger on 4); Vegas slope 1.814 -> 1.442; unexplained gaps -4 in all
  flat_third     points MAE 5.562 -> 5.705 (better on 0 of 9); |shape| 0.013 -> 0.014 (larger on 4); Vegas slope 1.814 -> 1.647; unexplained gaps -1 in all
  flatpos_third  points MAE 5.562 -> 5.701 (better on 0 of 9); |shape| 0.013 -> 0.014 (larger on 4); Vegas slope 1.814 -> 1.654; unexplained gaps -1 in all
  flatgrp_third  points MAE 5.562 -> 5.560 (better on 6 of 9); |shape| 0.013 -> 0.013 (larger on 3); Vegas slope 1.814 -> 1.669; unexplained gaps +2 in all
  shrink_third   points MAE 5.562 -> 5.632 (better on 0 of 9); |shape| 0.013 -> 0.013 (larger on 3); Vegas slope 1.814 -> 1.731; unexplained gaps +0 in all
```

```
Rule-free banks at bank noise 0.35, the same seeds under each projection, scored on real points (5 nights with standings: thin).
night       variant            n   proj   own  top10%  cash%   pctl  cheap
2026-11-16  cur             2000  215.4  256%    1.4%   4.0%  30.6%      -
2026-11-16  flat_5k         2000  208.5  226%    1.4%   3.6%  29.5%   2.23
2026-11-16  flatpos_5k      2000  208.5  226%    1.4%   3.8%  29.5%   2.23
2026-11-16  flatgrp_5k      2000  207.4  221%    1.4%   3.8%  28.5%   1.85
2026-11-16  shrink_5k       2000  212.6  240%    1.8%   4.3%  31.8%   2.20
2026-11-16  flat_third      2000  212.7  251%    1.1%   2.5%  25.4%   0.64
2026-11-16  flatpos_third   2000  212.7  251%    1.1%   2.5%  25.3%   0.64
2026-11-16  flatgrp_third   2000  214.8  256%    1.6%   3.8%  30.2%   0.18
2026-11-16  shrink_third    2000  214.9  255%    1.2%   3.4%  29.1%   0.32
2026-11-17  cur             2000  213.4  212%   16.4%  32.2%  56.1%      -
2026-11-17  flat_5k         2000  207.7  207%   13.0%  25.9%  49.7%   1.88
2026-11-17  flatpos_5k      2000  207.1  208%   10.9%  22.6%  47.1%   1.88
2026-11-17  flatgrp_5k      2000  209.1  213%   11.0%  23.2%  47.7%   1.48
2026-11-17  shrink_5k       2000  212.0  211%   16.3%  32.4%  55.8%   1.55
2026-11-17  flat_third      2000  208.2  216%   10.3%  21.6%  45.9%   0.65
2026-11-17  flatpos_third   2000  207.9  217%   10.0%  21.1%  45.3%   0.69
2026-11-17  flatgrp_third   2000  211.7  214%   14.1%  28.4%  52.3%   0.23
2026-11-17  shrink_third    2000  212.5  213%   15.0%  30.2%  53.9%   0.12
2026-11-18  cur             2000  198.7  287%    1.3%   2.9%  31.3%      -
2026-11-18  flat_5k         2000  192.3  260%    0.1%   0.9%  30.3%   2.04
2026-11-18  flatpos_5k      2000  193.0  267%    0.1%   0.8%  27.1%   1.99
2026-11-18  flatgrp_5k      2000  193.9  266%    0.3%   1.1%  29.2%   1.63
2026-11-18  shrink_5k       2000  197.1  282%    0.4%   1.4%  30.2%   1.56
2026-11-18  flat_third      2000  194.2  275%    0.2%   0.9%  25.5%   1.27
2026-11-18  flatpos_third   2000  194.3  277%    0.2%   0.8%  24.1%   1.37
2026-11-18  flatgrp_third   2000  195.2  265%    1.1%   3.0%  32.3%   0.58
2026-11-18  shrink_third    2000  198.0  288%    0.7%   1.8%  29.5%   0.86
2026-11-19e cur             2000  200.1  309%    2.9%  11.8%  42.0%      -
2026-11-19e flat_5k         2000  196.9  290%    2.6%  11.8%  40.3%   2.55
2026-11-19e flatpos_5k      2000  196.1  283%    2.2%  11.6%  40.6%   2.52
2026-11-19e flatgrp_5k      2000  196.3  286%    2.5%  11.8%  41.1%   2.31
2026-11-19e shrink_5k       2000  199.3  303%    2.8%  12.3%  41.7%   2.40
2026-11-19e flat_third      2000  197.2  300%    2.1%  10.4%  40.1%   0.36
2026-11-19e flatpos_third   2000  197.9  302%    2.2%  10.7%  40.4%   0.29
2026-11-19e flatgrp_third   2000  199.1  307%    2.5%  11.3%  41.0%   0.16
2026-11-19e shrink_third    2000  199.7  308%    2.6%  11.7%  41.4%   0.07
2026-11-19  cur             2000  204.2  209%    1.7%   5.0%  19.6%      -
2026-11-19  flat_5k         2000  199.0  194%    0.9%   2.5%  14.0%   1.60
2026-11-19  flatpos_5k      2000  198.5  192%    0.7%   2.1%  13.1%   1.55
2026-11-19  flatgrp_5k      2000  199.8  196%    0.9%   2.8%  14.8%   1.42
2026-11-19  shrink_5k       2000  202.6  204%    1.2%   4.0%  17.6%   1.38
2026-11-19  flat_third      2000  200.8  201%    0.5%   1.8%  12.9%   0.80
2026-11-19  flatpos_third   2000  200.1  199%    0.4%   1.6%  12.0%   0.91
2026-11-19  flatgrp_third   2000  202.0  204%    0.9%   2.9%  15.1%   0.58
2026-11-19  shrink_third    2000  203.3  207%    1.3%   4.0%  17.4%   0.33

Pooled (mean of the nights) and nights better than our projection:
  cur            top10 4.7% cash 11.2% pctl 35.9%   better: top10 0, cash 0, pctl 0 of 5
  flat_5k        top10 3.6% cash 9.0% pctl 32.8%   better: top10 0, cash 1, pctl 0 of 5
  flatpos_5k     top10 3.1% cash 8.1% pctl 31.5%   better: top10 0, cash 0, pctl 0 of 5
  flatgrp_5k     top10 3.2% cash 8.5% pctl 32.3%   better: top10 0, cash 1, pctl 0 of 5
  shrink_5k      top10 4.5% cash 10.9% pctl 35.4%   better: top10 1, cash 3, pctl 1 of 5
  flat_third     top10 2.9% cash 7.4% pctl 30.0%   better: top10 0, cash 0, pctl 0 of 5
  flatpos_third  top10 2.8% cash 7.3% pctl 29.4%   better: top10 0, cash 0, pctl 0 of 5
  flatgrp_third  top10 4.0% cash 9.9% pctl 34.2%   better: top10 1, cash 1, pctl 1 of 5
  shrink_third   top10 4.2% cash 10.2% pctl 34.3%   better: top10 0, cash 0, pctl 0 of 5
```

Columns: `cheap` = cheap players per lineup in the variant's bank; `pctl` = the lineup's real points percentile in the
contest's real field; top 10% / cash = share of lineups at or over the contest's real lines.

Lenses not measured: ownership shape (the field build's ownership against real) would need the nightly field builder
rerun on each variant's projections; not run here. The minutes lens can't move (minutes untouched).
