# Field studies, 14 NBA main slates (Oct 20 - Nov 2, 2026)

Flagship contests, about 200k teams, from analysis/nba/contests/. Ranges are 80%, from resampling whole
nights. Descriptions of what happened, not rules; see the shared spec's evidence rules. Scripts were one-off
analyses run from the contest files, the daily records and the box archive (2023-24 on).

## 1. Peer-group breakers (3 seasons of box scores, fit on 2023-25, tested on 2025-26)
Peer group: the 5 players projected just above him and the 5 just below that night (minutes x points a minute,
known before the game); he breaks when he outscores all 10. The night's top and bottom 5 aren't counted.
- First pass, with one-sided peers at the top of the night, looked like a doubling (20%+ history: 21.7% next game
  vs 10.4%); that was mostly the top players "breaking" against peers all projected below them.
- Counted symmetrically: a mild lean, about x1.16 on the odds of his next break per 10 points of history
  (held-out 2025-26: 7.9% at a 0-7% history, 9.3% at 10-16%, 13.0% at 16-20%; the 20%+ group is too small to read).
- Now in the morning file as pbr [breaks, games] over his last 40; not in Boom.

## 2. Ownership vs projection (decision pairs: ADP within 4, ETR medians within 2, drafted% 10+ points apart)
- 665 pairs over 13 nights (rounds 5+, where drafted% is under 100).
- Points: the lower-drafted player outscored the higher 47% of the time (43-51): a coin flip.
- Teams carrying the lower-drafted player finished top 1% 1.14% of the time vs 0.95% (difference -0.02 to +0.36).
- Read: the same points, shared by fewer teams. A weak lean toward the lower-drafted player at a tie; it costs
  no projection by construction.

## 5. Stars and co-stars (a team's top two by projection that night)
- 6,635 team-games: their nights over/under projection correlate +0.09. When the co-star had a top-10% night
  (+15 over), the star averaged +1.8 over his projection (all games +0.2). They move together, not against.
- Named pairs: Jokic-Murray +0.03, Luka-Reaves +0.18, Wemby-Fox +0.22, Wemby-Castle -0.07,
  SGA-J.Williams +0.01, Cade-Duren +0.11, Tatum-Brown +0.08.
- This season's field: teams with a top-3-round co-star AND his star finished top 1% 1.54% of the time
  (n=22,836) vs 1.06% with the co-star alone (n=130,018).
- Read: no sign a co-star's big night holds his star back; if anything, pairing them is a mild stack.

## 6. Risers and Q tags
- Risers can't be measured from Underdog's displayed ADP: it averages every draft since the slate opened, so it
  lags news (Paul George 35.3 to 31.9 across the whole day Tatum was ruled out, Nov 4). From Nov 4 the poller logs
  each contest's entry count hourly, so the recent-draft ADP can be recovered; the riser test waits on that.
- Questionable/Doubtful at the AM lock, then played: 17 players, +3.0 FP over their closing price (median +3.4),
  8 of 17 beat their round's 90th percentile (10% expected). Teams that drafted them nearer the morning price
  finished top 1% 1.27% of the time vs 0.81% for teams that took them later.
- Q/D at the AM lock, then sat: 10 players. The leaderboards show almost none of them because Underdog swaps a
  ruled-out player for the drafter's highest-ranked undrafted player: the team keeps a 6th-round-ish value in that
  slot (worse on small slates). The swap can't be seen in the public data, so this cost isn't measured.
- Read: small sample, but so far an early Q tag has not hurt; the ruled-in ones were value.

## Turns (from the contest measures)
- 2/3 turn: teams with a top-3 player's most-owned round 2-3 pair finished top 1% 0.64% (0.30-1.04) vs 1.34%
  (1.09-1.60) with any other pair.
- 1/2 turn: the opposite. The most-owned pair of ranks 5-8 finished top 1% 2.15% vs 0.50% for other pairs there
  (difference +0.2 to +2.9). Likely: the popular pair there is the two best players left; the others include reaches.
- Read: no general "fade the popular combo" rule. Show combo ownership with its projection; test each turn forward.

## 7. Your AM against PM teams (scripts/nba_ampm_study.py, run 2026-11-09)
Every one of your teams on file, AM or PM by the lock nearest its draft time; per team over its six picks, by closing-ADP
round band: ETR value (ETR's last number before lock over the band's average), FPOE (points over the band's average),
ADP gained from the morning to lock.

| Drafters | Window | Teams | Nights | Top 10% (x field) | Top 1% (x field) | ETR value | FPOE | ADP gained |
|---|---|---|---|---|---|---|---|---|
| 6 | AM | 447 | 13 | 1.43 | 1.12 | +12.3 | +17.3 | +1.9 |
| 6 | PM | 712 | 14 | 1.32 | 1.12 | +12.0 | +17.0 | +2.1 |
| 4 | AM | 52 | 4 | 0.77 | 0.00 | +13.6 | +13.2 | +0.9 |
| 4 | PM | 172 | 5 | 1.74 | 1.16 | +12.4 | +23.0 | +0.6 |

- 4-drafter AM teams were drafted as well as the PM ones on ETR's own numbers at lock (+13.6 vs +12.4) and gained
  ADP by lock, but scored 10 points a team less against their bands. The gap ran the same way on all 4 nights
  (FPOE AM/PM: 10-22 +7.5/+23.0, 10-29 +30.8/+33.1, 11-01 +4.6/+17.4, 11-05 +1.6/+9.5).
- Read: no draft flaw shows. The picks were as good on the projection; they scored less. 52 teams on 4 nights, many
  sharing players, so it is mostly a few players' nights. It stays in the morning report's contest summary (AM and PM
  at the top 10%, by pod size); look again at 10 4-drafter nights. If the AM tail is still under 1.0 then with equal
  ETR value, check what the AM teams share (the same few players, a stack) before calling it a habit.
- 6-drafter: no gap (AM 1.43, PM 1.32 at the top 10%).
