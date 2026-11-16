# DraftKings CBB: parked ideas for the 30-slate review

**Revised freeze (the owner's call, 2026-11-16):** week 1 (through 2026-11-23) is open for tweaks to anything.
After that, freeze only what's graded: the sim model, the quadrant recipe and lines, the five shadow rule sets,
and the portfolio pick. Layout, buttons, the bank/cut/review/export workflow, speed and bug fixes stay open any
time. The 30-slate count starts at the freeze; slates before it are logged as warm-up, tagged with the version
they ran on (`phase`, `version` in eval.csv and tiles_eval.csv). Anything new for a frozen part goes here, dated,
with why it came up, and is decided at the review, not before.

The review starts from the monthly readout (`python3 scripts/dk_eval.py weights`, then `readout`): rule sets and
the owner's entries against the field's top-10% rate (the 30-slate decision), the random-set percentiles, the
quadrants on their three targets, the Quality weights (fitted against equal on held-out slates), the projection
gate, the sim's calibration and correlation checks.

## Parked

| Date | Idea | Why it came up |
|---|---|---|
| 2026-11-16 | Give an Out player's minutes to his teammates (by position and role) | The biggest gap in the projection: Booker out didn't raise any UCLA teammate. Test on 2025-26 games where a starter sat. |
| 2026-11-16 | A hedge for Questionable players (lower projection or exposure) | Owner: wait until there's a record of how often Q-tagged players sit. |
| 2026-11-16 | EvanMiya rank 8+ (and rank against minutes) as a fifth fragility fact | Two Underdog nights: ranks 8+ missed by more in both minute bands. Test at ~2,000 graded DK player-games. |
| 2026-11-16 | Fit the field model (`FIELD_W`, `FIELD_NOISE` in battle-royale-research `scripts/dk_cbb_field.py`) to real ownership | Projected ownership is a guess until standings come in; the readout's ownership-by-band shows how far off. |
| 2026-11-16 | Recheck Sim & pick's candidate settings (`CAND_UNIQUE` 2, `CAND_RAND` 20%) | Chosen on one slate (filled 20 of 20 where the old pool filled 16). |
| 2026-11-16 | Teammate / opponent correlation in the sim | The sim draws players independently (2025-26: correlation about 0). Add it only if the readout's correlation, game-total and #1-bust checks show it. |
| 2026-11-16 | Quadrant thresholds (50, borderline 10) and the quadrant buttons' shares (75 / 50 / 25 / 25%) | Judgment calls; the quadrant grading on three targets tests them. |
| 2026-11-16 | Same-coach list for the blowout fallback (`cbb/inputs/coaches.csv`) | ESPN's API names no coach; an input, so it can be filled any time without a code change. |
| 2026-11-16 | Suggest news sources automatically for teams new to a slate | Done by hand now (`cbb_news.py suggest`), a handful of calls a team. |
| 2026-11-16 | DraftKings triple-double bonus: do the double-double and triple-double bonuses stack? | Unconfirmed; 7 triple-doubles in 37,405 college player-games, so it barely matters. |
