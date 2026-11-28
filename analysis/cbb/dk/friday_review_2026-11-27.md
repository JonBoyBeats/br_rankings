# DraftKings CBB: the full Friday review (2026-11-27)

The coordinator's request, approved by the operator. **This is analysis and proposals only.** Nothing changes on the
page, in the projections or in the field until the operator approves each proposal.

- **Data:** 18 graded slates, 2026-11-16_156660 to 2026-11-26_157382. 11-27 (157545, 157547) is not graded yet.
- **Rules:** [process.md](process.md).
- **Headlines:** `python3 scripts/dk_eval.py scorecard` ([scorecard.md](scorecard.md)). Each cell is a mean over slates ± SE (slates).
- **Section 5** was redefined by the coordinator after the first draft: it's about the best DFS users, not basketball players.
- **Code:** every other number comes from the scripts in [friday_review_2026-11-27/](friday_review_2026-11-27/), and their printed output is saved beside them.

**How to read the scorecard rules.** Three rules from process.md decide what can ship this week:
- The minutes and per-minute arms are **settling 4 of 7**, and ownership is settling 5 of 7. None of the three can take a change this week except a bug fix (rule 4). I found no clear bug in any of them.
- The fill arm is settling 6 of 7, and it reaches 7 when 11-27 is graded.
- The field, pool, fill and late-swap arms log **no PREVIOUS column** (rule 3). Before any of them can change, it needs one built.

So the proposal list below is short, by design. Most findings go to the watch list, each with its check at 7 slates.

---

## 1. Minutes

**Headline (ROTATION minutes MAE, proj-2026-11-25, settling 4 of 7):**

| | Value |
|---|---|
| Last 7 | 7.50 ± 0.48 (7) |
| Season | 7.11 ± 0.22 (18) |
| LIVE − PREVIOUS | **+0.25 ± 0.13 (4)** |
| LIVE − RULER | **+0.12 ± 0.06 (6)**; 3 of the 6 are backfilled at 0 by construction, and the 3 logged slates read +0.24 ± 0.06 |

The rebuild trails both the previous version and the ruler, by about two SE. Neither gap is past noise at 4 slates.

**Where it loses** (`fr_proj.py`, `fr_proj3.py`; rotation band; LIVE − PREVIOUS per slate):

| Group | Rows | LIVE MAE | LIVE − PREV | LIVE − RULER |
|---|---|---|---|---|
| all | 1,128 | 7.11 ± 0.22 (18) | +0.25 ± 0.13 (4) | +0.24 ± 0.06 (3) |
| played (min > 0) | 1,038 | 5.97 ± 0.24 (18) | +0.30 ± 0.12 (4) | +0.26 ± 0.05 (3) |
| DNP (0 min) | 90 | 21.27 ± 0.68 (16) | −0.09 ± 0.23 (4) | +0.08 ± 0.16 (3) |
| close game (final margin < 10) | 558 | 7.38 ± 0.37 (15) | +0.22 ± 0.14 (4) | +0.29 ± 0.11 (3) |
| mid (10–19) | 383 | 6.65 ± 0.34 (18) | +0.48 ± 0.23 (4) | +0.24 ± 0.15 (3) |
| blowout (20+) | 187 | 7.13 ± 0.70 (9) | −0.43 ± 0.60 (2) | −0.06 ± 0.51 (2) |
| OT game | 85 | 8.76 ± 0.69 (6) | −0.14 ± 0.19 (2) | n/a (1) |
| teammate out at lock (lineup context) | 121 | 7.67 ± 0.61 (10) | +0.10 ± 0.30 (4) | −0.06 ± 0.33 (3) |
| full roster | 1,007 | 7.05 ± 0.21 (18) | +0.28 ± 0.15 (4) | +0.28 ± 0.10 (3) |
| newcomer (no 2025-26 prior) | 161 | 5.59 ± 0.47 (18) | +0.39 ± 0.20 (4) | +0.37 ± 0.09 (3) |
| returner | 967 | 7.26 ± 0.26 (18) | +0.25 ± 0.17 (4) | +0.23 ± 0.08 (3) |
| 3+ games played | 1,041 | 6.19 ± 0.28 (18) | +0.28 ± 0.14 (4) | +0.26 ± 0.08 (3) |
| ≤ 2 games played | 87 | 17.98 ± 0.75 (17) | −0.16 ± 0.14 (4) | −0.19 ± 0.30 (3) |

**Diagnosis.**
- **The rebuild does not lose where it was built to help.** It is level or ahead on:
  - DNPs;
  - blowouts and OT;
  - lineup-context nights (a rotation teammate Out at lock);
  - players with ≤ 2 games.
- **It loses on the ordinary case:** full-roster rotation players with 3+ games, who played in close or mid-margin games. That is most of the rows. The loss is the same size on newcomers and returners. Newcomers look slightly worse, but only 161 rows.
- **Its parts** (`min_parts`, from 11-25, 4 slates), rotation-band MAE relative to `final`:
  - `pre` is +0.22 ± 0.06 and `form` is +0.16 ± 0.09, so the FORM 0.5 blend beats both of its inputs;
  - `qmin` is +0.42 ± 0.11.
  - Over the 4 slates, the signed minutes bias (actual − ours) is −0.01 ± 0.58 for the rotation band and +0.83 ± 0.86 for stars. No level problem.
- **A steepen refit doesn't help.** I rescaled the final minutes around each slate's rotation mean (s from 0.70 to 1.30, fitted on the other slates). Held out, it gains −0.03 ± 0.03 (4): nothing. The fitted s sits at 1.0–1.2, so if anything slightly *steeper*, not flatter.
- **Verdict: noise, or a small spread in the state weights. Not a bug.** Nothing is proposed before 7 slates.

**Watch at 7 slates:**
- Does LIVE − PREV stay positive on the "played, full roster, 3+ games" rows? If it does, the candidate is a re-fit of the state weights and k_ctx on those rows, held out by slate. Steepen and FORM are already shown not to be the lever.

---

## 2. Points per minute

**Headline (STARS points MAE, proj-2026-11-25, settling 4 of 7):**

| | Value |
|---|---|
| Last 7 | 9.96 ± 0.27 (7) |
| Season | 9.63 ± 0.39 (18) |
| LIVE − PREVIOUS | −0.29 ± 0.30 (4) |
| LIVE − RULER | +0.14 ± 0.13 (6) |

The rotation band's points MAE is 8.17 ± 0.16 (18). There the rebuild beats PREVIOUS by −0.14 ± 0.03 (4) and the ruler by −0.23 ± 0.09 (3).

**By group, STARS band** (`fr_proj.py`):

| Group | Rows | LIVE MAE | Bias (actual − ours) | LIVE − PREV | LIVE − RULER |
|---|---|---|---|---|---|
| all | 293 | 9.63 ± 0.39 (18) | −0.49 ± 0.80 (18) | −0.29 ± 0.30 (4) | +0.27 ± 0.27 (3) |
| minutes within 4 of ours | 134 | 8.07 ± 0.75 (18) | −0.83 ± 1.30 | +0.19 ± 0.19 (4) | +0.54 ± 0.30 (3) |
| minutes off by 4+ | 159 | 11.32 ± 0.55 (18) | −1.37 ± 1.58 | −0.59 ± 0.34 (4) | +0.33 ± 0.52 (3) |
| blowout (20+) | 48 | 11.58 ± 0.91 (9) | −3.85 ± 1.47 | +0.49 ± 0.61 (2) | −0.00 ± 1.20 (2) |
| close (< 10) | 141 | 9.65 ± 1.10 (15) | −1.98 ± 1.65 | −0.36 ± 0.26 (4) | +0.19 ± 0.50 (3) |

