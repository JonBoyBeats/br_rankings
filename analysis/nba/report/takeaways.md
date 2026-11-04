# NBA takeaways

Written by the morning report (/morning-report), newest first. Each section: last night, any theme with 3+ cases on 2+ slates in misses.csv, and a change to try when a theme backs it.

## 2026-11-04 Rule change

- Adopted the ownership tiebreak on the user's experience (contest side's study, field_studies.md section 2): in the afternoon T5 rule, within 2 points of ETR and 4 picks of ADP, the player with the lower projected drafted% goes first when they're 10+ points apart (both at least 2%). The board's T5 note now reads "Sixth Round – Proj (3: ADP) then ETR (2: less drafted)". PM T5's nights start over from 2026-11-04 (RULE_SINCE in nba_report.py). The morning T5 rule is unchanged: the study defines a tie on ETR, and in the morning projected drafted% just follows ADP.
- The forward test keeps running as the check (nba_forward.py, slates 11-05 to 12-02): take it back out if the 80% range of the top-1% difference ends below zero.

## 2026-11-02 Mon main

- First night with tier lines on both locks (Lock AM 8:24am, Lock PM 2:15pm), so the tier-rule forward test starts here (1 of 14 nights). Jalen Johnson (ADP 19.7, Questionable all day) was ruled out after the PM lock, so ATL is left out of both halves. The leaderboards show picks after swaps: the field had him on 0.3% of teams, you on none.
- Morning: your board edged ADP (55%; season 54%, your board wins, range 51-57%) but trailed our number (46%; season 58%). Afternoon: 53% against ETR; with ATL out, the season is 47% (44-50%), back to too close to call. Your PM raises on Curry, Dosunmu (both on minutes above their usual), Caleb Wilson and Bam were right; the Brunson raise and the LaMelo fade on his Questionable tag (he played 33 and scored 34) were wrong. Season log of PM calls, hedges aside: 24 right, 30 wrong.
- Blowouts again: SAS (-16.5) won by 22 with Wembanyama at 24 minutes, Fox 22 and Castle 26; Keyonte George played 22 in the loss; Embiid played 25 in a 19-point win. The log now has 22 blowout misses on 6 slates, ours too high on 21 of them, but only 5 had a 10+ spread before tip, so the spread rules (H2-H4) can only ever catch a slice. H2 still reads "retire?" at 8 nights (-0.13); hold for the full 14.
- Field (first night joined to your tiers): 85 teams, median finish top 53%, top-10% tail 0.86 in the flagship. Noise for weeks yet.

## 2026-11-01 Sun main

- Early three-game slate (lock 1:52pm), one ETR upload (12:57pm). Poeltl and Ziaire Williams sat after the PM lock and Toppin after the AM lock, but none was being drafted early, so the whole slate is graded and calls on their teammates are logged as hedges (revised 11-02: late news only takes a team out when the scratch was drafted in the first two-thirds).
- Morning: ADP beat your board (40%); the Brooklyn reads missed (Traore fade 0 of 6, Ellis raise 0 of 3) and the Gui Santos raise hit a 9-minute night on a probable tag. Afternoon: 47% against ETR and 44% against ADP. Season: your board against ADP at lock is back to too close to call (52%).
- The blend at Lock PM is 0% ours: our number adds nothing to ETR's at lock so far. Not settled, but heading there.
- Boom 4+: too early, morning (218 moves, 41%) and afternoon (442 moves, 46%).

## 2026-10-31 Sat main

- Late-news night. Dejounte (ADP 16.8) and Jerome (17.7) were ruled out after the PM lock, so NOP and MEM are left out of the grading (analysis/nba/report/late_news.json). Gobert, VanVleet and Sheppard also sat late but weren't drafted early, so MIN and HOU stay graded and the calls on their teammates (Kuminga, Beringer, McDaniels, Eason) are logged as hedges.
- Your boards: AM beat ADP on 58% of disagreements and our number on 60%; PM split with ETR (51%) and lost to ADP (41%). Raises on Ware, Mara and Harper were right; raises into blowouts (Wiggins, Ajay, LaVine) were wrong.
- Blowouts are now a full theme in the log (final margin 15+, known only afterward): 13 of the 16 blowout misses were 30+ minute starters, and raises on players who ended up in a blowout went 1 right, 10 wrong. The pre-game version is tested in H2-H4 (see blowout_study.md). Fades still run 15 right, 22 wrong.
- Boom 4+: too early, morning (204 moves, 43%) and afternoon (424 moves, 47%).

## 2026-10-30 Fri main

