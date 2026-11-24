# Caps backtest (2026-11-24)

The operator's question, through the coordinator, was whether the caps help or just cost money, given that the fill already scores each lineup by what it adds to the set. This is analysis only. Nothing changes until the operator decides.

**Method.** `scripts/dk_caps_backtest.js` takes each graded night with a saved build. It refills that night's real contests from the build's final pool the way the page's Fill all contests does:

- the largest stake first;
- `DKSim.pick` on each contest's seeded nights, at 1,000 nights per contest;
- the night cap enforced as each player's Max% from what earlier contests used;
- each lineup in at most 3 contests.

It then scores every set on real points against each contest's real entries. The owner's own entries are left out and ties are split.

There are **7 nights**: 11-16, 11-17, 11-18, 11-19 early and main, 11-20 early and main. That is 33 contests and 381 seats. Every filled entry had standings.

Each run used the current gate.json, or the build's gate where the build saved one. Per-night output is in `caps_backtest_2026-11-24/`.

**Settings:**

| Setting | Contest exposure | Night cap | Min unique | Max core | Contests per lineup | Stranded seats |
|---|---|---|---|---|---|---|
| a | 60% | 60% | 3 | 15% | 3 | Left empty |
| b | 80% | 80% | 3 | 15% | 3 | Left empty |
| c | Off | Off | 3 | Off | 3 | Left empty |
| d | Off | Off | 1 | Off | Any | Left empty |
| e | 60% | 60% | 3 | 15% | 3 | Topped up |

In setting e, each contest's stranded seats are topped up by added value with the caps off, keeping the set so far. That is close to "Add best", which picks the lineup breaking the caps least.

## Per night

The cells are real net $ / ROI / entries at the real top-1% line / entries at the real top-10% line / largest single-player share of the filled entries / stranded seats.

| Night | Contests | Seats | a | b | c | d | e |
|---|---|---|---|---|---|---|---|
| 11-16 | 4 | 46 | −22.50 / −97% / 0 / 0 / 82% / **13** | −25.80 / −96% / 0 / 0 / 78% / 0 | −23.50 / −87% / 0 / 1 / 89% / 0 | −25.80 / −96% / 0 / 0 / 94% / 0 | −25.80 / −96% / 0 / 0 / 85% / 0 |
| 11-17 | 4 | 67 | −14.90 / −80% / 0 / 2 / 60% / 0 | −16.00 / −86% / 0 / 1 / 78% / 0 | −16.00 / −86% / 0 / 1 / 82% / 0 | −16.00 / −86% / 0 / 1 / 84% / 0 | −14.90 / −80% / 0 / 2 / 60% / 0 |
| 11-18 | 5 | 54 | +127.10 / 363% / 3 / 4 / 59% / 0 | +130.05 / 372% / 3 / 5 / 80% / 0 | +131.00 / 374% / 3 / 6 / 98% / 0 | +131.70 / 376% / 3 / 6 / 98% / 0 | +127.10 / 363% / 3 / 4 / 59% / 0 |
| 11-19 early | 4 | 26 | −1.10 / −4% / 0 / 3 / 62% / 2 | −4.30 / −14% / 0 / 3 / 77% / 0 | −5.00 / −16% / 0 / 1 / 100% / 0 | −0.80 / −3% / 0 / 2 / 100% / 0 | −1.50 / −5% / 0 / 4 / 65% / 0 |
| 11-19 | 5 | 68 | −59.55 / −83% / 0 / 6 / 71% / **12** | −68.90 / −90% / 0 / 4 / 79% / 0 | −68.80 / −89% / 0 / 3 / 87% / 0 | −71.20 / −93% / 0 / 2 / 97% / 0 | −64.95 / −84% / 0 / 5 / 78% / 0 |
| 11-20 early | 5 | 56 | +100.50 / 174% / 5 / 17 / 61% / 2 | +106.00 / 182% / 5 / 23 / 79% / 0 | +106.95 / 184% / 5 / 24 / 89% / 0 | +59.89 / 103% / 7 / 26 / 93% / 0 | +100.70 / 173% / 5 / 18 / 61% / 0 |
| 11-20 | 5 | 64 | +10.75 / 15% / 4 / 8 / 76% / **14** | **+98.10 / 128%** / 5 / 15 / 81% / 1 | +19.80 / 26% / 3 / 12 / 100% / 0 | +20.19 / 26% / 3 / 12 / 100% / 0 | +12.53 / 16% / 4 / 12 / 81% / 0 |

