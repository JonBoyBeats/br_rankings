# DraftKings CBB: minutes tiers (2026-11-28)

The operator approved this study. It is analysis only, and **the HOLD stands: nothing ships without the operator's go.** Every finding carries a tag from the tiered bar ([process.md](process.md), rule 5).

- **Code and output:** [minutes_tiers_2026-11-28/mt.py, mt.out](minutes_tiers_2026-11-28/).
- **Rows:** 2,837 graded player-games on 18 slates. 1,128 of them are in the ROTATION band (we projected 10–25 DK points). That band's minutes MAE is the headline.
- **LIVE** is the minutes at lock, **PREVIOUS** is `min_old` and **RULER** is `ruler_min`.
- **The constraint that shapes everything:** PREVIOUS is logged on only **4 slates** (11-25 and 11-26; the ruler on 3 of them). Every rebuild-against-previous number and every blend fit uses those 4. 11-27 isn't graded yet.

**Ordinary vs fringe, as known before lock:**
- **Fringe** is any one of these:
  - blowout-likely: |spread| ≥ 15;
  - ≤ 2 games played;
  - a rotation teammate (15+ mpg) Out at lock;
  - DNP risk: Questionable, or P(play) < 0.9.
- **Ordinary** is the rest: **70% of rotation rows.**
- OT can't be flagged before lock in a usable way. A spread-based "OT-sensitive" flag (|spread| ≤ 2.5) caught 36% of rotation rows, so close games stay ordinary, as the operator defined it.

## Verdict

**Yes, the minutes model can be made better in ordinary games. The quickest way is to stop using the rebuild there.**
- **On the 4 slates both were logged, the rebuild loses only on ordinary rows:**
  - ordinary: rotation-minutes MAE **+0.32 ± 0.15 worse than PREVIOUS, worse on 4 of 4**;
  - fringe: level, −0.02 ± 0.19.
- **The loss is concentrated at the top.** Players we project 30+ minutes in ordinary games: the rebuild is **+1.74 ± 0.37 worse (4 of 4)** than PREVIOUS, and +1.77 ± 0.62 worse than the ruler.
- **20–30 minutes:** +0.48 ± 0.27 worse (3 of 4). **10–20:** level (+0.01 ± 0.04).
- **On these 4 slates the rebuild doesn't beat PREVIOUS anywhere in the rotation band.** Its fringe advantage, seen after the fact in the Friday review (DNPs, blowouts), is level when fringe is defined before lock.

**Best candidate: (a) the situation switch.**
- **The rule:** PREVIOUS (blended) on ordinary rows, the rebuild on fringe rows, with the blend weight fitted per tier on the other slates. The fitted weight on the rebuild is 0–0.2, so in practice ordinary rows go back to PREVIOUS.
- **Held out:** **+0.24 ± 0.11 on the rotation headline, ahead on 4 of 4.** Ordinary rows gain +0.30 ± 0.14. Fringe rows are untouched (0.00) by construction.
- **Tag: PROVEN by the letter** (4 of 4, +0.24 against 2×SE 0.22), **treated as DIRECTIONAL** until the projection arm's 7-slate review.
  - Four slates is the thinnest sample the bar allows, and the margin over 2×SE is 0.02.
  - It's cheap to undo, and the mechanism is plain: the rebuild's minutes for regulars in ordinary games are worse.
- **The arm is settling 4 of 7 and the HOLD stands.** Proposed for the operator's review only.

---

## 1. By projected-minutes tier

Every graded player, LIVE minutes at lock. MAE and bias are per slate, then mean ± SE over slates. Bias is actual − LIVE. "Off 5+" is the share of players missed by 5+ minutes. LIVE − X is paired on the rebuild-era slates; negative means the rebuild is better.

