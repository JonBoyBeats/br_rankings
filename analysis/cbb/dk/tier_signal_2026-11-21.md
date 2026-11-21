# Do the cut's tiers carry signal? (2026-11-21)

Question 1 from the coordinator. Every kept lineup of each saved build whose entered contests all have standings, scored on the night's real points, alone in each entered contest (averaged over them): percentile among the real entries, top 10%, top 1%, cash. Tiers as the page draws them (DKSim.tiers: A within 2 x sqrt(2) x sigma of the best, at most A / B / C).

**Tier source.** The builds saved no per-lineup tier. *Rebuilt*: the Cut step's idea board re-simmed (scripts/dk_tier_signal_study.js: each kept lineup alone in every entered contest on the slate's nights, 3,000, entries-weighted, the build's own gate and nights seed, the lock-time slate and simulated field). *Shown*: where the build saved its board (values per kept lineup and tier A's sigma, 2026-11-19 on), the tiers the page displayed, rebuilt from those. Projection overrides, marked-out players and minute shifts made on the page are not in a build before 11-20, so the rebuild can differ from what the page showed; the shown/rebuilt agreement below measures that.

Nights: 2026-11-16_156660, 2026-11-17_156663, 2026-11-18_157033, 2026-11-19_157138, 2026-11-19_157139 (5). Standings for 2026-11-20 (early 157013, main 157015) were not in yet.

