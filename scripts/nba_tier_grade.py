"""NBA grade by combined tier: every season number cut by tier and window, from analysis/nba/report/tier_history.csv.

Decision pairs only: two players in the same combined tier whose ADP at that window's lock is within 4 picks. T3 and
T4 are graded as one middle band (T3/T4) and also apart, with pairs straddling the T3/T4 line on their own; pairs
straddling the other lines (adjacent tiers, ADP within 4) are reported apart as a check on where the lines fall.

Every slot is scored with the swap rule: T5 counts only players with a draft ADP (below that, the board's order is its tail sort, not a choice). A
player who sat counts his swap's points (his credited swaps in swaps.csv,
else that night's average swap, else the season's), and he is not a breaker.

  head to head   your locked board against each source in the window (AM: ours, ADP; PM: ETR, ours at Lock PM, ADP):
                 on the pairs the two order differently, how often yours was right, points per pair (what your order
                 gained over the source's), and on those where exactly one broke, how often yours took the breaker
  flags          VALUE against its pair partners (did it outscore them?) and PRICEY (did it lag them?)
  sources        each projection's error (mean absolute), bias (actual minus projection) and rank correlation with
                 the actual inside each tier, per slate then averaged; ADP's rank correlation beside them

Evidence: LEAN = 40+ pairs and 80%+ of resamples (by slate) on one side; RULE = 80+ pairs, a 90% range clear of zero,
the same side on the last 5 slates as on the ones before, and no single player whose pairs, taken out, flip it.
Under 40 pairs: "not enough yet (n)". Writes analysis/nba/report/tier_grade.md.

  python3 scripts/nba_tier_grade.py
"""
import collections, csv, glob, math, os, random

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = os.path.join(HERE, "analysis", "nba", "report")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(REP, "tier_grade.md")
DECISION = 4
RESAMPLES = 2000


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load():
    H = list(csv.DictReader(open(os.path.join(REP, "tier_history.csv"))))
    sw, night = collections.defaultdict(lambda: [0, 0.0]), collections.defaultdict(lambda: [0, 0.0])
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        n = int(r["teams"])
        for d, k in ((sw, (r["date"], r["out_id"])), (night, r["date"])):
            d[k][0] += n
            d[k][1] += n * float(r["swap_fp"])
    season = sum(v[1] for v in night.values()) / max(1, sum(v[0] for v in night.values()))
    extra = {}
    for p in glob.glob(os.path.join(DAILY, "*_main.csv")):
        for r in csv.DictReader(open(p)):
            extra[(r["date"], r["player_id"])] = r
    for r in H:
        if r["scratched"] == "1":
            k = (r["date"], r["player_id"])
            v = sw[k][1] / sw[k][0] if k in sw else (night[r["date"]][1] / night[r["date"]][0] if r["date"] in night else season)
            r["slot"], r["slot_brk"] = v, 0
        else:
            r["slot"], r["slot_brk"] = num(r["actual"]), int(r["breaker"] or 0)
        e = extra.get((r["date"], r["player_id"]), {})
        r["ours_pm"] = num(e.get("ours_pm"))
        r["etr_first"] = num(e.get("etr_first"))
    return [r for r in H if r["slot"] is not None]


def cap(r):
    return 24.0 if r["pod"] == "4" else 36.0


def adp(r):
    return num(r["adp"]) if num(r["adp"]) is not None else cap(r)


def sources(window):
    """[(name, key)]: key(row) -> a value, higher first (None: no value)."""
    out = [("ADP", lambda r: -adp(r))]
    if window == "am":
        out.insert(0, ("Ours", lambda r: num(r["proj"])))
    else:
        out[:0] = [("ETR", lambda r: num(r["proj"])), ("Ours PM", lambda r: r["ours_pm"])]
    return out


def pairs(rows, inside, across=None):
    """Decision pairs of one slate-window: inside a tier group (a set of tiers graded as one), or straddling a line
    (across: (upper tier, lower tier))."""
    out = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            x, y = rows[i], rows[j]
            if abs(adp(x) - adp(y)) > DECISION:
                continue
            tx, ty = int(x["tier"]), int(y["tier"])
            if across:
                if {tx, ty} != set(across):
                    continue
            elif tx not in inside or ty not in inside:
                continue
            out.append((x, y))
    return out


