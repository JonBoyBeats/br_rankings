# Section 7: greens on every slate, Lab d's control, and a better bank recipe (2026-11-28)

The operator's two questions, relayed by the coordinator. This is analysis only, with one lab-definition change. The HOLD stands: nothing on the page, in the projections, the ownership, the field, the cut or the fill changes. Tags follow rule 5 of [process.md](process.md). Contest types come from `scripts/dk_contest_type.py`.

Every number below is computed by the scripts in [bank_recipe_2026-11-28/](bank_recipe_2026-11-28/), and their printed output sits beside them (`*.out`).

## Verdict

| Question | Answer | Tag |
|---|---|---|
| 1a. Do greens beat our own projection? | Greens beat matched non-greens on outcomes, but mostly on slates the weights were fit on. After the fit (6 slates), they still score more per $1k (+0.65 ± 0.27 DK/$1k, 5 of 6), but they do **not** beat our projection (+0.98 ± 1.39, 3 of 6). They mostly identify players we already rate higher. | Identify better players: DIRECTIONAL. Beat our projection: NOISE |
| 1b. A GREENS rule draw vs the plain L0 U0 draw | +1.55 ± 0.74 finish percentile, ahead on 12 of 16 slates. All of it is on the fit slates (+2.65, 9 of 10). After the fit it is −0.29 ± 1.25 (3 of 6). | NOISE: the sign flips out of sample |
| 1c. Lab d with its new control | 5 slates counted: +7.59 ± 6.77, ahead on 3 of 5. Every drawn green lineup against the replay: +5.65 ± 4.56, ahead on 4 of 5. | running (lab) |
| 2. Which bank recipe gives variety and results? | **All plain** gives the best results but loses variety: kept pool +3.22 ± 0.84 (12 of 14), fill +2.93 ± 1.14 (10 of 14), with 40 fewer distinct cores and +10 points of max exposure. **Plain + projection noise at half the measured miss** keeps Draw-the-9's variety (cores +0.4, max exposure −2.8 points): fill +4.15 ± 1.91 (10 of 14), kept +1.05 ± 0.86 (12 of 14). At the full measured miss it turns negative (−5.23 kept). The lean cells are what cost Draw-the-9 its results: its bank scores 7.7 points below the plain bank. | All plain over Draw-the-9: PROVEN on results, fails on variety. Jitter at 0.5: DIRECTIONAL (size-sensitive). Green cores and light leverage: no better than plain |
| $ | Every recipe's dollar difference is inside the noise. Single flagship cashes carry each total, e.g. light's +$1,818 on one night. | NOISE |

## 1. Greens on every slate

### How greens were rebuilt

`greens_player.py` rebuilds the greens with the shipped `checksMap` (dk.html, 2026-11-24). The score is out of 7:

| Box | Weight | How it's measured |
|---|---|---|
| OBPR | 0.42 | 75% slate-wide percentile, 25% within salary band; top-2 BPR on his team floors it at 0.7 |
| MPG | 1.63 | the same 75/25 mix |
| DK/min | 0 | not weighted |
| 5x rate | 4.45 | half his last 5 games, half his season, at tonight's salary |
| under-2x rate | 0.50 | the same blend, reversed |

- Each box is a mid-rank percentile among the slate's rotation players: season mpg 15+, 3+ games, any status.
- A player is green at a score of 5.2+ with 20+ season mpg and 20+ projected minutes, and not Out.
- It covers every graded slate: 18 slates, 3 to 22 greens a slate (`greens_by_slate.json`).

**What can't be rebuilt exactly at lock**
- **OBPR:** the lock rows have no OBPR before 2026-11-20. The OBPR box sits at the neutral 0.5 there, which is weight 0.42 of 7.
- **Last 5 games:** missing before 2026-11-18. Those slates use the last five games of the season log.
- **Season game log (`season_dk`):** only in the lock rows from 2026-11-24 on. Earlier slates use ESPN's game log fetched on 2026-11-28 and filtered to games before tip-off, so later ESPN stat corrections are in.
- **Questionable players:** they count as never green. The page greys a Questionable player until the operator sets Play, and those decisions are not logged.
- **Sit risk:** the flag is not rebuilt.
- **The weights are partly in-sample.** They were fit on the slates through 2026-11-23 (`checks_weights_2026-11-24.md`). So 12 of these 18 slates are in-sample for 1a, and 10 of 16 for 1b. The split in `oos.out` is the honest read.

