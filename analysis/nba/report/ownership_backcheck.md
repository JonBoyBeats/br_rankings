# Composite ownership: backcheck

**Read (2026-11-13):** the composite doesn't beat the current curve at 2pm. ADP is itself a running average of where the field has been drafting a player, so its rank at 2pm already carries what the hour-by-hour build adds up, and the build adds noise from earlier hours' ADPs. Keyed to ADP values it misses most late (a slate's length moves what an ADP of 34 means); keyed to rank it comes within 0.3 points overall but loses in the 10-90% band, where ownership matters. The live hourly counts change nothing (by rank: 2.2 with or without them). Not wired in.

Every night with contests on file, the flagship contest, at 2pm PT. Actual: pre-swap drafted% from the rosters (the share of pods that took him; picks carrying a draft ADP), players who played. Each night scored with the chance curve and fill shape fitted on the other nights of its pod size. Errors in percentage points of drafted% (mean absolute; bias = modeled minus actual).

- composite: the new build as specified, the chance keyed to his ADP at each hour (live hourly counts where on file, else the fill shape)
- composite by rank: the same, the chance keyed to his ADP rank at each hour
- by rank, fill shape only: that with the typical fill shape on every night (no live counts)
- current, as stored: field_model.json's drafted% by ADP rank (fitted on every night, these included)
- current, refitted: the same curve refitted without the night

23 nights (18 six-drafter, 5 four-drafter; 9 with live hourly counts), 1671 player-nights.

|  | n | composite | composite by rank | by rank, fill shape only | current, as stored | current, refitted |
|---|---|---|---|---|---|---|
| **all** | 1671 | 2.5 (-0.0) | 2.2 (-0.1) | 2.2 (-0.1) | 1.9 (+0.7) | 1.9 (-0.7) |
| 6-drafter | 1449 | 2.4 (-0.1) | 2.2 (-0.1) | 2.2 (-0.1) | 2.0 (+0.8) | 1.9 (-0.7) |
| 4-drafter | 222 | 2.6 (+0.2) | 2.0 (-0.1) | 2.0 (-0.1) | 1.9 (+0.2) | 2.0 (-0.5) |
| nights with live counts | 676 | 2.5 (-0.2) | 2.2 (-0.1) | 2.2 (-0.2) | 1.9 (+0.8) | 1.9 (-0.8) |
| actual 10-90% (where it matters) | 223 | 10.5 (-3.5) | 9.6 (-1.6) | 9.6 (-1.8) | 8.8 (+3.6) | 8.2 (-3.9) |

**By tier (the button's afternoon tier)**

| tier | n | composite | composite by rank | by rank, fill shape only | current, as stored | current, refitted |
|---|---|---|---|---|---|---|
| T1 | 77 | 0.0 (+0.0) | 0.0 (+0.0) | 0.0 (+0.0) | 0.0 (+0.0) | 0.1 (-0.1) |
| T2 | 218 | 0.5 (+0.5) | 0.5 (+0.5) | 0.5 (+0.5) | 0.5 (+0.5) | 0.9 (+0.0) |
| T3 | 146 | 0.1 (-0.0) | 0.1 (-0.1) | 0.1 (-0.1) | 0.0 (+0.0) | 0.1 (-0.0) |
| T4 | 169 | 2.5 (-1.3) | 2.9 (-2.2) | 2.9 (-2.2) | 1.6 (+0.0) | 2.6 (-2.1) |
| T5 | 1013 | 3.5 (+0.1) | 3.0 (+0.1) | 3.0 (+0.0) | 2.8 (+1.1) | 2.5 (-0.8) |
| no tier (unpriced at the PM lock) | 48 | 1.7 (-0.7) | 1.4 (+0.1) | 1.4 (+0.1) | 1.3 (+0.3) | 1.4 (-0.5) |

**By actual drafted%**

| band | n | composite | composite by rank | by rank, fill shape only | current, as stored | current, refitted |
|---|---|---|---|---|---|---|
| 99.5%+ | 563 | 0.1 (-0.1) | 0.2 (-0.2) | 0.2 (-0.2) | 0.1 (-0.1) | 0.3 (-0.3) |
| 90-99.5% | 76 | 4.0 (-2.4) | 4.9 (-3.8) | 5.0 (-4.0) | 2.6 (-0.8) | 5.0 (-4.2) |
| 60-90% | 67 | 10.7 (-4.1) | 11.1 (-3.5) | 11.1 (-3.5) | 8.5 (+5.3) | 10.2 (-5.0) |
| 30-60% | 69 | 13.1 (-3.2) | 11.9 (+0.2) | 11.7 (-0.1) | 13.0 (+6.4) | 9.5 (-3.9) |
| 10-30% | 87 | 8.2 (-3.2) | 6.7 (-1.6) | 6.7 (-1.6) | 5.8 (+0.1) | 5.6 (-2.9) |
| under 10% | 809 | 1.7 (+1.2) | 1.3 (+0.7) | 1.3 (+0.7) | 1.3 (+0.7) | 1.0 (+0.2) |

In the 10-90% band, night by night, the composite by rank was closer than the refitted current curve on 7 of 23 nights (by ADP: 4).

**Biggest misses, composite (last 3 nights)**

| night | player | ADP at 2pm | actual | composite | by rank | current |
|---|---|---|---|---|---|---|
| 2026-11-12 | Collin Murray-Boyles | 34.2 | 78% | 32% | 46% | 74% |
| 2026-11-11 | Damian Lillard | 34.1 | 39% | 70% | 70% | 68% |
| 2026-11-12 | Dillon Brooks | 35.0 | 61% | 34% | 51% | 68% |
| 2026-11-10 | Isaiah Collier | 35.0 | 44% | 22% | 29% | 58% |
| 2026-11-12 | Kevin Huerter | 35.7 | 27% | 6% | 19% | 33% |
| 2026-11-11 | Dejounte Murray | 34.5 | 52% | 31% | 33% | 58% |
| 2026-11-11 | Desmond Bane | 32.4 | 71% | 92% | 95% | 95% |
| 2026-11-12 | Moussa Diabate | 32.4 | 96% | 79% | 72% | 89% |
| 2026-11-11 | Jamal Shead | 35.4 | 16% | 33% | 22% | 17% |
| 2026-11-10 | Brayden Burries | 34.1 | 73% | 56% | 65% | 84% |
| 2026-11-10 | Klay Thompson | 35.4 | 18% | 35% | 35% | 33% |
| 2026-11-11 | Wendell Carter Jr. | 34.7 | 37% | 53% | 49% | 39% |
