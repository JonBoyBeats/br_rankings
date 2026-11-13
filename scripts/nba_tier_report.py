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


def money_words(v):
    """A money verdict ('RULE for (...)', 'LEAN against', 'no lean (...)', 'pending') in words, with its direction."""
    return "contest results: " + money_short(v)


def gaining(mean, unit="pair"):
    return "%s %.1f points per %s" % ("gaining" if mean >= 0 else "losing", abs(mean), unit)


def season_read(v, unit="pair"):
    """A points verdict (n, mean, lo, hi, label): 'gaining 1.2 points per pair over 120 pairs (an early sign it helps)'."""
    n, mean, _, _, label = v
    if not n:
        return None
    return "%s over %d %ss (%s)" % (gaining(mean, unit), n, unit, said(label, mean) if n >= 40 else "too early to say")


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


def biggest_bets(night, mt):
    """Your three biggest overweights against the field last night (both windows pooled) and how each went."""
    if not mt or mt.get("night") != night:
        return []
    den, acc = {}, {}
    for k, blk in (mt.get("tiers") or {}).items():
        if not k.isdigit() or not isinstance(blk, dict):
            continue
        for w, e in (blk.get("exposure") or {}).items():
            if not e or not e.get("my_teams"):
                continue
            den[w] = (e["my_teams"], e["field_teams"])
            for x in e.get("players", []):
                if x.get("mine") is not None:
                    acc.setdefault(x["name"], {})[w] = x
    if not den:
        return []
    my_n, f_n = sum(m for m, _ in den.values()), sum(f for _, f in den.values())
    rows = []
    for name, by in acc.items():
        mine = sum(by[w]["mine"] * den[w][0] for w in by) / my_n
        field = sum(by[w]["field"] * den[w][1] for w in by) / f_n
        heavy = max(by, key=lambda w: by[w]["mine"])
        rows.append((mine - field, name, mine, field, heavy, by[heavy]))
    rows.sort(reverse=True)
    led = {r["name"]: r for r in csv.DictReader(open(os.path.join(HERE, "analysis", "nba", "ledger.csv"))) if r["date"] == night}
    md = ["**Your biggest bets.**", ""]
    for _, name, mine, field, heavy, x in rows[:3]:
        l = led.get(name) or {}
        note = (l.get("note") or l.get("draft") or "").strip() or "No box line."
        lift = x.get("lift10")
        md.append("- **%s**, on %s of your teams (%s of your %s ones) against %s of the field. %s%s" % (
            name, pct(mine), pct(x["mine"]), {"am": "morning", "pm": "afternoon"}[heavy], pct(field), note,
            "" if lift is None else " His holders made the top 10%% %s." % (
                "%.1f times as often as the field" % lift if lift >= 0.1 else "almost never")))
    return md + [""]


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
        if c["kind"] == "check" and n >= FORWARD_NIGHTS:
            lost = lab_side(lab) < 0 and lab_words(lab) in ("proven so far", "an early sign")
            items.append((c["id"], "%s: keep it?" % (SHADOW_WORDS.get(c["id"]) or c["name"]), "Drop it" if lost else "Keep it",
                          "After %d nights its check has been %s." % (n, season_read((fv["n"], fv["mean"], fv["lo"], fv["hi"], lab)) or "without pairs")))
            continue
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
    testing = collections.Counter(t for h in hyp.values() if h.get("status") == "testing" for t in h["tiers"])
    for k, h in hyp.items():
        if h.get("status") != "queued":
            continue
        full = [t for t in h["tiers"] if testing[t] >= 3]
        if not full:
            items.append((k, "%s: start testing it?" % h.get("plain", h["idea"]), "Start it", "A test slot is free in T%s." % "/T".join(map(str, h["tiers"]))))
        else:
            now = [(hyp[x].get("name") or x) for x, g in hyp.items() if g.get("status") == "testing" and set(g["tiers"]) & set(full)]
            items.append((k, "%s: it's ready, but T%s already has three tests (%s). Drop one to start it?" % (
                h.get("plain", h["idea"]), "/T".join(map(str, full)), names(now)), "Your call", h.get("why", "").split(":")[-1].strip().rstrip(".") + "."))
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
            decision_text(rid, reg, mt), said(cur), said(x["proposed"])),
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
    """A money verdict in a few words with its direction: 'proven to help so far', 'an early sign it hurts'..."""
    return said((v or "pending").split(" (")[0].split(";")[0].strip())


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


