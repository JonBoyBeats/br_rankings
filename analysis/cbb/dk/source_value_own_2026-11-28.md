# Do source value scores predict ownership? (2026-11-28)

Analysis only. Separate from the batch build; nothing the page, the projection, the ownership model or the field
reads. Per-player source values (Gajewski, RotoWire: paid content) stay in the private battle-royale-research repo;
this file and the scorecard carry aggregates only.

**Hypothesis.** The field reads public projections. Players the sources rate as strong value get owned more than our
ownership model expects. If so, source value is the missing input behind S3's concentration miss (the field's top 8
+21.8 over ours, "needs inputs we don't log") and the field diagnostic's finding (92800a0) that the real field piles
onto players we under-project.

## Pre-registration (committed before anything was run)

### Data

- Every contest with real ownership in br_rankings `own_eval.csv` (the fixed grade, 683c36d: every projected player
  graded, undrafted = 0, ownership from lineup counts), on a slate that has at least one source file mapped in
  battle-royale-research `data/dk/cbb/sources/<source>_table.csv`. Any contest type.
- A **source night** = one DraftKings slate (draft group) with both. Players: those in the slate's source table with
  `in_lock` = 1 and not Out at lock; a source's 0-minute row is a projected out and gives that source a value of 0.
- Contest types from `scripts/dk_contest_type.py` (for the by-type view only).

### Features (per slate, per player, at lock)

- `src_val_<s>` = source s projected DK points / (salary / 1000), for s in {gajewski, rotowire} where available.
- `src_val_max`, `src_val_mean` = max and mean of `src_val_<s>` over the sources available for that player.
- `our_val` = our lock-time `fp_dk` / (salary / 1000), 0 if Out.
- **`src_edge` = `src_val_mean` − `our_val`** (the primary feature: how much more the sources like him than we do).
- Published value / rank columns: Gajewski's `Value` column equals FPTs / salary × 10,000 on the first file
  (checked before this registration: all 155 rows with points, max difference 0.016), so it is a rescale of
  `src_val_gajewski` and adds nothing; RotoWire publishes none. Recorded, not tested separately. If a later file
  carries a genuinely different value or rank column, it is added as a secondary feature by a dated amendment
  before it is graded.

### Test 1, descriptive (context, not tagged)

Our ownership error e = real − our projected ownership (the live `own_proj`, the number the page shows; the raw
`own_raw` reported beside it), per player-contest, entries-weighted within a slate. Bin players by **within-slate
quintile of `src_edge`** (Q1 = sources like him least relative to us, Q5 = most). Report the mean e per bin with SE
over source nights, and the Q5 − Q1 difference ± SE, k of n nights positive. All contest types together, then by
contest type where a type has 3+ source nights. The hypothesis predicts e rising from Q1 to Q5 and Q5 − Q1 > 0.

### Test 2, model (tagged under process.md rule 5)

S3's grading exactly as `dk_chalk_miss.run(..., "B")` and the Friday review's `fr_own.py`: fitted on raw ownership
(`own_raw`), applied to players we projected 10%+ raw, scored on the held-out slate's chalk band (max(projected,
real) ≥ 15) by chalk MAE and the share off by 10+; leave one source night out.

- **PREVIOUS** = the ownership correction as live on origin when the run happens: team + big (`chalk_team`, `big`),
  plus `q` if the batch build ships the Q term (recorded per run). Refit leave-one-slate-out **on the same source
  nights**, so both arms see the same data.
- **Candidate** = PREVIOUS's terms + `src_edge` (one extra term), same fit.
- **Gain** per held-out night = PREVIOUS chalk MAE − candidate chalk MAE. Rule 5 on the gain: PROVEN = mean gain
  > 2 × SE over nights, better on most nights, and off-10+ not worse beyond noise; DIRECTIONAL = better on 60–65%+ of
  nights with the off-10+ share not worse; otherwise NOISE.
- Secondary, context only (not tagged): the same with `src_val_max` in place of `src_edge`; and the concentration
  miss (the field's top-8 real sum minus the top-8 sum of each arm's prediction), per night.

### Nights and the re-run

- Fewer than 5 source nights: CONTEXT only, no tag; the count needed is stated.
- **First read at 5 source nights, decision at 10**, both computed automatically by the nightly run
  (battle-royale-research `scripts/dk_source.py`, aggregates into `source_grades.json` / the mirror's
  `dk_cbb_source_grades.json`) and shown in the scorecard's external-sources section with the running count. The
  rule-5 tag above is the decision at 10; the 5-night read is reported with the same numbers, labelled a first read.
