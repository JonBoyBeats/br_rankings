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
| 2026-10-25 | 6 | 1 | 11148 | 0 | 6244 | 2721 | 99% | 100% | 80 |
| 2026-10-26 | 6 | 1 | 13530 | 0 | 997 | 634 | 100% | 100% | 100 |
| 2026-10-27 | 6 | 1 | 15750 | 0 | 21 | 0 | 100% | 100% | 150 |
| 2026-10-28 | 6 | 1 | 15750 | 0 | 2619 | 1782 | 100% | 100% | 110 |
| 2026-10-29 | 4 | 1 | 13556 | 0 | 2789 | 2419 | 100% | 100% | 100 |
| 2026-10-30 | 6 | 5 | 20874 | 0 | 5028 | 3646 | 100% | 100% | 182 |
| 2026-10-31 | 6 | 3 | 14016 | 0 | 6070 | 2642 | 100% | 100% | 40 |
| 2026-11-01 | 4 | 2 | 10292 | 0 | 1455 | 0 | 100% | 100% | 40 |
| 2026-11-02 | 6 | 5 | 18678 | 0 | 4157 | 1519 | 100% | 100% | 85 |
| 2026-11-04 | 6 | 7 | 21432 | 0 | 5590 | 3786 | 100% | 100% | 90 |
| 2026-11-05 | 4 | 5 | 20492 | 0 | 45 | 0 | 100% | 100% | 60 |
| 2026-11-06 | 6 | 5 | 20880 | 0 | 9763 | 4312 | 99% | 100% | 92 |
| 2026-11-07 | 6 | 5 | 18600 | 0 | 4741 | 2906 | 100% | 100% | 40 |
| 2026-11-08 | 6 | 3 | 10290 | 0 | 3351 | 2571 | 100% | 100% | 40 |

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
| 2026-10-27 | Tuesday Tip-Off | 6 | PM | 4 | 229.2 | 191.0 | 1.2, 13.3, 16.4, 22.4, 26.6, 32.5 |
| 2026-10-30 | Buzzer Beater | 6 | PM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
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
| Contest (its mean against its night's) | The Crossover | -0.3 | 8 |
| Contest (its mean against its night's) | The Layup Line | -0.5 | 9 |
| Contest (its mean against its night's) | flagships | +0.0 | 17 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +3.6 | 39 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +6.1 | 54226 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.3 | 54255 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.3 | 54273 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -1.8 | 53851 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.1 | 54729 |
| Swap on the team (inside contest) | no | +1.0 | 222131 |
| Swap on the team (inside contest) | yes | -4.4 | 49203 |
| Window (inside contest) | AM | -0.6 | 83260 |
| Window (inside contest) | PM | +0.3 | 187596 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fast Break Friday | 6 | 3 | 290 | 0.69 | 1.72 | 1.62 | 1.55 | 38.6 | 2.06 (34) | 1.56 (256) | $1450 | $1467 | +1% |
| Hump Day Hoops | 6 | 3 | 250 | 1.20 | 1.20 | 1.36 | 1.14 | 51.5 | 1.80 (100) | 1.07 (150) | $1250 | $757 | -39% |
| Monday Night Hoops | 6 | 2 | 170 | 0.00 | 0.94 | 0.88 | 1.06 | 48.4 | 0.82 (61) | 0.92 (109) | $850 | $479 | -44% |
| Tuesday Tip-Off | 6 | 1 | 150 | 0.67 | 1.07 | 1.13 | 1.27 | 46.7 | - (0) | 1.13 (150) | $750 | $840 | +12% |
| Saturday Slam | 6 | 3 | 120 | 4.17 | 2.33 | 1.58 | 1.25 | 47.0 | 1.43 (28) | 1.63 (92) | $600 | $6569 | +995% |
| Sunday Shootaround | 6 | 2 | 120 | 0.83 | 1.33 | 1.33 | 1.38 | 41.3 | 3.00 (30) | 0.78 (90) | $600 | $480 | -20% |
| Buzzer Beater | 6 | 3 | 40 | 2.50 | 2.00 | 2.00 | 1.38 | 44.8 | - (0) | 2.00 (40) | $120 | $159 | +32% |
| The Layup Line | 6 | 3 | 19 | 0.00 | 2.11 | 1.05 | 1.05 | 48.1 | - (0) | 1.05 (19) | $95 | $40 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 0.95 (42) | 1.81 (138) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 14 | 1159 | 1.12 | 1.45 | 1.36 (1.16-1.59) | 1.29 | 45.4 | 1.70 (253) | 1.27 (906) | $5715 | $10791 | +89% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.77 (52) | 1.74 (172) | $1120 | $847 | -24% |
| **all** | - | 19 | 1383 | 1.08 | 1.45 | 1.39 (1.22-1.60) | 1.31 | 44.9 | 1.54 (305) | 1.35 (1078) | $6835 | $11638 | +70% |

Dollars: $6835 in fees, $11638 won, +70% ROI over 19 nights (80% range -28% to +205%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -20%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

**Concentration and uniqueness**: per night, across all my teams. Top player: my most-used player and the share of my teams with him; top pair likewise; cores: a team's three earliest picks, how many of my teams share the most-used one. Uniqueness (flagship, from the contest measures): the median share of the field holding 4+ of a team's 6, and my teams with an exact duplicate in the field.

| Night | My teams | Top player | Top pair | Biggest shared core | Field share with 4+ of 6 (median) | Teams with a duplicate |
|---|---|---|---|---|---|---|
| 2026-10-20 | 4 | Tyrese Maxey 50% | Dylan Harper + Tyrese Maxey 50% | 1 (LeBron James + Tyrese Maxey + Victor Wembanyama) | 5.2% | 3 of 4 |
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

Reference for the Mine column: all my teams against same-price field teams run 1.39 (1.23-1.60) at 10%, 1.02 at 1%; finish -5.8; 1329 teams, 17 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.24 (1.10-1.37) at 10%, 1.48 at 1%; finish -2.4; 309571 teams, 17 slates | 1.13 (1.00-1.27) at 10%, 1.16 at 1%; finish -1.7; 208547 teams, 12 slates | 1.49 (1.23-1.77) at 10%, 2.40 at 1%; finish -4.1; 101024 teams, 5 slates | 1.84 (1.34-2.49) at 10%, 1.40 at 1%; finish -7.8; 1940 teams, 17 slates | RULE for | RULE for |
|   AM only | 1.14 (1.05-1.24) at 10%, 1.47 at 1%; finish -0.0; 79142 teams, 15 slates | 1.08 (0.98-1.19) at 10%, 1.23 at 1%; finish +0.2; 52155 teams, 10 slates | 1.25 (1.10-1.45) at 10%, 1.93 at 1%; finish -0.5; 26987 teams, 5 slates | 1.52 (1.11-1.95) at 10%, 0.88 at 1%; finish -3.4; 351 teams, 11 slates | RULE for | RULE for |
|   PM only | 1.27 (1.10-1.44) at 10%, 1.47 at 1%; finish -3.3; 230423 teams, 17 slates | 1.14 (0.98-1.33) at 10%, 1.14 at 1%; finish -2.2; 156392 teams, 12 slates | 1.62 (1.28-1.91) at 10%, 2.62 at 1%; finish -5.4; 74031 teams, 5 slates | 1.93 (1.29-2.66) at 10%, 1.55 at 1%; finish -8.7; 1589 teams, 16 slates | RULE for | RULE for |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.40 (1.18-1.71) at 10%, 2.24 at 1%; finish -5.9; 19453 teams, 6 slates | 1.29 (1.17-1.65) at 10%, 2.12 at 1%; finish -4.9; 13720 teams, 4 slates | 1.70 at 10%, 2.72 at 1%; finish -8.3; 5733 teams, 2 slates | 1.99 (0.62-3.63) at 10%, 1.77 at 1%; finish -13.5; 60 teams, 6 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.17 (1.06-1.28) at 10%, 1.30 at 1%; finish -1.5; 1208999 teams, 17 slates | 1.17 (1.01-1.32) at 10%, 1.36 at 1%; finish -1.7; 809739 teams, 12 slates | 1.17 (1.04-1.29) at 10%, 1.18 at 1%; finish -1.1; 399260 teams, 5 slates | 1.42 (1.06-1.75) at 10%, 0.66 at 1%; finish -5.2; 8785 teams, 17 slates | RULE for | RULE for |
|   T3 | 1.17 (0.85-1.63) at 10%, 1.22 at 1%; finish -2.1; 111927 teams, 13 slates | 1.31 (0.85-2.13) at 10%, 1.41 at 1%; finish -5.0; 82363 teams, 10 slates | 0.85 (0.68-0.92) at 10%, 0.81 at 1%; finish +6.0; 29564 teams, 3 slates | 1.30 (0.94-1.77) at 10%, 0.00 at 1%; finish -7.3; 860 teams, 13 slates | no lean | no lean |
|   T4 | 1.18 (1.01-1.37) at 10%, 1.31 at 1%; finish -1.9; 176520 teams, 16 slates | 1.13 (0.90-1.41) at 10%, 1.19 at 1%; finish -1.2; 102667 teams, 11 slates | 1.28 (1.15-1.39) at 10%, 1.55 at 1%; finish -2.9; 73853 teams, 5 slates | 1.34 (0.96-1.85) at 10%, 1.37 at 1%; finish -3.2; 1513 teams, 15 slates | LEAN for | LEAN for |
|   T5 | 1.18 (1.03-1.33) at 10%, 1.36 at 1%; finish -1.4; 920430 teams, 16 slates | 1.19 (0.95-1.41) at 10%, 1.50 at 1%; finish -1.7; 624636 teams, 11 slates | 1.16 (0.98-1.39) at 10%, 1.13 at 1%; finish -0.8; 295794 teams, 5 slates | 1.47 (1.05-1.90) at 10%, 0.55 at 1%; finish -5.8; 6412 teams, 15 slates | LEAN for | LEAN for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.13 (1.02-1.24) at 10%, 1.16 at 1%; finish -1.1; 729847 teams, 17 slates | 1.14 (1.01-1.30) at 10%, 1.11 at 1%; finish -2.6; 508804 teams, 12 slates | 1.09 (0.95-1.25) at 10%, 1.32 at 1%; finish +2.2; 221043 teams, 5 slates | 1.65 (1.38-1.95) at 10%, 1.68 at 1%; finish -7.1; 4191 teams, 17 slates | RULE for | LEAN for **(changes)** |
|   T1 | 1.87 (1.47-2.37) at 10%, 2.78 at 1%; finish -7.6; 99587 teams, 12 slates | 1.68 (1.17-2.53) at 10%, 1.81 at 1%; finish -8.9; 54966 teams, 8 slates | 2.20 (1.85-2.39) at 10%, 7.65 at 1%; finish -5.9; 44621 teams, 4 slates | 2.59 (1.61-3.72) at 10%, 4.13 at 1%; finish -13.0; 507 teams, 11 slates | RULE for | RULE for |
|   T2 | 1.00 (0.84-1.20) at 10%, 0.94 at 1%; finish +0.6; 271140 teams, 17 slates | 1.03 (0.81-1.26) at 10%, 0.90 at 1%; finish -0.9; 184203 teams, 12 slates | 0.94 (0.75-1.16) at 10%, 1.05 at 1%; finish +3.8; 86937 teams, 5 slates | 1.43 (1.12-1.84) at 10%, 1.47 at 1%; finish -5.2; 1547 teams, 17 slates | no lean | no lean |
|   T3 | 1.31 (1.01-1.63) at 10%, 1.39 at 1%; finish -4.6; 175023 teams, 15 slates | 1.30 (0.95-1.69) at 10%, 1.43 at 1%; finish -4.0; 148399 teams, 11 slates | 1.37 (0.98-2.27) at 10%, 1.23 at 1%; finish -8.1; 26624 teams, 4 slates | 2.40 (1.85-2.89) at 10%, 2.33 at 1%; finish -14.1; 1122 teams, 15 slates | LEAN for | LEAN for |
|   T4 | 0.94 (0.79-1.17) at 10%, 0.90 at 1%; finish +2.5; 184013 teams, 17 slates | 1.00 (0.79-1.35) at 10%, 0.94 at 1%; finish -0.5; 121218 teams, 12 slates | 0.81 (0.64-1.18) at 10%, 0.77 at 1%; finish +8.1; 62795 teams, 5 slates | 1.12 (0.92-1.39) at 10%, 0.93 at 1%; finish -0.8; 1015 teams, 16 slates | no lean | no lean |
|   T5 | none | none | none | none | not enough | not enough |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.15 (0.79-1.44) at 10%, 1.26 at 1%; finish -2.9; 45861 teams, 9 slates | 1.16 (0.78-1.41) at 10%, 1.29 at 1%; finish -2.2; 34034 teams, 7 slates | 1.08 at 10%, 1.01 at 1%; finish -4.9; 11827 teams, 2 slates | 1.16 (1.07-1.29) at 10%, 1.13 at 1%; finish -0.5; 237 teams, 6 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.06 (0.93-1.19) at 10%, 1.15 at 1%; finish -1.4; 1103618 teams, 15 slates | 0.94 (0.86-1.03) at 10%, 0.94 at 1%; finish -0.2; 595952 teams, 10 slates | 1.21 (0.97-1.50) at 10%, 1.43 at 1%; finish -2.9; 507666 teams, 5 slates | 1.67 (1.45-1.91) at 10%, 0.78 at 1%; finish -2.3; 3868 teams, 12 slates | no lean | no lean |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 1.19 (0.91-1.56) at 10%, 1.44 at 1%; finish -3.1; 81691 teams, 13 slates | 1.20 (0.88-1.69) at 10%, 1.44 at 1%; finish -2.7; 59590 teams, 10 slates | 1.17 (0.82-1.79) at 10%, 1.45 at 1%; finish -4.2; 22101 teams, 3 slates | 1.76 (1.20-2.32) at 10%, 2.96 at 1%; finish -10.5; 660 teams, 13 slates | LEAN for | LEAN for |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.94 (0.77-1.20) at 10%, 0.87 at 1%; finish +1.8; 56133 teams, 13 slates | 1.02 (0.85-1.35) at 10%, 1.10 at 1%; finish +1.2; 45292 teams, 9 slates | 0.64 (0.38-1.33) at 10%, 0.28 at 1%; finish +4.1; 10841 teams, 4 slates | 0.88 (0.54-1.21) at 10%, 0.00 at 1%; finish -4.5; 273 teams, 12 slates | no lean | no lean |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 0.80 (0.67-0.95) at 10%, 0.66 at 1%; finish +2.3; 602708 teams, 16 slates | 0.94 (0.78-1.12) at 10%, 0.94 at 1%; finish +0.1; 400114 teams, 11 slates | 0.60 (0.46-0.81) at 10%, 0.36 at 1%; finish +6.7; 202594 teams, 5 slates | 1.47 (1.17-1.83) at 10%, 0.60 at 1%; finish -7.6; 1858 teams, 16 slates | LEAN against | LEAN against |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.84 (0.67-1.09) at 10%, 0.81 at 1%; finish +3.0; 92188 teams, 15 slates | 0.86 (0.66-1.19) at 10%, 0.82 at 1%; finish +1.9; 69023 teams, 11 slates | 0.78 (0.34-1.15) at 10%, 0.78 at 1%; finish +6.2; 23165 teams, 4 slates | 0.98 (0.64-1.57) at 10%, 0.86 at 1%; finish -3.2; 280 teams, 13 slates | LEAN against | LEAN against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.19 (0.91-1.53) at 10%, 1.43 at 1%; finish -1.7; 10773 teams, 10 slates | 1.24 (0.75-2.12) at 10%, 1.54 at 1%; finish -2.1; 4728 teams, 6 slates | 1.15 (0.92-1.38) at 10%, 1.35 at 1%; finish -1.4; 6045 teams, 4 slates | 1.48 (0.95-2.19) at 10%, 1.08 at 1%; finish -4.8; 94 teams, 7 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.03 (0.82-1.25) at 10%, 1.02 at 1%; finish -0.6; 23183 teams, 14 slates | 0.99 (0.76-1.23) at 10%, 1.00 at 1%; finish -0.8; 17550 teams, 10 slates | 1.14 (0.70-1.76) at 10%, 1.07 at 1%; finish +0.1; 5633 teams, 4 slates | 1.17 (0.69-1.77) at 10%, 0.68 at 1%; finish -3.9; 144 teams, 11 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 1.02 (0.83-1.24) at 10%, 1.05 at 1%; finish +0.4; 143805 teams, 12 slates | 1.07 (0.77-1.36) at 10%, 1.22 at 1%; finish +0.6; 89522 teams, 8 slates | 0.97 (0.75-1.29) at 10%, 0.89 at 1%; finish +0.1; 54283 teams, 4 slates | 1.46 (0.92-2.06) at 10%, 0.87 at 1%; finish -1.4; 580 teams, 11 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 1.02 (0.85-1.25) at 10%, 0.96 at 1%; finish -0.8; 198314 teams, 12 slates | 1.05 (0.84-1.42) at 10%, 1.03 at 1%; finish -1.7; 149592 teams, 8 slates | 0.93 (0.66-1.12) at 10%, 0.80 at 1%; finish +2.1; 48722 teams, 4 slates | 1.13 (0.70-1.79) at 10%, 0.32 at 1%; finish -3.4; 1167 teams, 11 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | none | none | none | none | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 1.11 (0.76-1.79) at 10%, 1.10 at 1%; finish -1.9; 6249 teams, 14 slates | 1.11 (0.77-1.80) at 10%, 1.10 at 1%; finish -2.2; 6158 teams, 10 slates | 0.75 (0.50-1.33) at 10%, 1.17 at 1%; finish +20.3; 91 teams, 4 slates | 1.79 (1.39-2.50) at 10%, 0.00 at 1%; finish -12.4; 51 teams, 4 slates | no lean | no lean |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 0.97 (0.85-1.12) at 10%, 0.97 at 1%; finish +0.8; 27211 teams, 9 slates | 0.86 (0.73-0.97) at 10%, 0.83 at 1%; finish +1.8; 15601 teams, 5 slates | 1.12 (0.90-1.39) at 10%, 1.16 at 1%; finish -0.6; 11610 teams, 4 slates | 0.96 (0.52-1.45) at 10%, 1.09 at 1%; finish +0.9; 174 teams, 9 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 0.90 (0.76-1.14) at 10%, 0.69 at 1%; finish +0.1; 11706 teams, 13 slates | 0.87 (0.68-1.28) at 10%, 0.68 at 1%; finish +1.5; 5909 teams, 8 slates | 0.95 (0.73-1.34) at 10%, 0.72 at 1%; finish -1.2; 5797 teams, 5 slates | 2.51 (1.27-4.33) at 10%, 5.77 at 1%; finish -3.8; 35 teams, 8 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.91 (1.44-2.56) at 10%, 2.79 at 1%; finish -7.8; 4417 teams, 10 slates | 2.10 (1.41-3.89) at 10%, 3.90 at 1%; finish -8.6; 2961 teams, 6 slates | 1.56 (1.13-1.93) at 10%, 1.32 at 1%; finish -6.1; 1456 teams, 4 slates | 1.37 (0.36-3.63) at 10%, 0.00 at 1%; finish -7.8; 16 teams, 5 slates | RULE for | RULE for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.19 (0.97-1.48) at 10%, 1.62 at 1%; finish -1.2; 48820 teams, 15 slates | 1.12 (0.92-1.40) at 10%, 1.67 at 1%; finish +1.3; 32187 teams, 10 slates | 1.34 (0.76-2.06) at 10%, 1.50 at 1%; finish -5.9; 16633 teams, 5 slates | 2.26 (1.42-3.09) at 10%, 1.18 at 1%; finish -12.0; 281 teams, 13 slates | LEAN for | LEAN for |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 0.96 (0.78-1.18) at 10%, 0.98 at 1%; finish +0.2; 202545 teams, 16 slates | 0.91 (0.74-1.16) at 10%, 0.93 at 1%; finish +1.5; 146242 teams, 11 slates | 1.12 (0.68-1.48) at 10%, 1.14 at 1%; finish -3.0; 56303 teams, 5 slates | 1.10 (0.86-1.63) at 10%, 0.34 at 1%; finish -5.6; 1455 teams, 15 slates | no lean | no lean |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 0.98 (0.80-1.20) at 10%, 0.96 at 1%; finish -0.2; 108088 teams, 16 slates | 1.14 (0.90-1.47) at 10%, 1.30 at 1%; finish -2.5; 77854 teams, 11 slates | 0.68 (0.58-0.85) at 10%, 0.48 at 1%; finish +5.7; 30234 teams, 5 slates | 1.33 (1.04-1.65) at 10%, 0.68 at 1%; finish -7.3; 685 teams, 16 slates | no lean | no lean |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.26 (1.05-1.55) at 10%, 1.51 at 1%; finish -2.5; 128671 teams, 15 slates | 1.65 (1.32-2.05) at 10%, 2.12 at 1%; finish -5.3; 75878 teams, 10 slates | 0.87 (0.67-1.06) at 10%, 0.90 at 1%; finish +1.5; 52793 teams, 5 slates | 1.71 (1.32-2.25) at 10%, 1.10 at 1%; finish -4.6; 625 teams, 12 slates | LEAN for | LEAN for |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 | RULE for | +2.5 | +2.5 (101%) | -0.0 (-1%) | -0.6 | 1.18 (1.03-1.33) at 10%, 1.37 at 1%; finish -1.8; 309571 teams, 17 slates | RULE for |
| ownership-tiebreak-t5 AM only | RULE for | +0.0 | +1.3 | -1.2 | -3.2 | 1.07 (0.96-1.20) at 10%, 1.28 at 1%; finish +0.8; 79143 teams, 15 slates | no lean |
| ownership-tiebreak-t5 PM only | RULE for | +3.3 | +2.8 (86%) | +0.5 (14%) | +0.2 | 1.22 (1.05-1.40) at 10%, 1.40 at 1%; finish -2.7; 230423 teams, 17 slates | RULE for |
| leverage-t2-t4 | RULE for | +5.5 | +5.6 (101%) | -0.1 (-1%) | -1.8 | 1.51 (1.23-2.18) at 10%, 2.23 at 1%; finish -6.6; 19451 teams, 6 slates | RULE for |
| value-up-middle-t5 | RULE for | +1.4 | +1.1 (80%) | +0.3 (20%) | -1.5 | 1.13 (1.01-1.25) at 10%, 1.26 at 1%; finish -0.9; 1208999 teams, 17 slates | LEAN for |
| value-up-middle-t5 T4 | LEAN for | +2.1 | +2.0 (95%) | +0.1 (5%) | +2.1 | 1.13 (0.95-1.33) at 10%, 1.24 at 1%; finish -1.3; 176523 teams, 16 slates | LEAN for |
| value-up-middle-t5 T5 | LEAN for | +1.2 | +0.1 (8%) | +1.2 (92%) | -0.9 | 1.18 (1.01-1.34) at 10%, 1.31 at 1%; finish -1.6; 920399 teams, 16 slates | LEAN for |
| pricey-flags | RULE for | +1.4 | +2.0 (144%) | -0.6 (-44%) | +2.6 | 1.15 (1.04-1.27) at 10%, 1.19 at 1%; finish -1.4; 729865 teams, 17 slates | RULE for |
| pricey-flags T1 | RULE for | +5.8 | +6.2 (107%) | -0.4 (-7%) | +8.9 | 1.93 (1.55-2.42) at 10%, 2.84 at 1%; finish -8.0; 99583 teams, 12 slates | RULE for |
| pricey-flags T3 | LEAN for | +4.8 | +6.2 (128%) | -1.3 (-28%) | +5.2 | 1.33 (1.02-1.63) at 10%, 1.46 at 1%; finish -4.6; 175025 teams, 15 slates | LEAN for |
| pm-t2-adp-etr2 | LEAN for | +2.9 | +1.7 (57%) | +1.3 (43%) | +0.9 | 1.13 (0.86-1.51) at 10%, 1.33 at 1%; finish -2.7; 81693 teams, 13 slates | no lean |
| pm-t5-adp-value | LEAN against | -2.4 | -2.1 (88%) | -0.3 (12%) | +0.2 | 0.83 (0.69-0.99) at 10%, 0.70 at 1%; finish +1.8; 602709 teams, 16 slates | LEAN against |
| one-tier-cap | LEAN against | -3.1 | -2.8 (91%) | -0.3 (9%) | -0.5 | 0.81 (0.64-1.05) at 10%, 0.77 at 1%; finish +3.6; 92202 teams, 15 slates | LEAN against |
| beneficiary-round6:played | RULE for | +7.7 | +9.5 (123%) | -1.8 (-23%) | - (holding) | 1.89 (1.43-2.53) at 10%, 2.77 at 1%; finish -7.7; 4417 teams, 10 slates | RULE for |
| pm-t5-beneficiary | LEAN for | +0.9 | +2.4 (261%) | -1.5 (-161%) | - (holding) | 1.11 (0.92-1.35) at 10%, 1.49 at 1%; finish -0.0; 48815 teams, 15 slates | no lean |
| am-t5-other-reads | LEAN for | +2.7 | +1.2 (44%) | +1.5 (56%) | +1.5 | 1.29 (1.07-1.59) at 10%, 1.50 at 1%; finish -3.0; 128699 teams, 15 slates | LEAN for |
| turn 1/2: a. reach vs trust | LEAN against | -0.1 | +1.0 | -1.1 | +0.0 | 0.74 (0.53-1.02) at 10%, 0.53 at 1%; finish +1.3; 23369 teams, 17 slates | LEAN against |
| turn 1/2: fallers vs trust | RULE for | +5.3 | +3.2 (61%) | +2.1 (39%) | +5.9 | 1.63 (1.16-2.47) at 10%, 2.00 at 1%; finish -6.1; 36295 teams, 17 slates | RULE for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +0.5 | +0.9 (172%) | -0.4 (-72%) | +0.1 | 1.42 (0.35-3.06) at 10%, 1.91 at 1%; finish +1.3; 3962 teams, 14 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | -0.3 | +3.2 | -3.5 | +0.5 | 1.07 (0.91-1.25) at 10%, 1.51 at 1%; finish +1.5; 20865 teams, 17 slates | no lean |
| turn 2/3: fallers vs trust | RULE for | +2.4 | +0.7 (29%) | +1.7 (71%) | +1.8 | 1.21 (1.06-1.42) at 10%, 1.29 at 1%; finish -3.2; 14922 teams, 17 slates | RULE for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +8.3 | +9.6 (116%) | -1.3 (-16%) | +6.8 | 1.70 (1.37-2.00) at 10%, 3.00 at 1%; finish -7.0; 4964 teams, 17 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | LEAN for | +0.7 | +1.0 (141%) | -0.3 (-41%) | - (holding) | 1.06 (0.92-1.22) at 10%, 1.28 at 1%; finish +0.9; 107722 teams, 17 slates | no lean |
| stack: Same-position teammates | RULE against | -3.7 | -7.9 (213%) | +4.2 (-113%) | - (holding) | 0.75 (0.64-0.87) at 10%, 0.93 at 1%; finish +4.2; 66427 teams, 17 slates | RULE against |
| stack: Same-position teammates, spread 5+ | RULE against | -0.8 | -2.8 (325%) | +1.9 (-225%) | - (holding) | 0.83 (0.73-0.92) at 10%, 0.72 at 1%; finish +1.9; 23802 teams, 14 slates | RULE against |

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
| any round | 1.08 (0.87-1.35) at 10%, 0.99 at 1%; finish -1.3; 15905 teams, 14 slates | +1.6 | +2.3 (143%) | -0.7 (-43%) | 1.07 (0.87-1.32) at 10%, 0.99 at 1%; finish -1.0; 15904 teams, 14 slates | no lean |
| rounds 1-2 | 3.05 (2.15-3.84) at 10%, 6.22 at 1%; finish -14.6; 899 teams, 3 slates | +14.0 | +10.0 (71%) | +4.0 (29%) | 2.89 (2.13-3.61) at 10%, 5.70 at 1%; finish -14.1; 899 teams, 3 slates | RULE for |
| rounds 3-4 | 1.12 (0.86-1.50) at 10%, 1.01 at 1%; finish -1.1; 4993 teams, 5 slates | +1.5 | +7.5 (505%) | -6.0 (-405%) | 1.13 (0.88-1.47) at 10%, 1.02 at 1%; finish -1.3; 4991 teams, 5 slates | no lean |
| rounds 5-6 or undrafted | 0.95 (0.77-1.30) at 10%, 0.82 at 1%; finish -0.1; 10053 teams, 13 slates | +0.5 | -1.0 (-199%) | +1.5 (299%) | 0.95 (0.77-1.28) at 10%, 0.82 at 1%; finish +0.3; 10054 teams, 13 slates | no lean |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.73 (0.54-1.00) at 10%, 0.53 at 1%; finish +1.1; 23372 teams, 17 slates | 1.75 (0.82-2.87) at 10%, 0.00 at 1%; finish -3.1; 121 teams, 15 slates |
| 1/2 | fallers vs trust | 1.63 (1.18-2.42) at 10%, 1.99 at 1%; finish -5.6; 36274 teams, 17 slates | 2.05 (1.24-3.42) at 10%, 3.01 at 1%; finish -8.2; 167 teams, 17 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.47 (0.37-3.02) at 10%, 2.42 at 1%; finish +1.0; 3963 teams, 14 slates | 2.00 (0.00-4.70) at 10%, 0.00 at 1%; finish +1.5; 63 teams, 8 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.19 (0.84-1.46) at 10%, 1.19 at 1%; finish -2.9; 10245 teams, 12 slates | 1.08 (0.00-2.45) at 10%, 0.00 at 1%; finish -8.8; 56 teams, 9 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.58 (0.22-1.20) at 10%, 0.17 at 1%; finish +3.8; 8285 teams, 13 slates | 2.12 (0.00-4.61) at 10%, 0.00 at 1%; finish -6.1; 33 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.04 (0.50-1.53) at 10%, 1.44 at 1%; finish +2.7; 7956 teams, 13 slates | 1.44 (0.65-2.14) at 10%, 4.75 at 1%; finish -5.5; 41 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 1.04 (0.60-1.48) at 10%, 1.17 at 1%; finish +0.9; 5783 teams, 12 slates | 1.61 (0.00-2.74) at 10%, 0.00 at 1%; finish -5.1; 41 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.69 (0.33-4.02) at 10%, 1.99 at 1%; finish -4.5; 5636 teams, 12 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -3.2; 28 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 0.91 (0.48-1.27) at 10%, 0.93 at 1%; finish +0.6; 4892 teams, 13 slates | 1.26 (0.00-3.54) at 10%, 0.00 at 1%; finish -6.3; 22 teams, 7 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.62 (0.65-2.86) at 10%, 1.79 at 1%; finish -2.2; 3565 teams, 12 slates | 3.17 (1.49-4.53) at 10%, 0.00 at 1%; finish -10.2; 32 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.48 (0.28-0.82) at 10%, 0.14 at 1%; finish -0.7; 3284 teams, 13 slates | 1.14 (0.00-5.18) at 10%, 0.00 at 1%; finish +7.2; 20 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.71 (0.25-1.31) at 10%, 0.40 at 1%; finish -1.0; 2795 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.12 (0.74-1.42) at 10%, 1.46 at 1%; finish -2.1; 1359 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +2.7; 13 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 0.71 (0.36-0.87) at 10%, 1.10 at 1%; finish +3.4; 1314 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +5.9; 10 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 1.46 (0.70-2.21) at 10%, 1.59 at 1%; finish -4.2; 1273 teams, 12 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.32 (0.27-2.49) at 10%, 2.04 at 1%; finish -7.0; 927 teams, 13 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.47 (0.31-0.66) at 10%, 0.00 at 1%; finish +0.7; 862 teams, 13 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.30 (0.11-0.52) at 10%, 0.00 at 1%; finish +10.5; 778 teams, 13 slates | none |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 1.34 (0.58-2.00) at 10%, 2.19 at 1%; finish -2.2; 693 teams, 12 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 2/3 | a. reach vs trust | 1.03 (0.84-1.24) at 10%, 1.30 at 1%; finish +1.8; 20807 teams, 17 slates | 1.64 (0.94-2.26) at 10%, 2.07 at 1%; finish -7.6; 98 teams, 16 slates |
| 2/3 | fallers vs trust | 1.23 (1.04-1.47) at 10%, 1.30 at 1%; finish -3.2; 14924 teams, 17 slates | 2.26 (1.68-2.88) at 10%, 2.10 at 1%; finish -10.7; 83 teams, 15 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.66 (1.28-2.09) at 10%, 2.41 at 1%; finish -7.1; 4948 teams, 17 slates | 2.07 (1.02-2.97) at 10%, 4.67 at 1%; finish -13.8; 51 teams, 10 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.28 (0.76-1.79) at 10%, 1.53 at 1%; finish +2.3; 2376 teams, 13 slates | 0.35 (0.00-0.53) at 10%, 0.00 at 1%; finish -5.4; 28 teams, 7 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.66 (0.44-0.84) at 10%, 0.20 at 1%; finish -1.7; 2690 teams, 12 slates | 0.93 (0.00-2.12) at 10%, 0.00 at 1%; finish -8.5; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 0.95 (0.49-1.39) at 10%, 0.99 at 1%; finish +5.2; 2578 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +19.2; 10 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 1.24 (0.68-1.70) at 10%, 0.92 at 1%; finish +2.2; 2411 teams, 12 slates | 1.95 (0.00-2.72) at 10%, 0.00 at 1%; finish +2.7; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 0.93 (0.59-1.38) at 10%, 0.76 at 1%; finish -0.2; 2284 teams, 13 slates | 0.35 (0.00-1.35) at 10%, 0.00 at 1%; finish +1.8; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.26 (0.70-1.76) at 10%, 2.08 at 1%; finish +7.2; 2154 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +18.4; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 0.94 (0.55-1.35) at 10%, 0.88 at 1%; finish -2.8; 1866 teams, 13 slates | 0.73 (0.00-1.63) at 10%, 2.91 at 1%; finish +0.8; 17 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 1.02 (0.72-1.38) at 10%, 0.81 at 1%; finish -3.1; 1861 teams, 13 slates | 1.34 (0.00-1.70) at 10%, 0.00 at 1%; finish -5.5; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.42 (0.26-0.64) at 10%, 0.19 at 1%; finish +1.6; 1857 teams, 13 slates | 0.00 at 10%, 0.00 at 1%; finish -12.9; 3 teams, 2 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.74 (1.02-2.62) at 10%, 1.58 at 1%; finish -5.5; 1544 teams, 13 slates | 0.00 at 10%, 0.00 at 1%; finish -17.4; 3 teams, 2 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.83 (0.42-1.25) at 10%, 0.58 at 1%; finish +0.3; 1424 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +11.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.44 (0.93-1.93) at 10%, 1.28 at 1%; finish -4.7; 1385 teams, 13 slates | 3.56 (2.66-4.42) at 10%, 0.00 at 1%; finish -26.9; 10 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.71 (1.07-2.32) at 10%, 1.83 at 1%; finish -10.3; 1377 teams, 13 slates | 1.79 (0.68-3.18) at 10%, 4.07 at 1%; finish -7.3; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 1.15 (0.62-1.66) at 10%, 0.94 at 1%; finish -1.5; 1304 teams, 12 slates | 1.35 (0.00-1.91) at 10%, 0.00 at 1%; finish -6.8; 7 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 15 | 0.97 (0.41-1.42) at 10%, 1.02 at 1%; finish +8.0; 1168 teams, 12 slates | 1.30 (0.00-2.18) at 10%, 0.00 at 1%; finish +6.5; 9 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 1.10 (0.68-1.52) at 10%, 0.68 at 1%; finish -4.3; 1157 teams, 13 slates | 3.01 (0.85-6.14) at 10%, 0.00 at 1%; finish -22.1; 7 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.49 (0.26-0.78) at 10%, 0.68 at 1%; finish +2.0; 1109 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.8; 7 teams, 4 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 129 | 95% | 95% | +1 |
| AM | T1-T2 | Q TRAP | 15 | 67% | 93% | -26 |
| AM | T1-T2 | VALUE | 10 | 94% | 95% | -1 |
| AM | T3-T4 | PRICEY | 101 | 93% | 95% | -2 |
| AM | T3-T4 | Q FAIR | 4 | 77% | 88% | -11 |
| AM | T3-T4 | VALUE | 92 | 88% | 94% | -6 |
| AM | T5 | Q FAIR | 211 | 10% | 19% | -9 |
| AM | T5 | VALUE | 457 | 37% | 19% | +17 |
| PM | T1-T2 | PRICEY | 142 | 99% | 99% | +0 |
| PM | T1-T2 | Q TRAP | 18 | 75% | 99% | -24 |
| PM | T1-T2 | VALUE | 6 | 99% | 99% | -0 |
| PM | T3-T4 | PRICEY | 152 | 97% | 98% | -1 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 11 | 87% | 96% | -9 |
| PM | T3-T4 | VALUE | 137 | 95% | 99% | -4 |
| PM | T5 | Q FAIR | 192 | 13% | 20% | -7 |
| PM | T5 | VALUE | 502 | 63% | 23% | +40 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 97 (of all T5 breakers: VALUE 11, unflagged 106).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.17 (1.03-1.33) at 10%, 1.36 at 1%; finish -0.8; 107740 teams, 17 slates | 1.63 (1.36-1.95) at 10%, 1.77 at 1%; finish -7.3; 533 teams, 17 slates |
| Same-position teammates | 0.80 (0.71-0.93) at 10%, 0.91 at 1%; finish +4.4; 70565 teams, 17 slates | 1.32 (1.04-1.72) at 10%, 1.99 at 1%; finish -4.0; 300 teams, 17 slates |
| Same-position teammates, spread 5+ | 0.88 (0.79-0.95) at 10%, 0.77 at 1%; finish +1.0; 23802 teams, 14 slates | 1.62 (1.07-2.19) at 10%, 2.00 at 1%; finish -11.6; 134 teams, 13 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.71 | 1.69 | 1.08 | 1.33 | 0.87 | 1.07 | 1.03 | 0.02 | 0.09 | 0.00 | 2.96 |
| Field | 0.61 | 1.67 | 1.12 | 1.35 | 0.92 | 0.98 | 1.09 | 0.02 | 0.10 | 0.00 | 1.10 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.75 (0.60-0.89) at 10%, 0.80 at 1%; finish +6.1; 47351 teams, 16 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

447 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 173798 | 0.62 | 1.69 | 1.15 | 1.34 | 0.89 | 1.06 | 1.01 | 0.25 | 93% |
| Me | 1383 | 0.64 | 1.68 | 1.21 | 1.38 | 1.00 | 1.58 | 0.63 | 0.35 | 91% |
| Everyone | 298362 | 0.61 | 1.67 | 1.12 | 1.35 | 0.92 | 0.98 | 1.09 | 0.23 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.54 (0.26-0.81) at 10%, 0.36 at 1%; finish +11.5; 7913 teams, 5 slates |
| T1-T2 | AM | 0.69 (0.37-1.02) at 10%, 0.51 at 1%; finish +7.1; 3860 teams, 5 slates |
| T1-T2 | PM | 0.41 (0.11-0.65) at 10%, 0.23 at 1%; finish +15.7; 4053 teams, 3 slates |
| T3-T5 | both | 0.87 (0.72-1.04) at 10%, 0.98 at 1%; finish +2.2; 17670 teams, 12 slates |
| T3-T5 | AM | 0.87 (0.65-1.05) at 10%, 0.94 at 1%; finish +2.5; 6848 teams, 9 slates |
| T3-T5 | PM | 0.87 (0.69-1.11) at 10%, 1.01 at 1%; finish +2.1; 10822 teams, 9 slates |
| not credited | both | 0.75 (0.58-0.93) at 10%, 0.86 at 1%; finish +7.1; 18824 teams, 16 slates |
| not credited | AM | 0.79 (0.60-1.01) at 10%, 0.81 at 1%; finish +6.0; 9498 teams, 14 slates |
| not credited | PM | 0.72 (0.50-0.92) at 10%, 0.90 at 1%; finish +8.2; 9326 teams, 16 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 16 show a lean or rule and 8 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | no lean | no lean | 1.06 (0.93-1.19) | keep on points; money not settled |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | LEAN for | 1.17 (1.06-1.28) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | RULE for (deciles: LEAN for) | RULE for | 1.13 (1.02-1.24) | candidate: hand to the rankings side with its points cost |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 1.15 (0.79-1.44) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 1.03 (0.82-1.25) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | no lean | 1.19 (0.91-1.53) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 1.02 (0.83-1.24) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | no lean | 1.02 (0.85-1.25) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | no lean | no lean | 1.11 (0.76-1.79) | not enough on either side yet |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 0.97 (0.85-1.12) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 0.90 (0.76-1.14) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | RULE for | RULE for | 1.91 (1.44-2.56) | candidate: hand to the rankings side with its points cost |
| pm-t5-beneficiary | adopted | LEAN (listed) | LEAN for | no lean | 1.19 (0.97-1.48) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | RULE for | RULE for | 1.24 (1.10-1.37) | keep: the leverage pays (money RULE) |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.40 (1.18-1.71) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | LEAN for | no lean | 1.19 (0.91-1.56) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.94 (0.77-1.20) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | LEAN against | LEAN against | 0.80 (0.67-0.95) | keep on points; money leans against (watch) |
| one-tier-cap | adopted | LEAN (both windows) | LEAN against | LEAN against | 0.84 (0.67-1.09) | keep on points; money leans against (watch) |
| pm-middle-takes | candidate | LEAN (single window) | no lean | no lean | 0.96 (0.78-1.18) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | no lean | no lean | 0.98 (0.80-1.20) | keep on points; money not settled |
| am-t5-other-reads | candidate | LEAN against (single window) | LEAN for | LEAN for | 1.26 (1.05-1.55) | watch: money leans for the leverage, not yet its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

Verdicts that change on ten price groups: pricey-flags (RULE for on five, LEAN for on ten).

