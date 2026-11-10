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
    (1, "am"): "In the morning, T1 is ordered by ADP, and the higher Boom (his ceiling) goes first when two players are within two picks of each other",
    (1, "pm"): "In the afternoon, T1 is ordered by ETR's projection",
    (2, "am"): "In the morning, T2 is ordered straight by ADP",
    (2, "pm"): "In the afternoon, T2 is ordered by ADP, and ETR breaks ties when two players are within two picks of each other",
    (3, "am"): "In the morning, T3 is ordered by our projection, and ADP decides when two players are within three points",
    (3, "pm"): "In the afternoon, T3 is ordered by ETR's projection, with ADP and then Boom breaking exact ties",
    (4, "am"): "In the morning, T4 is ordered by our projection, and ADP decides when two players are within three points",
    (4, "pm"): "In the afternoon, T4 is ordered by ADP, and ETR breaks ties when two players are within two picks of each other",
    (5, "am"): "In the morning, T5 follows the Tiers button: our projection, with ADP deciding when two players are within three points",
    (5, "pm"): "In the afternoon, T5 is ordered by ADP",
}
TIEBREAKS = {5: ("ownership-tiebreak-t5", "In both windows T5 then puts the less drafted player first when two are within two "
                 "projected points and at least 10 points apart in how often they're drafted")}
SHADOW_REG = {"t5-less-drafted-am": "ownership-tiebreak-t5", "t5-less-drafted-pm": "ownership-tiebreak-t5",
              "pm-t5-vs-old-etr": "pm-t5-adp-value"}     # shadow.json ids whose money verdict sits on another register row
SHADOW_WORDS = {   # shadow.json switch rows in words (the tier ideas carry their own "plain" line in hypotheses.json)
    "pm-t2-adp-etr2": "Afternoon T2's rule in use (ETR breaks ties within two picks) against the old one (within one pick)",
    "pm-t4-adp-etr2": "Afternoon T4's rule in use (ADP, ETR breaking ties within two picks) against the old one (straight ETR)",
    "pm-t5-vs-old-etr": "Afternoon T5's rule in use (ADP) against the old one (ETR's projection), both with the tiebreak",
    "t5-less-drafted-am": "The less-drafted tiebreak in morning T5, against the button's plain order",
    "t5-less-drafted-pm": "The less-drafted tiebreak in afternoon T5, against plain ADP",
}
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


def money_words(v):
    """A money verdict ('RULE for (...)', 'LEAN against', 'no lean (...)', 'pending') in words."""
    v = (v or "pending").split(" (")[0].split(";")[0].strip()
    w, s = lab_words(v), lab_side(v)
    if w == "proven so far":
        return "contest results have proven it so far" if s > 0 else "contest results have proven it wrong so far"
    if w == "an early sign":
        return "contest results show an early sign %s it" % ("for" if s > 0 else "against")
    if w == "no clear signal":
        return "contest results show no clear signal"
    if w == "too early to say":
        return "contest results are too early to say"
    return "contest results are still to come"


def gaining(mean, unit="pair"):
    return "%s %.1f points per %s" % ("gaining" if mean >= 0 else "losing", abs(mean), unit)


def season_read(v, unit="pair"):
    """A points verdict (n, mean, lo, hi, label): 'gaining 1.2 points per pair over 120 pairs (an early sign)'."""
    n, mean, _, _, label = v
    if not n:
        return None
    return "%s over %d %ss (%s)" % (gaining(mean, unit), n, unit, lab_words(label) or "too early to say")


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
def decision_text(rid, reg, mt):
    if rid in reg:
        return reg[rid]["decision"]
    for x in [d for blk in ((mt or {}).get("tiers") or {}).values() if isinstance(blk, dict) for d in blk.get("decisions") or []]:
        if x.get("id") == rid and x.get("decision"):
            return x["decision"]
    for x in (mt or {}).get("splits", []):
        if x.get("id") == rid:
            m = re.match(r"takes:([^:]+):(\w+)", rid)
            if m:
                src, w = m.groups()
                who = {"all": "all your moves off the button"}.get(src, "your moves off the button %s" % TAKE_SRC.get(src, src))
                return "%s, %s" % (who, {"am": "in the morning", "pm": "in the afternoon", "both": "both windows"}.get(w, w))
            return x.get("decision") or rid
    return rid.replace("-", " ")