def status_of(rid, by_reg, reg, shadow):
    """One of the five statuses for a rule in use, by its register id."""
    st = by_reg.get(rid)
    if st is None and (rid or "").startswith("kept-"):
        m = (reg.get(rid) or {}).get("money_verdict") or ""
        read = KEPT_READ.get(rid) if not lab_words(m) else m
        if not read:
            return "in use, original rule"
        words = ("contest results say it helps" if lab_side(read) > 0 and lab_words(read) in ("proven so far", "an early sign") else
                 "contest results say it hurts" if lab_side(read) < 0 and lab_words(read) in ("proven so far", "an early sign") else
                 "contest results: no difference from the alternative")
        return "in use, original rule; %s%s" % (words, ", first read, confirmed Monday" if not lab_words(m) else "")
    m = (reg.get(rid) or {}).get("money_verdict")
    if st == "RULE" and lab_words(m) == "proven so far" and lab_side(m) > 0:
        return "locked in"
    c = next((c for c in shadow if c["id"] == rid or SHADOW_REG.get(c["id"]) == rid or (rid == "one-tier-cap" and c["id"] == "one-tier-cap")), None)
    if not c:
        return "in use, on trial"
    n = min(c["forward_nights"], FORWARD_NIGHTS)
    return "in use, on trial, " + ("night %d of %d" % (n, FORWARD_NIGHTS) if n else "its 14-night check starts tonight")


def status_key():
    return ["**How to read the statuses.**", ""] + ["- **%s**: %s" % kv for kv in STATUS_KEY] + [""]


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


def take_note(date, r):
    """Why a take was made, in words: the note it followed, or news, or your own read."""
    src = r.get("source") or "OTHER"
    if src == "NEWS":
        return "on news"
    if src == "OTHER":
        return "your own read"
    words = []
    for who, f in (("ETR", "etr_matchups"), ("Bagel", "zakarian")):
        if who not in src:
            continue
        p = os.path.join(HERE, "analysis", "nba", "takes", "%s_%s.csv" % (date, f))
        notes = {x["player"]: x["stance"] for x in csv.DictReader(open(p))} if os.path.exists(p) else {}
        up, down = notes.get(r["you_first"]), notes.get(r["button_first"])
        if up in ("Great", "Good", "Like", "Lean"):
            words.append("%s %s %s" % (who, {"Great": "called", "Good": "called", "Like": "liked", "Lean": "leaned to"}[up],
                                       short(r["you_first"]) + (" a %s matchup" % up.lower() if up in ("Great", "Good") else "")))
        elif down in ("Bad", "Fade"):
            words.append("%s %s %s" % (who, "called" if down == "Bad" else "faded", short(r["button_first"]) + (" a bad matchup" if down == "Bad" else "")))
    return " and ".join(words) or TAKE_SRC.get(src, src)


