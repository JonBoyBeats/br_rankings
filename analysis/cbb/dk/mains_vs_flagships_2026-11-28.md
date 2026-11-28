# Mains vs flagships (2026-11-28)

The question: why do our main contests run +50% ROI while flagships run −63% (Friday review, section 11)? Is it the pick method, the contest structure, or noise?

This is analysis only. The HOLD stands, and nothing on the page, in the projections, ownership, field, cut or fill changed. Tags follow process.md rule 5.

**Data:** our real entries in all 84 graded contests (16 slates, 11-16 to 11-26), replayed from the standings files. Fees ($1,081.35) and dollars back ($1,066.20) reconcile exactly with eval.csv.

**Scripts and outputs:** in [mains_vs_flagships_2026-11-28/](mains_vs_flagships_2026-11-28/).
- `mf.py` builds the per-contest rows.
- `mf2.py` covers results, variance, construction and era.
- `mf3.py` is the random-finish noise check.
- `mf4.py` compares entered portfolios with random kept fills (from `fr_fill.py`, rerun).
- `page_types.py` reclassifies contests by the DK page's profile.

Our entries are "us" throughout.

## Verdict

**Mostly noise, plus contest structure; not the pick method.**

1. **The main +50% is two cashes.**
   - All the profit is the $1 And-One: 196 entries, +73%. The $125 cash on 11-18 and the $80 cash on 11-20 make it.
   - Without the top cash, main ROI is **+2%**; without the top two, **−28%**.
   - Only 4 of 13 slates were in profit, and the median slate lost 52%.
   - Bootstrap over slates, 90%: **[−39%, +153%]**.
   - The cheaper mains lost: $0.10 Dime Time −38%, $0.25 Quarter Jukebox −9%.
   - **Tag: NOISE.**
2. **The flagship −63% is the $15 Pull Up Jumper.**
   - It carries $540 of the $622 flagship fees: 36 entries, −69%.
   - A uniformly random finish in these exact contests returns −12%. Our −63% sits at the **16th percentile** of random-finish outcomes.
   - Payouts of 5x the fee or more: random finishing expects 4.6 of them; we had 4 (P = 0.52).
   - Nothing says we finish worse there: our mean finish percentile is 49.8.
   - **Tag: NOISE**, as a claim that flagships are worse for us.
3. **The pick method doesn't separate the two types.**
   - The gap was there before the joint fill: flagships −65% before 11-24 and −61% from it.
   - Mains swung from +82% before to +4% from 11-24, under the same per-contest Max ROI method throughout.
   - From 11-24, **both** types' entered portfolios trail random fills from the same kept pool: flagships by −60 ROI points (6 slates), mains by −35 (4 slates).
   - The flagship gap is the held proposal 1 (top-half random fill, PROVEN, held). The main gap is 4 slates, so **NOISE** for now.
4. **We build the same way in both.** Against each contest's field, per slate:
   - own sum −11 (flagship) and −9 (main);
   - about $83–92 less salary left;
   - more 3-2 game stacks (15 of 16 slates, 13 of 13);
   - about +13 projected points.
   - Construction doesn't explain the split. **DIRECTIONAL** (finding).
5. **Structure decides how often a result can swing.**
   - Flagships are small and top-heavy: median field 313, first place 20% of the pool against 10% in mains, and fees of $5–15 against $0.10–1.
   - We enter few lineups each: 2.1 per contest under the page's profile, against 14.3 in mains.
   - So the flagship result turns on whether one top finish lands. At about 1 expected big cash over the whole sample, 16 nights can't tell an edge from bad luck.

**For the operator's main-only week:** the main sample's honest read is about break-even (+2% without its top cash). A week of mains will mostly measure the process, not profit, which suits the plan.

## 1. Results and variance, by contest type

Types are the Friday review's by-size split (qualifier/small: qualifier, satellite or under 100 entries; flagship: Pull Up Jumper or 100–799 entries; main: 800+).

| Type | Contests | Slates | Entries | Fees | Back | ROI | Cash rate | Top cash, 2nd | ROI w/o top 1 | ROI w/o top 2 | Bootstrap 90% (slates) | Slates in profit | Mean finish pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flagship | 37 | 16 | 156 | $622.35 | $230.55 | −63.0% | 28.2% | $30, $30 | −67.8% | −72.6% | [−82%, −39%] | 4 of 16 | 49.8 |
| main | 32 | 13 | 576 | $261.00 | $391.65 | +50.1% | 24.8% | $125, $80 | +2.2% | −28.5% | [−39%, +153%] | 4 of 13 | 52.5 |
| qualifier/small | 15 | 9 | 18 | $198.00 | $444.00 | +124.2% | 11.1% | $222, $222 | +12.1% | −100% | [−100%, +407%] | 2 of 9 | 28.9 |

Qualifier "back" is two $222 satellite tickets (11-24 and 11-25), counted at face value as eval.csv does.

