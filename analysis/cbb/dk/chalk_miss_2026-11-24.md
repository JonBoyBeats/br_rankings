# What predicts the chalk misses (2026-11-24)

Analysis only: nothing here changes the page's ownership until the operator approves a specific correction.
Computed by `python3 scripts/dk_chalk_miss.py --mirror ../br-adp-mirror` on `own_eval.csv`. That is 3,585
player-contests with lock-time features, on 9 slates (45 contests) from 11-16 to 11-22. 11-23 and 11-24 have no
graded standings yet.

**The chalk band** is players with max(ours, actual) of 15% or more: 937 player-contests. Today it has a MAE of
11.3 points, 47.7% of players are off by 10+, and it holds 69% of all absolute ownership error.

## Verdict

- **Two things predict the chalk misses, and both hold up held out by slate.**
  1. **Team chalk concentration.** We over-project players on teams where we have several players at 15%+. Among the
     players we project 10%+, a team with 3 such players averaged −3.4 points (actual minus ours), and a team with 4
     averaged −3.1. A team with 0 averaged +0.9, and one with 1 averaged −0.6. The field spreads a team's ownership
     more than we do. The correlation with the signed miss is r −0.32, negative on 8 of 9 slates.
  2. **Coming off a big game**, meaning last game's DK points were 10+ over his season average (`dk_eval.ownwatch`'s
     flag). The field owns these players more than we do: +5.9 points against −2.6 for the rest of the 10%+ players.
     r is +0.19, positive on 5 of the 6 slates that had any flagged player.
- **The deployable correction passes the bar.**
  - The correction is own' = ours + 0.53 − 1.27 × (players on his team we project 15%+) + 8.4 × big-game flag. It is
    applied only to players we project 10%+, which is known at lock. These are coefficients fitted on all 9 slates.
  - Held out by slate, it brings chalk-band MAE from 11.34 to 10.72: a gain of 0.62 against 2×SE of 0.38, better on
    8 of 9 slates.
  - The share off by 10+ goes from 47.7% to 41.3%, lower on 8 of 9.
  - Each term alone also passes: big 10.96 (7 of 9), team concentration 10.98 (7 of 9).
- **Nothing else does.** Value rank in the salary tier, salary, Q status, the game total, the spread and our own
  projection level each move chalk-band MAE by 0.15 points or less held out (directional only). Our own projection level
  (g) looks like it matters at first (r −0.26: the higher we project, the more we over-project). Once applied it doesn't
  improve the held-out grade.
- **Worth putting on the page? Probably, but shadow it first.** It's 9 slates, and the big-game flag rests on about 107
  player-contests (roughly 25 player-slates) on 6 slates. The additive form also doesn't keep a contest's ownership
  summing to 800%. Adopting it would need a renormalization step, and that step would need its own held-out check.
  - My suggestion: log the corrected ownership beside ours each night for about a week and grade both on the chalk band.
  - Change the page only if it keeps its edge on the new slates.

## The numbers

Each feature against the signed miss (actual − ours) on the chalk band: the pooled correlation, and on how many slates
the correlation was positive.

| Feature | r | Positive on |
|---|---|---|
| (a) value rank in salary tier | +0.08 | 6 of 9 |
| (b) chalky players in his game | −0.14 | 1 of 9 |
| (b) chalky players on his team | −0.32 | 1 of 9 |
| (b) his rank by our own on his team | +0.16 | 8 of 9 |
| (c) salary | −0.00 | 4 of 9 |
| (d) big-game flag | +0.19 | 5 of 6 |
| (e) Questionable at lock | −0.16 | 0 of 1 |
| (f) game total | +0.11 | 6 of 9 |
| (f) his team's spread | −0.19 | 1 of 9 |
| (g) our projected ownership | −0.26 | 2 of 9 |

**Held out by slate (fit on the other 8, scored on the 9th), version B.** This is the deployable version: fitted and
applied on players we project 10%+ and scored on the chalk band. Ours is MAE 11.34 and 47.7% off by 10+.

| Correction | Chalk MAE | Gain (2×SE) | Better on | Off by 10+ | Pass |
|---|---|---|---|---|---|
| bias only | 11.23 | +0.11 (0.17) | 6 of 9 | 44.6% | no |
| big-game flag | 10.96 | +0.38 (0.33) | 7 of 9 | 43.3% | yes |
| team chalk count | 10.98 | +0.35 (0.23) | 7 of 9 | 43.3% | yes |
| game total | 11.19 | +0.14 (0.17) | 6 of 9 | 46.4% | no |
| rank on team | 11.21 | +0.13 (0.17) | 6 of 9 | 43.9% | no |
| Q, salary, value rank, game chalk count, own | 11.23–11.29 | ≤ +0.11 | 5–6 of 9 | 44–46% | no |
| spread | 11.44 | −0.10 (0.93) | 7 of 9 | 46.2% | no |
| **team chalk count + big-game flag** | **10.72** | **+0.62 (0.38)** | **8 of 9** | **41.3%** | **yes** |
| rank on team + big | 10.95 | +0.38 (0.32) | 6 of 9 | 43.2% | no |

**Version A, as specified.** This one is fitted and applied on the chalk-band rows. The band uses the actual
ownership, so it can't be run at lock. It points the same way, with team concentration strongest:
- team chalk count alone: 10.54 (7 of 9, pass);
- team chalk count + his rank on the team: 10.22 (8 of 9, pass);
- team chalk count + big: 10.32 (7 of 9, pass).

## Method and limits

- **Features.** Every feature comes from the night record at lock (`analysis/cbb/dk/<date>_<draft group>.csv`). The
  big-game flag comes from the mirror's morning file before the slate started, using `dk_own_review.big_game_flags`.
  Out players are excluded. Value rank is within the page's salary tiers (6000+, 4000–5999, under 4000).
- **Correction and scoring.** The correction is additive on the signed miss, with ownership clipped at 0. The pass bar
  is the Lab's, scaled to 9 slates: better MAE on 7+ of the slates, a mean gain over 2×SE, and an off-by-10+ share no
  worse than ours.
- **Sample.** Player-contests share players across a slate's contests, so the slate is the unit. With 9 slates, this is
  a first read, not a settled rule.
- **11-24.** Tonight's TCU-MIA showed both patterns pulling against each other. TCU had three players we projected 15%+
  (Harding 43 → 24 and Robinson 32 → 6 fell, as the team term expects), but Avila rose 21 → 42. 11-24 isn't in this data
  until its standings are graded.
