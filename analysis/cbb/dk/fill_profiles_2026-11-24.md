# Contest profiles in the Fill (2026-11-24)

The operator approved contest profiles for the Fill and decided the details after the first preview (relayed by the coordinator). This note covers what the `fill-profiles` branch does, what the in-sim checks say, and what they can't say. Nothing is on main until the operator's OK.

## What the profiles do

Each contest you enter is recognised once, by its name and size. An override on the Fill step's Profiles screen is kept for that slate. It is never a nightly dial.

| Profile | Recognised by | Filled |
|---|---|---|
| **Flagship (top-1% coverage)** | "Pull Up Jumper"; by size 100–800 (the High Five, a late add) | First, **all flagships together** (`DKSim.pickJoint`): greedily by the added share of nights on which at least one flagship lineup reaches the top 1% of its own contest, with added expected payout as the tiebreak. Every flagship is simulated on the same nights. Min unique is off. P(1st) is shown at 2, 3 and 4 lineups. First in the Swap step's order. |
| **Main (max ROI)** | "And-One", "Quarter Jukebox"; by size 800+ | Each contest by its own Max ROI, so each keeps its own diminishing returns. |
| **Main · lab** | "Dime Time" | Max ROI, and the only contest a test idea's lineups can enter. |
| **Qualifier (max ROI, chalk field)** | "Qualifier" / "Satellite"; by size under 100 | Max ROI, simulated against a chalk-leaning field. Qualifiers and satellites are winner-take-all: one ticket to 1st. |
| **Standard** | override only | The fill as before (Start from). |

Rules that apply across profiles:

- **Lineup reuse.** A lineup can go into up to Max contests per lineup (3), flagship lineups included, within the 60% night cap.
- **Caps and top-up.** The 60/60 caps and Auto top-up apply to every profile.
- **Short sets.** A flagship left short gets the fill's usual relax steps on its own, by its top-1% coverage: Max core 20%, then 25%, then Max exposure 70%.
- **Test ideas.** Each idea row in the Bank step has a **test** toggle. A marked idea's lineups go only into Dime Time: never the flagships, the And-One or the Quarter Jukebox.

**Why coverage and not "win".** The first preview's "win" objective counted the nights a set places 1st. On fresh nights it did not beat Max ROI on P(1st) and it cost expected payout. Top-1% coverage did better on both. That comparison is in `fill_profiles_2026-11-24/flagship_compare*.jsonl`, from the script's version at commit 577892c. The operator chose coverage.

**Fresh nights.** All flagship numbers on the page are scored on a fresh draw of nights, not the nights the set was picked on, because those flatter it.

### The qualifiers' chalk field

Small winner-take-all fields lean to the chalk. The field builder (battle-royale-research `scripts/dk_cbb_field.py`) has a chalk style: projection on DraftKings' average alone, noise 0.10, fitted as a fifth of the field.

Rebuilding a field of that style in the page would need the optimizer, so the slate's own field is **reweighted** instead:

- its lineups are ranked by summed DraftKings average, which is what that style maximises;
- the top fifth (the chalk-style lineups) makes up `QUAL_CHALK` = 80% of the qualifiers' field, each repeated, since chalk players land on the same lineup;
- the other 20% is the remaining lineups, spread evenly.

On the 11-23 slate this moves the field's median summed projected ownership from 248% to 309%.

`QUAL_CHALK` is a first setting. It is to be refit from the real qualifier fields as `dk_eval.py fieldusers` captures them into `analysis/cbb/dk/field_users.csv`. That file has one row per user per graded small contest: entries, lineups, own_sum, own_avg, and sub5 (players under 5% projected). It has 13 rows so far.

**What it shows.** The Profiles screen shows each qualifier's lineups' summed ownership against that field's median.

**A finding.** On the 11-23 build (illustration below), Max ROI against the chalk field chose lineups at 202% and 209% against a 309% median. That is contrarian, not "chalk with a pivot or two". The pool is the reason:

- the build's 2,221 kept lineups have a median own sum of 207% and a 90th percentile of 245%;
- only 1 of them reaches 309%.

The fill can only pick from what was banked. To land near chalk, the qualifiers need chalk lineups in their candidates. Two ways to add them, not done here (each is a new source of lineups for the fill):

- a chalk batch drawn for them;
- the chalk field's own top lineups.

## Flagships together or apart: in-sim, fresh nights

**Script.** `scripts/dk_flagship_compare.py` (driver) and `scripts/dk_flagship_compare.js` → `fill_profiles_2026-11-24/flagship_joint.jsonl`.

