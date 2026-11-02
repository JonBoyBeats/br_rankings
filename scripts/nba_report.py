"""NBA morning report: your board against the straight orders, and your tier rules, for the last
slate and the season.

Reads analysis/nba/daily/*.csv (scripts/nba_daily.py) and prints Markdown, in the order it goes
in chat:

  Headline     every pair your board and a straight order (ours, ETR, ADP) disagree on: how often
               yours was right. Morning: your AM board against ours and ADP; afternoon: your PM
               board against ETR, ours and ADP at lock. Over 50% and settled: your moves beat it.
  Tier rules   inside each of your tiers (the board's tier lines at each lock), the rule written
               beside it on the board, against ADP and the half's projection straight, and whether
               your own moves off the rule paid. A verdict only after TIER_NIGHTS nights.
  Ours vs ETR  how our morning number tracks ETR's first and last uploads.
  For the log  your biggest calls, our biggest misses and splits, the ADP movers tally: written up in
               misses.csv for the themes, not shown in chat.

Each barbell scores the night's top 48 by its ADP plus anyone a source put in its top 48. A player
who didn't play, or who left early (see gone_early), isn't scored at all: there is nothing to learn
from him.

Late news: analysis/nba/report/late_news.json lists, per slate, the teams whose news broke after a
lock (a player drafted early ruled out late). Their players are left out of that half's grading, so
the scramble around a late scratch doesn't count for or against anyone.

Over several slates a difference carries an 80% range from resampling the slates; a range that
spans 0 isn't settled yet.

  python3 scripts/nba_report.py [--date YYYY-MM-DD] [--mirror ../br-adp-mirror]

--mirror (a full clone of br-adp-mirror) gives the tier rules the board's Boom %, for the rules
that use it; without it Boom is skipped and the rule falls to its next key.
"""
import argparse, csv, datetime as dt, glob, json, os, random
from zoneinfo import ZoneInfo

DAILY = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "daily")
LATE_FILE = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "report", "late_news.json")
LATE = json.load(open(LATE_FILE)) if os.path.exists(LATE_FILE) else {}   # {date: {"am": [teams], "pm": [teams], "note": ...}}
DEPTH, GAP = 48, 3
# Left early: a player who usually plays EARLY_USUAL+ minutes and got under half of them in a game
# decided by less than EARLY_MARGIN. A starter cut that short in a close game is almost always hurt;
# a bench player's short night is usually the rotation, which is worth learning from, so he stays.
EARLY_USUAL, EARLY_MARGIN = 25, 15
TEXT = ("date", "slate", "player_id", "name", "team", "pos", "injury", "opp", "fg", "fg3", "ft", "mtch_label", "mtch_cats")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load():
    slates = []
    for path in sorted(glob.glob(os.path.join(DAILY, "*.csv"))):
        rows = list(csv.DictReader(open(path)))
        if not rows or "am_rank" not in rows[0]:
            continue
        for r in rows:
            for k in r:
                if k not in TEXT:
                    r[k] = num(r[k])
        slates.append({"file": os.path.basename(path), "date": rows[0]["date"], "slate": rows[0]["slate"], "rows": rows})
    return slates


# ---------------------------------------------------------------- the two barbells
class Src:
    def __init__(self, col, label, higher, fallback=None):
        self.col, self.label, self.higher, self.fallback = col, label, higher, fallback

    def col_for(self, rows):
        """The column, or its fallback on a slate that doesn't have it (our Proj before the board kept it)."""
        if self.fallback and not any(r[self.col] is not None for r in rows):
            return self.fallback
        return self.col

    def key(self, rows):
        c = self.col_for(rows)
        return lambda r: None if r[c] is None else (r[c] if self.higher else -r[c])


AM = {"adp": "adp_am", "half": "am", "sources": [Src("am_rank", "Your AM ranks", False), Src("ours_am", "Ours at Lock AM", True, "ours_raw"),
                                   Src("adp_am", "ADP at Lock AM", False)]}
PM = {"adp": "adp_close", "half": "pm", "sources": [Src("pm_rank", "Your PM ranks", False), Src("etr_last", "ETR last upload", True),
                                      Src("ours_pm", "Ours at Lock PM", True), Src("adp_close", "ADP at lock", False)]}


