"""NBA morning report: your board against the straight orders, and your tier rules, for the last
slate and the season.

Reads analysis/nba/daily/*.csv (scripts/nba_daily.py) and prints Markdown, in the order it goes
in chat:

  Headline     every decision pair (ADP within DECISION picks at the window's lock) your board and a
               straight order (ours, ETR, ADP) disagree on: how often yours was right; and, where
               exactly one of the pair was a breaker (90th percentile of his ADP round band), how
               often yours took him. Morning: your AM board against ours and ADP at Lock AM only;
               afternoon: your PM board against ETR, ours and ADP at lock only. Each window is graded
               only on what was known in it. Over 50% and settled: your moves beat it.
  Tier rules   inside each of your tiers (the board's tier lines at each lock), the rule written
               beside it on the board, against ADP and the half's projection straight, and whether
               your own moves off the rule paid. A verdict only after TIER_NIGHTS nights.
  Ours vs ETR  how our number at Lock PM tracks ETR's last upload (the same window).
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
import argparse, csv, datetime as dt, glob, json, math, os, random
from zoneinfo import ZoneInfo

DAILY = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "daily")
LATE_FILE = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "report", "late_news.json")
LATE = json.load(open(LATE_FILE)) if os.path.exists(LATE_FILE) else {}   # {date: {"am": [teams], "pm": [teams], "note": ...}}
DEPTH, GAP = 48, 3
DECISION = 4         # picks: two players whose ADP at the window's lock is this close are a decision pair
# Left early: a player who usually plays EARLY_USUAL+ minutes and got under half of them in a game
# decided by less than EARLY_MARGIN. A starter cut that short in a close game is almost always hurt;
# a bench player's short night is usually the rotation, which is worth learning from, so he stays.
EARLY_USUAL, EARLY_MARGIN = 25, 15
TEXT = ("date", "slate", "player_id", "name", "team", "pos", "injury", "injury_am", "opp", "fg", "fg3", "ft", "mtch_label", "mtch_cats")


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


def is_decision(x, y, bar):
    """A decision pair: ADP at the window's lock within DECISION picks. Only these are graded."""
    return abs(x[bar["adp"]] - y[bar["adp"]]) <= DECISION