def t5_menu(H, last, mt):
    """T5 graded as a menu: your share of each T5 player against the field's, how he scored against the T5 average, and
    whether your overweights beat the field's T5 picks; late-news hedges apart."""
    blk = ((mt or {}).get("tiers") or {}).get("5") or {}
    if not blk.get("exposure") or (mt or {}).get("night") != last:
        return ["No contest data for T5 last night.", ""]
    rows = {}
    for r in H:
        if r["date"] == last:
            rows.setdefault(r["name"], {})[r["window"]] = r
    out = []
    hedges = []
    for w, label in (("am", "morning"), ("pm", "afternoon")):
        e = blk["exposure"].get(w)
        if not e or not e.get("my_teams"):
            continue
        ps = [dict(x, act=rows.get(x["name"], {}).get(w, {}).get("slot")) for x in e.get("players", [])]
        ps = [x for x in ps if x["act"] is not None]
        if not ps:
            continue
        fw = sum(x["field"] for x in ps)
        mw = sum(x["mine"] or 0 for x in ps)
        avg_f = sum(x["field"] * x["act"] for x in ps) / fw if fw else 0
        avg_m = sum((x["mine"] or 0) * x["act"] for x in ps) / mw if mw else None
        # a hedge: a T5 player whose teammate was tagged Q/D/GTD at this window's record
        tagged = {}
        for n, by in rows.items():
            r = by.get(w)
            if r and QT.match(r["tag"] or ""):
                tagged.setdefault(r["team"], []).append(r)
        over = sorted([x for x in ps if (x["mine"] or 0) - x["field"] >= 0.05], key=lambda x: x["field"] - (x["mine"] or 0))
        hedge_names = set()
        for x in over:
            r = rows[x["name"]][w]
            tms = [tg for tg in tagged.get(r["team"], []) if tg["name"] != x["name"]]
            if tms:
                hedge_names.add(x["name"])
                tg = tms[0]
                sat = tg["scratched"] == "1" or num(tg["min"]) == 0
                hedges.append("%s, on %s of your %s teams (%s of the field) for %s (%s at the lock): %s." % (
                    x["name"], pct(x["mine"]), label, pct(x["field"]), tg["name"], tg["tag"],
                    "%s sat and %s scored %.0f, so the hedge %s" % (short(tg["name"]), short(x["name"]), x["act"], "paid" if x["act"] >= avg_f else "didn't pay")
                    if sat else "%s played, so the hedge wasn't needed; %s scored %.0f" % (short(tg["name"]), short(x["name"]), x["act"])))
        bets = [x for x in over if x["name"] not in hedge_names][:3]
        out.append("Your %s teams' T5 picks averaged %s points, the field's %.0f%s." % (
            label, "%.0f" % avg_m if avg_m is not None else "-", avg_f,
            ", about level" if avg_m is not None and abs(avg_m - avg_f) < 1 else
            ": your overweights beat the field's T5 picks" if avg_m is not None and avg_m > avg_f else
            ": the field's T5 picks did better" if avg_m is not None else ""))
        for x in bets:
            out.append("- **%s**, %s of yours against %s of the field: scored %.0f, %s the T5 average." % (
                x["name"], pct(x["mine"]), pct(x["field"]), x["act"],
                "%.0f over" % (x["act"] - avg_f) if x["act"] >= avg_f else "%.0f under" % (avg_f - x["act"])))
        out.append("")
    if hedges:
        out += ["**Late-news hedges.**", ""] + ["- " + h for h in hedges] + [""]
    return out or ["No contest data for T5 last night.", ""]


def rules_played(t, reg, by_reg, shadow, leans):
    am, pm = SWITCHES[t]
    st = lambda rid: status_of(rid, by_reg, reg, shadow)
    s = ["%s (%s). %s (%s)." % (RULE_WORDS[(t, "am")], st(am), RULE_WORDS[(t, "pm")], st(pm))]
    if t in TIEBREAKS:
        s.append("%s (%s)." % (TIEBREAKS[t][1], st(TIEBREAKS[t][0])))
    if t >= 3:
        s.append("VALUE players go first in this tier (%s)." % st("value-up-middle-t5"))
    if t == 5:
        s.append("In the afternoon you also raise beneficiaries, a player whose teammate is tagged or out (%s)." % st("pm-t5-beneficiary"))
    return [" ".join(s), ""]


def everywhere(reg, by_reg, shadow):
    """The rules every tier shares, said once."""
    st = lambda rid: status_of(rid, by_reg, reg, shadow)
    return ["**In every tier.** A player's tier is his ADP tier, moved at most one tier toward our projection's (%s). PRICEY "
            "players (a tier below their ADP on our projection) go last in their tier (%s); VALUE players go first in "
            "T3 to T5. A Questionable player keeps his tier in the morning (%s) and drops two in the afternoon (%s). A close call "
            "is two players in the same tier within 4 picks of ADP; points on it are how much more the chosen one scored. Contest "
            "results are how often teams that followed a rule made the top 10%%." % (
                st("one-tier-cap"), st("pricey-flags"), st("am-questionable-no-push"), st("pm-questionable-back-two")), ""]


