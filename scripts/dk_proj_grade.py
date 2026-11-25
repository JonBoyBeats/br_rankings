"""The projection grade by projection band (2026-11-25, the coordinator's request, the operator's yes). Grading only:
no projection changes here.

The miss grows with the projection in points (and falls as a share of it), and the bands fail differently, so the
headline is two bands by OUR projected DraftKings points at lock (fp_dk), players with fp_dk > 0 and a real score:
  ROTATION  10 <= fp_dk < 25   role and playing time: the worst minutes miss (about 7)
  STARS     fp_dk >= 25        the steadiest minutes, about 10 points of game swing
For each: points MAE, signed bias (actual - ours: positive means we projected him low), the share off by 10+ points,
and minutes MAE (|min - min_proj|), per slate and pooled. Players projected under 10 are one secondary line, with
the all-player MAE, so nothing drops out of view.

THE RULE (from now on): a projection change counts as an improvement only if it lowers the ROTATION band's minutes
MAE or the STARS band's points MAE, held out by slate, without making the other band worse beyond noise (its
per-slate mean change inside 2 x SE).

Beside it:
  ownership crossover  the same four numbers by projected field ownership at lock: 15%+, 5-15, 1-5, under 1 (own_raw
                       where the slate file has it, else own: the ownership the page showed before 2026-11-24's
                       correction is the raw one), with the 5-15% band's per-slate bias
  missed ceilings      per slate, the players who hit 5x their salary, with our projection, field ownership and their
                       share of the base bank (tags or ideas named BASE, Draw the 9's L0 U0 cell only; the whole bank
                       when the build has no base) from the saved build, n/a without one

  python3 scripts/dk_proj_grade.py [--md]      (dk_eval.py projgrade prints the same)
"""
import argparse, csv, glob, json, math, os, re, statistics as S

DK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "cbb", "dk")
BUILDS = os.path.join(DK, "builds")
ROTATION, STARS, LOW = (10.0, 25.0), (25.0, math.inf), 10.0
OWN_BANDS = [("15%+", 15.0, math.inf), ("5-15%", 5.0, 15.0), ("1-5%", 1.0, 5.0), ("under 1%", -math.inf, 1.0)]
FINE = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, math.inf)]
OFF = 10.0          # "off by 10+" in DraftKings points
CEIL_X = 5.0        # a ceiling game: 5x salary in thousands
BANK_LOW = 0.02     # "held under 2% of our bank"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def graded(rows):
    """The rows the grade uses: projected above 0 and a real DraftKings score."""
    return [r for r in rows if (num(r.get("fp_dk")) or 0) > 0 and num(r.get("actual_dk")) is not None]


def slates():
    """[(name, rows)] for every slate file with real scores, oldest first."""
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if any(num(r.get("actual_dk")) is not None for r in rows):
            out.append((os.path.basename(f)[:-4], rows))
    return out


def own_of(r):
    v = num(r.get("own_raw"))
    return v if v is not None else (num(r.get("own")) or 0.0)


def stats(rows):
    """n, points MAE, bias (actual - ours), share off by OFF+, minutes MAE (rows with both minutes)."""
    if not rows:
        return None
    e = [num(r["actual_dk"]) - num(r["fp_dk"]) for r in rows]
    m = [abs(num(r["min"]) - num(r["min_proj"])) for r in rows if num(r.get("min")) is not None and num(r.get("min_proj")) is not None]
    return {"n": len(e), "mae": S.mean(abs(x) for x in e), "bias": S.mean(e), "off": sum(abs(x) >= OFF for x in e) / len(e),
            "min_mae": S.mean(m) if m else None}


def band(rows, lo, hi, key=lambda r: num(r["fp_dk"])):
    return [r for r in rows if lo <= key(r) < hi]


def fmt(st):
    if not st:
        return "–"
    return "%.1f MAE, %+.1f bias, %.0f%% off 10+, min MAE %s (n %d)" % (st["mae"], st["bias"], 100 * st["off"],
                                                                       "%.1f" % st["min_mae"] if st["min_mae"] is not None else "–", st["n"])


