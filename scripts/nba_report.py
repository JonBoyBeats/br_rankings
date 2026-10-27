"""NBA morning report: the morning and afternoon barbells, for the last slate and all of them.

Reads analysis/nba/daily/*.csv (scripts/nba_daily.py) and prints Markdown.

  Morning    your AM ranks and our Proj at Lock AM, against ADP at that moment
  Afternoon  your PM ranks, ETR's last upload and our Proj at Lock PM, against ADP at lock

Each barbell scores the night's top 48 by its ADP plus anyone a source put in its top 48 (a
player who sat counts as 0, as he does in a draft):

  rank corr   how well the source's order matched what they scored
  top 12      how many of its top 12 finished top 12
  round picks its 2 favourites in each ADP round (the Live page's groups) against the round's
              average, in points; rounds 5-6 apart, where finding the best late picks pays
  CLV         size-weighted: how far a source sat from ADP against how far ADP then moved (a
              correlation; 0 is no signal), and picks moved its way on players 3+ spots off
  calls       every pair two orders disagree on: how often each side was right

Over several slates a difference carries an 80% range from resampling the slates; a range
that spans 0 isn't settled yet.

  python3 scripts/nba_report.py [--date YYYY-MM-DD]
"""
import argparse, csv, datetime as dt, glob, json, os, random
from zoneinfo import ZoneInfo

DAILY = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "daily")
DEPTH, TOP, GAP = 48, 12, 3
ROUNDS = [(1, 7), (6, 13), (12, 20), (17, 26), (23, 32), (29, 40)]   # ADP ranks per round, as on the Live page
TEXT = ("date", "slate", "player_id", "name", "team", "pos", "injury")


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


AM = {"adp": "adp_am", "sources": [Src("am_rank", "Your AM ranks", False), Src("ours_am", "Ours at Lock AM", True, "ours_raw"),
                                   Src("adp_am", "ADP at Lock AM", False)]}
PM = {"adp": "adp_close", "sources": [Src("pm_rank", "Your PM ranks", False), Src("etr_last", "ETR last upload", True),
                                      Src("ours_pm", "Ours at Lock PM", True), Src("adp_close", "ADP at lock", False)]}


def pool(rows, bar):
    """The barbell's top DEPTH by its ADP, plus each source's top DEPTH; with an ADP and a result."""
    have = [r for r in rows if r[bar["adp"]] is not None and r["actual"] is not None]
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
def results(rows, bar, src):
    """Rank corr, top-12 hits, round picks (all rounds, 5-6) for one source on one slate."""
    p = pool(rows, bar)
    k = src.key(rows)
    have = [r for r in p if k(r) is not None]
    if len(have) < 5:
        return None
    rho = corr(ranks([k(r) for r in have]), ranks([r["actual"] for r in have]))
    best = set(id(r) for r in sorted(p, key=lambda r: -r["actual"])[:TOP])
    hit = sum(id(r) in best for r in sorted(have, key=lambda r: -k(r))[:TOP])
    by_adp = sorted(p, key=lambda r: r[bar["adp"]])
    picks = []
    for lo, hi in ROUNDS:
        band = [r for r in by_adp[lo - 1:hi] if k(r) is not None]
        if len(band) >= 3:
            fav = sorted(band, key=lambda r: -k(r))[:2]
            picks.append(mean([r["actual"] for r in fav]) - mean([r["actual"] for r in band]))
        else:
            picks.append(None)
    return {"rho": rho, "hit": hit, "of": min(TOP, len(have)), "picks": picks}


@cached
def clv_pairs(rows, bar, src, frm):
    """(how far the source sat ahead of ADP at `frm`, in ranks; picks ADP moved earlier by lock)."""
    k = src.key(rows)
    p = [r for r in pool(rows, bar) if r[frm] is not None and r["adp_close"] is not None and k(r) is not None]
    if len(p) < 5:
        return []
    mine, adp = ranks([-k(r) for r in p]), ranks([r[frm] for r in p])
    return [(a - m, r[frm] - r["adp_close"]) for r, m, a in zip(p, mine, adp)]


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