def gone_early(r):
    return ((r["usual_min"] or 0) >= EARLY_USUAL and r["min"] is not None and r["min"] < r["usual_min"] / 2
            and (r["margin"] is None or abs(r["margin"]) < EARLY_MARGIN))


def graded(r):
    """He played, and didn't leave early."""
    return r["actual"] is not None and (r["min"] or 0) > 0 and not gone_early(r)


def pool(rows, bar, late=True):
    """The barbell's top DEPTH by its ADP, plus each source's top DEPTH; who played and didn't leave early,
    and (late) wasn't on a team with late news for that half."""
    skip = set(LATE.get(rows[0]["date"], {}).get(bar.get("half"), [])) if late and rows else set()
    have = [r for r in rows if r[bar["adp"]] is not None and graded(r) and r["team"] not in skip]
    keep = set()
    for s in bar["sources"]:
        k = s.key(rows)
        keep.update(id(r) for r in sorted((r for r in have if k(r) is not None), key=lambda r: -k(r))[:DEPTH])
    return [r for r in have if id(r) in keep]


def ranks(vals):
    """Average ranks, 1 = smallest."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out, i = [0.0] * len(vals), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return out


def corr(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx, syy = sum((x - mx) ** 2 for x in xs), sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5 if sxx and syy else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


# ---------------------------------------------------------------- per slate
def cached(fn):
    """Per slate, bar and sources: the resampling asks for the same slate many times."""
    memo = {}
    def wrap(rows, bar, *srcs):
        k = (id(rows), bar["adp"]) + tuple((x.col, x.label) if isinstance(x, Src) else x for x in srcs)
        if k not in memo:
            memo[k] = fn(rows, bar, *srcs)
        return memo[k]
    return wrap


@cached
def calls(rows, bar, a, b):
    """Pairs a and b order differently: (a right, b right)."""
    ka, kb = a.key(rows), b.key(rows)
    p = [r for r in pool(rows, bar) if ka(r) is not None and kb(r) is not None]
    win = lose = 0
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            x, y = p[i], p[j]
            da, db = ka(x) - ka(y), kb(x) - kb(y)
            if da * db >= 0 or x["actual"] == y["actual"]:
                continue
            if (da > 0) == (x["actual"] > y["actual"]):
                win += 1
            else:
                lose += 1
    return win, lose


# ---------------------------------------------------------------- over slates
def boot(slates, fn):
    """80% range of fn over resampled slates, or None with fewer than 3."""
    if len(slates) < 3:
        return None
    rnd = random.Random(7)
    vals = sorted(v for v in (fn([rnd.choice(slates) for _ in slates]) for _ in range(300)) if v is not None)
    return (vals[len(vals) // 10], vals[len(vals) * 9 // 10]) if vals else None


def rng(r, spec):
    return "" if not r else " (%s to %s)" % (spec % r[0], spec % r[1])


def fmt(v, spec="%.2f"):
    return "-" if v is None else spec % v


def call_rate(slates, bar, a, b):
    w = l = 0
    for x in slates:
        ww, ll = calls(x["rows"], bar, a, b)
        w, l = w + ww, l + ll
    return (w / (w + l) if w + l else None), w + l


def headline(last, upto, bar, title, h2h):
    """Your board head to head against each straight order: last night, the season, and a verdict."""
    out = ["### " + title, "", "| Your board against | Last night | Season | Range | So far |", "|---|---|---|---|---|"]
    for a, b in h2h:
        r1, n1 = call_rate(last, bar, a, b)
        r2, n2 = call_rate(upto, bar, a, b)
        rg = boot([x for x in upto if sum(calls(x["rows"], bar, a, b))], lambda xs: call_rate(xs, bar, a, b)[0])
        verdict = ("not enough slates" if not rg else "your board wins" if rg[0] > 0.5
                   else "%s alone wins" % b.label if rg[1] < 0.5 else "too close to call")
        out.append("| %s | %s | %s of %d pairs | %s | %s |" % (
            b.label, "%.0f%%" % (100 * r1) if r1 is not None else "-", "%.0f%%" % (100 * r2) if r2 is not None else "-", n2,
            "%.0f-%.0f%%" % (100 * rg[0], 100 * rg[1]) if rg else "-", verdict if r2 is not None else "-"))
    return out + [""]


ETRB = {"adp": "adp_close", "half": "am", "sources": [Src("ours_am", "Ours (morning)", True, "ours_raw"), Src("etr_first", "ETR first", True),
                                        Src("etr_last", "ETR last", True)]}


def ours_vs_etr(last, upto):
    """How our morning number tracks ETR's first and last uploads: order, gap, whether ETR moved our way, and who was closer."""
    raw = [r for x in upto for r in pool(x["rows"], ETRB) if r["ours_raw"] is not None and r["etr_first"] is not None and r["etr_last"] is not None]
    xs, ys = [r["ours_raw"] for r in raw], [(r["etr_first"] + r["etr_last"]) / 2 for r in raw]
    mx, my = mean(xs), mean(ys)
    sxx = sum((v - mx) ** 2 for v in xs) if raw else 0
    a = sum((v - mx) * (u - my) for v, u in zip(xs, ys)) / sxx if sxx else 1

    def players(xs_):
        out = []
        for x in xs_:
            c = ETRB["sources"][0].col_for(x["rows"])
            rs = [r for r in pool(x["rows"], ETRB) if r[c] is not None and r["etr_first"] is not None and r["etr_last"] is not None]
            ps = [(r[c] if c == "ours_am" else a * r[c] + my - a * mx, r["etr_first"], r["etr_last"], r["actual"]) for r in rs]
            # each relative to its slate average, so a slate-wide shift (ETR running high, or moving the whole slate) isn't agreement or a miss
            avg = [mean([p[i] for p in ps]) for i in range(4)]
            out.append([tuple(p[i] - avg[i] for i in range(4)) for p in ps])
        return out

    def cell(xs_, f, spec):
        return fmt(f(players(xs_)), spec)

    def both(f, spec):
        return "%s (%s)" % (cell(last, f, spec), cell(upto, f, spec))

    flat = lambda gs: [p for g in gs for p in g]
    rho = lambda i: lambda gs: mean([corr(ranks([p[0] for p in g]), ranks([p[i] for p in g])) for g in gs if len(g) >= 5])
    near = lambda i: lambda gs: (lambda f: 100 * sum(abs(p[0] - p[i]) < GAP for p in f) / len(f) if f else None)(flat(gs))
    apart = lambda gs: [p for p in flat(gs) if abs(p[0] - p[1]) >= GAP]
    toward = lambda gs: (lambda f: 100 * sum((p[2] - p[1]) * (p[0] - p[1]) > 0 for p in f) / len(f) if f else None)(apart(gs))
    closer = lambda i: lambda gs: (lambda f: 100 * sum(abs(p[0] - p[3]) < abs(p[i] - p[3]) for p in f) / len(f) if f else None)(
        [p for p in flat(gs) if abs(p[0] - p[i]) >= GAP])
    miss = lambda i: lambda gs: mean([abs(p[i] - p[3]) for p in flat(gs)])
    return ["### Ours vs ETR", "",
            "Our Proj at Lock AM against ETR's last upload, player by player (each taken against its slate's average). "
            "Last night (season): rank corr %s; within %d pts %s; where %d+ apart ours was closer to the actual %s; "
            "average miss ours %s, ETR %s. Where ETR's first upload started %d+ from ours, its last moved our way %s." % (
                both(rho(2), "%.2f"), GAP, both(near(2), "%.0f%%"), GAP, both(closer(2), "%.0f%%"), both(miss(0), "%.1f"),
                both(miss(2), "%.1f"), GAP, both(toward, "%.0f%%")), ""]