**The layers** (`ppm_parts`, from 11-25, 4 slates; players projected 10+ who played 10+ minutes; DK points per minute at actual minutes):
- **The full per-minute MAE is 0.24 ± 0.01.**
- **Each layer helps a little.** Dropping it would make the MAE worse:
  - matchup: +0.01 ± 0.00;
  - Vegas: +0.01 ± 0.00;
  - GAME_ADJ: +0.01 ± 0.00.
- **None is misbehaving.** Their ranges are narrow:
  - matchup 0.907–0.997;
  - Vegas 0.910–1.053;
  - GAME_ADJ 0.947–0.990.
  - GAME_ADJ took a single value (0.979) on two of the four slates.
- **The finding: the per-minute level runs high** (`fr_proj2.py`; actual − ours, DK points a minute, players who played 10+):
  - rotation: **−0.07 ± 0.02 (4)**;
  - stars: **−0.09 ± 0.03 (4)**;
  - PREVIOUS (`old_ppm`) was −0.04 ± 0.02.
  - At 30 minutes that's about 2–3 points a player too high. On the same 4 slates the points bias (actual − ours) is −1.10 ± 0.74 for stars, against PREVIOUS's +0.44 ± 0.84, and −1.11 ± 0.54 for rotation, against −0.70 ± 0.58. The headline MAE hides it because the minutes misses dominate.
  - It is consistent across all 4 slates and both bands, at 3–4 SE. But it is 4 slates, and a level offset is exactly what settling is meant to catch.
- **Verdict:** this is not a bug, since no layer is wrong. It's a level, and probably comes from the band prior or the last-season baseline. Nothing is proposed before 7.

**Watch at 7 slates:**
- If the −0.08/min holds, the candidate is a single per-minute level factor fitted on the other slates, judged on the STARS points MAE.
- It also feeds section 6: the field's projected level runs high by about the same amount.

---

## 3. Ownership

**Headline (chalk-band MAE, share off 10+; own-2026-11-24, settling 5 of 7):**

| | Value |
|---|---|
| Last 7 | 11.82 ± 0.88 (7), 46% off 10+ |
| Season | 11.59 ± 0.60 (16), 47% |
| LIVE − PREVIOUS (raw) | **+0.17 ± 0.22 (5)** |
| LIVE − RULER | −0.35 ± 0.27 (6) |

**The correction since it went live.** Here "raw" is the uncorrected own (`own_raw`), and every fit is held out by slate (`fr_own.py`):
- **Since it went live, it has been neutral.** On the 5 slates from 157026, live minus raw is +0.17 ± 0.22. The shipped coefficients applied to raw, without the renormalization, gain +0.03 ± 0.25 there (3 of 5 better).
- **On all 16 slates the shipped coefficients still pass:** chalk MAE 11.61 → 11.18, a gain of +0.43 (2×SE 0.30), better on 13 of 16. The first 9 slates are where they were fitted, so they carry it.
- **Refit on all 16:**
  - c0 +0.65, team −1.03, big +5.6, against the shipped +0.53 / −1.27 / +8.44;
  - on the 5 slates since alone: +1.76 / −0.80 / +1.87.
  - **The big-game term is fading.** On the flagged players, actual − raw ran:
    - +7.5 to +9.9 on 157015, 157033 and 157139;
    - −1.9 to +2.2 on 157024, 157293, 157295 and 157382;
    - +12.7 on 157380.
  - Team concentration holds: negative on 13 of 16 slates.
- **Candidates held out on raw** (version B: fitted on players projected 10%+, scored on the chalk band; 16 slates):

