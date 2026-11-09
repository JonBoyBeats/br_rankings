# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-09. Slates 2026-10-20 to 2026-11-08: 19 nights, 50 contests, 298840 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

## 0. Data checks

Every team in every contest pulled (scripts/nba_contests.py): picks, ADP at draft, draft (pod) id, place, points and payout on every row. Entry fees are not in Underdog's data: read off each contest's prize pool per entry and confirmed (flagships and The Layup Line $5, Buzzer Beater $3, The Alley-oop $10, Heat Check $20, The Crossover $25, Pick & Roll $100). Pick order and slot are not public: turns are read from rosters by ADP rank (section 4), never rebuilt. No contest mixes 4- and 6-drafter pods.

| Night | Drafters | Contests | Teams | Short teams | Swapped-in picks | Swaps credited | Teams with a draft window | Priced | Mine |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 | 4 | 1 | 11252 | 0 | 3 | 0 | 100% | 0% | 4 |
| 2026-10-21 | 6 | 1 | 16254 | 0 | 50 | 20 | 100% | 0% | 50 |
| 2026-10-22 | 4 | 1 | 15740 | 0 | 50 | 0 | 100% | 100% | 20 |
| 2026-10-23 | 6 | 1 | 15732 | 0 | 26 | 0 | 100% | 100% | 60 |
| 2026-10-24 | 6 | 1 | 14574 | 0 | 2885 | 433 | 100% | 100% | 40 |
| 2026-10-25 | 6 | 1 | 11148 | 0 | 6244 | 2772 | 99% | 100% | 80 |
| 2026-10-26 | 6 | 1 | 13530 | 0 | 997 | 634 | 100% | 100% | 100 |
| 2026-10-27 | 6 | 1 | 15750 | 0 | 21 | 0 | 100% | 100% | 150 |
| 2026-10-28 | 6 | 1 | 15750 | 0 | 2619 | 1782 | 100% | 100% | 110 |
| 2026-10-29 | 4 | 1 | 13556 | 0 | 2789 | 2419 | 100% | 100% | 100 |
| 2026-10-30 | 6 | 5 | 20874 | 0 | 5028 | 3632 | 100% | 100% | 182 |
| 2026-10-31 | 6 | 3 | 14016 | 0 | 6070 | 2642 | 100% | 100% | 40 |
| 2026-11-01 | 4 | 2 | 10292 | 0 | 1455 | 0 | 100% | 100% | 40 |
| 2026-11-02 | 6 | 5 | 18678 | 0 | 4157 | 1575 | 100% | 100% | 85 |
| 2026-11-04 | 6 | 7 | 21432 | 0 | 5590 | 3786 | 100% | 100% | 90 |
| 2026-11-05 | 4 | 5 | 20492 | 0 | 45 | 0 | 100% | 100% | 60 |
| 2026-11-06 | 6 | 5 | 20880 | 0 | 9763 | 4310 | 99% | 100% | 92 |
| 2026-11-07 | 6 | 5 | 18600 | 0 | 4741 | 2906 | 100% | 100% | 40 |
| 2026-11-08 | 6 | 3 | 10290 | 0 | 3351 | 2560 | 100% | 100% | 40 |

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 7 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_mon_main, nba_sat_main, nba_sun_main, nba_thu_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 271334 of 298840 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

**Ten random teams**

| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |
|---|---|---|---|---|---|---|---|
| 2026-10-22 | Thursday Night Hoops | 4 | PM | 4 | 216.7 | 144.7 | 3.3, 7.5, 8.1, 14.9, 20.2, 21.0 |
| 2026-10-23 | Fast Break Friday | 6 | PM | 2 | 236.8 | 214.1 | 3.0, 10.3, 14.1, 19.0, 31.6, 34.8 |
| 2026-10-26 | Monday Night Hoops | 6 | PM | 4 | 227.5 | 213.7 | 3.3, 8.7, 15.0, 21.8, 30.3, 33.7 |
| 2026-10-27 | Tuesday Tip-Off | 6 | AM | 4 | 229.2 | 191.0 | 1.2, 13.3, 16.4, 22.4, 26.6, 32.5 |
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
| 2026-10-30 | Fast Break Friday | 6 | PM | 3 | 223.0 | 203.5 | 4.1, 8.1, 17.0, 24.6, 26.3, 31.0 |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-04 | Hump Day Hoops | 6 | PM | 1 | 210.4 | 218.5 | 5.0, 9.2, 28.7, 34.8, 34.9, 16.8 (swap) |
| 2026-11-07 | Saturday Slam | 6 | PM | 2 | 221.3 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 15.8 (swap) |
| 2026-11-07 | Saturday Slam | 6 | AM | 3 | 225.4 | 215.2 | 1.0, 16.3, 17.5, 21.9, 24.3, 32.3 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.1 | 6 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.8 | 6 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.2 | 8 |
| Contest (its mean against its night's) | The Layup Line | -0.5 | 9 |
| Contest (its mean against its night's) | flagships | +0.0 | 17 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +3.6 | 39 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +6.1 | 54225 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.3 | 54253 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.3 | 54277 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -1.8 | 53851 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.2 | 54728 |
| Swap on the team (inside contest) | no | +1.0 | 222131 |
| Swap on the team (inside contest) | yes | -4.4 | 49203 |
| Window (inside contest) | AM | -0.4 | 118915 |
| Window (inside contest) | PM | +0.3 | 151941 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fast Break Friday | 6 | 3 | 290 | 0.69 | 1.72 | 1.62 | 1.55 | 38.6 | 1.40 (86) | 1.72 (204) | $1450 | $1467 | +1% |
| Hump Day Hoops | 6 | 3 | 250 | 1.20 | 1.20 | 1.36 | 1.14 | 51.5 | 1.75 (120) | 1.00 (130) | $1250 | $757 | -39% |
| Monday Night Hoops | 6 | 2 | 170 | 0.00 | 0.94 | 0.88 | 1.06 | 48.4 | 0.75 (80) | 1.00 (90) | $850 | $479 | -44% |
| Tuesday Tip-Off | 6 | 1 | 150 | 0.67 | 1.07 | 1.13 | 1.27 | 46.7 | 1.17 (60) | 1.11 (90) | $750 | $840 | +12% |
| Saturday Slam | 6 | 3 | 120 | 4.17 | 2.33 | 1.58 | 1.25 | 47.0 | 1.43 (28) | 1.63 (92) | $600 | $6569 | +995% |
| Sunday Shootaround | 6 | 2 | 120 | 0.83 | 1.33 | 1.33 | 1.38 | 41.3 | 1.72 (64) | 0.89 (56) | $600 | $480 | -20% |
| Buzzer Beater | 6 | 3 | 40 | 2.50 | 2.00 | 2.00 | 1.38 | 44.8 | 5.00 (4) | 1.67 (36) | $120 | $159 | +32% |
| The Layup Line | 6 | 3 | 19 | 0.00 | 2.11 | 1.05 | 1.05 | 48.1 | 2.00 (5) | 0.71 (14) | $95 | $40 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 0.95 (42) | 1.81 (138) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 14 | 1159 | 1.12 | 1.45 | 1.36 (1.16-1.59) | 1.29 | 45.4 | 1.43 (447) | 1.32 (712) | $5715 | $10791 | +89% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.77 (52) | 1.74 (172) | $1120 | $847 | -24% |
| **all** | - | 19 | 1383 | 1.08 | 1.45 | 1.39 (1.22-1.60) | 1.31 | 44.9 | 1.36 (499) | 1.40 (884) | $6835 | $11638 | +70% |

Dollars: $6835 in fees, $11638 won, +70% ROI over 19 nights (80% range -28% to +205%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -20%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

**Concentration and uniqueness**: per night, across all my teams. Top player: my most-used player and the share of my teams with him; top pair likewise; cores: a team's three earliest picks, how many of my teams share the most-used one. Uniqueness (flagship, from the contest measures): the median share of the field holding 4+ of a team's 6, and my teams with an exact duplicate in the field.

| Night | My teams | Top player | Top pair | Biggest shared core | Field share with 4+ of 6 (median) | Teams with a duplicate |
|---|---|---|---|---|---|---|
| 2026-10-20 | 4 | Dylan Harper 50% | Dylan Harper + Tyrese Maxey 50% | 1 (LeBron James + Tyrese Maxey + Victor Wembanyama) | 5.2% | 3 of 4 |
| 2026-10-21 | 50 | Brandon Miller 68% | Alperen Sengun + Brandon Miller 30% | 6 (Alperen Sengun + Brandon Miller + Domantas Sabonis) | 0.5% | 3 of 50 |
| 2026-10-22 | 20 | Ajay Mitchell 50% | Ajay Mitchell + Jarrett Allen 30% | 3 (Donovan Mitchell + Joel Embiid + Jalen Williams) | 4.5% | 13 of 20 |
| 2026-10-23 | 60 | Lauri Markkanen 42% | Jayson Tatum + Deni Avdija 18% | 5 (Scottie Barnes + Victor Wembanyama + Kawhi Leonard) | 0.7% | 4 of 60 |
| 2026-10-24 | 40 | James Harden 58% | Jamal Murray + Caleb Wilson 35% | 6 (Nikola Jokic + Jamal Murray + Devin Booker) | 1.0% | 16 of 40 |
| 2026-10-25 | 80 | Immanuel Quickley 42% | Karl-Anthony Towns + Darius Garland 20% | 5 (Darius Acuff Jr. + Karl-Anthony Towns + Scottie Barnes) | 0.8% | 11 of 80 |
| 2026-10-26 | 100 | Lauri Markkanen 30% | Alperen Sengun + Anthony Davis 17% | 6 (Lauri Markkanen + Alperen Sengun + Anthony Davis) | 0.6% | 8 of 100 |
| 2026-10-27 | 150 | Derrick White 44% | Deni Avdija + Derrick White 21% | 9 (Karl-Anthony Towns + Paul Reed + Deni Avdija) | 1.0% | 49 of 150 |
| 2026-10-28 | 110 | LeBron James 46% | Joel Embiid + LaMelo Ball 16% | 7 (Nikola Jokic + Scottie Barnes + Anthony Davis) | 0.6% | 9 of 110 |
| 2026-10-29 | 100 | Cameron Boozer 50% | Nickeil Alexander-Walker + Cameron Boozer 28% | 8 (James Harden + Jalen Johnson + Cameron Boozer) | 3.0% | 53 of 100 |
| 2026-10-30 | 182 | Devin Booker 40% | LaMelo Ball + Devin Booker 13% | 7 (Luka Doncic + Tyrese Maxey + Kevin Durant) | 0.6% | 22 of 150 |
| 2026-10-31 | 40 | Joan Beringer 48% | Nickeil Alexander-Walker + Kevin Durant 25% | 3 (Alperen Sengun + Cameron Boozer + Cam Spencer) | 0.5% | 4 of 40 |
| 2026-11-01 | 40 | Julius Randle 52% | Immanuel Quickley + Julius Randle 30% | 7 (Luka Doncic + Austin Reaves + Andrew Nembhard) | 2.9% | 17 of 40 |
| 2026-11-02 | 85 | Luka Doncic 44% | Luka Doncic + Franz Wagner 19% | 6 (Luka Doncic + Anthony Davis + Franz Wagner) | 0.5% | 1 of 70 |
| 2026-11-04 | 90 | Julius Randle 41% | Anthony Davis + Victor Wembanyama 17% | 6 (Anthony Davis + Victor Wembanyama + Jalen Brunson) | 0.5% | 9 of 90 |
| 2026-11-05 | 60 | Tristan da Silva 42% | Yaxel Lendeborg + Franz Wagner 23% | 9 (Stephen Curry + Desmond Bane + Brandin Podziemski) | 3.6% | 33 of 60 |
| 2026-11-06 | 92 | Dyson Daniels 42% | LaMelo Ball + Cameron Boozer 15% | 4 (Joel Embiid + Tyrese Maxey + Evan Mobley) | 0.4% | 3 of 80 |
| 2026-11-07 | 40 | Kevin Durant 45% | Kevin Durant + Donovan Clingan 20% | 5 (Donovan Mitchell + Alperen Sengun + Evan Mobley) | 0.7% | 6 of 40 |
| 2026-11-08 | 40 | Ace Bailey 62% | Ace Bailey + LaMelo Ball 28% | 2 (Darius Garland + Julius Randle + Giannis Antetokounmpo) | 0.7% | 5 of 40 |

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.39 (1.23-1.60) at 10%, 1.02 at 1%; finish -5.7; 1329 teams, 17 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.25 (1.14-1.36) at 10%, 1.48 at 1%; finish -2.6; 314402 teams, 17 slates | 1.17 (1.06-1.28) at 10%, 1.21 at 1%; finish -2.1; 218668 teams, 12 slates | 1.44 (1.20-1.67) at 10%, 2.24 at 1%; finish -3.7; 95734 teams, 5 slates | 1.89 (1.41-2.50) at 10%, 1.34 at 1%; finish -7.9; 2041 teams, 17 slates | RULE for | RULE for |
|   AM only | 1.21 (1.12-1.29) at 10%, 1.40 at 1%; finish -1.8; 127129 teams, 17 slates | 1.18 (1.06-1.29) at 10%, 1.23 at 1%; finish -1.9; 90441 teams, 12 slates | 1.27 (1.14-1.42) at 10%, 1.84 at 1%; finish -1.6; 36688 teams, 5 slates | 1.52 (1.24-1.75) at 10%, 0.47 at 1%; finish -5.9; 684 teams, 14 slates | RULE for | RULE for |
|   PM only | 1.27 (1.12-1.43) at 10%, 1.49 at 1%; finish -3.0; 187264 teams, 17 slates | 1.15 (1.00-1.32) at 10%, 1.16 at 1%; finish -2.2; 128224 teams, 12 slates | 1.57 (1.20-1.94) at 10%, 2.53 at 1%; finish -4.9; 59040 teams, 5 slates | 2.11 (1.37-2.95) at 10%, 1.89 at 1%; finish -8.9; 1357 teams, 16 slates | RULE for | RULE for |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.37 (1.14-1.83) at 10%, 2.12 at 1%; finish -5.0; 18711 teams, 6 slates | 1.26 (1.14-1.89) at 10%, 2.02 at 1%; finish -3.8; 13623 teams, 4 slates | 1.72 at 10%, 2.50 at 1%; finish -8.3; 5088 teams, 2 slates | 2.16 (0.68-3.73) at 10%, 1.76 at 1%; finish -13.4; 58 teams, 6 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.18 (1.08-1.29) at 10%, 1.29 at 1%; finish -1.6; 1242811 teams, 17 slates | 1.23 (1.07-1.37) at 10%, 1.44 at 1%; finish -2.4; 826138 teams, 12 slates | 1.09 (1.01-1.15) at 10%, 1.03 at 1%; finish -0.2; 416673 teams, 5 slates | 1.46 (1.13-1.77) at 10%, 0.71 at 1%; finish -5.6; 8981 teams, 17 slates | RULE for | RULE for |
|   T3 | 1.20 (0.88-1.62) at 10%, 1.31 at 1%; finish -2.4; 114862 teams, 13 slates | 1.35 (0.89-2.07) at 10%, 1.56 at 1%; finish -5.4; 85298 teams, 10 slates | 0.85 (0.68-0.92) at 10%, 0.81 at 1%; finish +6.0; 29564 teams, 3 slates | 1.13 (0.80-1.64) at 10%, 0.00 at 1%; finish -5.9; 914 teams, 13 slates | no lean | no lean |
|   T4 | 1.13 (0.96-1.32) at 10%, 1.19 at 1%; finish -1.3; 163693 teams, 16 slates | 1.06 (0.83-1.36) at 10%, 1.07 at 1%; finish +0.1; 87701 teams, 11 slates | 1.23 (1.09-1.37) at 10%, 1.39 at 1%; finish -2.9; 75992 teams, 5 slates | 1.38 (0.93-1.97) at 10%, 1.42 at 1%; finish -3.9; 1277 teams, 16 slates | LEAN for | LEAN for |
|   T5 | 1.22 (1.04-1.38) at 10%, 1.39 at 1%; finish -1.8; 964136 teams, 17 slates | 1.30 (1.08-1.50) at 10%, 1.67 at 1%; finish -2.9; 653066 teams, 12 slates | 1.06 (0.95-1.22) at 10%, 0.97 at 1%; finish +0.5; 311070 teams, 5 slates | 1.53 (1.15-1.85) at 10%, 0.67 at 1%; finish -6.0; 6790 teams, 16 slates | LEAN for | LEAN for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.08 (0.98-1.19) at 10%, 1.09 at 1%; finish -0.3; 734553 teams, 17 slates | 1.10 (0.97-1.26) at 10%, 1.05 at 1%; finish -1.9; 505817 teams, 12 slates | 1.03 (0.95-1.12) at 10%, 1.19 at 1%; finish +3.2; 228736 teams, 5 slates | 1.65 (1.42-1.90) at 10%, 1.67 at 1%; finish -6.9; 4186 teams, 17 slates | LEAN for | LEAN for |
|   T1 | 1.68 (1.31-2.16) at 10%, 2.46 at 1%; finish -6.2; 96942 teams, 12 slates | 1.52 (1.04-2.36) at 10%, 1.52 at 1%; finish -8.0; 50524 teams, 8 slates | 1.91 (1.55-2.11) at 10%, 6.27 at 1%; finish -4.3; 46418 teams, 4 slates | 2.67 (1.55-3.78) at 10%, 4.50 at 1%; finish -12.2; 466 teams, 12 slates | RULE for | RULE for |
|   T2 | 1.01 (0.85-1.21) at 10%, 0.94 at 1%; finish +0.7; 292633 teams, 17 slates | 1.08 (0.84-1.35) at 10%, 0.93 at 1%; finish -1.1; 196405 teams, 12 slates | 0.89 (0.73-1.05) at 10%, 0.95 at 1%; finish +4.5; 96228 teams, 5 slates | 1.59 (1.30-1.92) at 10%, 1.63 at 1%; finish -6.6; 1657 teams, 17 slates | no lean | no lean |
|   T3 | 1.13 (0.89-1.38) at 10%, 1.10 at 1%; finish -2.1; 166869 teams, 15 slates | 1.12 (0.83-1.41) at 10%, 1.11 at 1%; finish -1.7; 145665 teams, 11 slates | 1.22 (0.86-2.04) at 10%, 1.04 at 1%; finish -5.2; 21204 teams, 4 slates | 2.18 (1.75-2.56) at 10%, 2.01 at 1%; finish -12.1; 1053 teams, 15 slates | no lean | no lean |
|   T4 | 0.93 (0.79-1.13) at 10%, 0.90 at 1%; finish +2.2; 178015 teams, 17 slates | 0.98 (0.79-1.26) at 10%, 0.94 at 1%; finish -0.8; 113187 teams, 12 slates | 0.85 (0.65-1.22) at 10%, 0.80 at 1%; finish +7.4; 64828 teams, 5 slates | 1.16 (0.98-1.36) at 10%, 0.87 at 1%; finish -2.6; 1010 teams, 17 slates | no lean | no lean |
|   T5 | none | none | none | none | not enough | not enough |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.15 (0.81-1.46) at 10%, 1.25 at 1%; finish -3.0; 40215 teams, 9 slates | 1.16 (0.79-1.42) at 10%, 1.30 at 1%; finish -2.3; 28388 teams, 7 slates | 1.08 at 10%, 1.01 at 1%; finish -4.9; 11827 teams, 2 slates | 1.48 (1.28-1.70) at 10%, 1.04 at 1%; finish -5.1; 176 teams, 6 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.02 (0.94-1.09) at 10%, 1.02 at 1%; finish -0.8; 1572591 teams, 17 slates | 1.00 (0.93-1.09) at 10%, 1.00 at 1%; finish -0.8; 940746 teams, 12 slates | 1.03 (0.91-1.19) at 10%, 1.04 at 1%; finish -0.8; 631845 teams, 5 slates | 1.49 (1.35-1.63) at 10%, 0.64 at 1%; finish -2.9; 6073 teams, 15 slates | no lean | no lean |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 1.19 (0.87-1.58) at 10%, 1.49 at 1%; finish -3.2; 59946 teams, 13 slates | 1.12 (0.80-1.62) at 10%, 1.32 at 1%; finish -2.1; 46069 teams, 10 slates | 1.44 (0.92-1.91) at 10%, 2.10 at 1%; finish -6.7; 13877 teams, 3 slates | 1.77 (1.10-2.44) at 10%, 3.15 at 1%; finish -10.6; 535 teams, 13 slates | no lean | no lean |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.86 (0.71-1.09) at 10%, 0.79 at 1%; finish +3.0; 42555 teams, 13 slates | 0.99 (0.83-1.32) at 10%, 1.10 at 1%; finish +1.6; 34065 teams, 9 slates | 0.48 (0.35-0.75) at 10%, 0.20 at 1%; finish +8.7; 8490 teams, 4 slates | 0.77 (0.51-1.08) at 10%, 0.00 at 1%; finish -3.2; 219 teams, 12 slates | no lean | LEAN against **(changes)** |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 0.84 (0.73-0.98) at 10%, 0.73 at 1%; finish +1.3; 574567 teams, 17 slates | 0.92 (0.76-1.09) at 10%, 0.91 at 1%; finish +0.5; 394688 teams, 12 slates | 0.71 (0.54-0.89) at 10%, 0.50 at 1%; finish +3.2; 179879 teams, 5 slates | 1.35 (1.07-1.69) at 10%, 0.46 at 1%; finish -5.5; 1982 teams, 17 slates | LEAN against | LEAN against |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.84 (0.67-1.10) at 10%, 0.88 at 1%; finish +3.1; 86316 teams, 15 slates | 0.86 (0.65-1.21) at 10%, 0.91 at 1%; finish +2.0; 62351 teams, 11 slates | 0.80 (0.37-1.19) at 10%, 0.81 at 1%; finish +6.1; 23965 teams, 4 slates | 1.13 (0.75-1.69) at 10%, 1.10 at 1%; finish -4.8; 235 teams, 13 slates | LEAN against | LEAN against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.18 (0.95-1.45) at 10%, 1.36 at 1%; finish -2.1; 16489 teams, 12 slates | 1.10 (0.76-1.67) at 10%, 1.18 at 1%; finish -1.5; 8495 teams, 8 slates | 1.27 (1.09-1.45) at 10%, 1.59 at 1%; finish -2.8; 7994 teams, 4 slates | 1.20 (0.75-1.82) at 10%, 1.36 at 1%; finish -2.0; 140 teams, 9 slates | LEAN for | LEAN for |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 0.98 (0.76-1.21) at 10%, 0.99 at 1%; finish +0.4; 17554 teams, 14 slates | 1.00 (0.74-1.30) at 10%, 1.10 at 1%; finish -0.6; 13777 teams, 10 slates | 0.88 (0.67-1.41) at 10%, 0.65 at 1%; finish +4.1; 3777 teams, 4 slates | 1.53 (0.83-2.39) at 10%, 0.00 at 1%; finish -7.8; 97 teams, 11 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 1.05 (0.87-1.25) at 10%, 1.10 at 1%; finish +0.2; 169934 teams, 12 slates | 1.07 (0.77-1.39) at 10%, 1.25 at 1%; finish +0.3; 100839 teams, 8 slates | 1.02 (0.81-1.32) at 10%, 0.97 at 1%; finish +0.0; 69095 teams, 4 slates | 1.35 (0.87-1.91) at 10%, 0.91 at 1%; finish -1.5; 626 teams, 12 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 1.08 (0.86-1.36) at 10%, 1.05 at 1%; finish -0.8; 162665 teams, 12 slates | 1.11 (0.84-1.51) at 10%, 1.13 at 1%; finish -1.9; 122151 teams, 8 slates | 1.00 (0.65-1.37) at 10%, 0.88 at 1%; finish +2.5; 40514 teams, 4 slates | 1.35 (0.88-2.08) at 10%, 0.10 at 1%; finish -6.1; 969 teams, 11 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | none | none | none | none | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 1.19 (0.77-2.01) at 10%, 1.26 at 1%; finish -2.5; 6093 teams, 14 slates | 1.19 (0.77-1.99) at 10%, 1.27 at 1%; finish -2.9; 6002 teams, 10 slates | 0.75 (0.50-1.34) at 10%, 1.17 at 1%; finish +20.3; 91 teams, 4 slates | 1.97 (1.40-2.94) at 10%, 0.00 at 1%; finish -13.0; 52 teams, 4 slates | no lean | no lean |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 0.96 (0.84-1.12) at 10%, 0.97 at 1%; finish +1.2; 24755 teams, 9 slates | 0.83 (0.73-0.93) at 10%, 0.79 at 1%; finish +2.9; 13052 teams, 5 slates | 1.12 (0.90-1.39) at 10%, 1.17 at 1%; finish -0.6; 11703 teams, 4 slates | 1.02 (0.50-1.71) at 10%, 0.66 at 1%; finish +0.4; 139 teams, 9 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 0.96 (0.78-1.25) at 10%, 0.73 at 1%; finish -1.0; 14593 teams, 14 slates | 0.89 (0.71-1.29) at 10%, 0.66 at 1%; finish +0.8; 7472 teams, 9 slates | 1.08 (0.82-1.47) at 10%, 0.86 at 1%; finish -2.9; 7121 teams, 5 slates | 2.02 (0.84-3.43) at 10%, 4.29 at 1%; finish -8.5; 52 teams, 9 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.41 (1.21-1.72) at 10%, 1.52 at 1%; finish -4.5; 11546 teams, 12 slates | 1.36 (1.14-1.77) at 10%, 1.50 at 1%; finish -3.5; 8731 teams, 8 slates | 1.61 (1.19-1.80) at 10%, 1.60 at 1%; finish -7.5; 2815 teams, 4 slates | 1.07 (0.39-2.62) at 10%, 0.00 at 1%; finish -11.2; 32 teams, 7 slates | RULE for | RULE for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.20 (0.95-1.56) at 10%, 1.84 at 1%; finish -1.1; 39656 teams, 15 slates | 1.15 (0.91-1.50) at 10%, 2.09 at 1%; finish +1.5; 25119 teams, 10 slates | 1.31 (0.72-2.14) at 10%, 1.49 at 1%; finish -5.6; 14537 teams, 5 slates | 2.34 (1.48-3.19) at 10%, 1.30 at 1%; finish -11.8; 260 teams, 13 slates | LEAN for | LEAN for |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 0.99 (0.80-1.19) at 10%, 0.98 at 1%; finish -0.6; 161537 teams, 16 slates | 0.97 (0.80-1.23) at 10%, 0.98 at 1%; finish +0.2; 115866 teams, 11 slates | 1.02 (0.59-1.38) at 10%, 0.97 at 1%; finish -2.8; 45671 teams, 5 slates | 1.18 (0.89-1.69) at 10%, 0.36 at 1%; finish -6.3; 1252 teams, 15 slates | no lean | no lean |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 0.93 (0.76-1.14) at 10%, 0.85 at 1%; finish +0.5; 81995 teams, 16 slates | 1.11 (0.86-1.39) at 10%, 1.16 at 1%; finish -2.0; 59950 teams, 11 slates | 0.62 (0.57-0.75) at 10%, 0.42 at 1%; finish +7.2; 22045 teams, 5 slates | 1.26 (1.00-1.53) at 10%, 0.59 at 1%; finish -6.0; 572 teams, 16 slates | no lean | no lean |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.27 (1.10-1.49) at 10%, 1.53 at 1%; finish -2.7; 147761 teams, 17 slates | 1.41 (1.18-1.68) at 10%, 1.69 at 1%; finish -3.6; 101642 teams, 12 slates | 1.03 (0.87-1.29) at 10%, 1.26 at 1%; finish -0.7; 46119 teams, 5 slates | 1.40 (1.12-1.77) at 10%, 0.53 at 1%; finish -4.4; 853 teams, 14 slates | RULE for | RULE for |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 | RULE for | +2.6 | +2.6 (100%) | -0.0 (-0%) | -0.4 | 1.19 (1.07-1.33) at 10%, 1.37 at 1%; finish -1.9; 314402 teams, 17 slates | RULE for |
| ownership-tiebreak-t5 AM only | RULE for | +1.8 | +2.4 (133%) | -0.6 (-33%) | -1.6 | 1.15 (1.05-1.26) at 10%, 1.27 at 1%; finish -1.2; 127130 teams, 17 slates | RULE for |
| ownership-tiebreak-t5 PM only | RULE for | +3.1 | +2.6 (85%) | +0.5 (15%) | +0.3 | 1.22 (1.06-1.40) at 10%, 1.42 at 1%; finish -2.5; 187264 teams, 17 slates | RULE for |
| leverage-t2-t4 | RULE for | +4.6 | +4.2 (91%) | +0.4 (9%) | -3.4 | 1.38 (1.15-2.13) at 10%, 1.86 at 1%; finish -4.8; 18710 teams, 6 slates | RULE for |
| value-up-middle-t5 | RULE for | +1.6 | +1.2 (75%) | +0.4 (25%) | -1.5 | 1.14 (1.03-1.25) at 10%, 1.24 at 1%; finish -1.1; 1242763 teams, 17 slates | LEAN for |
| value-up-middle-t5 T4 | LEAN for | +1.5 | +1.2 (83%) | +0.3 (17%) | +1.3 | 1.09 (0.91-1.28) at 10%, 1.14 at 1%; finish -0.8; 163701 teams, 16 slates | no lean |
| value-up-middle-t5 T5 | LEAN for | +1.6 | +0.4 (24%) | +1.2 (76%) | -0.6 | 1.21 (1.03-1.39) at 10%, 1.33 at 1%; finish -1.9; 964074 teams, 17 slates | LEAN for |
| pricey-flags | LEAN for | +0.5 | +1.2 (224%) | -0.7 (-124%) | +1.9 | 1.08 (0.98-1.20) at 10%, 1.10 at 1%; finish -0.3; 734571 teams, 17 slates | LEAN for |
| pricey-flags T1 | RULE for | +4.8 | +5.6 (116%) | -0.8 (-16%) | +8.0 | 1.73 (1.37-2.18) at 10%, 2.50 at 1%; finish -6.4; 96939 teams, 12 slates | RULE for |
| pm-t5-adp-value | LEAN against | -1.5 | -1.3 (86%) | -0.2 (14%) | +0.6 | 0.88 (0.75-1.02) at 10%, 0.77 at 1%; finish +0.7; 574588 teams, 17 slates | LEAN against |
| one-tier-cap | LEAN against | -3.2 | -2.6 (82%) | -0.6 (18%) | -0.7 | 0.80 (0.64-1.04) at 10%, 0.84 at 1%; finish +4.1; 86325 teams, 15 slates | LEAN against |
| am-questionable-no-push | LEAN for | +2.2 | +1.2 (56%) | +1.0 (44%) | - (holding) | 1.11 (0.88-1.37) at 10%, 1.28 at 1%; finish -1.4; 16489 teams, 12 slates | no lean |
| beneficiary-round6:played | RULE for | +4.2 | +2.4 (58%) | +1.8 (42%) | - (holding) | 1.37 (1.17-1.70) at 10%, 1.45 at 1%; finish -4.0; 11545 teams, 12 slates | RULE for |
| pm-t5-beneficiary | LEAN for | +0.8 | +3.3 (393%) | -2.4 (-293%) | - (holding) | 1.13 (0.90-1.44) at 10%, 1.68 at 1%; finish +0.1; 39651 teams, 15 slates | no lean |
| am-t5-other-reads | RULE for | +2.9 | +2.6 (90%) | +0.3 (10%) | +1.4 | 1.30 (1.11-1.52) at 10%, 1.58 at 1%; finish -3.1; 147763 teams, 17 slates | RULE for |
| turn 1/2: a. reach vs trust | LEAN against | -0.1 | +1.0 | -1.1 | +0.1 | 0.74 (0.53-1.02) at 10%, 0.53 at 1%; finish +1.3; 23369 teams, 17 slates | LEAN against |
| turn 1/2: fallers vs trust | RULE for | +5.2 | +3.2 (61%) | +2.0 (39%) | +5.9 | 1.63 (1.16-2.47) at 10%, 2.00 at 1%; finish -6.1; 36296 teams, 17 slates | RULE for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +1.1 | +2.0 (181%) | -0.9 (-81%) | +1.2 | 1.68 (0.41-3.42) at 10%, 2.76 at 1%; finish +0.4; 3750 teams, 14 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | -0.3 | +3.2 | -3.5 | +0.5 | 1.07 (0.90-1.25) at 10%, 1.51 at 1%; finish +1.5; 20864 teams, 17 slates | no lean |
| turn 2/3: fallers vs trust | RULE for | +2.4 | +0.7 (27%) | +1.7 (73%) | +1.7 | 1.21 (1.06-1.42) at 10%, 1.29 at 1%; finish -3.2; 14922 teams, 17 slates | RULE for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +8.6 | +10.0 (115%) | -1.3 (-15%) | +7.1 | 1.77 (1.46-2.04) at 10%, 3.09 at 1%; finish -7.5; 4818 teams, 17 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | LEAN for | +0.8 | +1.1 (143%) | -0.3 (-43%) | - (holding) | 1.07 (0.93-1.23) at 10%, 1.26 at 1%; finish +0.5; 107642 teams, 17 slates | no lean |
| stack: Same-position teammates | RULE against | -3.7 | -7.9 (213%) | +4.2 (-113%) | - (holding) | 0.75 (0.64-0.87) at 10%, 0.93 at 1%; finish +4.2; 66434 teams, 17 slates | RULE against |
| stack: Same-position teammates, spread 5+ | RULE against | -0.8 | -2.7 (326%) | +1.9 (-226%) | - (holding) | 0.83 (0.73-0.92) at 10%, 0.73 at 1%; finish +1.9; 23797 teams, 14 slates | RULE against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 10 | 155 | -0.2 | +0 | -20 |
| the swap board, near-ties least drafted first (leverage) | 10 | 155 | +0.6 | +1 | -100 |
| the swap board, near-ties most drafted first (spread) | 10 | 155 | -0.6 | +1 | -53 |

Leverage against spread: the leverage board's swaps would have made +0 top-10% finishes and $+47 against the spread board's (real minus each, differenced). Leverage put 67% of a night's replayed swaps on one player, spread 58%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.11 (0.94-1.34) at 10%, 0.95 at 1%; finish -2.0; 25124 teams, 16 slates | +2.1 | +1.0 (48%) | +1.1 (52%) | 1.09 (0.93-1.31) at 10%, 0.94 at 1%; finish -1.6; 25122 teams, 16 slates | no lean |
| rounds 1-2 | 2.24 (1.61-4.00) at 10%, 3.42 at 1%; finish -11.2; 1666 teams, 3 slates | +10.7 | +3.5 (32%) | +7.2 (68%) | 2.17 (1.59-3.79) at 10%, 3.29 at 1%; finish -10.9; 1666 teams, 3 slates | RULE for |
| rounds 3-4 | 1.19 (0.92-1.51) at 10%, 1.02 at 1%; finish -2.5; 6191 teams, 6 slates | +2.6 | +8.5 (330%) | -5.9 (-230%) | 1.19 (0.93-1.49) at 10%, 1.02 at 1%; finish -2.6; 6188 teams, 6 slates | LEAN for |
| rounds 5-6 or undrafted | 1.01 (0.85-1.23) at 10%, 0.82 at 1%; finish -0.8; 17352 teams, 15 slates | +1.0 | -1.9 (-197%) | +2.9 (297%) | 0.99 (0.85-1.20) at 10%, 0.82 at 1%; finish -0.4; 17353 teams, 15 slates | no lean |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.73 (0.54-1.00) at 10%, 0.53 at 1%; finish +1.0; 23372 teams, 17 slates | 1.75 (0.82-2.86) at 10%, 0.00 at 1%; finish -3.1; 121 teams, 15 slates |
| 1/2 | fallers vs trust | 1.63 (1.18-2.42) at 10%, 1.98 at 1%; finish -5.6; 36275 teams, 17 slates | 2.07 (1.25-3.46) at 10%, 3.07 at 1%; finish -8.2; 167 teams, 17 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.69 (0.43-3.28) at 10%, 3.16 at 1%; finish +0.1; 3751 teams, 14 slates | 2.91 (0.00-4.84) at 10%, 0.00 at 1%; finish -5.1; 52 teams, 8 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.19 (0.84-1.47) at 10%, 1.19 at 1%; finish -2.9; 10244 teams, 12 slates | 1.08 (0.00-2.45) at 10%, 0.00 at 1%; finish -8.8; 56 teams, 9 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.58 (0.22-1.20) at 10%, 0.17 at 1%; finish +3.8; 8285 teams, 13 slates | 2.12 (0.00-4.60) at 10%, 0.00 at 1%; finish -6.1; 33 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.04 (0.50-1.53) at 10%, 1.44 at 1%; finish +2.7; 7956 teams, 13 slates | 1.44 (0.65-2.14) at 10%, 4.75 at 1%; finish -5.5; 41 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 1.04 (0.60-1.48) at 10%, 1.16 at 1%; finish +0.9; 5783 teams, 12 slates | 1.61 (0.00-2.74) at 10%, 0.00 at 1%; finish -5.1; 41 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.69 (0.33-4.02) at 10%, 2.00 at 1%; finish -4.5; 5636 teams, 12 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -3.3; 28 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 0.91 (0.48-1.28) at 10%, 0.93 at 1%; finish +0.6; 4892 teams, 13 slates | 1.26 (0.00-3.53) at 10%, 0.00 at 1%; finish -6.2; 22 teams, 7 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.62 (0.65-2.86) at 10%, 1.78 at 1%; finish -2.2; 3565 teams, 12 slates | 3.16 (1.47-4.53) at 10%, 0.00 at 1%; finish -10.2; 32 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.48 (0.28-0.82) at 10%, 0.14 at 1%; finish -0.7; 3284 teams, 13 slates | 1.14 (0.00-5.18) at 10%, 0.00 at 1%; finish +7.2; 20 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.71 (0.25-1.31) at 10%, 0.40 at 1%; finish -1.0; 2795 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.12 (0.73-1.41) at 10%, 1.46 at 1%; finish -2.1; 1359 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +2.7; 13 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 0.70 (0.36-0.87) at 10%, 1.10 at 1%; finish +3.5; 1314 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +5.9; 10 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 1.46 (0.70-2.21) at 10%, 1.60 at 1%; finish -4.2; 1273 teams, 12 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.32 (0.27-2.49) at 10%, 2.04 at 1%; finish -7.0; 927 teams, 13 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.47 (0.31-0.67) at 10%, 0.00 at 1%; finish +0.6; 862 teams, 13 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.30 (0.11-0.52) at 10%, 0.00 at 1%; finish +10.5; 778 teams, 13 slates | none |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 1.34 (0.58-2.00) at 10%, 2.19 at 1%; finish -2.2; 693 teams, 12 slates | 0.00 at 10%, 0.00 at 1%; finish -2.8; 2 teams, 1 slates |
| 2/3 | a. reach vs trust | 1.03 (0.84-1.24) at 10%, 1.30 at 1%; finish +1.8; 20803 teams, 17 slates | 1.64 (0.94-2.25) at 10%, 2.08 at 1%; finish -7.6; 98 teams, 16 slates |
| 2/3 | fallers vs trust | 1.23 (1.05-1.47) at 10%, 1.30 at 1%; finish -3.2; 14922 teams, 17 slates | 2.28 (1.69-2.88) at 10%, 2.10 at 1%; finish -10.8; 83 teams, 15 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.69 (1.31-2.13) at 10%, 2.46 at 1%; finish -7.5; 4802 teams, 17 slates | 2.04 (0.95-2.90) at 10%, 4.72 at 1%; finish -13.3; 53 teams, 11 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.25 (0.74-1.76) at 10%, 1.55 at 1%; finish +3.5; 2534 teams, 13 slates | 0.33 (0.00-0.52) at 10%, 0.00 at 1%; finish -2.8; 31 teams, 8 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.66 (0.44-0.84) at 10%, 0.20 at 1%; finish -1.7; 2690 teams, 12 slates | 0.94 (0.00-2.12) at 10%, 0.00 at 1%; finish -8.5; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 0.95 (0.49-1.39) at 10%, 0.99 at 1%; finish +5.2; 2578 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +19.2; 10 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 1.25 (0.68-1.70) at 10%, 0.92 at 1%; finish +2.2; 2411 teams, 12 slates | 1.96 (0.00-2.72) at 10%, 0.00 at 1%; finish +2.7; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 0.93 (0.59-1.38) at 10%, 0.76 at 1%; finish -0.2; 2284 teams, 13 slates | 0.35 (0.00-1.36) at 10%, 0.00 at 1%; finish +1.8; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.26 (0.70-1.76) at 10%, 2.08 at 1%; finish +7.2; 2154 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +18.4; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 0.94 (0.55-1.35) at 10%, 0.88 at 1%; finish -2.8; 1866 teams, 13 slates | 0.73 (0.00-1.63) at 10%, 2.91 at 1%; finish +0.8; 17 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 1.02 (0.72-1.37) at 10%, 0.81 at 1%; finish -3.1; 1861 teams, 13 slates | 1.34 (0.00-1.70) at 10%, 0.00 at 1%; finish -5.5; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.42 (0.26-0.64) at 10%, 0.19 at 1%; finish +1.6; 1857 teams, 13 slates | 0.00 at 10%, 0.00 at 1%; finish -12.9; 3 teams, 2 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.74 (1.03-2.62) at 10%, 1.58 at 1%; finish -5.5; 1544 teams, 13 slates | 0.00 at 10%, 0.00 at 1%; finish -17.4; 3 teams, 2 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.83 (0.42-1.25) at 10%, 0.58 at 1%; finish +0.3; 1424 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +11.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.44 (0.93-1.93) at 10%, 1.27 at 1%; finish -4.7; 1385 teams, 13 slates | 3.56 (2.66-4.42) at 10%, 0.00 at 1%; finish -26.9; 10 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.71 (1.07-2.32) at 10%, 1.83 at 1%; finish -10.3; 1377 teams, 13 slates | 1.79 (0.68-3.17) at 10%, 4.07 at 1%; finish -7.4; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 1.15 (0.62-1.66) at 10%, 0.94 at 1%; finish -1.5; 1304 teams, 12 slates | 1.34 (0.00-1.88) at 10%, 0.00 at 1%; finish -6.7; 7 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 15 | 0.97 (0.41-1.42) at 10%, 1.02 at 1%; finish +8.0; 1168 teams, 12 slates | 1.30 (0.00-2.16) at 10%, 0.00 at 1%; finish +6.5; 9 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 1.10 (0.68-1.53) at 10%, 0.68 at 1%; finish -4.3; 1157 teams, 13 slates | 3.03 (0.85-6.23) at 10%, 0.00 at 1%; finish -22.1; 7 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.49 (0.26-0.78) at 10%, 0.68 at 1%; finish +2.1; 1109 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.8; 7 teams, 4 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 155 | 97% | 96% | +0 |
| AM | T1-T2 | Q TRAP | 15 | 69% | 97% | -29 |
| AM | T1-T2 | VALUE | 10 | 92% | 92% | -0 |
| AM | T3-T4 | PRICEY | 114 | 93% | 95% | -2 |
| AM | T3-T4 | Q FAIR | 6 | 83% | 92% | -8 |
| AM | T3-T4 | VALUE | 111 | 91% | 96% | -5 |
| AM | T5 | Q FAIR | 217 | 12% | 20% | -8 |
| AM | T5 | VALUE | 631 | 40% | 21% | +20 |
| PM | T1-T2 | PRICEY | 142 | 99% | 99% | +0 |
| PM | T1-T2 | Q TRAP | 18 | 72% | 96% | -24 |
| PM | T1-T2 | VALUE | 6 | 99% | 98% | +0 |
| PM | T3-T4 | PRICEY | 152 | 97% | 98% | -1 |
| PM | T3-T4 | Q FAIR | 4 | 12% | 98% | -86 |
| PM | T3-T4 | Q TRAP | 11 | 80% | 94% | -14 |
| PM | T3-T4 | VALUE | 137 | 95% | 98% | -4 |
| PM | T5 | Q FAIR | 192 | 12% | 20% | -8 |
| PM | T5 | VALUE | 502 | 64% | 22% | +41 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 97 (of all T5 breakers: VALUE 11, unflagged 106).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.17 (1.03-1.34) at 10%, 1.36 at 1%; finish -0.9; 107656 teams, 17 slates | 1.61 (1.33-1.95) at 10%, 1.74 at 1%; finish -7.4; 533 teams, 17 slates |
| Same-position teammates | 0.80 (0.71-0.93) at 10%, 0.91 at 1%; finish +4.4; 70572 teams, 17 slates | 1.32 (1.04-1.72) at 10%, 1.99 at 1%; finish -4.0; 300 teams, 17 slates |
| Same-position teammates, spread 5+ | 0.88 (0.79-0.95) at 10%, 0.77 at 1%; finish +1.0; 23797 teams, 14 slates | 1.62 (1.08-2.20) at 10%, 2.01 at 1%; finish -11.6; 134 teams, 13 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.72 | 1.68 | 1.09 | 1.31 | 0.89 | 1.05 | 1.15 | 0.03 | 0.09 | 0.00 | 2.97 |
| Field | 0.61 | 1.66 | 1.14 | 1.34 | 0.94 | 0.96 | 1.18 | 0.02 | 0.09 | 0.00 | 1.10 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.75 (0.60-0.89) at 10%, 0.80 at 1%; finish +6.1; 47351 teams, 16 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

447 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 173798 | 0.62 | 1.68 | 1.16 | 1.32 | 0.91 | 1.04 | 1.10 | 0.23 | 93% |
| Me | 1383 | 0.63 | 1.68 | 1.24 | 1.33 | 1.02 | 1.55 | 0.66 | 0.30 | 91% |
| Everyone | 298362 | 0.61 | 1.66 | 1.14 | 1.34 | 0.94 | 0.96 | 1.18 | 0.21 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.55 (0.26-0.81) at 10%, 0.39 at 1%; finish +11.4; 8010 teams, 5 slates |
| T1-T2 | AM | 0.55 (0.26-0.88) at 10%, 0.42 at 1%; finish +11.4; 5645 teams, 5 slates |
| T1-T2 | PM | 0.53 (0.14-0.69) at 10%, 0.29 at 1%; finish +11.5; 2365 teams, 3 slates |
| T3-T5 | both | 0.87 (0.73-1.04) at 10%, 0.96 at 1%; finish +2.2; 17928 teams, 12 slates |
| T3-T5 | AM | 0.79 (0.64-0.95) at 10%, 0.81 at 1%; finish +3.0; 10063 teams, 10 slates |
| T3-T5 | PM | 0.98 (0.75-1.30) at 10%, 1.20 at 1%; finish +1.2; 7865 teams, 9 slates |
| not credited | both | 0.75 (0.57-0.92) at 10%, 0.86 at 1%; finish +7.2; 18743 teams, 16 slates |
| not credited | AM | 0.73 (0.56-0.93) at 10%, 0.79 at 1%; finish +7.5; 12250 teams, 16 slates |
| not credited | PM | 0.77 (0.54-0.95) at 10%, 1.01 at 1%; finish +6.5; 6493 teams, 16 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 15 show a lean or rule and 8 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | no lean | no lean | 1.02 (0.94-1.09) | keep on points; money not settled |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | LEAN for | 1.18 (1.08-1.29) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | LEAN for | LEAN for | 1.08 (0.98-1.19) | watch: money leans for |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 1.15 (0.81-1.46) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 0.98 (0.76-1.21) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | LEAN for | no lean | 1.18 (0.95-1.45) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 1.05 (0.87-1.25) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | no lean | 1.08 (0.86-1.36) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | no lean | no lean | 1.19 (0.77-2.01) | not enough on either side yet |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 0.96 (0.84-1.12) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 0.96 (0.78-1.25) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | RULE for | RULE for | 1.41 (1.21-1.72) | candidate: hand to the rankings side with its points cost |
| pm-t5-beneficiary | adopted | LEAN (listed) | LEAN for | no lean | 1.20 (0.95-1.56) | keep on points; money not settled |
| ownership-tiebreak-t5 | paused (under contest test) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md) | RULE for | RULE for | 1.25 (1.14-1.36) | keep: the leverage pays (money RULE) |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.37 (1.14-1.83) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 1.19 (0.87-1.58) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean (deciles: LEAN against) | no lean | 0.86 (0.71-1.09) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | LEAN against | LEAN against | 0.84 (0.73-0.98) | keep on points; money leans against (watch) |
| one-tier-cap | adopted | LEAN (both windows) | LEAN against | LEAN against | 0.84 (0.67-1.10) | keep on points; money leans against (watch) |
| pm-middle-takes | candidate | LEAN (single window) | no lean | no lean | 0.99 (0.80-1.19) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | no lean | no lean | 0.93 (0.76-1.14) | keep on points; money not settled |
| am-t5-other-reads | candidate | LEAN against (single window) | RULE for | RULE for | 1.27 (1.10-1.49) | keep: the leverage pays (money RULE) |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

Verdicts that change on ten price groups: pm-t4-adp-etr2 (no lean on five, LEAN against on ten).