- A normal big slate (Lock AM 7:23am, Lock PM 2:22pm). Morning: your board edged ADP (56%; season 52%, too close to call) but split with our number (49%; season 56%, still your board wins). Raises on Naz (back from the benching), IQ, VanVleet and Ausar were right; the Caleb Wilson fade (6-11 from three) was the worst miss.
- Afternoon: 46% against ETR (season 48%, too close to call). Your board against ADP at lock is now settled: your board wins (53%, range 50-56%). The HOU raises (Sengun questionable) and the LeBron fade (Jaylen Brown questionable) are logged as hedges.
- Themes, first time with 5 slates: minutes misreads are the top fixable cause (32 cases, 24 above his usual), which H1 is testing. Blowouts are second among causes we can see coming (24 cases, every slate) and ours ran too high on 30 of 40 misses: a spread-based minutes trim is a candidate, but needs spreads on file before it can be tested.
- Fades stay the drafting habit to watch: 10 right, 20 wrong, and 12 of the 20 wrong ones played above their usual minutes. Raises on players who then played above usual went 13-7. Boom 4+: too early, morning (134 moves, 43%) and afternoon (379 moves, 48%).

## 2026-10-29 Thu main

- Your best morning yet (Lock AM 6:00am): your board beat ADP on 67% of disagreements (season 51%, still too close to call) and picked +19.6 in rounds 5-6. The call of the night was raising Fears (beat all 8 he passed) with Dejounte and Poole out.
- Afternoon went to ETR: your PM board was right on only 33% of disagreements with it (season 48%, too close to call). The misses were fading players who got a teammate's minutes (Fears, Clingan with Robert Williams out) and raising Ja and Dame into a 21-point loss.
- Fades remain the habit to watch: 7 right, 16 wrong across four slates (AM and PM), and 10 of the 16 wrong fades played above their usual minutes. Not a theme for the model; a drafting note.
- Our morning number tracked ETR's first upload very closely (rank corr 0.98). Lock PM blend moved to 40% ours with a range of 0-90%: nothing settled. Boom 4+: too early, morning (89 moves, 45%) and afternoon (336 moves, 48%).

## 2026-10-28 Wed main

- First night with both locks (AM 4:05am, PM 2:22pm). A chaotic big slate: every order correlated poorly (0.32-0.47), with blowouts (OKC, ORL, TOR) and late outs (Luka, Haliburton).
- Morning: your board beat our number again (56%; season 57%, settled) but lost to ADP (42%; season 50%, too close to call). Afternoon: 46% against ETR (season 49%), 42% against ADP.
- Your fades are going badly: 4 right, 11 wrong across three slates (Curry, Caleb Wilson twice, Bam, Lendeborg this time), mostly players who then played more minutes than usual. Worth a look before fading someone whose role is growing; not yet a theme (3 slates).
- First blend read with our board number (Lock PM, two slates, 110 players): 70% ours missed least (9.73 against 9.80 all ETR). Far too early; no range yet.
- Boom vs ADP, Boom gap 4+: too early, morning and afternoon. Morning 58 moves (one night), the moved-up player won 36%; afternoon 314 moves, 47%. A real edge needs 500+ moves at 53%+ for two weeks running.

## 2026-10-27 Tue main

- Morning: no Lock AM again (8:06am board used). Your board (0.72) and ADP (0.70) were close on order; ADP's round picks won the night (+6.1 against your +1.8), most of it in rounds 5-6. Season verdict unchanged: your board beats our raw number (57%), too close to call against ADP (52%).
- Afternoon (your Lock PM, 2:41pm; first read as missing, recovered from an earlier save): ETR edged your PM board (0.71 to 0.70); your calls against it went 49%, season 50%, too close to call. Raises on MPJ, Holiday and Reed were right; Jenkins, Fox and LaVine (both in the blowout) and the Vassell fade were wrong. Your board beat our Lock PM number on 59% of their disagreements (one slate).
- Early lean to watch, not yet a theme (2 slates): calls that leaned into a player running above his usual minutes went 6 of 7 (MPJ, Holiday, Robert Williams, McDaniels, PJ Washington, Gobert PM); "minutes" is the most common cause in the log (16 of 58).
- Grimes has played 20 and 19 minutes the last two nights against a usual of 26.

## 2026-10-26 Mon main

- Morning: your board (6:20am save, no Lock AM yet) ordered the slate the same as ADP (0.55 each) but picked better within rounds than our raw number (+8.1 against -2.0). Small morning CLV (+0.27); our morning file showed none (+0.02).
- Afternoon: ETR edged your PM board (0.62 to 0.60), and your calls against it went 42%. Your two worst calls, Dosunmu and LaMelo, were hedges on Edwards sitting (questionable in ETR's notes; he played). You update those live once news lands, so they're logged as hedges, not misses. McDaniels, also raised, was right (7 of 11).
- Our misses this night were mostly stars under-projected by the raw morning file (Flagg, Edwards, Miller, Sengun), partly because it is a plain average, below the board's scale. Judge ours on the board number once Lock AM and Lock PM are in use.
- One slate in the log: too thin for themes. Nothing to change yet.
