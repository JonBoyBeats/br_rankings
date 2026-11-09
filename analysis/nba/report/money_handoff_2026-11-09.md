# Contest side to rankings side: money batch, 2026-11-09

From scripts/nba_money.py (money_report.md, sections 3, 3b and 5). The MONEY column of decision_register.csv is written for
this batch, approved by the user. Every money verdict here is the top-10% lift after the price-split check: teams matched
on the price of their other picks, so a cheaper pick can't win by freeing money for the rest. Slates 10-22 to 11-08 (17
priced nights); find on all but the last 5, check on the last 5.

Rule for the two verdicts, agreed with the user: money wins over points only if its evidence clears its own bar (a RULE);
a decision that loses points is kept only on a money RULE; both negative, drop it. Nothing changes rankings without both
sides seeing it.

## Proposed changes, with their points cost

| # | Decision (register id) | POINTS (yours) | MONEY | Proposal |
|---|---|---|---|---|
| 1 | ownership-tiebreak-t5 (paused) | costs points: AM -4.2/take (112), PM -6.6 (84) | RULE for, 1.19 (1.06-1.32); AM 1.16, PM 1.22 | Un-pause it in T5, both windows: the leverage case. The gap is the less-drafted pick itself (+2.6 over price on 0.4 fewer raw points), not better other picks. |
| 2 | pm-t5-adp-value (adopted) | RULE, +2.3/pair (560) | LEAN against, 0.87, against the old ETR (2: less drafted) | No change on a lean. But it is the same comparison as #1: if the tiebreak comes back, PM T5 needs one rule. Suggest ADP with VALUE first, then less-drafted first within 2 projected points; define it and the contest side will grade it. |
| 3 | am-t5-other-reads (candidate) | LEAN against, -3.9/take (73) | RULE for, 1.31 (1.12-1.54) | Keep making the AM T5 reads. Please reconcile the points number first: in the contest data, teams holding the user's choice also scored more raw points (+1.4) than teams holding the button's, so the -3.9 may come from a different set of pairs (only the user's own takes, or slots scored through swaps). |
| 4 | pricey-flags:T1 (new row) | not graded for T1 alone | RULE for, 1.73 (1.38-2.20), 12 slates | Grade "PRICEY last in T1" on points. Not leverage: the unflagged player scored 8.0 more points in the same teams. |
| 5 | leverage-t2-t4 (candidate) | AM about free (+1.0 middle, +2.8 T4); PM costs (-4.1 middle, RULE against) | LEAN for (RULE numbers on 6 slates) | No change yet; the contest side re-reads it at 14 slates. |
| 6 | beneficiary-round6 (candidate) | anecdote (8 players) | played: RULE for, 1.37; sat: no lean | Caution: whether the teammate plays isn't known at the AM draft, so the split isn't a draft rule. The contest side will grade the knowable version (any round-6 teammate of a player tagged at Lock AM). Please grade it on points too. |
| 7 | one-tier-cap (adopted) | LEAN (both windows) | LEAN against, 0.79 | Keep on points; watch. |
| 8 | value-up-middle-t5 (adopted) | LEAN (both windows) | LEAN for, 1.14 (was RULE before the price check) | Keep: both agree. |

No change, written as no lean or not enough: am-t5-button-order, pm-t4-pricey-last-off, both Questionable rules, Q-tag
pushes and raises, Q classes, pm-t5-beneficiary (no lean after the check), pm-t2-adp-etr2, pm-t4-adp-etr2 (no lean; a
lean against on ten price groups), pm-middle-takes, pm-t2-other-reads, live moves, and both swap rows. The kept-* rows
weren't tested on the contest side yet; they stay pending.

## Draft-card candidates (new rows, money only; please grade them on points)

| Register id | Money | What the contest data shows |
|---|---|---|
| card-turn23-reach-higher-proj | RULE for, 1.82 (1.51-2.10), 4,580 teams | At the 2/3 turn, reaching in general is a coin flip (1.09); reaching toward a player who outprojects everyone he jumped wins, and the reached player scored +10.4 over his price. |
| card-turn12-reach | LEAN against, 0.74 (0.54-1.02) | At the 1/2 turn, trust ADP order; reaching toward the higher projection there is too thin to read (3,721 teams, wide). |
| card-fallers | RULE for at both turns | A top player who falls to the turn: always take him (1/2: 1.64, 2/3: 1.22). |
| card-same-position-teammates | RULE against, 0.76; 0.84 at spreads of 5+ | Two teammates in one position group lose on points too (-7.9 over price for the pair). |
| card-opposing-stars | LEAN for, 1.10 | Stars on opposite sides of one game, +1.2 over price for the pair; a lean only. |

Turns are read from rosters by closing-ADP rank, since pick order isn't public (definitions in nba_money.py turn_teams).

## Data asks

1. Swap crediting: 10-31 (6,070 swapped-in picks) and 11-01 (1,455) have none credited to the player they replaced.
   nba_swaps.py matches by the missing round, which misses when a player's ADP at draft and at lock sit in different
   rounds (Dejounte and Jerome, 10-31). The contest side recomputes credits nightly from the contest files, so a fix in
   nba_swaps.py flows through.
2. Swaps cost teams by the ruled-out player's tier: T1-T2 0.42, T3-T5 0.79 (top-10% lift against same-price teams with no
   swap). Context for the Q lane and the swap board.
