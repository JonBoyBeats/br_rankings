# Q-1: the Questionable push, split by flag, chance to play and tier

Written by scripts/nba_q_split.py, as pre-registered in hypotheses.json (Q-1, 2026-11-09). Points per pair on decision pairs where the push orders a cell's Questionable players differently from no push; positive: the push was right. AM: the primary sample (Lock AM on our Proj); PM: every 6-drafter slate. Players: distinct Questionable players in the cell. 72 cells: about 40% of the cells with enough pairs would lean by chance alone.

## AM

| Flag | Chance to play | Tier | Players | Back one vs no push | Back two vs no push |
|---|---|---|---|---|---|
| VALUE | under 50% | T3-T5 | 3 | -5.4, not enough yet (16) | -5.4, not enough yet (16) |
| VALUE | 50-70% | T3-T5 | 4 | -0.8, not enough yet (21) | +2.8 (-4.5 to +7.7), 41 pairs, no lean |
| unflagged | under 50% | T1-T2 | 1 | -7.1, not enough yet (3) | -7.1, not enough yet (3) |
| unflagged | under 50% | T3-T5 | 0 | - | - |
| unflagged | 50-70% | T1-T2 | 3 | +3.2, not enough yet (9) | +0.3, not enough yet (14) |
| unflagged | 50-70% | T3-T5 | 0 | - | - |

By one dimension at a time (AM):

| Split | Group | Players | Back one vs no push | Back two vs no push |
|---|---|---|---|---|
| flag | VALUE | 7 | -2.8, not enough yet (37) | +0.5 (-4.6 to +4.6), 57 pairs, no lean |
| flag | unflagged | 4 | +0.6, not enough yet (12) | -1.0, not enough yet (17) |
| chance | under 50% | 4 | -5.7, not enough yet (19) | -5.7, not enough yet (19) |
| chance | 50-70% | 6 | +0.4, not enough yet (30) | +2.2 (-2.9 to +6.1), 55 pairs, no lean |
| tier | T1-T2 | 4 | +0.6, not enough yet (12) | -1.0, not enough yet (17) |
| tier | T3-T5 | 7 | -2.8, not enough yet (37) | +0.5 (-4.6 to +4.6), 57 pairs, no lean |

## PM

| Flag | Chance to play | Tier | Players | Back one vs no push | Back two vs no push |
|---|---|---|---|---|---|
| VALUE | under 50% | T3-T5 | 1 | -10.4, not enough yet (5) | -10.4, not enough yet (5) |
| VALUE | 50-70% | T3-T5 | 3 | +5.4, not enough yet (15) | +5.1, not enough yet (23) |
| VALUE | over 70% | T3-T5 | 1 | - | +12.8, not enough yet (8) |
| unflagged | under 50% | T1-T2 | 1 | -7.7, not enough yet (1) | -7.7, not enough yet (1) |
| unflagged | under 50% | T3-T5 | 3 | +1.6, not enough yet (14) | +1.5, not enough yet (15) |
| unflagged | 50-70% | T1-T2 | 2 | -7.6, not enough yet (13) | -6.2, not enough yet (17) |
| unflagged | 50-70% | T3-T5 | 1 | +6.6, not enough yet (1) | +6.6, not enough yet (1) |

By one dimension at a time (PM):

| Split | Group | Players | Back one vs no push | Back two vs no push |
|---|---|---|---|---|
| flag | VALUE | 5 | +1.4, not enough yet (20) | +4.7, not enough yet (36) |
| flag | unflagged | 7 | -2.7, not enough yet (29) | -2.5, not enough yet (34) |
| chance | under 50% | 5 | -1.0, not enough yet (19) | -0.9, not enough yet (20) |
| chance | 50-70% | 5 | -0.4, not enough yet (29) | +0.5 (-1.6 to +3.3), 41 pairs, no lean |
| chance | over 70% | 1 | - | +12.8, not enough yet (8) |
| tier | T1-T2 | 3 | -7.6, not enough yet (14) | -6.3, not enough yet (18) |
| tier | T3-T5 | 9 | +2.3, not enough yet (34) | +4.3 (+2.5 to +5.8), 51 pairs, LEAN + |

0 cells show a lean or rule.

**Q-1 against the button, in sample** (both windows, 6-drafter, Questionable players included): -8.5, not enough yet (19). Forward nights from 2026-11-10 decide it.