def lift_words(lift, mine=None):
    if not lift or lift.get("lift10") is None:
        return ""
    s = "teams that followed it finished in the top 10%% %.2f times as often as similar teams (80%% range %.2f to %.2f, %d slates)" % (
        lift["lift10"], lift["range80"][0], lift["range80"][1], lift.get("slates", 0))
    if mine and mine.get("top10_ratio") is not None:
        s += "; your %d such teams, %.2f times" % (mine["teams"], mine["top10_ratio"])
    return s


def monday(shadow, hyp, reg, leans, mt, recs):
    """Each decision in words with a recommendation and its evidence."""
    md = ["## Monday: decisions for today", ""]
    items = []
    for c in shadow:
        n, fv = c["forward_nights"], c["forward"]
        lab = fv.get("label") or ""
        what = SHADOW_WORDS.get(c["id"]) or (hyp.get(c["id"].split(":")[0]) or {}).get("plain") or c["name"]
        if n < FORWARD_NIGHTS or c["kind"] not in ("switch", "candidate") or (c["kind"] == "switch" and not c.get("drop_if")):
            if c["kind"] == "candidate" and lab_side(lab) < 0 and lab_words(lab) in ("proven so far", "an early sign") and fv.get("n", 0) >= 40:
                items.append((c["id"], "%s: drop it early?" % what, "Drop it",
                              "Over its first %d forward nights it has been %s." % (n, season_read((fv["n"], fv["mean"], fv["lo"], fv["hi"], lab)))))
            continue
        read = season_read((fv["n"], fv["mean"], fv["lo"], fv["hi"], lab)) or "no pairs"
        won, lost = lab_side(lab) > 0 and lab_words(lab) != "no clear signal", lab_side(lab) < 0 and lab_words(lab) != "no clear signal"
        if c["kind"] == "switch":
            keep = not lost if c["drop_if"] == "loss" else won
            items.append((c["id"], "%s: keep it for good, or drop it?" % what, "Keep it for good" if keep else "Drop it",
                          "After %d forward nights against the old rule it has been %s." % (n, read)))
        else:
            m = (reg.get((hyp.get(c["id"].split(":")[0]) or {}).get("register"), {}) or {}).get("money_verdict")
            ok = won and lab_side((m or "").split(" (")[0]) >= 0
            items.append((c["id"], "%s: adopt it?" % what, "Adopt it" if ok else "Drop it",
                          "After %d forward nights against the button it has been %s, and %s." % (n, read, money_words(m))))
    for x in leans.get("adopted", []):
        m = (reg.get(x.get("register")) or {}).get("money_verdict", "pending")
        if lab_side(m.split(" (")[0]) < 0 and lab_words(m) in ("proven so far", "an early sign"):
            points_rule = x.get("basis") == "RULE" or ", RULE)" in x.get("evidence", "")
            if lab_words(m) == "proven so far" or not points_rule:
                items.append((x["id"], "%s: drop it on contest results?" % (LEAN_WORDS.get(x["id"]) or x["statement"]).rstrip("."),
                              "Drop it", "%s, and the money policy lets that overturn it." % money_words(m).capitalize()))
    doc = json.load(open(os.path.join(REP, "money_proposals.json"))) if os.path.exists(os.path.join(REP, "money_proposals.json")) else {}
    new = []
    for x in (doc.get("proposals", []) if isinstance(doc, dict) else doc):
        if not isinstance(x, dict) or not x.get("proposed"):
            continue
        rid, cur = x.get("id", ""), (x.get("current_money") or "pending").split(" (")[0].split(";")[0]
        read = (x.get("read") or {})
        if cur.startswith("none"):
            if lab_words(x["proposed"]) in ("proven so far", "an early sign"):
                new.append("%s (%s; %s)" % (decision_text(rid, reg, mt), money_words(x["proposed"]), lift_words(read.get("lift"))))
            continue
        adopted = any(a.get("register") == rid for a in leans.get("adopted", []))
        rec = "Record the new reading"
        if adopted and lab_side(x["proposed"]) < 0:
            points_rule = any(a.get("register") == rid and (a.get("basis") == "RULE") for a in leans.get("adopted", []))
            rec = ("Record it and drop the rule (contest results proven against it)" if lab_words(x["proposed"]) == "proven so far"
                   else "Record it but keep the rule (an early sign can't overturn a points rule)" if points_rule
                   else "Record it and drop the rule (the money policy: an early sign wins when points disagree)")
        items.append((rid, "Contest results on \"%s\" moved from %s to %s." % (
            decision_text(rid, reg, mt), (lab_words(cur) or "still to come"), lab_words(x["proposed"]) or x["proposed"]),
            rec, (lift_words(read.get("lift"), read.get("mine")) or "").capitalize() + "."))
    if not items and not new:
        return md + ["Nothing is ready to decide this week.", ""]
    for rid, q, rec, ev in items:
        md += ["- **%s** I recommend: %s. %s" % (q, (recs.get(rid) or rec)[0].lower() + (recs.get(rid) or rec)[1:], ev), ""]
    if new:
        md += ["- **New splits worth recording:** %s." % "; ".join(new), ""]
    return md