def your_moves(H, last, t, hand_moves):
    """Each move off the button in this tier: who over whom, why, what each scored, right or wrong. A move on news is
    "forced" when a player in the pair was tagged Out at the window's record (not a judgment, so not graded) and a "news
    judgment" otherwise (a Questionable player moved, or a role or minutes change); then the week's record by source,
    which kind of news judgment lost, and one takeaway."""
    slot = {(r["date"], r["window"], r["name"]): r for r in H}
    def scored(d, w, n):
        r = slot.get((d, w, n))
        if not r:
            return "?"
        return "scratched, his swap %.0f" % r["slot"] if r["scratched"] == "1" else "%.0f" % r["slot"]
    def kind(r):
        if (r.get("source") or "OTHER") != "NEWS":
            return None
        a, b = slot.get((r["date"], r["window"], r["you_first"])), slot.get((r["date"], r["window"], r["button_first"]))
        if any(x and (x["tag"] or "").lower().startswith("o") for x in (a, b)):
            return "forced"
        if b and QT.match(b["tag"] or "") and not (a and QT.match(a["tag"] or "")):
            return "q-down"
        if a and QT.match(a["tag"] or "") and not (b and QT.match(b["tag"] or "")):
            return "q-up"
        return "role"
    kind_words = {"q-down": "a Questionable player moved down", "q-up": "a Questionable player moved up", "role": "a role or minutes change"}
    tk = list(csv.DictReader(open(os.path.join(REP, "takes_history.csv"))))
    md = []
    for r in [r for r in tk if r["date"] == last and int(r["tier"]) == t]:
        g, k = float(r["gain"]), kind(r)
        why = "forced: a player ruled out" if k == "forced" else "news judgment (%s)" % kind_words[k] if k else take_note(last, r)
        md.append("- %s: **%s** ahead of **%s**, %s. %s scored %s, %s %s%s." % (
            "Morning" if r["window"] == "am" else "Afternoon", short(r["you_first"]), short(r["button_first"]), why,
            short(r["you_first"]), scored(last, r["window"], r["you_first"]), short(r["button_first"]),
            scored(last, r["window"], r["button_first"]),
            " (not graded)" if k == "forced" else ": " + ("right" if g > 0 else "wrong" if g < 0 else "even")))
    md = [m.replace("Jr..", "Jr.") for m in md]
    week = (dt.date.fromisoformat(last) - dt.timedelta(days=6)).isoformat()
    by, nk, forced = collections.defaultdict(lambda: [0, 0]), collections.defaultdict(lambda: [0, 0]), 0
    for r in tk:
        if not (week <= r["date"] <= last and int(r["tier"]) == t):
            continue
        k = kind(r)
        if k == "forced":
            forced += 1
            continue
        name = "news judgments" if k else {"OTHER": "your own reads"}.get(r.get("source") or "OTHER",
                                                                         "%s notes" % (r.get("source") or "").replace("+", " and "))
        by[name][0] += float(r["gain"]) > 0
        by[name][1] += 1
        if k:
            nk[k][0] += float(r["gain"]) > 0
            nk[k][1] += 1
    pat = []
    if by or forced:
        parts = ["%s %d for %d" % (n, a, b) for n, (a, b) in sorted(by.items(), key=lambda kv: -kv[1][1])]
        pat.append("This week in T%d: %s%s." % (t, "; ".join(parts), "%s%d forced by a player ruled out (not graded)" % (
            "; " if parts else "", forced) if forced else ""))
    if nk:
        words = {"q-down": "moving a Questionable player down", "q-up": "moving a Questionable player up", "role": "role or minutes calls"}
        pat.append("Of the news judgments, %s." % "; ".join("%s went %d for %d" % (words[k], a, b)
                                                            for k, (a, b) in sorted(nk.items(), key=lambda kv: -kv[1][1])))
        big = [kv for kv in nk.items() if kv[1][1] >= 3]
        k, (a, b) = min(big, key=lambda kv: (kv[1][0] / kv[1][1], -kv[1][1])) if big else (None, (0, 0))
        if b >= 3 and a / b < 0.4:
            pat.append("Takeaway: %s is what lost (%d for %d this week); leave those to the button." % (words[k], a, b))
        elif sum(x[1] for x in nk.values()) >= 3 and sum(x[0] for x in nk.values()) / sum(x[1] for x in nk.values()) >= 0.6:
            pat.append("Takeaway: your news judgments are working; keep making them.")
        else:
            pat.append("Takeaway: no news pattern is clear yet this week.")
    head = ["No moves off the button here last night."] if not md else []
    return head + md + ([""] if md else []) + ([" ".join(pat)] if pat else []) + ([hand_moves] if hand_moves else []) + [""]


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


