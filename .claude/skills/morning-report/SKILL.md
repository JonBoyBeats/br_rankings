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

## 1b. The report: your morning sports section

```
python3 scripts/nba_tier_report.py --mirror ../br-adp-mirror
```

It writes `analysis/nba/report/today.md`: the report on top, the season tables at the bottom. It is what the chat
posts (see "In chat"), so it is written for a phone: plain technical English in short paragraphs, readable in a few
minutes. In order:

- **Top**: a link to the standing rulebook (`analysis/nba/report/rulebook.md`, written by the script: the button's rules,
  how things are graded, the words the report uses), and one line when a rule went live on the board last night
  (`rule_dates.json`).
- **Front page**, hand-written, one paragraph of 5-8 sentences: the story of last night's slate (blowouts, late news, who
  broke it open), how your teams did (finishes, top 10%, entries and winnings), the one or two lessons, and anything to
  decide today. Never hindsight ("fading a player who then plays 4+ minutes over his usual") and never answering the
  operator ("your memory is mostly right"): the report is built every day, not in reply.
- **What decided the night, and where you stood** (built): the 4-5 players whose holders moved the contest most, your
  share against the field's, which of your moves faded or backed them, one verdict line.
- **Your biggest bets and fades** (built): overweights cut at the natural gap (3-5), underweights the same in T1-T3;
  each with share against the field, why (a move's source, a note, VALUE/PRICEY, the button), what the close did after
  your lock (ETR's final, the late ADP), the result, and "sound/shaky and won/lost".
- **Each tier** opens with its theme and rules in two or three lines (no statuses, counters or leanings). T1: how the
  night went (where ADP and the projection split, which side the night and you took), recap, contest view. T2: how the
  night went, your moves, the turn lines (card_decisions), recap, contest view. T3/T4: how the night went (who to trust),
  your moves, recap, contest view (with your VALUE share). T5: the menu on contest results (round-6 picks drafted in
  under 60% of pods against 60%+, you against the field, last night and season), recap, contest view. "Your moves" is
  one question per move (did you go against the button, and did it help, on the pair it changed; Q moves left out) and
  one season line per tier: keep doing what you're doing / press the button / too early. Recaps in the button's order.
- **Questionable**: last night's Q players at the lock (where the button put them, played or sat and the swaps), your Q
  moves graded, the Swap button's line, the chance-to-play tracker, today's Q players with play chances and beneficiaries.
- **Back page**: our morning projection against ETR's final, ETR's final against the box score, Gallagher's Bad-matchup
  arrows (published before your lock; logged to `gallagher_arrows.csv` for the Friday report), data notes.
- Gone: the status definitions and "in every tier" blocks (in the rulebook now), the separate draft card, Monday
  proposals (the Friday report has them), 14-night counters.

**Words, not codes.** The report never shows register ids, rule codes or verdict labels. Every verdict says which way:
RULE is "proven to help so far" or "proven to hurt so far", LEAN "an early sign it helps" or "an early sign it hurts"
(contest results the same: "contest results: an early sign it hurts"); never a bare "proven so far". No lean is "no
clear signal", not enough "too early to say" (with the pair count when small: "only 21 pairs"), provisional "on trial".
About 2,000 words in all: per tier, the recap is overs, unders and scratches with the reason only; "did they work" is
last night in a sentence or two plus one season line; the contest view one sentence. The front page ends with your
three biggest bets against the field and how each went (generated). Points are
the rankings grade, contest results the money grade. Rules are said in words ("In the afternoon, T2 is ordered by ADP,
and ETR breaks ties when two players are within two picks of each other"), and every number carries its meaning in
the same sentence. A new tier idea gets a `plain` line in `hypotheses.json` (one sentence, no codes) and a short `name`, and a new
switch a line in the script's `SHADOW_WORDS`/`RULE_WORDS`.

**The hand-written parts** go in `analysis/nba/report/morning/<night>.json` (the nightly runs keep them; the script
fills everything else from the files):

```
{"front": "the front page paragraph",
 "moves": {"2": "a sentence or two on why your moves in T2 went the way they did"},
 "back": "a decision or note for the back page",
 "proposals": {"<decision id>": "your recommendation, when it differs from the script's"}}
```

Write it **after step 7** (the recap reads the ledger's notes, and "your moves" the calls logged in step 4), then
re-run the script. The front page is the one part always written by hand; the others only when there is something
the numbers don't say (a reason, a pattern across tiers). Use only numbers the script, the field section or the
earlier steps printed.

**The record of each window** (the daily record, `scripts/nba_daily.py`): your manual Lock AM and Lock PM. The AM
window starts at 4:30am PT; drafts before then (the night before included) are the OVERNIGHT window, labelled, kept
out of the AM grades and graded on their own (your board saved before your first overnight draft against ADP then;
the report's season section). A Lock AM counts when pressed by your first draft at or after 4:30am (the contest
rosters' draft time, plus half an hour since draft times are the nearest hourly ADP snapshot; noon PT when you drafted
no AM teams). With more than one Lock PM, the last one before swaps (the slate's first tip) counts. Fallbacks only
when you didn't lock, labelled "fallback" in the history and the report: AM, the last board saved (or Tiers build) in
the AM window (from 4:30am) by then; PM, the last export before contests close, else the last board saved before then. Swaps are graded from the contest data (your real
swaps and the inferred app order), never from a lock. Nights before 2026-11-10 carry the old fallbacks, labelled
"fallback (old rule)".

**Sources.** When the user pastes Gallagher's (ETR) or Zakarian's (Bagel) columns, save them as
`analysis/nba/takes/<date>_etr_matchups.csv` (or `_etr_top_plays.csv`) and `<date>_zakarian.csv` with an `at`
column: when the column came out if the text says so, else when it was pasted (ISO time, like ETR's uploads).
Then `python3 scripts/build_takes.py`. A take (your order against the button on a decision pair) is credited to
ETR or Bagel only when your move matches their note, stamped (`at`) on the slate's day and before that window's
record (the lock, or the save it fell back to); a note from an earlier day never counts: you moved up a player the
note likes (Great, Good, Like, Lean) or moved down one it fades (Bad, Fade); a plain Note credits no one. Else NEWS
(his projection or his team's status changed since the last lock); else OTHER (`scripts/nba_tier_takes.py`).

Every number comes from the script; don't recompute any of them.

**Money verdicts.** The contest side writes a MONEY verdict (top finishes and dollars) into
`decision_register.csv` (`money_verdict`) beside our POINTS verdict. Everything adopted or kept,
switches and leans alike, is provisional until its money verdict is in, and may be changed by it
(`leans.json` "money_policy"; each entry's `register` field names its row). Say so wherever a rule's
status is given. Points and money together:

The money bar (the contest side uses the same): **MONEY LEAN** is at least 80% of slate resamples
in the same direction on top-10% lift or average finish percentile, with enough teams in the cell;
**MONEY RULE** is a 90% range above zero on the same reader, the same direction in the check slates.
Money clears its bar at MONEY LEAN or better; to overturn a points RULE, money must reach MONEY RULE.
The contest side's verdicts say LEAN or RULE and which reader they rest on; quote both.

| Points | Money | Do |
|---|---|---|
| positive | positive | keep |
| positive | pending | keep, provisionally |
| positive | negative | drop only if money is at least a MONEY LEAN (a MONEY RULE when points is a RULE); otherwise keep |
| negative | positive | keep only if money is at least a MONEY LEAN (a MONEY RULE when points is a RULE against it); otherwise drop |
| negative | negative | drop |

Every change still needs the user's yes.

**A proposal from the contest side** (the user brings it over): before changing anything, check
(1) its points cost on the same decision pairs: grade it against the current rule on the 6-drafter
decision pairs in its window and tier the way `nba_tier_rules.py` grades a candidate, with the pairs,
the 80% range and the label; and (2) its shadow record: its comparison in `shadow.md` if there is one,
else add it to `nba_shadow.py` and give the season-in-sample line, saying it has no forward nights yet.
Show the user both beside the money evidence and the table above's call, then change only on a yes.

**The loop.** Ideas for a tier live in `analysis/nba/report/hypotheses.json` under `"tiers"`. Each new idea is
written with its test before any grading: its tiers and window, the alternative order (rule steps, or a pairwise
function in `scripts/nba_shadow.py`), what it's graded against (the button) and the bar, with `status` "testing" and
`forward_from` the next night. At most 3 ideas under test per tier (the shadow refuses more); the rest wait as
"queued". The shadow grades them nightly (`shadow.md`, `shadow.json`). An idea marked `split_windows` (T2-1) is
graded as one row per window (`<id>:am`, `<id>:pm`) and decided per window at its Monday call: one window can be
adopted on its own forward read even if the other isn't.

**Monday proposals** (the report shows them on Mondays only, each with a recommendation): a provisional switch at 14 forward nights is
kept if it beat the old rule there, else dropped (the T5 tiebreak is dropped only if it lost: its points cost is a
known price for a money RULE); an idea at 14 forward nights is proposed for adoption at a forward LEAN or better when
its money verdict isn't against, else dropped; an idea leaning against early may be dropped early; a free test slot
with a queued idea is offered; an adopted rule with money against is proposed for dropping under the money table
above. The contest side's weekly money proposals (`analysis/nba/report/money_proposals.json`) are listed in the same
section, so the user approves everything in one place ("no money proposals this week" when the file is missing).
Change the board, `leans.json` or `hypotheses.json` only with the user's yes.

**Monthly re-check** (the first report of each month; the report flags it until `recheck.json` names the month): rerun `nba_tier_grade.py`,
`nba_tier_rules.py`, `nba_q_lane.py` and `nba_backtest_rest.py` and read each adopted lean, rule and
provisional switch against the bar it was adopted on (LEAN: 40+ pairs, 80% of resamples; RULE: 80+
pairs, a 90% range clear of zero, the check slates, the drop-one test), then beside its money
verdict from `decision_register.csv`, through the points-and-money table above. One that no longer
clears its points bar, or that the table says to drop, is proposed for demotion in chat with both
sets of numbers, and changed only with the user's yes. Every entry still at "money pending" is
listed as provisional. Never move a bar after the results are in. When done, set `recheck.json` "last" to the month.

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
python3 scripts/nba_field.py --mirror ../br-adp-mirror --summary
```

The contests themselves: every team in every main-slate contest, pulled by the nightly run's
Contests step (`scripts/nba_contests.py`, into `analysis/nba/contests/`). The nightly job's Field step
also writes the whole section, with every table, to `analysis/nba/report/field.md` and records the
night's forward-test numbers (`analysis/nba/report/forward_tests.json`). If last night has no contests on
file, say so (the Contests step may have failed: it doesn't stop the workflow).

The morning report reads **only the contest summary** (`--summary`): about 6 lines.

- **Your results**: your teams' tail ratios against the field (1.00 is the field's rate), 6- and 4-drafter
  apart, with 80% ranges; AM against PM teams at the top 10%; last night's contests.
- **Forward tests** (`scripts/nba_forward.py`, pre-registered 2026-11-04 for slates 11-05 to 12-02): the
  less-drafted tiebreak (a rule in use), Questionable at Lock AM drafted before against after noon, the
  most-owned turn combo against the rest, the Boom peer bump, risers. A line each. **Nothing is decided
  before 12-02**: don't call a verdict, don't suggest a rule change from them before then.
- **Last night, where it touched a rule**: your takes off the tier rules against the field, and the
  players Questionable at Lock AM (played or sat, on how many of your teams).

The full tables in `field.md` (cut lines, ownership, pairs and cores, tiers in the top 1%, uniqueness,
what won) are reference: don't summarize them in the daily report. Open them only when the user asks
about a night, or when a summary line needs explaining. "What won" (top teams had more breakers) is
true by definition and never a takeaway.

Weekly, on the first report of each week (Monday's, or the first after it): add one short "Contest
week" bullet to the takeaways: each forward test's running number against last week's, and your results
by pod size against last week's. Say only what moved; no verdicts before 12-02.

On 12-02's report (the window's last night): give each forward test's verdict from `field.md`'s
section 10 against its pre-registered bar, and for each rule it touches (the less-drafted tiebreak,
early Q tags, the turn combos) what to keep, change or drop. The user decides.

Studies the summary points to are in `analysis/nba/report/field_studies.md`. The 4-drafter AM tail
(section 7, scripts/nba_ampm_study.py): on 2026-11-09, AM teams 0.77 at the top 10% against PM 1.74,
with equal ETR value at lock, so no draft flaw showed; look again at 10 4-drafter nights.

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

### Morning Proj vs ETR (one bullet in the takeaways)

Read `analysis/nba/report/etr_match.md`. The 2:17am job rewrites it (`scripts/nba_etr_match.py`,
whose docstring has the definitions). The morning Proj's job is to match ETR's final number (your
call, 2026-11-13): the market drafts off it at lock, and getting there before the market is the CLV.
So it scores our Lock AM Proj against ETR's last upload before lock (until 11-13 the first upload,
which carries a random multiplier; uploads after 2pm PT don't), both read against ADP: a player's value is his projection minus the average of the 6 players
nearest him by morning ADP, so the two scales never need to match. Only slates where Lock AM came
before ETR's first file are graded, top 60 by morning ADP (40 on 4-drafter nights). It is a
scorecard for our morning number: it changes no grading and no rule.

Add one bullet, "Morning Proj vs ETR", to the night's takeaways section:

1. Last night's row in "By slate": direction, big misses, and anything unusual (a CLV gap, a
   cluster of one team in the biggest misses).
2. Name everyone on "Missed the same way on 3+ of the last 10 slates". That's where a
   player-specific look pays off.
3. Weekly, or when a group's direction or big-miss share moves 5+ points: compare Season against
   Last 7 slates by group.

Late news isn't the model's miss (a Questionable tag resolved after Lock AM, a rotation change):
that's the Lock PM's job. Use the tag and minutes columns in "Biggest misses" to tell, and say so
rather than counting it.

Baseline against the final upload (15 slates, 10-28 to 11-12): corr 0.78, direction 87%, big
misses 24%, CLV ours 0.15 vs ETR 0.33. ETR's own first upload lands within 0.8 points of its final
on average, ours 2.1: that is the gap to close.

**The ETR review, every couple of weeks** (on a Friday, when asked): no forward tests for these.
Rerun the study in `analysis/nba/report/etr_gap_study.md` on everything since the last review
(where our morning number and ETR's final differ, by player, team and position, and what
explains it), try the tweaks that would close the gap on those slates, bake in the ones that do
(in index.html's NBA morning Proj, with the numbers in its comment), add a dated section to the
study, and carry on. 2026-11-13: box scores count as 3 days of ETR (was 1), their minutes halfway
to his last 3 games: 2.10 -> 1.88 points from ETR's final, 3+ apart 24% -> 20%. Also 11-13: a teammate out for the first or second night moves his teammates 1.5 times the table.

Old baseline against the first upload (8 slates, 10-28 to 11-05): direction 88% (elite 100%, next 83%, middle 93%, 6th round
on 86%); ETR's bottom 5 we had below 40 of 40, top 5 above 37 of 40; big misses 24%; CLV ours
0.22 vs ETR 0.33, widest in next (0.22 vs 0.50); rookie gap +2.9.

Rookie forward check: from the 11-07 slate the board averages a player with no last season over
his last 3 ETR nights instead of 10. The replay on 10-28 to 11-05 cut the gap from +2.9 to +1.6,
but on the same nights that showed the pattern. So "Rookies, before and after" is the check:
report the "from 2026-11-07" row once it has 15+ entries, and if the gap hasn't come down by about
11-21, flag it to take back out. Players who changed teams or moved 5+ minutes keep the 10-night
average: tested, and a shorter one made them worse.

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

Post the report from `today.md` as it stands, from the title down to "Season" (the season tables stay in the file),
after re-running the script with the morning file written. Nothing else, except one closing line for anything that
needs the user and isn't already on the front page (a proposal awaiting a yes, something missing from the record).
The scores tables (step 2), the field section (2b), the calls and misses (3-4), the themes (5) and the takeaways (6)
feed the report and the logs; they aren't posted on their own. On the first report of the month, add the re-check
(step 1b's "Monthly re-check") after the report.