def cells(st):
    if not st:
        return ["–"] * 5
    return ["%d" % st["n"], "%.1f" % st["mae"], "%+.1f" % st["bias"], "%.0f%%" % (100 * st["off"]),
            "%.1f" % st["min_mae"] if st["min_mae"] is not None else "–"]


def se_mean(xs):
    return S.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else None


def headline(sl):
    """{"per": [(name, rot, stars, low)], "pooled": (rot, stars, low, all)}"""
    per, P = [], []
    for n, rows in sl:
        g = graded(rows); P += g
        per.append((n, stats(band(g, *ROTATION)), stats(band(g, *STARS)), stats(band(g, 0, LOW))))
    return {"per": per, "pooled": (stats(band(P, *ROTATION)), stats(band(P, *STARS)), stats(band(P, 0, LOW)), stats(P))}


def crossover(sl):
    """Pooled stats per ownership band, and the 5-15% band's per-slate bias (positive count, mean, SE)."""
    P = [r for _, rows in sl for r in graded(rows)]
    pooled = [(nm, stats(band(P, lo, hi, own_of))) for nm, lo, hi in OWN_BANDS]
    lo, hi = OWN_BANDS[1][1], OWN_BANDS[1][2]
    per = []
    for n, rows in sl:
        st = stats(band(graded(rows), lo, hi, own_of))
        if st:
            per.append((n, st))
    b = [st["bias"] for _, st in per]
    return {"pooled": pooled, "mid_per": per, "mid_pos": sum(x > 0 for x in b), "mid_mean": S.mean(b) if b else None, "mid_se": se_mean(b),
            "src": "own_raw" if any(r.get("own_raw") not in (None, "") for _, rows in sl for r in rows) else "own"}


def base_tags(doc):
    """The build's base tags: a tag, or its idea name, containing the word BASE; of Draw the 9's cells only L0 U0."""
    groups = doc.get("groups") or {}
    tags = {t for ts in doc.get("tags") or [] for t in (ts if isinstance(ts, list) else [ts])}
    out = set()
    for t in tags:
        if not re.search(r"\bbase\b", "%s %s" % (t, groups.get(t) or ""), re.I):
            continue
        m = re.search(r"\bL([\d.]+) U([\d.]+)$", t)
        if m and (float(m.group(1)) != 0 or float(m.group(2)) != 0):
            continue
        out.add(t)
    return out


def bank_shares(name):
    """({dk_id: share}, "base" | "whole bank") from the slate's saved build, or (None, None)."""
    f = os.path.join(BUILDS, "dk_bank_%s.json" % name)
    if not os.path.exists(f):
        return None, None
    doc = json.load(open(f))
    pool, tags = doc.get("pool") or [], doc.get("tags") or []
    bt = base_tags(doc)
    idx = [k for k in range(len(pool)) if bt and any(t in bt for t in (tags[k] if k < len(tags) and isinstance(tags[k], list) else [tags[k] if k < len(tags) else ""]))]
    kind = "base"
    if not idx:
        idx, kind = list(range(len(pool))), "whole bank"
    sh = {}
    for k in idx:
        for i in pool[k]:
            sh[str(i)] = sh.get(str(i), 0) + 1.0 / len(idx)
    return sh, kind


def ceilings(sl):
    """[(name, kind, [(name, team, salary, actual, fp_dk, own, bank share or None)], n_proj_under_10, n_bank_under_2pct)]"""
    out = []
    for n, rows in sl:
        hits = [r for r in rows if num(r.get("actual_dk")) is not None and num(r.get("salary")) and num(r["actual_dk"]) >= CEIL_X * num(r["salary"]) / 1000]
        sh, kind = bank_shares(n)
        lst = [(r["name"], r.get("team"), int(num(r["salary"])), num(r["actual_dk"]), num(r.get("fp_dk")) or 0.0, own_of(r),
                (sh.get(str(r.get("dk_id")), 0.0) if sh is not None else None)) for r in hits]
        lst.sort(key=lambda x: -x[3])
        out.append((n, kind, lst, sum(x[4] < LOW for x in lst), sum(x[6] is not None and x[6] < BANK_LOW for x in lst) if sh is not None else None))
    return out