CHECK_SLATES, CHECK_BEFORE = 5, 9     # a RULE is chosen on the slates before the last 5 (at least 9) and checked on those 5
AUDIT = []                            # every cell graded: (cut, tier, test, n, label, the RULE bar part by part)


def verdict(per, players=None, where=None):
    """per: {slate: [values]} (positive = the thing graded wins). Returns (n, mean, lo80, hi80, label).
    A cell that clears the RULE bar's own numbers (80+ pairs, a 90% range clear of zero) but can't be checked yet
    (fewer than 14 slates: 9 to choose on, 5 to check) or fails the check or the drop-one-player test is a LEAN."""
    ds = sorted(per)
    allv = [v for d in ds for v in per[d]]
    n = len(allv)
    if not n:
        return 0, None, None, None, "-"
    mean = sum(allv) / n
    if n < 40:
        if where:
            AUDIT.append(where + (n, "not enough yet", ""))
        return n, mean, None, None, "not enough yet (%d)" % n
    rnd = random.Random(7)
    bs = []
    for _ in range(RESAMPLES):
        s = [v for d in (rnd.choice(ds) for _ in ds) for v in per[d]]
        if s:
            bs.append(sum(s) / len(s))
    bs.sort()
    q = lambda p: bs[min(len(bs) - 1, int(p * len(bs)))]
    lo80, hi80, lo90, hi90 = q(0.1), q(0.9), q(0.05), q(0.95)
    side = 1 if mean > 0 else -1
    share = sum(1 for b in bs if b * side > 0) / len(bs)
    label, audit = "no lean", ""
    if share >= 0.8:
        label = "LEAN " + ("+" if side > 0 else "-")
    if n >= 80 and (lo90 > 0 or hi90 < 0):
        parts = ["80+ pairs: yes", "90% range clear of 0: yes"]
        if len(ds) >= CHECK_BEFORE + CHECK_SLATES:
            early, late = [v for d in ds[:-CHECK_SLATES] for v in per[d]], [v for d in ds[-CHECK_SLATES:] for v in per[d]]
            same = bool(early and late) and (sum(early) > 0) == (sum(late) > 0) == (side > 0)
            parts.append("check slates (last %d) same side: %s" % (CHECK_SLATES, "yes" if same else "no"))
        else:
            same = None
            parts.append("check slates: can't yet (%d slates, needs %d)" % (len(ds), CHECK_BEFORE + CHECK_SLATES))
        flip = None
        if players:
            flip = next((p for p, vals in players.items() if n - len(vals) and
                         ((sum(allv) - sum(vals)) / (n - len(vals))) * side <= 0), None)
            parts.append("drop one player: %s" % ("flips without %s" % flip if flip else "holds"))
        if same and players and not flip:
            label = "RULE " + ("+" if side > 0 else "-")
        else:
            label = "LEAN " + ("+" if side > 0 else "-") + " (RULE numbers, %s)" % (
                "check pending" if same is None else "check failed" if not same else "one player flips it")
        audit = "; ".join(parts)
    if where:
        AUDIT.append(where + (n, label, audit))
    return n, mean, lo80, hi80, label


def fmt(v):
    n, mean, lo, hi, label = v
    if not n:
        return "-"
    if lo is None:
        return "%+.1f, %s" % (mean, label)
    return "%+.1f (%+.1f to %+.1f), %d pairs, %s" % (mean, lo, hi, n, label)


