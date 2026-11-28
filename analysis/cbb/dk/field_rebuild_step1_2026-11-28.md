# Field model rebuild, step 1: real field vs sim field (2026-11-28)

Analysis only. The HOLD stands; nothing is built into the page or into `dk_cbb_field.py`.

## Plain-English summary

Our simulated field is too flat and too unique. Real people pile onto the same chalk and the same lineups much more than the sim does.
- **Ownership:** real lineups carry about 35 more points of total ownership than the sim's, a third more chalk players and a much wider spread of ownership totals.
- **Duplication:** in a 1,000-lineup sample, 23% of real lineups have an exact twin, against 5% of the sim's. The most popular player pairs and trios show up in 8–10 points more lineups in the real field.
- **Projection on our numbers:** the sim's lineups score 2.3 points better on our projections, so the sim field is a little too smart. That's the +3.4 construction gap from section 6 again, mostly in mains (+3.3, 14 of 14).
- **Two reasons, both in how the field is built:**
  - It's one field per slate for every contest. Real flagships are the chalkiest, at an ownership total of 264 against 242 in mains.
  - The rake step draws lineups without replacement, so it rules out duplicates by design.
- **The rebuild:** a field per contest type, a sharper ownership curve, and duplicates allowed at the real rate. The held-out test is pre-registered below and not run yet.

## Data and method

- **Script:** `field_rebuild_step1_2026-11-28/fb.py`; output in `fb.out`, rows in `fb_rows.json`.
- **Contests:** every graded contest with standings and a sim field saved at lock (the mirror's `dk_cbb_field.json` before the slate's start, as `dk_eval.py fieldcheck` reads it). That's **75 contests on 16 slates, 11-16 to 11-26**: 22 flagship, 49 main and 4 qualifier contests, typed by `dk_contest_type.py` via `field_lineups.csv`.
- **Real side:** the standings lineups mapped to DK ids, with our own entries removed.
- **Sim side:** the 1,000 sim lineups.
- **Sampling:** both sides are sampled to the same n (the smaller of the real count and 1,000) with a fixed seed, so duplication and combination frequencies are comparable.
- **Ownership:** chalk counts and ownership totals use the contest's real ownership (each player's share of the real lineups). `pown_sum` uses the sim's own projected ownership. Projected points and minutes are our lock-time numbers (the slate at lock in `dk_cbb_morning.json`).
- **Averaging:** each sim − real difference is averaged over a slate's contests, with SE over slates.

## Results by contest type

Sim − real, mean ± SE over slates, then the number of slates where the sim is higher. The full table is in `fb.out`.

