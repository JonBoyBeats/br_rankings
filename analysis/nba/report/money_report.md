# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-23. Slates 2026-10-20 to 2026-11-22: 33 nights, 114 contests, 545452 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

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
| 2026-11-17 | 6 | 5 | 20838 | 0 | 5368 | 3522 | 100% | 100% | 99 |
| 2026-11-18 | 6 | 5 | 19818 | 0 | 9359 | 5396 | 100% | 100% | 100 |
| 2026-11-19 | 6 | 5 | 18192 | 0 | 6372 | 3688 | 99% | 100% | 40 |
| 2026-11-20 | 6 | 5 | 18132 | 0 | 973 | 410 | 100% | 100% | 50 |
| 2026-11-21 | 6 | 5 | 15900 | 0 | 8171 | 3332 | 98% | 100% | 0 |
| 2026-11-22 | 6 | 2 | 10536 | 0 | 2342 | 1171 | 100% | 100% | 20 |

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 21 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_fri_main, nba_fri_main, nba_mon_main, nba_mon_main, nba_mon_main, nba_sat_main, nba_sat_main, nba_sat_main, nba_sun_main, nba_sun_main, nba_sun_main, nba_thu_main, nba_thu_main, nba_thu_main, nba_tue_main, nba_tue_main, nba_wed_main, nba_wed_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
  - 2026-11-13: 428 swapped-in picks, 0 credited
  - 2026-11-14: 14048 swapped-in picks, 2379 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 517946 of 545452 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

**Ten random teams**

| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |
|---|---|---|---|---|---|---|---|
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-11 | Hump Day Hoops | 6 | AM | 2 | 213.8 | 216.5 | 4.3, 12.1, 15.1, 20.4, 29.1, 32.5 |
| 2026-11-12 | Thursday Night Hoops | 6 | PM | 2 | 216.3 | 279.2 | 2.1, 13.5, 18.6, 21.3, 26.3, 32.2 |
| 2026-11-13 | Fast Break Friday | 6 | PM | 5 | 227.0 | 231.6 | 1.1, 11.6, 13.5, 19.8, 23.8, 32.8 |
| 2026-11-15 | Sunday Shootaround | 6 | PM | 5 | 226.2 | 229.9 | 4.2, 10.3, 12.2, 21.2, 23.2, 25.9 |
| 2026-11-15 | Sunday Shootaround | 6 | PM | 4 | 221.6 | 148.1 | 2.6, 10.6, 14.5, 21.1, 25.3, 33.4 |
| 2026-11-17 | Tuesday Tip-Off | 6 | PM | 3 | 218.6 | 178.5 | 1.5, 12.9, 13.4, 22.7, 25.1, 35.4 |
| 2026-11-18 | Hump Day Hoops | 6 | PM | 3 | 215.2 | 275.9 | 4.2, 8.1, 15.3, 17.8, 31.3, 35.7 |
| 2026-11-21 | Saturday Slam | 6 | PM | 2 | 211.8 | 213.9 | 4.3, 12.1, 16.5, 18.6, 26.8, 33.7 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.2 | 18 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.1 | 18 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | +0.0 | 20 |
| Contest (its mean against its night's) | The Layup Line | -0.3 | 23 |
| Contest (its mean against its night's) | flagships | +0.0 | 31 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | -0.2 | 103 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +5.6 | 103516 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.9 | 103588 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.1 | 103603 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -2.2 | 103186 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.2 | 104053 |
| Swap on the team (inside contest) | no | +1.2 | 411432 |
| Swap on the team (inside contest) | yes | -4.7 | 106514 |
| Window (inside contest) | AM | -0.6 | 150096 |
| Window (inside contest) | PM | +0.3 | 365600 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hump Day Hoops | 6 | 5 | 410 | 0.73 | 1.07 | 1.20 | 1.04 | 51.5 | 1.41 (156) | 1.06 (254) | $2050 | $1027 | -50% |
| Fast Break Friday | 6 | 5 | 402 | 0.50 | 1.29 | 1.39 | 1.29 | 41.3 | 1.36 (88) | 1.40 (314) | $2010 | $1614 | -20% |
| Monday Night Hoops | 6 | 4 | 330 | 0.00 | 1.03 | 1.03 | 1.14 | 45.8 | 1.14 (79) | 1.00 (251) | $1650 | $1030 | -38% |
| Tuesday Tip-Off | 6 | 3 | 310 | 0.97 | 1.03 | 1.19 | 1.24 | 45.0 | 1.00 (110) | 1.30 (200) | $1550 | $1745 | +13% |
| Buzzer Beater | 6 | 10 | 169 | 0.59 | 1.54 | 1.42 | 1.24 | 43.0 | 1.79 (39) | 1.31 (130) | $507 | $433 | -15% |
| Sunday Shootaround | 6 | 3 | 140 | 0.71 | 1.14 | 1.14 | 1.25 | 42.8 | 3.00 (30) | 0.64 (110) | $700 | $500 | -29% |
| Saturday Slam | 6 | 4 | 130 | 3.85 | 2.15 | 1.46 | 1.19 | 47.4 | 1.43 (28) | 1.50 (100) | $650 | $6579 | +912% |
| Thursday Night Hoops | 6 | 2 | 100 | 1.00 | 1.20 | 1.20 | 1.20 | 42.2 | 1.78 (45) | 0.73 (55) | $500 | $391 | -22% |
| The Layup Line | 6 | 4 | 24 | 0.00 | 1.67 | 1.25 | 1.25 | 49.8 | 2.00 (5) | 1.05 (19) | $120 | $50 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 1.03 (39) | 1.77 (141) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 26 | 2015 | 0.79 | 1.23 | 1.24 (1.11-1.37) | 1.19 | 45.5 | 1.43 (580) | 1.17 (1433) | $9737 | $13369 | +37% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.82 (49) | 1.71 (175) | $1120 | $847 | -24% |
| **all** | - | 31 | 2239 | 0.80 | 1.25 | 1.27 (1.15-1.42) | 1.21 | 45.2 | 1.38 (629) | 1.23 (1608) | $10857 | $14216 | +31% |

Dollars: $10857 in fees, $14216 won, +31% ROI over 31 nights (80% range -32% to +113%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -26%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

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
| 2026-11-17 | 99 | Ayo Dosunmu 39% | Darius Garland + Ayo Dosunmu 19% | 6 (Karl-Anthony Towns + Darius Garland + Jaden McDaniels) | 0.6% | 11 of 80 |
| 2026-11-18 | 100 | Domantas Sabonis 44% | Domantas Sabonis + Yaxel Lendeborg 22% | 8 (Luka Doncic + Donovan Mitchell + Yaxel Lendeborg) | 0.6% | 5 of 80 |
| 2026-11-19 | 40 | Jonathan Kuminga 45% | Darius Garland + Victor Wembanyama 20% | 4 (Tyler Herro + Darius Garland + Victor Wembanyama) | 0.8% | 4 of 20 |
| 2026-11-20 | 50 | Walker Kessler 44% | James Harden + Devin Booker 20% | 3 (Donovan Mitchell + Walker Kessler + Shai Gilgeous-Alexander) | 0.9% | 6 of 30 |
| 2026-11-22 | 20 | Ace Bailey 60% | Ace Bailey + Andrew Nembhard 35% | 2 (Keyonte George + Jayson Tatum + Trae Young) | 1.0% | 9 of 20 |

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.26 (1.14-1.40) at 10%, 0.75 at 1%; finish -5.1; 2183 teams, 29 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.05 (0.95-1.14) at 10%, 1.12 at 1%; finish +0.9; 164338 teams, 30 slates | 1.01 (0.90-1.14) at 10%, 1.20 at 1%; finish +0.6; 104061 teams, 25 slates | 1.11 (0.96-1.27) at 10%, 0.97 at 1%; finish +1.4; 60277 teams, 5 slates | 1.51 (1.12-1.91) at 10%, 1.03 at 1%; finish -6.3; 1201 teams, 29 slates | no lean | no lean |
|   AM only | 1.05 (0.76-1.33) at 10%, 0.94 at 1%; finish +0.3; 35412 teams, 22 slates | 0.79 (0.61-1.05) at 10%, 0.43 at 1%; finish +3.2; 19225 teams, 19 slates | 1.42 (0.90-1.84) at 10%, 1.54 at 1%; finish -3.1; 16187 teams, 3 slates | 0.76 (0.26-1.68) at 10%, 0.00 at 1%; finish -2.5; 98 teams, 12 slates | no lean | no lean |
|   PM only | 1.04 (0.95-1.13) at 10%, 1.15 at 1%; finish +1.1; 128200 teams, 30 slates | 1.06 (0.94-1.20) at 10%, 1.37 at 1%; finish +0.1; 84114 teams, 25 slates | 0.99 (0.91-1.07) at 10%, 0.68 at 1%; finish +2.9; 44086 teams, 5 slates | 1.65 (1.21-2.07) at 10%, 1.17 at 1%; finish -6.9; 1092 teams, 27 slates | no lean | no lean |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.91 (1.50-2.51) at 10%, 3.23 at 1%; finish -8.8; 27500 teams, 8 slates | 1.59 (1.19-2.15) at 10%, 2.28 at 1%; finish -6.3; 16039 teams, 6 slates | 2.84 at 10%, 9.00 at 1%; finish -12.3; 11461 teams, 2 slates | 4.32 (2.81-5.56) at 10%, 2.26 at 1%; finish -18.2; 126 teams, 8 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.36 (1.21-1.51) at 10%, 1.51 at 1%; finish -3.8; 839556 teams, 30 slates | 1.37 (1.18-1.57) at 10%, 1.51 at 1%; finish -4.5; 612114 teams, 25 slates | 1.33 (1.14-1.51) at 10%, 1.51 at 1%; finish -1.9; 227442 teams, 5 slates | 1.54 (1.29-1.82) at 10%, 0.57 at 1%; finish -7.4; 5947 teams, 28 slates | RULE for | RULE for |
|   T3 | 1.49 (1.12-1.97) at 10%, 1.71 at 1%; finish -5.1; 251688 teams, 23 slates | 1.52 (1.11-2.05) at 10%, 1.78 at 1%; finish -6.6; 215459 teams, 19 slates | 1.27 (0.66-2.29) at 10%, 1.16 at 1%; finish +3.8; 36229 teams, 4 slates | 1.32 (0.96-1.82) at 10%, 0.00 at 1%; finish -10.0; 1839 teams, 22 slates | RULE for | RULE for |
|   T4 | 1.41 (1.24-1.59) at 10%, 1.65 at 1%; finish -4.3; 281168 teams, 26 slates | 1.39 (1.21-1.56) at 10%, 1.59 at 1%; finish -4.0; 230323 teams, 21 slates | 1.49 (0.97-2.20) at 10%, 1.96 at 1%; finish -5.4; 50845 teams, 5 slates | 1.73 (1.30-2.24) at 10%, 1.38 at 1%; finish -7.1; 1772 teams, 24 slates | RULE for | RULE for |
|   T5 | 1.19 (0.98-1.44) at 10%, 1.17 at 1%; finish -2.6; 306532 teams, 23 slates | 1.14 (0.90-1.43) at 10%, 1.04 at 1%; finish -2.6; 166205 teams, 18 slates | 1.26 (0.90-1.81) at 10%, 1.41 at 1%; finish -2.7; 140327 teams, 5 slates | 1.53 (1.30-1.75) at 10%, 0.43 at 1%; finish -6.0; 2336 teams, 22 slates | LEAN for | LEAN for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.26 (1.17-1.36) at 10%, 1.40 at 1%; finish -2.5; 1049805 teams, 30 slates | 1.32 (1.20-1.45) at 10%, 1.51 at 1%; finish -3.0; 815507 teams, 25 slates | 1.11 (1.02-1.21) at 10%, 1.09 at 1%; finish -0.8; 234298 teams, 5 slates | 1.71 (1.44-1.98) at 10%, 1.35 at 1%; finish -8.1; 5407 teams, 29 slates | RULE for | RULE for |
|   T1 | 1.71 (1.30-2.22) at 10%, 2.43 at 1%; finish -4.2; 165438 teams, 18 slates | 1.58 (1.25-2.02) at 10%, 2.38 at 1%; finish -3.8; 140030 teams, 15 slates | 2.47 (0.93-8.55) at 10%, 2.69 at 1%; finish -6.8; 25408 teams, 3 slates | 1.90 (1.11-2.76) at 10%, 2.42 at 1%; finish -5.6; 728 teams, 16 slates | RULE for | RULE for |
|   T2 | 1.23 (1.08-1.40) at 10%, 1.32 at 1%; finish -2.6; 473843 teams, 28 slates | 1.26 (1.10-1.45) at 10%, 1.34 at 1%; finish -2.8; 401867 teams, 23 slates | 1.08 (0.74-1.45) at 10%, 1.21 at 1%; finish -1.1; 71976 teams, 5 slates | 1.57 (1.29-1.89) at 10%, 1.12 at 1%; finish -8.2; 2585 teams, 27 slates | RULE for | RULE for |
|   T3 | 1.41 (1.18-1.72) at 10%, 1.59 at 1%; finish -5.4; 294066 teams, 25 slates | 1.45 (1.17-1.83) at 10%, 1.64 at 1%; finish -5.2; 236346 teams, 20 slates | 1.27 (0.88-1.58) at 10%, 1.36 at 1%; finish -6.0; 57720 teams, 5 slates | 2.17 (1.79-2.62) at 10%, 1.59 at 1%; finish -11.6; 1722 teams, 24 slates | RULE for | RULE for |
|   T4 | 0.92 (0.79-1.10) at 10%, 0.79 at 1%; finish +2.1; 91801 teams, 9 slates | 1.97 (0.66-3.92) at 10%, 2.48 at 1%; finish -11.5; 12667 teams, 4 slates | 0.83 (0.74-0.90) at 10%, 0.67 at 1%; finish +4.3; 79134 teams, 5 slates | 0.94 (0.38-1.44) at 10%, 0.00 at 1%; finish +1.4; 296 teams, 8 slates | no lean | no lean |
|   T5 | 0.78 (0.65-1.04) at 10%, 0.70 at 1%; finish +6.5; 24456 teams, 6 slates | 0.78 (0.65-1.04) at 10%, 0.70 at 1%; finish +6.5; 24456 teams, 6 slates | none | 1.11 (0.69-1.45) at 10%, 1.22 at 1%; finish -5.8; 76 teams, 5 slates | LEAN against | LEAN against |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.08 (0.89-1.32) at 10%, 1.12 at 1%; finish -1.4; 90832 teams, 24 slates | 1.05 (0.81-1.40) at 10%, 0.95 at 1%; finish -1.5; 61839 teams, 19 slates | 1.17 (0.99-1.38) at 10%, 1.63 at 1%; finish -1.1; 28993 teams, 5 slates | 0.77 (0.57-0.99) at 10%, 0.00 at 1%; finish -2.4; 351 teams, 22 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.39 (1.18-1.64) at 10%, 1.60 at 1%; finish -4.6; 276652 teams, 24 slates | 1.44 (1.18-1.76) at 10%, 1.68 at 1%; finish -5.6; 231881 teams, 21 slates | 1.12 (0.92-1.23) at 10%, 1.27 at 1%; finish +0.7; 44771 teams, 3 slates | 1.58 (1.26-1.98) at 10%, 0.71 at 1%; finish -6.2; 1490 teams, 21 slates | RULE for | RULE for |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 0.85 (0.70-1.03) at 10%, 0.90 at 1%; finish +2.9; 210547 teams, 29 slates | 0.86 (0.70-1.06) at 10%, 0.96 at 1%; finish +2.8; 181251 teams, 24 slates | 0.77 (0.55-1.06) at 10%, 0.58 at 1%; finish +3.7; 29296 teams, 5 slates | 1.12 (0.79-1.49) at 10%, 1.58 at 1%; finish -2.2; 1053 teams, 28 slates | LEAN against | LEAN against |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 1.07 (0.61-1.79) at 10%, 1.30 at 1%; finish +0.1; 28849 teams, 8 slates | 0.87 (0.41-1.52) at 10%, 1.02 at 1%; finish +4.8; 20544 teams, 6 slates | 2.50 at 10%, 4.82 at 1%; finish -11.7; 8305 teams, 2 slates | 2.78 (0.85-7.33) at 10%, 3.30 at 1%; finish -13.6; 80 teams, 7 slates | no lean | no lean |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 1.10 (1.01-1.20) at 10%, 1.03 at 1%; finish -3.1; 215398 teams, 30 slates | 1.11 (1.00-1.22) at 10%, 0.94 at 1%; finish -2.7; 150537 teams, 25 slates | 1.08 (0.92-1.30) at 10%, 1.29 at 1%; finish -4.0; 64861 teams, 5 slates | 1.28 (0.94-1.71) at 10%, 0.57 at 1%; finish -7.0; 1037 teams, 27 slates | LEAN for | LEAN for |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.79 (0.66-0.95) at 10%, 0.71 at 1%; finish +3.2; 378288 teams, 28 slates | 0.91 (0.79-1.05) at 10%, 0.90 at 1%; finish +1.3; 291266 teams, 23 slates | 0.50 (0.33-0.92) at 10%, 0.35 at 1%; finish +9.6; 87022 teams, 5 slates | 1.19 (0.97-1.50) at 10%, 0.75 at 1%; finish -2.6; 1514 teams, 26 slates | RULE against | RULE against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.29 (1.00-1.62) at 10%, 1.55 at 1%; finish -2.9; 26952 teams, 21 slates | 1.07 (0.82-1.38) at 10%, 1.10 at 1%; finish -0.5; 21572 teams, 18 slates | 2.53 (1.37-4.63) at 10%, 5.06 at 1%; finish -12.8; 5380 teams, 3 slates | 1.13 (0.76-1.50) at 10%, 1.08 at 1%; finish +0.4; 184 teams, 14 slates | LEAN for | LEAN for |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.34 (1.08-1.67) at 10%, 1.47 at 1%; finish -4.5; 47796 teams, 25 slates | 1.06 (0.91-1.23) at 10%, 1.06 at 1%; finish -1.4; 36965 teams, 21 slates | 2.86 (1.80-4.06) at 10%, 4.38 at 1%; finish -14.8; 10831 teams, 4 slates | 1.37 (0.90-2.01) at 10%, 0.49 at 1%; finish -9.5; 230 teams, 20 slates | RULE for | RULE for |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 0.91 (0.76-1.09) at 10%, 0.85 at 1%; finish +2.4; 523827 teams, 24 slates | 0.99 (0.85-1.14) at 10%, 1.00 at 1%; finish +1.5; 435916 teams, 20 slates | 0.60 (0.31-1.45) at 10%, 0.40 at 1%; finish +6.9; 87911 teams, 4 slates | 1.23 (0.97-1.56) at 10%, 0.48 at 1%; finish -3.7; 1673 teams, 23 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 1.17 (0.92-1.46) at 10%, 1.16 at 1%; finish -2.9; 334931 teams, 24 slates | 0.89 (0.81-0.98) at 10%, 0.71 at 1%; finish +0.3; 246663 teams, 20 slates | 2.12 (1.19-3.19) at 10%, 2.86 at 1%; finish -11.9; 88268 teams, 4 slates | 1.09 (0.72-1.54) at 10%, 0.84 at 1%; finish -4.2; 1530 teams, 20 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | 2.29 at 10%, 3.78 at 1%; finish -18.9; 2071 teams, 1 slates | 2.29 at 10%, 3.78 at 1%; finish -18.9; 2071 teams, 1 slates | none | 1.32 at 10%, 0.00 at 1%; finish -20.4; 33 teams, 1 slates | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 1.31 (0.53-1.79) at 10%, 1.67 at 1%; finish -2.9; 5113 teams, 11 slates | 0.89 (0.41-1.01) at 10%, 0.65 at 1%; finish +1.5; 2041 teams, 9 slates | 1.62 at 10%, 2.56 at 1%; finish -5.8; 3072 teams, 2 slates | 1.10 (0.50-1.51) at 10%, 0.00 at 1%; finish -4.2; 36 teams, 4 slates | no lean | no lean |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 1.07 (0.90-1.24) at 10%, 1.06 at 1%; finish -0.2; 41376 teams, 16 slates | 0.99 (0.82-1.16) at 10%, 0.98 at 1%; finish +0.8; 33770 teams, 13 slates | 1.51 (0.81-2.57) at 10%, 1.52 at 1%; finish -4.6; 7606 teams, 3 slates | 1.16 (0.78-1.52) at 10%, 0.00 at 1%; finish -0.8; 205 teams, 14 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 1.09 (0.92-1.29) at 10%, 0.98 at 1%; finish -1.5; 22906 teams, 21 slates | 1.05 (0.90-1.25) at 10%, 0.88 at 1%; finish -1.2; 21191 teams, 18 slates | 1.47 (0.57-3.57) at 10%, 2.36 at 1%; finish -4.9; 1715 teams, 3 slates | 2.02 (1.38-2.70) at 10%, 2.54 at 1%; finish -6.7; 76 teams, 13 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.03 (0.84-1.28) at 10%, 1.04 at 1%; finish +0.3; 18143 teams, 18 slates | 1.14 (0.92-1.44) at 10%, 1.22 at 1%; finish -0.7; 14844 teams, 15 slates | 0.54 (0.48-0.60) at 10%, 0.32 at 1%; finish +4.8; 3299 teams, 3 slates | 0.79 (0.34-1.44) at 10%, 0.00 at 1%; finish -3.0; 51 teams, 11 slates | no lean | no lean |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.02 (0.91-1.17) at 10%, 1.01 at 1%; finish -0.6; 56465 teams, 23 slates | 0.96 (0.87-1.09) at 10%, 1.00 at 1%; finish -0.9; 44390 teams, 19 slates | 1.26 (0.87-2.11) at 10%, 1.04 at 1%; finish +0.2; 12075 teams, 4 slates | 1.99 (1.37-2.63) at 10%, 1.37 at 1%; finish -10.4; 253 teams, 18 slates | no lean | no lean |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 0.82 (0.73-0.95) at 10%, 0.72 at 1%; finish +2.4; 273955 teams, 28 slates | 0.85 (0.73-1.00) at 10%, 0.78 at 1%; finish +2.4; 209912 teams, 23 slates | 0.73 (0.58-1.20) at 10%, 0.53 at 1%; finish +2.4; 64043 teams, 5 slates | 0.95 (0.75-1.23) at 10%, 0.26 at 1%; finish -2.5; 1763 teams, 26 slates | RULE against | RULE against |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 1.36 (1.12-1.70) at 10%, 1.41 at 1%; finish -4.8; 175813 teams, 25 slates | 1.43 (1.14-1.81) at 10%, 1.47 at 1%; finish -5.6; 155424 teams, 22 slates | 0.85 (0.49-1.42) at 10%, 0.83 at 1%; finish +2.0; 20389 teams, 3 slates | 1.47 (1.17-1.84) at 10%, 0.63 at 1%; finish -7.3; 1138 teams, 25 slates | LEAN for | LEAN for |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.23 (0.83-1.62) at 10%, 1.71 at 1%; finish -1.5; 31337 teams, 16 slates | 1.24 (0.82-1.66) at 10%, 1.74 at 1%; finish -2.0; 29686 teams, 14 slates | 0.98 at 10%, 1.19 at 1%; finish +8.2; 1651 teams, 2 slates | 0.96 (0.51-1.49) at 10%, 0.00 at 1%; finish +4.7; 87 teams, 12 slates | no lean | no lean |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| leverage-t2-t4 | RULE for | +7.6 | +7.5 (99%) | +0.1 (1%) | +0.6 | 1.82 (1.38-2.50) at 10%, 2.48 at 1%; finish -7.9; 27443 teams, 8 slates | RULE for |
| value-up-middle-t5 | RULE for | +3.6 | +2.7 (73%) | +1.0 (27%) | +0.7 | 1.31 (1.16-1.46) at 10%, 1.43 at 1%; finish -3.4; 839551 teams, 30 slates | RULE for |
| value-up-middle-t5 T3 | RULE for | +5.0 | +3.6 (72%) | +1.4 (28%) | +3.9 | 1.51 (1.13-2.00) at 10%, 1.72 at 1%; finish -5.3; 251705 teams, 23 slates | RULE for |
| value-up-middle-t5 T4 | RULE for | +4.3 | +3.7 (86%) | +0.6 (14%) | +3.4 | 1.38 (1.21-1.57) at 10%, 1.63 at 1%; finish -4.2; 281175 teams, 26 slates | RULE for |
| value-up-middle-t5 T5 | LEAN for | +2.1 | +0.6 (30%) | +1.5 (70%) | -1.2 | 1.15 (0.96-1.39) at 10%, 1.10 at 1%; finish -2.5; 306222 teams, 23 slates | LEAN for |
| pricey-flags | RULE for | +2.6 | +3.6 (135%) | -0.9 (-35%) | +4.4 | 1.27 (1.17-1.39) at 10%, 1.43 at 1%; finish -2.6; 1049865 teams, 30 slates | RULE for |
| pricey-flags T1 | RULE for | +3.3 | +5.9 (181%) | -2.7 (-81%) | +9.1 | 1.67 (1.21-2.28) at 10%, 2.34 at 1%; finish -4.3; 165461 teams, 18 slates | RULE for |
| pricey-flags T2 | RULE for | +2.6 | +2.9 (112%) | -0.3 (-12%) | +3.6 | 1.23 (1.08-1.42) at 10%, 1.32 at 1%; finish -2.9; 473837 teams, 28 slates | RULE for |
| pricey-flags T3 | RULE for | +5.5 | +6.1 (111%) | -0.6 (-11%) | +5.6 | 1.39 (1.17-1.69) at 10%, 1.59 at 1%; finish -5.2; 294076 teams, 25 slates | RULE for |
| pricey-flags T5 | LEAN against | -5.4 | +0.4 (-7%) | -5.8 (107%) | -7.7 | 0.89 (0.65-1.39) at 10%, 0.81 at 1%; finish +3.6; 24472 teams, 6 slates | no lean |
| am-t5-button-order | RULE for | +4.4 | +3.0 (68%) | +1.4 (32%) | +0.8 | 1.39 (1.18-1.66) at 10%, 1.62 at 1%; finish -4.7; 276623 teams, 24 slates | RULE for |
| pm-t2-adp-etr2 | LEAN against | -2.3 | -2.4 (103%) | +0.1 (-3%) | -1.9 | 0.86 (0.71-1.05) at 10%, 0.92 at 1%; finish +2.7; 210557 teams, 29 slates | LEAN against |
| pm-t5-adp-value | LEAN for | +2.3 | -0.1 (-3%) | +2.4 (103%) | +2.1 | 0.98 (0.86-1.14) at 10%, 0.84 at 1%; finish -2.1; 215429 teams, 30 slates | no lean |
| one-tier-cap | RULE against | -2.8 | -2.3 (84%) | -0.5 (16%) | -0.9 | 0.80 (0.67-0.97) at 10%, 0.73 at 1%; finish +2.8; 378301 teams, 28 slates | LEAN against |
| am-questionable-no-push | LEAN for | +2.6 | +1.8 (68%) | +0.8 (32%) | - (holding) | 1.13 (0.90-1.40) at 10%, 1.05 at 1%; finish +0.3; 26573 teams, 21 slates | no lean |
| pm-questionable-back-two | RULE for | +3.7 | +2.0 (55%) | +1.7 (45%) | - (holding) | 1.28 (1.05-1.56) at 10%, 1.39 at 1%; finish -4.1; 47787 teams, 25 slates | LEAN for |
| pm-middle-takes | RULE against | -2.3 | -1.9 (82%) | -0.4 (18%) | -1.2 | 0.84 (0.74-0.97) at 10%, 0.75 at 1%; finish +2.1; 273955 teams, 28 slates | LEAN against |
| pm-t2-other-reads | LEAN for | +4.3 | +3.8 (89%) | +0.5 (11%) | +3.4 | 1.33 (1.10-1.67) at 10%, 1.32 at 1%; finish -4.4; 175815 teams, 25 slates | LEAN for |
| turn 1/2: a. reach vs trust | LEAN against | -1.8 | -0.2 (9%) | -1.6 (91%) | -1.7 | 0.77 (0.65-0.94) at 10%, 0.63 at 1%; finish +3.3; 45439 teams, 31 slates | LEAN against |
| turn 1/2: fallers vs trust | RULE for | +3.0 | +0.1 (2%) | +2.9 (98%) | +3.3 | 1.44 (1.13-1.86) at 10%, 1.81 at 1%; finish -3.2; 66903 teams, 31 slates | RULE for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +1.8 | +2.7 (146%) | -0.8 (-46%) | +1.5 | 1.22 (0.79-1.87) at 10%, 1.05 at 1%; finish -1.0; 6635 teams, 23 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | -0.0 | +2.8 | -2.8 | +0.3 | 0.99 (0.85-1.15) at 10%, 1.22 at 1%; finish +1.1; 38614 teams, 31 slates | no lean |
| turn 2/3: fallers vs trust | LEAN for | +2.3 | +1.4 (60%) | +0.9 (40%) | +2.8 | 1.16 (1.03-1.31) at 10%, 1.34 at 1%; finish -3.4; 27573 teams, 31 slates | LEAN for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +7.4 | +8.5 (115%) | -1.1 (-15%) | +5.9 | 1.57 (1.33-1.82) at 10%, 2.26 at 1%; finish -6.5; 8454 teams, 29 slates | LEAN for |
| stack: Opposing stars (their team's top 2 by projection, same game) | RULE for | +1.9 | +1.8 (94%) | +0.1 (6%) | - (holding) | 1.02 (0.92-1.13) at 10%, 1.11 at 1%; finish -0.0; 201781 teams, 30 slates | no lean |
| stack: Same-position teammates | RULE against | -3.0 | -6.9 (231%) | +3.9 (-131%) | - (holding) | 0.73 (0.66-0.82) at 10%, 0.77 at 1%; finish +4.0; 115496 teams, 31 slates | RULE against |
| stack: Same-position teammates, spread 5+ | LEAN against | -0.6 | -3.1 (507%) | +2.5 (-407%) | - (holding) | 0.86 (0.78-0.94) at 10%, 0.70 at 1%; finish +1.5; 54003 teams, 28 slates | RULE against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 18 | 264 | -1.4 | +1 | -202 |
| the swap board, near-ties least drafted first (leverage) | 18 | 264 | +1.1 | +4 | -73 |
| the swap board, near-ties most drafted first (spread) | 18 | 264 | -0.6 | +1 | -194 |

Leverage against spread: the leverage board's swaps would have made -3 top-10% finishes and $-121 against the spread board's (real minus each, differenced). Leverage put 68% of a night's replayed swaps on one player, spread 53%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.04 (0.91-1.19) at 10%, 1.02 at 1%; finish -0.4; 39332 teams, 23 slates | +0.3 | +0.7 | -0.4 | 1.00 (0.87-1.14) at 10%, 0.96 at 1%; finish +0.3; 39330 teams, 23 slates | no lean |
| rounds 1-2 | 4.04 (3.21-4.62) at 10%, 12.14 at 1%; finish -20.3; 1202 teams, 4 slates | +16.5 | +14.0 (84%) | +2.6 (16%) | 3.91 (3.00-4.66) at 10%, 11.70 at 1%; finish -20.1; 1201 teams, 4 slates | RULE for |
| rounds 3-4 | 1.02 (0.84-1.25) at 10%, 0.89 at 1%; finish +0.5; 9319 teams, 12 slates | -0.5 | +0.5 | -1.0 | 0.99 (0.81-1.22) at 10%, 0.82 at 1%; finish +0.7; 9315 teams, 12 slates | no lean |
| rounds 5-6 or undrafted | 0.97 (0.82-1.12) at 10%, 0.88 at 1%; finish +0.3; 29058 teams, 20 slates | -0.1 | +0.2 | -0.2 | 0.94 (0.80-1.09) at 10%, 0.85 at 1%; finish +0.8; 29058 teams, 20 slates | no lean |

## 3c. Splits for Monday: teammates and takes by source

Each with the price-split check (section 3b). Lift: top-10% against same-contest, same-price teams.

### Teammates, by the rounds paid for them

A: teams with that teammate pair; B: teams with no two teammates at all (so same- and different-position pairs face the same comparison).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pair | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| Same position, both rounds 1-3 | 1.04 (0.72-1.37) at 10%, 1.04 at 1%; finish -2.5; 13025 teams, 20 slates | +1.7 | -3.3 (-195%) | +5.0 (295%) | 1.03 (0.72-1.37) at 10%, 1.09 at 1%; finish -2.2; 13024 teams, 20 slates | no lean |
| Same position, one in rounds 1-3 and one in 4-6 | 0.88 (0.81-0.95) at 10%, 0.80 at 1%; finish +1.5; 61340 teams, 29 slates | -1.4 | -5.8 (408%) | +4.4 (-308%) | 0.73 (0.65-0.83) at 10%, 0.66 at 1%; finish +3.5; 61244 teams, 29 slates | RULE against |
| Same position, both rounds 4-6 | 1.07 (0.94-1.19) at 10%, 1.01 at 1%; finish -2.7; 25911 teams, 29 slates | +2.2 | -0.4 (-19%) | +2.6 (119%) | 1.05 (0.93-1.17) at 10%, 1.01 at 1%; finish -2.4; 25908 teams, 29 slates | no lean |
| Different-position teammates (any rounds) | 1.09 (1.02-1.15) at 10%, 1.09 at 1%; finish -1.4; 238708 teams, 29 slates | +1.3 | -1.3 (-107%) | +2.6 (207%) | 0.99 (0.89-1.11) at 10%, 0.96 at 1%; finish -0.5; 194221 teams, 29 slates | no lean |

### Your takes by source (takes_history.csv)

A: teams holding the player you put first; B: the button's first, in the take's window (field and mine). Field drafted%: the share of that window's pods that took each. Points: the takes file's average gain per take (yours).

| Source | Window | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pick | From the other picks | Lift matched on the other picks' price | Verdict that survives | Takes, points per take | Field drafted%: yours / the button's | Yours the more drafted |
|---|---|---|---|---|---|---|---|---|---|---|
| ETR | PM | 0.76 (0.64-1.01) at 10%, 0.64 at 1%; finish +4.0; 90026 teams, 13 slates | -3.6 | -3.2 (88%) | -0.4 (12%) | 0.78 (0.65-1.05) at 10%, 0.66 at 1%; finish +3.6; 90017 teams, 13 slates | LEAN against | 71, -2.8 | 64% / 65% | 42% |
| ETR | both | 0.76 (0.64-1.01) at 10%, 0.64 at 1%; finish +4.0; 90026 teams, 13 slates | -3.6 | -3.2 (88%) | -0.4 (12%) | 0.78 (0.65-1.05) at 10%, 0.66 at 1%; finish +3.6; 90017 teams, 13 slates | LEAN against | 71, -2.8 | 64% / 65% | 42% |
| Bagel | PM | 1.08 (0.87-1.42) at 10%, 1.18 at 1%; finish +0.3; 59643 teams, 11 slates | -0.4 | +0.6 | -1.0 | 1.10 (0.92-1.36) at 10%, 1.19 at 1%; finish +0.2; 59637 teams, 11 slates | no lean | 38, +1.6 | 81% / 81% | 58% |
| Bagel | both | 1.08 (0.87-1.42) at 10%, 1.18 at 1%; finish +0.3; 59643 teams, 11 slates | -0.4 | +0.6 | -1.0 | 1.10 (0.92-1.36) at 10%, 1.19 at 1%; finish +0.2; 59637 teams, 11 slates | no lean | 38, +1.6 | 81% / 81% | 58% |
| Bagel+ETR | PM | 1.07 (0.91-1.28) at 10%, 1.03 at 1%; finish -0.5; 158992 teams, 12 slates | +0.9 | +1.1 (119%) | -0.2 (-19%) | 1.09 (0.93-1.30) at 10%, 1.06 at 1%; finish -0.8; 158998 teams, 12 slates | no lean | 115, +2.4 | 70% / 70% | 47% |
| Bagel+ETR | both | 1.07 (0.91-1.28) at 10%, 1.03 at 1%; finish -0.5; 158992 teams, 12 slates | +0.9 | +1.1 (119%) | -0.2 (-19%) | 1.09 (0.93-1.30) at 10%, 1.06 at 1%; finish -0.8; 158998 teams, 12 slates | no lean | 115, +2.4 | 70% / 70% | 47% |
| NEWS | AM | 1.02 (0.90-1.17) at 10%, 1.06 at 1%; finish -0.5; 253219 teams, 24 slates | +0.4 | -0.6 | +1.0 | 1.01 (0.89-1.15) at 10%, 1.04 at 1%; finish -0.2; 253211 teams, 24 slates | no lean | 315, -0.5 | 80% / 77% | 51% |
| NEWS | PM | 0.95 (0.77-1.17) at 10%, 0.88 at 1%; finish -0.6; 182124 teams, 23 slates | -0.1 | -0.4 | +0.3 | 0.94 (0.76-1.15) at 10%, 0.87 at 1%; finish -0.5; 182110 teams, 23 slates | no lean | 140, -1.0 | 71% / 75% | 38% |
| NEWS | both | 1.00 (0.89-1.12) at 10%, 0.99 at 1%; finish -0.6; 435371 teams, 29 slates | +0.3 | -0.4 | +0.7 | 0.98 (0.88-1.10) at 10%, 0.98 at 1%; finish -0.4; 435363 teams, 29 slates | no lean | 455, -0.6 | 77% / 77% | 47% |
| OTHER | AM | 1.08 (0.92-1.29) at 10%, 1.07 at 1%; finish +0.4; 19370 teams, 3 slates | +0.2 | +0.5 | -0.3 | 1.09 (0.94-1.28) at 10%, 1.09 at 1%; finish +0.4; 19370 teams, 3 slates | LEAN for | 43, +3.2 | 49% / 49% | 49% |
| OTHER | PM | 0.71 (0.42-1.19) at 10%, 0.52 at 1%; finish +2.6; 39799 teams, 13 slates | -2.0 | -4.3 (213%) | +2.3 (-113%) | 0.69 (0.42-1.11) at 10%, 0.51 at 1%; finish +3.6; 39801 teams, 13 slates | LEAN against | 70, -1.8 | 60% / 65% | 34% |
| OTHER | both | 0.84 (0.59-1.14) at 10%, 0.71 at 1%; finish +1.9; 59169 teams, 14 slates | -1.3 | -2.7 (205%) | +1.4 (-105%) | 0.83 (0.57-1.12) at 10%, 0.70 at 1%; finish +2.5; 59171 teams, 14 slates | no lean | 113, +0.1 | 56% / 59% | 40% |
| all | AM | 1.03 (0.91-1.16) at 10%, 1.06 at 1%; finish -0.5; 272589 teams, 24 slates | +0.4 | -0.5 | +0.9 | 1.02 (0.90-1.15) at 10%, 1.05 at 1%; finish -0.2; 272581 teams, 24 slates | no lean | 358, -0.0 | 76% / 74% | 51% |
| all | PM | 0.95 (0.85-1.08) at 10%, 0.89 at 1%; finish +0.6; 530657 teams, 29 slates | -0.6 | -0.7 (112%) | +0.1 (-12%) | 0.95 (0.85-1.08) at 10%, 0.90 at 1%; finish +0.5; 530658 teams, 29 slates | no lean | 434, -0.3 | 69% / 71% | 42% |
| all | both | 0.98 (0.91-1.08) at 10%, 0.95 at 1%; finish +0.2; 803269 teams, 29 slates | -0.2 | -0.5 | +0.3 | 0.98 (0.90-1.07) at 10%, 0.95 at 1%; finish +0.2; 803269 teams, 29 slates | no lean | 792, -0.2 | 72% / 72% | 46% |

## 3d. Candidate: my AM teams against my PM teams (for the Monday section; not a proposal)

A = my AM teams, B = my PM teams, inside the same contest and price group. Raw: each window's top-10% rate over the field's 10%. Then what differs, per team.

| | Teams | Raw top-10% | VALUE picks | PRICEY picks | Tagged picks | Projected drafted% of picks | Field sharing 4+ of 6 | Teams with an exact duplicate | Price | Points over price | Swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AM | 629 | 1.38 | 1.72 | 0.67 | 0.31 | 93% | 0.95% | 17% | 220.1 | +3.9 | 0.47 |
| PM | 1554 | 1.24 | 1.50 | 0.67 | 0.17 | 90% | 1.11% | 20% | 217.9 | +6.4 | 0.12 |

Inside the same contest and price group, AM against PM: 1.22 (0.92-1.57) at 10%, 1.25 at 1%; finish +0.8; 617 teams, 22 slates (five price groups); 1.07 (0.82-1.38) at 10%, 1.71 at 1%; finish +1.8; 584 teams, 22 slates (ten).

## 3e. Candidates for 11-16 (asked 2026-11-09; not proposals)

### 1. Same-position teammates: source, examples, and starter/backup instead

Position: Underdog's own position on the slate (the record's `pos`), grouped G (PG, SG, G), F (SF, PF, F), C. Underdog scores everyone as flex, so position matters here only as a stand-in for sharing minutes and touches. Five early/late same-position pairs on 2026-11-22's rosters:

- Desmond Bane (SG, round 3) + Jalen Suggs (PG, round 5), ORL
- Trae Young (PG, round 3) + Kyshawn George (SG, round 4), WAS
- Josh Giddey (PG, round 3) + Tre Jones (PG, round 6), CHI
- Jamal Murray (PG, round 2) + Christian Braun (SG, round 5), DEN
- Anthony Black (PG, round 2) + Jalen Suggs (PG, round 5), ORL

Starter and direct backup instead of position: the starter averages 28+ minutes; his backup scores 4+ more points a game when the starter sits. Both from the morning file as it stood at that night's lock (the mirror's history: games through the night before, nothing later). The with/without splits start in the morning file around 10-29, so earlier nights have no pairs. Against teams with no two teammates:

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Same position, early + late (the approved card row) | 0.88 (0.81-0.95) at 10%, 0.80 at 1%; finish +1.5; 61340 teams, 29 slates | -1.4 | -5.8 (408%) | +4.4 (-308%) | - (holding) | 0.73 (0.65-0.83) at 10%, 0.66 at 1%; finish +3.5; 61244 teams, 29 slates | RULE against |
| Starter + his backup, any rounds | 0.91 (0.78-1.04) at 10%, 0.77 at 1%; finish +1.2; 45576 teams, 21 slates | -1.2 | -3.2 (278%) | +2.1 (-178%) | - (holding) | 0.81 (0.66-0.97) at 10%, 0.63 at 1%; finish +1.9; 45561 teams, 21 slates | LEAN against |
| Starter early (rounds 1-3) + his backup late (rounds 4-6) | 0.93 (0.76-1.09) at 10%, 0.76 at 1%; finish -0.4; 18834 teams, 20 slates | -0.1 | -2.2 | +2.2 | - (holding) | 0.88 (0.71-1.06) at 10%, 0.71 at 1%; finish +0.1; 18836 teams, 20 slates | LEAN against |

### 2. Fallers: the definitions behind card-fallers

Ranks are the night's closing-ADP order. 6-drafter pods (4-drafter in brackets):
- **1/2 turn** (picks 6-7, or 5 and 8 [3-4, or 3 and 6]): your first player is a top-4 [top-2] ADP rank and your second is ranked 5-8 [3-6]. In the draft room: a top-4 [top-2] player still there at your turn pick; take him.
- **2/3 turn** (picks 12-13, or 11 and 14 [8-9, or 7 and 10]), for the 1.01 and 1.02 drafters: your second player is ranked 9th or better [5th or better], 3+ ranks ahead of your turn pick; take him.
Measured against same-contest, same-price teams that took the ADP-order pair at that turn (the trusting teams); the price-split check is in 3b. Fallers elsewhere in the draft: part 4 below.

### 3. Exposure, not order: T3 VALUE and T4 PRICEY

Against same-contest, same-price teams without (at each team's draft window).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| 2+ T3 VALUE players | 1.58 (1.26-1.84) at 10%, 2.17 at 1%; finish -8.5; 16158 teams, 19 slates | +8.5 | +10.0 (117%) | -1.5 (-17%) | - (holding) | 1.59 (1.27-1.86) at 10%, 2.20 at 1%; finish -8.5; 16158 teams, 19 slates | LEAN for |
| 1+ T3 VALUE player | 1.21 (0.97-1.46) at 10%, 1.21 at 1%; finish -3.9; 132195 teams, 26 slates | +3.8 | +3.4 (90%) | +0.4 (10%) | - (holding) | 1.10 (0.90-1.31) at 10%, 1.11 at 1%; finish -2.8; 132187 teams, 26 slates | no lean |
| A T4 PRICEY player | 1.03 (0.89-1.16) at 10%, 1.09 at 1%; finish -0.3; 53763 teams, 13 slates | +0.3 | -0.3 | +0.6 | - (holding) | 0.94 (0.82-1.05) at 10%, 0.99 at 1%; finish +0.4; 53754 teams, 13 slates | no lean |

### 4. Fallers in every round

A team's k-th player by the ADP it paid stands for its round-k pick (pick order isn't public, so this is a lower bound on the slide). A faller was paid an ADP 3+ picks before that round's first pick (round 3 on 6 drafters: ADP 10 or better). Explained: tagged at the team's window, or his tag changed between Lock AM and lock. A: teams with that faller in round k; B: teams whose round-k player wasn't a faller.

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Round 1, nothing explains it | none | - | - | - |
| Round 1, explained | none | - | - | - |
| Round 2, nothing explains it | 0.38 (0.00-1.05) at 10%, 3.84 at 1%; finish +7.7; 23 teams, 8 slates | -9.8 | +2.0 (-21%) | -11.8 (121%) | +7.5 | 0.42 (0.00-1.13) at 10%, 3.85 at 1%; finish +6.1; 23 teams, 8 slates | not enough |
| Round 2, explained (tag or news) | 1.06 at 10%, 0.00 at 1%; finish +30.5; 5 teams, 2 slates | -37.9 | -34.3 (90%) | -3.6 (10%) | -24.1 | 1.20 at 10%, 0.00 at 1%; finish +27.1; 5 teams, 2 slates | not enough |
| Round 3, nothing explains it | 1.23 (1.02-1.51) at 10%, 2.08 at 1%; finish -4.3; 596 teams, 26 slates | +1.2 | -1.5 (-132%) | +2.7 (232%) | +3.4 | 1.34 (1.07-1.76) at 10%, 2.33 at 1%; finish -4.5; 596 teams, 26 slates | LEAN for |
| Round 3, explained (tag or news) | 1.89 (1.22-2.66) at 10%, 2.32 at 1%; finish -14.4; 148 teams, 9 slates | +15.1 | +13.2 (88%) | +1.8 (12%) | +18.2 | 2.62 (1.92-3.14) at 10%, 3.59 at 1%; finish -19.4; 148 teams, 9 slates | RULE for |
| Round 4, nothing explains it | 1.46 (1.13-1.77) at 10%, 1.75 at 1%; finish -6.7; 2154 teams, 31 slates | +5.0 | +1.8 (37%) | +3.2 (63%) | +3.9 | 1.53 (1.21-1.82) at 10%, 1.88 at 1%; finish -7.3; 2154 teams, 31 slates | RULE for |
| Round 4, explained (tag or news) | 2.28 (1.48-3.24) at 10%, 1.02 at 1%; finish -12.3; 72 teams, 8 slates | +9.1 | +6.5 (72%) | +2.5 (28%) | +8.7 | 2.35 (1.52-3.31) at 10%, 1.10 at 1%; finish -12.5; 72 teams, 8 slates | not enough |
| Round 5, nothing explains it | 1.74 (1.45-2.03) at 10%, 2.80 at 1%; finish -8.1; 4446 teams, 30 slates | +7.0 | +2.4 (34%) | +4.6 (66%) | +2.6 | 1.78 (1.49-2.06) at 10%, 2.93 at 1%; finish -8.3; 4446 teams, 30 slates | LEAN for |
| Round 5, explained (tag or news) | 2.17 (1.28-3.05) at 10%, 3.18 at 1%; finish -14.8; 177 teams, 9 slates | +11.0 | +10.1 (92%) | +0.9 (8%) | +9.3 | 2.13 (1.34-2.87) at 10%, 3.02 at 1%; finish -14.0; 177 teams, 9 slates | LEAN for |
| Round 6, nothing explains it | 1.04 (0.91-1.18) at 10%, 0.99 at 1%; finish -0.1; 7533 teams, 31 slates | -0.3 | -3.5 | +3.2 | -0.5 | 1.17 (1.03-1.29) at 10%, 1.15 at 1%; finish -1.8; 7533 teams, 31 slates | RULE for |
| Round 6, explained (tag or news) | 1.62 (1.01-1.82) at 10%, 1.31 at 1%; finish -10.2; 221 teams, 5 slates | +8.4 | +3.2 (38%) | +5.3 (62%) | +6.8 | 1.62 (1.19-1.73) at 10%, 1.32 at 1%; finish -10.6; 221 teams, 5 slates | RULE for |

### 5. The original rules (kept-*), asked 2026-11-11

Each tier's kept rule is the Tiers button's order there. A: teams holding the button's first of a decision pair (ADP within 4, same tier) and not its second; B: the reverse. Only pairs with the same flag and no tag on either, so the order is the rule's steps, not VALUE first / PRICEY last or a Questionable push (those have their own rows).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| AM T1: ADP, Boom deciding within 2 picks | 1.78 (1.31-2.42) at 10%, 2.08 at 1%; finish -6.4; 64281 teams, 23 slates | +6.6 | +5.4 (81%) | +1.2 (19%) | +6.1 | 1.83 (1.34-2.53) at 10%, 2.09 at 1%; finish -7.2; 64270 teams, 23 slates | LEAN for |
| PM T1: ETR | 1.20 (1.03-1.42) at 10%, 1.26 at 1%; finish -3.0; 188915 teams, 30 slates | +3.0 | +3.4 (113%) | -0.4 (-13%) | +4.8 | 1.30 (1.08-1.57) at 10%, 1.40 at 1%; finish -4.0; 188917 teams, 30 slates | RULE for |
| AM T2: ADP straight | 0.96 (0.87-1.04) at 10%, 0.98 at 1%; finish +0.6; 420938 teams, 24 slates | -0.7 | +0.4 (-53%) | -1.1 (153%) | +1.6 | 0.99 (0.91-1.08) at 10%, 1.04 at 1%; finish +0.1; 420928 teams, 24 slates | no lean |
| AM T3/T4: Proj, ADP deciding within 3 points | 1.05 (0.90-1.24) at 10%, 1.01 at 1%; finish -0.4; 188882 teams, 24 slates | +0.2 | +0.6 | -0.4 | +2.0 | 1.09 (0.93-1.28) at 10%, 1.04 at 1%; finish -1.0; 188877 teams, 24 slates | no lean |
| PM T3: ETR, ties to ADP then Boom | 1.09 (0.97-1.20) at 10%, 0.99 at 1%; finish -2.0; 283025 teams, 29 slates | +1.9 | +2.2 (116%) | -0.3 (-16%) | +2.2 | 1.11 (0.98-1.25) at 10%, 1.02 at 1%; finish -2.3; 283029 teams, 29 slates | LEAN for |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.77 (0.65-0.93) at 10%, 0.59 at 1%; finish +3.0; 45442 teams, 31 slates | 1.27 (0.70-2.00) at 10%, 0.00 at 1%; finish -2.9; 170 teams, 24 slates |
| 1/2 | fallers vs trust | 1.36 (1.08-1.76) at 10%, 1.84 at 1%; finish -2.7; 66789 teams, 31 slates | 1.44 (0.96-2.07) at 10%, 1.72 at 1%; finish -7.1; 315 teams, 28 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.23 (0.80-1.88) at 10%, 0.99 at 1%; finish -1.5; 6638 teams, 23 slates | 1.57 (0.65-3.22) at 10%, 0.00 at 1%; finish -5.6; 67 teams, 12 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.17 (0.79-1.59) at 10%, 1.65 at 1%; finish -2.1; 23530 teams, 26 slates | 0.55 (0.00-1.27) at 10%, 0.00 at 1%; finish -4.9; 88 teams, 18 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.17 (0.90-1.46) at 10%, 1.35 at 1%; finish -0.1; 18907 teams, 27 slates | 1.74 (1.11-2.44) at 10%, 1.65 at 1%; finish -8.0; 87 teams, 20 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.94 (0.61-1.33) at 10%, 0.61 at 1%; finish -0.7; 17785 teams, 27 slates | 1.02 (0.22-2.15) at 10%, 0.00 at 1%; finish -7.2; 71 teams, 20 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.05 (0.61-1.68) at 10%, 0.79 at 1%; finish -2.3; 13623 teams, 26 slates | 0.34 (0.00-0.69) at 10%, 0.00 at 1%; finish -5.6; 54 teams, 17 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 0.97 (0.77-1.17) at 10%, 0.73 at 1%; finish -0.5; 11340 teams, 26 slates | 1.47 (0.67-2.28) at 10%, 0.00 at 1%; finish -6.6; 55 teams, 17 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 0.91 (0.50-1.31) at 10%, 1.30 at 1%; finish +1.3; 10757 teams, 27 slates | 1.31 (0.47-2.40) at 10%, 0.00 at 1%; finish -5.4; 40 teams, 13 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.12 (0.55-1.78) at 10%, 1.03 at 1%; finish +0.5; 7597 teams, 26 slates | 2.60 (1.09-3.95) at 10%, 0.00 at 1%; finish -7.2; 42 teams, 9 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.89 (0.51-1.36) at 10%, 0.63 at 1%; finish -0.1; 6825 teams, 27 slates | 0.33 (0.00-1.21) at 10%, 0.00 at 1%; finish +3.4; 41 teams, 7 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.68 (0.43-0.94) at 10%, 0.37 at 1%; finish +1.6; 5527 teams, 27 slates | 0.71 (0.00-1.42) at 10%, 0.00 at 1%; finish +1.3; 22 teams, 8 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 0.63 (0.39-0.98) at 10%, 0.39 at 1%; finish +3.4; 3265 teams, 26 slates | 1.17 (0.00-3.49) at 10%, 0.00 at 1%; finish -10.8; 14 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 1.10 (0.64-1.47) at 10%, 1.35 at 1%; finish +0.4; 3249 teams, 27 slates | 0.85 (0.00-1.97) at 10%, 0.00 at 1%; finish -2.0; 13 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 0.91 (0.63-1.20) at 10%, 0.89 at 1%; finish +2.8; 3059 teams, 27 slates | 1.06 (0.00-3.52) at 10%, 0.00 at 1%; finish -0.4; 14 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.24 (0.76-1.78) at 10%, 0.88 at 1%; finish -6.8; 1933 teams, 27 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.40 (0.27-0.55) at 10%, 0.00 at 1%; finish +3.5; 1889 teams, 27 slates | none |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 0.94 (0.61-1.33) at 10%, 1.22 at 1%; finish +0.4; 1849 teams, 26 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.42 (0.29-0.55) at 10%, 0.24 at 1%; finish +11.5; 1669 teams, 26 slates | none |
| 2/3 | a. reach vs trust | 1.01 (0.87-1.15) at 10%, 1.24 at 1%; finish +1.0; 38543 teams, 31 slates | 1.48 (1.01-1.98) at 10%, 1.65 at 1%; finish -3.9; 168 teams, 25 slates |
| 2/3 | fallers vs trust | 1.13 (1.00-1.31) at 10%, 1.27 at 1%; finish -3.0; 27582 teams, 31 slates | 1.69 (1.23-2.18) at 10%, 1.26 at 1%; finish -7.1; 127 teams, 27 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.59 (1.34-1.87) at 10%, 2.15 at 1%; finish -6.6; 8432 teams, 29 slates | 1.61 (0.91-2.25) at 10%, 3.30 at 1%; finish -6.9; 94 teams, 17 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.23 (0.91-1.56) at 10%, 1.57 at 1%; finish -1.0; 5417 teams, 26 slates | 0.22 (0.00-0.40) at 10%, 0.00 at 1%; finish -5.7; 47 teams, 12 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.94 (0.69-1.16) at 10%, 0.70 at 1%; finish -0.7; 7362 teams, 25 slates | 0.97 (0.00-1.72) at 10%, 0.00 at 1%; finish -7.1; 27 teams, 13 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 1.11 (0.80-1.43) at 10%, 0.96 at 1%; finish +2.7; 5423 teams, 27 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +11.2; 19 teams, 10 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 1.35 (1.01-1.74) at 10%, 1.57 at 1%; finish -6.5; 5266 teams, 27 slates | 0.57 (0.00-1.47) at 10%, 0.00 at 1%; finish -1.5; 22 teams, 11 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 0.80 (0.46-1.19) at 10%, 0.55 at 1%; finish +8.7; 4969 teams, 25 slates | 0.89 (0.00-1.65) at 10%, 0.00 at 1%; finish +8.2; 28 teams, 10 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 1.34 (1.01-1.65) at 10%, 1.26 at 1%; finish -8.2; 4287 teams, 27 slates | 0.54 (0.00-1.11) at 10%, 2.15 at 1%; finish -0.9; 25 teams, 12 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 0.98 (0.72-1.26) at 10%, 0.45 at 1%; finish -2.6; 3938 teams, 27 slates | 1.83 (0.28-4.36) at 10%, 0.00 at 1%; finish -15.8; 18 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 1.10 (0.75-1.51) at 10%, 1.22 at 1%; finish +3.8; 3881 teams, 26 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +2.3; 19 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.81 (0.55-1.13) at 10%, 0.71 at 1%; finish -0.8; 3824 teams, 27 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +4.9; 8 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.39 (1.00-1.84) at 10%, 1.59 at 1%; finish -5.3; 3515 teams, 27 slates | 1.55 (0.57-2.72) at 10%, 3.65 at 1%; finish -2.7; 22 teams, 10 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.07 (0.65-1.53) at 10%, 1.17 at 1%; finish +1.7; 3368 teams, 26 slates | 0.93 (0.00-2.65) at 10%, 0.00 at 1%; finish -6.9; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.88 (0.62-1.18) at 10%, 0.55 at 1%; finish -0.1; 3225 teams, 27 slates | 0.71 (0.00-2.62) at 10%, 0.00 at 1%; finish +13.5; 9 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.18 (0.83-1.57) at 10%, 1.10 at 1%; finish -2.0; 2949 teams, 27 slates | 3.34 (2.75-3.70) at 10%, 0.00 at 1%; finish -20.1; 19 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.52 (0.34-0.70) at 10%, 0.44 at 1%; finish +4.8; 2923 teams, 27 slates | 0.56 (0.00-1.69) at 10%, 0.00 at 1%; finish +9.6; 15 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 13 | 1.06 (0.79-1.33) at 10%, 1.02 at 1%; finish -3.7; 2817 teams, 27 slates | 2.14 (0.71-3.62) at 10%, 0.00 at 1%; finish -10.1; 16 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.78 (0.57-1.07) at 10%, 0.40 at 1%; finish -0.1; 2784 teams, 27 slates | 1.68 (0.00-3.24) at 10%, 0.00 at 1%; finish -13.1; 14 teams, 11 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 15 | 0.77 (0.51-1.09) at 10%, 1.15 at 1%; finish +0.9; 2758 teams, 27 slates | 1.25 (0.00-1.98) at 10%, 0.00 at 1%; finish -12.8; 6 teams, 3 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 212 | 96% | 96% | +0 |
| AM | T1-T2 | Q TRAP | 26 | 81% | 96% | -15 |
| AM | T1-T2 | VALUE | 16 | 79% | 97% | -17 |
| AM | T3-T4 | PRICEY | 104 | 95% | 96% | -1 |
| AM | T3-T4 | Q TRAP | 6 | 96% | 89% | +7 |
| AM | T3-T4 | VALUE | 140 | 90% | 96% | -6 |
| AM | T5 | PRICEY | 13 | 96% | 59% | +37 |
| AM | T5 | Q FAIR | 325 | 11% | 19% | -8 |
| AM | T5 | VALUE | 464 | 46% | 26% | +19 |
| PM | T1-T2 | PRICEY | 224 | 95% | 98% | -3 |
| PM | T1-T2 | Q TRAP | 43 | 79% | 99% | -20 |
| PM | T1-T2 | VALUE | 21 | 94% | 98% | -4 |
| PM | T3-T4 | PRICEY | 151 | 99% | 99% | -0 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 8 | 77% | 99% | -22 |
| PM | T3-T4 | VALUE | 239 | 95% | 99% | -3 |
| PM | T5 | PRICEY | 26 | 92% | 48% | +44 |
| PM | T5 | Q FAIR | 185 | 7% | 21% | -14 |
| PM | T5 | VALUE | 527 | 67% | 29% | +38 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 61 (of all T5 breakers: PRICEY 14, VALUE 9, unflagged 67).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.19 (1.09-1.29) at 10%, 1.30 at 1%; finish -2.1; 202845 teams, 30 slates | 1.50 (1.31-1.72) at 10%, 1.11 at 1%; finish -7.8; 940 teams, 29 slates |
| Same-position teammates | 0.82 (0.75-0.91) at 10%, 0.85 at 1%; finish +3.4; 119637 teams, 31 slates | 1.28 (1.06-1.58) at 10%, 1.55 at 1%; finish -4.2; 463 teams, 29 slates |
| Same-position teammates, spread 5+ | 0.95 (0.88-1.02) at 10%, 0.84 at 1%; finish +0.4; 54003 teams, 28 slates | 1.50 (1.06-1.99) at 10%, 1.56 at 1%; finish -9.8; 233 teams, 22 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.70 | 1.66 | 1.09 | 0.93 | 0.68 | 1.13 | 1.00 | 0.02 | 0.13 | 0.01 | 2.86 |
| Field | 0.58 | 1.68 | 1.11 | 0.97 | 0.63 | 0.98 | 1.10 | 0.02 | 0.11 | 0.01 | 1.05 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.73 (0.64-0.82) at 10%, 0.67 at 1%; finish +6.8; 102890 teams, 30 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

914 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 381167 | 0.58 | 1.69 | 1.13 | 0.98 | 0.61 | 1.04 | 1.06 | 0.24 | 93% |
| Me | 2237 | 0.61 | 1.74 | 1.32 | 1.09 | 0.59 | 1.56 | 0.66 | 0.32 | 91% |
| Everyone | 543202 | 0.58 | 1.68 | 1.11 | 0.97 | 0.63 | 0.98 | 1.10 | 0.23 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.56 (0.40-0.76) at 10%, 0.29 at 1%; finish +11.5; 20490 teams, 12 slates |
| T1-T2 | AM | 0.54 (0.35-0.77) at 10%, 0.35 at 1%; finish +9.3; 8687 teams, 10 slates |
| T1-T2 | PM | 0.57 (0.39-0.77) at 10%, 0.25 at 1%; finish +13.2; 11803 teams, 8 slates |
| T3-T5 | both | 0.92 (0.81-1.03) at 10%, 1.05 at 1%; finish +1.7; 27582 teams, 21 slates |
| T3-T5 | AM | 0.89 (0.77-1.00) at 10%, 1.06 at 1%; finish +2.2; 15155 teams, 19 slates |
| T3-T5 | PM | 0.95 (0.78-1.16) at 10%, 1.05 at 1%; finish +1.2; 12427 teams, 14 slates |
| not credited | both | 0.73 (0.65-0.82) at 10%, 0.69 at 1%; finish +7.4; 42942 teams, 30 slates |
| not credited | AM | 0.80 (0.69-0.93) at 10%, 0.77 at 1%; finish +5.5; 17957 teams, 23 slates |
| not credited | PM | 0.69 (0.60-0.79) at 10%, 0.65 at 1%; finish +8.8; 24985 teams, 30 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 18 show a lean or rule and 12 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | RULE for | RULE for | 1.39 (1.18-1.64) | keep: points and money agree |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | RULE for | 1.36 (1.21-1.51) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | RULE for | RULE for | 1.26 (1.17-1.36) | candidate: hand to the rankings side with its points cost |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 1.08 (0.89-1.32) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | RULE for | LEAN for | 1.34 (1.08-1.67) | keep: points and money agree |
| am-questionable-no-push | adopted | no variant beats it | LEAN for | no lean | 1.29 (1.00-1.62) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 0.91 (0.76-1.09) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | no lean | 1.17 (0.92-1.46) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | no lean | no lean | 1.31 (0.53-1.79) | not enough on either side yet |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 1.07 (0.90-1.24) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 1.09 (0.92-1.29) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 1.03 (0.84-1.28) | not enough on either side yet |
| pm-t5-beneficiary | adopted | LEAN (listed) | no lean | no lean | 1.02 (0.91-1.17) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | no lean | no lean | 1.05 (0.95-1.14) | drop on points unless money clears its bar |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.91 (1.50-2.51) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | LEAN against | LEAN against | 0.85 (0.70-1.03) | keep on points; money leans against (watch) |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 1.07 (0.61-1.79) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | LEAN for | no lean | 1.10 (1.01-1.20) | keep on points; money not settled |
| one-tier-cap | adopted | LEAN (both windows) | RULE against | LEAN against | 0.79 (0.66-0.95) | keep on points; money leans against (watch) |
| pm-middle-takes | candidate | LEAN (single window) | RULE against | LEAN against | 0.82 (0.73-0.95) | keep on points; money leans against (watch) |
| pm-t2-other-reads | candidate | LEAN (single window) | LEAN for | LEAN for | 1.36 (1.12-1.70) | keep: points and money agree |
| am-t5-other-reads | candidate | LEAN against (single window) | no lean | no lean | 1.23 (0.83-1.62) | drop on points unless money clears its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

