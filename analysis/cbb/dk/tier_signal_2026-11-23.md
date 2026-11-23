# Do the cut's tiers carry signal? (rerun 2026-11-23, 7 nights)

Question 1 from the coordinator. Every kept lineup of each saved build whose entered contests all have standings, scored on the night's real points, alone in each entered contest (averaged over them): percentile among the real entries, top 10%, top 1%, cash. Tiers as the page draws them (DKSim.tiers: A within 2 x sqrt(2) x sigma of the best, at most A / B / C).

**Tier source.** The builds saved no per-lineup tier. *Rebuilt*: the Cut step's idea board re-simmed (scripts/dk_tier_signal_study.js: each kept lineup alone in every entered contest on the slate's nights, 3,000, entries-weighted, the build's own gate and nights seed, the lock-time slate and simulated field). *Shown*: where the build saved its board (values per kept lineup and tier A's sigma, 2026-11-19 on), the tiers the page displayed, rebuilt from those. Projection overrides, marked-out players and minute shifts made on the page are not in a build before 11-20, so the rebuild can differ from what the page showed; the shown/rebuilt agreement below measures that.

Nights: 2026-11-16_156660, 2026-11-17_156663, 2026-11-18_157033, 2026-11-19_157138, 2026-11-19_157139, 2026-11-20_157013, 2026-11-20_157015 (7): every saved build whose entered contests all have standings.

