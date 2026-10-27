---
name: morning-report
description: NBA morning report. Scores the morning barbell (your AM board and our Proj against ADP) and the afternoon barbell (your PM board, ETR and our Proj against closing ADP) for last night's main slate and every slate so far; writes up your biggest calls and our misses and why; keeps the running log of causes and the themes in it. Use when asked for the morning report.
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

Show its tables as printed. Every number comes from the script. Don't estimate, round
differently or recompute any of them. The report is in two halves, the way the day runs:

- **Morning barbell**: the board your early drafts come off (Lock AM on the board, else the
  board saved before ETR's first upload) and our Proj then, against ADP at that moment. Did
  the morning work beat just drafting ADP?
- **Afternoon barbell**: your final board (Lock PM, else the board at lock), ETR's last upload
  and our Proj at Lock PM, against ADP at lock. Do your tweaks beat ETR straight, and does our
  number deserve a share of the projection?

Read them for the user in a few lines:

- **Rank corr** and its difference from the barbell's ADP: who ordered the slate best.
- **Round picks**: a source's two favourites in each ADP round against the round's average, in
  points. **Rounds 5-6** separately: finding the best late picks is where a lot of drafts are won.
- **CLV**: how far a source sat from ADP against how far ADP then moved, size-weighted (a
  correlation; 0 is no signal). Morning: from Lock AM to lock. ETR: from its first upload to lock.
- **Calls**: of the pairs of players two orders disagree on, how often the first was right.
  Your AM ranks against ADP and against our raw order; your PM ranks against ETR and against ADP.
  Over 50% means your moves are adding value.
- **Blend**: the share of ours in a mix with ETR that missed least.
- A cumulative difference shows an 80% range. A range that spans 0 (or 50% for calls, or most
  of 0-100% for the blend) isn't settled: say so, and don't recommend a change on it.

## 3. Write up the calls and misses

From last night's tables:

- **Your biggest AM calls against ADP** and **your biggest PM calls against ETR**: for each,
  whether the call was right (did he beat or trail the players you moved him past?) and the
  reason it went that way, from the causes below.
- **Biggest projection misses** (ours off by 8+) and **biggest ours-vs-ETR splits** (4+ apart):
  the cause, and for a split who was closer.

Give each one cause from this list, using only what is in that slate's CSV (minutes and usual
minutes, margin, injury tag at lock, the box line, and who else on his team sat):

| cause | when | fixable |
|---|---|---|
| `minutes` | minutes far from his usual with no injury, blowout or teammate absence to explain it: his role was misread | yes |
| `teammate-out` | a teammate sat and his number moved wrongly for it, in either direction | yes |
| `blowout` | margin 15+ either way and his minutes cut short | partly (the spread was known) |
| `news` | tagged at lock, scratched late (0 minutes), or left the game early | no |
| `shooting` | normal minutes, points well off what his minutes would give | no |
| `peripherals` | normal minutes and points, rebounds, assists or stocks well off | no |
| `other` | none of the above fits; say what you see in `note` | ? |

Where ETR was closer, note anything visible that ETR may have priced in and we didn't. Don't
guess at news the data doesn't show. Write "unclear" instead.

## 4. Log them

Append one row per player to `analysis/nba/report/misses.csv`. Don't add rows for a date and
slate already in it: running the report twice in a morning must not count anything twice.

```
date,slate,player,team,kind,ours,etr_last,actual,min,usual_min,margin,cause,fixable,closer,note
```

`kind` is `am_call`, `pm_call`, `miss` or `split`. For a call, `closer` is `right` or `wrong`.
`ours` is our number at Lock PM when there is one, else at Lock AM, else the morning file.

## 5. Look for themes

Read all of `misses.csv`. Count causes, fixable against not, ours too high against too low,
and your calls right against wrong by kind. Then look for patterns repeating across slates: position, usual-minutes band (under 20,
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

In this order, short and scannable: last night's morning and afternoon barbells, the same so
far, your calls and our misses (one line each: player, cause, right or closer), themes,
takeaways. Close with anything missing from
the record (no ETR on file, no board number, unmatched box scores) so it can be fixed.
