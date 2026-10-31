"""NBA player ledger: a line on every rotation player's night, kept night after night.

Context only: nothing here feeds Proj, the ranks or the morning report's grading.

  draft    for a night on file (default the newest, or --date): every rotation player in every
           game (the nightly <date>_box.csv), how far he landed from ETR (from our usual, on ETR's
           scale, when ETR didn't project him) and why, split into what moved, with tags and a
           draft note. Writes analysis/nba/ledger.csv (a night's rows replace that night's,
           keeping any note already edited) and prints the newspaper: the players the morning
           report grades, in ADP order.
  print    the newspaper from the ledger, as edited.
  form     the facts behind each Recent note due one written by hand: every player on the day's
           slates (--slates, the mirror's nba_latest.json; main and late) with 3+ graded games whose
           note is an auto note or older than his last game.
  write    saves notes written by hand from a JSON file {key: note} (2-3 sentences on his recent
           form against his projections; keys as form prints them) into analysis/nba/form.csv, then
           recent. The 2am scheduled task writes them after the job's auto notes go in.
  recent   for today (or --date): each player's note, tagged with his last-5 tally (and his average
           gap to ETR over them, for the board's form arrow), to
           analysis/nba/takes/<date>_recent.csv, which the board shows in its row dropdown
           (run scripts/build_takes.py after).
  auto     what the 2am job (nba_daily.yml) runs after the nightly record: drafts every night on file
           that the ledger lacks, writes an auto note (auto_note() below) for each player due one so
           the board always has something, then recent. A current written note is never replaced.

  python3 scripts/nba_ledger.py draft|print|form|write|recent|auto [file] [--date YYYY-MM-DD] [--slates nba_latest.json]

The split: his usual is his usual minutes times his usual per-minute line (the morning file on
file that day). Actual minus usual is exactly the minutes part (minutes over or under his usual,
at his usual rate) plus each stat's part (what he did in the minutes he played against his usual
rate for them), in Underdog points. ETR's projection against his usual is the remaining part.
"""
import argparse, csv, datetime as dt, glob, json, os, sys
from collections import defaultdict
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import nba_daily as daily   # noqa: E402  names, as the nightly record writes them
import nba_report as rep   # noqa: E402  the graded pool: the newspaper covers the same players

HERE = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba")
LEDGER = os.path.join(HERE, "ledger.csv")
FORM = os.path.join(HERE, "form.csv")       # key,name,team,through,by,blurb: the Recent note per player
FORM_COLS = ["key", "name", "team", "through", "by", "blurb"]   # by: "auto" (auto_note) or "written" (by hand)
WINDOW, SHOW_AT = 5, 3          # the Recent note: last 5 graded games, once there are 3
NEAR = 6                        # within this many points of ETR is "in line"
BIG = 4                         # a part this size (points) is worth naming
MIN_OFF = 4                     # and minutes only when he played this many more or fewer than usual
BOX_TO_ETR = [1.103, -6.91]     # a box-score average on ETR's median scale: the board's NBA_BOX_TO_ETR, refit by fit_scale()
COLS = ["date", "slate", "key", "player_id", "name", "team", "opp", "pos", "adp_close", "in_report", "etr", "etr_from",
        "actual", "gap", "result",
        "min", "usual_min", "pf", "fg", "fg3", "ft", "pts", "reb", "ast", "stk", "tov",
        "c_proj", "c_min", "c_pts", "c_reb", "c_ast", "c_stk", "c_tov", "mtch_label", "mtch_cats",
        "tags", "graded", "draft", "note"]
STICKY = {"minutes up", "minutes down"}          # role: tends to carry to the next game
NOISE = {"hot shooting", "cold shooting", "stocks up", "stocks down"}   # mostly variance


def made(s):
    try:
        m, a = str(s).split("-")
        return int(m), int(a)
    except ValueError:
        return None, None


