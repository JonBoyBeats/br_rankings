# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-10. Slates 2026-10-20 to 2026-11-09: 20 nights, 55 contests, 317512 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

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

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 8 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_mon_main, nba_mon_main, nba_sat_main, nba_sun_main, nba_thu_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 290006 of 317512 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

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
| 2026-11-04 | Hump Day Hoops | 6 | PM | 1 | 210.4 | 218.5 | 5.0, 9.2, 28.7, 34.8, 34.9, 16.8 (swap) |
| 2026-11-07 | Saturday Slam | 6 | PM | 2 | 221.3 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 15.8 (swap) |
| 2026-11-09 | Monday Night Hoops | 6 | PM | 4 | 220.9 | 247.4 | 3.4, 11.7, 14.6, 20.1, 29.0, 31.3 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.2 | 7 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.8 | 7 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.3 | 9 |
| Contest (its mean against its night's) | The Layup Line | -0.5 | 10 |
| Contest (its mean against its night's) | flagships | +0.0 | 18 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +4.6 | 44 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +5.8 | 57958 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.0 | 57990 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.5 | 58009 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -1.9 | 57584 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -4.4 | 58465 |
| Swap on the team (inside contest) | no | +1.0 | 234702 |
| Swap on the team (inside contest) | yes | -4.3 | 55304 |
| Window (inside contest) | AM | -0.6 | 88093 |
| Window (inside contest) | PM | +0.3 | 201373 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fast Break Friday | 6 | 3 | 290 | 0.69 | 1.72 | 1.62 | 1.55 | 38.6 | 1.56 (77) | 1.64 (213) | $1450 | $1467 | +1% |
| Hump Day Hoops | 6 | 3 | 250 | 1.20 | 1.20 | 1.36 | 1.14 | 51.5 | 1.80 (100) | 1.07 (150) | $1250 | $757 | -39% |
| Monday Night Hoops | 6 | 3 | 250 | 0.00 | 0.96 | 1.00 | 1.12 | 46.6 | 1.02 (59) | 0.99 (191) | $1250 | $760 | -39% |
| Tuesday Tip-Off | 6 | 1 | 150 | 0.67 | 1.07 | 1.13 | 1.27 | 46.7 | 1.17 (60) | 1.11 (90) | $750 | $840 | +12% |
| Saturday Slam | 6 | 3 | 120 | 4.17 | 2.33 | 1.58 | 1.25 | 47.0 | 1.43 (28) | 1.63 (92) | $600 | $6569 | +995% |
| Sunday Shootaround | 6 | 2 | 120 | 0.83 | 1.33 | 1.33 | 1.38 | 41.3 | 3.00 (30) | 0.78 (90) | $600 | $480 | -20% |
| Buzzer Beater | 6 | 4 | 50 | 2.00 | 1.60 | 1.60 | 1.30 | 44.7 | 5.00 (4) | 1.30 (46) | $150 | $171 | +14% |
| The Layup Line | 6 | 4 | 24 | 0.00 | 1.67 | 1.25 | 1.25 | 49.8 | 2.00 (5) | 1.05 (19) | $120 | $50 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 1.03 (39) | 1.77 (141) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 15 | 1254 | 1.04 | 1.40 | 1.35 (1.16-1.55) | 1.29 | 45.2 | 1.63 (363) | 1.23 (891) | $6170 | $11094 | +80% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.82 (49) | 1.71 (175) | $1120 | $847 | -24% |
| **all** | - | 20 | 1478 | 1.01 | 1.41 | 1.37 (1.21-1.58) | 1.31 | 44.8 | 1.53 (412) | 1.31 (1066) | $7290 | $11941 | +64% |

Dollars: $7290 in fees, $11941 won, +64% ROI over 20 nights (80% range -29% to +190%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -21%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

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
| 2026-11-09 | 95 | Paul Reed 47% | Paul Reed + Kevin Durant 18% | 4 (Alperen Sengun + Cade Cunningham + Kevin Durant) | 0.5% | 4 of 80 |

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.38 (1.22-1.56) at 10%, 0.96 at 1%; finish -5.9; 1424 teams, 18 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.25 (1.14-1.37) at 10%, 1.49 at 1%; finish -2.7; 312973 teams, 17 slates | 1.15 (1.05-1.26) at 10%, 1.25 at 1%; finish -1.6; 239691 teams, 13 slates | 1.67 (1.48-1.81) at 10%, 2.88 at 1%; finish -6.3; 73282 teams, 4 slates | 1.83 (1.38-2.45) at 10%, 1.39 at 1%; finish -8.0; 1957 teams, 17 slates | RULE for | RULE for |
|   AM only | 1.21 (1.10-1.33) at 10%, 1.38 at 1%; finish -1.4; 84064 teams, 14 slates | 1.13 (1.02-1.23) at 10%, 1.13 at 1%; finish -0.6; 67259 teams, 10 slates | 1.54 (1.25-1.94) at 10%, 2.75 at 1%; finish -4.4; 16805 teams, 4 slates | 1.51 (1.19-1.87) at 10%, 0.61 at 1%; finish -5.4; 456 teams, 10 slates | RULE for | RULE for |
|   PM only | 1.27 (1.12-1.42) at 10%, 1.52 at 1%; finish -3.2; 228901 teams, 17 slates | 1.16 (1.03-1.29) at 10%, 1.28 at 1%; finish -1.9; 172429 teams, 13 slates | 1.78 (1.36-1.97) at 10%, 3.01 at 1%; finish -7.2; 56472 teams, 4 slates | 1.99 (1.34-2.76) at 10%, 1.75 at 1%; finish -9.1; 1501 teams, 17 slates | RULE for | RULE for |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.42 (1.23-1.62) at 10%, 2.36 at 1%; finish -6.1; 21384 teams, 6 slates | 1.28 (1.18-1.39) at 10%, 2.11 at 1%; finish -4.9; 15777 teams, 5 slates | 1.92 at 10%, 3.73 at 1%; finish -9.6; 5607 teams, 1 slates | 2.01 (0.65-3.14) at 10%, 1.73 at 1%; finish -12.4; 71 teams, 6 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.22 (1.10-1.34) at 10%, 1.33 at 1%; finish -2.1; 1268141 teams, 17 slates | 1.19 (1.04-1.32) at 10%, 1.29 at 1%; finish -1.8; 1005340 teams, 13 slates | 1.33 (1.07-1.53) at 10%, 1.50 at 1%; finish -3.5; 262801 teams, 4 slates | 1.47 (1.16-1.81) at 10%, 0.67 at 1%; finish -6.1; 9487 teams, 17 slates | RULE for | RULE for |
|   T3 | 1.24 (0.81-1.78) at 10%, 1.44 at 1%; finish -2.5; 116776 teams, 13 slates | 1.37 (0.80-2.13) at 10%, 1.60 at 1%; finish -4.8; 92643 teams, 11 slates | 0.83 at 10%, 0.91 at 1%; finish +6.5; 24133 teams, 2 slates | 1.33 (0.88-1.96) at 10%, 0.00 at 1%; finish -8.1; 1013 teams, 13 slates | no lean | no lean |
|   T4 | 1.24 (1.08-1.38) at 10%, 1.39 at 1%; finish -2.3; 167951 teams, 15 slates | 1.21 (1.01-1.42) at 10%, 1.36 at 1%; finish -2.5; 113790 teams, 11 slates | 1.31 (1.14-1.47) at 10%, 1.46 at 1%; finish -2.0; 54161 teams, 4 slates | 1.82 (1.36-2.42) at 10%, 1.75 at 1%; finish -7.9; 1225 teams, 14 slates | RULE for | RULE for |
|   T5 | 1.23 (1.05-1.41) at 10%, 1.36 at 1%; finish -2.2; 983286 teams, 17 slates | 1.18 (0.97-1.38) at 10%, 1.28 at 1%; finish -1.5; 798819 teams, 13 slates | 1.48 (1.22-1.64) at 10%, 1.74 at 1%; finish -5.6; 184467 teams, 4 slates | 1.45 (1.09-1.83) at 10%, 0.57 at 1%; finish -5.8; 7249 teams, 16 slates | RULE for | RULE for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.21 (1.11-1.31) at 10%, 1.32 at 1%; finish -2.0; 724345 teams, 17 slates | 1.22 (1.10-1.36) at 10%, 1.28 at 1%; finish -2.8; 545036 teams, 13 slates | 1.17 (1.03-1.34) at 10%, 1.47 at 1%; finish +0.5; 179309 teams, 4 slates | 1.75 (1.49-2.02) at 10%, 1.86 at 1%; finish -7.3; 4263 teams, 17 slates | RULE for | RULE for |
|   T1 | 2.04 (1.59-2.59) at 10%, 3.53 at 1%; finish -8.1; 94533 teams, 11 slates | 1.89 (1.34-2.93) at 10%, 2.35 at 1%; finish -9.5; 48814 teams, 7 slates | 2.26 (2.01-2.45) at 10%, 7.65 at 1%; finish -6.7; 45719 teams, 4 slates | 2.68 (1.52-4.08) at 10%, 4.39 at 1%; finish -13.0; 466 teams, 10 slates | RULE for | RULE for |
|   T2 | 1.14 (0.96-1.35) at 10%, 1.11 at 1%; finish -1.4; 258017 teams, 15 slates | 1.23 (1.02-1.46) at 10%, 1.17 at 1%; finish -3.7; 192670 teams, 11 slates | 0.86 (0.64-1.15) at 10%, 0.87 at 1%; finish +5.3; 65347 teams, 4 slates | 1.64 (1.35-2.00) at 10%, 1.71 at 1%; finish -7.0; 1629 teams, 15 slates | LEAN for | LEAN for |
|   T3 | 1.41 (1.10-1.78) at 10%, 1.63 at 1%; finish -5.3; 179389 teams, 15 slates | 1.43 (1.08-1.88) at 10%, 1.79 at 1%; finish -5.0; 153873 teams, 12 slates | 1.32 (0.94-2.19) at 10%, 1.10 at 1%; finish -7.1; 25516 teams, 3 slates | 2.35 (1.90-2.80) at 10%, 2.41 at 1%; finish -12.1; 1136 teams, 15 slates | RULE for | RULE for |
|   T4 | 0.93 (0.80-1.14) at 10%, 0.90 at 1%; finish +2.1; 192308 teams, 17 slates | 0.92 (0.77-1.18) at 10%, 0.85 at 1%; finish +2.1; 149645 teams, 13 slates | 0.99 (0.72-1.38) at 10%, 1.26 at 1%; finish +2.2; 42663 teams, 4 slates | 1.18 (0.99-1.43) at 10%, 0.82 at 1%; finish -1.5; 1032 teams, 16 slates | no lean | no lean |
|   T5 | none | none | none | none | not enough | not enough |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.11 (0.78-1.41) at 10%, 1.18 at 1%; finish -2.5; 48789 teams, 9 slates | 1.19 (0.84-1.52) at 10%, 1.29 at 1%; finish -3.9; 40448 teams, 8 slates | 0.47 at 10%, 0.33 at 1%; finish +3.8; 8341 teams, 1 slates | 1.29 (1.11-1.59) at 10%, 0.74 at 1%; finish -3.6; 233 teams, 6 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.13 (1.01-1.26) at 10%, 1.20 at 1%; finish -2.1; 1157677 teams, 14 slates | 1.03 (0.95-1.12) at 10%, 1.04 at 1%; finish -1.3; 829157 teams, 10 slates | 1.39 (1.03-1.74) at 10%, 1.67 at 1%; finish -4.2; 328520 teams, 4 slates | 1.62 (1.45-1.83) at 10%, 0.79 at 1%; finish -3.7; 5033 teams, 11 slates | LEAN for | LEAN for |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 1.22 (0.88-1.66) at 10%, 1.50 at 1%; finish -3.4; 85103 teams, 13 slates | 1.29 (0.88-1.90) at 10%, 1.62 at 1%; finish -3.6; 66876 teams, 11 slates | 0.96 at 10%, 1.11 at 1%; finish -2.4; 18227 teams, 2 slates | 1.69 (1.07-2.33) at 10%, 2.89 at 1%; finish -10.9; 593 teams, 13 slates | no lean | no lean |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.89 (0.74-1.14) at 10%, 0.79 at 1%; finish +2.4; 52105 teams, 13 slates | 0.97 (0.82-1.27) at 10%, 1.00 at 1%; finish +1.9; 41264 teams, 9 slates | 0.64 (0.38-1.33) at 10%, 0.28 at 1%; finish +4.1; 10841 teams, 4 slates | 0.76 (0.54-1.05) at 10%, 0.00 at 1%; finish -3.9; 241 teams, 12 slates | no lean | no lean |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 0.78 (0.66-0.93) at 10%, 0.63 at 1%; finish +2.7; 589630 teams, 16 slates | 0.90 (0.77-1.07) at 10%, 0.80 at 1%; finish +0.4; 433324 teams, 12 slates | 0.52 (0.41-0.77) at 10%, 0.30 at 1%; finish +9.0; 156306 teams, 4 slates | 1.48 (1.13-1.88) at 10%, 0.66 at 1%; finish -7.8; 1768 teams, 16 slates | RULE against | RULE against |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.83 (0.66-1.05) at 10%, 0.78 at 1%; finish +2.9; 92026 teams, 14 slates | 0.80 (0.61-1.07) at 10%, 0.73 at 1%; finish +2.9; 72651 teams, 11 slates | 0.97 (0.42-1.25) at 10%, 1.01 at 1%; finish +3.3; 19375 teams, 3 slates | 0.96 (0.73-1.30) at 10%, 0.53 at 1%; finish -4.9; 237 teams, 11 slates | LEAN against | LEAN against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 0.95 (0.79-1.12) at 10%, 0.94 at 1%; finish +0.1; 12173 teams, 11 slates | 0.82 (0.73-0.94) at 10%, 0.70 at 1%; finish +2.2; 8481 teams, 8 slates | 1.27 (0.83-1.56) at 10%, 1.70 at 1%; finish -4.5; 3692 teams, 3 slates | 0.92 (0.65-1.22) at 10%, 1.71 at 1%; finish +3.4; 105 teams, 8 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.07 (0.84-1.30) at 10%, 1.07 at 1%; finish -1.0; 22074 teams, 14 slates | 1.04 (0.78-1.32) at 10%, 1.08 at 1%; finish -1.3; 17022 teams, 11 slates | 1.17 (0.67-1.88) at 10%, 1.03 at 1%; finish -0.2; 5052 teams, 3 slates | 1.33 (0.73-2.19) at 10%, 0.00 at 1%; finish -6.4; 117 teams, 11 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 1.08 (0.90-1.27) at 10%, 1.19 at 1%; finish +0.1; 153630 teams, 11 slates | 1.15 (0.96-1.34) at 10%, 1.51 at 1%; finish -0.4; 120030 teams, 8 slates | 0.91 (0.61-1.52) at 10%, 0.71 at 1%; finish +2.0; 33600 teams, 3 slates | 1.59 (1.08-2.20) at 10%, 1.24 at 1%; finish -2.5; 622 teams, 10 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 0.99 (0.83-1.20) at 10%, 0.89 at 1%; finish -0.8; 192038 teams, 12 slates | 1.02 (0.83-1.29) at 10%, 0.96 at 1%; finish -1.3; 149976 teams, 9 slates | 0.92 (0.64-1.14) at 10%, 0.70 at 1%; finish +1.3; 42062 teams, 3 slates | 1.03 (0.60-1.76) at 10%, 0.18 at 1%; finish -2.4; 1046 teams, 11 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | none | none | none | none | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 0.82 (0.64-1.03) at 10%, 0.63 at 1%; finish +1.3; 5661 teams, 13 slates | 0.82 (0.68-1.03) at 10%, 0.62 at 1%; finish +1.2; 5639 teams, 10 slates | 1.29 (0.00-1.40) at 10%, 3.68 at 1%; finish +8.1; 22 teams, 3 slates | 1.46 (1.18-1.79) at 10%, 0.00 at 1%; finish -8.5; 40 teams, 3 slates | LEAN against | LEAN against |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 0.95 (0.84-1.09) at 10%, 0.92 at 1%; finish +1.1; 25908 teams, 9 slates | 0.85 (0.75-0.95) at 10%, 0.81 at 1%; finish +2.5; 17181 teams, 6 slates | 1.14 (0.90-1.48) at 10%, 1.12 at 1%; finish -1.4; 8727 teams, 3 slates | 0.99 (0.51-1.61) at 10%, 0.60 at 1%; finish +0.5; 153 teams, 9 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 0.99 (0.80-1.31) at 10%, 0.90 at 1%; finish -0.7; 10645 teams, 12 slates | 1.06 (0.80-1.60) at 10%, 1.09 at 1%; finish -1.2; 6410 teams, 8 slates | 0.86 (0.66-1.26) at 10%, 0.63 at 1%; finish +0.1; 4235 teams, 4 slates | 2.53 (1.27-4.39) at 10%, 5.76 at 1%; finish -4.9; 34 teams, 7 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.49 (1.19-2.10) at 10%, 1.84 at 1%; finish -4.6; 6633 teams, 9 slates | 1.51 (1.18-2.40) at 10%, 1.94 at 1%; finish -4.7; 5708 teams, 7 slates | 1.36 at 10%, 1.19 at 1%; finish -4.2; 925 teams, 2 slates | 2.10 (0.77-5.00) at 10%, 0.00 at 1%; finish -5.5; 16 teams, 5 slates | RULE for | RULE for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.20 (0.95-1.52) at 10%, 1.69 at 1%; finish -1.1; 44845 teams, 15 slates | 1.13 (0.90-1.43) at 10%, 1.80 at 1%; finish +1.3; 30257 teams, 11 slates | 1.36 (0.70-2.20) at 10%, 1.49 at 1%; finish -6.0; 14588 teams, 4 slates | 2.27 (1.40-3.05) at 10%, 1.23 at 1%; finish -12.0; 279 teams, 14 slates | LEAN for | LEAN for |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 1.03 (0.83-1.24) at 10%, 1.06 at 1%; finish -0.9; 193908 teams, 16 slates | 0.98 (0.79-1.22) at 10%, 1.01 at 1%; finish +0.2; 139240 teams, 12 slates | 1.16 (0.70-1.61) at 10%, 1.22 at 1%; finish -3.7; 54668 teams, 4 slates | 1.18 (0.91-1.68) at 10%, 0.34 at 1%; finish -6.6; 1325 teams, 15 slates | no lean | no lean |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 0.94 (0.79-1.10) at 10%, 0.85 at 1%; finish +0.3; 110816 teams, 16 slates | 0.98 (0.81-1.23) at 10%, 0.94 at 1%; finish -0.8; 88075 teams, 12 slates | 0.76 (0.62-0.98) at 10%, 0.56 at 1%; finish +4.7; 22741 teams, 4 slates | 1.17 (0.92-1.42) at 10%, 0.52 at 1%; finish -5.8; 654 teams, 16 slates | no lean | no lean |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.24 (1.01-1.54) at 10%, 1.53 at 1%; finish -2.4; 113049 teams, 14 slates | 1.32 (1.01-1.77) at 10%, 1.65 at 1%; finish -3.0; 91599 teams, 10 slates | 0.94 (0.77-1.20) at 10%, 1.14 at 1%; finish +0.2; 21450 teams, 4 slates | 1.00 (0.65-1.40) at 10%, 0.00 at 1%; finish +1.4; 654 teams, 11 slates | LEAN for | LEAN for |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 | RULE for | +2.7 | +2.5 (93%) | +0.2 (7%) | -0.5 | 1.19 (1.06-1.32) at 10%, 1.38 at 1%; finish -2.0; 312973 teams, 17 slates | RULE for |
| ownership-tiebreak-t5 AM only | RULE for | +1.4 | +1.2 (90%) | +0.1 (10%) | -2.4 | 1.12 (0.99-1.27) at 10%, 1.21 at 1%; finish -0.3; 84067 teams, 14 slates | LEAN for |
| ownership-tiebreak-t5 PM only | RULE for | +3.2 | +3.0 (92%) | +0.2 (8%) | +0.2 | 1.23 (1.07-1.40) at 10%, 1.45 at 1%; finish -2.8; 228901 teams, 17 slates | RULE for |
| leverage-t2-t4 | RULE for | +5.7 | +6.6 (116%) | -0.9 (-16%) | -0.5 | 1.59 (1.32-2.13) at 10%, 2.49 at 1%; finish -7.5; 21382 teams, 6 slates | RULE for |
| value-up-middle-t5 | RULE for | +2.0 | +1.6 (79%) | +0.4 (21%) | -0.9 | 1.18 (1.05-1.31) at 10%, 1.28 at 1%; finish -1.5; 1268141 teams, 17 slates | RULE for |
| value-up-middle-t5 T4 | RULE for | +2.6 | +2.3 (89%) | +0.3 (11%) | +2.5 | 1.17 (1.00-1.34) at 10%, 1.29 at 1%; finish -1.6; 167947 teams, 15 slates | LEAN for |
| value-up-middle-t5 T5 | RULE for | +1.9 | +0.6 (31%) | +1.3 (69%) | -0.2 | 1.23 (1.03-1.42) at 10%, 1.31 at 1%; finish -2.4; 983242 teams, 17 slates | LEAN for |
| pricey-flags | RULE for | +2.1 | +2.9 (135%) | -0.7 (-35%) | +3.4 | 1.24 (1.12-1.36) at 10%, 1.36 at 1%; finish -2.4; 724363 teams, 17 slates | RULE for |
| pricey-flags T1 | RULE for | +6.4 | +7.1 (112%) | -0.7 (-12%) | +10.0 | 2.12 (1.75-2.68) at 10%, 3.82 at 1%; finish -8.6; 94534 teams, 11 slates | RULE for |
| pricey-flags T2 | LEAN for | +1.8 | +2.6 (147%) | -0.8 (-47%) | +3.2 | 1.17 (0.98-1.38) at 10%, 1.15 at 1%; finish -1.8; 258013 teams, 15 slates | LEAN for |
| pricey-flags T3 | RULE for | +5.5 | +6.9 (127%) | -1.5 (-27%) | +6.1 | 1.41 (1.11-1.79) at 10%, 1.67 at 1%; finish -5.3; 179391 teams, 15 slates | RULE for |
| am-t5-button-order | LEAN for | +1.8 | +0.9 (51%) | +0.9 (49%) | +0.7 | 1.14 (1.03-1.28) at 10%, 1.21 at 1%; finish -2.3; 1157705 teams, 14 slates | LEAN for |
| pm-t5-adp-value | RULE against | -2.7 | -2.6 (95%) | -0.1 (5%) | -0.1 | 0.81 (0.68-0.97) at 10%, 0.66 at 1%; finish +2.4; 589630 teams, 16 slates | LEAN against |
| one-tier-cap | LEAN against | -3.1 | -2.3 (73%) | -0.8 (27%) | -0.1 | 0.80 (0.63-1.03) at 10%, 0.76 at 1%; finish +3.7; 92040 teams, 14 slates | LEAN against |
| q-class-x:FAIR | LEAN against | -1.3 | +2.8 (-212%) | -4.1 (312%) | - (holding) | 0.79 (0.63-0.97) at 10%, 0.61 at 1%; finish +2.1; 5661 teams, 13 slates | LEAN against |
| beneficiary-round6:played | RULE for | +4.4 | +4.2 (95%) | +0.2 (5%) | - (holding) | 1.44 (1.14-2.11) at 10%, 1.75 at 1%; finish -4.0; 6633 teams, 9 slates | RULE for |
| pm-t5-beneficiary | LEAN for | +0.8 | +2.7 (321%) | -1.9 (-221%) | - (holding) | 1.12 (0.91-1.39) at 10%, 1.55 at 1%; finish +0.1; 44839 teams, 15 slates | no lean |
| am-t5-other-reads | LEAN for | +2.4 | -0.1 (-5%) | +2.6 (105%) | +0.9 | 1.24 (1.00-1.54) at 10%, 1.49 at 1%; finish -2.3; 113082 teams, 14 slates | LEAN for |
| turn 1/2: a. reach vs trust | LEAN against | -0.5 | +0.9 | -1.4 | -0.2 | 0.74 (0.56-1.01) at 10%, 0.56 at 1%; finish +1.7; 24334 teams, 18 slates | LEAN against |
| turn 1/2: fallers vs trust | LEAN for | +4.3 | +2.2 (52%) | +2.1 (48%) | +4.8 | 1.59 (1.12-2.38) at 10%, 1.96 at 1%; finish -5.4; 38105 teams, 18 slates | LEAN for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +1.2 | +1.3 (109%) | -0.1 (-9%) | +0.5 | 1.47 (0.45-3.15) at 10%, 1.76 at 1%; finish +0.6; 3933 teams, 13 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | -0.0 | +3.5 | -3.5 | +0.8 | 1.08 (0.93-1.23) at 10%, 1.45 at 1%; finish +1.3; 21934 teams, 18 slates | no lean |
| turn 2/3: fallers vs trust | LEAN for | +1.3 | -0.3 (-24%) | +1.7 (124%) | +0.8 | 1.13 (0.98-1.32) at 10%, 1.17 at 1%; finish -2.2; 15543 teams, 18 slates | LEAN for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +8.0 | +9.4 (118%) | -1.4 (-18%) | +6.7 | 1.70 (1.36-2.00) at 10%, 3.04 at 1%; finish -6.6; 5034 teams, 17 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | LEAN for | +0.6 | +1.0 (161%) | -0.4 (-61%) | - (holding) | 1.05 (0.91-1.21) at 10%, 1.28 at 1%; finish +1.0; 107676 teams, 17 slates | no lean |
| stack: Same-position teammates | RULE against | -3.8 | -7.9 (205%) | +4.0 (-105%) | - (holding) | 0.74 (0.63-0.85) at 10%, 0.90 at 1%; finish +4.4; 68416 teams, 18 slates | RULE against |
| stack: Same-position teammates, spread 5+ | RULE against | -1.6 | -3.5 (220%) | +1.9 (-120%) | - (holding) | 0.80 (0.70-0.89) at 10%, 0.70 at 1%; finish +2.6; 24788 teams, 15 slates | RULE against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 11 | 174 | +0.3 | +0 | +0 |
| the swap board, near-ties least drafted first (leverage) | 11 | 174 | +0.6 | +1 | -220 |
| the swap board, near-ties most drafted first (spread) | 11 | 174 | -0.2 | +1 | -33 |

Leverage against spread: the leverage board's swaps would have made +0 top-10% finishes and $+187 against the spread board's (real minus each, differenced). Leverage put 65% of a night's replayed swaps on one player, spread 56%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.13 (0.95-1.38) at 10%, 1.16 at 1%; finish -1.6; 17249 teams, 13 slates | +1.9 | +2.8 (153%) | -1.0 (-53%) | 1.11 (0.94-1.37) at 10%, 1.13 at 1%; finish -1.2; 17248 teams, 13 slates | no lean |
| rounds 1-2 | 3.66 at 10%, 12.43 at 1%; finish -16.3; 708 teams, 2 slates | +15.9 | +13.9 (88%) | +2.0 (12%) | 3.41 at 10%, 10.57 at 1%; finish -15.7; 708 teams, 2 slates | not enough |
| rounds 3-4 | 1.14 (0.89-1.52) at 10%, 0.97 at 1%; finish -1.4; 5228 teams, 7 slates | +1.7 | +7.1 (413%) | -5.4 (-313%) | 1.14 (0.91-1.50) at 10%, 0.99 at 1%; finish -1.5; 5226 teams, 7 slates | no lean |
| rounds 5-6 or undrafted | 1.04 (0.85-1.35) at 10%, 1.07 at 1%; finish -0.7; 11356 teams, 11 slates | +1.0 | +0.2 (19%) | +0.8 (81%) | 1.03 (0.85-1.32) at 10%, 1.03 at 1%; finish -0.2; 11357 teams, 11 slates | no lean |

## 3c. Splits for Monday: teammates and takes by source

Each with the price-split check (section 3b). Lift: top-10% against same-contest, same-price teams.

### Teammates, by the rounds paid for them

A: teams with that teammate pair; B: teams with no two teammates at all (so same- and different-position pairs face the same comparison).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pair | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| Same position, both rounds 1-3 | 1.11 (0.62-1.61) at 10%, 1.10 at 1%; finish -3.6; 7978 teams, 11 slates | +2.2 | -1.7 (-75%) | +3.9 (175%) | 1.08 (0.61-1.58) at 10%, 1.13 at 1%; finish -3.1; 7978 teams, 11 slates | no lean |
| Same position, one in rounds 1-3 and one in 4-6 | 0.87 (0.77-0.97) at 10%, 0.82 at 1%; finish +1.9; 29713 teams, 16 slates | -1.7 | -4.3 (249%) | +2.6 (-149%) | 0.76 (0.68-0.84) at 10%, 0.66 at 1%; finish +3.6; 29655 teams, 16 slates | RULE against |
| Same position, both rounds 4-6 | 1.10 (0.96-1.24) at 10%, 1.29 at 1%; finish -2.6; 13167 teams, 16 slates | +1.9 | -1.1 (-55%) | +3.0 (155%) | 1.06 (0.93-1.20) at 10%, 1.26 at 1%; finish -2.1; 13166 teams, 16 slates | no lean |
| Different-position teammates (any rounds) | 1.10 (1.03-1.18) at 10%, 1.24 at 1%; finish -0.9; 115976 teams, 16 slates | +0.8 | -0.8 (-98%) | +1.6 (198%) | 0.97 (0.85-1.11) at 10%, 1.05 at 1%; finish +1.5; 98210 teams, 16 slates | no lean |

### Your takes by source (takes_history.csv)

A: teams holding the player you put first; B: the button's first, in the take's window (field and mine). Field drafted%: the share of that window's pods that took each. Points: the takes file's average gain per take (yours).

| Source | Window | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pick | From the other picks | Lift matched on the other picks' price | Verdict that survives | Takes, points per take | Field drafted%: yours / the button's | Yours the more drafted |
|---|---|---|---|---|---|---|---|---|---|---|
| ETR | PM | 1.08 (0.73-1.52) at 10%, 1.08 at 1%; finish -0.1; 53437 teams, 7 slates | +0.0 | +0.1 | -0.1 | 1.11 (0.75-1.56) at 10%, 1.11 at 1%; finish -0.7; 53437 teams, 7 slates | no lean | 109, -0.7 | 23% / 36% | 22% |
| ETR | both | 1.08 (0.73-1.52) at 10%, 1.08 at 1%; finish -0.1; 53437 teams, 7 slates | +0.0 | +0.1 | -0.1 | 1.11 (0.75-1.56) at 10%, 1.11 at 1%; finish -0.7; 53437 teams, 7 slates | no lean | 109, -0.7 | 23% / 36% | 22% |
| Bagel | PM | 0.97 (0.77-1.28) at 10%, 0.95 at 1%; finish -0.3; 76065 teams, 8 slates | -0.1 | -0.2 | +0.1 | 0.96 (0.76-1.28) at 10%, 0.93 at 1%; finish -0.1; 76061 teams, 8 slates | no lean | 94, -3.5 | 40% / 42% | 45% |
| Bagel | both | 0.97 (0.77-1.28) at 10%, 0.95 at 1%; finish -0.3; 76065 teams, 8 slates | -0.1 | -0.2 | +0.1 | 0.96 (0.76-1.28) at 10%, 0.93 at 1%; finish -0.1; 76061 teams, 8 slates | no lean | 94, -3.5 | 40% / 42% | 45% |
| Bagel+ETR | PM | 0.86 (0.74-1.03) at 10%, 0.81 at 1%; finish +2.4; 157695 teams, 8 slates | -1.8 | -1.7 (92%) | -0.1 (8%) | 0.89 (0.77-1.06) at 10%, 0.85 at 1%; finish +1.9; 157690 teams, 8 slates | LEAN against | 162, -2.0 | 47% / 54% | 35% |
| Bagel+ETR | both | 0.86 (0.74-1.03) at 10%, 0.81 at 1%; finish +2.4; 157695 teams, 8 slates | -1.8 | -1.7 (92%) | -0.1 (8%) | 0.89 (0.77-1.06) at 10%, 0.85 at 1%; finish +1.9; 157690 teams, 8 slates | LEAN against | 162, -2.0 | 47% / 54% | 35% |
| NEWS | AM | 1.03 (0.91-1.18) at 10%, 1.08 at 1%; finish -0.3; 271810 teams, 14 slates | +0.4 | -1.8 | +2.1 | 1.06 (0.92-1.21) at 10%, 1.11 at 1%; finish -0.7; 271813 teams, 14 slates | no lean | 629, -1.5 | 39% / 49% | 34% |
| NEWS | PM | 0.95 (0.84-1.05) at 10%, 0.90 at 1%; finish -0.6; 199150 teams, 16 slates | +0.4 | +0.1 | +0.3 | 0.98 (0.85-1.09) at 10%, 0.91 at 1%; finish -1.0; 199161 teams, 16 slates | no lean | 336, -1.7 | 31% / 45% | 23% |
| NEWS | both | 1.00 (0.92-1.07) at 10%, 1.00 at 1%; finish -0.5; 470963 teams, 17 slates | +0.4 | -1.0 | +1.4 | 1.03 (0.94-1.10) at 10%, 1.03 at 1%; finish -0.8; 470979 teams, 17 slates | no lean | 965, -1.6 | 36% / 48% | 30% |
| OTHER | AM | 1.23 (0.66-1.90) at 10%, 1.11 at 1%; finish -3.3; 39166 teams, 3 slates | +4.3 | +1.1 (25%) | +3.2 (75%) | 1.25 (0.72-1.83) at 10%, 1.15 at 1%; finish -3.3; 39166 teams, 3 slates | no lean | 113, +2.3 | 36% / 50% | 38% |
| OTHER | PM | 0.98 (0.79-1.21) at 10%, 1.03 at 1%; finish +1.3; 71880 teams, 12 slates | -0.9 | +0.0 (-2%) | -0.9 (102%) | 0.92 (0.73-1.13) at 10%, 0.95 at 1%; finish +2.1; 71880 teams, 12 slates | no lean | 223, -0.6 | 34% / 46% | 32% |
| OTHER | both | 1.10 (0.83-1.34) at 10%, 1.13 at 1%; finish -0.5; 111046 teams, 12 slates | +1.1 | +0.5 (45%) | +0.6 (55%) | 1.06 (0.81-1.30) at 10%, 1.10 at 1%; finish -0.1; 111046 teams, 12 slates | no lean | 336, +0.4 | 35% / 48% | 34% |
| all | AM | 1.06 (0.93-1.21) at 10%, 1.10 at 1%; finish -0.8; 310976 teams, 14 slates | +0.9 | -1.3 (-147%) | +2.3 (247%) | 1.09 (0.95-1.23) at 10%, 1.13 at 1%; finish -1.1; 310979 teams, 14 slates | no lean | 742, -0.9 | 38% / 49% | 35% |
| all | PM | 0.96 (0.89-1.05) at 10%, 0.94 at 1%; finish +0.3; 558249 teams, 17 slates | -0.3 | -0.4 | +0.1 | 0.98 (0.90-1.06) at 10%, 0.96 at 1%; finish +0.1; 558249 teams, 17 slates | no lean | 924, -1.6 | 34% / 46% | 29% |
| all | both | 1.00 (0.93-1.07) at 10%, 0.99 at 1%; finish -0.0; 869228 teams, 17 slates | +0.1 | -0.8 | +0.9 | 1.02 (0.95-1.09) at 10%, 1.02 at 1%; finish -0.3; 869228 teams, 17 slates | no lean | 1666, -1.3 | 36% / 47% | 32% |

## 3d. Candidate: my AM teams against my PM teams (for the Monday section; not a proposal)

A = my AM teams, B = my PM teams, inside the same contest and price group. Raw: each window's top-10% rate over the field's 10%. Then what differs, per team.

| | Teams | Raw top-10% | VALUE picks | PRICEY picks | Tagged picks | Projected drafted% of picks | Field sharing 4+ of 6 | Teams with an exact duplicate | Price | Points over price | Swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AM | 412 | 1.53 | 1.60 | 0.48 | 0.27 | 85% | 1.05% | 20% | 220.3 | +5.9 | 0.46 |
| PM | 1012 | 1.33 | 1.41 | 0.56 | 0.13 | 85% | 1.26% | 22% | 217.9 | +7.9 | 0.11 |

Inside the same contest and price group, AM against PM: 1.32 (1.08-1.59) at 10%, 1.74 at 1%; finish +2.6; 410 teams, 13 slates (five price groups); 1.13 (0.93-1.37) at 10%, 2.85 at 1%; finish +3.3; 394 teams, 13 slates (ten).

## 3e. Candidates for 11-16 (asked 2026-11-09; not proposals)

### 1. Same-position teammates: source, examples, and starter/backup instead

Position: Underdog's own position on the slate (the record's `pos`), grouped G (PG, SG, G), F (SF, PF, F), C. Underdog scores everyone as flex, so position matters here only as a stand-in for sharing minutes and touches. Five early/late same-position pairs on 2026-11-09's rosters:

- Donovan Mitchell (SG, round 2) + James Harden (PG, round 5), CLE
- Kevin Durant (PF, round 3) + Amen Thompson (SF, round 4), HOU
- Devin Booker (SG, round 3) + Jalen Green (SG, round 6), PHX
- RJ Barrett (SF, round 4) + Scottie Barnes (PF, round 2), TOR
- Cade Cunningham (PG, round 1) + Daniss Jenkins (PG, round 6), DET

Starter and direct backup instead of position: the starter averages 28+ minutes; his backup scores 4+ more points a game when the starter sits. Both from the morning file as it stood at that night's lock (the mirror's history: games through the night before, nothing later). The with/without splits start in the morning file around 10-29, so earlier nights have no pairs. Against teams with no two teammates:

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Same position, early + late (the approved card row) | 0.87 (0.77-0.97) at 10%, 0.82 at 1%; finish +1.9; 29713 teams, 16 slates | -1.7 | -4.3 (249%) | +2.6 (-149%) | - (holding) | 0.76 (0.68-0.84) at 10%, 0.66 at 1%; finish +3.6; 29655 teams, 16 slates | RULE against |
| Starter + his backup, any rounds | 0.62 (0.34-0.95) at 10%, 0.65 at 1%; finish +10.0; 9293 teams, 8 slates | -8.9 | -10.3 (115%) | +1.3 (-15%) | - (holding) | 0.54 (0.29-0.83) at 10%, 0.48 at 1%; finish +11.3; 9294 teams, 8 slates | RULE against |
| Starter early (rounds 1-3) + his backup late (rounds 4-6) | 0.47 (0.30-0.78) at 10%, 0.29 at 1%; finish +7.6; 3608 teams, 7 slates | -7.4 | -7.6 (102%) | +0.2 (-2%) | - (holding) | 0.40 (0.24-0.71) at 10%, 0.21 at 1%; finish +9.8; 3609 teams, 7 slates | RULE against |

### 2. Fallers: the definitions behind card-fallers

Ranks are the night's closing-ADP order. 6-drafter pods (4-drafter in brackets):
- **1/2 turn** (picks 6-7, or 5 and 8 [3-4, or 3 and 6]): your first player is a top-4 [top-2] ADP rank and your second is ranked 5-8 [3-6]. In the draft room: a top-4 [top-2] player still there at your turn pick; take him.
- **2/3 turn** (picks 12-13, or 11 and 14 [8-9, or 7 and 10]), for the 1.01 and 1.02 drafters: your second player is ranked 9th or better [5th or better], 3+ ranks ahead of your turn pick; take him.
Measured against same-contest, same-price teams that took the ADP-order pair at that turn (the trusting teams); the price-split check is in 3b. Fallers elsewhere in the draft: part 4 below.

### 3. Exposure, not order: T3 VALUE and T4 PRICEY

Against same-contest, same-price teams without (at each team's draft window).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| 2+ T3 VALUE players | 1.42 (0.94-1.86) at 10%, 1.82 at 1%; finish -5.1; 9603 teams, 10 slates | +5.6 | +8.7 (154%) | -3.0 (-54%) | - (holding) | 1.44 (0.96-1.87) at 10%, 1.84 at 1%; finish -5.2; 9603 teams, 10 slates | LEAN for |
| 1+ T3 VALUE player | 0.91 (0.72-1.14) at 10%, 0.83 at 1%; finish +0.3; 65878 teams, 14 slates | +0.1 | +2.1 | -2.0 | - (holding) | 0.86 (0.70-1.06) at 10%, 0.83 at 1%; finish +1.4; 65869 teams, 14 slates | LEAN against |
| A T4 PRICEY player | 1.01 (0.85-1.17) at 10%, 1.05 at 1%; finish -0.5; 89794 teams, 17 slates | +0.4 | +1.1 | -0.7 | - (holding) | 1.05 (0.86-1.26) at 10%, 1.20 at 1%; finish -1.3; 89694 teams, 17 slates | no lean |

### 4. Fallers in every round

A team's k-th player by the ADP it paid stands for its round-k pick (pick order isn't public, so this is a lower bound on the slide). A faller was paid an ADP 3+ picks before that round's first pick (round 3 on 6 drafters: ADP 10 or better). Explained: tagged at the team's window, or his tag changed between Lock AM and lock. A: teams with that faller in round k; B: teams whose round-k player wasn't a faller.

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Round 1, nothing explains it | none | - | - | - |
| Round 1, explained | none | - | - | - |
| Round 2, nothing explains it | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +7.1; 9 teams, 3 slates | -6.9 | -1.9 (28%) | -5.0 (72%) | -1.5 | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +7.2; 9 teams, 3 slates | not enough |
| Round 2, explained (tag or news) | 5.48 at 10%, 0.00 at 1%; finish -36.6; 1 teams, 1 slates | +49.6 | +13.9 (28%) | +35.7 (72%) | +23.1 | 7.37 at 10%, 0.00 at 1%; finish -41.7; 1 teams, 1 slates | not enough |
| Round 3, nothing explains it | 1.46 (1.12-1.94) at 10%, 3.28 at 1%; finish -5.0; 233 teams, 14 slates | +2.6 | +1.1 (44%) | +1.5 (56%) | +6.0 | 1.70 (1.31-2.20) at 10%, 3.83 at 1%; finish -7.7; 233 teams, 14 slates | RULE for |
| Round 3, explained (tag or news) | 1.90 (1.21-2.75) at 10%, 2.45 at 1%; finish -15.2; 136 teams, 4 slates | +15.9 | +15.3 (96%) | +0.7 (4%) | +20.2 | 2.69 (2.01-3.30) at 10%, 3.80 at 1%; finish -20.9; 136 teams, 4 slates | RULE for |
| Round 4, nothing explains it | 1.62 (1.08-2.08) at 10%, 2.04 at 1%; finish -9.5; 1202 teams, 18 slates | +7.2 | +2.8 (39%) | +4.3 (61%) | +5.8 | 1.71 (1.22-2.07) at 10%, 2.14 at 1%; finish -10.4; 1202 teams, 18 slates | RULE for |
| Round 4, explained (tag or news) | 1.39 (0.00-1.98) at 10%, 0.00 at 1%; finish -8.6; 20 teams, 3 slates | +2.2 | -0.6 (-28%) | +2.8 (128%) | +4.0 | 1.43 (0.00-2.07) at 10%, 0.00 at 1%; finish -8.4; 20 teams, 3 slates | not enough |
| Round 5, nothing explains it | 1.70 (1.32-2.07) at 10%, 2.74 at 1%; finish -7.1; 2626 teams, 17 slates | +5.7 | +1.0 (18%) | +4.7 (82%) | +0.8 | 1.71 (1.34-2.07) at 10%, 2.83 at 1%; finish -7.3; 2626 teams, 17 slates | RULE for |
| Round 5, explained (tag or news) | 2.24 (1.44-3.27) at 10%, 2.94 at 1%; finish -15.5; 166 teams, 5 slates | +11.5 | +10.7 (93%) | +0.8 (7%) | +9.7 | 2.15 (1.40-2.96) at 10%, 2.69 at 1%; finish -14.5; 166 teams, 5 slates | RULE for |
| Round 6, nothing explains it | 0.97 (0.79-1.15) at 10%, 1.02 at 1%; finish +1.8; 5012 teams, 18 slates | -1.9 | -4.8 (245%) | +2.8 (-145%) | -1.6 | 1.11 (0.93-1.28) at 10%, 1.20 at 1%; finish -0.4; 5012 teams, 18 slates | LEAN for |
| Round 6, explained (tag or news) | 1.83 (1.27-1.84) at 10%, 1.19 at 1%; finish -12.1; 187 teams, 3 slates | +10.2 | +2.8 (27%) | +7.4 (73%) | +6.6 | 1.74 (1.32-1.75) at 10%, 1.16 at 1%; finish -11.9; 187 teams, 3 slates | LEAN for |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.74 (0.56-1.01) at 10%, 0.56 at 1%; finish +1.4; 24337 teams, 18 slates | 1.74 (0.78-2.76) at 10%, 0.00 at 1%; finish -3.3; 122 teams, 16 slates |
| 1/2 | fallers vs trust | 1.57 (1.13-2.31) at 10%, 1.96 at 1%; finish -4.6; 38084 teams, 18 slates | 2.00 (1.18-3.35) at 10%, 2.91 at 1%; finish -8.1; 180 teams, 18 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.60 (0.50-3.26) at 10%, 2.53 at 1%; finish +0.1; 3934 teams, 13 slates | 2.84 (0.00-4.70) at 10%, 0.00 at 1%; finish -5.3; 53 teams, 8 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.06 (0.70-1.36) at 10%, 1.05 at 1%; finish -0.2; 11209 teams, 13 slates | 1.01 (0.00-2.36) at 10%, 0.00 at 1%; finish -6.5; 60 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.96 (0.38-1.87) at 10%, 0.62 at 1%; finish +0.2; 9173 teams, 14 slates | 2.02 (0.00-4.42) at 10%, 0.00 at 1%; finish -9.4; 37 teams, 12 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.01 (0.51-1.45) at 10%, 1.28 at 1%; finish +0.8; 8940 teams, 14 slates | 2.24 (1.00-3.48) at 10%, 4.14 at 1%; finish -9.9; 47 teams, 12 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.28 (0.25-2.99) at 10%, 1.43 at 1%; finish -1.8; 6857 teams, 13 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -2.7; 31 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 1.04 (0.63-1.45) at 10%, 1.12 at 1%; finish +0.4; 6045 teams, 13 slates | 1.58 (0.00-2.74) at 10%, 0.00 at 1%; finish -5.3; 42 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 0.84 (0.47-1.15) at 10%, 0.85 at 1%; finish +0.8; 5325 teams, 14 slates | 1.10 (0.00-2.96) at 10%, 0.00 at 1%; finish -7.6; 24 teams, 8 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.50 (0.58-2.61) at 10%, 1.65 at 1%; finish -0.0; 3797 teams, 13 slates | 3.17 (1.49-4.53) at 10%, 0.00 at 1%; finish -10.2; 32 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.46 (0.27-0.78) at 10%, 0.13 at 1%; finish -0.3; 3418 teams, 14 slates | 1.14 (0.00-5.18) at 10%, 0.00 at 1%; finish +7.2; 20 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.70 (0.27-1.26) at 10%, 0.38 at 1%; finish -1.6; 2916 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.05 (0.67-1.35) at 10%, 1.37 at 1%; finish -0.1; 1435 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +2.7; 13 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 1.17 (0.53-1.86) at 10%, 1.98 at 1%; finish -0.1; 1428 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +2.7; 11 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 1.42 (0.70-2.18) at 10%, 1.54 at 1%; finish -3.7; 1302 teams, 13 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.29 (0.27-2.49) at 10%, 1.99 at 1%; finish -6.4; 946 teams, 14 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.46 (0.29-0.65) at 10%, 0.00 at 1%; finish +1.3; 884 teams, 14 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.34 (0.17-0.56) at 10%, 0.00 at 1%; finish +8.9; 827 teams, 14 slates | none |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 1.24 (0.60-1.83) at 10%, 1.92 at 1%; finish -1.9; 772 teams, 13 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 2/3 | a. reach vs trust | 1.05 (0.89-1.24) at 10%, 1.29 at 1%; finish +1.5; 21879 teams, 18 slates | 1.60 (0.97-2.15) at 10%, 1.96 at 1%; finish -7.1; 105 teams, 17 slates |
| 2/3 | fallers vs trust | 1.14 (0.96-1.36) at 10%, 1.16 at 1%; finish -2.2; 15545 teams, 18 slates | 1.97 (1.36-2.70) at 10%, 1.76 at 1%; finish -8.0; 88 teams, 16 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.66 (1.28-2.10) at 10%, 2.45 at 1%; finish -6.7; 5018 teams, 17 slates | 2.03 (0.93-2.88) at 10%, 4.64 at 1%; finish -12.7; 54 teams, 11 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.25 (0.73-1.74) at 10%, 1.54 at 1%; finish +3.1; 2378 teams, 14 slates | 0.34 (0.00-0.53) at 10%, 0.00 at 1%; finish -3.4; 30 teams, 8 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.70 (0.51-0.85) at 10%, 0.21 at 1%; finish -2.0; 2876 teams, 13 slates | 0.93 (0.00-2.12) at 10%, 0.00 at 1%; finish -8.5; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 1.15 (0.67-1.57) at 10%, 1.28 at 1%; finish +3.7; 2767 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +19.2; 10 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 1.24 (0.72-1.78) at 10%, 1.55 at 1%; finish -1.8; 2507 teams, 14 slates | 0.35 (0.00-1.35) at 10%, 0.00 at 1%; finish +1.8; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 1.14 (0.62-1.57) at 10%, 0.83 at 1%; finish +2.8; 2498 teams, 13 slates | 1.95 (0.00-2.72) at 10%, 0.00 at 1%; finish +2.7; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.26 (0.75-1.72) at 10%, 1.94 at 1%; finish +7.0; 2196 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +18.4; 11 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.52 (0.32-0.75) at 10%, 0.29 at 1%; finish +0.8; 2006 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -13.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 1.06 (0.63-1.47) at 10%, 0.95 at 1%; finish -3.4; 1983 teams, 14 slates | 0.73 (0.00-1.63) at 10%, 2.91 at 1%; finish +0.8; 17 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 0.95 (0.66-1.28) at 10%, 0.72 at 1%; finish -2.5; 1950 teams, 14 slates | 0.74 (0.00-1.51) at 10%, 0.00 at 1%; finish -5.7; 6 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.44 (0.82-2.30) at 10%, 1.24 at 1%; finish -2.4; 1667 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +4.4; 7 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.29 (0.81-2.01) at 10%, 1.24 at 1%; finish -7.8; 1574 teams, 14 slates | 1.79 (0.68-3.18) at 10%, 4.07 at 1%; finish -7.3; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.75 (0.41-1.15) at 10%, 0.54 at 1%; finish +0.7; 1517 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +11.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.36 (0.86-1.83) at 10%, 1.20 at 1%; finish -4.1; 1427 teams, 14 slates | 3.56 (2.66-4.42) at 10%, 0.00 at 1%; finish -26.9; 10 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.76 (0.46-1.28) at 10%, 0.41 at 1%; finish -0.8; 1384 teams, 14 slates | 3.01 (0.85-6.14) at 10%, 0.00 at 1%; finish -22.1; 7 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 1.00 (0.54-1.48) at 10%, 0.80 at 1%; finish +0.5; 1380 teams, 13 slates | 1.35 (0.00-1.91) at 10%, 0.00 at 1%; finish -6.8; 7 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.40 (0.27-0.64) at 10%, 0.33 at 1%; finish +2.5; 1379 teams, 14 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +5.4; 9 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 11 | 1.20 (0.56-1.64) at 10%, 2.20 at 1%; finish -4.1; 1273 teams, 14 slates | 3.17 (1.78-4.21) at 10%, 0.00 at 1%; finish -14.8; 7 teams, 5 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 111 | 95% | 94% | +0 |
| AM | T1-T2 | Q TRAP | 15 | 67% | 93% | -26 |
| AM | T1-T2 | VALUE | 6 | 95% | 96% | -0 |
| AM | T3-T4 | PRICEY | 100 | 93% | 95% | -2 |
| AM | T3-T4 | Q FAIR | 1 | 15% | 95% | -80 |
| AM | T3-T4 | VALUE | 93 | 87% | 96% | -9 |
| AM | T5 | Q FAIR | 252 | 9% | 20% | -11 |
| AM | T5 | VALUE | 499 | 39% | 19% | +20 |
| PM | T1-T2 | PRICEY | 142 | 99% | 99% | -0 |
| PM | T1-T2 | Q TRAP | 18 | 75% | 99% | -24 |
| PM | T1-T2 | VALUE | 6 | 98% | 98% | -0 |
| PM | T3-T4 | PRICEY | 152 | 98% | 99% | -1 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 11 | 87% | 96% | -9 |
| PM | T3-T4 | VALUE | 137 | 95% | 99% | -4 |
| PM | T5 | Q FAIR | 192 | 12% | 20% | -8 |
| PM | T5 | VALUE | 502 | 61% | 23% | +38 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 98 (of all T5 breakers: VALUE 11, unflagged 107).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.16 (1.02-1.33) at 10%, 1.35 at 1%; finish -0.7; 107690 teams, 17 slates | 1.61 (1.34-1.95) at 10%, 1.74 at 1%; finish -7.3; 539 teams, 17 slates |
| Same-position teammates | 0.79 (0.70-0.93) at 10%, 0.89 at 1%; finish +4.5; 72554 teams, 18 slates | 1.31 (1.03-1.69) at 10%, 1.95 at 1%; finish -3.6; 308 teams, 18 slates |
| Same-position teammates, spread 5+ | 0.85 (0.75-0.93) at 10%, 0.74 at 1%; finish +1.7; 24788 teams, 15 slates | 1.60 (1.05-2.17) at 10%, 1.98 at 1%; finish -10.9; 136 teams, 14 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.67 | 1.59 | 1.03 | 1.25 | 0.80 | 0.98 | 0.87 | 0.01 | 0.08 | 0.00 | 2.78 |
| Field | 0.57 | 1.57 | 1.08 | 1.25 | 0.87 | 0.91 | 0.99 | 0.02 | 0.09 | 0.00 | 1.04 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.75 (0.62-0.88) at 10%, 0.77 at 1%; finish +6.0; 53390 teams, 17 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

477 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 187642 | 0.59 | 1.59 | 1.11 | 1.25 | 0.84 | 0.99 | 0.92 | 0.23 | 93% |
| Me | 1478 | 0.58 | 1.58 | 1.22 | 1.19 | 0.95 | 1.47 | 0.53 | 0.30 | 91% |
| Everyone | 316972 | 0.57 | 1.57 | 1.08 | 1.25 | 0.87 | 0.91 | 0.99 | 0.21 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.54 (0.26-0.81) at 10%, 0.36 at 1%; finish +11.5; 7913 teams, 5 slates |
| T1-T2 | AM | 0.69 (0.37-1.02) at 10%, 0.51 at 1%; finish +7.1; 3860 teams, 5 slates |
| T1-T2 | PM | 0.41 (0.11-0.65) at 10%, 0.23 at 1%; finish +15.7; 4053 teams, 3 slates |
| T3-T5 | both | 0.88 (0.73-1.04) at 10%, 1.00 at 1%; finish +2.0; 17349 teams, 11 slates |
| T3-T5 | AM | 0.86 (0.68-1.03) at 10%, 0.95 at 1%; finish +2.4; 8096 teams, 9 slates |
| T3-T5 | PM | 0.90 (0.68-1.15) at 10%, 1.05 at 1%; finish +1.6; 9253 teams, 9 slates |
| not credited | both | 0.76 (0.60-0.91) at 10%, 0.81 at 1%; finish +7.0; 21143 teams, 17 slates |
| not credited | AM | 0.79 (0.62-0.98) at 10%, 0.79 at 1%; finish +5.8; 10876 teams, 14 slates |
| not credited | PM | 0.72 (0.52-0.90) at 10%, 0.82 at 1%; finish +8.2; 10267 teams, 17 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 18 show a lean or rule and 12 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | LEAN for | LEAN for | 1.13 (1.01-1.26) | keep: points and money agree |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | RULE for | 1.22 (1.10-1.34) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | RULE for | RULE for | 1.21 (1.11-1.31) | candidate: hand to the rankings side with its points cost |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 1.11 (0.78-1.41) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 1.07 (0.84-1.30) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | no lean | 0.95 (0.79-1.12) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 1.08 (0.90-1.27) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | no lean | 0.99 (0.83-1.20) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | LEAN against | LEAN against | 0.82 (0.64-1.03) | watch: money leans against |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 0.95 (0.84-1.09) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 0.99 (0.80-1.31) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | RULE for | RULE for | 1.49 (1.19-2.10) | candidate: hand to the rankings side with its points cost |
| pm-t5-beneficiary | adopted | LEAN (listed) | LEAN for | no lean | 1.20 (0.95-1.52) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | RULE for | RULE for | 1.25 (1.14-1.37) | keep: the leverage pays (money RULE) |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.42 (1.23-1.62) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 1.22 (0.88-1.66) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.89 (0.74-1.14) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | RULE against | LEAN against | 0.78 (0.66-0.93) | keep on points; money leans against (watch) |
| one-tier-cap | adopted | LEAN (both windows) | LEAN against | LEAN against | 0.83 (0.66-1.05) | keep on points; money leans against (watch) |
| pm-middle-takes | candidate | LEAN (single window) | no lean | no lean | 1.03 (0.83-1.24) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | no lean | no lean | 0.94 (0.79-1.10) | keep on points; money not settled |
| am-t5-other-reads | candidate | LEAN against (single window) | LEAN for | LEAN for | 1.24 (1.01-1.54) | watch: money leans for the leverage, not yet its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

