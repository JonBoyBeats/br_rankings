# Checks weighting study (2026-11-24)

Analysis only. Nothing on the page changes until the operator approves the change at the end.
Code: `scripts/dk_checks_weights.py`. Per-slate output: `analysis/cbb/dk/checks_weights_2026-11-24/`
(per_slate.csv, variants.csv, greens.csv, summary.json).

## Verdict

**Weighting the checks is clearly better than counting them as equals, but the weighted checks do not beat our own projection.**

- **Weighted score vs today's equal count** (held out by slate, 12 slates): it ranks tonight's 5x players better.
  - AUC 0.680 against 0.588, a gain of +0.093 (SE 0.030), better on 10 of 12 slates.
  - That passes the Lab bar: 7 of 10, scaled to 9 of 12, and the gain is above 2×SE.
  - Its top 10 per slate finds 37 5x hits against 24; its top 20 finds 61 against 48.
- **Weighted score vs our projection:** no. It is level with our own P(5x) (AUC 0.666, gain +0.014, SE 0.045, better on only 5 of 12) and with plain value fp/salary (0.642, gain +0.038, SE 0.048, 5 of 12).
  - **So the greens are a fast shortcut, not new information.** They point at roughly the players our projection already rates for 5x.
  - Today's equal count was worse than simply sorting by value (0.588 vs 0.642).
- **What carries the weight:** two signals. The **5x rate** (box 4) and **minutes** (box 2).
  - OBPR and the under-2x rate add a little.
  - DK per minute adds nothing once the others are in, so its weight is 0.
  - That fits the coordinator's read: boxes 1–3 are one "good player" signal counted three times, and the 5x rate already carries most of it at tonight's price.
- **The operator's options barely matter yet.** Every combination of last-5/season blend, minutes version and price treatment lands within 0.01 AUC (variants.csv):
  - **Blend weight:** this early, season and last-5 are almost the same games. Through 11-24 no rotation player has more than 6 games, and the last 5 is 4–5 of them.
  - **Minutes:** season mpg was best by a hair, ahead of recent-weighted and tonight's projection, which suits the operator's distrust of the minutes projection.
  - **Price:** "a little" (75% slate-wide, 25% within salary band) was picked over pure slate-wide.
  - **Fully within-band pricing was rejected.** On its own it did no better, but it turned about 5 fringe players a slate green.
- **Greens at the same count as today, held out:** 94 greens with 35 5x hits (37%), against today's 104 greens with 25 hits (24%).
  - Picking the same number of players by our own P(5x) gets 30 hits.
  - So on this measure the new greens edge the projection, while on AUC they don't. Both are within noise.

## Data