def fine(sl):
    """The 0-5 ... 30+ check bands, pooled."""
    P = [r for _, rows in sl for r in graded(rows)]
    return [((lo, hi), stats(band(P, lo, hi))) for lo, hi in FINE]


def lines(sl=None, md=False):
    sl = sl if sl is not None else slates()
    if not sl:
        return ["Projection grade: no graded slates yet"]
    h, c, ce = headline(sl), crossover(sl), ceilings(sl)
    rot, stars, low, allp = h["pooled"]
    out = ["Projection grade by projection band, %d graded slates (%s to %s); bias = actual - ours." % (len(sl), sl[0][0], sl[-1][0]),
           "  ROTATION 10-25 (minutes is its lens): " + fmt(rot),
           "  STARS 25+ (points is its lens):       " + fmt(stars),
           "  secondary, projected under 10: %s; all players: %s" % (fmt(low), fmt(allp)),
           "  Rule: a projection change counts only if it lowers ROTATION minutes MAE or STARS points MAE, held out by slate, without worsening the other band beyond noise (2 x SE)."]
    if md:
        out += ["", "| Slate | Rotation n | MAE | bias | off 10+ | min MAE | Stars n | MAE | bias | off 10+ | min MAE | under 10: MAE |", "|---|" + "---|" * 11]
        for n, a, b, l in h["per"]:
            out.append("| %s | %s | %s | %s |" % (n, " | ".join(cells(a)), " | ".join(cells(b)), "%.1f" % l["mae"] if l else "–"))
        out.append("| **pooled** | %s | %s | %.1f |" % (" | ".join("**%s**" % x for x in cells(rot)), " | ".join("**%s**" % x for x in cells(stars)), low["mae"] if low else float("nan")))
    else:
        out.append("  per slate (rotation | stars: MAE bias off10 minMAE):")
        for n, a, b, l in h["per"]:
            f = lambda st: "%4.1f %+5.1f %3.0f%% %4s" % (st["mae"], st["bias"], 100 * st["off"], "%.1f" % st["min_mae"] if st["min_mae"] is not None else "–") if st else "   –"
            out.append("    %-18s %s | %s" % (n, f(a), f(b)))
    out += ["", "Ownership crossover (projected field ownership at lock, %s):" % c["src"]]
    for nm, st in c["pooled"]:
        out.append("  %-9s %s" % (nm, fmt(st)))
    if c["mid_mean"] is not None:
        out.append("  5-15%% band bias per slate: positive on %d of %d, mean %+.1f (SE %s)%s" % (
            c["mid_pos"], len(c["mid_per"]), c["mid_mean"], "%.1f" % c["mid_se"] if c["mid_se"] else "–",
            "; " + ", ".join("%s %+.1f (n %d)" % (n, st["bias"], st["n"]) for n, st in c["mid_per"])))
    tot = sum(len(x[2]) for x in ce)
    out += ["", "Missed ceilings (5x salary), %d hits: %d projected under 10; %d held under 2%% of our bank (of %d hits on slates with a saved build)." % (
        tot, sum(x[3] for x in ce), sum(x[4] or 0 for x in ce), sum(len(x[2]) for x in ce if x[4] is not None))]
    for n, kind, lst, u10, b2 in ce:
        out.append("  %s: %d hits, %d projected under 10, %s%s" % (n, len(lst), u10, "%d under 2%% of the %s" % (b2, kind) if b2 is not None else "bank n/a (no saved build)",
                   (": " + "; ".join("%s %d (ours %.0f, own %.0f%%, bank %s)" % (x[0], round(x[3]), x[4], x[5], "%.0f%%" % (100 * x[6]) if x[6] is not None else "n/a") for x in lst)) if lst else ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--check", action="store_true", help="the 0-5 ... 30+ bands, pooled (the coordinator's check)")
    a = ap.parse_args()
    if a.check:
        for (lo, hi), st in fine(slates()):
            print("%2d-%-4s %s" % (lo, "" if hi == math.inf else int(hi), fmt(st)))
        return
    print("\n".join(lines(md=a.md)))


if __name__ == "__main__":
    main()