def usual_rate(r):
    """His usual points a minute, built from his per-stat rates (turnovers being what the total leaves),
    so the parts add up exactly; the file's total can run a little off their sum."""
    tov_pm = max(0.0, r["pts_pm"] + 1.2 * r["reb_pm"] + 1.5 * r["ast_pm"] + r["stk_pm"] - r["fp_pm"])
    return r["pts_pm"] + 1.2 * r["reb_pm"] + 1.5 * r["ast_pm"] + r["stk_pm"] - tov_pm


def parts(r):
    """{part: points} for one player's night, or {} without his usual per-minute line."""
    u, m = r["usual_min"], r["min"]
    if not r["fp_pm"] or u is None or m is None:
        return {}
    tov_pm = max(0.0, r["pts_pm"] + 1.2 * r["reb_pm"] + 1.5 * r["ast_pm"] + r["stk_pm"] - r["fp_pm"])
    fp_pm = usual_rate(r)
    out = {"min": (m - u) * fp_pm, "pts": r["pts"] - r["pts_pm"] * m, "reb": 1.2 * (r["reb"] - r["reb_pm"] * m),
           "ast": 1.5 * (r["ast"] - r["ast_pm"] * m), "stk": 3 * (r["stl"] + r["blk"]) - r["stk_pm"] * m,
           "tov": -(r["tov"] - tov_pm * m)}
    etr = r["etr_median"] if r["etr_median"] is not None else r["etr_last"]
    # ETR's number against his usual, both on ETR's (median) scale, so a median running below an
    # average isn't read as ETR expecting less of him
    out["proj"] = max(0.0, BOX_TO_ETR[0] * u * fp_pm + BOX_TO_ETR[1]) - etr if etr is not None else 0.0
    return out


def fit_scale(slates):
    """Refit the line on every 15+ minute player with both numbers on file, as the board does once it can."""
    xs, ys = [], []
    for x in slates:
        for r in x["rows"]:
            if r.get("fp_pm") and (r["usual_min"] or 0) >= 15 and r["etr_median"] is not None:
                xs.append(r["usual_min"] * usual_rate(r))
                ys.append(r["etr_median"])
    if len(xs) >= 40:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        BOX_TO_ETR[:] = [a, my - a * mx]


def tag_night(r, c):
    """[(tag, phrase)] for the parts worth naming, biggest first."""
    out = []
    fgm, fga = made(r["fg"])
    for k, v in sorted(c.items(), key=lambda x: -abs(x[1])):
        if abs(v) < BIG or (k == "min" and abs(r["min"] - r["usual_min"]) < MIN_OFF):
            continue
        m = r["min"]
        if k == "proj":
            usual = max(0.0, BOX_TO_ETR[0] * r["usual_min"] * usual_rate(r) + BOX_TO_ETR[1])
            out.append(("ETR above his usual" if v < 0 else "ETR below his usual",
                        "ETR had him %s his usual (%.0f vs %.0f)" % ("above" if v < 0 else "below", usual - v, usual)))
        elif k == "min":
            why = (" with %d fouls" % r["pf"] if v < 0 and (r["pf"] or 0) >= 5 else
                   " in a %d-point blowout" % abs(r["margin"]) if v < 0 and r["margin"] is not None and abs(r["margin"]) >= 15 else "")
            t = "foul trouble" if "fouls" in why else "blowout" if "blowout" in why else "minutes up" if v > 0 else "minutes down"
            out.append((t, "%d min (usual %d)%s" % (m, r["usual_min"], why)))
        elif k == "pts":
            hot = fga and fga >= 8 and fgm / fga >= 0.55
            cold = fga and fga >= 8 and fgm / fga <= 0.40
            t = ("hot shooting" if hot else "scoring up") if v > 0 else ("cold shooting" if cold else "scoring down")
            out.append((t, "%d pts on %s FG%s" % (r["pts"], r["fg"] or "?", ", %s 3s" % r["fg3"] if r["fg3"] else "")))
        elif k in ("reb", "ast"):
            name = {"reb": "rebounds", "ast": "assists"}[k]
            exp = r[k + "_pm"] * m
            out.append(("%s %s" % (name, "up" if v > 0 else "down"), "%d %s (about %.0f usual for his minutes)" % (r[k], k, exp)))
        elif k == "stk":
            out.append(("stocks up" if v > 0 else "stocks down",
                        "%d stl + %d blk" % (r["stl"], r["blk"]) if r["stl"] + r["blk"] else "no steals or blocks"))
        elif k == "tov" and v < 0:
            out.append(("turnovers", "%d turnovers" % r["tov"]))
    return out[:3]


