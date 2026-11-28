# Max-entry random draws, flagship vs main (2026-11-28)

Analysis only. The HOLD stands; no proposal. Everything here comes from `max_entry_draws_2026-11-28/med.py` (draws and
scoring) and `med_report.py` (tables). The output is in `med_report.out`; the per-contest draws are in `med_rows.json`.

## Plain-English summary

The question is how much of the flagship loss comes from entering only a handful of lineups. To test it, every
contest is replayed with random lineups from our own kept pool, once at the number of lineups we actually entered and
once at the contest's maximum.

- **Flagships still lose when we max-enter at random.** Random draws at the max count return **−25%** on an average
  slate, against **−66%** for the lineups we entered. Over the whole period, the middle outcome is **−33%**, and **71%**
  of draw sets finish negative.
- **Max-entering narrows the spread a lot.** At the max count the period ranges from −70% to +69% (5th to 95th
  percentile). At our real count it ranged from −82% to +210%.
- **So the flagship loss has three parts.** Part is our pick: entered −66% against random −27% at the same count. Part
  is small samples. Underneath both, flagships still look negative.
- **Mains break about even with plain random draws:** about −5% a slate, and 59% of draw sets finish negative.
  Drawing from the board's top half improves this to **+28%** a slate, with a period median of +16% and 34% finishing
  negative, but on 7 slates.
- **Mains beat flagships** on 9 of 11 slates that had both, by about 16 points of ROI. That's inside 2×SE, so it's
  tagged **DIRECTIONAL** under rule 5. The mechanism makes sense: flagships are top-heavy, and the fields are smaller
  but much more expensive.
- **The entered mains' +36%** comes from two slates, 11-18 (+557%) and 11-20 157015 (+324%), as found before.

## Data and method

- **Slates:** 14 builds from 11-16 to 11-26, with 68 contests (20 flagship, 43 main, 5 qualifier).
  - 11-27 (157547) is **not included**. Its standings for 198269753 and 198278517 weren't on origin when this was
    committed. `med.py` picks it up on a re-run once they're added.
  - Builds from before 11-20 have no board values, so the top-half rule covers 9 flagship and 7 main slates.
- **Contest type:** `scripts/dk_contest_type.py`.
- **Max entries:** each contest's `max_per_user` from the slate's contest list. Flagships allow 1, 3, 7, 9, 14 or 16;
  mains allow 3 to 20; qualifiers allow 2. We entered 1–4 in flagships, so the max count is about 4× our real count
  there; in mains we were usually already at the max. The kept pool (1,000–2,400 lineups) was never smaller than the
  max entries.
- **Draws:** 1,000 per contest, uniform without replacement.
  - **plain:** from the whole kept pool.
  - **top50:** from the top half of the kept pool by board sim value.
- **Caps, as the page's main profile:**
  - a player appears in at most ceil(60% of the entries);
  - any two of our lineups differ by at least 3 players.
  - Draws that break a cap are redrawn up to 200 times a seat.
  - Seats left empty: flagships 2–5%, mains 4–9% per draw. Fees are charged only on filled seats.
- **Scoring:** our real entries are removed from the standings (`dk_eval.USER`), then the drawn lineups are added
  together.
  - Each of our lineups is paid the mean of the places its points tie over, so our lineups push each other down.
  - The contest's payout table is unchanged; with extra entries, the contest would be over its real size.
  - "Entered lineups, re-scored" puts the lineups we entered back in the same way. It reads close to, but not exactly
    at, what DraftKings paid.
- **Not modelled:** caps across contests (the 60% night cap, max contests per lineup), hand edits and late swap.

## Results by contest type

ROI is payouts ÷ fees − 1.
- **Slate ROI** is each slate's expected ROI across draws: mean ± SE over slates, then k of n positive and the
  median.
- **Period ROI** pools every contest of that type for each draw set: 5th / 50th / 95th percentile over the 1,000
  sets, and P(negative).

