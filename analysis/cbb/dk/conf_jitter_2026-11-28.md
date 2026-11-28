# Confidence-scaled projection noise in the bank (2026-11-28)

This is an analysis-only study requested by the operator through the coordinator. The HOLD stands: nothing on the page, in the projections, the ownership, the field, the cut or the fill changes. Tags follow rule 5 of [process.md](process.md).

It refines Section 7's jitter recipe (d) from [bank_recipe_2026-11-28.md](bank_recipe_2026-11-28.md). Recipe (d) multiplies each draw's projections by `exp(σZ − σ²/2)`, where `σ = k × tier miss / tier mean` and k = 0.5. The idea under test is to scale σ per player by how much we trust that player's projection:
- **Greens:** more trusted, so less noise.
- **Source agreement:** less noise when we, Gajewski and RotoWire agree on both minutes and points per minute. More noise when the sources disagree with us on minutes or points per minute, in either direction.

## Pre-registration (committed before anything was run)

Everything in this section was written and pushed before any of the analysis below was computed.

### Step A1: do greens predict a smaller miss?

- **Data:** the greens rebuilt in [bank_recipe_2026-11-28/greens_by_slate.json](bank_recipe_2026-11-28/greens_by_slate.json) on the 18 graded slates. The rows are the graded night records (`analysis/cbb/dk/<slate>.csv`): `fp_dk` is our lock projection and `actual_dk` is the result.
- **Population:** the same as Section 7's 1a, so rotation players only (season mpg 15+, 3+ games, not Out at lock).
- **Measures:**
  - the absolute miss `|actual − fp_dk|`;
  - the relative miss `|actual − fp_dk| / fp_dk`, on rows with `fp_dk ≥ 5`.
- **Comparison:** greens minus matched non-greens, matched by salary band (<$5k, $5–7k, $7k+) × projection band (<10, 10–25, 25+). Each cell is compared separately, weighted by the cell's greens, with the slate as the unit.
- **Reporting:** all 18 slates, and the 6 slates after the weights' fit (2026-11-24 on) separately, each as mean ± SE over slates with k of n.
- **Right direction:** greens miss by less. The matched difference is negative.

### Step A2: does source disagreement predict a bigger miss?

- **Data:** every slate with a Gajewski or RotoWire file, any contest type, from the private source tables in battle-royale-research (`data/dk/cbb/sources/<source>_table.csv`). Actual minutes and DK points come from ESPN box scores, scored the same way as the night records.
- **Population:**
  - The player is not Out at lock.
  - Our projected minutes are at least 10.
  - At least one source covers him and projects 10+ minutes.
  - The game is final.
- **Disagreement:**
  - On minutes: `dm = max over sources |our min − source min|`.
  - On points per minute: `dp = max over sources |our fp_dk / our min − source DK points / source min|`.
- **Bins,** by quantiles within each slate, fixed now:
  - Take each player's slate percentile on `dm` and on `dp`, and let `D` be the larger of the two.
  - **Agree:** `D < 0.50`.
  - **Mild:** `0.50 ≤ D < 0.80`.
  - **Strong:** `D ≥ 0.80`.
- **Outcomes by bin:**
  - `|actual DK − fp_dk|`;
  - `|actual minutes − our min|`, with players who didn't play counted as 0 minutes and 0 points;
  - the gap between the strong and agree bins, per slate.
- **Who is right:** in the mild and strong bins, how often a source's points are closer to the actual than ours, and the same for minutes. With two sources, the source closest to us is used.
- **Right direction:** misses grow from agree to strong. The strong − agree gap is positive.
- **Thin-sample rule:** with fewer than 5 slates this is labelled context only, and I state how many more nights the test needs. That estimate is the number of slates at which the observed gap would reach 2×SE at the observed spread per slate.

### Step B: bank replay (only if A1 or A2 points the right way)

