"""Sit risk: each player's chance to play, before lock (2026-11-21, the operator's approval of step B's flag; the model
and its test: scripts/dk_dnp_study.py, analysis/cbb/dk/dnp_2026-11-21.md). Display only: it moves no projection, field
or draw. The pipeline (battle-royale-research scripts/cbb_nightly.py) writes p_play and p_play_why on every card from
sit_model.json; the DK page tags in-pool players with no Q / D / Out status under FLAG_P as "sit risk".

The model: a small L2 logistic fit of played (real minutes > 0) on what the card holds before lock (features() below,
the one definition: the card, the training rows and the study all use it). Fitted on every graded slate to date, refit
nightly as box scores arrive; its leave-one-slate-out Brier against the current implied chance (0 Out, the gate's Q
factor, else 1) is kept in the model file as the running check.

Files (analysis/cbb/dk/):
  sit_train.csv   every graded slate's players not Out, at lock: the features, played and real minutes
  sit_model.json  the weights, the features' means (for the why), the slates fitted and the held-out Brier
  sit_log.csv     every flag on a lock card that carried p_play: date, slate, player, p_play, why, salary, the pool basis
                  (the page's default pool, or the build's excludes / deep-bench picks when a build is on file), his bank
                  share at lock (with a build), played and minutes. Rebuilt whole each night (a build added later counts)
  sit_log.md      the report by week: flagged, sat, hit rate against the mean p_play, what the flagged sitters cost the banks

  python3 scripts/dk_sit.py nightly --mirror ../br-adp-mirror    the nightly workflow: train, fit, log, report
"""
import argparse, csv, datetime as dt, glob, json, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
TRAIN, MODEL, LOG, REPORT = (os.path.join(DK, f) for f in ("sit_train.csv", "sit_model.json", "sit_log.csv", "sit_log.md"))
FEATS = ["const", "logmin", "depth", "part", "gmiss", "known", "miss5", "misslast", "days", "q", "thin", "touts"]
FLAG_P = 0.70          # the page's tag: in-pool, no Q / D / Out status, p_play under this
PUNT_MIN = 15          # the page's punt line (dk.html PUNT_MIN): projected under it, out of the pool without news
ZERO_GP_TEAM = 3       # cbb_nightly's zero-games group: 0 games this season, his team 3+; its factor is refit here (zero_gp_f)
ZERO_GP_MIN_N = 20     # player-slates before the refit replaces cbb_nightly's ZERO_GP_F
num = lambda v: float(v) if v not in ("", None) else None


def features(players, date):
    """players: [{id, team, status, min_proj, min_avg, gp, last5, src}], one slate's cards at lock (last5: [[date, min,
    pts], ...]); date: the slate's day (YYYY-MM-DD). -> {id: (x, raw)} for every player not Out: x the FEATS vector,
    raw the readable values behind it (for the why)."""
    team = {}
    for p in players:
        team.setdefault(p["team"], []).append(p)
    out = {}
    for t, ps in team.items():
        live = sorted([p for p in ps if p.get("status") != "Out"], key=lambda p: -(p.get("min_proj") or 0))
        tg = max([p.get("gp") or 0 for p in ps] + [0])
        touts = sum(1 for p in ps if p.get("status") == "Out" and ((p.get("min_proj") or p.get("min_avg") or 0) >= 15))
        dates = sorted({x[0] for p in ps for x in (p.get("last5") or []) if isinstance(x, list)})[-5:]
        for k, p in enumerate(live):
            gp = p.get("gp") or 0
            l5 = [x[0] for x in (p.get("last5") or []) if isinstance(x, list)]
            miss5 = sum(1 for x in dates if x not in l5) if dates else 0
            misslast = 1.0 if dates and dates[-1] not in l5 else 0.0
            days = min(21, (dt.date.fromisoformat(date) - dt.date.fromisoformat(l5[-1])).days) if l5 else (21 if dates else 0)
            thin = 1.0 if (p.get("src") != "box" or gp < 3) else 0.0
            x = {"const": 1.0, "logmin": math.log1p(p.get("min_proj") or 0), "depth": min(k + 1, 12) / 12, "part": gp / tg if tg else 0.0,
                 "gmiss": min(5, tg - gp) if tg else 0.0, "known": 1.0 if dates else 0.0, "miss5": miss5 / 5, "misslast": misslast,
                 "days": days / 21, "q": 1.0 if p.get("status") == "Questionable" else 0.0, "thin": thin, "touts": min(touts, 3) / 3}
            raw = {"min": p.get("min_proj") or 0, "rank": k + 1, "gp": gp, "tg": tg, "miss5": miss5, "n5": len(dates),
                   "misslast": bool(misslast), "days": days if l5 else None, "thin": bool(thin), "touts": touts}
            out[p["id"]] = ([x[f] for f in FEATS], raw)
    return out


