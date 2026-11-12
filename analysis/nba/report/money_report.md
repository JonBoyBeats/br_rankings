# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-12. Slates 2026-10-20 to 2026-11-11: 22 nights, 65 contests, 359248 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

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
| 2026-10-30 | 6 | 5 | 20874 | 0 | 5028 | 3642 | 100% | 100% | 182 |
| 2026-10-31 | 6 | 3 | 14016 | 0 | 6070 | 2642 | 100% | 100% | 40 |
| 2026-11-01 | 4 | 2 | 10292 | 0 | 1455 | 0 | 100% | 100% | 40 |
| 2026-11-02 | 6 | 5 | 18678 | 0 | 4157 | 1519 | 100% | 100% | 85 |
| 2026-11-04 | 6 | 7 | 21432 | 0 | 5590 | 3786 | 100% | 100% | 90 |
| 2026-11-05 | 4 | 5 | 20492 | 0 | 45 | 0 | 100% | 100% | 60 |
| 2026-11-06 | 6 | 5 | 20880 | 0 | 9763 | 4312 | 99% | 100% | 92 |
| 2026-11-07 | 6 | 5 | 18600 | 0 | 4741 | 2906 | 100% | 100% | 40 |
| 2026-11-08 | 6 | 3 | 10290 | 0 | 3351 | 2571 | 100% | 100% | 40 |
| 2026-11-09 | 6 | 5 | 18672 | 0 | 7234 | 3920 | 100% | 100% | 95 |
| 2026-11-10 | 6 | 5 | 20868 | 0 | 4973 | 2744 | 100% | 100% | 80 |
| 2026-11-11 | 6 | 5 | 20868 | 0 | 1509 | 828 | 100% | 100% | 80 |

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 10 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_mon_main, nba_mon_main, nba_sat_main, nba_sun_main, nba_thu_main, nba_tue_main, nba_wed_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 331742 of 359248 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

**Ten random teams**

| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |
|---|---|---|---|---|---|---|---|
| 2026-10-22 | Thursday Night Hoops | 4 | PM | 4 | 216.7 | 144.7 | 3.3, 7.5, 8.1, 14.9, 20.2, 21.0 |
| 2026-10-23 | Fast Break Friday | 6 | PM | 2 | 236.8 | 214.1 | 3.0, 10.3, 14.1, 19.0, 31.6, 34.8 |
| 2026-10-26 | Monday Night Hoops | 6 | PM | 4 | 227.5 | 213.7 | 3.3, 8.7, 15.0, 21.8, 30.3, 33.7 |
| 2026-10-27 | Tuesday Tip-Off | 6 | PM | 4 | 229.2 | 191.0 | 1.2, 13.3, 16.4, 22.4, 26.6, 32.5 |
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
| 2026-10-30 | Fast Break Friday | 6 | PM | 3 | 223.0 | 203.5 | 4.1, 8.1, 17.0, 24.6, 26.3, 31.0 |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-07 | Saturday Slam | 6 | PM | 2 | 221.3 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 15.8 (swap) |
| 2026-11-09 | Monday Night Hoops | 6 | PM | 4 | 220.9 | 247.4 | 3.4, 11.7, 14.6, 20.1, 29.0, 31.3 |
| 2026-11-11 | Hump Day Hoops | 6 | AM | 2 | 213.8 | 216.5 | 4.3, 12.1, 15.1, 20.4, 29.1, 32.5 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.1 | 9 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.5 | 9 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.2 | 11 |
| Contest (its mean against its night's) | The Layup Line | -0.5 | 12 |
| Contest (its mean against its night's) | flagships | +0.0 | 20 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +1.6 | 54 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +5.9 | 66301 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.6 | 66339 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.4 | 66357 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -2.3 | 65931 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -4.7 | 66814 |
| Swap on the team (inside contest) | no | +0.9 | 270481 |
| Swap on the team (inside contest) | yes | -4.2 | 61261 |
| Window (inside contest) | AM | -0.5 | 106212 |
| Window (inside contest) | PM | +0.3 | 224933 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hump Day Hoops | 6 | 4 | 330 | 0.91 | 1.21 | 1.30 | 1.12 | 50.6 | 1.62 (136) | 1.08 (194) | $1650 | $907 | -45% |
| Fast Break Friday | 6 | 3 | 290 | 0.69 | 1.72 | 1.62 | 1.55 | 38.6 | 1.56 (77) | 1.64 (213) | $1450 | $1467 | +1% |
| Monday Night Hoops | 6 | 3 | 250 | 0.00 | 0.96 | 1.00 | 1.12 | 46.6 | 1.02 (59) | 0.99 (191) | $1250 | $760 | -39% |
| Tuesday Tip-Off | 6 | 2 | 230 | 1.30 | 1.13 | 1.22 | 1.22 | 46.4 | 0.78 (90) | 1.50 (140) | $1150 | $1530 | +33% |
| Saturday Slam | 6 | 3 | 120 | 4.17 | 2.33 | 1.58 | 1.25 | 47.0 | 1.43 (28) | 1.63 (92) | $600 | $6569 | +995% |
| Sunday Shootaround | 6 | 2 | 120 | 0.83 | 1.33 | 1.33 | 1.38 | 41.3 | 3.00 (30) | 0.78 (90) | $600 | $480 | -20% |
| Buzzer Beater | 6 | 4 | 50 | 2.00 | 1.60 | 1.60 | 1.30 | 44.7 | 5.00 (4) | 1.30 (46) | $150 | $171 | +14% |
| The Layup Line | 6 | 4 | 24 | 0.00 | 1.67 | 1.25 | 1.25 | 49.8 | 2.00 (5) | 1.05 (19) | $120 | $50 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 1.03 (39) | 1.77 (141) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 17 | 1414 | 1.06 | 1.39 | 1.34 (1.18-1.51) | 1.27 | 45.4 | 1.47 (429) | 1.28 (985) | $6970 | $11934 | +71% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.82 (49) | 1.71 (175) | $1120 | $847 | -24% |
| **all** | - | 22 | 1638 | 1.04 | 1.39 | 1.36 (1.21-1.54) | 1.29 | 45.0 | 1.40 (478) | 1.34 (1160) | $8090 | $12781 | +58% |

Dollars: $8090 in fees, $12781 won, +58% ROI over 22 nights (80% range -27% to +165%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -19%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

**Concentration and uniqueness**: per night, across all my teams. Top player: my most-used player and the share of my teams with him; top pair likewise; cores: a team's three earliest picks, how many of my teams share the most-used one. Uniqueness (flagship, from the contest measures): the median share of the field holding 4+ of a team's 6, and my teams with an exact duplicate in the field.

| Night | My teams | Top player | Top pair | Biggest shared core | Field share with 4+ of 6 (median) | Teams with a duplicate |
|---|---|---|---|---|---|---|
| 2026-10-20 | 4 | LeBron James 50% | Dylan Harper + Tyrese Maxey 50% | 1 (LeBron James + Tyrese Maxey + Victor Wembanyama) | 5.2% | 3 of 4 |
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
| 2026-11-09 | 95 | Paul Reed 47% | Paul Reed + Kevin Durant 18% | 4 (Alperen Sengun + Cade Cunningham + Kevin Durant) | 0.5% | 4 of 80 |
| 2026-11-10 | 80 | Desmond Bane 40% | Desmond Bane + Isaiah Hartenstein 19% | 4 (Paul George + Darius Acuff Jr. + Karl-Anthony Towns) | 1.0% | 21 of 80 |
| 2026-11-11 | 80 | Pascal Siakam 44% | Keyonte George + Cameron Boozer 18% | 4 (Nikola Jokic + Deni Avdija + Pascal Siakam) | 0.6% | 9 of 80 |

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.37 (1.22-1.55) at 10%, 0.99 at 1%; finish -5.6; 1584 teams, 20 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.24 (1.14-1.35) at 10%, 1.51 at 1%; finish -2.6; 382173 teams, 20 slates | 1.20 (1.08-1.33) at 10%, 1.35 at 1%; finish -2.2; 284592 teams, 15 slates | 1.40 (1.30-1.51) at 10%, 2.13 at 1%; finish -3.9; 97581 teams, 5 slates | 1.74 (1.38-2.22) at 10%, 1.23 at 1%; finish -7.8; 2560 teams, 20 slates | RULE for | RULE for |
|   AM only | 1.23 (1.14-1.32) at 10%, 1.39 at 1%; finish -2.0; 106779 teams, 17 slates | 1.10 (1.03-1.19) at 10%, 1.13 at 1%; finish -0.6; 74222 teams, 12 slates | 1.56 (1.36-1.80) at 10%, 2.16 at 1%; finish -5.1; 32557 teams, 5 slates | 1.28 (0.99-1.59) at 10%, 0.47 at 1%; finish -3.9; 619 teams, 13 slates | RULE for | RULE for |
|   PM only | 1.24 (1.11-1.37) at 10%, 1.53 at 1%; finish -2.8; 275386 teams, 20 slates | 1.23 (1.07-1.41) at 10%, 1.41 at 1%; finish -2.8; 210367 teams, 15 slates | 1.30 (1.14-1.43) at 10%, 2.04 at 1%; finish -2.9; 65019 teams, 5 slates | 1.90 (1.40-2.50) at 10%, 1.53 at 1%; finish -8.9; 1941 teams, 20 slates | RULE for | RULE for |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.50 (1.24-1.87) at 10%, 2.67 at 1%; finish -6.5; 22559 teams, 7 slates | 1.34 (1.14-1.55) at 10%, 2.27 at 1%; finish -4.9; 20691 teams, 6 slates | 6.09 at 10%, 53.73 at 1%; finish -23.5; 1868 teams, 1 slates | 2.03 (0.85-3.07) at 10%, 1.73 at 1%; finish -11.5; 81 teams, 7 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.23 (1.13-1.34) at 10%, 1.32 at 1%; finish -2.6; 1593294 teams, 20 slates | 1.23 (1.09-1.37) at 10%, 1.36 at 1%; finish -2.3; 1150688 teams, 15 slates | 1.24 (1.08-1.39) at 10%, 1.23 at 1%; finish -3.4; 442606 teams, 5 slates | 1.56 (1.28-1.84) at 10%, 1.10 at 1%; finish -6.5; 11715 teams, 20 slates | RULE for | RULE for |
|   T3 | 1.07 (0.74-1.51) at 10%, 1.10 at 1%; finish -0.9; 140385 teams, 15 slates | 1.32 (0.79-2.03) at 10%, 1.51 at 1%; finish -3.7; 99003 teams, 12 slates | 0.69 (0.52-0.85) at 10%, 0.55 at 1%; finish +5.8; 41382 teams, 3 slates | 1.20 (0.81-1.68) at 10%, 0.00 at 1%; finish -6.6; 1151 teams, 15 slates | no lean | no lean |
|   T4 | 1.23 (1.09-1.38) at 10%, 1.38 at 1%; finish -2.1; 198189 teams, 17 slates | 1.26 (1.07-1.42) at 10%, 1.44 at 1%; finish -3.0; 142106 teams, 13 slates | 1.13 (0.89-1.50) at 10%, 1.17 at 1%; finish +0.1; 56083 teams, 4 slates | 1.78 (1.35-2.33) at 10%, 1.67 at 1%; finish -6.9; 1373 teams, 16 slates | RULE for | RULE for |
|   T5 | 1.28 (1.12-1.43) at 10%, 1.42 at 1%; finish -3.1; 1254539 teams, 20 slates | 1.24 (1.04-1.42) at 10%, 1.39 at 1%; finish -2.3; 909452 teams, 15 slates | 1.39 (1.10-1.73) at 10%, 1.49 at 1%; finish -5.4; 345087 teams, 5 slates | 1.61 (1.25-1.99) at 10%, 1.24 at 1%; finish -6.9; 9191 teams, 19 slates | RULE for | RULE for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.16 (1.06-1.27) at 10%, 1.26 at 1%; finish -1.1; 855026 teams, 20 slates | 1.21 (1.11-1.33) at 10%, 1.33 at 1%; finish -1.9; 667991 teams, 15 slates | 1.00 (0.76-1.28) at 10%, 1.03 at 1%; finish +1.6; 187035 teams, 5 slates | 1.63 (1.37-1.88) at 10%, 1.60 at 1%; finish -6.6; 4929 teams, 20 slates | LEAN for | RULE for **(changes)** |
|   T1 | 1.69 (1.26-2.31) at 10%, 2.62 at 1%; finish -5.3; 112896 teams, 12 slates | 2.02 (1.58-2.61) at 10%, 3.54 at 1%; finish -7.8; 86150 teams, 9 slates | 0.61 (0.38-2.54) at 10%, 0.50 at 1%; finish +2.8; 26746 teams, 3 slates | 2.24 (1.20-3.44) at 10%, 3.51 at 1%; finish -9.1; 554 teams, 11 slates | LEAN for | LEAN for |
|   T2 | 1.13 (0.98-1.31) at 10%, 1.17 at 1%; finish -0.5; 313105 teams, 18 slates | 1.13 (0.95-1.35) at 10%, 1.10 at 1%; finish -1.3; 234575 teams, 13 slates | 1.14 (0.87-1.52) at 10%, 1.41 at 1%; finish +1.8; 78530 teams, 5 slates | 1.52 (1.24-1.85) at 10%, 1.47 at 1%; finish -5.8; 1943 teams, 18 slates | LEAN for | LEAN for |
|   T3 | 1.30 (1.05-1.59) at 10%, 1.41 at 1%; finish -4.0; 212072 teams, 18 slates | 1.44 (1.11-1.81) at 10%, 1.78 at 1%; finish -5.0; 166202 teams, 13 slates | 0.99 (0.84-1.34) at 10%, 0.87 at 1%; finish -0.3; 45870 teams, 5 slates | 2.09 (1.67-2.52) at 10%, 1.73 at 1%; finish -11.7; 1343 teams, 18 slates | LEAN for | LEAN for |
|   T4 | 0.94 (0.81-1.12) at 10%, 0.89 at 1%; finish +1.6; 216833 teams, 19 slates | 0.94 (0.79-1.17) at 10%, 0.90 at 1%; finish +1.7; 180984 teams, 15 slates | 0.95 (0.59-1.28) at 10%, 0.77 at 1%; finish +1.3; 35849 teams, 4 slates | 1.15 (0.96-1.39) at 10%, 0.81 at 1%; finish -1.5; 1089 teams, 18 slates | no lean | no lean |
|   T5 | none | none | none | none | not enough | not enough |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.05 (0.76-1.31) at 10%, 1.14 at 1%; finish -1.2; 63240 teams, 10 slates | 1.11 (0.78-1.41) at 10%, 1.18 at 1%; finish -2.5; 48789 teams, 9 slates | 0.73 at 10%, 0.82 at 1%; finish +3.5; 14451 teams, 1 slates | 1.28 (1.10-1.57) at 10%, 0.74 at 1%; finish -3.5; 241 teams, 7 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.14 (1.05-1.23) at 10%, 1.26 at 1%; finish -2.4; 1640168 teams, 17 slates | 1.04 (0.97-1.12) at 10%, 1.05 at 1%; finish -1.5; 951139 teams, 12 slates | 1.30 (1.12-1.50) at 10%, 1.66 at 1%; finish -3.6; 689029 teams, 5 slates | 1.46 (1.23-1.67) at 10%, 0.62 at 1%; finish -4.3; 7076 teams, 14 slates | RULE for | RULE for |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 1.20 (0.93-1.57) at 10%, 1.42 at 1%; finish -2.4; 105347 teams, 16 slates | 1.31 (0.94-1.83) at 10%, 1.74 at 1%; finish -3.9; 76573 teams, 12 slates | 0.97 (0.73-1.40) at 10%, 0.91 at 1%; finish +1.5; 28774 teams, 4 slates | 1.72 (1.21-2.25) at 10%, 2.47 at 1%; finish -10.7; 696 teams, 16 slates | LEAN for | LEAN for |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.89 (0.76-1.10) at 10%, 0.82 at 1%; finish +2.3; 61295 teams, 15 slates | 0.89 (0.74-1.12) at 10%, 0.87 at 1%; finish +2.9; 48370 teams, 11 slates | 0.90 (0.53-1.65) at 10%, 0.58 at 1%; finish +0.2; 12925 teams, 4 slates | 0.79 (0.57-1.06) at 10%, 0.00 at 1%; finish -3.7; 250 teams, 13 slates | no lean | no lean |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 0.73 (0.63-0.84) at 10%, 0.54 at 1%; finish +3.6; 737989 teams, 19 slates | 0.78 (0.66-0.96) at 10%, 0.64 at 1%; finish +2.6; 549368 teams, 14 slates | 0.59 (0.51-0.72) at 10%, 0.34 at 1%; finish +6.4; 188621 teams, 5 slates | 1.38 (1.06-1.72) at 10%, 0.53 at 1%; finish -6.4; 2050 teams, 19 slates | RULE against | RULE against |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.89 (0.71-1.09) at 10%, 0.90 at 1%; finish +2.4; 118567 teams, 17 slates | 0.77 (0.60-1.02) at 10%, 0.69 at 1%; finish +3.2; 74778 teams, 12 slates | 1.13 (0.78-1.37) at 10%, 1.53 at 1%; finish +1.1; 43789 teams, 5 slates | 1.48 (0.90-2.20) at 10%, 1.89 at 1%; finish -6.0; 334 teams, 14 slates | no lean | no lean |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.11 (0.82-1.43) at 10%, 1.21 at 1%; finish -1.0; 19326 teams, 14 slates | 0.84 (0.75-0.94) at 10%, 0.71 at 1%; finish +1.7; 9832 teams, 9 slates | 1.48 (0.85-2.31) at 10%, 2.00 at 1%; finish -3.7; 9494 teams, 5 slates | 1.01 (0.66-1.43) at 10%, 1.47 at 1%; finish +0.4; 153 teams, 11 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.05 (0.85-1.28) at 10%, 1.03 at 1%; finish -1.1; 24419 teams, 16 slates | 1.00 (0.76-1.22) at 10%, 0.99 at 1%; finish -0.6; 19154 teams, 12 slates | 1.26 (0.77-1.78) at 10%, 1.17 at 1%; finish -2.8; 5265 teams, 4 slates | 1.31 (0.76-2.04) at 10%, 0.00 at 1%; finish -6.9; 139 teams, 13 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 0.98 (0.84-1.15) at 10%, 1.02 at 1%; finish +1.1; 229116 teams, 14 slates | 1.17 (1.01-1.34) at 10%, 1.54 at 1%; finish -0.7; 135868 teams, 9 slates | 0.79 (0.61-1.02) at 10%, 0.69 at 1%; finish +3.6; 93248 teams, 5 slates | 1.42 (1.04-1.93) at 10%, 0.97 at 1%; finish -1.9; 881 teams, 13 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 1.01 (0.86-1.18) at 10%, 0.91 at 1%; finish -0.8; 221966 teams, 15 slates | 0.99 (0.81-1.22) at 10%, 0.89 at 1%; finish -1.0; 166338 teams, 10 slates | 1.06 (0.86-1.24) at 10%, 0.96 at 1%; finish -0.4; 55628 teams, 5 slates | 1.02 (0.63-1.63) at 10%, 0.16 at 1%; finish -2.9; 1218 teams, 14 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | 0.57 at 10%, 0.08 at 1%; finish +1.4; 1190 teams, 1 slates | none | 0.57 at 10%, 0.08 at 1%; finish +1.4; 1190 teams, 1 slates | 0.67 at 10%, 0.00 at 1%; finish -6.3; 20 teams, 1 slates | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 0.90 (0.77-1.06) at 10%, 0.75 at 1%; finish +0.6; 8053 teams, 16 slates | 0.82 (0.64-1.02) at 10%, 0.62 at 1%; finish +1.2; 5640 teams, 11 slates | 1.10 (0.98-1.27) at 10%, 1.08 at 1%; finish -1.0; 2413 teams, 5 slates | 1.20 (0.74-1.48) at 10%, 0.00 at 1%; finish -6.9; 50 teams, 5 slates | no lean | no lean |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 0.98 (0.85-1.14) at 10%, 0.97 at 1%; finish +1.2; 31098 teams, 11 slates | 0.84 (0.75-0.92) at 10%, 0.76 at 1%; finish +2.5; 20663 teams, 7 slates | 1.29 (0.98-1.51) at 10%, 1.45 at 1%; finish -1.4; 10435 teams, 4 slates | 1.02 (0.59-1.53) at 10%, 0.51 at 1%; finish -0.1; 192 teams, 11 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 1.02 (0.86-1.23) at 10%, 0.87 at 1%; finish -1.4; 15993 teams, 15 slates | 1.05 (0.82-1.43) at 10%, 1.05 at 1%; finish -1.7; 8955 teams, 10 slates | 0.99 (0.77-1.24) at 10%, 0.66 at 1%; finish -1.1; 7038 teams, 5 slates | 2.06 (0.87-3.26) at 10%, 4.95 at 1%; finish -8.0; 44 teams, 10 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.36 (1.09-1.76) at 10%, 1.56 at 1%; finish -3.5; 10718 teams, 12 slates | 1.54 (1.23-2.26) at 10%, 1.90 at 1%; finish -5.3; 6330 teams, 8 slates | 1.11 (0.57-1.71) at 10%, 1.07 at 1%; finish -0.9; 4388 teams, 4 slates | 1.38 (0.72-2.59) at 10%, 0.00 at 1%; finish -5.3; 31 teams, 7 slates | RULE for | RULE for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.06 (0.84-1.32) at 10%, 1.37 at 1%; finish +0.3; 52433 teams, 17 slates | 1.28 (1.00-1.63) at 10%, 1.94 at 1%; finish -1.6; 39623 teams, 13 slates | 0.58 (0.49-0.75) at 10%, 0.42 at 1%; finish +6.3; 12810 teams, 4 slates | 2.27 (1.47-3.03) at 10%, 1.12 at 1%; finish -11.6; 294 teams, 15 slates | no lean | no lean |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 1.04 (0.88-1.23) at 10%, 1.14 at 1%; finish -0.8; 233083 teams, 19 slates | 1.00 (0.81-1.19) at 10%, 0.99 at 1%; finish -0.8; 184926 teams, 14 slates | 1.28 (1.03-2.00) at 10%, 2.35 at 1%; finish -1.0; 48157 teams, 5 slates | 1.21 (0.93-1.64) at 10%, 0.45 at 1%; finish -6.9; 1462 teams, 18 slates | no lean | no lean |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 0.99 (0.85-1.17) at 10%, 0.99 at 1%; finish -0.4; 128426 teams, 19 slates | 0.93 (0.78-1.16) at 10%, 0.85 at 1%; finish +0.4; 101032 teams, 14 slates | 1.20 (0.85-1.89) at 10%, 1.49 at 1%; finish -3.0; 27394 teams, 5 slates | 1.23 (0.97-1.51) at 10%, 0.61 at 1%; finish -6.5; 738 teams, 19 slates | no lean | no lean |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.24 (1.04-1.52) at 10%, 1.55 at 1%; finish -2.2; 136771 teams, 17 slates | 1.28 (1.03-1.63) at 10%, 1.64 at 1%; finish -2.6; 105549 teams, 12 slates | 1.10 (0.83-1.64) at 10%, 1.22 at 1%; finish -0.9; 31222 teams, 5 slates | 0.85 (0.52-1.22) at 10%, 0.00 at 1%; finish +3.3; 832 teams, 14 slates | LEAN for | LEAN for |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 | RULE for | +2.6 | +2.5 (96%) | +0.1 (4%) | -0.3 | 1.18 (1.07-1.30) at 10%, 1.39 at 1%; finish -1.9; 382173 teams, 20 slates | RULE for |
| ownership-tiebreak-t5 AM only | RULE for | +2.0 | +1.6 (80%) | +0.4 (20%) | -2.3 | 1.14 (1.03-1.26) at 10%, 1.24 at 1%; finish -1.0; 106782 teams, 17 slates | RULE for |
| ownership-tiebreak-t5 PM only | RULE for | +2.7 | +2.8 (101%) | -0.0 (-1%) | +0.3 | 1.19 (1.06-1.34) at 10%, 1.45 at 1%; finish -2.4; 275386 teams, 20 slates | RULE for |
| leverage-t2-t4 | RULE for | +6.4 | +7.0 (110%) | -0.6 (-10%) | -0.0 | 1.67 (1.29-2.43) at 10%, 2.71 at 1%; finish -7.4; 22556 teams, 7 slates | RULE for |
| value-up-middle-t5 | RULE for | +2.3 | +1.5 (65%) | +0.8 (35%) | -0.7 | 1.20 (1.09-1.31) at 10%, 1.29 at 1%; finish -2.1; 1593294 teams, 20 slates | RULE for |
| value-up-middle-t5 T4 | RULE for | +2.4 | +2.0 (80%) | +0.5 (20%) | +2.2 | 1.16 (1.01-1.33) at 10%, 1.28 at 1%; finish -1.5; 198200 teams, 17 slates | LEAN for |
| value-up-middle-t5 T5 | RULE for | +2.6 | +1.1 (45%) | +1.4 (55%) | +0.6 | 1.28 (1.12-1.45) at 10%, 1.39 at 1%; finish -3.2; 1254495 teams, 20 slates | RULE for |
| pricey-flags | LEAN for | +1.4 | +2.1 (153%) | -0.7 (-53%) | +2.8 | 1.16 (1.04-1.29) at 10%, 1.26 at 1%; finish -1.3; 855058 teams, 20 slates | LEAN for |
| pricey-flags T1 | LEAN for | +4.1 | +5.5 (134%) | -1.4 (-34%) | +8.7 | 1.55 (1.07-2.32) at 10%, 2.28 at 1%; finish -4.5; 112910 teams, 12 slates | LEAN for |
| pricey-flags T2 | LEAN for | +1.0 | +1.8 (179%) | -0.8 (-79%) | +2.5 | 1.14 (0.97-1.34) at 10%, 1.20 at 1%; finish -0.8; 313109 teams, 18 slates | LEAN for |
| pricey-flags T3 | LEAN for | +4.0 | +5.4 (134%) | -1.4 (-34%) | +4.7 | 1.30 (1.05-1.60) at 10%, 1.43 at 1%; finish -4.0; 212077 teams, 18 slates | LEAN for |
| am-t5-button-order | RULE for | +2.1 | +1.1 (51%) | +1.0 (49%) | +0.9 | 1.16 (1.07-1.25) at 10%, 1.27 at 1%; finish -2.6; 1640196 teams, 17 slates | RULE for |
| pm-t2-adp-etr2 | LEAN for | +2.5 | +1.9 (76%) | +0.6 (24%) | +0.8 | 1.14 (0.87-1.52) at 10%, 1.29 at 1%; finish -2.0; 105347 teams, 16 slates | no lean |
| pm-t5-adp-value | RULE against | -3.3 | -3.2 (96%) | -0.1 (4%) | -1.2 | 0.75 (0.65-0.88) at 10%, 0.58 at 1%; finish +3.2; 737995 teams, 19 slates | RULE against |
| beneficiary-round6:played | RULE for | +2.7 | +2.2 (80%) | +0.5 (20%) | - (holding) | 1.27 (1.03-1.64) at 10%, 1.41 at 1%; finish -2.8; 10717 teams, 12 slates | LEAN for |
| am-t5-other-reads | LEAN for | +2.1 | +0.2 (8%) | +2.0 (92%) | +1.1 | 1.24 (1.03-1.52) at 10%, 1.52 at 1%; finish -2.2; 136806 teams, 17 slates | LEAN for |
| turn 1/2: a. reach vs trust | LEAN against | -0.7 | +0.6 (-85%) | -1.3 (185%) | -0.6 | 0.74 (0.59-0.95) at 10%, 0.52 at 1%; finish +2.1; 28341 teams, 20 slates | LEAN against |
| turn 1/2: fallers vs trust | LEAN for | +3.0 | +0.8 (28%) | +2.2 (72%) | +3.6 | 1.37 (1.01-1.99) at 10%, 1.56 at 1%; finish -3.9; 43533 teams, 20 slates | LEAN for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +2.0 | +2.5 (125%) | -0.5 (-25%) | +1.4 | 1.36 (0.73-2.27) at 10%, 1.43 at 1%; finish -0.4; 5140 teams, 16 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | +0.8 | +3.9 (497%) | -3.1 (-397%) | +1.2 | 1.05 (0.91-1.20) at 10%, 1.29 at 1%; finish +0.9; 24712 teams, 20 slates | no lean |
| turn 2/3: fallers vs trust | LEAN for | +2.1 | +0.7 (33%) | +1.4 (67%) | +1.9 | 1.18 (1.02-1.37) at 10%, 1.19 at 1%; finish -3.7; 17906 teams, 20 slates | LEAN for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +7.6 | +9.0 (120%) | -1.5 (-20%) | +6.2 | 1.54 (1.27-1.82) at 10%, 2.27 at 1%; finish -5.6; 6003 teams, 20 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | LEAN for | +1.3 | +1.2 (92%) | +0.1 (8%) | - (holding) | 0.97 (0.86-1.12) at 10%, 1.02 at 1%; finish +0.7; 135896 teams, 20 slates | no lean |
| stack: Same-position teammates | RULE against | -3.7 | -7.9 (217%) | +4.3 (-117%) | - (holding) | 0.75 (0.65-0.86) at 10%, 0.91 at 1%; finish +4.2; 74225 teams, 20 slates | RULE against |
| stack: Same-position teammates, spread 5+ | LEAN against | -0.9 | -3.1 (327%) | +2.1 (-227%) | - (holding) | 0.85 (0.74-0.98) at 10%, 0.79 at 1%; finish +1.7; 26727 teams, 17 slates | LEAN against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 12 | 187 | +0.3 | -1 | -10 |
| the swap board, near-ties least drafted first (leverage) | 12 | 187 | +0.1 | +1 | -90 |
| the swap board, near-ties most drafted first (spread) | 12 | 187 | +0.0 | +0 | -33 |

Leverage against spread: the leverage board's swaps would have made -1 top-10% finishes and $+57 against the spread board's (real minus each, differenced). Leverage put 67% of a night's replayed swaps on one player, spread 53%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.08 (0.92-1.28) at 10%, 1.04 at 1%; finish -1.2; 25291 teams, 16 slates | +1.1 | +1.0 (86%) | +0.2 (14%) | 1.02 (0.88-1.21) at 10%, 0.96 at 1%; finish -0.5; 25290 teams, 16 slates | no lean |
| rounds 1-2 | 3.41 (2.71-4.05) at 10%, 10.75 at 1%; finish -15.3; 743 teams, 3 slates | +14.9 | +12.7 (85%) | +2.2 (15%) | 3.19 (2.64-3.99) at 10%, 9.37 at 1%; finish -14.8; 743 teams, 3 slates | LEAN for |
| rounds 3-4 | 1.07 (0.81-1.40) at 10%, 0.99 at 1%; finish +0.0; 6590 teams, 9 slates | +0.0 | +4.4 | -4.4 | 1.06 (0.80-1.39) at 10%, 0.99 at 1%; finish -0.0; 6587 teams, 9 slates | no lean |
| rounds 5-6 or undrafted | 1.05 (0.89-1.24) at 10%, 0.97 at 1%; finish -1.3; 18129 teams, 14 slates | +1.2 | -0.7 (-63%) | +1.9 (163%) | 0.99 (0.87-1.16) at 10%, 0.89 at 1%; finish -0.5; 18129 teams, 14 slates | no lean |

## 3c. Splits for Monday: teammates and takes by source

Each with the price-split check (section 3b). Lift: top-10% against same-contest, same-price teams.

### Teammates, by the rounds paid for them

A: teams with that teammate pair; B: teams with no two teammates at all (so same- and different-position pairs face the same comparison).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pair | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| Same position, both rounds 1-3 | 1.04 (0.60-1.49) at 10%, 0.99 at 1%; finish -2.9; 8976 teams, 12 slates | +1.8 | -2.9 (-164%) | +4.7 (264%) | 1.04 (0.60-1.47) at 10%, 1.05 at 1%; finish -2.6; 8976 teams, 12 slates | no lean |
| Same position, one in rounds 1-3 and one in 4-6 | 0.88 (0.79-0.96) at 10%, 0.87 at 1%; finish +1.9; 32888 teams, 18 slates | -1.6 | -5.0 (305%) | +3.4 (-205%) | 0.77 (0.69-0.84) at 10%, 0.70 at 1%; finish +3.5; 32830 teams, 18 slates | RULE against |
| Same position, both rounds 4-6 | 1.15 (1.03-1.29) at 10%, 1.36 at 1%; finish -2.9; 14959 teams, 18 slates | +2.2 | -0.9 (-40%) | +3.1 (140%) | 1.13 (1.00-1.26) at 10%, 1.35 at 1%; finish -2.6; 14958 teams, 18 slates | LEAN for |
| Different-position teammates (any rounds) | 1.13 (1.05-1.21) at 10%, 1.26 at 1%; finish -1.4; 135479 teams, 18 slates | +1.2 | -1.2 (-104%) | +2.4 (204%) | 1.00 (0.85-1.19) at 10%, 1.06 at 1%; finish +0.7; 116794 teams, 18 slates | no lean |

### Your takes by source (takes_history.csv)

A: teams holding the player you put first; B: the button's first, in the take's window (field and mine). Field drafted%: the share of that window's pods that took each. Points: the takes file's average gain per take (yours).

| Source | Window | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pick | From the other picks | Lift matched on the other picks' price | Verdict that survives | Takes, points per take | Field drafted%: yours / the button's | Yours the more drafted |
|---|---|---|---|---|---|---|---|---|---|---|
| ETR | PM | 1.18 (0.84-1.63) at 10%, 1.30 at 1%; finish -1.8; 59788 teams, 8 slates | +1.3 | +1.5 (116%) | -0.2 (-16%) | 1.22 (0.88-1.67) at 10%, 1.36 at 1%; finish -2.5; 59783 teams, 8 slates | no lean | 125, +1.1 | 23% / 36% | 23% |
| ETR | both | 1.18 (0.84-1.63) at 10%, 1.30 at 1%; finish -1.8; 59788 teams, 8 slates | +1.3 | +1.5 (116%) | -0.2 (-16%) | 1.22 (0.88-1.67) at 10%, 1.36 at 1%; finish -2.5; 59783 teams, 8 slates | no lean | 125, +1.1 | 23% / 36% | 23% |
| Bagel | PM | 0.97 (0.83-1.16) at 10%, 1.01 at 1%; finish +0.7; 124094 teams, 11 slates | -0.8 | -0.7 (96%) | -0.0 (4%) | 0.96 (0.83-1.16) at 10%, 0.99 at 1%; finish +0.8; 124091 teams, 11 slates | no lean | 134, -2.8 | 46% / 44% | 50% |
| Bagel | both | 0.97 (0.83-1.16) at 10%, 1.01 at 1%; finish +0.7; 124094 teams, 11 slates | -0.8 | -0.7 (96%) | -0.0 (4%) | 0.96 (0.83-1.16) at 10%, 0.99 at 1%; finish +0.8; 124091 teams, 11 slates | no lean | 134, -2.8 | 46% / 44% | 50% |
| Bagel+ETR | PM | 1.02 (0.85-1.27) at 10%, 0.99 at 1%; finish -0.1; 187659 teams, 10 slates | +0.3 | +0.4 | -0.1 | 1.05 (0.88-1.31) at 10%, 1.04 at 1%; finish -0.5; 187654 teams, 10 slates | no lean | 222, +0.9 | 41% / 50% | 36% |
| Bagel+ETR | both | 1.02 (0.85-1.27) at 10%, 0.99 at 1%; finish -0.1; 187659 teams, 10 slates | +0.3 | +0.4 | -0.1 | 1.05 (0.88-1.31) at 10%, 1.04 at 1%; finish -0.5; 187654 teams, 10 slates | no lean | 222, +0.9 | 41% / 50% | 36% |
| NEWS | AM | 1.06 (0.95-1.22) at 10%, 1.12 at 1%; finish -1.0; 328535 teams, 17 slates | +0.8 | -0.8 (-104%) | +1.7 (204%) | 1.09 (0.97-1.26) at 10%, 1.16 at 1%; finish -1.4; 328540 teams, 17 slates | LEAN for | 806, -0.9 | 35% / 47% | 33% |
| NEWS | PM | 0.95 (0.84-1.04) at 10%, 0.90 at 1%; finish -0.3; 212894 teams, 19 slates | +0.1 | -0.1 | +0.2 | 0.97 (0.85-1.08) at 10%, 0.92 at 1%; finish -0.6; 212903 teams, 19 slates | no lean | 369, -1.4 | 30% / 44% | 25% |
| NEWS | both | 1.02 (0.94-1.10) at 10%, 1.03 at 1%; finish -0.8; 541441 teams, 20 slates | +0.6 | -0.6 (-101%) | +1.2 (201%) | 1.05 (0.96-1.14) at 10%, 1.06 at 1%; finish -1.2; 541451 teams, 20 slates | no lean | 1175, -1.0 | 34% / 46% | 30% |
| OTHER | AM | 1.22 (0.66-1.89) at 10%, 1.11 at 1%; finish -3.2; 39499 teams, 3 slates | +4.2 | +1.0 (24%) | +3.2 (76%) | 1.24 (0.72-1.82) at 10%, 1.15 at 1%; finish -3.2; 39499 teams, 3 slates | no lean | 114, +2.3 | 36% / 49% | 39% |
| OTHER | PM | 0.99 (0.80-1.20) at 10%, 1.12 at 1%; finish +1.5; 75664 teams, 13 slates | -1.2 | -0.5 (38%) | -0.7 (62%) | 0.93 (0.74-1.14) at 10%, 1.05 at 1%; finish +2.2; 75662 teams, 13 slates | no lean | 249, -0.8 | 32% / 46% | 30% |
| OTHER | both | 1.09 (0.85-1.31) at 10%, 1.17 at 1%; finish -0.2; 115163 teams, 13 slates | +0.8 | +0.2 (28%) | +0.5 (72%) | 1.06 (0.81-1.27) at 10%, 1.14 at 1%; finish +0.1; 115161 teams, 13 slates | no lean | 363, +0.2 | 33% / 47% | 33% |
| all | AM | 1.09 (0.96-1.24) at 10%, 1.13 at 1%; finish -1.3; 368034 teams, 17 slates | +1.2 | -0.6 (-49%) | +1.8 (149%) | 1.11 (0.99-1.27) at 10%, 1.17 at 1%; finish -1.7; 368039 teams, 17 slates | LEAN for | 920, -0.5 | 35% / 47% | 33% |
| all | PM | 1.02 (0.94-1.12) at 10%, 1.04 at 1%; finish -0.2; 660128 teams, 20 slates | +0.2 | +0.1 | +0.1 | 1.04 (0.95-1.14) at 10%, 1.07 at 1%; finish -0.5; 660140 teams, 20 slates | no lean | 1099, -0.7 | 34% / 45% | 31% |
| all | both | 1.05 (0.97-1.13) at 10%, 1.07 at 1%; finish -0.7; 1028179 teams, 20 slates | +0.6 | -0.2 (-27%) | +0.8 (127%) | 1.07 (0.99-1.16) at 10%, 1.10 at 1%; finish -1.0; 1028179 teams, 20 slates | LEAN for | 2019, -0.6 | 35% / 46% | 32% |

## 3d. Candidate: my AM teams against my PM teams (for the Monday section; not a proposal)

A = my AM teams, B = my PM teams, inside the same contest and price group. Raw: each window's top-10% rate over the field's 10%. Then what differs, per team.

| | Teams | Raw top-10% | VALUE picks | PRICEY picks | Tagged picks | Projected drafted% of picks | Field sharing 4+ of 6 | Teams with an exact duplicate | Price | Points over price | Swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AM | 478 | 1.40 | 1.70 | 0.68 | 0.36 | 92% | 1.02% | 19% | 220.2 | +3.4 | 0.44 |
| PM | 1106 | 1.37 | 1.48 | 0.64 | 0.14 | 90% | 1.23% | 22% | 218.1 | +6.4 | 0.10 |

Inside the same contest and price group, AM against PM: 1.07 (0.81-1.40) at 10%, 1.25 at 1%; finish +3.7; 476 teams, 15 slates (five price groups); 0.95 (0.73-1.25) at 10%, 1.71 at 1%; finish +4.2; 454 teams, 15 slates (ten).

## 3e. Candidates for 11-16 (asked 2026-11-09; not proposals)

### 1. Same-position teammates: source, examples, and starter/backup instead

Position: Underdog's own position on the slate (the record's `pos`), grouped G (PG, SG, G), F (SF, PF, F), C. Underdog scores everyone as flex, so position matters here only as a stand-in for sharing minutes and touches. Five early/late same-position pairs on 2026-11-11's rosters:

- Luka Doncic (PG, round 1) + Austin Reaves (SG, round 4), LAL
- Kevin Durant (PF, round 3) + Amen Thompson (SF, round 6), HOU
- Shai Gilgeous-Alexander (PG, round 1) + Jared McCain (SG, round 6), OKC
- Jalen Brunson (PG, round 3) + Josh Hart (SG, round 6), NYK
- Donovan Mitchell (SG, round 2) + James Harden (PG, round 6), CLE

Starter and direct backup instead of position: the starter averages 28+ minutes; his backup scores 4+ more points a game when the starter sits. Both from the morning file as it stood at that night's lock (the mirror's history: games through the night before, nothing later). The with/without splits start in the morning file around 10-29, so earlier nights have no pairs. Against teams with no two teammates:

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Same position, early + late (the approved card row) | 0.88 (0.79-0.96) at 10%, 0.87 at 1%; finish +1.9; 32888 teams, 18 slates | -1.6 | -5.0 (305%) | +3.4 (-205%) | - (holding) | 0.77 (0.69-0.84) at 10%, 0.70 at 1%; finish +3.5; 32830 teams, 18 slates | RULE against |
| Starter + his backup, any rounds | 0.65 (0.46-0.88) at 10%, 0.55 at 1%; finish +7.6; 14116 teams, 10 slates | -6.8 | -10.7 (158%) | +3.9 (-58%) | - (holding) | 0.58 (0.40-0.78) at 10%, 0.43 at 1%; finish +8.4; 14117 teams, 10 slates | RULE against |
| Starter early (rounds 1-3) + his backup late (rounds 4-6) | 0.57 (0.40-0.77) at 10%, 0.26 at 1%; finish +6.9; 5747 teams, 9 slates | -6.5 | -9.1 (140%) | +2.6 (-40%) | - (holding) | 0.51 (0.35-0.73) at 10%, 0.21 at 1%; finish +8.2; 5748 teams, 9 slates | RULE against |

### 2. Fallers: the definitions behind card-fallers

Ranks are the night's closing-ADP order. 6-drafter pods (4-drafter in brackets):
- **1/2 turn** (picks 6-7, or 5 and 8 [3-4, or 3 and 6]): your first player is a top-4 [top-2] ADP rank and your second is ranked 5-8 [3-6]. In the draft room: a top-4 [top-2] player still there at your turn pick; take him.
- **2/3 turn** (picks 12-13, or 11 and 14 [8-9, or 7 and 10]), for the 1.01 and 1.02 drafters: your second player is ranked 9th or better [5th or better], 3+ ranks ahead of your turn pick; take him.
Measured against same-contest, same-price teams that took the ADP-order pair at that turn (the trusting teams); the price-split check is in 3b. Fallers elsewhere in the draft: part 4 below.

### 3. Exposure, not order: T3 VALUE and T4 PRICEY

Against same-contest, same-price teams without (at each team's draft window).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| 2+ T3 VALUE players | 1.28 (0.86-1.66) at 10%, 1.54 at 1%; finish -4.1; 11488 teams, 13 slates | +4.6 | +6.8 (148%) | -2.2 (-48%) | - (holding) | 1.28 (0.86-1.65) at 10%, 1.54 at 1%; finish -4.0; 11488 teams, 13 slates | no lean |
| 1+ T3 VALUE player | 0.89 (0.74-1.07) at 10%, 0.77 at 1%; finish +0.1; 84289 teams, 17 slates | +0.2 | +1.5 | -1.3 | - (holding) | 0.83 (0.71-0.98) at 10%, 0.75 at 1%; finish +1.4; 84280 teams, 17 slates | LEAN against |
| A T4 PRICEY player | 1.02 (0.85-1.21) at 10%, 1.08 at 1%; finish -1.0; 116203 teams, 20 slates | +0.5 | +1.0 (199%) | -0.5 (-99%) | - (holding) | 0.90 (0.73-1.10) at 10%, 0.95 at 1%; finish -0.4; 115820 teams, 20 slates | no lean |

### 4. Fallers in every round

A team's k-th player by the ADP it paid stands for its round-k pick (pick order isn't public, so this is a lower bound on the slide). A faller was paid an ADP 3+ picks before that round's first pick (round 3 on 6 drafters: ADP 10 or better). Explained: tagged at the team's window, or his tag changed between Lock AM and lock. A: teams with that faller in round k; B: teams whose round-k player wasn't a faller.

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Round 1, nothing explains it | none | - | - | - |
| Round 1, explained | none | - | - | - |
| Round 2, nothing explains it | 0.94 (0.00-3.58) at 10%, 10.57 at 1%; finish +3.4; 12 teams, 4 slates | -3.2 | +1.5 (-48%) | -4.7 (148%) | +3.5 | 0.90 (0.00-3.81) at 10%, 8.93 at 1%; finish +3.0; 12 teams, 4 slates | not enough |
| Round 2, explained (tag or news) | 5.48 at 10%, 0.00 at 1%; finish -36.6; 1 teams, 1 slates | +49.6 | +13.9 (28%) | +35.7 (72%) | +23.1 | 7.37 at 10%, 0.00 at 1%; finish -41.7; 1 teams, 1 slates | not enough |
| Round 3, nothing explains it | 1.32 (1.07-1.75) at 10%, 2.38 at 1%; finish -7.0; 375 teams, 16 slates | +3.4 | +2.0 (60%) | +1.4 (40%) | +6.9 | 1.58 (1.28-2.01) at 10%, 2.91 at 1%; finish -8.8; 375 teams, 16 slates | RULE for |
| Round 3, explained (tag or news) | 1.88 (1.20-2.73) at 10%, 2.43 at 1%; finish -14.4; 141 teams, 5 slates | +15.1 | +14.1 (93%) | +1.0 (7%) | +19.0 | 2.62 (1.86-3.17) at 10%, 3.72 at 1%; finish -19.7; 141 teams, 5 slates | RULE for |
| Round 4, nothing explains it | 1.57 (1.10-1.99) at 10%, 1.96 at 1%; finish -8.6; 1332 teams, 20 slates | +6.5 | +2.8 (44%) | +3.6 (56%) | +5.7 | 1.67 (1.24-2.01) at 10%, 2.10 at 1%; finish -9.5; 1332 teams, 20 slates | RULE for |
| Round 4, explained (tag or news) | 1.27 (0.00-1.86) at 10%, 0.00 at 1%; finish -5.7; 25 teams, 4 slates | +0.1 | -4.8 | +5.0 | -0.6 | 1.28 (0.00-1.91) at 10%, 0.00 at 1%; finish -5.5; 25 teams, 4 slates | not enough |
| Round 5, nothing explains it | 1.76 (1.41-2.05) at 10%, 2.83 at 1%; finish -7.8; 3266 teams, 19 slates | +6.2 | +1.7 (28%) | +4.4 (72%) | +1.6 | 1.78 (1.45-2.07) at 10%, 2.93 at 1%; finish -8.0; 3266 teams, 19 slates | RULE for |
| Round 5, explained (tag or news) | 2.24 (1.44-3.27) at 10%, 2.94 at 1%; finish -15.5; 166 teams, 5 slates | +11.5 | +10.7 (93%) | +0.8 (7%) | +9.7 | 2.15 (1.40-2.96) at 10%, 2.69 at 1%; finish -14.5; 166 teams, 5 slates | RULE for |
| Round 6, nothing explains it | 0.97 (0.80-1.15) at 10%, 1.01 at 1%; finish +1.5; 5226 teams, 20 slates | -1.7 | -4.6 (263%) | +2.8 (-163%) | -1.4 | 1.12 (0.95-1.29) at 10%, 1.21 at 1%; finish -0.6; 5226 teams, 20 slates | LEAN for |
| Round 6, explained (tag or news) | 1.83 (1.27-1.84) at 10%, 1.19 at 1%; finish -12.1; 187 teams, 3 slates | +10.2 | +2.8 (27%) | +7.4 (73%) | +6.6 | 1.74 (1.32-1.75) at 10%, 1.16 at 1%; finish -11.9; 187 teams, 3 slates | LEAN for |

### 5. The original rules (kept-*), asked 2026-11-11

Each tier's kept rule is the Tiers button's order there. A: teams holding the button's first of a decision pair (ADP within 4, same tier) and not its second; B: the reverse. Only pairs with the same flag and no tag on either, so the order is the rule's steps, not VALUE first / PRICEY last or a Questionable push (those have their own rows).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| AM T1: ADP, Boom deciding within 2 picks | 2.05 (1.42-3.00) at 10%, 2.57 at 1%; finish -8.2; 50891 teams, 16 slates | +8.5 | +7.4 (87%) | +1.1 (13%) | +8.1 | 2.04 (1.40-3.09) at 10%, 2.45 at 1%; finish -8.7; 50885 teams, 16 slates | LEAN for |
| PM T1: ETR | 1.02 (0.87-1.22) at 10%, 1.06 at 1%; finish +0.0; 114961 teams, 20 slates | +0.3 | +1.3 | -1.1 | +2.5 | 1.07 (0.89-1.32) at 10%, 1.11 at 1%; finish -1.2; 114967 teams, 20 slates | no lean |
| AM T2: ADP straight | 0.95 (0.84-1.07) at 10%, 1.01 at 1%; finish +0.5; 298679 teams, 17 slates | -0.6 | +1.1 (-191%) | -1.7 (291%) | +2.1 | 0.98 (0.87-1.10) at 10%, 1.06 at 1%; finish -0.0; 298672 teams, 17 slates | no lean |
| AM T3/T4: Proj, ADP deciding within 3 points | 0.94 (0.83-1.06) at 10%, 0.92 at 1%; finish +1.6; 190271 teams, 17 slates | -1.2 | -0.8 (71%) | -0.3 (29%) | +0.6 | 0.97 (0.87-1.09) at 10%, 0.95 at 1%; finish +0.9; 190268 teams, 17 slates | no lean |
| PM T3: ETR, ties to ADP then Boom | 0.93 (0.83-1.04) at 10%, 0.70 at 1%; finish +0.9; 186793 teams, 19 slates | -0.7 | -0.2 (25%) | -0.6 (75%) | -0.1 | 0.97 (0.85-1.09) at 10%, 0.75 at 1%; finish +0.2; 186791 teams, 19 slates | no lean |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.73 (0.59-0.94) at 10%, 0.49 at 1%; finish +1.6; 28347 teams, 20 slates | 1.97 (1.11-2.91) at 10%, 0.00 at 1%; finish -3.9; 128 teams, 18 slates |
| 1/2 | fallers vs trust | 1.36 (1.01-1.90) at 10%, 1.83 at 1%; finish -3.0; 43504 teams, 20 slates | 1.66 (1.00-2.67) at 10%, 3.26 at 1%; finish -5.7; 208 teams, 20 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.41 (0.77-2.33) at 10%, 1.46 at 1%; finish -1.0; 5142 teams, 16 slates | 2.79 (1.12-4.30) at 10%, 0.00 at 1%; finish -6.2; 56 teams, 10 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 0.87 (0.59-1.19) at 10%, 0.74 at 1%; finish +0.5; 13359 teams, 15 slates | 0.75 (0.00-1.78) at 10%, 0.00 at 1%; finish -4.7; 71 teams, 12 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.93 (0.49-1.52) at 10%, 0.57 at 1%; finish -0.2; 10875 teams, 16 slates | 1.30 (0.00-3.01) at 10%, 0.00 at 1%; finish -7.6; 47 teams, 14 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.19 (0.71-1.62) at 10%, 1.73 at 1%; finish +0.0; 10468 teams, 16 slates | 1.76 (0.74-2.82) at 10%, 3.38 at 1%; finish -7.1; 57 teams, 14 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.12 (0.29-2.46) at 10%, 1.10 at 1%; finish -0.7; 8179 teams, 15 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -2.5; 32 teams, 12 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 0.99 (0.69-1.30) at 10%, 0.87 at 1%; finish +0.6; 7300 teams, 15 slates | 1.65 (0.65-2.82) at 10%, 0.00 at 1%; finish -5.1; 47 teams, 13 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 1.34 (0.63-1.86) at 10%, 2.39 at 1%; finish -1.5; 6514 teams, 16 slates | 2.13 (0.00-3.55) at 10%, 0.00 at 1%; finish -10.0; 27 teams, 9 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.26 (0.57-2.15) at 10%, 1.11 at 1%; finish +0.3; 4430 teams, 15 slates | 3.46 (1.99-4.79) at 10%, 0.00 at 1%; finish -11.0; 33 teams, 6 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.53 (0.32-0.79) at 10%, 0.21 at 1%; finish -0.1; 4249 teams, 16 slates | 1.06 (0.00-4.40) at 10%, 0.00 at 1%; finish +7.3; 22 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.77 (0.45-1.15) at 10%, 0.41 at 1%; finish -1.7; 3333 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 1.57 (0.83-2.04) at 10%, 2.27 at 1%; finish -5.0; 1882 teams, 16 slates | 0.85 (0.00-1.97) at 10%, 0.00 at 1%; finish -2.0; 13 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.19 (0.86-1.41) at 10%, 1.02 at 1%; finish -1.4; 1717 teams, 16 slates | 1.06 (0.00-3.52) at 10%, 0.00 at 1%; finish -0.4; 14 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 0.89 (0.37-1.75) at 10%, 0.74 at 1%; finish +0.9; 1595 teams, 15 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.08 (0.37-1.97) at 10%, 1.14 at 1%; finish -4.6; 1135 teams, 16 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 0.87 (0.50-1.45) at 10%, 0.76 at 1%; finish -0.9; 1048 teams, 15 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.41 (0.26-0.59) at 10%, 0.00 at 1%; finish +2.4; 999 teams, 16 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.40 (0.23-0.58) at 10%, 0.00 at 1%; finish +8.8; 951 teams, 16 slates | none |
| 2/3 | a. reach vs trust | 1.08 (0.92-1.26) at 10%, 1.25 at 1%; finish +0.2; 24648 teams, 20 slates | 1.63 (1.06-2.16) at 10%, 1.87 at 1%; finish -7.0; 114 teams, 19 slates |
| 2/3 | fallers vs trust | 1.16 (0.98-1.38) at 10%, 1.15 at 1%; finish -3.3; 17908 teams, 20 slates | 1.83 (1.27-2.46) at 10%, 1.60 at 1%; finish -7.1; 98 teams, 18 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.61 (1.33-1.97) at 10%, 2.16 at 1%; finish -6.7; 5985 teams, 20 slates | 1.92 (1.04-2.67) at 10%, 3.75 at 1%; finish -10.8; 66 teams, 13 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.18 (0.76-1.58) at 10%, 1.15 at 1%; finish +0.5; 2988 teams, 17 slates | 0.28 (0.00-0.46) at 10%, 0.00 at 1%; finish -2.5; 33 teams, 9 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.76 (0.56-0.90) at 10%, 0.22 at 1%; finish -2.5; 3953 teams, 15 slates | 1.15 (0.00-2.06) at 10%, 0.00 at 1%; finish -11.2; 21 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 0.81 (0.36-1.33) at 10%, 0.54 at 1%; finish +10.3; 3341 teams, 15 slates | 1.26 (0.00-2.24) at 10%, 0.00 at 1%; finish +13.3; 16 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 1.27 (0.81-1.65) at 10%, 1.30 at 1%; finish -0.7; 3253 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +9.4; 13 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 1.35 (0.88-1.89) at 10%, 1.68 at 1%; finish -5.8; 3003 teams, 16 slates | 0.64 (0.00-1.84) at 10%, 0.00 at 1%; finish -2.6; 20 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.01 (0.55-1.52) at 10%, 1.47 at 1%; finish +8.9; 2577 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +17.1; 13 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 1.18 (0.79-1.52) at 10%, 1.15 at 1%; finish -6.7; 2410 teams, 16 slates | 0.72 (0.00-1.64) at 10%, 2.89 at 1%; finish -0.6; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 0.83 (0.54-1.15) at 10%, 0.62 at 1%; finish +1.1; 2303 teams, 16 slates | 0.72 (0.00-1.48) at 10%, 0.00 at 1%; finish -10.4; 8 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.62 (0.42-0.85) at 10%, 0.45 at 1%; finish -1.8; 2289 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -13.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.18 (0.61-1.92) at 10%, 1.00 at 1%; finish +3.4; 2024 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +4.4; 7 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.39 (0.88-2.02) at 10%, 1.46 at 1%; finish -7.4; 1982 teams, 16 slates | 1.75 (0.66-3.13) at 10%, 4.07 at 1%; finish -4.9; 20 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.75 (0.46-1.07) at 10%, 0.42 at 1%; finish -0.0; 1906 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +13.5; 5 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.06 (0.60-1.60) at 10%, 0.89 at 1%; finish +3.4; 1787 teams, 16 slates | 3.34 (2.13-3.81) at 10%, 0.00 at 1%; finish -15.6; 13 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 0.84 (0.43-1.34) at 10%, 0.66 at 1%; finish +7.1; 1728 teams, 15 slates | 1.06 (0.00-1.69) at 10%, 0.00 at 1%; finish +4.5; 10 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.58 (0.32-0.89) at 10%, 0.60 at 1%; finish +0.1; 1712 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.5; 11 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.83 (0.49-1.29) at 10%, 0.46 at 1%; finish -1.3; 1620 teams, 16 slates | 2.95 (0.84-6.00) at 10%, 0.00 at 1%; finish -18.5; 8 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 13 | 1.05 (0.77-1.31) at 10%, 0.88 at 1%; finish -7.1; 1567 teams, 16 slates | 1.79 (0.00-3.82) at 10%, 0.00 at 1%; finish -4.8; 12 teams, 6 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 135 | 95% | 95% | -0 |
| AM | T1-T2 | Q TRAP | 24 | 75% | 95% | -20 |
| AM | T1-T2 | VALUE | 6 | 95% | 96% | -0 |
| AM | T3-T4 | PRICEY | 117 | 92% | 95% | -3 |
| AM | T3-T4 | Q FAIR | 1 | 15% | 95% | -80 |
| AM | T3-T4 | Q TRAP | 2 | 98% | 97% | +1 |
| AM | T3-T4 | VALUE | 100 | 88% | 96% | -8 |
| AM | T5 | Q FAIR | 367 | 10% | 18% | -9 |
| AM | T5 | VALUE | 683 | 36% | 19% | +17 |
| PM | T1-T2 | PRICEY | 160 | 99% | 99% | -0 |
| PM | T1-T2 | Q TRAP | 18 | 75% | 99% | -24 |
| PM | T1-T2 | VALUE | 13 | 96% | 97% | -1 |
| PM | T3-T4 | PRICEY | 174 | 97% | 98% | -1 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 11 | 87% | 96% | -9 |
| PM | T3-T4 | VALUE | 161 | 95% | 99% | -3 |
| PM | T5 | Q FAIR | 262 | 9% | 20% | -11 |
| PM | T5 | VALUE | 613 | 61% | 24% | +38 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 117 (of all T5 breakers: VALUE 12, unflagged 127).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.15 (1.02-1.28) at 10%, 1.25 at 1%; finish -1.4; 135915 teams, 20 slates | 1.62 (1.37-1.88) at 10%, 1.52 at 1%; finish -7.4; 688 teams, 20 slates |
| Same-position teammates | 0.80 (0.71-0.93) at 10%, 0.90 at 1%; finish +4.3; 78363 teams, 20 slates | 1.43 (1.15-1.84) at 10%, 2.10 at 1%; finish -4.4; 332 teams, 20 slates |
| Same-position teammates, spread 5+ | 0.90 (0.80-1.01) at 10%, 0.84 at 1%; finish +0.9; 26727 teams, 17 slates | 1.81 (1.29-2.43) at 10%, 2.46 at 1%; finish -12.4; 147 teams, 16 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.73 | 1.70 | 1.15 | 1.26 | 0.87 | 1.00 | 1.07 | 0.02 | 0.09 | 0.00 | 2.93 |
| Field | 0.60 | 1.70 | 1.18 | 1.30 | 0.93 | 0.97 | 1.14 | 0.02 | 0.10 | 0.00 | 1.09 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.77 (0.65-0.89) at 10%, 0.81 at 1%; finish +5.5; 59290 teams, 19 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

557 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 219620 | 0.61 | 1.72 | 1.20 | 1.29 | 0.90 | 1.05 | 1.06 | 0.26 | 93% |
| Me | 1638 | 0.61 | 1.74 | 1.35 | 1.19 | 1.02 | 1.54 | 0.64 | 0.34 | 91% |
| Everyone | 358651 | 0.60 | 1.70 | 1.18 | 1.30 | 0.93 | 0.97 | 1.14 | 0.24 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.55 (0.31-0.78) at 10%, 0.37 at 1%; finish +10.4; 9151 teams, 6 slates |
| T1-T2 | AM | 0.67 (0.42-0.93) at 10%, 0.47 at 1%; finish +6.2; 5098 teams, 6 slates |
| T1-T2 | PM | 0.41 (0.11-0.65) at 10%, 0.23 at 1%; finish +15.7; 4053 teams, 3 slates |
| T3-T5 | both | 0.90 (0.78-1.05) at 10%, 1.05 at 1%; finish +1.8; 20920 teams, 14 slates |
| T3-T5 | AM | 0.86 (0.72-1.01) at 10%, 0.99 at 1%; finish +2.8; 10762 teams, 12 slates |
| T3-T5 | PM | 0.95 (0.75-1.18) at 10%, 1.12 at 1%; finish +0.7; 10158 teams, 10 slates |
| not credited | both | 0.78 (0.63-0.92) at 10%, 0.82 at 1%; finish +6.3; 23531 teams, 19 slates |
| not credited | AM | 0.80 (0.66-0.99) at 10%, 0.77 at 1%; finish +5.3; 12439 teams, 16 slates |
| not credited | PM | 0.75 (0.57-0.93) at 10%, 0.88 at 1%; finish +7.3; 11092 teams, 19 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 16 show a lean or rule and 10 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | RULE for | RULE for | 1.14 (1.05-1.23) | keep: points and money agree |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | RULE for | 1.23 (1.13-1.34) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | LEAN for (deciles: RULE for) | LEAN for | 1.16 (1.06-1.27) | watch: money leans for |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 1.05 (0.76-1.31) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 1.05 (0.85-1.28) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | no lean | 1.11 (0.82-1.43) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 0.98 (0.84-1.15) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | no lean | 1.01 (0.86-1.18) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | no lean | no lean | 0.90 (0.77-1.06) | not enough on either side yet |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 0.98 (0.85-1.14) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 1.02 (0.86-1.23) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | RULE for | LEAN for | 1.36 (1.09-1.76) | watch: money leans for |
| pm-t5-beneficiary | adopted | LEAN (listed) | no lean | no lean | 1.06 (0.84-1.32) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | RULE for | RULE for | 1.24 (1.14-1.35) | keep: the leverage pays (money RULE) |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.50 (1.24-1.87) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | LEAN for | no lean | 1.20 (0.93-1.57) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.89 (0.76-1.10) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | RULE against | RULE against | 0.73 (0.63-0.84) | rethink: money RULE against it |
| one-tier-cap | adopted | LEAN (both windows) | no lean | no lean | 0.89 (0.71-1.09) | keep on points; money not settled |
| pm-middle-takes | candidate | LEAN (single window) | no lean | no lean | 1.04 (0.88-1.23) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | no lean | no lean | 0.99 (0.85-1.17) | keep on points; money not settled |
| am-t5-other-reads | candidate | LEAN against (single window) | LEAN for | LEAN for | 1.24 (1.04-1.52) | watch: money leans for the leverage, not yet its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

Verdicts that change on ten price groups: pricey-flags (LEAN for on five, RULE for on ten).