# ---------------------------------------------------------------- one tier
def money_short(v):
    """A money verdict in a few words: 'proven so far', 'an early sign against', 'still to come'..."""
    v = (v or "pending").split(" (")[0].split(";")[0].strip()
    w, s = lab_words(v), lab_side(v)
    if w == "proven so far":
        return "proven so far" if s > 0 else "proven wrong so far"
    if w == "an early sign":
        return "an early sign %s" % ("for" if s > 0 else "against")
    return w or "still to come"


def rules_played(t, reg, by_reg, shadow, leans):
    def status(rid):
        st = by_reg.get(rid, "kept")
        if st == "provisional":
            c = next((c for c in shadow if c["id"] == rid or SHADOW_REG.get(c["id"]) == rid), None)
            words = "on trial%s" % (", %d of %d nights in" % (min(c["forward_nights"], FORWARD_NIGHTS), FORWARD_NIGHTS) if c else "")
        else:
            words = {"kept": "kept, nothing has beaten it", "adopted": "adopted",
                     "RULE": "proven so far on points"}.get(st, st)
        return "%s; contest results: %s" % (words, money_short((reg.get(rid) or {}).get("money_verdict")))
    am, pm = SWITCHES[t]
    s = ["%s (%s). %s (%s)." % (RULE_WORDS[(t, "am")], status(am), RULE_WORDS[(t, "pm")], status(pm))]
    if t in TIEBREAKS:
        s.append("%s (%s)." % (TIEBREAKS[t][1], status(TIEBREAKS[t][0])))
    ms = lambda rid: money_short((reg.get(rid) or {}).get("money_verdict"))
    if t == 1 and "pricey-flags:T1" in reg:
        s.append("PRICEY players go last here as everywhere, and in T1 contest results read it on its own: %s." % ms("pricey-flags:T1"))
    if t >= 3:
        s.append("VALUE players go first in this tier (contest results: %s)." % ms("value-up-middle-t5"))
    if t == 5:
        s.append("In the afternoon you also raise beneficiaries, a player whose teammate is tagged or out (contest results: %s)." % ms("pm-t5-beneficiary"))
    return [" ".join(x for x in s if x), ""]


def everywhere(reg):
    """The rules every tier shares, said once."""
    ms = lambda rid: money_short((reg.get(rid) or {}).get("money_verdict"))
    return ["**In every tier.** The Tiers button sets each player's tier from his ADP, moved at most one tier toward where our "
            "projection puts him (contest results on that cap: %s). Inside a tier, PRICEY players (a tier below their ADP on our "
            "projection) go last (%s), and in T3 to T5 VALUE players (a tier above) go first. A Questionable player keeps his tier "
            "in the morning (%s) and drops two tiers in the afternoon (%s). Contest results grade a rule by how often teams that "
            "followed it finished in the top 10%%; points grade it on head-to-head pairs: two players in the same tier within 4 "
            "picks of each other's ADP, where the points a pair are how much more the chosen player scored (a scratch counts as "
            "what his swap scored)." % (ms("one-tier-cap"), ms("pricey-flags"), ms("am-questionable-no-push"), ms("pm-questionable-back-two")), ""]


def did_they_work(H, last, t):
    s = []
    for w, label in (("am", "Morning"), ("pm", "Afternoon")):
        rn = [r for r in H if r["date"] == last and r["window"] == w]
        if not rn:
            s.append("%s: no board on file." % label)
            continue
        _, _, h2h, _, _, flags, _ = G.grade([r for r in H if r["date"] == last], rn[0]["pod"], w, None, [("T", {t}, None)])[0]
        bits = []
        for src in (("Ours", "ADP") if w == "am" else ("ETR", "ADP")):
            g = h2h[src][0].get(last, [])
            if g:
                bits.append("%s on %d of %d (%+.1f points a pair)" % (SRC_WORDS[src], sum(1 for x in g if x > 0), len(g), sum(g) / len(g)))
        fl = ["%s right %d of %d" % (how, sum(1 for x in flags[f].get(last, []) if x > 0), len(flags[f].get(last, [])))
              for f, how in (("VALUE", "VALUE-first"), ("PRICEY", "PRICEY-last")) if flags[f].get(last)]
        s.append("%s%s: %s%s." % (label, " (fallback board)" if "fallback" in rn[0]["board"] else "",
                                  "where they disagreed, your board beat " + " and ".join(bits) if bits else "your board matched the straight orders",
                                  "; " + ", ".join(fl) if fl else ""))
    seas = []
    for w, label, main in (("am", "morning", "Ours"), ("pm", "afternoon", "ETR")):
        _, nights, h2h, _, _, _, _ = G.grade(H, "6", w, "primary", [("T", {t}, None)])[0]
        reads = []
        for src in (main, "ADP"):
            if h2h[src][0]:
                n, mean, _, _, lab = G.verdict(h2h[src][0], h2h[src][1])
                w_ = lab_words(lab)
                reads.append("%+.1f against %s (%d pairs%s)" % (mean, SRC_WORDS[src].replace("our projection", "ours"), n,
                                                             ", %s" % w_ if w_ in ("an early sign", "proven so far") else ""))
        if reads:
            seas.append("%s %s" % (label, ", ".join(reads)))
    if seas:
        s.append("Season, points a pair for your board: %s." % "; ".join(seas))
    return [" ".join(s), ""]


def your_moves(last, t, names_in, hand_moves):
    s = []
    tk = [r for r in csv.DictReader(open(os.path.join(REP, "takes_history.csv"))) if r["date"] == last and int(r["tier"]) == t]
    for w, label in (("am", "Morning"), ("pm", "Afternoon")):
        xs = [r for r in tk if r["window"] == w]
        if not xs:
            continue
        g = [float(r["gain"]) for r in xs]
        big = max(xs, key=lambda r: abs(float(r["gain"])))
        s.append("%s: %d move%s off the Tiers button, %d right (%+.1f points a move); the biggest, %s ahead of %s %s, was %s by %s points." % (
            label, len(xs), "" if len(xs) == 1 else "s", sum(1 for x in g if x > 0), sum(g) / len(g), short(big["you_first"]),
            short(big["button_first"]), TAKE_SRC.get(big.get("source") or "OTHER", big.get("source")),
            "right" if float(big["gain"]) > 0 else "wrong", round(abs(float(big["gain"])), 1 if abs(float(big["gain"])) < 1 else None)))
    calls = [r for r in csv.DictReader(open(os.path.join(REP, "misses.csv"))) if r["date"] == last and r["kind"] in ("am_call", "pm_call")
             and r["player"] in names_in]
    calls.sort(key=lambda r: r["closer"] != "wrong")
    if calls:
        s.append("Your calls: %s." % (". ".join("%s %s (%s), %s: %s" % (
            short(r["player"]), "raised" if r["note"].startswith("raised") else "faded" if r["note"].startswith("faded") else "moved",
            "morning, against ADP" if r["kind"] == "am_call" else "afternoon, against ETR", r["closer"],
            (r["note"].split("; ", 1)[1] if "; " in r["note"] else r["note"]).strip().rstrip(".")) for r in calls[:2]) +
            (". %d more in misses.csv" % (len(calls) - 2) if len(calls) > 2 else "")))
    if hand_moves:
        s.append(hand_moves)
    return [" ".join(s) if s else "No moves off the Tiers button in this tier last night.", ""]


def recap(H, last, t):
    pm = {r["player_id"]: r for r in H if r["date"] == last and r["window"] == "pm"}
    am = {r["player_id"]: r for r in H if r["date"] == last and r["window"] == "am"}
    rows = [r for pid, r in {**am, **pm}.items() if int(r["tier"]) == t and (t != 5 or (num(r["adp"]) is not None and num(r["adp"]) < G.cap(r)))]
    rows.sort(key=G.adp)
    led = {r["player_id"]: r for r in csv.DictReader(open(os.path.join(HERE, "analysis", "nba", "ledger.csv"))) if r["date"] == last}
    sw = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        if r["date"] == last:
            sw[r["out_id"]].append(r)
    md, inline, idle = [], [], []
    for r in rows:
        l = led.get(r["player_id"]) or {}
        note = (l.get("note") or "").strip() or (l.get("draft") or "").strip()
        tag = " Tagged %s at the lock." % r["tag"] if QT.match(r["tag"] or "") and r["tag"].lower() not in note.lower() else ""
        brk = " A top score for his round." if r["breaker"] == "1" else ""
        if r["scratched"] == "1":
            xs = sorted(sw.get(r["player_id"], []), key=lambda x: -int(x["teams"]))
            if not xs:
                idle.append(short(r["name"]))
                continue
            md.append("- **%s** (%s): scratched%s; swaps landed on %s." % (r["name"], r["team"], " (%s)" % r["tag"] if r["tag"] else "",
                      ", ".join("%s (%d teams, %.0f points)" % (short(x["swap"]), int(x["teams"]), float(x["swap_fp"])) for x in xs[:3])))
        elif (l.get("result") or "") == "in line" and not tag and not brk:
            extra = re.sub(r"^in line[:,.]?\s*", "", note, flags=re.I).rstrip(".")
            inline.append(short(r["name"]) + (", %s" % (extra[0].lower() + extra[1:]) if extra else ""))
        else:
            md.append("- **%s** (%s): %s%s%s" % (r["name"], r["team"], note or "no box line", tag, brk))
    if inline:
        md.append("- In line: %s." % "; ".join(inline))
    if idle:
        md.append("- Scratched, no swaps credited: %s." % names(idle))
    return (md or ["No players in this tier last night."]) + [""], {r["name"] for r in rows}


