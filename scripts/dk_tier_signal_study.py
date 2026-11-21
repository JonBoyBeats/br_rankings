"""Tier signal study (2026-11-21, the coordinator's question 1): do the Cut step's tiers carry signal on real results?

  extract --mirror DIR --out OUT   per saved build (analysis/cbb/dk/builds) whose entered contests all have standings:
                                   the slate and simulated field as they stood at lock, the entered contests (entries =
                                   the portfolio's size, as the page's entries file had them), the kept lineups, the
                                   build's gate and nights seed -> OUT/<key>.json for scripts/dk_tier_signal_study.js
  score --dir OUT --md FILE        each kept lineup's tier (rebuilt: OUT/<key>_board.json; and, where the build saved
                                   its board's values and tier-A noise, 2026-11-19 on, the tiers the page showed)
                                   scored on the night's real points in every entered contest alone: its percentile
                                   among the real entries, top 10% / top 1% / cash; per night, then pooled with the
                                   night as the unit; and within tier A, played against not played.

Tiers as the page draws them (dk_sim.js tiers): best value first, a lineup starts the next tier once it is 2 x sqrt(2) x
sigma below the top of its own; at most A / B / C.
"""
import argparse
import json
import math
import os
import statistics as St
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dk_eval as E                        # noqa: E402
from nba_daily import Mirror, iso          # noqa: E402
import datetime as dt                      # noqa: E402

TIERS = "ABC"


def builds():
    """The latest saved build of each draft group, oldest night first, keyed date + draft group."""
    out = {}
    for f in sorted(os.listdir(E.BUILDS)):
        if f.endswith(".json"):
            b = json.load(open(os.path.join(E.BUILDS, f)))
            g = str(b["draft_group"])
            if g not in out or (b.get("saved_at") or "") >= (out[g].get("saved_at") or ""):
                out[g] = b
    return sorted(out.values(), key=lambda b: (b["day"], b.get("start") or b.get("saved_at") or ""))


def key_of(b):
    return "%s_%s" % (b["day"], b["draft_group"])


def graded(b):
    pf = {c: ks for c, ks in (b.get("portfolios") or {}).items() if ks}
    return pf if pf and all(os.path.exists(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c)) for c in pf) else None