def predict(model, x):
    z = sum(w * v for w, v in zip(model["w"], x))
    return 1 / (1 + math.exp(-max(-30, min(30, z))))


PHRASE = {   # a feature lowering his chance, in words (the why keeps the three that lower it most)
    "logmin": lambda r: "projected %.0f min" % r["min"],
    "depth": lambda r: "#%d on his team by minutes" % r["rank"],
    "part": lambda r: "played %d of %d games" % (r["gp"], r["tg"]),
    "gmiss": lambda r: "missed %d of the team's games" % (r["tg"] - r["gp"]),
    "miss5": lambda r: "missed %d of last %d" % (r["miss5"], r["n5"]),
    "misslast": lambda r: "missed the last game",
    "days": lambda r: "last game %d days ago" % r["days"] if r["days"] is not None else "no game on file",
    "thin": lambda r: "thin sample (%d games)" % r["gp"],
    "touts": lambda r: "%d teammate%s out" % (r["touts"], "" if r["touts"] == 1 else "s"),
}


def why(model, x, raw):
    """The three features that lower his chance most against the training average, as ' · '-joined words."""
    c = []
    for i, f in enumerate(FEATS):
        if f not in PHRASE:
            continue
        d = model["w"][i] * (x[i] - model["mean"][i])
        if d < -0.05 and not (f == "misslast" and not raw["misslast"]) and not (f == "thin" and not raw["thin"]) and not (f == "miss5" and not raw["miss5"]):
            c.append((d, PHRASE[f](raw)))
    c = sorted(c)
    if any(t.startswith("played ") for _, t in c):        # "missed 5 of the team's games" says the same again
        c = [x for x in c if not x[1].startswith("missed %d of the team" % (raw["tg"] - raw["gp"]))]
    return " · ".join(t for _, t in c[:3])


def card_chances(model, players, date):
    """{id: (p_play, why)} for one slate's cards (the pipeline's call)."""
    return {i: (round(predict(model, x), 2), why(model, x, raw)) for i, (x, raw) in features(players, date).items()}


def card_players(cards):
    """A slate's cards (the pipeline's / the mirror's {id: card}) -> features()' players."""
    return [{"id": str(i), "team": c.get("team"), "status": c.get("status") or "", "min_proj": num(c.get("min")),
             "min_avg": num(c.get("min_avg")), "gp": c.get("gp") or 0, "last5": c.get("last5") or [], "src": c.get("src")} for i, c in cards.items()]


def load_model(path=MODEL):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return None


