# Middle band and tighter cores (2026-11-28)

This covers the Friday review section 5 decisions, the operator's two candidates:
1. Aim for the middle on ownership.
2. Concentrate the fill on fewer cores, built on greens.

This is analysis only. The HOLD stands and nothing on the page, in the projections, ownership, field, cut or fill changed. Tags follow process.md rule 5. Contest types are the page's profile (`scripts/dk_contest_type.py`). Scripts and outputs are in [middle_band_cores_2026-11-28/](middle_band_cores_2026-11-28/): `mb.py`, `mb.js`, `mb.out` and `run.log`.

## Verdict

| Item | Result | Tag |
|---|---|---|
| Projected own_sum tracks real own_sum | Spearman **0.82 ± 0.03** per contest. **53%** land in the same quintile (chance 20%) and **90%** within one quintile. The extremes hold best: 80% of projected bottom-quintile lineups are really bottom quintile, and 60% at the top. | (measurement) |
| 1. Ownership band (drop low and high projected own_sum) | Fitted held out, the band picks 30th–70th every time. Its overall +5.57 ± 4.42 finish pct comes from qualifier contests, where it changed a pick on only one slate. On **flagships** it is **−5.98 ± 2.17, ahead on 1 of 9**; on **mains** +0.52 ± 0.66, 3 of 7. Dollars are worse or flat. | **NOISE** (worse on flagships) |
| 2a. Fewer cores (top 3 / 5 / 8 cores only) | **Mains: +7.4 to +8.5 finish pct, ahead on 6 of 7 at each K.** Top 8 is +7.74 ± 2.53, top 5 +7.42 ± 2.71. Dollars are flat (+$0.17 ± $0.50 a lineup). Flagships are mixed (−2.9 to +3.9, with dollars down by one lost cash). Qualifiers are worse (−12.5 to −15, 0 of 5). | **DIRECTIONAL** (mains, finish percentile only) |
| 2a. A higher core cap (30% / 50% for 15%) | +0.0 to +0.2 finish pct. Today's 15% cap barely binds on the pick. | NOISE (no effect) |
| 2b. Cores with 2+ greens | Green cores (`green2`) alone: +5.41 ± 3.76 overall (5 of 9), mains +5.20 (3 of 7), flagships +7.52 ± 6.74 (5 of 9). **Green cores, top 5 (`green2_top5`): mains +11.18 ± 3.42, ahead on 6 of 7.** Flagships +4.71 ± 3.09 (6 of 9). Qualifiers −15. Dollars flat on mains. | **DIRECTIONAL** (mains, finish percentile only) |
| 3. Band + cores together | The 20/80 band adds nothing to the cores. Mains: 20/80 band + green cores, top 5 is +11.51 ± 3.14, against +11.18 without the band. | NOISE (the band) |
| 3. The held flagship fill (top-half random), from each set | From the whole kept pool against the entered lineups: **+$6.02 ± $2.82 a lineup, ahead on 8 of 9**, consistent with proposal 1. From green cores it's +$9.18 ± $6.02 (7 of 9), and from 20/80 band + green cores +$13.23 ± $9.09 (7 of 9). Against top-half random from the whole kept pool, neither restriction clears noise: green cores +$3.16 ± $3.46, band + green cores +$7.20 ± $6.53. | proposal 1 unchanged; restrictions NOISE |

**In plain terms:**
- **The middle band doesn't help, and on flagships it hurts.** Dropping the chalkiest third of the pool costs flagship finishes, which fits the users study (the top users are chalkier, not less chalky).
- **Tighter cores help in the 20-max mains, on finish percentile.** Both the plain and the green-built version help, ahead on 6 of 7 slates. Cores built on greens are the strongest (+11 finish pct). Neither moves dollars beyond noise on 7 slates, and both are worse in qualifiers.
- These fit the operator's mains-only week. That week is the place to log them as PREVIOUS-vs-candidate if the operator wants (HELD).

## The data and what was replayed