| Measure | Flagship (22 contests / 15 slates): real, sim, sim − real | Main (49 / 14) | Qualifier (4 / 3) | All (75 / 16) |
|---|---|---|---|---|
| Ownership total, mean | 264 · 214 · **−50.5 ± 3.7** (0 of 15) | 242 · 218 · **−24.3 ± 3.4** (0 of 14) | 282 · 238 · −40.3 ± 6.8 (0 of 3) | 250 · 218 · **−35.5 ± 3.7** (0 of 16) |
| Ownership total, p10 / p50 / p90 | real 172 / 275 / 338; sim 145 / 214 / 283 | real 148 / 253 / 317; sim 155 / 218 / 279 | real 202 / 291 / 353; sim 166 / 240 / 299 | real 158 / 261 / 325; sim 152 / 218 / 281 |
| Ownership total, SD across lineups | 64.8 · 53.3 · −10.4 ± 1.9 | 64.0 · 48.0 · **−16.4 ± 1.2** (0 of 14) | 61.2 · 53.0 · −9.3 | 64.1 · 49.8 · **−14.9 ± 1.1** (0 of 16) |
| Players 10%+ / 20%+ / 30%+ owned, per lineup | real 6.49 / 5.04 / 3.79; sim −1.03 / −1.10 / −0.94 (all 0 of 15) | real 6.41 / 4.95 / 3.57; sim −0.56 / −0.55 / −0.51 | real 6.91 / 5.60 / 4.49; sim −1.12 / −0.89 / −0.55 | real 6.46 / 5.01 / 3.68; sim **−0.76 / −0.81 / −0.71** (1, 0, 0 of 16) |
| Holds a punt: under 15 projected minutes (% of lineups) | 14.0 · 12.3 · −0.6 ± 2.7 | 18.2 · 13.9 · −4.6 ± 2.5 | 16.7 · 9.6 · −6.8 | 16.9 · 13.2 · −3.4 ± 2.2 (6 of 16) |
| Holds a punt: under $4k (%) | 25.7 · 26.8 · +3.8 ± 5.0 | 31.3 · 35.3 · +3.8 ± 5.1 | 14.9 · 6.6 · −7.5 | 28.7 · 31.3 · +3.2 ± 4.5 (9 of 16) |
| Salary left | $151 · $175 · +$25 ± 10 | $167 · $184 · +$17 ± 4 (12 of 14) | $223 · $178 · −$41 | $166 · $181 · +$14 ± 7 (12 of 16) |
| Team stack 2+ / 3+ (%) | 91.4 / 29.0; sim +1.7 / +0.9 | 95.3 / 35.7; sim +0.5 / −0.7 | 98.5 / 37.8; sim −0.0 / −3.2 | 94.3 / 33.8; sim +1.3 / −0.2 |
| Game stack: 3+ from one game, both teams (%) | 67.9 · 64.9 · −3.3 ± 1.9 | 72.7 · 69.9 · −2.8 ± 1.6 | 90.7 · 84.6 · −4.3 | 72.2 · 69.2 · −2.9 ± 1.5 (6 of 16) |
| **Duplication:** share of lineups with an exact twin in the sample (%) | 12.1 · 2.4 · **−10.7 ± 1.5** (0 of 15) | 28.2 · 5.8 · **−22.5 ± 1.3** (0 of 14) | 11.2 · 1.3 · −7.9 | 22.6 · 4.6 · **−17.4 ± 1.5** (0 of 16) |
| Most common pair: % of lineups | 46.9 · 33.8 · **−12.3 ± 1.8** | 40.9 · 35.9 · −5.4 ± 1.4 | 44.0 · 35.7 · −6.4 | 42.8 · 35.3 · **−8.2 ± 1.4** (2 of 16) |
| Top-5 pairs, mean % | 40.0 · 27.8 · −11.5 ± 1.2 | 35.1 · 30.2 · −5.3 ± 1.1 | 37.9 · 31.7 · −4.7 | 36.7 · 29.5 · −7.8 ± 1.1 (1 of 16) |
| Most common trio: % of lineups | 31.3 · 17.5 · **−13.2 ± 1.9** | 26.5 · 19.4 · −7.7 ± 1.8 | 27.9 · 23.8 · −2.6 | 28.0 · 19.1 · **−9.8 ± 1.6** (1 of 16) |
| Top-5 trios, mean % | 25.4 · 14.6 · −10.5 ± 1.3 | 22.0 · 16.2 · −6.3 ± 1.2 | 25.5 · 18.4 · −6.1 | 23.2 · 15.9 · −8.1 ± 1.2 (1 of 16) |
| Our projected points per lineup | 201.9 · 202.3 · +0.5 ± 0.6 (10 of 15) | 198.6 · 201.9 · **+3.3 ± 0.5** (14 of 14) | 200.2 · 202.9 · +2.8 | 199.6 · 202.1 · **+2.3 ± 0.5** (15 of 16) |
| Sim's projected ownership total (pown) | 213.5 · 218.0 · +5.3 ± 5.0 | 217.1 · 237.2 · +18.7 ± 3.9 (13 of 14) | 237.4 · 249.9 · +14.9 | 217.1 · 232.2 · +14.0 ± 4.0 (14 of 16) |

How to read the last row: on the sim's own ownership numbers, the sim's lineups are chalkier than the real ones, by +14. On real ownership, the real lineups are chalkier, by +35. So the sim isn't too contrarian; it concentrates on our idea of chalk, while real people concentrate on players we under-project. That's the section 3 concentration miss showing up in the field.

## The three biggest construction differences

1. **Not chalky enough, and too narrow.**
   - The real ownership total is higher by 35 overall (50 in flagships, 24 in mains, 0 of 16 slates the other way), with +0.7 to +0.8 more chalk players per lineup at every threshold.
   - The real spread across lineups is wider: SD 64 against 50. Real people stack heavy-chalk builds at the top and a contrarian tail at the bottom, and the sim sits in the middle.
