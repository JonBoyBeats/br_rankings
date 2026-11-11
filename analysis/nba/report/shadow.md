# NBA shadow orders

Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two orders disagree on (80% range from resampling slates). Switch: positive = the switch beat the rule it replaced. Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start 2026-11-10; a provisional switch is dropped if it doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered.

| Comparison | Kind | Season | Forward nights | Forward |
|---|---|---|---|---|
| PM T2: ADP (2: ETR) vs the old ADP (1: ETR) | switch | +4.1 (+0.1 to +8.1), 43 pairs, LEAN + | 1 | -3.9, not enough yet (4) |
| PM T4: ADP (2: ETR) vs the old ETR rule | switch | -0.4, not enough yet (24) | 1 | +6.3, not enough yet (1) |
| PM T5: the button (ADP, then the less drafted within 2 pts) vs the old ETR (2: less drafted) | switch | +0.9 (-0.4 to +2.4), 843 pairs, LEAN + | 1 | +0.9 (+0.9 to +0.9), 50 pairs, LEAN + |
| AM T5: the less drafted within 2 pts vs the old Proj (3: ADP) | switch | +2.6 (+0.7 to +4.7), 151 pairs, LEAN + (RULE numbers, check failed) | 1 | +6.2, not enough yet (14) |
| PM T5: the less drafted within 2 pts vs the old ADP | switch | -2.4 (-4.9 to +0.1), 88 pairs, LEAN - | 1 | -7.9, not enough yet (4) |
| All tiers, kept: the one-tier cap against the projection tier's order where they disagree | cap | +0.1 (-2.0 to +2.3), 70 pairs, no lean | 1 | +7.8, not enough yet (8) |
| T4-1: PRICEY-last off in PM T4 (VALUE first kept) | candidate | +3.5, not enough yet (22) | 0 | none yet |
| T2-T4-1: T2-T4 leverage on money's definition: the less drafted first within 2 projected points (drafted% 10+ apart, both 2%+) | candidate | +2.2, not enough yet (19) | 0 | none yet |
| T5-1: AM T5: a round-6 pick whose teammate is tagged Q/D/GTD at the AM record goes ahead of his decision-pair partners | candidate | -2.9 (-4.2 to -1.3), 732 pairs, RULE - | 1 | +5.0 (+5.0 to +5.0), 55 pairs, LEAN + |
| Q-1: Q push by flag, chance and tier: VALUE or over 70% to play, no push; T1-T2 PRICEY or under 50%, two tiers back; else the current rule (AM no push, PM two back) | candidate | -7.8, not enough yet (24) | 0 | none yet |
| T2-1 (AM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | -2.1 (-4.3 to +0.4), 41 pairs, LEAN - | 1 | -8.5, not enough yet (5) |
| T2-1 (PM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | +0.4 (-1.9 to +3.1), 74 pairs, no lean | 1 | +4.5, not enough yet (4) |
| T5-2 (AM): T5 by the window's projection to the whole point, the less drafted first within the same point (VALUE first and PRICEY last kept) | candidate | -2.4 (-4.0 to -0.9), 624 pairs, RULE - | 0 | none yet |
| T5-2 (PM): T5 by the window's projection to the whole point, the less drafted first within the same point (VALUE first and PRICEY last kept) | candidate | -2.0 (-3.5 to -0.6), 668 pairs, LEAN - (RULE numbers, check failed) | 0 | none yet |
