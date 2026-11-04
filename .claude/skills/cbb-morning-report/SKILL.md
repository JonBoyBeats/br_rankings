---
name: cbb-morning-report
description: College basketball (CBB) morning report. Grades last night's college projections against the box scores (ours, ours without EvanMiya, Underdog's), splits our misses into minutes and points per minute, writes up the biggest misses with a cause and logs them, reads last night's college contests (cut lines, your results, what the field did), and keeps the EvanMiya trial's running verdict. Use when asked for the college, CBB or college basketball morning report.
---

# College basketball morning report

The 2:17am PT nightly job (`.github/workflows/nba_daily.yml`, its "CBB record" and "CBB contests"
steps) writes last night's college slate to `analysis/cbb/daily/<date>_<day>_main.csv` (our
projection at lock against ESPN's box scores, `scripts/cbb_daily.py`) and its contests to
`analysis/cbb/contests/` (`scripts/nba_contests.py --sport cbb`). This report reads them and keeps
a log of why we missed, so patterns show up over weeks instead of being remembered night to night.

Unlike the NBA report there's no ETR and no board locks or tier rules on the CBB page: the
questions are whether our projection is accurate, where it misses (minutes or rate), whether
EvanMiya is earning its place, and what the field did.

## 1. Get the newest record

```
git pull origin main
git clone -q https://github.com/JonBoyBeats/br-adp-mirror ../br-adp-mirror 2>/dev/null || git -C ../br-adp-mirror pull -q
git -C ../br-adp-mirror fetch -q --unshallow 2>/dev/null || true
```

The newest file should be yesterday's main slate. If it isn't there, say so first (the "NBA daily
record" workflow may have failed or not run yet, or there was no college slate) and report on
the newest slate on file. If last night's contests aren't in `analysis/cbb/contests/contests.csv`,
say so too: they may not have settled by 2:17am; `python3 scripts/nba_contests.py pull --sport cbb
--mirror ../br-adp-mirror` picks them up.

## 2. The scores

```
python3 scripts/cbb_daily.py report
```

Every number comes from the script: don't estimate, round differently or recompute any of them.
It prints, for last night and the season:

- **Accuracy**: mean error and bias of ours, ours without EvanMiya and Underdog's, on players who
  played and had both ours and Underdog's: everyone, drafted only, and by what the projection was
  built from (`box`: a college season behind him; `miya` / `miya+ud`: a newcomer EvanMiya started,
  where "without EvanMiya" is Underdog's number, what we used before; `ud` / `ud+box`).
- **Where ours missed**: minutes off and points per minute off, for everyone, drafted, and
  newcomers. Biases say which way (positive: we were too high).
- **Last night's misses** of 8+ points among the drafted (or anyone we projected 15+), and the
  drafted players who didn't play.

One night is noise: say so for the first two weeks, and don't call ours better or worse than
Underdog's until the season line has about 300 drafted player-games.

**The EvanMiya trial** (November 2026; the owner pays for a month). Its verdict is the season line
"ours" against "ours w/o Miya" for everyone and for newcomers. Give it as a line each morning.
Around 2026-12-01 call it: keep EvanMiya if ours beats ours without it overall, and newcomers
aren't worse; otherwise recommend dropping it. If kept, the next question is its weight (`MIYA_W`
in battle-royale-research `scripts/cbb_nightly.py`, 0.5 to start), set from the record, not by
feel.

## 3. Write up the misses

For each of last night's misses (step 2's list), one cause, from what the row shows (minutes and
projected minutes, points per minute and projected, the spread, how it was built):

| cause | when | fixable |
|---|---|---|
| `minutes` | minutes far from projected with no blowout or injury to explain it: role misread | yes |
| `newcomer` | built from EvanMiya or Underdog (no college season) and the minutes or rate were wrong | yes |
| `blowout` | spread 18+ either way and his minutes ran well off the projection | partly |
| `out` | a teammate was out (EvanMiya's injury report, `cbb/inputs/outs.csv` in battle-royale-research) and his number didn't move for it | yes |
| `news` | tagged at lock, or he sat or left early | no |
| `shooting` | minutes close, points well off what his minutes would give | no |
| `peripherals` | minutes and points close, rebounds, assists or stocks well off | no |
| `other` | none fits: say what you see | ? |

Don't guess at news the data doesn't show: write "unclear".

## 4. Log them

Append one row per miss to `analysis/cbb/report/misses.csv` (create it with this header):

```
date,slate,player,team,adp,ours,ours_wo_miya,ud,actual,min,min_proj,ppm,ppm_proj,spread,src,cause,fixable,note
```

Don't add rows for a date and slate already in it: running the report twice must not count
anything twice.

## 5. Themes

Read all of `misses.csv`. Count causes, fixable against not, ours too high against too low, and
look for patterns repeating across slates: newcomers (and by EvanMiya rank on his team), transfers
moving up, crowded teams, heavy favorites or underdogs, minutes band (under 20, 20-28, 28+), the
same team. Report a theme only with at least 3 cases on at least 2 slates, with its count. With
fewer than about 5 slates logged, say the log is too thin for themes. A theme that crosses the bar
can propose a model change, but say how to test it on past seasons first
(`scripts/cbb_calibrate.py` in battle-royale-research has the 2024-25 and 2025-26 box scores), and
make no change without the owner's yes.

**Standing watches** (carried from the 2026-11-03 report; the script prints both under "Watch"):

- **EvanMiya's top 3**: players built from last season whom EvanMiya ranks 1st-3rd on their team
  (by offensive BPR from 2026-11-04; total BPR on 11-03, which mostly agrees)
  played their projected minutes on the first night (+0.6) where ranks 4-7 came in 3-5 short. The
  board marks the 1-3s with a green rank chip as our surer projections. Give the season line by
  rank band each morning; once it has about 100 players a band, say whether it still holds. If
  ranks 4-7 stay short, propose cutting their minutes, tested on past seasons first.
- **Back from a missed season** (`MISSED_SEASON` in battle-royale-research `scripts/cbb_nightly.py`,
  minutes x0.831 from 132 players on 2025-26): check their minutes still land near projected
  (the season line under "back from a missed season"). The factor was measured, so leave it
  alone unless the season line is clearly off with 30+ players.

## 6. The field

```
python3 scripts/nba_contests.py measures --sport cbb --mirror ../br-adp-mirror --date <last night>
```

For the biggest contest: cut lines (win, top 1%, median, top 1% over median), the drafted% bands
and the first priced player the field left in some pods, value (FPOE and breakers, field against
top 1%), the most-owned pairs and cores, your uniqueness, draft times, and your results (median
finish, tail ratios, payout). If `analysis/nba/expo.json` has your exposures for the slate, set
them against what scored. Rounds are estimates (pick order isn't public). The first weeks of
results are noise: say so, and propose no rule from them.

## 7. Takeaways

Add a dated section at the top of `analysis/cbb/report/takeaways.md` (newest first, create it if
missing): 2-4 bullets on last night, the EvanMiya line, any theme that crossed the bar, and a
change to try only when a theme supports it.

## 8. Save

```
git add analysis/cbb/report
git commit -m "CBB report: takeaways for <date>" && git push origin HEAD:main
```

## In chat

Short and scannable, in this order:

1. **Last night**: ours, without EvanMiya, and Underdog's (drafted players), one line, and the
   season line under it.
2. **Where we missed**: minutes or points per minute, and newcomers against the rest.
3. **The misses**: a line each, with its cause.
4. **The field**: the cut lines, your results, and one thing that stood out.
5. **EvanMiya trial**: the running line, and days left.
6. **Themes and takeaways**: or "too early" while the log is thin.
