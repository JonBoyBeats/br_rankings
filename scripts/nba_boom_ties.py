"""Boom as a tiebreak, graded the way it's used: on each night's main slate, pairs of the top 60 by
projection within 2 points of each other where Boom would move one player past an earlier ADP.
Did the moved-up player do better? Morning: our Proj and the morning's ADP; afternoon: ETR's median
and the closing ADP. Split by the Boom gap (under 4 points is a tie; 4+ is an outlier).

Boom % is the board's own (NBA_BOOM, nbaBars and nbaChance in index.html, on his median as the board
reads it), from that day's nba_morning.json in br-adp-mirror's history. A boom is a night 10+ over
his median. Every night on file is regraded each run into analysis/nba/boom_ties.csv, and the
running totals print.

  python3 scripts/nba_boom_ties.py --mirror ../br-adp-mirror     (a full clone: it reads the history)
"""
import argparse, csv, glob, itertools, json, math, os, re, subprocess, unicodedata

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(HERE, "analysis", "nba", "boom_ties.csv")
GAP = 4                                       # Boom points apart before it counts as an outlier
html = open(os.path.join(HERE, "index.html")).read()


def jsobj(name):
    return json.loads(re.sub(r"(\w+):", r'"\1":', re.search(r"var %s = (\{.*?\} \});" % name, html, re.S).group(1)))


BOOM = jsobj("NBA_BOOM")
CEIL = json.loads(re.search(r"var NBA_CEIL = (\[[^\]]+\]);", html).group(1))


def norm(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z ]", "", s.replace("-", " ").replace(".", ""))
    return " ".join(w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv"))


def median_of_proj(v):                        # the board's nbaMedianOf
    return (v - 0.75 * CEIL[1]) / (0.25 + 0.75 * CEIL[0])


def chance(model, x, bar, r):                 # the board's nbaChance
    v = {"gap": x - bar, "pred": x, "pred2": x * x / 100, "upm": r.get("upm"), "min_sd": r.get("min_sd"), "min_l10": r.get("min"),
         "ast_pm": r.get("apm"), "reb_pm": r.get("rpm"), "starter_rate": r.get("start"), "ppm_sd": r.get("sd"), "foul_pm": r.get("fpm"),
         "stk_share": r["spm"] / r["ppm"] if r.get("spm") is not None and r.get("ppm") else None}
    z = model["intercept"]
    for k, (avg, sd, w) in model["terms"].items():
        if isinstance(v.get(k), (int, float)):
            z += w * (v[k] - avg) / sd
    return 1 / (1 + math.exp(-z))


def med(xs):
    xs = sorted(xs)
    return (xs[(len(xs) - 1) // 2] + xs[len(xs) // 2]) / 2


def window(lst, i):                           # the board's nbaWindowBar
    b, a = min(6, i), min(6, len(lst) - 1 - i)
    nb = lst[i - min(b, max(a, 3)):i] + lst[i + 1:i + 1 + min(a, max(b, 3))]
    return med([q["x"] for q in nb]) if nb else lst[i]["x"]


def bars(rows):                               # the board's nbaBars
    cap = max([r["adp"] for r in rows] + [0])
    byx = sorted(rows, key=lambda r: -r["x"])
    bya = sorted(rows, key=lambda r: (min(r["adp"], cap), -r["x"]))
    px = {id(r): window(byx, i) for i, r in enumerate(byx)}
    return {id(r): (window(bya, i) + px[id(r)]) / 2 for i, r in enumerate(bya)}


def morning_at(mirror, day):
    h = subprocess.run(["git", "-C", mirror, "log", "-1", "--format=%H", "--before=" + day + "T17:00:00Z", "--", "nba_morning.json"],
                       capture_output=True, text=True).stdout.strip()
    if not h:
        return {}
    doc = json.loads(subprocess.run(["git", "-C", mirror, "show", h + ":nba_morning.json"], capture_output=True, text=True).stdout)
    return {norm(r["name"]): r for r in doc["players"]}


def night(path, mo, when):
    rows = []
    for r in csv.DictReader(open(path)):
        proj = r["ours_am"] if when == "am" else r["etr_median"]
        adp = r["adp_am"] if when == "am" else r["adp_close"]
        m = mo.get(norm(r["name"]))
        if not proj or not adp or not r["actual"] or not m or m.get("ppm") is None:
            continue
        x = median_of_proj(float(proj)) if when == "am" else float(proj)
        rows.append({"adp": float(adp), "x": x, "m": m, "actual": float(r["actual"]), "min": float(r["min"] or 0)})
    if len(rows) < 13:
        return []
    b = bars(rows)
    top = sorted(rows, key=lambda r: -r["x"])[:60]
    for r in top:
        r["boom_p"] = chance(BOOM, r["x"], b[id(r)], r["m"])
    moves = []
    for a, c in itertools.combinations([r for r in top if r["min"] > 0], 2):
        if abs(a["x"] - c["x"]) > 2 or a["adp"] == c["adp"] or a["boom_p"] == c["boom_p"]:
            continue
        up = a if a["boom_p"] > c["boom_p"] else c
        early = a if a["adp"] < c["adp"] else c
        if up is not early:                   # Boom would move him past the earlier ADP
            moves.append((abs(a["boom_p"] - c["boom_p"]) * 100, up, early))
    return moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True, help="a full clone of br-adp-mirror")
    mirror = ap.parse_args().mirror
    out = []
    for path in sorted(glob.glob(os.path.join(DAILY, "*_main.csv"))):
        day = os.path.basename(path)[:10]
        mo = morning_at(mirror, day)
        for when in ("am", "pm"):
            for label, lo, hi in (("under %d" % GAP, 0, GAP), ("%d+" % GAP, GAP, 1e9)):
                ms = [(up, early) for g, up, early in night(path, mo, when) if lo <= g < hi]
                if not ms:
                    continue
                out.append({"date": day, "when": when, "gap": label, "moves": len(ms),
                            "moved_won": sum(up["actual"] > early["actual"] for up, early in ms),
                            "pts_diff": round(sum(up["actual"] - early["actual"] for up, early in ms), 1),
                            "moved_boom": sum(up["actual"] >= up["x"] + 10 for up, early in ms),
                            "adp_boom": sum(early["actual"] >= early["x"] + 10 for up, early in ms)})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "when", "gap", "moves", "moved_won", "pts_diff", "moved_boom", "adp_boom"])
        w.writeheader()
        w.writerows(out)
    nights = sorted({r["date"] for r in out})
    print("Boom moves past an earlier ADP, %d nights (%s to %s); 50%% = no better than ADP" % (len(nights), nights[0], nights[-1]))
    for when in ("am", "pm"):
        for gap in ("under %d" % GAP, "%d+" % GAP):
            rs = [r for r in out if r["when"] == when and r["gap"] == gap]
            n = sum(r["moves"] for r in rs)
            if n:
                print("  %s, Boom gap %-8s %5d moves: moved-up outscored the earlier ADP %3.0f%% (%+.1f pts); boomed %3.0f%% vs %3.0f%%" % (
                    "morning  " if when == "am" else "afternoon", gap + ":", n, 100 * sum(r["moved_won"] for r in rs) / n,
                    sum(r["pts_diff"] for r in rs) / n, 100 * sum(r["moved_boom"] for r in rs) / n, 100 * sum(r["adp_boom"] for r in rs) / n))
    last = [r for r in out if r["date"] == nights[-1]]
    print("Last night (%s): " % nights[-1] + "; ".join("%s %s %d moves, won %d" % (r["when"], r["gap"], r["moves"], r["moved_won"]) for r in last))


if __name__ == "__main__":
    main()