**Data.** Each saved build's final pool, plus the lineups it entered, with the slate and simulated field at lock and 3,000 nights.

**Sets compared.** Under contest exposure 60%, Max core 15% and Min unique off, with a short set relaxed as the page relaxes it:

- **separate:** each flagship by its own Max coverage, the largest stake first;
- **joint:** the flagship profile.

Every flagship is simulated on the same nights. Each set is scored on a fresh, independent draw. **Joint coverage** is the share of nights on which at least one flagship lineup reaches the top 1% of its contest.

Two of the eight builds entered two flagships. Five entered one, where joint and separate are the same set by construction. 11-17 entered none.

| Night | Flagships (ours) | Set | Joint coverage | Pull Up Jumper top 1% | High Five top 1% | Expected payout, both |
|---|---|---|---|---|---|---|
| 11-20 main | $6K PUJ (3), $500 High Five (1) | separate | 7.10% | 6.47% | 3.30% | $83.36 |
| | | **joint** | **8.30%** | 5.30% | 3.30% | **$69.41** |
| | | entered | 7.43% | 5.40% | 3.10% | $70.94 |
| 11-23 | $4K PUJ (4), $750 High Five (1) | separate | 10.77% | 10.77% | 2.47% | $103.95 |
| | | **joint** | **13.70%** | 11.47% | 2.80% | **$105.13** |
| | | entered | 10.93% | 10.93% | 3.10% | $106.20 |

**Difference, joint minus separate, on fresh nights:**

| Night | Joint coverage | Expected payout |
|---|---|---|
| 11-20 | +1.20 points | −$13.95 |
| 11-23 | +2.93 points | +$1.18 |
| Both nights | | −$12.77 |

**Why joint helps.** Filled apart on 11-23, the High Five's lineup added no nights the Pull Up Jumper set didn't already cover: joint coverage equals the PUJ's own 10.77%. Picked together, the High Five lineup goes where the PUJ set misses.

**Why it can cost.** On 11-20 the joint pick gave up $13.95 of expected payout in the PUJ for that coverage.

In-sample, on the nights picked from, joint led on coverage on both nights:

| Night | Joint coverage, joint | Joint coverage, separate | Expected payout, joint | Expected payout, separate |
|---|---|---|---|---|
| 11-20 | 9.73% | 8.57% | $78.23 | $92.84 |
| 11-23 | 16.17% | 13.73% | $111.26 | $114.76 |

**On the page (11-23 build, fresh nights):**

| Contest | Top-1% coverage | P(1st) |
|---|---|---|
| $4K Pull Up Jumper (4 lineups) | 11.5% | 2.9% |
| $750 High Five (1 lineup) | 2.8% | 0.9% |
| Together | 13.7% | |

### What this can and cannot say

- **Two nights.** The joint-vs-separate difference rests on 2 nights with two flagships. Both moved coverage the same way, and expected payout went opposite ways.
- **All in-sim.** The field, projections and correlations are the model the fill uses; a model error hits both ways alike.
- **Real results can't confirm it yet.** At a few percent a night, a dozen graded nights cannot confirm top-1% coverage or P(1st).

## On the 11-23 build

The build was loaded with the slate and simulated field as they stood at lock; the mirror's current file has dropped that slate's field. Fill all contests filled 79 of 79 entries (`fill_profiles_2026-11-24/fill_note.txt`):

- **flagships:** together, as above;
- **main contests and Dime Time:** each by its own Max ROI;
- **$50 Quarter Jukebox:** left 2 short by the caps, then topped up by Auto top-up.

## Files

- `dk.html`, `dk_sim.js`: `builder.score(k, ext)` joint coverage, `builder.cover1`, `pickJoint`.
- `tests/dk_page.js`: profiles, joint coverage, per-contest main fills, the qualifier's WTA and chalk field, the test toggle, the Swap order, the phone layout.
- `scripts/dk_eval.py fieldusers` → `analysis/cbb/dk/field_users.csv`.
- `scripts/dk_flagship_compare.py` and `.js` → `fill_profiles_2026-11-24/flagship_joint.jsonl`.
- `fill_profiles_2026-11-24/`:
  - `profiles_desktop.png` and `profiles_phone.png` (390px): the 11-23 build as entered;
  - `profiles_with_qualifier_illustration.png`: the same build with 2 entries placed in the night's $150 King of the Bracket qualifier, for illustration only; the build entered no qualifier;
  - `fill_note.txt`.