def grade(H, pod, window, sample, groups):
    rows = [r for r in H if r["pod"] == pod and r["window"] == window and (sample is None or r["sample"] == sample)
            and (r["tier"] != "5" or (num(r["adp"]) is not None and num(r["adp"]) < cap(r)))]   # T5: drafted players only
    by_slate = collections.defaultdict(list)
    for r in rows:
        by_slate[r["date"]].append(r)
    out = []
    for gname, inside, across in groups:
        h2h = {s: (collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)) for s, _ in sources(window)}
        hits = {s: [0, 0] for s, _ in sources(window)}
        brk = {s: [0, 0] for s, _ in sources(window)}
        flags = {"VALUE": collections.defaultdict(list), "PRICEY": collections.defaultdict(list)}
        fplayers = {"VALUE": collections.defaultdict(list), "PRICEY": collections.defaultdict(list)}
        nights = set()
        for d, rs in by_slate.items():
            for x, y in pairs(rs, inside, across):
                if x["slot"] == y["slot"]:
                    continue
                nights.add(d)
                for (s, key) in sources(window):
                    if not x["your_rank"] or not y["your_rank"]:
                        continue
                    kx, ky = key(x), key(y)
                    if kx is None or ky is None or kx == ky:
                        continue
                    you = int(x["your_rank"]) < int(y["your_rank"])
                    if you == (kx > ky):
                        continue
                    a, b = (x, y) if you else (y, x)
                    g = a["slot"] - b["slot"]
                    h2h[s][0][d].append(g)
                    for p in (a["player_id"], b["player_id"]):
                        h2h[s][1][p].append(g)
                    hits[s][0] += g > 0
                    hits[s][1] += 1
                    if a["slot_brk"] + b["slot_brk"] == 1:
                        brk[s][0] += a["slot_brk"]
                        brk[s][1] += 1
                for f in ("VALUE", "PRICEY"):
                    if (x["flag"] == f) != (y["flag"] == f):
                        a, b = (x, y) if x["flag"] == f else (y, x)
                        g = (a["slot"] - b["slot"]) * (1 if f == "VALUE" else -1)
                        flags[f][d].append(g)
                        fplayers[f][a["player_id"]].append(g)
        out.append((gname, len(nights), h2h, hits, brk, flags, fplayers))
    return out


def source_errors(H, pod, window, sample, tiers):
    out = {}
    rows = [r for r in H if r["pod"] == pod and r["window"] == window and (sample is None or r["sample"] == sample)
            and int(r["tier"]) in tiers]
    names = [("Ours", "proj")] if window == "am" else [("ETR", "proj"), ("Ours PM", "ours_pm")]
    by_slate = collections.defaultdict(list)
    for r in rows:
        by_slate[r["date"]].append(r)
    for name, col in names + [("ADP", None)]:
        errs, bias, cors = [], [], []
        for d, rs in by_slate.items():
            if col:
                vs = [(num(r[col]) if col == "proj" else r[col], r["slot"]) for r in rs]
                vs = [(v, a) for v, a in vs if v is not None]
            else:
                vs = [(-adp(r), r["slot"]) for r in rs]
            if len(vs) < 4:
                continue
            if col:
                errs += [abs(a - v) for v, a in vs]
                bias += [a - v for v, a in vs]
            cors.append(spearman([v for v, _ in vs], [a for _, a in vs]))
        cors = [c for c in cors if c is not None]
        out[name] = (sum(errs) / len(errs) if errs else None, sum(bias) / len(bias) if bias else None,
                     sum(cors) / len(cors) if cors else None, len(cors))
    return out


