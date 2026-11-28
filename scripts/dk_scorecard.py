"""The DraftKings CBB scorecard (2026-11-25, the coordinator's tracking and grading framework): one headline per arm,
LIVE against PREVIOUS (the arm's version before its last change, logged the same nights) against RULER (the frozen
ruler-2026-11-23, battle-royale-research scripts/cbb_ruler.py), over the last LAST slates and the season. The slate is
the unit: every number is a per-slate value, averaged over slates, and every comparison is a paired difference over the
slates that logged both, +- its SE (the per-slate differences' sd / sqrt(slates)). Grading only.

  minutes      ROTATION band (ours 10-25 DK points) minutes MAE: min_proj | min_old | ruler_min
  per-minute   STARS band (ours 25+) points MAE: fp_dk | old_fp | ruler_fp (all without the DK-average gate; ruler_fp_gate,
               the lock's gated number, is in the night record beside it)
  ownership    the chalk band (max(projected, actual) 15%+) over the slate's graded player-contests: MAE in points and
               the share off by 10+: own_proj | own_raw | own_ruler (the record's, joined by player)
  field        the simulated field's lines against the real ones, per graded contest of 100+ entries: cash line and
               top-10% line, sim minus real (the top-1% line is not logged; eval.csv has the winning score, cash and
               top 10%)
  pool         the cut's kept lineups minus the whole bank: mean real finish percentile in each 100+ contest (as the lab)
  fill         the entered set minus random fills from the whole bank (fill_eval.csv): dollars back, and the entered
               set's percentile among the random fills
  late swap    accepted swaps: DraftKings points of the player in minus the player out (swap_grades.csv); n/a if none
  results      the owner's entries: dollars back minus fees, and return on fees. Read over 20+ nights only.

Columns that were not logged on a slate are n/a on it, never filled in, with three exceptions marked "backfilled":
the ruler's projection on 2026-11-23 and 2026-11-24 (157021, 157024, 157026) IS the live one (the live model was the
lock's until 2026-11-25), and its ownership there is own_raw (the lock's field, before the correction). Slates before
2026-11-23 have no ruler: the lock model's inputs (careers, game logs) for them were never stored.

Versions: scripts/dk_arms.py (analysis/cbb/dk/arm_versions.json). An arm is settling until LAST graded slates have run
under its current version. The same-night-pair check: after a change, the PREVIOUS column must be logged on each of
the first LAST slates (analysis/cbb/dk/process.md); where it is missing, the scorecard says so.

  python3 scripts/dk_eval.py scorecard        (writes analysis/cbb/dk/scorecard.md; misses --friday prints it too)
"""
import datetime as dt, glob, json, math, os, statistics as S
from collections import defaultdict

import dk_arms
import dk_eval as E
import dk_proj_grade as PG

LAST = 7
SCORECARD = os.path.join(E.DK, "scorecard.md")
RULER = "ruler-2026-11-23"
RULER_BACKFILL = {"157021", "157024", "157026"}     # the live model was the ruler's: see the docstring
ARM_OF = {"minutes": "projection", "per-minute": "projection", "ownership": "ownership", "field": "field", "pool": "cut",
          "fill": "fill", "late swap": "late_swap", "results": None}
num = PG.num


def mae(pairs):
    return S.mean(abs(a - p) for a, p in pairs) if pairs else None


def three_way(rows, act, live, prev, ruler):
    """{"live", "prev", "ruler", "d_prev", "d_ruler", "n"}: live MAE on every row; each other column's MAE on the rows
    that have it, and live minus it on those same rows (None where it isn't logged)."""
    L = [(act(r), live(r)) for r in rows]
    out = {"live": mae(L), "n": len(L), "prev": None, "ruler": None, "d_prev": None, "d_ruler": None}
    for k, f in (("prev", prev), ("ruler", ruler)):
        rs = [r for r in rows if f(r) is not None]
        if rs:
            c, l = mae([(act(r), f(r)) for r in rs]), mae([(act(r), live(r)) for r in rs])
            out[k], out["d_" + k] = c, l - c
    return out