- **Builds:** 9 saved builds with board values, a lock-time slate and simulated field on the mirror, and graded standings: 11-20 to 11-26, 46 contests (16 flagship, 25 main, 5 qualifier). The earlier builds have no board values. 11-27 isn't graded yet.
- **The fill:** each variant is the **page's own pick** (`DKSim.pick` through `mb.js`: Max ROI for mains and qualifiers, Max coverage for flagships, each contest on its own, the build's caps). It runs on the fixed simulated field at lock with the same player draws as the ownership-uncertainty study's variant A. The candidate set is cut down first (band, cores, greens).
- **Scoring:** the chosen lineups are scored on the real standings, as finish percentile and dollars a lineup a contest, per slate, by contest type. Every comparison is the same night, same contest and same machinery: variant − base, where base is the page's pick on the whole kept pool.
- **Projected own_sum** is the lineup's sum of our lock-time own (the night record's `own`). The band's percentiles are the kept pool's.
- **A core** is the lineup's 3 highest-salary players, as in the users study. "Top K cores" keeps only lineups whose core is among the K cores with the best board value of any of their lineups. Within those, the core cap is lifted to 100%, so the pick can concentrate.
- **Greens:** the **checks green flag recomputed at lock**. The lock-time projection file comes from battle-royale-research git, with `fr_best.py`'s `checks()`: score ≥ 5.2, 20+ minutes average and projected, not Out/Q/D. It found 7–22 greens a slate. The GREENS / green 3/4/5 tag forms aren't used: they mark lineups, not players, and exist only on some nights.
- **Not replayed:**
  - The page's cross-contest caps (the 60% night cap, Max contests per lineup).
  - The operator's hand edits after the pick.
  - Late swap.
  - **So base is not today's real fill.** Base − entered is +3.44 ± 3.53 finish pct overall and −3.37 ± 2.54 on mains (1 of 7). Each candidate is therefore graded against base on the same machinery, not against what was entered, except the held flagship fill, which is graded both ways.
- **Dollars are lumpy.** One flagship cash that the base pick caught and most restricted sets missed moves every flagship dollar row by about −$25 ± $24. Read finish percentile first on 9 slates.
- **What's fitted:** only the band's X/Y was fitted, held out by slate (`mb.out`). The core counts (3 / 5 / 8) and the green rule were fixed in advance and are reported as a grid, not picked after the fact. Several variants were looked at, so the mains result is tagged DIRECTIONAL, not PROVEN, even where a single row clears 2×SE (top 8 cores: +7.74 ± 2.53).

## 1. Projected vs real own_sum (the first check)

Every field entry with a complete lineup, per contest with 50+ such entries (73 contests on 16 slates; `field_lineups.csv`). Real own_sum uses the contest's real ownership counted from its lineups.

| Type | Contests | Spearman | Same quintile | Within one |
|---|---|---|---|---|
| all | 73 | 0.82 ± 0.03 | 53% ± 3 | 90% ± 2 |
| flagship | 22 | 0.80 ± 0.03 | 49% ± 3 | 88% ± 2 |
| main | 49 | 0.84 ± 0.03 | 54% ± 3 | 92% ± 2 |

Projected quintile (rows, 1 = least owned) → real quintile, row %:

| | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| Q1 | 80 | 17 | 3 | 0 | 0 |
| Q2 | 17 | 50 | 24 | 7 | 1 |
| Q3 | 3 | 23 | 39 | 27 | 9 |
| Q4 | 0 | 8 | 23 | 38 | 30 |
| Q5 | 0 | 2 | 11 | 28 | 60 |

So a band on projected own_sum does cut roughly the lineups it means to, especially at the low end. The band's failure below isn't a tracking problem.

## 2. The ownership band

