"""NBA daily record: one CSV per main slate, for the morning report (scripts/nba_report.py).

Each row is a player on the slate, for the two halves of the day:

  morning    am_rank and ours_am: your order and our Proj when you pressed Lock AM on the board
             (else the board you'd saved before ETR's first upload, and our Proj then);
             adp_am: ADP at that moment
  ETR        etr_first and etr_last: its first and last upload before lock; adp_etr: ADP when
             the first came in
  afternoon  pm_rank and ours_pm: your order and our Proj when you pressed Lock PM (else the
             board saved at lock, and no ours_pm); adp_close: the last ADP before lock
  ours_raw   the mirror's nba_morning.json on file when ETR's first upload came in
  actual     ESPN's box scores in Underdog points (the Live page's scoring); 0 for a player
             whose team played without him

Beside it, <date>_box.csv: every rotation player (15+ minutes, usual or that night) in every
game of the night, main slate or not, with his box line, usual rates, ETR and matchup row, for
the player ledger (scripts/nba_ledger.py).

ADP comes from the mirror's git history (nba_latest.json is committed every poll), the board
and ETR from your gist's (a git clone of it). ours_*, etr_first and etr_last are on the board's
Proj scale (median nudged toward ceiling); etr_median is ETR's own number.

  python3 scripts/nba_daily.py --mirror ../br-adp-mirror [--gist ../gist] [--since 2026-10-20] [--rebuild]
"""
import argparse, csv, datetime as dt, json, os, re, subprocess, sys, unicodedata, urllib.request
from collections import defaultdict
from zoneinfo import ZoneInfo

PT, ET, UTC = ZoneInfo("America/Los_Angeles"), ZoneInfo("America/New_York"), dt.timezone.utc
OUT = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "daily")
MORNING_ADP_HOUR = 5     # PT
ETR_FALLBACK_HOUR = 9    # PT: when no ETR came in, the morning file on file by then
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
# as on the Live page
TEAM = {"SA": "SAS", "NY": "NYK", "GS": "GSW", "NO": "NOP", "UTAH": "UTA", "WSH": "WAS"}
ESPN_ALIASES = {"miles mcbride": "deuce mcbride", "herbert jones": "herb jones", "moritz wagner": "moe wagner",
                "luguentz dort": "lu dort", "cameron johnson": "cam johnson"}
STAT = {"MIN": "min", "PTS": "pts", "REB": "reb", "AST": "ast", "STL": "stl", "BLK": "blk", "TO": "tov", "PF": "pf",
        "minutes": "min", "points": "pts", "rebounds": "reb", "assists": "ast", "steals": "stl", "blocks": "blk",
        "turnovers": "tov", "fouls": "pf"}
# made-attempted, kept as ESPN writes them (as on the Live page)
SHOT = {"FG": "fg", "3PT": "fg3", "FT": "ft", "fieldGoalsMade-fieldGoalsAttempted": "fg",
        "threePointFieldGoalsMade-threePointFieldGoalsAttempted": "fg3", "freeThrowsMade-freeThrowsAttempted": "ft"}
COLS = ["date", "slate", "player_id", "name", "team", "pos", "adp_am", "adp_etr", "adp_close", "injury", "usual_min",
        "am_rank", "ours_am", "pm_rank", "ours_pm", "ours_raw", "etr_first", "etr_last", "etr_median",
        "min", "pts", "reb", "ast", "stl", "blk", "tov", "actual", "margin",
        # for the player-by-player notes (scripts/nba_ledger.py): his night and his usual per minute
        "opp", "pf", "fg", "fg3", "ft", "pts_pm", "reb_pm", "ast_pm", "stk_pm", "fp_pm", "mtch", "mtch_label", "mtch_cats"]