def logged(rows, col, live_col):
    """The previous column counts as logged on a slate only where it differs from live on some row (cbb_daily fills it
    with the live value before it existed)."""
    return any(num(r.get(col)) is not None and num(r.get(live_col)) is not None and abs(num(r[col]) - num(r[live_col])) > 1e-9 for r in rows)


def ruler_col(rows, g, col, live_col):
    """The ruler's value getter for a slate: the logged column, the live one on the backfilled slates, else None."""
    if g in RULER_BACKFILL:
        return lambda r: num(r.get(live_col))
    if any(num(r.get(col)) is not None for r in rows):
        return lambda r: num(r.get(col))
    return lambda r: None


def projection_arms(name, rows):
    g = name.split("_")[1]
    G = PG.graded(rows)
    rot = [r for r in PG.band(G, *PG.ROTATION) if num(r.get("min")) is not None and num(r.get("min_proj")) is not None]
    stars = PG.band(G, *PG.STARS)
    mp = logged(rows, "min_old", "min_proj")
    pp = logged(rows, "old_fp", "fp_dk")
    m = three_way(rot, lambda r: num(r["min"]), lambda r: num(r["min_proj"]),
                  (lambda r: num(r.get("min_old"))) if mp else (lambda r: None), ruler_col(rows, g, "ruler_min", "min_proj"))
    p = three_way(stars, lambda r: num(r["actual_dk"]), lambda r: num(r["fp_dk"]),
                  (lambda r: num(r.get("old_fp"))) if pp else (lambda r: None), ruler_col(rows, g, "ruler_fp", "fp_dk"))
    for x in (m, p):
        x["backfilled"] = g in RULER_BACKFILL
    return m, p


def ownership_arm(g, rec, own_rows):
    """The chalk band for live, raw and ruler, each scored on the player-contests in the band by max(actual, live, it)."""
    ruler_by = {r["dk_id"]: num(r.get("own_ruler")) for r in rec}
    rows = [r for r in own_rows if str(r["draft_group"]) == g]
    if not rows:
        return None
    prev_on = any(abs(r["p"] - r["raw"]) > 1e-9 for r in rows)
    get = {"prev": (lambda r: r["raw"]) if prev_on else (lambda r: None),
           "ruler": (lambda r: r["raw"]) if g in RULER_BACKFILL else (lambda r: ruler_by.get(r["dk_id"]))}
    band = [r for r in rows if max(r["a"], r["p"]) >= E.CHALK_OWN]
    if not band:
        return None
    off = lambda rs, f: sum(abs(r["a"] - f(r)) >= E.CHALK_OFF for r in rs) / len(rs)
    out = {"live": mae([(r["a"], r["p"]) for r in band]), "live_off": off(band, lambda r: r["p"]), "n": len(band),
           "backfilled": g in RULER_BACKFILL}
    for k, f in get.items():
        rs = [r for r in rows if f(r) is not None and max(r["a"], r["p"], f(r)) >= E.CHALK_OWN]
        if rs:
            c, l = mae([(r["a"], f(r)) for r in rs]), mae([(r["a"], r["p"]) for r in rs])
            out[k], out[k + "_off"], out["d_" + k] = c, off(rs, f), l - c
        else:
            out[k] = out[k + "_off"] = out["d_" + k] = None
    return out


def field_arm(evals):
    """{draft group: {"cash": mean sim - real, "top10": ..., "n": contests}} over graded contests of 100+ entries."""
    by = defaultdict(dict)
    for r in evals:
        if (num(r.get("entries")) or 0) >= 100 and num(r.get("sim_cash")) is not None and num(r.get("field_cash")) is not None:
            by[str(r["draft_group"])][r["contest_id"]] = r
    out = {}
    for g, cs in by.items():
        v = list(cs.values())
        out[g] = {"cash": S.mean(num(r["sim_cash"]) - num(r["field_cash"]) for r in v),
                  "top10": S.mean(num(r["sim_top10"]) - num(r["field_top10"]) for r in v if num(r.get("sim_top10")) is not None),
                  "n": len(v)}
    return out


