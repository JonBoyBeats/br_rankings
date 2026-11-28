# Tight cores + fragile cap, mains only (2026-11-28)

Analysis only. The HOLD stands; flagships stay on fill proposal 1 and are not touched; nothing is added to the
green-core shadow log. Contest types from `scripts/dk_contest_type.py` (main only).

## Pre-registration (committed before any replay was run)

Everything in this section was written and committed before any result was computed. Results go in a later section
below; this section is not edited afterwards.

### Fragile A (primary)

The ownership-disagreement study (`ownership_disagreement_2026-11-28.md`, follow-up, `ownership_tiered_2026-11-28.md`)
defines its disagreement `d = real ownership − our ownership` and its 10-point buckets with **hindsight** (real)
ownership, so `d` itself cannot be computed at lock. The study's own pre-lock finding (its finding 4, `pval`) is
the proxy used here, unchanged: *our projected value (fp per $1k) is the one pre-lock signal that predicts both
where the field disagrees and where it is right (11 of 16 held out); our biggest projected values run hot.* The
crossover (follow-up) puts the "field was right" band under **$7k / 25 projected points**.

**Fragile A, per slate, computable at lock:**
- the player is on the slate, not `Out` at lock;
- salary **< $7,000** and our lock-time projection `fp_dk` **≥ 10 and < 25** (the study's rotation band, under the crossover);
- his projected value `fp_dk / (salary / 1000)` is in the **top quartile** (≥ the 75th percentile, ties included) of
  projected value among the slate's players meeting the two lines above.

`fp_dk`, salary and status are the lock-time values in the night record (`analysis/cbb/dk/<day>_<dg>.csv`). The
quartile is the one fixed cut (no tuning; the same quartile convention as Fragile B).

### Fragile B (secondary, context only)

On nights with external source files in battle-royale-research `data/dk/cbb/sources/` (Gajewski, RotoWire): our
`fp_dk` exceeds **every available source** (both, or the one present) by at least the slate's **75th percentile of
(ours − source)** over players both project at 10+ (computed per source; the player must clear each source's own
cut). Only nights with source files count, and `n` nights is reported. **Known before running:** the only banked
source files are for 2026-11-27 (157545 / 157547), and 11-27 had no main contest, so B is expected to have **n = 0
graded main nights** today; it is registered so that it runs unchanged when source nights with mains accumulate.

### Nights

Every main contest (`contest_type == "main"`) of every saved build that has board values, a lock-time simulated
field, a graded night record and the contest's standings on hand: the cc44bc8 / 69e2358 nights (7 slates with mains,
11-20 → 11-26) plus any later night that meets the same conditions when this runs.

### Fills (each fills every seat; graded on the real standings)

