"""NBA contests: every team in every tournament on the night's main slate, and the field measures built on them.

Underdog's leaderboards are public once a contest locks: each team's username, place, points,
payout, its six picks and the ADP each pick was taken at, and the draft (pod) it came from.
Contest ids come from the ADP poller, which keeps each slate's open contests from the lobby
(the mirror's slates carry them as `contests`); analysis/nba/contests/seed.json adds ones found
before that existed. Pick order, draft slot and pick times are not public, so rounds here are
estimated: a pod's 36 picks sorted by the ADP each was taken at.

  pull      every main-slate contest that locked in the last --days (default 3) and isn't on file:
            analysis/nba/contests/<date>_<contest id>.csv.gz, one row per team (a pod's teams together,
            picks in ADP-at-draft order), and a row per contest in contests.csv
  measures  for a night (--date, default every night on file): the measures below, printed and kept
            in analysis/nba/contests/<date>_measures.json (with my teams one by one: picks, place, inferred draft time)
  seed      add contest ids (arguments) to seed.json, for contests the lobby never caught

  python3 scripts/nba_contests.py pull|measures|seed [ids...] --mirror ../br-adp-mirror [--date YYYY-MM-DD]

Definitions (the shared spec): drafted% = pods a player was drafted in / pods (ownership is that over
the pod size); top X% = rank <= ceil(X% of entries), never pooled across contests; a breaker scored at
least the 90th percentile of the players in his ADP round band that night; FPOE = fantasy points over
the average for his ADP round band across every night on file.
"""
import argparse, csv, datetime as dt, glob, gzip, itertools, json, math, os, sys, time, urllib.request
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import nba_daily as daily   # noqa: E402  the mirror's history and Pacific days, as the nightly record reads them

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "nba")
OUT = os.path.join(HERE, "contests")
DAILY = os.path.join(HERE, "daily")
API = "https://api.underdogfantasy.com/v1"
Q = "product=fantasy&product_experience_id=c7ade3c1-71ae-4593-a7e1-07f63c7e94ae&state_config_id=725014ef-3570-4e93-871d-d69674ab3521"
ME = "jonboybeats"
PT = ZoneInfo("America/Los_Angeles")
AM_UNTIL = 12               # a team drafted before noon Pacific is an AM team
TOPS = (1, 5, 10, 20)
TEAM_COLS = ["contest_id", "draft_id", "username", "place", "points", "payout", "tied"] + \
            ["p%d" % i for i in range(1, 7)] + ["adp%d" % i for i in range(1, 7)]
CONTEST_COLS = ["date", "slate", "slate_id", "contest_id", "title", "description", "max_entries", "entries",
                "pods", "pod_size", "cutoff", "pulled_at"]


def get(path):
    url = API + path + ("&" if "?" in path else "?") + Q
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "br-rankings/1.0"}), timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == 3:
                raise
            print("  retry %s: %r" % (path.split("?")[0], e), flush=True)
            time.sleep(3 * (i + 1))


# ---------------------------------------------------------------- finding the night's contests
def main_slates(mirror, days):
    now = dt.datetime.now(dt.timezone.utc)
    return mirror.main_slates(now - dt.timedelta(days=days), now)


def mirror_contests(mirror, slate):
    """{contest id: the lobby's record} for a slate, from every mirror version while it was open."""
    found = {}
    for _, sha in mirror.versions("nba_latest.json", slate["lock"] - dt.timedelta(hours=48), slate["lock"]):
        for s in mirror.show(sha, "nba_latest.json").get("slates", []):
            if s["slate_id"] == slate["slate_id"]:
                for c in s.get("contests") or []:
                    found[c["id"]] = c
    return found


def appearance_map(mirror, slate):
    """{appearance id: player id} for a slate: its priced players and its pool file, every version."""
    out = {}
    for _, sha in mirror.versions("nba_latest.json", slate["lock"] - dt.timedelta(hours=48), slate["lock"]):
        for s in mirror.show(sha, "nba_latest.json").get("slates", []):
            if s["slate_id"] != slate["slate_id"]:
                continue
            for p in s.get("players") or []:
                out[p["appearance_id"]] = p["player_id"]
            if s.get("pool"):
                try:
                    for p in mirror.show(sha, s["pool"]).get("players", []):
                        if p.get("appearance_id"):
                            out[p["appearance_id"]] = p["player_id"]
                except Exception:
                    pass
    return out