def extract(a):
    M = Mirror(a.mirror)
    os.makedirs(a.out, exist_ok=True)

    def last_before(file, start, g, listy):
        for _, sha in reversed(M.versions(file, start - dt.timedelta(days=2), start)):
            d = M.show(sha, file)
            sl = d.get("slates") or ([] if listy else {})
            x = next((x for x in sl if str(x["draft_group_id"]) == g), None) if listy else sl.get(g)
            if x and (x.get("players") or x.get("field")):
                return d, x
        return None, None
    for b in builds():
        g, pf = str(b["draft_group"]), graded(b)
        if not pf:
            print(key_of(b), "skipped: standings missing")
            continue
        start = None
        for _, sha in reversed(M.versions("dk_cbb_morning.json", iso(b["day"] + "T00:00:00Z") - dt.timedelta(days=1), iso(b["day"] + "T00:00:00Z") + dt.timedelta(days=2))):
            s = next((x for x in M.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
            if s:
                start = iso(s["start"])
                break
        _, s = last_before("dk_cbb_morning.json", start, g, True)
        f, F = last_before("dk_cbb_field.json", start, g, False)
        cs = []
        for cid, ks in pf.items():
            c = next((c for c in s.get("contests", []) if str(c["id"]) == cid), None)
            if c and c.get("payouts"):
                cs.append({"contest": c, "n": min(len(ks), c.get("max_per_user") or 1)})
        keep = [b["pool"][i] for i in b["final"]]
        json.dump({"key": key_of(b), "date": b["day"], "g": g, "slate": s, "field": F, "z": f["z"], "contests": cs, "keep": keep,
                   "seed": b.get("nights_seed") or 1, "gate": b.get("gate")}, open(os.path.join(a.out, key_of(b) + ".json"), "w"))
        print(key_of(b), len(keep), "kept,", len(cs), "contests,", len(F["field"]), "field lineups")


def page_tiers(b):
    """The tiers the page showed, where the build saved its board (values: each kept lineup's value per entry, rounded
    to cents; tierA.sigma: the noise on the entries-weighted sum): rebuilt with the gap scaled to per-entry values."""
    bd = (b.get("cut_state") or {}).get("board") or b.get("idea_board") or {}
    v, ta = bd.get("values"), bd.get("tierA") or {}
    if not v or ta.get("sigma") is None:
        return None, None
    w = sum(x["n"] for x in EXTRACTED[key_of(b)]["contests"])      # the page's entries-weighted count
    gap = 2 * math.sqrt(2) * ta["sigma"] / max(1, w)
    order = sorted(range(len(v)), key=lambda k: -v[k])
    out, t, top = [None] * len(v), 0, v[order[0]]
    for k in order:
        if t < 2 and v[k] < top - gap:
            t, top = t + 1, v[k]
        out[k] = TIERS[t]
    return out, ta.get("n")


def real(b):
    """Per kept lineup, on the night's real points, each entered contest alone: percentile among the real entries (share
    of entries it outscores), top 10% / top 1% / cash; averaged over the contests."""
    pf = graded(b)
    rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (b["day"], b["draft_group"])))
    out = [dict(pct=0.0, t10=0.0, t1=0.0, cash=0.0) for _ in b["final"]]
    n_c = 0
    M = None
    for cid in pf:
        entries, players = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
        pts = E.night_points(rec, players)
        field = sorted((e["points"] for e in entries), reverse=True)
        n = len(field)
        t10, t1 = field[math.ceil(0.1 * n) - 1], field[math.ceil(0.01 * n) - 1]
        paid = contest_paid(b, cid, n)
        cash = field[min(paid, n) - 1] if paid else None
        asc = sorted(field)
        for j, i in enumerate(b["final"]):
            p = sum(pts.get(str(x)) or 0 for x in b["pool"][i])
            o = out[j]
            o["pct"] += bisect_left(asc, p) / n
            o["t10"] += p >= t10
            o["t1"] += p >= t1
            o["cash"] += (p >= cash) if cash is not None else 0
        n_c += 1
    for o in out:
        for k in o:
            o[k] /= max(1, n_c)
    return out


def contest_paid(b, cid, n):
    """The last paid place, from the contest's payouts in the extracted lock-time slate."""
    N = EXTRACTED.get(key_of(b))
    if not N:
        return None
    c = next((x["contest"] for x in N["contests"] if str(x["contest"]["id"]) == cid), None)
    return max(E.pay_table(c["payouts"])) if c else None


def bisect_left(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


EXTRACTED = {}
METRICS = [("pct", "pctile"), ("t10", "top10%"), ("t1", "top1%"), ("cash", "cash%")]


def ladder(rows, tiers):
    out = {}
    for t in TIERS:
        ks = [k for k, x in enumerate(tiers) if x == t]
        if ks:
            out[t] = dict(n=len(ks), **{m: St.mean(rows[k][m] for k in ks) for m, _ in METRICS})
    return out


def fmt_ladder(L):
    return ["| %s | %d | %s |" % (t, L[t]["n"], " | ".join("%.1f" % (100 * L[t][m]) for m, _ in METRICS)) for t in TIERS if t in L]


def sign_p(k, n):
    """Two-sided sign test: probability of a split at least this lopsided under 50/50."""
    if n == 0:
        return 1.0
    lo = min(k, n - k)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(lo + 1)) / 2 ** n)