- Nothing ships from this study without a separate proposal and the operator's approval.

## Amendment 2026-11-28, before any grading (0 source nights so far)

Operator addition, analysis only. It's committed before any night has been graded: the run so far found 0 source
nights (28b4485). Per-player values stay in battle-royale-research; br_rankings carries aggregates only.

**Per-source comparison: which source's implied value tracks real ownership best?**
- Sources, each taken separately: US (our lock-time `fp_dk`), GJ (Gajewski), RW (RotoWire). Value = projected DK
  points / (salary / 1000), on the players that source covers. A source's explicit 0 counts as 0; a player it doesn't
  list is missing, not zero.
- Per source night and per contest (real ownership from `own_eval.csv`): the Spearman correlation with real
  ownership of three measures:
  - (a) the value;
  - (b) the projection;
  - (c) the value WITHIN salary tier. This is the real test, since ownership is mostly price-driven. Tiers are
    dk_eval.BANDS ($6k+, $4–6k, under $4k). The Spearman is computed inside each tier and averaged, weighted by the
    tier's player count.
- **Fairness:** each source is compared with US on the players both cover, so coverage doesn't decide the winner.
  The common-player n is reported.
- **Summary:** contest Spearmans are averaged within a night, then mean ± SE over nights, all contest types together
  and per type where a type has 3+ nights. For each measure, "leads" counts the nights where a source beats US on
  their common players (k of n); GJ vs RW is likewise compared on their common players.
- **Model variants:** held out exactly as Test 2 (S3 grading, leave one source night out, fit on raw). The live
  correction plus one extra term per source (`val_us`, `val_gj`, `val_rw`), against the live correction plus the
  mean source value (`src_val_mean`). Each variant is fit on the rows where its term exists. The gain is per night
  against PREVIOUS (the live correction alone) on the same rows. These are context until the decision count: the
  rule-5 tag is given to Test 2's `src_edge` only, as registered. A per-source variant can become a proposal only
  through a separate pre-registration.
- **Context, triangulation groups:** the ownership miss (real − our live projection, weighted by entries) by
  triangulation group G1–G5 (and ungrouped), mean ± SE over nights. Labels are read from br_rankings
  `analysis/cbb/dk/triangulation_labels.csv` or BRR `data/dk/cbb/sources/triangulation_*.csv` if present;
  otherwise the run logs "pending labels".
- **Nights rule:** unchanged. A night needs a source file and real ownership. The first read comes at 5 source
  nights, the decision at 10. The nightly run computes it into `source_grades.json` → `value_own`; the scorecard's
  value_own lines show it.

## Results (run 2026-11-28, after the pre-registration ed9377e)

**No source night exists yet, so neither test can run: 0 nights, CONTEXT, no numbers.**

- The banked source files cover one day, 2026-11-27: Gajewski for the main slate (157547), RotoWire for the early
  (157545) and main slates.
- Neither slate has real ownership in `own_eval.csv`. The main slate's standings (contests 198269753, 198278517)
  aren't uploaded, and the early slate had no contest entered.
- The run (battle-royale-research `scripts/dk_source.py`, `value_own`) reads `source_nights: 0`,
  `status: context`, "no slate has both a source file and graded real ownership yet".
- PREVIOUS's terms read from the live `OWN_FIX`: chalk_team + big. No Q term on origin at run time.

**Nights needed:**
- 11-27 main becomes night 1 once its standings are uploaded.
- Test 2 needs 3 nights to fit leave-one-out.
- The first read comes at 5 source nights, and the rule-5 decision at 10. Each night needs a source file banked
  before lock and the night's standings.

**Automatic re-run:**
- `dk_source.py` now computes Test 1 and Test 2 on every nightly run, in the existing workflow step
  (`--br br_rankings --mirror mirror`).
- It writes aggregates only to `source_grades.json` / the mirror's `dk_cbb_source_grades.json` under `value_own`:
  counts, per-quintile means, gains ± SE, the tag at 10.
- The scorecard's external-sources section reads them: "Source value vs ownership (pre-registered; source nights
  with real ownership: N …)".
- Tests: battle-royale-research `tests/dk_source_value_own.py` (8 pass, on a made-up tree where real = raw + edge)
  and br_rankings `tests/dk_scorecard.py` (27 pass).