- **Harness:** [bank_recipe_2026-11-28/recipe.js](bank_recipe_2026-11-28/recipe.js) and `score.py`, with the same 14 builds, the same 1,500 lineups, the same merit cut to 30%, the same fill and the same seed policy.
- **Recipes:**
  - **(d):** uniform k = 0.5 (the comparison).
  - **(d-g):** k = 0.5, with a green's σ multiplied by 0.5.
  - **(d-s):** k = 0.5, with σ multiplied by the source bin: agree × 0.5, mild × 1, strong × 1.5. Uncovered players get × 1. This runs only on builds with source files and graded standings.
  - **(d-gs):** both multipliers together, where possible.
- **Reporting:** kept-pool and fill finish percentile against (d), dollars, distinct cores and max exposure, each as k of n slates, and the rule-5 tag.
- **Decision:**
  - Uniform (d) stays the batch item.
  - A scaled version replaces it only if it beats (d) under rule 5. That means PROVEN, or DIRECTIONAL (positive on at least 60–65% of slates with no secondary worse beyond noise) to ship as PROVISIONAL.
  - (d-s) can't be tagged on fewer than 5 builds.

## Results (run after the pre-registration commit ec8ebe0)

The scripts and their printed output are in [conf_jitter_2026-11-28/](conf_jitter_2026-11-28/): `a1.py` → `a1.out`, and `a2.py` → `a2.out`. `a2.py` reads the private source tables and prints aggregates only.

### Verdict

| Step | Result | Tag |
|---|---|---|
| A1, greens | On all 18 slates, greens miss our projection by **more** than matched non-greens, not less: absolute miss +1.49 ± 1.00 (greens miss less on only 7 of 18), relative miss +0.006 ± 0.039 (11 of 18). On the 6 slates after the weights' fit, the direction is right but inside noise: −0.32 ± 0.81 and −0.050 ± 0.031, each 4 of 6. The sign flips between the fit slates and the later ones. | NOISE. Greens are not a reliable "trust this projection" signal. |
| A2, source disagreement | 2 slates (11-27 early and main), 257 players. Strong − agree on the points miss: +1.80 ± 1.85, positive on 1 of 2. On the minutes miss: −0.02 ± 0.31. Where we disagree, the source is closer on points 55–57% of the time, but on minutes only 43–45%. | Context only (2 of the 5 slates the rule needs). At the observed spread it needs about 9 slates to reach 2×SE, so 7 more source nights. |
| B, bank replay | **Not run.** A1 doesn't point the right way. A2 is context only, and (d-s) would have no graded build with a source file anyway: the only source nights are 11-27, whose standings aren't uploaded. | Uniform (d) at k = 0.5 stays the batch item. |

### A1 detail (`a1.out`)

| Greens − matched non-greens | All 18 slates | Fit slates (12) | After the fit (6) |
|---|---|---|---|
| \|actual − proj\| | +1.49 ± 1.00, less on 7 of 18 | +2.40 ± 1.39, less on 3 of 12 | −0.32 ± 0.81, less on 4 of 6 |
| \|actual − proj\| / proj | +0.006 ± 0.039, less on 11 of 18 | +0.034 ± 0.056, less on 7 of 12 | −0.050 ± 0.031, less on 4 of 6 |

One fit slate (2026-11-18 157032, 3 matched greens, +16.7) pulls the all-slate absolute figure up. The relative miss is the steadier measure, and it is flat overall.

### A2 detail (`a2.out`)

| Slate | Agree (n, \|miss\|, \|min miss\|) | Mild | Strong |
|---|---|---|---|
| 2026-11-27 early 157545 (RotoWire) | 33, 7.24, 5.47 | 48, 6.29, 4.52 | 47, 10.89, 5.76 |
| 2026-11-27 main 157547 (both sources) | 36, 8.22, 7.81 | 48, 11.56, 9.16 | 45, 8.16, 7.48 |

- The early slate fits the idea: the strong bin misses by 3.6 more points.
- The main slate doesn't: the mild bin is worst, and strong is level with agree.
- On minutes the sources were closer than us less than half the time. That is consistent with RotoWire's minutes running behind ours on the early slate.

### What would change this

- **Sources:** after about 7 more slates with a source file, ideally with graded mains, A2 can be tested properly, and (d-s) replayed on builds that have source files.
- **Greens:** nothing here supports scaling their noise down.
