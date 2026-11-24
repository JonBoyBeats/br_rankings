# Contest profiles in the Fill (2026-11-24)

The operator approved contest profiles for the Fill, relayed by the coordinator. This note covers what was built (branch `fill-profiles`, not yet on main) and the in-sim check of the flagship's win objective.

## Bottom line

**The win objective as specified does not hold up out of sample.**

- **On the nights it picks from** (in-sample), it beats the current Max ROI fill on P(1st) on 6 or 7 of the 7 flagship contests.
- **On a fresh draw of nights** (out of sample), it never beats Max ROI on P(1st). It is level or lower on most contests and gives up expected payout:
  - **at the entered count:** level or lower on 5 of 7 contests, −$35.38 expected payout across the 7;
  - **at 3 lineups:** lower on 7 of 7, −$57.96.

The greedy is chasing the few nights (about 1–3% of 3,000) on which a lineup happened to win.

**Top-1% coverage does better.** That is the existing "Max coverage" objective. Out of sample, it raises P(1st) over Max ROI on 4 to 6 of the 7 contests at every set size, with equal or higher expected payout.

**P(1st) cannot be proven on real results.** At 1–4% a night, about a dozen graded nights give well under one expected 1st for any set, so every number here is in-sim.

**Recommendation for the operator:** keep the flagship profile and its fill order, but run it on top-1% coverage rather than the win objective, until more nights say otherwise. The change is one line: the flagship's objective in `pickPortfolios`. It is not made here because the operator approved "win".

## What was built

### Contest profiles

Each contest you enter is recognised once, by its name and size. An override on the Fill step's Profiles screen is kept for that slate. It is never a nightly dial.

| Profile | Recognised by | Filled |
|---|---|---|
| **Flagship (win)** | "Pull Up Jumper"; a late add of 100–800 entries | First, from the whole kept pool. `DKSim.pick` objective `win`: the added nights one of the set places 1st, weighted by the share of 1st's prize it takes; added expected payout breaks ties. Min unique is off; the 60/60 caps stay. P(1st) is shown at 2, 3 and 4 lineups. Its standings come first in the Swap step. |
| **Main block** | "And-One", "Quarter Jukebox"; a late add of 800+ | One shared block, entered in every block contest. Each contest takes the block in order while it has entries. Picked greedily by the added expected payout summed over the contests it goes into (`DKSim.pickBlock`). A block lineup counts once per contest against the night cap and Max pair. Max contests per lineup allows the block's contests. |
| **Main block · lab** | "Dime Time" | In the block, and the only contest a test idea's lineups can enter. |
| **Qualifier (max ROI)** | "Qualifier" / "Satellite"; a late add under 100 entries | Max ROI, with no structural rule. |
| **Standard** | override only | The fill as before (Start from). |

How the block handles a short contest and a lone main contest:

- A block contest left short gets the fill's usual relax steps on its own: Max core 20%, then 25%, then Max exposure 70%.
- A night with only one main contest fills it with that contest's own Max ROI.

The 60/60 caps and Auto top-up apply to every profile.

**Test ideas.** Each idea row in the Bank step has a **test** toggle. A marked idea's lineups go only into the lab contest. The mark is kept with the bank and in Save build (`test_ideas`).

**Ticket contests.** DraftKings' lobby gives qualifiers and satellites no payout table. Their prize is taken as one ticket worth the prize pool, paid to 1st. This is an assumption; the screen marks it ("ticket: 1 to 1st (assumed)").

**P(1st) on the page** is scored on a fresh draw of nights, not the ones the set was picked on, and is labelled "(fresh nights, in-sim)". The reason is the in-sample flattery shown below.

**Field users (capture only).** `python3 scripts/dk_eval.py fieldusers --mirror ../br-adp-mirror` writes `analysis/cbb/dk/field_users.csv`. It takes each graded small contest (10–30 entries, or a qualifier / satellite under 100) and writes one row per user with:

- entries and distinct lineups;
- the mean summed projected ownership of their lineups (own_sum, chalk-follow), and per player (own_avg);
- the mean number of players projected under 5% (sub5, leverage).

Projected ownership is the night record's `own`. The owner's own entries are left out. Today it has 13 rows from 2 contests; only two graded standings files are that small. Nothing reads it yet.

### On the 11-23 build (157021)

The build was loaded with the slate and simulated field as they stood at lock; the mirror's current file has dropped that slate's field. Fill all contests then:

- recognised 7 contests: 2 flagship (the $4K Pull Up Jumper, and the $750 High Five by its size of 178), 4 main block and Dime Time as the lab;
- filled 79 of 79 entries;
- shared 17 lineups across the main block, with the relax steps and Auto top-up filling the rest.

The flagship's P(1st) on fresh nights was 2.7% with 4 lineups (1.2% / 2.2% / 2.7% at 2 / 3 / 4). The full fill note is in `fill_profiles_2026-11-24/fill_note.txt`. The screenshots are `fill_profiles_2026-11-24/profiles_desktop.png` and `profiles_phone.png` (390px).

## The in-sim comparison

**Script.** `scripts/dk_flagship_compare.py` (driver) and `scripts/dk_flagship_compare.js`. It covers every saved build with a Pull Up Jumper entry: 7 contests on 6 nights, 11-16 to 11-23.

**Data.** Each build's final pool, the slate and simulated field at lock, and the contest's seeded nights (seeded as the caps backtest seeds them).

**Sets compared.** Under contest exposure 60% and Max core 15%, with a short set relaxed as the page relaxes it:

- **Max ROI:** the fill before profiles; Min unique 3.
- **Win:** the flagship profile; Min unique off.
- **Top-1% coverage:** Min unique 3.
- **Entered:** the set actually entered.

**Scoring.** Each set is scored on the nights it was picked on (in-sample) and on a second, independent draw (out of sample).

### 3,000 nights (the page's default)

P(1st) is the mean over the 7 contests. EV is expected payout, summed over the 7.

| Set size | Score on | P(1st) Max ROI | P(1st) win | P(1st) top-1% | EV Max ROI | EV win | EV top-1% | Win vs Max ROI on P(1st) (higher / lower) |
|---|---|---|---|---|---|---|---|---|
| entered count | in-sample | 1.41% | 1.74% | 1.35% | $386.61 | $377.20 | $382.61 | 6 / 0 |
| entered count | **fresh nights** | 1.14% | 1.10% | **1.29%** | $343.71 | $308.33 | **$348.77** | 2 / 4 |
| 2 | **fresh nights** | 1.05% | 0.96% | **1.20%** | $322.81 | $284.80 | **$335.31** | 0 / 5 |
| 3 | in-sample | 1.84% | 2.23% | 1.77% | $512.40 | $489.26 | $511.81 | 7 / 0 |
| 3 | **fresh nights** | 1.49% | 1.30% | **1.63%** | $450.68 | $392.72 | **$469.64** | 0 / 7 |
| 4 | in-sample | 2.39% | 2.95% | 2.32% | $655.89 | $640.86 | $655.44 | 7 / 0 |
| 4 | **fresh nights** | 1.84% | 1.80% | **2.09%** | $571.05 | $519.94 | **$593.34** | 2 / 5 |

**Top-1% coverage against Max ROI**, on fresh nights, by set size:

| Set size | Coverage higher on P(1st) | Coverage lower on P(1st) |
|---|---|---|
| entered count | 5 | 1 |
| 2 | 4 | 0 |
| 3 | 4 | 1 |
| 4 | 6 | 1 |

At 10,000 nights (`flagship_compare_10000.jsonl`), the win objective's in-sample lead shrinks, and on fresh nights it is still no better than Max ROI:

- **P(1st):** 1.05% against 1.16% at the entered count; 1.75% against 1.73% at 4.
- **Expected payout:** $31–60 lower across the 7 at every set size.

Top-1% coverage is level with Max ROI or ahead on P(1st) (1.23% against 1.16% at the entered count; 1.90% against 1.73% at 4).

### By contest

3,000 nights, scored on fresh nights. Each cell is P(1st) / expected payout.

| Night | Contest | Size | Ours | Entered | Max ROI | Win | Top-1% coverage |
|---|---|---|---|---|---|---|---|
| 11-16 | $6K Pull Up Jumper | 470 | 1 | 0.9% / $39.92 | 0.9% / $39.92 | 0.9% / $39.92 | 0.9% / $39.92 |
| 11-18 | $7K Pull Up Jumper | 549 | 1 | 0.3% / $17.92 | 0.2% / $15.40 | 0.1% / $11.09 | 0.3% / $17.92 |
| 11-19 | $3K Pull Up Jumper | 235 | 1 | 0.4% / $15.66 | 0.4% / $18.07 | 0.4% / $10.74 | 0.5% / $15.81 |
| 11-19 | $6K Pull Up Jumper | 470 | 3 | 0.9% / $51.40 | 1.3% / $67.79 | 1.1% / $59.45 | 1.2% / $61.03 |
| 11-20 | $3K Pull Up Jumper | 235 | 2 | 0.9% / $31.72 | 1.4% / $40.77 | 1.1% / $34.07 | 1.5% / $41.97 |
| 11-20 | $6K Pull Up Jumper | 470 | 3 | 1.2% / $63.81 | 1.4% / $63.81 | 1.4% / $61.19 | 1.8% / $76.78 |
| 11-23 | $4K Pull Up Jumper | 313 | 4 | 2.4% / $95.94 | 2.3% / $97.95 | 2.7% / $91.88 | 2.9% / $95.33 |

### Why the win objective overfits

A lineup places 1st on roughly 1 night in 100 or fewer, which is about 10–40 of the 3,000 nights. Picking to maximise the nights the set wins rewards lineups that happened to win on those particular nights, which is mostly noise. Expected payout and top-1% coverage use many more nights per lineup (every paid place, or the top 1%), so what they pick holds up on new nights.

### What this can and cannot say

- **It is all in-sim.** The sim's field, projections and correlations are the same model the fill uses. A model error would hit every objective alike, and nothing here checks it.
- **Real results cannot settle P(1st) yet.** About a dozen graded nights at 1–4% per night give under one expected 1st for any set. Telling a 1.3% set from a 1.6% one on real results would take hundreds of flagship nights.
- **It is 7 contests on 6 nights,** one pool each.
- **The fresh-night check is the honest in-sim test.** It is what the page now shows.

## Files

- `dk.html`, `dk_sim.js` (`builder` win credit, `pick` objective `win`, `pickBlock`).
- `tests/dk_page.js`: profiles, the win pick, the block and its night cap, the test toggle, the Swap order, the phone layout.
- `scripts/dk_eval.py fieldusers` → `analysis/cbb/dk/field_users.csv`.
- `scripts/dk_flagship_compare.py` and `.js` → `fill_profiles_2026-11-24/flagship_compare.jsonl` (3,000 nights) and `flagship_compare_10000.jsonl`.
- `fill_profiles_2026-11-24/profiles_desktop.png`, `profiles_phone.png`, `fill_note.txt` (11-23 build).
