"""Calibration of the Live page's My lineups chances, replayed on past nights.

For each night's flagship (its largest contest) every game is stopped at the same point (tip, end of the first
quarter, half, end of the third), each player's points at that point rebuilt from his stints in the mirror's
nba_minutes.json (in and out, in seconds, and the points scored on the floor), and the page's model run for the
whole field: points so far plus his usual (the morning file's minutes x points a minute, as the page uses without
an ETR upload) for the share of the game left, with a spread of K x the square root of his usual x the square root
of the share left, 400 draws, one per player shared by every lineup that has him. A lineup's chance is the share
of draws it lands in the top 1%; each is then set against where it really finished.

A player with no minutes that night counts as out once his game has started (ESPN lists inactives as out; a
coach's decision DNP would still read as "to play" on the page, so the page is a little more hopeful there).
All games are stopped at the same point, though on a real night they tip at different times.

Run for each spread K (the page uses 3.0 to a quarter in, 2.0 from the half) and for both usuals (the morning file's,
and ETR's median, which the page uses when today's ETR file is uploaded on the board). Each night is replayed once,
when its stints are in the mirror, and kept in analysis/nba/contests/live_calibration.json (band counts and log-loss
sums); the pooled reliability tables (predicted chance band against how often those lineups made the top 1%, for
the whole field and for mine) are rebuilt from every night kept. The 2:17am job runs it.

  python3 scripts/nba_live_calibration.py --mirror ../br-adp-mirror [--k 1.6,2.0,3.0]
"""
import argparse, collections, json, math, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import nba_contests as nc   # noqa: E402  the contest files and the daily record, as the measures read them

SIMS, AT = 400, (0.0, 0.25, 0.5, 0.75)
BANDS = [0, 0.005, 0.02, 0.05, 0.10, 0.25, 0.50, 1.01]


def minutes_history(mirror):
    """{(date, name key, team): (stints, game length)} from every version of the mirror's nba_minutes.json."""
    hs = subprocess.run(["git", "-C", mirror, "log", "--format=%H", "--", "nba_minutes.json"], capture_output=True, text=True).stdout.split()
    out = {}
    for h in hs:
        doc = json.loads(subprocess.run(["git", "-C", mirror, "show", h + ":nba_minutes.json"], capture_output=True, text=True).stdout)
        games = doc.get("games", {})
        for p in doc.get("players", []):
            for g in p.get("g", []):
                if len(g) < 4 or g[0] not in games:
                    continue
                gm = games[g[0]]
                out.setdefault((gm["d"], nc.daily.norm_name(p["name"]), p["team"]), (g[3], 2880))
    return out


def points_at(stints, frac, length):
    t, pts = frac * length, 0.0
    for s in stints:
        if len(s) < 3:
            continue
        a, b, x = s
        if t >= b:
            pts += x
        elif t > a:
            pts += x * (t - a) / (b - a)
    return pts


def night(date, mins, proj="morning"):
    contests, teams = nc.load_night(date)
    c = max(contests, key=lambda c: int(c["entries"]))
    ts = teams[c["contest_id"]]
    path = os.path.join(nc.DAILY, "%s_%s.csv" % (date, c["slate"].replace("nba_", "")))
    rows = {r["player_id"]: r for r in nc.csv.DictReader(open(path))}
    pids = sorted({p for t in ts for p in t["picks"]})
    ix = {p: i for i, p in enumerate(pids)}
    usual, final, played, stint = np.zeros(len(pids)), np.zeros(len(pids)), np.zeros(len(pids), bool), [None] * len(pids)
    for p, i in ix.items():
        r = rows.get(p)
        if not r:
            continue
        um, pm = float(r["usual_min"] or 0), float(r["fp_pm"] or 0)
        usual[i] = float(r["etr_median"]) if proj == "etr" and r["etr_median"] else um * pm
        final[i] = float(r["actual"] or 0)
        played[i] = bool(r["min"]) and float(r["min"]) > 0
        m = mins.get((date, nc.daily.norm_name(r["name"]), r["team"]))
        stint[i] = m[0] if m else None
    tm = np.full((len(ts), 6), -1)
    for k, t in enumerate(ts):
        for j, p in enumerate(t["picks"][:6]):
            tm[k, j] = ix[p]
    place = np.array([t["place"] for t in ts])
    mine = np.array([t["username"] == nc.ME for t in ts])
    have = float((usual > 0)[played].mean()) if played.any() else 0
    return {"date": date, "pod": int(c["pod_size"]), "have": have, "tm": tm, "place": place, "mine": mine, "usual": usual,
            "final": final, "played": played, "stint": stint, "matched": sum(s is not None for s in stint) / max(1, int(played.sum()))}


def chances(n, frac, k, rng):
    """Each lineup's share of SIMS draws in the top 1%, with every game stopped at frac."""
    np_ = len(n["usual"])
    now = np.zeros(np_)
    for i in range(np_):
        if frac > 0 and n["played"][i]:
            now[i] = points_at(n["stint"][i], frac, 2880) if n["stint"][i] is not None else frac * n["usual"][i]   # no peeking
    left = (1 - frac) * n["usual"]
    left[(frac > 0) & ~n["played"]] = 0                    # out once his game has started
    sd = k * np.sqrt(np.maximum(n["usual"], 0)) * math.sqrt(1 - frac)
    sd[left == 0] = 0
    tm, nt = n["tm"], len(n["tm"])
    cut = math.ceil(nt / 100)
    hit = np.zeros(nt)
    for s0 in range(0, SIMS, 50):
        draws = now + np.maximum(-now, left + sd * rng.standard_normal((50, np_)))          # (50, players)
        draws = np.concatenate([draws, np.zeros((50, 1))], axis=1)                          # index -1: an empty slot
        tot = draws[:, tm].sum(axis=2)                                                      # (50, lineups)
        line = np.partition(tot, nt - cut, axis=1)[:, nt - cut][:, None]
        hit += (tot >= line).sum(axis=0)
    return hit / SIMS