def pool_arm(evals):
    """{draft group: {"diff": kept minus whole bank, mean real finish percentile, "n": contests}} from the latest saved
    bank with a cut, over its slate's graded contests of 100+ entries."""
    banks = {}
    for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if b.get("pool") and b.get("final") and (g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or "")):
            banks[g] = b
    contests = defaultdict(set)
    for r in evals:
        contests[str(r["draft_group"])].add(r["contest_id"])
    out = {}
    for g, b in banks.items():
        rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (b["day"], g)))
        if not rec:
            continue
        kept, diffs = sorted(set(b["final"])), []
        for cid in sorted(contests.get(g, ())):
            path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
            if not os.path.exists(path):
                continue
            entries, players = E.standings(path)
            n = len(entries)
            if n < E.LAB_MIN_ENTRIES:
                continue
            pts = E.night_points(rec, players)
            field = sorted((e["points"] for e in entries), reverse=True)
            pct = [100.0 * (n - (E.placed(sum(pts.get(str(i)) or 0 for i in lu), field) - 1)) / n for lu in b["pool"]]
            diffs.append(S.mean(pct[k] for k in kept) - S.mean(pct))
        if diffs:
            out[g] = {"diff": S.mean(diffs), "n": len(diffs)}
    return out


def fill_arm():
    out = {}
    for r in E.read(E.FILL_EVAL) if os.path.exists(E.FILL_EVAL) else []:
        if r["subset"] == "bank" and num(r.get("entered_dollars")) is not None:
            out[str(r["draft_group"])] = {"dollars": num(r["entered_dollars"]) - num(r["avg_dollars"]),
                                          "pct": 100.0 * (1 - num(r["beat_entered"]))}
    return out


def swap_arm():
    by = defaultdict(list)
    for r in E.read(E.SWAP_GRADES) if os.path.exists(E.SWAP_GRADES) else []:
        if r.get("accepted") == "1" and num(r.get("gain_actual")) is not None:
            by[str(r["draft_group"])].append(num(r["gain_actual"]))
    return {g: {"gain": S.mean(v), "n": len(v)} for g, v in by.items()}


def results_arm(evals):
    by = defaultdict(lambda: [0.0, 0.0])
    for r in evals:
        if r.get("who") == "mine" and num(r.get("fees")):
            by[str(r["draft_group"])][0] += num(r.get("dollars_back")) or 0
            by[str(r["draft_group"])][1] += num(r["fees"])
    return {g: {"net": d - f, "roi": (d - f) / f} for g, (d, f) in by.items() if f}


def collect():
    """[{slate, date, group, arms: {arm: per-slate dict or None}}] for every graded slate, oldest first."""
    evals = E.read(E.EVAL)
    own_rows = E.own_grade_rows()
    fld, pool, fill, swap, res = field_arm(evals), pool_arm(evals), fill_arm(), swap_arm(), results_arm(evals)
    out = []
    for name, rows in PG.slates():
        d, g = name.split("_")
        m, p = projection_arms(name, rows)
        out.append({"slate": name, "date": d, "group": g, "arms": {
            "minutes": m if m["live"] is not None else None, "per-minute": p if p["live"] is not None else None,
            "ownership": ownership_arm(g, rows, own_rows), "field": fld.get(g), "pool": pool.get(g), "fill": fill.get(g),
            "late swap": swap.get(g), "results": res.get(g)}})
    return out


def agg(vals):
    """(mean, SE, slates) of per-slate values (None skipped)."""
    v = [x for x in vals if x is not None]
    if not v:
        return None, None, 0
    return S.mean(v), (S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else None), len(v)


def f_ms(m, se, n, fmt="%.2f", signed=False):
    if not n:
        return "n/a"
    f = ("%+" + fmt[1:]) if signed else fmt
    return (f % m) + (" ± " + fmt % se if se is not None else "") + " (%d)" % n


def current(arm, arms, today):
    """(the arm's version live today, the one before it): a slate later today than any draft group."""
    return dk_arms.version(arm, today, 10 ** 12, arms)


