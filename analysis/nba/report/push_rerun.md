# Pairs as a tally, with pushes (2026-11-17)

From 2026-11-17 every pair grade is a tally: a pair is won or lost when its two players finish 3+ points apart, a push
under 3; a night goes to the side with more wins, and the night-resamples run on wins minus losses. Points per pair stay
as the backup. Code: `nba_tier_season_tests.summarize` (season tests, the Friday report, the Q rules test) and
`nba_report_sections.moves` (your moves by tier). Rerun on 26 nights (2026-10-21 to 2026-11-16).

Read: which side is ahead in the night-resamples; 90%+ is clear, 80-90% watching, under 80% no signal (the Friday
report's bars).

## Season tier tests

| Test | Before (points) | After (tally, 3-pt pushes) | Holds? |
|---|---|---|---|
| T1 morning: ours vs ADP | ours 67% | ours 67% (12-9) | holds: no signal |
| T2 morning: ours vs ADP | ADP 92% (clear) | ADP 81% (110-133, 38 pushes) | weakens to watching |
| T2 morning elite break vs ADP | ADP 86% (watching) | ADP 71% | weakens to no signal |
| T3 morning: shared sort vs ADP | sort 68% | sort 67% | holds: no signal |
| T4 morning: shared sort vs ADP | ADP 62% | ADP 68% | holds: no signal |
| T4 VALUE vs T3 PRICEY, morning | T3 PRICEY 88% | T3 PRICEY 88% (41-58) | holds: watching (the rule in force) |
| T5 top 3 vs T4 PRICEY, morning | T4 PRICEY 100% | T4 PRICEY 100% (5-19) | holds: clear |
| T1 afternoon: ETR vs ADP | ETR 91% | ETR 91% (12-6) | holds: clear (the rule in force) |
| T2 afternoon: ETR vs ADP | ADP 72% | even, 52% / 46% (107-105) | holds: no signal |
| T2 afternoon elite break vs ADP | break 84% | break 86% (27-20) | holds: watching (the rule in force) |
| T3 afternoon: shared sort vs ADP | sort 86% | sort 88% (96-65) | holds: watching (the rule in force) |
| T4 afternoon: shared sort vs ADP | sort 90% (clear) | sort 87% (78-58) | weakens to watching |
| T4 VALUE vs T3 PRICEY, afternoon | T3 PRICEY 74% | T3 PRICEY 69% | holds: no signal |
| T5 top 3 vs T4 PRICEY, afternoon | T5 top 3 77% | T5 top 3 64% | holds: no signal |

## Your moves against the button, by tier

| Tier, window | Before (points a move; ahead) | After (won-lost-pushes; ahead) | Verdict before -> after |
|---|---|---|---|
| T1 morning | -4.2; 10% | 11-11-1; 45% | press the button -> too early |
| T1 both windows | -7.1; 1% | 12-16-1; 14% | press the button -> press the button |
| T2 morning | +2.5; 90% | 61-40-18; 94% | keep -> keep |
| T2 afternoon | +3.1; 92% | 50-33-16; 93% | keep -> keep |
| T3 morning | -6.1; 2% | 9-21-9; 6% | press the button -> press the button |
| T3 afternoon | -3.9; 5% | 20-29-8; 10% | press the button -> press the button |
| T4 morning | +1.0; 68% | 11-11-5; 42% | too early -> too early |
| T4 afternoon | -0.6; 38% | 18-17-6; 49% | too early -> too early |
| T5 morning | +1.6; 72% | 31-36-20; 34% | too early -> too early |
| T5 afternoon | +1.9; 86% | 53-42-25; 79% | keep -> too early |

T5's order line is retired from the grading (2026-11-17): T5 is graded on drafted picks and swaps, not order.