def score(a):
    lines, per, src_note = [], [], []
    for b in builds():
        k = key_of(b)
        if not graded(b) or not os.path.exists(os.path.join(a.dir, k + ".json")):
            continue
        EXTRACTED[k] = json.load(open(os.path.join(a.dir, k + ".json")))
        bp = os.path.join(a.dir, k + "_board.json")
        reb = json.load(open(bp)) if os.path.exists(bp) else None
        shown, shownA = page_tiers(b)
        rows = real(b)
        played = {i for ks in b["portfolios"].values() for i in ks}
        night = {"key": k, "kept": len(rows)}
        # the continuous check, every kept lineup: the sim's value against its real percentile (rank correlation), and the
        # top 10% by value against the other 90%
        for name, vals in (("rebuilt", reb and reb["values"]), ("shown", ((b.get("cut_state") or {}).get("board") or b.get("idea_board") or {}).get("values"))):
            if vals and len(vals) == len(rows):
                o = sorted(range(len(vals)), key=lambda j: -vals[j]); top = set(o[:max(1, len(o) // 10)])
                night[name + "_cont"] = {"rho": E.spearman(list(vals), [r["pct"] for r in rows]),
                                         "top": St.mean(rows[j]["pct"] for j in top), "rest": St.mean(rows[j]["pct"] for j in range(len(rows)) if j not in top)}
        for name, tiers in (("rebuilt", reb and reb["tier"]), ("shown", shown)):
            if tiers:
                night[name] = ladder(rows, tiers)
                A = [j for j, t in enumerate(tiers) if t == "A"]
                pa = [j for j in A if b["final"][j] in played]
                na = [j for j in A if b["final"][j] not in played]
                night[name + "_play"] = {"played": dict(n=len(pa), **{m: St.mean(rows[j][m] for j in pa) for m, _ in METRICS}) if pa else None,
                                         "not": dict(n=len(na), **{m: St.mean(rows[j][m] for j in na) for m, _ in METRICS}) if na else None}
        if shown and reb:
            agree = sum(x == y for x, y in zip(shown, reb["tier"])) / len(shown)
            vs = [r for r in zip(b.get("idea_board", {}).get("values") or (b.get("cut_state") or {}).get("board", {}).get("values"), reb["values"])]
            src_note.append("%s: rebuilt tiers agree with the page's on %.0f%% of kept lineups; tier A %d rebuilt vs %d shown (%s from the saved values); value rank correlation %.2f" % (
                k, 100 * agree, reb["tier"].count("A"), shown.count("A"), shownA, E.spearman([x for x, _ in vs], [y for _, y in vs])))
        per.append(night)
    # the tables
    md = ["# Do the cut's tiers carry signal? (2026-11-21)", "",
          "Question 1 from the coordinator. Every kept lineup of each saved build whose entered contests all have standings, scored on the night's real points, alone in each entered contest (averaged over them): percentile among the real entries, top 10%, top 1%, cash. Tiers as the page draws them (DKSim.tiers: A within 2 x sqrt(2) x sigma of the best, at most A / B / C).", "",
          "**Tier source.** The builds saved no per-lineup tier. *Rebuilt*: the Cut step's idea board re-simmed (scripts/dk_tier_signal_study.js: each kept lineup alone in every entered contest on the slate's nights, 3,000, entries-weighted, the build's own gate and nights seed, the lock-time slate and simulated field). *Shown*: where the build saved its board (values per kept lineup and tier A's sigma, 2026-11-19 on), the tiers the page displayed, rebuilt from those. Projection overrides, marked-out players and minute shifts made on the page are not in a build before 11-20, so the rebuild can differ from what the page showed; the shown/rebuilt agreement below measures that.", ""]
    md += ["Nights: " + ", ".join(n["key"] for n in per) + " (%d). Standings for 2026-11-20 (early 157013, main 157015) were not in yet." % len(per), ""]
    if src_note:
        md += ["**Rebuild check.** " + "; ".join(src_note) + ". (The shown tier-A counts rebuilt from the saved values differ a little from the count the page saved: the values are rounded to cents, and the page's entries count came from the entries file rather than the portfolio sizes.)", ""]
    for name, title in (("rebuilt", "Rebuilt tiers"), ("shown", "Tiers as shown (saved boards only)")):
        nights = [n for n in per if name in n]
        if not nights:
            continue
        md += ["## " + title, "", "Per night (rates in %, each lineup's average over the night's entered contests):", ""]
        order_ct = {"A>B>C": 0, "other": 0}
        gaps = {"A-B": [], "B-C": []}
        for n in nights:
            L = n[name]
            md += ["**%s** (%d kept)" % (n["key"], n["kept"]), "", "| tier | n | " + " | ".join(lbl for _, lbl in METRICS) + " |", "|---|---|" + "---|" * len(METRICS)] + fmt_ladder(L) + [""]
            ok = all(t in L for t in "ABC") and L["A"]["pct"] > L["B"]["pct"] > L["C"]["pct"]
            order_ct["A>B>C" if ok else "other"] += 1
            if "A" in L and "B" in L:
                gaps["A-B"].append(L["A"]["pct"] - L["B"]["pct"])
            if "B" in L and "C" in L:
                gaps["B-C"].append(L["B"]["pct"] - L["C"]["pct"])
        md += ["Nights in A > B > C order on percentile: %d of %d (other: %d)." % (order_ct["A>B>C"], len(nights), order_ct["other"]), ""]
        md += ["Paired by night (percentile points, night as the unit):", "", "| gap | nights | mean | sd across nights | positive | sign-test p |", "|---|---|---|---|---|---|"]
        for gname, g in gaps.items():
            if g:
                pos = sum(x > 0 for x in g)
                md.append("| %s | %d | %+.1f | %s | %d of %d | %.2f |" % (gname, len(g), 100 * St.mean(g), "%.1f" % (100 * St.stdev(g)) if len(g) > 1 else "-", pos, len(g), sign_p(pos, len(g))))
        # pooled: each night weighted equally
        md += ["", "Pooled, each night weighted equally (mean of the nightly tier means):", "", "| tier | nights | " + " | ".join(lbl for _, lbl in METRICS) + " |", "|---|---|" + "---|" * len(METRICS)]
        for t in TIERS:
            have = [n[name][t] for n in nights if t in n[name]]
            if have:
                md.append("| %s | %d | %s |" % (t, len(have), " | ".join("%.1f" % (100 * St.mean(x[m] for x in have)) for m, _ in METRICS)))
        cont = [n[name + "_cont"] for n in nights if name + "_cont" in n]
        if cont:
            md += ["", "Continuous check, every kept lineup (not just the handful in tier A): rank correlation of the sim's value with the real percentile, and the top 10% of kept lineups by value against the other 90% (percentile):", "",
                   "| night | rho | top 10% by value | other 90% | gap |", "|---|---|---|---|---|"]
            for n in nights:
                c = n.get(name + "_cont")
                if c:
                    md.append("| %s | %+.2f | %.1f | %.1f | %+.1f |" % (n["key"], c["rho"], 100 * c["top"], 100 * c["rest"], 100 * (c["top"] - c["rest"])))
            pos = sum(c["rho"] > 0 for c in cont)
            md += ["", "rho positive on %d of %d nights (sign-test p %.2f); mean rho %+.2f; mean top-10%% gap %+.1f points." % (
                pos, len(cont), sign_p(pos, len(cont)), St.mean(c["rho"] for c in cont), 100 * St.mean(c["top"] - c["rest"] for c in cont))]
        md += ["", "Within tier A, played (in the saved portfolios) against not played:", "", "| night | played n | not n | " + " | ".join("played " + lbl + " / not" for _, lbl in METRICS) + " |", "|---|---|---|" + "---|" * len(METRICS)]
        dif = []
        for n in nights:
            p = n[name + "_play"]
            if p["played"] and p["not"]:
                md.append("| %s | %d | %d | %s |" % (n["key"], p["played"]["n"], p["not"]["n"], " | ".join("%.1f / %.1f" % (100 * p["played"][m], 100 * p["not"][m]) for m, _ in METRICS)))
                dif.append(p["played"]["pct"] - p["not"]["pct"])
            else:
                md.append("| %s | %s | %s | (one side empty) |" % (n["key"], p["played"]["n"] if p["played"] else 0, p["not"]["n"] if p["not"] else 0) + " |" * (len(METRICS) - 1))
        if dif:
            pos = sum(x > 0 for x in dif)
            md += ["", "Played minus not, percentile points: mean %+.1f over %d nights, played ahead on %d (sign-test p %.2f)." % (100 * St.mean(dif), len(dif), pos, sign_p(pos, len(dif)))]
        md += [""]
    md += ["**Sample.** %d nights. A sign test on this few nights cannot reach p < 0.05 unless every night agrees (5 of 5 gives p 0.06); read the per-night rows and their direction, not the pooled means alone." % len(per), ""]
    open(a.md, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("extract")
    x.add_argument("--mirror", required=True)
    x.add_argument("--out", required=True)
    s = sp.add_parser("score")
    s.add_argument("--dir", required=True)
    s.add_argument("--md", required=True)
    a = p.parse_args()
    {"extract": extract, "score": score}[a.cmd](a)


if __name__ == "__main__":
    main()