def settling(arm, slates, arms, today):
    """(version live today, last-changed date, graded slates under it, status)."""
    if arm is None:
        return None, None, None, "-"
    v, _ = current(arm, arms, today)
    if v is None:
        return None, None, 0, "-"
    k = sum(1 for s in slates if dk_arms.version(arm, s["date"], s["group"], arms)[0] is v)
    return v, v["from"] + (" from %s" % v["first_slate"] if v.get("first_slate") else ""), k, ("settled" if k >= LAST else "settling %d of %d" % (k, LAST))


def pair_check(name, arm, slates, arms, today):
    """The same-night-pair check for the arm's version live today: PREVIOUS logged on each of its first LAST graded
    slates."""
    if arm is None:
        return None
    v, before = current(arm, arms, today)
    if v is None or before is None:
        return None
    under = [s for s in slates if dk_arms.version(arm, s["date"], s["group"], arms)[0] is v][:LAST]
    if name in ("minutes", "per-minute", "ownership"):
        miss = [s["slate"] for s in under if not s["arms"].get(name) or s["arms"][name].get("prev") is None]
        if not under:
            return "%s since %s: no graded slate yet; PREVIOUS must be logged on its first %d" % (v["tag"], v["from"], LAST)
        return ("%s: PREVIOUS logged on %d of %d slates" % (v["tag"], len(under) - len(miss), len(under))) + (
            "; MISSING on " + ", ".join(miss) if miss else "")
    return "%s: no PREVIOUS column is logged for this arm (a change here can't be paired on the same nights)" % v["tag"]


HEAD = {"minutes": "ROTATION minutes MAE", "per-minute": "STARS points MAE", "ownership": "chalk-band MAE (off 10+)",
        "field": "sim - real: cash line (top 10%)", "pool": "kept - bank, finish pct", "fill": "entered - random fills: $ (pct)",
        "late swap": "in - out, DK pts", "results": "net $ (ROI); 20+ nights only"}


def window_cells(name, part):
    """[LIVE, PREVIOUS, RULER, LIVE-PREV, LIVE-RULER] for one window."""
    xs = [s["arms"].get(name) for s in part]
    xs = [x for x in xs if x]
    if name in ("minutes", "per-minute", "ownership"):
        live = agg([x["live"] for x in xs])
        cells = [f_ms(*live), f_ms(*agg([x["prev"] for x in xs])), f_ms(*agg([x["ruler"] for x in xs])),
                 f_ms(*agg([x["d_prev"] for x in xs]), signed=True), f_ms(*agg([x["d_ruler"] for x in xs]), signed=True)]
        if name == "ownership":
            for i, k in ((0, "live_off"), (1, "prev_off"), (2, "ruler_off")):
                m, _, n = agg([x.get(k) for x in xs])
                if n:
                    cells[i] += " (%.0f%%)" % (100 * m)
        if any(x.get("backfilled") for x in xs):
            cells[2] += "*"
        return cells
    if name == "field":
        c, t = agg([x["cash"] for x in xs]), agg([x["top10"] for x in xs])
        return [f_ms(*c, fmt="%.1f", signed=True) + (" (%s)" % f_ms(*t, fmt="%.1f", signed=True) if t[2] else ""), "n/a", "n/a", "n/a", "n/a"]
    if name == "pool":
        return [f_ms(*agg([x["diff"] for x in xs]), fmt="%.1f", signed=True), "n/a", "n/a", "n/a", "n/a"]
    if name == "fill":
        d, p = agg([x["dollars"] for x in xs]), agg([x["pct"] for x in xs])
        return [f_ms(*d, fmt="%.2f", signed=True) + (" (%.0f pct)" % p[0] if p[2] else ""), "n/a", "n/a", "n/a", "n/a"]
    if name == "late swap":
        return [f_ms(*agg([x["gain"] for x in xs]), fmt="%.1f", signed=True), "n/a", "n/a", "n/a", "n/a"]
    if name == "results":
        n, r = agg([x["net"] for x in xs]), agg([x["roi"] for x in xs])
        return [f_ms(*n, fmt="%.2f", signed=True) + (" (%+.0f%%)" % (100 * r[0]) if r[2] else ""), "n/a", "n/a", "n/a", "n/a"]