def score(p, y):
    q = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-(y * np.log(q) + (1 - y) * np.log(1 - q)).mean()), float(((p - y) ** 2).mean())


def night_record(n, ks, rng):
    """One night's results for every (projection, K, point in the game): band counts and log-loss sums, kept so the
    pooled tables can be rebuilt from the store without replaying old nights."""
    y = (n["place"] <= math.ceil(len(n["tm"]) / 100)).astype(float)
    me, out = n["mine"], {}
    for k in ks:
        for f in AT:
            p = chances(n, f, k, rng)
            q = np.clip(p, 1e-4, 1 - 1e-4)
            ll = -(y * np.log(q) + (1 - y) * np.log(1 - q))
            bands = []
            for lo, hi in zip(BANDS, BANDS[1:]):
                s = (p >= lo) & (p < hi)
                bands.append([int(s.sum()), round(float(p[s].sum()), 3), int(y[s].sum()), int((s & me).sum()), int(y[s & me].sum())])
            out["%g|%g" % (k, f)] = {"ll": round(float(ll.sum()), 3), "n": len(p), "ll_mine": round(float(ll[me].sum()), 3),
                                     "n_mine": int(me.sum()), "bands": bands}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--k", default="1.6,2.0,3.0")
    a = ap.parse_args()
    ks = [float(x) for x in a.k.split(",")]
    path = os.path.join(nc.OUT, "live_calibration.json")
    store = json.load(open(path)) if os.path.exists(path) else {"nights": {}}
    mins = minutes_history(a.mirror)
    rng = np.random.default_rng(7)
    for d in sorted({c["date"] for c in nc.load_contests()}):
        if d in store["nights"]:
            continue
        rec = {}
        for proj in ("morning", "etr"):
            n = night(d, mins, proj)
            if n["have"] < 0.8 or n["matched"] < 0.9:      # no usuals (opening night), or its stints aren't in this mirror
                rec = None
                break
            rec[proj] = night_record(n, ks, rng)
        if rec is None:
            print("%s: skipped (usuals for %.0f%%, stints for %.0f%% of the players who played)" % (d, 100 * n["have"], 100 * n["matched"]))
            continue
        rec["lineups"], rec["mine"] = len(n["tm"]), int(n["mine"].sum())
        store["nights"][d] = rec
        print("%s: %d lineups, %d mine" % (d, rec["lineups"], rec["mine"]), flush=True)
    # pooled over every night kept
    pooled = {}
    for proj in ("morning", "etr"):
        for key in sorted({k for r in store["nights"].values() for k in r.get(proj, {})}):
            rs = [r[proj][key] for r in store["nights"].values() if key in r.get(proj, {})]
            bands = np.sum([r["bands"] for r in rs], axis=0).tolist()
            n, nm = sum(r["n"] for r in rs), sum(r["n_mine"] for r in rs)
            pooled["%s|%s" % (proj, key)] = {"nights": len(rs), "log_loss": round(sum(r["ll"] for r in rs) / n, 5),
                                            "mine_log_loss": round(sum(r["ll_mine"] for r in rs) / nm, 5) if nm else None,
                                            "bands": [{"band": [lo, min(hi, 1)], "lineups": b[0],
                                                       "predicted": round(b[1] / b[0], 4) if b[0] else None,
                                                       "actual": round(b[2] / b[0], 4) if b[0] else None,
                                                       "mine": b[3], "mine_actual": round(b[4] / b[3], 4) if b[3] else None}
                                                      for (lo, hi), b in zip(zip(BANDS, BANDS[1:]), bands) if b[0]]}
    store["pooled"] = pooled
    json.dump(store, open(path, "w"), indent=1)
    print("\nlog loss over %d nights (lower is better), all lineups" % len(store["nights"]))
    for proj in ("morning", "etr"):
        for f in AT:
            print("  %-7s stopped at %3.0f%%: " % (proj, 100 * f) + "  ".join(
                "K %g %.4f" % (k, pooled["%s|%g|%g" % (proj, k, f)]["log_loss"]) for k in ks if "%s|%g|%g" % (proj, k, f) in pooled))
    for proj, k, f in (("etr", 3.0, 0.25), ("etr", 2.0, 0.5), ("etr", 2.0, 0.75)):
        key = "%s|%g|%g" % (proj, k, f)
        if key in pooled:
            print("\n%s, K %g, stopped at %d%%: predicted band -> lineups, predicted, actual top-1%%" % (proj, k, 100 * f))
            for b in pooled[key]["bands"]:
                print("  %5.1f-%5.1f%%: %7d  %6.2f%%  %6.2f%%   (mine %d)" % (100 * b["band"][0], 100 * b["band"][1], b["lineups"],
                                                                     100 * b["predicted"], 100 * b["actual"], b["mine"]))


if __name__ == "__main__":
    main()
