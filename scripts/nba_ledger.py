"""NBA player ledger: a line on every graded player's night, kept night after night.

Context only: nothing here feeds Proj, the ranks or the morning report's grading.

  draft    for the slate on file (or --date), each player the morning report grades, in ADP
           order: how far he landed from ETR and why, split into what moved (his projection
           against his usual, minutes, scoring, rebounds, assists, stocks, turnovers), with
           tags and a draft note. Writes analysis/nba/ledger.csv (a night's rows replace that
           night's, keeping any note already edited) and prints them.
  print    the night from the ledger, as edited: the newspaper.
  recent   for today's slate (or --date): a Recent note on every player with 3+ graded games in
           his last 5, to analysis/nba/takes/<date>_recent.csv, which the board shows in its
           row dropdown (run scripts/build_takes.py after).

  python3 scripts/nba_ledger.py draft|print|recent [--date YYYY-MM-DD]

The split: his usual is his usual minutes times his usual per-minute line (the morning file on
file that day). Actual minus usual is exactly the minutes part (minutes over or under his usual,
at his usual rate) plus each stat's part (what he did in the minutes he played against his usual
rate for them), in Underdog points. ETR's projection against his usual is the remaining part.
"""
import argparse, csv, datetime as dt, glob, os, sys
from collections import defaultdict
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import nba_report as rep   # noqa: E402  the graded pool, so the ledger covers the same players