**Rebuild check.** 2026-11-19_157138: rebuilt tiers agree with the page's on 95% of kept lineups; tier A 4 rebuilt vs 10 shown (11 from the saved values); value rank correlation 0.65; 2026-11-19_157139: rebuilt tiers agree with the page's on 84% of kept lineups; tier A 13 rebuilt vs 36 shown (33 from the saved values); value rank correlation 0.77; 2026-11-20_157013: rebuilt tiers agree with the page's on 95% of kept lineups; tier A 6 rebuilt vs 12 shown (12 from the saved values); value rank correlation 0.60; 2026-11-20_157015: rebuilt tiers agree with the page's on 90% of kept lineups; tier A 16 rebuilt vs 21 shown (23 from the saved values); value rank correlation 0.61. (The shown tier-A counts rebuilt from the saved values differ a little from the count the page saved: the values are rounded to cents, and the page's entries count came from the entries file rather than the portfolio sizes.)

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

**2026-11-20_157013** (2002 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 6 | 92.5 | 76.7 | 20.0 | 96.7 |
| B | 40 | 73.8 | 34.5 | 11.0 | 49.0 |
| C | 1956 | 46.5 | 10.0 | 1.3 | 19.4 |

**2026-11-20_157015** (2278 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 16 | 59.4 | 35.0 | 1.2 | 37.5 |
| B | 139 | 61.8 | 16.8 | 4.6 | 37.7 |
| C | 2123 | 58.2 | 16.7 | 4.3 | 34.7 |

Nights in A > B > C order on percentile: 3 of 7 (other: 4).

Paired by night (percentile points, night as the unit):

| gap | nights | mean | sd across nights | positive | sign-test p |
|---|---|---|---|---|---|
| A-B | 7 | +4.7 | 12.5 | 4 of 7 | 1.00 |
| B-C | 7 | +8.2 | 12.0 | 4 of 7 | 1.00 |

Pooled, each night weighted equally (mean of the nightly tier means):

| tier | nights | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 7 | 54.6 | 18.8 | 5.9 | 33.7 |
| B | 7 | 49.9 | 9.8 | 2.3 | 20.4 |
| C | 7 | 41.7 | 6.5 | 1.0 | 14.6 |

Continuous check, every kept lineup (not just the handful in tier A): rank correlation of the sim's value with the real percentile, and the top 10% of kept lineups by value against the other 90% (percentile):

| night | rho | top 10% by value | other 90% | gap |
|---|---|---|---|---|
| 2026-11-16_156660 | -0.02 | 37.2 | 40.3 | -3.1 |
| 2026-11-17_156663 | +0.06 | 40.4 | 39.0 | +1.4 |
| 2026-11-18_157033 | +0.25 | 48.0 | 33.4 | +14.7 |
| 2026-11-19_157138 | +0.09 | 53.2 | 45.7 | +7.4 |
| 2026-11-19_157139 | +0.13 | 27.2 | 26.6 | +0.6 |
| 2026-11-20_157013 | +0.44 | 68.3 | 44.9 | +23.4 |
| 2026-11-20_157015 | +0.05 | 61.5 | 58.0 | +3.4 |

rho positive on 6 of 7 nights (sign-test p 0.12); mean rho +0.14; mean top-10% gap +6.8 points.

Within tier A, played (in the saved portfolios) against not played:

| night | played n | not n | played pctile / not | played top10% / not | played top1% / not | played cash% / not |
|---|---|---|---|---|---|---|
| 2026-11-16_156660 | 5 | 1 | 32.9 / 14.0 | 0.0 / 0.0 | 0.0 / 0.0 | 0.0 / 0.0 |
| 2026-11-17_156663 | 3 | 0 | (one side empty) | | | |
| 2026-11-18_157033 | 5 | 0 | (one side empty) | | | |
| 2026-11-19_157138 | 4 | 0 | (one side empty) | | | |
| 2026-11-19_157139 | 5 | 8 | 43.1 / 34.3 | 0.0 / 0.0 | 0.0 / 0.0 | 28.0 / 22.5 |
| 2026-11-20_157013 | 4 | 2 | 92.0 / 93.6 | 75.0 / 80.0 | 25.0 / 10.0 | 95.0 / 100.0 |
| 2026-11-20_157015 | 5 | 11 | 81.2 / 49.6 | 52.0 / 27.3 | 0.0 / 1.8 | 60.0 / 27.3 |

Played minus not, percentile points: mean +14.4 over 4 nights, played ahead on 3 (sign-test p 0.62).

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

**2026-11-20_157013** (2002 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 12 | 55.0 | 3.3 | 0.0 | 16.7 |
| B | 65 | 47.1 | 7.1 | 0.0 | 16.6 |
| C | 1925 | 47.2 | 10.8 | 1.6 | 20.3 |

**2026-11-20_157015** (2278 kept)

| tier | n | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 21 | 70.8 | 31.4 | 4.8 | 46.7 |
| B | 136 | 69.4 | 27.8 | 8.7 | 50.6 |
| C | 2121 | 57.6 | 16.0 | 4.0 | 33.8 |

Nights in A > B > C order on percentile: 2 of 4 (other: 2).

Paired by night (percentile points, night as the unit):

| gap | nights | mean | sd across nights | positive | sign-test p |
|---|---|---|---|---|---|
| A-B | 4 | +5.8 | 7.3 | 3 of 4 | 0.62 |
| B-C | 4 | +4.7 | 5.1 | 3 of 4 | 0.62 |

Pooled, each night weighted equally (mean of the nightly tier means):

| tier | nights | pctile | top10% | top1% | cash% |
|---|---|---|---|---|---|
| A | 4 | 54.8 | 8.7 | 1.2 | 27.2 |
| B | 4 | 49.0 | 10.6 | 2.3 | 23.2 |
| C | 4 | 44.3 | 8.4 | 1.5 | 19.8 |

Continuous check, every kept lineup (not just the handful in tier A): rank correlation of the sim's value with the real percentile, and the top 10% of kept lineups by value against the other 90% (percentile):

| night | rho | top 10% by value | other 90% | gap |
|---|---|---|---|---|
| 2026-11-19_157138 | +0.02 | 51.6 | 45.9 | +5.7 |
| 2026-11-19_157139 | +0.11 | 27.6 | 26.6 | +1.0 |
| 2026-11-20_157013 | +0.04 | 51.1 | 46.8 | +4.3 |
| 2026-11-20_157015 | +0.13 | 67.7 | 57.4 | +10.4 |

rho positive on 4 of 4 nights (sign-test p 0.12); mean rho +0.07; mean top-10% gap +5.3 points.

Within tier A, played (in the saved portfolios) against not played:

| night | played n | not n | played pctile / not | played top10% / not | played top1% / not | played cash% / not |
|---|---|---|---|---|---|---|
| 2026-11-19_157138 | 6 | 4 | 61.5 / 72.1 | 0.0 / 0.0 | 0.0 / 0.0 | 33.3 / 43.8 |
| 2026-11-19_157139 | 13 | 23 | 18.5 / 32.5 | 0.0 / 0.0 | 0.0 / 0.0 | 7.7 / 7.8 |
| 2026-11-20_157013 | 6 | 6 | 59.9 / 50.2 | 3.3 / 3.3 | 0.0 / 0.0 | 16.7 / 16.7 |
| 2026-11-20_157015 | 13 | 8 | 70.8 / 70.8 | 35.4 / 25.0 | 0.0 / 12.5 | 46.2 / 47.5 |

Played minus not, percentile points: mean -3.7 over 4 nights, played ahead on 1 (sign-test p 0.62).

**Sample.** 7 nights. A sign test on this few nights cannot reach p < 0.05 unless every night agrees (5 of 5 gives p 0.06); read the per-night rows and their direction, not the pooled means alone.