### 1a. Player level (`greens_player.out`, `oos.out`)

The comparison: greens minus non-greens among the slate's rotation players who were not Out. Each salary band (<$5k, $5–7k, $7k+) × projection band (<10, 10–25, 25+) cell is compared separately, weighted by the cell's greens. The slate is the unit.

| Matched difference | All 18 slates | Fit slates (12) | After the fit (6) |
|---|---|---|---|
| 5x rate | +0.185 ± 0.055, 15 of 18 | +0.248 ± 0.068, 11 of 12 | +0.060 ± 0.078, 4 of 6 |
| actual − our projection | +2.11 ± 1.21, 12 of 18 | +2.68 ± 1.70, 9 of 12 | +0.98 ± 1.39, 3 of 6 |
| DK points per $1k | +0.88 ± 0.19, 15 of 18 | +1.00 ± 0.24, 10 of 12 | +0.65 ± 0.27, 5 of 6 |
| our projected value (reference) | +0.59 ± 0.06, 18 of 18 | | |

- **Within the same salary and projection band, greens carry more projected value.** We already rate them higher, by +0.59 points per $1k.
- **Their outcome edge over that is what the projection misses:** +2.11 points on all slates.
- **One slate pulls that figure up.** It is +1.12 ± 0.73 (11 of 17) without 2026-11-18 157032, where 3 greens were +19.1.
- **After the fit it is +0.98 ± 1.39, 3 of 6.** That is NOISE as "greens beat our projection".
- **As a marker of players who score more per dollar, it holds out of sample** (+0.65 ± 0.27, 5 of 6). That is DIRECTIONAL, and it overlaps our own value ranking.

### 1b. Lineup level (`recipe.js`, `score.py`, `score.out`)

On each of the 16 graded slates with standings (lock-time slate and field from the mirror, `extract.py`), two draws of 600 lineups each:
- **GREENS rule:** at least n of the slate's greens, n = 3 with 5+ greens, else 2, as Set greens sets it.
- **Plain L0 U0.**

Both draws use the page's draw: DKSim.poolDraw, Bank noise 0.35, the deep bench left out, a fixed seed per draft group. They are scored as the Lab scores, on real finish percentile in every graded contest of 100+ entries.

| GREENS − plain | Diff ± SE | Slates ahead |
|---|---|---|
| All contests | +1.55 ± 0.74 | 12 of 16 |
| Flagship | +1.56 ± 0.82 | 11 of 14 |
| Main | +1.66 ± 0.82 | 11 of 14 |
| Qualifier | no 100+ entry qualifier with standings | |
| Top-10% rate | +1.05 ± 0.53 points | 12 of 16 |
| Fit slates | +2.65 ± 0.76 | 9 of 10 |
| After the fit | −0.29 ± 1.25 | 3 of 6 |

The overall figure clears 2×SE, but only because of the slates the weights were fit on. Out of sample the sign flips, so this is **NOISE**. The per-contest rows are in `score.out`.

**Limitation:** the rule is slate-wide. The page's Set greens works per game (GREENS <game>), and the per-game form was not replayed.

### 1c. Lab d's control (lab definition change; `lab.json`, `scripts/dk_eval.py`, `scripts/dk_lab_control.py`)

