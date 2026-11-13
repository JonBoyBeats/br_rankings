"""Q-tag rules on points, all pairs by nights (results only; 2026-11-13).

A player Questionable at a window's lock is placed four ways on the button's board, everyone else as built:
  a  keeps his tier                      b  drops two tiers (to T5 at most)
  c  no higher than the top of T4        d  goes to the bottom of the list
Each rule against each other: every pair involving a Q player that the two orders put differently, scored by who
scored more; a player who sat scores his swap's points (nba_tier_grade.load: his credited swaps, else the night's
average swap, else the season's). A night goes to the order with more of its pairs right.

Beneficiaries: teammates of a Q player taken before T5 (tier 1-4 in that window), untagged, who played: actual minus
the window's projection (AM ours, PM ETR), when a Q teammate sat against when they all played.

  python3 scripts/nba_q_rules_test.py > analysis/nba/report/q_rules_test.md
"""
import collections, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as TG          # noqa: E402  rows with swap-scored slots
import nba_tier_history as TH        # noqa: E402  the button's rule sort
import nba_tier_season_tests as TS   # noqa: E402  nights won / resamples / points per pair

num = TH.num
Q = re.compile(r"^q", re.I)
RULES = {"a": "keeps his tier", "b": "drops two tiers", "c": "no higher than the top of T4", "d": "bottom of the list"}


def keyed(r):
    cap = 24.0 if r["pod"] == "4" else 36.0
    a = num(r["adp"])
    v = num(r["proj"])
    return {"row": r, "adp": -(min(a, cap) if a is not None else cap), "proj": float(int(v + 0.5)) if v is not None else None,
            "projx": v, "boom": num(r["boom"]), "drafted": -num(r["drafted"]) if num(r["drafted"]) is not None else None}


def order(rows, window, rule):
    """{player_id: position} on the board with every Q player placed by `rule`."""
    def place(r):
        t, q = int(r["tier"]), bool(Q.match(r["tag"]))
        if not q or rule == "a":
            return t, "normal"
        if rule == "b":
            return min(5, t + 2), "normal"
        if rule == "c":
            return (4, "top") if t <= 3 else (t, "normal")
        return 6, "bottom"
    by = collections.defaultdict(list)
    for r in rows:
        by[place(r)].append(r)
    seq = []
    for t in range(1, 7):
        top = sorted(by.get((t, "top"), []), key=lambda r: num(r["built"]) or 9e9)
        seq += top
        if t == 6:                   # below the cut (the 2026-11-13 button), then the bottom placement
            seq += sorted(by.get((6, "normal"), []), key=lambda r: num(r["built"]) or 9e9)
            seq += sorted(by.get((6, "bottom"), []), key=lambda r: num(r["built"]) or 9e9)
            continue
        normal = by.get((t, "normal"), [])
        for f in ("VALUE", "", "PRICEY"):
            grp = [keyed(r) for r in normal if r["flag"] == f]
            seq += [k["row"] for k in TH.rule_sort(grp, TH.RULE_STEPS[window][t])]
    return {r["player_id"]: i for i, r in enumerate(seq)}


def run():
    H = TG.load()                       # rows with a slot (points, or the swap's for a sat player)
    nights = collections.defaultdict(list)
    for r in H:
        nights[(r["date"], r["window"])].append(r)
    out = {}
    for w in ("am", "pm"):
        orders = {}
        for night, rows in nights.items():
            if night[1] == w and any(Q.match(r["tag"]) for r in rows):
                orders[night] = {k: order(rows, w, k) for k in RULES}
        for x in RULES:
            for y in RULES:
                if x >= y:
                    continue
                by = collections.defaultdict(list)
                for night, o in orders.items():
                    rows = nights[night]
                    qs = [r for r in rows if Q.match(r["tag"])]
                    seen = set()
                    for q in qs:
                        for r in rows:
                            if r is q or (r["player_id"], q["player_id"]) in seen:
                                continue
                            seen.add((q["player_id"], r["player_id"]))
                            a1, b1 = o[x][q["player_id"]], o[x][r["player_id"]]
                            a2, b2 = o[y][q["player_id"]], o[y][r["player_id"]]
                            if (a1 < b1) == (a2 < b2):
                                continue
                            first, second = (q, r) if a1 < b1 else (r, q)
                            if first["slot"] != second["slot"]:
                                by[night].append(first["slot"] - second["slot"])
                out[(w, x, y)] = TS.summarize(by)
    return nights, out


