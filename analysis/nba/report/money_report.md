# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-09. Slates 2026-10-20 to 2026-11-08: 19 nights, 50 contests, 298840 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

## 0. Data checks

Every team in every contest pulled (scripts/nba_contests.py): picks, ADP at draft, draft (pod) id, place, points and payout on every row. Entry fees are not in Underdog's data: read off each contest's prize pool per entry and confirmed (flagships and The Layup Line $5, Buzzer Beater $3, The Alley-oop $10, Heat Check $20, The Crossover $25, Pick & Roll $100). Pick order and slot are not public: turns are read from rosters by ADP rank (section 4), never rebuilt. No contest mixes 4- and 6-drafter pods.

| Night | Drafters | Contests | Teams | Short teams | Swapped-in picks | Swaps credited | Teams with a draft window | Priced | Mine |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 | 4 | 1 | 11252 | 0 | 3 | 0 | 100% | 0% | 4 |
| 2026-10-21 | 6 | 1 | 16254 | 0 | 50 | 21 | 100% | 0% | 50 |
| 2026-10-22 | 4 | 1 | 15740 | 0 | 50 | 0 | 100% | 100% | 20 |
| 2026-10-23 | 6 | 1 | 15732 | 0 | 26 | 0 | 100% | 100% | 60 |
| 2026-10-24 | 6 | 1 | 14574 | 0 | 2885 | 1377 | 100% | 100% | 40 |
| 2026-10-25 | 6 | 1 | 11148 | 0 | 6244 | 2304 | 99% | 100% | 80 |
| 2026-10-26 | 6 | 1 | 13530 | 0 | 997 | 516 | 100% | 100% | 100 |
| 2026-10-27 | 6 | 1 | 15750 | 0 | 21 | 0 | 100% | 100% | 150 |
| 2026-10-28 | 6 | 1 | 15750 | 0 | 2619 | 1662 | 100% | 100% | 110 |
| 2026-10-29 | 4 | 1 | 13556 | 0 | 2789 | 732 | 100% | 100% | 100 |
| 2026-10-30 | 6 | 5 | 20874 | 0 | 5028 | 2571 | 100% | 100% | 182 |
| 2026-10-31 | 6 | 3 | 14016 | 0 | 6070 | 0 | 100% | 100% | 40 |
| 2026-11-01 | 4 | 2 | 10292 | 0 | 1455 | 0 | 100% | 100% | 40 |
| 2026-11-02 | 6 | 5 | 18678 | 0 | 4157 | 1567 | 100% | 100% | 85 |
| 2026-11-04 | 6 | 7 | 21432 | 0 | 5590 | 3707 | 100% | 100% | 90 |
| 2026-11-05 | 4 | 5 | 20492 | 0 | 45 | 0 | 100% | 100% | 60 |
| 2026-11-06 | 6 | 5 | 20880 | 0 | 9763 | 2596 | 99% | 100% | 92 |
| 2026-11-07 | 6 | 5 | 18600 | 0 | 4741 | 2222 | 100% | 100% | 40 |
| 2026-11-08 | 6 | 3 | 10290 | 0 | 3351 | 2333 | 100% | 100% | 40 |

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 7 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_mon_main, nba_sat_main, nba_sun_main, nba_thu_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-31: 6070 swapped-in picks, 0 credited
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
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 241.8 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 14.1 (swap) |
| 2026-10-30 | Fast Break Friday | 6 | PM | 3 | 223.0 | 203.5 | 4.1, 8.1, 17.0, 24.6, 26.3, 31.0 |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-04 | Hump Day Hoops | 6 | PM | 1 | 211.9 | 218.5 | 5.0, 9.2, 28.7, 34.8, 34.9, 15.5 (swap) |
| 2026-11-07 | Saturday Slam | 6 | PM | 5 | 235.7 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 3.5 (swap) |
| 2026-11-07 | Saturday Slam | 6 | AM | 3 | 225.4 | 215.2 | 1.0, 16.3, 17.5, 21.9, 24.3, 32.3 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.2 | 6 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -1.0 | 6 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.3 | 8 |
| Contest (its mean against its night's) | The Layup Line | -0.4 | 9 |
| Contest (its mean against its night's) | flagships | +0.0 | 17 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +3.4 | 39 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +6.1 | 54223 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.2 | 54249 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.4 | 54254 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -1.6 | 53874 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.3 | 54734 |
| Swap on the team (inside contest) | no | +1.1 | 222131 |
| Swap on the team (inside contest) | yes | -4.8 | 49203 |
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

Reference for the Mine column: all my teams against same-price field teams run 1.41 (1.25-1.62) at 10%, 1.03 at 1%; finish -5.9; 1329 teams, 17 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.24 (1.13-1.36) at 10%, 1.46 at 1%; finish -2.5; 313730 teams, 17 slates | 1.16 (1.05-1.28) at 10%, 1.19 at 1%; finish -2.0; 217996 teams, 12 slates | 1.44 (1.20-1.67) at 10%, 2.24 at 1%; finish -3.7; 95734 teams, 5 slates | 1.90 (1.42-2.51) at 10%, 1.34 at 1%; finish -8.1; 2041 teams, 17 slates | RULE for | RULE for |
|   AM only | 1.20 (1.11-1.29) at 10%, 1.39 at 1%; finish -1.7; 126457 teams, 17 slates | 1.17 (1.05-1.28) at 10%, 1.21 at 1%; finish -1.7; 89769 teams, 12 slates | 1.28 (1.15-1.42) at 10%, 1.85 at 1%; finish -1.7; 36688 teams, 5 slates | 1.56 (1.28-1.82) at 10%, 0.48 at 1%; finish -6.3; 684 teams, 14 slates | RULE for | RULE for |
|   PM only | 1.26 (1.11-1.43) at 10%, 1.47 at 1%; finish -3.0; 187264 teams, 17 slates | 1.15 (1.00-1.32) at 10%, 1.14 at 1%; finish -2.1; 128224 teams, 12 slates | 1.57 (1.20-1.93) at 10%, 2.52 at 1%; finish -4.9; 59040 teams, 5 slates | 2.10 (1.36-2.88) at 10%, 1.82 at 1%; finish -8.9; 1357 teams, 16 slates | RULE for | RULE for |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.36 (1.14-1.83) at 10%, 2.08 at 1%; finish -4.9; 18661 teams, 6 slates | 1.25 (1.13-1.89) at 10%, 1.98 at 1%; finish -3.7; 13577 teams, 4 slates | 1.72 at 10%, 2.45 at 1%; finish -8.2; 5084 teams, 2 slates | 2.12 (0.66-3.62) at 10%, 1.67 at 1%; finish -13.0; 58 teams, 6 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.18 (1.07-1.28) at 10%, 1.29 at 1%; finish -1.6; 1238367 teams, 17 slates | 1.23 (1.07-1.37) at 10%, 1.44 at 1%; finish -2.3; 823188 teams, 12 slates | 1.09 (1.01-1.15) at 10%, 1.04 at 1%; finish -0.2; 415179 teams, 5 slates | 1.50 (1.17-1.82) at 10%, 0.74 at 1%; finish -5.8; 8937 teams, 17 slates | RULE for | RULE for |
|   T3 | 1.19 (0.85-1.61) at 10%, 1.32 at 1%; finish -2.0; 107876 teams, 13 slates | 1.32 (0.85-2.04) at 10%, 1.53 at 1%; finish -4.7; 79806 teams, 10 slates | 0.87 (0.66-0.95) at 10%, 0.88 at 1%; finish +5.8; 28070 teams, 3 slates | 1.20 (0.86-1.75) at 10%, 0.00 at 1%; finish -5.6; 876 teams, 12 slates | no lean | no lean |
|   T4 | 1.12 (0.95-1.31) at 10%, 1.17 at 1%; finish -1.1; 165617 teams, 16 slates | 1.04 (0.82-1.34) at 10%, 1.04 at 1%; finish +0.5; 89632 teams, 11 slates | 1.23 (1.10-1.36) at 10%, 1.40 at 1%; finish -2.9; 75985 teams, 5 slates | 1.39 (0.94-2.00) at 10%, 1.43 at 1%; finish -4.0; 1271 teams, 16 slates | LEAN for | LEAN for |
|   T5 | 1.21 (1.04-1.38) at 10%, 1.39 at 1%; finish -1.8; 964751 teams, 17 slates | 1.30 (1.07-1.51) at 10%, 1.67 at 1%; finish -2.8; 653681 teams, 12 slates | 1.06 (0.95-1.22) at 10%, 0.97 at 1%; finish +0.5; 311070 teams, 5 slates | 1.56 (1.18-1.90) at 10%, 0.70 at 1%; finish -6.2; 6790 teams, 16 slates | LEAN for | LEAN for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.07 (0.97-1.18) at 10%, 1.08 at 1%; finish -0.3; 731775 teams, 17 slates | 1.09 (0.96-1.24) at 10%, 1.04 at 1%; finish -1.8; 504515 teams, 12 slates | 1.03 (0.95-1.12) at 10%, 1.19 at 1%; finish +3.2; 227260 teams, 5 slates | 1.66 (1.42-1.92) at 10%, 1.63 at 1%; finish -7.0; 4167 teams, 17 slates | LEAN for | LEAN for |
|   T1 | 1.69 (1.32-2.18) at 10%, 2.31 at 1%; finish -6.3; 96942 teams, 12 slates | 1.53 (1.04-2.39) at 10%, 1.52 at 1%; finish -8.1; 50524 teams, 8 slates | 1.91 (1.56-2.11) at 10%, 4.70 at 1%; finish -4.3; 46418 teams, 4 slates | 2.71 (1.57-3.85) at 10%, 4.71 at 1%; finish -12.3; 466 teams, 12 slates | RULE for | RULE for |
|   T2 | 1.00 (0.84-1.20) at 10%, 0.92 at 1%; finish +0.8; 290058 teams, 17 slates | 1.06 (0.83-1.33) at 10%, 0.91 at 1%; finish -0.9; 195355 teams, 12 slates | 0.89 (0.73-1.05) at 10%, 0.94 at 1%; finish +4.5; 94703 teams, 5 slates | 1.60 (1.31-1.95) at 10%, 1.54 at 1%; finish -6.9; 1634 teams, 17 slates | no lean | no lean |
|   T3 | 1.13 (0.88-1.38) at 10%, 1.08 at 1%; finish -2.1; 166978 teams, 15 slates | 1.11 (0.83-1.41) at 10%, 1.09 at 1%; finish -1.7; 145721 teams, 11 slates | 1.20 (0.85-2.00) at 10%, 1.01 at 1%; finish -4.9; 21257 teams, 4 slates | 2.20 (1.76-2.58) at 10%, 2.01 at 1%; finish -12.1; 1057 teams, 15 slates | no lean | no lean |
|   T4 | 0.93 (0.80-1.13) at 10%, 0.90 at 1%; finish +2.2; 177716 teams, 17 slates | 0.98 (0.79-1.26) at 10%, 0.94 at 1%; finish -0.8; 112889 teams, 12 slates | 0.85 (0.65-1.22) at 10%, 0.81 at 1%; finish +7.4; 64827 teams, 5 slates | 1.17 (0.99-1.37) at 10%, 0.86 at 1%; finish -2.7; 1010 teams, 17 slates | no lean | no lean |
|   T5 | none | none | none | none | not enough | not enough |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.15 (0.80-1.45) at 10%, 1.26 at 1%; finish -3.0; 40178 teams, 9 slates | 1.16 (0.79-1.42) at 10%, 1.30 at 1%; finish -2.3; 28351 teams, 7 slates | 1.09 at 10%, 1.01 at 1%; finish -4.9; 11827 teams, 2 slates | 1.48 (1.27-1.70) at 10%, 1.02 at 1%; finish -4.8; 179 teams, 7 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.01 (0.94-1.09) at 10%, 1.02 at 1%; finish -0.8; 1562299 teams, 17 slates | 1.00 (0.92-1.09) at 10%, 1.00 at 1%; finish -0.7; 930454 teams, 12 slates | 1.03 (0.91-1.19) at 10%, 1.05 at 1%; finish -0.8; 631845 teams, 5 slates | 1.50 (1.35-1.63) at 10%, 0.62 at 1%; finish -2.9; 6073 teams, 15 slates | no lean | no lean |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 1.18 (0.87-1.56) at 10%, 1.40 at 1%; finish -2.6; 59586 teams, 13 slates | 1.12 (0.80-1.63) at 10%, 1.32 at 1%; finish -2.1; 46068 teams, 10 slates | 1.38 (0.87-1.85) at 10%, 1.64 at 1%; finish -4.6; 13518 teams, 3 slates | 1.75 (1.09-2.38) at 10%, 3.11 at 1%; finish -9.9; 530 teams, 13 slates | no lean | no lean |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.86 (0.72-1.09) at 10%, 0.79 at 1%; finish +3.0; 42598 teams, 13 slates | 0.99 (0.83-1.32) at 10%, 1.09 at 1%; finish +1.7; 34108 teams, 9 slates | 0.48 (0.36-0.75) at 10%, 0.21 at 1%; finish +8.6; 8490 teams, 4 slates | 0.77 (0.52-1.06) at 10%, 0.00 at 1%; finish -3.3; 219 teams, 12 slates | no lean | LEAN against **(changes)** |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 0.84 (0.72-0.98) at 10%, 0.74 at 1%; finish +1.3; 570484 teams, 17 slates | 0.92 (0.75-1.09) at 10%, 0.92 at 1%; finish +0.4; 390609 teams, 12 slates | 0.71 (0.54-0.88) at 10%, 0.50 at 1%; finish +3.2; 179875 teams, 5 slates | 1.44 (1.16-1.80) at 10%, 0.54 at 1%; finish -6.3; 1970 teams, 17 slates | LEAN against | LEAN against |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.85 (0.67-1.11) at 10%, 0.88 at 1%; finish +2.9; 86495 teams, 15 slates | 0.86 (0.66-1.21) at 10%, 0.93 at 1%; finish +1.9; 62289 teams, 11 slates | 0.81 (0.37-1.23) at 10%, 0.75 at 1%; finish +5.6; 24206 teams, 4 slates | 1.12 (0.75-1.71) at 10%, 1.09 at 1%; finish -4.8; 235 teams, 13 slates | LEAN against | LEAN against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.12 (0.87-1.43) at 10%, 1.22 at 1%; finish -0.9; 16011 teams, 12 slates | 1.01 (0.68-1.55) at 10%, 1.01 at 1%; finish +0.4; 8704 teams, 8 slates | 1.27 (1.04-1.52) at 10%, 1.51 at 1%; finish -2.4; 7307 teams, 4 slates | 1.16 (0.69-1.83) at 10%, 0.68 at 1%; finish -1.3; 129 teams, 9 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 0.98 (0.74-1.23) at 10%, 1.07 at 1%; finish -0.2; 15767 teams, 14 slates | 1.00 (0.70-1.31) at 10%, 1.09 at 1%; finish -0.7; 12987 teams, 10 slates | 0.89 (0.61-1.64) at 10%, 0.97 at 1%; finish +1.9; 2780 teams, 4 slates | 1.94 (1.19-2.91) at 10%, 0.00 at 1%; finish -6.8; 93 teams, 11 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 1.12 (0.91-1.37) at 10%, 1.19 at 1%; finish -1.0; 161581 teams, 11 slates | 1.21 (0.88-1.51) at 10%, 1.46 at 1%; finish -2.1; 92245 teams, 7 slates | 1.04 (0.79-1.43) at 10%, 0.99 at 1%; finish +0.5; 69336 teams, 4 slates | 1.62 (0.95-2.34) at 10%, 1.33 at 1%; finish -2.5; 545 teams, 11 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 1.10 (0.85-1.44) at 10%, 1.16 at 1%; finish -1.5; 144183 teams, 11 slates | 1.11 (0.83-1.53) at 10%, 1.14 at 1%; finish -2.1; 111525 teams, 7 slates | 1.08 (0.66-1.46) at 10%, 1.24 at 1%; finish +0.7; 32658 teams, 4 slates | 1.62 (1.12-2.49) at 10%, 0.11 at 1%; finish -6.0; 911 teams, 11 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | none | none | none | none | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 1.22 (0.64-2.68) at 10%, 1.38 at 1%; finish -2.7; 4898 teams, 14 slates | 1.23 (0.64-2.72) at 10%, 1.38 at 1%; finish -3.2; 4807 teams, 10 slates | 0.75 (0.50-1.34) at 10%, 1.18 at 1%; finish +20.2; 91 teams, 4 slates | 2.02 (1.45-3.00) at 10%, 0.00 at 1%; finish -12.2; 53 teams, 3 slates | no lean | no lean |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 0.95 (0.81-1.13) at 10%, 0.98 at 1%; finish +1.2; 22330 teams, 9 slates | 0.80 (0.65-0.92) at 10%, 0.74 at 1%; finish +3.2; 12315 teams, 5 slates | 1.13 (0.91-1.38) at 10%, 1.30 at 1%; finish -1.2; 10015 teams, 4 slates | 1.19 (0.60-2.06) at 10%, 0.00 at 1%; finish +2.2; 123 teams, 9 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 0.96 (0.78-1.26) at 10%, 0.73 at 1%; finish -1.1; 14593 teams, 14 slates | 0.89 (0.72-1.31) at 10%, 0.67 at 1%; finish +0.6; 7472 teams, 9 slates | 1.08 (0.82-1.47) at 10%, 0.86 at 1%; finish -3.0; 7121 teams, 5 slates | 2.02 (0.84-3.55) at 10%, 4.26 at 1%; finish -9.1; 52 teams, 9 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.41 (1.21-1.71) at 10%, 1.52 at 1%; finish -4.5; 11546 teams, 12 slates | 1.36 (1.14-1.76) at 10%, 1.49 at 1%; finish -3.6; 8731 teams, 8 slates | 1.60 (1.19-1.80) at 10%, 1.60 at 1%; finish -7.6; 2815 teams, 4 slates | 1.11 (0.40-2.78) at 10%, 0.00 at 1%; finish -12.0; 32 teams, 7 slates | RULE for | RULE for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.21 (0.96-1.56) at 10%, 1.84 at 1%; finish -1.0; 39656 teams, 15 slates | 1.16 (0.92-1.51) at 10%, 2.08 at 1%; finish +1.6; 25119 teams, 10 slates | 1.31 (0.72-2.13) at 10%, 1.50 at 1%; finish -5.5; 14537 teams, 5 slates | 2.34 (1.49-3.17) at 10%, 1.28 at 1%; finish -11.6; 260 teams, 13 slates | LEAN for | LEAN for |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 0.99 (0.80-1.20) at 10%, 0.97 at 1%; finish -0.6; 161936 teams, 16 slates | 0.96 (0.79-1.22) at 10%, 0.96 at 1%; finish +0.3; 116113 teams, 11 slates | 1.05 (0.62-1.46) at 10%, 0.98 at 1%; finish -3.0; 45823 teams, 5 slates | 1.20 (0.91-1.73) at 10%, 0.36 at 1%; finish -6.5; 1252 teams, 15 slates | no lean | no lean |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 0.93 (0.76-1.13) at 10%, 0.84 at 1%; finish +0.6; 81896 teams, 16 slates | 1.10 (0.85-1.38) at 10%, 1.16 at 1%; finish -1.8; 59938 teams, 11 slates | 0.62 (0.57-0.75) at 10%, 0.43 at 1%; finish +7.2; 21958 teams, 5 slates | 1.32 (1.03-1.62) at 10%, 0.65 at 1%; finish -6.6; 563 teams, 16 slates | no lean | no lean |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.28 (1.10-1.51) at 10%, 1.55 at 1%; finish -2.9; 147285 teams, 17 slates | 1.43 (1.19-1.72) at 10%, 1.72 at 1%; finish -3.8; 101161 teams, 12 slates | 1.03 (0.87-1.29) at 10%, 1.27 at 1%; finish -0.8; 46124 teams, 5 slates | 1.40 (1.12-1.79) at 10%, 0.53 at 1%; finish -4.6; 853 teams, 14 slates | RULE for | RULE for |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 9 | 100 | -1.0 | -1 | -12 |
| the swap board, near-ties least drafted first (leverage) | 9 | 100 | +0.4 | +2 | +15 |
| the swap board, near-ties most drafted first (spread) | 9 | 100 | +0.4 | +2 | -31 |

Leverage against spread: the leverage board's swaps would have made +0 top-10% finishes and $-46 against the spread board's (real minus each, differenced). Leverage put 69% of a night's replayed swaps on one player, spread 53%.

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.73 (0.54-1.00) at 10%, 0.53 at 1%; finish +1.1; 23284 teams, 17 slates | 1.87 (0.90-3.05) at 10%, 0.00 at 1%; finish -3.4; 120 teams, 15 slates |
| 1/2 | fallers vs trust | 1.65 (1.18-2.45) at 10%, 2.05 at 1%; finish -5.9; 36123 teams, 17 slates | 2.05 (1.21-3.54) at 10%, 3.58 at 1%; finish -9.3; 159 teams, 17 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.67 (0.40-3.26) at 10%, 3.05 at 1%; finish +0.2; 3721 teams, 14 slates | 2.91 (0.00-4.85) at 10%, 0.00 at 1%; finish -5.2; 52 teams, 8 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.18 (0.83-1.46) at 10%, 1.19 at 1%; finish -2.6; 10231 teams, 12 slates | 1.07 (0.00-2.45) at 10%, 0.00 at 1%; finish -8.3; 56 teams, 9 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.58 (0.22-1.21) at 10%, 0.17 at 1%; finish +3.7; 8286 teams, 13 slates | 2.11 (0.00-4.65) at 10%, 0.00 at 1%; finish -6.1; 33 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.04 (0.51-1.53) at 10%, 1.43 at 1%; finish +2.6; 7956 teams, 13 slates | 1.43 (0.65-2.13) at 10%, 4.60 at 1%; finish -5.6; 41 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 1.05 (0.60-1.49) at 10%, 1.14 at 1%; finish +0.7; 5784 teams, 12 slates | 1.63 (0.00-2.80) at 10%, 0.00 at 1%; finish -5.7; 41 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.68 (0.33-3.96) at 10%, 2.03 at 1%; finish -4.3; 5635 teams, 12 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -3.2; 28 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 0.91 (0.48-1.27) at 10%, 0.92 at 1%; finish +0.4; 4891 teams, 13 slates | 1.26 (0.00-3.65) at 10%, 0.00 at 1%; finish -6.2; 22 teams, 7 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.62 (0.66-2.83) at 10%, 1.80 at 1%; finish -2.2; 3564 teams, 12 slates | 3.40 (1.73-4.55) at 10%, 0.00 at 1%; finish -10.6; 32 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.48 (0.28-0.82) at 10%, 0.14 at 1%; finish -0.7; 3275 teams, 13 slates | 1.16 (0.00-5.49) at 10%, 0.00 at 1%; finish +6.7; 20 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.72 (0.25-1.32) at 10%, 0.41 at 1%; finish -1.2; 2794 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.1; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.11 (0.73-1.41) at 10%, 1.48 at 1%; finish -1.8; 1353 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +0.7; 13 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 0.70 (0.36-0.87) at 10%, 1.10 at 1%; finish +3.3; 1314 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.0; 10 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 1.42 (0.71-2.11) at 10%, 1.46 at 1%; finish -3.8; 1272 teams, 12 slates | 3.51 (0.00-3.75) at 10%, 0.00 at 1%; finish -17.1; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.32 (0.27-2.48) at 10%, 2.07 at 1%; finish -6.9; 927 teams, 13 slates | 5.92 at 10%, 0.00 at 1%; finish -28.7; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.47 (0.31-0.67) at 10%, 0.00 at 1%; finish +0.6; 856 teams, 13 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.24 (0.06-0.42) at 10%, 0.00 at 1%; finish +11.3; 753 teams, 12 slates | none |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 1.34 (0.58-1.98) at 10%, 2.18 at 1%; finish -2.0; 691 teams, 12 slates | 0.00 at 10%, 0.00 at 1%; finish -1.8; 2 teams, 1 slates |
| 2/3 | a. reach vs trust | 1.04 (0.84-1.26) at 10%, 1.30 at 1%; finish +1.6; 20074 teams, 17 slates | 1.68 (0.97-2.30) at 10%, 2.63 at 1%; finish -7.6; 94 teams, 16 slates |
| 2/3 | fallers vs trust | 1.24 (1.05-1.48) at 10%, 1.33 at 1%; finish -3.3; 14917 teams, 17 slates | 2.26 (1.68-2.86) at 10%, 1.97 at 1%; finish -10.6; 83 teams, 15 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.71 (1.30-2.18) at 10%, 2.39 at 1%; finish -7.8; 4572 teams, 17 slates | 2.02 (0.93-2.90) at 10%, 4.41 at 1%; finish -13.9; 52 teams, 11 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.29 (0.74-1.82) at 10%, 1.52 at 1%; finish +3.7; 2337 teams, 13 slates | 0.33 (0.00-0.52) at 10%, 0.00 at 1%; finish -3.4; 30 teams, 8 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +18.9; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.65 (0.43-0.83) at 10%, 0.21 at 1%; finish -1.6; 2697 teams, 12 slates | 0.94 (0.00-2.12) at 10%, 0.00 at 1%; finish -8.6; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 0.96 (0.46-1.41) at 10%, 0.99 at 1%; finish +5.2; 2573 teams, 12 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +19.6; 10 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 1.25 (0.68-1.72) at 10%, 0.96 at 1%; finish +2.2; 2411 teams, 12 slates | 1.98 (0.00-2.83) at 10%, 0.00 at 1%; finish +2.5; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 0.92 (0.59-1.37) at 10%, 0.76 at 1%; finish +0.1; 2298 teams, 13 slates | 0.35 (0.00-1.36) at 10%, 0.00 at 1%; finish +1.8; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.28 (0.70-1.78) at 10%, 2.19 at 1%; finish +7.3; 2154 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +18.4; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 0.94 (0.56-1.34) at 10%, 0.89 at 1%; finish -2.6; 1880 teams, 13 slates | 0.73 (0.00-1.62) at 10%, 2.98 at 1%; finish +0.9; 17 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 1.01 (0.72-1.37) at 10%, 0.82 at 1%; finish -2.9; 1861 teams, 13 slates | 1.32 (0.00-1.65) at 10%, 0.00 at 1%; finish -5.4; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.43 (0.27-0.66) at 10%, 0.20 at 1%; finish +1.6; 1814 teams, 12 slates | 0.00 at 10%, 0.00 at 1%; finish -9.3; 3 teams, 2 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.74 (1.03-2.64) at 10%, 1.58 at 1%; finish -5.4; 1544 teams, 13 slates | 0.00 at 10%, 0.00 at 1%; finish -17.6; 3 teams, 2 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.83 (0.45-1.28) at 10%, 0.59 at 1%; finish +0.4; 1431 teams, 12 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +11.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.69 (1.07-2.30) at 10%, 1.87 at 1%; finish -10.2; 1385 teams, 13 slates | 1.74 (0.67-3.07) at 10%, 3.82 at 1%; finish -7.0; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 1.15 (0.64-1.65) at 10%, 0.98 at 1%; finish -1.4; 1304 teams, 12 slates | 1.24 (0.00-1.77) at 10%, 0.00 at 1%; finish -6.4; 7 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.45 (0.94-1.97) at 10%, 1.26 at 1%; finish -5.5; 1302 teams, 12 slates | 3.57 (2.68-4.45) at 10%, 0.00 at 1%; finish -26.9; 10 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 15 | 0.97 (0.41-1.42) at 10%, 1.01 at 1%; finish +8.1; 1139 teams, 12 slates | 1.31 (0.00-2.19) at 10%, 0.00 at 1%; finish +6.6; 9 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.99 (0.56-1.46) at 10%, 0.43 at 1%; finish -3.7; 1112 teams, 12 slates | 3.76 (1.20-8.87) at 10%, 0.00 at 1%; finish -23.2; 6 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.47 (0.23-0.79) at 10%, 0.61 at 1%; finish +2.2; 1084 teams, 12 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +7.1; 7 teams, 4 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 155 | 97% | 96% | +1 |
| AM | T1-T2 | Q TRAP | 15 | 55% | 97% | -43 |
| AM | T1-T2 | VALUE | 10 | 92% | 92% | -0 |
| AM | T3-T4 | PRICEY | 114 | 93% | 95% | -2 |
| AM | T3-T4 | Q FAIR | 6 | 81% | 89% | -8 |
| AM | T3-T4 | VALUE | 111 | 89% | 95% | -6 |
| AM | T5 | Q FAIR | 217 | 10% | 19% | -9 |
| AM | T5 | VALUE | 631 | 40% | 21% | +20 |
| PM | T1-T2 | PRICEY | 142 | 99% | 98% | +0 |
| PM | T1-T2 | Q TRAP | 18 | 69% | 96% | -28 |
| PM | T1-T2 | VALUE | 6 | 99% | 98% | +0 |
| PM | T3-T4 | PRICEY | 152 | 97% | 98% | -1 |
| PM | T3-T4 | Q FAIR | 4 | 9% | 98% | -89 |
| PM | T3-T4 | Q TRAP | 11 | 81% | 94% | -13 |
| PM | T3-T4 | VALUE | 137 | 93% | 98% | -6 |
| PM | T5 | Q FAIR | 192 | 11% | 20% | -9 |
| PM | T5 | VALUE | 502 | 64% | 22% | +41 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 97 (of all T5 breakers: VALUE 11, unflagged 106).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.18 (1.03-1.35) at 10%, 1.37 at 1%; finish -0.9; 106835 teams, 17 slates | 1.63 (1.34-2.00) at 10%, 1.73 at 1%; finish -7.3; 536 teams, 17 slates |
| Same-position teammates | 0.80 (0.70-0.93) at 10%, 0.91 at 1%; finish +4.5; 70181 teams, 17 slates | 1.35 (1.06-1.78) at 10%, 1.77 at 1%; finish -4.2; 301 teams, 17 slates |
| Same-position teammates, spread 5+ | 0.89 (0.79-0.96) at 10%, 0.80 at 1%; finish +1.0; 23746 teams, 14 slates | 1.76 (1.18-2.39) at 10%, 2.11 at 1%; finish -11.9; 138 teams, 13 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.72 | 1.67 | 1.08 | 1.31 | 0.89 | 1.05 | 1.14 | 0.02 | 0.08 | 0.00 | 2.97 |
| Field | 0.61 | 1.66 | 1.12 | 1.34 | 0.93 | 0.96 | 1.17 | 0.02 | 0.08 | 0.00 | 1.10 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.74 (0.60-0.89) at 10%, 0.79 at 1%; finish +6.4; 48725 teams, 17 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

447 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 173798 | 0.62 | 1.68 | 1.15 | 1.32 | 0.90 | 1.03 | 1.09 | 0.21 | 93% |
| Me | 1383 | 0.63 | 1.66 | 1.22 | 1.33 | 1.02 | 1.53 | 0.65 | 0.27 | 91% |
| Everyone | 298362 | 0.61 | 1.66 | 1.12 | 1.34 | 0.93 | 0.96 | 1.17 | 0.20 | 93% |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 14 show a lean or rule and 8 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.

| Decision | Status | POINTS | MONEY | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | no lean | 1.01 (0.94-1.09) | keep on points; money not settled |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | 1.18 (1.07-1.28) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | LEAN for | 1.07 (0.97-1.18) | watch: money leans for |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | 1.15 (0.80-1.45) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | 0.98 (0.74-1.23) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | 1.12 (0.87-1.43) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | 1.12 (0.91-1.37) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | 1.10 (0.85-1.44) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | no lean | 1.22 (0.64-2.68) | not enough on either side yet |
| q-class-x:TRAP | candidate | not enough yet | no lean | 0.95 (0.81-1.13) | not enough on either side yet |
| beneficiary-round6:sat | candidate | anecdote (8 players) | no lean | 0.96 (0.78-1.26) | not enough on either side yet |
| beneficiary-round6:played | candidate | anecdote (8 players) | RULE for | 1.41 (1.21-1.71) | candidate: hand to the rankings side with its points cost |
| pm-t5-beneficiary | adopted | LEAN (listed) | LEAN for | 1.21 (0.96-1.56) | keep: points and money agree |
| ownership-tiebreak-t5 | paused (under contest test) | costs points | RULE for | 1.24 (1.13-1.36) | keep: the leverage pays (money RULE) |
| leverage-t2-t4 | candidate | AM about free / PM costs | RULE for | 1.36 (1.14-1.83) | keep: the leverage pays (money RULE) |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | 1.18 (0.87-1.56) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean (deciles: LEAN against) | 0.86 (0.72-1.09) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | LEAN against | 0.84 (0.72-0.98) | keep on points; money leans against (watch) |
| one-tier-cap | adopted | LEAN (both windows) | LEAN against | 0.85 (0.67-1.11) | keep on points; money leans against (watch) |
| pm-middle-takes | candidate | LEAN (single window) | no lean | 0.99 (0.80-1.20) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | no lean | 0.93 (0.76-1.13) | keep on points; money not settled |
| am-t5-other-reads | candidate | LEAN against (single window) | RULE for | 1.28 (1.10-1.51) | keep: the leverage pays (money RULE) |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (100 credited swaps of 229; 11 nights) | not enough (about 100 swaps; section 3f has the dollars) | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | no points difference (small sample: 100 swaps, 9 nights) | not enough (about 100 swaps; section 3f has the dollars) | - | not enough on either side yet |

Verdicts that change on ten price groups: pm-t4-adp-etr2 (no lean on five, LEAN against on ten).

