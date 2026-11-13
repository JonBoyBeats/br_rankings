"""NBA morning report: your morning sports section, tier by tier, in plain English. Writes
analysis/nba/report/today.md and prints it.

  Front page   last night's story, how your teams did, the lessons and anything to decide today
  Proposals    Mondays only: each a plain-English decision with a recommendation and its evidence
  T1 ... T5    each tier: the rules we played, did they work last night, your moves, the player recap, the contest
               view, what we're leaning toward, today in this tier
  Draft card   how the turns went last night, and where contest results stand on each card rule
  Back page    the model (ours against ETR, the projection hypotheses, decisions due), data status, links
  Season       the season tables (reference)

The hand-written parts live in analysis/nba/report/morning/<night>.json, written by the morning report and kept by
the nightly runs: {"front": str, "proposals": {decision id: recommendation}, "moves": {"1".."5": str}, "card": str,
"back": str}. Until it exists the front page is a summary built from the files. Every number in the generated parts
comes from the files.

Words, not codes: no register ids, rule codes or verdict labels. RULE: proven so far; LEAN: an early sign; no lean:
no clear signal; not enough yet: too early to say; provisional: on trial. Points are the rankings grade (fantasy
points per head-to-head pair); contest results are the money grade (top-10% finishes against similar teams).

Today's slate is read at report time (ADP now, the morning projection file): a directional read, since the board's own
Proj isn't on the server; the real build is the Tiers button.

  python3 scripts/nba_tier_report.py --mirror ../br-adp-mirror [--today YYYY-MM-DD]
"""
import argparse, collections, csv, datetime as dt, glob, json, math, os, re, subprocess, sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_history as T    # noqa: E402
import nba_tier_grade as G      # noqa: E402
import nba_q_lane as Q          # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = G.REP
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
CONTESTS = os.path.join(HERE, "analysis", "nba", "contests")
OUT = os.path.join(REP, "today.md")
MORNING = os.path.join(REP, "morning")           # <night>.json: the morning report's hand-written parts
RECHECK = os.path.join(REP, "recheck.json")      # {"last": "YYYY-MM"}: the month of the last monthly re-check
PT = ZoneInfo("America/Los_Angeles")
QT = re.compile(r"^(q|d|g)", re.I)
num = G.num
FORWARD_NIGHTS = 14
GROUPS = [("T1", {1}), ("T2", {2}), ("T3/T4", {3, 4}), ("T5", {5})]     # the season tables
SWITCHES = {   # tier: the decision_register.csv ids of its AM and PM switch
    1: ("kept-am-t1", "kept-pm-t1"), 2: ("kept-am-t2", "pm-t2-adp-etr2"), 3: ("kept-am-middle", "kept-pm-t3"),
    4: ("kept-am-middle", "pm-t4-adp-etr2"), 5: ("am-t5-button-order", "pm-t5-adp-value")}
RULE_WORDS = {   # (tier, window): the switch in words (nba_tier_history.RULE_STEPS)
    (1, "am"): "Morning: ADP, with the higher Boom (his ceiling) first when two are within two picks",
    (1, "pm"): "Afternoon: ETR's projection",
    (2, "am"): "Morning: straight ADP",
    (2, "pm"): "Afternoon: ADP, with ETR breaking ties within two picks",
    (3, "am"): "Morning: our projection, with ADP deciding within three points",
    (3, "pm"): "Afternoon: ETR's projection, with ADP and then Boom breaking exact ties",
    (4, "am"): "Morning: our projection, with ADP deciding within three points",
    (4, "pm"): "Afternoon: ADP, with ETR breaking ties within two picks",
    (5, "am"): "Morning: the Tiers button's order, our projection with ADP deciding within three points",
    (5, "pm"): "Afternoon: ADP",
}
TIEBREAKS = {5: ("ownership-tiebreak-t5", "Then, in both windows, the less drafted of two players goes first when they're within two "
                 "projected points and at least 10 points apart in how often they're drafted")}
SHADOW_REG = {"t5-less-drafted-am": "ownership-tiebreak-t5", "t5-less-drafted-pm": "ownership-tiebreak-t5",
              "pm-t5-vs-old-etr": "pm-t5-adp-value", "check-value-first": "value-up-middle-t5", "check-pricey-last": "pricey-flags",
              "check-am-q": "am-questionable-no-push", "check-pm-q": "pm-questionable-back-two",
              "check-am-t5-button": "am-t5-button-order"}     # shadow.json ids whose money verdict sits on another register row
SHADOW_WORDS = {   # shadow.json switch rows in words (the tier ideas carry their own "plain" line in hypotheses.json)
    "pm-t2-adp-etr2": "ETR within two picks in afternoon T2 (the old rule: within one)",
    "pm-t4-adp-etr2": "ADP with ETR within two picks in afternoon T4 (the old rule: straight ETR)",
    "pm-t5-vs-old-etr": "ADP in afternoon T5 (the old rule: ETR's projection)",
    "t5-less-drafted-am": "The less-drafted tiebreak in morning T5",
    "t5-less-drafted-pm": "The less-drafted tiebreak in afternoon T5",
    "check-value-first": "VALUE first in T3 to T5, against leaving VALUE players with the rest",
    "check-pricey-last": "PRICEY last, against leaving PRICEY players with the rest",
    "check-am-q": "No morning push for a Questionable player, against two tiers back",
    "check-pm-q": "The afternoon Questionable push, against no push",
    "check-am-t5-button": "The button's order in morning T5, against ADP straight",
}
KEPT_READ = {}   # register id -> the contest side's first read of an original rule (money_tiers.json candidates), set in main
LEAN_WORDS = {   # leans.json adopted rules that aren't a tier's switch, in words
    "value-up-middle-t5": "VALUE players (our projection rates them at least a tier above their ADP) go first in the tier",
    "keep-one-tier-cap": "no player moves more than one tier from his ADP tier",
    "am-questionable-no-push": "in the morning a Questionable player keeps his tier",
    "pm-questionable-back-two": "in the afternoon a Questionable player drops two tiers (to T5 at most)",
    "pm-t5-beneficiary-picks": "in the afternoon you keep raising beneficiaries (a player whose teammate is tagged or out)",
}
SRC_WORDS = {"Ours": "our projection", "ADP": "ADP", "ETR": "ETR", "Ours PM": "our afternoon projection"}
TAKE_SRC = {"ETR": "on an ETR note", "Bagel": "on a Bagel note", "Bagel+ETR": "on ETR and Bagel notes", "NEWS": "on news",
            "OTHER": "on your own read"}
DRAFT_CARD = [   # (the card line, what contest results grade, its register id); index.html #draftCard
    ("Fallers: at the 1/2 turn, a top-4 ADP player still there at picks 5-8; at the 2/3 turn (from the 1.01/1.02), a "
     "top-9 player still there at picks 11-14 (4-person pods: top-2 / top-5). Take them.", "taking a faller", "card-fallers"),
    ("1/2 turn: don't reach unless a top player falls.", "reaching at the 1/2 turn", "card-turn12-reach"),
    ("2/3 turn: reach toward the higher projection.", "reaching toward the higher projection at the 2/3 turn",
     "card-turn23-reach-higher-proj"),
    ("Avoid same-position teammates.", "holding an early pick and a late teammate at his position", "card-same-position-teammates"),
    ("Opposing stars from the same game: a plus.", "pairing stars from opposite sides of one game", "card-opposing-stars"),
]
DRAFT_NOTE = "Later rounds: a player well past his ADP through round 5 leans worth taking (a candidate, not yet tested)."


# ---------------------------------------------------------------- words
def lab_words(label):
    l = (label or "").strip().lower()
    return ("proven so far" if l.startswith("rule") else "an early sign" if l.startswith("lean") else
            "no clear signal" if l.startswith("no lean") else "too early to say" if l.startswith("not enough") else None)


def lab_side(label):
    l = (label or "").strip().lower().split(" (")[0] + " "
    return 1 if ("+ " in l or " for " in l) else -1 if ("- " in l or "against" in l) else 0


def said(label, mean=None):
    """A verdict in words with its direction: 'proven to help so far', 'an early sign it hurts', 'no clear signal'..."""
    w = lab_words(label)
    sd = lab_side(label) or (1 if (mean or 0) > 0 else -1 if (mean or 0) < 0 else 0)
    if w == "proven so far":
        return "proven to help so far" if sd > 0 else "proven to hurt so far"
    if w == "an early sign":
        return "an early sign it helps" if sd > 0 else "an early sign it hurts"
    return w or "still to come"


def short(name):
    return name.split(" ", 1)[-1] if name.count(" ") else name


def poss(name):
    return name + ("'" if name.endswith("s") else "'s")