def contest_view(t, mt):
    blk = ((mt or {}).get("tiers") or {}).get(str(t)) or {}
    s = []
    for w, label in (("am", "morning"), ("pm", "afternoon")):
        e = (blk.get("exposure") or {}).get(w)
        if not e or not e.get("my_teams"):
            continue
        ppt = e.get("picks_per_team") or {}
        ps = [x for x in e.get("players", []) if x.get("mine") is not None]
        over = [x for x in sorted(ps, key=lambda x: x["field"] - x["mine"])[:1] if x["mine"] - x["field"] >= 0.05]
        s.append("Your %d %s teams took %.1f T%d players each to the field's %.1f%s." % (
            e["my_teams"], label, ppt.get("mine") or 0, t, ppt.get("field") or 0,
            ", heaviest on %s (%s of yours, %s of the field)" % (short(over[0]["name"]), pct(over[0]["mine"]), pct(over[0]["field"])) if over else ""))
    dr = (blk.get("drafted") or {}).get("pm") or (blk.get("drafted") or {}).get("am") or {}
    fl = ["%s %s" % (lab, ", ".join("%s %s" % (short(x["name"]), pct(x["drafted"])) for x in dr[lab][:4]))
          for lab in ("VALUE", "PRICEY") if dr.get(lab)]
    if fl:
        s.append("How often the flagged players were drafted (share of pods): %s." % "; ".join(fl))
    e = (blk.get("exposure") or {}).get("pm") or (blk.get("exposure") or {}).get("am") or {}
    ls = [x for x in e.get("players", []) if x.get("lift10") is not None]
    paid = sorted([x for x in ls if x["lift10"] >= 1.3], key=lambda x: -x["lift10"])[:2]
    hurt = sorted([x for x in ls if x["lift10"] <= 0.7], key=lambda x: x["lift10"])[:2]
    if paid or hurt:
        s.append("In the standings, %s." % "; ".join(
            (["teams holding %s made the top 10%% %.1f times as often as the field" % (short(paid[0]["name"]), paid[0]["lift10"])] if paid else []) +
            ["%s %.1f times" % (poss(short(x["name"])), x["lift10"]) for x in paid[1:]] +
            ["%s holders %s" % (poss(short(x["name"])), "never got there" if x["lift10"] == 0 else "only %.1f times" % x["lift10"]) for x in hurt]))
    return [" ".join(s) if s else "No contest data for this tier last night.", ""]


def leaning(t, shadow, hyp, reg, shown):
    s, again = [], []
    for c in shadow:
        if not (c["kind"] == "candidate" or (c["kind"] == "switch" and c.get("drop_if"))) or t not in c["tiers"]:
            continue
        base = c["id"].split(":")[0]
        what = SHADOW_WORDS.get(c["id"]) or (hyp.get(base) or {}).get("plain") or c["name"]
        if c["id"] in shown:
            again.append((hyp.get(base) or {}).get("name") or what[0].lower() + what[1:].split(",")[0])
            continue
        shown.add(c["id"])
        rid = (hyp.get(base) or {}).get("register") or SHADOW_REG.get(c["id"], c["id"])
        rows = [x for x in shadow if x["id"].split(":")[0] == base] if ":" in c["id"] else [c]
        shown.update(x["id"] for x in rows)
        wn = {"am": "morning ", "pm": "afternoon "}
        back = ["%s%+.1f a pair (%d pairs, %s)" % (wn.get(x["id"].split(":")[1], "") if ":" in x["id"] else "", x["season"]["mean"],
                                                      x["season"]["n"], lab_words(x["season"]["label"]) or "too early to say")
                for x in rows if x["season"].get("n")]
        fwd = ["%+.1f a pair so far" % x["forward"]["mean"] for x in rows if x["forward"].get("n")]
        s.append("- %s. %s%s, %d of %d nights in%s; season backtest %s; contest results: %s." % (
            what, "On trial" if c["kind"] == "switch" else "Under test", ", each window decided on its own" if len(rows) > 1 else "",
            min(c["forward_nights"], FORWARD_NIGHTS), FORWARD_NIGHTS, " (%s)" % ", ".join(fwd) if fwd else "",
            "; ".join(back) or "no pairs", money_short((reg.get(rid) or {}).get("money_verdict"))))
    if again:
        s.append("- Also testing here (above): %s." % "; ".join(sorted(set(again))))
    return (s or ["Nothing under test in this tier."]) + [""]