- **The new control** is the same night's plain L0 U0 draw, replayed at lock: no rules, Bank noise 0.35, the deep bench out, seeded by draft group, 600 lineups, uncut.
- **Where it's saved:** `analysis/cbb/dk/lab_controls/<date>_<draft group>.json`. `scripts/dk_lab_control.py` writes it for any saved build without one; it runs recipe.js `plain600` and is run by hand.
- **What it replaces:** the operator's own "at least N of" group lineups. Green-only nights now count.
- **The treatment is unchanged:** the kept green lineups.
- **Grading:** `dk_eval.py lab` appends the replay after the bank's pool and scores it the same way. A night without a saved replay has no control.
- **Recorded:** a dated amendment in `lab.json` and a row in `versions.csv`.
- **Test:** `tests/dk_lab.py` checks the new control, and all 13 checks pass.
- **11-27 (157547):** its replay is written once its night record exists. `slate_for` needs the record.

**Re-grade** (5 counted slates):

| Night | Green kept | Kept − replay | Every drawn green lineup − replay |
|---|---|---|---|
| 2026-11-24 157024 | 260 | +11.05 | +5.74 |
| 2026-11-25 157293 | 609 | +3.82 | +2.13 |
| 2026-11-25 157295 | 522 | −5.47 | −3.32 |
| 2026-11-26 157380 | 764 | −3.48 | +0.78 |
| 2026-11-26 157382 | 750 | +32.03 | +22.95 |
| **Lab d** | | **+7.59 ± 6.77, ahead 3 of 5** | +5.65 ± 4.56, ahead 4 of 5 |

- The registered form compares kept (cut) green lineups with an uncut replay. The cut keeps lineups with the better simulated value, which gives the treatment a small head start.
- The symmetric check, every drawn green lineup against the same replay (`lab_d_check.out`), is smaller but has the same sign.
- One night, 157382, carries most of the mean.
- The lab keeps running to its 10 slates.

## 2. A better bank recipe (`recipe.js`, `score.py`, `score.out`, `pairs.out`, `score_jk1.out`)

### How each recipe was replayed

There are 14 saved builds; 11-21 and 11-22 have none. On each, every recipe is replayed in the same steps:

1. **Draw** 1,500 lineups with the page's draw, as in 1b.
2. **Cut** by merit to 30% (DKSim.cutPool, each batch its own idea, floors max(5, 1%), 1,000 nights). The builds kept 20–35%.
3. **Fill** every contest the build entered, as the fill studies do:
   - largest stake first;
   - a lineup in at most 3 contests;
   - night cap 60%;
   - DKSim.pick with the build's pick settings: Max coverage for flagships, Max ROI otherwise.

The recipes:

| Recipe | What it draws |
|---|---|
| (a) d9 | today's Draw-the-9 mix: the 9 cells L{0, .1, .2} × U{0, 1, 2}, equal shares, Under at 10% owned |
| (b) plain | L0 U0 only |
| (c) greencore | a third under the slate's GREENS rule, as in 1b; the rest plain |
| (d) jitter | plain, but each lineup's draw multiplies every projection by exp(σZ − σ²/2), with σ = k × the tier's measured miss / its mean projection |
| (e) light | half plain, half L0.1 U0 |

**Jitter's sizes:** the graded slates' miss (MAE of fp_dk against actual, played, projected 5+) over the tier's mean projection:

| Tier | MAE / mean projection | σ at k = 0.5 |
|---|---|---|
| under $5k | 6.09 / 10.6 | 0.29 |
| $5–7k | 7.92 / 19.0 | 0.21 |
| $7k+ | 8.33 / 29.0 | 0.14 |

The sensitivity run uses k = 1, the full measured miss.

**Scoring:** real finish percentile and net $ per entry, as in the Lab. In the fill, our lineups are placed among the real entries with ours left out and ties split. Every difference is paired by slate; the table gives mean ± SE over slates.

### The pool: bank, kept, and the kept pool's variety (14 slates, all graded 100+ contests)

