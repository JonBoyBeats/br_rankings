"""NBA morning report: the scores of every source for the last slate and for all of them.

Reads analysis/nba/daily/*.csv (scripts/nba_daily.py) and prints Markdown:

  accuracy   among the night's top 48 (by ADP at lock, or by any source) who played: rank correlation with what they scored,
             how many of the source's top 12 finished top 12, and for projections the average
             miss and bias (projection minus actual)
  CLV        players a source ranked 3+ spots ahead of (or behind) the 5am ADP: how often the
             ADP moved their way by lock, and by how many picks on average
  blend      the mix of ours and ETR's last upload that missed by least, with an 80% range
             from resampling the slates
  misses     last slate's biggest misses and biggest ours-vs-ETR splits, for the write-up

  python3 scripts/nba_report.py [--date YYYY-MM-DD]
"""
import argparse, csv, datetime as dt, glob, json, os, random
from zoneinfo import ZoneInfo

DAILY = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "daily")
TOP, GAP, MOVED = 12, 3, 0.5
# Scored each night: the top DEPTH by ADP at lock, plus anyone a source put in its top DEPTH.
# About what gets drafted (36) and ranked (44-48); the bench players below don't matter.
DEPTH = 48
SOURCES = [   # column, label, higher is better, a projection in points
    ("ours", "Ours (board)", True, True),
    ("ours_raw", "Ours (morning file)", True, True),
    ("etr_first", "ETR first upload", True, True),
    ("etr_last", "ETR last upload", True, True),
    ("adp_am", "ADP 5am", False, False),
    ("adp_close", "ADP at lock", False, False),
    ("final_rank", "Your final ranks", False, False),
]
CLV_SOURCES = [s for s in SOURCES if s[0] not in ("adp_am", "adp_close")]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load():
    slates = []
    for path in sorted(glob.glob(os.path.join(DAILY, "*.csv"))):
        rows = list(csv.DictReader(open(path)))
        for r in rows:
            for k in r:
                if k not in ("date", "slate", "player_id", "name", "team", "pos", "injury"):
                    r[k] = num(r[k])
        if rows:
            slates.append({"file": os.path.basename(path), "date": rows[0]["date"], "slate": rows[0]["slate"], "rows": rows})
    return slates


def scored(rows):
    """Players priced at lock in the top DEPTH by ADP at lock or by any source."""
    priced = [r for r in rows if r["adp_close"] is not None]
    keep = set()
    for col, _, higher, _ in SOURCES:
        have = [r for r in priced if r[col] is not None]
        keep.update(id(r) for r in sorted(have, key=lambda r: -r[col] if higher else r[col])[:DEPTH])
    return [r for r in priced if id(r) in keep]


def played(rows):
    return [r for r in scored(rows) if r["actual"] is not None and (r["min"] or 0) > 0]


