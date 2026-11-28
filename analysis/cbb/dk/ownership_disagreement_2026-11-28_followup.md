# Ownership disagreement test: follow-up (2026-11-28)

This is analysis only, and it is **HELD**. It follows up [ownership_disagreement_2026-11-28.md](ownership_disagreement_2026-11-28.md), with the same data: 16 graded slates, 675 players at 5%+ on either side, d = real − our ownership, and the slate as the unit (mean ± SE over slates [90% bootstrap], slates positive).

Code and output: [od_followup.py / od_followup.out](ownership_disagreement_2026-11-28/). Tags follow the tiered bar in [process.md](process.md) (rule 5). **The operator's hold stands. Nothing here ships without the operator's go.**

## (a) Where does "field right" turn into "we're right"?

The test, per tier and per slate:
- **loved** (the field 10+ over us): their actual − projection, minus the slate's within-10 players';
- **faded** (10+ under): within-10 minus their actual − projection.

Positive means the field was right. "Pooled" combines both directions.

| Tier | n | Loved: n, field right by | Faded: n, field right by | Pooled field-right | r(d, act − proj) |
|---|---|---|---|---|---|
| salary < $4k | 34 | 5, +7.60 ± 6.73 | 3, +9.39 ± 8.93 | +8.27 ± 4.98 (8), +5 | (2 slates) |
| $4–5k | 122 | 19, +4.31 ± 2.82 | 24, +2.86 ± 2.42 | **+3.58 ± 1.83 (24), +16** | +0.14 ± 0.13, +10 of 15 |
| $5–6k | 168 | 14, +6.40 ± 2.14 | 11, +4.81 ± 1.79 | **+5.81 ± 1.47 (16), +13** | +0.17 ± 0.10, +11 |
| $6–7k | 139 | 15, +1.43 ± 2.62 | 9, +4.92 ± 3.97 | +2.52 ± 2.15 (16), +8 | +0.14 ± 0.10, +11 |
| $7–8k | 103 | 10, −0.82 ± 4.10 | 8, **−7.78 ± 3.22** | **−4.30 ± 2.69 (14), +5** | +0.01 ± 0.11 |
| $8k+ | 109 | 11, +5.03 ± 3.33 | 9, −2.66 ± 3.06 | +1.95 ± 2.48 (15), +7 | +0.10 ± 0.10 |
| proj 10–15 | 55 | 8, +11.16 ± 4.75 | 3, −6.67 ± 4.56 | +5.21 ± 4.47 (9), +6 | +0.36 ± 0.18 |
| proj 15–20 | 149 | 17, +3.62 ± 3.54 | 20, +4.32 ± 2.86 | **+4.01 ± 2.18 (23), +15** | +0.13 ± 0.12 |
| proj 20–25 | 226 | 18, +2.91 ± 2.31 | 18, **+8.88 ± 2.20** | **+5.90 ± 1.70 (20), +16** | +0.16 ± 0.09, +10 |
| proj 25–30 | 151 | 19, −0.31 ± 2.72 | 12, −4.93 ± 3.58 | −2.07 ± 2.17 (21), +8 | +0.01 ± 0.09 |
| proj 30+ | 87 | 11, +1.46 ± 3.04 | 11, **−4.30 ± 2.15** | −1.10 ± 2.03 (18), +7 | +0.09 ± 0.10 |

**The crossover: a step, not a gradient.** It sits at about **$7k / a 25-point projection**.
- **Below it, the field is right in both directions.** It's clearest at $4–6k and at projections of 15–25 (+3.6 to +5.9, positive on about two-thirds or more of slate-cells). It weakens at $6–7k (+2.5 ± 2.2, 8 of 16).
- **Above it, the field's *fades* are wrong.** Players the field faded beat our projection at $7–8k (by 7.8 ± 3.2) and at 30+ (by 4.3 ± 2.2).
- **The field's *loves* above it are mixed.** $8k+ loved players still beat our projection by +5.0 ± 3.3, but $7–8k loved players by −0.8 ± 4.1.
- So above the step, "we're right" holds only where we like a star more than the field does. It doesn't hold where the field likes one more than we do.
- Cells are 3–24 players. Each row is directional on its own; the step shows in the pattern across rows.

## (b) The operator's candidate: lean in above the crossover, cap fades of field-loved cheap / rotation players

**Pre-lock form.** Real ownership isn't known at lock, so each player's d is replaced by **d̂**: the leave-one-slate-out prediction of d from the four signals that predicted it in the main test (our projected value, last game's points, the checks score, last game's minutes against ours). It is fitted on the *other* slates only.

Each kept lineup scores:
- **+ d̂** summed over its players under $7k (holding the field's likely-loved cheap players);
- **− d̂** summed over its $7k+ players (leaning into our own disagreements).

The candidate keeps **the top half of the kept pool** by that score. Today's kept pool is the baseline. There is no free parameter beyond the $7k step, which was read off (a) before (b) was run. It is scored on the same nights' 100+ entry contests: mean real finish percentile, and mean payout per lineup per contest from each contest's table. That gives 14 builds.

| Candidate − all kept (14 slates) | Finish percentile | $ per lineup per contest |
|---|---|---|
| **candidate (pre-lock, d̂)** | **−1.16 ± 0.89, ahead on 4 of 14** | +0.27 ± 0.25, ahead on 7 of 14 |
| oracle (real d, hindsight) | +1.45 ± 1.14, ahead on 9 of 14 | −0.36 ± 0.48, ahead on 9 of 14 |
| the candidate's bottom half | +1.16 ± 0.89, ahead on 10 of 14 | −0.27 ± 0.25 |

- **The pre-lock candidate points the wrong way on finish** (4 of 14 ahead). Its own bottom half did better than its top half: −2.33 ± 1.78 between them. On dollars it is a coin flip (7 of 14).
- **Even with hindsight, the ceiling is small.** The oracle is ahead on 9 of 14 (64%) on finish but negative in mean dollars. The pre-lock signals can't recover the disagreement's direction at lineup level: they predict d per player (main test, r ~0.1), and summed over 8 players that's too weak to rank lineups.
- **Effect on the other arms:**
  - *pool:* its headline (kept − bank finish percentile) would move by the candidate's −1.16;
  - *fill:* unchanged in method, but it draws from the smaller pool;
  - *projection, ownership, field:* untouched.

**Tag: NOISE.** The sign is wrong on 10 of 14 slates for the deployable version, and the dollars split 7–7. It goes to the watch list, not to PROVISIONAL.
- **What would move it up:** a pre-lock predictor of d stronger than r ~0.1. The main test found none.
- The tier finding in (a) stands on its own as **DIRECTIONAL (finding)**: the step at about $7k / 25 points, in the right direction across rows, with a plausible mechanism (the field reads cheap players' roles better than we do, and over-fades stars). But it has no deployable form yet.