def beneficiaries(nights):
    out = {}
    for w in ("am", "pm"):
        sat, played = collections.defaultdict(list), collections.defaultdict(list)
        base = collections.defaultdict(list)
        for night, rows in nights.items():
            if night[1] != w:
                continue
            qs = [r for r in rows if Q.match(r["tag"])]
            qteams = {r["team"] for r in qs}
            for r in rows:
                if r["tag"] or r["played"] != "1" or int(r["tier"]) > 4 or num(r["proj"]) is None or num(r["actual"]) is None:
                    continue
                res = num(r["actual"]) - num(r["proj"])
                mates = [q for q in qs if q["team"] == r["team"]]
                if not mates:
                    base[night].append(res)
                elif any(q["scratched"] == "1" for q in mates):
                    sat[night].append(res)
                else:
                    played[night].append(res)
        out[w] = (sat, played, base)
    return out


def mean(d):
    v = [x for xs in d.values() for x in xs]
    return (sum(v) / len(v), len(v), len([k for k in d if d[k]])) if v else (float("nan"), 0, 0)


def diff_range(a, b):
    """80% range of mean(a) - mean(b) over night resamples (nights from either side)."""
    ds = sorted(set(a) | set(b))
    rnd, ms = random.Random(5), []
    for _ in range(2000):
        s = [rnd.choice(ds) for _ in ds]
        va = [x for d in s for x in a.get(d, [])]
        vb = [x for d in s for x in b.get(d, [])]
        if va and vb:
            ms.append(sum(va) / len(va) - sum(vb) / len(vb))
    ms.sort()
    return ms[len(ms) // 10], ms[9 * len(ms) // 10], sum(m > 0 for m in ms) / len(ms)


def main():
    nights, R = run()
    qn = collections.Counter(n[1] for n, rows in nights.items() if any(Q.match(r["tag"]) for r in rows))
    qp = collections.Counter((r["window"], "T1-T4" if int(r["tier"]) <= 4 else "T5", r["scratched"] == "1")
                             for rows in nights.values() for r in rows if Q.match(r["tag"]))
    print("# Q-tag rules on points (all pairs, by nights)\n")
    print("Questionable at the lock: morning %d players on %d nights (T1-T4: %d, of whom %d sat; T5: %d, %d sat); afternoon "
          "%d on %d nights (T1-T4: %d, %d sat; T5: %d, %d sat). Players who sat score their swap's points. Every pair "
          "involving a Q player that the two placements order differently; a night goes to the one with more pairs right.\n" % (
              sum(v for k, v in qp.items() if k[0] == "am"), qn["am"],
              qp[("am", "T1-T4", False)] + qp[("am", "T1-T4", True)], qp[("am", "T1-T4", True)],
              qp[("am", "T5", False)] + qp[("am", "T5", True)], qp[("am", "T5", True)],
              sum(v for k, v in qp.items() if k[0] == "pm"), qn["pm"],
              qp[("pm", "T1-T4", False)] + qp[("pm", "T1-T4", True)], qp[("pm", "T1-T4", True)],
              qp[("pm", "T5", False)] + qp[("pm", "T5", True)], qp[("pm", "T5", True)]))
    print("Rules: a = %s; b = %s; c = %s; d = %s.\n" % tuple(RULES[k] for k in "abcd"))
    print(TS.HEAD)
    for w, wl in (("am", "morning"), ("pm", "afternoon")):
        for x in RULES:
            for y in RULES:
                if x < y:
                    print(TS.line("%s: %s vs %s" % (wl, x, y), x, y, R[(w, x, y)]))
    B = beneficiaries(nights)
    print("\n## Beneficiaries\n")
    print("Teammates of a Q player, taken before T5 (tier 1-4 in the window), untagged, who played: actual minus the window's "
          "projection (morning ours, afternoon ETR).\n")
    print("| window | a Q teammate sat | all Q teammates played | no Q teammate (reference) | sat minus played (80% range; resamples above 0) |")
    print("|---|---|---|---|---|")
    for w, wl in (("am", "morning"), ("pm", "afternoon")):
        sat, played, base = B[w]
        (ms, ns, ds), (mp, np_, dp), (mb, nb, db) = mean(sat), mean(played), mean(base)
        lo, hi, up = diff_range(sat, played) if ns and np_ else (float("nan"),) * 3
        print("| %s | %+.2f (%d on %d nights) | %+.2f (%d on %d nights) | %+.2f (%d) | %+.2f (%+.2f to %+.2f; %.0f%%) |" % (
            wl, ms, ns, ds, mp, np_, dp, mb, nb, ms - mp, lo, hi, 100 * up))


if __name__ == "__main__":
    main()
