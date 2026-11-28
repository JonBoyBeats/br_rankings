# Field model rebuild, step 2: the pre-registered test (2026-11-28)

The test registered in `field_rebuild_step1_2026-11-28.md` (commit 92800a0), run offline. Analysis only: `dk_cbb_field.py`'s live path and the page are untouched, and the HOLD stands.

## Plain-English summary

- **Verdict: NOISE.** The rebuilt field (R1+R2+R3) is much closer to real fields in how it's built: chalkier and duplicating at about the real rate. But it doesn't move the sim's cash line any closer to the real one.
  - Cash line: −0.35 ± 0.47, better on 6 of 16 slates.
  - It also makes the field too optimal on our projections, worse beyond noise.
- **The R4 add-on was triggered and run: also NOISE.** R4 replaces part of each main field with noisier lineups. It fixed that, but the cash-line gain is +0.22 ± 0.29, better on only 7 of 16 slates.
- **Mains alone look a bit better with R4:** +0.20 ± 0.17, 9 of 14. That's context only, since the decision is on all contests pooled.
- **Our payout overstatement doesn't come from the too-unique field.**
  - Re-scored against the rebuilt field, last week's entries are stated at 2.77x what they really won, against 2.86x on today's field.
  - The rebuilt field copies each of our lineups slightly more often (0.15 per 1,000 field lineups, against 0.11), which is far too little to matter.
  - The overstatement sits in the flagships (stated 5.0–5.2x what they won), not in duplication.

## What was run

Scripts and outputs are in `field_rebuild_step2_2026-11-28/`.

- **`extract.py`** gathers, for every graded slate with a sim field saved at lock:
  - the slate as it stood at lock;
  - the saved field (PREVIOUS), z and the shadow's gate;
  - every graded contest's lobby record, real lineups (our entries removed), our entries, and eval.csv's lines.
  - That's 16 slates, 11-16 to 11-26.
- **`gen.py`** builds the candidate pool. It runs battle-royale-research `dk_cbb_field.field()` on the lock-time slate, for 1,500 lineups (FIELD_N × RAKE_POOL, as the live run draws), seed 7, with the saved field's Questionable factor. Then it applies today's ownership correction (own_fix, renormalised to 800).
- **`fit.py`** fits R1+R2+R3, leaving one slate out, on construction only. Cash lines are never used in fitting.
  - **R1:** one field per contest type.
  - **R2:** the rake's weights toward own^γ (renormalised to 800, capped at 100).
  - **R3:** the draw, using either of the pre-registration's two forms:
    - "pow": with replacement, P ∝ weight^β;
    - "copy": (1 − c) × 1,000 drawn the rake's way, plus c × 1,000 copies drawn by weight.
  - **Selection:** γ, the R3 form and its value are picked per type by the loss below, averaged over the other slates' contests of that type.
  - **Loss:** (Δown total/10)² + (Δtop-8/20)² + (Δdup/5)² + (Δtop pair/5)².
  - **Qualifiers:** with fewer than 3 training slates they take the pooled parameters. That happened on 3 of 16 folds.
  - **Chosen held out:**
    - flagship γ 1.75–2.0 with copy 0.10;
    - main γ 1.25 with copy 0.10;
    - qualifier γ 1.0–1.25 with copy 0.1–0.2.
- **`grade.js`** computes the sim's cut lines with `dk_sim.js simulate` exactly as the shadow called it: N = 20, 3,000 nights, our lock-time projection through the gate. It does this for PREVIOUS and for the candidate of the contest's type, on the same seeded nights, against the real cash and top-10% lines in eval.csv.
  - **Reproduction check:** PREVIOUS recomputed this way matches eval.csv's logged `sim_cash` within 1.1 points on 12 of the 13 contests that logged one.
  - **The exception is 11-17,** which is 21 points off: that night's shadow ran on a different field from the one saved at lock.
- **`r4.py`** is the R4 add-on (see below). **`report.py`** produces the tables (`report.out`, `report_r4.out`), and **`shadow_subset.py`** gives section 6's own contest set.

## Results: R1+R2+R3, the registered candidate

The primary contest set is every graded contest with 100+ entries and a real cash line: 69 contests on 16 slates. Gain = |PREVIOUS gap| − |candidate gap|, per slate, ± SE over slates. Positive means the candidate is better.

