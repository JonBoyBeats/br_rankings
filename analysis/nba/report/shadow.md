# NBA shadow orders

Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two orders disagree on (80% range from resampling slates). Switch: positive = the switch beat the rule it replaced. Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start 2026-11-10; a provisional switch is dropped if it doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered.

| Comparison | Kind | Season | Forward nights | Forward |
|---|---|---|---|---|
| PM T2: ADP (2: ETR) vs the old ADP (1: ETR) | switch | +4.1, not enough yet (37) | 0 | none yet |
| PM T4: ADP (2: ETR) vs the old ETR rule | switch | -0.5, not enough yet (19) | 0 | none yet |
| PM T5: the button (ADP, then the less drafted within 2 pts) vs the old ETR (2: less drafted) | switch | +1.1 (-0.5 to +2.8), 705 pairs, no lean | 0 | none yet |
| AM T5: the less drafted within 2 pts vs the old Proj (3: ADP) | switch | +0.1 (-1.7 to +2.2), 120 pairs, no lean | 0 | none yet |
| PM T5: the less drafted within 2 pts vs the old ADP | switch | -2.9 (-5.1 to -0.8), 90 pairs, LEAN - (RULE numbers, check pending) | 0 | none yet |
| All tiers, kept: the one-tier cap against the projection tier's order where they disagree | cap | -0.7 (-2.8 to +1.3), 56 pairs, no lean | 0 | none yet |
| T4-1: PRICEY-last off in PM T4 (VALUE first kept) | candidate | +6.8, not enough yet (14) | 0 | none yet |
| T2-T4-1: T2-T4 leverage on money's definition: the less drafted first within 2 projected points (drafted% 10+ apart, both 2%+) | candidate | +1.9, not enough yet (19) | 0 | none yet |
| T5-1: AM T5: a round-6 pick whose teammate is tagged Q/D/GTD at the AM record goes ahead of his decision-pair partners | candidate | -2.9 (-4.3 to -1.5), 546 pairs, LEAN - (RULE numbers, check pending) | 0 | none yet |
| Q-1: Q push by flag, chance and tier: VALUE or over 70% to play, no push; T1-T2 PRICEY or under 50%, two tiers back; else the current rule (AM no push, PM two back) | candidate | -8.5, not enough yet (19) | 0 | none yet |
