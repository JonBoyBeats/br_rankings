# Money: checkpoint 1 (data checks and the price baseline)

Written by scripts/nba_money.py, 2026-11-09. The full report (sections 0-5) will be money_report.md.

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

