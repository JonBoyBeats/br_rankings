"""NBA daily record: one CSV per main slate, for the morning report (scripts/nba_report.py).

Each row is a player on the slate, for the two halves of the day:

  morning    am_rank and ours_am: your order and our Proj when you pressed Lock AM on the board
             (else the board you'd saved before ETR's first upload, and our Proj then);
             adp_am: ADP at that moment
  ETR        etr_first and etr_last: its first and last upload before lock; adp_etr: ADP when
             the first came in
  injury     his Underdog tag at lock; injury_am: his tag when the AM board locked
  tiers      am_tier and pm_tier: the tier (1-5) your board's tier lines put him in at each lock
             (blank past your line, or when the tiers weren't on)
  at PM     adp_pm, injury_pm and etr_pm: ADP, his tag and ETR's upload as they stood when the PM board locked
             (Lock PM, else the board saved at lock); play_am and play_pm: our chance he plays (1 - the mirror's
             nba_sit.json miss chance) at each lock, from 2026-10-27 when the file started (blank before)
  ladders    the Tiers button's build as it rode with each lock (or the board it falls back to), from 2026-11-09:
             {am,pm}_a and _p his ADP and projection ladder tiers, _c the combined tier, _flag VALUE or PRICEY,
             _q his Q class (SMASH, FAIR, TRAP) with _play his chance to play, _built his rank in the build
             before any hand move (your order against it is your takes), _src the ladder's projection (ours or etr)
  afternoon  pm_rank and ours_pm: your order and our Proj when you pressed Lock PM (else the
             board saved at lock, and no ours_pm); adp_close: the last ADP before lock
  ours_raw   the mirror's nba_morning.json on file when ETR's first upload came in
  spread     his team's line in the mirror's nba_odds.json as of lock (negative: favored), the
             board's day-of snapshot; blank before 2026-10-23, when the mirror started keeping it
  actual     ESPN's box scores in Underdog points (the Live page's scoring); 0 for a player
             whose team played without him

And <date>_<slate>_orders.json.gz: your board's order every time it was saved (the board pushes to your gist two
seconds after each change, stamped with the change time), from the evening before through the last tip, so a swap
can be graded against the order that chose it.

Beside it, <date>_box.csv: every rotation player (15+ minutes, usual or that night) in every
game of the night, main slate or not, with his box line, usual rates, ETR and matchup row, for
the player ledger (scripts/nba_ledger.py).

ADP comes from the mirror's git history (nba_latest.json is committed every poll), the board
and ETR from your gist's (a git clone of it). ours_*, etr_first and etr_last are on the board's
Proj scale (median nudged toward ceiling); etr_median is ETR's own number.

  python3 scripts/nba_daily.py --mirror ../br-adp-mirror [--gist ../gist] [--since 2026-10-20] [--rebuild]
"""
import argparse, csv, datetime as dt, gzip, json, os, re, subprocess, sys, unicodedata, urllib.request
from collections import defaultdict
from zoneinfo import ZoneInfo

PT, ET, UTC = ZoneInfo("America/Los_Angeles"), ZoneInfo("America/New_York"), dt.timezone.utc
OUT = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "daily")
MORNING_ADP_HOUR = 5     # PT
ETR_FALLBACK_HOUR = 9    # PT: when no ETR came in, the morning file on file by then
# The record of each window (2026-11-09): your manual locks; fallbacks only when you didn't lock, labelled "fallback".
AM_UNTIL = 12            # PT: a draft before noon is an AM draft (nba_contests.AM_UNTIL)
AM_GRACE = dt.timedelta(minutes=30)       # draft times are the nearest hourly ADP snapshot: a Lock AM that much after counts
SWAP_FALLBACK = dt.timedelta(minutes=20)  # swaps start at the first tip; without tip times, this long after the slate locks
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
COLS = ["date", "slate", "player_id", "name", "team", "pos", "adp_am", "adp_etr", "adp_close", "injury", "injury_am", "usual_min",
        "am_rank", "ours_am", "pm_rank", "ours_pm", "ours_raw", "etr_first", "etr_last", "etr_median",
        "min", "pts", "reb", "ast", "stl", "blk", "tov", "actual", "margin", "am_tier", "pm_tier",
        # for the player-by-player notes (scripts/nba_ledger.py): his night and his usual per minute
        "opp", "pf", "fg", "fg3", "ft", "pts_pm", "reb_pm", "ast_pm", "stk_pm", "fp_pm", "mtch", "mtch_label", "mtch_cats", "spread"]
LADDER = ["a", "p", "c", "flag", "q", "play", "built", "src"]
COLS += ["adp_pm", "injury_pm", "etr_pm", "play_am", "play_pm"]
COLS += ["%s_%s" % (w, k) for w in ("am", "pm") for k in LADDER]


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
    latest = "nba_latest.json"      # the slates file main_slates and snapshots read (the contest script sets cbb_latest.json)

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
        for _, sha in self.versions(self.latest, since - dt.timedelta(days=2), until):
            for s in self.show(sha, self.latest).get("slates", []):
                lock = iso(s["cutoff"])
                if s["label"].endswith("_main") and since <= lock <= until:
                    found[s["slate_id"]] = {"slate_id": s["slate_id"], "label": s["label"], "lock": lock}
        return sorted(found.values(), key=lambda s: s["lock"])

    def snapshots(self, slate):
        """[(snapshot time, players)] while the slate was priced, oldest first."""
        seen = {}
        for _, sha in self.versions(self.latest, slate["lock"] - dt.timedelta(hours=48), slate["lock"]):
            for s in self.show(sha, self.latest).get("slates", []):
                if s["slate_id"] == slate["slate_id"] and isinstance(s.get("players"), list) and s["players"]:
                    seen[snap_time(s["snapshot_utc"])] = s["players"]
        return sorted(seen.items(), key=lambda x: x[0])

    def lines_at(self, t, day):
        """{team: spread} for the day's games, from nba_odds.json as it stood at t."""
        v = self.versions("nba_odds.json", t - dt.timedelta(days=2), t)
        return ((self.show(v[-1][1], "nba_odds.json").get("lines") or {}).get(day) or {}) if v else {}

    def sit_at(self, t, day):
        """{name key: our chance he plays} for the day, from nba_sit.json as it stood at t ({} before the file)."""
        v = self.versions("nba_sit.json", t - dt.timedelta(days=2), t)
        if not v:
            return {}
        d = self.show(v[-1][1], "nba_sit.json")
        d = d if d.get("date") == day else (d.get("days") or {}).get(day) or {}
        return {norm_name(k): round(1 - x["p"], 3) for k, x in (d.get("players") or {}).items() if isinstance(x.get("p"), (int, float))}

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


def tiers_near(gist, slate, at):
    """Your tier lines on the board saved nearest after `at` (within 15 minutes), else just before it:
    for a lock pressed before the board kept tiers with its locks."""
    t0 = iso(at)
    after = [r for r in gist.revs if t0 <= r[0] <= t0 + dt.timedelta(minutes=15)]
    before = [r for r in gist.revs if r[0] < t0]
    for _, version in after + list(reversed(before))[:1]:
        b = board_at(gist, version, slate)
        if b and isinstance(b.get("tiers"), dict) and isinstance(b["tiers"].get("starts"), list):
            return b["tiers"]
    return None


def tier_of(order, tiers, cut=None):
    """{player_id: tier 1-5} as the board draws them: tiers 2-5 start at tiers["starts"] (ranks),
    the last running to your line (or the end of your order); none past it, or when tiers are off.
    Boards from before 2026-11-02 had six tiers; their sixth line is dropped, as the board now reads them."""
    if not tiers or not tiers.get("on") or len(tiers.get("starts") or []) not in (4, 5):
        return {}
    starts = tiers["starts"][:4]
    end = cut if cut is not None else len(order)
    return {pid: 1 + sum(1 for s in starts if i + 1 >= s) for i, pid in enumerate(order) if i + 1 <= end}


def board_orders(gist, slate):
    """[{"at": change time, "cut", "order"}]: each distinct board the gist saved for the slate from 36 hours before
    lock to 8 hours after (the last tip), oldest first."""
    out, seen = [], None
    for t, version in gist.revs:
        if t < slate["lock"] - dt.timedelta(hours=36) or t > slate["lock"] + dt.timedelta(hours=8):
            continue
        b = board_at(gist, version, slate)
        if not b or not b.get("order"):
            continue
        sig = (tuple(b["order"]), b.get("cut"))
        if sig != seen:
            out.append({"at": b.get("saved_at") or t.isoformat(), "commit_at": t.isoformat(), "cut": b.get("cut"), "order": b["order"]})
            seen = sig
    return out


def lock_line(slate, locks, t):
    pt_time = lambda iso_s: iso(iso_s).astimezone(PT).strftime("%-I:%M%p").lower()
    return "  %s: %s, %s%s" % (slate["label"], "Lock AM " + pt_time(locks["am"]["at"]) if locks.get("am") else "no Lock AM",
                                "Lock PM " + pt_time(locks["pm"]["at"]) if locks.get("pm") else "no Lock PM",
                                " (board saved %s)" % t.astimezone(PT).strftime("%b %-d %-I:%M%p").lower() if t else " (no saved board)")


def lock_history(gist, slate):
    """Every distinct Lock AM, Lock PM and export the gist saved for the slate, and every saved board, oldest first:
    ({"am": [...], "pm": [...], "exp": [...]}, [board]). A re-lock replaces the lock on the board, so the earlier ones
    come from the gist's history; an export carries the tiers and build of the board saved with it."""
    locks, boards = {"am": {}, "pm": {}, "exp": {}}, {}
    for t, version in gist.revs:
        if t < slate["lock"] - dt.timedelta(hours=36) or t > slate["lock"] + dt.timedelta(hours=8):
            continue
        b = board_at(gist, version, slate)
        if not b:
            continue
        if b.get("saved_at") and b.get("order"):
            boards.setdefault(b["saved_at"], b)
        for k, lk in (b.get("locks") or {}).items():
            if k in locks and isinstance(lk, dict) and lk.get("at") and lk.get("order"):
                locks[k].setdefault(lk["at"], dict(lk, tiers=b.get("tiers"), build=b.get("build")) if k == "exp" else lk)
    srt = lambda d: [d[k] for k in sorted(d, key=iso)]
    return {k: srt(v) for k, v in locks.items()}, srt(boards)


def choose_boards(hist, boards, day, am_cut, close, swaps_at):
    """The record of each window. AM: the last Lock AM by am_cut (your first AM draft plus AM_GRACE, else noon); else
    (fallback) the last board saved in the AM window by then, with its Tiers build if it had one. PM: the last Lock PM
    before swaps (a re-lock after setting the swap order counts); else (fallback) the last export before contests close,
    else the last board saved before then. Each comes back with "source" saying which."""
    start = at_pt(day, 0)
    am = [l for l in hist["am"] if iso(l["at"]) <= am_cut]
    if am:
        am_rec = dict(am[-1], source="Lock AM" + (" (last of %d)" % len(am) if len(am) > 1 else ""))
    else:
        win = [b for b in boards if start <= iso(b["saved_at"]) <= am_cut]
        b = win[-1] if win else None
        am_rec = {"at": b["saved_at"], "order": b["order"], "cut": b.get("cut"), "tiers": b.get("tiers"), "build": b.get("build"),
                  "source": "fallback: last %s in the AM window" % ("Tiers build" if b.get("build") else "board saved")} if b else None
    pm = [l for l in hist["pm"] if iso(l["at"]) <= swaps_at]
    if pm:
        pm_rec = dict(pm[-1], source="Lock PM" + (" (last of %d before swaps)" % len(pm) if len(pm) > 1 else ""))
    else:
        ex = [e for e in hist["exp"] if iso(e["at"]) <= close]
        bd = [b for b in boards if iso(b["saved_at"]) <= close]
        if ex:
            e = ex[-1]
            pm_rec = {"at": e["at"], "order": e["order"], "cut": e.get("cut"), "tiers": e.get("tiers"), "build": e.get("build"),
                      "source": "fallback: last export"}
        elif bd:
            b = bd[-1]
            pm_rec = {"at": b["saved_at"], "order": b["order"], "cut": b.get("cut"), "tiers": b.get("tiers"), "build": b.get("build"),
                      "source": "fallback: last board saved before contests closed"}
        else:
            pm_rec = None
    return am_rec, pm_rec


def first_am_draft(slate, snaps):
    """Your first AM draft of the slate's day (its nearest hourly ADP snapshot), from the pulled contests; None without."""
    try:
        import nba_contests as C
        day = pacific_day(slate["lock"])
        _, teams = C.load_night(day)
        mine = [t for ts in teams.values() for t in ts if t["username"] == C.ME]
        times = C.draft_times(mine, snaps)
    except Exception as e:                                   # no contests pulled yet: noon stands in
        print("  %s: no draft times (%s)" % (slate["label"], e))
        return None
    am = sorted(t for t in times.values() if pacific_day(t) == day and t.astimezone(PT).hour < AM_UNTIL)
    return am[0] if am else None


def swaps_start(slate, snaps):
    """When swaps start: the slate's first tip (ESPN, cached in contests/tips.json), else SWAP_FALLBACK after lock."""
    try:
        import nba_swaps as S
        teams = {p.get("team") for p in (snaps[-1][1] if snaps else [])}
        tip = S.tips(pacific_day(slate["lock"]))
        t = [v for k, v in tip.items() if k in teams and v >= slate["lock"] - dt.timedelta(minutes=30)]
        if t:
            return min(t)
    except Exception as e:
        print("  %s: no tip times (%s)" % (slate["label"], e))
    return slate["lock"] + SWAP_FALLBACK


def gist_parts(gist, slate, snaps=None):
    """ETR's first and last upload of the lock day; your morning and afternoon boards (the Lock
    presses, else the board before ETR's first upload and the board at lock); our Proj at each."""
    day = pacific_day(slate["lock"])
    revs = [r for r in gist.revs if r[0] < slate["lock"]]
    if not revs:
        return {}
    last = revs[-1][1]
    out = {"etr_last": etr_day(gist.store(last), day), "etr_first": None}
    board = board_at(gist, last, slate)
    hist, boards = lock_history(gist, slate)
    drafted = first_am_draft(slate, snaps or [])
    am_cut = min(drafted + AM_GRACE, at_pt(day, AM_UNTIL)) if drafted else at_pt(day, AM_UNTIL)
    swaps_at = swaps_start(slate, snaps or [])
    am_rec, pm_rec = choose_boards(hist, boards, day, am_cut, slate["lock"], swaps_at)
    locks = {k: v for k, v in (("am", am_rec), ("pm", pm_rec)) if v}
    out["cuts"] = {"am_by": am_cut.isoformat(), "am_by_from": "first AM draft" if drafted else "noon (no AM draft found)",
                   "close": slate["lock"].isoformat(), "swaps_at": swaps_at.isoformat(),
                   "seen": {k: [l["at"] for l in v] for k, v in hist.items()}}
    print("  %s: AM %s, PM %s" % (slate["label"], (am_rec or {}).get("source", "none"), (pm_rec or {}).get("source", "none")))
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
    for which in ("am", "pm"):
        if locks.get(which) and not locks[which].get("tiers"):
            tn = tiers_near(gist, slate, locks[which]["at"])
            if tn:
                locks[which] = dict(locks[which], tiers=tn)
    out["am"] = locks.get("am")
    if out["am"] and not out["am"].get("ours"):            # a fallback board: our Proj as the board stashed it that day
        stash = gist.store(last)["ours"].get(day + " " + slate["label"])
        out["am"] = dict(out["am"], ours=stash["values"] if stash else {})
    out["pm"] = locks.get("pm")
    if out["pm"] and "ours" not in out["pm"]:
        out["pm"] = dict(out["pm"], ours={})
    if out.get("pm"):                                     # ETR's upload as it stood when the PM board locked
        pm_at = min(iso(out["pm"]["at"]), slate["lock"])
        at_pm = [r for r in revs if r[0] <= pm_at]
        out["etr_pm"] = etr_day(gist.store(at_pm[-1][1]), day) if at_pm else None
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
            "etr_median", "etr_last", "mtch", "mtch_label", "mtch_cats", "spread"]
ROTATION_MIN = 15    # the box file keeps a player who usually plays this many minutes, or did tonight


def box_rows(day, box, mfile, etr_entries, slate_rows, line):
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
            "spread": r1(line.get(team)),
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
    parts = gist_parts(gist, slate, snaps) if gist else {}
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
    injury_am = {p["player_id"]: p.get("injury") or "" for p in (s_am[1] if s_am else [])}   # his tag when the AM board locked
    pm_at = min(iso(pm["at"]), slate["lock"]) if pm else slate["lock"]
    s_pm = adp_at(snaps, pm_at)
    adp_pm = adp(s_pm)
    injury_pm = {p["player_id"]: p.get("injury") or "" for p in (s_pm[1] if s_pm else [])}
    etr_pm = join_etr(plist, parts["etr_pm"]["entries"] if parts.get("etr_pm") else None, name_map)
    am_at = iso(am["at"]) if am else at_pt(day, MORNING_ADP_HOUR)
    sit_am, sit_pm = mirror.sit_at(am_at, day), mirror.sit_at(pm_at, day)
    etr1 = join_etr(plist, first["entries"] if first else None, name_map)
    etr2 = join_etr(plist, parts["etr_last"]["entries"] if parts.get("etr_last") else None, name_map)
    rank = lambda b: {pid: i + 1 for i, pid in enumerate((b or {}).get("order", []))}
    am_rank, pm_rank = rank(am), rank(pm)
    tier = lambda b: tier_of((b or {}).get("order", []), (b or {}).get("tiers"), (b or {}).get("cut"))
    am_tier, pm_tier = tier(am), tier(pm)
    ours_am, ours_pm = (am or {}).get("ours") or {}, (pm or {}).get("ours") or {}

    def ladder(b, pid):
        """His row of the Tiers button's build that rode with this board, or blanks."""
        bd = (b or {}).get("build") or {}
        x = (bd.get("players") or {}).get(pid) or {}
        built = {q: i + 1 for i, q in enumerate(bd.get("order") or [])}
        return {"a": x.get("a", ""), "p": x.get("p", ""), "c": x.get("c", ""), "flag": x.get("flag", ""), "q": x.get("q", ""),
                "play": x.get("play", ""), "built": built.get(pid, ""), "src": bd.get("source", "") if x else ""}
    mfile = {}
    for r in (morning or {}).get("players", []):
        k = norm_name(r["name"])
        mfile[(ESPN_ALIASES.get(k, k), r.get("team"))] = r
    played_teams = {t for _, t in box}
    line = mirror.lines_at(slate["lock"], day)

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
            "injury": p.get("injury") or "", "injury_am": injury_am.get(pid, ""), "usual_min": r1(m and m.get("min")),
            "am_rank": am_rank.get(pid, ""), "ours_am": r1(ours_am.get(pid)),
            "pm_rank": pm_rank.get(pid, ""), "ours_pm": r1(ours_pm.get(pid)), "ours_raw": r1(m and m.get("fp")),
            "etr_first": r1(etr1[pid].get("proj")) if pid in etr1 else "",
            "etr_last": r1(etr2[pid].get("proj")) if pid in etr2 else "",
            "etr_median": r1(etr2[pid].get("median")) if pid in etr2 else "",
            "min": r1(b and b["min"]), "pts": r1(b and b["pts"]), "reb": r1(b and b["reb"]), "ast": r1(b and b["ast"]),
            "stl": r1(b and b["stl"]), "blk": r1(b and b["blk"]), "tov": r1(b and b["tov"]),
            "actual": ud_points(b) if b else "", "margin": r1(b and b["margin"]),
            "am_tier": am_tier.get(pid, ""), "pm_tier": pm_tier.get(pid, ""),
            "opp": (b or {}).get("opp", ""), "pf": r1(b and b.get("pf")),
            "fg": (b or {}).get("fg", ""), "fg3": (b or {}).get("fg3", ""), "ft": (b or {}).get("ft", ""),
            "pts_pm": r3(m and m.get("upm")), "reb_pm": r3(m and m.get("rpm")), "ast_pm": r3(m and m.get("apm")),
            "stk_pm": r3(m and m.get("spm")), "fp_pm": r3(m and m.get("ppm")),
            "mtch": r1(mt[0]) if mt else "", "mtch_label": mt[2] if mt and len(mt) > 2 else "",
            "mtch_cats": " ".join("%s%+.1f" % (k, v) for k, v in sorted(mt[1].items(), key=lambda x: -abs(x[1]))) if mt else "",
            "spread": r1(line.get(p["team"])),
        })
        for w, b in (("am", am), ("pm", pm)):
            rows[-1].update({"%s_%s" % (w, k): v for k, v in ladder(b, pid).items()})
        rows[-1].update({"adp_pm": r1(adp_pm.get(pid)), "injury_pm": injury_pm.get(pid, ""),
                         "etr_pm": r1(etr_pm[pid].get("proj")) if pid in etr_pm else "",
                         "play_am": sit_am.get(key, ""), "play_pm": sit_pm.get(key, "")})
    when = lambda x: {"at": x["at"], "from": x["source"], "ours": bool(x.get("ours")),
                      "tiers": (x.get("tiers") or {}).get("starts") if (x.get("tiers") or {}).get("on") else None} if x else None
    meta = {"lock": slate["lock"].isoformat(), "adp_am_at": s_am[0].isoformat() if s_am else None,
            "adp_etr_at": s_etr[0].isoformat() if s_etr else None, "adp_close_at": close[0].isoformat(),
            "morning_through": (morning or {}).get("games_through"),
            "etr_first": {"at": first["at"], "file": first.get("file")} if first else None,
            "etr_last": {"at": parts["etr_last"]["at"], "file": parts["etr_last"].get("file")} if parts.get("etr_last") else None,
            "etr_pm": {"at": parts["etr_pm"]["at"], "file": parts["etr_pm"].get("file")} if parts.get("etr_pm") else None,
            "adp_pm_at": s_pm[0].isoformat() if s_pm else None,
            "am": when(am), "pm": when(pm), "gist": bool(gist), "cuts": parts.get("cuts")}
    return rows, meta, box_rows(day, box, mfile, parts["etr_last"]["entries"] if parts.get("etr_last") else None, rows, line)


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
        if gist:
            snaps = board_orders(gist, slate)
            with gzip.open(path.replace("_main.csv", "_orders.json.gz"), "wt") as f:
                json.dump(snaps, f, separators=(",", ":"))
            meta["orders"] = len(snaps)
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
