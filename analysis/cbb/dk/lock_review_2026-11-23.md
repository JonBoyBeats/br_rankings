# Monday lock review, 2026-11-23: the week's version

One review of projections, ownership and the sim on every graded slate (11-16 to 11-22). It is the coordinator's
11-23 request (the review agreed on 11-20). **Nothing changes until the operator approves.** An area that isn't ready
keeps its current settings. Every number here comes from a section file. Each section has its own tables, per night
and pooled with counts:

- projections: `review_projections_2026-11-23.md` (commit 37fc5ad)
- ownership: `review_ownership_2026-11-23.md` (15fca8c)
- the sim: `review_sim_2026-11-23.md` (e0a5765)
- the sim field: `field_study_2026-11-23.md` (13b3168)

**Sample.** 11 graded slates (11-16 to 11-22). Standings cover 9 of them, 45 contests in all. 7 nights have both a
build and standings. That is thin: a slate is the unit, so per-night direction counts for more than pooled p-values.

## The decisions for the operator

| # | Proposal | Area | Evidence (A2) | Default if not approved |
|---|---|---|---|---|
| 1 | **Close the projection gate under $6k** (ours alone under $6k; the 50/50 blend stays at $6k+) | Projections | Points MAE 5.630 -> 5.421, better on 10 of 11 slates; Vegas slope 1.50 -> 2.09; banks: top 10% better 7 / worse 2 nights, cash 6 / 3, pooled top 10% 9.2 -> 11.4%, cash 18.4 -> 22.0%. **Strict A2 flags it**: the shape lens (0.007 -> 0.020) and unexplained salary gaps (+10) get worse, and both favour the blend by construction | gate as is (w 0.50 every band) |
| 2 | **Ownership: mix toward even b = 0.04, plus "coming off a big game" x1.22** | Ownership | Held out by slate: log error 0.476 -> 0.428, MAE 4.50 -> 4.37, better on 9 of 9 slates. The under-5% band 2.08x -> 1.56x; the middle and top bands hold. Order is unchanged, and 0.9 players a contest cross the page's 10% / 20% lines. The big-game pattern is now **confirmed** on the watchlist (49 player-nights, 7 nights, x1.25, same direction 6 of 7). The field study changes no field (4), so this is the only fix on the table for the under-5% floor (the field study measures it at 1.90x Large, 1.75x Medium) | as is |
| 3 | **De-emphasize the tiers** on the page | Sim | Tiers: A > B > C on 3 of 7 nights, sign test p 1.00. The continuous sim value: positive with the real percentile on 6 of 7 nights, and the top tenth by value 6.8 points ahead | as is |
| 4 | **Pin the nightly refits for the week** (Q factor, zero-games factor, sit model: computed nightly, applied only at the Friday review) | The lock | Makes the locked version actually fixed: the zero-games factor moved 0.041 -> 0.057 this week on its own | refits keep applying nightly |
| 5 | **No field change this week**; start the nightly field-fit measure and its page line (display only), and test the no-punt field pool next | Sim field | No candidate passes A2 held out by night (the chosen Large setting beats the current on 2 of 9 nights; banks top 10% better 4 / worse 5, cash 4 / 4) | current FIELD_STYLES |

Not proposed (tested and rejected): B.3 shared-lineup credit (pooled percentile 48.5 -> 48.3; worse on the one night
with real sharing); a flattening exponent on ownership (fails A2: MAE 4.50 -> 4.53).

## 1. Projections