def results_table(slates, bar):
    base = bar["sources"][-1]
    out = ["| Source | Rank corr | vs %s | Top-12 hits | Round picks | Rounds 5-6 |" % base.label, "|---|---|---|---|---|---|"]
    for s in bar["sources"]:
        got = [results(x["rows"], bar, s) for x in slates]
        if not any(got):
            out.append("| %s | - | - | - | - | - |" % s.label)
            continue

        def rho_of(xs):
            return mean([(results(x["rows"], bar, s) or {}).get("rho") for x in xs])

        def diff_of(xs):
            ds = []
            for x in xs:
                a, b = results(x["rows"], bar, s), results(x["rows"], bar, base)
                if a and b and a["rho"] is not None and b["rho"] is not None:
                    ds.append(a["rho"] - b["rho"])
            return mean(ds)
        g = [x for x in got if x]
        all_r = mean([mean(x["picks"]) for x in g])
        late = mean([mean(x["picks"][4:]) for x in g])
        d = None if s is base else diff_of(slates)
        out.append("| %s | %s | %s | %d of %d | %s | %s |" % (
            s.label, fmt(rho_of(slates)), "-" if s is base else fmt(d, "%+.2f") + rng(boot(slates, diff_of), "%+.2f"),
            sum(x["hit"] for x in g), sum(x["of"] for x in g), fmt(all_r, "%+.1f"), fmt(late, "%+.1f")))
    return out


def clv_table(slates, rows_of):
    out = ["| Source | From | Signal (corr) | Picks moved its way, 3+ spots off |", "|---|---|---|---|"]
    for bar, s, frm, when in rows_of:
        def sig(xs):
            pairs = [q for x in xs for q in clv_pairs(x["rows"], bar, s, frm)]
            return corr([g for g, _ in pairs], [m for _, m in pairs]) if len(pairs) >= 5 else None
        pairs = [q for x in slates for q in clv_pairs(x["rows"], bar, s, frm)]
        far = [(1 if g > 0 else -1) * m for g, m in pairs if abs(g) >= GAP]
        out.append("| %s | %s | %s%s | %s |" % (s.label, when, fmt(sig(slates), "%+.2f"), rng(boot(slates, sig), "%+.2f"),
                                              "%+.2f on %d players" % (mean(far), len(far)) if far else "-"))
    return out


def calls_table(slates, bar, pairs):
    out = ["| Disagreement | Pairs | First side right | Range |", "|---|---|---|---|"]
    for a, b in pairs:
        def rate(xs):
            w = l = 0
            for x in xs:
                ww, ll = calls(x["rows"], bar, a, b)
                w, l = w + ww, l + ll
            return w / (w + l) if w + l else None
        w = l = 0
        for x in slates:
            ww, ll = calls(x["rows"], bar, a, b)
            w, l = w + ww, l + ll
        out.append("| %s vs %s | %d | %s | %s |" % (a.label, b.label, w + l, "%.0f%%" % (100 * w / (w + l)) if w + l else "-",
                                                rng(boot(slates, rate), "%.2f").strip(" ()") or "-"))
    return out


def blend_lines(slates):
    out = []
    for col, name in (("ours_pm", "Ours at Lock PM"), ("ours_raw", "Ours (morning file)")):
        groups = []
        for x in slates:
            rs = [r for r in pool(x["rows"], PM) if r[col] is not None and r["etr_last"] is not None]
            if len(rs) >= 5:
                groups.append(rs)
        flat = [r for g in groups for r in g]
        if len(flat) < 10:
            out.append("- %s with ETR: not enough players with both yet." % name)
            continue
        xs, ys = [r[col] for r in flat], [r["etr_last"] for r in flat]
        mx, my = mean(xs), mean(ys)
        sxx = sum((v - mx) ** 2 for v in xs)
        a = sum((v - mx) * (u - my) for v, u in zip(xs, ys)) / sxx if sxx else 1
        trip = [[(a * r[col] + my - a * mx, r["etr_last"], r["actual"]) for r in g] for g in groups]   # ours on ETR's scale

        def best(gs):
            f = [t for g in gs for t in g]
            mae = {w: mean([abs(w / 10 * o + (1 - w / 10) * e - y) for o, e, y in f]) for w in range(11)}
            return min(mae, key=mae.get) / 10, mae
        w, mae = best(trip)
        r = None
        if len(trip) >= 3:
            rnd = random.Random(7)
            ws = sorted(best([rnd.choice(trip) for _ in trip])[0] for _ in range(200))
            r = (ws[20], ws[179])
        out.append("- %s with ETR's last upload, %d players: least miss at **%d%% ours** (%.2f), against %.2f all ETR%s." % (
            name, len(flat), round(w * 100), mae[round(w * 10)], mae[0],
            "; 80%% range %d-%d%%" % (round(r[0] * 100), round(r[1] * 100)) if r else ""))
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