| Candidate | Chalk MAE | Gain (2×SE) | Better on | Off 10+ |
|---|---|---|---|---|
| raw | 11.61 | | | 47.5% |
| team + big (today's form) | 11.27 | +0.34 (0.19) | 13 of 16 | 43.8% |
| team only | 11.41 | +0.20 (0.16) | 11 of 16 | 44.2% |
| big only | 11.47 | +0.15 (0.16) | 11 of 16 | 44.6% |
| team + Q | 11.17 | +0.44 (0.42) | 13 of 16 | 43.7% |
| **team + big + Q** | **11.05** | **+0.57 (0.39)** | **13 of 16** | **43.1%** |

**The 11-26 chalk misses.** Raw / live / real (`fr_own2.py`; the 235-entry contest):

| Player | Raw | Live | Real |
|---|---|---|---|
| Avila | 5.4 | 5.7 | 39.1 |
| Hall | 17.1 | 14.6 | 47.2 |
| Allen | 29.9 | 30.9 | 56.6 |
| West Jr. (157380, early) | 18.6 | 16.4 | 37.4 |

On the main slate:
- Stillwell went 21.9 → 54.9, Ruzic 54.6 → 85.7 and Trimble 49.5 → 69.4.

**What they had in common at lock:**
- None was a big-game flag. None was Questionable.
- They were not all value plays: value rank in tier ran 14, 11 and 1. Salaries ran $4.9k–$8.3k.
- Their teams had 1–3 of our 15%+ players, so the correction pulled Hall *down* by 2.5 points. That is the wrong way.

The common thread isn't a player feature. It's **the whole slate concentrating harder than we project**:
- **Concentration** (`fr_own2.py`; 200+ entry contests): the field's 8 most-owned players summed to more than our raw top 8 by **+21.8 ± 7.1 (16), larger on 12 of 16**.
  - On 11-26 the gap was +61 (early) and +83 (main). From 11-24 on it ran +12 to +83.
- **But not on our chalk:** the real ownership of *our* raw top 8 was −20.4 ± 9.6 below our figure. So we don't just under-concentrate. We concentrate on the wrong players.
- **11-26 had only 1–2 contests a slate,** so its real ownership is noisy (one 8-entry contest; it is left out of the 200+ figures).

**Verdict:**
- **The 11-26 misses are a new pattern.** It isn't teammates or big games: the field concentrated on players we didn't rank as chalk, and our own ownership got flatter. Our raw top-8 sum fell from 323–448 before 11-24 to 222–344 since. A guess, not tested: the rebuilt projection has fewer clear standouts (sections 1–2), and the ownership arm inherits that.
- **Q is the strongest new term,** but it rests on 8 players: 38 player-contests on 5 slates, with real − raw −22.7.
- **Nothing ships this week** (settling 5 of 7).

**At 7 slates (after 11-27 grades):**
- Re-run the table above. If team + big + Q still passes, it is the ownership proposal for next Friday, with `own_raw` as its PREVIOUS (already logged).
- Test a concentration exponent (own^a, a > 1, renormalized) held out. It is the opposite of the 11-23 "flat" candidate.

---

## 4. The qualifier field refit

**Headline (field arm, field-2026-11-24, settling 5 of 7):**

| | Value |
|---|---|
| Cash line, sim − real, last 7 | +11.4 ± 8.1 (5) |
| Cash line, sim − real, season | +7.0 ± 6.0 (13) |
| Top-10% line, last 7 | +13.4 ± 7.2 (5) |
| PREVIOUS / RULER | n/a (not logged) |

**10 of 10 qualifier fields are captured** (`dk_eval.py qualcheck`; 77 user rows; `fr_qual.py`). The real users' lineups are scored on own_sum, our projected ownership summed over the lineup (the same definition `fieldusers` uses). Each is set against the slate's lock-time simulated field, reweighted as dk.html `qualField` does for QUAL_CHALK from 0 to 1. Below, sim − real is the sim's own_sum median minus the real field's.

| QUAL_CHALK | 0.0 | 0.2 (no reweight) | 0.3 | 0.4 | 0.5 | 0.8 (today) | 1.0 |
|---|---|---|---|---|---|---|---|
| sim − real own_sum median, mean of 10 | −23.7 | −11.7 | −2.5 | +10.0 | +25.4 | **+45.3** | +52.2 |

- **Today's 0.8 assumes a field far chalkier than the real qualifiers.** It is +45 own-sum points high, and the sim has 0.38 fewer sub-5% players a lineup than the real users. The real qualifier fields sit at about QUAL_CHALK 0.3: only a little chalkier than the slate's main field.
- **Held out by field** (fit on 9, score the 10th; fitted c* 0.3–0.4 every time): the absolute error of the median falls by **+16.3 ± 8.3 (10), better on 8 of 10**. The pass bar is 2×SE = 16.6.
  - **It misses by 0.3.** Directional only.
- **Thin:** 4–23 users a field (mostly 13-entry satellites), and one lineup each. field_users.csv logs no lineups, so the duplicate rate can't be fitted yet.

**Verdict:** not proposed. It misses the bar narrowly, and the field arm needs a PREVIOUS column first.

**Watch:** re-run `fr_qual.py` at 13+ fields. The refit itself is a one-number change (QUAL_CHALK 0.8 → 0.35), so it can go in the first Friday batch after it passes.

---

## 5. The best DFS users in our contests

**Headline:** no scorecard arm. This is context for the bank, cut and fill settings.

Redefined by the coordinator: "best players" means the best **users**. The data is every graded slate's contests with standings on hand (`fr_users.py`, `fr_users2.py`; outputs beside them):
- 48,884 entries by 3,558 users on 16 slates (84 contests);
- usernames as the public standings show them;
- our own entries labelled "us".

**Finish percentile** is 100 × (entries − those scoring more) / entries. The top 10% and top 1% are by place, and the payout comes from the contest's table (ties not split).

**The basketball players, briefly** (`fr_best.py`, [fr_best.out](friday_review_2026-11-27/fr_best.out)). We'd projected each slate's top 10 values at 18.4 points; they scored 34.0.
- They beat both halves: 29.9 minutes against our 21.9, and 1.15 DK points a minute against our 0.83.
- The field missed them too: 15.7% real ownership against our 16.4%.
- Greens hit 5x at 30.5% against 15.0% for non-greens, the only lock-time signal that separated them.
- We held them at 1.45× the base share in the bank and 1.6× in our entries.

### Who

Users with ≥ 5 slates and ≥ 10 entries (729 users), ranked by mean finish percentile over their slates. The 90% band comes from resampling slates (2,000 draws).

**Read with care:**
- **516 of the 729 have a band that contains 50.** At 5–16 slates, most of the ranking is luck.
- **The ranking doesn't hold held out.** Pick the top 10 on alternate slates and test them on the others: they beat the field by only +7.10 ± 7.11 (8 slates) and +3.21 ± 5.31 (7). Neither is past noise.

**Multi-entry (max 20–150 entries in a contest; 76 users):**

| # | User | Slates | Entries | Mean pct [90% band] | Top 10% | Top 1% | ROI |
|---|---|---|---|---|---|---|---|
| 1 | mrrodgershood12 | 8 | 203 | 76.6 [66.0, 85.9] | 0.325 | 0.261 | +219% |
| 2 | clarkb17 | 12 | 96 | 70.8 [61.1, 79.8] | 0.542 | 0.000 | −46% |
| 3 | mattryan858 | 5 | 120 | 70.3 [53.9, 86.7] | 0.258 | 0.042 | +36% |
| 4 | Johnny_Great | 9 | 365 | 68.4 [59.6, 77.1] | 0.162 | 0.003 | +9% |
| 5 | zachj7 | 13 | 522 | 68.1 [60.5, 76.0] | 0.272 | 0.013 | +41% |
| 6 | bryan34k | 9 | 386 | 68.0 [61.4, 75.0] | 0.249 | 0.010 | +13% |
| 7 | kozy6813 | 9 | 147 | 66.6 [57.8, 74.3] | 0.204 | 0.048 | +187% |
| 8 | 7isaunit | 13 | 356 | 65.9 [53.1, 77.5] | 0.275 | 0.000 | +8% |
| 9 | Greenie4020 | 11 | 64 | 65.5 [55.5, 75.4] | 0.172 | 0.000 | −28% |
| 10 | WaveyJones18 | 10 | 281 | 65.3 [60.1, 70.7] | 0.203 | 0.018 | +25% |
| 53 | **us** | 16 | 711 | 51.3 [45.2, 57.4] | 0.115 | 0.018 | +0% |

**Single-entry** (one entry a contest; 272 users) has the top two of the whole list:
- WriteHook: 11 slates, 76.3 [68.9, 83.8];
- cedarpip: 11 slates, 73.0 [66.3, 79.6].

The next 13 and the "few entries" (2–19) group are in [fr_users.out](friday_review_2026-11-27/fr_users.out).

**ROI and percentile disagree.** clarkb17 is 2nd on percentile but −46% on ROI. atfrost is 14th, at +233%. A steady measure (percentile) and a paying one (ROI) pick different people, and that's the first clue to what follows.

### How they build

Per lineup, the top 10 users by percentile against the field and against us. Each is a per-slate difference from the field **in the same contests**, as a mean ± SE over 16 slates, with the number of slates where it's positive.

| Trait | Top 10 − field | Us − field |
|---|---|---|
| total real ownership (own_sum) | **+62.65 ± 7.06, +16 of 16** | −5.08 ± 5.13, +7 |
| players under 10% | **−1.08 ± 0.09, +0** | +0.03 ± 0.10, +7 |
| players 15%+ (the slate's chalk) | **+1.31 ± 0.12, +16** | −0.22 ± 0.12, +5 |
| duplicate copies of the lineup | +6.31 ± 1.96, +13 | **−1.81 ± 0.24, +0** |
| salary left | −39.03 ± 22.91, +6 | **−72.07 ± 13.68, +2** |
| most players from one game | −0.26 ± 0.07, +3 | +0.22 ± 0.15, +11 |
| most players from one team | −0.22 ± 0.08, +3 | +0.17 ± 0.10, +11 |
| 2+1 game stack | +0.03 ± 0.06, +11 | +0.06 ± 0.07, +10 |
| 3+2 game stack | −0.07 ± 0.01, +0 | +0.02 ± 0.03, +5 |
| punts (ours under 15 min) | −0.12 ± 0.04, +1 | −0.14 ± 0.05, +2 |
| coming off a big game | +0.12 ± 0.13, +8 | −0.03 ± 0.08, +3 |
| the slate's top-10 value players (an outcome) | +0.60 ± 0.14, +13 | −0.01 ± 0.12, +8 |

**Exposure** (users with 20+ entries that slate):
- top-10 multi: max player exposure 1.00, distinct 3-player cores 0.04 per entry (7 user-slates, so thin);
- other multi: 0.86 / 0.43;
- us: 0.73 / 0.54.

**Contests:** the top multi-entry users play mostly main (800+) contests. On the list above, the main share runs 42–97% of entries.

### Consistency

- **Each top user's style is steady across slates.** 8 of the 10 have an SD of 0.2–1.0 sub-10% players over slates. 9 of the 10 have a high own_sum every night (slate means 239–338, SD 30–90, against a field mean of 233).
- **The top users share one trait: chalk.** Their means differ a lot on salary left ($5–$253) and duplication (0–12). They are alike only on ownership: high own_sum, few sub-10% players, almost no 3+2 stacks.
- **mm87505 is the exception:** own_sum 218, 2.4 sub-10% players. A different style that also ranked.

### Us against them

**Where we differ most from the top group:**
- **ownership:** we're slightly *below* the field (−5), where they're +63 above. Only 30 of our 711 entries (4%) sit in their contest's top own-sum quintile, against 20% of the field;
- **chalk:** −0.22 players at 15%+;
- **duplication:** we almost never duplicate (−1.81 against the field);
- **salary:** we leave less than anyone ($88 against the field's $159);
- **stacking:** we stack one game and team a little more.

### Actionable?

**The trait to test is ownership sum.** It holds across the top group, separates it from the field (16 of 16 slates), and the style carries held out: the fit-half top group is +56.56 ± 6.62 above the field on the test half.

**But does it pay?** Entries binned by own-sum quintile within their contest (`fr_users2.py`; per slate, then over 16 slates):

| own_sum quintile | Mean pct | Top 10% | Top 1% | ROI |
|---|---|---|---|---|
| 0 (least owned) | 34.0 ± 2.3 | 0.054 | 0.0077 | −41% ± 21 |
| 1 | 45.4 ± 1.3 | 0.088 | 0.0150 | −12% ± 15 |
| 2 | 53.4 ± 0.7 | 0.110 | 0.0161 | +3% ± 15 |
| 3 | 55.6 ± 1.4 | 0.102 | 0.0116 | −20% ± 12 |
| 4 (most owned) | 63.7 ± 2.2 | 0.167 | 0.0125 | −7% ± 18 |

- **Held out (pick the bin on alternate slates, score it on the others):**
  - **on finish percentile,** the top quintile wins both ways: +10.6 ± 3.6 (6 of 8) and +16.1 ± 2.1 (8 of 8);
  - **on ROI it fails:** the bin picked was −0.23 ± 0.14 (2 of 8) one way and +0.03 ± 0.19 (3 of 8) the other.
- **So the "best users" are mostly chalk players, and a percentile ranking rewards chalk by construction.** A chalky lineup lands mid-to-high in the field more often, but it doesn't cash big more often.
  - The top-1% rate peaks in the middle quintiles (0.016), not at the top.
  - Real ownership is also only known after lock. Ours is the projection of it (section 3).
- **Salary left:** $101–400 left edges out ≤ $100 on percentile held out (+2.9 ± 1.0, 7 of 8; +1.6 ± 1.2, 5 of 8). On ROI it fails (−0.31 ± 0.02, 0 of 8; −0.00 ± 0.13).

**Verdict: nothing actionable passes on what pays.** The one robust separator, high ownership, buys percentile and not ROI. No bank, cut or fill setting is proposed from this section.

**Watch list:**
- **Our lineups are the least chalky in their contests.** 18% of our entries are in the least-owned quintile, which has the worst ROI (−41%), and 4% in the most-owned. A floor on own_sum (keep us out of quintile 0) is the candidate. Test it on ROI held out once 20+ slates are graded.
- **We never duplicate.** That's fine on this evidence: duplication tracks chalk.

## 6. Field model: the high cash line

**Headline:** cash line sim − real +11.4 ± 8.1 (5) over the last 7 and +7.0 ± 6.0 (13) for the season; top-10% line +13.4 / +8.6. No PREVIOUS or RULER is logged.

**Decomposition** (`fr_field.py`; one 100+ entry contest a slate that logs both the sim and the real field; 13 slates). The gap splits into:

| Part | Value |
|---|---|
| **construction:** the sim field's projected mean − the real field's, both on our projections | **+3.4 ± 0.5**, positive on 13 of 13 |
| **level:** the real field's projected mean − its actual mean | +5.4 ± 5.5, swinging −36 to +31 a night |
| **spread:** (sim cash − sim mean) − (real cash − real mean) | 18.3 − 20.1 = −1.8 |
| **total** | +7.0 ± 6.0 |

- **Projection level is the big, noisy part.** On nights where our projections run high on everyone, the sim's line runs high. Its average, +5.4 a lineup, is about 0.7 points a player: the same sign as the rebuild's −1.1 a player in section 2, though these 13 slates are mostly before the rebuild. It is a projection problem the field inherits.
- **Construction is small but certain.** The sim field is built from slightly better lineups (on our numbers) than real people play. The real field is:
  - chalkier: own sum 236 against the sim's 215;
  - punts more: 19.2% of lineups hold a player projected under 15 minutes (field_eval's punt1), against 14.1%;
  - salary is the same (49,840 vs 49,816).
- **Duplication** isn't logged for the sim side (dup_field is blank). It can't be judged.
- **Fix tested:** lower the sim's lines by the other slates' mean construction gap.
  - Held out, the |cash gap| shrinks by +1.11 ± 0.89 (9 of 13 better) and top-10% by +1.36 ± 0.90.
  - That's under 2×SE, so it doesn't pass. A total-gap shift does worse (+0.19 ± 1.96).

**Verdict:** no field change. The field arm's real fix is upstream:
- the per-minute level (section 2);
- the ownership concentration (section 3: the real field is chalkier).

The field also needs a PREVIOUS column before any change.

**Watch:** log the sim field's projected mean and its dup rate per contest, so the decomposition runs nightly.

---

## 7. Bank and draw

**Headline:** no scorecard arm. This is the Lab (`dk_eval.py lab`, [lab.json](lab.json)). Each experiment is planned for 10 slates. To pass: ahead on 7+ AND the pooled difference above 2× noise.

**c. Draw the 9: each cell against L0 U0** (6 of 10 counted; real finish percentile, cell − L0U0):

| Cell | Diff | Noise | Ahead / behind |
|---|---|---|---|
| L0 U1 | −0.54 | 0.82 | 1 / 5 |
| L0 U2 | −2.07 | 2.09 | 3 / 3 |
| L0.1 U0 | −0.04 | 1.54 | 3 / 3 |
| L0.1 U1 | −1.47 | 1.61 | 2 / 4 |
| L0.1 U2 | −3.06 | 2.92 | 2 / 4 |
| L0.2 U0 | −1.16 | 3.30 | 3 / 3 |
| L0.2 U1 | −2.22 | 2.98 | 2 / 4 |
| L0.2 U2 | −3.61 | 2.16 | 1 / 5 |

- **Every cell's mean is behind L0 U0.**
- **Five cells can no longer pass,** because they're already behind on 4+ of 10: L0 U1, L0.1 U1, L0.1 U2, L0.2 U1 and L0.2 U2.
- **The worst are the strongest lean cells.** L0.2 U2 is −3.61 and L0.1 U2 is −3.06. More leverage plus more unders reads worse.
- **No cell is significantly behind either.** The verdict waits for 10.

**d. Greens against hand groups**, both tag forms counted ("GREENS <game>" and the GREEN / green 3/4/5 ideas; amended 2026-11-27, before any counted slate):
- **3 slates counted, +4.73 ± 5.95; ahead 2, behind 1; top-10% rate +0.085.**
  - 157024: +16.19 (GREENS <game>);
  - 157293: +1.75;
  - 157295: −3.76 (GREEN).
- 11-26 (157380, 157382) had green 3/4/5 batches but no hand-group control, so they can't count. 11-27 has the same shape.
- **Lab d will keep losing slates to this.** It needs at least one hand group ("at least N of ...") drawn on a night to count.

**The green batches each night** (`fr_green.py`; kept lineups' mean real finish percentile; one representative contest, all are listed in the output):

| Slate | All kept | Green group(s) | Other hand / base | Variants |
|---|---|---|---|---|
| 11-24 157024 | 67.6 | GREENS <game> **81.5** | 65.5 | 67.3 |
| 11-25 157293 | 40.9 | GREEN 42.0 | 40.2 | 42.0 |
| 11-25 157295 | 47.0 | GREEN 44.5 | 47.8 | 47.2 |
| 11-26 157380 | 40.6 | GREEN 3 39.1 · GREEN 4 40.8 · **GREEN 5 39.7** | 39.2 | 43.2 |
| 11-26 157382 | 53.8 | green 3 50.5 · green 4 59.9 · **green 5 69.7** | 40.8 | 48.6 |

**GREEN 5** existed on two graded nights:
- 11-26 early: 39.7, against 40.6 for all kept (−0.9);
- 11-26 main: 69.7, against 53.8 (+15.9). On the main it was also the best fill subset ($100.76 a random fill against $60.66 for all kept).
- 11-27 main (157547) has green 3/4/5 again, and grades tomorrow.
- Two nights is colour, not evidence.

**Verdict:** no change. Lab c and d keep running to 10.

---

## 8. Cut

**Headline (pool: kept − whole bank, mean real finish percentile; cut-2026-11-20, settled):** +4.4 ± 2.8 (7) over the last 7 and +5.7 ± 1.7 (14) for the season. No PREVIOUS is logged.

**Keep size and merit** (`fr_cut.py`; 11 builds that store the board's sim values, 100+ entry contests). The board's own ranking of the kept pool carries real signal, in a clean gradient:

| Kept lineups, by board sim value | − all kept (finish pct) | Positive on |
|---|---|---|
| top 10% | +2.63 ± 1.45 | 7 of 11 |
| top 25% | +1.69 ± 0.99 | 8 of 11 |
| top 50% | +1.08 ± 0.60 | 8 of 11 |
| top 75% | +0.59 ± 0.31 | 8 of 11 |

- None passes 2×SE. The closest is top 75%, at +0.59 against 0.62.
- So a tighter keep size (or a higher merit floor) points the right way but isn't proven. Kept − bank on these 11 builds is +5.65 ± 2.10 (positive on 9).
- **Rounds:** not tested here. Variants ran one round on every build since 11-24 (Lab e).

**Variants** (Lab e, 6 of 10):
- They trail their own parents by **−4.22 ± 1.15, behind on 6 of 6.** They can't reach 7 of 10 ahead, so Lab e will end as a fail.
- But on the pool headline they're neutral (`fr_var.py`). Kept with variants minus kept without, on the same nights, is **+0.22 ± 0.23 (11), positive on 7.** Variants lose to the parents they copy, but beat the rest of the kept pool.
  - So retiring them would *lower* the pool headline slightly, and fails the pass bar.
- What hurts is where they land. They fill 25–67% of the top tenth, the fill's candidate list (Lab e per night), and so crowd out parents.

**Verdict:** no cut change.
- **Watch:** variants' share of the top tenth (the operator's working rule is to stop past about a quarter), and keep size at 20+ builds.
- The pool arm also needs its PREVIOUS column. The cheapest one is "kept without variants", which `fr_var.py` already computes.

---

## 9. Fill

**Headline (entered − random fills, fill-2026-11-24, settling 6 of 7):** +$21.77 ± 30.60 (7) over the last 7, at the 54th percentile; +$24.93 ± 17.18 (14) for the season, at the 60th. No PREVIOUS is logged.

**By contest type** (`fr_fill.py`; the fill's portfolios against 1,000 random fills from the kept pool, per contest, summed per slate; 68 contests on 14 slates).
- Flagship: "Pull Up Jumper", or 100–800 entries.
- Main: 800+ entries.
- Qualifier / small: qualifier, satellite or under 100 entries.

| Type | Contests | Entered − random, mean $ | Entered − random, median $ | Entered's percentile among random fills | Finish pct, entered − random |
|---|---|---|---|---|---|
| all | 68 | +12.51 ± 18.18 (14) | +54.78 ± 24.54 | 51 | +1.99 ± 3.36 |
| **flagship** | 31 | **−18.70 ± 8.17 (14)** | **+8.36 ± 3.23** | 54 | +4.88 ± 3.97 |
| main | 31 | +9.50 ± 11.73 (12) | +17.16 ± 12.26 | 46 | +3.55 ± 1.84 |
| qualifier / small | 6 | +53.82 ± 40.49 (6) | +74.00 ± 46.80 | 61 | −3.03 ± 14.33 |

**The mean-vs-median split is a flagship effect.** It comes from the joint top-1% fill (`DKSim.pickJoint`, from 11-24):
- Since 11-24 our flagship entries trail random kept fills by **−$33.85 ± 10.61 (6), behind on 6 of 6**. Before, it was −$7.34 ± 10.65 (8).
- They still beat them on the median (+$10.25 ± 5.15) and on finish percentile.
- So the joint fill buys a better typical finish and gives up the rare big cash that random fills catch. In main contests since 11-24 it's −$9.52 ± 3.88 (4), the same sign but smaller.

**Softened fills against today's, same nights** (random draws from the board's top 10% / 25% / 50% of the kept pool):

| Flagship, from 11-24 (6 slates) | Value |
|---|---|
| Top-half random − entered, mean $ | **+$35.76 ± 14.93 (6), ahead on 6 of 6** |
| Top-half random − entered, median $ | −$2.50 ± 6.92 |
| All 9 slates with board values | +$34.84 ± 14.59, ahead on 8 of 9 |
| Top 25% / top 10%, all 9 slates | +$39.48 ± 18.25 / +$35.13 ± 18.25 |

- **Main and qualifier:** none beats today's fill beyond noise.
  - Main, top-half: +$1.89 ± 8.82 (7).
  - Qualifier: the softened fills are worse, −$67 to −$71 ± about $49 (5 slates). Not beyond noise, but no case for softening there.
- **Ownership-weighted random:** not run. Without the field sim I had no clean definition. Left for the next round.

**Variants in the fill:** Lab e's "vs rest of top tenth" arm is −3.17 ± 2.75 (2 ahead, 4 behind). Variants are behind their parents on 6 of 6 (section 8). Retiring them doesn't pass on the pool headline, so they aren't proposed for retirement.

**Verdict:** this is the one change in the review that clears the bar on its own arm's headline:
- **mean dollars, held out by slate:** the comparison is fit-free, with the same nights, contests and kept pool. Top half was the coordinator's named variant, so it wasn't picked after the fact.
- It is proposal 1 below, conditional on the fill arm settling (11-27 grades) and a PREVIOUS column.

---

## 10. Late swap

**Headline (in − out, DK points; swap-2026-11-24, settling 6 of 7):** n/a. No swap has been graded: the scorecard's swap arm has no rows.

**Calibration** (`python3 scripts/dk_lateswap_calib.py --mirror ../br-adp-mirror`, with all six of 11-24 to 11-26 added: 15 nights; full tables in [lateswap_calibration_2026-11-27.md](lateswap_calibration_2026-11-27.md)). The script's boilerplate line "2026-11-24 is not in yet" is stale: 157024 and 157026 are in.

- **Expected payout:** at each night's first break, our entries' stated expected payout sums to **$2,228 against $1,064 paid (2.1x; fees $874).** The 11-24 calibration, on 11 nights, read about 1.5x. The field sample scored the same way states $11,511 against $10,435 (1.10x), so the board itself isn't inflating payouts.
- **Top 1%:** our entries stated at 5–50% (458 entry-breaks, mean 10.7%) finished top 1% 4.8% of the time. The field sample's (mean 12.3%) did so 9.5% of the time.
- **Cash:**
  - Stated 95%+ holds: 132 entry-breaks at a mean 98.7% cashed 91.7%.
  - From 20% to 95% it runs high. Our entries were stated at 49.7% and cashed 34.5% (1,599 entry-breaks), against the field sample's 40.7% stated and 36.9% cashed.
- **The cause is bias, not width:**
  - Each entry's realized miss is 0.93x the simulated spread for ours and 1.02x for the field.
  - Our entries finish **7.5 points under their simulated mean** (mean percentile 0.409), against −1.4 for the field. The 11-24 calibration read 5.7, and the 11-24 selection-haircut study read 2.5.
  - It's the same over-projection as section 2's per-minute level, concentrated on the players our lineups are built from.
- **Variance fix (x1.25 on every draw):** better held out on only 9 of 15 nights, and first-break stated payout is still $1,913 against $1,064. Not worth it.
- **Graded swaps:** none. The scorecard's late-swap arm still has no rows.

**Verdict: no late-swap change.**
- Read our stated payout and top 1% as about 2x too high, and the 20–95% cash figures as about 15 points high.
- The candidate is a haircut on our own entries' simulated points, about the 7.5-point mean miss, fitted held out by night. It needs the arm's PREVIOUS column (today's stated numbers, logged beside it).
- The per-minute level fix (section 2), if it passes at 7 slates, should shrink this gap on its own. Re-run the calibration after it.

---

## 11. Results (context only; read over 20+ nights)

**Headline:** net $ (ROI). Last 7: +$2.62 ± 60.62 (7), +9%. Season: −$0.95 ± 27.03 (16), −2%.

The owner's real entries (eval.csv, who = mine; 16 slates):
- **Total: fees $1,081.35, back $1,066.20, net −$15.15, ROI −1.4%.**

| By contest type | Fees | Back | Net | ROI | Entries | Slates |
|---|---|---|---|---|---|---|
| flagship | $622.35 | $230.55 | −$391.80 | −63.0% | 156 | 16 |
| main | $261.00 | $391.65 | +$130.65 | +50.1% | 576 | 13 |
| qualifier / small | $198.00 | $444.00 | +$246.00 | +124.2% | 18 | 9 |

| By slate type | Fees | Back | Net | ROI | Slates |
|---|---|---|---|---|---|
| early (two-slate days) | $379.20 | $455.65 | +$76.45 | +20.2% | 5 |
| main (two-slate days) | $408.00 | $463.55 | +$55.55 | +13.6% | 5 |
| single-slate days (11-16 to 11-23) | $294.15 | $147.00 | −$147.15 | −50.0% | 6 |

**Context, not a pass bar:**
- The flagships are 58% of fees and the whole of the loss. That fits section 9 (flagship entries trail random fills on mean $), but at 16 nights a single top-1% finish would flip it.
- The early/main split is level. The single-slate warm-up days carry the loss.

---

## The proposal list

At most one per arm, ranked by expected impact. None ships without the operator's yes, and each first goes into
[ideas.md](ideas.md) with its arm, test plan, pass bar and PREVIOUS column (process.md rule 1).

**1. Fill (flagship): enter from the board's top half at random instead of the joint top-1% pick.**
- **Evidence (section 9, same nights):**
  - since the joint fill (11-24, 6 slates), top-half random beats our flagship entries by **+$35.76 ± 14.93, ahead on 6 of 6**;
  - over all 9 slates with board values, +$34.84 ± 14.59, ahead on 8 of 9.
  - Our flagship entries trail plain random kept fills by −$33.85 ± 10.61 (0 of 6 ahead).
- **Against previous and ruler:** the fill arm logs neither yet. The pair here is today's joint pick against the softened pick on the same nights and contests.
- **Other arms:** the fill is the last step, so nothing upstream moves.
- **Risk:**
  - Mean dollars are heavy-tailed. The joint pick still wins on the median (+$2.50 a slate) and on finish percentile.
  - 6 slates.
  - The in-sim top-1% coverage the joint fill maximizes would fall.
- **Exact change:**
  - in dk.html, the flagship profile's fill becomes: draw the contest's entries uniformly from the top 50% of the kept pool by `cut_state.board.values`, with the flagship's min-unique setting unchanged;
  - main and qualifier unchanged;
  - log the joint pick's lineups beside it every night as the fill arm's PREVIOUS (new `fill_prev` in the build and `fill_eval.csv`) for 7 slates.
- **When:** after 11-27 grades (the arm reaches settled 7 of 7), and only if the 7-slate number still clears 2×SE. The PREVIOUS column is built first.

**2. Ownership: add the Questionable term to the correction (team + big + Q, refit on raw).** *Ready next Friday, not this one.*
- **Evidence (section 3), held out on raw, 16 slates:**
  - chalk MAE 11.61 → 11.05, gain +0.57 (2×SE 0.39), better on 13 of 16, off 10+ 47.5% → 43.1%;
  - against today's form (team + big): 0.22 better.
  - PREVIOUS (`own_raw`) is already logged; ruler `own_ruler`.
- **Risk:** the Q term rests on 8 players (38 player-contests, 5 slates). The big-game term is fading on recent slates. It doesn't address the 11-26 concentration miss.
- **Exact change:** in battle-royale-research `dk_cbb_field.py`, the own fix becomes c0 + b_team × teammates ≥ 15% + b_big × big + b_q × Questionable, for players 10%+, refit on raw over all graded slates, then renormalized to 800.
- **When:** blocked by rule 4 (settling 5 of 7). Re-run at 7 slates. Ship next Friday only if it still passes.

**Other arms (no proposal this week):**
- **Minutes and per-minute:** settling 4 of 7, and no bug. The per-minute level (−0.08/min) is on the watch list.
- **Field and qualifier:** the refit misses by 0.3 against 2×SE, and the field has no PREVIOUS column.
- **Pool / cut, variants, keep size:** nothing passes. Retiring variants would lower the pool headline.
- **Late swap:** no graded swaps. The 15-night calibration reads our stated payout 2.1x high, from our entries finishing 7.5 points under their simulated mean. A haircut on our entries is the candidate, held out by night, once a PREVIOUS column is logged (watch list).

## The watch list

| Item | Arm | Now | Check at |
|---|---|---|---|
| Our lineups sit low on ownership sum (18% in the least-owned quintile, ROI −41% ± 21) | bank / cut | users study, section 5 | 20+ slates: an own_sum floor, on ROI held out |
| Rebuild trails on "played, full roster, 3+ games" rows | minutes | LIVE − PREV +0.30 ± 0.12 (4); steepen refit no gain | 7 slates: state weights / k_ctx refit on those rows, held out |
| Per-minute level runs high | per-minute | −0.07 / −0.09 DK pts a minute (rotation / stars), 4 slates | 7 slates: one level factor held out, on STARS MAE |
| Field concentrates harder, on players we don't rank as chalk | ownership | real top 8 +21.8 ± 7.1 over ours (12 of 16); +61 / +83 on 11-26 | 7 slates: a concentration exponent (own^a, a > 1) held out |
| Q term in the ownership correction | ownership | proposal 2, 8 players | 7 slates |
| Qualifier field refit QUAL_CHALK 0.8 → ~0.35 | field | +16.3 ± 8.3 vs bar 16.6 (8 of 10) | 13+ qualifier fields |
| Sim field construction gap | field | +3.4 ± 0.5 (13 of 13); shift fix +1.11 ± 0.89 | log sim projected mean and dup rate nightly; build the field PREVIOUS |
| Keep size by board value | pool | top 75% − all +0.59 ± 0.31 (bar 0.62) | 20 builds |
| Variants crowding the top tenth | pool / fill | 25–67% of top tenth; Lab e −4.22 ± 1.15 (0 of 6) | Lab e's 10th slate; share cap at a quarter |
| Draw the 9 lean cells | bank | all 8 behind L0U0; 5 can't pass | Lab c's 10th slate |
| Lab d (greens) can't count green-only nights | bank | 3 slates, +4.73 ± 5.95 | needs a hand group drawn on green nights |
| GREEN 5 group | bank | 2 nights: −0.9 and +15.9 vs all kept | every night; 157547 grades tomorrow |
| Late-swap stated payout high | late swap | 2.1x high on 15 nights; our entries 7.5 pts under their sim mean | haircut fitted held out by night; re-run after any per-minute level fix |
| PREVIOUS columns for field, pool, fill, late swap | process | none logged | before each arm's next change |

---

## Tier tags (added 2026-11-28)

These tags apply the tiered bar now in [process.md](process.md) (rule 5) to this review's proposal and watch lists.
The review above is unchanged. **The operator's hold stands:** nothing ships without the operator's go.

**Proposals:**

| Item | Tag | Why |
|---|---|---|
| 1. Fill (flagship): top-half random instead of the joint pick | **PROVEN** | +$35.76 ± 14.93, ahead 6 of 6 (8 of 9 over all slates with board values). It still waits for the fill arm to settle and for a PREVIOUS column. |
| 2. Ownership: add the Questionable term | **PROVEN** | Held out on raw: +0.57 (2×SE 0.39), 13 of 16. It still waits for the ownership arm to settle (5 of 7) and rests on 8 players. |

**Watch list:**

| Item | Tag | Why |
|---|---|---|
| Rebuild trails on "played, full roster, 3+ games" rows | NOISE | The one candidate tested (steepen refit) gained −0.03 ± 0.03. No candidate has a direction yet. |
| Per-minute level runs high | DIRECTIONAL (finding) | −0.07 / −0.09 a minute on 4 of 4 slates, and the mechanism is plausible (band prior or baseline level). The level factor itself isn't tested yet, and the arm is settling. |
| Field concentrates harder, on players we don't rank as chalk | DIRECTIONAL (finding) | 12 of 16 slates. The concentration exponent isn't tested yet. |
| Q term in the ownership correction | PROVEN | See proposal 2. |
| Qualifier refit QUAL_CHALK 0.8 → ~0.35 | DIRECTIONAL | Better on 8 of 10 held out, +16.3 against a bar of 16.6. A one-number change, cheap to undo, with a clear mechanism (real qualifiers are less chalky than assumed). The field arm needs PREVIOUS first. |
| Sim field construction gap | DIRECTIONAL | The shift fix was better on 9 of 13 (69%), +1.11 ± 0.89. Small and cheap. |
| Keep size by board value (top 75% of kept) | DIRECTIONAL | Positive on 8 of 11 (73%), +0.59 ± 0.31. The mechanism is the board's own gradient. |
| Retire variants | NOISE | On the pool headline, keeping variants is +0.22 ± 0.23 (7 of 11). Retiring them points the wrong way. |
| Draw the 9 lean cells | DIRECTIONAL to drop L0 U1 and L0.2 U2 (each behind L0 U0 on 5 of 6); NOISE for the other six cells (3–4 of 6 behind) | |
| Lab d (greens vs hand groups) | NOISE | Only 3 slates, ahead on 2. Too few. |
| GREEN 5 group | NOISE | 2 nights, 1 ahead. |
| Late-swap stated payout high | DIRECTIONAL (finding) | Our entries are 2.1x high on 15 nights. The haircut fix isn't tested yet. |
| Our lineups low on ownership sum (users study) | NOISE | The own-sum bins fail on ROI held out. |
| PREVIOUS columns for field, pool, fill and late swap | n/a | A process item, not a finding. |

---

## Correction 2026-11-28: unified contest types

The review's by-type figures used a by-size split. It sometimes counted as a flagship any contest under 800 entries, and sometimes any contest with 100–799 entries, wherever the contest name didn't say otherwise. That split called 17 of the 84 contests flagships that the DK page treats as mains: 20-max And-One, Quarter Jukebox and Dime Time with 118–713 entries. It also called one Pull Up Jumper (78 entries) a qualifier.

Every type is now the page's own profile, defined once in `scripts/dk_contest_type.py` (a copy of dk.html `profileAuto`):
- flagship: Pull Up Jumper, or 100–799 entries;
- main: And-One, Quarter Jukebox or Dime Time, or 800+ entries;
- qualifier: qualifier or satellite, or under 100 entries.

Re-cut by `fr_fill_recut.py`, `fr_results_recut.py`, `fr_users.py` (output `fr_users_recut.out`), `ownership_tiered_2026-11-28/ot_recut.out` and `own_uncertainty_sim_2026-11-28/ous_recut.out`. Under the old labels each script reproduces the figures above exactly, so the changes below are the re-label alone. The earlier text is left as written.

**Section 9, fill by contest type** (entered − random kept fills, mean $ per slate):

| | Before (by size) | After (page profile) |
|---|---|---|
| Flagship, all slates | −$18.70 ± 8.17 (14), 31 contests | −$20.64 ± 8.28 (13), 20 contests |
| **Flagship since 11-24: entered − random** | **−$33.85 ± 10.61 (6), ahead 0 of 6** | **−$33.36 ± 10.24 (6), ahead 0 of 6** |
| Flagship since 11-24: median $ | +$10.25 ± 5.15 | +$10.00 ± 5.00 |
| **Proposal 1: top-half random − entered, flagship since 11-24** | **+$35.76 ± 14.93 (6), ahead 6 of 6** | **+$35.22 ± 14.61 (6), ahead 6 of 6** |
| **Proposal 1: same, all slates with board values** | **+$34.84 ± 14.59 (9), ahead 8 of 9** | **+$35.38 ± 14.10 (9), ahead 8 of 9** |
| Main, all slates | +$9.50 ± 11.73 (12), 31 contests | +$9.98 ± 11.60 (12), 43 contests |
| Main since 11-24 | −$9.52 ± 3.88 (4) | −$10.27 ± 4.24 (4) |
| Main, top-half random − entered | +$1.89 ± 8.82 (7) | +$1.19 ± 8.65 (7) |
| Qualifier / small | +$53.82 ± 40.49 (6), 6 contests | +$64.74 ± 47.76 (5), 5 contests |

**Section 11, our results by contest type** (slate types are unchanged):

| | Before: fees / net / ROI / entries / slates | After |
|---|---|---|
| flagship | $622.35 / −$391.80 / −63.0% / 156 / 16 | $600.00 / −$405.00 / **−67.5%** / 46 / 15 |
| main | $261.00 / +$130.65 / +50.1% / 576 / 13 | $301.35 / +$125.85 / **+41.8%** / 690 / 14 |
| qualifier / small | $198.00 / +$246.00 / +124.2% / 18 / 9 | $180.00 / +$264.00 / **+146.7%** / 14 / 8 |

True flagships are 55% of fees (was 58%) and still the whole loss. Our flagship play is 46 entries at $5–15, so one big cash would still flip it.

**Section 5, the users' contest mix:**
- The re-label moves only the mix columns. Every ranking, band and construction statistic is unchanged.
- The users' tables also moved by 0.1–0.3 on own-sum, because the night records were updated after the review. That isn't from the re-label.
- The top 15 multi-entry users' main share is now **57–100% of entries, median 94%** (was 42–97%, median 82%).
- Our own mix is now 45 flagship, 652 main and 14 qualifier entries (was 150 / 543 / 18).

**Tiered-ownership test (B and C, by contest type):** the moves are within ±0.12 $ per lineup and ±0.01 finish percentile on every row. On true flagships, B (today's ownership) against the board's top half is +$0.26 ± $0.56 (4 of 9), and the finish percentile is +0.10 ± 0.40 (4 of 9). Still NOISE.

**Ownership-uncertainty study (f0c040c):**
- Its grade (`ous.py`) used the by-size split. `ous.js` already picked with the page's flagship rule.
- At the measured size (×1), main B − A is +1.73 ± 0.74 finish pct, ahead on 9 of 12 (was +1.78 ± 0.81, 9 of 12).
- Flagship B − A is −4.07 ± 3.61, 6 of 13 (was −2.82 ± 3.28, 8 of 14).
- The main result is still positive at every size: 6–12 of 12 slates ahead (was 8–10).

**Verdict:**
- **Proposal 1 still clears its bar on true flagships.** It's +$35.22 ± 14.61 since 11-24 (2×SE = 29.22), ahead on 6 of 6, and +$35.38 ± 14.10 on all 9 slates with board values, ahead on 8 of 9. It stays PROVEN and HELD, as before.
- **No rule-5 tag changes.** Entered vs random kept fills on flagships stays clearly negative since 11-24. The users' findings, the tiered test (NOISE) and the uncertainty study (overall NOISE, mains DIRECTIONAL, flagships NOISE) keep their tags. The changes are in the by-type sizes, all inside the existing intervals.

## Addendum 2026-11-28: sections 7 and 8, operator decisions

The operator agreed these conclusions on 2026-11-28. The HOLD stands: everything below is recorded for the
end-of-walkthrough batch, and nothing ships until the operator gives the go. Numbers are quoted from the commits
named; the S8 re-cut and proposal 1 check were run for this addendum
([fr_cut_recut.py](friday_review_2026-11-27/fr_cut_recut.py) → `.out`,
[fr_p1_recut.py](friday_review_2026-11-27/fr_p1_recut.py) → `.out`).

### Section 7: bank and draw (decisions)

| Decision | Tier | Evidence |
|---|---|---|
| Drop the Draw-the-9 lean cells | batch, near-PROVEN | f0c012b: the lean cells pull the bank 7.7 pts below plain draws; all-plain beats today's D9 mix on the kept pool +3.22 ± 0.84 (12 of 14 builds) and on the fill +2.93 ± 1.14 (10 of 14) |
| Bank draw = plain + projection jitter at k 0.5 (half the measured miss, wider below $7k) | batch, PROVISIONAL; review at 10 builds; D9 logged as PREVIOUS | f0c012b: kept +1.05 ± 0.86 (12 of 14), fill +4.15 ± 1.91 (10 of 14), distinct cores +0.4, max exposure −2.8 pp; the only recipe with variety AND results. Size-sensitive: at the full measured miss it is −5.23 ± 1.84 on the kept pool (3 of 14) |
| All-plain as the fallback | PROVEN on results | as above; it loses variety (distinct cores −19%, max exposure +10 pp) |
| No greens rule | — | f0c012b: GREENS-rule draws vs plain flip out of sample (last 6 slates −0.29 ± 1.25, 3 of 6), NOISE. The green-core shadow (69e2358) decides instead, at 7 of 10 counted main slates with $ AND finish pct ahead; pre-registration (cc44bc8) green top-5 cores +11.18 ± 3.42 finish pct on mains (6 of 7), $ flat, and the restricted picks fill only 276 of 429 main entries |

### Section 8: cut (decisions)

| Decision | Tier | Evidence |
|---|---|---|
| No cut change | — | no cut setting passed held out |
| Keep size ships through fill proposal 1, not as its own rule | — | same lever (draw from the board's top half); counting it twice would double-count one effect |
| Cap variants at about 25% of the fill's candidate list | batch, DIRECTIONAL | variants trail their parents −4.22 ± 1.15 (0 of 6) but are neutral on the pool headline (fr_var.out: with minus without variants +0.22 ± 0.23, 11 slates, positive on 7); they are over-represented at the top of the board (below) |
| Pool arm PREVIOUS column = "kept without variants" | decision recorded | fr_var.py already computes it. Not built into the scorecard here: it needs the build's tags and every contest's standings, so it is not a trivial logging-only column; it goes in with the variants cap |

### S8 re-cut: keep-size gradient by unified contest type

Kept lineups ranked by the board's sim value; top share minus all kept, real finish percentile, mean over each
slate's contests of that type, then mean ± SE over slates. Contest types are `scripts/dk_contest_type.py`; every
contest with standings on hand is used (the review's fr_cut.py used 100+ entry contests only, reproduced exactly in
the first block of the .out). Builds: 11-19 to 11-26, 11 builds. Excluded: 11-16, 11-17, 11-18 (no board values),
**11-27 157547 (not graded: no night record and no standings yet)**. Tags by rule 5 (PROVEN = gain > 2×SE and ahead
on most slates; DIRECTIONAL = right direction on about 60%+).

| Type | Band | Top − all kept (finish pct) | Positive | 2×SE | Tag |
|---|---|---|---|---|---|
| Flagship (11 slates) | top 10% | +2.64 ± 1.48 | 7 of 11 | 2.96 | DIRECTIONAL |
| | top 25% | +1.67 ± 1.01 | 8 of 11 | 2.01 | DIRECTIONAL |
| | top 50% | +1.08 ± 0.61 | 8 of 11 | 1.21 | DIRECTIONAL |
| | top 75% | +0.59 ± 0.31 | 8 of 11 | 0.62 | DIRECTIONAL |
| Main (9 slates) | top 10% | +3.43 ± 1.63 | 7 of 9 | 3.27 | PROVEN by the letter (margin 0.16, one of four bands looked at) → treated as DIRECTIONAL |
| | top 25% | +2.05 ± 1.18 | 7 of 9 | 2.35 | DIRECTIONAL |
| | top 50% | +1.31 ± 0.71 | 7 of 9 | 1.43 | DIRECTIONAL |
| | top 75% | +0.62 ± 0.38 | 6 of 9 | 0.75 | DIRECTIONAL |
| Qualifier (6 slates) | top 10% | −0.79 ± 1.15 | 2 of 6 | 2.30 | NOISE |
| | top 25% | −0.44 ± 0.86 | 2 of 6 | 1.72 | NOISE |
| | top 50% | −0.27 ± 0.58 | 2 of 6 | 1.16 | NOISE |
| | top 75% | +0.04 ± 0.36 | 4 of 6 | 0.72 | NOISE (flat) |

Variants' share of the board's top tenth (mean over slates): flagship 29.8% (all kept 13.6%), main 23.3% (11.6%),
qualifier 37.8% (16.6%). Variants roughly double their share at the top of the board in every type.

**Should proposal 1 cover mains?** On finish percentile the gradient is as strong on mains as on flagships (top 50%
+1.31 ± 0.71, 7 of 9, DIRECTIONAL), but on dollars it does not pass on mains: top-half random − entered +10.91 ±
7.67 since 11-24 (3 of 4 slates), +1.19 ± 8.65 over all 7 main slates (5 of 7). So extending proposal 1 to mains is
a DIRECTIONAL candidate (PROVISIONAL, review on the mains-only week), not part of the PROVEN flagship proposal. Do not
extend it to qualifiers (NOISE, wrong sign at the top).

### Proposal 1 gate: true flagships since 11-24

The gate is "after 11-27 grades, only if the 7-slate number still clears 2×SE". **11-27 is pending**: the standings
for its contests (198269753, 198278517) and its night record were not on hand at the time of this addendum, so this
is the current 6 slates (11 contests). fr_p1_recut.py picks 11-27 up once fr_fill.py is re-run with those files.

| Flagships since 11-24 (6 slates) | Mean $ per slate | Ahead | 2×SE | Clears? |
|---|---|---|---|---|
| Top-half random − entered | +35.22 ± 14.61 | 6 of 6 | 29.21 | yes |
| Top-25% random − entered | +36.85 ± 20.23 | 5 of 6 | 40.47 | no |
| Top-10% random − entered | +29.76 ± 20.36 | 5 of 6 | 40.71 | no |
| Top-half random, median $ − entered | −2.50 ± 6.92 | 1 of 6 | 13.84 | no (the joint pick still wins the median) |
| Entered − plain random kept | −33.36 ± 10.24 | 0 of 6 | 20.48 | entered trails |

Top half remains the right band: narrower bands do not add and lose the 2×SE margin. Over all 9 flagship slates
with board values, top-half random − entered is +35.38 ± 14.10 (8 of 9).

Variants' share of the TOP HALF of the kept pool on flagship nights since 11-24: 30.9%, 50.9%, 28.1%, 23.1%, 41.2%,
35.9% (mean 35.0%, against 20.1% of all kept). A 25% variants cap would bind on 5 of the 6 nights, so the cap does
change what proposal 1 draws from; the two should be reviewed together.