| | All (69 / 16 slates) | Flagship (21 / 14) | Main (48 / 14) |
|---|---|---|---|
| Mean cash gap, sim − real: PREVIOUS → candidate | +5.0 → +6.9 | +2.6 → +5.3 | +6.1 → +7.6 |
| **PRIMARY:** \|cash gap\| gain | **−0.35 ± 0.47**, 6 of 16 | −0.27 ± 0.72, 7 of 14 | −0.72 ± 0.38, 4 of 14 |
| \|top-10% gap\| gain | −0.32 ± 0.33, 5 of 16 | −0.25 ± 0.51, 6 of 14 | −0.62 ± 0.24, 2 of 14 |
| \|ownership total gap\| gain | +16.4 ± 2.5, 15 of 16 | +28.5 ± 2.4, 14 of 14 | +10.2 ± 2.4, 11 of 14 |
| \|duplication gap\| gain (points) | +11.3 ± 1.0, 16 of 16 | +4.7 ± 1.6, 11 of 14 | +15.0 ± 0.9, 14 of 14 |
| \|top pair gap\| gain | +1.2 ± 2.0, 9 of 16 | +5.4 ± 2.5, 10 of 14 | −1.5 ± 2.0, 5 of 14 |
| \|our projected points per lineup gap\| gain | **−2.65 ± 0.22, 0 of 16** (worse beyond noise) | −2.89 ± 0.65, 1 of 14 | −2.32 ± 0.18, 0 of 14 |

There's no primary for qualifiers: none has 100+ entries.

Construction over every held-out contest (any size), real / PREVIOUS / candidate:

| Type | Ownership total | Duplication % | Top pair % | Projected points per lineup |
|---|---|---|---|---|
| Flagship | 264 / 213 / 243 | 12.1 / 2.4 / 11.6 | 46.9 / 33.8 / 53.2 | 201.8 / 202.2 / 206.4 |
| Main | 242 / 218 / 234 | 28.0 / 5.9 / 23.7 | 40.8 / 36.0 / 48.0 | 198.6 / 201.9 / 204.3 |
| Qualifier | 282 / 237 / 256 | 11.2 / 3.3 / 3.3 | 44.0 / 35.7 / 44.0 | 200.1 / 202.8 / 205.3 |

On section 6's own contests (the one shadow contest a slate, 13 slates), the cash-line gain is −0.70 ± 0.44, better on 4 of 13.

**Rule 5: NOISE.**
- The primary is negative and better on only 6 of 16 slates. The bar is 2×SE for PROVEN, and about 10 of 16 for DIRECTIONAL.
- The projected-points secondary is worse beyond noise.

### Why the construction improved but the line didn't

- R2 and R3 make the field chalkier and more duplicated, as real fields are. But the chalk they concentrate on is our idea of chalk, which is section 3's miss.
- The lineups also project 2–4 points better on our numbers. A field that's more optimal on our projections scores higher in the sim, so the sim's cash line rises, while the real one doesn't.

## R4: the add-on (triggered)

**Why it ran.** The registered condition was that R1–R3 leave a gap in our projected points per lineup. They left one, and widened it: the candidate is 2.3–4.6 points above the real field, against PREVIOUS at 0.4–3.3.

**What it does.** Part of each type's R1–R3 field (a share s) is replaced by lineups drawn uniformly from a second pool. That pool is built with every build style's noise doubled (`gen.py --noise-x 2`). The share s is fit per type, held out, on the R1–R3 loss plus (Δprojected points/2)². The fit chose s = 0.3 for mains (0.0 on 2 folds), 0.0 for flagships and 0.1 for qualifiers.

| | All (69 / 16) | Flagship (21 / 14) | Main (48 / 14) |
|---|---|---|---|
| **PRIMARY:** \|cash gap\| gain | **+0.22 ± 0.29**, 7 of 16 | −0.27 ± 0.72, 7 of 14 (s = 0, same as R1–R3) | +0.20 ± 0.17, 9 of 14 |
| \|top-10% gap\| gain | +0.19 ± 0.22, 7 of 16 | −0.25 ± 0.51 | +0.19 ± 0.15, 9 of 14 |
| \|ownership total gap\| gain | +11.1 ± 2.1, 15 of 16 | +28.5 ± 2.4 | +1.1 ± 1.3, 7 of 14 |
| \|duplication gap\| gain | +7.5 ± 0.8, 16 of 16 | +4.7 ± 1.6 | +9.0 ± 1.0, 14 of 14 |
| \|top pair gap\| gain | +2.4 ± 1.7, 11 of 16 | +5.4 ± 2.5 | −0.1 ± 1.6, 9 of 14 |
| \|projected points gap\| gain | −1.07 ± 0.38, 5 of 16 (worse beyond noise) | −2.89 ± 0.65 | +0.16 ± 0.30, 11 of 14 |

On section 6's contests: +0.26 ± 0.20, better on 9 of 13.