def spearman(a, b):
    def ranks(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    sab = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    saa, sbb = sum((x - ma) ** 2 for x in ra), sum((y - mb) ** 2 for y in rb)
    return sab / math.sqrt(saa * sbb) if saa and sbb else None


GROUPS = [("T1", {1}, None), ("T2", {2}, None), ("T3/T4 (middle)", {3, 4}, None), ("T3", {3}, None), ("T4", {4}, None),
          ("T5", {5}, None), ("Across T1/T2", None, (1, 2)), ("Across T2/T3", None, (2, 3)),
          ("Across T3/T4", None, (3, 4)), ("Across T4/T5", None, (4, 5))]
CUTS = [("6", "am", "primary", "6-drafter AM, primary (Lock AM on our Proj, 10-28 on)"),
        ("6", "am", "secondary", "6-drafter AM, secondary (10-21 to 10-27 on the raw morning file; 11-08 an afternoon board)"),
        ("6", "pm", None, "6-drafter PM"),
        ("4", "am", None, "4-drafter AM (small slates)"),
        ("4", "pm", None, "4-drafter PM (small slates)")]


def main():
    H = load()
    out = ["# NBA grade by combined tier", "",
           "Written by scripts/nba_tier_grade.py from tier_history.csv. Decision pairs (same tier, ADP within 4 at the lock); "
           "a player who sat is scored with his swap. Each cell: points per pair (80% range from resampling slates), pairs, "
           "and the evidence level. Head to head: positive = your board beat the source on the pairs you ordered differently.", ""]
    for pod, window, sample, title in CUTS:
        res = grade(H, pod, window, sample, GROUPS)
        srcs = [s for s, _ in sources(window)]
        out += ["## " + title, "", "### Your board against each source", "",
                "| Tier | Nights | " + " | ".join(srcs) + " |", "|---|---|" + "---|" * len(srcs)]
        for gname, nights, h2h, hits, brk, _, _ in res:
            cells = []
            for s in srcs:
                v = verdict(h2h[s][0], h2h[s][1], (title, gname, "your board vs " + s))
                right = "%.0f%% right" % (100 * hits[s][0] / hits[s][1]) if hits[s][1] else ""
                b = "breaker %d of %d" % (brk[s][0], brk[s][1]) if brk[s][1] else ""
                cells.append("; ".join(x for x in (fmt(v), right, b) if x and x != "-") or "-")
            out.append("| %s | %d | %s |" % (gname, nights, " | ".join(cells)))
        out += ["", "### The flag test (positive: VALUE outscored its partners / PRICEY lagged them)", "",
                "| Tier | VALUE | PRICEY |", "|---|---|---|"]
        for gname, nights, _, _, _, flags, fpl in res:
            out.append("| %s | %s | %s |" % (gname, fmt(verdict(flags["VALUE"], fpl["VALUE"], (title, gname, "VALUE flag"))),
                                             fmt(verdict(flags["PRICEY"], fpl["PRICEY"], (title, gname, "PRICEY flag")))))
        out += ["", "### Each source inside the tier (error = mean |actual - projection|; bias = actual - projection; rank correlation per slate, averaged)", "",
                "| Tier | " + " | ".join(srcs) + " |", "|---|" + "---|" * len(srcs)]
        for gname, tiers in (("T1", {1}), ("T2", {2}), ("T3/T4", {3, 4}), ("T5 (priced)", {5})):
            e = source_errors([r for r in H if not (tiers == {5} and num(r["adp"]) is None)], pod, window, sample, tiers)
            cells = []
            for s in srcs:
                err, bias, cor, n = e.get(s, (None, None, None, 0))
                cells.append(("err %.1f, bias %+.1f, " % (err, bias) if err is not None else "") +
                             ("rank corr %.2f (%d slates)" % (cor, n) if cor is not None else "-"))
            out.append("| %s | %s |" % (gname, " | ".join(cells)))
        out.append("")
    tested = [a for a in AUDIT if a[3] >= 40]
    leans = [a for a in tested if a[4].startswith(("LEAN", "RULE"))]
    out += ["## How many of these could be chance", "",
            "%d cells were graded (%d with 40+ pairs, so testable). The 80%% LEAN bar means about 80%% of resamples on one "
            "side, which a cell with no real effect clears about 40%% of the time (|mean| at least 0.84 standard errors, "
            "either side). So with %d testable cells, about %d leans would appear by chance alone; %d did. Treat any single "
            "lean as a candidate, and weigh the ones that repeat in both windows or across tiers." % (
                len(AUDIT), len(tested), len(tested), round(0.4 * len(tested)), len(leans)), "",
            "## The RULE bar, part by part", "", "| Cut | Tier | Test | Pairs | Label | Parts |", "|---|---|---|---|---|---|"]
    out += ["| %s | %s | %s | %d | %s | %s |" % a for a in AUDIT if a[5]]
    open(OUT, "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
