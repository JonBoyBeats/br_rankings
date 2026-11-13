# NBA money report (draft)

Written by scripts/nba_money.py (definitions in its docstring), 2026-11-13. Slates 2026-10-20 to 2026-11-12: 23 nights, 70 contests, 377098 teams. The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's (decision_register.csv).

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

Found:

- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.
- 11 contests aren't public (HTTP 401, Underdog's admin promos): nba_fri_main, nba_mon_main, nba_mon_main, nba_sat_main, nba_sun_main, nba_thu_main, nba_thu_main, nba_tue_main, nba_wed_main, nba_wed_main, nba_wed_main.
- Teams are all complete: every contest's team count equals its entries, no short teams.
- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):
  - 2026-10-24: 2885 swapped-in picks, 433 credited
  - 2026-11-01: 1455 swapped-in picks, 0 credited
- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 priced picks (mostly swaps) get none and sit out the window tests.

## 1. The price baseline

E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price group (quintiles; deciles as the robustness check). 349592 of 377098 teams priced (each pod size's first night, 10-20 and 10-21, has no earlier slate).

**Ten random teams**

| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |
|---|---|---|---|---|---|---|---|
| 2026-10-22 | Thursday Night Hoops | 4 | PM | 4 | 216.7 | 144.7 | 3.3, 7.5, 8.1, 14.9, 20.2, 21.0 |
| 2026-10-23 | Fast Break Friday | 6 | PM | 2 | 236.8 | 214.1 | 3.0, 10.3, 14.1, 19.0, 31.6, 34.8 |
| 2026-10-30 | Buzzer Beater | 6 | AM | 5 | 240.5 | 239.5 | 1.3, 8.0, 10.7, 25.9, 33.0, 15.5 (swap) |
| 2026-10-30 | Fast Break Friday | 6 | PM | 3 | 223.0 | 203.5 | 4.1, 8.1, 17.0, 24.6, 26.3, 31.0 |
| 2026-11-04 | Hump Day Hoops | 6 | AM | 3 | 223.7 | 261.6 | 4.1, 7.8, 17.4, 23.8, 27.0, 32.3 |
| 2026-11-07 | Saturday Slam | 6 | PM | 2 | 221.3 | 230.3 | 6.5, 8.4, 17.1, 29.7, 34.6, 15.8 (swap) |
| 2026-11-09 | Monday Night Hoops | 6 | PM | 4 | 220.9 | 247.4 | 3.4, 11.7, 14.6, 20.1, 29.0, 31.3 |
| 2026-11-11 | Hump Day Hoops | 6 | AM | 2 | 213.8 | 216.5 | 4.3, 12.1, 15.1, 20.4, 29.1, 32.5 |
| 2026-11-12 | Thursday Night Hoops | 6 | PM | 2 | 216.3 | 279.2 | 2.1, 13.5, 18.6, 21.3, 26.3, 32.2 |
| 2026-11-12 | Thursday Night Hoops | 6 | AM | 4 | 219.6 | 162.3 | 1.1, 12.7, 16.9, 24.3, 27.3, 35.1 |

**Bias checks**: points over price. Whole nights swing with the slate's scoring (-47 to +37), which never matters: teams are compared only inside a contest.

| Check | Group | Points over price | n |
|---|---|---|---|
| Contest (its mean against its night's) | Buzzer Beater | -0.1 | 10 |
| Contest (its mean against its night's) | Heat Check | -0.4 | 1 |
| Contest (its mean against its night's) | Pick & Roll | -0.4 | 10 |
| Contest (its mean against its night's) | The Alley-oop | +0.4 | 1 |
| Contest (its mean against its night's) | The Crossover | -0.1 | 12 |
| Contest (its mean against its night's) | The Layup Line | -0.4 | 13 |
| Contest (its mean against its night's) | flagships | +0.0 | 21 |
| Pod size (contest mean) | 4 | -9.7 | 9 |
| Pod size (contest mean) | 6 | +0.3 | 59 |
| Price quintile (inside contest; 1 = cheapest) | 1 | +5.7 | 69868 |
| Price quintile (inside contest; 1 = cheapest) | 2 | +1.7 | 69910 |
| Price quintile (inside contest; 1 = cheapest) | 3 | -0.2 | 69930 |
| Price quintile (inside contest; 1 = cheapest) | 4 | -2.2 | 69501 |
| Price quintile (inside contest; 1 = cheapest) | 5 | -5.0 | 70383 |
| Swap on the team (inside contest) | no | +0.9 | 286677 |
| Swap on the team (inside contest) | yes | -4.2 | 62915 |
| Window (inside contest) | AM | -0.5 | 112548 |
| Window (inside contest) | PM | +0.3 | 236441 |

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
| Thursday Night Hoops | 6 | 1 | 80 | 0.00 | 1.00 | 1.00 | 0.94 | 45.9 | 1.75 (40) | 0.25 (40) | $400 | $234 | -42% |
| Buzzer Beater | 6 | 4 | 50 | 2.00 | 1.60 | 1.60 | 1.30 | 44.7 | 5.00 (4) | 1.30 (46) | $150 | $171 | +14% |
| The Layup Line | 6 | 4 | 24 | 0.00 | 1.67 | 1.25 | 1.25 | 49.8 | 2.00 (5) | 1.05 (19) | $120 | $50 | -58% |
| Thursday Night Hoops | 4 | 3 | 180 | 0.56 | 1.56 | 1.61 | 1.56 | 40.9 | 1.03 (39) | 1.77 (141) | $900 | $678 | -25% |
| Sunday Shootaround | 4 | 1 | 40 | 2.50 | 1.00 | 1.25 | 0.87 | 47.9 | 0.00 (10) | 1.67 (30) | $200 | $169 | -16% |
| Tuesday Tip-Off | 4 | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 59.4 | - (0) | 0.00 (4) | $20 | $0 | -100% |
| **all 6-drafter** | 6 | 18 | 1494 | 1.00 | 1.37 | 1.32 (1.17-1.48) | 1.25 | 45.5 | 1.49 (469) | 1.24 (1025) | $7370 | $12168 | +65% |
| **all 4-drafter** | 4 | 5 | 224 | 0.89 | 1.43 | 1.52 (1.12-1.79) | 1.41 | 42.5 | 0.82 (49) | 1.71 (175) | $1120 | $847 | -24% |
| **all** | - | 23 | 1718 | 0.99 | 1.37 | 1.34 (1.20-1.51) | 1.27 | 45.1 | 1.43 (518) | 1.31 (1200) | $8490 | $13015 | +53% |

Dollars: $8490 in fees, $13015 won, +53% ROI over 23 nights (80% range -26% to +157%, resampling nights). Without the best night (2026-10-24, $6357 won on $200) it is -20%: the money so far rests on one top finish, so the tail ratios above are the faster reader.

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

## 3. The register in money

A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10% with its 80% range (resampling slates), at the top 1%, and finish (A's average finish percentile minus B's: negative is better). Find = slates before the last 5, check = the last 5.

Reference for the Mine column: all my teams against same-price field teams run 1.35 (1.21-1.51) at 10%, 0.94 at 1%; finish -5.5; 1664 teams, 21 slates. Mine reads against that, not against 1.00.

| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |
|---|---|---|---|---|---|---|
| **ownership-tiebreak-t5** T5: the less-drafted of two within 2 projected points | 1.23 (1.13-1.33) at 10%, 1.49 at 1%; finish -2.4; 393911 teams, 21 slates | 1.18 (1.07-1.30) at 10%, 1.36 at 1%; finish -1.9; 303302 teams, 16 slates | 1.40 (1.27-1.54) at 10%, 2.12 at 1%; finish -4.1; 90609 teams, 5 slates | 1.70 (1.34-2.19) at 10%, 1.16 at 1%; finish -7.3; 2616 teams, 21 slates | RULE for | RULE for |
|   AM only | 1.21 (1.12-1.31) at 10%, 1.38 at 1%; finish -1.8; 113008 teams, 18 slates | 1.12 (1.04-1.20) at 10%, 1.24 at 1%; finish -0.4; 84265 teams, 13 slates | 1.59 (1.35-1.91) at 10%, 2.00 at 1%; finish -6.1; 28743 teams, 5 slates | 1.26 (1.00-1.55) at 10%, 0.43 at 1%; finish -3.6; 685 teams, 14 slates | RULE for | RULE for |
|   PM only | 1.22 (1.09-1.36) at 10%, 1.51 at 1%; finish -2.6; 280895 teams, 21 slates | 1.21 (1.04-1.37) at 10%, 1.39 at 1%; finish -2.5; 219029 teams, 16 slates | 1.29 (1.08-1.48) at 10%, 2.09 at 1%; finish -2.7; 61866 teams, 5 slates | 1.87 (1.36-2.51) at 10%, 1.49 at 1%; finish -8.5; 1931 teams, 21 slates | RULE for | RULE for |
| **leverage-t2-t4** T2-T4: the less-drafted of two within 2 projected points | 1.51 (1.24-1.92) at 10%, 2.56 at 1%; finish -6.6; 21734 teams, 8 slates | 1.33 (1.14-1.55) at 10%, 2.23 at 1%; finish -4.8; 18263 teams, 6 slates | 3.81 at 10%, 9.03 at 1%; finish -16.5; 3471 teams, 2 slates | 2.44 (1.25-3.37) at 10%, 2.21 at 1%; finish -16.6; 70 teams, 7 slates | RULE for | RULE for |
| **value-up-middle-t5** VALUE over an unflagged player (T3-T5) | 1.26 (1.15-1.38) at 10%, 1.37 at 1%; finish -3.0; 1640522 teams, 21 slates | 1.21 (1.08-1.35) at 10%, 1.33 at 1%; finish -2.0; 1218720 teams, 16 slates | 1.39 (1.19-1.63) at 10%, 1.47 at 1%; finish -5.7; 421802 teams, 5 slates | 1.56 (1.29-1.84) at 10%, 1.08 at 1%; finish -6.7; 12092 teams, 21 slates | RULE for | RULE for |
|   T3 | 1.15 (0.82-1.59) at 10%, 1.24 at 1%; finish -1.7; 152637 teams, 16 slates | 1.24 (0.81-1.78) at 10%, 1.44 at 1%; finish -2.5; 116776 teams, 13 slates | 0.96 (0.52-1.63) at 10%, 0.83 at 1%; finish +0.8; 35861 teams, 3 slates | 1.17 (0.80-1.62) at 10%, 0.00 at 1%; finish -6.8; 1241 teams, 16 slates | no lean | no lean |
|   T4 | 1.23 (1.08-1.38) at 10%, 1.39 at 1%; finish -2.2; 199134 teams, 18 slates | 1.24 (1.08-1.39) at 10%, 1.40 at 1%; finish -2.3; 165507 teams, 14 slates | 1.18 (0.82-1.89) at 10%, 1.31 at 1%; finish -1.9; 33627 teams, 4 slates | 1.78 (1.37-2.35) at 10%, 1.67 at 1%; finish -7.0; 1389 teams, 17 slates | RULE for | RULE for |
|   T5 | 1.31 (1.14-1.47) at 10%, 1.47 at 1%; finish -3.6; 1288570 teams, 21 slates | 1.23 (1.03-1.42) at 10%, 1.36 at 1%; finish -2.1; 936310 teams, 16 slates | 1.54 (1.23-1.96) at 10%, 1.76 at 1%; finish -7.4; 352260 teams, 5 slates | 1.63 (1.28-1.99) at 10%, 1.22 at 1%; finish -7.2; 9462 teams, 20 slates | RULE for | RULE for |
| **pricey-flags** An unflagged player over a PRICEY one (T1-T5) | 1.17 (1.08-1.27) at 10%, 1.29 at 1%; finish -1.3; 931108 teams, 21 slates | 1.19 (1.09-1.29) at 10%, 1.30 at 1%; finish -1.7; 701428 teams, 16 slates | 1.13 (0.89-1.38) at 10%, 1.25 at 1%; finish -0.4; 229680 teams, 5 slates | 1.61 (1.38-1.86) at 10%, 1.49 at 1%; finish -6.4; 5362 teams, 21 slates | RULE for | RULE for |
|   T1 | 1.63 (1.23-2.15) at 10%, 2.47 at 1%; finish -4.1; 124792 teams, 13 slates | 2.04 (1.60-2.65) at 10%, 3.57 at 1%; finish -7.9; 92336 teams, 10 slates | 0.80 (0.40-1.44) at 10%, 0.98 at 1%; finish +6.7; 32456 teams, 3 slates | 2.20 (1.28-3.27) at 10%, 3.06 at 1%; finish -7.8; 602 teams, 12 slates | LEAN for | LEAN for |
|   T2 | 1.17 (1.01-1.36) at 10%, 1.23 at 1%; finish -1.1; 322352 teams, 19 slates | 1.12 (0.94-1.34) at 10%, 1.09 at 1%; finish -1.1; 244719 teams, 14 slates | 1.33 (0.98-1.92) at 10%, 1.77 at 1%; finish -1.2; 77633 teams, 5 slates | 1.59 (1.29-1.98) at 10%, 1.43 at 1%; finish -6.5; 2027 teams, 19 slates | LEAN for | LEAN for |
|   T3 | 1.37 (1.12-1.65) at 10%, 1.54 at 1%; finish -4.8; 242458 teams, 19 slates | 1.37 (1.07-1.72) at 10%, 1.59 at 1%; finish -4.6; 173453 teams, 14 slates | 1.36 (0.98-1.88) at 10%, 1.45 at 1%; finish -5.2; 69005 teams, 5 slates | 2.07 (1.70-2.44) at 10%, 1.67 at 1%; finish -11.1; 1499 teams, 19 slates | RULE for | RULE for |
|   T4 | 0.89 (0.77-1.07) at 10%, 0.81 at 1%; finish +2.2; 241386 teams, 20 slates | 0.92 (0.78-1.11) at 10%, 0.89 at 1%; finish +2.2; 190826 teams, 16 slates | 0.78 (0.59-1.28) at 10%, 0.51 at 1%; finish +2.5; 50560 teams, 4 slates | 1.04 (0.86-1.27) at 10%, 0.66 at 1%; finish -1.1; 1234 teams, 19 slates | LEAN against | LEAN against |
|   T5 | none | none | none | none | not enough | not enough |
| **pm-t4-pricey-last-off** PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button | 1.05 (0.76-1.31) at 10%, 1.14 at 1%; finish -1.2; 63240 teams, 10 slates | 1.11 (0.78-1.41) at 10%, 1.18 at 1%; finish -2.5; 48789 teams, 9 slates | 0.73 at 10%, 0.82 at 1%; finish +3.5; 14451 teams, 1 slates | 1.28 (1.10-1.57) at 10%, 0.74 at 1%; finish -3.5; 241 teams, 7 slates | no lean | no lean |
| **am-t5-button-order** AM T5: the button's first of the pair | 1.14 (1.05-1.23) at 10%, 1.27 at 1%; finish -2.4; 1698557 teams, 18 slates | 1.12 (1.00-1.26) at 10%, 1.22 at 1%; finish -2.2; 1102178 teams, 13 slates | 1.16 (1.08-1.25) at 10%, 1.37 at 1%; finish -2.7; 596379 teams, 5 slates | 1.48 (1.26-1.70) at 10%, 0.59 at 1%; finish -4.9; 7531 teams, 15 slates | RULE for | RULE for |
| **pm-t2-adp-etr2** PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR) | 1.17 (0.93-1.50) at 10%, 1.34 at 1%; finish -2.1; 110424 teams, 17 slates | 1.31 (0.94-1.83) at 10%, 1.74 at 1%; finish -3.9; 76573 teams, 12 slates | 0.93 (0.73-1.24) at 10%, 0.84 at 1%; finish +1.9; 33851 teams, 5 slates | 1.63 (1.13-2.15) at 10%, 2.34 at 1%; finish -10.2; 724 teams, 17 slates | LEAN for | LEAN for |
| **pm-t4-adp-etr2** PM T4: the switch ADP (2: ETR) over the old ETR rule | 0.84 (0.70-1.06) at 10%, 0.74 at 1%; finish +3.0; 62901 teams, 16 slates | 0.84 (0.71-1.05) at 10%, 0.76 at 1%; finish +3.4; 49951 teams, 12 slates | 0.83 (0.44-1.64) at 10%, 0.65 at 1%; finish +1.2; 12950 teams, 4 slates | 0.75 (0.53-1.03) at 10%, 0.00 at 1%; finish -3.6; 253 teams, 14 slates | LEAN against | LEAN against |
| **pm-t5-adp-value** PM T5: ADP with VALUE first over the old ETR (2: less drafted) | 0.72 (0.63-0.84) at 10%, 0.54 at 1%; finish +3.5; 750707 teams, 20 slates | 0.79 (0.67-0.96) at 10%, 0.65 at 1%; finish +2.3; 576465 teams, 15 slates | 0.55 (0.48-0.64) at 10%, 0.30 at 1%; finish +7.2; 174242 teams, 5 slates | 1.39 (1.04-1.76) at 10%, 0.53 at 1%; finish -6.4; 2053 teams, 20 slates | RULE against | RULE against |
| **one-tier-cap** The combined tier's order over the projection tier's, where they differ | 0.88 (0.71-1.06) at 10%, 0.87 at 1%; finish +2.7; 123699 teams, 18 slates | 0.84 (0.64-1.06) at 10%, 0.78 at 1%; finish +2.8; 89970 teams, 13 slates | 0.98 (0.66-1.30) at 10%, 1.13 at 1%; finish +2.2; 33729 teams, 5 slates | 1.42 (0.85-2.09) at 10%, 1.75 at 1%; finish -5.9; 340 teams, 15 slates | LEAN against | LEAN against |
| **am-questionable-no-push** AM: holding a player Questionable at Lock AM | 1.07 (0.81-1.36) at 10%, 1.10 at 1%; finish -0.4; 21206 teams, 15 slates | 0.96 (0.80-1.13) at 10%, 0.98 at 1%; finish +0.3; 11754 teams, 10 slates | 1.24 (0.66-1.99) at 10%, 1.29 at 1%; finish -1.4; 9452 teams, 5 slates | 1.17 (0.80-1.54) at 10%, 1.17 at 1%; finish -0.5; 175 teams, 12 slates | no lean | no lean |
| **pm-questionable-back-two** PM: holding a player Questionable at Lock PM | 1.03 (0.84-1.23) at 10%, 1.00 at 1%; finish -0.8; 26334 teams, 17 slates | 0.98 (0.76-1.20) at 10%, 0.94 at 1%; finish -0.1; 20305 teams, 13 slates | 1.23 (0.79-1.69) at 10%, 1.24 at 1%; finish -2.9; 6029 teams, 4 slates | 1.26 (0.73-1.96) at 10%, 0.00 at 1%; finish -6.1; 143 teams, 14 slates | no lean | no lean |
| **q-tag-pushes** Passing a tagged player for the one the button ranked below him | 1.01 (0.87-1.19) at 10%, 1.10 at 1%; finish +0.6; 243879 teams, 15 slates | 1.06 (0.89-1.25) at 10%, 1.15 at 1%; finish +0.1; 150567 teams, 10 slates | 0.94 (0.75-1.30) at 10%, 1.05 at 1%; finish +1.3; 93312 teams, 5 slates | 1.49 (1.10-2.00) at 10%, 0.92 at 1%; finish -3.2; 949 teams, 14 slates | no lean | no lean |
| **q-tag-raises** Taking a tagged player over one the button ranked above him | 1.01 (0.88-1.18) at 10%, 0.91 at 1%; finish -0.8; 232502 teams, 16 slates | 0.96 (0.80-1.16) at 10%, 0.83 at 1%; finish -0.4; 177549 teams, 11 slates | 1.17 (1.04-1.26) at 10%, 1.16 at 1%; finish -2.4; 54953 teams, 5 slates | 0.99 (0.62-1.59) at 10%, 0.15 at 1%; finish -2.6; 1244 teams, 15 slates | no lean | no lean |
| **q-class-x:SMASH** Holding a SMASH-class tagged player | 0.57 at 10%, 0.08 at 1%; finish +1.4; 1190 teams, 1 slates | none | 0.57 at 10%, 0.08 at 1%; finish +1.4; 1190 teams, 1 slates | 0.67 at 10%, 0.00 at 1%; finish -6.3; 20 teams, 1 slates | not enough | not enough |
| **q-class-x:FAIR** Holding a FAIR-class tagged player | 0.90 (0.77-1.06) at 10%, 0.75 at 1%; finish +0.6; 8053 teams, 16 slates | 0.82 (0.65-1.03) at 10%, 0.63 at 1%; finish +1.3; 5658 teams, 12 slates | 1.09 (0.98-1.27) at 10%, 1.05 at 1%; finish -1.0; 2395 teams, 4 slates | 1.20 (0.74-1.48) at 10%, 0.00 at 1%; finish -6.9; 50 teams, 5 slates | no lean | no lean |
| **q-class-x:TRAP** Holding a TRAP-class tagged player | 0.95 (0.83-1.10) at 10%, 0.92 at 1%; finish +1.5; 34893 teams, 12 slates | 0.88 (0.79-0.98) at 10%, 0.84 at 1%; finish +2.1; 23723 teams, 8 slates | 1.11 (0.80-1.42) at 10%, 1.12 at 1%; finish +0.2; 11170 teams, 4 slates | 1.10 (0.70-1.54) at 10%, 0.44 at 1%; finish -0.4; 218 teams, 12 slates | no lean | no lean |
| **beneficiary-round6:sat** AM: a round-6 pick whose teammate was tagged at Lock AM and sat | 1.01 (0.87-1.20) at 10%, 0.85 at 1%; finish -1.0; 18435 teams, 16 slates | 0.98 (0.80-1.30) at 10%, 0.91 at 1%; finish -0.6; 10454 teams, 11 slates | 1.04 (0.89-1.24) at 10%, 0.77 at 1%; finish -1.6; 7981 teams, 5 slates | 2.04 (1.13-3.03) at 10%, 3.80 at 1%; finish -6.8; 55 teams, 11 slates | no lean | no lean |
| **beneficiary-round6:played** AM: a round-6 pick whose teammate was tagged at Lock AM and played | 1.36 (1.09-1.72) at 10%, 1.55 at 1%; finish -3.5; 10744 teams, 13 slates | 1.49 (1.19-2.10) at 10%, 1.84 at 1%; finish -4.6; 6633 teams, 9 slates | 1.16 (0.58-1.86) at 10%, 1.08 at 1%; finish -1.7; 4111 teams, 4 slates | 1.38 (0.72-2.59) at 10%, 0.00 at 1%; finish -5.3; 31 teams, 7 slates | RULE for | RULE for |
| **pm-t5-beneficiary** PM: a T5 player whose teammate was tagged or out at Lock PM | 1.06 (0.83-1.32) at 10%, 1.37 at 1%; finish +0.3; 52479 teams, 18 slates | 1.19 (0.94-1.51) at 10%, 1.70 at 1%; finish -0.9; 43267 teams, 14 slates | 0.60 (0.47-0.87) at 10%, 0.45 at 1%; finish +6.3; 9212 teams, 4 slates | 2.27 (1.47-3.03) at 10%, 1.12 at 1%; finish -11.6; 294 teams, 15 slates | no lean | no lean |
| **pm-middle-takes** PM T3/T4: your board's first where it differs from ETR's | 1.01 (0.86-1.17) at 10%, 1.09 at 1%; finish -0.6; 243747 teams, 20 slates | 1.00 (0.82-1.19) at 10%, 1.01 at 1%; finish -0.9; 188300 teams, 15 slates | 1.05 (0.87-1.46) at 10%, 1.45 at 1%; finish +0.6; 55447 teams, 5 slates | 1.17 (0.91-1.55) at 10%, 0.43 at 1%; finish -6.5; 1507 teams, 19 slates | no lean | no lean |
| **pm-t2-other-reads** PM T2: your board's first against the button (no tag on either) | 1.00 (0.85-1.17) at 10%, 1.00 at 1%; finish -0.4; 130097 teams, 20 slates | 0.93 (0.78-1.13) at 10%, 0.83 at 1%; finish +0.4; 102468 teams, 15 slates | 1.27 (0.90-1.99) at 10%, 1.69 at 1%; finish -3.3; 27629 teams, 5 slates | 1.24 (0.98-1.51) at 10%, 0.61 at 1%; finish -6.5; 746 teams, 20 slates | no lean | no lean |
| **am-t5-other-reads** AM T5: your board's first against the button (no tag on either) | 1.23 (1.03-1.50) at 10%, 1.49 at 1%; finish -2.1; 141820 teams, 18 slates | 1.24 (0.99-1.55) at 10%, 1.54 at 1%; finish -2.3; 112817 teams, 13 slates | 1.20 (0.97-1.67) at 10%, 1.29 at 1%; finish -1.4; 29003 teams, 5 slates | 0.99 (0.67-1.32) at 10%, 0.00 at 1%; finish +2.2; 923 teams, 15 slates | LEAN for | LEAN for |

## 3b. The price-split check

Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding have no decision pick, so their other picks' price is taken as their price less the average price of the holders' decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.

| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| ownership-tiebreak-t5 | RULE for | +2.4 | +2.4 (101%) | -0.0 (-1%) | -0.4 | 1.16 (1.06-1.28) at 10%, 1.37 at 1%; finish -1.7; 393911 teams, 21 slates | RULE for |
| ownership-tiebreak-t5 AM only | RULE for | +1.9 | +1.6 (87%) | +0.2 (13%) | -2.3 | 1.13 (1.02-1.25) at 10%, 1.23 at 1%; finish -0.9; 113011 teams, 18 slates | LEAN for |
| ownership-tiebreak-t5 PM only | RULE for | +2.5 | +2.7 (106%) | -0.1 (-6%) | +0.2 | 1.18 (1.04-1.32) at 10%, 1.43 at 1%; finish -2.1; 280895 teams, 21 slates | RULE for |
| leverage-t2-t4 | RULE for | +6.6 | +6.6 (100%) | -0.0 (-0%) | -0.4 | 1.68 (1.28-2.33) at 10%, 2.51 at 1%; finish -7.7; 21725 teams, 8 slates | RULE for |
| value-up-middle-t5 | RULE for | +2.7 | +1.7 (64%) | +1.0 (36%) | -0.6 | 1.22 (1.11-1.34) at 10%, 1.33 at 1%; finish -2.4; 1640522 teams, 21 slates | RULE for |
| value-up-middle-t5 T4 | RULE for | +2.5 | +2.0 (80%) | +0.5 (20%) | +2.2 | 1.16 (1.00-1.33) at 10%, 1.29 at 1%; finish -1.6; 199142 teams, 18 slates | LEAN for |
| value-up-middle-t5 T5 | RULE for | +3.1 | +1.5 (49%) | +1.6 (51%) | +0.8 | 1.32 (1.14-1.49) at 10%, 1.44 at 1%; finish -3.7; 1288493 teams, 21 slates | RULE for |
| pricey-flags | RULE for | +1.6 | +2.3 (140%) | -0.7 (-40%) | +2.9 | 1.18 (1.07-1.29) at 10%, 1.28 at 1%; finish -1.5; 931140 teams, 21 slates | RULE for |
| pricey-flags T1 | LEAN for | +2.9 | +4.8 (164%) | -1.9 (-64%) | +8.1 | 1.57 (1.11-2.25) at 10%, 2.38 at 1%; finish -3.8; 124806 teams, 13 slates | LEAN for |
| pricey-flags T2 | LEAN for | +1.7 | +2.3 (138%) | -0.6 (-38%) | +3.1 | 1.18 (1.01-1.39) at 10%, 1.26 at 1%; finish -1.4; 322356 teams, 19 slates | LEAN for |
| pricey-flags T3 | RULE for | +5.0 | +6.2 (123%) | -1.2 (-23%) | +5.5 | 1.37 (1.12-1.65) at 10%, 1.56 at 1%; finish -4.8; 242463 teams, 19 slates | RULE for |
| pricey-flags T4 | LEAN against | -2.0 | -2.7 (140%) | +0.8 (-40%) | -2.8 | 0.91 (0.78-1.10) at 10%, 0.84 at 1%; finish +1.9; 241386 teams, 20 slates | no lean |
| am-t5-button-order | RULE for | +2.1 | +1.1 (54%) | +1.0 (46%) | +0.7 | 1.16 (1.07-1.25) at 10%, 1.28 at 1%; finish -2.6; 1698585 teams, 18 slates | RULE for |
| pm-t2-adp-etr2 | LEAN for | +2.1 | +1.8 (82%) | +0.4 (18%) | +0.7 | 1.13 (0.89-1.48) at 10%, 1.26 at 1%; finish -1.9; 110424 teams, 17 slates | no lean |
| pm-t4-adp-etr2 | LEAN against | -2.8 | -3.5 (126%) | +0.7 (-26%) | -2.3 | 0.84 (0.70-1.05) at 10%, 0.73 at 1%; finish +2.9; 62909 teams, 16 slates | LEAN against |
| pm-t5-adp-value | RULE against | -3.2 | -3.1 (96%) | -0.1 (4%) | -1.1 | 0.75 (0.65-0.87) at 10%, 0.58 at 1%; finish +3.2; 750708 teams, 20 slates | RULE against |
| one-tier-cap | LEAN against | -2.9 | -1.8 (63%) | -1.1 (37%) | +0.1 | 0.87 (0.70-1.06) at 10%, 0.87 at 1%; finish +3.1; 123732 teams, 18 slates | LEAN against |
| beneficiary-round6:played | RULE for | +2.7 | +2.1 (79%) | +0.6 (21%) | - (holding) | 1.27 (1.04-1.63) at 10%, 1.41 at 1%; finish -2.8; 10743 teams, 13 slates | LEAN for |
| am-t5-other-reads | LEAN for | +2.0 | -0.0 (-0%) | +2.0 (100%) | +1.2 | 1.23 (1.03-1.49) at 10%, 1.45 at 1%; finish -2.1; 141855 teams, 18 slates | LEAN for |
| turn 1/2: a. reach vs trust | LEAN against | -0.9 | +0.7 (-75%) | -1.6 (175%) | -0.6 | 0.73 (0.59-0.91) at 10%, 0.52 at 1%; finish +2.4; 29554 teams, 21 slates | LEAN against |
| turn 1/2: fallers vs trust | LEAN for | +2.7 | +0.8 (29%) | +1.9 (71%) | +3.6 | 1.35 (0.99-1.91) at 10%, 1.54 at 1%; finish -3.5; 45389 teams, 21 slates | LEAN for |
| turn 1/2: b. reach toward higher projection vs trust | no lean | +2.0 | +2.6 (131%) | -0.6 (-31%) | +1.5 | 1.35 (0.76-2.26) at 10%, 1.41 at 1%; finish -0.4; 5219 teams, 17 slates | no lean |
| turn 2/3: a. reach vs trust | no lean | +0.6 | +4.0 (698%) | -3.4 (-598%) | +1.4 | 1.08 (0.94-1.22) at 10%, 1.31 at 1%; finish +0.7; 26007 teams, 21 slates | no lean |
| turn 2/3: fallers vs trust | LEAN for | +3.6 | +1.2 (34%) | +2.3 (66%) | +2.5 | 1.26 (1.07-1.51) at 10%, 1.37 at 1%; finish -4.6; 18799 teams, 21 slates | RULE for |
| turn 2/3: b. reach toward higher projection vs trust | RULE for | +8.0 | +9.2 (114%) | -1.2 (-14%) | +6.4 | 1.58 (1.33-1.84) at 10%, 2.28 at 1%; finish -6.3; 6158 teams, 21 slates | RULE for |
| stack: Opposing stars (their team's top 2 by projection, same game) | RULE for | +1.4 | +1.2 (85%) | +0.2 (15%) | - (holding) | 1.00 (0.88-1.14) at 10%, 1.05 at 1%; finish +0.5; 142163 teams, 21 slates | no lean |
| stack: Same-position teammates | RULE against | -3.6 | -7.8 (213%) | +4.1 (-113%) | - (holding) | 0.74 (0.65-0.85) at 10%, 0.82 at 1%; finish +4.1; 80793 teams, 21 slates | RULE against |
| stack: Same-position teammates, spread 5+ | LEAN against | -1.4 | -3.6 (254%) | +2.2 (-154%) | - (holding) | 0.82 (0.72-0.93) at 10%, 0.64 at 1%; finish +1.8; 33295 teams, 18 slates | RULE against |

### f. Swaps, replayed in money (my credited swaps)

Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. Nights left uncredited on purpose (2026-11-01) are out.

| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |
|---|---|---|---|---|---|
| my last saved board order's pick (is the app shuffle worth it?) | 13 | 202 | -0.4 | -1 | -55 |
| the swap board, near-ties least drafted first (leverage) | 13 | 202 | -0.6 | +1 | -135 |
| the swap board, near-ties most drafted first (spread) | 13 | 202 | -0.3 | +1 | -73 |

Leverage against spread: the leverage board's swaps would have made +0 top-10% finishes and $+62 against the spread board's (real minus each, differenced). Leverage put 68% of a night's replayed swaps on one player, spread 53%.

### The knowable round-6 rule

AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.

| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| any round | 1.07 (0.92-1.24) at 10%, 1.01 at 1%; finish -1.0; 27733 teams, 17 slates | +0.9 | +0.1 (7%) | +0.8 (93%) | 1.01 (0.88-1.17) at 10%, 0.91 at 1%; finish -0.2; 27732 teams, 17 slates | no lean |
| rounds 1-2 | 3.41 (2.71-4.05) at 10%, 10.75 at 1%; finish -15.3; 743 teams, 3 slates | +14.9 | +12.7 (85%) | +2.2 (15%) | 3.19 (2.64-3.99) at 10%, 9.37 at 1%; finish -14.8; 743 teams, 3 slates | LEAN for |
| rounds 3-4 | 1.03 (0.84-1.26) at 10%, 0.90 at 1%; finish +0.5; 9032 teams, 10 slates | -0.5 | +0.6 (-119%) | -1.2 (219%) | 1.00 (0.82-1.24) at 10%, 0.83 at 1%; finish +0.7; 9029 teams, 10 slates | no lean |
| rounds 5-6 or undrafted | 1.05 (0.89-1.24) at 10%, 0.97 at 1%; finish -1.3; 18129 teams, 14 slates | +1.2 | -0.7 (-63%) | +1.9 (163%) | 0.99 (0.87-1.16) at 10%, 0.89 at 1%; finish -0.5; 18129 teams, 14 slates | no lean |

## 3c. Splits for Monday: teammates and takes by source

Each with the price-split check (section 3b). Lift: top-10% against same-contest, same-price teams.

### Teammates, by the rounds paid for them

A: teams with that teammate pair; B: teams with no two teammates at all (so same- and different-position pairs face the same comparison).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pair | From the other picks | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|
| Same position, both rounds 1-3 | 1.07 (0.70-1.48) at 10%, 1.05 at 1%; finish -3.5; 9973 teams, 13 slates | +2.5 | -2.0 (-80%) | +4.5 (180%) | 1.06 (0.69-1.47) at 10%, 1.10 at 1%; finish -3.2; 9972 teams, 13 slates | no lean |
| Same position, one in rounds 1-3 and one in 4-6 | 0.91 (0.81-0.99) at 10%, 0.94 at 1%; finish +1.6; 36677 teams, 19 slates | -1.5 | -5.6 (374%) | +4.1 (-274%) | 0.81 (0.72-0.90) at 10%, 0.75 at 1%; finish +2.9; 36620 teams, 19 slates | RULE against |
| Same position, both rounds 4-6 | 1.17 (1.04-1.30) at 10%, 1.37 at 1%; finish -3.4; 17236 teams, 19 slates | +2.9 | -1.0 (-36%) | +3.9 (136%) | 1.14 (1.02-1.27) at 10%, 1.35 at 1%; finish -3.1; 17235 teams, 19 slates | LEAN for |
| Different-position teammates (any rounds) | 1.16 (1.08-1.24) at 10%, 1.36 at 1%; finish -1.9; 148658 teams, 19 slates | +1.7 | -1.2 (-71%) | +2.9 (171%) | 1.01 (0.87-1.19) at 10%, 1.09 at 1%; finish +0.4; 120926 teams, 19 slates | no lean |

### Your takes by source (takes_history.csv)

A: teams holding the player you put first; B: the button's first, in the take's window (field and mine). Field drafted%: the share of that window's pods that took each. Points: the takes file's average gain per take (yours).

| Source | Window | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the pick | From the other picks | Lift matched on the other picks' price | Verdict that survives | Takes, points per take | Field drafted%: yours / the button's | Yours the more drafted |
|---|---|---|---|---|---|---|---|---|---|---|
| ETR | PM | 1.18 (0.84-1.63) at 10%, 1.30 at 1%; finish -1.8; 59788 teams, 8 slates | +1.3 | +1.5 (116%) | -0.2 (-16%) | 1.22 (0.88-1.67) at 10%, 1.36 at 1%; finish -2.5; 59783 teams, 8 slates | no lean | 125, +1.1 | 23% / 36% | 23% |
| ETR | both | 1.18 (0.84-1.63) at 10%, 1.30 at 1%; finish -1.8; 59788 teams, 8 slates | +1.3 | +1.5 (116%) | -0.2 (-16%) | 1.22 (0.88-1.67) at 10%, 1.36 at 1%; finish -2.5; 59783 teams, 8 slates | no lean | 125, +1.1 | 23% / 36% | 23% |
| Bagel | PM | 0.97 (0.83-1.16) at 10%, 1.01 at 1%; finish +0.7; 125460 teams, 11 slates | -0.7 | -0.7 (96%) | -0.0 (4%) | 0.97 (0.83-1.17) at 10%, 0.99 at 1%; finish +0.7; 125457 teams, 11 slates | no lean | 135, -2.7 | 46% / 44% | 50% |
| Bagel | both | 0.97 (0.83-1.16) at 10%, 1.01 at 1%; finish +0.7; 125460 teams, 11 slates | -0.7 | -0.7 (96%) | -0.0 (4%) | 0.97 (0.83-1.17) at 10%, 0.99 at 1%; finish +0.7; 125457 teams, 11 slates | no lean | 135, -2.7 | 46% / 44% | 50% |
| Bagel+ETR | PM | 1.02 (0.85-1.27) at 10%, 0.99 at 1%; finish -0.1; 187659 teams, 10 slates | +0.3 | +0.4 | -0.1 | 1.05 (0.88-1.31) at 10%, 1.04 at 1%; finish -0.5; 187654 teams, 10 slates | no lean | 222, +0.9 | 41% / 50% | 36% |
| Bagel+ETR | both | 1.02 (0.85-1.27) at 10%, 0.99 at 1%; finish -0.1; 187659 teams, 10 slates | +0.3 | +0.4 | -0.1 | 1.05 (0.88-1.31) at 10%, 1.04 at 1%; finish -0.5; 187654 teams, 10 slates | no lean | 222, +0.9 | 41% / 50% | 36% |
| NEWS | AM | 1.05 (0.93-1.20) at 10%, 1.08 at 1%; finish -0.7; 346210 teams, 18 slates | +0.5 | -1.1 | +1.5 | 1.08 (0.96-1.24) at 10%, 1.13 at 1%; finish -1.1; 346215 teams, 18 slates | no lean | 831, -1.0 | 36% / 48% | 33% |
| NEWS | PM | 0.89 (0.77-0.99) at 10%, 0.83 at 1%; finish +0.8; 232371 teams, 20 slates | -1.0 | -1.1 (115%) | +0.1 (-15%) | 0.91 (0.77-1.03) at 10%, 0.83 at 1%; finish +0.4; 232380 teams, 20 slates | LEAN against | 384, -1.6 | 32% / 45% | 25% |
| NEWS | both | 0.98 (0.90-1.07) at 10%, 0.97 at 1%; finish -0.2; 578593 teams, 21 slates | -0.0 | -1.1 | +1.1 | 1.01 (0.92-1.10) at 10%, 1.00 at 1%; finish -0.5; 578603 teams, 21 slates | no lean | 1215, -1.2 | 35% / 47% | 31% |
| OTHER | AM | 1.28 (0.71-1.92) at 10%, 1.18 at 1%; finish -3.8; 39039 teams, 3 slates | +4.7 | +1.4 (30%) | +3.3 (70%) | 1.29 (0.78-1.84) at 10%, 1.21 at 1%; finish -3.8; 39039 teams, 3 slates | LEAN for | 113, +2.6 | 36% / 50% | 38% |
| OTHER | PM | 0.99 (0.80-1.21) at 10%, 1.12 at 1%; finish +1.5; 75892 teams, 14 slates | -1.2 | -0.5 (39%) | -0.7 (61%) | 0.93 (0.74-1.14) at 10%, 1.05 at 1%; finish +2.2; 75890 teams, 14 slates | no lean | 251, -0.8 | 32% / 46% | 30% |
| OTHER | both | 1.11 (0.85-1.31) at 10%, 1.19 at 1%; finish -0.4; 114931 teams, 14 slates | +0.9 | +0.3 (36%) | +0.6 (64%) | 1.07 (0.83-1.27) at 10%, 1.16 at 1%; finish -0.1; 114929 teams, 14 slates | no lean | 364, +0.3 | 33% / 47% | 32% |
| all | AM | 1.07 (0.95-1.22) at 10%, 1.10 at 1%; finish -1.1; 385249 teams, 18 slates | +0.9 | -0.8 (-85%) | +1.7 (185%) | 1.10 (0.98-1.26) at 10%, 1.15 at 1%; finish -1.4; 385254 teams, 18 slates | LEAN for | 944, -0.5 | 36% / 48% | 34% |
| all | PM | 0.99 (0.92-1.09) at 10%, 1.01 at 1%; finish +0.1; 681199 teams, 21 slates | -0.2 | -0.2 | +0.1 | 1.01 (0.93-1.11) at 10%, 1.03 at 1%; finish -0.2; 681211 teams, 21 slates | no lean | 1117, -0.8 | 35% / 45% | 31% |
| all | both | 1.03 (0.95-1.12) at 10%, 1.04 at 1%; finish -0.4; 1066465 teams, 21 slates | +0.3 | -0.4 | +0.7 | 1.04 (0.97-1.14) at 10%, 1.07 at 1%; finish -0.6; 1066465 teams, 21 slates | no lean | 2061, -0.7 | 35% / 46% | 32% |

## 3d. Candidate: my AM teams against my PM teams (for the Monday section; not a proposal)

A = my AM teams, B = my PM teams, inside the same contest and price group. Raw: each window's top-10% rate over the field's 10%. Then what differs, per team.

| | Teams | Raw top-10% | VALUE picks | PRICEY picks | Tagged picks | Projected drafted% of picks | Field sharing 4+ of 6 | Teams with an exact duplicate | Price | Points over price | Swaps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AM | 518 | 1.43 | 1.70 | 0.69 | 0.38 | 93% | 1.01% | 19% | 220.1 | +2.7 | 0.45 |
| PM | 1146 | 1.33 | 1.46 | 0.65 | 0.14 | 90% | 1.22% | 22% | 218.1 | +5.7 | 0.10 |

Inside the same contest and price group, AM against PM: 1.17 (0.86-1.56) at 10%, 1.25 at 1%; finish +2.0; 516 teams, 16 slates (five price groups); 1.02 (0.76-1.34) at 10%, 1.71 at 1%; finish +3.0; 488 teams, 16 slates (ten).

## 3e. Candidates for 11-16 (asked 2026-11-09; not proposals)

### 1. Same-position teammates: source, examples, and starter/backup instead

Position: Underdog's own position on the slate (the record's `pos`), grouped G (PG, SG, G), F (SF, PF, F), C. Underdog scores everyone as flex, so position matters here only as a stand-in for sharing minutes and touches. Five early/late same-position pairs on 2026-11-12's rosters:

- Cade Cunningham (PG, round 1) + Daniss Jenkins (PG, round 4), DET
- Jaden McDaniels (PF, round 3) + Jonathan Kuminga (PF, round 5), MIN
- Trae Young (PG, round 3) + Kyshawn George (SG, round 4), WAS
- Cooper Flagg (SF, round 1) + PJ Washington (PF, round 5), DAL
- Naz Reid (C, round 2) + Moussa Diabate (C, round 6), CHA

Starter and direct backup instead of position: the starter averages 28+ minutes; his backup scores 4+ more points a game when the starter sits. Both from the morning file as it stood at that night's lock (the mirror's history: games through the night before, nothing later). The with/without splits start in the morning file around 10-29, so earlier nights have no pairs. Against teams with no two teammates:

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Same position, early + late (the approved card row) | 0.91 (0.81-0.99) at 10%, 0.94 at 1%; finish +1.6; 36677 teams, 19 slates | -1.5 | -5.6 (374%) | +4.1 (-274%) | - (holding) | 0.81 (0.72-0.90) at 10%, 0.75 at 1%; finish +2.9; 36620 teams, 19 slates | RULE against |
| Starter + his backup, any rounds | 0.85 (0.55-1.13) at 10%, 0.88 at 1%; finish +3.9; 18060 teams, 11 slates | -3.0 | -7.9 (264%) | +4.9 (-164%) | - (holding) | 0.78 (0.49-1.10) at 10%, 0.57 at 1%; finish +4.4; 18047 teams, 11 slates | LEAN against |
| Starter early (rounds 1-3) + his backup late (rounds 4-6) | 0.74 (0.50-1.03) at 10%, 0.50 at 1%; finish +5.0; 6721 teams, 10 slates | -4.5 | -7.9 (174%) | +3.4 (-74%) | - (holding) | 0.67 (0.44-0.96) at 10%, 0.40 at 1%; finish +6.0; 6722 teams, 10 slates | LEAN against |

### 2. Fallers: the definitions behind card-fallers

Ranks are the night's closing-ADP order. 6-drafter pods (4-drafter in brackets):
- **1/2 turn** (picks 6-7, or 5 and 8 [3-4, or 3 and 6]): your first player is a top-4 [top-2] ADP rank and your second is ranked 5-8 [3-6]. In the draft room: a top-4 [top-2] player still there at your turn pick; take him.
- **2/3 turn** (picks 12-13, or 11 and 14 [8-9, or 7 and 10]), for the 1.01 and 1.02 drafters: your second player is ranked 9th or better [5th or better], 3+ ranks ahead of your turn pick; take him.
Measured against same-contest, same-price teams that took the ADP-order pair at that turn (the trusting teams); the price-split check is in 3b. Fallers elsewhere in the draft: part 4 below.

### 3. Exposure, not order: T3 VALUE and T4 PRICEY

Against same-contest, same-price teams without (at each team's draft window).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| 2+ T3 VALUE players | 1.29 (0.90-1.62) at 10%, 1.55 at 1%; finish -4.5; 12224 teams, 14 slates | +5.0 | +7.0 (140%) | -2.0 (-40%) | - (holding) | 1.29 (0.90-1.62) at 10%, 1.54 at 1%; finish -4.4; 12224 teams, 14 slates | LEAN for |
| 1+ T3 VALUE player | 0.95 (0.79-1.14) at 10%, 0.87 at 1%; finish -0.4; 91054 teams, 18 slates | +0.8 | +2.0 (250%) | -1.2 (-150%) | - (holding) | 0.88 (0.75-1.05) at 10%, 0.84 at 1%; finish +0.7; 91045 teams, 18 slates | LEAN against |
| A T4 PRICEY player | 1.06 (0.89-1.24) at 10%, 1.15 at 1%; finish -1.4; 124891 teams, 21 slates | +1.0 | +1.0 (97%) | +0.0 (3%) | - (holding) | 0.94 (0.77-1.14) at 10%, 1.02 at 1%; finish -1.2; 124508 teams, 21 slates | no lean |

### 4. Fallers in every round

A team's k-th player by the ADP it paid stands for its round-k pick (pick order isn't public, so this is a lower bound on the slide). A faller was paid an ADP 3+ picks before that round's first pick (round 3 on 6 drafters: ADP 10 or better). Explained: tagged at the team's window, or his tag changed between Lock AM and lock. A: teams with that faller in round k; B: teams whose round-k player wasn't a faller.

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| Round 1, nothing explains it | none | - | - | - |
| Round 1, explained | none | - | - | - |
| Round 2, nothing explains it | 0.84 (0.00-2.90) at 10%, 8.63 at 1%; finish +4.3; 13 teams, 5 slates | -3.8 | +2.4 (-64%) | -6.2 (164%) | +4.8 | 0.82 (0.00-3.05) at 10%, 8.38 at 1%; finish +4.5; 13 teams, 5 slates | not enough |
| Round 2, explained (tag or news) | 5.48 at 10%, 0.00 at 1%; finish -36.6; 1 teams, 1 slates | +49.6 | +13.9 (28%) | +35.7 (72%) | +23.1 | 7.37 at 10%, 0.00 at 1%; finish -41.7; 1 teams, 1 slates | not enough |
| Round 3, nothing explains it | 1.28 (1.03-1.69) at 10%, 2.28 at 1%; finish -6.3; 386 teams, 17 slates | +2.7 | +1.7 (62%) | +1.1 (38%) | +6.6 | 1.54 (1.24-1.97) at 10%, 2.80 at 1%; finish -8.1; 386 teams, 17 slates | RULE for |
| Round 3, explained (tag or news) | 1.88 (1.20-2.73) at 10%, 2.43 at 1%; finish -14.4; 141 teams, 5 slates | +15.1 | +14.1 (93%) | +1.0 (7%) | +19.0 | 2.62 (1.86-3.17) at 10%, 3.72 at 1%; finish -19.7; 141 teams, 5 slates | RULE for |
| Round 4, nothing explains it | 1.57 (1.14-1.95) at 10%, 2.02 at 1%; finish -8.7; 1361 teams, 21 slates | +6.6 | +2.9 (44%) | +3.7 (56%) | +5.7 | 1.66 (1.27-1.98) at 10%, 2.18 at 1%; finish -9.6; 1361 teams, 21 slates | RULE for |
| Round 4, explained (tag or news) | 1.13 (0.56-1.57) at 10%, 0.00 at 1%; finish -4.2; 42 teams, 5 slates | +0.4 | -1.9 | +2.3 | +0.9 | 1.15 (0.56-1.62) at 10%, 0.00 at 1%; finish -4.0; 42 teams, 5 slates | not enough |
| Round 5, nothing explains it | 1.84 (1.52-2.12) at 10%, 3.06 at 1%; finish -9.1; 3693 teams, 20 slates | +8.0 | +2.5 (31%) | +5.5 (69%) | +2.4 | 1.87 (1.56-2.14) at 10%, 3.18 at 1%; finish -9.3; 3693 teams, 20 slates | RULE for |
| Round 5, explained (tag or news) | 2.21 (1.35-3.10) at 10%, 2.79 at 1%; finish -15.5; 171 teams, 6 slates | +11.7 | +10.5 (90%) | +1.1 (10%) | +9.7 | 2.13 (1.39-2.89) at 10%, 2.59 at 1%; finish -14.5; 171 teams, 6 slates | RULE for |
| Round 6, nothing explains it | 0.97 (0.80-1.14) at 10%, 1.01 at 1%; finish +1.4; 5269 teams, 21 slates | -1.6 | -4.5 (274%) | +2.8 (-174%) | -1.3 | 1.12 (0.95-1.28) at 10%, 1.22 at 1%; finish -0.7; 5269 teams, 21 slates | LEAN for |
| Round 6, explained (tag or news) | 1.83 (1.27-1.84) at 10%, 1.19 at 1%; finish -12.1; 187 teams, 3 slates | +10.2 | +2.8 (27%) | +7.4 (73%) | +6.6 | 1.74 (1.32-1.75) at 10%, 1.16 at 1%; finish -11.9; 187 teams, 3 slates | LEAN for |

### 5. The original rules (kept-*), asked 2026-11-11

Each tier's kept rule is the Tiers button's order there. A: teams holding the button's first of a decision pair (ADP within 4, same tier) and not its second; B: the reverse. Only pairs with the same flag and no tag on either, so the order is the rule's steps, not VALUE first / PRICEY last or a Questionable push (those have their own rows).

| Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the decision pick(s) | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |
|---|---|---|---|---|---|---|---|
| AM T1: ADP, Boom deciding within 2 picks | 2.10 (1.47-3.03) at 10%, 2.70 at 1%; finish -8.9; 53001 teams, 17 slates | +9.3 | +8.3 (89%) | +1.1 (11%) | +8.9 | 2.10 (1.45-3.11) at 10%, 2.58 at 1%; finish -9.5; 52996 teams, 17 slates | RULE for |
| PM T1: ETR | 1.05 (0.89-1.26) at 10%, 1.09 at 1%; finish -0.9; 118796 teams, 21 slates | +1.3 | +2.2 (177%) | -1.0 (-77%) | +3.4 | 1.11 (0.92-1.36) at 10%, 1.15 at 1%; finish -2.1; 118801 teams, 21 slates | no lean |
| AM T2: ADP straight | 0.95 (0.84-1.07) at 10%, 1.01 at 1%; finish +0.5; 308648 teams, 18 slates | -0.6 | +1.0 (-170%) | -1.7 (270%) | +2.0 | 0.99 (0.88-1.10) at 10%, 1.07 at 1%; finish +0.0; 308641 teams, 18 slates | no lean |
| AM T3/T4: Proj, ADP deciding within 3 points | 0.95 (0.85-1.06) at 10%, 0.94 at 1%; finish +1.3; 200654 teams, 18 slates | -0.9 | -0.6 (62%) | -0.4 (38%) | +0.8 | 0.98 (0.88-1.10) at 10%, 0.97 at 1%; finish +0.7; 200651 teams, 18 slates | no lean |
| PM T3: ETR, ties to ADP then Boom | 0.99 (0.87-1.12) at 10%, 0.77 at 1%; finish -0.3; 209567 teams, 20 slates | +0.5 | +0.9 (175%) | -0.4 (-75%) | +0.9 | 1.03 (0.90-1.16) at 10%, 0.81 at 1%; finish -0.9; 209565 teams, 20 slates | no lean |

## 4. The field

### Turns, from rosters by ADP rank (no pick order)

Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching (a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. Definitions in turn_teams().

| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|---|
| 1/2 | a. reach vs trust | 0.73 (0.59-0.92) at 10%, 0.49 at 1%; finish +1.8; 29560 teams, 21 slates | 1.97 (1.11-2.91) at 10%, 0.00 at 1%; finish -3.9; 128 teams, 18 slates |
| 1/2 | fallers vs trust | 1.34 (1.00-1.88) at 10%, 1.77 at 1%; finish -2.7; 45360 teams, 21 slates | 1.57 (0.96-2.51) at 10%, 3.07 at 1%; finish -4.8; 217 teams, 21 slates |
| 1/2 | b. reach toward higher projection vs trust | 1.40 (0.81-2.31) at 10%, 1.44 at 1%; finish -1.0; 5221 teams, 17 slates | 2.79 (1.12-4.30) at 10%, 0.00 at 1%; finish -6.2; 56 teams, 10 slates |
| 1/2 | b. reach toward VALUE flag vs trust | none | none |
| 1/2 | b. reach toward less drafted vs trust | none | none |
| 1/2 | c. 6-drafter, ranks 6 + 7 | 0.92 (0.66-1.22) at 10%, 0.75 at 1%; finish -0.6; 14620 teams, 16 slates | 0.71 (0.00-1.66) at 10%, 0.00 at 1%; finish -5.1; 74 teams, 13 slates |
| 1/2 | c. 6-drafter, ranks 5 + 8 | 0.84 (0.44-1.36) at 10%, 0.52 at 1%; finish +1.2; 11704 teams, 17 slates | 1.00 (0.00-2.39) at 10%, 0.00 at 1%; finish -6.2; 56 teams, 15 slates |
| 1/2 | c. 6-drafter, ranks 5 + 7 | 1.35 (0.90-1.79) at 10%, 1.87 at 1%; finish -1.6; 11374 teams, 17 slates | 1.84 (0.90-2.83) at 10%, 3.16 at 1%; finish -8.6; 64 teams, 15 slates |
| 1/2 | c. 6-drafter, ranks 6 + 8 | 1.04 (0.28-2.21) at 10%, 1.04 at 1%; finish +0.6; 8641 teams, 16 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -2.2; 34 teams, 13 slates |
| 1/2 | c. 6-drafter, ranks 5 + 6 | 0.94 (0.65-1.22) at 10%, 0.83 at 1%; finish +0.9; 7763 teams, 16 slates | 1.58 (0.60-2.66) at 10%, 0.00 at 1%; finish -5.3; 49 teams, 14 slates |
| 1/2 | c. 6-drafter, ranks 5 + 9 | 1.37 (0.72-1.86) at 10%, 2.41 at 1%; finish -2.0; 6819 teams, 17 slates | 2.18 (1.03-3.25) at 10%, 0.00 at 1%; finish -10.3; 32 teams, 10 slates |
| 1/2 | c. 6-drafter, ranks 6 + 9 | 1.24 (0.60-2.17) at 10%, 1.06 at 1%; finish -0.2; 4713 teams, 16 slates | 3.46 (1.99-4.79) at 10%, 0.00 at 1%; finish -11.0; 33 teams, 6 slates |
| 1/2 | c. 6-drafter, ranks 7 + 8 | 0.51 (0.32-0.76) at 10%, 0.20 at 1%; finish +0.3; 4472 teams, 17 slates | 1.06 (0.00-4.40) at 10%, 0.00 at 1%; finish +7.3; 22 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 5 + 10 | 0.75 (0.45-1.10) at 10%, 0.40 at 1%; finish -1.4; 3458 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +6.3; 14 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 5 + 11 | 1.52 (0.81-1.92) at 10%, 2.22 at 1%; finish -3.9; 1975 teams, 17 slates | 0.85 (0.00-1.97) at 10%, 0.00 at 1%; finish -2.0; 13 teams, 5 slates |
| 1/2 | c. 6-drafter, ranks 7 + 9 | 1.26 (0.94-1.50) at 10%, 1.30 at 1%; finish -2.6; 1810 teams, 17 slates | 1.06 (0.00-3.52) at 10%, 0.00 at 1%; finish -0.4; 14 teams, 4 slates |
| 1/2 | c. 6-drafter, ranks 6 + 10 | 0.85 (0.36-1.66) at 10%, 0.70 at 1%; finish +1.3; 1720 teams, 16 slates | 3.41 (0.00-3.66) at 10%, 0.00 at 1%; finish -16.7; 8 teams, 3 slates |
| 1/2 | c. 6-drafter, ranks 8 + 9 | 1.06 (0.38-1.90) at 10%, 1.14 at 1%; finish -4.6; 1148 teams, 17 slates | 5.91 at 10%, 0.00 at 1%; finish -28.5; 6 teams, 2 slates |
| 1/2 | c. 6-drafter, ranks 6 + 11 | 0.84 (0.51-1.38) at 10%, 0.74 at 1%; finish +0.7; 1133 teams, 16 slates | 0.00 at 10%, 0.00 at 1%; finish -3.1; 2 teams, 1 slates |
| 1/2 | c. 6-drafter, ranks 7 + 10 | 0.41 (0.27-0.58) at 10%, 0.00 at 1%; finish +2.5; 1062 teams, 17 slates | none |
| 1/2 | c. 6-drafter, ranks 5 + 12 | 0.42 (0.25-0.60) at 10%, 0.00 at 1%; finish +8.6; 971 teams, 17 slates | none |
| 2/3 | a. reach vs trust | 1.10 (0.94-1.26) at 10%, 1.29 at 1%; finish +0.4; 25943 teams, 21 slates | 1.79 (1.24-2.39) at 10%, 1.84 at 1%; finish -8.3; 120 teams, 20 slates |
| 2/3 | fallers vs trust | 1.25 (1.04-1.53) at 10%, 1.33 at 1%; finish -4.5; 18804 teams, 21 slates | 1.80 (1.25-2.40) at 10%, 1.57 at 1%; finish -7.4; 100 teams, 19 slates |
| 2/3 | b. reach toward higher projection vs trust | 1.65 (1.36-2.01) at 10%, 2.19 at 1%; finish -7.1; 6140 teams, 21 slates | 1.99 (1.13-2.69) at 10%, 3.75 at 1%; finish -11.2; 67 teams, 14 slates |
| 2/3 | b. reach toward VALUE flag vs trust | 1.12 (0.73-1.50) at 10%, 1.09 at 1%; finish +1.9; 3245 teams, 18 slates | 0.27 (0.00-0.46) at 10%, 0.00 at 1%; finish -2.9; 34 teams, 10 slates |
| 2/3 | b. reach toward less drafted vs trust | 0.00 at 10%, 0.00 at 1%; finish +17.6; 12 teams, 1 slates | none |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 13 | 0.72 (0.54-0.85) at 10%, 0.22 at 1%; finish -1.8; 4211 teams, 16 slates | 1.08 (0.00-1.92) at 10%, 0.00 at 1%; finish -9.9; 23 teams, 10 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 12 | 1.17 (0.78-1.54) at 10%, 1.18 at 1%; finish +3.3; 3647 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +12.5; 15 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 12 + 14 | 0.76 (0.35-1.23) at 10%, 0.51 at 1%; finish +12.1; 3570 teams, 16 slates | 1.15 (0.00-2.06) at 10%, 0.00 at 1%; finish +16.4; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 13 | 1.30 (0.86-1.79) at 10%, 1.60 at 1%; finish -4.7; 3192 teams, 17 slates | 0.64 (0.00-1.84) at 10%, 0.00 at 1%; finish -2.6; 20 teams, 9 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 11 + 14 | 0.97 (0.52-1.46) at 10%, 1.40 at 1%; finish +9.9; 2696 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +17.1; 13 teams, 6 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 13 | 1.27 (0.88-1.65) at 10%, 1.32 at 1%; finish -9.1; 2575 teams, 17 slates | 0.72 (0.00-1.64) at 10%, 2.89 at 1%; finish -0.6; 18 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 12 | 0.62 (0.43-0.85) at 10%, 0.43 at 1%; finish -3.3; 2459 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -13.6; 4 teams, 3 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 11 + 14 | 0.81 (0.53-1.13) at 10%, 0.59 at 1%; finish +0.4; 2414 teams, 17 slates | 0.72 (0.00-1.48) at 10%, 0.00 at 1%; finish -10.4; 8 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 13 | 1.63 (1.08-2.31) at 10%, 1.79 at 1%; finish -10.9; 2159 teams, 17 slates | 1.75 (0.66-3.13) at 10%, 4.07 at 1%; finish -4.9; 20 teams, 8 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 14 | 1.20 (0.64-1.92) at 10%, 1.00 at 1%; finish +2.0; 2123 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish -1.0; 8 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 13 | 0.87 (0.57-1.22) at 10%, 0.54 at 1%; finish -2.0; 1997 teams, 17 slates | 0.97 (0.00-4.05) at 10%, 0.00 at 1%; finish +1.2; 6 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 12 | 0.54 (0.29-0.81) at 10%, 0.55 at 1%; finish +3.3; 1956 teams, 17 slates | 0.00 (0.00-0.00) at 10%, 0.00 at 1%; finish +8.7; 12 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 13 + 14 | 1.00 (0.56-1.49) at 10%, 0.84 at 1%; finish +4.0; 1902 teams, 17 slates | 3.34 (2.13-3.81) at 10%, 0.00 at 1%; finish -15.6; 13 teams, 4 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 12 + 14 | 0.82 (0.45-1.23) at 10%, 0.70 at 1%; finish +5.4; 1853 teams, 16 slates | 1.06 (0.00-1.69) at 10%, 0.00 at 1%; finish +4.5; 10 teams, 5 slates |
| 2/3 | c. 6-drafter, anchor 2, ranks 10 + 12 | 0.82 (0.52-1.24) at 10%, 0.46 at 1%; finish -4.2; 1814 teams, 17 slates | 2.68 (0.73-5.30) at 10%, 0.00 at 1%; finish -17.4; 9 teams, 7 slates |
| 2/3 | c. 6-drafter, anchor 1, ranks 10 + 13 | 1.02 (0.75-1.27) at 10%, 0.84 at 1%; finish -6.8; 1693 teams, 17 slates | 1.79 (0.00-3.82) at 10%, 0.00 at 1%; finish -4.8; 12 teams, 6 slates |

Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at that turn.

### Drafted% by tier, flag and Q class

Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the flagged one less.

| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |
|---|---|---|---|---|---|---|
| AM | T1-T2 | PRICEY | 149 | 95% | 96% | -0 |
| AM | T1-T2 | Q TRAP | 24 | 75% | 95% | -20 |
| AM | T1-T2 | VALUE | 8 | 84% | 97% | -13 |
| AM | T3-T4 | PRICEY | 133 | 93% | 96% | -3 |
| AM | T3-T4 | Q FAIR | 1 | 15% | 95% | -80 |
| AM | T3-T4 | Q TRAP | 2 | 98% | 97% | +1 |
| AM | T3-T4 | VALUE | 103 | 88% | 96% | -8 |
| AM | T5 | Q FAIR | 367 | 10% | 18% | -9 |
| AM | T5 | VALUE | 697 | 36% | 19% | +17 |
| PM | T1-T2 | PRICEY | 164 | 99% | 99% | -0 |
| PM | T1-T2 | Q TRAP | 22 | 80% | 99% | -19 |
| PM | T1-T2 | VALUE | 13 | 96% | 97% | -1 |
| PM | T3-T4 | PRICEY | 197 | 97% | 98% | -1 |
| PM | T3-T4 | Q FAIR | 4 | 13% | 98% | -85 |
| PM | T3-T4 | Q TRAP | 11 | 87% | 96% | -9 |
| PM | T3-T4 | VALUE | 167 | 95% | 99% | -3 |
| PM | T5 | Q FAIR | 262 | 9% | 20% | -11 |
| PM | T5 | VALUE | 624 | 62% | 24% | +38 |

T5 breakers (PM tiers) drafted in under half the flagship's pods: VALUE 4, unflagged 121 (of all T5 breakers: VALUE 13, unflagged 131).

### Stacks (residual_correlations.md): teams holding the structure against same-price teams without

| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |
|---|---|---|
| Opposing stars (their team's top 2 by projection, same game) | 1.17 (1.05-1.31) at 10%, 1.28 at 1%; finish -1.5; 142182 teams, 21 slates | 1.63 (1.40-1.89) at 10%, 1.48 at 1%; finish -7.6; 721 teams, 21 slates |
| Same-position teammates | 0.80 (0.72-0.92) at 10%, 0.87 at 1%; finish +4.2; 84931 teams, 21 slates | 1.34 (1.08-1.74) at 10%, 1.93 at 1%; finish -4.1; 361 teams, 21 slates |
| Same-position teammates, spread 5+ | 0.89 (0.80-0.98) at 10%, 0.77 at 1%; finish +1.2; 33295 teams, 18 slates | 1.56 (1.07-2.15) at 10%, 2.04 at 1%; finish -10.3; 176 teams, 17 slates |

### What top-1% teams held (a description, not a rule)

Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.

| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Top 1% | 0.74 | 1.70 | 1.17 | 1.27 | 0.85 | 1.00 | 1.08 | 0.02 | 0.10 | 0.00 | 2.93 |
| Field | 0.60 | 1.70 | 1.20 | 1.30 | 0.92 | 0.95 | 1.17 | 0.02 | 0.10 | 0.00 | 1.09 |

### Swaps in the field

Teams with a swap against same-price teams without (each priced at what it paid): 0.77 (0.64-0.89) at 10%, 0.80 at 1%; finish +5.5; 60938 teams, 20 slates.

### High-volume users (100+ teams on 8+ nights; studied, never ranked)

600 users. Per team, against the field and me:

| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |
|---|---|---|---|---|---|---|---|---|---|---|
| High-volume | 234800 | 0.61 | 1.71 | 1.23 | 1.29 | 0.88 | 1.03 | 1.10 | 0.26 | 93% |
| Me | 1718 | 0.61 | 1.74 | 1.36 | 1.18 | 1.00 | 1.53 | 0.65 | 0.35 | 91% |
| Everyone | 376495 | 0.60 | 1.70 | 1.20 | 1.30 | 0.92 | 0.95 | 1.17 | 0.24 | 93% |

### Swaps by the ruled-out player's tier (at the team's draft window)

Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights nba_swaps.py leaves uncredited on purpose are out of every swap test (2026-11-01).

| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |
|---|---|---|
| T1-T2 | both | 0.56 (0.34-0.77) at 10%, 0.38 at 1%; finish +10.3; 9662 teams, 7 slates |
| T1-T2 | AM | 0.67 (0.44-0.89) at 10%, 0.48 at 1%; finish +6.4; 5609 teams, 7 slates |
| T1-T2 | PM | 0.41 (0.11-0.65) at 10%, 0.23 at 1%; finish +15.7; 4053 teams, 3 slates |
| T3-T5 | both | 0.89 (0.76-1.04) at 10%, 1.04 at 1%; finish +1.9; 21423 teams, 15 slates |
| T3-T5 | AM | 0.84 (0.70-0.98) at 10%, 0.96 at 1%; finish +3.0; 11265 teams, 13 slates |
| T3-T5 | PM | 0.95 (0.75-1.18) at 10%, 1.12 at 1%; finish +0.7; 10158 teams, 10 slates |
| not credited | both | 0.77 (0.63-0.91) at 10%, 0.82 at 1%; finish +6.2; 24229 teams, 20 slates |
| not credited | AM | 0.79 (0.65-0.96) at 10%, 0.77 at 1%; finish +5.2; 13133 teams, 17 slates |
| not credited | PM | 0.75 (0.55-0.93) at 10%, 0.88 at 1%; finish +7.3; 11096 teams, 20 slates |

## 5. Draft verdicts (not yet written to decision_register.csv)

MONEY rests on the top-10% lift (the faster reader); the top-1% lift and finish are beside it in section 3 as the long-run and steadier checks. 33 cells tested; 19 show a lean or rule and 12 a rule. By chance alone about 13 would show a lean (40% of cells: 80%+ of resamples one side happens 40% of the time with nothing there) and about 2 a rule (90% range clear of 1.0 and the check slates agreeing, about 5%). So a lone lean is weak; a rule, or a lean that agrees with the points verdict, counts.
A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.

| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |
|---|---|---|---|---|---|---|
| am-t5-button-order | adopted | LEAN (both windows) | RULE for | RULE for | 1.14 (1.05-1.23) | keep: points and money agree |
| value-up-middle-t5 | adopted | LEAN (both windows) | RULE for | RULE for | 1.26 (1.15-1.38) | keep: points and money agree |
| pricey-flags | candidate | mixed / not enough | RULE for | RULE for | 1.17 (1.08-1.27) | candidate: hand to the rankings side with its points cost |
| pm-t4-pricey-last-off | candidate (shadow) | not enough yet | no lean | no lean | 1.05 (0.76-1.31) | not enough on either side yet |
| pm-questionable-back-two | adopted | LEAN (RULE numbers; check pending) | no lean | no lean | 1.03 (0.84-1.23) | keep on points; money not settled |
| am-questionable-no-push | adopted | no variant beats it | no lean | no lean | 1.07 (0.81-1.36) | not enough on either side yet |
| q-tag-pushes | candidate | not enough yet | no lean | no lean | 1.01 (0.87-1.19) | not enough on either side yet |
| q-tag-raises | candidate | not enough yet | no lean | no lean | 1.01 (0.88-1.18) | not enough on either side yet |
| q-class-x:SMASH | candidate | not enough yet | not enough | not enough | - | not enough on either side yet |
| q-class-x:FAIR | candidate | not enough yet | no lean | no lean | 0.90 (0.77-1.06) | not enough on either side yet |
| q-class-x:TRAP | candidate | not enough yet | no lean | no lean | 0.95 (0.83-1.10) | not enough on either side yet |
| beneficiary-round6:sat | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | no lean | no lean | 1.01 (0.87-1.20) | not enough on either side yet |
| beneficiary-round6:played | candidate | Round-6 AM picks over their ADP round band: teammate tagged and played +2.5 (31, not enough yet), sat +1.7 (36, not enough yet), no tagged teammate -0.5 (299) | RULE for | LEAN for | 1.36 (1.09-1.72) | watch: money leans for |
| pm-t5-beneficiary | adopted | LEAN (listed) | no lean | no lean | 1.06 (0.83-1.32) | keep on points; money not settled |
| ownership-tiebreak-t5 | adopted (provisional, 2026-11-09; money RULE; the shadow decides) | On money's definition (within 2 projected points, drafted% 10+ apart): AM primary -3.7/pair (195, LEAN against, RULE numbers, check pending); PM -0.3 (577, no lean); every slate -0.5 (1084, no lean). The -4 to -7 was your board's ownership moves (takes), not this definition (money_points.md). Known price, not a reason to drop it: AM -3.7 (check pending); the button's realized order in sample AM +5.0 (105, RULE +), PM -2.8 (91, LEAN against) | RULE for | RULE for | 1.23 (1.13-1.33) | keep: the leverage pays (money RULE) |
| leverage-t2-t4 | candidate | On money's definition: not enough yet (AM 13 pairs, PM 6: T2-T3 are near 100% drafted, so 10-point drafted gaps are rare); in the shadow from 2026-11-10 | RULE for | RULE for | 1.51 (1.24-1.92) | candidate: hand to the rankings side with its points cost |
| pm-t2-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | LEAN for | no lean | 1.17 (0.93-1.50) | keep on points; money not settled |
| pm-t4-adp-etr2 | adopted (provisional; best of 8) | LEAN (listed) | LEAN against | LEAN against | 0.84 (0.70-1.06) | keep on points; money leans against (watch) |
| pm-t5-adp-value | adopted | RULE | RULE against | RULE against | 0.72 (0.63-0.84) | rethink: money RULE against it |
| one-tier-cap | adopted | LEAN (both windows) | LEAN against | LEAN against | 0.88 (0.71-1.06) | keep on points; money leans against (watch) |
| pm-middle-takes | candidate | LEAN (single window) | no lean | no lean | 1.01 (0.86-1.17) | keep on points; money not settled |
| pm-t2-other-reads | candidate | LEAN (single window) | no lean | no lean | 1.00 (0.85-1.17) | keep on points; money not settled |
| am-t5-other-reads | candidate | LEAN against (single window) | LEAN for | LEAN for | 1.23 (1.03-1.50) | watch: money leans for the leverage, not yet its bar |
| live-moves | candidate | not enough yet (3 nights) | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |
| swap-shuffle | candidate | not enough yet (155 credited swaps of 268; 12 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |
| swap-ownership-order | adopted as the swap board default (leverage); under contest test against spread | not enough yet: lowest first -0.8/swap against projection only, highest first +0.4 (155 swaps, 10 nights) | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |

