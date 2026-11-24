"""Late swap with a partially revealed field: a backtest (2026-11-21, the coordinator's research request; analysis only).

Mid-slate, DraftKings' standings export shows each entry's started players only (real ownership, live points), and an
edited entries file is accepted mid-slate as long as every started player stays in the slot he started in; unstarted
players can move between unstarted slots or be swapped for any slot-eligible player whose game hasn't started, within
the cap. At each window break (after a tip, before the next) this study masks the games still to tip in the saved
standings, which hold every entry's full lineup, and asks two things.

Test 1, field completion: (a) the hidden players' ownership in the contest, from our pre-lock projection (the field
file's own at lock), that scaled to the hidden ownership mass the revealed part pins down exactly (each entry's open slots
are known), that plus a steepness fitted on the revealed players' early miss (log real ~ b log projected), and the mean of
the imputations; (b) imputing each entry's hidden players: drawn slot by slot from the hidden games' players, weighted by
the ownership estimate, the slots' positions, the salary left (real entries leave $500 or less 95% of the time, so a draw
leaving over $1,000 is mostly redrawn) and the entry's style (its user's revealed ownership against the field's, all his
entries pooled: the export names users). Variants: a baseline (pre-lock ownership, positions only) and the full one. The
measure: per player, the share of an entry's real hidden players its imputation holds, and how often the whole hidden set
matches.

Test 2, swap value: our real entries, at each break, swaps on the unstarted slots only (one in, one out, the unstarted
players free to move between unstarted slots), chosen by simulating the rest of the night. The decision is made at the
next game's tip (its players' swap deadline), while the earlier games are still going (the operator's correction): a
started player counts his DraftKings points so far, rebuilt from ESPN's play-by-play up to that wall-clock time (never a
share of his final line), plus a simulated rest of game scaled by the game time left (from the same feed's clock); a
started game without play-by-play counts ownership known, points simulated in full. The games still to tip are drawn
from the page's own model (scripts/dk_lateswap_study.js, DKSim.nightPoints), every other entry completed by an imputation (a
different one each night), our other entries in the field as they are (we know them). Three policies (the operator's
amendment): per entry, maximize its top-1% chance; per entry, maximize its expected payout; and the capped portfolio (the
expected-payout swaps, an incoming player in at most 60% of our entries in the contest and one swap in at most half of
them). Scored on real results against what we entered: points, top 1%, cash and payout, placed among the real field with
our other entries as that policy left them.

  python3 scripts/dk_lateswap_study.py [--mirror ../br-adp-mirror] [--S 600] [--M 6] [--out analysis/cbb/dk/lateswap_2026-11-21.md]

Usernames are used in memory only (the style pool, telling our entries apart); nothing written names a user or an entry.
"""
import argparse, collections, csv, glob, itertools, json, math, os, random, subprocess, sys, tempfile, datetime as dt
import statistics as S
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E          # noqa: E402  (standings, lineup_names, at_lock, pay_table, USER)
import dk_sit as K           # noqa: E402  (lock_doc: the slate's card just before lock)

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
SLATES = [("2026-11-16", "156660"), ("2026-11-17", "156663"), ("2026-11-18", "157033"), ("2026-11-19", "157138"), ("2026-11-19", "157139")]
CAP, SLOTS = 50000, ["G", "G", "G", "F", "F", "F", "UTIL", "UTIL"]
LEFT_OK, LEFT_KEEP = 1000, 0.1      # a draw leaving over $1,000 is kept 10% of the time (real: 98.7% leave $1,000 or less)
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={}"


def iso(t):
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00"))


def summary(event, cache):
    """ESPN's summary for a game, cached as {plays, athletes}: its plays (wallclock, period, clock) and its box score's
    athletes [{id, name, jersey, team}] (the name fallback for a card without an ESPN id, 2026-11-24). A cache file from
    before the athletes were kept is fetched again once."""
    f = os.path.join(cache, "%s.json" % event)
    c = json.load(open(f)) if os.path.exists(f) else None
    if c is None or "athletes" not in c:
        import urllib.request
        d = None
        for t in range(3):
            try:
                d = json.load(urllib.request.urlopen(ESPN.format(event), timeout=30)); break
            except Exception:
                d = None
        if d is None:
            return c or {"plays": [], "athletes": []}
        ath = []
        for tm in (d.get("boxscore") or {}).get("players") or []:
            ab = (tm.get("team") or {}).get("abbreviation") or ""
            for st in tm.get("statistics") or []:
                for a in st.get("athletes") or []:
                    x = a.get("athlete") or {}
                    if x.get("id"):
                        ath.append({"id": str(x["id"]), "name": x.get("displayName") or "", "jersey": x.get("jersey") or "", "team": ab})
        c = {"plays": d.get("plays") or [], "athletes": ath}
        json.dump(c, open(f, "w"))
    return c


def pbp(event, cache):
    """A game's plays (summary()), None when it has none."""
    return summary(event, cache).get("plays") or None


