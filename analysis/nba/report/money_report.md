# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-17. Slates 2026-10-20 to 2026-11-16: 27 nights, 87 contests, 442036 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

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
| 2026-11-12 | 6 | 5 | 17850 | 0 | 1824 | 1014 | 100% | 100% | 80 |
| 2026-11-13 | 6 | 5 | 20358 | 0 | 428 | 0 | 100% | 100% | 102 |
| 2026-11-14 | 6 | 5 | 16416 | 0 | 14048 | 2379 | 95% | 100% | 10 |
| 2026-11-15 | 6 | 2 | 9564 | 0 | 2919 | 1327 | 99% | 100% | 0 |
| 2026-11-16 | 6 | 5 | 18600 | 0 | 4593 | 2727 | 100% | 100% | 100 |

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 15 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_fri_main, nba_mon_main, nba_mon_main, nba_mon_main, nba_sat_main, nba_sat_main, nba_sun_main, nba_sun_main, nba_thu_main, nba_thu_main, nba_tue_main, nba_wed_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
  - 2026-11-13: 428 swapped-in picks, 0 credited
  - 2026-11-14: 14048 swapped-in picks, 2379 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 414530 of 442036 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

**Ten random teams**

| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |
|---|---|---|---|---|---|---|---|
| 2026-10-22 | Thursday Night Hoops | 4 | PM | 4 | 216.7 | 144.7 | 3.3, 7.5, 8.1, 14.9, 20.2, 21.0 |
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-07 | Saturday Slam | 6 | PM | 2 | 221.3 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 15.8 (swap) |
| 2026-11-09 | Monday Night Hoops | 6 | PM | 4 | 220.9 | 247.4 | 3.4, 11.7, 14.6, 20.1, 29.0, 31.3 |
| 2026-11-11 | Hump Day Hoops | 6 | AM | 2 | 213.8 | 216.5 | 4.3, 12.1, 15.1, 20.4, 29.1, 32.5 |
| 2026-11-12 | Thursday Night Hoops | 6 | PM | 2 | 216.3 | 279.2 | 2.1, 13.5, 18.6, 21.3, 26.3, 32.2 |
| 2026-11-13 | Fast Break Friday | 6 | PM | 5 | 227.0 | 231.6 | 1.1, 11.6, 13.5, 19.8, 23.8, 32.8 |
| 2026-11-15 | Sunday Shootaround | 6 | PM | 5 | 226.2 | 229.9 | 4.2, 10.3, 12.2, 21.2, 23.2, 25.9 |
| 2026-11-15 | Sunday Shootaround | 6 | PM | 4 | 221.6 | 148.1 | 2.6, 10.6, 14.5, 21.1, 25.3, 33.4 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.1 | 13 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.2 | 13 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.0 | 15 |
| Contest (its mean against its night's) | The Layup Line | -0.3 | 17 |
| Contest (its mean against its night's) | flagships | +0.0 | 25 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +2.0 | 76 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +6.0 | 82846 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.8 | 82900 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.0 | 82917 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -2.3 | 82496 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.5 | 83371 |
| Swap on the team (inside contest) | no | +1.0 | 335198 |
| Swap on the team (inside contest) | yes | -4.2 | 79332 |
| Window (inside contest) | AM | -0.5 | 124455 |
| Window (inside contest) | PM | +0.3 | 288477 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fast Break Friday | 6 | 4 | 372 | 0.54 | 1.40 | 1.45 | 1.34 | 40.0 | 1.38 (87) | 1.47 (285) | $1860 | $1567 | -16% |
| Hump Day Hoops | 6 | 4 | 330 | 0.91 | 1.21 | 1.30 | 1.12 | 50.6 | 1.62 (136) | 1.08 (194) | $1650 | $907 | -45% |
| Monday Night Hoops | 6 | 4 | 330 | 0.00 | 1.03 | 1.03 | 1.14 | 45.8 | 1.14 (79) | 1.00 (251) | $1650 | $1030 | -38% |
| Tuesday Tip-Off | 6 | 2 | 230 | 1.30 | 1.13 | 1.22 | 1.22 | 46.4 | 0.78 (90) | 1.50 (140) | $1150 | $1530 | +33% |
| Saturday Slam | 6 | 4 | 130 | 3.85 | 2.15 | 1.46 | 1.19 | 47.4 | 1.43 (28) | 1.50 (100) | $650 | $6579 | +912% |
| Sunday Shootaround | 6 | 2 | 120 | 0.83 | 1.33 | 1.33 | 1.38 | 41.3 | 3.00 (30) | 0.78 (90) | $600 | $480 | -20% |
| Buzzer Beater | 6 | 6 | 90 | 1.11 | 1.33 | 1.22 | 1.22 | 43.1 | 2.11 (19) | 0.99 (71) | $270 | $239 | -11% |
| Thursday Night Hoops | 6 | 1 | 80 | 0.00 | 1.00 | 1.00 | 0.94 | 45.9 | 1.75 (40) | 0.25 (40) | $400 | $234 | -42% |
| The Layup Line | 6 | 4 | 24 | 0.00 | 1.67 | 1.25 | 1.25 | 49.8 | 2.00 (5) | 1.05 (19) | $120 | $50 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 1.03 (39) | 1.77 (141) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 21 | 1706 | 0.88 | 1.29 | 1.27 (1.13-1.42) | 1.21 | 45.3 | 1.46 (514) | 1.18 (1190) | $8350 | $12616 | +51% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.82 (49) | 1.71 (175) | $1120 | $847 | -24% |
| **all** | - | 26 | 1930 | 0.88 | 1.31 | 1.30 (1.17-1.45) | 1.23 | 44.9 | 1.40 (563) | 1.25 (1365) | $9470 | $13463 | +42% |

Dollars: $9470 in fees, $13463 won, +42% ROI over 26 nights (80% range -29% to +134%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -23%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

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
| 2026-11-12 | 80 | Moussa Diabate 40% | Moussa Diabate + Ausar Thompson 20% | 4 (Kyrie Irving + Kyshawn George + LaMelo Ball) | 0.7% | 13 of 80 |
| 2026-11-13 | 102 | Zion Williamson 33% | Cameron Boozer + Josh Giddey 17% | 6 (Bam Adebayo + Cameron Boozer + Giannis Antetokounmpo) | 0.7% | 17 of 82 |
| 2026-11-14 | 10 | Thomas Bryant 80% | Thomas Bryant + Cam Spencer 60% | 2 (Aaron Gordon + Jamal Murray + Cameron Boozer) | 0.5% | 1 of 10 |
| 2026-11-16 | 100 | Donovan Mitchell 43% | Donovan Mitchell + Joel Embiid 19% | 6 (Donovan Mitchell + Joel Embiid + Deni Avdija) | 0.6% | 5 of 80 |

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.30 (1.17-1.46) at 10%, 0.83 at 1%; finish -5.6; 1874 teams, 24 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 0.98 (0.87-1.09) at 10%, 1.17 at 1%; finish +1.2; 101846 teams, 24 slates | 0.96 (0.85-1.08) at 10%, 1.17 at 1%; finish +1.5; 89677 teams, 20 slates | 1.17 (0.94-1.36) at 10%, 1.17 at 1%; finish -1.3; 12169 teams, 4 slates | 1.65 (1.19-2.12) at 10%, 1.23 at 1%; finish -7.2; 949 teams, 24 slates | no lean | no lean |
|   AM only | 0.70 (0.56-0.88) at 10%, 0.34 at 1%; finish +4.5; 18801 teams, 18 slates | 0.68 (0.55-0.86) at 10%, 0.34 at 1%; finish +4.9; 18416 teams, 15 slates | 7.48 (2.07-9.57) at 10%, 0.00 at 1%; finish -13.3; 385 teams, 3 slates | 0.47 (0.14-1.04) at 10%, 0.00 at 1%; finish +1.9; 65 teams, 10 slates | LEAN against | LEAN against |
|   PM only | 1.04 (0.92-1.17) at 10%, 1.36 at 1%; finish +0.6; 82323 teams, 24 slates | 1.03 (0.90-1.18) at 10%, 1.38 at 1%; finish +0.8; 70549 teams, 20 slates | 1.11 (0.82-1.36) at 10%, 1.15 at 1%; finish -0.6; 11774 teams, 4 slates | 1.84 (1.34-2.31) at 10%, 1.40 at 1%; finish -8.1; 873 teams, 22 slates | no lean | no lean |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.59 (1.19-2.15) at 10%, 2.28 at 1%; finish -6.3; 16039 teams, 6 slates | 1.59 (1.19-2.15) at 10%, 2.28 at 1%; finish -6.3; 16039 teams, 6 slates | none | 2.99 (0.92-3.65) at 10%, 3.42 at 1%; finish -14.8; 59 teams, 6 slates | LEAN for | LEAN for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.37 (1.19-1.57) at 10%, 1.51 at 1%; finish -4.5; 605555 teams, 24 slates | 1.17 (1.03-1.32) at 10%, 1.23 at 1%; finish -1.8; 463398 teams, 20 slates | 2.28 (1.77-3.03) at 10%, 3.16 at 1%; finish -13.3; 142157 teams, 4 slates | 1.62 (1.35-1.93) at 10%, 0.52 at 1%; finish -8.3; 5222 teams, 23 slates | RULE for | RULE for |
|   T3 | 1.53 (1.10-2.06) at 10%, 1.82 at 1%; finish -6.6; 211164 teams, 18 slates | 1.07 (0.73-1.53) at 10%, 1.12 at 1%; finish -1.1; 132087 teams, 14 slates | 2.75 (1.86-5.23) at 10%, 4.70 at 1%; finish -15.6; 79077 teams, 4 slates | 1.35 (0.97-1.87) at 10%, 0.00 at 1%; finish -10.1; 1749 teams, 18 slates | RULE for | RULE for |
|   T4 | 1.39 (1.22-1.58) at 10%, 1.59 at 1%; finish -4.2; 228210 teams, 20 slates | 1.24 (1.10-1.39) at 10%, 1.42 at 1%; finish -2.1; 184910 teams, 17 slates | 2.20 (1.84-2.36) at 10%, 2.56 at 1%; finish -13.1; 43300 teams, 3 slates | 1.91 (1.46-2.48) at 10%, 1.57 at 1%; finish -9.0; 1571 teams, 19 slates | RULE for | RULE for |
|   T5 | 1.14 (0.89-1.45) at 10%, 1.04 at 1%; finish -2.6; 166054 teams, 17 slates | 1.10 (0.85-1.44) at 10%, 1.01 at 1%; finish -1.6; 146316 teams, 14 slates | 1.60 (1.18-2.23) at 10%, 1.62 at 1%; finish -9.5; 19738 teams, 3 slates | 1.58 (1.42-1.75) at 10%, 0.23 at 1%; finish -6.5; 1902 teams, 17 slates | no lean | no lean |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.29 (1.17-1.41) at 10%, 1.47 at 1%; finish -2.6; 770407 teams, 24 slates | 1.21 (1.09-1.33) at 10%, 1.34 at 1%; finish -1.5; 629741 teams, 20 slates | 1.78 (1.52-2.12) at 10%, 2.28 at 1%; finish -7.3; 140666 teams, 4 slates | 1.80 (1.51-2.09) at 10%, 1.69 at 1%; finish -8.4; 4397 teams, 24 slates | RULE for | RULE for |
|   T1 | 1.58 (1.25-2.02) at 10%, 2.38 at 1%; finish -3.8; 140030 teams, 15 slates | 1.69 (1.26-2.31) at 10%, 2.62 at 1%; finish -5.3; 112896 teams, 12 slates | 1.24 (0.94-1.40) at 10%, 1.77 at 1%; finish +2.5; 27134 teams, 3 slates | 2.02 (1.20-3.04) at 10%, 2.77 at 1%; finish -6.6; 671 teams, 14 slates | RULE for | RULE for |
|   T2 | 1.26 (1.09-1.46) at 10%, 1.35 at 1%; finish -2.7; 377472 teams, 22 slates | 1.13 (0.98-1.31) at 10%, 1.17 at 1%; finish -0.5; 312149 teams, 18 slates | 2.14 (1.56-3.86) at 10%, 2.77 at 1%; finish -13.3; 65323 teams, 4 slates | 1.64 (1.33-2.01) at 10%, 1.32 at 1%; finish -8.1; 2222 teams, 22 slates | RULE for | RULE for |
|   T3 | 1.33 (1.07-1.67) at 10%, 1.44 at 1%; finish -4.0; 215647 teams, 19 slates | 1.25 (0.97-1.63) at 10%, 1.28 at 1%; finish -3.3; 174253 teams, 16 slates | 1.90 (1.43-3.19) at 10%, 3.48 at 1%; finish -7.0; 41394 teams, 3 slates | 2.18 (1.73-2.65) at 10%, 1.86 at 1%; finish -11.5; 1400 teams, 19 slates | LEAN for | RULE for **(changes)** |
|   T4 | 1.97 (0.66-3.92) at 10%, 2.48 at 1%; finish -11.5; 12667 teams, 4 slates | 1.65 (0.30-3.64) at 10%, 1.97 at 1%; finish -9.4; 11062 teams, 3 slates | 8.04 at 10%, 51.27 at 1%; finish -26.5; 1605 teams, 1 slates | 0.29 (0.00-0.32) at 10%, 0.00 at 1%; finish +7.9; 28 teams, 4 slates | LEAN for | LEAN for |
|   T5 | 0.78 (0.65-1.04) at 10%, 0.70 at 1%; finish +6.5; 24456 teams, 6 slates | 0.77 (0.61-1.07) at 10%, 0.76 at 1%; finish +6.1; 19305 teams, 4 slates | 0.84 at 10%, 0.48 at 1%; finish +7.9; 5151 teams, 2 slates | 1.11 (0.69-1.45) at 10%, 1.22 at 1%; finish -5.8; 76 teams, 5 slates | LEAN against | LEAN against |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 0.97 (0.76-1.30) at 10%, 0.86 at 1%; finish -0.0; 58018 teams, 18 slates | 0.93 (0.72-1.28) at 10%, 0.83 at 1%; finish +0.5; 51227 teams, 16 slates | 1.41 at 10%, 1.33 at 1%; finish -3.8; 6791 teams, 2 slates | 0.87 (0.63-1.11) at 10%, 0.00 at 1%; finish -4.5; 283 teams, 17 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.44 (1.19-1.76) at 10%, 1.68 at 1%; finish -5.6; 230298 teams, 20 slates | 1.43 (1.17-1.75) at 10%, 1.64 at 1%; finish -5.3; 216194 teams, 17 slates | 1.71 (1.11-2.62) at 10%, 3.43 at 1%; finish -10.0; 14104 teams, 3 slates | 1.62 (1.27-2.05) at 10%, 0.73 at 1%; finish -6.6; 1420 teams, 18 slates | RULE for | RULE for |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 0.87 (0.68-1.11) at 10%, 0.98 at 1%; finish +2.8; 166457 teams, 23 slates | 0.94 (0.73-1.21) at 10%, 1.07 at 1%; finish +1.8; 143585 teams, 20 slates | 0.53 (0.13-0.86) at 10%, 0.54 at 1%; finish +9.5; 22872 teams, 3 slates | 1.17 (0.77-1.65) at 10%, 1.68 at 1%; finish -2.1; 886 teams, 23 slates | no lean | no lean |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.87 (0.41-1.52) at 10%, 1.02 at 1%; finish +4.8; 20544 teams, 6 slates | 0.99 (0.46-1.83) at 10%, 1.25 at 1%; finish +3.0; 18937 teams, 5 slates | 0.13 at 10%, 0.03 at 1%; finish +26.5; 1607 teams, 1 slates | 1.49 (0.34-5.12) at 10%, 3.40 at 1%; finish -7.0; 43 teams, 6 slates | no lean | no lean |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 1.07 (0.98-1.17) at 10%, 0.88 at 1%; finish -2.3; 144549 teams, 24 slates | 1.06 (0.97-1.16) at 10%, 0.80 at 1%; finish -1.7; 119379 teams, 20 slates | 1.15 (0.78-1.54) at 10%, 1.75 at 1%; finish -5.3; 25170 teams, 4 slates | 1.36 (1.03-1.79) at 10%, 0.55 at 1%; finish -6.3; 793 teams, 22 slates | LEAN for | LEAN for |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.92 (0.79-1.04) at 10%, 0.91 at 1%; finish +1.3; 290157 teams, 22 slates | 0.95 (0.81-1.09) at 10%, 0.95 at 1%; finish +0.7; 247432 teams, 18 slates | 0.74 (0.59-0.92) at 10%, 0.64 at 1%; finish +5.0; 42725 teams, 4 slates | 1.34 (1.11-1.69) at 10%, 0.91 at 1%; finish -5.2; 1255 teams, 22 slates | LEAN against | LEAN against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.07 (0.81-1.37) at 10%, 1.09 at 1%; finish -0.4; 21237 teams, 17 slates | 1.11 (0.82-1.43) at 10%, 1.21 at 1%; finish -1.0; 19326 teams, 14 slates | 0.70 (0.17-0.71) at 10%, 0.35 at 1%; finish +5.1; 1911 teams, 3 slates | 1.17 (0.80-1.54) at 10%, 1.17 at 1%; finish -0.5; 175 teams, 12 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.11 (0.93-1.30) at 10%, 1.15 at 1%; finish -2.2; 33202 teams, 20 slates | 1.05 (0.85-1.28) at 10%, 1.03 at 1%; finish -1.1; 24419 teams, 16 slates | 1.24 (0.93-1.61) at 10%, 1.51 at 1%; finish -5.3; 8783 teams, 4 slates | 1.26 (0.81-1.86) at 10%, 0.00 at 1%; finish -8.8; 178 teams, 16 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 0.95 (0.82-1.10) at 10%, 0.95 at 1%; finish +2.2; 411296 teams, 19 slates | 0.89 (0.76-1.04) at 10%, 0.90 at 1%; finish +2.1; 300480 teams, 15 slates | 1.12 (0.86-1.67) at 10%, 1.06 at 1%; finish +2.5; 110816 teams, 4 slates | 1.18 (0.89-1.56) at 10%, 0.55 at 1%; finish -2.2; 1287 teams, 19 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 0.88 (0.80-0.99) at 10%, 0.71 at 1%; finish +0.3; 239738 teams, 19 slates | 0.86 (0.78-0.97) at 10%, 0.67 at 1%; finish +0.5; 213976 teams, 15 slates | 1.07 (0.68-1.17) at 10%, 1.17 at 1%; finish -1.2; 25762 teams, 4 slates | 0.93 (0.61-1.37) at 10%, 0.68 at 1%; finish -2.7; 1297 teams, 16 slates | LEAN against | LEAN against |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | 2.29 at 10%, 3.78 at 1%; finish -18.9; 2071 teams, 1 slates | none | 2.29 at 10%, 3.78 at 1%; finish -18.9; 2071 teams, 1 slates | 1.32 at 10%, 0.00 at 1%; finish -20.4; 33 teams, 1 slates | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 0.89 (0.41-1.01) at 10%, 0.65 at 1%; finish +1.5; 2041 teams, 9 slates | 0.89 (0.34-1.00) at 10%, 0.67 at 1%; finish +1.6; 1976 teams, 8 slates | 1.09 at 10%, 0.00 at 1%; finish -1.3; 65 teams, 1 slates | 1.38 (1.16-2.14) at 10%, 0.00 at 1%; finish -9.8; 30 teams, 3 slates | LEAN against | LEAN against |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 1.02 (0.84-1.21) at 10%, 1.06 at 1%; finish +0.4; 30007 teams, 12 slates | 1.08 (0.82-1.32) at 10%, 1.16 at 1%; finish +0.2; 21546 teams, 9 slates | 0.88 (0.66-1.03) at 10%, 0.82 at 1%; finish +0.8; 8461 teams, 3 slates | 1.09 (0.74-1.41) at 10%, 0.00 at 1%; finish +1.5; 157 teams, 11 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 1.08 (0.92-1.31) at 10%, 0.93 at 1%; finish -1.7; 19582 teams, 17 slates | 1.02 (0.86-1.23) at 10%, 0.87 at 1%; finish -1.4; 15993 teams, 15 slates | 1.35 at 10%, 1.14 at 1%; finish -2.9; 3589 teams, 2 slates | 2.04 (1.13-3.03) at 10%, 3.80 at 1%; finish -6.8; 55 teams, 11 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.14 (0.92-1.44) at 10%, 1.22 at 1%; finish -0.7; 14844 teams, 15 slates | 1.36 (1.09-1.76) at 10%, 1.56 at 1%; finish -3.5; 10718 teams, 12 slates | 0.66 (0.41-0.80) at 10%, 0.52 at 1%; finish +6.6; 4126 teams, 3 slates | 0.86 (0.37-1.60) at 10%, 0.00 at 1%; finish -5.6; 47 teams, 9 slates | no lean | LEAN for **(changes)** |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 0.98 (0.87-1.12) at 10%, 1.04 at 1%; finish -1.3; 41269 teams, 18 slates | 1.02 (0.87-1.22) at 10%, 1.14 at 1%; finish -0.5; 29287 teams, 14 slates | 0.90 (0.82-1.06) at 10%, 0.82 at 1%; finish -3.2; 11982 teams, 4 slates | 1.86 (1.04-2.67) at 10%, 1.12 at 1%; finish -8.3; 205 teams, 14 slates | no lean | no lean |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 0.90 (0.79-1.04) at 10%, 0.86 at 1%; finish +1.5; 201860 teams, 22 slates | 0.94 (0.79-1.12) at 10%, 0.92 at 1%; finish +0.2; 161942 teams, 18 slates | 0.79 (0.65-1.05) at 10%, 0.72 at 1%; finish +6.5; 39918 teams, 4 slates | 1.03 (0.80-1.37) at 10%, 0.33 at 1%; finish -4.8; 1455 teams, 21 slates | LEAN against | LEAN against |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 1.43 (1.14-1.81) at 10%, 1.47 at 1%; finish -5.6; 155424 teams, 22 slates | 1.32 (1.07-1.68) at 10%, 1.36 at 1%; finish -4.4; 146835 teams, 20 slates | 8.45 at 10%, 26.07 at 1%; finish -26.9; 8589 teams, 2 slates | 1.57 (1.24-1.96) at 10%, 0.77 at 1%; finish -9.3; 962 teams, 22 slates | RULE for | RULE for |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.24 (0.82-1.66) at 10%, 1.74 at 1%; finish -2.0; 29686 teams, 14 slates | 1.29 (0.85-1.71) at 10%, 1.90 at 1%; finish -2.8; 28563 teams, 13 slates | 0.40 at 10%, 0.14 at 1%; finish +18.5; 1123 teams, 1 slates | 1.02 (0.58-1.58) at 10%, 0.00 at 1%; finish +3.8; 82 teams, 11 slates | no lean | no lean |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 AM only | LEAN against | -4.4 | -2.8 (63%) | -1.7 (37%) | -5.1 | 0.70 (0.56-0.90) at 10%, 0.34 at 1%; finish +5.7; 18814 teams, 18 slates | LEAN against |
| leverage-t2-t4 | LEAN for | +6.0 | +5.1 (85%) | +0.9 (15%) | -2.8 | 1.50 (1.09-2.16) at 10%, 1.69 at 1%; finish -4.8; 15979 teams, 6 slates | LEAN for |
| value-up-middle-t5 | RULE for | +4.3 | +3.1 (73%) | +1.2 (27%) | +1.4 | 1.32 (1.13-1.53) at 10%, 1.43 at 1%; finish -4.0; 605548 teams, 24 slates | RULE for |
| value-up-middle-t5 T3 | RULE for | +6.1 | +5.1 (84%) | +1.0 (16%) | +5.4 | 1.55 (1.11-2.10) at 10%, 1.83 at 1%; finish -6.8; 211180 teams, 18 slates | RULE for |
| value-up-middle-t5 T4 | RULE for | +4.2 | +3.4 (82%) | +0.7 (18%) | +3.4 | 1.37 (1.19-1.57) at 10%, 1.58 at 1%; finish -4.0; 228224 teams, 20 slates | RULE for |
| pricey-flags | RULE for | +2.8 | +4.0 (143%) | -1.2 (-43%) | +4.8 | 1.29 (1.15-1.44) at 10%, 1.50 at 1%; finish -2.6; 770467 teams, 24 slates | RULE for |
| pricey-flags T1 | RULE for | +2.7 | +5.1 (190%) | -2.4 (-90%) | +8.3 | 1.52 (1.12-2.07) at 10%, 2.26 at 1%; finish -3.4; 140052 teams, 15 slates | RULE for |
| pricey-flags T2 | RULE for | +3.0 | +3.5 (117%) | -0.5 (-17%) | +4.1 | 1.25 (1.07-1.48) at 10%, 1.33 at 1%; finish -2.9; 377486 teams, 22 slates | RULE for |
| pricey-flags T3 | LEAN for | +4.3 | +5.1 (117%) | -0.7 (-17%) | +4.4 | 1.32 (1.06-1.64) at 10%, 1.44 at 1%; finish -3.8; 215662 teams, 19 slates | LEAN for |
| pricey-flags T4 | LEAN for | +10.9 | +6.9 (63%) | +4.0 (37%) | +6.9 | 1.93 (0.66-3.70) at 10%, 2.40 at 1%; finish -11.1; 12666 teams, 4 slates | LEAN for |
| pricey-flags T5 | LEAN against | -5.4 | +0.4 (-7%) | -5.8 (107%) | -7.7 | 0.89 (0.65-1.39) at 10%, 0.81 at 1%; finish +3.6; 24472 teams, 6 slates | no lean |
| am-t5-button-order | RULE for | +5.4 | +3.7 (68%) | +1.7 (32%) | +1.4 | 1.46 (1.20-1.78) at 10%, 1.72 at 1%; finish -5.9; 230269 teams, 20 slates | RULE for |
| pm-t5-adp-value | LEAN for | +1.4 | -1.3 (-93%) | +2.8 (193%) | +0.7 | 0.92 (0.79-1.10) at 10%, 0.68 at 1%; finish -0.9; 144560 teams, 24 slates | no lean |
| one-tier-cap | LEAN against | -1.2 | -0.6 (52%) | -0.6 (48%) | +0.9 | 0.93 (0.81-1.05) at 10%, 0.92 at 1%; finish +1.0; 290187 teams, 22 slates | no lean |
| q-tag-raises | LEAN against | -0.5 | -1.1 (215%) | +0.6 (-115%) | +1.6 | 0.90 (0.82-1.02) at 10%, 0.74 at 1%; finish -0.2; 239710 teams, 19 slates | LEAN against |
| q-class-x:FAIR | LEAN against | -1.1 | -4.1 (385%) | +3.1 (-285%) | - (holding) | 0.81 (0.37-0.91) at 10%, 0.59 at 1%; finish +3.3; 2041 teams, 9 slates | LEAN against |
| pm-middle-takes | LEAN against | -1.5 | -1.2 (79%) | -0.3 (21%) | -0.6 | 0.92 (0.81-1.05) at 10%, 0.91 at 1%; finish +1.1; 201863 teams, 22 slates | no lean |
| pm-t2-other-reads | RULE for | +5.2 | +4.6 (89%) | +0.6 (11%) | +4.3 | 1.42 (1.13-1.81) at 10%, 1.39 at 1%; finish -5.5; 155419 teams, 22 slates | RULE for |
| turn 1/2: a. reach vs trust | RULE against | -1.7 | +0.0 (-0%) | -1.7 (100%) | -1.5 | 0.69 (0.58-0.85) at 10%, 0.50 at 1%; finish +3.1; 35218 teams, 25 slates | RULE against |
| turn 1/2: fallers vs trust | LEAN for | +2.9 | -0.0 (-1%) | +2.9 (101%) | +3.0 | 1.35 (1.03-1.86) at 10%, 1.52 at 1%; finish -3.6; 53478 teams, 25 slates | LEAN for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +1.5 | +2.2 (147%) | -0.7 (-47%) | +1.0 | 1.18 (0.70-1.98) at 10%, 0.96 at 1%; finish -0.1; 5734 teams, 19 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | -0.1 | +3.3 | -3.4 | +0.7 | 1.03 (0.88-1.19) at 10%, 1.18 at 1%; finish +0.8; 30727 teams, 25 slates | no lean |
| turn 2/3: fallers vs trust | LEAN for | +2.8 | +0.6 (21%) | +2.2 (79%) | +1.9 | 1.19 (1.03-1.39) at 10%, 1.33 at 1%; finish -3.8; 22373 teams, 25 slates | LEAN for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +8.2 | +9.7 (118%) | -1.4 (-18%) | +6.9 | 1.65 (1.39-1.93) at 10%, 2.33 at 1%; finish -7.6; 6940 teams, 23 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | RULE for | +1.6 | +2.0 (123%) | -0.4 (-23%) | - (holding) | 1.04 (0.93-1.17) at 10%, 1.09 at 1%; finish +0.4; 165139 teams, 24 slates | no lean |
| stack: Same-position teammates | RULE against | -3.0 | -6.6 (221%) | +3.6 (-121%) | - (holding) | 0.77 (0.68-0.87) at 10%, 0.82 at 1%; finish +3.4; 92547 teams, 25 slates | RULE against |
| stack: Same-position teammates, spread 5+ | LEAN against | -0.9 | -2.9 (311%) | +2.0 (-211%) | - (holding) | 0.82 (0.73-0.92) at 10%, 0.64 at 1%; finish +1.5; 42215 teams, 22 slates | RULE against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 15 | 222 | -1.0 | -1 | -230 |
| the swap board, near-ties least drafted first (leverage) | 15 | 222 | -0.6 | +2 | -111 |
| the swap board, near-ties most drafted first (spread) | 15 | 222 | -0.9 | +0 | -246 |

Leverage against spread: the leverage board's swaps would have made -2 top-10% finishes and $-135 against the spread board's (real minus each, differenced). Leverage put 69% of a night's replayed swaps on one player, spread 55%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.07 (0.92-1.24) at 10%, 1.01 at 1%; finish -0.7; 32701 teams, 19 slates | +0.7 | +0.9 (129%) | -0.2 (-29%) | 1.03 (0.89-1.20) at 10%, 0.94 at 1%; finish -0.2; 32700 teams, 19 slates | no lean |
| rounds 1-2 | 3.41 (2.71-4.05) at 10%, 10.75 at 1%; finish -15.3; 743 teams, 3 slates | +14.9 | +12.7 (85%) | +2.2 (15%) | 3.19 (2.64-3.99) at 10%, 9.37 at 1%; finish -14.8; 743 teams, 3 slates | LEAN for |
| rounds 3-4 | 1.03 (0.84-1.26) at 10%, 0.90 at 1%; finish +0.5; 9032 teams, 10 slates | -0.5 | +0.6 (-119%) | -1.2 (219%) | 1.00 (0.82-1.24) at 10%, 0.83 at 1%; finish +0.7; 9029 teams, 10 slates | no lean |
| rounds 5-6 or undrafted | 1.06 (0.89-1.25) at 10%, 0.98 at 1%; finish -0.8; 23097 teams, 16 slates | +0.9 | +0.7 (74%) | +0.2 (26%) | 1.03 (0.87-1.23) at 10%, 0.94 at 1%; finish -0.3; 23097 teams, 16 slates | no lean |

## 3c. Splits for Monday: teammates and takes by source

Each with the price-split check (section 3b). Lift: top-10% against same-contest, same-price teams.

### Teammates, by the rounds paid for them

A: teams with that teammate pair; B: teams with no two teammates at all (so same- and different-position pairs face the same comparison).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pair | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| Same position, both rounds 1-3 | 1.16 (0.79-1.56) at 10%, 1.20 at 1%; finish -4.7; 10685 teams, 16 slates | +3.4 | -1.8 (-53%) | +5.2 (153%) | 1.16 (0.79-1.56) at 10%, 1.27 at 1%; finish -4.4; 10684 teams, 16 slates | no lean |
| Same position, one in rounds 1-3 and one in 4-6 | 0.89 (0.80-0.97) at 10%, 0.89 at 1%; finish +1.5; 44628 teams, 23 slates | -1.4 | -4.8 (348%) | +3.4 (-248%) | 0.80 (0.71-0.89) at 10%, 0.72 at 1%; finish +2.7; 44571 teams, 23 slates | RULE against |
| Same position, both rounds 4-6 | 1.23 (1.11-1.36) at 10%, 1.38 at 1%; finish -4.5; 20802 teams, 23 slates | +3.8 | +0.6 (17%) | +3.2 (83%) | 1.21 (1.09-1.33) at 10%, 1.38 at 1%; finish -4.2; 20799 teams, 23 slates | RULE for |
| Different-position teammates (any rounds) | 1.14 (1.07-1.21) at 10%, 1.26 at 1%; finish -1.8; 181683 teams, 23 slates | +1.6 | -0.4 (-27%) | +2.0 (127%) | 1.00 (0.87-1.16) at 10%, 1.03 at 1%; finish +0.3; 152345 teams, 23 slates | no lean |

### Your takes by source (takes_history.csv)

A: teams holding the player you put first; B: the button's first, in the take's window (field and mine). Field drafted%: the share of that window's pods that took each. Points: the takes file's average gain per take (yours).

| Source | Window | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pick | From the other picks | Lift matched on the other picks' price | Verdict that survives | Takes, points per take | Field drafted%: yours / the button's | Yours the more drafted |
|---|---|---|---|---|---|---|---|---|---|---|
| ETR | PM | 1.03 (0.79-1.34) at 10%, 0.95 at 1%; finish -0.2; 36896 teams, 11 slates | -0.2 | -1.0 | +0.8 | 1.07 (0.82-1.40) at 10%, 1.02 at 1%; finish -0.8; 36887 teams, 11 slates | no lean | 33, +0.1 | 57% / 62% | 24% |
| ETR | both | 1.03 (0.79-1.34) at 10%, 0.95 at 1%; finish -0.2; 36896 teams, 11 slates | -0.2 | -1.0 | +0.8 | 1.07 (0.82-1.40) at 10%, 1.02 at 1%; finish -0.8; 36887 teams, 11 slates | no lean | 33, +0.1 | 57% / 62% | 24% |
| Bagel | PM | 1.08 (0.87-1.42) at 10%, 1.18 at 1%; finish +0.3; 59643 teams, 11 slates | -0.4 | +0.6 | -1.0 | 1.10 (0.92-1.36) at 10%, 1.19 at 1%; finish +0.2; 59637 teams, 11 slates | no lean | 38, +1.6 | 81% / 81% | 58% |
| Bagel | both | 1.08 (0.87-1.42) at 10%, 1.18 at 1%; finish +0.3; 59643 teams, 11 slates | -0.4 | +0.6 | -1.0 | 1.10 (0.92-1.36) at 10%, 1.19 at 1%; finish +0.2; 59637 teams, 11 slates | no lean | 38, +1.6 | 81% / 81% | 58% |
| Bagel+ETR | PM | 1.07 (0.91-1.28) at 10%, 1.03 at 1%; finish -0.5; 158992 teams, 12 slates | +0.9 | +1.1 (119%) | -0.2 (-19%) | 1.09 (0.93-1.30) at 10%, 1.06 at 1%; finish -0.8; 158998 teams, 12 slates | no lean | 115, +2.4 | 70% / 70% | 47% |
| Bagel+ETR | both | 1.07 (0.91-1.28) at 10%, 1.03 at 1%; finish -0.5; 158992 teams, 12 slates | +0.9 | +1.1 (119%) | -0.2 (-19%) | 1.09 (0.93-1.30) at 10%, 1.06 at 1%; finish -0.8; 158998 teams, 12 slates | no lean | 115, +2.4 | 70% / 70% | 47% |
| NEWS | AM | 1.01 (0.87-1.16) at 10%, 1.02 at 1%; finish -0.4; 226184 teams, 20 slates | +0.3 | -0.9 | +1.2 | 1.00 (0.86-1.16) at 10%, 1.01 at 1%; finish -0.1; 226183 teams, 20 slates | no lean | 281, -0.6 | 80% / 78% | 51% |
| NEWS | PM | 0.90 (0.69-1.12) at 10%, 0.81 at 1%; finish +0.1; 138258 teams, 17 slates | -0.7 | -0.8 (112%) | +0.1 (-12%) | 0.87 (0.67-1.11) at 10%, 0.78 at 1%; finish +0.3; 138248 teams, 17 slates | no lean | 108, -1.2 | 70% / 75% | 35% |
| NEWS | both | 0.97 (0.86-1.11) at 10%, 0.94 at 1%; finish -0.2; 364464 teams, 23 slates | -0.1 | -0.8 | +0.8 | 0.95 (0.84-1.09) at 10%, 0.92 at 1%; finish -0.0; 364459 teams, 23 slates | no lean | 389, -0.8 | 77% / 77% | 46% |
| OTHER | AM | 1.08 (0.92-1.29) at 10%, 1.07 at 1%; finish +0.4; 19370 teams, 3 slates | +0.2 | +0.5 | -0.3 | 1.09 (0.94-1.28) at 10%, 1.09 at 1%; finish +0.4; 19370 teams, 3 slates | LEAN for | 43, +3.2 | 49% / 49% | 49% |
| OTHER | PM | 0.80 (0.44-1.40) at 10%, 0.63 at 1%; finish +0.3; 33611 teams, 10 slates | +0.0 | -2.7 | +2.8 | 0.78 (0.44-1.31) at 10%, 0.61 at 1%; finish +1.3; 33613 teams, 10 slates | no lean | 64, -0.9 | 61% / 65% | 36% |
| OTHER | both | 0.91 (0.64-1.25) at 10%, 0.80 at 1%; finish +0.4; 52981 teams, 11 slates | +0.0 | -1.6 | +1.6 | 0.90 (0.63-1.22) at 10%, 0.79 at 1%; finish +1.0; 52983 teams, 11 slates | no lean | 107, +0.8 | 56% / 59% | 41% |
| all | AM | 1.01 (0.88-1.16) at 10%, 1.02 at 1%; finish -0.3; 245554 teams, 20 slates | +0.3 | -0.8 | +1.1 | 1.01 (0.88-1.15) at 10%, 1.01 at 1%; finish -0.1; 245553 teams, 20 slates | no lean | 324, -0.1 | 76% / 74% | 50% |
| all | PM | 0.99 (0.87-1.12) at 10%, 0.94 at 1%; finish -0.0; 427468 teams, 23 slates | -0.0 | -0.2 | +0.2 | 0.99 (0.87-1.13) at 10%, 0.94 at 1%; finish -0.1; 427469 teams, 23 slates | no lean | 358, +0.4 | 69% / 71% | 41% |
| all | both | 1.00 (0.92-1.10) at 10%, 0.97 at 1%; finish -0.2; 673040 teams, 23 slates | +0.1 | -0.3 | +0.5 | 0.99 (0.91-1.09) at 10%, 0.97 at 1%; finish -0.1; 673040 teams, 23 slates | no lean | 682, +0.2 | 72% / 72% | 45% |

## 3d. Candidate: my AM teams against my PM teams (for the Monday section; not a proposal)

A = my AM teams, B = my PM teams, inside the same contest and price group. Raw: each window's top-10% rate over the field's 10%. Then what differs, per team.

| | Teams | Raw top-10% | VALUE picks | PRICEY picks | Tagged picks | Projected drafted% of picks | Field sharing 4+ of 6 | Teams with an exact duplicate | Price | Points over price | Swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AM | 563 | 1.40 | 1.82 | 0.66 | 0.35 | 93% | 0.98% | 18% | 220.1 | +4.4 | 0.45 |
| PM | 1311 | 1.27 | 1.58 | 0.60 | 0.15 | 90% | 1.16% | 21% | 218.1 | +7.6 | 0.11 |

Inside the same contest and price group, AM against PM: 1.18 (0.89-1.55) at 10%, 1.25 at 1%; finish +1.3; 561 teams, 18 slates (five price groups); 1.03 (0.79-1.34) at 10%, 1.71 at 1%; finish +2.3; 530 teams, 18 slates (ten).

## 3e. Candidates for 11-16 (asked 2026-11-09; not proposals)

### 1. Same-position teammates: source, examples, and starter/backup instead

Position: Underdog's own position on the slate (the record's `pos`), grouped G (PG, SG, G), F (SF, PF, F), C. Underdog scores everyone as flex, so position matters here only as a stand-in for sharing minutes and touches. Five early/late same-position pairs on 2026-11-16's rosters:

- Tyrese Maxey (PG, round 2) + VJ Edgecombe (SG, round 6), PHI
- Donovan Mitchell (SG, round 2) + James Harden (PG, round 4), CLE
- LaMelo Ball (PG, round 2) + Ayo Dosunmu (SG, round 6), MIN
- Jayson Tatum (PF, round 1) + Paul George (PF, round 5), BOS
- Jaylen Brown (SF, round 3) + LeBron James (SF, round 5), PHI

Starter and direct backup instead of position: the starter averages 28+ minutes; his backup scores 4+ more points a game when the starter sits. Both from the morning file as it stood at that night's lock (the mirror's history: games through the night before, nothing later). The with/without splits start in the morning file around 10-29, so earlier nights have no pairs. Against teams with no two teammates:

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Same position, early + late (the approved card row) | 0.89 (0.80-0.97) at 10%, 0.89 at 1%; finish +1.5; 44628 teams, 23 slates | -1.4 | -4.8 (348%) | +3.4 (-248%) | - (holding) | 0.80 (0.71-0.89) at 10%, 0.72 at 1%; finish +2.7; 44571 teams, 23 slates | RULE against |
| Starter + his backup, any rounds | 0.94 (0.70-1.14) at 10%, 0.95 at 1%; finish +2.1; 27538 teams, 15 slates | -1.8 | -4.4 (239%) | +2.5 (-139%) | - (holding) | 0.90 (0.65-1.14) at 10%, 0.73 at 1%; finish +2.3; 27522 teams, 15 slates | no lean |
| Starter early (rounds 1-3) + his backup late (rounds 4-6) | 0.78 (0.62-0.97) at 10%, 0.57 at 1%; finish +3.4; 10688 teams, 14 slates | -3.2 | -5.1 (161%) | +1.9 (-61%) | - (holding) | 0.74 (0.56-0.93) at 10%, 0.51 at 1%; finish +4.1; 10689 teams, 14 slates | LEAN against |

### 2. Fallers: the definitions behind card-fallers

Ranks are the night's closing-ADP order. 6-drafter pods (4-drafter in brackets):
- **1/2 turn** (picks 6-7, or 5 and 8 [3-4, or 3 and 6]): your first player is a top-4 [top-2] ADP rank and your second is ranked 5-8 [3-6]. In the draft room: a top-4 [top-2] player still there at your turn pick; take him.
- **2/3 turn** (picks 12-13, or 11 and 14 [8-9, or 7 and 10]), for the 1.01 and 1.02 drafters: your second player is ranked 9th or better [5th or better], 3+ ranks ahead of your turn pick; take him.
Measured against same-contest, same-price teams that took the ADP-order pair at that turn (the trusting teams); the price-split check is in 3b. Fallers elsewhere in the draft: part 4 below.

### 3. Exposure, not order: T3 VALUE and T4 PRICEY

Against same-contest, same-price teams without (at each team's draft window).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| 2+ T3 VALUE players | 1.63 (1.27-1.90) at 10%, 2.27 at 1%; finish -9.6; 15186 teams, 16 slates | +9.4 | +11.3 (121%) | -1.9 (-21%) | - (holding) | 1.64 (1.28-1.91) at 10%, 2.30 at 1%; finish -9.6; 15186 teams, 16 slates | RULE for |
| 1+ T3 VALUE player | 1.24 (0.98-1.53) at 10%, 1.26 at 1%; finish -4.5; 111223 teams, 21 slates | +4.3 | +4.4 (101%) | -0.1 (-1%) | - (holding) | 1.12 (0.90-1.35) at 10%, 1.16 at 1%; finish -3.4; 111218 teams, 21 slates | no lean |
| A T4 PRICEY player | 0.79 (0.62-0.97) at 10%, 0.60 at 1%; finish +3.2; 21670 teams, 8 slates | -3.0 | -5.2 (175%) | +2.2 (-75%) | - (holding) | 0.75 (0.60-0.93) at 10%, 0.56 at 1%; finish +3.6; 21670 teams, 8 slates | LEAN against |

### 4. Fallers in every round

A team's k-th player by the ADP it paid stands for its round-k pick (pick order isn't public, so this is a lower bound on the slide). A faller was paid an ADP 3+ picks before that round's first pick (round 3 on 6 drafters: ADP 10 or better). Explained: tagged at the team's window, or his tag changed between Lock AM and lock. A: teams with that faller in round k; B: teams whose round-k player wasn't a faller.

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Round 1, nothing explains it | none | - | - | - |
| Round 1, explained | none | - | - | - |
| Round 2, nothing explains it | 0.49 (0.00-1.46) at 10%, 5.04 at 1%; finish +1.0; 20 teams, 7 slates | -2.5 | +2.9 (-116%) | -5.3 (216%) | +7.5 | 0.50 (0.00-1.43) at 10%, 4.72 at 1%; finish +0.3; 20 teams, 7 slates | not enough |
| Round 2, explained (tag or news) | 5.48 at 10%, 0.00 at 1%; finish -36.6; 1 teams, 1 slates | +49.6 | +13.9 (28%) | +35.7 (72%) | +23.1 | 7.37 at 10%, 0.00 at 1%; finish -41.7; 1 teams, 1 slates | not enough |
| Round 3, nothing explains it | 1.16 (0.94-1.50) at 10%, 1.82 at 1%; finish -3.6; 523 teams, 21 slates | +0.8 | -1.8 (-236%) | +2.6 (336%) | +3.0 | 1.26 (0.96-1.75) at 10%, 2.00 at 1%; finish -3.6; 523 teams, 21 slates | LEAN for |
| Round 3, explained (tag or news) | 1.86 (1.15-2.68) at 10%, 2.38 at 1%; finish -13.8; 143 teams, 6 slates | +14.6 | +13.3 (91%) | +1.3 (9%) | +18.2 | 2.60 (1.84-3.15) at 10%, 3.70 at 1%; finish -18.9; 143 teams, 6 slates | LEAN for |
| Round 4, nothing explains it | 1.48 (1.11-1.85) at 10%, 1.71 at 1%; finish -7.0; 1666 teams, 25 slates | +5.0 | +1.6 (33%) | +3.4 (67%) | +4.1 | 1.56 (1.21-1.87) at 10%, 1.85 at 1%; finish -7.8; 1666 teams, 25 slates | RULE for |
| Round 4, explained (tag or news) | 1.66 (0.97-2.18) at 10%, 0.00 at 1%; finish -9.6; 60 teams, 6 slates | +5.0 | +6.0 (120%) | -1.0 (-20%) | +8.4 | 1.73 (0.98-2.29) at 10%, 0.00 at 1%; finish -9.8; 60 teams, 6 slates | not enough |
| Round 5, nothing explains it | 1.81 (1.50-2.10) at 10%, 3.03 at 1%; finish -8.8; 3888 teams, 24 slates | +7.7 | +2.2 (29%) | +5.5 (71%) | +2.2 | 1.85 (1.54-2.12) at 10%, 3.15 at 1%; finish -9.0; 3888 teams, 24 slates | RULE for |
| Round 5, explained (tag or news) | 2.22 (1.41-3.14) at 10%, 3.27 at 1%; finish -15.4; 174 teams, 8 slates | +11.6 | +10.3 (89%) | +1.3 (11%) | +9.5 | 2.15 (1.42-2.92) at 10%, 3.04 at 1%; finish -14.5; 174 teams, 8 slates | RULE for |
| Round 6, nothing explains it | 1.02 (0.88-1.19) at 10%, 1.03 at 1%; finish -0.1; 6089 teams, 25 slates | -0.3 | -4.0 | +3.6 | -0.8 | 1.15 (1.01-1.29) at 10%, 1.19 at 1%; finish -1.7; 6089 teams, 25 slates | LEAN for |
| Round 6, explained (tag or news) | 1.83 (1.27-1.84) at 10%, 1.19 at 1%; finish -12.1; 187 teams, 3 slates | +10.2 | +2.8 (27%) | +7.4 (73%) | +6.6 | 1.74 (1.32-1.75) at 10%, 1.16 at 1%; finish -11.9; 187 teams, 3 slates | LEAN for |

### 5. The original rules (kept-*), asked 2026-11-11

Each tier's kept rule is the Tiers button's order there. A: teams holding the button's first of a decision pair (ADP within 4, same tier) and not its second; B: the reverse. Only pairs with the same flag and no tag on either, so the order is the rule's steps, not VALUE first / PRICEY last or a Questionable push (those have their own rows).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| AM T1: ADP, Boom deciding within 2 picks | 1.96 (1.39-2.79) at 10%, 2.43 at 1%; finish -7.6; 57921 teams, 19 slates | +7.9 | +6.9 (87%) | +1.0 (13%) | +7.5 | 2.00 (1.39-2.89) at 10%, 2.42 at 1%; finish -8.3; 57914 teams, 19 slates | RULE for |
| PM T1: ETR | 1.13 (0.97-1.31) at 10%, 1.14 at 1%; finish -2.2; 153091 teams, 24 slates | +2.2 | +1.9 (88%) | +0.3 (12%) | +3.4 | 1.21 (1.01-1.46) at 10%, 1.25 at 1%; finish -3.3; 153096 teams, 24 slates | LEAN for |
| AM T2: ADP straight | 0.97 (0.87-1.08) at 10%, 1.03 at 1%; finish +0.3; 331388 teams, 20 slates | -0.5 | +1.1 | -1.6 | +2.1 | 1.00 (0.90-1.11) at 10%, 1.07 at 1%; finish -0.1; 331381 teams, 20 slates | no lean |
| AM T3/T4: Proj, ADP deciding within 3 points | 0.97 (0.83-1.16) at 10%, 0.90 at 1%; finish +0.6; 156359 teams, 20 slates | -0.5 | -0.0 | -0.5 | +1.5 | 1.01 (0.86-1.21) at 10%, 0.92 at 1%; finish -0.0; 156358 teams, 20 slates | no lean |
| PM T3: ETR, ties to ADP then Boom | 1.10 (0.97-1.24) at 10%, 0.97 at 1%; finish -2.4; 224136 teams, 23 slates | +2.4 | +2.9 (120%) | -0.5 (-20%) | +2.8 | 1.13 (0.99-1.28) at 10%, 1.01 at 1%; finish -2.9; 224134 teams, 23 slates | LEAN for |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.69 (0.58-0.85) at 10%, 0.48 at 1%; finish +2.7; 35225 teams, 25 slates | 1.52 (0.74-2.45) at 10%, 0.00 at 1%; finish -3.4; 140 teams, 21 slates |
| 1/2 | fallers vs trust | 1.34 (1.03-1.81) at 10%, 1.71 at 1%; finish -2.9; 53440 teams, 25 slates | 1.56 (0.97-2.40) at 10%, 2.32 at 1%; finish -6.0; 270 teams, 23 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.19 (0.73-1.99) at 10%, 0.92 at 1%; finish -0.7; 5737 teams, 19 slates | 1.51 (0.49-3.43) at 10%, 0.00 at 1%; finish -4.5; 63 teams, 11 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.34 (0.82-1.88) at 10%, 1.96 at 1%; finish -2.9; 18729 teams, 20 slates | 0.65 (0.00-1.54) at 10%, 0.00 at 1%; finish -5.2; 78 teams, 14 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.22 (0.88-1.55) at 10%, 1.29 at 1%; finish -1.3; 14291 teams, 21 slates | 1.72 (1.00-2.61) at 10%, 2.21 at 1%; finish -8.6; 68 teams, 16 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.71 (0.39-1.14) at 10%, 0.41 at 1%; finish +2.1; 14008 teams, 21 slates | 0.90 (0.00-2.16) at 10%, 0.00 at 1%; finish -6.3; 63 teams, 17 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.07 (0.48-1.91) at 10%, 0.80 at 1%; finish -1.0; 10306 teams, 20 slates | 0.41 (0.00-0.82) at 10%, 0.00 at 1%; finish -8.6; 47 teams, 14 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 1.00 (0.77-1.22) at 10%, 0.82 at 1%; finish -0.2; 9661 teams, 20 slates | 1.54 (0.73-2.33) at 10%, 0.00 at 1%; finish -5.9; 53 teams, 16 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 1.08 (0.54-1.55) at 10%, 1.73 at 1%; finish +0.7; 8140 teams, 21 slates | 2.05 (0.92-3.10) at 10%, 0.00 at 1%; finish -10.4; 34 teams, 11 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.01 (0.50-1.73) at 10%, 0.78 at 1%; finish +0.7; 5721 teams, 20 slates | 3.24 (1.70-4.49) at 10%, 0.00 at 1%; finish -10.8; 38 teams, 8 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.58 (0.42-0.76) at 10%, 0.19 at 1%; finish +0.2; 5277 teams, 21 slates | 0.41 (0.00-1.92) at 10%, 0.00 at 1%; finish +6.7; 29 teams, 6 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.64 (0.39-0.95) at 10%, 0.32 at 1%; finish +1.9; 3957 teams, 21 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 1.28 (0.72-1.69) at 10%, 1.64 at 1%; finish -3.0; 2491 teams, 21 slates | 0.85 (0.00-1.97) at 10%, 0.00 at 1%; finish -2.0; 13 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 0.96 (0.63-1.29) at 10%, 0.90 at 1%; finish +0.3; 2235 teams, 21 slates | 1.06 (0.00-3.52) at 10%, 0.00 at 1%; finish -0.4; 14 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 0.72 (0.36-1.26) at 10%, 0.49 at 1%; finish +3.8; 2183 teams, 20 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.16 (0.48-1.82) at 10%, 0.87 at 1%; finish -6.4; 1585 teams, 21 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 1.10 (0.71-1.62) at 10%, 1.45 at 1%; finish -2.4; 1404 teams, 20 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.44 (0.29-0.64) at 10%, 0.31 at 1%; finish +10.3; 1353 teams, 21 slates | none |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.37 (0.26-0.51) at 10%, 0.00 at 1%; finish +4.6; 1305 teams, 21 slates | none |
| 2/3 | a. reach vs trust | 1.03 (0.89-1.18) at 10%, 1.16 at 1%; finish +0.9; 30662 teams, 25 slates | 1.71 (1.16-2.23) at 10%, 1.81 at 1%; finish -8.2; 130 teams, 22 slates |
| 2/3 | fallers vs trust | 1.17 (1.00-1.40) at 10%, 1.25 at 1%; finish -3.6; 22381 teams, 25 slates | 1.75 (1.24-2.30) at 10%, 1.50 at 1%; finish -7.5; 112 teams, 22 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.66 (1.39-1.98) at 10%, 2.14 at 1%; finish -7.6; 6920 teams, 23 slates | 1.95 (1.13-2.68) at 10%, 3.73 at 1%; finish -10.8; 71 teams, 15 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.16 (0.80-1.50) at 10%, 1.27 at 1%; finish +0.9; 3572 teams, 20 slates | 0.25 (0.00-0.44) at 10%, 0.00 at 1%; finish -3.1; 38 teams, 11 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.77 (0.48-1.04) at 10%, 0.60 at 1%; finish +1.9; 5619 teams, 20 slates | 1.01 (0.00-1.83) at 10%, 0.00 at 1%; finish -7.5; 26 teams, 12 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 1.36 (1.00-1.71) at 10%, 1.21 at 1%; finish +0.1; 4228 teams, 21 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +11.6; 16 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 0.70 (0.32-1.15) at 10%, 0.47 at 1%; finish +10.3; 4094 teams, 20 slates | 0.98 (0.00-1.84) at 10%, 0.00 at 1%; finish +9.4; 25 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 1.39 (0.97-1.86) at 10%, 1.55 at 1%; finish -6.7; 3935 teams, 21 slates | 0.64 (0.00-1.84) at 10%, 0.00 at 1%; finish -2.6; 20 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 1.31 (0.97-1.68) at 10%, 1.38 at 1%; finish -9.8; 3155 teams, 21 slates | 0.68 (0.00-1.47) at 10%, 2.82 at 1%; finish -1.5; 20 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.01 (0.58-1.46) at 10%, 1.31 at 1%; finish +7.4; 3036 teams, 20 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +4.8; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 1.00 (0.68-1.35) at 10%, 0.58 at 1%; finish -2.2; 2937 teams, 21 slates | 2.49 (0.00-6.44) at 10%, 0.00 at 1%; finish -21.3; 15 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 1.00 (0.66-1.43) at 10%, 0.99 at 1%; finish -6.4; 2896 teams, 21 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +3.0; 7 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.37 (0.92-1.92) at 10%, 1.48 at 1%; finish -5.5; 2800 teams, 21 slates | 1.68 (0.61-3.01) at 10%, 3.96 at 1%; finish -2.9; 21 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.01 (0.56-1.59) at 10%, 0.84 at 1%; finish +3.2; 2620 teams, 20 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -4.2; 13 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.51 (0.30-0.74) at 10%, 0.48 at 1%; finish +5.3; 2504 teams, 21 slates | 0.56 (0.00-1.69) at 10%, 0.00 at 1%; finish +9.6; 15 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.87 (0.59-1.20) at 10%, 0.59 at 1%; finish -0.7; 2466 teams, 21 slates | 0.71 (0.00-2.62) at 10%, 0.00 at 1%; finish +13.5; 9 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 13 | 0.83 (0.59-1.06) at 10%, 0.67 at 1%; finish -1.2; 2306 teams, 21 slates | 1.79 (0.00-3.82) at 10%, 0.00 at 1%; finish -4.8; 12 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 0.93 (0.54-1.34) at 10%, 0.68 at 1%; finish +3.4; 2281 teams, 21 slates | 3.34 (2.27-3.74) at 10%, 0.00 at 1%; finish -18.1; 15 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.86 (0.59-1.24) at 10%, 0.46 at 1%; finish -3.2; 2265 teams, 21 slates | 2.32 (0.65-4.54) at 10%, 0.00 at 1%; finish -15.4; 11 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 0.77 (0.44-1.18) at 10%, 0.61 at 1%; finish +4.5; 2169 teams, 20 slates | 1.06 (0.00-1.69) at 10%, 0.00 at 1%; finish +4.5; 10 teams, 5 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 177 | 96% | 96% | -0 |
| AM | T1-T2 | Q TRAP | 26 | 81% | 96% | -15 |
| AM | T1-T2 | VALUE | 8 | 84% | 97% | -13 |
| AM | T3-T4 | PRICEY | 57 | 94% | 96% | -2 |
| AM | T3-T4 | Q TRAP | 2 | 98% | 97% | +1 |
| AM | T3-T4 | VALUE | 122 | 89% | 96% | -7 |
| AM | T5 | PRICEY | 13 | 96% | 59% | +37 |
| AM | T5 | Q FAIR | 279 | 10% | 19% | -9 |
| AM | T5 | VALUE | 413 | 48% | 25% | +23 |
| PM | T1-T2 | PRICEY | 185 | 96% | 98% | -2 |
| PM | T1-T2 | Q TRAP | 25 | 74% | 98% | -24 |
| PM | T1-T2 | VALUE | 13 | 96% | 97% | -1 |
| PM | T3-T4 | PRICEY | 95 | 99% | 99% | +0 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 6 | 70% | 99% | -29 |
| PM | T3-T4 | VALUE | 201 | 96% | 99% | -3 |
| PM | T5 | PRICEY | 20 | 90% | 39% | +52 |
| PM | T5 | Q FAIR | 155 | 8% | 22% | -14 |
| PM | T5 | VALUE | 448 | 68% | 28% | +40 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 53 (of all T5 breakers: PRICEY 14, VALUE 7, unflagged 56).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.19 (1.08-1.32) at 10%, 1.29 at 1%; finish -1.8; 165961 teams, 24 slates | 1.57 (1.35-1.82) at 10%, 1.27 at 1%; finish -8.0; 820 teams, 24 slates |
| Same-position teammates | 0.83 (0.74-0.93) at 10%, 0.88 at 1%; finish +3.4; 96685 teams, 25 slates | 1.26 (1.01-1.59) at 10%, 1.77 at 1%; finish -4.1; 406 teams, 24 slates |
| Same-position teammates, spread 5+ | 0.89 (0.81-0.98) at 10%, 0.76 at 1%; finish +0.7; 42215 teams, 22 slates | 1.35 (0.92-1.87) at 10%, 1.79 at 1%; finish -9.8; 205 teams, 19 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.71 | 1.65 | 1.10 | 0.83 | 0.72 | 1.17 | 0.96 | 0.01 | 0.09 | 0.01 | 2.87 |
| Field | 0.59 | 1.64 | 1.10 | 0.90 | 0.64 | 1.02 | 1.06 | 0.02 | 0.10 | 0.01 | 1.06 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.77 (0.67-0.86) at 10%, 0.74 at 1%; finish +5.6; 76360 teams, 24 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

719 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 288786 | 0.60 | 1.65 | 1.12 | 0.92 | 0.62 | 1.09 | 1.01 | 0.24 | 93% |
| Me | 1928 | 0.62 | 1.70 | 1.32 | 1.07 | 0.61 | 1.64 | 0.61 | 0.33 | 91% |
| Everyone | 440438 | 0.59 | 1.64 | 1.10 | 0.90 | 0.64 | 1.02 | 1.06 | 0.23 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.52 (0.34-0.75) at 10%, 0.29 at 1%; finish +11.5; 9571 teams, 8 slates |
| T1-T2 | AM | 0.65 (0.41-0.89) at 10%, 0.41 at 1%; finish +6.7; 5306 teams, 7 slates |
| T1-T2 | PM | 0.38 (0.21-0.55) at 10%, 0.17 at 1%; finish +17.5; 4265 teams, 4 slates |
| T3-T5 | both | 0.90 (0.79-1.03) at 10%, 1.02 at 1%; finish +2.0; 25307 teams, 17 slates |
| T3-T5 | AM | 0.85 (0.73-0.97) at 10%, 0.98 at 1%; finish +2.7; 12986 teams, 15 slates |
| T3-T5 | PM | 0.96 (0.78-1.17) at 10%, 1.06 at 1%; finish +1.1; 12321 teams, 12 slates |
| not credited | both | 0.77 (0.67-0.88) at 10%, 0.73 at 1%; finish +6.1; 33495 teams, 24 slates |
| not credited | AM | 0.81 (0.68-0.97) at 10%, 0.74 at 1%; finish +4.6; 14264 teams, 19 slates |
| not credited | PM | 0.74 (0.63-0.86) at 10%, 0.72 at 1%; finish +7.2; 19231 teams, 24 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 18 show a lean or rule and 8 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | RULE for | RULE for | 1.44 (1.19-1.76) | keep: points and money agree |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | RULE for | 1.37 (1.19-1.57) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | RULE for | RULE for | 1.29 (1.17-1.41) | candidate: hand to the rankings side with its points cost |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 0.97 (0.76-1.30) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 1.11 (0.93-1.30) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | no lean | 1.07 (0.81-1.37) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 0.95 (0.82-1.10) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | LEAN against | LEAN against | 0.88 (0.80-0.99) | watch: money leans against |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | LEAN against | LEAN against | 0.89 (0.41-1.01) | watch: money leans against |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 1.02 (0.84-1.21) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 1.08 (0.92-1.31) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean (deciles: LEAN for) | no lean | 1.14 (0.92-1.44) | not enough on either side yet |
| pm-t5-beneficiary | adopted | LEAN (listed) | no lean | no lean | 0.98 (0.87-1.12) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | no lean | no lean | 0.98 (0.87-1.09) | drop on points unless money clears its bar |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | LEAN for | LEAN for | 1.59 (1.19-2.15) | watch: money leans for |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.87 (0.68-1.11) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.87 (0.41-1.52) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | LEAN for | no lean | 1.07 (0.98-1.17) | keep on points; money not settled |
| one-tier-cap | adopted | LEAN (both windows) | LEAN against | no lean | 0.92 (0.79-1.04) | keep on points; money not settled |
| pm-middle-takes | candidate | LEAN (single window) | LEAN against | no lean | 0.90 (0.79-1.04) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | RULE for | RULE for | 1.43 (1.14-1.81) | keep: points and money agree |
| am-t5-other-reads | candidate | LEAN against (single window) | no lean | no lean | 1.24 (0.82-1.66) | drop on points unless money clears its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

Verdicts that change on ten price groups: pricey-flags T3 (LEAN for on five, RULE for on ten); beneficiary-round6:played (no lean on five, LEAN for on ten).