| Tier | Situation | Rows | LIVE MAE | Bias | Off 5+ | LIVE − PREV (4) | LIVE − RULER (3) |
|---|---|---|---|---|---|---|---|
| 30+ | all | 212 | 5.89 ± 0.58 | −0.99 ± 0.88 | 0.40 | **+1.37 ± 0.26, 4 of 4** | +1.31 ± 0.40, 3 of 3 |
| 30+ | ordinary | 168 | 4.49 ± 0.37 | +0.86 ± 0.81 | 0.39 | **+1.74 ± 0.37, 4 of 4** | +1.77 ± 0.62, 3 of 3 |
| 30+ | fringe | 44 | 9.97 ± 1.95 | −7.77 ± 2.47 | 0.37 | −0.52 ± 0.64 (3) | −0.25 ± 0.58 |
| 20–30 | all | 764 | 7.10 ± 0.22 | +0.18 ± 0.57 | 0.58 | +0.41 ± 0.20, 3 of 4 | +0.33 ± 0.17 |
| 20–30 | ordinary | 558 | 5.87 ± 0.31 | **+1.74 ± 0.48 (15 of 17)** | 0.55 | +0.48 ± 0.27, 3 of 4 | +0.39 ± 0.23 |
| 20–30 | fringe | 206 | 11.42 ± 0.98 | −5.24 ± 1.57 | 0.73 | +0.15 ± 0.19 | +0.11 ± 0.30 |
| 10–20 | all | 708 | 7.10 ± 0.21 | −0.04 ± 0.43 | 0.59 | −0.02 ± 0.06 | +0.10 ± 0.03 |
| 10–20 | ordinary | 453 | 6.18 ± 0.25 | **+1.49 ± 0.49 (13 of 17)** | 0.56 | +0.01 ± 0.04 | +0.12 ± 0.04 |
| 10–20 | fringe | 255 | 9.54 ± 0.64 | −4.37 ± 1.21 | 0.70 | −0.11 ± 0.20 | +0.04 ± 0.06 |
| < 10 | all | 1,153 | 3.27 ± 0.12 | −0.92 ± 0.29 | 0.22 | +0.55 ± 0.16, 4 of 4 | +0.93 ± 0.12 |
| < 10 | ordinary | 218 | 4.83 ± 0.46 | +0.69 ± 0.84 | 0.41 | −0.69 ± 0.67 | −0.56 ± 1.38 |
| < 10 | fringe | 935 | 2.93 ± 0.16 | −1.36 ± 0.30 | 0.18 | +0.60 ± 0.15, 4 of 4 | +0.96 ± 0.10 |

Rotation band (the headline), rebuild era:

| | Rows | LIVE | PREV | LIVE − PREV |
|---|---|---|---|---|
| all | 318 | 7.77 ± 0.67 | 7.52 ± 0.74 | +0.25 ± 0.13, 4 of 4 |
| **ordinary** | 259 | 6.59 ± 0.75 | 6.27 ± 0.82 | **+0.32 ± 0.15, 4 of 4** |
| fringe | 59 | 13.22 ± 1.15 | 13.24 ± 1.12 | −0.02 ± 0.19, 1 of 4 |

**Findings:**
- **The rebuild loses on ordinary regulars, worst at 30+ projected minutes. DIRECTIONAL.** It is 4 of 4 slates at both 30+ and the rotation headline, and it fits the Friday review (played, full roster, 3+ games). The sample is 4 slates.
- **In ordinary games we under-project minutes by 1.5–1.7 at 10–30 projected minutes, across all 18 slates.** Fringe games are over-projected by 4–8 minutes. These are opposite-sign biases that a single model averages away.
  - The ordinary bias is the stronger signal: 15 of 17 slates at 20–30, and 13 of 17 at 10–20.
  - **DIRECTIONAL (finding).** It's measured on each slate's live minutes across model versions, so it isn't a fix yet.

## 2. Teams and coaches

Rotation-band minutes MAE per team over all 18 slates (each slate's live minutes), shrunk toward the pooled MAE of 7.02 with 10 pseudo-rows. Volatility is measured before lock from the ESPN box cache:
- **vol:** the mean game-to-game SD of the team's regulars' minutes;
- **churn:** the share of consecutive games whose top 8 changed by 2+ players.

That gives 81 teams with 6+ rotation rows.

| Best | Rows | MAE (shrunk) | Bias | vol | churn |
|---|---|---|---|---|---|
| BAMA | 17 | 2.75 (4.33) | +0.65 | 5.64 | 0.55 |
| BAY | 12 | 3.87 (5.30) | +1.15 | 3.61 | 0.00 |
| JAC | 7 | 2.94 (5.34) | −2.00 | 4.25 | 0.50 |
| VT | 12 | 3.95 (5.34) | −1.55 | 5.50 | 0.40 |
| PUR | 11 | 3.85 (5.36) | +1.58 | 7.18 | 0.00 |

| Worst | Rows | MAE (shrunk) | Bias | vol | churn |
|---|---|---|---|---|---|
| SMU | 13 | 12.35 (10.03) | +0.42 | 5.33 | 0.00 |
| CLEM | 19 | 11.29 (9.82) | −4.72 | 3.98 | 0.00 |
| PROV | 18 | 10.60 (9.32) | −1.97 | 8.13 | 0.73 |
| UF | 11 | 11.29 (9.26) | +0.02 | 7.03 | 0.00 |
| MIA | 15 | 10.75 (9.25) | −6.04 | 5.03 | 0.00 |
| UNLV | 18 | 10.27 (9.11) | −7.02 | 4.48 | 0.00 |
| UCONN | 13 | 10.60 (9.04) | −5.46 | 4.74 | 0.00 |

The rest are in `mt.out`.

**Is it the swingy teams? Partly.**
- **Volatility before lock predicts the miss.** The per-slate r between team volatility and the player's absolute miss is **+0.115 ± 0.043, positive on 14 of 18**. High-volatility teams (above the slate median) miss by +0.66 ± 0.35 more (10 of 18).
- **Churn (top-8 turnover) doesn't:** −0.007 ± 0.034.
- **Team skill persistence is weak.** A team's miss on the first 9 slates against the last 9 gives r 0.26 (25 teams with 3+ rows in each half). Team volatility against the second-half miss gives r 0.09.
- **Several of the worst teams are bad on bias, not volatility.** UNLV −7.0, MIA −6.0, UCONN −5.5 and CLEM −4.7 are over-projected, with low churn. That's a role call we keep getting wrong (minutes we give that the coach doesn't), not swinginess.
- **Tags:**
  - volatility as a predictor of miss size: **DIRECTIONAL** (14 of 18, a mechanism, measurable before lock);
  - team-level skill and bias: **NOISE** for now (r 0.26 persistence, small samples);
  - coach-level effects: can't be separated from team effects with one season of team rows.