def fit(X, y, lam=1.0):
    """L2 logistic by Newton, the constant unpenalized (pure Python: the nightly runs without numpy)."""
    k = len(X[0]); w = [0.0] * k
    for _ in range(50):
        g = [-(lam * w[j] if j else 0.0) for j in range(k)]
        H = [[(lam if (i == j and i) else 0.0) for j in range(k)] for i in range(k)]
        for xv, yv in zip(X, y):
            p = 1 / (1 + math.exp(-max(-30, min(30, sum(a * b for a, b in zip(w, xv))))))
            r, q = yv - p, p * (1 - p)
            for i in range(k):
                g[i] += r * xv[i]
                if xv[i]:
                    qi = q * xv[i]
                    for j in range(k):
                        H[i][j] += qi * xv[j]
        step = solve(H, g)
        w = [a + b for a, b in zip(w, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return w


def solve(A, b):
    n = len(b); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-12:
            continue
        for r in range(n):
            if r != c and M[r][c]:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * b2 for a, b2 in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


# --- the nightly: train, fit, log ----------------------------------------------------------------------------------
def lock_doc(mirror, fname, date, g, start=None):
    """The slate's entry in the mirror's fname just before lock (the first game: the morning card's start, or start),
    and the lock time: (entry, start), entry None when the mirror has no version before it. Newest version first, as
    scripts/dk_q_missed_study.py finds the lock card."""
    from nba_daily import Mirror, iso
    Mi = lock_doc.M = getattr(lock_doc, "M", None) or Mirror(mirror)
    day = iso(date + "T00:00:00Z")
    for t, sha in reversed(Mi.versions(fname, day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
        sl = Mi.show(sha, fname).get("slates")
        x = sl.get(g) if isinstance(sl, dict) else next((e for e in (sl or []) if str(e.get("draft_group_id")) == g), None)
        if not x:
            continue
        if start is None and x.get("start"):
            start = iso(x["start"])
        if start is not None and t < start:
            return x, start
    return None, start


def graded():
    """[(date, draft group, rows)] for every graded slate file (real minutes in)."""
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        b = os.path.basename(f)[:-4]
        rows = list(csv.DictReader(open(f)))
        if rows and any(r.get("actual_dk") not in ("", None) for r in rows):
            out.append((b[:10], b[11:], rows))
    return out


def train(mirror):
    have = set()
    old = list(csv.DictReader(open(TRAIN))) if os.path.exists(TRAIN) else []
    for r in old:
        have.add((r["date"], r["draft_group"]))
    new = []
    for date, g, rows in graded():
        if (date, g) in have:
            continue
        sl, _ = lock_doc(mirror, "dk_cbb_morning.json", date, g)
        if not sl:
            print("sit: no lock card for %s %s on the mirror (outside its history?): not trained" % (date, g)); continue
        P = sl.get("players") or {}
        players = [{"id": r["dk_id"], "team": r["team"], "status": r.get("status") or "", "min_proj": num(r.get("min_proj")), "min_avg": num(r.get("min_avg")),
                    "gp": (P.get(r["dk_id"]) or {}).get("gp") or 0, "last5": (P.get(r["dk_id"]) or {}).get("last5") or [], "src": r.get("src")} for r in rows]
        F = features(players, date); by = {r["dk_id"]: r for r in rows}
        for i, (x, raw) in F.items():
            r = by[i]; z = (P.get(i) or {}).get("zero_gp") or {}
            # the zero-games group (cbb_nightly ZERO_GP_TEAM) and his projection before that fix (its orig once it is live)
            new.append(dict({"date": date, "draft_group": g, "dk_id": i, "name": r["name"], "team": r["team"], "salary": r["salary"], "status": r.get("status") or "",
                             "min_proj": r.get("min_proj"), "played": 1 if (num(r.get("min")) or 0) > 0 else 0, "min": r.get("min") or "",
                             "zero_gp": 1 if (raw["gp"] == 0 and raw["tg"] >= ZERO_GP_TEAM) else 0,
                             "fp_raw": (z.get("orig") or {}).get("fp_dk", r.get("fp_dk")), "actual_dk": r.get("actual_dk")},
                            **{f: round(v, 6) for f, v in zip(FEATS, x)}))
        print("sit: trained %s %s (%d players)" % (date, g, len(F)))
    if new:
        rows = old + new
        with open(TRAIN, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(new[0].keys()), restval=""); w.writeheader(); w.writerows(rows)
    return old + new


def qf():
    try:
        return json.load(open(os.path.join(DK, "gate.json")))["questionable"]["factor"]
    except (OSError, ValueError, KeyError):
        return 1.0


def refit(rows):
    X = [[float(r[f]) for f in FEATS] for r in rows]; y = [int(r["played"]) for r in rows]
    w = fit(X, y)
    sl = sorted({(r["date"], r["draft_group"]) for r in rows}); Q = qf()
    # held out by slate: the running check that the model still beats the current implied chance
    bm, bc, n = 0.0, 0.0, 0
    for s in sl:
        tr = [i for i, r in enumerate(rows) if (r["date"], r["draft_group"]) != s]
        if len({(rows[i]["date"], rows[i]["draft_group"]) for i in tr}) < 2:
            continue
        ws = fit([X[i] for i in tr], [y[i] for i in tr]); m = {"w": ws}
        for i, r in enumerate(rows):
            if (r["date"], r["draft_group"]) == s:
                cur = Q if r["status"] == "Questionable" else 1.0
                bm += (predict(m, X[i]) - y[i]) ** 2; bc += (cur - y[i]) ** 2; n += 1
    model = {"feats": FEATS, "w": [round(v, 6) for v in w], "mean": [round(S.mean(x[j] for x in X), 6) for j in range(len(FEATS))],
             "flag_p": FLAG_P, "n": len(rows), "slates": ["%s_%s" % s for s in sl], "fitted_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
             "heldout_brier": {"model": round(bm / n, 4) if n else None, "current": round(bc / n, 4) if n else None, "n": n}}
    # the zero-games factor: their real DK points over their projection before the fix (actual / projected, the mean-
    # correct scale, as the Questionable factor); cbb_nightly reads it, ZERO_GP_F until ZERO_GP_MIN_N player-slates
    z = [r for r in rows if str(r.get("zero_gp")) == "1" and num(r.get("fp_raw")) and r.get("actual_dk") not in ("", None)]
    if len(z) >= ZERO_GP_MIN_N:
        model["zero_gp_f"] = round(sum(num(r["actual_dk"]) for r in z) / sum(num(r["fp_raw"]) for r in z), 4)
    model["zero_gp_n"] = len(z)
    json.dump(model, open(MODEL, "w"), indent=1)
    print("sit: model fitted on %d players, %d slates; held-out Brier %s vs current %s; zero-games factor %s on %d" % (
        len(rows), len(sl), model["heldout_brier"]["model"], model["heldout_brier"]["current"], model.get("zero_gp_f"), model["zero_gp_n"]))
    return model


def in_pool(c, cards, deep, excl, deep_in):
    """The page's default pool for a no-status player (dk.html usable / isPunt / deepIds, with no operator state but a
    build's excludes and deep-bench picks when one is on file)."""
    i = c["id"]
    if i in excl:
        return False
    if i in deep and i not in deep_in:
        return False
    m = num(c.get("min")) or 0
    if m >= PUNT_MIN or i in deep_in:
        return True
    news = any(x.get("team") == c.get("team") and x.get("status") == "Out" for x in cards.values())
    return bool(news and c.get("min_avg") is not None and m > c["min_avg"])


def log(mirror):
    out = []
    for date, g, rows in graded():
        sl, start = lock_doc(mirror, "dk_cbb_morning.json", date, g)
        P = (sl or {}).get("players") or {}
        if not any("p_play" in c for c in P.values()):
            continue                     # the card carried no p_play then: nothing was shown
        tsl, _ = lock_doc(mirror, "dk_cbb_teams.json", date, g, start)
        deep = {i for t in ((tsl or {}).get("teams") or []) for i in ((t.get("card") or {}).get("deep") or [])}
        bf = os.path.join(DK, "builds", "dk_bank_%s_%s.json" % (date, g))
        B = json.load(open(bf)) if os.path.exists(bf) else None
        op = (B or {}).get("operator") or {}
        excl, deep_in = set((op.get("excl") or {}).keys()), set((op.get("deep_in") or {}).keys())
        pool = (B or {}).get("pool") or []
        act = {r["dk_id"]: r for r in rows}
        cards = {i: dict(c, id=i) for i, c in P.items()}
        for i, c in cards.items():
            p = c.get("p_play")
            if p is None or p >= FLAG_P or c.get("status") or not in_pool(c, cards, deep, excl, deep_in):
                continue
            a = act.get(i) or {}
            out.append({"date": date, "draft_group": g, "dk_id": i, "name": c.get("name"), "team": c.get("team"), "salary": c.get("salary"),
                        "p_play": p, "why": c.get("p_play_why") or "", "pool_basis": "build" if B else "default",
                        "bank_share": round(sum(1 for L in pool if i in L) / len(pool), 4) if pool else "",
                        "played": (1 if (num(a.get("min")) or 0) > 0 else 0) if a else "", "min": a.get("min", "")})
    cols = ["date", "draft_group", "dk_id", "name", "team", "salary", "p_play", "why", "pool_basis", "bank_share", "played", "min"]
    with open(LOG, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(out)
    report(out)
    print("sit: %d flags logged" % len(out))


def report(rows):
    """By ISO week: flagged, sat, the hit rate (share who sat) against 1 - the mean p_play, and the sitters' cost to the
    banks (their mean bank share where a build is on file)."""
    L = ["# Sit-risk flags: the running report", "",
         "Generated by `scripts/dk_sit.py nightly`. A flag: in the draw's pool, no Q / D / Out status, p_play under %.2f on the lock card. "
         "Hit rate: the share of flagged players who sat; the model expects 1 - mean p_play. Cost: the flagged sitters' mean share of the bank "
         "(slates with a build on file). Thin until a few weeks are in; the operator decides after two weeks." % FLAG_P, "",
         "| Week | Flagged | Sat | Hit rate | Expected (1 - mean p) | Sitters with a build | Their mean bank share |", "|---|---|---|---|---|---|---|"]
    wk = {}
    for r in rows:
        if r["played"] == "":
            continue
        y, w, _ = dt.date.fromisoformat(r["date"]).isocalendar()
        wk.setdefault("%d-W%02d" % (y, w), []).append(r)
    for k in sorted(wk):
        rs = wk[k]; sat = [r for r in rs if r["played"] == 0]; sb = [r["bank_share"] for r in sat if r["bank_share"] != ""]
        L.append("| %s | %d | %d | %.0f%% | %.0f%% | %d | %s |" % (k, len(rs), len(sat), 100 * len(sat) / len(rs), 100 * (1 - S.mean(r["p_play"] for r in rs)),
                                                             len(sb), "%.1f%%" % (100 * S.mean(sb)) if sb else "–"))
    if not wk:
        L.append("| – | 0 | 0 | – | – | 0 | – |")
    open(REPORT, "w").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nightly"); n.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    rows = train(a.mirror)
    if rows:
        refit(rows)
    log(a.mirror)


if __name__ == "__main__":
    main()