**Rebuild check.** 2026-11-19_157138: rebuilt tiers agree with the page's on 95% of kept lineups; tier A 4 rebuilt vs 10 shown (11 from the saved values); value rank correlation 0.65; 2026-11-19_157139: rebuilt tiers agree with the page's on 84% of kept lineups; tier A 13 rebuilt vs 36 shown (33 from the saved values); value rank correlation 0.77. (The shown tier-A counts rebuilt from the saved values differ a little from the count the page saved: the values are rounded to cents, and the page's entries count came from the entries file rather than the portfolio sizes.)

## Rebuilt tiers

Per night (rates in %, each lineup's average over the night's entered contests):

**2026-11-16_156660** (1000 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 6 | 29.8 | 0.0 | 0.0 | 0.0 |
| B | 169 | 38.3 | 0.6 | 0.0 | 0.3 |
| C | 825 | 40.4 | 2.6 | 0.0 | 0.8 |

**2026-11-17_156663** (2000 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 3 | 26.7 | 0.0 | 0.0 | 0.0 |
| B | 16 | 36.4 | 0.0 | 0.0 | 6.2 |
| C | 1981 | 39.2 | 7.7 | 0.9 | 15.6 |

**2026-11-18_157033** (1500 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 5 | 76.3 | 20.0 | 20.0 | 52.0 |
| B | 9 | 55.6 | 11.1 | 0.0 | 17.8 |
| C | 1486 | 34.6 | 2.0 | 0.3 | 6.4 |

**2026-11-19_157138** (1521 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 4 | 59.7 | 0.0 | 0.0 | 25.0 |
| B | 35 | 57.5 | 3.6 | 0.0 | 23.6 |
| C | 1482 | 46.2 | 3.2 | 0.1 | 16.7 |

**2026-11-19_157139** (2098 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 13 | 37.6 | 0.0 | 0.0 | 24.6 |
| B | 166 | 25.8 | 2.0 | 0.2 | 8.1 |
| C | 1919 | 26.7 | 3.6 | 0.4 | 8.6 |

Nights in A > B > C order on percentile: 2 of 5 (other: 3).

Paired by night (percentile points, night as the unit):

| gap | nights | mean | sd across nights | positive | sign-test p |
|---|---|---|---|---|---|
| A-B | 5 | +3.3 | 13.1 | 3 of 5 | 1.00 |
| B-C | 5 | +5.3 | 10.5 | 2 of 5 | 1.00 |

Pooled, each night weighted equally (mean of the nightly tier means):

| tier | nights | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 5 | 46.0 | 4.0 | 4.0 | 20.3 |
| B | 5 | 42.7 | 3.5 | 0.0 | 11.2 |
| C | 5 | 37.4 | 3.8 | 0.3 | 9.6 |

Continuous check, every kept lineup (not just the handful in tier A): rank correlation of the sim's value with the real percentile, and the top 10% of kept lineups by value against the other 90% (percentile):

| night | rho | top 10% by value | other 90% | gap |
|---|---|---|---|---|
| 2026-11-16_156660 | -0.02 | 37.2 | 40.3 | -3.1 |
| 2026-11-17_156663 | +0.06 | 40.4 | 39.0 | +1.4 |
| 2026-11-18_157033 | +0.25 | 48.0 | 33.4 | +14.7 |
| 2026-11-19_157138 | +0.09 | 53.2 | 45.7 | +7.4 |
| 2026-11-19_157139 | +0.13 | 27.2 | 26.6 | +0.6 |

rho positive on 4 of 5 nights (sign-test p 0.38); mean rho +0.10; mean top-10% gap +4.2 points.

Within tier A, played (in the saved portfolios) against not played:

| night | played n | not n | played pctile / not | played top10% / not | played top1% / not | played cash% / not |
|---|---|---|---|---|---|---|
| 2026-11-16_156660 | 5 | 1 | 32.9 / 14.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| 2026-11-17_156663 | 3 | 0 | (one side empty) | | | |
| 2026-11-18_157033 | 5 | 0 | (one side empty) | | | |
| 2026-11-19_157138 | 4 | 0 | (one side empty) | | | |
| 2026-11-19_157139 | 5 | 8 | 43.1 / 34.3 | 0.0 / 0.0 | 0.0 / 0.0 | 28.0 / 22.5 |

Played minus not, percentile points: mean +13.9 over 2 nights, played ahead on 2 (sign-test p 0.50).

## Tiers as shown (saved boards only)

Per night (rates in %, each lineup's average over the night's entered contests):

**2026-11-19_157138** (1521 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 10 | 65.7 | 0.0 | 0.0 | 37.5 |
| B | 78 | 50.7 | 4.2 | 0.0 | 15.7 |
| C | 1433 | 46.1 | 3.1 | 0.1 | 16.8 |

**2026-11-19_157139** (2098 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 36 | 27.5 | 0.0 | 0.0 | 7.8 |
| B | 379 | 28.8 | 3.3 | 0.4 | 10.0 |
| C | 1683 | 26.2 | 3.6 | 0.4 | 8.4 |

Nights in A > B > C order on percentile: 1 of 2 (other: 1).

Paired by night (percentile points, night as the unit):

| gap | nights | mean | sd across nights | positive | sign-test p |
|---|---|---|---|---|---|
| A-B | 2 | +6.9 | 11.6 | 1 of 2 | 1.00 |
| B-C | 2 | +3.6 | 1.4 | 2 of 2 | 0.50 |

Pooled, each night weighted equally (mean of the nightly tier means):

| tier | nights | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 2 | 46.6 | 0.0 | 0.0 | 22.6 |
| B | 2 | 39.7 | 3.7 | 0.2 | 12.8 |
| C | 2 | 36.1 | 3.4 | 0.3 | 12.6 |

Continuous check, every kept lineup (not just the handful in tier A): rank correlation of the sim's value with the real percentile, and the top 10% of kept lineups by value against the other 90% (percentile):

| night | rho | top 10% by value | other 90% | gap |
|---|---|---|---|---|
| 2026-11-19_157138 | +0.02 | 51.6 | 45.9 | +5.7 |
| 2026-11-19_157139 | +0.11 | 27.6 | 26.6 | +1.0 |

rho positive on 2 of 2 nights (sign-test p 0.50); mean rho +0.07; mean top-10% gap +3.3 points.

Within tier A, played (in the saved portfolios) against not played:

| night | played n | not n | played pctile / not | played top10% / not | played top1% / not | played cash% / not |
|---|---|---|---|---|---|---|
| 2026-11-19_157138 | 6 | 4 | 61.5 / 72.1 | 0.0 / 0.0 | 0.0 / 0.0 | 33.3 / 43.8 |
| 2026-11-19_157139 | 13 | 23 | 18.5 / 32.5 | 0.0 / 0.0 | 0.0 / 0.0 | 7.7 / 7.8 |

Played minus not, percentile points: mean -12.3 over 2 nights, played ahead on 0 (sign-test p 0.50).

**Sample.** 5 nights. A sign test on this few nights cannot reach p < 0.05 unless every night agrees (5 of 5 gives p 0.06); read the per-night rows and their direction, not the pooled means alone.