def norm(s):
    """dk_swap.js norm: accents folded, lowercase, suffixes and punctuation dropped."""
    import re, unicodedata
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def name_match(r, ath):
    """dk_swap.js nameMatch: a card's ESPN athlete in the game's box score by name, then first initial + last name, the
    team breaking a tie; None unless exactly one."""
    nm = norm(r.get("name"))
    c = [a for a in ath if norm(a["name"]) == nm]
    if len(c) != 1:
        w = nm.split(" ")
        if not c:
            c = [a for a in ath if norm(a["name"]).split(" ")[-1:] == w[-1:] and norm(a["name"])[:1] == nm[:1]]
        if len(c) > 1 and r.get("team"):
            t = [a for a in c if a["team"] and a["team"].upper() == str(r["team"]).upper()]
            c = t or c
    return c[0]["id"] if len(c) == 1 else None


def elapsed(p):
    """Game minutes gone at a play: two 20-minute halves, then 5-minute overtimes."""
    per = (p.get("period") or {}).get("number") or 1
    mm, _, ss = ((p.get("clock") or {}).get("displayValue") or "0:00").partition(":")
    left = int(mm or 0) + (float(ss or 0) / 60)
    return (per - 1) * 20 + (20 - left) if per <= 2 else 40 + (per - 3) * 5 + (5 - left)


def so_far(plays, until, espn2dk):
    """({dk id: DraftKings points from the plays before `until`}, the game's share of regulation left, finished?).
    Points 1, a made three +0.5, rebound 1.25, assist 1.5, steal 2, block 2, turnover -0.5, a double-double +1.5 once
    reached (DraftKings' college rules, as scripts/cbb_calibrate.py)."""
    st = collections.defaultdict(lambda: collections.Counter())
    last, done = None, False
    for p in plays:
        if not p.get("wallclock") or iso(p["wallclock"]) >= until:
            continue
        last = p
        t = (p.get("type") or {}).get("text") or ""
        if t == "End Game":
            done = True
        who = [str((x.get("athlete") or {}).get("id")) for x in (p.get("participants") or [])]
        if p.get("scoringPlay") and who:
            st[who[0]]["pts"] += p.get("scoreValue") or 0
            if p.get("scoreValue") == 3:
                st[who[0]]["tpm"] += 1
            if len(who) > 1 and t != "MadeFreeThrow":
                st[who[1]]["ast"] += 1
        elif who and "Rebound" in t:
            st[who[0]]["reb"] += 1
        elif who and t == "Steal":
            st[who[0]]["stl"] += 1
        elif who and t == "Block Shot":
            st[who[0]]["blk"] += 1
        elif who and "Turnover" in t:
            st[who[0]]["tov"] += 1
    out = {}
    for a, x in st.items():
        if a in espn2dk:
            dd = sum(x[k] >= 10 for k in ("pts", "reb", "ast", "stl", "blk")) >= 2
            out[espn2dk[a]] = x["pts"] + 0.5 * x["tpm"] + 1.25 * x["reb"] + 1.5 * x["ast"] + 2 * x["stl"] + 2 * x["blk"] - 0.5 * x["tov"] + (1.5 if dd else 0)
    left = 0.0 if done else (1.0 if last is None else max(0.0, (40 - elapsed(last)) / 40) if elapsed(last) < 40 else 0.03)
    return out, left, done


def fits(slot, roster):
    return slot == "UTIL" or slot in (roster or "").split("/")


def can_fill(players, slots, R):
    """Do these players fill these slot labels (each player one slot)?"""
    if len(players) != len(slots):
        return False
    for perm in itertools.permutations(players):
        if all(fits(s, R[p]["roster"]) for s, p in zip(slots, perm)):
            return True
    return False


def lineup_slots(s):
    """[(slot, name)] from a standings Lineup cell."""
    parts = __import__("re").split(r"(?:^|\s)(G|F|UTIL)\s", " " + s.strip())
    return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def load(mirror):
    from nba_daily import Mirror
    Mi = Mirror(mirror)
    out = []
    for date, g in SLATES:
        sl, start = K.lock_doc(mirror, "dk_cbb_morning.json", date, g)
        fd = E.at_lock(Mi, "dk_cbb_field.json", start, slate=g)
        P = sl["players"]
        R = {i: {"id": i, "name": c["name"], "roster": c.get("roster") or c.get("position") or "", "salary": c["salary"], "tip": c.get("game_start"),
                 "team": c.get("team"), "game": c.get("game"), "status": c.get("status"), "proj": c.get("fp_gate") if c.get("fp_gate") is not None else c.get("fp_dk") or 0,
                 "miss_dk": c.get("miss_dk"), "espn": str(c.get("espn") or ""), "event": str(c.get("event") or "")} for i, c in P.items()}
        byname = {}
        for i, r in R.items():
            byname.setdefault(r["name"], i)
        actual = {}
        gr = os.path.join(DK, "%s_%s.csv" % (date, g))
        for r in csv.DictReader(open(gr)) if os.path.exists(gr) else []:
            if r.get("actual_dk") not in ("", None):
                actual[r["dk_id"]] = float(r["actual_dk"])
        own = fd["slates"][g]["own"]
        pays = {str(c["id"]): c for c in sl.get("contests", [])}
        contests = []
        for f in sorted(glob.glob(os.path.join(DK, "standings", "contest-standings-*.csv"))):
            ent, pl = E.standings(f)
            if len(set(pl) & set(byname)) < 0.9 * len(pl):
                continue
            for nm, (_, fp) in pl.items():
                if nm in byname and fp is not None:
                    actual[byname[nm]] = fp
            cid = os.path.basename(f)[18:-4]
            L, users, bad = [], [], 0
            for e in ent:
                sl8 = lineup_slots(e["lineup"])
                if len(sl8) != 8 or any(n not in byname for _, n in sl8):
                    bad += 1; continue
                L.append([(s, byname[n]) for s, n in sl8]); users.append(e["name"].split(" (")[0].lower())
            contests.append({"id": cid, "L": L, "users": users, "dropped": bad, "pay": pays.get(cid)})
        tips = sorted({r["tip"] for r in R.values() if r["tip"]})
        out.append({"date": date, "g": g, "R": R, "own": own, "z": fd["z"], "actual": actual, "contests": contests, "tips": tips})
    return out