Finish pct, band − base (page's pick), per slate. The full grid is in `mb.out`; selected rows here.

| Band (kept-pool percentiles) | All | Flagship | Main |
|---|---|---|---|
| 20–80 (the starting point) | +1.19 ± 1.39 (9), 5 | +0.48 ± 2.95 (9), 4 | +1.77 ± 2.31 (7), 3 |
| 30–70 (picked by every fold on all contests) | +5.57 ± 4.42 (9), 7 | +0.08 ± 3.94 (9), 4 | +3.08 ± 2.54 (7), 4 |
| 20–100 (lowest only) | +1.24 ± 1.11 (9), 4 | +1.74 ± 2.22 (9), 2 | +0.74 ± 0.83 (7), 4 |
| **Held out, fitted per type** | +5.57 ± 4.42 (9), 7 | **−5.98 ± 2.17 (9), 1** | +0.52 ± 0.66 (7), 3 |

- The "all" figure is carried by the qualifiers: +12.50 ± 12.50, a pick that changed on one of 5 slates.
- Fitted within flagships, the band flips sign held out.
- On dollars the bands cost −$0.2 to −$13 a lineup, mostly from the flagship cash.
- **NOISE**, and harmful on flagships.

## 3. Tighter cores and green cores

Finish pct, variant − base per slate, plus the level's spread over slates (SD, worst slate):

| Variant | Main | Flagship | Qualifier | Main slate SD / worst (base 13.3 / 34.8) |
|---|---|---|---|---|
| core cap 30% | +0.18 ± 0.13, 2 of 7 | +0.00 | +0.00 | 13.3 / 35.2 |
| top 3 cores | +8.51 ± 3.34, 6 of 7 | +3.92 ± 4.85, 6 of 9 | −15.00 ± 12.12, 0 of 5 | 17.7 / 38.0 |
| top 5 cores | +7.42 ± 2.71, 6 of 7 | −2.93 ± 6.08, 5 of 9 | −15.00 ± 12.12 | 15.8 / 37.5 |
| top 8 cores | +7.74 ± 2.53, 6 of 7 | −1.07 ± 4.52, 4 of 9 | −12.50 ± 12.50 | 15.3 / 40.8 |
| green cores (2+ greens) | +5.20 ± 3.94, 3 of 7 | +7.52 ± 6.74, 5 of 9 | −5.00 ± 5.00 | 15.8 / 37.7 |
| green cores, top 5 | **+11.18 ± 3.42, 6 of 7** | +4.71 ± 3.09, 6 of 9 | −15.00 ± 15.00 | 17.7 / 39.4 |

- **Variance:** fewer cores make the mains lumpier, with slate SD up from 13.3 to 15–18. But the worst slate got better, not worse (34.8 → 37.5–40.8), on these 7 slates.
- **Dollars on mains** are flat for every variant, from −$0.20 to +$0.31 ± about $0.50 a lineup. The finish gain hasn't turned into cashes yet on 7 slates.
- **Qualifiers** are worse with fewer cores on every variant.

## 4. Combinations, and the held flagship fill

- **Band + cores (mains):** 20/80 band + top 5 cores is +6.84 ± 3.37, and 20/80 band + green cores, top 5 is +11.51 ± 3.14. Neither beats the cores alone; the band adds nothing.
- **The held flagship fill:** top-half random by board value, 300 draws, from each set. Against the entered lineups:

| Set | Finish pct | $ a lineup |
|---|---|---|
| whole kept pool | −0.09 ± 3.59, 6 of 9 | **+6.02 ± 2.82, 8 of 9** |
| 20/80 band | −0.72 ± 3.39, 5 of 9 | +6.37 ± 2.64, 8 of 9 |
| green cores | +2.84 ± 6.35, 6 of 9 | +9.18 ± 6.02, 7 of 9 |
| 20/80 band + green cores | +3.91 ± 6.37, 5 of 9 | +13.23 ± 9.09, 7 of 9 |

None of the restrictions beats top-half random from the whole kept pool beyond noise. The best is band + green cores at +$7.20 ± $6.53, 5 of 9. Proposal 1 itself is unchanged.

## Watch list (HELD, for the operator's review)

| Candidate | Tag | What would settle it |
|---|---|---|
| Mains: fill from the top 5–8 cores only (core cap lifted within them) | DIRECTIONAL | The mains-only week. Log the page's pick on the whole kept pool (PREVIOUS) beside the top-5-cores pick each night. PROVEN needs dollars as well as finish pct ahead on 7 of 10 more main slates. |
| Mains: the same from green cores (2+ greens at lock) | DIRECTIONAL | As above, beside it. Greens are the checks flag at lock, recomputed the same way. |
| Ownership band | NOISE | Dropped. It costs flagship finishes. |
| Qualifiers: fewer cores | NOISE (worse) | Leave qualifiers on today's fill. |

**Note, 2026-11-28 (found while building the shadow log, `scripts/dk_core_shadow.py`): the restricted picks fill short.** Within 5 cores, the build's max exposure and min-unique caps leave the page's pick unable to fill every entry.

| Pick | Main entries filled |
|---|---|
| Top-5 cores | 287 of 429 |
| Top-5 green cores | 276 of 429 |
| Page's pick (base) | 412 of 429 |

The finish percentile and dollar figures above are per lineup picked, so they compare lineup quality, not a full portfolio. Net of fees on the lineups each pick would have entered, pooled over the 7 main slates:

| Pick | Net, % of fees |
|---|---|
| Top-5 green cores | +130.0% |
| Top-5 cores | +105.0% |
| Page's pick (base) | +98.6% |
| Entered | +27.6% |

A real version would need a fill rule for the rest: more cores, or the caps relaxed within the cores. The shadow log shows the shortfall nightly.
