"""How close our morning Proj comes to ETR's, read the way you draft: who sits above or below his ADP.

For every main slate with a Lock AM pressed before ETR's first upload (analysis/nba/daily/*_main.csv):
each priced player's value is his projection minus the average of the 6 players nearest him by morning ADP
(3 either side), worked out separately for ours (ours_am) and ETR's first upload (etr_first), so the two
scales never need to agree. Then:

  direction   of the players ETR has 2+ points above or below their ADP, the share we had the same way
  ETR's top / bottom 5   per slate, how many of ETR's 5 most above (below) ADP we also had above (below)
  big misses  ours and ETR's value 3+ points apart
  corr        correlation of the two values
  CLV         correlation of each value with his ADP move from the morning to lock (positive: he went earlier)
  rookies     players with no last season on file (the mirror's morning file has no crowd for them):
              ETR's value minus ours on average; the board averages their last 3 ETR nights from NEW_SINCE

Only the top 10 rounds by morning ADP are graded (60 players on a 6-drafter slate, 40 on a 4-drafter one), in four
groups: the elite (ETR's top 2 to 4 projections, cut at the biggest drop after the 2nd, 3rd or 4th), the rest under
ADP 19, ADP 19-31, and ADP 32 on. By group and overall, for the season and
the last 7 slates, then each slate, the latest slate's biggest misses and players missed the same way on
3+ slates. Writes analysis/nba/report/etr_match.md. The 2:17am job runs it.

  python3 scripts/nba_etr_match.py [--mirror ../br-adp-mirror]
"""
import argparse, collections, csv, glob, json, os, statistics as st

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(HERE, "analysis", "nba", "report", "etr_match.md")
NEW_SINCE = "2026-11-07"      # first slate with the board's last-3 average for players with no last season
DIR, BIG, TOP, ROUNDS = 2.0, 3.0, 5, 10
GROUPS = ("elite", "to ADP 19", "ADP 19-31", "ADP 32+")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def value(xs):
    return [xs[i] - st.mean(xs[max(0, i - 3):i] + xs[i + 1:i + 4]) for i in range(len(xs))]


def slates(rookies):
    meta = json.load(open(os.path.join(DAILY, "meta.json")))
    out = []
    for path in sorted(glob.glob(os.path.join(DAILY, "*_main.csv"))):
        m = meta.get(os.path.basename(path)) or {}
        am, e1 = m.get("am") or {}, m.get("etr_first") or {}
        if not am.get("ours") or not e1 or am["at"] >= e1["at"]:      # no Lock AM, or it came after ETR's file
            continue
        rs = [r for r in csv.DictReader(open(path)) if all(num(r[k]) is not None for k in ("ours_am", "etr_first", "adp_am"))]
        if len(rs) < 30:
            continue
        rs.sort(key=lambda r: num(r["adp_am"]))
        pod = 6 if len(rs) >= 60 else 4
        vo, ve = value([num(r["ours_am"]) for r in rs]), value([num(r["etr_first"]) for r in rs])
        best = sorted((num(r["etr_first"]) for r in rs), reverse=True)[:5]
        gaps = [best[k - 1] - best[k] for k in (2, 3, 4)]
        elite = best[1 + gaps.index(max(gaps))]                 # the lowest elite projection
        ps = []
        for i, r in enumerate(rs[:ROUNDS * pod]):      # values use the whole slate's neighbors; only the top 60 (40) graded
            rd, adp = i // pod + 1, num(r["adp_am"])
            grp = GROUPS[0] if num(r["etr_first"]) >= elite else GROUPS[1] if adp < 19 else GROUPS[2] if adp < 32 else GROUPS[3]
            move = num(r["adp_am"]) - num(r["adp_close"]) if num(r["adp_close"]) is not None else None
            ps.append({"date": r["date"], "name": r["name"], "team": r["team"], "rd": rd, "adp": adp,
                       "grp": grp, "ours": vo[i], "etr": ve[i], "move": move,
                       "rookie": r["name"] in rookies, "usual": r["usual_min"], "min": r["min"],
                       "tag": " / ".join(t for t in (r["injury_am"], r["injury"]) if t)})
        for k in sorted(range(len(ps)), key=lambda k: ps[k]["etr"])[-TOP:]:
            ps[k]["etr_top"] = True
        for k in sorted(range(len(ps)), key=lambda k: ps[k]["etr"])[:TOP]:
            ps[k]["etr_bottom"] = True
        out.append((rs[0]["date"], ps))
    return out


def corr(xs, ys):
    return st.correlation(xs, ys) if len(xs) > 2 and len(set(xs)) > 1 and len(set(ys)) > 1 else None


def measures(ps):
    d = [p for p in ps if abs(p["etr"]) >= DIR]
    top, bot = [p for p in ps if p.get("etr_top")], [p for p in ps if p.get("etr_bottom")]
    mv = [p for p in ps if p["move"] is not None]
    rk = [p["etr"] - p["ours"] for p in ps if p["rookie"]]
    return {"n": len(ps), "corr": corr([p["ours"] for p in ps], [p["etr"] for p in ps]),
            "dir": (sum((p["ours"] > 0) == (p["etr"] > 0) for p in d), len(d)),
            "top": (sum(p["ours"] > 0 for p in top), len(top)), "bot": (sum(p["ours"] < 0 for p in bot), len(bot)),
            "big": sum(abs(p["ours"] - p["etr"]) >= BIG for p in ps),
            "clv": (corr([p["ours"] for p in mv], [p["move"] for p in mv]), corr([p["etr"] for p in mv], [p["move"] for p in mv])),
            "rookie": (st.mean(rk) if rk else None, len(rk))}