def nights(sl, S, seed):
    rows = [{"id": i, "team": r["team"], "game": r["game"], "proj": r["proj"] if r["status"] != "Out" else 0, "miss_dk": r["miss_dk"], "status": r["status"] or ""} for i, r in sl["R"].items()]
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "in.json"), os.path.join(d, "out.json")
        json.dump({"rows": rows, "z": sl["z"], "S": S, "seed": seed}, open(a, "w"))
        subprocess.run(["node", os.path.join(HERE, "dk_lateswap_study.js"), a, b], check=True)
        o = json.load(open(b))
    return o["ids"], np.array(o["nights"], dtype=np.float32)


# --- Test 1: ownership and imputation ------------------------------------------------------------------------------
def estimates(sl, c, hidden, revealed):
    """{method: {id: estimated ownership %}} for the hidden players, and the real {id: %}."""
    L, N, own = c["L"], len(c["L"]), sl["own"]
    cnt = collections.Counter(i for lu in L for _, i in lu)
    real = {i: 100 * cnt[i] / N for i in set(hidden) | set(revealed)}
    mass = 100 * sum(1 for lu in L for _, i in lu if i in hidden) / N
    pre = {i: own.get(i, 0.0) for i in hidden}
    sp = sum(pre.values()) or 1.0
    scaled = {i: v * mass / sp for i, v in pre.items()}
    xs = [(math.log(own.get(i, 0) + 0.5), math.log(real[i] + 0.5)) for i in revealed if own.get(i, 0) > 0.5 or real[i] > 0]
    b = 1.0
    if len(xs) >= 5:
        mx, my = S.mean(x for x, _ in xs), S.mean(y for _, y in xs)
        vx = sum((x - mx) ** 2 for x, _ in xs)
        b = max(0.5, min(2.0, sum((x - mx) * (y - my) for x, y in xs) / vx)) if vx else 1.0
    st = {i: max(0.0, math.exp(b * math.log(v + 0.5)) - 0.5) for i, v in pre.items()}
    ss = sum(st.values()) or 1.0
    steep = {i: v * mass / ss for i, v in st.items()}
    return {"pre": pre, "scaled": scaled, "steep": steep}, real, b


def impute_one(rng, open_slots, left, pool, R, w):
    """One draw of an entry's hidden players: slot by slot (G and F first, UTIL last), weighted, within the cap.
    pool: the arrays of the hidden games' players (ids, salaries, eligibility by slot) from pool_arrays()."""
    ids, sal_a, elig = pool
    order = sorted(open_slots, key=lambda s: {"G": 0, "F": 0, "UTIL": 1}[s])
    got = None
    for _ in range(25):
        used = np.zeros(len(ids), dtype=bool); sal, pick, ok = 0, [], True
        for n_, slot in enumerate(order):
            m = elig[slot] & ~used & (sal_a + sal + 3000 * (len(order) - n_ - 1) <= left)
            if not m.any():
                ok = False; break
            ww = w[m]; ix = np.flatnonzero(m)[int(rng.choice(m.sum(), p=ww / ww.sum()))]
            used[ix] = True; sal += sal_a[ix]; pick.append(ids[ix])
        if not ok:
            continue
        got = pick
        if left - sal <= LEFT_OK or rng.random() < LEFT_KEEP:
            return pick
    return got


def pool_arrays(hidden, R):
    ids = list(hidden)
    return ids, np.array([R[i]["salary"] for i in ids], dtype=float), {s: np.array([fits(s, R[i]["roster"]) for i in ids]) for s in ("G", "F", "UTIL")}