@cached
def breakers(rows, bar):
    """ids of the night's breakers: FP at or above the 90th percentile (nearest rank) of the graded players in
    his ADP round band (by the window's ADP: picks 1-6, 7-12, ... on a 6-drafter slate, 1-4, 5-8, ... on a
    4-drafter one; everyone past the last round is one band)."""
    p = sorted(pool(rows, bar), key=lambda r: r[bar["adp"]])
    pod = pod_size(rows)
    band = {}
    for i, r in enumerate(p):
        band.setdefault(min(i // pod, 6), []).append(r)
    out = set()
    for rs in band.values():
        a = sorted(r["actual"] for r in rs)
        out |= {id(r) for r in rs if r["actual"] >= a[math.ceil(0.9 * len(a)) - 1]}
    return out


def pod_size(rows):
    """Drafters per pod: 4 on the 24-pick small slates, else 6."""
    return 4 if max((r["adp_close"] or r["adp_am"] or 0) for r in rows) <= 28 else 6


@cached
def calls(rows, bar, a, b, cut="decision"):
    """Pairs a and b order differently: (a right, b right). cut: "decision" (ADP within DECISION), "all", or
    "breaker" (decision pairs where exactly one broke; right = took the breaker)."""
    ka, kb = a.key(rows), b.key(rows)
    p = [r for r in pool(rows, bar) if ka(r) is not None and kb(r) is not None]
    brk = breakers(rows, bar) if cut == "breaker" else None
    win = lose = 0
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            x, y = p[i], p[j]
            da, db = ka(x) - ka(y), kb(x) - kb(y)
            if da * db >= 0 or x["actual"] == y["actual"]:
                continue
            if cut != "all" and not is_decision(x, y, bar):
                continue
            if brk is not None:
                if (id(x) in brk) == (id(y) in brk):
                    continue
                x_won = id(x) in brk
            else:
                x_won = x["actual"] > y["actual"]
            if (da > 0) == x_won:
                win += 1
            else:
                lose += 1
    return win, lose


# ---------------------------------------------------------------- over slates
def boot(slates, fn, level=0.8):
    """The `level` range (80% unless asked) of fn over resampled slates, or None with fewer than 3."""
    if len(slates) < 3:
        return None
    rnd = random.Random(7)
    vals = sorted(v for v in (fn([rnd.choice(slates) for _ in slates]) for _ in range(500)) if v is not None)
    tail = int(len(vals) * (1 - level) / 2)
    return (vals[tail], vals[len(vals) - 1 - tail]) if vals else None


def rng(r, spec):
    return "" if not r else " (%s to %s)" % (spec % r[0], spec % r[1])


def fmt(v, spec="%.2f"):
    return "-" if v is None else spec % v


def call_rate(slates, bar, a, b, cut="decision"):
    w = l = 0
    for x in slates:
        ww, ll = calls(x["rows"], bar, a, b, cut)
        w, l = w + ww, l + ll
    return (w / (w + l) if w + l else None), w + l


def headline(last, upto, bar, title, h2h):
    """Your board head to head against each straight order on decision pairs: last night, the season, a verdict;
    then on breakers (where exactly one of the pair broke), and on every pair, the old cut, for comparison."""
    out = ["### " + title, "",
           "| Your board against | Last night | Season | Range | So far | Breakers: you took the breaker | All pairs (old cut) |",
           "|---|---|---|---|---|---|---|"]
    pct = lambda r: "%.0f%%" % (100 * r) if r is not None else "-"
    for a, b in h2h:
        r1, n1 = call_rate(last, bar, a, b)
        r2, n2 = call_rate(upto, bar, a, b)
        rg = boot([x for x in upto if sum(calls(x["rows"], bar, a, b))], lambda xs: call_rate(xs, bar, a, b)[0])
        verdict = ("not enough slates" if not rg else "your board wins" if rg[0] > 0.5
                   else "%s alone wins" % b.label if rg[1] < 0.5 else "too close to call")
        rb, nb = call_rate(upto, bar, a, b, "breaker")
        gb = boot([x for x in upto if sum(calls(x["rows"], bar, a, b, "breaker"))], lambda xs: call_rate(xs, bar, a, b, "breaker")[0])
        ra, na = call_rate(upto, bar, a, b, "all")
        out.append("| %s | %s | %s of %d pairs | %s | %s | %s of %d%s | %s of %d |" % (
            b.label, pct(r1), pct(r2), n2, "%.0f-%.0f%%" % (100 * rg[0], 100 * rg[1]) if rg else "-", verdict if r2 is not None else "-",
            pct(rb), nb, " (%.0f-%.0f%%)" % (100 * gb[0], 100 * gb[1]) if gb else "", pct(ra), na))
    return out + [""]


ETRB = {"adp": "adp_close", "half": "pm", "sources": [Src("ours_pm", "Ours at Lock PM", True), Src("etr_last", "ETR last", True)]}


def ours_vs_etr(last, upto):
    """How our number tracks ETR's in the same window (both at Lock PM): order, gap, and who was closer to the actual."""
    def players(xs_):
        out = []
        for x in xs_:
            rs = [r for r in pool(x["rows"], ETRB) if r["ours_pm"] is not None and r["etr_last"] is not None]
            if not rs:
                continue
            ps = [(r["ours_pm"], None, r["etr_last"], r["actual"]) for r in rs]
            # each relative to its slate average, so a slate-wide shift (ETR running high, or moving the whole slate) isn't agreement or a miss
            avg = [mean([p[i] for p in ps]) for i in range(4)]
            out.append([tuple(None if p[i] is None else p[i] - avg[i] for i in range(4)) for p in ps])
        return out

    def cell(xs_, f, spec):
        return fmt(f(players(xs_)), spec)

    def both(f, spec):
        return "%s (%s)" % (cell(last, f, spec), cell(upto, f, spec))

    flat = lambda gs: [p for g in gs for p in g]
    rho = lambda i: lambda gs: mean([corr(ranks([p[0] for p in g]), ranks([p[i] for p in g])) for g in gs if len(g) >= 5])
    near = lambda i: lambda gs: (lambda f: 100 * sum(abs(p[0] - p[i]) < GAP for p in f) / len(f) if f else None)(flat(gs))
    closer = lambda i: lambda gs: (lambda f: 100 * sum(abs(p[0] - p[3]) < abs(p[i] - p[3]) for p in f) / len(f) if f else None)(
        [p for p in flat(gs) if abs(p[0] - p[i]) >= GAP])
    miss = lambda i: lambda gs: mean([abs(p[i] - p[3]) for p in flat(gs)])
    return ["### Ours vs ETR", "",
            "Our Proj at Lock PM against ETR's last upload, the same window, player by player (each taken against its slate's "
            "average). Last night (season): rank corr %s; within %d pts %s; where %d+ apart ours was closer to the actual %s; "
            "average miss ours %s, ETR %s." % (
                both(rho(2), "%.2f"), GAP, both(near(2), "%.0f%%"), GAP, both(closer(2), "%.0f%%"), both(miss(0), "%.1f"),
                both(miss(2), "%.1f")), ""]


def tag_line(upto):
    """How often a drafted player sat, by his Underdog tag when the AM board locked (season): the miss chance
    behind how far to push a tagged player back in the morning."""
    c = {}
    for x in upto:
        for r in x["rows"]:
            if r["adp_am"] is None or "injury_am" not in r:
                continue
            k = r["injury_am"] or "no tag"
            n, d = c.get(k, (0, 0))
            c[k] = (n + 1, d + (not (r["min"] or 0) > 0))
    if not c:
        return []
    return ["Sat, by tag at Lock AM (season, drafted players): " + "; ".join(
        "%s %d of %d (%.0f%%)" % (k, d, n, 100 * d / n) for k, (n, d) in sorted(c.items(), key=lambda kv: -kv[1][0])) + ".", ""]


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
MIN_PAIRS = 30       # and pairs a comparison needs (with fewer the resampled ranges collapse). Set 2026-11-02, likewise.
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


def pair_pts(order, bar):
    """(sum over every decision pair of the earlier one's actual minus the later one's, pairs)."""
    tot = n = 0
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            if is_decision(order[i], order[j], bar):
                tot += order[i]["actual"] - order[j]["actual"]
                n += 1
    return tot, n


@cached
def tier_nights(rows, bar, half):
    """{tier: {"pairs": [(name x, name y, rule - ADP, rule - proj)], "off": [(name x, name y, you right)],
    "gap": [actual - proj]}} for one slate, decision pairs only. A pair's value under an order is the actual
    of the one it puts first minus the other's, so rule - ADP is what following the rule gained over ADP."""
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
        vals = [(r, {"adp": -r[bar["adp"]], "proj": float(int(r[pcol] + 0.5)), "projx": r[pcol], "boom": boom.get(id(r))}) for r in q]
        pos = {k: {id(r): i for i, r in enumerate(o)} for k, o in (
            ("rule", rule_order(vals, TIER_RULES[half][t][1])), ("adp", rule_order(vals, [("adp", 0)])),
            ("proj", rule_order(vals, [("projx", 0)])), ("you", sorted(q, key=lambda r: r[you])))}
        pairs, off = [], []
        for i in range(len(q)):
            for j in range(i + 1, len(q)):
                x, y = q[i], q[j]
                if not is_decision(x, y, bar) or x["actual"] == y["actual"]:
                    continue
                g = {k: (x["actual"] - y["actual"]) * (1 if ps[id(x)] < ps[id(y)] else -1) for k, ps in pos.items()}
                pairs.append((x["name"], y["name"], g["rule"] - g["adp"], g["rule"] - g["proj"]))
                if (pos["you"][id(x)] < pos["you"][id(y)]) != (pos["rule"][id(x)] < pos["rule"][id(y)]):
                    off.append((x["name"], y["name"], g["you"] > 0))       # you broke the rule on this pair
        out[t] = {"pairs": pairs, "off": off, "gap": [r["actual"] - r[pcol] for r in q]}
    return out


def tier_stats(upto, half):
    """Per tier: nights, and per comparison ("adp", "proj", "off") the season value, 80% and 90% ranges and the
    drop-one-player range (the value with each single player's pairs taken out)."""
    bar = TIER_HALVES[half][0]
    per = {x["date"]: tier_nights(x["rows"], bar, half) for x in upto}
    out = {}
    for t in sorted({t for v in per.values() for t in v}):
        ds = [d for d in per if t in per[d]]
        for key, k, f in (("adp", 2, None), ("proj", 3, None), ("off", 2, "off")):
            src = "off" if f else "pairs"
            val = lambda xs, drop=None: mean([pr[k] for d in xs for pr in per[d][t][src] if drop not in pr[:2]])
            names = {n for d in ds for pr in per[d][t][src] for n in pr[:2]}
            v = val(ds)
            out.setdefault(t, {"nights": ds, "per": per})[key] = {
                "v": v, "r80": boot(ds, val), "r90": boot(ds, val, 0.9),
                "drop": (min(val(ds, n) for n in names), max(val(ds, n) for n in names)) if names and v is not None else None,
                "same": key != "off" and all(pr[k] == 0 for d in ds for pr in per[d][t][src]), "n": sum(len(per[d][t][src]) for d in ds)}
    return out


def tier_verdict(st, t, key, other_half, mid):
    """"holds" / "loses" / None for one comparison, by the adoption bar: a 90% range clear of `mid`, or an 80% range
    clear of it with the same direction in the other window or in 3+ tiers of this one; and no single player's pairs
    able to flip it."""
    c = st[t][key]
    if c["same"] or c["v"] is None or not c["r80"] or c["n"] < MIN_PAIRS:
        return None
    for sign, word in ((1, "holds"), (-1, "loses")):
        clear = lambda g: g and (g[0] - mid if sign > 0 else mid - g[1]) > 0
        backed = clear(other_half.get(t, {}).get(key, {}).get("r80")) or sum(clear(st[u][key]["r80"]) for u in st if key in st[u]) >= 3
        if clear(c["r90"]) or (clear(c["r80"]) and backed):
            return word if c["drop"] and (c["drop"][0] - mid if sign > 0 else mid - c["drop"][1]) > 0 else "hangs on one player"
    return None


def tier_rule_lines(last, upto):
    """Per half, per tier: the rule against ADP and the projection straight, and your moves off the rule."""
    out = ["## Tier rules", "",
           "Inside each tier at each lock, decision pairs only (ADP within %d picks): what following the rule gained per pair over "
           "ADP and over the projection straight (a pair's value: the actual of the one an order puts first minus the other's), "
           "and where you broke the rule, how often you were right. Each cell: last night · season (80%% range). A verdict "
           "needs %d nights and %d pairs, then a 90%% range clear of 0 (or 80%% backed by the other window or 3+ "
           "tiers), and no single player able to flip it." % (DECISION, TIER_NIGHTS, MIN_PAIRS), ""]
    stats = {h: tier_stats(upto, h) for h in ("am", "pm")}
    for half in ("am", "pm"):
        pname = TIER_HALVES[half][3]
        st, other = stats[half], stats["pm" if half == "am" else "am"]
        if not st:
            out += ["**%s**: no tier lines on a Lock %s yet." % ("Morning" if half == "am" else "Afternoon", half.upper()), ""]
            continue
        out += ["**%s (%s)**" % ("Morning" if half == "am" else "Afternoon", pname), "",
                "| Tier | Rule | Nights | Rule vs ADP | Rule vs %s | Your moves off the rule | Actual - %s | Verdict |" % (pname, pname),
                "|---|---|---|---|---|---|---|---|"]
        for t in st:
            ds, per = st[t]["nights"], st[t]["per"]
            lastd = [x["date"] for x in last if x["date"] in ds]

            def cell(key, k, scale=1, spec="%+.1f"):
                c = st[t][key]
                if c["same"]:
                    return "same order"
                lv = mean([pr[k] for d in lastd for pr in per[d][t]["off" if key == "off" else "pairs"]])
                rg = c["r80"] and (scale * c["r80"][0], scale * c["r80"][1])
                return "%s · %s%s%s" % (fmt(lv and scale * lv, spec) if lv is not None else "-", fmt(c["v"] and scale * c["v"], spec),
                                        rng(rg, spec), " of %d" % c["n"] if key == "off" else "")
            if len(ds) < TIER_NIGHTS:
                verdict = "too early (%d of %d)" % (len(ds), TIER_NIGHTS)
            else:
                vs = {nm: tier_verdict(st, t, key, other, 0) for nm, key in (("ADP", "adp"), (pname, "proj"))}
                vs = {nm: v for nm, v in vs.items() if not st[t]["adp" if nm == "ADP" else "proj"]["same"]}
                lost = [nm for nm, v in vs.items() if v == "loses"]
                verdict = ("%s beats the rule" % " and ".join(lost) if lost else "rule holds" if vs and all(v == "holds" for v in vs.values())
                           else "hangs on one player" if "hangs on one player" in vs.values() else "too close to call")
                mv = tier_verdict(st, t, "off", other, 0.5)
                if mv in ("holds", "loses"):
                    verdict += "; your moves %s" % ("win" if mv == "holds" else "lose")
            out.append("| T%d | %s | %d | %s | %s | %s | %s | %s |" % (
                t, TIER_RULES[half][t][0], len(ds), cell("adp", 2), cell("proj", 3), cell("off", 2, 100, "%.0f%%"),
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
    out += headlines(last, upto) + tier_rule_lines(last, upto) + ours_vs_etr(last, upto) + tag_line(upto)
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
