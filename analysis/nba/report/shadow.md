# NBA shadow orders

Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two orders disagree on (80% range from resampling slates). Switch: positive = the switch beat the rule it replaced. Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start 2026-11-10; a provisional switch is dropped if it doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered.

| Comparison | Kind | Season | Forward nights | Forward |
|---|---|---|---|---|
| PM T2: ADP (2: ETR) vs the old ADP (1: ETR) | switch | +4.1, not enough yet (37) | 0 | none yet |
| PM T4: ADP (2: ETR) vs the old ETR rule | switch | -0.5, not enough yet (19) | 0 | none yet |
| PM T5: ADP vs the old ETR (2: less drafted), the paused ownership tiebreak | switch | +1.2 (-0.4 to +2.8), 770 pairs, LEAN + | 0 | none yet |
| PM T4 candidate: PRICEY-last off (VALUE first kept) | candidate | +6.8, not enough yet (14) | 0 | none yet |
| AM T4 candidate: the leverage tiebreak | candidate | +0.4 (-1.6 to +2.9), 73 pairs, no lean | 0 | none yet |
| AM T5 candidate: the button's order, VALUE first, then the less drafted within 2 projected points | candidate | -0.9 (-3.1 to +1.3), 372 pairs, no lean | 0 | none yet |
| PM T5 candidate: ADP, VALUE first, then the less drafted within 2 projected points | candidate | -0.6 (-2.3 to +1.0), 466 pairs, no lean | 0 | none yet |
| AM T2-T4 candidate: the less drafted within 2 projected points | candidate | -2.6, not enough yet (13) | 0 | none yet |
| PM T2-T4 candidate: the less drafted within 2 projected points | candidate | +11.1, not enough yet (5) | 0 | none yet |
| All tiers, kept: the one-tier cap against the projection tier's order where they disagree | cap | +0.2 (-2.2 to +2.5), 52 pairs, no lean | 0 | none yet |
