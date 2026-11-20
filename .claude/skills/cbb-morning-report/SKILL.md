---
name: cbb-morning-report
description: College basketball (CBB) morning report, Underdog and DraftKings. Grades last night's college projections against the box scores (ours, ours without EvanMiya, Underdog's; on DraftKings ours against DraftKings' average, fragility, double-doubles), splits our misses into minutes and points per minute, writes up the biggest misses with a cause and logs them, reads last night's college contests (cut lines, your results, what the field did), and keeps the EvanMiya trial's running verdict. Use when asked for the college, CBB or college basketball morning report.
---

# College basketball morning report

The 2:17am PT nightly job (`.github/workflows/nba_daily.yml`, its "CBB record" and "CBB contests"
steps) writes last night's college slate to `analysis/cbb/daily/<date>_<day>_main.csv` (our
projection at lock against ESPN's box scores, `scripts/cbb_daily.py`), each DraftKings Classic slate
to `analysis/cbb/dk/<date>_<draft group>.csv` (our DraftKings projection as it stood before the first
game against what DraftKings paid, bonuses in) and its Underdog contests to
`analysis/cbb/contests/` (`scripts/nba_contests.py --sport cbb`). Either site can run alone or
both the same night; the report covers whichever has a slate. This report reads them and keeps
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

**DraftKings** (the report's DRAFTKINGS part, when there's a DraftKings slate):

- **Accuracy**: ours (DraftKings points, the double-double bonus at its chance), ours without
  EvanMiya, and DraftKings' season average (what the field sees) against what DraftKings paid: for
  players who played, for everyone not tagged Out (a player who sat scores 0, as in a lineup), by
  salary band and by build.
- **Fragility**: expected miss against actual, and fragile against the rest as a share of their
  projection (2025-26: 49% against 35-36%). Give the season line; once it has about 300 players
  projected 10+, say whether the fragile tag still separates.
- **Double-doubles** expected against had, and the **200-minute cap**: minutes off after the cut
  against before it, for the players it cut.
- **Watch, EvanMiya rank**: miss as a share of projection by rank band, within under-20 and 20+
  projected minutes. On the two Underdog nights of 11-03 and 11-04, ranks 8+ missed by more in
  both (83% against 63%, 49% against 37%). Around 2,000 player-games (about two weeks of slates),
  propose it as a fragility fact if it holds, tested the way `scripts/cbb_form_study.py` tests
  the four, and make no change without the owner's yes.
- **Misses** of 8+ among $5,000+ or projected 20+, and players $4,000+ not tagged Out who sat.
- **One projection, both sites**: minutes and points per minute over every player either site
  carried. This is the line that says whether the projection itself is improving.

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

DraftKings misses go in `analysis/cbb/report/dk_misses.csv`, the same causes, with this header:

```
date,draft_group,player,team,salary,ours,ours_wo_miya,dk_avg,actual,min,min_proj,min_raw,fragile,own,spread,src,cause,fixable,note
```

The automatic log beside it (A3, all five lenses: minutes, shape, Vegas, salary gaps, ownership, each miss with
reason tags; rebuilt nightly): `python3 scripts/dk_eval.py misses` prints last night's rows from
`analysis/cbb/dk/misses.csv`. On Fridays, `python3 scripts/dk_eval.py misses --friday` gives the counts by tag for
the week; a tag that recurs is a candidate fix under A2, tested first and adopted only with the operator's yes.

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

**DraftKings**: when the owner has dropped a contest's full standings CSV (it lists each player's
drafted %), compare it with `own` in last night's DraftKings file: projected ownership against
actual, biggest misses both ways. The field model's two guesses (`FIELD_W`, `FIELD_NOISE` in
battle-royale-research `scripts/dk_cbb_field.py`) get fit from these once a few slates are in;
until then, report the gap and propose nothing.

**Underdog**:

```
python3 scripts/nba_contests.py measures --sport cbb --mirror ../br-adp-mirror --date <last night>
```