def test1(sl, c, k, M, rng, styles):
    R, L = sl["R"], c["L"]
    cut = sl["tips"][k]
    started = {i for i, r in R.items() if r["tip"] and r["tip"] <= cut}
    hidden = [i for i, r in R.items() if i not in started and r["status"] != "Out"]
    revealed = [i for i in R if i in started]
    est, real, b = estimates(sl, c, set(hidden), revealed)
    users = c["users"]
    rev_sum = [sum(sl["own"].get(i, 0) for _, i in lu if i in started) for lu in L]
    nrev = [sum(1 for _, i in lu if i in started) for lu in L]
    # the style: each user's revealed ownership against entries with the same number revealed, pooled over his entries
    by_n = collections.defaultdict(list)
    for s_, n_ in zip(rev_sum, nrev):
        by_n[n_].append(s_)
    mu = {n_: (S.mean(v), S.pstdev(v) or 1.0) for n_, v in by_n.items()}
    zu = collections.defaultdict(list)
    for u, s_, n_ in zip(users, rev_sum, nrev):
        if n_:
            zu[u].append((s_ - mu[n_][0]) / mu[n_][1])
    gam = {u: min(1.6, max(0.6, math.exp(0.3 * S.mean(v)))) for u, v in zu.items()}
    variants = {"baseline": (est["pre"], False, False), "full": (est["steep"], True, True)}
    res, imps = {}, []
    PA = pool_arrays(hidden, R)
    for name, (w0, use_sal, use_style) in variants.items():
        hit, sets, nh = 0.0, 0, 0
        drawn = collections.Counter()
        for e, lu in enumerate(L):
            hid = [(s, i) for s, i in lu if i not in started]
            if not hid:
                continue
            left = CAP - sum(R[i]["salary"] for _, i in lu if i in started) if use_sal else 10 ** 9
            g = gam.get(users[e], 1.0) if use_style else 1.0
            w = np.array([max(w0.get(i, 0.0), 0) ** g + 1e-3 for i in PA[0]])
            truth = {i for _, i in hid}
            for m in range(M):
                got = impute_one(rng, [s for s, _ in hid], left, PA, R, w)
                if got is None:
                    continue
                hit += len(truth & set(got)) / len(truth); sets += set(got) == truth; nh += 1
                drawn.update(got)
                if name == "full":
                    imps.append((e, m, got))
        res[name] = {"hit": hit / nh if nh else None, "set": sets / nh if nh else None, "n": nh}
        if name == "full":
            est["imputed"] = {i: 100 * drawn[i] / M / len(L) for i in hidden}
    keep = [i for i in hidden if est["pre"].get(i, 0) >= 0.5 or real.get(i, 0) > 0]
    mae = {m: S.mean(abs(est[m].get(i, 0) - real.get(i, 0)) for i in keep) for m in ("pre", "scaled", "steep", "imputed")} if keep else {}
    return {"mae": mae, "b": b, "imp": res, "nhid": len(keep), "share_hidden": len(hidden) / max(1, len(hidden) + len(revealed))}, imps, started, hidden


# --- what's known at the decision: points so far, game time left -------------------------------------------------
def knowledge(sl, k, cache):
    """At the decision (the next tip, tips[k + 1]): ({dk id: points so far}, {dk id: share of his game left}, a summary).
    Players of the started games (tip <= tips[k]); a game without play-by-play: points unknown, simulated in full."""
    R = sl["R"]
    until = iso(sl["tips"][k + 1])
    espn2dk = {r["espn"]: i for i, r in R.items() if r["espn"]}
    base, left, games = {}, {}, {}
    for ev in sorted({r["event"] for r in R.values() if r["tip"] and r["tip"] <= sl["tips"][k] and r["event"]}):
        pl = pbp(ev, cache)
        if pl is None:
            games[ev] = None
            continue
        e2d = dict(espn2dk)
        ath = summary(ev, cache).get("athletes") or []
        for i, r in R.items():       # a card without an ESPN id: by name in the box score (2026-11-24)
            if r["event"] == ev and not r["espn"]:
                a = name_match(r, ath)
                if a and a not in e2d:
                    e2d[a] = i
        pts, f, done = so_far(pl, until, e2d)
        games[ev] = (f, done)
        for i, r in R.items():
            if r["event"] == ev:
                base[i], left[i] = pts.get(i, 0.0), f
    for i, r in R.items():
        if r["tip"] and r["tip"] <= sl["tips"][k] and i not in left:
            base[i], left[i] = 0.0, 1.0            # no play-by-play: points unknown, the whole game simulated
    have = [v for v in games.values() if v]
    summ = {"gap": (until - iso(sl["tips"][k])).total_seconds() / 60, "started": len(games), "no_pbp": sum(1 for v in games.values() if v is None),
            "left": S.mean(f for f, _ in have) if have else None, "done": sum(1 for _, d in have if d)}
    return base, left, summ


def validate(sl, cache):
    """The play-by-play rebuild at full time against the box score's DraftKings points (a check of the rebuild only)."""
    R, act = sl["R"], {}
    gr = os.path.join(DK, "%s_%s.csv" % (sl["date"], sl["g"]))
    for r in csv.DictReader(open(gr)) if os.path.exists(gr) else []:
        if r.get("actual_dk") not in ("", None) and float(r.get("min") or 0) > 0:
            act[r["dk_id"]] = float(r["actual_dk"])
    espn2dk = {r["espn"]: i for i, r in R.items() if r["espn"]}
    diff = []
    for ev in sorted({r["event"] for r in R.values() if r["event"]}):
        pl = pbp(ev, cache)
        if pl is None:
            continue
        pts, _, _ = so_far(pl, iso("2100-01-01T00:00:00Z"), espn2dk)
        diff += [pts.get(i, 0.0) - a for i, a in act.items() if R[i]["event"] == ev]
    return diff


# --- Test 2: swaps ---------------------------------------------------------------------------------------------------
def pay_of(c):
    p = c.get("pay")
    return E.pay_table(p["payouts"]) if p and p.get("payouts") else None, (p or {}).get("entry_fee") or 0


def place_pay(place, table):
    return (table or {}).get(int(place), 0.0) if table else 0.0


