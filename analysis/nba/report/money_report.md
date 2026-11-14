# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-14. Slates 2026-10-20 to 2026-11-13: 24 nights, 75 contests, 397456 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

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

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 12 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_fri_main, nba_mon_main, nba_mon_main, nba_sat_main, nba_sun_main, nba_thu_main, nba_thu_main, nba_tue_main, nba_wed_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
  - 2026-11-13: 428 swapped-in picks, 0 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 369950 of 397456 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

**Ten random teams**

| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |
|---|---|---|---|---|---|---|---|
| 2026-10-22 | Thursday Night Hoops | 4 | PM | 4 | 216.7 | 144.7 | 3.3, 7.5, 8.1, 14.9, 20.2, 21.0 |
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
| 2026-10-30 | Fast Break Friday | 6 | PM | 3 | 223.0 | 203.5 | 4.1, 8.1, 17.0, 24.6, 26.3, 31.0 |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-07 | Saturday Slam | 6 | PM | 2 | 221.3 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 15.8 (swap) |
| 2026-11-09 | Monday Night Hoops | 6 | PM | 4 | 220.9 | 247.4 | 3.4, 11.7, 14.6, 20.1, 29.0, 31.3 |
| 2026-11-11 | Hump Day Hoops | 6 | AM | 2 | 213.8 | 216.5 | 4.3, 12.1, 15.1, 20.4, 29.1, 32.5 |
| 2026-11-12 | Thursday Night Hoops | 6 | PM | 2 | 216.3 | 279.2 | 2.1, 13.5, 18.6, 21.3, 26.3, 32.2 |
| 2026-11-12 | Thursday Night Hoops | 6 | AM | 4 | 219.6 | 162.3 | 1.1, 12.7, 16.9, 24.3, 27.3, 35.1 |
| 2026-11-13 | Fast Break Friday | 6 | PM | 5 | 227.0 | 231.6 | 1.1, 11.6, 13.5, 19.8, 23.8, 32.8 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.1 | 11 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.5 | 11 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.1 | 13 |
| Contest (its mean against its night's) | The Layup Line | -0.4 | 14 |
| Contest (its mean against its night's) | flagships | +0.0 | 22 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +2.1 | 64 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +5.9 | 73937 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +2.0 | 73981 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.2 | 73999 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -2.4 | 73579 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.3 | 74454 |
| Swap on the team (inside contest) | no | +0.9 | 306643 |
| Swap on the team (inside contest) | yes | -4.2 | 63307 |
| Window (inside contest) | AM | -0.5 | 118276 |
| Window (inside contest) | PM | +0.2 | 251064 |

Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and 6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test compares teams inside one price group, and runs again on ten groups.

## 2. My results

Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.

| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fast Break Friday | 6 | 4 | 372 | 0.54 | 1.40 | 1.45 | 1.34 | 40.0 | 1.38 (87) | 1.47 (285) | $1860 | $1567 | -16% |
| Hump Day Hoops | 6 | 4 | 330 | 0.91 | 1.21 | 1.30 | 1.12 | 50.6 | 1.62 (136) | 1.08 (194) | $1650 | $907 | -45% |
| Monday Night Hoops | 6 | 3 | 250 | 0.00 | 0.96 | 1.00 | 1.12 | 46.6 | 1.02 (59) | 0.99 (191) | $1250 | $760 | -39% |
| Tuesday Tip-Off | 6 | 2 | 230 | 1.30 | 1.13 | 1.22 | 1.22 | 46.4 | 0.78 (90) | 1.50 (140) | $1150 | $1530 | +33% |
| Saturday Slam | 6 | 3 | 120 | 4.17 | 2.33 | 1.58 | 1.25 | 47.0 | 1.43 (28) | 1.63 (92) | $600 | $6569 | +995% |
| Sunday Shootaround | 6 | 2 | 120 | 0.83 | 1.33 | 1.33 | 1.38 | 41.3 | 3.00 (30) | 0.78 (90) | $600 | $480 | -20% |
| Thursday Night Hoops | 6 | 1 | 80 | 0.00 | 1.00 | 1.00 | 0.94 | 45.9 | 1.75 (40) | 0.25 (40) | $400 | $234 | -42% |
| Buzzer Beater | 6 | 5 | 70 | 1.43 | 1.14 | 1.14 | 1.07 | 44.6 | 1.43 (14) | 1.07 (56) | $210 | $183 | -13% |
| The Layup Line | 6 | 4 | 24 | 0.00 | 1.67 | 1.25 | 1.25 | 49.8 | 2.00 (5) | 1.05 (19) | $120 | $50 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 1.03 (39) | 1.77 (141) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 19 | 1596 | 0.94 | 1.29 | 1.28 (1.13-1.43) | 1.21 | 45.4 | 1.43 (489) | 1.21 (1107) | $7840 | $12280 | +57% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.82 (49) | 1.71 (175) | $1120 | $847 | -24% |
| **all** | - | 24 | 1820 | 0.93 | 1.31 | 1.31 (1.16-1.47) | 1.23 | 45.1 | 1.38 (538) | 1.28 (1282) | $8960 | $13127 | +47% |

Dollars: $8960 in fees, $13127 won, +47% ROI over 24 nights (80% range -29% to +142%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -23%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

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

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.31 (1.18-1.46) at 10%, 0.89 at 1%; finish -5.5; 1766 teams, 22 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 0.96 (0.86-1.08) at 10%, 1.12 at 1%; finish +1.4; 90940 teams, 22 slates | 0.89 (0.78-0.99) at 10%, 0.94 at 1%; finish +2.3; 76843 teams, 17 slates | 1.43 (1.09-2.10) at 10%, 2.80 at 1%; finish -3.5; 14097 teams, 5 slates | 1.55 (1.12-1.98) at 10%, 1.14 at 1%; finish -6.3; 836 teams, 22 slates | no lean | no lean |
|   AM only | 0.66 (0.52-0.83) at 10%, 0.29 at 1%; finish +5.1; 17689 teams, 17 slates | 0.66 (0.51-0.85) at 10%, 0.29 at 1%; finish +5.1; 16178 teams, 13 slates | 0.67 (0.48-1.64) at 10%, 0.31 at 1%; finish +5.0; 1511 teams, 4 slates | 0.36 (0.00-0.81) at 10%, 0.00 at 1%; finish +2.2; 63 teams, 9 slates | RULE against | RULE against |
|   PM only | 1.03 (0.91-1.17) at 10%, 1.32 at 1%; finish +0.6; 72522 teams, 22 slates | 0.94 (0.83-1.07) at 10%, 1.10 at 1%; finish +1.5; 60639 teams, 17 slates | 1.60 (1.25-2.10) at 10%, 4.19 at 1%; finish -3.8; 11883 teams, 5 slates | 1.78 (1.31-2.22) at 10%, 1.34 at 1%; finish -7.5; 762 teams, 20 slates | no lean | no lean |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.59 (1.19-2.15) at 10%, 2.28 at 1%; finish -6.3; 16039 teams, 6 slates | 1.34 (0.98-1.63) at 10%, 1.68 at 1%; finish -4.0; 14171 teams, 5 slates | 6.09 at 10%, 53.73 at 1%; finish -23.5; 1868 teams, 1 slates | 2.99 (0.92-3.65) at 10%, 3.42 at 1%; finish -14.8; 59 teams, 6 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.25 (1.11-1.41) at 10%, 1.34 at 1%; finish -3.2; 542122 teams, 22 slates | 1.23 (1.07-1.40) at 10%, 1.35 at 1%; finish -2.4; 399107 teams, 17 slates | 1.33 (0.95-1.64) at 10%, 1.30 at 1%; finish -5.5; 143015 teams, 5 slates | 1.52 (1.26-1.82) at 10%, 0.54 at 1%; finish -7.2; 4734 teams, 21 slates | RULE for | RULE for |
|   T3 | 1.25 (0.93-1.65) at 10%, 1.36 at 1%; finish -3.8; 178528 teams, 16 slates | 1.26 (0.81-1.85) at 10%, 1.49 at 1%; finish -2.9; 108478 teams, 12 slates | 1.24 (0.81-1.65) at 10%, 1.19 at 1%; finish -5.1; 70050 teams, 4 slates | 1.13 (0.83-1.52) at 10%, 0.00 at 1%; finish -7.8; 1541 teams, 16 slates | LEAN for | LEAN for |
|   T4 | 1.31 (1.16-1.47) at 10%, 1.50 at 1%; finish -3.1; 204041 teams, 18 slates | 1.27 (1.12-1.42) at 10%, 1.48 at 1%; finish -2.4; 158324 teams, 15 slates | 1.49 (0.91-2.17) at 10%, 1.64 at 1%; finish -5.6; 45717 teams, 3 slates | 1.79 (1.36-2.37) at 10%, 1.70 at 1%; finish -8.0; 1420 teams, 17 slates | RULE for | RULE for |
|   T5 | 1.15 (0.90-1.46) at 10%, 1.05 at 1%; finish -2.6; 159443 teams, 16 slates | 1.08 (0.82-1.45) at 10%, 0.96 at 1%; finish -1.6; 132223 teams, 12 slates | 1.47 (0.82-2.14) at 10%, 1.56 at 1%; finish -7.1; 27220 teams, 4 slates | 1.60 (1.43-1.78) at 10%, 0.24 at 1%; finish -6.8; 1773 teams, 16 slates | no lean | no lean |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.26 (1.13-1.39) at 10%, 1.45 at 1%; finish -2.1; 700561 teams, 22 slates | 1.29 (1.18-1.41) at 10%, 1.45 at 1%; finish -2.9; 533514 teams, 17 slates | 1.17 (0.81-1.62) at 10%, 1.45 at 1%; finish +0.3; 167047 teams, 5 slates | 1.80 (1.51-2.09) at 10%, 1.75 at 1%; finish -8.0; 4157 teams, 22 slates | RULE for | RULE for |
|   T1 | 1.59 (1.23-2.07) at 10%, 2.46 at 1%; finish -3.7; 127656 teams, 14 slates | 2.04 (1.59-2.59) at 10%, 3.53 at 1%; finish -8.1; 94533 teams, 11 slates | 0.68 (0.30-1.14) at 10%, 0.86 at 1%; finish +8.9; 33123 teams, 3 slates | 2.16 (1.27-3.32) at 10%, 3.04 at 1%; finish -7.6; 611 teams, 13 slates | LEAN for | LEAN for |
|   T2 | 1.18 (1.02-1.37) at 10%, 1.25 at 1%; finish -1.3; 328777 teams, 20 slates | 1.14 (0.97-1.35) at 10%, 1.11 at 1%; finish -1.4; 257061 teams, 15 slates | 1.33 (0.99-2.04) at 10%, 1.88 at 1%; finish -0.7; 71716 teams, 5 slates | 1.57 (1.27-1.93) at 10%, 1.33 at 1%; finish -6.6; 2056 teams, 20 slates | LEAN for | LEAN for |
|   T3 | 1.35 (1.09-1.69) at 10%, 1.46 at 1%; finish -4.2; 210904 teams, 18 slates | 1.37 (1.02-1.77) at 10%, 1.56 at 1%; finish -4.5; 154737 teams, 14 slates | 1.31 (0.93-2.17) at 10%, 1.24 at 1%; finish -3.6; 56167 teams, 4 slates | 2.18 (1.77-2.66) at 10%, 1.86 at 1%; finish -11.5; 1399 teams, 18 slates | RULE for | RULE for |
|   T4 | 1.97 (0.66-3.92) at 10%, 2.48 at 1%; finish -11.5; 12667 teams, 4 slates | 2.65 at 10%, 2.89 at 1%; finish -18.1; 7821 teams, 2 slates | 1.20 at 10%, 1.76 at 1%; finish -1.0; 4846 teams, 2 slates | 0.29 (0.00-0.32) at 10%, 0.00 at 1%; finish +7.9; 28 teams, 4 slates | LEAN for | LEAN for |
|   T5 | 0.76 (0.61-1.03) at 10%, 0.75 at 1%; finish +6.5; 20472 teams, 5 slates | 0.77 (0.61-1.07) at 10%, 0.76 at 1%; finish +6.1; 19305 teams, 4 slates | 0.40 at 10%, 0.00 at 1%; finish +12.5; 1167 teams, 1 slates | 1.37 (1.16-1.76) at 10%, 1.72 at 1%; finish -8.6; 63 teams, 4 slates | LEAN against | LEAN against |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 0.95 (0.73-1.28) at 10%, 0.83 at 1%; finish +0.5; 55669 teams, 17 slates | 0.93 (0.71-1.30) at 10%, 0.81 at 1%; finish +0.4; 47681 teams, 14 slates | 1.07 (0.84-1.19) at 10%, 1.04 at 1%; finish +1.1; 7988 teams, 3 slates | 0.87 (0.64-1.12) at 10%, 0.00 at 1%; finish -4.6; 281 teams, 16 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.46 (1.19-1.78) at 10%, 1.69 at 1%; finish -5.8; 225905 teams, 19 slates | 1.55 (1.22-1.99) at 10%, 1.94 at 1%; finish -6.2; 179407 teams, 14 slates | 1.22 (1.01-1.51) at 10%, 1.24 at 1%; finish -3.9; 46498 teams, 5 slates | 1.62 (1.29-2.08) at 10%, 0.74 at 1%; finish -6.6; 1391 teams, 17 slates | RULE for | RULE for |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 0.94 (0.74-1.21) at 10%, 1.05 at 1%; finish +1.8; 147162 teams, 21 slates | 0.92 (0.69-1.23) at 10%, 1.03 at 1%; finish +2.2; 127055 teams, 17 slates | 1.05 (0.88-1.44) at 10%, 1.14 at 1%; finish -0.6; 20107 teams, 4 slates | 1.27 (0.82-1.77) at 10%, 1.81 at 1%; finish -3.5; 837 teams, 21 slates | no lean | no lean |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.87 (0.41-1.52) at 10%, 1.02 at 1%; finish +4.8; 20544 teams, 6 slates | 0.99 (0.46-1.83) at 10%, 1.25 at 1%; finish +3.0; 18937 teams, 5 slates | 0.13 at 10%, 0.03 at 1%; finish +26.5; 1607 teams, 1 slates | 1.49 (0.34-5.12) at 10%, 3.40 at 1%; finish -7.0; 43 teams, 6 slates | no lean | no lean |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 1.03 (0.93-1.12) at 10%, 0.79 at 1%; finish -1.2; 120607 teams, 22 slates | 1.07 (0.98-1.17) at 10%, 0.86 at 1%; finish -1.6; 104592 teams, 17 slates | 0.77 (0.62-0.99) at 10%, 0.39 at 1%; finish +1.6; 16015 teams, 5 slates | 1.52 (1.18-1.98) at 10%, 0.64 at 1%; finish -7.0; 652 teams, 20 slates | no lean | no lean |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.92 (0.79-1.06) at 10%, 0.92 at 1%; finish +1.3; 262188 teams, 20 slates | 0.93 (0.78-1.09) at 10%, 0.88 at 1%; finish +0.6; 204141 teams, 15 slates | 0.90 (0.71-1.19) at 10%, 1.03 at 1%; finish +4.0; 58047 teams, 5 slates | 1.49 (1.24-1.88) at 10%, 1.09 at 1%; finish -5.6; 1081 teams, 20 slates | no lean | no lean |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.07 (0.82-1.37) at 10%, 1.09 at 1%; finish -0.4; 21228 teams, 16 slates | 0.95 (0.79-1.12) at 10%, 0.94 at 1%; finish +0.1; 12173 teams, 11 slates | 1.27 (0.66-2.08) at 10%, 1.36 at 1%; finish -1.2; 9055 teams, 5 slates | 1.17 (0.80-1.54) at 10%, 1.17 at 1%; finish -0.5; 175 teams, 12 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.03 (0.83-1.24) at 10%, 1.00 at 1%; finish -0.8; 26392 teams, 18 slates | 1.07 (0.84-1.30) at 10%, 1.07 at 1%; finish -1.0; 22074 teams, 14 slates | 0.86 (0.65-1.11) at 10%, 0.67 at 1%; finish +0.5; 4318 teams, 4 slates | 1.26 (0.73-1.96) at 10%, 0.00 at 1%; finish -6.1; 143 teams, 14 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 0.97 (0.83-1.15) at 10%, 1.02 at 1%; finish +1.0; 333514 teams, 17 slates | 0.93 (0.78-1.11) at 10%, 0.94 at 1%; finish +1.8; 222576 teams, 12 slates | 1.06 (0.75-1.74) at 10%, 1.24 at 1%; finish -0.7; 110938 teams, 5 slates | 1.25 (0.92-1.70) at 10%, 0.61 at 1%; finish -2.8; 1221 teams, 17 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 0.86 (0.79-0.96) at 10%, 0.66 at 1%; finish +0.6; 219160 teams, 17 slates | 0.83 (0.75-0.97) at 10%, 0.64 at 1%; finish +1.0; 172548 teams, 12 slates | 0.97 (0.92-1.04) at 10%, 0.76 at 1%; finish -1.2; 46612 teams, 5 slates | 0.94 (0.61-1.38) at 10%, 0.68 at 1%; finish -2.8; 1293 teams, 15 slates | RULE against | RULE against |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | none | none | none | none | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 0.89 (0.41-1.01) at 10%, 0.65 at 1%; finish +1.5; 2041 teams, 9 slates | 0.98 (0.46-1.03) at 10%, 0.78 at 1%; finish -0.5; 1736 teams, 7 slates | 0.46 at 10%, 0.00 at 1%; finish +13.1; 305 teams, 2 slates | 1.38 (1.16-2.14) at 10%, 0.00 at 1%; finish -9.8; 30 teams, 3 slates | LEAN against | LEAN against |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 1.03 (0.82-1.24) at 10%, 1.06 at 1%; finish +0.7; 25341 teams, 10 slates | 1.06 (0.79-1.32) at 10%, 1.12 at 1%; finish -0.2; 16356 teams, 7 slates | 0.97 (0.53-1.33) at 10%, 0.94 at 1%; finish +2.5; 8985 teams, 3 slates | 1.10 (0.75-1.42) at 10%, 0.00 at 1%; finish +1.6; 155 teams, 10 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 1.08 (0.92-1.31) at 10%, 0.93 at 1%; finish -1.7; 19582 teams, 17 slates | 0.99 (0.80-1.31) at 10%, 0.90 at 1%; finish -0.7; 10645 teams, 12 slates | 1.19 (0.99-1.51) at 10%, 0.96 at 1%; finish -2.9; 8937 teams, 5 slates | 2.04 (1.13-3.03) at 10%, 3.80 at 1%; finish -6.8; 55 teams, 11 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.23 (1.01-1.57) at 10%, 1.32 at 1%; finish -2.2; 13383 teams, 14 slates | 1.49 (1.19-2.10) at 10%, 1.84 at 1%; finish -4.6; 6633 teams, 9 slates | 0.99 (0.67-1.38) at 10%, 0.88 at 1%; finish +0.2; 6750 teams, 5 slates | 0.96 (0.42-1.88) at 10%, 0.00 at 1%; finish -6.5; 43 teams, 8 slates | LEAN for | LEAN for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.01 (0.88-1.19) at 10%, 1.12 at 1%; finish -0.7; 30760 teams, 16 slates | 0.95 (0.83-1.13) at 10%, 1.05 at 1%; finish +1.1; 26256 teams, 12 slates | 1.47 (0.92-1.98) at 10%, 1.58 at 1%; finish -11.1; 4504 teams, 4 slates | 2.08 (1.26-3.00) at 10%, 1.26 at 1%; finish -8.5; 183 teams, 12 slates | no lean | no lean |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 0.88 (0.76-1.02) at 10%, 0.85 at 1%; finish +1.5; 189750 teams, 20 slates | 0.89 (0.74-1.06) at 10%, 0.82 at 1%; finish +0.8; 144663 teams, 15 slates | 0.86 (0.69-1.22) at 10%, 0.93 at 1%; finish +3.9; 45087 teams, 5 slates | 1.05 (0.82-1.42) at 10%, 0.35 at 1%; finish -5.0; 1408 teams, 19 slates | LEAN against | LEAN against |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 1.33 (1.07-1.66) at 10%, 1.37 at 1%; finish -4.4; 148506 teams, 21 slates | 1.32 (1.07-1.68) at 10%, 1.29 at 1%; finish -4.9; 126593 teams, 17 slates | 1.38 (0.73-2.77) at 10%, 1.80 at 1%; finish -1.4; 21913 teams, 4 slates | 1.47 (1.15-1.82) at 10%, 0.77 at 1%; finish -7.8; 902 teams, 21 slates | RULE for | RULE for |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.24 (0.82-1.66) at 10%, 1.74 at 1%; finish -2.0; 29686 teams, 14 slates | 1.36 (0.87-1.86) at 10%, 2.11 at 1%; finish -3.3; 27724 teams, 11 slates | 0.38 (0.37-0.40) at 10%, 0.09 at 1%; finish +16.8; 1962 teams, 3 slates | 1.02 (0.58-1.58) at 10%, 0.00 at 1%; finish +3.8; 82 teams, 11 slates | no lean | no lean |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 AM only | RULE against | -5.0 | -3.1 (63%) | -1.8 (37%) | -5.7 | 0.66 (0.52-0.86) at 10%, 0.29 at 1%; finish +6.3; 17700 teams, 17 slates | RULE against |
| leverage-t2-t4 | RULE for | +6.0 | +5.1 (85%) | +0.9 (15%) | -2.8 | 1.50 (1.09-2.16) at 10%, 1.69 at 1%; finish -4.8; 15979 teams, 6 slates | RULE for |
| value-up-middle-t5 | RULE for | +3.3 | +2.3 (70%) | +1.0 (30%) | +0.4 | 1.20 (1.05-1.37) at 10%, 1.26 at 1%; finish -2.6; 542117 teams, 22 slates | RULE for |
| value-up-middle-t5 T3 | LEAN for | +3.9 | +3.3 (85%) | +0.6 (15%) | +3.7 | 1.27 (0.94-1.68) at 10%, 1.37 at 1%; finish -4.1; 178534 teams, 16 slates | LEAN for |
| value-up-middle-t5 T4 | RULE for | +3.4 | +2.9 (87%) | +0.4 (13%) | +2.8 | 1.29 (1.13-1.46) at 10%, 1.49 at 1%; finish -3.0; 204049 teams, 18 slates | RULE for |
| pricey-flags | RULE for | +2.4 | +3.6 (149%) | -1.2 (-49%) | +4.4 | 1.27 (1.12-1.44) at 10%, 1.48 at 1%; finish -2.3; 700599 teams, 22 slates | RULE for |
| pricey-flags T1 | LEAN for | +2.5 | +4.5 (176%) | -1.9 (-76%) | +7.8 | 1.54 (1.10-2.18) at 10%, 2.37 at 1%; finish -3.5; 127670 teams, 14 slates | LEAN for |
| pricey-flags T2 | LEAN for | +1.8 | +2.4 (132%) | -0.6 (-32%) | +3.1 | 1.19 (1.02-1.40) at 10%, 1.28 at 1%; finish -1.5; 328781 teams, 20 slates | LEAN for |
| pricey-flags T3 | RULE for | +4.6 | +5.4 (117%) | -0.8 (-17%) | +4.7 | 1.33 (1.08-1.65) at 10%, 1.46 at 1%; finish -4.0; 210917 teams, 18 slates | RULE for |
| pricey-flags T4 | LEAN for | +10.9 | +6.9 (63%) | +4.0 (37%) | +6.9 | 1.93 (0.66-3.70) at 10%, 2.40 at 1%; finish -11.1; 12666 teams, 4 slates | LEAN for |
| pricey-flags T5 | LEAN against | -5.5 | +2.0 (-36%) | -7.5 (136%) | -5.8 | 0.88 (0.60-1.62) at 10%, 0.89 at 1%; finish +3.1; 20470 teams, 5 slates | no lean |
| am-t5-button-order | RULE for | +5.6 | +3.9 (70%) | +1.7 (30%) | +1.5 | 1.48 (1.20-1.81) at 10%, 1.73 at 1%; finish -6.0; 225879 teams, 19 slates | RULE for |
| q-tag-raises | RULE against | -0.8 | -1.4 (189%) | +0.7 (-89%) | +1.6 | 0.88 (0.81-0.99) at 10%, 0.69 at 1%; finish -0.0; 219137 teams, 17 slates | LEAN against |
| q-class-x:FAIR | LEAN against | -1.1 | -4.1 (385%) | +3.1 (-285%) | - (holding) | 0.81 (0.37-0.91) at 10%, 0.59 at 1%; finish +3.3; 2041 teams, 9 slates | RULE against |
| beneficiary-round6:played | LEAN for | +1.6 | +2.5 (162%) | -1.0 (-62%) | - (holding) | 1.21 (1.01-1.49) at 10%, 1.30 at 1%; finish -1.9; 13382 teams, 14 slates | LEAN for |
| pm-middle-takes | LEAN against | -1.6 | -1.2 (77%) | -0.4 (23%) | -0.7 | 0.90 (0.78-1.04) at 10%, 0.89 at 1%; finish +1.2; 189755 teams, 20 slates | LEAN against |
| pm-t2-other-reads | RULE for | +4.1 | +3.6 (88%) | +0.5 (12%) | +3.3 | 1.32 (1.07-1.64) at 10%, 1.29 at 1%; finish -4.2; 148498 teams, 21 slates | RULE for |
| turn 1/2: a. reach vs trust | RULE against | -1.5 | +0.2 (-16%) | -1.7 (116%) | -1.1 | 0.68 (0.57-0.86) at 10%, 0.48 at 1%; finish +2.9; 31262 teams, 22 slates | RULE against |
| turn 1/2: fallers vs trust | LEAN for | +2.0 | -0.1 (-5%) | +2.1 (105%) | +2.8 | 1.23 (0.93-1.69) at 10%, 1.29 at 1%; finish -2.9; 47259 teams, 22 slates | LEAN for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +1.1 | +1.9 (164%) | -0.7 (-64%) | +0.7 | 1.13 (0.66-1.91) at 10%, 0.94 at 1%; finish +0.3; 5653 teams, 18 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | +0.0 | +3.5 | -3.5 | +0.9 | 1.05 (0.91-1.20) at 10%, 1.29 at 1%; finish +1.3; 27615 teams, 22 slates | no lean |
| turn 2/3: fallers vs trust | LEAN for | +2.9 | +0.7 (23%) | +2.2 (77%) | +1.9 | 1.24 (1.05-1.48) at 10%, 1.36 at 1%; finish -3.8; 19640 teams, 22 slates | RULE for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +7.8 | +9.0 (115%) | -1.2 (-15%) | +6.2 | 1.56 (1.31-1.83) at 10%, 2.26 at 1%; finish -6.0; 6418 teams, 22 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | RULE for | +1.5 | +1.6 (111%) | -0.2 (-11%) | - (holding) | 1.02 (0.90-1.16) at 10%, 1.07 at 1%; finish +0.8; 152131 teams, 22 slates | no lean |
| stack: Same-position teammates | RULE against | -3.5 | -7.3 (207%) | +3.8 (-107%) | - (holding) | 0.74 (0.65-0.85) at 10%, 0.82 at 1%; finish +3.9; 83189 teams, 22 slates | RULE against |
| stack: Same-position teammates, spread 5+ | RULE against | -1.4 | -3.2 (224%) | +1.8 (-124%) | - (holding) | 0.82 (0.72-0.92) at 10%, 0.65 at 1%; finish +1.7; 34976 teams, 19 slates | RULE against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 13 | 202 | -0.4 | -1 | -55 |
| the swap board, near-ties least drafted first (leverage) | 13 | 202 | -0.5 | +1 | -135 |
| the swap board, near-ties most drafted first (spread) | 13 | 202 | -0.3 | +1 | -73 |

Leverage against spread: the leverage board's swaps would have made +0 top-10% finishes and $+62 against the spread board's (real minus each, differenced). Leverage put 67% of a night's replayed swaps on one player, spread 53%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.11 (0.96-1.28) at 10%, 1.04 at 1%; finish -1.3; 31240 teams, 18 slates | +1.3 | +1.2 (98%) | +0.0 (2%) | 1.07 (0.92-1.24) at 10%, 0.98 at 1%; finish -0.8; 31239 teams, 18 slates | no lean |
| rounds 1-2 | 3.41 (2.71-4.05) at 10%, 10.75 at 1%; finish -15.3; 743 teams, 3 slates | +14.9 | +12.7 (85%) | +2.2 (15%) | 3.19 (2.64-3.99) at 10%, 9.37 at 1%; finish -14.8; 743 teams, 3 slates | LEAN for |
| rounds 3-4 | 1.03 (0.84-1.26) at 10%, 0.90 at 1%; finish +0.5; 9032 teams, 10 slates | -0.5 | +0.6 (-119%) | -1.2 (219%) | 1.00 (0.82-1.24) at 10%, 0.83 at 1%; finish +0.7; 9029 teams, 10 slates | no lean |
| rounds 5-6 or undrafted | 1.11 (0.95-1.29) at 10%, 1.03 at 1%; finish -1.8; 21636 teams, 15 slates | +1.7 | +1.1 (64%) | +0.6 (36%) | 1.08 (0.92-1.28) at 10%, 0.99 at 1%; finish -1.2; 21636 teams, 15 slates | no lean |

## 3c. Splits for Monday: teammates and takes by source

Each with the price-split check (section 3b). Lift: top-10% against same-contest, same-price teams.

### Teammates, by the rounds paid for them

A: teams with that teammate pair; B: teams with no two teammates at all (so same- and different-position pairs face the same comparison).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pair | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| Same position, both rounds 1-3 | 1.07 (0.69-1.47) at 10%, 1.05 at 1%; finish -3.5; 9974 teams, 14 slates | +2.5 | -2.0 (-80%) | +4.5 (180%) | 1.06 (0.69-1.46) at 10%, 1.10 at 1%; finish -3.2; 9973 teams, 14 slates | no lean |
| Same position, one in rounds 1-3 and one in 4-6 | 0.89 (0.80-0.97) at 10%, 0.89 at 1%; finish +1.6; 38345 teams, 20 slates | -1.5 | -5.2 (351%) | +3.7 (-251%) | 0.80 (0.71-0.88) at 10%, 0.73 at 1%; finish +2.8; 38288 teams, 20 slates | RULE against |
| Same position, both rounds 4-6 | 1.15 (1.03-1.27) at 10%, 1.38 at 1%; finish -3.4; 18003 teams, 20 slates | +2.9 | -0.3 (-10%) | +3.2 (110%) | 1.13 (1.02-1.25) at 10%, 1.37 at 1%; finish -3.1; 18002 teams, 20 slates | LEAN for |
| Different-position teammates (any rounds) | 1.15 (1.07-1.23) at 10%, 1.31 at 1%; finish -1.9; 157892 teams, 20 slates | +1.7 | -0.5 (-30%) | +2.2 (130%) | 1.00 (0.87-1.17) at 10%, 1.06 at 1%; finish +0.6; 130156 teams, 20 slates | no lean |

### Your takes by source (takes_history.csv)

A: teams holding the player you put first; B: the button's first, in the take's window (field and mine). Field drafted%: the share of that window's pods that took each. Points: the takes file's average gain per take (yours).

| Source | Window | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pick | From the other picks | Lift matched on the other picks' price | Verdict that survives | Takes, points per take | Field drafted%: yours / the button's | Yours the more drafted |
|---|---|---|---|---|---|---|---|---|---|---|
| ETR | PM | 0.88 (0.69-1.09) at 10%, 0.69 at 1%; finish +1.4; 33283 teams, 10 slates | -1.6 | -2.4 (154%) | +0.8 (-54%) | 0.93 (0.71-1.16) at 10%, 0.74 at 1%; finish +0.7; 33277 teams, 10 slates | no lean | 31, -0.7 | 54% / 60% | 26% |
| ETR | both | 0.88 (0.69-1.09) at 10%, 0.69 at 1%; finish +1.4; 33283 teams, 10 slates | -1.6 | -2.4 (154%) | +0.8 (-54%) | 0.93 (0.71-1.16) at 10%, 0.74 at 1%; finish +0.7; 33277 teams, 10 slates | no lean | 31, -0.7 | 54% / 60% | 26% |
| Bagel | PM | 1.08 (0.87-1.42) at 10%, 1.18 at 1%; finish +0.3; 59643 teams, 11 slates | -0.4 | +0.6 | -1.0 | 1.10 (0.92-1.36) at 10%, 1.19 at 1%; finish +0.2; 59637 teams, 11 slates | no lean | 38, +1.6 | 81% / 81% | 58% |
| Bagel | both | 1.08 (0.87-1.42) at 10%, 1.18 at 1%; finish +0.3; 59643 teams, 11 slates | -0.4 | +0.6 | -1.0 | 1.10 (0.92-1.36) at 10%, 1.19 at 1%; finish +0.2; 59637 teams, 11 slates | no lean | 38, +1.6 | 81% / 81% | 58% |
| Bagel+ETR | PM | 1.05 (0.87-1.27) at 10%, 1.07 at 1%; finish +0.2; 149084 teams, 11 slates | +0.3 | +0.6 | -0.3 | 1.06 (0.88-1.28) at 10%, 1.10 at 1%; finish -0.0; 149084 teams, 11 slates | no lean | 107, +2.2 | 71% / 69% | 50% |
| Bagel+ETR | both | 1.05 (0.87-1.27) at 10%, 1.07 at 1%; finish +0.2; 149084 teams, 11 slates | +0.3 | +0.6 | -0.3 | 1.06 (0.88-1.28) at 10%, 1.10 at 1%; finish -0.0; 149084 teams, 11 slates | no lean | 107, +2.2 | 71% / 69% | 50% |
| NEWS | AM | 0.99 (0.86-1.15) at 10%, 1.01 at 1%; finish +0.0; 221313 teams, 19 slates | -0.1 | -1.3 | +1.2 | 0.98 (0.86-1.14) at 10%, 0.99 at 1%; finish +0.3; 221312 teams, 19 slates | no lean | 276, -1.0 | 80% / 77% | 51% |
| NEWS | PM | 0.90 (0.69-1.15) at 10%, 0.82 at 1%; finish +0.1; 137177 teams, 16 slates | -0.6 | -0.7 (115%) | +0.1 (-15%) | 0.87 (0.67-1.12) at 10%, 0.79 at 1%; finish +0.2; 137167 teams, 16 slates | no lean | 107, -1.2 | 71% / 75% | 35% |
| NEWS | both | 0.96 (0.85-1.09) at 10%, 0.94 at 1%; finish +0.0; 358512 teams, 22 slates | -0.3 | -1.1 | +0.8 | 0.94 (0.83-1.08) at 10%, 0.92 at 1%; finish +0.2; 358507 teams, 22 slates | no lean | 383, -1.0 | 77% / 77% | 46% |
| OTHER | AM | 1.08 (0.92-1.29) at 10%, 1.07 at 1%; finish +0.4; 19370 teams, 3 slates | +0.2 | +0.5 | -0.3 | 1.09 (0.94-1.28) at 10%, 1.09 at 1%; finish +0.4; 19370 teams, 3 slates | LEAN for | 43, +3.2 | 49% / 49% | 49% |
| OTHER | PM | 0.80 (0.44-1.40) at 10%, 0.63 at 1%; finish +0.3; 33611 teams, 10 slates | +0.0 | -2.7 | +2.8 | 0.78 (0.44-1.31) at 10%, 0.61 at 1%; finish +1.3; 33613 teams, 10 slates | no lean | 64, -0.9 | 61% / 65% | 36% |
| OTHER | both | 0.91 (0.64-1.25) at 10%, 0.80 at 1%; finish +0.4; 52981 teams, 11 slates | +0.0 | -1.6 | +1.6 | 0.90 (0.63-1.22) at 10%, 0.79 at 1%; finish +1.0; 52983 teams, 11 slates | no lean | 107, +0.8 | 56% / 59% | 41% |
| all | AM | 1.00 (0.88-1.15) at 10%, 1.02 at 1%; finish +0.1; 240683 teams, 19 slates | -0.0 | -1.2 | +1.1 | 0.99 (0.87-1.14) at 10%, 1.00 at 1%; finish +0.3; 240682 teams, 19 slates | no lean | 319, -0.4 | 76% / 74% | 50% |
| all | PM | 0.97 (0.86-1.10) at 10%, 0.93 at 1%; finish +0.3; 412859 teams, 22 slates | -0.3 | -0.5 | +0.1 | 0.96 (0.85-1.10) at 10%, 0.93 at 1%; finish +0.3; 412860 teams, 22 slates | no lean | 347, +0.3 | 69% / 71% | 41% |
| all | both | 0.98 (0.90-1.09) at 10%, 0.96 at 1%; finish +0.2; 653560 teams, 22 slates | -0.2 | -0.7 | +0.5 | 0.98 (0.90-1.08) at 10%, 0.96 at 1%; finish +0.3; 653560 teams, 22 slates | no lean | 666, -0.1 | 72% / 72% | 46% |

## 3d. Candidate: my AM teams against my PM teams (for the Monday section; not a proposal)

A = my AM teams, B = my PM teams, inside the same contest and price group. Raw: each window's top-10% rate over the field's 10%. Then what differs, per team.

| | Teams | Raw top-10% | VALUE picks | PRICEY picks | Tagged picks | Projected drafted% of picks | Field sharing 4+ of 6 | Teams with an exact duplicate | Price | Points over price | Swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AM | 538 | 1.38 | 1.77 | 0.66 | 0.36 | 92% | 0.99% | 19% | 220.1 | +3.7 | 0.44 |
| PM | 1228 | 1.29 | 1.58 | 0.60 | 0.13 | 90% | 1.20% | 22% | 218.1 | +7.2 | 0.09 |

Inside the same contest and price group, AM against PM: 1.15 (0.85-1.52) at 10%, 1.25 at 1%; finish +1.8; 536 teams, 17 slates (five price groups); 1.00 (0.75-1.30) at 10%, 1.71 at 1%; finish +2.8; 505 teams, 17 slates (ten).

## 3e. Candidates for 11-16 (asked 2026-11-09; not proposals)

### 1. Same-position teammates: source, examples, and starter/backup instead

Position: Underdog's own position on the slate (the record's `pos`), grouped G (PG, SG, G), F (SF, PF, F), C. Underdog scores everyone as flex, so position matters here only as a stand-in for sharing minutes and touches. Five early/late same-position pairs on 2026-11-13's rosters:

- Dyson Daniels (SG, round 3) + Nickeil Alexander-Walker (SG, round 5), ATL
- Kevin Durant (PF, round 3) + Amen Thompson (SF, round 5), HOU
- Donovan Mitchell (SG, round 2) + James Harden (PG, round 4), CLE
- Kevin Durant (PF, round 3) + Jabari Smith Jr. (PF, round 6), HOU
- Dyson Daniels (SG, round 3) + CJ McCollum (PG, round 6), ATL

Starter and direct backup instead of position: the starter averages 28+ minutes; his backup scores 4+ more points a game when the starter sits. Both from the morning file as it stood at that night's lock (the mirror's history: games through the night before, nothing later). The with/without splits start in the morning file around 10-29, so earlier nights have no pairs. Against teams with no two teammates:

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Same position, early + late (the approved card row) | 0.89 (0.80-0.97) at 10%, 0.89 at 1%; finish +1.6; 38345 teams, 20 slates | -1.5 | -5.2 (351%) | +3.7 (-251%) | - (holding) | 0.80 (0.71-0.88) at 10%, 0.73 at 1%; finish +2.8; 38288 teams, 20 slates | RULE against |
| Starter + his backup, any rounds | 0.79 (0.53-1.05) at 10%, 0.76 at 1%; finish +4.5; 20359 teams, 12 slates | -3.8 | -7.0 (181%) | +3.1 (-81%) | - (holding) | 0.75 (0.49-1.03) at 10%, 0.52 at 1%; finish +5.0; 20346 teams, 12 slates | LEAN against |
| Starter early (rounds 1-3) + his backup late (rounds 4-6) | 0.71 (0.51-0.94) at 10%, 0.41 at 1%; finish +4.2; 8007 teams, 11 slates | -3.8 | -4.5 (118%) | +0.7 (-18%) | - (holding) | 0.66 (0.47-0.90) at 10%, 0.35 at 1%; finish +5.0; 8008 teams, 11 slates | RULE against |

### 2. Fallers: the definitions behind card-fallers

Ranks are the night's closing-ADP order. 6-drafter pods (4-drafter in brackets):
- **1/2 turn** (picks 6-7, or 5 and 8 [3-4, or 3 and 6]): your first player is a top-4 [top-2] ADP rank and your second is ranked 5-8 [3-6]. In the draft room: a top-4 [top-2] player still there at your turn pick; take him.
- **2/3 turn** (picks 12-13, or 11 and 14 [8-9, or 7 and 10]), for the 1.01 and 1.02 drafters: your second player is ranked 9th or better [5th or better], 3+ ranks ahead of your turn pick; take him.
Measured against same-contest, same-price teams that took the ADP-order pair at that turn (the trusting teams); the price-split check is in 3b. Fallers elsewhere in the draft: part 4 below.

### 3. Exposure, not order: T3 VALUE and T4 PRICEY

Against same-contest, same-price teams without (at each team's draft window).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| 2+ T3 VALUE players | 1.59 (1.19-1.89) at 10%, 1.92 at 1%; finish -9.7; 12602 teams, 14 slates | +9.8 | +10.1 (104%) | -0.4 (-4%) | - (holding) | 1.60 (1.19-1.92) at 10%, 1.95 at 1%; finish -9.7; 12602 teams, 14 slates | RULE for |
| 1+ T3 VALUE player | 1.09 (0.89-1.32) at 10%, 1.06 at 1%; finish -2.7; 96120 teams, 19 slates | +2.9 | +3.1 (108%) | -0.2 (-8%) | - (holding) | 0.99 (0.82-1.18) at 10%, 1.00 at 1%; finish -1.3; 96115 teams, 19 slates | no lean |
| A T4 PRICEY player | 0.79 (0.62-0.97) at 10%, 0.60 at 1%; finish +3.2; 21670 teams, 8 slates | -3.0 | -5.2 (175%) | +2.2 (-75%) | - (holding) | 0.75 (0.60-0.93) at 10%, 0.56 at 1%; finish +3.6; 21670 teams, 8 slates | LEAN against |

### 4. Fallers in every round

A team's k-th player by the ADP it paid stands for its round-k pick (pick order isn't public, so this is a lower bound on the slide). A faller was paid an ADP 3+ picks before that round's first pick (round 3 on 6 drafters: ADP 10 or better). Explained: tagged at the team's window, or his tag changed between Lock AM and lock. A: teams with that faller in round k; B: teams whose round-k player wasn't a faller.

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Round 1, nothing explains it | none | - | - | - |
| Round 1, explained | none | - | - | - |
| Round 2, nothing explains it | 0.84 (0.00-2.90) at 10%, 8.63 at 1%; finish +4.3; 13 teams, 5 slates | -3.8 | +2.4 (-64%) | -6.2 (164%) | +4.8 | 0.82 (0.00-3.05) at 10%, 8.38 at 1%; finish +4.5; 13 teams, 5 slates | not enough |
| Round 2, explained (tag or news) | 5.48 at 10%, 0.00 at 1%; finish -36.6; 1 teams, 1 slates | +49.6 | +13.9 (28%) | +35.7 (72%) | +23.1 | 7.37 at 10%, 0.00 at 1%; finish -41.7; 1 teams, 1 slates | not enough |
| Round 3, nothing explains it | 1.28 (1.01-1.68) at 10%, 2.27 at 1%; finish -6.5; 389 teams, 18 slates | +2.9 | +1.8 (64%) | +1.1 (36%) | +6.8 | 1.53 (1.21-1.94) at 10%, 2.79 at 1%; finish -8.3; 389 teams, 18 slates | RULE for |
| Round 3, explained (tag or news) | 1.88 (1.20-2.73) at 10%, 2.43 at 1%; finish -14.4; 141 teams, 5 slates | +15.1 | +14.1 (93%) | +1.0 (7%) | +19.0 | 2.62 (1.86-3.17) at 10%, 3.72 at 1%; finish -19.7; 141 teams, 5 slates | LEAN for |
| Round 4, nothing explains it | 1.50 (1.07-1.88) at 10%, 1.83 at 1%; finish -6.8; 1538 teams, 22 slates | +4.9 | +1.6 (33%) | +3.2 (67%) | +4.2 | 1.57 (1.18-1.90) at 10%, 1.96 at 1%; finish -7.6; 1538 teams, 22 slates | LEAN for |
| Round 4, explained (tag or news) | 1.13 (0.56-1.57) at 10%, 0.00 at 1%; finish -4.2; 42 teams, 5 slates | +0.4 | -1.9 | +2.3 | +0.9 | 1.15 (0.56-1.62) at 10%, 0.00 at 1%; finish -4.0; 42 teams, 5 slates | not enough |
| Round 5, nothing explains it | 1.83 (1.52-2.11) at 10%, 3.07 at 1%; finish -8.9; 3797 teams, 21 slates | +7.8 | +2.3 (30%) | +5.4 (70%) | +2.3 | 1.86 (1.55-2.14) at 10%, 3.19 at 1%; finish -9.1; 3797 teams, 21 slates | RULE for |
| Round 5, explained (tag or news) | 2.21 (1.35-3.10) at 10%, 2.79 at 1%; finish -15.5; 171 teams, 6 slates | +11.7 | +10.5 (90%) | +1.1 (10%) | +9.7 | 2.13 (1.39-2.89) at 10%, 2.59 at 1%; finish -14.5; 171 teams, 6 slates | RULE for |
| Round 6, nothing explains it | 1.00 (0.84-1.18) at 10%, 1.06 at 1%; finish +0.5; 5690 teams, 22 slates | -0.8 | -4.4 (576%) | +3.7 (-476%) | -1.3 | 1.13 (0.98-1.28) at 10%, 1.25 at 1%; finish -1.3; 5690 teams, 22 slates | LEAN for |
| Round 6, explained (tag or news) | 1.83 (1.27-1.84) at 10%, 1.19 at 1%; finish -12.1; 187 teams, 3 slates | +10.2 | +2.8 (27%) | +7.4 (73%) | +6.6 | 1.74 (1.32-1.75) at 10%, 1.16 at 1%; finish -11.9; 187 teams, 3 slates | LEAN for |

### 5. The original rules (kept-*), asked 2026-11-11

Each tier's kept rule is the Tiers button's order there. A: teams holding the button's first of a decision pair (ADP within 4, same tier) and not its second; B: the reverse. Only pairs with the same flag and no tag on either, so the order is the rule's steps, not VALUE first / PRICEY last or a Questionable push (those have their own rows).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| AM T1: ADP, Boom deciding within 2 picks | 2.05 (1.45-2.96) at 10%, 2.64 at 1%; finish -8.3; 55865 teams, 18 slates | +8.6 | +7.4 (87%) | +1.2 (13%) | +8.0 | 2.10 (1.47-3.12) at 10%, 2.62 at 1%; finish -9.1; 55858 teams, 18 slates | RULE for |
| PM T1: ETR | 1.04 (0.89-1.24) at 10%, 1.08 at 1%; finish -0.8; 133396 teams, 22 slates | +1.0 | +1.0 (100%) | +0.0 (0%) | +2.4 | 1.11 (0.92-1.36) at 10%, 1.15 at 1%; finish -1.8; 133401 teams, 22 slates | no lean |
| AM T2: ADP straight | 0.96 (0.86-1.08) at 10%, 1.02 at 1%; finish +0.3; 316663 teams, 19 slates | -0.4 | +1.2 | -1.6 | +2.1 | 0.99 (0.89-1.10) at 10%, 1.06 at 1%; finish -0.1; 316656 teams, 19 slates | no lean |
| AM T3/T4: Proj, ADP deciding within 3 points | 0.90 (0.78-1.07) at 10%, 0.82 at 1%; finish +1.7; 135940 teams, 19 slates | -1.4 | -0.8 (60%) | -0.6 (40%) | +0.8 | 0.94 (0.80-1.13) at 10%, 0.84 at 1%; finish +1.0; 135939 teams, 19 slates | no lean |
| PM T3: ETR, ties to ADP then Boom | 1.09 (0.95-1.23) at 10%, 0.92 at 1%; finish -2.5; 207209 teams, 21 slates | +2.5 | +3.0 (122%) | -0.5 (-22%) | +3.0 | 1.12 (0.97-1.28) at 10%, 0.96 at 1%; finish -3.0; 207207 teams, 21 slates | LEAN for |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.68 (0.57-0.85) at 10%, 0.45 at 1%; finish +2.4; 31269 teams, 22 slates | 1.54 (0.69-2.54) at 10%, 0.00 at 1%; finish -3.3; 135 teams, 19 slates |
| 1/2 | fallers vs trust | 1.22 (0.93-1.67) at 10%, 1.48 at 1%; finish -2.0; 47230 teams, 22 slates | 1.33 (0.81-2.20) at 10%, 2.37 at 1%; finish -3.5; 231 teams, 22 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.14 (0.69-1.94) at 10%, 0.90 at 1%; finish -0.3; 5656 teams, 18 slates | 1.51 (0.49-3.43) at 10%, 0.00 at 1%; finish -4.5; 63 teams, 11 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 1.39 (0.82-1.96) at 10%, 2.05 at 1%; finish -2.7; 15942 teams, 17 slates | 0.65 (0.00-1.54) at 10%, 0.00 at 1%; finish -5.2; 78 teams, 14 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.67 (0.33-1.16) at 10%, 0.36 at 1%; finish +2.7; 12518 teams, 18 slates | 0.95 (0.00-2.19) at 10%, 0.00 at 1%; finish -6.2; 57 teams, 16 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.28 (0.92-1.64) at 10%, 1.34 at 1%; finish -2.2; 12394 teams, 18 slates | 1.72 (1.00-2.61) at 10%, 2.21 at 1%; finish -8.6; 68 teams, 16 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 0.94 (0.35-1.85) at 10%, 0.74 at 1%; finish +0.6; 9389 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -2.2; 34 teams, 13 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 1.01 (0.77-1.24) at 10%, 0.82 at 1%; finish +0.0; 8406 teams, 17 slates | 1.56 (0.72-2.46) at 10%, 0.00 at 1%; finish -5.7; 52 teams, 15 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 1.17 (0.58-1.66) at 10%, 1.84 at 1%; finish -0.3; 7144 teams, 18 slates | 2.18 (1.03-3.25) at 10%, 0.00 at 1%; finish -10.3; 32 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.06 (0.52-1.82) at 10%, 0.81 at 1%; finish +0.8; 4957 teams, 17 slates | 3.46 (1.99-4.79) at 10%, 0.00 at 1%; finish -11.0; 33 teams, 6 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.55 (0.37-0.72) at 10%, 0.14 at 1%; finish +0.2; 4920 teams, 18 slates | 0.41 (0.00-1.92) at 10%, 0.00 at 1%; finish +6.7; 29 teams, 6 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.68 (0.40-1.01) at 10%, 0.33 at 1%; finish -0.3; 3579 teams, 18 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 1.34 (0.72-1.81) at 10%, 1.71 at 1%; finish -3.0; 2146 teams, 18 slates | 0.85 (0.00-1.97) at 10%, 0.00 at 1%; finish -2.0; 13 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.03 (0.68-1.36) at 10%, 0.93 at 1%; finish -0.6; 1942 teams, 18 slates | 1.06 (0.00-3.52) at 10%, 0.00 at 1%; finish -0.4; 14 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 0.76 (0.39-1.38) at 10%, 0.51 at 1%; finish +1.7; 1848 teams, 17 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 1.09 (0.68-1.60) at 10%, 1.40 at 1%; finish -1.0; 1261 teams, 17 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 0.97 (0.33-1.75) at 10%, 0.98 at 1%; finish -3.4; 1181 teams, 18 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.39 (0.28-0.54) at 10%, 0.00 at 1%; finish +2.7; 1116 teams, 18 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.38 (0.26-0.53) at 10%, 0.11 at 1%; finish +9.1; 1082 teams, 18 slates | none |
| 2/3 | a. reach vs trust | 1.07 (0.92-1.24) at 10%, 1.28 at 1%; finish +0.9; 27548 teams, 22 slates | 1.77 (1.19-2.32) at 10%, 1.84 at 1%; finish -8.4; 126 teams, 21 slates |
| 2/3 | fallers vs trust | 1.23 (1.02-1.49) at 10%, 1.32 at 1%; finish -3.7; 19645 teams, 22 slates | 1.76 (1.18-2.38) at 10%, 1.56 at 1%; finish -6.0; 105 teams, 20 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.64 (1.34-1.99) at 10%, 2.18 at 1%; finish -6.9; 6399 teams, 22 slates | 1.95 (1.13-2.68) at 10%, 3.73 at 1%; finish -10.8; 71 teams, 15 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.10 (0.70-1.49) at 10%, 1.08 at 1%; finish +1.6; 3470 teams, 19 slates | 0.25 (0.00-0.44) at 10%, 0.00 at 1%; finish -3.1; 38 teams, 11 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.66 (0.47-0.80) at 10%, 0.21 at 1%; finish +0.8; 4804 teams, 17 slates | 1.03 (0.00-1.84) at 10%, 0.00 at 1%; finish -8.2; 25 teams, 11 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 0.75 (0.33-1.21) at 10%, 0.50 at 1%; finish +9.7; 3877 teams, 17 slates | 1.10 (0.00-2.09) at 10%, 0.00 at 1%; finish +6.7; 23 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 1.30 (0.89-1.69) at 10%, 1.21 at 1%; finish +1.5; 3817 teams, 18 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +12.5; 15 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 1.26 (0.82-1.74) at 10%, 1.57 at 1%; finish -3.6; 3387 teams, 18 slates | 0.64 (0.00-1.84) at 10%, 0.00 at 1%; finish -2.6; 20 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 0.97 (0.53-1.43) at 10%, 1.39 at 1%; finish +8.5; 2838 teams, 18 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +4.8; 17 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 1.22 (0.84-1.58) at 10%, 1.30 at 1%; finish -8.1; 2812 teams, 18 slates | 0.70 (0.00-1.50) at 10%, 2.84 at 1%; finish -0.6; 19 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 0.92 (0.64-1.29) at 10%, 0.59 at 1%; finish -1.8; 2596 teams, 18 slates | 2.75 (0.00-7.22) at 10%, 0.00 at 1%; finish -22.9; 14 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.82 (0.52-1.22) at 10%, 0.72 at 1%; finish -5.2; 2587 teams, 18 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -13.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.55 (1.01-2.19) at 10%, 1.75 at 1%; finish -6.8; 2415 teams, 18 slates | 1.68 (0.61-3.01) at 10%, 3.96 at 1%; finish -2.9; 21 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.17 (0.64-1.84) at 10%, 0.99 at 1%; finish +1.1; 2351 teams, 18 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -4.2; 13 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.84 (0.54-1.17) at 10%, 0.53 at 1%; finish -1.0; 2172 teams, 18 slates | 0.97 (0.00-4.05) at 10%, 0.00 at 1%; finish +1.2; 6 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.54 (0.31-0.80) at 10%, 0.54 at 1%; finish +2.1; 2108 teams, 18 slates | 0.59 (0.00-1.86) at 10%, 0.00 at 1%; finish +4.7; 13 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 0.88 (0.50-1.30) at 10%, 0.70 at 1%; finish +3.2; 1983 teams, 17 slates | 1.06 (0.00-1.69) at 10%, 0.00 at 1%; finish +4.5; 10 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 0.99 (0.55-1.50) at 10%, 0.84 at 1%; finish +4.8; 1970 teams, 18 slates | 3.34 (2.13-3.81) at 10%, 0.00 at 1%; finish -15.6; 13 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.85 (0.55-1.26) at 10%, 0.45 at 1%; finish -5.3; 1946 teams, 18 slates | 2.32 (0.65-4.54) at 10%, 0.00 at 1%; finish -15.4; 11 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 13 | 0.98 (0.72-1.22) at 10%, 0.83 at 1%; finish -3.2; 1861 teams, 18 slates | 1.79 (0.00-3.82) at 10%, 0.00 at 1%; finish -4.8; 12 teams, 6 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 160 | 96% | 96% | -0 |
| AM | T1-T2 | Q TRAP | 26 | 81% | 96% | -15 |
| AM | T1-T2 | VALUE | 8 | 84% | 97% | -13 |
| AM | T3-T4 | PRICEY | 57 | 94% | 96% | -2 |
| AM | T3-T4 | Q TRAP | 2 | 98% | 97% | +1 |
| AM | T3-T4 | VALUE | 104 | 90% | 96% | -6 |
| AM | T5 | PRICEY | 13 | 96% | 59% | +37 |
| AM | T5 | Q FAIR | 279 | 10% | 19% | -9 |
| AM | T5 | VALUE | 386 | 48% | 25% | +23 |
| PM | T1-T2 | PRICEY | 164 | 99% | 99% | -0 |
| PM | T1-T2 | Q TRAP | 19 | 86% | 99% | -13 |
| PM | T1-T2 | VALUE | 13 | 96% | 97% | -1 |
| PM | T3-T4 | PRICEY | 93 | 99% | 99% | +0 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 4 | 90% | 99% | -9 |
| PM | T3-T4 | VALUE | 180 | 97% | 99% | -2 |
| PM | T5 | PRICEY | 15 | 93% | 45% | +48 |
| PM | T5 | Q FAIR | 139 | 8% | 21% | -13 |
| PM | T5 | VALUE | 390 | 67% | 29% | +37 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 50 (of all T5 breakers: PRICEY 12, VALUE 7, unflagged 53).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.18 (1.07-1.31) at 10%, 1.28 at 1%; finish -1.6; 152953 teams, 22 slates | 1.56 (1.33-1.81) at 10%, 1.36 at 1%; finish -7.6; 776 teams, 22 slates |
| Same-position teammates | 0.80 (0.72-0.91) at 10%, 0.87 at 1%; finish +4.1; 87327 teams, 22 slates | 1.31 (1.05-1.69) at 10%, 1.90 at 1%; finish -4.1; 371 teams, 22 slates |
| Same-position teammates, spread 5+ | 0.88 (0.79-0.96) at 10%, 0.78 at 1%; finish +1.2; 34976 teams, 19 slates | 1.49 (1.02-2.04) at 10%, 1.98 at 1%; finish -10.2; 185 teams, 18 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.70 | 1.71 | 1.14 | 0.83 | 0.76 | 1.14 | 1.01 | 0.02 | 0.09 | 0.00 | 2.93 |
| Field | 0.60 | 1.68 | 1.13 | 0.92 | 0.66 | 1.03 | 1.10 | 0.02 | 0.09 | 0.00 | 1.09 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.77 (0.64-0.90) at 10%, 0.80 at 1%; finish +5.4; 61323 teams, 21 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

636 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 251996 | 0.61 | 1.69 | 1.16 | 0.95 | 0.63 | 1.11 | 1.04 | 0.25 | 93% |
| Me | 1820 | 0.62 | 1.71 | 1.33 | 1.06 | 0.60 | 1.63 | 0.61 | 0.33 | 91% |
| Everyone | 396846 | 0.60 | 1.68 | 1.13 | 0.92 | 0.66 | 1.03 | 1.10 | 0.23 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.50 (0.31-0.72) at 10%, 0.26 at 1%; finish +11.3; 8427 teams, 7 slates |
| T1-T2 | AM | 0.65 (0.41-0.89) at 10%, 0.41 at 1%; finish +6.7; 5306 teams, 7 slates |
| T1-T2 | PM | 0.27 (0.11-0.47) at 10%, 0.05 at 1%; finish +19.2; 3121 teams, 3 slates |
| T3-T5 | both | 0.90 (0.77-1.03) at 10%, 1.05 at 1%; finish +2.0; 22740 teams, 15 slates |
| T3-T5 | AM | 0.85 (0.73-0.98) at 10%, 0.98 at 1%; finish +2.8; 11775 teams, 14 slates |
| T3-T5 | PM | 0.94 (0.76-1.15) at 10%, 1.12 at 1%; finish +1.1; 10965 teams, 10 slates |
| not credited | both | 0.78 (0.63-0.92) at 10%, 0.82 at 1%; finish +6.0; 24614 teams, 21 slates |
| not credited | AM | 0.79 (0.66-0.97) at 10%, 0.77 at 1%; finish +5.2; 13271 teams, 18 slates |
| not credited | PM | 0.76 (0.56-0.95) at 10%, 0.89 at 1%; finish +7.0; 11343 teams, 21 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 17 show a lean or rule and 9 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | RULE for | RULE for | 1.46 (1.19-1.78) | keep: points and money agree |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | RULE for | 1.25 (1.11-1.41) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | RULE for | RULE for | 1.26 (1.13-1.39) | candidate: hand to the rankings side with its points cost |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 0.95 (0.73-1.28) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 1.03 (0.83-1.24) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | no lean | 1.07 (0.82-1.37) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 0.97 (0.83-1.15) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | RULE against | LEAN against | 0.86 (0.79-0.96) | watch: money leans against |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | LEAN against | RULE against | 0.89 (0.41-1.01) | candidate: hand to the rankings side with its points cost |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 1.03 (0.82-1.24) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 1.08 (0.92-1.31) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | LEAN for | LEAN for | 1.23 (1.01-1.57) | watch: money leans for |
| pm-t5-beneficiary | adopted | LEAN (listed) | no lean | no lean | 1.01 (0.88-1.19) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | no lean | no lean | 0.96 (0.86-1.08) | drop on points unless money clears its bar |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.59 (1.19-2.15) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.94 (0.74-1.21) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | no lean | no lean | 0.87 (0.41-1.52) | keep on points; money not settled |
| pm-t5-adp-value | adopted | RULE | no lean | no lean | 1.03 (0.93-1.12) | keep on points; money not settled |
| one-tier-cap | adopted | LEAN (both windows) | no lean | no lean | 0.92 (0.79-1.06) | keep on points; money not settled |
| pm-middle-takes | candidate | LEAN (single window) | LEAN against | LEAN against | 0.88 (0.76-1.02) | keep on points; money leans against (watch) |
| pm-t2-other-reads | candidate | LEAN (single window) | RULE for | RULE for | 1.33 (1.07-1.66) | keep: points and money agree |
| am-t5-other-reads | candidate | LEAN against (single window) | no lean | no lean | 1.24 (0.82-1.66) | drop on points unless money clears its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