The page's pick (`DKSim.pick`, Max ROI for mains) on the simulated field at lock, the machinery of
`scripts/dk_core_shadow.js` (cc44bc8), from the build's kept pool. "Today" uses the brief's main profile for every
night (not each build's saved settings, which vary): **exposure 60%, min unique 3, max core 15%**.

1. **TODAY**: the whole kept pool, 60 / 3 / 15.
2. **FRAGILE CAP**: as TODAY, plus a per-player exposure cap of **25%** on each fragile player (the page's player Max%,
   `state.cap`), 60% on everyone else.
3. **TIGHT CORES**: candidates are the kept lineups whose core (the 3 highest salaries) is among the **top 3 cores**,
   ranked as cc44bc8: cores with 2+ green players at lock first (by the best board value of any of their lineups),
   then the other cores by the same value, until 3 cores; **max core 40%, min unique 1, exposure 60%**.
4. **TIGHT CORES + FRAGILE CAP**: fill 3 plus the 25% fragile cap.

Run 2 and 4 under A, and again under B on B's nights.

**Fill every seat:** if a fill's restricted set cannot fill the contest, it is topped up from the whole kept pool
with the same fill's settings (the picks so far kept, `preset`), and the number topped up is reported. Greens are
the checks green flag recomputed at lock (`dk_core_shadow.greens`). Same simulated nights and seeds for every fill.

### Comparison and decision rule

Per fill, against TODAY on the same contests, one value per slate (seat-weighted over its main contests), mean ± SE
over slates:
- finish percentile (mean over the fill's lineups), ± SE, slates ahead k of n;
- dollars per lineup, ± SE, k of n;
- net % of fees over the whole sample;
- seats filled (and topped up), max player exposure, distinct cores.

Rule-5 tag (process.md), on **both** finish percentile and dollars:
- **PROVEN**: held out (no fitting here; every setting is fixed above), gain > 2×SE and ahead on most slates, on both.
- **DIRECTIONAL**: right direction on ~60–65%+ of slates on both, with a sensible mechanism.
- **NOISE**: otherwise.

**Fragile A sanity check** (out of sample: its rule was fixed in the study before these nights' standings were
looked at here): per night, players flagged; their mean actual − projection and beat-projection rate, against the
other players in the same band (salary < $7k, fp_dk 10–25).

If any fill tags DIRECTIONAL or better, a proposal to add it as a line in the green-core shadow log (counted on new
main nights toward 7 of 10, both $ and finish pct ahead) is written below, marked *awaiting coordinator
confirmation*, and not implemented.

## Results (run after the pre-registration commit 877b1ee)

`tight_cores_fragile_2026-11-28/tcf.py` (driver) and `tcf.js` (`scripts/dk_core_shadow.js` with per-variant caps and
the top-up); output `tcf.out`, rows `tcf_rows.json`, summary `tcf_summary.json`. 500 simulated nights per contest.

**Nights:** 7 slates with main contests and everything needed (11-20 157013 / 157015, 11-23, 11-24 157024 / 157026,
11-25 157293 / 157295), 25 main contests, 429 seats. 11-26 and 11-27 have no main contest with standings on hand;
builds before 11-20 have no board values. **Fragile B: n = 0 nights** (as expected at registration: the only source
files are 11-27, which had no main contest).

### Fills against TODAY (per slate, seat-weighted; mean ± SE over 7 slates)

| Fill | Finish pct vs today | $ / lineup vs today | Net % of fees | Seats filled (topped up) | Max player expo | Distinct cores / contest | Tag |
|---|---|---|---|---|---|---|---|
| 1 TODAY (60 / 3 / 15) | (base) | (base) | +95.2% | 416 / 429 (0) | 62% | 14.5 | |
| 2 FRAGILE CAP (A) | +1.82 ± 3.16, 3 of 7 | −0.06 ± 0.30, 3 of 7 | +90.4% | 353 / 429 (0) | 73% | 12.0 | **NOISE** |
| 3 TIGHT CORES | +3.92 ± 2.02, 5 of 7 | −0.19 ± 0.33, 3 of 7 | +44.5% | 393 / 429 (136) | 65% | 7.4 | **NOISE** |
| 4 TIGHT CORES + FRAGILE CAP (A) | +4.88 ± 2.88, 6 of 7 | −0.13 ± 0.35, 4 of 7 | +52.8% | 342 / 429 (89) | 75% | 5.9 | **NOISE** (finish alone would be directional; $ is not) |
| 2 / 4 under Fragile B | n = 0 slates | | | | | | not run |

Per slate (finish pct / $ per lineup) is in `tcf.out`.

**Reading:**
- **No fill clears the pre-registered rule on both measures.** Tight cores lift finish percentile (+3.9, 5 of 7;
  with the fragile cap +4.9, 6 of 7), consistent with cc44bc8, but dollars per lineup are flat to slightly negative
  (3–4 of 7) and net % of fees roughly halves (+95% → +45–53%), because the tighter sets missed the one or two cashes
  that carry today's total.
- **The fragile cap alone does nothing** (+1.8 ± 3.2, 3 of 7; $ 3 of 7).
- **"Fill every seat" was not achieved, even with the top-up.** The caps bind on the whole pool too (60% exposure,
  min unique, the 25% fragile cap), so seats go unfilled: today 416 of 429; fragile cap 353; tight 393 (136 of them
  topped up from outside the 3 cores); tight + fragile 342 (89 topped up). Per-lineup comparisons are still like for
  like, but net % of fees counts only filled seats, and a real version would need the caps relaxed to fill.
- **Max exposure above 60%** comes from the page's small-contest round-up (≤ 5 entries round the limit up).

### Fragile A sanity check (out of sample)

| Group (salary < $7k, fp_dk 10–25, not Out) | Per night | Actual − projection | Beat-projection rate |
|---|---|---|---|
| Fragile A (top quartile of projected value) | 14.1 | −1.33 ± 0.70 | 0.360 ± 0.049 |
| Other players in the band | 40.7 | −0.75 ± 0.45 | 0.415 ± 0.034 |
| **Fragile − other** | | **−0.59 ± 0.87, fragile worse on 4 of 7 nights** | |

Fragile A points the expected way (they fall further short of projection and beat it less often) but weakly, inside
one SE and on 4 of 7 nights. That matches the source study (r ≈ −0.12): the signal is real on average but too weak
to cap individual players with, which is why the fragile cap moves nothing.

### Verdict and proposal

- Fragile cap (A): **NOISE**. Tight cores: **NOISE** under the both-measures rule (finish-only directional, $ flat).
  Tight cores + fragile cap: **NOISE** (finish 6 of 7, $ 4 of 7). Fragile B: not testable yet (n = 0).
- **No proposal.** Nothing tags DIRECTIONAL or better on both $ and finish, so nothing is proposed for the green-core
  shadow log. The existing shadow (top-5 cores, green top-5) already tracks the tight-core idea on new main nights;
  the fragile cap adds nothing to it on this evidence.
- Watch: Fragile B re-runs unchanged once source files exist on main nights (Gajewski / RotoWire on the mains-only week).