2. **Almost no duplication.**
   - Real: 23% of lineups duplicated (28% in mains). Sim: 5%.
   - The top pair is in 43% of real lineups against 35%, and the top trio in 28% against 19%.
   - The sim's rake draws without replacement, which rules out duplicates by design; the few it has come from identical optimizer solutions.
3. **One field for every contest type, and slightly too optimal.**
   - The sim is one 1,000-lineup field per slate, while real fields differ by type: flagships chalkier and more pair-concentrated, mains more duplicated.
   - On our projections the sim's lineups are 2.3 points better (3.3 in mains, 14 of 14), and they leave $14–25 more salary unspent in flagships and mains.
   - Punts and stacks are close, within noise: team stacks within 2 points, game stacks −3, punts mixed by definition. They aren't the problem.

## Proposed rebuild

All changes are inside `dk_cbb_field.py`'s draw. The lineup generator (the MILP styles) stays as it is, so each change is small and easy to undo.
- **R1. A field per contest type.** Draw the sim's 1,000 lineups from the slate's candidate pool separately for flagship, main and qualifier, each with its own targets below. The page reads the field for a contest's type, falling back to today's single field.
- **R2. A sharper ownership target.**
  - Rake toward own_t ∝ own^γ, renormalised to 800, where own is today's corrected ownership. γ_type is fit on the training slates so the mean ownership total and the top-8 ownership sum match the real fields of that type.
  - It doesn't try to pick the players the field will over-own. Section 3 showed that isn't predictable before lock. It only matches how concentrated the field is.
- **R3. Duplicates at the real rate.**
  - Replace the rake's without-replacement draw with a draw with replacement, with the weights raised to a power (or a fixed copy share) fit per type, so the sampled duplication rate and the top pair and trio frequencies match the training fields at n = 1,000.
  - Ties then split prizes naturally; the tie split stays off until the test passes.
- **R4 (secondary, only if R1–R3 leave a gap).** Add a share of near-optimal lineups (more noise in the build styles) so our projected points per lineup and the salary left match per type. Expect it to be small (+2.3 points), and possibly absorbed by R2.

## Pre-registered held-out test

Written and committed before any candidate field is built or graded. Step 1 runs none of it.

- **Contests:** every graded contest with standings and a sim field saved at lock, from 11-16 through the latest slate graded when the test is run (75 contests on 16 slates today). Contest type by `dk_contest_type.py`.
- **Held-out split:** leave-one-slate-out.
  - For each slate, fit γ_type (R2), the duplication parameter_type (R3) and, if used, the R4 noise share on the other slates' real fields only.
  - Build the candidate fields for the held-out slate from its lock-time inputs, the same `dk_cbb_field.py` inputs and seed 7.
  - Types with fewer than 3 training slates (qualifiers today) reuse the pooled all-type parameters.
- **PREVIOUS:** today's sim field (the mirror's `dk_cbb_field.json` at lock) is graded beside the candidate on the same contests with the same scoring. RULER isn't applicable to the field arm.
- **Primary metric:** the absolute cash-line gap |sim cash line − real cash line|.
  - Scored exactly as `eval.csv`'s `sim_cash` / `field_cash` (dk_eval's sim of the field against the contest's real standings), on contests of 100+ entries as in section 6.
  - Gain = |gap_PREVIOUS| − |gap_candidate|, averaged per slate, with mean ± SE over slates.
- **Secondary metrics:**
  - the absolute top-10% line gap, the same way;
  - the construction gap: |sim − real| on the ownership total, duplication rate, top-pair %, and our projected points per lineup, each as gain over PREVIOUS.
- **Pass rule (rule 5), decided on the pooled contests; per-type results are reported as context:**
  - **PROVEN:** primary gain > 2×SE, ahead on most slates, and no secondary metric worse beyond noise (more than 2×SE).
  - **DIRECTIONAL:** primary gain positive on at least 60–65% of slates (10 of 16 today), the mechanism above, no secondary metric worse beyond noise. It ships as PROVISIONAL, with PREVIOUS logged nightly and a review at 10 slates.
  - **NOISE:** otherwise.
- **Order:** R1+R2+R3 together is the registered candidate. R4 is tested only as an add-on to it, under the same rule. Single-component runs are context, not decisions.
- **What the test can't fix:** the cash-line gap also carries the projection-level part from section 6 (+5.4 ± 5.5, swinging −36 to +31 a night). A better field can't remove it, so the expected gain is bounded by the construction and concentration parts. The test reports the gap with that level part shown separately.