def barbells(slates):
    out = ["### Morning", ""] + results_table(slates, AM) + [""]
    out += clv_table(slates, [(AM, AM["sources"][0], "adp_am", "Lock AM"), (AM, AM["sources"][1], "adp_am", "Lock AM")]) + [""]
    out += calls_table(slates, AM, [(AM["sources"][0], AM["sources"][2]), (AM["sources"][0], AM["sources"][1])]) + [""]
    out += ["### Afternoon", ""] + results_table(slates, PM) + [""]
    out += clv_table(slates, [(PM, Src("etr_first", "ETR first upload", True), "adp_etr", "its upload")]) + [""]
    p = PM["sources"]
    out += calls_table(slates, PM, [(p[0], p[1]), (p[0], p[3]), (p[2], p[1])]) + [""]
    return out + blend_lines(slates) + [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="the slate day to report on (default: the newest on file)")
    a = ap.parse_args()
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
        sat = [r for r in pool(s["rows"], PM) if r["min"] == 0]
        out += ["# NBA morning report: %s %s" % (s["date"], s["slate"].replace("nba_", "")), "",
                "Times PT. Morning: %s %s (ADP from %s)%s. ETR: %s. Afternoon: %s %s%s. Lock %s." % (
                    am.get("from", "no board"), pt(am.get("at")), pt(m.get("adp_am_at")),
                    "" if am.get("ours") else ", our Proj from the morning file",
                    " and ".join(pt(x["at"]) for x in (m.get("etr_first"), m.get("etr_last")) if x) or "none on file",
                    pm.get("from", "no board"), pt(pm.get("at")), "" if pm.get("ours") else ", no ours at PM",
                    pt(m.get("lock"))),
                "Sat (scored 0): %s." % (", ".join("%s (ADP %.0f)" % (r["name"], r["adp_close"]) for r in sat) or "nobody"), ""]
    out += ["## Last night", ""] + barbells(last)
    for s in last:
        rows = s["rows"]
        rank_of = lambda col, rs: {id(r): i + 1 for i, r in enumerate(sorted((r for r in rs if r[col] is not None), key=lambda r: r[col]))}
        am_p = [r for r in pool(rows, AM) if r["am_rank"] is not None and r["adp_am"] is not None]
        ra, rm = rank_of("adp_am", am_p), rank_of("am_rank", am_p)
        out += player_table(am_p, "Your biggest AM calls against ADP", [
            ("Player", lambda r: r["name"]), ("ADP AM", lambda r: fmt(r["adp_am"], "%.1f")), ("Your rank", lambda r: "%d" % rm[id(r)]),
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
        out += player_table(both, "Biggest projection misses (ours, %s)" % oc, cols, lambda r: -abs(r[oc] - r["actual"]), 8)
        out += player_table(both, "Biggest ours-vs-ETR splits", cols, lambda r: -abs(r[oc] - r["etr_last"]), 6)
    out += ["## Since %s: %d slates" % (upto[0]["date"], len(upto)), ""] + barbells(upto)
    out += ["**By slate** (rank corr)", "", "| Slate | AM you | AM ADP | PM you | PM ETR | PM ADP |", "|---|---|---|---|---|---|"]
    for s in upto:
        f = lambda bar, i: fmt((results(s["rows"], bar, bar["sources"][i]) or {}).get("rho"))
        out.append("| %s %s | %s | %s | %s | %s | %s |" % (s["date"], s["slate"].replace("nba_", ""), f(AM, 0), f(AM, 2), f(PM, 0), f(PM, 1), f(PM, 3)))
    out += ["", "Ours, ETR and the board are on the board's Proj scale; the morning file is a plain average, put on "
            "ETR's scale by a line fit wherever the two are blended."]
    print("\n".join(out))


if __name__ == "__main__":
    main()
