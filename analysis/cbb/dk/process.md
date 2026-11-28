# DraftKings CBB: how a change ships (from 2026-11-25)

The rules for changing the live model, and how each change is graded. The numbers come from
`python3 scripts/dk_eval.py scorecard` (written to [scorecard.md](scorecard.md); also printed by
`dk_eval.py misses --friday`). Ideas wait in [ideas.md](ideas.md).

## The arms

| Arm | Headline (scorecard) | Version tag (arm_versions.json) | PREVIOUS logged as |
|---|---|---|---|
| minutes | ROTATION band (ours 10-25) minutes MAE | projection | `min_old` |
| per-minute | STARS band (ours 25+) points MAE | projection | `old_fp` |
| ownership | chalk band MAE and share off by 10+ | ownership | `own_raw` |
| field model | sim minus real cash line and top-10% line, 100+ contests | field | not logged yet |
| qualifier field (from 2026-11-28) | entered minus `fill_prev` on qualifier contests (QUAL_CHALK 0.35 vs 0.8) | field | `fill_prev` (its qualifier picks made under the 0.8 field) |
| pool | kept minus whole bank, mean real finish percentile | cut | not logged yet |
| bank (from 2026-11-28) | live bank minus the night's Draw-the-9 replay at lock, mean real finish percentile | cut (bank draw) | `bank_prev/` (dk_eval.py bankprev) |
| fill | entered minus random fills, dollars and percentile; entered minus `fill_prev` per contest type (from 2026-11-28) | fill | `fill_prev` (Save build, from 2026-11-28) |
| late swap | removed from the scorecard 2026-11-28 (the operator doesn't use late swap) | late_swap | — |
| over-trust gauge (from 2026-11-28) | our entries' real minus projected points against the field's, per night and rolling (context, not an arm) | — | — |
| results | net dollars and return on fees | none | read over 20+ nights only |

Every night record (`analysis/cbb/dk/<date>_<draft group>.csv`) carries `ver_<arm>`, each arm's version that night
(`scripts/dk_arms.py`), and the frozen ruler's columns.

## The ruler

`ruler-2026-11-23` is the 2026-11-23 lock's projection and field. It lives in battle-royale-research at
`scripts/cbb_ruler.py`. It is computed every night beside the live model and logged as `ruler_min`, `ruler_fp`,
`ruler_fp_gate` and `own_ruler`. It never changes. Every version is measured against it on the same nights. A new
ruler would be a new file with a new id, and the old one would keep running.

## The rules

1. **Ideas queue.** Every proposed change goes into [ideas.md](ideas.md) first. Each entry needs:
   - the arm;
   - the hypothesis;
   - the test plan: what is measured, held out by slate, on which slates;
   - the pass bar (rule 5);
   - the PREVIOUS column it will log (rule 3).
2. **Friday batch.** Changes ship together at the Friday review. Bug fixes are the exception: they ship any day, with
   a `versions.csv` row that says it is a bug fix.
3. **Same-night pairs.** A change ships only with the arm's previous version logged beside it in the night record,
   on the same nights. `min_old`, `old_fp` and `own_raw` are the pattern. The previous version keeps being logged
   for at least 7 graded slates. The scorecard's pair check must read "PREVIOUS logged on k of k slates" for the
   change's first 7 slates. A MISSING slate means that slate can't be paired. An arm with no PREVIOUS column
   (field, pool, fill and late swap, today) needs one built before its next change.
4. **One change per arm per week, then settle.** After a change, the arm is *settling* until 7 graded slates have
   run under it. The scorecard shows "settling k of 7". No further change to that arm until it reads "settled".
   Bug fixes are the exception.
5. **The pass bar, held out by slate.** A change passes only if, held out by slate:
   - its arm's headline is better on most slates;
   - the mean per-slate gain is more than 2 × its SE;
   - no other arm is worse beyond noise, meaning every other arm's paired difference is within 2 × SE.

   The paired difference is LIVE − PREVIOUS on the same slates and rows. Projection changes also keep the
   band rule in `scripts/dk_proj_grade.py`. Results (dollars, return) are never a pass bar: read them over 20+
   nights only.

   **The tiered bar (added 2026-11-28, approved by the operator, beside rule 5).** Every finding is tagged with one
   of three tiers:
   - **PROVEN**: today's bar. Held out by slate, ahead on most slates, gain > 2 × SE. It ships.
   - **DIRECTIONAL**: all of these hold:
     - it points the right way on clearly more slates than not (about 60–65%+);
     - it has a sensible mechanism;
     - it is small and cheap to undo;
     - no other arm's headline is worse beyond noise.

     It ships as **PROVISIONAL**, with its PREVIOUS logged nightly (rule 3). It gets an automatic review at a stated
     slate count: by default 7 for the projection and ownership arms, and 10 for bank and fill. It is kept if it
     holds and reverted if it flips.
   - **NOISE**: the sign flips, or there is no mechanism. It goes to the watch list.

   *Principle:* stack small, directionally accurate edges rather than waiting for one silver bullet.

   From now on, every Friday-review finding carries a PROVEN / DIRECTIONAL / NOISE tag. Approval of this bar does
   not lift the operator's hold (2026-11-28): shipping still waits for the operator's go.
6. **Bookkeeping.** Each live change needs two entries:
   - a `versions.csv` row, written with `csv.writer(lineterminator="\r\n")`, with the slate date it takes effect;
   - a new version in `arm_versions.json` with that date (plus `first_slate` if it lands between a day's slates),
     listing its `versions.csv` rows.

   `tests/dk_scorecard.py` checks that every listed row exists.

## Standing re-runs

**The green-core shadow logs every main night** (added 2026-11-28, the operator; logging only).
- **What runs:** `scripts/dk_core_shadow.py`, in `dk_eval.py nightly`.
- **What it logs:** for every main contest of a saved build, the top-5-cores and top-5 green-core picks beside the page's pick and the real entries, graded on the standings.
- **Where:** analysis/cbb/dk/core_shadow.csv, read by the scorecard's "Green-core shadow (mains)".
- **The decision:** PROVEN needs dollars and finish pct ahead of the page's pick on 7 of 10 counted main slates. The 7 cc44bc8 nights are pre-registration and don't count.
- **A main night with no saved build can't be graded.** The scorecard names it.

**The projection pair backtest re-runs every 10 graded slates** (added 2026-11-28).
- **What runs:** `analysis/cbb/dk/projection_pair_backtest_2026-11-28/ppb.py`, `MIN_GP=5` and `MIN_GP=7` of it, and `ppb_trend.py`. Run them from that folder, with battle-royale-research beside br_rankings.
- **What it covers:** the minutes switch, the per-minute level and the pair, replayed on every graded slate.
- **When it's due:** the scorecard prints "next re-run due at N graded slates" from [pair_backtest_runs.json](pair_backtest_runs.json).
- **After a run:** append the run there and add the results to the write-up.
- **No CI job runs it;** it is run by hand when due.

**External projection sources in shadow** (added 2026-11-28).
- **Where they come from:** battle-royale-research `scripts/dk_source.py` grades each banked source (first: Gajewski) against ours and the ruler, and publishes aggregates to the mirror. The scorecard shows them as "External projection sources (shadow)".
- **The source files stay private:** they are paid content, so no per-player source value is written in this public repo.
- **The sources so far:** Gajewski, one file per slate, and RotoWire, a whole-day file that covers only some players. Only players a source covers are graded, with its coverage shown beside the grade.
- **The blend test** is due at 10 graded slates per source. The scorecard prints "due at 10 graded slates (now N)". It compares, held out by slate, for projection and ownership by salary tier, on covered players:
  - ours;
  - Gajewski;
  - RotoWire;
  - blends of ours and the sources, with held-out weights;
  - a hybrid for each source: its minutes × our points per minute (RotoWire minutes × ours included);
  - a minutes-only blend, with a held-out weight.
- **The shadow grades also log:**
  - minutes disagreements of 6+ minutes (who was closer on actual minutes, by the $7k tier);
  - points-per-minute MAE and bias for ours and the source, by tier, on players with 10+ actual minutes.
- **Nothing feeds the live model** until the operator approves.

## Reading the scorecard

The scorecard has:
- one block per arm, with the version live today, its last-changed date and its settling status;
- for the last 7 graded slates and for the season, the columns LIVE, PREVIOUS and RULER, each a mean over slates ± SE
  (slates).

PREVIOUS and RULER are levels on the slates that logged them. The comparison to read is LIVE − X, which is paired per
slate on the rows both logged.

Columns that weren't logged are n/a. They are never filled in, with one marked exception: the ruler on 2026-11-23 and
2026-11-24 (157021, 157024, 157026). On those slates the live model was the lock's, so the ruler is the live projection
and the raw field ownership. Slates before 2026-11-23 have no ruler, because the lock model's inputs for them were
never stored. The ruler is logged from 2026-11-25 on.