def today_tier(t, pool, ben, pod):
    if pool is None:
        return ["Today's slate isn't on the mirror yet.", ""]
    rs = [r for r in pool if r["c"] == t and r["drafted"]]
    s = []
    for r in rs:
        if QT.match(r["tag"]):
            q = r["tag"].lower().startswith("q")
            s.append("%s (%s) is %s, %s to play on our calibrated chance: %s." % (
                r["name"], r["team"], r["tag"], pct(r["play"]),
                ("he stays in T%d in the morning and drops to T%d in the afternoon" % (t, t + 2) if t <= 3 else
                 "he stays in T%d in the morning and drops to T5 in the afternoon" % t if t == 4 else "T5 is the bottom tier, so he stays put") if q
                else "he stays in T%d in both windows (only Questionable players are pushed)" % t))
    for f, how in (("VALUE", "VALUE (our projection rates him a tier above his ADP)"), ("PRICEY", "PRICEY (a tier below)")):
        xs = [r for r in rs if r["flag"] == f]
        if xs:
            s.append("%s: %s." % (how, ", ".join("%s (ADP %.1f)" % (r["name"], r["adp"]) for r in xs)))
    bs = [(r, tg) for r, tg in ben if (r["c"] if r.get("drafted") else 5) == t]
    if bs:
        by = collections.OrderedDict()
        for r, tg in bs:
            by.setdefault(short(tg["name"]), []).append("%s (%s)" % (r["name"], "ADP %.1f" % r["adp"] if r.get("drafted") else "undrafted"))
        s.append("Beneficiaries to watch: %s." % "; ".join("if %s sits, %s" % (k, names(v)) for k, v in by.items()))
    return [" ".join(s) if s else "Nothing flagged or tagged in this tier today.", ""]


