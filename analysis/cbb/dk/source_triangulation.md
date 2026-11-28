# Source triangulation (shadow), pre-registration, 2026-11-28

Asked for by the operator on 2026-11-28. Ours, Gajewski and RotoWire are read side by side, and each player is put in a
group by whether the sources agree on **minutes** and on **points per minute** (ppm). A combo projection uses the
sources where they agree and ours where we are thought strongest. It is a **shadow**: nothing feeds the live
projection, fill or exposures. Written and committed before the builder or any grade was run.

Per-player source numbers and the combo projection are paid-source derived and live only in the private research repo
(`data/dk/cbb/sources/triangulation_<date>_<dg>.csv`). This public repo carries only the definitions, the per-player
group and outlier labels (`analysis/cbb/dk/triangulation_labels.csv`, no numbers) and aggregates on the scorecard.

## Definitions (fixed)

- **Players:** every player on the slate who is not Out at lock and whom at least one source projects at 10+ minutes.
- **Sources:** US = our lock-time `fp_dk` and `min`; GJ = Gajewski (`FPTs`, `TTL Min`); RW = RotoWire (DK points
  computed from its category lines with our DK scoring, no double-double bonus, as `dk_source.py` does; `MIN`).
  A source "has" a player only if its file lists him. ppm = DK points / minutes.
- **In/out split (G5):** some listing source has him under 8 minutes (or 0) while another has him at 10+.
- Otherwise, over the sources at 8+ minutes (at least 2 needed, else **ungrouped**):
  - **minutes agree** when (max − min) / mean ≤ 15%;
  - **ppm agree** when (max − min) / mean ≤ 10%.
- **Groups:** G1 = minutes agree + ppm agree; G2 = minutes split + ppm agree; G3 = minutes agree + ppm split;
  G4 = both split; G5 = in/out split. Players with only US are ungrouped.
- **Outlier source** on a split dimension: the source farthest from the mean of the others (minutes or ppm).
- **COMBO projection** (the operator's rule):
  - G1: ours.
  - G2: mean of the *other* sources' minutes × our ppm.
  - G3: mean of *all* sources' minutes × our ppm.
  - G4: ours, flagged toss-up.
  - G5: ours (news decides).
  - Ungrouped: ours.

## Grading (nightly, once box scores are final)

Per group, on players graded (did-not-play = 0 minutes / 0 points):

- MAE of DK points and of minutes for US / GJ / RW / mean of the available sources / COMBO (each source graded only
  where it lists the player);
- |actual − our projection| by group, to check whether the consensus groups really miss less;
- in each split, which source was closest to actual, by which source was the outlier;
- COMBO − US (points MAE gain), per slate, with SE over slates and k of n slates ahead.

## Decision rule (process.md rule 5)

COMBO becomes a projection candidate (arm projection, PREVIOUS = `fp_dk`) only at **10+ graded source slates**, and
only if its points-MAE gain over ours clears the bar: PROVEN = gain > 2×SE and ahead on most slates; DIRECTIONAL =
ahead on clearly more slates than not (about 60–65%+) with a sensible mechanism. Before 10 slates every number is
context. Exposure ideas for G4 come later and are not part of this test.

The 15% / 10% / 8 / 10 minute thresholds are fixed here and are not tuned on results.

## Amendment 2026-11-28, before any grading (the coordinator, consistent with the operator's direction)

Committed before the builder was run or any slate graded. Still logging only.

1. **Projection recipes per group.** Minutes and ppm are graded separately (minutes MAE; ppm MAE on players with 10+
   actual minutes), then their product (points MAE), for: US, GJ, RW; MEAN of the available sources (US included);
   MEDIAN of the available sources (with 2 sources, the mean); the operator's COMBO; and BEST-BY-COMPONENT: per group,
   the source whose minutes and the source whose ppm had the lowest MAE in that group on **prior** graded slates only
   (walk-forward, never the same slate; US until a group has a prior slate), its projection = that minutes × that ppm.
   **Selection rule:** at 10 graded source slates, the live candidate per group is the recipe with the lowest
   held-out points MAE in that group (mean over slates ± SE, k of n), and it must clear rule 5 against US (as above).
2. **Noise per group:** each night logs the realised |actual − proj| / proj by group (players with proj ≥ 10), beside
   the bank's per-tier σ (`bank_noise.json`, miss / mean by salary tier), for a later per-group σ bank candidate.
3. **G5 as play probability:** for every G5 player, each source's in/out call (in = 10+ minutes, out = under 8 or 0)
   and whether he played (any actual minutes) are logged, so a P(plays) × full projection treatment can be fitted
   later.
4. **Cutoffs:** 15% / 10% stay frozen for the count. Each player's raw minutes spread and ppm spread ((max − min) / mean)
   are logged privately so other cutoffs can be checked at 10 slates without recomputing.

Per-player numbers stay in the private repo; aggregates and labels here.