- **Slates:** the 12 graded slates 11-16 → 11-23 (11-24's are not graded yet).
  - **Pool:** the checks' own rotation pool (season mpg ≥ 15, 3+ games), not tagged Out at lock: 712 player-slates, 119 hit 5x.
  - **Lock-time rows:** BRR `data/dk/cbb/<date>_<dg>_proj.json`.
  - **Results:** `analysis/cbb/dk/<date>_<dg>.csv` (`actual_dk`).
- **Season game logs exist.** ESPN's athlete gamelog (the endpoint `cbb_nightly.form()` reads) was fetched for the 1,004 graded players, and 949 returned a log. Games are cut to those before tonight's tip.
  - The reconstructed last 5 matches the lock files' `last5` exactly (156 of 156 players on 11-20 main).
  - The lock files of 11-16 and 11-17 had no `last5`, so the logs fill it there for both the equal count and the weighted score. The comparison is of the method, not of the data the page had then.
- **Boxes 6–7 are not fitted.**
  - Bank/field: 8 graded slates have a saved bank (11-16 → 11-23), and its definition changed today (base bank).
  - Scan read: only 4 graded slates were scanned (11-19 main, 11-20 ×2, 11-23).
  - Fit them once about 10 scanned, graded slates exist. Until then they stay out of the score.

## Method

- **Box scores:** each of boxes 1–5 is a continuous score in 0–1: the player's percentile in the slate's rotation pool. The under-2x rate is reversed, so a high score is good.
  - Box 1 keeps the page's "top 2 on his team" route as a floor of 0.7.
- **Variants:** 5 blend weights (last 5 vs season: 0 / .25 / .5 / .75 / 1) × 3 minutes versions × price treatments.
  - Price options: slate-wide; 75/25 slate/band. Pure band and 50/50 were in the first run (see below).
- **Model:** L2 logistic (λ = 1) on the five scores, with no negative weights. A weight below 0 is dropped and the fit redone.
  - **Held out:** for each slate, the variant is chosen by an inner leave-one-slate-out on the other 11, so the held-out slate never chooses its own variant. Then the model is fit on the 11 and scored on the one.
- **Comparisons on the held-out slate:**
  - (a) the page's equal count of boxes 1–5 at its cutoffs (30/70/60/60/40, the mpg-28 and top-2 routes), ties broken by projection;
  - (b) the weighted score;
  - (c) value (fp/salary) and our P(5x): normal around fp, with sd 1.25 × the expected miss.
- **Price restriction:** the first run allowed pure within-band pricing. It was picked on 8 of 12 slates and held-out AUC was 0.676, but at an F1-chosen cut about 59 bench or fringe players went newly green. The operator ruled that out, so the reported run allows only slate-wide or 75/25.

## Results per slate (held out)

| Slate | Pool | 5x hits | AUC equal count (a) | AUC weighted (b) | AUC value | AUC P(5x) | Top 10 hits (a / b) | Top 20 hits (a / b) |
|---|---|---|---|---|---|---|---|---|
| 11-16 156660 | 79 | 13 | 0.622 | 0.678 | 0.789 | 0.789 | 3 / 3 | 4 / 6 |
| 11-17 156662 | 27 | 4 | 0.370 | 0.707 | 0.283 | 0.348 | 1 / 2 | 3 / 4 |
| 11-17 156663 | 101 | 16 | 0.550 | 0.671 | 0.687 | 0.740 | 1 / 2 | 4 / 6 |
| 11-18 157032 | 29 | 6 | 0.761 | 0.783 | 0.743 | 0.645 | 4 / 4 | 6 / 5 |
| 11-18 157033 | 57 | 10 | 0.511 | 0.532 | 0.657 | 0.711 | 2 / 2 | 3 / 6 |
| 11-19 157138 | 45 | 4 | 0.652 | 0.713 | 0.616 | 0.665 | 2 / 2 | 2 / 2 |
| 11-19 157139 | 78 | 16 | 0.495 | 0.598 | 0.612 | 0.658 | 1 / 3 | 4 / 5 |
| 11-20 157013 | 38 | 6 | 0.599 | 0.589 | 0.661 | 0.703 | 2 / 3 | 5 / 4 |
| 11-20 157015 | 79 | 18 | 0.559 | 0.675 | 0.761 | 0.742 | 2 / 5 | 5 / 7 |
| 11-21 157017 | 56 | 7 | 0.665 | 0.892 | 0.656 | 0.738 | 1 / 5 | 3 / 5 |
| 11-22 157019 | 68 | 12 | 0.623 | 0.594 | 0.665 | 0.670 | 3 / 4 | 6 / 6 |
| 11-23 157021 | 55 | 7 | 0.646 | 0.732 | 0.579 | 0.589 | 2 / 2 | 3 / 5 |

**Totals:**

| | Mean AUC | Top-10 hits | Top-20 hits |
|---|---|---|---|
| (a) equal count | 0.588 | 24 | 48 |
| (b) weighted | 0.680 | 37 | 61 |
| (c) value | 0.642 | 36 | 59 |
| (c) P(5x) | 0.666 | 37 | 63 |

**Paired, per slate:**

| Comparison | Mean diff | SE | Better / worse (of 12) |
|---|---|---|---|
| (b) − (a), AUC | +0.093 | 0.030 | 10 / 2 |
| (b) − value | +0.038 | 0.048 | 5 / 7 |
| (b) − P(5x) | +0.014 | 0.045 | 5 / 7 |
| (b) − (a), top-10 hits | +1.08 a slate | 0.38 | 7 / 0 |

Points per $1k (secondary): the Spearman correlation is about 0.27 for every method, so none separates the middle of the pack.

## The weights (fit on all 12 slates), rescaled so a perfect player scores 7

| Box | Weight of 7 |
|---|---|
| 1 OBPR (75% slate-wide, 25% within salary band) | 0.42 |
| 2 MPG (season mpg; 75/25 slate/band) | 1.63 |
| 3 DK per minute | 0.00 (dropped) |
| 4 5x rate at tonight's salary (blend of last 5 and season) | 4.45 |
| 5 under-2x rate (same blend, reversed) | 0.50 |

The weights are the same to two decimals whether the blend is last-5 only, 50/50 or season only, because the games are the same games this early. Use the 50/50 blend the operator asked for; it costs nothing now, and it will matter once a season runs past 10 games.

## Green threshold (held out)

- **The cut:** greens are set to the same share as today's (4+ of 5 boxes, about 15% of the pool). The cut is taken on the training slates and scored on the held-out one. The cut lands at **5.2 of 7**; per-slate cuts range 5.11–5.36.
- **Fringe guard:** with the guard (season mpg ≥ 20 AND tonight's projected minutes ≥ 20), 94 greens, 35 hits.
  - Without the guard, 105 greens and 36 hits.
  - The guard removes 11 newly green fringe players and costs 1 hit.
  - Today's rule (no guard) has 2 fringe greens.

**Bench and fringe players who would be newly green without the guard** (green at 5.2, not green today, season mpg or tonight's projection under 20):

| Slate | Player | Team | Salary | Proj min | Season mpg | Score | Hit 5x |
|---|---|---|---|---|---|---|---|
| 11-16 | Joe Philon III | UCLA | 4,500 | 19.9 | 18.7 | 5.44 | no |
| 11-16 | Jeremy Dent-Smith | STMRY | 4,000 | 17.8 | 21.5 | 5.54 | no |
| 11-18 | Jamichael Davis | RU | 4,500 | 17.8 | 19.5 | 5.28 | no |
| 11-18 | Jordan Frison | WICH | 5,100 | 17.1 | 22.2 | 5.70 | no |
| 11-19 | Wei Lin | ORE | 4,900 | 17.6 | 19.0 | 5.46 | no |
| 11-19 | Fedor Zugic | STC | 4,200 | 19.7 | 20.6 | 5.55 | no |
| 11-20 | Thomas Bassong | MSST | 4,700 | 16.7 | 18.6 | 5.27 | no |
| 11-21 | Jordan Frison | WICH | 4,900 | 19.4 | 22.6 | 5.38 | yes |
| 11-22 | Jaylon Dean-Vines | MCNE | 4,900 | 19.4 | 22.7 | 5.77 | no |
| 11-22 | Christian Nitu | MCNE | 4,400 | 18.3 | 21.7 | 5.52 | no |

1 hit in 10, which is why the guard is part of the proposal. With the guard, none of these is green.

## Proposed page change (for the operator to approve; nothing ships until then)

In `dk.html` `checksMap()` and `ckBadge()`:

1. **Badge:** reads "5.3 of 7", replacing "4/5".
   - Score = 0.42 × OBPR + 1.63 × MPG + 0 × DK/min + 4.45 × 5x rate + 0.50 × under-2x.
   - Each box is the player's percentile in the slate's rotation pool (season mpg ≥ 15, 3+ games).
   - Boxes 1 and 2 use 0.75 × the slate-wide percentile + 0.25 × the percentile within his salary band (< $5k, $5–7k, $7k+).
   - Box 1 keeps the top-2-on-his-team floor (0.7).
   - Box 2 uses season mpg.
   - Boxes 4 and 5 use a 50/50 blend of the last-5 and season rate at tonight's salary.
2. **Green:** score ≥ 5.2 AND season mpg ≥ 20 AND tonight's projected minutes ≥ 20.
   - The existing greys stay (Out, unresolved Q, sit risk, 0 games).
   - Light green is not tested; drop it, or set it at 4.6–5.2 as display only.
3. **Hover:** lists each box's score and its weight (e.g. "5x rate 0.80 × 4.45 = 3.56"). DK/min is shown as "not weighted (carried by the others)".
4. **Boxes 6 (bank/field) and 7 (scan read):** shown as separate marks in the hover, outside the score, until they're fitted.
5. **Weights:** in one constant (`CK_W`), refit monthly with this script. The Boxes fold's percentile cutoffs go away.

**A cheaper alternative with the same information:** the evidence says the weighted checks and our P(5x) agree. Showing our P(5x) as the badge, and greening the top ~15% with the same minutes guard, would be equally good and needs no new weights. The weighted checks keep the "which boxes" explanation the operator likes. That's the operator's call.
