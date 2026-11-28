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