**Rule 5: NOISE.**
- The primary is positive but better on only 7 of 16 slates.
- The projected-points secondary is still worse beyond noise overall, carried by the flagships, where the fit kept s at 0.
- Mains alone (+0.20 ± 0.17, 9 of 14) would read DIRECTIONAL. They're context only, because the registered decision is on pooled contests.

## Section 6's projection-level part, shown separately

The level part is the real field's projected mean minus its actual mean, on our lock-time projections. A field rebuild can't remove it.

| Contests | Level |
|---|---|
| All (16 slates) | +2.83 ± 5.02 |
| Flagship | +1.76 ± 6.31 |
| Main | +5.63 ± 5.04 |

On these 69 contests, PREVIOUS's cash gap is +1.68 ± 5.37 per slate, against section 6's +7.0 on its 13. Almost all of it is that noisy level part, which is why a construction fix can't show a 2×SE gain here.

## Context (outside the tag): our entries against the rebuilt field

This covers last week's entered lineups (11-20 to 11-26) in flagship and main contests. Each is re-scored with `simulate` and `value`, the page's builder with ties split, under today's field and under the rebuilt field (R1–R3, plus R4 where it ran). The real outcome is beside them.

| | Entries (contests), fees | Sim expected payout: today's field | Rebuilt R1–R3 | Rebuilt + R4 | Real won | Top-1% per lineup: today / rebuilt / real | Field copies of each entry, per 1,000 field lineups: today / rebuilt |
|---|---|---|---|---|---|---|---|
| Flagship | 39 (17), $495 | $913.67 (5.22x real) | $877.74 (5.02x) | $877.74 | $175.00 | 0.028 / 0.028 / 0.000 | 0.08 / 0.13 |
| Main | 435 (31), $202.65 | $338.42 (1.29x) | $335.19 (1.28x) | $357.93 (1.36x) | $262.50 | 0.026 / 0.026–0.028 / 0.021 | 0.11 / 0.14–0.16 |
| Both | 474 (48), $697.65 | $1,252.09 (2.86x) | $1,212.93 (2.77x) | $1,235.67 (2.82x) | $437.50 | 0.026 / 0.026–0.028 / 0.019 | 0.11 / 0.14–0.15 |

**The answer:** almost none of the overstatement comes from a too-unique field. Rebuilding the field to duplicate at the real rate moves our stated payout by 1–4%. Even in the rebuilt field our lineups are almost never duplicated (0.15 copies per 1,000). The overstatement is in the flagships (5x), where real results ran far below the sim on 39 entries. That points back at our lineups scoring under their simulated mean (the projection side), not at the field.

## Deviations and notes, stated plainly

1. **R3's form (a deviation in procedure, within the registered wording).**
   - The first fit used only R3's "pow" form. It over-duplicates at every β: 1,000 draws with replacement from a 1,500-lineup pool duplicate 40–50% of lineups even near uniform, against 28% real in mains.
   - I added the registered alternative, "a fixed copy share", to the same held-out fit, which picks the form per type by training loss. It chose the copy form on every fold.
   - This was decided after seeing the training construction fit (`fit_powonly.log`, `construction_powonly.json`), before any cash line was graded.
2. **The loss scales** (10 / 20 / 5 / 5, and 2 for R4's projected points) weren't in the pre-registration. They were fixed before any grading.
3. **Grading projection (a correction, disclosed with the result it replaced).**
   - The first grading pass used today's `gatedProj` (our projection × the Questionable factor). Before 11-25 the shadow used the DraftKings-average gate (`fp_gate`), so the reproduction check failed: mean −9.7 against the logged `sim_cash`.
   - I switched the grading projection to the lock-time `fp_gate` (× the Questionable factor). That reproduces the logged lines on 12 of 13 contests, and every number above uses it.
   - The superseded first pass read +0.46 ± 0.39, better on 11 of 16, for R1–R3. It was graded with the wrong projection for early slates and is not the result.
   - The construction measure "our projected points per lineup" was also switched from fp_dk to fp_gate, to match fieldcheck and step 1. It isn't in the fitting loss.
4. **The primary contest set** is every graded 100+ entry contest (69). Section 6's 13-contest subset is reported beside it, and it agrees: R1–R3 −0.70, R4 +0.26.
5. **What the candidate is built from.** The candidate pool runs today's `dk_cbb_field.py` (styles, own_fix) on each slate's lock-time inputs. PREVIOUS is the field each night actually saved, and fields before 11-24 had no own_fix or rake. So the candidate also differs from PREVIOUS by today's ownership correction, not only by R1–R3.
6. **Qualifiers:** there's no qualifier contest of 100+ entries, so there's no qualifier primary. Qualifier construction is shown for context.