# ---------------------------------------------------------------- draft card and back page
def draft_card(mt, reg, night, hand_card):
    md = ["## The draft card", ""]
    c = (mt or {}).get("card") if (mt or {}).get("night") == night else None
    if c:
        def k(key, what):
            x = c.get(key)
            return "%s %d (%d top 10%%)" % (what, x["teams"], x["top10"]) if x else None
        bits = []
        for turn in ("1/2", "2/3"):
            got = [b for b in (k("%s faller" % turn, "took a faller on"), k("%s reach" % turn, "reached on"),
                               k("%s trust" % turn, "trusted ADP on")) if b]
            if got:
                bits.append("at the %s turn you %s" % (turn, ", ".join(got)))
        hi = c.get("2/3 reach: higher projection")
        if hi:
            bits.append("%d of the 2/3-turn reaches went toward the higher projection" % hi["teams"])
        for key, what in (("same-position teammates", "held same-position teammates on"), ("opposing stars", "paired opposing stars on")):
            b = k(key, what)
            if b:
                bits.append("you " + b)
        res = mt.get("results") or {}
        md.append("Last night, of your %s teams, %s." % (res.get("teams", "?"), "; ".join(bits) if bits else "none reached a turn the card reads"))
    else:
        md.append("Last night's turns aren't read yet (the contest side's file is from an earlier night).")
    if hand_card:
        md[-1] += " " + hand_card
    md += ["", "Where contest results stand: %s. %s" % (
        "; ".join("%s, %s" % (what, money_short((reg.get(rid) or {}).get("money_verdict"))) for _, what, rid in DRAFT_CARD),
        DRAFT_NOTE), ""]
    return md


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
                 "ETR's by %.1f; ranked against how they finished, ours scored %.2f and ETR's %.2f (1 is a perfect order)." % (
                     len(both), e_our, e_etr, c_our or 0, c_etr or 0))
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
            if h["status"] == "retired":
                if h.get("retired", "") >= (dt.date.fromisoformat(today) - dt.timedelta(days=7)).isoformat():
                    hs.append("the %s was retired on %s and taken out of the board" % (name.lower(), h["retired"][5:]))
                continue
            fwd = HY.summary(HY.gains(rule, history, since=h["opened"]))
            recent = dates[-HY.RECHECK_DAYS:] if dates else []
            rc = HY.summary(HY.gains(rule, history, since=recent[0])) if h["status"] == "adopted" and recent else None
            p = HY.proposal(h, fwd, rc)
            x = rc if h["status"] == "adopted" else fwd
            if x:
                hs.append("the %s (%s) lands %.2f points %s than the base projection on %d players%s%s" % (
                    name.lower(), "in the model" if h["status"] == "adopted" else "under test",
                    abs(x["mean"]), "closer" if x["mean"] >= 0 else "further off", x["n"],
                    " (%d of %d nights in)" % (min(x["nights"], HY.FORWARD_DAYS), HY.FORWARD_DAYS) if h["status"] == "testing" else " over the last %d nights" % HY.RECHECK_DAYS,
                    {"**adopt?**": ": ready to adopt?", "**reject?**": ": time to reject it?", "**retire?**": ": time to retire it?"}.get(p.split(" ")[0], "")))
        if hs:
            s.append("Projection hypotheses: %s." % "; ".join(hs))
    except Exception as e:                                      # the back page must not fail the report
        s.append("Projection hypotheses not read (%s)." % e)
    if recheck_due(today):
        s.append("The monthly re-check is due this month.")
    if hand_back:
        s.append(hand_back)
    bad = problems(health_lines)
    s2 = "Data: " + ("; ".join(bad) + "." if bad else "everything for last night came in, and today's inputs were ready on time.")
    md += [" ".join(s), "", s2, "", "Season tables are below; every player's night is in the ledger (analysis/nba/ledger.csv), "
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
    today = a.today or dt.datetime.now(dt.timezone.utc).astimezone(PT).date().isoformat()
    _, _, _, latest = today_slate(a.mirror)
    last = max(r["date"] for r in H)
    hw = hand(last)
    hl = health(a.mirror, today, latest)
    slate, lock, pod, pool, ben = today_pool(a.mirror, H)
    day = lambda d: dt.date.fromisoformat(d).strftime("%A %-m/%-d")
    md = ["# NBA morning report, %s" % day(today), "", "*Last night: %s's main slate.*" % day(last), "", "## Front page", ""]
    md += [hw["front"], ""] if hw.get("front") else front_page(last, H, mt, hl, (slate, lock, pod) if slate else None)
    if dt.date.fromisoformat(today).weekday() == 0:
        md += monday(shadow, hyp, reg, leans, mt, hw.get("proposals") or {})
    shown = set()
    md += everywhere(reg)
    for t in range(1, 6):
        rc, in_tier = recap(H, last, t)
        md += ["## T%d" % t, "", "**The rules we played.** "] 
        md[-1] += rules_played(t, reg, by_reg, shadow, leans)[0]
        md += ["", "**Did they work last night.** " + did_they_work(H, last, t)[0], ""]
        md += ["**Your moves.** " + your_moves(last, t, in_tier, (hw.get("moves") or {}).get(str(t)))[0], "",
               "**Player recap.**", ""] + rc
        md += ["**Contest view.** " + contest_view(t, mt)[0], "", "**What we're leaning toward.**", ""] + leaning(t, shadow, hyp, reg, shown)
        md += ["**Today in T%d.** " % t + today_tier(t, pool, ben, pod)[0], ""]
    md += draft_card(mt, reg, last, hw.get("card"))
    md += back_page(H, last, hl, today, hw.get("back"))
    md += ["## Season", "", "*Reference tables; points per pair as above. Labels here are the grading's own (RULE: proven so far; "
           "LEAN: an early sign; no lean: no clear signal; not enough yet: too early to say).*", ""] + overnight(H) + season_tables(H)
    md += ["", "**Adopted and rules** (leans.json; points status, money verdict)."]
    for x in leans["adopted"]:
        md.append("- %s, %s: %s" % (status[x["id"]], money(x.get("register")), x["statement"]))
    md += ["", "**Paused**: " + ("; ".join(x["statement"] for x in leans.get("paused", [])) or "none"), "",
           "Full tables: tier_grade.md, tier_rules.md, q_lane.md, shadow.md, swap_board.md, my_swaps.md, money_points.md, decision_register.csv."]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