| Recipe | Bank pct | Kept pct | Kept − bank | Distinct kept cores | Cores / kept | Max player exposure in kept |
|---|---|---|---|---|---|---|
| (a) d9 | 35.38 | 42.51 | +7.13 | 207 | 0.46 | 75.6% |
| (b) plain | 43.05 | 45.73 | +2.68 | 168 | 0.37 | 85.5% |
| (c) greencore | 43.51 | 46.06 | +2.54 | 158 | 0.35 | 86.3% |
| (d) jitter, k 0.5 | 39.57 | 43.56 | +4.00 | 208 | 0.46 | 72.7% |
| (e) light | 39.51 | 43.78 | +4.26 | 187 | 0.42 | 80.8% |
| (d) jitter, k 1 (sensitivity) | 31.77 | 37.27 | +5.50 | 288 | 0.64 | 53.4% |

Each recipe against today's d9:

| Recipe − d9 | Kept pct | Kept − bank | Distinct kept cores | Max exposure |
|---|---|---|---|---|
| (b) plain | +3.22 ± 0.84, 12 of 14 | −4.45 ± 1.24, 1 of 14 | −39.7 ± 6.0 | +9.98 ± 2.07 |
| (c) greencore | +3.55 ± 1.10, 11 of 14 | −4.59 ± 1.02 | −48.7 ± 7.5 | +10.72 ± 2.17 |
| (d) jitter, k 0.5 | +1.05 ± 0.86, 12 of 14 | −3.13 ± 0.82 | +0.4 ± 4.4 | −2.83 ± 1.13 |
| (e) light | +1.27 ± 0.45, 11 of 14 | −2.87 ± 0.79 | −19.9 ± 4.2 | +5.21 ± 1.42 |
| (d) jitter, k 1 | −5.23 ± 1.84, 3 of 14 | −1.62 ± 0.81 | +81.1 ± 8.9 | not tabled |

- **The lean cells drag the bank down.** Draw-the-9's bank is 7.7 points of finish percentile below the plain bank.
- **The cut recovers most of it but not all.** d9's kept pool still trails plain's kept pool by 3.2 points.
- **So Draw-the-9's large "kept − bank" is the cut throwing out the lean cells' lineups,** not the bank's variety adding value. It agrees with Lab c, where all 8 cells trail L0 U0.

### The fill: entered contests with standings, entries-weighted within a slate

| Recipe − d9 | All contests, finish pct | All, net $ per entry | Main, finish pct (12 slates) | Flagship, finish pct (13 slates) |
|---|---|---|---|---|
| (b) plain | +2.93 ± 1.14, 10 of 14 | −0.90 ± 1.15 | +2.70 ± 0.96, 9 of 12 | +0.38 ± 3.43 |
| (c) greencore | +2.97 ± 1.82, 9 of 14 | −0.92 ± 1.07 | +1.95 ± 1.22 | +2.99 ± 3.84 |
| (d) jitter, k 0.5 | +4.15 ± 1.91, 10 of 14 | +4.36 ± 5.53 | +1.83 ± 1.27 | +3.25 ± 4.44 |
| (e) light | +0.28 ± 1.39, 8 of 14 | +1.53 ± 3.14 | +1.22 ± 1.44 | +0.81 ± 3.47 |
| (d) jitter, k 1 | −2.21 ± 2.51, 5 of 14 | −1.02 ± 0.69 | −0.78 ± 2.52 | −8.61 ± 6.42 |

- **Spread across the night's entries:** the most-used player's share of entries is 74.3% for d9, 77.8% plain, 80.5% greencore, 67.9% jitter at k 0.5, and 75.7% light. The entries' distinct cores per entry run 22.6 of 42.4, 19.9 of 38.1, 18.9 of 36.5, 23.9 of 44.1, and 21.7 of 40.1.
- **The entry count varies by recipe** (36–44 a night), because the cap of 3 contests per lineup and the night cap bind differently on each pool.

### Head to head against all plain (`pairs.out`)

