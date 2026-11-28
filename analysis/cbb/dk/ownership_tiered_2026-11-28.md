# DraftKings CBB: the tiered-ownership test (2026-11-28)

The operator approved this study (Friday review section 3). It is analysis only, and **the HOLD stands.** Tags follow the tiered bar ([process.md](process.md), rule 5).

- **Code:** [ownership_tiered_2026-11-28/ot.py](ownership_tiered_2026-11-28/ot.py)
- **Output:** [ot.out](ownership_tiered_2026-11-28/ot.out)
- **Data:** 16 graded slates with 100+ entry contests (69 contests). There are 2,632 player rows (not Out, with our ownership).
  - Real ownership is the entries-weighted mean over the slate's 100+ contests, with 0 for a player a contest's standings don't list.
  - Everything is leave-one-slate-out, with SE over slates.

**The framing, as agreed.** Projection, field ownership and our exposure are three numbers. Our field-ownership model is built on our projection. The projection is reliable at $7k+ and weak below. So the test asks whether **(A)** a field-side ownership model below a crossover, **(B)** a cap on fading the field's cheap and rotation players, or **(C)** both beat today's numbers.

## Verdict

**All three are NOISE. None beats today's numbers, and A is worse.**

- **A (the tiered field-ownership model) loses wherever it's used, and the data pushes it off the table.**
  - In every fold, the held-out choice put the crossover at the lowest option offered ($5k). The field-side model was confined to the cheapest tier.
  - Even there it was worse: **chalk MAE −1.17 ± 1.54 (ahead on 6 of 16)** and all-player MAE −0.17 ± 0.11.
  - It also makes the concentration miss worse: **the field's top 8 minus the model's runs 34.8 against today's 18.6** (−11.3 ± 4.8, 5 of 16).
  - **The reason:** the field-side prediction correlates **0.94** with our own raw ownership below $7k. Today's ownership model already carries the field-visible signals (DK-average value, recent box scores, the line), and a linear refit of them is flatter, not sharper.
  - The concentration miss isn't an input problem the field-side signals can fix.