def names(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


def pct(x):
    return "%d%%" % round(100 * x)


def iso(t):
    return dt.datetime.fromisoformat(str(t).replace("Z", "+00:00"))


def hm(t):
    return iso(t).astimezone(PT).strftime("%-I:%M%p").lower() if t else "-"


def norm(s):
    return T.re.sub(r"[^a-z ]", "", (s or "").lower().replace("-", " ").replace(".", "")).strip()



def f1(v):
    return "%+.1f (%d)" % (sum(v) / len(v), len(v)) if v else "-"


def today_slate(mirror):
    latest = json.load(open(os.path.join(mirror, "nba_latest.json")))
    day = dt.datetime.now(dt.timezone.utc).astimezone(PT).date().isoformat()
    for s in latest.get("slates", []):
        lock = iso(s["cutoff"])
        if s["label"].endswith("_main") and lock.astimezone(PT).date().isoformat() == day and isinstance(s.get("players"), list) and s["players"]:
            return s, lock, day, latest
    return None, None, day, latest


def calibrated_play(H):
    cal = [dict(p=float(r["play"]), y=int(r["played"]), tagged=bool(QT.match(r["tag"] or ""))) for r in H if r["play"] != "" and r["played"] != ""]
    a, b, c = Q.fit(cal)
    return lambda p, tagged: 1 / (1 + math.exp(-(a + b * Q.logit(p) + (c if tagged else 0))))


# ---------------------------------------------------------------- top: pipeline health
def mirror_first(mirror, file, day, ok):
    """When the mirror first committed a version of `file` that ok(doc) accepts on the Pacific day (None if never)."""
    since = dt.datetime.fromisoformat(day + "T00:00:00").replace(tzinfo=PT)
    try:
        out = subprocess.run(["git", "-C", mirror, "log", "--reverse", "--format=%H %ct", "--since=" + since.isoformat(), "--", file],
                             capture_output=True, text=True, check=True).stdout.split("\n")
        for line in out:
            if not line.strip():
                continue
            sha, t = line.split()
            doc = json.loads(subprocess.run(["git", "-C", mirror, "show", sha + ":" + file], capture_output=True, text=True, check=True).stdout)
            if ok(doc):
                return dt.datetime.fromtimestamp(int(t), dt.timezone.utc)
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None


def health(mirror, today, latest):
    """One line per input for last night and for today's inputs."""
    y = (dt.date.fromisoformat(today) - dt.timedelta(days=1)).isoformat()
    meta = json.load(open(os.path.join(DAILY, "meta.json")))
    name = next((k for k in sorted(meta) if k.startswith(y)), None)
    m = meta.get(name, {}) if name else {}
    lines = []
    cs = [r for r in csv.DictReader(open(os.path.join(CONTESTS, "contests.csv")))] if os.path.exists(os.path.join(CONTESTS, "contests.csv")) else []
    cy = [r for r in cs if r["date"] == y]
    files = glob.glob(os.path.join(CONTESTS, "%s_*.csv.gz" % y))
    lines.append("- Contests: %s" % ("%d pulled of %d listed, %s teams%s" % (len(files), len(cy), "{:,}".format(sum(int(r["entries"] or 0) for r in cy)),
                 "; measures in" if os.path.exists(os.path.join(CONTESTS, "%s_measures.json" % y)) else "; measures not run")
                 if cy else "none listed for %s" % y))
    path = os.path.join(DAILY, name) if name else None
    if path and os.path.exists(path):
        rows = list(csv.DictReader(open(path)))
        lines.append("- Results: %s, %d players, %d with a box line" % (name[:-4], len(rows), sum(1 for r in rows if r["actual"] != "")))
    else:
        newest = sorted(meta)[-1] if meta else "none"
        lines.append("- Results: no daily record for %s (newest %s): check the NBA daily record workflow" % (y, newest[:10]))
    try:
        import nba_swaps as S
        n = S.night(y) if path else None
        if y in getattr(S, "EXCLUDED", {}):
            lines.append("- Swaps: %s excluded from swap tests (%s)" % (y, S.EXCLUDED[y]))
        elif n:
            lines.append("- Swaps credited: %d of %d (%.0f%%)" % (len(n["credited"]), n["n_swaps"], 100 * len(n["credited"]) / max(1, n["n_swaps"])))
        else:
            lines.append("- Swaps credited: no contests or record for %s yet" % y)
    except Exception as e:                                  # contests not on file: say so rather than fail
        lines.append("- Swaps credited: not read (%s)" % e)
    if m:
        ef, el = m.get("etr_first") or {}, m.get("etr_last") or {}
        lines.append("- ETR: " + ("first upload %s, last %s" % (hm(ef.get("at")), hm(el.get("at"))) if ef else "none on file for %s" % y))
        cuts = m.get("cuts") or {}
        seen = cuts.get("seen") or {}
        for w in ("am", "pm"):
            x = m.get(w) or {}
            frm = x.get("from") or "none"
            extra = ""
            if w == "am" and cuts.get("am_by"):
                extra = "; counts by %s (%s)" % (hm(cuts["am_by"]), cuts.get("am_by_from"))
            if w == "pm" and cuts.get("swaps_at"):
                extra = "; swaps from %s; %d Lock PM, %d export%s seen" % (hm(cuts["swaps_at"]), len(seen.get("pm", [])), len(seen.get("exp", [])),
                                                                     "" if len(seen.get("exp", [])) == 1 else "s")
            lines.append("- Lock %s: %s at %s%s" % (w.upper(), frm, hm(x.get("at")), extra))
        on = m.get("on")
        lines.append("- Overnight (drafts before 4:30am, kept out of the AM grades): %s" % (
            "%d drafts from %s; %s at %s" % (on.get("drafts", 0), hm(on.get("first")), on.get("source"), hm(on.get("at"))) if on else "none"))
        lines.append("- ADP snapshots: AM board %s, closing %s (lock %s)" % (hm(m.get("adp_am_at")), hm(m.get("adp_close_at")), hm(m.get("lock"))))
    due = dt.datetime.fromisoformat(today + "T04:30:00").replace(tzinfo=PT)
    mo = mirror_first(mirror, "nba_morning.json", (dt.date.fromisoformat(today) - dt.timedelta(days=1)).isoformat(),
                      lambda d: d.get("games_through") == y)
    sit = mirror_first(mirror, "nba_sit.json", today, lambda d: d.get("date") == today or today in (d.get("days") or {}))
    tags = iso(re.sub(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})(\d{2})(\d{2})Z$", r"\1-\2-\3T\4:\5:\6Z", latest.get("generated_at", ""))) \
        if latest.get("generated_at") else None
    ok = lambda t: "ready %s" % hm(t.isoformat()) + ("" if t <= due else " (late: due 4:30am)") if t else "NOT READY (due 4:30am)"
    lines.append("- Today's inputs: our Proj %s; chance to play %s; Q-tags polled %s" % (ok(mo), ok(sit), hm(tags.isoformat()) if tags else "-"))
    return lines



def recheck_due(today):
    last = json.load(open(RECHECK)).get("last") if os.path.exists(RECHECK) else None
    return last != today[:7]


def problems(lines):
    """The health lines that say something is wrong."""
    bad = re.compile(r"NOT READY|late:|none listed|none on file|no daily record|not run|not read|no contests|fallback", re.I)
    return [l[2:] for l in lines if bad.search(l)]


# ---------------------------------------------------------------- today's slate (a directional read)
def today_pool(mirror, H):
    """(slate, lock, pod, pool rows with their combined tier c, flag, chance to play; beneficiaries [(row, tagged row)])."""
    s, lock, day, latest = today_slate(mirror)
    if not s:
        return None, None, None, [], []
    pcal = calibrated_play(H)
    players = [p for p in s["players"] if p.get("player_id")]
    pod = 4 if max((p.get("adp") or 0) for p in players) <= 28 else 6
    cap = 24 if pod == 4 else 36
    mo = {norm(r["name"]): r for r in json.load(open(os.path.join(mirror, "nba_morning.json"))).get("players", [])}
    sit_doc = json.load(open(os.path.join(mirror, "nba_sit.json")))
    sit_day = sit_doc if sit_doc.get("date") == day else (sit_doc.get("days") or {}).get(day) or {}
    sit = {norm(k): v for k, v in (sit_day.get("players") or {}).items()}
    rows = []
    for p in players:
        name = (p.get("first_name") or "") + " " + (p.get("last_name") or "")
        mm = mo.get(norm(name)) or {}
        rows.append({"p": p, "name": name, "team": p.get("team") or "", "adp": p.get("adp"), "proj": mm.get("fp"),
                     "tag": p.get("injury") or "", "sit": sit.get(norm(name))})
    pool = [r for r in rows if r["adp"] is not None or r["proj"] is not None]
    adp = lambda r: min(r["adp"], cap) if r["adp"] is not None else cap
    A = sorted(pool, key=lambda r: (adp(r), -(r["proj"] or 0)))
    P = sorted(pool, key=lambda r: (-(r["proj"] or -1e9), adp(r)))
    la = T.lines([adp(r) for r in A], T.LADDER[pod], T.MIN_TIER[pod])
    lp = T.lines([max(r["proj"] or 0, 0) for r in P], T.LADDER[pod], T.MIN_TIER[pod])
    for i, r in enumerate(A):
        r["a"] = T.tier_of(i + 1, la)
    for i, r in enumerate(P):
        r["pt"] = T.tier_of(i + 1, lp)
    for r in pool:
        d = r["a"] - r["pt"]
        r["c"] = r["a"] - (1 if d > 0 else -1) if abs(d) >= 2 else r["a"]
        r["flag"] = "VALUE" if d > 0 else "PRICEY" if d < 0 else ""
        miss = r["sit"]["p"] if r["sit"] and isinstance(r["sit"].get("p"), (int, float)) else (1.0 if r["tag"].lower().startswith("o") else 0.02)
        r["play"] = pcal(min(max(1 - miss, 0.005), 0.995), bool(QT.match(r["tag"])))
        r["drafted"] = r["adp"] is not None and r["adp"] < cap
    tagged = [r for r in pool if QT.match(r["tag"]) and r["drafted"]]
    ben = []
    for tg in tagged + [r for r in pool if r["tag"].lower().startswith("o")]:
        for r in pool:
            if r["team"] == tg["team"] and r is not tg and (r["adp"] is None or r["adp"] >= cap - 6) and (r["proj"] or 0) >= 15:
                ben.append((r, tg))
    return s, lock, pod, sorted(pool, key=adp), ben[:8]


# ---------------------------------------------------------------- front page
def hand(night):
    p = os.path.join(MORNING, "%s.json" % night)
    return json.load(open(p)) if os.path.exists(p) else {}


def front_page(night, H, mt, health_lines, slate):
    """The automatic summary, used until the morning report writes the front page."""
    md = []
    rec = {}
    for p in glob.glob(os.path.join(DAILY, "%s_*_main.csv" % night)):
        rec = {r["player_id"]: r for r in csv.DictReader(open(p))}
    games = {}
    for r in rec.values():
        m = num(r.get("margin"))
        if m is not None and m > 0:
            games[(r["team"], r["opp"])] = m
    blow = sorted(((m, a, b) for (a, b), m in games.items() if m >= 15), reverse=True)
    late = (json.load(open(os.path.join(REP, "late_news.json"))) if os.path.exists(os.path.join(REP, "late_news.json")) else {}).get(night) or {}
    led = [r for r in csv.DictReader(open(os.path.join(HERE, "analysis", "nba", "ledger.csv"))) if r["date"] == night and num(r["gap"]) is not None
           and num(r["adp_close"]) is not None and num(r["adp_close"]) < 36]
    s = ["Last night's main slate had %d games" % len(games)]
    if blow:
        s[0] += ", %d of them blowouts (%s)" % (len(blow), "; ".join("%s by %d over %s" % (a, m, b) for m, a, b in blow))
    s[0] += "."
    if late.get("am") or late.get("pm"):
        s.append("Late news took %s out of the morning grades%s." % (names(late.get("am") or []) or "no team",
                                                                   " and %s out of the afternoon's" % names(late["pm"]) if late.get("pm") else ""))
    up = sorted(led, key=lambda r: -num(r["gap"]))[:3]
    if up:
        s.append("The biggest nights against ETR's number among drafted players: %s." % "; ".join(
            "%s %.0f points over" % (r["name"], num(r["gap"])) for r in up))
    res = (mt or {}).get("results")
    if res and (mt or {}).get("night") == night:
        s.append("Your %d teams (%d drafted in the morning, %d in the afternoon) had a median finish in the top %d%%; %d made the "
                 "top 10%% and %d the top 1%%, and %d cashed. They cost $%.0f in entries and won $%.0f." % (
                     res["teams"], res["am"], res["pm"], round(res["median_pct"]), res["top10"], res["top1"], res["cashed"], res["fees"], res["won"]))
    bad = problems(health_lines)
    if bad:
        s.append("Something in the pipeline needs a look: %s." % "; ".join(bad))
    if slate:
        s.append("Today: %s, lock %s PT, %d-drafter pods." % (slate[0]["label"].replace("nba_", "").replace("_", " ").title(),
                                                           slate[1].astimezone(PT).strftime("%-I:%M %p"), slate[2]))
    s.append("(The written front page comes with the morning report; this is the automatic summary.)")
    return [" ".join(s), ""]


# ---------------------------------------------------------------- Monday proposals
# ---------------------------------------------------------------- one tier
STATUS_KEY = [
    ("Locked in", "proven on points and in contest results."),
    ("In use, on trial", "adopted and in use; where its 14-night check is running, the night it's on (\"night 3 of 14\")."),
    ("In use, original rule", "the rule we started with: nothing has beaten it, and contest results haven't graded it yet."),
    ("Being tested", "not in use; graded in the background against what is."),
    ("Retired", "taken out."),
]
RULE_MAIN = {(1, "am"): "adp", (1, "pm"): "proj", (2, "am"): "adp", (2, "pm"): "adp", (3, "am"): "proj", (3, "pm"): "proj",
             (4, "am"): "proj", (4, "pm"): "adp", (5, "am"): "proj", (5, "pm"): "adp"}   # which straight order each rule mostly follows
KINDS = {   # tier: [(kind, register id, flag or tag the exposure players carry, how it's said)]
    1: [("PRICEY", "pricey-flags:T1", "PRICEY", "putting PRICEY players last")],
    2: [("less drafted", "leverage-t2-t4", None, "taking the less drafted of two close players"), ("PRICEY", "pricey-flags", "PRICEY", "putting PRICEY players last")],
    3: [("VALUE", "value-up-middle-t5", "VALUE", "taking VALUE players first"), ("less drafted", "leverage-t2-t4", None, "taking the less drafted of two close players"),
        ("PRICEY", "pricey-flags", "PRICEY", "putting PRICEY players last")],
    4: [("VALUE", "value-up-middle-t5", "VALUE", "taking VALUE players first"), ("less drafted", "leverage-t2-t4", None, "taking the less drafted of two close players"),
        ("PRICEY", "pricey-flags", "PRICEY", "putting PRICEY players last")],
    5: [("VALUE", "value-up-middle-t5", "VALUE", "taking VALUE players first"), ("less drafted", "ownership-tiebreak-t5", None, "taking the less drafted of two close players"),
        ("beneficiary", "pm-t5-beneficiary", None, "afternoon beneficiary picks"), ("Q-tag", "q-tag-raises", "Q", "raising Questionable players"),
        ("PRICEY", "pricey-flags", "PRICEY", "putting PRICEY players last")],
}
CARD = [   # (money_tiers "card" key, what you did)
    ("1/2 faller", "took a faller at the 1/2 turn"), ("1/2 reach", "reached at the 1/2 turn"), ("1/2 trust", "trusted ADP at the 1/2 turn"),
    ("2/3 faller", "took a faller at the 2/3 turn"), ("2/3 reach: higher projection", "reached toward the higher projection at the 2/3 turn"),
    ("2/3 trust", "trusted ADP at the 2/3 turn"), ("same-position teammates", "paired an early pick with a late same-position teammate"),
    ("opposing stars", "paired stars from opposite sides of one game"),
]


def who_to_trust(H, last, t):
    """Projection straight against ADP straight on this tier's close calls: last night in a sentence, the season in one,
    ending in what to do."""
    def calls(rows, w):
        per = collections.defaultdict(list)
        pl = collections.defaultdict(list)
        by = collections.defaultdict(list)
        for r in rows:
            by[r["date"]].append(r)
        for d, rs in by.items():
            for x, y in G.pairs(rs, {t}):
                px, py = num(x["proj"]), num(y["proj"])
                if px is None or py is None or px == py or G.adp(x) == G.adp(y) or x["slot"] == y["slot"]:
                    continue
                pf = x if px > py else y
                if pf is (x if G.adp(x) < G.adp(y) else y):
                    continue
                o = y if pf is x else x
                g = pf["slot"] - o["slot"]
                per[d].append(g)
                pl[x["player_id"]].append(g)
                pl[y["player_id"]].append(g)
        return per, pl
    who = {"am": "our projection", "pm": "ETR"}
    s, night = [], []
    for w in ("am", "pm"):
        rows = [r for r in H if r["date"] == last and r["window"] == w and int(r["tier"]) == t]
        per, _ = calls(rows, w)
        g = per.get(last, [])
        if len(g) == 1:
            night.append("%s's pick %s the only close call%s" % (who[w], "won" if g[0] > 0 else "lost", " in the morning" if w == "am" else " in the afternoon"))
        elif g:
            k = sum(1 for x in g if x > 0)
            night.append("%s's pick %s%s" % (who[w], ("won both" if len(g) == 2 else "won all %d" % len(g)) if k == len(g) else ("lost both" if len(g) == 2 else "lost all %d" % len(g)) if k == 0 else
                                             "scored more %d times out of %d" % (k, len(g)), " in the morning" if w == "am" else " in the afternoon"))
    s.append("Last night, when %s disagreed with ADP about two close players here, %s." % (
        "our projection or ETR", "; ".join(night)) if night else "Last night the projection and ADP agreed on every close call here.")
    best = None
    for w in ("am", "pm"):
        rows = [r for r in H if r["pod"] == "6" and r["window"] == w and (w == "pm" or r["sample"] == "primary") and int(r["tier"]) == t]
        per, pl = calls(rows, w)
        if not per:
            continue
        n, mean, _, _, lab = G.verdict(per, pl)
        rank = {"proven so far": 2, "an early sign": 1}.get(lab_words(lab), 0)
        if best is None or (rank, n) > (best[0], best[1]):
            best = (rank, n, mean, lab, w)
    if not best:
        return [" ".join(s), ""]
    rank, n, mean, lab, w = best
    when = "in the morning" if w == "am" else "in the afternoon"
    if not rank:
        s.append("On the season there's no clear answer here yet (%s close calls): nothing to change." % n)
    else:
        win, lose = (who[w], "ADP") if mean > 0 else ("ADP", who[w])
        follows = RULE_MAIN[(t, w)] == ("proj" if mean > 0 else "adp")
        s.append("On the season, trusting %s over %s here %s gains about %.0f point%s per close call (%s): %s." % (
            win, lose, when, abs(mean), "" if round(abs(mean)) == 1 else "s", said(lab, abs(mean)), "keep doing it, the rule already does" if follows
            else "the rule leans the other way here, so this is worth a test"))
    return [" ".join(s), ""]


def recap(H, last, t):
    """Overs, unders and scratches in this tier, the reason only; in-line nights are left out."""
    pm = {r["player_id"]: r for r in H if r["date"] == last and r["window"] == "pm"}
    am = {r["player_id"]: r for r in H if r["date"] == last and r["window"] == "am"}
    rows = [r for pid, r in {**am, **pm}.items() if int(r["tier"]) == t and (t != 5 or (num(r["adp"]) is not None and num(r["adp"]) < G.cap(r)))]
    rows.sort(key=G.adp)
    led = {r["player_id"]: r for r in csv.DictReader(open(os.path.join(HERE, "analysis", "nba", "ledger.csv"))) if r["date"] == last}
    sw = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        if r["date"] == last:
            sw[r["out_id"]].append(r)
    md = []
    last_names = collections.Counter(short(r["name"]) for r in rows)
    nm = lambda n: short(n) if last_names[short(n)] == 1 else n
    for r in rows:
        l = led.get(r["player_id"]) or {}
        note = ((l.get("note") or "").strip() or (l.get("draft") or "").strip())
        if r["scratched"] == "1":
            xs = sorted(sw.get(r["player_id"], []), key=lambda x: -int(x["teams"]))[:2]
            if xs:
                md.append("- **%s**: scratched; swaps went to %s." % (nm(r["name"]), " and ".join(
                    "%s (%d teams, %.0f points)" % (short(x["swap"]), int(x["teams"]), float(x["swap_fp"])) for x in xs)))
        elif (l.get("result") or "") in ("over", "under"):
            md.append("- **%s**: %s" % (nm(r["name"]), note or l["result"].capitalize() + "."))
    return (md or ["Everyone here played to his number."]) + [""], {r["name"] for r in rows}


# ---------------------------------------------------------------- draft card and back page
def q_tracker(H, last):
    """How well the chance-to-play model sorts players tagged Questionable at the morning record, season to date: how
    many played, whether its calibrated chance orders the ones who play above the ones who sit (AUC: 0.5 is a coin flip,
    1 is perfect), and whether it beats a flat guess at the season's rate (Brier score, lower is better)."""
    pcal = calibrated_play(H)
    seen, rows = set(), []
    for r in H:
        if r["window"] != "am" or not (r["tag"] or "").lower().startswith("q") or r["play"] == "" or r["played"] == "":
            continue
        if (r["date"], r["player_id"]) in seen:
            continue
        seen.add((r["date"], r["player_id"]))
        rows.append((pcal(min(max(float(r["play"]), 0.005), 0.995), True), int(r["played"]), r["date"], r["name"]))
    if len(rows) < 10:
        return []
    base = sum(y for _, y, _, _ in rows) / len(rows)
    brier = sum((p - y) ** 2 for p, y, _, _ in rows) / len(rows)
    flat = sum((base - y) ** 2 for _, y, _, _ in rows) / len(rows)
    pos, neg = [p for p, y, _, _ in rows if y], [p for p, y, _, _ in rows if not y]
    auc = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / (len(pos) * len(neg)) if pos and neg else None
    night = [(n, p, y) for p, y, d, n in rows if d == last]
    out = "Chance to play, morning Questionable players: %d this season, %d played (%s). The model sorts the ones who play from " \
          "the ones who sit at %.2f (0.5 is a coin flip, 1 is perfect), and %s a flat %s guess (Brier %.3f against %.3f; lower " \
          "is better)." % (len(rows), sum(y for _, y, _, _ in rows), pct(base), auc if auc is not None else 0.5,
                           "beats" if brier < flat else "doesn't beat", pct(base), brier, flat)
    if night:
        out += " Last night: %s." % "; ".join("%s at %s, %s" % (n, pct(p), "played" if y else "sat") for n, p, y in night)
    return [out]


def back_page(H, last, health_lines, today, hand_back):
    md = ["## Back page", ""]
    pm = [r for r in H if r["date"] == last and r["window"] == "pm" and r["scratched"] != "1" and num(r["actual"]) is not None]
    both = [r for r in pm if num(r["proj"]) is not None and r["ours_pm"] is not None]
    s = []
    if len(both) >= 8:
        act = [num(r["actual"]) for r in both]
        e_etr = sum(abs(num(r["proj"]) - a) for r, a in zip(both, act)) / len(both)
        e_our = sum(abs(r["ours_pm"] - a) for r, a in zip(both, act)) / len(both)
        c_etr, c_our = G.spearman([num(r["proj"]) for r in both], act), G.spearman([r["ours_pm"] for r in both], act)
        s.append("The model: on the %d players both projected at the afternoon lock, ours missed by %.1f points on average and "
                 "ETR's by %.1f; their rank correlations with the finish were %.2f and %.2f (1 is perfect)." % (
                     len(both), e_our, e_etr, c_our or 0, c_etr or 0))
    tracker = q_tracker(H, last)
    hyp_lines = []
    try:
        import nba_hypotheses as HY
        reg = json.load(open(HY.REGISTRY))
        HY.L.fit_scale(HY.rep.load())
        history = HY.nights()
        dates = [d for d, _ in history]
        hs = []
        for hid, h in reg.items():
            rule = HY.RULES.get(h.get("rule", "")) if hid != "tiers" else None
            if not rule or h["status"] not in ("testing", "adopted", "retired"):
                continue
            name = h["title"].split(":")[0].split(" (")[0]
            plain = h.get("plain") or h["title"].split(": ", 1)[-1]
            if h["status"] == "retired":
                if h.get("retired", "") >= (dt.date.fromisoformat(today) - dt.timedelta(days=7)).isoformat():
                    hs.append("- **%s** (retired %s): %s; %s." % (name, h["retired"][5:], plain, h.get("retired_plain") or "it stopped helping"))
                continue
            fwd = HY.summary(HY.gains(rule, history, since=h["opened"]))
            recent = dates[-HY.RECHECK_DAYS:] if dates else []
            rc = HY.summary(HY.gains(rule, history, since=recent[0])) if h["status"] == "adopted" and recent else None
            p = HY.proposal(h, fwd, rc).split(" ")[0]
            x = rc if h["status"] == "adopted" else fwd
            if not x:
                hs.append("- **%s**: %s. It hasn't fired yet." % (name, plain))
                continue
            closer = "%.2f points %s" % (abs(x["mean"]), "closer" if x["mean"] >= 0 else "further off")
            if h["status"] == "adopted":
                tail = "it's in the model; over the last %d nights it lands %s across %d players%s" % (
                    HY.RECHECK_DAYS, closer, x["n"], ", so it comes to you to retire" if p == "**retire?**" else "")
            else:
                left = HY.FORWARD_DAYS - min(x["nights"], HY.FORWARD_DAYS)
                tail = "it lands %s across %d players, %d of %d nights in; %s" % (
                    closer, x["n"], min(x["nights"], HY.FORWARD_DAYS), HY.FORWARD_DAYS,
                    "it comes to you as a proposal to adopt" if p == "**adopt?**" else "it comes to you as a proposal to reject" if p == "**reject?**"
                    else "%d more night%s and it comes to you as a proposal" % (left, "" if left == 1 else "s") if left else
                    "it's still short of a clear answer" )
            hs.append("- **%s**: %s; adopting it would %s. So far %s." % (name, plain, h.get("adopt_plain") or "build it into the morning Proj", tail))
        hyp_lines = hs
    except Exception as e:                                      # the back page must not fail the report
        s.append("Projection hypotheses not read (%s)." % e)
    if recheck_due(today):
        s.append("The monthly re-check is due this month.")
    if hand_back:
        s.append(hand_back)
    bad = problems(health_lines)
    s2 = "Data: " + ("; ".join(bad) + "." if bad else "everything for last night came in, and today's inputs were ready on time.")
    try:                                                   # the Swap button: each swap against the PM list's (season to date)
        import nba_swap_grade
        swap_line = nba_swap_grade.season_line()
    except Exception as e:
        swap_line = "Swap button: not graded (%s)." % e
    md += [" ".join(s), ""] + ([tracker[0], ""] if tracker else []) + [swap_line, ""] + (["**Projection hypotheses.**", ""] + hyp_lines + [""] if hyp_lines else []) + [s2, "", "Season tables are below; every player's night is in the ledger (analysis/nba/ledger.csv), "
           "the calls and misses in misses.csv, and the full tier tables in tier_grade.md, shadow.md and money_report.md.", ""]
    return md


def overnight(H):
    """The overnight window on its own: your board saved before your first overnight draft against ADP then, on decision
    pairs (ADP within 4, drafted players), each slot scored through his swap; positive: your board won."""
    slot = {(r["date"], r["player_id"]): r["slot"] for r in H if r["window"] == "pm"}
    meta = json.load(open(os.path.join(DAILY, "meta.json")))
    per, teams, nights = collections.defaultdict(list), 0, 0
    for name, m in sorted(meta.items()):
        if not m.get("on"):
            continue
        teams += m["on"].get("drafts", 0)
        nights += 1
        rows = [r for r in csv.DictReader(open(os.path.join(DAILY, name))) if r.get("on_rank") and num(r.get("adp_on")) is not None
                and (r["date"], r["player_id"]) in slot]
        cap = 24 if max((num(r["adp_on"]) for r in rows), default=0) <= 28 else 36
        rows = [r for r in rows if num(r["adp_on"]) < cap]
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                if abs(num(a["adp_on"]) - num(b["adp_on"])) > G.DECISION:
                    continue
                you, adpf = int(a["on_rank"]) < int(b["on_rank"]), num(a["adp_on"]) < num(b["adp_on"])
                if you == adpf:
                    continue
                x, y = (a, b) if you else (b, a)
                g = slot[(x["date"], x["player_id"])] - slot[(y["date"], y["player_id"])]
                if g:
                    per[name[:10]].append(g)
    return ["**Overnight window** (drafts before 4:30am; kept out of the AM grades): %d nights, %d of your teams; your board "
            "against ADP then: %s" % (nights, teams, G.fmt(G.verdict(per)) if per else "no board on file yet"), ""]


def season_tables(H):
    md = []
    res = {x: G.grade(H, "6", x, "primary", [(n, t, None) for n, t in GROUPS]) for x in ("am", "pm")}
    tk = list(csv.DictReader(open(os.path.join(REP, "takes_history.csv"))))
    for i, (gname, tiers) in enumerate(GROUPS):
        md += ["**%s**" % gname, "", "| Window | vs projection | vs ADP | VALUE vs partners |", "|---|---|---|---|"]
        for x, src in (("am", "Ours"), ("pm", "ETR")):
            _, nights, h2h, _, _, flags, _ = res[x][i]
            flat = lambda d: [v for vs in d.values() for v in vs]
            md.append("| %s (%d nights) | %s | %s | %s |" % (x.upper(), nights if isinstance(nights, int) else len(nights), f1(flat(h2h[src][0])),
                                                           f1(flat(h2h["ADP"][0])), f1(flat(flags["VALUE"]))))
        by = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in tk:
            if r["pod"] == "6" and int(r["tier"]) in tiers and (r["window"] == "pm" or r["sample"] == "primary"):
                by[(r["window"], r.get("source") or "OTHER")][r["date"]].append(float(r["gain"]))
        if by:
            md += ["", "| Your takes | Source | Points per take |", "|---|---|---|"]
            for (w, src), per in sorted(by.items()):
                md.append("| %s | %s | %s |" % (w.upper(), src, G.fmt(G.verdict(per))))
        md.append("")
    md.append("Points per pair or take (count); positive: your board won, VALUE beat its partners, or your take beat the button. "
              "Takes are credited to ETR or Bagel when either player had a note from them before the lock, else NEWS (his "
              "projection or his team's status changed since the last lock) or OTHER. Verdicts and labels: tier_grade.md.")
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "br-adp-mirror"))
    ap.add_argument("--today", help="the report's date (YYYY-MM-DD; default today, Pacific)")
    a = ap.parse_args()
    H = G.load()
    leans = json.load(open(os.path.join(REP, "leans.json")))
    status = {x["id"]: ("provisional" if x.get("provisional") else "RULE" if x.get("basis") == "RULE" else "adopted") for x in leans["adopted"]}
    reg = {r["id"]: r for r in csv.DictReader(open(os.path.join(REP, "decision_register.csv")))}
    by_reg = {x["register"]: status[x["id"]] for x in leans["adopted"] if x.get("register")}
    money = lambda rid: "money " + ((reg.get(rid) or {}).get("money_verdict") or "pending").split(" (")[0]
    hyp = (json.load(open(os.path.join(REP, "hypotheses.json"))).get("tiers") or {})
    shadow = json.load(open(os.path.join(REP, "shadow.json"))) if os.path.exists(os.path.join(REP, "shadow.json")) else []
    mt_path = os.path.join(REP, "money_tiers.json")
    mt = json.load(open(mt_path)) if os.path.exists(mt_path) else None
    for c in (mt or {}).get("candidates") or []:
        if str(c.get("id", "")).startswith("kept-") and isinstance(c.get("read"), str):
            KEPT_READ[c["id"]] = c["read"]
    today = a.today or dt.datetime.now(dt.timezone.utc).astimezone(PT).date().isoformat()
    _, _, _, latest = today_slate(a.mirror)
    last = max(r["date"] for r in H)
    hw = hand(last)
    hl = health(a.mirror, today, latest)
    slate, lock, pod, pool, ben = today_pool(a.mirror, H)
    day = lambda d: dt.date.fromisoformat(d).strftime("%A %-m/%-d")
    md = ["# NBA morning report, %s" % day(today), "", "*Last night: %s's main slate.*" % day(last), "", "## Front page", ""]
    if not mt or mt.get("night", "") < last:     # nba_money.py runs `|| true` in the workflow, so a failure shows only here
        md[2:2] = ["**Contest numbers are stale:** money_tiers.json %s, last night was %s; the money step failed or didn't run." % (
            "is from %s" % day(mt["night"]) if mt and mt.get("night") else "is missing", day(last)), ""]
    import nba_report_sections as RS
    RS.write_rulebook()
    md[4:4] = ["*The standing rules and the words this report uses: [the rulebook](rulebook.md).*", ""] + RS.rule_change(last)
    md += [hw["front"], ""] if hw.get("front") else front_page(last, H, mt, hl, (slate, lock, pod) if slate else None)
    md += RS.decided(mt, last)
    md += RS.bets_and_fades(mt, last, H)
    for t in range(1, 6):
        rc, _ = recap(H, last, t)
        rc = RS.recap_order(H, last, t, rc)
        md += ["## T%d" % t, ""] + RS.THEME[t] + [""]
        hand_moves = (hw.get("moves") or {}).get(str(t))
        if t in (1, 2):
            md += ["**How the night went.** " + RS.night_line(H, last, t), ""]
        elif t in (3, 4):
            md += ["**How the night went.** " + who_to_trust(H, last, t)[0], ""]
        if t in (2, 3, 4):
            md += ["**Your moves.**", ""] + RS.moves(H, last, t) + ([hand_moves, ""] if hand_moves else [])
        if t == 2:
            md += ["**The turn lines.**", ""] + RS.turn_lines(mt, last)
        if t == 5:
            md += ["**Your T5 menu, on contest results.**", ""] + RS.t5_contest(H, mt) + ([hand_moves, ""] if hand_moves else [])
        md += ["**Player recap**, in the button's order.", ""] + rc
        md += ["**Contest view.** " + RS.contest(t, mt)[0], ""]
    md += RS.q_section(H, last, (pool, ben), q_tracker(H, last), mt)
    md += RS.back(last, problems(hl)) + ([hw["back"], ""] if hw.get("back") else [])
    md += ["## Season", "", "*Reference tables; points per pair as above. Labels here are the grading's own (RULE: proven so far, + helps and - hurts; "
           "LEAN: an early sign; no lean: no clear signal; not enough yet: too early to say).*", ""] + overnight(H) + season_tables(H)
    md += ["", "Full tables: tier_grade.md, q_lane.md, swap_board.md, my_swaps.md, money_points.md, rules_side_by_side.md, rule_dates.json."]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