def load_contests():
    path = os.path.join(OUT, "contests.csv")
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def save_contests(rows):
    rows = sorted(rows, key=lambda r: (r["date"], r["slate"], -int(r["entries"] or 0)))
    with open(os.path.join(OUT, "contests.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CONTEST_COLS)
        w.writeheader()
        w.writerows(rows)


def pull_contest(cid, slate, amap):
    pool = get("/draft_pools/%s" % cid)["draft_pool"]
    if pool.get("status") not in ("settled", "closed", "completed"):
        print("  %s %s: status %s, not settled yet; later" % (cid, pool.get("title"), pool.get("status")))
        return None
    entries, page = [], 1
    while page:
        d = get("/draft_pools/%s/leaderboard?page=%d" % (cid, page))
        entries += d["draft_pool_entries"]
        page = d["meta"].get("next")
        time.sleep(0.4)
    rows, missing = [], set()
    for e in entries:
        picks = []
        for a in e["appearance_ids"]:
            adp = (e.get("pick_adps") or {}).get(a)
            if a not in amap:
                missing.add(a)
            picks.append((float(adp) if adp not in (None, "") else 99.0, amap.get(a, "app:" + a)))
        picks.sort()
        rows.append(dict({"contest_id": cid, "draft_id": e["draft_id"], "username": (e.get("username") or "").lower(),
                          "place": e["place"], "points": e["points"], "payout": e["payout"], "tied": int(bool(e.get("tied")))},
                         **{"p%d" % (i + 1): p for i, (_, p) in enumerate(picks)},
                         **{"adp%d" % (i + 1): ("" if a == 99.0 else a) for i, (a, _) in enumerate(picks)}))
    day = daily.pacific_day(slate["lock"])
    rows.sort(key=lambda r: (r["draft_id"], r["place"]))      # a pod's teams together: the file packs to about half
    with gzip.open(os.path.join(OUT, "%s_%s.csv.gz" % (day, cid)), "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TEAM_COLS)
        w.writeheader()
        w.writerows(rows)
    pods = Counter(r["draft_id"] for r in rows)
    print("  %s %s: %d teams, %d pods%s" % (day, pool["title"], len(rows), len(pods),
                                          "; %d picks with no player id" % len(missing) if missing else ""), flush=True)
    return {"date": day, "slate": slate["label"], "slate_id": slate["slate_id"], "contest_id": cid, "title": pool["title"].strip(),
            "description": pool.get("description") or "", "max_entries": pool.get("max_entries"), "entries": len(rows),
            "pods": len(pods), "pod_size": Counter(pods.values()).most_common(1)[0][0], "cutoff": pool.get("cutoff_at"),
            "pulled_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def pull(mirror, days):
    os.makedirs(OUT, exist_ok=True)
    have = {r["contest_id"] for r in load_contests()}
    rows = load_contests()
    seed = json.load(open(os.path.join(OUT, "seed.json"))) if os.path.exists(os.path.join(OUT, "seed.json")) else []
    seed_by_slate = defaultdict(list)
    for cid in seed:
        if cid not in have:
            seed_by_slate[get("/draft_pools/%s" % cid)["draft_pool"]["slate_id"]].append(cid)
    for slate in main_slates(mirror, max(days, 30 if seed_by_slate else days)):
        ids = set(mirror_contests(mirror, slate)) | set(seed_by_slate.get(slate["slate_id"], []))
        todo = sorted(ids - have)
        if not todo:
            continue
        amap = appearance_map(mirror, slate)
        print("%s %s: %d contest(s) to pull" % (slate["label"], slate["lock"].isoformat(), len(todo)), flush=True)
        for cid in todo:
            r = pull_contest(cid, slate, amap)
            if r:
                rows.append(r)
                save_contests(rows)


# ---------------------------------------------------------------- the measures
def load_night(date):
    contests = [c for c in load_contests() if c["date"] == date]
    teams = {}
    for c in contests:
        with gzip.open(os.path.join(OUT, "%s_%s.csv.gz" % (date, c["contest_id"])), "rt") as f:
            teams[c["contest_id"]] = [dict(r, points=float(r["points"]), place=int(r["place"]), payout=float(r["payout"] or 0),
                                           picks=[r["p%d" % i] for i in range(1, 7) if r["p%d" % i]],
                                           adps=[float(r["adp%d" % i]) if r["adp%d" % i] else None for i in range(1, 7)])
                                      for r in csv.DictReader(f)]
    return contests, teams


def players_on(date, label):
    path = os.path.join(DAILY, "%s_%s.csv" % (date, label.replace("nba_", "")))
    out = {}
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            out[r["player_id"]] = {"name": r["name"], "team": r["team"], "adp": float(r["adp_close"]) if r["adp_close"] else None,
                                   "fp": float(r["actual"]) if r["actual"] else None}
    return out


def band_means(pod):
    """Average fantasy points by ADP round band (closing ADP) over every main-slate night on file."""
    by = defaultdict(list)
    for path in glob.glob(os.path.join(DAILY, "*_main.csv")):
        for r in csv.DictReader(open(path)):
            if r["adp_close"] and r["actual"]:
                by[math.ceil(float(r["adp_close"]) / pod)].append(float(r["actual"]))
    return {b: sum(v) / len(v) for b, v in by.items()}


def pct(x):
    return round(100 * x, 1)


def cut_lines(teams):
    pts = sorted((t["points"] for t in teams), reverse=True)
    n, med = len(pts), pts[len(pts) // 2]
    out = {"entries": n, "win": pts[0], "median": med}
    for x in TOPS:
        k = math.ceil(x * n / 100)
        out["top%d" % x] = pts[k - 1]
        out["top%d_over_median" % x] = round(pts[k - 1] - med, 2)
    return out


def drafted(teams, pod):
    pods = defaultdict(set)
    for t in teams:
        pods[t["draft_id"]].update(t["picks"])
    n = len(pods)
    c = Counter(p for s in pods.values() for p in s)
    return {p: k / n for p, k in c.items()}, n


def day_ranks(info):
    """{player id: rank by the night's closing ADP}: the order the slate was priced in at lock."""
    priced = sorted((r["adp"], p) for p, r in info.items() if r["adp"] is not None)
    return {p: i + 1 for i, (_, p) in enumerate(priced)}


def pair_counts(teams):
    """(teams carrying each pair, pods drafting both) and the lift baseline: given both were drafted in a pod,
    the chance they share a team if the pod's picks went to teams at random, 5/(6*pod - 1). Pick order isn't
    public, so the snake's turns are part of the lift: a turn pair the field lands on often shows well over 1."""
    share, both, by_pod = Counter(), Counter(), defaultdict(set)
    for t in teams:
        for k in itertools.combinations(sorted(t["picks"]), 2):
            share[k] += 1
        by_pod[t["draft_id"]].update(t["picks"])
    for ps in by_pod.values():
        for k in itertools.combinations(sorted(ps), 2):
            both[k] += 1
    return share, both


def pairs_and_cores(teams, pod, rank, names, share, both):
    n, together = len(teams), 5 / (6 * pod - 1)
    rnd = lambda p: math.ceil(rank[p] / pod) if p in rank else 0
    pairs = []
    for k, v in share.most_common(400):
        a, b = sorted(k, key=lambda p: rank.get(p, 999))
        pairs.append({"pair": "%s + %s" % (names(a), names(b)), "rounds": "%s/%s" % (rnd(a) or "?", rnd(b) or "?"),
                      "share": pct(v / n), "lift": round(v / (both[k] * together), 2)})
    cores = Counter(tuple(sorted(t["picks"][:3])) for t in teams)
    core_rows = [{"core": " + ".join(names(p) for p in k), "share": pct(v / n)} for k, v in cores.most_common(15)]
    return pairs, core_rows


def turns(teams, pod, rank, names, share, both):
    """The turns, by the night's closing-ADP ranks (no pick order needed):
    1/2 turn: pairs of players both ranked pod-1..pod+2 (5-8 in 6-person pods), the picks around the turn;
    2/3 turn: for each of the top 3 by ADP, the two round 2-3 players (ranks pod+1..3*pod) his teams paired
    him with. Each combo: share of teams (2/3: of the anchor's teams too), lift where it's a pair, how many
    made the top 1%, and the teams' average points: a description of what happened, not a rule."""
    n, together, cut = len(teams), 5 / (6 * pod - 1), math.ceil(len(teams) / 100)
    def outcome(ts):
        return {"top1": sum(1 for t in ts if t["place"] <= cut), "avg_points": round(sum(t["points"] for t in ts) / len(ts), 1)}
    lo, hi = pod - 1, pod + 2
    window = {p for p, r in rank.items() if lo <= r <= hi}
    t12 = []
    for k, v in share.items():
        if k[0] in window and k[1] in window:
            a, b = sorted(k, key=lambda p: rank[p])
            ts = [t for t in teams if a in t["picks"] and b in t["picks"]]
            t12.append(dict({"pair": "%s (%d) + %s (%d)" % (names(a), rank[a], names(b), rank[b]), "share": pct(v / n),
                             "lift": round(v / (both[k] * together), 2)}, **outcome(ts)))
    t12.sort(key=lambda r: -r["share"])
    t23 = []
    for anchor in sorted((p for p, r in rank.items() if r <= 3), key=lambda p: rank[p]):
        ts = [t for t in teams if anchor in t["picks"]]
        if not ts:
            continue
        combos = defaultdict(list)
        for t in ts:
            mid = sorted((p for p in t["picks"] if pod + 1 <= rank.get(p, 0) <= 3 * pod), key=lambda p: rank[p])
            for k in itertools.combinations(mid, 2):
                combos[k].append(t)
        rows = [dict({"combo": "%s + %s (%d) + %s (%d)" % (names(anchor), names(a), rank[a], names(b), rank[b]),
                      "of_anchor": pct(len(c) / len(ts)), "share": pct(len(c) / n)}, **outcome(c))
                for (a, b), c in sorted(combos.items(), key=lambda x: -len(x[1]))[:8]]
        t23.append({"anchor": names(anchor), "adp_rank": rank[anchor], "teams": len(ts), "combos": rows})
    return {"turn_1_2_ranks": [lo, hi], "turn_1_2": t12[:12], "turn_2_3": t23}


def uniqueness(teams):
    mine = [t for t in teams if t["username"] == ME]
    if not mine:
        return None
    field = [frozenset(t["picks"]) for t in teams if t["username"] != ME]
    exact, own = Counter(field), Counter(frozenset(t["picks"]) for t in mine)
    rows = []
    for t in mine:
        s = frozenset(t["picks"])
        rows.append({"share4": sum(1 for o in field if len(s & o) >= 4), "dupes": exact[s], "own": own[s] - 1})
    n = len(teams)
    my_pairs = Counter(p for t in mine for p in itertools.combinations(sorted(t["picks"]), 2))
    my_cores = Counter(tuple(sorted(t["picks"][:3])) for t in mine)
    return {"teams": len(mine),
            "share4_median": pct(sorted(r["share4"] for r in rows)[len(rows) // 2] / n),
            "share4_max": pct(max(r["share4"] for r in rows) / n),
            "teams_with_dupes": sum(1 for r in rows if r["dupes"]),          # someone else has the same six
            "repeats_of_mine": sum(1 for r in rows if r["own"]),             # another of my own teams has them
            "top_pairs": my_pairs.most_common(5), "top_cores": my_cores.most_common(5)}


def draft_times(teams, snaps):
    """Each team's nearest ADP snapshot to the ADPs its picks were taken at."""
    if not snaps:
        return {}
    tables = [(t, {p["player_id"]: p["adp"] for p in ps}) for t, ps in snaps]
    out = {}
    for tm in teams:
        best = None
        for t, tab in tables:
            errs = [abs(a - tab[p]) for p, a in zip(tm["picks"], tm["adps"]) if a is not None and p in tab]
            if len(errs) >= 4:
                e = sum(errs) / len(errs)
                if best is None or e < best[0]:
                    best = (e, t)
        if best:
            out[id(tm)] = best[1]
    return out


def my_results(teams):
    mine = sorted(t["place"] for t in teams if t["username"] == ME)
    if not mine:
        return None
    n = len(teams)
    return {"teams": len(mine), "median_pct": pct(mine[len(mine) // 2] / n),
            **{"tail%d" % x: round(sum(1 for p in mine if p <= math.ceil(x * n / 100)) / len(mine) / (x / 100), 2) for x in TOPS},
            "payout": round(sum(t["payout"] for t in teams if t["username"] == ME), 2)}


def measures(mirror, date):
    contests, teams = load_night(date)
    if not contests:
        return None
    label, slate_id = contests[0]["slate"], contests[0]["slate_id"]
    info = players_on(date, label)
    names = lambda p: info.get(p, {}).get("name") or p[:8]
    rank = day_ranks(info)
    pod = int(contests[0]["pod_size"])
    means = band_means(pod)
    by_band = defaultdict(list)
    for p, r in info.items():
        if r["adp"] and r["fp"] is not None:
            by_band[math.ceil(r["adp"] / pod)].append(r["fp"])
    p90 = {b: sorted(v)[int(0.9 * (len(v) - 1))] for b, v in by_band.items()}
    def fpoe(p):
        r = info.get(p)
        return None if not r or r["fp"] is None or not r["adp"] else r["fp"] - means[math.ceil(r["adp"] / pod)]
    def breaker(p):
        r = info.get(p)
        return bool(r and r["fp"] is not None and r["adp"] and r["fp"] >= p90[math.ceil(r["adp"] / pod)])
    lock = next((s for s in mirror.main_slates(dt.datetime.fromisoformat(date + "T00:00:00+00:00") - dt.timedelta(days=1),
                                               dt.datetime.fromisoformat(date + "T00:00:00+00:00") + dt.timedelta(days=2))
                 if s["slate_id"] == slate_id), None)
    snaps = mirror.snapshots(lock) if lock else []
    out = {"date": date, "slate": label, "contests": []}
    for c in contests:
        ts = teams[c["contest_id"]]
        d, npods = drafted(ts, pod)
        curve = sorted(({"player": names(p), "adp": info.get(p, {}).get("adp"), "drafted": pct(v)} for p, v in d.items()),
                       key=lambda r: r["adp"] if r["adp"] is not None else 999)
        # the first priced player the field left in some pods (under 10% reads as news: ruled out, not faded)
        below = next((r for r in curve if 10 <= r["drafted"] < 99.5 and r["adp"] is not None), None)
        share, both = pair_counts(ts)
        pairs, cores = pairs_and_cores(ts, pod, rank, names, share, both)
        top1 = [t for t in ts if t["place"] <= math.ceil(len(ts) / 100)]
        team_val = lambda t: (sum(fpoe(p) or 0 for p in t["picks"]), sum(breaker(p) for p in t["picks"]))
        times = draft_times(ts, snaps)
        am = lambda t: times[id(t)].astimezone(PT).hour < AM_UNTIL if id(t) in times else None
        hours = Counter(times[id(t)].astimezone(PT).strftime("%H") for t in ts if id(t) in times)
        row = {"contest": c["title"], "contest_id": c["contest_id"], "entries": len(ts), "pods": npods, "pod_size": pod,
               "cut_lines": cut_lines(ts),
               "drafted_curve": curve,
               "first_below_100": below,
               "drafted_bands": {"99.5+": sum(1 for r in curve if r["drafted"] >= 99.5), "60-99.5": sum(1 for r in curve if 60 <= r["drafted"] < 99.5),
                                 "10-60": sum(1 for r in curve if 10 <= r["drafted"] < 60), "<10": sum(1 for r in curve if r["drafted"] < 10)},
               "value": {"field_fpoe": round(sum(team_val(t)[0] for t in ts) / len(ts), 1),
                         "top1_fpoe": round(sum(team_val(t)[0] for t in top1) / len(top1), 1),
                         "field_breakers": round(sum(team_val(t)[1] for t in ts) / len(ts), 2),
                         "top1_breakers": round(sum(team_val(t)[1] for t in top1) / len(top1), 2)},
               "pairs": pairs[:25], "cores": cores, "turns": turns(ts, pod, rank, names, share, both),
               "uniqueness": uniqueness(ts),
               "draft_time": {"matched": len(times), "am_share": pct(sum(1 for t in ts if am(t)) / max(1, len(times))),
                              "by_hour_pt": dict(sorted(hours.items()))},
               "mine": my_results(ts)}
        if row["mine"]:
            mine = [t for t in ts if t["username"] == ME]
            for lab, f in (("am", lambda t: am(t) is True), ("pm", lambda t: am(t) is False)):
                sub = [t for t in mine if f(t)]
                row["mine"][lab + "_teams"] = len(sub)
                row["mine"][lab + "_tail10"] = round(sum(1 for t in sub if t["place"] <= math.ceil(len(ts) / 10)) / len(sub) / 0.1, 2) if sub else None
        # my teams one by one, so the report can split them by my own lock times and read their tiers
        row["my_teams"] = [{"place": t["place"], "points": t["points"], "payout": t["payout"], "draft_id": t["draft_id"],
                            "picks": t["picks"], "drafted_at": times[id(t)].isoformat() if id(t) in times else None}
                           for t in ts if t["username"] == ME]
        if row["uniqueness"]:
            row["uniqueness"]["top_pairs"] = [("%s + %s" % (names(a), names(b)), k) for (a, b), k in row["uniqueness"]["top_pairs"]]
            row["uniqueness"]["top_cores"] = [(" + ".join(names(p) for p in k), v) for k, v in row["uniqueness"]["top_cores"]]
        out["contests"].append(row)
    json.dump(out, open(os.path.join(OUT, "%s_measures.json" % date), "w"), indent=1, default=str)
    return out


def show(m):
    print("\n==== %s %s" % (m["date"], m["slate"]))
    for c in m["contests"]:
        cl = c["cut_lines"]
        print("\n%s: %d teams in %d pods of %d" % (c["contest"], c["entries"], c["pods"], c["pod_size"]))
        print("  1 cut lines: win %.1f | top1 %.1f top5 %.1f top10 %.1f top20 %.1f | median %.1f (top1 is +%.1f)" % (
            cl["win"], cl["top1"], cl["top5"], cl["top10"], cl["top20"], cl["median"], cl["top1_over_median"]))
        b = c["first_below_100"]
        print("  2 drafted%%: bands %s; first under 100%%: %s" % (c["drafted_bands"], "%s (ADP %.1f, %.1f%%)" % (b["player"], b["adp"], b["drafted"]) if b else "none"))
        v = c["value"]
        print("  3 value: FPOE a team %+.1f field, %+.1f top 1%%; breakers %.2f field, %.2f top 1%%" % (v["field_fpoe"], v["top1_fpoe"], v["field_breakers"], v["top1_breakers"]))
        print("  4 pairs (share of teams, lift over pod mechanics):")
        for p in c["pairs"][:6]:
            print("      %-44s r%s  %5.1f%%  x%s" % (p["pair"], p["rounds"], p["share"], p["lift"]))
        print("    cores: " + "; ".join("%s %.1f%%" % (r["core"], r["share"]) for r in c["cores"][:3]))
        tn = c["turns"]
        print("    1/2 turn (ADP ranks %d-%d):" % tuple(tn["turn_1_2_ranks"]))
        for r in tn["turn_1_2"][:4]:
            print("      %-44s %5.1f%%  x%-5s top1 %d  avg %.1f" % (r["pair"], r["share"], r["lift"], r["top1"], r["avg_points"]))
        print("    2/3 turn (top-3 ADP with their round 2-3 pair):")
        for an in tn["turn_2_3"]:
            r = an["combos"][0] if an["combos"] else None
            if r:
                print("      %-52s %4.1f%% of his %d teams  top1 %d  avg %.1f" % (r["combo"], r["of_anchor"], an["teams"], r["top1"], r["avg_points"]))
        u = c["uniqueness"]
        if u:
            print("  5 my %d teams: median share of the field holding 4+ of my 6 %.2f%% (max %.2f%%); %d duplicated in the field, %d repeats of my own" % (
                u["teams"], u["share4_median"], u["share4_max"], u["teams_with_dupes"], u["repeats_of_mine"]))
        dtm = c["draft_time"]
        print("  6 draft time: %d teams matched, %.0f%% AM; by hour PT %s" % (dtm["matched"], dtm["am_share"], dtm["by_hour_pt"]))
        if c["mine"]:
            r = c["mine"]
            print("  7 my results: %d teams, median finish %.0f%%, tail ratio top1 %.2f top5 %.2f top10 %.2f top20 %.2f; AM %d (top10 x%s), PM %d (top10 x%s)" % (
                r["teams"], r["median_pct"], r["tail1"], r["tail5"], r["tail10"], r["tail20"], r["am_teams"], r["am_tail10"], r["pm_teams"], r["pm_tail10"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["pull", "measures", "seed"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "..", "br-adp-mirror"))
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--date")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.cmd == "seed":
        path = os.path.join(OUT, "seed.json")
        seed = json.load(open(path)) if os.path.exists(path) else []
        json.dump(sorted(set(seed) | set(a.ids)), open(path, "w"), indent=1)
        return
    mirror = daily.Mirror(a.mirror)
    if a.cmd == "pull":
        pull(mirror, a.days)
        return
    for date in [a.date] if a.date else sorted({c["date"] for c in load_contests()}):
        m = measures(mirror, date)
        if m:
            show(m)


if __name__ == "__main__":
    main()