A note on setting a's largest share: it can pass 60% because it is a share of the entries actually filled, and a strands seats.

## Pooled (7 nights)

| Setting | Fees | Real $ | Net | ROI | Top 1% | Top 10% | Stranded | Nights better / worse than a |
|---|---|---|---|---|---|---|---|---|
| a, current | 305.80 | 446.10 | +140.30 | +45.9% | 12 | 40 | **43 of 381** | — |
| b, 80/80 | 323.65 | 542.80 | **+219.15** | **+67.7%** | 13 | 51 | 1 | 3 / 4 |
| c, no exposure caps | 323.90 | 468.35 | +144.45 | +44.6% | 11 | 48 | 0 | 3 / 4 |
| d, no caps | 323.90 | 421.88 | +97.98 | +30.3% | 13 | 49 | 0 | 3 / 4 |
| e, a plus top-up | 323.90 | 457.08 | +133.18 | +41.1% | 12 | 45 | 0 | 2 / 3 |

**The looser settings' gains come from one night.**

- **b's lead is 11-20.** b beats e by +$85.97 over the 7 nights, and +$85.57 of that is 11-20. Without 11-20, b against e is +$0.40.
- **c is level with e.** It is +$11.27 over all 7 nights and +$4.00 without 11-20.
- **d is worse.** It trails e by −$35.20 over all 7 nights and by −$42.86 without 11-20. Most of that is 11-20 early, at −$40.61.
- **Without 11-20, the ROIs are close:** a +55.0%, e +48.9%, b +49.0%, c +50.5%, d +31.5%.

Seven nights is thin. At these stakes, one night's big hit decides the totals.

**What the caps do and don't do:**

- **They don't lose money.** No looser setting beats the current caps outside one night.
- **No caps at all loses money.** Setting d is the worst, by about $35–43.
- **The cost is stranded seats.** Under the current caps, 43 of 381 seats (11%) were left empty, mostly on 11-16, 11-19 main and 11-20 main. Topped up (e), those seats earn about what the rest do. Raised to 80/80 (b), only 1 seat strands, with the same results on 6 of 7 nights.

## Is the model's overconcentration real?

Setting d, the fill left alone, shows where the model wants to concentrate. For each player, take his share of d's entries and compare it with his real DK points less his projection. The question is whether the players the model piles into beat what we projected.

| Share of d's entries | Player-nights | Beat projection | Mean actual − projection | Mean field own | Real pts per $1K |
|---|---|---|---|---|---|
| 40%+ | 45 | 42% | −0.72 | 44.6% | 4.22 |
| 10–40% | 93 | 44% | −1.71 | 21.3% | 3.70 |
| under 10% | 132 | 40% | −0.16 | 7.8% | 3.43 |

The Spearman correlation of share against (actual − projection), night by night, was:

| 11-16 | 11-17 | 11-18 | 11-19 early | 11-19 | 11-20 early | 11-20 | Mean |
|---|---|---|---|---|---|---|---|
| 0.11 | −0.22 | 0.03 | 0.04 | −0.10 | 0.17 | 0.01 | **0.01** |

It was positive on 5 of 7 nights.

**Reading:**

- **The heavy players score more per dollar** (4.22 against 3.43 points per $1K), but only because they were projected higher.
- **Against their own projections they do no better.** 42% beat it, against 40–44% for everyone else, and the rank correlation is zero.
- **So the concentration carries no information beyond the projection.** It is the projection's top values being piled into. There's no sign it's an edge, which is the case for a cap.
- **It's no worse either.** The caps don't cost real money (above), so they cost little.

## Proposal for the operator

1. **Keep caps; don't drop them.** No caps (d) was the worst setting, and the model's concentration shows no edge over its projection.
2. **Stop stranding seats.** Either:
   - (i) **raise the contest and night caps to 80%** (b), which strands 1 seat in 381 and matched the current caps on 6 of 7 nights, plus 11-20's upside; or
   - (ii) **keep 60/60 and top up stranded seats automatically** (e, the "Add best" step done for you).

   On these 7 nights (i) did better, but only because of 11-20. Without that night, (i) and (ii) are level.
3. **Re-run when there are 15+ nights**, since 11-23 and later builds add to it. Decide between (i) and (ii) then, unless the operator prefers simpler and picks (i) now.