HERE = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba")
LEDGER = os.path.join(HERE, "ledger.csv")
WINDOW, SHOW_AT = 5, 3          # the Recent note: last 5 graded games, once there are 3
NEAR = 6                        # within this many points of ETR is "in line"
BIG = 4                         # a part this size (points) is worth naming
COLS = ["date", "slate", "player_id", "name", "team", "opp", "pos", "adp_close", "etr", "actual", "gap", "result",
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


def parts(r):
    """{part: points} for one player's night, or {} without his usual per-minute line."""
    u, m = r["usual_min"], r["min"]
    if not r["fp_pm"] or u is None or m is None:
        return {}
    tov_pm = max(0.0, r["pts_pm"] + 1.2 * r["reb_pm"] + 1.5 * r["ast_pm"] + r["stk_pm"] - r["fp_pm"])
    out = {"min": (m - u) * r["fp_pm"], "pts": r["pts"] - r["pts_pm"] * m, "reb": 1.2 * (r["reb"] - r["reb_pm"] * m),
           "ast": 1.5 * (r["ast"] - r["ast_pm"] * m), "stk": 3 * (r["stl"] + r["blk"]) - r["stk_pm"] * m,
           "tov": -(r["tov"] - tov_pm * m)}
    etr = r["etr_median"] if r["etr_median"] is not None else r["etr_last"]
    out["proj"] = u * r["fp_pm"] - etr if etr is not None else 0.0
    return out


def tag_night(r, c):
    """[(tag, phrase)] for the parts worth naming, biggest first."""
    out = []
    fgm, fga = made(r["fg"])
    for k, v in sorted(c.items(), key=lambda x: -abs(x[1])):
        if abs(v) < BIG:
            continue
        m = r["min"]
        if k == "proj":
            out.append(("ETR above his usual" if v < 0 else "ETR below his usual",
                        "ETR had him %s his usual (%.0f vs %.0f)" % ("above" if v < 0 else "below",
                                                                       r["usual_min"] * r["fp_pm"] - v, r["usual_min"] * r["fp_pm"])))
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
            out.append(("%s %s" % (name, "up" if v > 0 else "down"), "%d %s (about %.0f usual for his minutes)" % (r[k], name[:3], exp)))
        elif k == "stk":
            out.append(("stocks up" if v > 0 else "stocks down", "%d stl + %d blk" % (r["stl"], r["blk"])))
        elif k == "tov" and v < 0:
            out.append(("turnovers", "%d turnovers" % r["tov"]))
    return out[:3]


def night(r):
    """One ledger row for a player's night."""
    graded = rep.graded(r)
    etr = r["etr_median"] if r["etr_median"] is not None else r["etr_last"]
    row = {k: r.get(k, "") for k in ("date", "slate", "player_id", "name", "team", "opp", "pos", "adp_close", "min", "usual_min",
                                     "pf", "fg", "fg3", "ft", "pts", "reb", "ast", "tov", "mtch_label", "mtch_cats")}
    row.update(etr=etr, actual=r["actual"], stk=(r["stl"] or 0) + (r["blk"] or 0), graded=int(graded))
    if not (r["min"] or 0) > 0:
        row.update(result="sat", tags="", draft="Didn't play.")
        return row
    if not graded:
        row.update(result="left early", tags="", draft="Left early: %d min of his usual %d (not graded)." % (r["min"], r["usual_min"]))
        return row
    gap = r["actual"] - etr if etr is not None else None
    result = "in line" if gap is None or abs(gap) < NEAR else "over" if gap > 0 else "under"
    c = parts(r)
    tags = tag_night(r, c)
    head = ("In line (%.1f vs ETR %.1f)" % (r["actual"], etr) if result == "in line" and etr is not None else
            "%s by %.0f (%.1f vs ETR %.1f)" % (result.capitalize(), abs(gap), r["actual"], etr) if etr is not None else "%.1f" % r["actual"])
    row.update(gap=round(gap, 1) if gap is not None else "", result=result, tags="; ".join(t for t, _ in tags),
               draft=head + (": " + ", ".join(p for _, p in tags) if tags else "") + ".",
               **{"c_" + k: round(v, 1) for k, v in c.items()})
    return row


def load_ledger():
    return list(csv.DictReader(open(LEDGER))) if os.path.exists(LEDGER) else []


def save_ledger(rows):
    rows.sort(key=lambda r: (r["date"], float(r["adp_close"] or 99)))
    with open(LEDGER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def slate_rows(date):
    slates = rep.load()
    s = [x for x in slates if x["date"] == (date or slates[-1]["date"])]
    if not s:
        sys.exit("No slate on file for %s." % date)
    rows = s[0]["rows"]
    if "fp_pm" not in rows[0]:
        sys.exit("%s was recorded before the nightly job kept box-score detail; rebuild it first." % s[0]["file"])
    graded = rep.pool(rows, rep.PM)
    top = [r for r in rows if (r["adp_close"] or r["adp_am"] or 99) <= rep.DEPTH and r["actual"] is not None
           and not rep.graded(r)]
    return s[0], graded + top


def newspaper(rows, date):
    out = ["# Last night, player by player: %s" % date, ""]
    for r in sorted((r for r in rows if r["graded"] in (1, "1")), key=lambda r: float(r["adp_close"] or 99)):
        out.append("- **%s** %s vs %s · ADP %s · %s — %s" % (r["name"], r["team"], r["opp"] or "?", r["adp_close"],
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


def recent(ledger, date):
    by = defaultdict(list)
    for r in ledger:
        if r["graded"] == "1" and r["date"] < date:
            by[(r["player_id"], r["name"], r["team"])].append(r)
    out = []
    for (pid, name, team), rs in sorted(by.items(), key=lambda x: x[0][1]):
        rs = sorted(rs, key=lambda r: r["date"])[-WINDOW:]
        if len(rs) < SHOW_AT:
            continue
        n = len(rs)
        count = lambda res: sum(1 for r in rs if r["result"] == res)
        tally = " · ".join("%d %s" % (count(x), x) for x in ("over", "in line", "under") if count(x))
        mins = [float(r["min"]) for r in rs]
        usual = float(rs[-1]["usual_min"] or 0)
        bits = ["Last %d against ETR: %s." % (n, tally),
                "Minutes %.0f a game (usual now %.0f)." % (sum(mins) / n, usual)]
        tags = defaultdict(int)
        for r in rs:
            for t in filter(None, (r["tags"] or "").split("; ")):
                tags[t] += 1
        sticky = [t for t in STICKY if tags[t] >= SHOW_AT]
        if sticky:
            bits.append("Trend: %s in %d of %d." % (" and ".join(sticky), max(tags[t] for t in sticky), n))
        misses = [r for r in rs if r["result"] != "in line"]
        if misses and all(set(filter(None, r["tags"].split("; "))) <= NOISE for r in misses):
            bits.append("The misses were shooting or stocks swings with minutes steady: variance.")
        last = rs[-1]
        bits.append("Last game (%s vs %s): %s" % (last["date"][5:], last["opp"], last["note"] or last["draft"]))
        out.append({"source": "Recent", "player": name, "team": team, "stance": "", "tags": "Last %d: %s" % (n, tally),
                    "blurb": " ".join(bits)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["draft", "print", "recent"])
    ap.add_argument("--date", help="draft/print: the slate day (default the newest); recent: the day it is for (default today, PT)")
    a = ap.parse_args()
    ledger = load_ledger()
    if a.cmd == "recent":
        day = a.date or dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
        notes = recent(ledger, day)
        path = os.path.join(HERE, "takes", "%s_recent.csv" % day)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["source", "player", "team", "stance", "tags", "blurb"])
            w.writeheader()
            w.writerows(notes)
        print("%d Recent notes -> %s" % (len(notes), os.path.relpath(path)))
        return
    if a.cmd == "print":
        day = a.date or max(r["date"] for r in ledger)
        print("\n".join(newspaper([r for r in ledger if r["date"] == day], day)))
        return
    slate, rows = slate_rows(a.date)
    kept = {r["player_id"]: r["note"] for r in ledger if r["date"] == slate["date"] and r["note"]}
    fresh = []
    for r in rows:
        n = night(r)
        n["note"] = kept.get(n["player_id"], "")
        fresh.append(n)
    ledger = [r for r in ledger if r["date"] != slate["date"]] + fresh
    save_ledger(ledger)
    out = newspaper([dict(r, adp_close=r["adp_close"]) for r in fresh], slate["date"])
    opp = opponent_lines(load_ledger(), slate["date"])
    print("\n".join(out + (["", "## Against the same team, lately", ""] + opp if opp else [])))


if __name__ == "__main__":
    main()