def norm_name(s):
    """The board's normName, with accents folded first (Jokić is Jokic)."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[‘’'`.]", "", s)
    s = re.sub(r"[-‐-―]", " ", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ud_points(s):
    return round(s["pts"] + 1.2 * s["reb"] + 1.5 * s["ast"] + 3 * (s["stl"] + s["blk"]) - s["tov"], 1)


def pacific_day(t):
    return t.astimezone(PT).strftime("%Y-%m-%d")


def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def snap_time(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=UTC)


def at_pt(day, hour):
    return dt.datetime.fromisoformat(day).replace(hour=hour, tzinfo=PT)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "br_rankings-nba-daily", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


# ---------------------------------------------------------------- the ADP mirror
class Mirror:
    def __init__(self, path):
        self.path, self.cache = path, {}

    def versions(self, file, since, until):
        """[(commit time, sha)] oldest first."""
        out = subprocess.run(["git", "-C", self.path, "log", "--format=%H %ct", "--since=" + since.isoformat(),
                              "--until=" + until.isoformat(), "--", file], capture_output=True, text=True, check=True)
        rows = [l.split() for l in out.stdout.split("\n") if l.strip()]
        return sorted((dt.datetime.fromtimestamp(int(t), UTC), h) for h, t in rows)

    def show(self, sha, file):
        if (sha, file) not in self.cache:
            out = subprocess.run(["git", "-C", self.path, "show", sha + ":" + file], capture_output=True, text=True, check=True)
            self.cache[(sha, file)] = json.loads(out.stdout)
        return self.cache[(sha, file)]

    def main_slates(self, since, until):
        """Every main slate that locked in [since, until], by slate_id."""
        found = {}
        for _, sha in self.versions("nba_latest.json", since - dt.timedelta(days=2), until):
            for s in self.show(sha, "nba_latest.json").get("slates", []):
                lock = iso(s["cutoff"])
                if s["label"].endswith("_main") and since <= lock <= until:
                    found[s["slate_id"]] = {"slate_id": s["slate_id"], "label": s["label"], "lock": lock}
        return sorted(found.values(), key=lambda s: s["lock"])

    def snapshots(self, slate):
        """[(snapshot time, players)] while the slate was priced, oldest first."""
        seen = {}
        for _, sha in self.versions("nba_latest.json", slate["lock"] - dt.timedelta(hours=48), slate["lock"]):
            for s in self.show(sha, "nba_latest.json").get("slates", []):
                if s["slate_id"] == slate["slate_id"] and isinstance(s.get("players"), list) and s["players"]:
                    seen[snap_time(s["snapshot_utc"])] = s["players"]
        return sorted(seen.items(), key=lambda x: x[0])

    def morning_at(self, t):
        """nba_morning.json as it stood at t."""
        v = self.versions("nba_morning.json", t - dt.timedelta(days=4), t)
        return self.show(v[-1][1], "nba_morning.json") if v else None


def adp_at(snaps, t):
    """The last snapshot at or before t (else the first after it, when the slate wasn't priced yet)."""
    before = [x for x in snaps if x[0] <= t]
    return before[-1] if before else (snaps[0] if snaps else None)


# ---------------------------------------------------------------- the gist
class Gist(Mirror):
    """A clone of your gist (git clone https://gist.github.com/<GIST_ID>.git): every save is a commit."""
    def __init__(self, path):
        super().__init__(path)
        out = subprocess.run(["git", "-C", path, "log", "--format=%H %ct"], capture_output=True, text=True, check=True)
        rows = [l.split() for l in out.stdout.split("\n") if l.strip()]
        self.revs = sorted((dt.datetime.fromtimestamp(int(t), UTC), h) for h, t in rows)   # oldest first

    def files(self, version):
        out = {}
        for name in ("br_rankings.json", "br_projections_nba.json"):
            try:
                out[name] = self.show(version, name)
            except (subprocess.CalledProcessError, ValueError):
                pass
        return out

    def store(self, version):
        """The board's normalizeProjStore: current only when it is on the blend the board uses now."""
        raw = self.files(version).get("br_projections_nba.json") or {}
        if raw.get("entries"):
            raw = {"current": raw}
        cur = raw.get("current")
        return {"current": cur if cur and cur.get("blend") == 1 else None, "ours": raw.get("ours") or {}}


def etr_day(store, day):
    cur = store["current"]
    return cur if cur and pacific_day(iso(cur["at"])) == day else None


def board_at(gist, version, slate):
    b = (gist.files(version).get("br_rankings.json") or {}).get("slates", {}).get(slate["label"])
    return b if b and b.get("slate_id") == slate["slate_id"] else None


def find_locks(gist, slate):
    """Your Lock AM / Lock PM for the slate, whenever you pressed them (a PM lock pressed after the
    slate locked still counts): each from the newest save of its board that has it, since a save
    from a device that never saw the press can leave it out. And when the newest save was."""
    locks, newest = {}, None
    for t, version in reversed(gist.revs):
        if t < slate["lock"] - dt.timedelta(days=2):
            break
        b = board_at(gist, version, slate)
        if not b:
            continue
        newest = newest or t
        for which, lk in ((b.get("locks") or {}).items()):
            if which in ("am", "pm") and which not in locks:
                locks[which] = lk
        if "am" in locks and "pm" in locks:
            break
    return locks, newest


def lock_line(slate, locks, t):
    pt_time = lambda iso_s: iso(iso_s).astimezone(PT).strftime("%-I:%M%p").lower()
    return "  %s: %s, %s%s" % (slate["label"], "Lock AM " + pt_time(locks["am"]["at"]) if locks.get("am") else "no Lock AM",
                                "Lock PM " + pt_time(locks["pm"]["at"]) if locks.get("pm") else "no Lock PM",
                                " (board saved %s)" % t.astimezone(PT).strftime("%b %-d %-I:%M%p").lower() if t else " (no saved board)")


def gist_parts(gist, slate):
    """ETR's first and last upload of the lock day; your morning and afternoon boards (the Lock
    presses, else the board before ETR's first upload and the board at lock); our Proj at each."""
    day = pacific_day(slate["lock"])
    revs = [r for r in gist.revs if r[0] < slate["lock"]]
    if not revs:
        return {}
    last = revs[-1][1]
    out = {"etr_last": etr_day(gist.store(last), day), "etr_first": None}
    board = board_at(gist, last, slate)
    locks, saved = find_locks(gist, slate)
    print(lock_line(slate, locks, saved))
    # the day's first upload: the earliest revision whose projections are today's (later ones only add to them)
    first_i = None
    if out["etr_last"]:
        lo, hi = next(i for i, r in enumerate(revs) if r[0] >= at_pt(day, 0)), len(revs)
        while lo < hi:
            mid = (lo + hi) // 2
            if etr_day(gist.store(revs[mid][1]), day):
                hi = mid
            else:
                lo = mid + 1
        first_i = lo
        out["etr_first"] = etr_day(gist.store(revs[lo][1]), day)
    if locks.get("am"):
        out["am"] = dict(locks["am"], source="Lock AM")
    else:
        cut = first_i if first_i is not None else len([r for r in revs if r[0] < at_pt(day, ETR_FALLBACK_HOUR)])
        pre = board_at(gist, revs[cut - 1][1], slate) if cut > 0 else None
        stash = gist.store(last)["ours"].get(day + " " + slate["label"])
        out["am"] = {"at": pre["saved_at"], "order": pre["order"], "ours": stash["values"] if stash else {},
                     "source": "board before ETR"} if pre else None
    if locks.get("pm"):
        out["pm"] = dict(locks["pm"], source="Lock PM")
    else:
        out["pm"] = {"at": board["saved_at"], "order": board["order"], "ours": {}, "source": "board at lock"} if board else None
    return out


def join_etr(players, entries, name_map):
    """The board's joinProjections: by Underdog id, else by a name only one slate player has."""
    by_app = {p["appearance_id"]: p for p in players if p.get("appearance_id")}
    by_pid = {p["player_id"]: p for p in players}
    by_name = {}
    for p in players:
        full = re.sub(r"\s+", " ", (p["first_name"] or "") + " " + (p["last_name"] or "")).strip()
        by_name.setdefault(norm_name(name_map.get(full, full)), []).append(p)
    out = {}
    for e in entries or []:
        if e.get("scenario"):
            continue
        hit = by_app.get(e.get("id")) or by_pid.get(e.get("id"))
        if not hit and len(by_name.get(e.get("norm"), [])) == 1:
            hit = by_name[e["norm"]][0]
        if hit:
            out[hit["player_id"]] = e
    return out


# ---------------------------------------------------------------- ESPN
def espn_box(lock):
    """{(name key, team): line} for the slate's ET day, or None while any game isn't final."""
    day = lock.astimezone(ET).strftime("%Y%m%d")
    board = fetch_json(ESPN + "/scoreboard?dates=%s&limit=50" % day)
    out = {}
    for e in board.get("events", []):
        if e["status"]["type"]["state"] != "post":
            return None
        score = {}
        for c in e["competitions"][0]["competitors"]:
            score[TEAM.get(c["team"]["abbreviation"], c["team"]["abbreviation"])] = float(c.get("score") or 0)
        summ = fetch_json(ESPN + "/summary?event=" + e["id"])
        for t in (summ.get("boxscore") or {}).get("players", []):
            team = TEAM.get(t["team"]["abbreviation"], t["team"]["abbreviation"])
            opp = [v for k, v in score.items() if k != team]
            st = (t.get("statistics") or [{}])[0]
            keys = st.get("keys") or st.get("labels") or st.get("names") or []
            for a in st.get("athletes", []):
                s = {"pts": 0.0, "reb": 0.0, "ast": 0.0, "stl": 0.0, "blk": 0.0, "tov": 0.0, "min": 0.0, "pf": 0.0}
                for i, v in enumerate(a.get("stats") or []):
                    k = STAT.get(keys[i]) if i < len(keys) else None
                    if i < len(keys) and keys[i] in SHOT:
                        s[SHOT[keys[i]]] = str(v)
                    if k:
                        try:
                            s[k] = float(str(v).split("-")[0])
                        except ValueError:
                            pass
                nm = norm_name(a["athlete"]["displayName"])
                s["margin"] = score.get(team, 0) - (opp[0] if opp else 0)
                s["opp"] = next((k for k in score if k != team), "")
                out[(ESPN_ALIASES.get(nm, nm), team)] = s
    return out


# ---------------------------------------------------------------- one slate
def r1(x):
    return "" if x is None else round(float(x), 1)


def r3(x):
    return "" if x is None else round(float(x), 4)


BOX_COLS = ["date", "name", "team", "opp", "pos", "player_id", "adp_close", "min", "pts", "reb", "ast", "stl", "blk", "tov",
            "pf", "fg", "fg3", "ft", "actual", "margin", "usual_min", "pts_pm", "reb_pm", "ast_pm", "stk_pm", "fp_pm",
            "etr_median", "etr_last", "mtch", "mtch_label", "mtch_cats"]
ROTATION_MIN = 15    # the box file keeps a player who usually plays this many minutes, or did tonight


def box_rows(day, box, mfile, etr_entries, slate_rows):
    """Every rotation player in every game of the night, main slate or not, for the player ledger."""
    etr = defaultdict(list)
    for e in etr_entries or []:
        if not e.get("scenario"):
            etr[e.get("norm")].append(e)
    on_slate = {norm_name(r["name"]): r for r in slate_rows}
    out = []
    for (key, team), b in sorted(box.items()):
        m = mfile.get((key, team)) or next((v for (k, _), v in mfile.items() if k == key), None)
        if max((m or {}).get("min") or 0, b["min"]) < ROTATION_MIN:
            continue
        es = [e for e in etr.get(key, []) if e.get("team") in (None, "", team)] or etr.get(key, [])
        e = es[0] if len(es) == 1 else None
        mt = ((m or {}).get("mtch") or {}).get(day)
        sr = on_slate.get(key) or {}
        out.append({
            "date": day, "name": (m or {}).get("name") or sr.get("name") or key.title(), "team": team, "opp": b.get("opp", ""),
            "pos": (m or {}).get("pos") or sr.get("pos", ""), "player_id": sr.get("player_id", ""), "adp_close": sr.get("adp_close", ""),
            "min": r1(b["min"]), "pts": r1(b["pts"]), "reb": r1(b["reb"]), "ast": r1(b["ast"]), "stl": r1(b["stl"]),
            "blk": r1(b["blk"]), "tov": r1(b["tov"]), "pf": r1(b.get("pf")), "fg": b.get("fg", ""), "fg3": b.get("fg3", ""),
            "ft": b.get("ft", ""), "actual": ud_points(b), "margin": r1(b.get("margin")), "usual_min": r1(m and m.get("min")),
            "pts_pm": r3(m and m.get("upm")), "reb_pm": r3(m and m.get("rpm")), "ast_pm": r3(m and m.get("apm")),
            "stk_pm": r3(m and m.get("spm")), "fp_pm": r3(m and m.get("ppm")),
            "etr_median": r1(e.get("median")) if e else "", "etr_last": r1(e.get("proj")) if e else "",
            "mtch": r1(mt[0]) if mt else "", "mtch_label": mt[2] if mt and len(mt) > 2 else "",
            "mtch_cats": " ".join("%s%+.1f" % (k, v) for k, v in sorted(mt[1].items(), key=lambda x: -abs(x[1]))) if mt else "",
        })
    return out


def build(mirror, gist, slate, name_map):
    snaps = [x for x in mirror.snapshots(slate) if x[0] < slate["lock"]]
    if not snaps:
        print("  %s: never priced, skipped" % slate["label"])
        return None
    box = espn_box(slate["lock"])
    if box is None:
        print("  %s: games not final yet, skipped" % slate["label"])
        return None
    parts = gist_parts(gist, slate) if gist else {}
    day = pacific_day(slate["lock"])
    first, am, pm = parts.get("etr_first"), parts.get("am"), parts.get("pm")
    morning = mirror.morning_at(iso(first["at"]) if first else at_pt(day, ETR_FALLBACK_HOUR))
    s_am = adp_at(snaps, iso(am["at"]) if am else at_pt(day, MORNING_ADP_HOUR))
    s_etr = adp_at(snaps, iso(first["at"])) if first else None
    close = snaps[-1]

    players = {}
    for snap in (s_am, s_etr, close):
        players.update({p["player_id"]: p for p in (snap[1] if snap else [])})
    plist = list(players.values())
    adp = lambda snap: {p["player_id"]: p.get("adp") for p in (snap[1] if snap else [])}
    adp_am, adp_etr, adp_close = adp(s_am), adp(s_etr), adp(close)
    etr1 = join_etr(plist, first["entries"] if first else None, name_map)
    etr2 = join_etr(plist, parts["etr_last"]["entries"] if parts.get("etr_last") else None, name_map)
    rank = lambda b: {pid: i + 1 for i, pid in enumerate((b or {}).get("order", []))}
    am_rank, pm_rank = rank(am), rank(pm)
    ours_am, ours_pm = (am or {}).get("ours") or {}, (pm or {}).get("ours") or {}
    mfile = {}
    for r in (morning or {}).get("players", []):
        k = norm_name(r["name"])
        mfile[(ESPN_ALIASES.get(k, k), r.get("team"))] = r
    played_teams = {t for _, t in box}

    rows = []
    for p in sorted(plist, key=lambda p: (adp_close.get(p["player_id"]) is None, adp_close.get(p["player_id"]) or 0)):
        pid, key = p["player_id"], norm_name(p["first_name"] + " " + p["last_name"])
        b = box.get((key, p["team"])) or next((v for (k, _), v in box.items() if k == key), None)
        if b is None and p["team"] in played_teams:      # his team played without him: a zero for whoever drafted him
            b = {"pts": 0.0, "reb": 0.0, "ast": 0.0, "stl": 0.0, "blk": 0.0, "tov": 0.0, "min": 0.0, "pf": 0.0, "margin": None}
        m = mfile.get((key, p["team"])) or next((v for (k, _), v in mfile.items() if k == key), None)
        mt = ((m or {}).get("mtch") or {}).get(day)        # our matchup row for tonight: [points, {category: points}, label]
        rows.append({
            "date": day, "slate": slate["label"], "player_id": pid, "name": p["first_name"] + " " + p["last_name"],
            "team": p["team"], "pos": p.get("position") or "",
            "adp_am": r1(adp_am.get(pid)), "adp_etr": r1(adp_etr.get(pid)), "adp_close": r1(adp_close.get(pid)),
            "injury": p.get("injury") or "", "usual_min": r1(m and m.get("min")),
            "am_rank": am_rank.get(pid, ""), "ours_am": r1(ours_am.get(pid)),
            "pm_rank": pm_rank.get(pid, ""), "ours_pm": r1(ours_pm.get(pid)), "ours_raw": r1(m and m.get("fp")),
            "etr_first": r1(etr1[pid].get("proj")) if pid in etr1 else "",
            "etr_last": r1(etr2[pid].get("proj")) if pid in etr2 else "",
            "etr_median": r1(etr2[pid].get("median")) if pid in etr2 else "",
            "min": r1(b and b["min"]), "pts": r1(b and b["pts"]), "reb": r1(b and b["reb"]), "ast": r1(b and b["ast"]),
            "stl": r1(b and b["stl"]), "blk": r1(b and b["blk"]), "tov": r1(b and b["tov"]),
            "actual": ud_points(b) if b else "", "margin": r1(b and b["margin"]),
            "opp": (b or {}).get("opp", ""), "pf": r1(b and b.get("pf")),
            "fg": (b or {}).get("fg", ""), "fg3": (b or {}).get("fg3", ""), "ft": (b or {}).get("ft", ""),
            "pts_pm": r3(m and m.get("upm")), "reb_pm": r3(m and m.get("rpm")), "ast_pm": r3(m and m.get("apm")),
            "stk_pm": r3(m and m.get("spm")), "fp_pm": r3(m and m.get("ppm")),
            "mtch": r1(mt[0]) if mt else "", "mtch_label": mt[2] if mt and len(mt) > 2 else "",
            "mtch_cats": " ".join("%s%+.1f" % (k, v) for k, v in sorted(mt[1].items(), key=lambda x: -abs(x[1]))) if mt else "",
        })
    when = lambda x: {"at": x["at"], "from": x["source"], "ours": bool(x.get("ours"))} if x else None
    meta = {"lock": slate["lock"].isoformat(), "adp_am_at": s_am[0].isoformat() if s_am else None,
            "adp_etr_at": s_etr[0].isoformat() if s_etr else None, "adp_close_at": close[0].isoformat(),
            "morning_through": (morning or {}).get("games_through"),
            "etr_first": {"at": first["at"], "file": first.get("file")} if first else None,
            "etr_last": {"at": parts["etr_last"]["at"], "file": parts["etr_last"].get("file")} if parts.get("etr_last") else None,
            "am": when(am), "pm": when(pm), "gist": bool(gist)}
    return rows, meta, box_rows(day, box, mfile, parts["etr_last"]["entries"] if parts.get("etr_last") else None, rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True, help="a clone of br-adp-mirror with history back to --since")
    ap.add_argument("--gist", help="a clone of your gist (the board's saved boards and projections)")
    ap.add_argument("--since", help="YYYY-MM-DD, Pacific; default three days back")
    ap.add_argument("--rebuild", action="store_true", help="rewrite slates already on file")
    a = ap.parse_args()
    now = dt.datetime.now(UTC)
    since = at_pt(a.since, 0) if a.since else at_pt(pacific_day(now - dt.timedelta(days=3)), 0)
    os.makedirs(OUT, exist_ok=True)
    meta_path = os.path.join(OUT, "meta.json")
    allmeta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}

    mirror = Mirror(a.mirror)
    try:
        name_map = json.load(open(os.path.join(a.mirror, "nba_name_map.json")))
    except (OSError, ValueError):
        name_map = {}
    gist = Gist(a.gist) if a.gist else None
    if not gist:
        print("::warning::no gist clone (GIST_ID not set): no ETR, our Proj or final ranks")

    for slate in mirror.main_slates(since, now - dt.timedelta(hours=3)):
        name = "%s_%s.csv" % (pacific_day(slate["lock"]), slate["label"].replace("nba_", ""))
        path = os.path.join(OUT, name)
        if os.path.exists(path) and not a.rebuild and (allmeta.get(name, {}).get("gist") or not gist):
            continue   # on file (built again once the gist is there, if it wasn't the first time)
        got = build(mirror, gist, slate, name_map)
        if not got:
            continue
        rows, meta, boxed = got
        with open(path.replace("_main.csv", "_box.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=BOX_COLS)
            w.writeheader()
            w.writerows(boxed)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
        allmeta[name] = meta
        print("  wrote %s: %d players, %d played" % (name, len(rows), sum(1 for r in rows if r["min"] not in ("", 0))))
    with open(meta_path, "w") as f:
        json.dump(dict(sorted(allmeta.items())), f, indent=1)
    if gist:                                              # the slates still to come today: are your locks in?
        print("Today's locks:")
        for s in json.load(open(os.path.join(a.mirror, "nba_latest.json"))).get("slates", []):
            lock = iso(s["cutoff"])
            if s["label"].endswith("_main") and lock > now and pacific_day(lock) == pacific_day(now):
                print(lock_line({"label": s["label"], "slate_id": s["slate_id"], "lock": lock}, *find_locks(gist, {
                    "label": s["label"], "slate_id": s["slate_id"], "lock": lock})))


if __name__ == "__main__":
    sys.exit(main())