def contest_view(t, mt, reg):
    """Who paid in this tier, what the top-10% teams held that you were light on (and the reverse), and the kind of pick
    that has paid on the season against your share of it last night, ending in a lean."""
    blk = ((mt or {}).get("tiers") or {}).get(str(t)) or {}
    ex = [(w, e) for w, e in (blk.get("exposure") or {}).items() if e and e.get("my_teams")]
    if not ex:
        return ["No contest data for this tier last night.", ""]
    w, e = max(ex, key=lambda x: x[1]["my_teams"])
    label = {"am": "morning", "pm": "afternoon"}[w]
    ps = [x for x in e.get("players", []) if x.get("mine") is not None]
    s = []
    paid = sorted([x for x in ps if (x.get("lift10") or 0) >= 1.3], key=lambda x: -x["lift10"])[:2]
    if paid:
        s.append("Holders of %s made the top 10%% at %s the field's rate." % (
            " and ".join(x["name"] for x in paid), " and ".join("%.1f times" % x["lift10"] for x in paid)))
    gap = [dict(x, top=x["field"] * x["lift10"]) for x in ps if x.get("lift10") is not None]
    light = max(gap, key=lambda x: x["top"] - x["mine"], default=None)
    heavy = max(gap, key=lambda x: x["mine"] - x["top"], default=None)
    bits = []
    if light and light["top"] - light["mine"] >= 0.05:
        bits.append("the top-10%% teams held %s on %s against your %s" % (light["name"], pct(light["top"]), pct(light["mine"])))
    if heavy and heavy["mine"] - heavy["top"] >= 0.05:
        bits.append("you held %s on %s against %s of the top-10%% teams" % (heavy["name"], pct(heavy["mine"]), pct(heavy["top"])))
    if bits:
        s.append("In your %s window, %s." % (label, "; ".join(bits)))
    best = None
    for kind, rid, mark, words in KINDS[t]:
        m = (reg.get(rid) or {}).get("money_verdict")
        rank = {"proven so far": 2, "an early sign": 1}.get(lab_words(m), 0)
        if rank and (best is None or rank > best[0]):
            best = (rank, kind, rid, mark, words, m)
    if best:
        _, kind, rid, mark, words, m = best
        line = "On the season, %s: contest results, %s" % (words, said(m))
        kd = (e.get("kinds") or {}).get(mark) if mark else None
        if kd and kd.get("mine") is not None:
            mine, field = kd["mine"], kd["field"]
            more = mine > field + 0.05
            level = abs(mine - field) <= 0.05
            good = lab_side(m) > 0 if mark != "PRICEY" else lab_side(m) < 0      # holding PRICEY players is the opposite of putting them last
            line += "; last night you had a %s player on %s of your %s teams, the field on %s%s" % (
                kind, pct(mine), label, pct(field), ", about level with the field" if level else ": lean more toward them" if good and not more else
                ": lean away from them" if not good and more else ", already on the right side")
        s.append(line + ".")
    return [" ".join(s) if s else "Nothing stood out in this tier's contest results last night.", ""]


def leaning(t, shadow, hyp, reg, shown):
    """Each switch on trial and idea being tested here: what it is, where it stands in words, what it means for you today."""
    s = []
    for c in shadow:
        if not (c["kind"] == "candidate" or (c["kind"] == "switch" and c.get("drop_if"))) or t not in c["tiers"] or c["id"] in shown:
            continue
        base = c["id"].split(":")[0]
        h = hyp.get(base) or {}
        what = SHADOW_WORDS.get(c["id"]) or h.get("plain") or c["name"]
        rid = h.get("register") or SHADOW_REG.get(c["id"], c["id"])
        rows = [x for x in shadow if x["id"].split(":")[0] == base] if ":" in c["id"] else [c]
        shown.update(x["id"] for x in rows)
        night = min(c["forward_nights"], FORWARD_NIGHTS)
        reads = []
        for x in rows:
            fwd = x["forward"].get("n", 0) >= 40 and x["forward_nights"] >= 5     # one big night is not a forward read
            v = x["forward"] if fwd else x["season"]
            wd = said(v["label"], v["mean"]) if v.get("n", 0) >= 40 else "too early to say"
            reads.append(("%s%s" % ("in the morning " if x["id"].endswith(":am") else "in the afternoon " if x["id"].endswith(":pm") else "",
                                    ("too early to say" if wd == "too early to say" else
                                     ("its forward nights show " if fwd else "the backtest shows ") + wd)), wd))
        m = (reg.get(rid) or {}).get("money_verdict")
        helps = any(wd.endswith("helps") or "help" in wd for _, wd in reads)
        hurts = any("hurt" in wd for _, wd in reads)
        if c["kind"] == "switch":
            where = "In use, on trial (night %d of %d); on points, %s" % (night, FORWARD_NIGHTS, ", ".join(r for r, _ in reads))
            today = "keep doing it while the check runs"
        else:
            where = "Being tested (night %d of %d); on points, %s" % (night, FORWARD_NIGHTS, ", ".join(r for r, _ in reads))
            today = ("nothing changes; not worth doing by hand" if hurts or lab_side(m) < 0 else
                     "worth trying by hand on close calls" if helps and lab_side(m) > 0 else "nothing changes yet")
        s.append("- %s. %s; contest results: %s. For today: %s." % (what, where, said(m), today))
    return (s or ["Nothing being tested here."]) + [""]