MOVE = 1.0    # picks: an ADP move worth listing


def adp_movers(rows, date):
    """ADP's move from ETR's first upload to lock, for players with no news of their own: no injury
    tag on him or his team, no regular (20+ usual minutes) of his sitting, his team not on the late-news
    list. Everyone drafted at one end or the other; [(row, move in picks, + = rose)]."""
    pile = max((r["adp_close"] or 0) for r in rows) or 0
    late = set(LATE.get(date, {}).get("pm", []))
    out_teams = {r["team"] for r in rows if r["actual"] is not None and (r["min"] or 0) == 0 and (r["usual_min"] or 0) >= 20}
    tagged = {r["team"] for r in rows if r["injury"]}
    out = []
    for r in rows:
        if r["adp_etr"] is None or r["adp_close"] is None or r["etr_last"] is None or not graded(r):
            continue
        if r["adp_etr"] >= pile and r["adp_close"] >= pile:
            continue
        if r["team"] in late or r["team"] in out_teams or r["team"] in tagged:
            continue
        out.append((r, r["adp_etr"] - r["adp_close"]))
    return out


def movers_line(upto):
    """The ADP movers watch list, season tally only: players ADP moved a pick or more on after ETR posted."""
    every = [(r, m) for x in upto for r, m in adp_movers(x["rows"], x["date"])]
    flat = [r["actual"] - r["etr_last"] for r, m in every if abs(m) < MOVE]
    up = [r["actual"] - r["etr_last"] for r, m in every if m >= MOVE]
    down = [r["actual"] - r["etr_last"] for r, m in every if m <= -MOVE]
    if not flat:
        return []
    line = lambda xs: "%d, %+.1f against the unmoved" % (len(xs), mean(xs) - mean(flat)) if xs else "none"
    return ["ADP movers after ETR posted, no injury news (season, actual against ETR's last, next to the %d ADP left within a pick): "
            "risers %s; fallers %s. A lean only once each side has 50+." % (len(flat), line(up), line(down)), ""]


