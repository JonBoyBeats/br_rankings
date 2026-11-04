---
name: morning-report
description: NBA morning report. Scores your AM and PM boards against the straight orders (ours, ETR, ADP) and tests the ordering rule on each of your five tiers, for last night's main slate and every slate so far; writes up your biggest calls and our misses and why; keeps the running log of causes and the themes in it. Use when asked for the morning report.
---

# NBA morning report

The nightly job (`.github/workflows/nba_daily.yml`, about 2am PT) writes one file per main
slate to `analysis/nba/daily/`. This report scores them and keeps a log of why we missed,
so patterns show up over weeks rather than being remembered night to night.

Its main job is the forward test of your tier rules: the five tiers you draw on the board each day,
each ordered by the rule written beside its tag (morning on our Proj, afternoon on ETR). The rules
came from the same 12 slates they were tuned on, so only nights after 2026-11-02 count for them.

## 1. Get the newest record

```
git pull origin main
git clone -q https://github.com/JonBoyBeats/br-adp-mirror ../br-adp-mirror 2>/dev/null || git -C ../br-adp-mirror pull -q
git -C ../br-adp-mirror fetch -q --unshallow 2>/dev/null || true
```

The tier rules use the board's Boom %, which reads the mirror's history: it must be a full clone.

The newest file should be yesterday's main slate (`analysis/nba/daily/<date>_<day>_main.csv`).
If it isn't there, say so first: the nightly run may have failed or not run yet (the
"NBA daily record" workflow). Then report on the newest slate on file.

## 2. The scores

```
python3 scripts/nba_report.py --mirror ../br-adp-mirror
```

