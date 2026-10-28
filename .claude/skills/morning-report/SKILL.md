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

Each barbell has two tables, every cell last night with the season beside it:

- **The orders**: rank corr (how well each order matched the finish), **round picks** (an
  order's two favourites in each ADP round of 6 picks, the 6th running to ADP rank 48, against
  that round's average, in points), **rounds 5-6** alone, top-12 hits, and CLV (morning from
  your AM lock, ETR from its first upload, to lock; 0 is no signal).
- **Your board against each straight order**: of the pairs of players your board and that
  order disagree on, how often yours was right, last night and season, with a range and a
  verdict. This answers the question the report is for: morning, should you draft off our
  number (or ADP) alone? Afternoon, should you draft off ETR alone? "Your board wins" means keep
  making your moves; "X alone wins" means stop; "too close to call" means not settled. Don't
  recommend a change on anything but a settled verdict.
- **By slate**: whether last night looked like the others or was an outlier.
- **Blend**: the share of ours in a mix with ETR that missed least.

## 3. Write up the calls and misses

From last night's tables:

- **Your biggest AM calls against ADP** and **your biggest PM calls against ETR**: for each,
  whether the call was right (did he beat or trail the players you moved him past?) and the
  reason it went that way, from the causes below.
- **Biggest projection misses** (ours off by 8+) and **biggest ours-vs-ETR splits** (4+ apart):
  the cause, and for a split who was closer.

Players who sat or left early aren't graded (the report lists them under "Not graded"), so they
aren't written up or logged. Give each one cause from this list, using only what is in that slate's CSV (minutes and usual
minutes, margin, injury tag at lock, the box line, and who else on his team sat):

| cause | when | fixable |
|---|---|---|
| `minutes` | minutes far from his usual with no injury, blowout or teammate absence to explain it: his role was misread | yes |
| `teammate-out` | a teammate sat and his number moved wrongly for it, in either direction | yes |
| `blowout` | margin 15+ either way and his minutes cut short | partly (the spread was known) |
| `news` | tagged at lock, or news during the day changed his role | no |
| `shooting` | normal minutes, points well off what his minutes would give | no |
| `peripherals` | normal minutes and points, rebounds, assists or stocks well off | no |
| `hedge` | a call on a teammate's uncertain status (questionable at your PM lock). You update those live as news lands, after the PM lock, so it isn't a process miss: log it, but leave it out of themes and right/wrong counts | no |
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

## 7. Last night, player by player

A line on every graded player's night (the newspaper), from a running ledger of every rotation
player. It is context only: it never
feeds Proj, the ranks or the grading above.

```
python3 scripts/nba_ledger.py draft
```

This writes the night to `analysis/nba/ledger.csv` and prints it in ADP order. Each row has
the gap to ETR, tags for what moved (minutes, scoring, rebounds, assists, stocks, turnovers,
or ETR's number against his usual) and a draft note built from the box score.

Review the drafts and write each player's final note in the `note` column of that night's rows,
as a one-liner a beat writer would give: what happened, and why when the data shows it.
Examples: "In line.", "Foul trouble: 22 minutes with 5 fouls, cold 4-13.", "Assists way up
(11), the way it has gone against CHA.", "Minutes cut to 24 in a close game: looks like a
rotation call." Keep the tags as the script set them, so the ledger stays consistent night to
night. Add matchup context only when `mtch_label`/`mtch_cats` or earlier ledger rows against the
same team support it. Don't invent news: if short minutes have no visible cause, say "unclear".
Then show it:

```
python3 scripts/nba_ledger.py print
```

## 8. Recent notes for today's board

Notes are written overnight: the 2:17am task records last night and puts template ("auto")
notes on the board, then the 2:47am task writes 2-3 sentences in this style for everyone due
(a scheduled task named "NBA Recent notes: written in style"). Here, check it went in:

```
git clone -q --depth 1 https://github.com/JonBoyBeats/br-adp-mirror ../br-adp-mirror 2>/dev/null || git -C ../br-adp-mirror pull -q
python3 scripts/nba_ledger.py form --slates ../br-adp-mirror/nba_latest.json
```

"0 notes due" means every player on today's slates (main and late) with 3+ graded games has a
written note covering his last game. Otherwise write the ones listed: 2-3 sentences on his
recent form against his projections. Synthesize, don't list the games: is he beating or
trailing his number, and is the reason sticky (minutes, role, usage) or noise (shooting,
stocks, a blowout)? Say what to expect if it holds. A game measured against "our usual" had no
ETR number; say so if it matters. Only what the ledger shows; no guessing at news. Save them as
a JSON file {key: note} (the key is in each player's header) and run:

```
python3 scripts/nba_ledger.py write <file> && python3 scripts/build_takes.py
```

## 9. Save

The session's files are gone when it ends, so commit and push everything:

```
git add analysis/nba/report analysis/nba/ledger.csv analysis/nba/form.csv analysis/nba/takes analysis/nba_takes.json
git commit -m "NBA report: takeaways and player notes for <date>" && git push origin HEAD:main
```

## In chat

In this order, short and scannable: last night's morning and afternoon barbells, the same so
far, themes, takeaways, then last night player by player (the printed list) and any "against
the same team" lines. The calls and misses from steps 3-4 are logged for the themes, not listed
in chat. Close with anything missing from the record (no lock, no ETR on file, unmatched box
scores, notes not written overnight) so it can be fixed.