def today_tier(t, pool, ben, pod):
    if pool is None:
        return ["Today's slate isn't on the mirror yet.", ""]
    rs = [r for r in pool if r["c"] == t and r["drafted"]]
    s = []
    for r in rs:
        if QT.match(r["tag"]):
            q = r["tag"].lower().startswith("q")
            s.append("%s is %s (%s to play): %s." % (
                r["name"], r["tag"], pct(r["play"]),
                "T%d in the morning, T%d in the afternoon" % (t, min(5, t + 2)) if q and t < 5 else "stays in T%d" % t))
    for f in ("VALUE", "PRICEY"):
        xs = [r for r in rs if r["flag"] == f]
        if xs:
            s.append("%s: %s." % (f, names([r["name"] for r in xs])))
    bs = [(r, tg) for r, tg in ben if (r["c"] if r.get("drafted") else 5) == t]
    if bs:
        by = collections.OrderedDict()
        for r, tg in bs:
            by.setdefault(tg["name"], []).append(r["name"])
        s.append("Beneficiaries to watch: %s." % "; ".join("if %s sits, %s" % (k, names(v)) for k, v in by.items()))
    return [" ".join(s).replace("..", ".") if s else "Nothing flagged or tagged in this tier today.", ""]


# ---------------------------------------------------------------- draft card and back page
def draft_card(mt, reg, night, hand_card):
    """Each card decision from the contest side's card_decisions block in money_tiers.json: your share last night against
    your season average, and the top-1% and top-10% rate of the field's teams doing it as a multiple of the whole field's
    rate (vs_field_top1 / vs_field_top10), last night and on the season; at a turn, the turn's teams as a group beside it
    (the team-weighted average of the turn's options, which cover every team at that turn). Then one takeaway: the best
    and worst option at each turn on the season's top-1% multiple, and whether you're over or under the field on it."""
    md = ["## The draft card", ""]
    cds = (mt or {}).get("card_decisions") if (mt or {}).get("night") == night else None
    if not cds:
        return md + ["The contest side's per-decision numbers for last night aren't in money_tiers.json yet.", ""]
    verb = {"1/2 turn: faller": "took a faller at the 1/2 turn", "1/2 turn: reach": "reached at the 1/2 turn",
            "1/2 turn: trust ADP": "trusted ADP at the 1/2 turn", "2/3 turn: faller": "took a faller at the 2/3 turn",
            "2/3 turn: reach toward projection": "reached toward the higher projection at the 2/3 turn",
            "2/3 turn: reach, not toward projection": "reached at the 2/3 turn, not toward the higher projection",
            "2/3 turn: trust ADP": "trusted ADP at the 2/3 turn",
            "Early pick + late same-position teammate": "paired an early pick with a late same-position teammate",
            "Opposing stars": "paired stars from opposite sides of one game"}
    short_name = {"faller": "taking a faller", "reach": "reaching", "trust ADP": "trusting ADP",
                  "reach toward projection": "reaching toward the higher projection",
                  "reach, not toward projection": "reaching anywhere else"}
    x_ = lambda v: "%.2fx" % v if v is not None else "n/a"
    turn_of = lambda c: c["decision"].split(":")[0] if c["decision"].endswith(tuple(short_name)) and "turn" in c["decision"] else None
    def group(turn, when):
        """The turn's teams as a group: the options' multiples weighted by the field's teams doing each."""
        rs = [(c.get(when) or {}) for c in cds if turn_of(c) == turn]
        out = []
        for k in ("vs_field_top1", "vs_field_top10"):
            w = [(r[k], (r.get("field") or {}).get("teams") or 0) for r in rs if r.get(k) is not None]
            tot = sum(n for _, n in w)
            out.append(sum(v * n for v, n in w) / tot if tot else None)
        return out
    for c in cds:
        ln, se = c.get("last_night") or {}, c.get("season") or {}
        mine_n, mine_s = (ln.get("mine") or {}).get("share"), (se.get("mine") or {}).get("share")
        turn = turn_of(c)
        line = "- Last night you %s on %s of %s vs your season average of %s." % (
            verb.get(c["decision"], c["decision"]), pct(mine_n) if mine_n is not None else "n/a",
            "your teams at that turn" if turn else "teams", pct(mine_s) if mine_s is not None else "n/a")
        if ln.get("vs_field_top1") is not None or se.get("vs_field_top1") is not None:
            g = group(turn, "season") if turn else None
            line += (" Last night, teams across the field that did this finished top 1%% at %s and top 10%% at %s the field's rate, "
                     "against %s and %s on the season%s." % (
                         x_(ln.get("vs_field_top1")), x_(ln.get("vs_field_top10")), x_(se.get("vs_field_top1")), x_(se.get("vs_field_top10")),
                         " (teams at the %s turn as a group: %s and %s)" % (turn.split()[0], x_(g[0]), x_(g[1])) if g else ""))
        md.append(line)
    take = []
    for turn in ("1/2 turn", "2/3 turn"):
        opts = [c for c in cds if turn_of(c) == turn and (c.get("season") or {}).get("vs_field_top1") is not None]
        if len(opts) < 2:
            continue
        key = lambda c: ((c["season"]["vs_field_top1"]), c["season"].get("vs_field_top10") or 0)
        best, worst = max(opts, key=key), min(opts, key=key)
        def side(c):
            m, f = (c["season"].get("mine") or {}).get("share"), (c["season"].get("field") or {}).get("share")
            if m is None or f is None:
                return "your share isn't read"
            return "you're about level with the field on it" if abs(m - f) < 0.03 else \
                "you're %s the field on it (%s against %s)" % ("over" if m > f else "under", pct(m), pct(f))
        nm = lambda c: short_name[c["decision"].split(": ", 1)[1]]
        take.append("at the %s, %s has done best (%s the field's top-1%% rate on the season) and %s; %s has done worst (%s) and %s" % (
            turn, nm(best), x_(best["season"]["vs_field_top1"]), side(best), nm(worst), x_(worst["season"]["vs_field_top1"]), side(worst)))
    if take:
        md += ["", "Takeaway: " + "; ".join(take) + "."]
    if hand_card:
        md += ["", hand_card]
    return md + [""]


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
            if h.get("target") in ("etr_first", "etr_last"):
                closer += " to ETR's %s upload" % ("first" if h["target"] == "etr_first" else "final")
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
    md += [" ".join(s), ""] + ([tracker[0], ""] if tracker else []) + (["**Projection hypotheses.**", ""] + hyp_lines + [""] if hyp_lines else []) + [s2, "", "Season tables are below; every player's night is in the ledger (analysis/nba/ledger.csv), "
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
    md += [hw["front"], ""] if hw.get("front") else front_page(last, H, mt, hl, (slate, lock, pod) if slate else None)
    md += biggest_bets(last, mt)
    if dt.date.fromisoformat(today).weekday() == 0:
        md += monday(shadow, hyp, reg, leans, mt, hw.get("proposals") or {})
    shown = set()
    md += status_key() + everywhere(reg, by_reg, shadow)
    for t in range(1, 6):
        rc, _ = recap(H, last, t)
        md += ["## T%d" % t, "", "**The rules we played.** " + rules_played(t, reg, by_reg, shadow, leans)[0], ""]
        hand_moves = (hw.get("moves") or {}).get(str(t))
        if t < 5:
            md += ["**Who to trust in this tier.** " + who_to_trust(H, last, t)[0], "", "**Your moves.**", ""] + your_moves(H, last, t, hand_moves)
        else:
            md += ["**Your T5 menu.**", ""] + t5_menu(H, last, mt) + ([hand_moves, ""] if hand_moves else [])
        md += ["**Player recap.**", ""] + rc
        md += ["**Contest view.** " + contest_view(t, mt, reg)[0], "", "**What we're leaning toward.**", ""] + leaning(t, shadow, hyp, reg, shown)
        md += ["**Today in T%d.** " % t + today_tier(t, pool, ben, pod)[0], ""]
    md += draft_card(mt, reg, last, hw.get("card"))
    md += back_page(H, last, hl, today, hw.get("back"))
    md += ["## Season", "", "*Reference tables; points per pair as above. Labels here are the grading's own (RULE: proven so far, + helps and - hurts; "
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
