"""Step 2 report: the pre-registered test (field_rebuild_step1, 92800a0) from grade_rows.json and construction.json.
python3 report.py  (run in this folder) -> stdout (report.out)"""
import json, math, statistics as S, sys
from collections import defaultdict
# python3 report.py [grade_rows_r4.json construction_r4.json]: the R4 add-on (its rows carry no PREVIOUS construction;
# PREVIOUS comes from construction.json)
G = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "grade_rows.json"))
C = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "construction.json"))
prev = {r["cid"]: r["prev"] for r in json.load(open("construction.json"))["construction"]}
for r in C["construction"]:
    r.setdefault("prev", prev.get(r["cid"]))
cons = {r["cid"]: r for r in C["construction"]}

def se(v): return S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
def by_slate(rows, f):
    d = defaultdict(list)
    for r in rows:
        v = f(r)
        if v is not None: d[r["slate"]].append(v)
    return [S.mean(v) for v in d.values()]
def line(lab, v):
    if not v: return "%-46s n/a" % lab
    return "%-46s %+7.2f ± %5.2f  better on %2d of %2d  (2xSE %.2f)" % (lab, S.mean(v), se(v), sum(x > 0 for x in v), len(v), 2 * se(v))

big = [r for r in G if r["entries"] >= 100 and r["field_cash"] is not None]
print("contests 100+ entries with a real cash line:", len(big), "on", len({r['slate'] for r in big}), "slates")
# reproduction check: PREVIOUS recomputed vs eval.csv's logged sim lines (the shadow contest)
rep = [r for r in G if r["sim_cash_logged"] is not None]
if rep:
    d = [r["prev"]["cash"] - r["sim_cash_logged"] for r in rep]; d10 = [r["prev"]["top10"] - r["sim_top10_logged"] for r in rep]
    print("reproduction: PREVIOUS cash line recomputed - logged sim_cash: mean %+.2f, max |%.2f| (%d contests); top-10%% %+.2f, max |%.2f|"
          % (S.mean(d), max(abs(x) for x in d), len(d), S.mean(d10), max(abs(x) for x in d10)))

for t in ("all", "flagship", "main", "qualifier"):
    R = [r for r in big if t == "all" or r["type"] == t]
    if not R: print("\n==", t, ": no contests"); continue
    print("\n== %s: %d contests, %d slates" % (t, len(R), len({r['slate'] for r in R})))
    print("  mean gap, sim - real: cash PREVIOUS %+.1f  candidate %+.1f | top-10%% PREVIOUS %+.1f  candidate %+.1f" % (
        S.mean(r["prev"]["cash"] - r["field_cash"] for r in R), S.mean(r["cand"]["cash"] - r["field_cash"] for r in R),
        S.mean(r["prev"]["top10"] - r["field_top10"] for r in R), S.mean(r["cand"]["top10"] - r["field_top10"] for r in R)))
    print(line("PRIMARY |cash gap| gain (prev - cand)", by_slate(R, lambda r: abs(r["prev"]["cash"] - r["field_cash"]) - abs(r["cand"]["cash"] - r["field_cash"]))))
    print(line("secondary |top-10% gap| gain", by_slate(R, lambda r: abs(r["prev"]["top10"] - r["field_top10"]) - abs(r["cand"]["top10"] - r["field_top10"]))))
    for k, lab in (("own", "own total"), ("dup", "duplication %"), ("pair", "top pair %"), ("proj", "our projected pts / lineup")):
        print(line("secondary |%s gap| gain" % lab, by_slate(R, lambda r, k=k: (abs(cons[r["cid"]]["prev"][k] - cons[r["cid"]]["real"][k])
                                                                        - abs(cons[r["cid"]]["cand"][k] - cons[r["cid"]]["real"][k])) if r["cid"] in cons else None)))
    print(line("context: S6 level (real field proj - actual mean)", by_slate(R, lambda r: (cons[r["cid"]]["real"]["proj"] - r["field_avg"]) if r["cid"] in cons and r["field_avg"] is not None else None)))
    print(line("context: cash gap PREVIOUS (sim - real)", by_slate(R, lambda r: r["prev"]["cash"] - r["field_cash"])))
    print(line("context: cash gap candidate (sim - real)", by_slate(R, lambda r: r["cand"]["cash"] - r["field_cash"])))

# all contests (any size) construction, as context
print("\nconstruction, all held-out contests (any size), mean real / PREVIOUS / candidate:")
for t in ("flagship", "main", "qualifier"):
    R = [r for r in C["construction"] if r["type"] == t]
    print("  %-9s %2d: " % (t, len(R)) + " | ".join("%s %.1f / %.1f / %.1f" % (k, S.mean(r["real"][k] for r in R), S.mean(r["prev"][k] for r in R), S.mean(r["cand"][k] for r in R)) for k in ("own", "top8", "dup", "pair", "proj")))

# CONTEXT: last week's entered flagship and main lineups, sim expected payout and top-1% under each field, real beside
print("\nCONTEXT (outside the tag): our entered lineups 11-20 to 11-26, flagship and main contests")
for t in ("flagship", "main", "both"):
    R = [r for r in G if r["date"] >= "2026-11-20" and r["mine_n"] and (r["type"] == t or (t == "both" and r["type"] in ("flagship", "main")))]
    if not R: continue
    n = sum(r["mine_n"] for r in R); fees = sum((r["fee"] or 0) * r["mine_n"] for r in R)
    ep, ec = sum(r["prev"]["mine_expected"] for r in R), sum(r["cand"]["mine_expected"] for r in R)
    won = sum(r["mine_won"] for r in R)
    t1p = sum(r["prev"]["mine_top1"] * r["mine_n"] for r in R) / n; t1c = sum(r["cand"]["mine_top1"] * r["mine_n"] for r in R) / n
    t1r = sum(r["mine_top1_real"] * r["mine_n"] for r in R) / n
    dp = sum(r["prev"]["mine_dups"] * r["mine_n"] for r in R) / n; dc = sum(r["cand"]["mine_dups"] * r["mine_n"] for r in R) / n
    print("  %-8s %d contests, %d entries, fees $%.2f | sim expected payout: today's field $%.2f (%.2fx real), rebuilt $%.2f (%.2fx real) | real won $%.2f"
          % (t, len(R), n, fees, ep, ep / won if won else float("nan"), ec, ec / won if won else float("nan"), won))
    print("  %-8s top-1%% per lineup: today's field %.3f, rebuilt %.3f, real %.3f | field copies of each entry (of 1,000): today's %.2f, rebuilt %.2f"
          % ("", t1p, t1c, t1r, dp, dc))