| Recipe − plain | Kept pct | Distinct kept cores | Max exposure | Fill pct |
|---|---|---|---|---|
| (d) jitter, k 0.5 | −2.17 ± 1.16, 5 of 14 | +40.1 ± 6.2, 14 of 14 | −12.8 ± 1.6 | +1.22 ± 2.01, 7 of 14 |
| (c) greencore | +0.33 ± 0.60 | −9.0 ± 3.1 | +0.74 | +0.04 ± 1.02 |
| (e) light | −1.95 ± 0.60, 3 of 14 | +19.9 ± 4.3 | −4.8 | −2.65 ± 1.45, 4 of 14 |

### Reading

**(b) all plain**
- It beats today's mix on results: the kept pool by +3.22 ± 0.84 (12 of 14) and the fill by +2.93 ± 1.14 (10 of 14). Both clear 2×SE: **PROVEN on results**.
- It fails the operator's goal of variety: −40 distinct cores (−19%) and +10 points of max exposure.

**(d) plain plus honest projection noise, at half the measured miss by tier**
- It keeps Draw-the-9's variety without leaning into our errors: the same core count and lower max exposure.
- It improves the fill: +4.15 ± 1.91, 10 of 14, just over 2×SE.
- It trails all plain on the kept pool (−2.17 ± 1.16) and is level on the fill.
- **It's size-sensitive.** At the full measured miss it is −5.23 on the kept pool, 3 of 14. It is **DIRECTIONAL**, and the setting matters.

**(c) green cores**
- No better than plain on results, with the least variety.
- Out-of-sample greens add nothing (1b), so this is **NOISE** against plain.

**(e) light leverage** sits between d9 and plain on both results and variety: kept +1.27 ± 0.45 against d9, NOISE on the fill.

**Dollars** are NOISE for every recipe. One or two flagship cashes decide each total.

**Answer: variety and results.** Plain gives the results; jitter at about half the measured miss gives Draw-the-9's variety with results at least as good as Draw-the-9's. It's a candidate for the end-of-walkthrough batch, as **DIRECTIONAL**, and its size would need to be fixed before it ships (k 0.5).

## What can't be replayed

- **The operator's ideas and rules:** the replays are rule-free banks. Real nights mix ideas, locks, excludes, STACK, SCANFLOOR and hand groups under Draw-the-9, so "today" here is the rule-free Draw-the-9 mix, not the operator's real bank.
- **Bank size and keep:** replays are 1,500 a recipe, cut to 30%. The real banks were 3,800–20,000, and the cut ran 2,000 nights where the replay runs 1,000.
- **The fill:** the page's qualifier chalk batch, the flagship joint top-1% pick, cross-contest reuse rules beyond 3 a lineup, hand edits and late swap are not replayed.
- **The greens:** see 1. They are partly in-sample, there's no OBPR before 11-20, Questionable decisions aren't logged, and the per-game GREENS form wasn't replayed.
- **Slates:** 11-21 and 11-22 have no build, so they are in 1b only. 11-27 is not graded yet.
- **Inputs:** the gamelogs and the lock-time nights come from ESPN and the mirror and are not committed. `extract.py` and the fetch in `greens_player.py`'s usage note rebuild them.

## Tags for the ledger

| Item | Tag |
|---|---|
| Greens identify players who score more per $1k, on top of salary and projection band | DIRECTIONAL (out of sample +0.65 ± 0.27, 5 of 6) |
| Greens beat our projection | NOISE (out of sample +0.98 ± 1.39, 3 of 6) |
| GREENS rule draw vs plain L0 U0 | NOISE (+2.65 on the fit slates; −0.29 ± 1.25 after) |
| Lab d (new control) | running: 5 of 10, +7.59 ± 6.77 |
| Bank: all plain over Draw-the-9 | PROVEN on results (kept +3.22 ± 0.84, fill +2.93 ± 1.14); fails on variety |
| Bank: plain + projection jitter, k 0.5 | DIRECTIONAL: variety kept, fill +4.15 ± 1.91 (10 of 14); size-sensitive (k 1 negative) |
| Bank: plain + green cores | NOISE against plain |
| Bank: plain + L0.1 U0 | NOISE against plain on the fill; between d9 and plain |

HELD: none of this ships without the operator's go.