def test2(sl, c, k, imps, started, hidden, ids, NIGHT, rng, base, left):
    R, L, act = sl["R"], c["L"], sl["actual"]
    mine = [e for e, u in enumerate(c["users"]) if u.startswith(E.USER)]
    if not mine:
        return None
    col = {i: j for j, i in enumerate(ids)}
    S_ = NIGHT.shape[0]
    N = len(L)
    T1 = max(1, math.ceil(0.01 * N))
    table, fee = pay_of(c)
    paid = max(table) if table else max(1, int(0.2 * N))
    # each entry's started players by night: points so far + the simulated rest of their games, scaled by the time left
    W_ = NIGHT * np.array([left.get(i, 1.0) for i in ids], dtype=np.float32)[None, :]
    START = np.empty((NIGHT.shape[0], len(L)), dtype=np.float32)
    for e, lu in enumerate(L):
        sc = [col[i] for _, i in lu if i in started]
        START[:, e] = sum(base.get(i, 0.0) for _, i in lu if i in started) + (W_[:, sc].sum(axis=1) if sc else 0.0)
    # each night, every entry's hidden part: ours exact, the others from their imputations (cycled by night)
    by_e = collections.defaultdict(list)
    for e, m, got in imps:
        by_e[e].append(got)
    hid_cols = {}
    for e, lu in enumerate(L):
        if e in mine:
            hid_cols[e] = [[col[i] for _, i in lu if i not in started]]
        else:
            hs = by_e.get(e) or [[i for _, i in lu if i not in started]]   # no imputation drawn: the real (rare)
            hid_cols[e] = [[col[i] for i in h] for h in hs]
    F = np.empty((S_, N), dtype=np.float32)
    rS = np.arange(S_)
    for e in range(N):
        opts = hid_cols[e]
        arr = np.stack([NIGHT[:, o].sum(axis=1) if o else np.zeros(S_, dtype=np.float32) for o in opts])
        F[:, e] = START[:, e] + arr[rS % len(opts), rS]
    # every night's field sorted, each night offset past the last so one searchsorted places all nights at once
    OFF = float(F.max() - F.min() + 10.0)
    flat = (np.sort(F, axis=1).astype(np.float64) + (rS * OFF)[:, None]).ravel()
    payv = np.array([place_pay(p, table) for p in range(N + 2)]) if table else np.zeros(N + 2)

    def score_many(e, H):
        """H: C x S, each candidate's hidden points by night -> [(top-1% rate, cash rate, expected payout)], our entry e
        as each candidate, the field holding the rest (e itself in it as entered, taken out)."""
        mine_s = START[:, e][None, :] + H
        le = np.searchsorted(flat, (mine_s + rS * OFF).ravel(), side="right").reshape(mine_s.shape) - rS * N
        above = N - le - (F[:, e][None, :] > mine_s)
        place = 1 + above
        return list(zip((place <= T1).mean(axis=1), (place <= paid).mean(axis=1), payv[np.minimum(place, N + 1)].mean(axis=1)))

    def score(e, lineup_ids):
        h = [col[i] for i in lineup_ids if i not in started]
        return score_many(e, (NIGHT[:, h].sum(axis=1) if h else np.zeros(S_, dtype=np.float32))[None, :])[0]

    pool = [i for i in hidden if R[i]["status"] != "Out"]
    prop = {}
    for e in mine:
        lu = L[e]
        ids_e = [i for _, i in lu]
        open_slots = [s for s, i in lu if i not in started]
        hid_e = [i for _, i in lu if i not in started]
        if not hid_e:
            prop[e] = {"cur": ids_e, "cands": [(ids_e, score(e, ids_e), None)]}
            continue
        sal = sum(R[i]["salary"] for i in ids_e)
        base = NIGHT[:, [col[i] for i in hid_e]].sum(axis=1)
        new_l, swaps, H = [], [], [base]
        for out_i in hid_e:
            for in_i in pool:
                if in_i in ids_e or sal - R[out_i]["salary"] + R[in_i]["salary"] > CAP:
                    continue
                new_hid = [x for x in hid_e if x != out_i] + [in_i]
                if not can_fill(new_hid, open_slots, R):
                    continue
                new_l.append([x if x != out_i else in_i for x in ids_e]); swaps.append((out_i, in_i))
                H.append(base - NIGHT[:, col[out_i]] + NIGHT[:, col[in_i]])
        sc = score_many(e, np.stack(H))
        prop[e] = {"cur": ids_e, "cands": [(ids_e, sc[0], None)] + [(l, s_, w) for l, s_, w in zip(new_l, sc[1:], swaps)]}
    pick = {}
    pick["top1"] = {e: max(p["cands"], key=lambda x: (x[1][0], x[1][2])) for e, p in prop.items()}
    pick["ev"] = {e: max(p["cands"], key=lambda x: (x[1][2], x[1][0])) for e, p in prop.items()}
    # the capped portfolio: the expected-payout swaps best gain first, an incoming player in at most 60% of our entries
    # here (counting those he's already in), one swap in at most half of them
    n = len(mine)
    cap_p, cap_s = max(1, math.floor(0.6 * n)), max(1, math.ceil(0.5 * n))
    cnt = collections.Counter(x for e in mine for _, x in L[e])
    used = collections.Counter()
    capd = {}
    order = sorted(mine, key=lambda e: -(max(x[1][2] for x in prop[e]["cands"]) - prop[e]["cands"][0][1][2]))
    for e in order:
        best = prop[e]["cands"][0]
        for cand in sorted(prop[e]["cands"][1:], key=lambda x: -x[1][2]):
            if cand[1][2] <= best[1][2]:
                break
            o, i = cand[2]
            if cnt[i] + 1 > cap_p or used[(o, i)] + 1 > cap_s:
                continue
            best = cand; cnt[i] += 1; cnt[o] -= 1; used[(o, i)] += 1
            break
        capd[e] = best
    pick["capped"] = capd
    # real results: each policy's lineups for all our entries, placed among the real field with ours as that policy left them
    real_pts = np.array([sum(act.get(i, 0.0) for _, i in lu) for lu in L])
    out = {}
    for pol in ("entered", "top1", "ev", "capped"):
        pts = real_pts.copy()
        for e in mine:
            if pol != "entered":
                pts[e] = sum(act.get(i, 0.0) for i in pick[pol][e][0])
        srt = np.sort(pts)[::-1]
        res = []
        for e in mine:
            place = 1 + int((srt > pts[e]).sum())
            res.append({"pts": float(pts[e]), "top1": place <= T1, "cash": place <= paid, "pay": place_pay(place, table), "pctile": 100 * (1 - (place - 1) / N)})
        out[pol] = res
    swapped = {pol: sum(1 for e in mine if pick[pol][e][0] != prop[e]["cur"]) for pol in ("top1", "ev", "capped")}
    same = {}
    for pol in ("top1", "ev"):
        ins = collections.Counter(pick[pol][e][2][1] for e in mine if pick[pol][e][2])
        same[pol] = max(ins.values()) if ins else 0
    dis = []
    for j, e in enumerate(mine):
        if pick["top1"][e][0] != pick["ev"][e][0]:
            pcash = prop[e]["cands"][0][1][1]
            dis.append({"near_cash": 0.2 <= pcash <= 0.8, "pay_top1": out["top1"][j]["pay"], "pay_ev": out["ev"][j]["pay"],
                        "pts_top1": out["top1"][j]["pts"], "pts_ev": out["ev"][j]["pts"]})
    # each policy's pick per entry of ours, (lineup ids, (out, in) or None): the late-swap tool's replay fixture reads them
    picks = {pol: {int(e): (list(pick[pol][e][0]), pick[pol][e][2]) for e in mine} for pol in ("top1", "ev")}
    picks["cands"] = {int(e): [(x[2], [float(v) for v in x[1]]) for x in prop[e]["cands"]] for e in mine}   # (swap, (top-1%, cash, EV))
    return {"n": n, "fee": fee, "has_pay": bool(table), "out": out, "swapped": swapped, "same": same, "dis": dis, "picks": picks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    ap.add_argument("--S", type=int, default=600)
    ap.add_argument("--M", type=int, default=6)
    ap.add_argument("--out", default=os.path.join(DK, "lateswap_2026-11-21.md"))
    ap.add_argument("--dump", default=os.path.join(tempfile.gettempdir(), "dk_lateswap_results.json"), help="the raw results (scratch, not committed)")
    ap.add_argument("--from-dump", action="store_true", help="only rewrite the report from --dump")
    ap.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "dk_lateswap_pbp"), help="ESPN play-by-play cache (not committed)")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    rng = np.random.default_rng(20261121)
    data = load(a.mirror)
    if a.from_dump:
        d = json.load(open(a.dump))
        return write(a, data, d["T1"], d["T2"], d["KN"], d["VAL"])
    T1rows, T2rows, KN, VAL = [], [], [], {}
    for sl in data:
        ids, NIGHT = nights(sl, a.S, int(sl["g"]))
        W = len(sl["tips"])
        VAL[sl["g"]] = validate(sl, a.cache)
        kn = {}
        for k in range(W - 1):
            kn[k] = knowledge(sl, k, a.cache)
            KN.append(dict(kn[k][2], date=sl["date"], g=sl["g"], k=k + 1))
        for c in sl["contests"]:
            for k in range(W - 1):
                t1, imps, started, hidden = test1(sl, c, k, a.M, rng, None)
                T1rows.append(dict(t1, date=sl["date"], g=sl["g"], cid=c["id"], k=k + 1, W=W, N=len(c["L"])))
                t2 = test2(sl, c, k, imps, started, hidden, ids, NIGHT, rng, kn[k][0], kn[k][1])
                if t2:
                    T2rows.append(dict(t2, date=sl["date"], g=sl["g"], cid=c["id"], k=k + 1, W=W, N=len(c["L"])))
                print("%s %s contest %s break %d/%d done" % (sl["date"], sl["g"], c["id"][-4:], k + 1, W - 1), file=sys.stderr)
    json.dump({"T1": T1rows, "T2": T2rows, "KN": KN, "VAL": VAL}, open(a.dump, "w"), default=lambda x: x.item() if hasattr(x, "item") else bool(x))
    write(a, data, T1rows, T2rows, KN, VAL)


