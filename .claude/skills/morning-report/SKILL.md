---
name: morning-report
description: NBA morning report. Scores last night's main slate and every slate so far for our Proj, ETR's first and last uploads, 5am and closing ADP, and the final board; writes up where we missed and why; keeps the running log of causes and the themes in it. Use when asked for the morning report.
---

# NBA morning report

The nightly job (`.github/workflows/nba_daily.yml`, about 2am PT) writes one file per main
slate to `analysis/nba/daily/`. This report scores them and keeps a log of why we missed,
so patterns show up over weeks rather than being remembered night to night.

## 1. Get the newest record

```
git pull origin main
```

The newest file should be yesterday's main slate (`analysis/nba/daily/<date>_<day>_main.csv`).
If it isn't there, say so first: the nightly run may have failed or not run yet (the
"NBA daily record" workflow). Then report on the newest slate on file.

## 2. The scores

```
python3 scripts/nba_report.py
```

Show its last-night and cumulative tables as printed. Every number comes from the script.
Don't estimate, round differently or recompute any of them. Read them for the user in a
few lines:

- **Accuracy**: rank correlation and top-12 hits say who ordered the slate best; average miss
  and bias are in points. Our Proj and ETR's are on the board's scale (median nudged toward
  ceiling), so both run a little high against actual scores. Compare them with each other,
  not with zero.
- **CLV**: of the players a source ranked 3+ spots off the 5am ADP, how often the ADP moved
  their way by lock. Our morning number beating that is the early-morning edge.
- **Blend**: the share of ours in a mix with ETR's last upload that missed least, with the
  range across resampled slates. A range that still spans most of 0-100% means not enough
  slates yet. Say so, and don't recommend a weight.
- "Ours (board)" is the number the board showed before the first ETR upload. "Ours (morning
  file)" is the raw box-score number. Slates before the board kept its number have only the
  second.

## 3. Write up the misses

Take last night's **Biggest misses** (ours off by 8+) and **Biggest ours-vs-ETR splits**
(4+ apart). Give each one cause from this list, using only what is in that slate's CSV
(minutes and usual minutes, margin, injury tag at lock, the box line, and who else on his
team sat):

| cause | when | fixable |
|---|---|---|
| `minutes` | minutes far from his usual with no injury, blowout or teammate absence to explain it: we misread his role | yes |
| `teammate-out` | a teammate sat and his number moved wrongly for it, in either direction | yes |
| `blowout` | margin 15+ either way and his minutes cut short | partly (the spread was known) |
| `news` | tagged at lock, scratched late, or left the game early (few minutes against a normal usual) | no |
| `shooting` | normal minutes, points well off what his minutes would give | no |
| `peripherals` | normal minutes and points, rebounds, assists or stocks well off | no |
| `other` | none of the above fits; say what you see in `note` | ? |

For a split, also record who was closer (`ours` or `etr`). Where ETR was closer, note
anything visible that ETR may have priced in and we didn't. Don't guess at news the data
doesn't show. Write "unclear" instead.

## 4. Log them

Append one row per player to `analysis/nba/report/misses.csv`. Don't add rows for a date and
slate already in it: running the report twice in a morning must not count a miss twice.

```
date,slate,player,team,kind,ours,etr_last,actual,min,usual_min,margin,cause,fixable,closer,note
```

`kind` is `miss` or `split`; `ours` is the board number when there is one, else the morning file.

## 5. Look for themes

Read all of `misses.csv`. Count causes, fixable against not, and ours too high against too
low. Then look for patterns repeating across slates: position, usual-minutes band (under 20,
20-28, 28+), ADP range, the same team, the same cause on the same kind of player. Report a
theme only when it has at least 3 cases on at least 2 slates, and give the count ("5 of our 7
`minutes` misses were bench bigs, too high every time"). With fewer than about 5 slates
logged, say the log is still too thin for themes.

## 6. Takeaways

Add a dated section at the top of `analysis/nba/report/takeaways.md` (newest first):
2-4 bullets on last night, any theme that crossed the bar above, and a change to try, but only
when a theme supports it. Keep earlier sections as they are.

## 7. Save

The session's files are gone when it ends, so commit the log and push it:

```
git add analysis/nba/report && git commit -m "NBA report: takeaways for <date>" && git push origin HEAD:main
```

## In chat

In this order, short and scannable: last night's scores, the scores so far, the misses
(one line each: player, cause, closer), themes, takeaways. Close with anything missing from
the record (no ETR on file, no board number, unmatched box scores) so it can be fixed.