| Type | Rule | Count | Lineups | Fees | Slate ROI | Positive | Median slate | Period p5 / p50 / p95 | P(period < 0) | Top-1% | Cash |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flagship | entered | real | 43 | $570 | −60.0% ± 14.5 | 2 of 13 | −84.6% | −65.8% (realised) | n/a | n/a | n/a |
| Flagship | plain | actual | 43 | $557 | −26.7% ± 24.9 | 3 of 13 | −62.9% | −82% / −56% / +210% | 0.78 | 0.014 | 0.173 |
| Flagship | plain | **max** | 158 | $2,283 | **−25.4% ± 24.2** | 3 of 13 | −63.8% | **−70% / −33% / +69%** | **0.71** | 0.012 | 0.168 |
| Flagship | top50 | actual | 36 | $460 | −4.3% ± 34.6 | 2 of 9 | −40.6% | −79% / −49% / +154% | 0.78 | 0.016 | 0.195 |
| Flagship | top50 | max | 105 | $1,494 | −6.3% ± 30.6 | 3 of 9 | −44.9% | −62% / −16% / +126% | 0.62 | 0.017 | 0.208 |
| Main | entered | real | n/a | $299 | +40.6% ± 60.2 | 3 of 12 | −52.4% | +35.7% (realised) | n/a | n/a | n/a |
| Main | plain | actual | 655 | $286 | −5.7% ± 30.1 | 2 of 12 | −36.1% | −45% / −6% / +52% | 0.58 | 0.014 | 0.196 |
| Main | plain | **max** | 714 | $338 | **−5.3% ± 32.2** | 2 of 12 | −38.1% | **−41% / −6% / +40%** | **0.59** | 0.014 | 0.198 |
| Main | top50 | actual | 391 | $183 | +26.3% ± 46.9 | 3 of 7 | −0.6% | −42% / +8% / +86% | 0.43 | 0.019 | 0.221 |
| Main | top50 | max | 397 | $189 | +28.0% ± 48.9 | 3 of 7 | −1.3% | −32% / +16% / +97% | 0.34 | 0.021 | 0.225 |
| Qualifier (context) | plain | max | 10 | $200 | +67.7% ± 74.5 | 3 of 5 | +24.0% | −100% / +122% / +233% | 0.10 | 0.152 | 0.152 |

## Flagship vs main (rule 5)

This is the per-slate ROI difference on the 11 slates with both types.

| Draw | Flagship − main | Flagship ahead | 2×SE | Tag |
|---|---|---|---|---|
| plain, max count | −16.2% ± 12.2 | 2 of 11 | 24.5 | DIRECTIONAL |
| top50, max count | −19.0% ± 15.8 | 2 of 7 | 31.7 | DIRECTIONAL (7 slates) |
| plain, actual count | −17.0% ± 8.8 | 1 of 11 | 17.6 | DIRECTIONAL (just short of 2×SE) |

## Per slate: entered vs random at the actual count vs random at the max count

Plain draws. Each cell is the slate's mean ROI over draws, with the [5th, 95th] percentile over draws. The full list
is in `med_report.out`. Selected flagship slates:

| Slate | Entered | Random, actual count | Random, max count |
|---|---|---|---|
| 11-20 157015 | −50% | +133% [−100%, +1360%] (4 lineups) | +144% [−66%, +974%] (15) |
| 11-24 157024 | +50% | +187% [−80%, +1178%] (4) | +163% [−32%, +904%] (15) |
| 11-24 157026 | −85% | −4% [−100%, +124%] (7) | −11% [−90%, +235%] (20) |
| 11-25 157295 | −29% | +16% [−100%, +114%] (3) | +39% [−77%, +860%] (15) |
| 11-23 157021 | −100% | −94% [−100%, −61%] (5) | −94% [−100%, −82%] (10) |

On most flagship slates, max-entering doesn't move the expected ROI much; it narrows the range. The nights that pay
(11-20 157015, 11-24 157024) pay at either count, and the nights that don't (11-23, 11-25 157293) lose at either
count.