def short(name):
    """A last name for a list: "Michael Porter Jr." reads Porter."""
    parts = [w for w in name.split() if w.rstrip(".") not in ("Jr", "Sr", "II", "III", "IV")]
    return parts[-1] if parts else name


# ---------------------------------------------------------------- tier rules
TIER_NIGHTS = 14     # nights a tier needs before its verdict counts. Set 2026-11-02, before any result: don't move it.
# Your rule for each tier, as written beside it on the board (NBA_TIER_NOTES in index.html): morning on our
# Proj, afternoon on ETR. Each step is (key, within): order by the key, and when two players are within
# `within` of each other on it, go to the next step. adp: earlier first, in picks. proj: higher first, in
# whole points as the board shows them. projx: higher first, decimals counting. boom: higher Boom % first.
# Whatever a rule leaves level goes by the projection, then ADP.
MIDDLE_AM = ("Proj (3: ADP)", [("proj", 3), ("adp", 0)])
MIDDLE_PM = ("ETR (Tie: ADP -> Boom)", [("proj", 0), ("adp", 0), ("boom", 0)])
TIER_RULES = {
    "am": {1: ("ADP (2: Boom)", [("adp", 2), ("boom", 0)]), 2: ("ADP", [("adp", 0)]), 3: MIDDLE_AM, 4: MIDDLE_AM, 5: MIDDLE_AM},
    "pm": {1: ("ETR", [("projx", 0)]), 2: ("ADP (1: ETR)", [("adp", 1), ("projx", 0)]), 3: MIDDLE_PM, 4: MIDDLE_PM,
           5: ("ETR", [("projx", 0)])},
}
TIER_HALVES = {"am": (AM, "am_tier", "ours_am", "Proj"), "pm": (PM, "pm_tier", "etr_last", "ETR")}
MIRROR = None        # --mirror: a full clone of br-adp-mirror, for Boom


def boom_of(rows, half):
    """{id(row): the board's Boom %} for the half (morning on our Proj, afternoon on ETR), or {} without --mirror."""
    if not MIRROR:
        return {}
    import nba_boom_ties as B
    adp, col = ("adp_am", "ours_am") if half == "am" else ("adp_close", "etr_last")
    mo = B.morning_at(MIRROR, rows[0]["date"])
    items = []
    for r in rows:
        m = mo.get(B.norm(r["name"]))
        if r[adp] is None or r[col] is None or not m or m.get("ppm") is None:
            continue
        items.append({"adp": r[adp], "x": B.median_of_proj(r[col]), "m": m, "r": r})
    if len(items) < 13:
        return {}
    bars = B.bars(items)
    return {id(it["r"]): B.chance(B.BOOM, it["x"], bars[id(it)], it["m"]) for it in items}


def rule_order(players, steps):
    """players ([(row, {key: value})]) in the rule's order."""
    import functools

    def cmp(x, y):
        for key, within in steps + [("projx", 0), ("adp", 0)]:
            a, b = x[1].get(key), y[1].get(key)
            if a is None or b is None or a == b or abs(a - b) <= within:
                continue
            return -1 if a > b else 1
        return 0
    return [p[0] for p in sorted(players, key=functools.cmp_to_key(cmp))]