Late news first: if a player who was being drafted (ADP in the first two-thirds of the draft: 24 or
earlier on a 36-pick slate, 16 on a 24-pick one) was ruled out after a lock (the report's "Not
graded" list against the lock times; ETR's last upload still having him is a sure sign), add his team to
`analysis/nba/report/late_news.json` for that date, under `am` (news after Lock AM) and/or `pm`
(after Lock PM), with a one-line note, and run the script again. Those teams' players are left out
of that half's grading, and calls and misses on them aren't logged, so a late scratch and the
boosts around it don't count for or against anyone. They still get their newspaper line. A late
scratch who wasn't being drafted doesn't take his team out: it stays graded, and calls on his
teammates are logged as `hedge`.

Every number comes from the script. Don't estimate, round differently or recompute any of them.
The report prints in the order it goes in chat:

- **Headline**: your board against each straight order, each window graded only on what was known
  in it. Morning: your AM board (Lock AM, else the board saved before ETR's first upload) against
  our Proj and ADP then. Afternoon: your PM board (Lock PM, else the board at lock) against ETR's
  last upload, our Proj and ADP at lock. Only decision pairs count (ADP within 4 picks at that
  window's lock): of those your board and the order disagree on, how often yours was right, last
  night and season, with a range and a verdict; beside it, on the pairs where exactly one player was
  a breaker (90th percentile of his ADP round band that night), how often yours took the breaker,
  and the old all-pairs rate for comparison. "Your board wins" means keep making your moves; "X alone
  wins" means stop; "too close to call" means not settled.
- **Tier rules**: the core. For each of your tiers at each lock (am_tier, pm_tier in the record),
  the rule beside it on the board (`TIER_RULES` in `scripts/nba_report.py`, matching
  `NBA_TIER_NOTES` in index.html) against ADP and the half's projection straight, in points per
  pair (for every decision pair in the tier, the earlier one's actual minus the later one's); where you
  broke the rule (your Q-tag reads and gut calls), how often you were right; and how the tier
  scored against its projection. A tier gets a verdict only after 14 nights and 30 pairs
  (`TIER_NIGHTS`, `MIN_PAIRS`, set before any result: never move them). Then, because about 27
  comparisons are under test at once, a comparison counts only with a 90% range clear of 0, or an
  80% range backed by the same direction in the other window or in 3+ tiers, and only if no single
  player's pairs can flip it ("hangs on one player" otherwise). Verdicts: "rule holds", "X beats
  the rule", "too close to call", plus "your moves win/lose" on the same bar around 50%. Until
  then "too early": say so, and don't suggest changing a rule.
- **Ours vs ETR**: one line on how our number at Lock PM tracks ETR's last upload, the same window.
- **For the log**: your biggest AM calls against ADP, PM calls against ETR, our biggest misses and
  splits, and the ADP movers season tally. These feed steps 3-5; they aren't shown in chat.

If you change a rule on the board's notes, change `TIER_RULES` to match (and the reverse), and
note the date in the takeaways: from then on its nights start over.

The season is the slates with last night's pod size: 4-drafter small slates and 6-drafter ones are
graded apart. Say which in the chat headline.

Your moves off the rule on untagged players are your takes (ETR show bumps, notes, gut calls),
graded as one category; moves on a player with an injury tag in that window are Q-tag reads, left
out of the takes (the tag line covers them). Pre-registered 2026-11-02: if a PM tier's takes don't beat its rule (verdict "your moves
win") by its 14th night, recommend stopping PM takes in that tier.

Monthly: on the first report of each month, also run the report with `--since` the first of the
previous month, and say whether any tier verdict differs on that month alone (October's rotations
aren't February's). Same bar; nothing changes on the monthly read alone. Also rerun
`python3 scripts/nba_residuals.py` (residual correlations for the contest work) and commit its file.

## 2b. The field

```
python3 scripts/nba_field.py --mirror ../br-adp-mirror
```

The contests themselves: every team in every main-slate contest, pulled by the nightly run's
Contests step (`scripts/nba_contests.py`, into `analysis/nba/contests/`), joined to the record's
locked-board columns. If last night has no contests on file, say so (the Contests step may have
failed: it runs after the record and doesn't stop the workflow). For the flagship contest (the most
entries) and running over every night: cut lines; where drafted% leaves 100% and the 60-99.5% and
10-60% players (priced players under 10% are news, not fades); the 5 most-owned pairs and 3 cores
with turn-pair, same-position-teammate and opposing-stars flags; your tiers in the top 1% against
the field; the field and you on players Questionable at Lock AM; your takes against the field; your
uniqueness; your results (tail ratios, AM/PM by your own lock times); what won (FPOE, breakers); and the
contest side's forward tests (`scripts/nba_forward.py`, pre-registered 2026-11-04 for slates 11-05 to 12-02,
each night kept in `analysis/nba/report/forward_tests.json`): the turns' crowding check, the Boom peer
bump's calibration, the ownership tiebreak, your teams (breakers, low-drafted picks, turn combos), Q tags
at Lock AM, and risers once the contest counts have two weeks. No verdict on the turns before 12-02.

Weighing a finding: the user's years of drafting are the prior. One that matches what they have seen can be
adopted now and tracked forward; one that contradicts it waits for more nights. Say which it is.

Pick order isn't public, so rounds are estimates; draft times are the nearest hourly ADP snapshot.
4-drafter slates are kept apart. Evidence rules as everywhere: structural rules (from drafted% and
pair rates) can be proposed on logic, with their points cost per team and the uniqueness gained;
outcome rules (anything about what wins) need pre-registration, resampling by night and a held-out
stretch. The first weeks of results are noise: say so.

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

## 6b. Hypotheses: what we learned, tested before it goes in the model

```
python3 scripts/nba_hypotheses.py
```

Every candidate learning lives in `analysis/nba/report/hypotheses.json` and moves through
watching → testing → adopted, or out as rejected / retired. Show the script's proposals in chat
in a line each, and act on them only with the user's yes:

- **New hypothesis**: when a theme from step 5 crosses its bar (3+ cases on 2+ slates), propose
  it, with a label: `input fix` (how minutes or rates are computed), `situational` (a condition
  known before tip, like a spread or a teammate out), or `matchup` (a check on our matchup
  numbers). Noise (shooting, stocks, fouls) and your own drafting habits are never hypotheses;
  the habits go in the takeaways. A hypothesis needs a rule that moves a player's projection
  using only what was known before tip; without one it stays `watching`. With a yes, write the
  rule as a function in `RULES` in `scripts/nba_hypotheses.py` and add its entry (opened today,
  status `testing`). Keep about 5 open at most: test 30 ideas and one passes by luck.
- **Adopt?** after its forward test (14 nights, 40+ players moved) beat the base model with a
  90% range above zero, and still beats it with any single player taken out. With a yes: status `adopted`, `since` today, and say where in the model it
  has to be built (that's a separate change).
- **Reject?** when it didn't beat the base model forward. Status `rejected`, with the date.
- **Retire?** when an adopted rule stops beating the base model over its rolling 14 nights.
  With a yes: status `retired`, and take it back out of the model, so nothing stale lingers.

Never change a pass bar after the results are in.

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
git clone -q https://github.com/JonBoyBeats/br-adp-mirror ../br-adp-mirror 2>/dev/null || git -C ../br-adp-mirror pull -q
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
git add analysis/nba/report analysis/nba/ledger.csv analysis/nba/form.csv analysis/nba/takes analysis/nba_takes.json scripts/nba_hypotheses.py
git commit -m "NBA report: takeaways and player notes for <date>" && git push origin HEAD:main
```

## In chat

In this order, short and scannable:

1. **Headline**: the morning and afternoon tables, with their verdicts.
2. **Tier rules**: the two tables, then one line on anything that stands out last night (a
   tier where the rule clearly beat or lost to ADP or the projection, or your moves off it).
   Until a tier has 14 nights, its verdict is "too early" and no rule changes are suggested.
3. **Ours vs ETR**: the one line, and the tag line.
4. **Field**: your results (last night's contests and the running table), the cut lines (last
   night and running), your tiers in the top 1%, the takes table, the Questionable table, then one
   line each: where drafted% leaves 100% and any news players, the top 3 pairs with flags, your
   uniqueness, what won; then the forward tests, a line each (turns, Boom bump, ownership tiebreak,
   your teams, Q tags).
5. **Hypotheses**: a line each, and any proposal (step 6b).
6. **Themes and takeaways**: only a theme that crossed its bar; otherwise one line saying none did.
7. **Last night, player by player**: only players whose ledger line carries a tag (the rest were
   in line), plus any "against the same team" lines.
8. **Missing**: anything missing from the record (no lock, no tier lines on a lock, no ETR on file,
   unmatched box scores, notes not written overnight, no contests on file) so it can be fixed.

The calls and misses from steps 3-4 are logged for the themes, not listed in chat.