- **B (fade cap against today's ownership):** held out against the board's top half (the same selection without the cap), it gains **+0.11 ± 0.40 finish pct (5 of 9)** and **+$0.08 ± 0.23 per lineup per contest (4 of 9).**
- **C (A + B):** **−0.22 ± 0.20 pct (2 of 9)** and +$0.19 ± 0.23 (6 of 9).
- Both B and C beat *all kept* (+1.0 and +0.7 pct). That comes from the board's own ranking (keeping the top half), not from the cap.

**Nothing is proposed.**

---

## A. The tiered field-ownership model

**How it works:**
- **At and above the crossover:** our ownership, unchanged (live: the record's `own`, with the correction).
- **Below it:** a field-side model, a ridge least-squares fit on log(real + 0.5), with a linear blend over the $1k below the crossover.
- **The field-side inputs**, all lock-time and field-visible. Each comes from the lock file, and each is also used as its percentile within the slate:
  - salary;
  - DraftKings' season average per $1k (the value the field sees on DK);
  - last game's and last 3 games' DK points per $1k;
  - last game's minutes and season mpg;
  - EvanMiya's per-minute × mpg per $1k;
  - the implied team total;
  - team concentration (teammates in the slate's top 15 by DK-average value);
  - games played.
- **Chosen held out on the other slates:** the crossover ($5k / $6k / $6.5k / $7k / $7.5k / $8k), the blend, whether to rescale the sub-crossover predictions to our own sub-crossover total, and a concentration exponent (pred^1 / 1.5 / 2 / 3).

**Choices made held out:** 16 of 16 folds chose the **$5k** crossover. 12 chose exponent 1.5 with no rescale, 3 chose exponent 1 with rescale, and 1 chose 1.5 with rescale. A first run without the $5k option or the exponent chose $6k on all 16 and was far worse: chalk −5.80 ± 2.22 under $5k, concentration 66 against 19.

Gain is today's MAE minus the new model's MAE, so positive means the tiered model is better:

| Tier | Measure | Tiered model | Live (today) | Raw | Gain vs live | Gain vs raw |
|---|---|---|---|---|---|---|
| < $5k | chalk-band MAE | 16.74 ± 2.27 | 15.57 ± 2.80 | 15.49 ± 2.80 | **−1.17 ± 1.54, 6 of 16** | −1.25 ± 1.55 |
| < $5k | off by 10+ | 0.62 | 0.64 | 0.64 | +0.01 ± 0.06, 7 | +0.01 ± 0.06 |
| < $5k | all-player MAE | 1.29 | 1.12 | 1.12 | −0.17 ± 0.11, 5 | −0.17 ± 0.11 |
| $5k+ | every measure | = live | | | 0 (not applied) | −0.06 to +0.15 (the correction vs raw) |
| all | chalk-band MAE | 10.13 ± 0.68 | 9.91 ± 0.66 | 9.97 ± 0.66 | −0.22 ± 0.30, 6 | −0.15 ± 0.33 |
| all | off by 10+ | 0.38 | 0.39 | 0.39 | +0.01 ± 0.01, 9 | +0.01 ± 0.02 |
| all | all-player MAE | 2.32 | 2.21 | 2.21 | −0.12 ± 0.07, 5 | −0.12 ± 0.07 |
| all | **concentration** (real top 8 − predicted top 8) | 34.8 ± 8.7 | 18.6 ± 7.6 | 17.8 ± 7.6 | **−11.3 ± 4.8 (on \|miss\|), 5 of 16** | −12.1 ± 4.9 |

**What the field-side model weights** (all slates): the field's value on DK's own screen dominates (percentile of DK-average value +3.46), then EvanMiya's value (+2.11), last-3 value (+1.23) and salary. That is the same information our ownership already reflects. The two correlate at 0.94 ± 0.01 per slate below $7k.

**Tag: NOISE.** It's worse on the chalk band and on concentration, and the data won't let it past the cheapest tier.

**Not reconstructable at lock** (field-visible, not stored):
- other sites' projections and ownership projections (the field reads them);
- news and lineup previews;
- line movement;
- DK's own projection display;
- player popularity and name value.

These are the likeliest sources of the field's concentration. None of them can be tested from what we log.

## B and C. Tiered exposure (bank, cut and fill weighting)

**How it works:**
- On the builds with board values and graded 100+ contests (**9 builds**; the other 5 of the 14 lack a graded 100+ contest in this data set or stored board values), keep half the kept pool.
- Rank by **board value rank + λ × the lineup's sub-$7k "fade gap"**. The fade gap is the sum over its sub-$7k players of max(0, predicted field ownership − our kept-pool exposure) / 100.
- **B** uses today's ownership as the field reference; **C** uses A's tiered model.
- λ is chosen held out on finish percentile, from 0 / 0.5 / 1 / 2 / 4. λ = 0 is the board-only top half (the reference).
- Scored on the 100+ contests by finish percentile and payout per lineup per contest.
- The optional cheap-tier value shrink wasn't run: it needs the bank re-drawn on shrunk projections, and the build replay can't do that.

| | Against | Finish pct, all | flagship | main | $ per lineup per contest, all | flagship | main |
|---|---|---|---|---|---|---|---|
| **B** (λ chosen 1 or 2) | board top half | **+0.11 ± 0.40, 5 of 9** | +0.10 ± 0.40 | +0.21 ± 0.51 (7) | **+0.079 ± 0.231, 4 of 9** | +0.227 ± 0.443 | +0.022 ± 0.043 |
| B | all kept | +1.01 ± 0.51, 7 | +1.02 ± 0.52 | +1.36 ± 0.59 | +0.174 ± 0.348 | +0.395 ± 0.720 | +0.067 ± 0.039 |
| **C** (λ chosen mostly 2) | board top half | **−0.22 ± 0.20, 2 of 9** | −0.23 ± 0.20 | −0.18 ± 0.25 | **+0.193 ± 0.232, 6 of 9** | +0.450 ± 0.424 | +0.038 ± 0.048 |
| C | all kept | +0.69 ± 0.55, 5 | +0.69 ± 0.56 | +0.97 ± 0.67 | +0.288 ± 0.333 | +0.617 ± 0.672 | +0.083 ± 0.040 |

**Fixed λ, for the shape only** (not held out; finish pct against the board top half):

| λ | B | C |
|---|---|---|
| 0.5 | +0.18 ± 0.13, 6 of 9 | +0.16 ± 0.11, 6 of 9 |
| 1 | +0.40 ± 0.33, 7 | +0.23 ± 0.26, 4 |
| 2 | +0.33 ± 0.58, 4 | +0.24 ± 0.53, 4 |
| 4 | −0.00 ± 0.81, 4 | −0.23 ± 0.68, 2 |

**Tags:**
- **B: NOISE.** Held out it's 5 of 9 on finish and 4 of 9 on dollars, inside noise. A small cap (λ 0.5) leans positive (6 of 9, +0.18 ± 0.13), but that's chosen after the fact.
- **C: NOISE.** Held out it's behind on finish (2 of 9). The dollars lean its way (6 of 9, +0.19 ± 0.23), inside noise.
- **The gain over all kept (B +1.01, 7 of 9) is the board's ranking, not the cap.** The board-only top half gets almost all of it; the Friday review found the same (section 8).

**How this differs from the failed re-ranking** ([ownership_disagreement_2026-11-28_followup.md](ownership_disagreement_2026-11-28_followup.md)):
- That one ranked lineups by a *predicted disagreement*: d̂ from pre-lock signals that track real − ours at r ≈ 0.1. It summed d̂ with a sign that flipped at $7k.
- This one changes the *ownership source* (A) and limits only how far below the field's predicted ownership our exposure may fall (B and C). It doesn't try to predict who the field will be right about.
- It did no better, for the reason A shows. Our ownership and the field-side read are nearly the same number (r 0.94). A cap built on either puts the kept pool back near the field, and on these 9 builds that hasn't paid.

## Summary of tags

| Item | Tag | Numbers |
|---|---|---|
| A: field-side ownership below a crossover | **NOISE** (worse) | crossover pushed to $5k in 16 of 16 folds; < $5k chalk −1.17 ± 1.54 (6 of 16); concentration −11.3 ± 4.8 (5 of 16) |
| B: fade cap against today's ownership | **NOISE** | +0.11 ± 0.40 pct (5 of 9), +$0.08 ± 0.23 (4 of 9) against the board top half |
| C: A + B | **NOISE** | −0.22 ± 0.20 pct (2 of 9), +$0.19 ± 0.23 (6 of 9) |
| The concentration miss is not fixed by field-visible inputs | finding | the field-side model is flatter (34.8 vs 18.6); the source is outside the data we log |

**Watch:** the concentration miss stays on the Friday watch list. It needs an input we don't have, such as a public ownership projection captured at lock, before it can be tested.

**Note, 2026-11-28 (unified contest types):** the flagship/main split in B/C used a by-size rule (under 800 entries = flagship). It's re-cut on the DK page's profile (`scripts/dk_contest_type.py`) in `ownership_tiered_2026-11-28/ot_recut.out`. Every row moves by at most ±0.12 $ per lineup and ±0.01 finish percentile. On true flagships, B against the board's top half is +$0.26 ± $0.56 (4 of 9), and the finish percentile is +0.10 ± 0.40 (4 of 9). All of it is still NOISE.