def pair_pts(order):
    """(sum over every pair of the earlier one's actual minus the later one's, pairs)."""
    a = [r["actual"] for r in order]
    return sum(a[i] - a[j] for i in range(len(a)) for j in range(i + 1, len(a))), len(a) * (len(a) - 1) // 2


@cached
def tier_nights(rows, bar, half):
    """{tier: {"rule"|"adp"|"proj"|"you": (pts, pairs), "off": (your right, pairs), "gap": [actual - proj]}} for one slate."""
    _, tcol, pcol, _ = TIER_HALVES[half]
    you = bar["sources"][0].col
    p = [r for r in pool(rows, bar) if r.get(tcol) is not None and r[pcol] is not None and r[you] is not None]
    if not p:
        return {}
    boom = boom_of(rows, half)
    out = {}
    for t in sorted({int(r[tcol]) for r in p}):
        q = [r for r in p if int(r[tcol]) == t]
        if len(q) < 2 or t not in TIER_RULES[half]:
            continue
        vals = [(r, {"adp": None if r[bar["adp"]] is None else -r[bar["adp"]], "proj": float(int(r[pcol] + 0.5)), "projx": r[pcol],
                     "boom": boom.get(id(r))}) for r in q]
        rule = rule_order(vals, TIER_RULES[half][t][1])
        mine = sorted(q, key=lambda r: r[you])
        orders = {"rule": rule, "adp": rule_order(vals, [("adp", 0)]), "proj": rule_order(vals, [("projx", 0)]), "you": mine}
        pos = {id(r): i for i, r in enumerate(rule)}
        right = n = 0
        for i in range(len(mine)):
            for j in range(i + 1, len(mine)):
                x, y = mine[i], mine[j]
                if pos[id(x)] < pos[id(y)] or x["actual"] == y["actual"]:
                    continue                                  # the rule agrees with you, or nobody was right
                n += 1
                right += x["actual"] > y["actual"]
        out[t] = dict({k: pair_pts(o) for k, o in orders.items()}, off=(right, n), gap=[r["actual"] - r[pcol] for r in q])
    return out


def tier_rule_lines(last, upto):
    """Per half, per tier: the rule against ADP and the projection straight, and your moves off the rule."""
    out = ["## Tier rules", "",
           "Inside each tier at each lock: points per pair (for every pair, the earlier one's actual minus the later one's) for "
           "the rule against ADP and the projection straight, and where you broke the rule, how often you were right. "
           "Each cell: last night · season (80%% range). Verdicts only after %d nights with the tier." % TIER_NIGHTS, ""]
    for half in ("am", "pm"):
        bar, _, _, pname = TIER_HALVES[half]
        per = {x["date"]: tier_nights(x["rows"], bar, half) for x in upto}
        tiers = sorted({t for v in per.values() for t in v})
        if not tiers:
            out += ["**%s**: no tier lines on a Lock %s yet." % ("Morning" if half == "am" else "Afternoon", half.upper()), ""]
            continue
        out += ["**%s (%s)**" % ("Morning" if half == "am" else "Afternoon", pname), "",
                "| Tier | Rule | Nights | Rule vs ADP | Rule vs %s | Your moves off the rule | Actual - %s | Verdict |" % (pname, pname),
                "|---|---|---|---|---|---|---|---|"]
        for t in tiers:
            ds = [d for d in per if t in per[d]]
            lastd = [x["date"] for x in last if x["date"] in ds]

            def diff(ds_, other):
                a = sum(per[d][t]["rule"][0] for d in ds_); n = sum(per[d][t]["rule"][1] for d in ds_)
                b = sum(per[d][t][other][0] for d in ds_)
                return (a - b) / n if n else None

            def off(ds_):
                w = sum(per[d][t]["off"][0] for d in ds_); n = sum(per[d][t]["off"][1] for d in ds_)
                return (w / n if n else None), n

            def cell(other):
                g = boot(ds, lambda xs: diff(xs, other))
                return "%s · %s%s" % (fmt(diff(lastd, other), "%+.1f") if lastd else "-", fmt(diff(ds, other), "%+.1f"), rng(g, "%+.1f"))
            r_last, n_last = off(lastd)
            r_all, n_all = off(ds)
            g_off = boot([d for d in ds if per[d][t]["off"][1]], lambda xs: off(xs)[0])
            ga, gp = boot(ds, lambda xs: diff(xs, "adp")), boot(ds, lambda xs: diff(xs, "proj"))
            if len(ds) < TIER_NIGHTS:
                verdict = "too early (%d of %d)" % (len(ds), TIER_NIGHTS)
            else:
                beats = [nm for nm, g in (("ADP", ga), (pname, gp)) if g and g[1] < 0]
                verdict = ("%s beats the rule" % " and ".join(beats) if beats else
                           "rule holds" if ga and gp and ga[0] > 0 and gp[0] > 0 else "too close to call")
                if g_off and (g_off[0] > 0.5 or g_off[1] < 0.5):
                    verdict += "; your moves %s" % ("win" if g_off[0] > 0.5 else "lose")
            out.append("| T%d | %s | %d | %s | %s | %s · %s | %s | %s |" % (
                t, TIER_RULES[half][t][0], len(ds), cell("adp"), cell("proj"),
                "%s of %d" % (fmt(r_last and 100 * r_last, "%.0f%%"), n_last) if n_last else "-",
                "%s of %d%s" % (fmt(r_all and 100 * r_all, "%.0f%%"), n_all, rng(g_off and (100 * g_off[0], 100 * g_off[1]), "%.0f%%")) if n_all else "-",
                fmt(mean([g for d in ds for g in per[d][t]["gap"]]), "%+.1f"), verdict))
        out.append("")
    if not MIRROR:
        out += ["(No --mirror: Boom left out of the rules that use it.)", ""]
    return out