def key_of(name):
    """The board's name key (Underdog's spelling), whichever source the name came from."""
    k = daily.norm_name(name)
    return daily.ESPN_ALIASES.get(k, k)


def night(r):
    """One ledger row for a player's night."""
    graded = rep.graded(r)
    etr = r["etr_median"] if r["etr_median"] is not None else r["etr_last"]
    row = {k: r.get(k, "") for k in ("date", "slate", "player_id", "name", "team", "opp", "pos", "adp_close", "min", "usual_min",
                                     "pf", "fg", "fg3", "ft", "pts", "reb", "ast", "tov", "mtch_label", "mtch_cats")}
    row.update(key=key_of(r["name"]), etr=etr if etr is not None else "", actual=r["actual"],
               stk=(r["stl"] or 0) + (r["blk"] or 0), graded=int(graded))
    if not (r["min"] or 0) > 0:
        row.update(result="sat", tags="", draft="Didn't play.")
        return row
    if not graded:
        row.update(result="left early", tags="", draft="Left early: %d min of his usual %d." % (r["min"], r["usual_min"]))
        return row
    c = parts(r)
    if etr is None and c:      # no ETR number for him that night: against our usual, on ETR's scale
        etr = round(max(0.0, BOX_TO_ETR[0] * r["usual_min"] * usual_rate(r) + BOX_TO_ETR[1]), 1)
        row.update(etr=etr, etr_from="usual")
        c["proj"] = 0.0
    gap = r["actual"] - etr if etr is not None else None
    result = "in line" if gap is None or abs(gap) < NEAR else "over" if gap > 0 else "under"
    tags = tag_night(r, c)
    vs = "our usual" if row.get("etr_from") == "usual" else "ETR"
    head = ("In line (%.1f vs %s %.1f)" % (r["actual"], vs, etr) if result == "in line" and etr is not None else
            "%s by %.0f (%.1f vs %s %.1f)" % (result.capitalize(), abs(gap), r["actual"], vs, etr) if etr is not None else "%.1f" % r["actual"])
    row.update(gap=round(gap, 1) if gap is not None else "", result=result, tags="; ".join(t for t, _ in tags),
               draft=head + (": " + ", ".join(p for _, p in (tags[:1] if result == "in line" else tags)) if tags else "") + ".",
               **{"c_" + k: round(v, 1) for k, v in c.items()})
    return row


def load_ledger():
    return list(csv.DictReader(open(LEDGER))) if os.path.exists(LEDGER) else []