def write(a, data, T1, T2, KN, VAL):
    L = ["# Late swap with a partially revealed field: backtest", "",
         "Generated by `scripts/dk_lateswap_study.py` (the night draws by `scripts/dk_lateswap_study.js`, the page's own DKSim.nightPoints), "
         "2026-11-21. Analysis only. %d nights with saved standings, every one with several tip windows; %d nights x imputations %d, sim nights %d. "
         "A thin sample: 5 slates, and the contests within a slate share their players' results, so the slate is the unit." % (len(data), len(data), a.M, a.S), "",
         "## Nights and windows", "", "| Slate | Tips | Breaks tested | Contests (standings) | Entries | Our entries |", "|---|---|---|---|---|---|"]
    for sl in data:
        L.append("| %s %s | %d | %d | %d | %d | %d |" % (sl["date"], sl["g"], len(sl["tips"]), len(sl["tips"]) - 1, len(sl["contests"]),
                                                    sum(len(c["L"]) for c in sl["contests"]), sum(1 for c in sl["contests"] for u in c["users"] if u.startswith(E.USER))))
    dropped = sum(c["dropped"] for sl in data for c in sl["contests"])
    L += ["", "## What was known at each decision", "",
          "The decision at each break is the next game's tip (its players' swap deadline). Points so far: rebuilt from ESPN's "
          "play-by-play up to that wall-clock time; the rest of each started game simulated, scaled by the game time left.", "",
          "| Slate | Break | Minutes since the last tip | Started games | Without play-by-play | Their game time left (mean) | Finished |", "|---|---|---|---|---|---|---|"]
    for r in KN:
        L.append("| %s %s | %d | %.0f | %d | %d | %s | %d |" % (r["date"], r["g"], r["k"], r["gap"], r["started"], r["no_pbp"],
                                                          "%.0f%%" % (100 * r["left"]) if r["left"] is not None else "–", r["done"]))
    alld = [x for v in VAL.values() for x in v]
    L += ["", "The rebuild checked at full time against the box score's DraftKings points (players who played): %d player-games, mean "
          "absolute difference %.2f, %.0f%% within 0.5 point, %.0f%% within 2. Per slate: %s." % (
              len(alld), S.mean(abs(x) for x in alld) if alld else float("nan"), 100 * S.mean(abs(x) <= 0.5 for x in alld) if alld else 0,
              100 * S.mean(abs(x) <= 2 for x in alld) if alld else 0,
              ", ".join("%s %d (%.2f)" % (g, len(v), S.mean(abs(x) for x in v)) for g, v in VAL.items() if v))]
    L += ["", "Entries left out (a player not on the lock card): %d." % dropped, "",
          "## Test 1: completing the field", "",
          "Ownership error on the hidden players (mean absolute error in percentage points, players projected 0.5%+ or drafted), by break "
          "(1 = after the first tip), each contest-break weighted equally:", "",
          "| Break | Contest-breaks | Hidden share of players | Pre-lock | Scaled to the known hidden mass | + steepness from the early miss | Imputed | Slates where imputed beats pre-lock |",
          "|---|---|---|---|---|---|---|---|"]
    for k in sorted({r["k"] for r in T1}):
        rs = [r for r in T1 if r["k"] == k and r["mae"]]
        if not rs:
            continue
        m = {x: S.mean(r["mae"][x] for r in rs) for x in ("pre", "scaled", "steep", "imputed")}
        sls = sorted({r["g"] for r in rs})
        wins = sum(1 for g in sls if S.mean(r["mae"]["imputed"] for r in rs if r["g"] == g) < S.mean(r["mae"]["pre"] for r in rs if r["g"] == g))
        L.append("| %d | %d | %.0f%% | %.2f | %.2f | %.2f | %.2f | %d of %d |" % (k, len(rs), 100 * S.mean(r["share_hidden"] for r in rs), m["pre"], m["scaled"], m["steep"], m["imputed"], wins, len(sls)))
    rs = [r for r in T1 if r["mae"]]
    L.append("| all | %d | %.0f%% | %.2f | %.2f | %.2f | %.2f | |" % (len(rs), 100 * S.mean(r["share_hidden"] for r in rs), *(S.mean(r["mae"][x] for r in rs) for x in ("pre", "scaled", "steep", "imputed"))))
    L += ["", "Per slate (all breaks):", "", "| Slate | Pre-lock | Scaled | + steepness | Imputed | Fitted steepness b (mean) |", "|---|---|---|---|---|---|"]
    for sl in data:
        rs = [r for r in T1 if r["g"] == sl["g"] and r["mae"]]
        if rs:
            L.append("| %s %s | %.2f | %.2f | %.2f | %.2f | %.2f |" % (sl["date"], sl["g"], *(S.mean(r["mae"][x] for r in rs) for x in ("pre", "scaled", "steep", "imputed")), S.mean(r["b"] for r in rs)))
    L += ["", "Imputing each entry's hidden players (share of its real hidden players the draw holds; the whole hidden set matching), by break:", "",
          "| Break | Baseline: per player | Baseline: whole set | Full: per player | Full: whole set |", "|---|---|---|---|---|"]
    for k in sorted({r["k"] for r in T1}):
        rs = [r for r in T1 if r["k"] == k and r["imp"]["full"]["hit"] is not None]
        if rs:
            L.append("| %d | %.1f%% | %.2f%% | %.1f%% | %.2f%% |" % (k, 100 * S.mean(r["imp"]["baseline"]["hit"] for r in rs), 100 * S.mean(r["imp"]["baseline"]["set"] for r in rs),
                                                         100 * S.mean(r["imp"]["full"]["hit"] for r in rs), 100 * S.mean(r["imp"]["full"]["set"] for r in rs)))
    L += ["", "## Test 2: swap value", "",
          "Our real entries at each break, three policies against what we entered, scored on real results. The decision is made at the next "
          "tip: started players count their points so far (the play-by-play to that minute) plus a simulated rest of game scaled by the time "
          "left; every other entry's hidden players are imputed, a different imputation each simulated night; our other entries sit in the field "
          "as entered. One swap per entry (one unstarted player out, one unstarted-game player in, the unstarted players free to move between "
          "unstarted slots). Payout where the contest's payout table is on file (11-16's contests have none on file); top 1% and cash on every "
          "contest. Each break is its own counterfactual on the same entries (a swap at break 1 is not carried into break 2), so the pooled row "
          "sums the same entries once per break: read it as the average break, not money that could all have been had.", "",
          "| Slate | Break | Our entries | Swapped (top 1% / EV / capped) | Points vs entered (top 1% / EV / capped) | Top-1% hits (entered / top 1% / EV / capped) | Cash (entered / top 1% / EV / capped) | Payout $ (entered / top 1% / EV / capped) |",
          "|---|---|---|---|---|---|---|---|"]

    def agg(rs):
        n = sum(r["n"] for r in rs)
        sw = [sum(r["swapped"][p] for r in rs) for p in ("top1", "ev", "capped")]
        pts = [S.mean(x["pts"] - y["pts"] for r in rs for x, y in zip(r["out"][p], r["out"]["entered"])) for p in ("top1", "ev", "capped")]
        t1 = [sum(x["top1"] for r in rs for x in r["out"][p]) for p in ("entered", "top1", "ev", "capped")]
        ca = [sum(x["cash"] for r in rs for x in r["out"][p]) for p in ("entered", "top1", "ev", "capped")]
        py = [sum(x["pay"] for r in rs if r["has_pay"] for x in r["out"][p]) for p in ("entered", "top1", "ev", "capped")]
        return n, sw, pts, t1, ca, py
    for g in [sl["g"] for sl in data]:
        for k in sorted({r["k"] for r in T2 if r["g"] == g}):
            rs = [r for r in T2 if r["g"] == g and r["k"] == k]
            n, sw, pts, t1, ca, py = agg(rs)
            L.append("| %s %s | %d | %d | %d / %d / %d | %+.2f / %+.2f / %+.2f | %d / %d / %d / %d | %d / %d / %d / %d | %.2f / %.2f / %.2f / %.2f |" % (
                rs[0]["date"], g, k, n, *sw, *pts, *t1, *ca, *py))
    n, sw, pts, t1, ca, py = agg(T2)
    L.append("| **pooled** | all | %d | %d / %d / %d | %+.2f / %+.2f / %+.2f | %d / %d / %d / %d | %d / %d / %d / %d | %.2f / %.2f / %.2f / %.2f |" % (n, *sw, *pts, *t1, *ca, *py))
    L += ["", "Per slate, pooled over its breaks (payout change against entered; the slate is the unit):", "", "| Slate | Payout change top 1% | EV | capped | Points change top 1% | EV | capped |", "|---|---|---|---|---|---|---|"]
    better = {"top1": 0, "ev": 0, "capped": 0}
    for sl in data:
        rs = [r for r in T2 if r["g"] == sl["g"]]
        if not rs:
            continue
        n, sw, pts, t1, ca, py = agg(rs)
        d = [py[1] - py[0], py[2] - py[0], py[3] - py[0]]
        for p, v in zip(("top1", "ev", "capped"), d):
            better[p] += v > 0
        L.append("| %s %s | %+.2f | %+.2f | %+.2f | %+.2f | %+.2f | %+.2f |" % (sl["date"], sl["g"], *d, *pts))
    L.append("")
    L.append("Slates where the policy's payout beat what we entered: top 1%% %d, EV %d, capped %d, of %d." % (better["top1"], better["ev"], better["capped"], len(data)))
    dis = [d for r in T2 for d in r["dis"]]
    near = [d for d in dis if d["near_cash"]]
    L += ["", "**Where the top-1%% and EV policies disagree:** %d entry-breaks; %d of them near the cash line (pre-swap cash chance 20-80%%). "
          "Paid more on real results: top 1%% %d, EV %d, same %d (near the cash line: top 1%% %d, EV %d, same %d)." % (
              len(dis), len(near), sum(d["pay_top1"] > d["pay_ev"] for d in dis), sum(d["pay_ev"] > d["pay_top1"] for d in dis), sum(d["pay_ev"] == d["pay_top1"] for d in dis),
              sum(d["pay_top1"] > d["pay_ev"] for d in near), sum(d["pay_ev"] > d["pay_top1"] for d in near), sum(d["pay_ev"] == d["pay_top1"] for d in near)), "",
          "**Our entries on the same swap** (the most of our entries in one contest taking the same incoming player, per contest-break): "
          "top 1%%: mean %.1f, %d contest-breaks with 3 or more; EV: mean %.1f, %d with 3 or more (of %d contest-breaks)." % (
              S.mean(r["same"]["top1"] for r in T2), sum(r["same"]["top1"] >= 3 for r in T2), S.mean(r["same"]["ev"] for r in T2), sum(r["same"]["ev"] >= 3 for r in T2), len(T2)), ""]
    open(a.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