def f2(x, fmt="%.2f"):
    return "-" if x is None else fmt % x


def frac(t):
    return "%d/%d (%.0f%%)" % (t[0], t[1], 100 * t[0] / t[1]) if t[1] else "-"


def row(label, m):
    return "| %s | %d | %s | %s | %s | %s | %d (%.0f%%) | %s / %s | %s (%d) |" % (
        label, m["n"], f2(m["corr"]), frac(m["dir"]), frac(m["top"]), frac(m["bot"]), m["big"], 100 * m["big"] / m["n"],
        f2(m["clv"][0]), f2(m["clv"][1]), f2(m["rookie"][0], "%+.1f"), m["rookie"][1])


HEAD = ("| | players | corr | direction (ETR 2+ off ADP) | ETR's top 5 we had above | ETR's bottom 5 we had below | "
        "big misses (3+) | CLV ours / ETR | rookie gap (n) |\n|---|---|---|---|---|---|---|---|---|")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "br-adp-mirror"))
    a = ap.parse_args()
    mpath = os.path.join(a.mirror, "nba_morning.json")
    rookies = {p["name"] for p in json.load(open(mpath))["players"] if p.get("crowd") is None and p.get("games")} \
        if os.path.exists(mpath) else set()
    ss = slates(rookies)
    if not ss:
        print("no slates with a Lock AM before ETR's first file")
        return
    allp = [p for _, ps in ss for p in ps]
    last7 = [p for _, ps in ss[-7:] for p in ps]
    L = ["# Our morning Proj vs ETR's first upload, against ADP", "",
         "Written nightly by scripts/nba_etr_match.py (its docstring has the definitions). Value = projection minus "
         "the average of the 6 players nearest by morning ADP, for ours at Lock AM and for ETR's first file; the top 60 by ADP graded (40 on a 4-drafter slate), "
         "in four groups: the elite (ETR's top 2-4, cut at the biggest drop), the rest under ADP 19, ADP 19-31 and 32 on. %d slates, "
         "%s to %s. Rookie gap: ETR's value minus ours for players with no last season (+: we're lower); the board "
         "averages their last 3 ETR nights from %s." % (len(ss), ss[0][0], ss[-1][0], NEW_SINCE), ""]
    for title, ps in (("Season", allp), ("Last 7 slates", last7)):
        L += ["## " + title, "", HEAD]
        for g in GROUPS:
            L.append(row(g, measures([p for p in ps if p["grp"] == g])))
        L += [row("**all**", measures(ps)), ""]
    before = [p for p in allp if p["rookie"] and p["date"] < NEW_SINCE]
    after = [p for p in allp if p["rookie"] and p["date"] >= NEW_SINCE]
    L += ["## Rookies (no last season), before and after the last-3 average", "",
          "| | n | ETR minus ours | big misses |", "|---|---|---|---|"]
    for lab, ps in (("before " + NEW_SINCE, before), ("from " + NEW_SINCE, after)):
        L.append("| %s | %d | %s | %d |" % (lab, len(ps), f2(st.mean([p["etr"] - p["ours"] for p in ps]) if ps else None, "%+.2f"),
                                            sum(abs(p["etr"] - p["ours"]) >= BIG for p in ps)))
    L += ["", "## By slate", "", HEAD]
    for d, ps in ss:
        L.append(row(d, measures(ps)))
    d, ps = ss[-1]
    L += ["", "## Biggest misses, %s" % d, "", "| player | ADP | ours vs ADP | ETR vs ADP | usual min | min | tag |", "|---|---|---|---|---|---|---|"]
    for p in sorted(ps, key=lambda p: -abs(p["ours"] - p["etr"]))[:10]:
        L.append("| %s %s%s | %.1f | %+.1f | %+.1f | %s | %s | %s |" % (p["name"], p["team"], " (rookie)" if p["rookie"] else "", p["adp"],
                                                                p["ours"], p["etr"], p["usual"], p["min"], p["tag"]))
    rep = collections.defaultdict(list)
    for _, ps in ss[-10:]:
        for p in ps:
            if abs(p["ours"] - p["etr"]) >= BIG:
                rep[p["name"]].append(p["etr"] - p["ours"])
    rep = {k: v for k, v in rep.items() if len(v) >= 3 and (all(x > 0 for x in v) or all(x < 0 for x in v))}
    L += ["", "## Missed the same way on 3+ of the last 10 slates", ""]
    L += ["- %s: ETR %s ours by %s" % (k, "above" if v[0] > 0 else "below", ", ".join("%.1f" % abs(x) for x in v))
          for k, v in sorted(rep.items(), key=lambda kv: -abs(st.mean(kv[1])))] or ["- none"]
    open(OUT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