def save_ledger(rows):
    rows.sort(key=lambda r: (r["date"], float(r["adp_close"] or 99), r["team"], r["name"]))
    with open(LEDGER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_box(date):
    paths = glob.glob(os.path.join(rep.DAILY, "%s_*_box.csv" % date))
    if not paths:
        sys.exit("No box file for %s: the nightly job writes one beside each slate (rebuild the night if it predates it)." % date)
    rows = list(csv.DictReader(open(paths[0])))
    for r in rows:
        for k in r:
            if k not in rep.TEXT:
                r[k] = rep.num(r[k])
        r["adp_am"] = None
    return rows


def report_keys(rows):
    """The players the morning report covers: its graded pool, and the top players who sat or left early."""
    graded = {key_of(r["name"]) for r in rep.pool(rows, rep.PM)}
    rest = {key_of(r["name"]) for r in rows if (r["adp_close"] or r["adp_am"] or 99) <= rep.DEPTH and r["actual"] is not None
            and not rep.graded(r)}
    return graded | rest


def newspaper(rows, date):
    rows = [r for r in rows if r["in_report"] in (1, "1")]
    out = ["# Last night, player by player: %s" % date, ""]
    for r in sorted((r for r in rows if r["graded"] in (1, "1")), key=lambda r: float(r["adp_close"] or 99)):
        out.append("- **%s** %s vs %s · ADP %s · %s — %s" % (r["name"], r["team"], r["opp"] or "?", r["adp_close"] or "-",
                                                         r["result"], r["note"] or r["draft"]))
    rest = [r for r in rows if r["graded"] not in (1, "1")]
    if rest:
        out += ["", "Not graded: " + "; ".join("%s (%s)" % (r["name"], r["note"] or r["draft"]) for r in rest)]
    return out


def opponent_lines(ledger, upto):
    """Position groups and categories where players kept beating or missing their usual against one team."""
    since = (dt.date.fromisoformat(upto) - dt.timedelta(days=21)).isoformat()
    group = lambda pos: "guards" if pos in ("PG", "SG", "G") else "bigs" if pos in ("PF", "C") else "wings"
    acc = defaultdict(list)
    for r in ledger:
        if r["graded"] != "1" or not (since <= r["date"] <= upto) or not r["opp"]:
            continue
        for k, name in (("c_reb", "rebounds"), ("c_ast", "assists"), ("c_pts", "scoring"), ("c_stk", "stocks")):
            if r.get(k):
                acc[(r["opp"], group(r["pos"]), name)].append((r["date"], float(r[k])))
    out = []
    for (opp, g, name), xs in sorted(acc.items()):
        avg = sum(v for _, v in xs) / len(xs)
        if len(xs) >= 4 and len({d for d, _ in xs}) >= 2 and abs(avg) >= 2:
            out.append("- %s against %s: %s %+.1f points a player over their usual (%d players, %d games)" % (
                g.capitalize(), opp, name, avg, len(xs), len({d for d, _ in xs})))
    return out


def windows(ledger, date):
    """{key: his last WINDOW graded games before `date`}, for players with SHOW_AT or more."""
    by = defaultdict(list)
    for r in ledger:
        if r["graded"] == "1" and r["date"] < date:
            by[r["key"]].append(r)
    return {k: sorted(rs, key=lambda r: r["date"])[-WINDOW:] for k, rs in by.items() if len(rs) >= SHOW_AT}


def tally(rs):
    count = lambda res: sum(1 for r in rs if r["result"] == res)
    return " · ".join("%d %s" % (count(x), x) for x in ("over", "in line", "under") if count(x))


def load_form():
    return {r["key"]: r for r in csv.DictReader(open(FORM))} if os.path.exists(FORM) else {}


def todays_keys(slates_file, date):
    """Every player Underdog lists on the day's slates (main and late), by name key."""
    doc = json.load(open(slates_file))
    out = set()
    for s in doc.get("slates", []):
        if s.get("sport", "nba") == "nba" and daily.pacific_day(daily.iso(s["cutoff"])) == date:
            out.update(key_of(p["first_name"] + " " + p["last_name"]) for p in s.get("players") or [])
    return out


def save_form(form):
    with open(FORM, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FORM_COLS)
        w.writeheader()
        w.writerows(sorted(({c: r.get(c, "") for c in FORM_COLS} for r in form.values()), key=lambda r: (r["team"], r["key"])))


def due_notes(ledger, date, slates_file, written=False):
    """{key: his window} for each Recent note due a rewrite: players on the day's slates (or, without
    the slates, everyone who played last night) with 3+ graded games and a game since their note.
    written: due a note written by hand, so an auto note covering his latest game is due too."""
    form, wins = load_form(), windows(ledger, date)
    if slates_file:
        today = todays_keys(slates_file, date)
        due = {k: rs for k, rs in wins.items() if k in today}
    else:
        newest = max(r["date"] for r in ledger if r["date"] < date)
        due = {k: rs for k, rs in wins.items() if rs[-1]["date"] == newest}
    current = lambda k, rs: k in form and form[k]["through"] >= rs[-1]["date"] and (not written or form[k].get("by") == "written")
    return {k: rs for k, rs in due.items() if not current(k, rs)}


def form_sheet(ledger, date, slates_file):
    """The facts behind each Recent note due a note written by hand (due_notes)."""
    form, out = load_form(), []
    due = due_notes(ledger, date, slates_file, written=True)
    out.append("%d notes due, %d teams" % (len(due), len({rs[-1]["team"] for rs in due.values()})))
    out.append("")
    for k, rs in sorted(due.items(), key=lambda x: (x[1][-1]["team"], -float(x[1][-1]["usual_min"] or 0))):
        mins = sum(float(r["min"]) for r in rs) / len(rs)
        out += ["### %s %s [key: %s] · last %d: %s · %.0f min a game (usual %.0f)" % (
            rs[-1]["name"], rs[-1]["team"], k, len(rs), tally(rs), mins, float(rs[-1]["usual_min"] or 0))]
        for r in rs:
            out.append("- %s vs %s: %s %s (%.1f vs %s %s), %s min; %s. %s" % (
                r["date"][5:], r["opp"], r["result"], "%+.0f" % float(r["gap"]) if r["gap"] else "", float(r["actual"]),
                "our usual" if r.get("etr_from") == "usual" else "ETR", r["etr"] or "-", r["min"], r["tags"] or "no part 4+",
                r["note"] or r["draft"]))
        if k in form:
            out.append("- %s before (through %s): %s" % ("auto note" if form[k].get("by") != "written" else "written",
                                                      form[k]["through"], form[k]["blurb"]))
        out.append("")
    return out


def _join(xs):
    xs = [str(x) for x in xs]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


# A part that keeps showing up in his window, as a sentence: (tag, {k: count, n: games, fg: shooting lines}).
RECUR = {
    "hot shooting": "Efficient shooting drove the good nights ({fg})",
    "cold shooting": "Cold shooting drove the bad nights ({fg})",
    "scoring up": "Scoring above his usual rate in {k} of {n}",
    "scoring down": "Scoring below his usual rate in {k} of {n}",
    "assists up": "Assists above his rate in {k} of {n}",
    "assists down": "Assists below his rate in {k} of {n}",
    "rebounds up": "Rebounding above his rate in {k} of {n}",
    "rebounds down": "Rebounding below his rate in {k} of {n}",
    "stocks up": "Steals and blocks have run hot ({k} of {n})",
    "stocks down": "Steals and blocks have dried up ({k} of {n})",
    "turnovers": "Turnovers have cost him in {k} of {n}",
    "ETR above his usual": "ETR has had him above his usual, so it's already pricing a bigger role",
    "ETR below his usual": "ETR has had him below his usual",
}


def auto_note(rs):
    """2-3 sentences on his recent form against his projections, from his window's ledger rows: how
    he's done against ETR, what his minutes say, and what keeps moving his number."""
    n, res = len(rs), [r["result"] for r in rs]
    gaps = [float(r["gap"] or 0) for r in rs]
    ov, inl, un = res.count("over"), res.count("in line"), res.count("under")
    off = lambda xs: _join(["%.0f" % abs(g) for g in xs])
    if ov == n:
        s1 = "Over ETR in all %d, by %s." % (n, off(gaps))
    elif un == n:
        s1 = "Under ETR in all %d, by %s." % (n, off(gaps))
    elif inl == n:
        s1 = "In line with ETR all %d games, never more than %.0f off." % (n, max(abs(g) for g in gaps))
    elif un == 0:
        s1 = "Never under: %d over and %d in line." % (ov, inl)
    elif ov == 0:
        s1 = "Never over: %d under and %d in line." % (un, inl)
    elif un == 1 and ov >= n - 1:
        s1 = "Mostly over: %d of %d, one under." % (ov, n)
    elif ov == 1 and un >= n - 1:
        s1 = "Mostly under: %d of %d, one over." % (un, n)
    else:
        s1 = "Mixed: " + _join(["%d %s" % (c, w) for c, w in ((ov, "over"), (inl, "in line"), (un, "under")) if c]) + "."
    if 0 < ov < n and gaps[-1] == max(gaps) and gaps[-1] >= NEAR:
        s1 = s1[:-1] + ", and the latest was his best (+%.0f)." % gaps[-1]
    elif 0 < un < n and gaps[-1] == min(gaps) and gaps[-1] <= -NEAR:
        s1 = s1[:-1] + ", and the latest was his worst (%.0f)." % gaps[-1]
    mins = [int(round(float(r["min"]))) for r in rs]
    usual = float(rs[-1]["usual_min"] or 0)
    avg = sum(mins) / n
    seq = ", ".join(map(str, mins[:-1])) + ", then " + str(mins[-1])
    why = []                                              # a short night with a reason: a blowout, foul trouble
    for r, m in zip(rs, mins):
        if "blowout" in r["tags"] or "foul trouble" in r["tags"]:
            d = r["draft"]
            i = d.find(" in a ") if "blowout" in r["tags"] else d.find(" with ")
            j = d.find(",", i) if d.find(",", i) > 0 else d.find(".", i + 6)
            why.append("the %d came%s" % (m, d[i:j] if i > 0 else " in a blowout"))
    if avg - usual >= 3:
        s2 = "Minutes went %s against a usual %.0f, so the role is bigger than his average says" % (seq, usual)
    elif usual - avg >= 3:
        s2 = "Minutes went %s, under his usual %.0f" % (seq, usual)
    elif max(mins) - min(mins) >= 10:
        s2 = "Minutes swing (%d-%d) around a usual %.0f" % (min(mins), max(mins), usual)
    elif max(mins) - min(mins) <= 5:
        s2 = "Minutes steady at %s (usual %.0f)" % ("%d" % mins[0] if min(mins) == max(mins) else "%d-%d" % (min(mins), max(mins)), usual)
    else:
        s2 = "Minutes ran %d-%d (usual %.0f)" % (min(mins), max(mins), usual)
    s2 += ("; " + "; ".join(why) + "." if why else ".")
    count = defaultdict(list)
    for r in rs:
        for t in filter(None, (x.strip() for x in r["tags"].split(";"))):
            count[t].append(r)
    recur = sorted(((t, rows) for t, rows in count.items() if t in RECUR and len(rows) >= 2), key=lambda x: -len(x[1]))
    if recur:
        t, rows = recur[0]
        s3 = RECUR[t].format(k=len(rows), n=n, fg=_join([r["fg"] for r in rows if r["fg"]])) + "."
    else:
        last = rs[-1]
        detail = last["draft"].split(": ", 1)[1].rstrip(".") if ": " in last["draft"] else ""
        s3 = ("Last time out against %s: %s." % (last["opp"], detail)) if detail and last["opp"] else ""
    return " ".join(x for x in (s1, s2, s3) if x)


def write_notes(due):
    """Put an auto_note in form.csv for each player due one: a stand-in until a written note replaces it."""
    form = load_form()
    for k, rs in due.items():
        form[k] = {"key": k, "name": rs[-1]["name"], "team": rs[-1]["team"], "through": rs[-1]["date"], "by": "auto",
                   "blurb": auto_note(rs)}
    save_form(form)


def write_written(ledger, date, path):
    """Notes written by hand, from a JSON file {key: blurb} (keys as the form sheet prints them)."""
    notes, wins, form = json.load(open(path)), windows(ledger, date), load_form()
    unknown = [k for k in notes if k not in wins]
    if unknown:
        sys.exit("No 3-game window for: %s" % ", ".join(unknown))
    for k, blurb in notes.items():
        rs = wins[k]
        form[k] = {"key": k, "name": rs[-1]["name"], "team": rs[-1]["team"], "through": rs[-1]["date"], "by": "written",
                   "blurb": blurb.strip()}
    save_form(form)
    print("%d written notes saved" % len(notes))


def avg(xs):
    xs = [float(x) for x in xs if x != ""]
    return round(sum(xs) / len(xs), 1) if xs else ""


def recent(ledger, date):
    """Today's Recent notes: your written read of each player's recent form, tagged with his tally."""
    form, out = load_form(), []
    for k, rs in sorted(windows(ledger, date).items()):
        if k in form and form[k]["blurb"]:
            name = rs[-1]["name"] if daily.norm_name(rs[-1]["name"]) == k else k.title()
            out.append({"source": "Recent", "player": name, "team": rs[-1]["team"], "stance": "",
                        "tags": "Last %d: %s" % (len(rs), tally(rs)), "blurb": form[k]["blurb"],
                        # his average gap to ETR over those games, and ETR's average then: the board's form arrow
                        "form": avg(r["gap"] for r in rs), "form_etr": avg(r["etr"] for r in rs)})
    return out


def draft(s, ledger):
    """The ledger with slate `s`'s night (re)drafted from its box file, and that night's rows."""
    in_report = report_keys(s["rows"])
    kept = {key_of(r["name"]): r["note"] for r in ledger if r["date"] == s["date"] and r["note"]}
    fresh = []
    for b in load_box(s["date"]):
        b["slate"] = s["slate"]
        n = night(b)
        n.update(note=kept.get(n["key"], ""), in_report=int(n["key"] in in_report))
        fresh.append(n)
    return [r for r in ledger if r["date"] != s["date"]] + fresh, fresh


def write_recent(ledger, today):
    notes = recent(ledger, today)
    path = os.path.join(HERE, "takes", "%s_recent.csv" % today)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source", "player", "team", "stance", "tags", "blurb", "form", "form_etr"])
        w.writeheader()
        w.writerows(notes)
    print("%d Recent notes -> %s" % (len(notes), os.path.relpath(path)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["draft", "print", "form", "write", "recent", "auto"])
    ap.add_argument("file", nargs="?", help="write: a JSON file of {key: note}")
    ap.add_argument("--date", help="draft/print: the slate day (default the newest); form/recent: the day it is for (default today, PT)")
    ap.add_argument("--slates", help="form: the mirror's nba_latest.json, so notes are due for everyone on the day's slates")
    a = ap.parse_args()
    ledger = load_ledger()
    today = a.date or dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    if a.cmd == "recent":
        write_recent(ledger, today)
        return
    if a.cmd == "auto":
        slates = rep.load()
        fit_scale(slates)
        newest = max((r["date"] for r in ledger), default="")
        for s in slates:                                  # every night since the ledger's newest, a missed one too
            if newest < s["date"] < today and glob.glob(os.path.join(rep.DAILY, "%s_*_box.csv" % s["date"])):
                ledger, fresh = draft(s, ledger)
                print("drafted %s: %d players" % (s["date"], len(fresh)))
        save_ledger(ledger)
        ledger = load_ledger()
        due = due_notes(ledger, today, a.slates)
        write_notes(due)
        print("%d Recent notes written" % len(due))
        write_recent(ledger, today)
        return
    if a.cmd == "form":
        print("\n".join(form_sheet(ledger, today, a.slates)))
        return
    if a.cmd == "write":
        write_written(ledger, today, a.file)
        write_recent(ledger, today)
        return
    if a.cmd == "print":
        day = a.date or max(r["date"] for r in ledger)
        print("\n".join(newspaper([r for r in ledger if r["date"] == day], day)))
        return
    slates = rep.load()
    fit_scale(slates)
    s = [x for x in slates if x["date"] == (a.date or slates[-1]["date"])]
    if not s:
        sys.exit("No slate on file for %s." % a.date)
    ledger, fresh = draft(s[0], ledger)
    save_ledger(ledger)
    s = s[0]
    opp = opponent_lines(load_ledger(), s["date"])
    print("\n".join(newspaper(fresh, s["date"]) + (["", "## Against the same team, lately", ""] + opp if opp else [])))


if __name__ == "__main__":
    main()