Fees and returns by entry fee, the concentration behind each headline:

| Type | Fee | Fees | Back | Entries | ROI |
|---|---|---|---|---|---|
| flagship | $15 | $540.00 | $170.00 | 36 | −69% |
| flagship | $5 | $45.00 | $25.00 | 9 | −44% |
| flagship | $1 | $22.00 | $16.50 | 22 | −25% |
| flagship | $0.25 | $10.75 | $6.25 | 43 | −42% |
| flagship | $0.10 | $4.60 | $12.80 | 46 | +178% |
| main | $1 | $196.00 | $338.50 | 196 | +73% |
| main | $0.25 | $45.00 | $40.75 | 180 | −9% |
| main | $0.10 | $20.00 | $12.40 | 200 | −38% |

**Random-finish check** (`mf3.py`): every one of our entries placed uniformly at random in its real contest, with the real payout tables, 4,000 draws. The spread is optimistic because it ignores the correlation between our own entries.

| Type | Random-finish ROI | 90% of random outcomes | Our real ROI's percentile among them | 5x-fee+ cashes expected / observed | P(observed or fewer) |
|---|---|---|---|---|---|
| flagship | −11.8% | [−72%, +167%] | 16th | 4.57 / 4 | 0.52 |
| main | −14.8% | [−47%, +36%] | 97th | 12.15 / 16 | 0.89 |
| qualifier/small | −33.7% | [−100%, +126%] | 89th | 0.77 / 2 | 0.96 |

The main result sits at the top of what random finishing produces, and the flagship result near the bottom. Both are within it. Both rest on a handful of finishes.

## 2. Pick method and era

The joint top-1% fill (`DKSim.pickJoint`) runs on flagships from 11-24. Mains use per-contest Max ROI throughout. Our real entries:

| Type | Era | Contests | Slates | Entries | ROI | ROI w/o top 1 | Finish pct |
|---|---|---|---|---|---|---|---|
| flagship | before 11-24 | 25 | 10 | 128 | −65% | −74% | 49.5 |
| flagship | 11-24 on | 12 | 6 | 28 | −61% | −70% | 51.1 |
| main | before 11-24 | 20 | 9 | 336 | +82% | +1% | 48.0 |
| main | 11-24 on | 12 | 4 | 240 | +4% | −19% | 58.9 |

**Entered portfolios against 1,000 random fills from the same night's kept pool** (`fr_fill.py` rerun, it reproduces section 9; `mf4.py` as ROI; 14 slates with saved portfolios):

| Type | Era | Contests | Slates | Fees | Entered ROI | Random kept fills ROI | Gap |
|---|---|---|---|---|---|---|---|
| flagship | all | 31 | 14 | $605.65 | −64% | −20% | −43 pts |
| flagship | before 11-24 | 19 | 8 | $269.65 | −67% | −45% | −22 pts |
| flagship | 11-24 on | 12 | 6 | $336.00 | −61% | −0% | −60 pts |
| main | all | 31 | 12 | $260.00 | +47% | +3% | +44 pts |
| main | before 11-24 | 19 | 8 | $152.00 | +77% | −24% | +100 pts |
| main | 11-24 on | 12 | 4 | $108.00 | +4% | +40% | −35 pts |

In dollars per slate (section 9): flagship entered − random −$18.70 ± 8.17 (14); main +$9.50 ± 11.73 (12). Main's lead over random is the two pre-11-24 cashes. Since 11-24 both types trail random. Only flagships changed method then, so the trailing isn't the joint pick alone.

## 3. Construction: us against the field

Per lineup. The field is 400 sampled other entries per contest. "us − field" is the per-contest difference averaged per slate, ± SE over slates, with the count of slates where it was positive. Ownership is real ownership from the lineups (the 683c36d fix). Projection is our fp_dk at lock.

| Measure | Flagship us | field | us − field | Main us | field | us − field |
|---|---|---|---|---|---|---|
| own sum | 261.2 | 261.9 | −11.48 ± 7.73 (5/16 +) | 210.8 | 223.8 | −8.61 ± 4.80 (4/13 +) |
| players under 10% | 1.30 | 1.40 | +0.16 ± 0.16 | 1.92 | 1.79 | +0.18 ± 0.16 |
| players 15%+ | 5.69 | 5.86 | −0.36 ± 0.20 | 5.31 | 5.41 | −0.10 ± 0.13 |
| salary left ($) | 76 | 167 | −91.8 ± 17.5 (2/16 +) | 90 | 159 | −82.7 ± 16.0 (1/13 +) |
| most from one team | 2.59 | 2.36 | +0.32 ± 0.13 | 2.50 | 2.29 | +0.21 ± 0.09 |
| most from one game | 3.51 | 3.35 | +0.26 ± 0.16 | 3.30 | 3.14 | +0.23 ± 0.15 |
| 3-2 game stack (share) | 0.87 | 0.76 | +0.18 ± 0.04 (15/16 +) | 0.79 | 0.68 | +0.11 ± 0.02 (13/13 +) |
| our projection (pts) | 202.5 | 191.5 | +12.84 ± 1.57 (15/16 +) | 205.5 | 191.2 | +12.98 ± 1.64 (13/13 +) |