For the biggest contest: cut lines (win, top 1%, median, top 1% over median), the drafted% bands
and the first priced player the field left in some pods, value (FPOE and breakers, field against
top 1%), the most-owned pairs and cores, your uniqueness, draft times, and your results (median
finish, tail ratios, payout). If `analysis/nba/expo.json` has your exposures for the slate, set
them against what scored. Rounds are estimates (pick order isn't public). The first weeks of
results are noise: say so, and propose no rule from them.

## FREEZE on the DK tools (the owner's revised freeze, 2026-11-16)

Week 1 (through 2026-11-23) is open for tweaks to anything. After that, until about 30 graded slates, these
are frozen because they're graded: **the sim model, the quadrant recipe and its lines, the five shadow rule
sets, and the portfolio pick** (`dk_sim.js` simulate / pick / RULESETS / BASE, `dk_cbb_field.py`,
`dk_cbb_teams.py`'s scores and quadrant). Open any time: the page's layout and buttons, the bank / cut /
review / export workflow, speed, and bug fixes. The 30-slate count starts at the freeze: graded rows on
slates through 2026-11-23 are tagged `phase` warm-up, with the `version` (both repos' commits) they ran on,
and the readout counts only `counted` rows toward the decision. Anything new for a frozen part, however
good, goes in `analysis/cbb/dk/ideas.md` (dated, with why it came up) for the review. Don't propose new
features in the report; point to that file.

## 6b. DraftKings standings, the shadow test, and the monthly readout

**When the owner sends a DraftKings standings CSV**: save it unchanged as
`analysis/cbb/dk/standings/contest-standings-<contest id>.csv` (the name DraftKings gives it), commit and
push; the 2:17am job grades it (`scripts/dk_eval.py nightly`), or run it now:
`python3 scripts/dk_eval.py nightly --mirror ../br-adp-mirror`.

**When the owner sends a saved build** (`dk_bank_<day>_<draft group>.json` from the DK page's Save build: the
night's bank of drawn lineups, each tagged with the idea it was drawn under, the final cut and each contest's
portfolio): save it unchanged in `analysis/cbb/dk/builds/`. The owner's own entries are graded against the bank
as their pool (random sets of the same size from it); without one, against No extra rules' shadow pool. Older
`dk_build_*` files (the page's former portfolio builder: a pool, a hand-built 20, an auto-pick) still grade as
`hand` and `auto`; the page no longer makes them.

Older `dk_entries_*` files (the former Save lineups + rules) go in `analysis/cbb/dk/builds/` too. The slate's
last saved file says which rule templates the owner used that night (the bank file's `rule_set`: every rule any
draw used); the monthly readout shows his results on nights each was used (directional only).

**Nightly**, give one line only: which standings were graded, and the projection gate's state
(`analysis/cbb/dk/gate.json`). No rule-set verdicts from one night.

**Injuries, daily (owner, 2026-11-17):** `cbb/inputs/outs.csv` in battle-royale-research is filled every day from
EvanMiya's injury reports (the matchup previews the owner sends): one row per player, date, the team's DraftKings
abbreviation, name, Out or Questionable, source. An Out regular (20+ minutes, 2+ games) has his minutes handed to his
teammates by the projection (team_minutes); a player Out with 0 games this season changes nothing. The file's Out
wins over DraftKings' Questionable.

**EvanMiya uploads, daily (owner, 2026-11-18):** three files only: the Skills Leaderboard, Player Ratings and Team
Ratings. File each unchanged under a new date: `cbb/inputs/evanmiya/<date>_skills.csv`, `<date>_ratings.csv`,
`<date>_team_ratings.csv` (never edited, never overwritten). Not needed: indispensability, and the per-team pages
(game analysis, on-off, lineups); ESPN box scores and team ratings cover them. After filing, trigger the projection
refresh (battle-royale-research `nba_adp_poll.yml`) and confirm in the mirror's `dk_cbb_morning.json` that
`evanmiya` names the new date's files and every slate player's game matched (no DraftKings-average fallbacks).
EvanMiya rows join on his Player ID (name and team for files without one). The DraftKings rate keeps EvanMiya's
all season (`MIYA_RATE_W` 0.35, from `scripts/cbb_miya_rate_study.py`); rerun that study as dated team ratings come
in, for the opponent-adjusted rate it can't judge yet (the first team ratings are 2026-11-18's).

**Calibration week (through 2026-11-23): the calibration note comes first in the DK part.** Run
`python3 scripts/dk_eval.py calnote --mirror ../br-adp-mirror` and give it short (a MATCH WARNING line, players whose
game found no ESPN match and sit on DraftKings' average, goes first and plainly; fix the matching before lock): bugs found, the audit's a / b / c in one line each, and any
change made with its reason. One-night results don't drive changes; principled, reversible tweaks do, and every
change goes in `analysis/cbb/dk/versions.csv` (date it takes effect, version, component, change, reason; numbers in a
reason are computed, never recalled) so the readout can split slates by version. Rules and shadow rule sets stay as
they are. Run `python3 scripts/dk_eval.py fieldcheck --mirror ../br-adp-mirror` first when new standings came in after the
nightly job, so the note's field line (the simulated field against last night's biggest graded contest, side by
side: duplication with another user, distinct lineups per 1,000, salary used, players 30%+ owned, the top one's
ownership, 3+ from one team) is current. The note includes the cut check: kept against cut, average score and each contest's top-10% rate, and how
many nights "kept averages more but reaches the top 10% less" has held.

**The ownership card, every morning (the owner, 2026-11-19):** `python3 scripts/dk_eval.py owncard` (after
fieldcheck). Ownership is the main $15 contest's (the Pull Up Jumper, not the Early one); the And-One, Quarter
Jukebox and Dime Time are shown against it. Give it as one short card: the headline "projected under 5% landed under
5%"; the 3 bands (under 5, 5-20, 20+) with actual / projected, the miss and how many nights ran over; projection
misses by the same bands; the leverage list (under 5% owned beating ours by 8+, 25%+ missing by 5+, with minutes,
points a minute and teammates who sat: a low-owned player who beat us is worth a cause); and the construction rows
(real, sim, bank, cut, entered, dbaggot3, feartheturtle7: 3+ from a team, low / high owned a lineup, summed
ownership, salary, shared lineups). Settings change only on the 3 bands, and only when most nights ran the same
way; the 5 bands are for reading. The owner keeps an entry in the Pull Up Jumper each night so its standings can be
downloaded (a night without it falls back to the biggest graded contest, and the card says which).
Under the card, the shape audit (B1, 2026-11-20): `python3 scripts/dk_eval.py ownaudit`: team sums (rank, miss,
real / projected for our top 3 teams), within a team (our most-owned the real one, order of the top 4, the #1-#2 gap
ours vs real), the top-5 hit and the 3 bands, and duplication real vs simulated on news and quiet nights. Shape, not
exact percentages; its biggest team misses are in the misses log.

**News sources and team cards, every morning (2026-11-19):** battle-royale-research's day's news read suggests
candidate X sources for tonight's teams with none listed (cbb/news/suggest/<date>.txt: the accounts naming the most of
a team's players, with followers and bio; 6 teams a day, each once). Vet them: a beat writer, the team's own account
or a school site, not a betting or aggregator account; add the keepers to cbb/inputs/news_sources.csv (espn_team,
school, handle, kind, added, note) and say which teams still have none. Check the DK page's team cards built (each
team's tile in mirror/dk_cbb_teams.json has a card with its game count); say how many deep-bench players are out
of the pool by default.

**From early January (conference play):** start the planned availability-report reader (analysis/cbb/dk/ideas.md,
2026-11-19): first say whether the conference reports are out yet and what form they're published in.

**The slate scan, graded (log only, 2026-11-19):** `python3 scripts/dk_eval.py scan`: when the night's build carried a
scan, give its two lines (the scan's top third of stacks against its bottom third on the real top 10% / top 1%, and
team stacks by tile verdict). Nothing changes on it until a couple of weeks of nights say which ranks stacks better.

**Mechanics freeze with the rest on 2026-11-23** (the owner, 2026-11-17): the draw (sim-night draws, Leverage
weight), the cut within each idea, the tie split, the pick (exposure, core and pair caps, unique entries) and the
night view. After it, effort moves to inputs, in this order: projections (minutes, news), ownership, the FIELD (the
simulated field's shape against the real one: dk_eval.py fieldcheck, battle-royale-research
scripts/dk_field_calibrate.py), player ranges, then late swap. Mechanics ideas go in `analysis/cbb/dk/ideas.md` for the 30-slate review.

**Duplication drift, every morning until the freeze:** the note's field check ends with "Duplication in line" or
"DUPLICATION DRIFT" (the simulated field's rate against the range of the night's real contests). On drift, say so in
the note, plainly, with the numbers; don't refit on one night (that waits for 11-22).

**The field refit, 2026-11-22 (before the 11-23 freeze):** in battle-royale-research,
`python3 scripts/dk_field_calibrate.py --br ../br_rankings --grid week` (every candidate on all the week's graded
nights together; ~20 candidates x 17 s a night). Freeze the setting that fits them together: write it into
`scripts/dk_cbb_field.py` FIELD_STYLES (keep the current one if it's the best or within noise of it, and prefer one
that doesn't duplicate the owner's entries more), log it in `analysis/cbb/dk/versions.csv`, and report the week's
fit night by night: duplication with another user, salary used, at the cap, the top player's ownership, 3+ from
one team.

**At the freeze (the 2026-11-24 report):** the 50/50 projection blend does NOT end by itself. Run
`python3 scripts/dk_eval.py calweek` (ours, DraftKings' average and the blend over the week's graded nights: average
miss, bias, rank correlation by salary band, and the nights each had the lowest miss), show it, and ask the owner
which one freezes. Until he chooses, the blend stays on. Record his choice in `dk_eval.py` PROJ_CHOICE ("ours", "dk"
or "blend") and as a line in `analysis/cbb/dk/versions.csv`.

**The audit, nightly, first in the DK part of the report** (`python3 scripts/dk_eval.py audit`): projections and
ownership come first; the sim's grading waits for enough slates. Give its short lines as they print, last night
and the season: (a) our projection against actual DraftKings points (average miss, bias, rank correlation) beside
DraftKings' average and the last-5 average; (b) projected against actual ownership; (c) the field against our value:
where it disagreed by 5+ points, how often it was right, and whether the readout flags FIELD KEEPS BEING RIGHT (only
when it's right well beyond chance and on 2/3+ of 5+ slates; say "directional" for anything short of that).

**The cut check, nightly** (`python3 scripts/dk_eval.py cutcheck`, run by the 2:17am job after the record;
rerun it in the report once new standings are in, since it rebuilds `analysis/cbb/dk/cut_eval.csv` whole):
for last night's saved bank, by rule tag, the lineups the cut removed, kept and entered, scored on the real
points: count, mean, best, and against each entered contest's real lines the share reaching the top 10%,
cashing and winning. Report it briefly: did the cut remove lineups that beat the best entered one, and which
tags lost the most (mean and best of cut against kept). One night is anecdote; say so.

**Risers vs fallers, nightly** (`python3 scripts/dk_eval.py risers`, run by the 2:17am job; rerun it with the cut check
once new points are in): the owner's question whether the players the cut raises (kept share above bank share) are the
ones to be overweight on. Give its two lines (also in the calibration note): last night's risers against fallers on
actual minus projection with the rank correlation, and the running count of nights risers beat fallers. The night is
the unit; under 10 nights say it's too few to call.

**Random fills, nightly** (`python3 scripts/dk_eval.py fills --mirror ../br-adp-mirror`, run by the 2:17am job; rerun it
once new standings are in): random fills of the owner's own entry counts from the bank, the cut's kept and removed
lineups and each kept idea, paid against the real fields. Give its two lines (also in the calibration note): last
night's entries against the average fill from each subset (and how often a kept fill beat them), and the running count
of nights the kept fills' average beat his entries. The night is the unit; under 10 nights say it's too few to call.

**The Auto-fill benchmark, nightly** (graded by `dk_eval.py nightly` as `auto_kept`, from the build's `auto_portfolios`,
which Save build records: what Pick portfolios would have entered from the same final pool, entry counts and pick
settings). Give the calibration note's line: his entries against it last night, and the running count of nights it
beat them. It answers whether hand picking adds anything over the automatic pick; under 10 nights, too few to call.

**Platoon rules, nightly** (`python3 scripts/dk_eval.py platoon`, run by the 2:17am job; from the build's `rule_log`).
Platoon rules stay global (the baseline). Give the calibration note's two lines: each platoon rule last night (the
pair both over, both under or split against projection; lineups it blocked of the draws' rule-free ones; the projected
and the real cost: blocked lineups against the banked ones), and the flags once a pair spans 14+ days (never binds,
never held). A flagged rule is the owner's call to drop; one night says nothing.

**Platoon pair sets, nightly** (`python3 scripts/dk_eval.py pairs --mirror ../br-adp-mirror`, run by the 2:17am job):
the tiles' pairs by EvanMiya's position bands and role (from 2026-11-18) against the ESPN G or F/C set computed beside
them, each graded split (one over projection, one under) or moved together, with any two rotation teammates as the
baseline. Give its lines; at 5 graded slates with both sets, report the comparison to the owner so the band cutoffs
(2.33 / 3.67, role gap 1.0, battle-royale-research dk_cbb_teams.py) can be checked against data.

**Monthly** (the first report of each month, and at 30 graded slates): first `python3 scripts/dk_eval.py
weights` (refits Quality's weights on the earlier 2/3 of the logged slates, tests them on the later 1/3, and
switches the tiles to them only if they beat equal weights there; commit `analysis/cbb/dk/team_weights.json`),
then `python3 scripts/dk_eval.py readout --sim-z ../br-adp-mirror/dk_cbb_field.json`. It leads with the audit in
full (projections and ownership first, the owner's priority): (a) projections by salary band, ours against DraftKings'
average and the last-5 average, last night and the season; (b) ownership by projected band; (c) the field against our
value, by size of the disagreement, then where the field was right by salary band, position and minutes change.
Report those first. Then, in this order:

1. Each rule set and the owner's entries: top-10% rate, cash rate, then dollars as the long-run check;
   each rule set against "No extra rules" slate by slate (slates won, paired gap), never pooled totals.
   Then every portfolio against 1,000 random sets of its size from its own pool: the mean percentile
   over slates (no skill is ~50) and slates beating the random median; the pick against the pool's top
   20 by value alone, and hand-built against auto-pick, slate by slate.
2. Projected ownership against real %Drafted by band.
3. The sim's players against reality: where real scores fell in the sim's range by tenth, the
   correlation of misses (teammates, opponents; the sim takes both as 0), game-total spread.
4. The projection gate.

It also grades the team tiles' quadrants (FOCUS / CHALK / LEVERAGE / FADE; `analysis/cbb/dk/tiles_eval.csv`
and `team_eval.csv`, written nightly) on three targets: the top 5 by salary beat their salary-implied
points; the team's actual points share beat its real ownership; 2+ of its players in the contest's top-1%
lineups against the field's rate. Report each quadrant on each, and the Quality weights line (fitted
against equal, on held-out slates). If FOCUS doesn't beat the others, say the quadrant recipe
(`scores()` / `quadrant()` in battle-royale-research `scripts/dk_cbb_teams.py`) needs revisiting and
propose a change, tested on the logged tiles first; make no change without the owner's yes. And the correlation check covers teammates and opponents of a
team's #1 on nights he busted (the pivot and bring-back rules lean on it).

The rule sets are frozen (`RULESETS` in `dk_sim.js`, 2026-11-16): no new ones and no changes until the
decision. **The decision at 30 graded slates**: does any rule set, or the owner's entries, beat the
field's top-10% rate (10%)? If none does, recommend cutting back. Before 30, report the numbers as
directional only.

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
   season line under it; for DraftKings, ours against DraftKings' average, the same way.
2. **Where we missed**: minutes or points per minute, and newcomers against the rest.
3. **The misses**: a line each, with its cause.
4. **The field**: the cut lines, your results, and one thing that stood out.
5. **EvanMiya trial**: the running line, and days left.
6. **Themes and takeaways**: or "too early" while the log is thin.