**LOCK** (each re-checked on all slates; numbers from the section):
- Steeper minutes STEEP 0.12. Before adoption, held-out steepening was better on 6 of 7 slates. Since adoption, extra steepening is 2 better / 2 worse, so 0.12 holds.
- Out hand-off OUT_REG_MIN 15: 4 of 5 team cases better; teammates' minutes MAE 4.738 -> 4.599 (68 teammate-nights).
- Questionable factor 0.333: beats no factor on 8 of 11 slates (34 player-nights).
- EvanMiya blend 0.35: MAE 5.551 vs 5.622 without, better on 6 of 11 slates (keep, on watch: a small edge).
- Zero-games cut 0.0571: beats no cut on 11 of 11 slates (59 player-slates).
- Sit model and flag (display): held-out Brier 0.0694 vs 0.268 for the current implied chance. 0 flags at lock so far (11-22's low chances were zero-games punts, out of the pool).

**CHANGE (operator):** decision 1, the gate under $6k.

**WATCH:**
- Our within-team shape is drifting steeper on the latest slates (top-2 vs recent +0.03 to +0.04 on 11-20 to 11-22).
- Cheap players under projection (bias -0.98 under $4k).
- Salary-gap misses: 43 of 71 unexplained.
- The EvanMiya edge.
- Sit-flag hits, once flags appear.

Misses by tag, largest first. Knowable before lock: salary-value spots, newcomers / few games, Q status. Not knowable
before lock: blowouts, late scratches, unexplained.

## 2. Ownership

**LOCK** the ownership model and the whole-number display.

The shape: real ÷ projected is 1.67x under 5% owned, 0.96x at 5-20%, 0.94x at 20%+. The miss is a **floor**
problem: players we project near zero get picked. It is not steepness (the #1-#2 gap is ours 13.0 vs real 12.8).

**CHANGE candidate:** decision 2, coordinated with the field (4).

**WATCH:**
- Medium's mix b (0.08 alone vs 0.04 shared).
- "Top-2 projected on the biggest favourite", emerging: x1.17, 18 player-nights.
- "The 5 highest salaries", watching: x0.88, 45 player-nights.
- Dead: top-2 in the highest-total game, blue bloods, round-number salaries, ranked teams, national TV games, salary drop of $300+.

By contest-size band:

| Band | Contests | Slates | Mix b |
|---|---|---|---|
| Large (300+) | 31 | 9 | 0.04 (range 0.02-0.04) |
| Medium (30-299) | 12 | 7 | 0.08 (range 0.04-0.10) |
| Small (under 30) | 2, both under 10 | 2 | too thin: shared setting |

Large and Medium overlap at 0.04, so one shared setting fits both.

## 3. The sim (all but the field)

| Item | Call | Evidence |
|---|---|---|
| Bank noise 0.35 | LOCK | Pooled over 9 nights, noise 1 / 0.5 / 0.35: top 10% 4.9 / 8.0 / 9.2%, cash 10.7 / 16.5 / 18.5%. 0.35 beats 1 on cash 9 of 9 nights. 0.25 untested (watch) |
| Bank size ~12,500 | LOCK | Half bank worse on real fills on both 11-20 builds |
| Cut: merit, floor 5 | LOCK | Beat equal share on real fills on both new nights. Watch: more entries short in the sim fill (11-20 early 11 vs 2) |
| Keep 2,000 / 10% / 2,000 nights | LOCK (not re-tested) | Kept beat cut on mean points 7 of 7 nights, top 10% 5 of 7 |
| Tiers | De-emphasize (decision 3), WATCH | See below |
| Variants of the top | LOCK | Kept variants beat the kept pool on cash 4 of 4 nights |
| Fill caps (Max ROI, 60% / 60% night, min unique 3, core 15%, max 3 contests) | LOCK, WATCH | No cap shown binding to bad effect; vs random kept fills 2 ahead / 2 behind / 1 even |
| Draw the 9 cells | WATCH (one night) | 11-20 main: leverage 0 > 0.1 > 0.2 on banked top 10% (11.4-12.4 / 7.5-8.8 / 4.2-5.0%); "under" makes little difference. If later nights agree, drop 0.2 from the default sweep |
| Template-5 spread | No data | No build saved after 11-21 is on file |
| B.3 shared credit | REJECT | Pooled no gain; worse on 11-20 early, the night with real sharing |

The tier de-emphasis (decision 3), concretely:
- "Variants of the top 15 by value" replaces "variants of tier A".
- The cut table's Tier A column becomes "Top 10%", and its red flag becomes a note.
- The builder sorts by value, with tiers muted.
- The one-screen list groups by value decile.
- The under-exposed line compares against the top tenth by value.
- Quick sim keeps its tiers: there they only say "within the noise".

## 4. The sim field

**LOCK** the current FIELD_STYLES, [0.2 w0 noise .10 / 0.8 w.5 .25]. No candidate passes A2.

**The B2 re-run** (9 nights, 45 contests; lower score is better):

| Setting | Score | Sim duplication (real 12.5%) | Owner's entries duplicated |
|---|---|---|---|
| Current | 1.630 (10th of 22) | 6.6% | 17 |
| Best [0.3 w.5 .08] | 1.329 | 13.2% | 35 |
| 4th [0.3 w0 .08] | 1.571 | 15.1% | 17 |

The best setting drifts outside the real range on 11-16 (duplication 15.7 vs 6.8%) and 11-18 (15.8 vs 10.8%).

**By contest-size band:**
- Large: 31 contests, 9 nights.
- Medium: 12 contests, 7 nights.
- Small: 2 contests, 2 nights (one under 10). Too thin to fit: read as "looks like Small" only.

**The gaps, real / current sim:**

| Measure | Large | Medium |
|---|---|---|
| Duplication | 13.4 / 8.0% | 12.3 / 3.8% |
| Entries playing a sub-$3.5k punt | 7.3 / 16.8% | 6.1 / 11.4% |
| Top-20 trio lift | 1.40 / 1.08 | 1.24 / 1.09 |
| Most common trio | 28.7 / 23.4% | 38.5 / 23.6% |

Medium fields are chalkier: real ownership-sum median 330, against 265 in Large.

**The fitted settings, scored on band means:**
- Large: 20% chalk on the DK average, noise .08, no punts. Score 2.874 vs 3.524 current.
- Medium: the same with 30% chalk. Score 3.122 vs 3.824.
- Only the chalk share differs by band. Weight, noise and the no-punt pool can be shared. The shared-core step didn't earn its place.

**Held out:**
- The chosen setting beats the current on 2 of 9 Large nights (mean 3.95 vs 3.77) and 4 of 7 Medium nights. The night-to-night noise is larger than the pooled gain.
- Banks: all 9 main contests are Large, so only the Large setting could be tested. Rule-free 2,000 cut to 200.
  - Top 10%: 11.1 -> 11.3%, better on 4 nights, worse on 5.
  - Cash: 23.8 -> 23.8%, better on 4, worse on 4.
  - Percentile: 51.5 -> 52.9, better on 8 of 9.
- The cut keeps the same lineups 70% of the time. There are no fewer chalky "falsely unique" lineups: 5.6% vs 5.8% of kept lineups appear in the real field.

**Proposed instead** (display and measurement only; decision 5):
- Measure the field fit nightly over the last 14 nights (field_fit.json), with a page line for the band you're entering, e.g. "Field fit: duplication 8% sim vs 13% real; punts 17% vs 7%".
- Refit weekly at the Friday review. A change is proposed only when it passes held out and the banks don't get worse.
- Test the no-punt field pool next. The punt gap (17% sim vs 7% real in Large) is the clearest single miss.

## 5. The lock and the Friday review

**The version.** On approval, one row in `versions.csv` tags the week's settings as a single version (`lock-2026-11-23`):
- the projection constants (STEEP, OUT_REG_MIN, MIYA_W, the gate w by band, the Q factor, the zero-games factor);
- the sit model;
- the ownership calibration;
- FIELD_STYLES;
- bank noise and bank size;
- the cut, variants and fill defaults;
- the tier display.

The builds and the grades carry the version, so the week is graded as one.

**Frozen between reviews:**
- Every model setting above, including the nightly refits (decision 4: computed and logged nightly, applied only at the Friday review).
- Still allowed: data refreshes (box scores, EvanMiya files, news, outs, lines), bug fixes and display-only changes.
- Separately gated tools the operator approves, such as the late-swap step: read-only until its live check.

**Graded weekly (Friday morning), over the week's slates and cumulatively:**
- Projections: the four lenses, MAE and bias by salary band and position; the misses by tag; each locked factor's refit beside its locked value.
- Ownership: the shape by band and contest-size band; the watchlist statuses.
- The sim: bank noise; cut vs kept; variants; fills vs entries vs random kept fills; Draw the 9 cells; the spread on and off; the tier and value signals.
- The field: simulated vs real duplication, salary left, stacks and ownership by band.
- The sit flag: hits; the zero-games group.

**What triggers a change proposal:**
- A setting, or a refit drifting from the locked value: an A2 pass. Held out by slate, better on at least 2 of 3 slates. No other lens worse beyond its noise. Same-seed banks better on more nights than worse, with the pooled rate up.
- A watchlist item: the confirmed rule (30+ player-nights, 5+ nights, 75% same direction, 25%+ off 1).
- A sim setting: the same direction on at least 5 graded nights.

Anything short of that stays on watch, and the version holds to the next Friday.