Every lineup, ours and the field's, has some 2-player game stack, so the 2+1 share is 1.00 everywhere and isn't shown.

| Our entries | Flagship | Main |
|---|---|---|
| duplicated by another entry in the contest | 3.0% | 1.4% |
| players shared, average pair of our entries (of 8) | 3.64 | 3.29 |
| max player exposure across our entries | 86% | 73% |
| distinct lineups / entries | 152 / 156 | 573 / 576 |

Qualifier/small, for completeness (9 slates, 18 entries): own sum −90 ± 23 under the field, and the qualifier fields are much chalkier than ours. Its full table is in `mf2.out`.

## 4. Contest structure

| Type | Field size, median (range) | Share paid | 1st prize / pool | Pool / fees | Fees per entry | Our entries per contest |
|---|---|---|---|---|---|---|
| flagship | 313 (114–713) | 22.8% | 20.4% | 0.88 | $0.10–$15 | 4.2 |
| main | 1,189 (831–1,646) | 23.8% | 10.3% | 0.86 | $0.10–$1 | 18.0 |
| qualifier/small | 10 (7–95) | 5.7% | 85.3% | 1.24 | $1–$20 | 1.2 |

The rake is the same in both (pool ≈ 0.86–0.88 of fees), so a random finish loses about 12–15% in either. The difference is shape and stake:
- flagships are twice as top-heavy and smaller fields;
- their entries cost 5–150x more, so the flagship dollars sit on 36 entries;
- the main dollars spread over 576 entries.

## 5. The page's profile instead of the by-size split

The by-size split puts 13 contests the page treats as mains (20-max And-One, Dime Time and Quarter Jukebox with 114–713 entries) into "flagship". `page_types.py` lists them. Under the page's profile (`dk_flagship_compare.js`: Pull Up Jumper, or 100–799 entries and not Dime Time / And-One / Quarter Jukebox):

| Type (page profile) | Contests | Slates | Entries | Fees | ROI | w/o top 1 | w/o top 2 | Bootstrap 90% | Random-finish pct | 5x+ cashes exp. / obs. |
|---|---|---|---|---|---|---|---|---|---|---|
| flagship | 21 | 14 | 45 | $585.00 | −66.7% | −71.8% | −76.9% | [−85%, −43%] | 15th | 1.09 / 0 (P = 0.34) |
| main | 48 | 14 | 687 | $298.35 | +43.2% | +1.3% | −25.5% | [−38%, +139%] | 97th | 15.63 / 20 |

Same verdict. The page's flagships are 45 entries over 14 slates, at $5–15 each, with about one big cash expected over the whole sample. Entered vs random kept fills under the page's profile, from 11-24: flagship −60 pts (6 slates), main −38 pts (4 slates). See `mf4_page.out`.

## 6. Main-only nights: does the scorecard read cleanly?

Checked on the existing main-only night (2026-11-17, 156663) and the full run:
- **`dk_eval.py scorecard`:** runs clean. The fill arm and `fills` (fill_eval.csv) are contest-type agnostic: they grade whatever portfolios a night has.
- **The flagship record (`flagjoint`, `dk_flagship_compare.js`):** writes no row on a night with no flagship (it exits 0), so it neither breaks nor misleads.
- **The results arm:** already per-night ROI.
- **One thing misled:** the fill arm's headline is entered − random in **dollars**. A $0.10–$1 main-only week shows near-zero dollar gaps, and averaging them with nights that carried $15 flagships mixes scales.
- **Fix (report only, allowed under the HOLD):** the fill cell now adds the gap as a **% of the night's fees**, e.g. "+21.77 ± 30.60 (7) (54 pct); +25 ± 36 (7) % of fees".
  - The code is `fill_arm` / `window_cells` in `scripts/dk_scorecard.py`.
  - A zero-fee night gives n/a rather than a division.
  - Tests: `tests/dk_scorecard.py`, 25 pass, two new ones for a main-only and a zero-fee night.

## Watch list (none of this is a proposal)

| Item | Tag | What would settle it |
|---|---|---|
| Main ROI edge (+50% / +43%) | NOISE | Without its top cash it's +1–2%. Read over 20+ main-only nights, on finish percentile and ROI without the top cash. |
| Flagships worse for us | NOISE | About 1 big cash expected in the sample; needs a far larger flagship sample than the plan will give. |
| Entered trails random kept fills from 11-24, in mains too | NOISE (mains, 4 slates) | The main-only week adds about 7 slates of exactly this comparison. Watch the fill arm's new % of fees column. |
| We build the same way in both types (own −9 to −11, more salary, more 3-2 stacks, +13 proj) | DIRECTIONAL (finding) | n/a |
