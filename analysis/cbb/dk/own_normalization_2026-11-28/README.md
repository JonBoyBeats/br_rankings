# Ownership grade normalization fix (2026-11-28)

This is a grading fix only. **The HOLD stands:** no model, page or field change.

## The causes

There were two causes, one on each side of the grade.

1. **Projected side: undrafted players were never graded.**
   - `dk_eval.py` (nightly and `ownsync`) wrote an `own_eval.csv` row only for players the contest's standings listed, i.e. players somebody drafted.
   - In small contests many players we projected went undrafted. They never appeared, so our over-projections on them were never counted.
   - The affected contests' projected sums are below 800:

     | Contest | Projected sum, before | Projected sum, after |
     |---|---|---|
     | 198181552 | 543 | 800 |
     | 198188320 | 543 | 785 |
     | 198230480 | 486 | 800 |
     | 198230492 | 465 | 790 |

   - The remaining shortfall from 800 is players in `_own.json` who have no row in the night record.
2. **Actual side: the standings' Player section undercounts.**
   - The section is supposed to list one row per roster slot a player was drafted in. It sometimes lists a player drafted at two slots (G/F and UTIL) only once, at one slot's share.
   - The lineups themselves were complete in every file: 8 names per entry, plus a few empty, unfilled entries.
   - So the shortfall wasn't rounding or missing rows; it was missing roster-slot rows.
   - On the 45 standings files where every entry has a complete lineup, **140 of 2,970 player-contests were short, in 37 of the 45 contests.** Examples:
     - a player in 1.7% of a 235-entry contest's lineups was logged at 0.85%;
     - in 198188320 (8 entries), Dylan Faulkner was in 75% of lineups but logged at 37.5%.
   - After the fix, actual sums are 800 except where a drafted player isn't in our night record (e.g. Jakub Szumert, 12.5% in 198230492).

## The fix

All in `scripts/dk_eval.py`:
- **`standings_rows`:** when every entry's Lineup cell is complete (or empty), ownership is the player's lineup count divided by the number of entries. The Player section's %Drafted is now only a fallback, for mid-slate files with hidden slots.
- **`own_log_rows`** (new), used by both writers (nightly and `ownsync`): every night-record player is logged. A player the complete standings don't list gets actual 0.
- **`scripts/dk_own_backfill.py`** rebuilt `own_eval.csv`: 13,653 rows, was 6,857. All 84 logged contests were rebuilt from their standings files.
- **Tests:** `tests/dk_own_grade.py` covers the new semantics and lineup-count ownership (13 pass); `tests/dk_scorecard.py` 23 pass.
- **battle-royale-research `dk_source.py`:** its real-ownership read (for a shadow source's ownership grade) now uses the lineups too.

**Do the grades count projected-but-undrafted players as 0?** Before the fix, no: they had no rows. Now, yes. `own_grade_rows` keeps `a = 0`, and the chalk band (max(projected, actual) ≥ 15) now includes a player we projected 15%+ whom nobody drafted.

## What changed

### The scorecard ownership headline (chalk-band MAE, share off by 10+)

| | Before | After |
|---|---|---|
| LIVE, last 7 | 11.82 ± 0.88 (46%) | 12.15 ± 0.91 (47%) |
| LIVE, season | 11.59 ± 0.60 (47%) | 11.74 ± 0.61 (47%) |
| PREVIOUS (raw) | 11.25 ± 1.19 (42%) | 11.75 ± 1.27 (43%) |
| RULER | 11.93 ± 1.06 (49%) | 12.28 ± 1.11 (51%) |
| LIVE − PREV | +0.17 ± 0.22 (5) | +0.14 ± 0.21 (5) |
| LIVE − RULER | −0.35 ± 0.27 (6) | −0.37 ± 0.35 (6) |

All three levels rise by 0.2–0.5. That's the newly graded over-projections and the corrected chalk shares. **The paired comparisons barely move.**

### Earlier findings, re-run on the fixed data

Outputs are in this folder.

| Finding | Before | After | Changes? |
|---|---|---|---|
| Correction held out on raw, team + big (Friday §3 / `fr_own.py`) | +0.34 (2×SE 0.19), 13 of 16 | +0.30 (2×SE 0.20), 13 of 16 | no |
| Shipped coefficients on raw | +0.43 (0.30), 13 of 16 | +0.44 (0.29), 13 of 16 | no |
| The same, since 157026 | +0.03, 3 of 5 | +0.06, 3 of 5 | no |
| Refit coefficients, all slates (c0 / team / big) | +0.65 / −1.03 / +5.6 | −0.24 / −0.81 / +5.93 | **the intercept**: undrafted zeros pull it down; team and big hold |
| **Q term** (team + big + Q, held out) | +0.57 (0.39), 13 of 16 | **+0.58 (0.40), 13 of 16** | no: still passes; Q coefficient −22.5 |
| Q players at 10%+ | 38 player-contests, −22.7 | 46 player-contests, −23.0 | no |
| Disagreement: loved − within, actual − projection | +3.31 ± 1.32, 12 of 15 | +3.29 ± 1.31, 12 of 15 | no |
| Disagreement: faded − within | −1.44 ± 1.44, 5 of 16 | −1.69 ± 1.42, 4 of 16 | slightly stronger, still noise |
| r(d, actual − projection) | +0.126 ± 0.057, 11 of 16 | +0.128 ± 0.057, 11 of 16 | no |
| Rotation band, loved / faded | +6.05 / −4.32 | +6.05 / −4.42 | no |
| Stars, faded | +5.51 ± 2.13 | +5.51 ± 2.13 | no |
| Ranking outcomes, field − ours | +0.002 ± 0.052 | +0.002 ± 0.052 | no |
| Tiered test A, all-player chalk gain vs live | −0.22 ± 0.30 | −0.20 ± 0.29 | no (NOISE) |
| Tiered test A, concentration | −11.3 ± 4.8 (5 of 16) | −13.3 ± 4.2 (3 of 16) | no (NOISE, a bit worse) |
| Tiered test B / C, pct vs board top half | +0.11 ± 0.40 / −0.22 ± 0.20 | +0.11 ± 0.40 / −0.14 ± 0.22 | no (NOISE) |
| Concentration miss, real top 8 − our raw top 8, 200+ contests | +21.8 ± 7.1, 12 of 16 | +21.8 ± 7.1, 12 of 16 | no (large contests barely affected) |

**Bottom line:** the levels of the ownership grade rose by a few tenths, and the correction's intercept changed. **No earlier finding, tag or held proposal changes.** The Q term still passes, the disagreement results hold, and the tiered test stays NOISE.