def lines(slates=None, arms=None, today=None):
    slates = collect() if slates is None else slates
    arms = arms or dk_arms.load()
    today = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    if not slates:
        return ["Scorecard: no graded slates yet"]
    last = slates[-LAST:]
    out = ["# DraftKings CBB scorecard", "",
           "%d graded slates (%s to %s); last %d: %s to %s. LIVE = what ran that night; PREVIOUS = the arm's version before "
           "its last change, logged the same nights; RULER = %s (frozen). Cells: mean over slates ± SE (slates). "
           "PREVIOUS and RULER: their own level on the slates that logged them; LIVE − X: paired per slate on the rows both "
           "logged, the comparison to read (negative = LIVE better for the MAE arms). Version: live today, with its last-changed date; "
           "status counts the graded slates under it. "
           "* = ruler backfilled (157021, 157024, 157026: the live model was the ruler's). Generated by "
           "`python3 scripts/dk_eval.py scorecard`." % (len(slates), slates[0]["slate"], slates[-1]["slate"], len(last),
                                                       last[0]["slate"], last[-1]["slate"], RULER), "",
           "| Arm | Headline | Version (last changed) | Status | Window | LIVE | PREVIOUS | RULER | LIVE − PREV | LIVE − RULER |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    checks = []
    for name, arm in ARM_OF.items():
        v, since, k, status = settling(arm, slates, arms, today)
        ver = "%s (%s)" % (v["tag"], since) if v else "-"
        for wname, part in (("last %d" % len(last), last), ("season %d" % len(slates), slates)):
            out.append("| %s | %s | %s | %s | %s | %s |" % (name, HEAD[name], ver, status, wname, " | ".join(window_cells(name, part))))
        c = pair_check(name, arm, slates, arms, today)
        if c:
            checks.append("- %s: %s" % (name, c))
    out += ["", "Same-night-pair check (process.md: after a change, PREVIOUS logged on each of the first %d slates):" % LAST, ""] + checks
    out += ["", "## Minutes and per-minute by games played at lock", "",
            "The same headlines split by how many games the player had played this season at lock (season, every graded slate; "
            "gp from the night record or analysis/cbb/dk/gp_at_lock.csv). Cells: mean over slates ± SE (slates).", ""] + gp_lines()
    sl_ = source_lines()
    if sl_:
        out += [""] + sl_
    pd = pair_due(len(slates))
    if pd:
        out += ["", pd]
    out += ["", "Notes: the field arm's top-1% line is not logged (eval.csv keeps the winning score, top 10% and cash); "
            "the field, pool, fill and late-swap arms log no PREVIOUS or RULER yet, so they read LIVE only. Results: read over 20+ nights only."]
    return out


# The games-played split (2026-11-28, the operator: the in-season pieces were starved on the early slates, so read the
# projection headlines by how many games a player had at lock). gp from the night record's gp column (cbb_daily.py from
# 2026-11-28) or, before that, analysis/cbb/dk/gp_at_lock.csv (scripts/dk_gp_backfill.py).
GP_BUCKETS = (("<=3 games", 0, 3), ("4-6 games", 4, 6), ("7+ games", 7, 10 ** 6))
GP_SIDECAR = os.path.join(E.DK, "gp_at_lock.csv")
PAIR_RUNS = os.path.join(E.DK, "pair_backtest_runs.json")


def gp_map():
    out = {}
    if os.path.exists(GP_SIDECAR):
        for r in E.read(GP_SIDECAR):
            out[(r["slate"], r["dk_id"])] = int(float(r["gp"]))
    return out


def gp_lines(window=None):
    """The minutes and per-minute headlines by games played at lock: per bucket, LIVE (mean over slates ± SE) and
    LIVE - PREV, LIVE - RULER (paired per slate on the rows both logged)."""
    side = gp_map()
    per = []
    for name, rows in PG.slates():
        g = name.split("_")[1]
        for r in rows:
            v = num(r.get("gp"))
            r["_gp"] = v if v is not None else side.get((name, r["dk_id"]))
        G = PG.graded(rows)
        mp, pp = logged(rows, "min_old", "min_proj"), logged(rows, "old_fp", "fp_dk")
        cells = {}
        for lab, lo, hi in GP_BUCKETS:
            B = [r for r in G if r["_gp"] is not None and lo <= r["_gp"] <= hi]
            rot = [r for r in PG.band(B, *PG.ROTATION) if num(r.get("min")) is not None and num(r.get("min_proj")) is not None]
            stars = PG.band(B, *PG.STARS)
            cells[lab] = (
                three_way(rot, lambda r: num(r["min"]), lambda r: num(r["min_proj"]), (lambda r: num(r.get("min_old"))) if mp else (lambda r: None),
                          ruler_col(rows, g, "ruler_min", "min_proj")) if rot else None,
                three_way(stars, lambda r: num(r["actual_dk"]), lambda r: num(r["fp_dk"]), (lambda r: num(r.get("old_fp"))) if pp else (lambda r: None),
                          ruler_col(rows, g, "ruler_fp", "fp_dk")) if stars else None)
        per.append(cells)
    if window:
        per = per[-window:]
    out = ["| Headline | Games at lock | LIVE | LIVE − PREV | LIVE − RULER | rows (season) |", "|---|---|---|---|---|---|"]
    for i, head in ((0, HEAD["minutes"]), (1, HEAD["per-minute"])):
        for lab, _, _ in GP_BUCKETS:
            xs = [c[lab][i] for c in per if c[lab][i]]
            out.append("| %s | %s | %s | %s | %s | %d |" % (head, lab, f_ms(*agg([x["live"] for x in xs])), f_ms(*agg([x["d_prev"] for x in xs]), signed=True),
                                                         f_ms(*agg([x["d_ruler"] for x in xs]), signed=True), sum(x["n"] for x in xs)))
    return out


def pair_due(n_graded):
    """The standing pair-backtest re-run: the last run's graded-slate count and when the next is due."""
    if not os.path.exists(PAIR_RUNS):
        return None
    d = json.load(open(PAIR_RUNS))
    last = d["runs"][-1]
    due = last["graded_slates"] + d["every"]
    return ("Projection pair backtest (analysis/cbb/dk/projection_pair_backtest_2026-11-28/ppb.py, ppb_trend.py): last run %s at %d graded "
            "slates; next re-run due at %d graded slates (now %d)%s." % (last["date"], last["graded_slates"], due, n_graded,
                                                                         " — DUE NOW" if n_graded >= due else ""))


# External projection sources in shadow (2026-11-28): battle-royale-research scripts/dk_source.py grades each source
# against ours and the ruler and publishes AGGREGATES only (the sources are paid content) to the mirror's
# dk_cbb_source_grades.json; read here from the mirror beside this checkout (MIRROR=<dir> overrides). Display only.
SOURCE_NAMES = {"gajewski": "Gajewski (shadow)"}
BLEND_AT = 10


def source_grades():
    root = os.path.abspath(os.path.join(E.DK, "..", "..", ".."))
    for d in (os.environ.get("MIRROR"), os.path.join(os.path.dirname(root), "br-adp-mirror")):
        if d and os.path.exists(os.path.join(d, "dk_cbb_source_grades.json")):
            return json.load(open(os.path.join(d, "dk_cbb_source_grades.json")))
    return None


def source_lines(doc=None):
    doc = doc if doc is not None else source_grades()
    if not doc:
        return []
    out = ["## External projection sources (shadow)", "",
           "Graded by battle-royale-research `scripts/dk_source.py` on the rows each source projects (aggregates only: the per-player "
           "values stay in the private repo). Bands by OUR projection; ours = 0 for a player Out at lock. Cells: mean over graded slates "
           "± SE (slates); source − ours is paired per slate (negative = the source better); 'better on' counts slates.", ""]
    for src, d in sorted((doc.get("sources") or {}).items()):
        name = SOURCE_NAMES.get(src, src + " (shadow)")
        sl = d.get("slates") or []
        g = [x for x in sl if x.get("status") == "graded"]
        pend = [x["slate"] for x in sl if x.get("status") != "graded"]
        out.append("### %s: %d graded slate%s%s" % (name, len(g), "" if len(g) == 1 else "s", ("; not final yet: " + ", ".join(pend)) if pend else ""))
        if g:
            out += ["", "| Headline | Ours | %s | Ruler | %s − ours | %s better on | rows |" % (name, name, name), "|---|---|---|---|---|---|---|"]
            for k, lab in (("rot_min", HEAD["minutes"]), ("stars_pts", HEAD["per-minute"]), ("rot_pts", "ROTATION points MAE")):
                xs = [x[k] for x in g if x.get(k) and x[k].get("ours") is not None and x[k].get("source") is not None]
                d_ = [x["source"] - x["ours"] for x in xs]
                out.append("| %s | %s | %s | %s | %s | %d of %d | %d |" % (lab, f_ms(*agg([x["ours"] for x in xs])), f_ms(*agg([x["source"] for x in xs])),
                                                                     f_ms(*agg([x["ruler"] for x in xs])), f_ms(*agg(d_), signed=True),
                                                                     sum(v < 0 for v in d_), len(d_), sum(x["n"] for x in xs)))
            sp = [x["spearman"] for x in g if x.get("spearman") and x["spearman"].get("ours") is not None and x["spearman"].get("source") is not None]
            out.append("| Spearman, projected 10+ (higher better) | %s | %s | n/a | %s | %d of %d | %d |" % (
                f_ms(*agg([x["ours"] for x in sp])), f_ms(*agg([x["source"] for x in sp])), f_ms(*agg([x["source"] - x["ours"] for x in sp]), signed=True),
                sum(x["source"] > x["ours"] for x in sp), len(sp), sum(x["n"] for x in sp)))
            out += ["", "Disagreements (|source − ours| ≥ 4 points), pooled over graded slates:"]
            for t in ("below $7k", "$7k+"):
                ds = [x["disagree"][t] for x in g if x.get("disagree") and x["disagree"].get(t) and x["disagree"][t].get("n")]
                n = sum(x["n"] for x in ds)
                if n:
                    closer = sum(x["source_closer"] * x["n"] for x in ds) / n
                    gap = sum(x["mae_ours_minus_source"] * x["n"] for x in ds) / n
                    out.append("- %s: %d players; the source closer on %.0f%%; |error| ours minus source %+.2f points" % (t, n, 100 * closer, gap))
                else:
                    out.append("- %s: none yet" % t)
            ow = [x["own"] for x in g if isinstance(x.get("own"), dict)]
            if ow:
                out.append("")
                out.append("Ownership (chalk band, real from 100+ entry contests): source MAE %s, ours %s; off 10+ source %s, ours %s; "
                           "concentration miss (field top 8 − projected top 8) source %s, ours %s." % (
                               f_ms(*agg([x["source"]["mae"] for x in ow])), f_ms(*agg([x["ours"]["mae"] for x in ow])),
                               f_ms(*agg([x["source"]["off10"] for x in ow])), f_ms(*agg([x["ours"]["off10"] for x in ow])),
                               f_ms(*agg([x["conc_source"] for x in ow]), fmt="%.1f", signed=True), f_ms(*agg([x["conc_ours"] for x in ow]), fmt="%.1f", signed=True)))
        out += ["", "%s blend test (ours vs the source vs a held-out blend weight, projection and ownership by salary tier): due at %d graded slates "
                "(now %d)%s." % (name, BLEND_AT, len(g), " — DUE NOW" if len(g) >= BLEND_AT else ""), ""]
    return out


def write(ls):
    with open(SCORECARD, "w", newline="\n") as f:
        f.write("\n".join(ls) + "\n")


def main(a=None):
    ls = lines()
    write(ls)
    print("\n".join(ls))