def player_table(rows, title, cols, key, n):
    head = [c[0] for c in cols]
    out = ["**%s**" % title, "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in sorted(rows, key=key)[:n]:
        out.append("| " + " | ".join(c[1](r) for c in cols) + " |")
    return out + [""]


def pt(iso):
    if not iso:
        return "-"
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
    return t.strftime("%I:%M%p").lstrip("0").lower()


def headlines(last, upto):
    a, p = AM["sources"], PM["sources"]
    return (headline(last, upto, AM, "Morning: your AM board against ours and ADP", [(a[0], a[1]), (a[0], a[2])]) +
            headline(last, upto, PM, "Afternoon: your PM board against ETR, ours and ADP at lock", [(p[0], p[1]), (p[0], p[2]), (p[0], p[3])]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="the slate day to report on (default: the newest on file)")
    ap.add_argument("--mirror", help="a full clone of br-adp-mirror, for Boom in the tier rules")
    a = ap.parse_args()
    global MIRROR
    MIRROR = a.mirror
    slates = load()
    if not slates:
        print("No slates on file in analysis/nba/daily yet.")
        return
    day = a.date or slates[-1]["date"]
    last = [s for s in slates if s["date"] == day]
    upto = [s for s in slates if s["date"] <= day]
    meta = json.load(open(os.path.join(DAILY, "meta.json"))) if os.path.exists(os.path.join(DAILY, "meta.json")) else {}
    out = []
    for s in last:
        m = meta.get(s["file"], {})
        am, pm = m.get("am") or {}, m.get("pm") or {}
        top = [r for r in s["rows"] if (r["adp_close"] or r["adp_am"] or 99) <= DEPTH and r["actual"] is not None]
        sat = [r for r in top if not (r["min"] or 0) > 0]
        early = [r for r in top if (r["min"] or 0) > 0 and gone_early(r)]
        out += ["# NBA morning report: %s %s" % (s["date"], s["slate"].replace("nba_", "")), "",
                "Times PT. Morning: %s %s (ADP from %s)%s. ETR: %s. Afternoon: %s %s%s. Lock %s." % (
                    am.get("from", "no board"), pt(am.get("at")), pt(m.get("adp_am_at")),
                    "" if am.get("ours") else ", our Proj from the morning file",
                    " and ".join(pt(x["at"]) for x in (m.get("etr_first"), m.get("etr_last")) if x) or "none on file",
                    pm.get("from", "no board"), pt(pm.get("at")), "" if pm.get("ours") else ", no ours at PM",
                    pt(m.get("lock"))),
                "Not graded: %s." % (", ".join(["%s (sat)" % r["name"] for r in sat] +
                                               ["%s (left early, %.0f of his usual %.0f min)" % (r["name"], r["min"], r["usual_min"]) for r in early])
                                     or "nobody")]
        ln = LATE.get(s["date"], {})
        if ln.get("am") or ln.get("pm"):
            out.append("Late news, left out of grading: morning %s; afternoon %s.%s" % (
                ", ".join(ln.get("am") or ["none"]), ", ".join(ln.get("pm") or ["none"]), " " + ln["note"] if ln.get("note") else ""))
        out.append("")
    out += ["## Headline: your board against the straight orders (%d slates since %s)" % (len(upto), upto[0]["date"]), ""]
    out += headlines(last, upto) + tier_rule_lines(last, upto) + ours_vs_etr(last, upto)
    out += ["## For the log (misses.csv; not shown in chat)", ""]
    for s in last:
        rows = s["rows"]
        rank_of = lambda col, rs: dict(zip(map(id, rs), ranks([r[col] for r in rs])))      # ties (the ADP 36 pile) share a rank
        am_p = [r for r in pool(rows, AM) if r["am_rank"] is not None and r["adp_am"] is not None]
        ra, rm = rank_of("adp_am", am_p), rank_of("am_rank", am_p)
        out += player_table(am_p, "Your biggest AM calls against ADP", [
            ("Player", lambda r: r["name"]), ("ADP AM", lambda r: fmt(r["adp_am"], "%.1f")), ("ADP rank", lambda r: "%.0f" % ra[id(r)]),
            ("Your rank", lambda r: "%.0f" % rm[id(r)]),
            ("ADP at lock", lambda r: fmt(r["adp_close"], "%.1f")), ("Actual", lambda r: fmt(r["actual"], "%.1f")),
            ("Min (usual)", lambda r: "%s (%s)" % (fmt(r["min"], "%.0f"), fmt(r["usual_min"], "%.0f")))],
            lambda r: -abs(ra[id(r)] - rm[id(r)]), 8)
        pm_p = [r for r in pool(rows, PM) if r["pm_rank"] is not None and r["etr_last"] is not None]
        re_, rp = {id(r): i + 1 for i, r in enumerate(sorted(pm_p, key=lambda r: -r["etr_last"]))}, rank_of("pm_rank", pm_p)
        out += player_table(pm_p, "Your biggest PM calls against ETR", [
            ("Player", lambda r: r["name"]), ("ETR rank", lambda r: "%d" % re_[id(r)]), ("Your rank", lambda r: "%d" % rp[id(r)]),
            ("ADP at lock", lambda r: fmt(r["adp_close"], "%.1f")), ("Actual", lambda r: fmt(r["actual"], "%.1f")),
            ("Min (usual)", lambda r: "%s (%s)" % (fmt(r["min"], "%.0f"), fmt(r["usual_min"], "%.0f")))],
            lambda r: -abs(re_[id(r)] - rp[id(r)]), 8)
        oc = PM["sources"][2].col_for(rows) if any(r["ours_pm"] is not None for r in rows) else AM["sources"][1].col_for(rows)
        both = [r for r in pool(rows, PM) if r[oc] is not None and r["etr_last"] is not None]
        cols = [("Player", lambda r: r["name"]), ("Team", lambda r: r["team"]), ("ADP at lock", lambda r: fmt(r["adp_close"], "%.1f")),
                ("Ours", lambda r: fmt(r[oc], "%.1f")), ("ETR", lambda r: fmt(r["etr_last"], "%.1f")), ("Actual", lambda r: fmt(r["actual"], "%.1f")),
                ("Min (usual)", lambda r: "%s (%s)" % (fmt(r["min"], "%.0f"), fmt(r["usual_min"], "%.0f"))),
                ("Margin", lambda r: fmt(r["margin"], "%+.0f")), ("Tag", lambda r: r["injury"] or "")]
        out += player_table(both, "Biggest projection misses (ours: %s)" % {"ours_pm": "Lock PM", "ours_am": "Lock AM", "ours_raw": "morning file"}[oc],
                            cols, lambda r: -abs(r[oc] - r["actual"]), 8)
        out += player_table(both, "Biggest ours-vs-ETR splits", cols, lambda r: -abs(r[oc] - r["etr_last"]), 6)
    out += movers_line(upto)
    out += ["Ours, ETR and the board are on the board's Proj scale; the morning file is a plain average, put on "
            "ETR's scale by a line fit wherever the two are blended."]
    print("\n".join(out))


if __name__ == "__main__":
    main()