## 3. Candidate fixes

Each is held out by slate on the rotation-minutes headline. The gain is LIVE MAE − candidate MAE, so positive is better.

| Candidate | All rotation rows | Ordinary | Fringe | Tag |
|---|---|---|---|---|
| reference: PREVIOUS outright | +0.25 ± 0.13, 4 of 4 | +0.32 ± 0.15, 4 of 4 | −0.02 ± 0.19, 1 of 4 | (2×SE 0.26: just short) |
| (b0) one blend weight on all rows | +0.24 ± 0.12, 4 of 4 | +0.31 ± 0.15 | −0.02 ± 0.17 | DIRECTIONAL |
| **(a) situation switch** (rebuild on fringe; on ordinary, a blend with the weight per tier) | **+0.24 ± 0.11, 4 of 4** | **+0.30 ± 0.14, 4 of 4** | **0.00 (untouched)** | **PROVEN by the letter (thin), treated as DIRECTIONAL** |
| (b) tier blend (weight per projected-minutes tier) | +0.25 ± 0.12, 4 of 4 | +0.32 ± 0.15, 4 of 4 | −0.02 ± 0.12, 1 of 4 | DIRECTIONAL (gain = 2×SE 0.24, not above it) |
| (c) volatility shrinkage toward season mpg, high-volatility teams, rebuild era | +0.01 ± 0.07, 2 of 4 | +0.05 ± 0.08 | −0.17 ± 0.09 | NOISE on the rebuild |
| (c) the same, on all 18 slates (each slate's own live minutes) | +0.09 ± 0.04, 12 of 18 | +0.11 ± 0.05, 12 of 17 | +0.08 ± 0.11, 7 of 18 | DIRECTIONAL: holds across older models, flat on the rebuild |

**Fitted parameters on all 4 rebuild-era slates** (weight on the rebuild):
- one weight: 0.0;
- ordinary per tier: 30+ 0.1, 20–30 0.0, 10–20 0.2;
- (b) per tier: 30+ 0.1, 20–30 0.0, 10–20 0.5;
- (c) shrink 0.7 toward season mpg, on teams above vol 5.8.

**Reading them:**
- **(a), (b) and (b0) are the same finding three ways.** On these slates PREVIOUS's minutes beat the rebuild's for regulars, and the fringe is where the rebuild at least breaks even.
- **(a) is the cleanest:** it leaves the fringe exactly as it is, so it can't hurt the cases the rebuild was built for.
- **(c) works on older models but not on the rebuild.** The rebuild may already absorb what volatility shrinkage did.

**Does any fix hurt the fringe cases enough to matter?**
- (a): no, the fringe is untouched by construction.
- (b) and (b0): −0.02 on fringe, level.
- (c) on the rebuild: −0.17 ± 0.09 on fringe (1 of 4). That would matter if it holds, and it is another reason (c) isn't the pick.

## For the operator's review (HELD)

**The minutes situation switch.**
- **The rule:** on rows ordinary before lock, use PREVIOUS's minutes. On fringe rows, keep the rebuild's.
- **PREVIOUS:** the rebuild's minutes, logged nightly as the new PREVIOUS.
- **Review at 7 graded slates under it.** The automatic review re-tests it on those slates: kept if it holds, reverted if it flips.
- **Today's numbers:** +0.24 ± 0.11 rotation-minutes MAE held out, 4 of 4 slates, fringe unchanged.
- **Risk:**
  - 4 slates, at the bar's thinnest.
  - The ordinary/fringe split is a definition (pre-lock flags) that wasn't itself tuned.
  - PREVIOUS's minutes are an older model that the per-minute half wasn't rebuilt against. STARS points must be checked beside it before any move.
- **Watch:** re-run `mt.py` once 11-27 grades (6 slates), and at 7.
