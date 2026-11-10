# NBA shadow orders

Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two orders disagree on (80% range from resampling slates). Switch: positive = the switch beat the rule it replaced. Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start 2026-11-10; a provisional switch is dropped if it doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered.

| Comparison | Kind | Season | Forward nights | Forward |
|---|---|---|---|---|
| PM T2: ADP (2: ETR) vs the old ADP (1: ETR) | switch | +5.0, not enough yet (39) | 0 | none yet |
| PM T4: ADP (2: ETR) vs the old ETR rule | switch | -0.7, not enough yet (23) | 0 | none yet |
| PM T5: the button (ADP, then the less drafted within 2 pts) vs the old ETR (2: less drafted) | switch | +0.9 (-0.6 to +2.4), 757 pairs, no lean | 0 | none yet |
| AM T5: the less drafted within 2 pts vs the old Proj (3: ADP) | switch | +2.2 (+0.2 to +4.5), 137 pairs, LEAN + | 0 | none yet |
| PM T5: the less drafted within 2 pts vs the old ADP | switch | -2.1 (-4.8 to +0.6), 84 pairs, LEAN - | 0 | none yet |
| All tiers, kept: the one-tier cap against the projection tier's order where they disagree | cap | -0.8 (-2.9 to +1.2), 62 pairs, no lean | 0 | none yet |
| T4-1: PRICEY-last off in PM T4 (VALUE first kept) | candidate | +3.5, not enough yet (22) | 0 | none yet |
| T2-T4-1: T2-T4 leverage on money's definition: the less drafted first within 2 projected points (drafted% 10+ apart, both 2%+) | candidate | +2.7, not enough yet (21) | 0 | none yet |
| T5-1: AM T5: a round-6 pick whose teammate is tagged Q/D/GTD at the AM record goes ahead of his decision-pair partners | candidate | -3.6 (-4.7 to -2.2), 677 pairs, RULE - | 0 | none yet |
| Q-1: Q push by flag, chance and tier: VALUE or over 70% to play, no push; T1-T2 PRICEY or under 50%, two tiers back; else the current rule (AM no push, PM two back) | candidate | -7.8, not enough yet (24) | 0 | none yet |
| T2-1 (AM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | -1.2, not enough yet (36) | 0 | none yet |
| T2-1 (PM): T2 by ADP to about pick 9 (the 1/2 turn), then by the window's projection from about pick 10 to the end of T2 | candidate | +0.2 (-2.4 to +3.1), 70 pairs, no lean | 0 | none yet |