def ranks(vals):
    """Average ranks, 1 = smallest."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out = [0.0] * len(vals)
    i = 0
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


def accuracy(rows, col, higher):
    pool = played(rows)
    have = [r for r in pool if r[col] is not None]
    if len(have) < 3:
        return None
    score = [r[col] if higher else -r[col] for r in have]
    rho = corr(ranks(score), ranks([r["actual"] for r in have]))
    best = set(id(r) for r in sorted(pool, key=lambda r: -r["actual"])[:TOP])
    picked = sorted(have, key=lambda r: -(r[col] if higher else -r[col]))[:TOP]
    errs = [r[col] - r["actual"] for r in have]
    return {"n": len(have), "rho": rho, "hit": sum(id(r) in best for r in picked), "of": len(picked),
            "mae": sum(abs(e) for e in errs) / len(errs), "bias": sum(errs) / len(errs)}


def clv(rows, col, higher):
    """[(gap direction, ADP move toward earlier)] for players the source ranked GAP+ spots off the 5am ADP."""
    pool = [r for r in scored(rows) if r["adp_am"] is not None and r[col] is not None]
    if len(pool) < 3:
        return []
    src = ranks([-r[col] if higher else r[col] for r in pool])
    adp = ranks([r["adp_am"] for r in pool])
    return [(1 if a - s > 0 else -1, r["adp_am"] - r["adp_close"])
            for r, s, a in zip(pool, src, adp) if abs(a - s) >= GAP]


def clv_line(flags):
    if not flags:
        return None
    hit = sum(1 for d, m in flags if d * m >= MOVED)
    miss = sum(1 for d, m in flags if d * m <= -MOVED)
    return {"n": len(flags), "hit": hit, "miss": miss, "toward": sum(d * m for d, m in flags) / len(flags)}


def blend_rows(slates, ours_col):
    """(ours on ETR's scale, ETR last, actual) by slate. A morning-file number is put on ETR's scale by a line fit."""
    out = []
    for s in slates:
        rows = [r for r in played(s["rows"]) if r[ours_col] is not None and r["etr_last"] is not None]
        if len(rows) >= 5:
            out.append(rows)
    flat = [r for rows in out for r in rows]
    if len(flat) < 10:
        return None
    xs, ys = [r[ours_col] for r in flat], [r["etr_last"] for r in flat]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 1
    b = my - a * mx
    return [[(a * r[ours_col] + b, r["etr_last"], r["actual"]) for r in rows] for rows in out]


def best_w(groups):
    flat = [t for g in groups for t in g]
    mae = {w: sum(abs(w / 10 * o + (1 - w / 10) * e - y) for o, e, y in flat) / len(flat) for w in range(11)}
    return min(mae, key=mae.get) / 10, mae


def pt(iso):
    """'4:24am' Pacific, or '-'."""
    if not iso:
        return "-"
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles"))
    return t.strftime("%I:%M%p").lstrip("0").lower()


def fmt(v, spec="%.2f"):
    return "-" if v is None else spec % v


def acc_table(slate_groups):
    out = ["| Source | Players | Rank corr | Top-%d hits | Avg miss | Bias |" % TOP, "|---|---|---|---|---|---|"]
    for col, label, higher, pts in SOURCES:
        got = [accuracy(rows, col, higher) for rows in slate_groups]
        got = [g for g in got if g]
        if not got:
            out.append("| %s | - | - | - | - | - |" % label)
            continue
        n = sum(g["n"] for g in got)
        rho = [g["rho"] for g in got if g["rho"] is not None]
        mae = sum(g["mae"] * g["n"] for g in got) / n
        bias = sum(g["bias"] * g["n"] for g in got) / n
        out.append("| %s | %d | %s | %d of %d | %s | %s |" % (
            label, n, fmt(sum(rho) / len(rho) if rho else None), sum(g["hit"] for g in got), sum(g["of"] for g in got),
            fmt(mae, "%.1f") if pts else "-", fmt(bias, "%+.1f") if pts else "-"))
    return out + ["", "The morning file is a plain average; ours (board) and ETR are on the board's scale, nudged toward "
                  "ceiling. Compare the morning file by rank corr and top-12, not by its miss or bias."]


def clv_table(slate_groups):
    out = ["| Source | Players %d+ spots off 5am ADP | ADP moved their way | Moved against | Avg picks toward |" % GAP,
           "|---|---|---|---|---|"]
    for col, label, higher, _ in CLV_SOURCES:
        c = clv_line([f for rows in slate_groups for f in clv(rows, col, higher)])
        if not c:
            out.append("| %s | - | - | - | - |" % label)
            continue
        out.append("| %s | %d | %d (%.0f%%) | %d | %+.2f |" % (label, c["n"], c["hit"], 100 * c["hit"] / c["n"], c["miss"], c["toward"]))
    return out


def blend_section(slates, label):
    out = []
    for col, name in (("ours", "Ours (board)"), ("ours_raw", "Ours (morning file)")):
        groups = blend_rows(slates, col)
        if not groups:
            out.append("- %s and ETR: not enough players with both yet." % name)
            continue
        w, mae = best_w(groups)
        line = "- %s and ETR's last upload, %d players: least miss at **%d%% ours** (%.2f), against %.2f all ETR and %.2f all ours" % (
            name, sum(len(g) for g in groups), round(w * 100), mae[round(w * 10)], mae[0], mae[10])
        if len(groups) >= 3:
            rnd = random.Random(7)
            ws = sorted(best_w([rnd.choice(groups) for _ in groups])[0] for _ in range(200))
            line += "; 80%% range over resampled slates %d-%d%%" % (round(ws[20] * 100), round(ws[179] * 100))
        out.append(line + ".")
    return out


def disagreements(slates, ours_col):
    """When ours (on ETR's scale, as in the blend) and ETR's last upload were 4+ apart: how often each was closer."""
    us = them = 0
    for o, e, y in [t for g in (blend_rows(slates, ours_col) or []) for t in g]:
        if abs(o - e) >= 4:
            if abs(o - y) < abs(e - y):
                us += 1
            else:
                them += 1
    return us, them


def player_rows(rows, title, key, n):
    out = ["**%s**" % title, "",
           "| Player | Team | ADP lock | Ours | ETR last | Actual | Min (usual) | Margin | Injury tag |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=key)[:n]:
        ours = r["ours"] if r["ours"] is not None else r["ours_raw"]
        out.append("| %s | %s | %s | %s | %s | %s | %s (%s) | %s | %s |" % (
            r["name"], r["team"], fmt(r["adp_close"], "%.1f"), fmt(ours, "%.1f"), fmt(r["etr_last"], "%.1f"),
            fmt(r["actual"], "%.1f"), fmt(r["min"], "%.0f"), fmt(r["usual_min"], "%.0f"), fmt(r["margin"], "%+.0f"), r["injury"] or ""))
    return out + [""]


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
        pool = scored(s["rows"])
        sat = [r for r in pool if r["actual"] is not None and not (r["min"] or 0) > 0]
        unmatched = [r["name"] for r in pool if r["actual"] is None]
        out += ["# NBA morning report: %s %s" % (s["date"], s["slate"].replace("nba_", "")), "",
                "%d scored (top %d by ADP at lock or by any source), %d played, %d sat%s." % (
                    len(pool), DEPTH, len(played(s["rows"])), len(sat),
                    (": " + ", ".join("%s (ADP %.0f)" % (r["name"], r["adp_close"]) for r in sorted(sat, key=lambda r: r["adp_close"])[:6])) if sat else ""),
                "Times PT. ADP %s and at lock %s (lock %s). ETR uploads %s. Ours from the board: %s. Final board saved %s." % (
                    pt(m.get("adp_am_at")), pt(m.get("adp_close_at")), pt(m.get("lock")),
                    " and ".join(pt(x["at"]) for x in (m.get("etr_first"), m.get("etr_last")) if x) or "none on file",
                    "yes" if m.get("ours_from_board") else "no, morning file only",
                    pt(m.get("board_saved_at")) if m.get("board_saved_at") else "- (none on file)")]
        if unmatched:
            out.append("No box score matched for: %s." % ", ".join(unmatched))
        out += [""]
    out += ["## Last night", ""] + acc_table([s["rows"] for s in last]) + ["", "**CLV**", ""] + clv_table([s["rows"] for s in last])
    out += ["", "**Blend**", ""] + blend_section(last, "last") + [""]
    for s in last:
        pool = played(s["rows"])
        ours = lambda r: r["ours"] if r["ours"] is not None else r["ours_raw"]
        out += player_rows([r for r in pool if ours(r) is not None], "Biggest misses (ours)", lambda r: -abs(ours(r) - r["actual"]), 10)
        out += player_rows([r for r in pool if ours(r) is not None and r["etr_last"] is not None],
                           "Biggest ours-vs-ETR splits", lambda r: -abs(ours(r) - r["etr_last"]), 8)

    out += ["## Since %s: %d slates, %d player-games" % (upto[0]["date"], len(upto), sum(len(played(s["rows"])) for s in upto)), ""]
    out += acc_table([s["rows"] for s in upto]) + ["", "**CLV**", ""] + clv_table([s["rows"] for s in upto])
    out += ["", "**Blend**", ""] + blend_section(upto, "all")
    for col, name in (("ours", "Ours (board)"), ("ours_raw", "Ours (morning file)")):
        us, them = disagreements(upto, col)
        if us + them:
            out.append("- When %s (on ETR's scale) and ETR were 4+ points apart: ours closer %d times, ETR %d." % (name, us, them))
    out += ["", "**By slate**", "", "| Slate | Played | Corr ours | Corr ETR last | Miss ours | Miss ETR last | CLV ours |", "|---|---|---|---|---|---|---|"]
    for s in upto:
        oc = "ours" if any(r["ours"] is not None for r in s["rows"]) else "ours_raw"
        o, e = accuracy(s["rows"], oc, True), accuracy(s["rows"], "etr_last", True)
        c = clv_line(clv(s["rows"], oc, True))
        out.append("| %s %s | %d | %s | %s | %s | %s | %s |" % (
            s["date"], s["slate"].replace("nba_", ""), len(played(s["rows"])), fmt(o and o["rho"]), fmt(e and e["rho"]),
            fmt(o and o["mae"], "%.1f"), fmt(e and e["mae"], "%.1f"), "%d of %d" % (c["hit"], c["n"]) if c else "-"))
    print("\n".join(out))


if __name__ == "__main__":
    main()
