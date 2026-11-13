# NBA shadow orders

Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two orders disagree on (80% range from resampling slates). Switch: positive = the switch beat the rule it replaced. Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start 2026-11-10; a provisional switch is dropped if it doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered.

| Comparison | Kind | Season | Forward nights | Forward |
|---|---|---|---|---|
| PM T2: ADP (2: ETR) vs the old ADP (1: ETR) | switch | +2.3 (-1.5 to +6.3), 50 pairs, no lean | 3 | -6.9, not enough yet (11) |
| PM T4: ADP (2: ETR) vs the old ETR rule | switch | -1.7, not enough yet (25) | 2 | -13.4, not enough yet (2) |
| PM T5: the button (ADP, then the less drafted within 2 pts) vs the old ETR (2: less drafted) | switch | +0.3 (-1.6 to +2.0), 890 pairs, no lean | 3 | -5.6 (-11.3 to +0.8), 125 pairs, no lean |
| AM T5: the less drafted within 2 pts vs the old Proj (3: ADP) | switch | +2.6 (+0.8 to +4.7), 168 pairs, RULE + | 3 | +5.5, not enough yet (37) |
| PM T5: the less drafted within 2 pts vs the old ADP | switch | -2.4 (-4.7 to -0.1), 96 pairs, LEAN - | 3 | -3.4, not enough yet (13) |
| All tiers, kept: the one-tier cap against the projection tier's order where they disagree | cap | -0.2 (-2.2 to +1.7), 78 pairs, no lean | 3 | +2.1, not enough yet (16) |
| T3-T5, in use: VALUE first against VALUE players left with the rest | check | +0.5 (-0.6 to +1.6), 427 pairs, no lean | 2 | -3.1, not enough yet (28) |
| All tiers, in use: PRICEY last against PRICEY players left with the rest | check | +2.7 (+1.6 to +3.9), 1254 pairs, RULE + | 2 | +0.6 (-0.4 to +1.7), 162 pairs, no lean |
| AM, in use: no push for a Questionable player against two tiers back | check | +0.8 (-3.1 to +4.7), 143 pairs, no lean | 1 | -9.0, not enough yet (14) |
| PM, in use: a Questionable player two tiers back against no push (by ADP in his tier) | check | -0.0 (-2.6 to +2.0), 99 pairs, no lean | 2 | +0.4, not enough yet (7) |
| AM T5, in use: the button's order against ADP straight | check | +2.3 (+0.4 to +4.4), 388 pairs, LEAN + | 2 | +9.9 (+6.8 to +10.6), 52 pairs, LEAN + |
| T4-1: PRICEY-last off in PM T4 (VALUE first kept) | candidate | +3.5, not enough yet (22) | 0 | none yet |
| T2-T4-1: T2-T4 leverage on money's definition: the less drafted first within 2 projected points (drafted% 10+ apart, both 2%+) | candidate | +0.7, not enough yet (18) | 0 | none yet |
| T5-1: AM T5: a round-6 pick whose teammate is tagged Q/D/GTD at the AM record goes ahead of his decision-pair partners | candidate | -3.2 (-4.4 to -1.8), 826 pairs, RULE - | 3 | -1.7 (-5.8 to +3.9), 153 pairs, no lean |
| T2-1 (AM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | -1.0 (-3.4 to +1.6), 44 pairs, no lean | 3 | -0.2, not enough yet (8) |
| T2-1 (PM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | +0.6 (-1.6 to +3.1), 79 pairs, no lean | 3 | +4.0, not enough yet (9) |
| T5-2 (AM): T5 by the window's projection to the whole point, the less drafted first within the same point (VALUE first and PRICEY last kept) | candidate | -1.6 (-3.3 to +0.2), 696 pairs, LEAN - | 2 | +5.2 (-5.9 to +8.1), 67 pairs, no lean |
| T5-2 (PM): T5 by the window's projection to the whole point, the less drafted first within the same point (VALUE first and PRICEY last kept) | candidate | -1.0 (-2.7 to +1.0), 723 pairs, no lean | 2 | +11.4 (+3.6 to +12.3), 55 pairs, LEAN + |
| Q-2: AM: a Questionable player in T1-T3 at the morning record drops to T4 (first in T4 by the button's order); in T4-T5 he keeps his tier; no chance-to-play split | candidate | -2.4 (-6.6 to +2.2), 89 pairs, no lean | 1 | +7.5, not enough yet (12) |
