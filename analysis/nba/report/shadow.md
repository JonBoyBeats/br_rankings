# NBA shadow orders

Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two orders disagree on (80% range from resampling slates). Switch: positive = the switch beat the rule it replaced. Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start 2026-11-10; a provisional switch is dropped if it doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered.

| Comparison | Kind | Season | Forward nights | Forward |
|---|---|---|---|---|
| PM T2: ADP (2: ETR) vs the old ADP (1: ETR) | switch | +2.7 (-1.1 to +6.9), 49 pairs, LEAN + | 2 | -5.9, not enough yet (10) |
| PM T4: ADP (2: ETR) vs the old ETR rule | switch | -0.4, not enough yet (24) | 1 | +6.3, not enough yet (1) |
| PM T5: the button (ADP, then the less drafted within 2 pts) vs the old ETR (2: less drafted) | switch | +0.1 (-1.7 to +1.9), 882 pairs, no lean | 2 | -6.6 (-13.0 to +0.9), 108 pairs, no lean |
| AM T5: the less drafted within 2 pts vs the old Proj (3: ADP) | switch | +2.7 (+1.0 to +4.7), 161 pairs, RULE + | 2 | +5.0, not enough yet (30) |
| PM T5: the less drafted within 2 pts vs the old ADP | switch | -2.4 (-4.9 to -0.0), 92 pairs, LEAN - | 2 | -5.1, not enough yet (8) |
| All tiers, kept: the one-tier cap against the projection tier's order where they disagree | cap | +0.0 (-2.1 to +2.0), 75 pairs, no lean | 2 | +4.1, not enough yet (13) |
| T3-T5, in use: VALUE first against VALUE players left with the rest | check | +0.4 (-0.6 to +1.5), 424 pairs, no lean | 1 | -3.5, not enough yet (27) |
| All tiers, in use: PRICEY last against PRICEY players left with the rest | check | +2.8 (+1.6 to +4.0), 1179 pairs, RULE + | 1 | -0.4 (-0.4 to -0.4), 84 pairs, LEAN - (RULE numbers, check pending) |
| AM, in use: no push for a Questionable player against two tiers back | check | +1.8 (-2.4 to +5.6), 129 pairs, no lean | 0 | none yet |
| PM, in use: a Questionable player two tiers back against no push (by ADP in his tier) | check | -0.1 (-2.7 to +1.9), 97 pairs, no lean | 1 | -0.8, not enough yet (5) |
| AM T5, in use: the button's order against ADP straight | check | +2.4 (+0.4 to +4.4), 380 pairs, LEAN + | 1 | +10.6 (+10.6 to +10.6), 44 pairs, LEAN + |
| T4-1: PRICEY-last off in PM T4 (VALUE first kept) | candidate | +3.5, not enough yet (22) | 0 | none yet |
| T2-T4-1: T2-T4 leverage on money's definition: the less drafted first within 2 projected points (drafted% 10+ apart, both 2%+) | candidate | +0.5, not enough yet (19) | 0 | none yet |
| T5-1: AM T5: a round-6 pick whose teammate is tagged Q/D/GTD at the AM record goes ahead of his decision-pair partners | candidate | -3.3 (-4.5 to -1.8), 808 pairs, RULE - | 2 | -1.6 (-6.4 to +5.0), 131 pairs, no lean |
| Q-1: Q push by flag, chance and tier: VALUE or over 70% to play, no push; T1-T2 PRICEY or under 50%, two tiers back; else the current rule (AM no push, PM two back) | candidate | -6.7, not enough yet (24) | 0 | none yet |
| T2-1 (AM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | -1.1 (-3.6 to +1.6), 43 pairs, no lean | 2 | -0.9, not enough yet (7) |
| T2-1 (PM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | +0.3 (-2.0 to +2.9), 77 pairs, no lean | 2 | +1.4, not enough yet (7) |
| T5-2 (AM): T5 by the window's projection to the whole point, the less drafted first within the same point (VALUE first and PRICEY last kept) | candidate | -1.6 (-3.4 to +0.1), 679 pairs, LEAN - | 1 | +8.1 (+8.1 to +8.1), 52 pairs, LEAN + |
| T5-2 (PM): T5 by the window's projection to the whole point, the less drafted first within the same point (VALUE first and PRICEY last kept) | candidate | -1.0 (-2.7 to +0.9), 717 pairs, no lean | 1 | +12.3 (+12.3 to +12.3), 49 pairs, LEAN + |
