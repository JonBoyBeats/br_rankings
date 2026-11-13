"""The Friday report (first edition 2026-11-20; replaces the Monday proposals): analysis/nba/report/friday.md.

Runs as its own Friday job after the nightly record (.github/workflows/nba_friday.yml), so it never delays the
morning notes. Front page: "What should change this week": nothing, or one line per proposal, then the contest side's
register proposals (money_friday.json "proposals"). Nothing moves without the operator's yes.

A test proposes a change only when it's clear on its main grade (90%+ of night-resamples: points for T1-T4 and the
projections, contest results for T5, Q tags and swaps) and the other grade doesn't disagree; 80-90% shows as
"watching". Every test shows "since the rule went in" (the first night it was live, analysis/nba/report/rule_dates.json;
a rule without a date shows season only) and "season". The contest side supplies the contest-result reads
(analysis/nba/report/money_friday.json, written by its Friday job just before this one); this side assembles the report.

  python3 scripts/nba_friday.py [--mirror ../br-adp-mirror] [--today YYYY-MM-DD]
"""
import argparse, collections, csv, datetime as dt, glob, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_season_tests as TS     # noqa: E402  all pairs by nights, on tier_history.csv
import nba_tier_history as TH          # noqa: E402
import nba_report_sections as RS       # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = os.path.join(HERE, "analysis", "nba", "report")
OUT = os.path.join(REP, "friday.md")
CLEAR, WATCH = 0.90, 0.80
MIN_PAIRS, MIN_NIGHTS = 40, 8             # below this a read shows, but proposes nothing and isn't watched
TWEAK_FROM = dt.date(2026, 11, 27)        # morning-projection tweaks are proposed every other Friday from here
PT = dt.timezone(dt.timedelta(hours=-8))
ALL_NW = dict(TS.NW)


def rule_dates():
    p = os.path.join(REP, "rule_dates.json")
    return {k: v for k, v in json.load(open(p)).items() if not k.startswith("_")} if os.path.exists(p) else {}


def since_of(rd, rid, window=None):
    r = rd.get(rid) or {}
    return (r.get("windows") or {}).get(window) or r.get("since")


def subset(since, window=None):
    """Point the season-test machinery at the night-windows from `since` (all of them when None)."""
    TS.NW = {k: v for k, v in ALL_NW.items() if (since is None or k[0] >= since) and (window is None or k[1] == window)}


def read(s, in_force_is_a=True):
    """(words, share for the alternative) from a summarize() block, A against B."""
    if not s or not s["nights"]:
        return "no disagreeing pairs yet", None
    alt = s["b_share"] if in_force_is_a else s["a_share"]
    wl = (s["won"], s["lost"], s["even"]) if in_force_is_a else (s["lost"], s["won"], s["even"])
    txt = "%d-%d-%d nights, the rule in force ahead in %d%% of resamples, %+.2f points a pair (%d pairs)" % (
        wl + (round(100 * (s["a_share"] if in_force_is_a else s["b_share"])), s["ppp"] if in_force_is_a else -s["ppp"], s["pairs"]))
    if s["pairs"] < MIN_PAIRS or s["nights"] < MIN_NIGHTS:
        return txt + " (too few to propose on)", None
    return txt, alt


PROPOSALS, WATCHING = [], []
MF = {}   # the contest side's money_friday.json, loaded in main


def money(test):
    """Lines for one of the contest side's Friday tests: each group's top-10% multiple of the whole field's rate (80% range,
    teams), season and since its rule went in."""
    t = (MF.get("tests") or {}).get(test)
    if not t:
        return ["- **On contest results** (%s): not in money_friday.json yet." % test]
    if t.get("status"):
        return ["- **%s** (contest results): %s." % (t["label"], t["status"])]
    out = ["- **%s** (contest results, top 10%% against the field's rate):" % t["label"]]
    for g, x in (t.get("groups") or {}).items():
        sd = x.get("since_dates")
        since = "; since %s: %s" % (min(sd.values()), RS.mult(x["since"])) if sd and x.get("since") else ""
        out.append("  - %s: season %s%s" % (g, RS.mult(x["season"]), since))
    return out


def test_line(title, rid, window, fn, in_force_is_a=True, change=None, rd=None):
    """One test: its since-the-rule and season reads; a proposal at 90%+ for the alternative, watching at 80-90%."""
    since = since_of(rd, rid, window) if rid else None
    subset(None, window)
    season, alt_s = read(fn(), in_force_is_a)
    out = "- **%s**: season %s." % (title, season)
    alt = alt_s
    if since:
        subset(since, window)
        txt, alt_n = read(fn(), in_force_is_a)
        out = "- **%s**: since the rule went in (%s) %s; season %s." % (title, since[5:], txt, season)
        alt = alt_n if alt_n is not None else alt_s
    subset(None)
    if alt is not None and change:
        if alt >= CLEAR:
            PROPOSALS.append("%s (%s; contest results: see the contest side's read)" % (change, title))
            out += " **Proposed: %s.**" % change
        elif alt >= WATCH:
            WATCHING.append(title)
            out += " Watching."
    return out


def am_groups_adp(rows, night):
    out = []
    for f in ("VALUE", "", "PRICEY"):
        out += sorted([r for r in rows if r["flag"] == f], key=TS.adp_of)
    return TS.positions(out)


def dropped(night):
    return [r for r in ALL_NW[night] if int(r["a_tier"]) <= 4 and r["flag"] == "PRICEY" and r["tierv"] >= 5 and r["ok"]]


def t5_top3(night):
    t5 = sorted([r for r in ALL_NW[night] if r["tierv"] == 5 and r["builtv"] is not None], key=lambda r: r["builtv"])[:3]
    return [r for r in t5 if r["ok"]]


def elite_right():
    """Do the elites (T1's top by projection, cut at the biggest gap) outscore the rest of T1? Points, by night."""
    by = collections.defaultdict(list)
    for (d, w), rows in ALL_NW.items():
        t1 = sorted([r for r in rows if r["a_tier"] == "1" and r["projv"] is not None], key=lambda r: -r["projv"])
        if len(t1) < 2:
            continue
        n = TH.elites([r["projv"] for r in t1])
        el, rest = [r for r in t1[:n] if r["ok"]], [r for r in t1[n:] if r["ok"]]
        by[(d, w)] += [a["act"] - b["act"] for a in el for b in rest if a["act"] != b["act"]]
    s = TS.summarize(by)
    return "%d-%d-%d nights, elites outscored the rest of T1 in %d%% of resamples, %+.1f points a pair" % (
        s["won"], s["lost"], s["even"], round(100 * s["a_share"]), s["ppp"]) if s["nights"] else "no nights yet"


def t4_lines():
    c = collections.Counter()
    for (d, w), rows in ALL_NW.items():
        pod = rows[0]["podv"]
        va = sorted(TS.adp_of(r) for r in rows)
        la = TH.lines(va, TH.LADDER[pod][:3], TH.MIN_TIER[pod])
        k = TH.t4_line(va, pod, la[2])
        c["at the start of round 6" if k == TH.R6[pod] else "earlier, at a 2-pick gap"] += 1
    return ", ".join("%s on %d" % kv for kv in c.items())


def floor_duds():
    bands = [(0, 16), (16, 20), (20, 24), (24, 99)]
    rows = [r for rs in ALL_NW.values() for r in rs if r["a_tier"] == "5" and r["ok"] and r["projv"] and num(r["proj_min"]) is not None
            and r["adpv"] is not None and r["adpv"] < TS.CAP[r["podv"]]]
    parts = []
    for lo, hi in bands:
        g = [r for r in rows if lo <= num(r["proj_min"]) < hi]
        if g:
            parts.append("%s minutes: %d%% duds (%d)" % ("%d-%d" % (lo, hi) if hi < 99 else "%d+" % lo,
                                                        round(100 * sum(r["act"] < 0.5 * r["projv"] for r in g) / len(g)), len(g)))
    return "; ".join(parts)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def curve_accuracy():
    try:
        import nba_ownership as O
        _, rows = O.backcheck()
        mid = [r for r in rows if 0.3 <= r["act"] < 0.9]
        return "the curve refitted without each night misses by %.1f points of drafted%% in the 30-90%% band (%+.1f), by %.1f overall (%d player-nights)" % (
            O.mae(mid, "cur_l"), O.bias(mid, "cur_l"), O.mae(rows, "cur_l"), len(rows))
    except Exception as e:
        return "not read (%s)" % e


def gallagher():
    rows = [r for r in RS.gallagher_log() if r["counted"] and r["played"] and r["vs_etr"] != ""]
    if not rows:
        return "no arrows published before a lock yet"
    since = [r for r in rows if r["date"] >= "2026-11-13"]
    def line(g):
        return "%d arrows, %+.1f against ETR's final, %d%% under it" % (len(g), sum(r["vs_etr"] for r in g) / len(g),
                                                                      round(100 * sum(r["vs_etr"] < 0 for r in g) / len(g)))
    return ("since the arrow went in (11-13): %s; " % line(since) if since else "") + "season: " + line(rows)


def proj_vs_etr(today):
    import nba_etr_match as EM
    ss = EM.slates(set(), target="etr_last")
    def line(ps, n):
        m = EM.measures(ps)
        return "%.2f points apart on average, correlation %.2f, %d%% 3+ apart (%d slates)" % (
            sum(abs(p["etr"] - p["ours"]) for p in ps) / len(ps), m["corr"], round(100 * m["big"] / m["n"]), n)
    since = [x for x in ss if x[0] >= "2026-11-14"]
    out = ("since the 11-14 tweaks: %s; " % line([p for _, _, ps in since for p in ps], len(since)) if since else "since the 11-14 tweaks: no graded slate yet; ")
    out += "season: " + line([p for _, _, ps in ss for p in ps], len(ss))
    weeks = (today - TWEAK_FROM).days
    if weeks >= 0 and weeks % 14 == 0:
        out += ". **Tweak Friday:** rerun etr_gap_study.md on the slates since the last tweak and bring the moves that close the gap."
    else:
        nxt = TWEAK_FROM + dt.timedelta(days=14 * max(0, math.ceil(weeks / 14))) if weeks > 0 else TWEAK_FROM
        out += ". Next tweak window: %s" % nxt.strftime("%-m/%-d")
    return out


def etr_vs_box():
    res = []
    for p in glob.glob(os.path.join(HERE, "analysis", "nba", "daily", "*_box.csv")):
        for r in csv.DictReader(open(p)):
            e, a = num(r["etr_median"]), num(r["actual"])
            if e is not None and a is not None and (num(r["min"]) or 0) > 0:
                res.append(a - e)
    return "%+.2f on average, off by %.1f a player (%d player-nights); the patterns study is etr_vs_box_study.md" % (
        sum(res) / len(res), sum(abs(x) for x in res) / len(res), len(res)) if res else "no box files"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "br-adp-mirror"))
    ap.add_argument("--today")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else dt.datetime.now(dt.timezone.utc).astimezone(PT).date()
    rd = rule_dates()
    mf = os.path.join(REP, "money_friday.json")
    MF.update(json.load(open(mf)) if os.path.exists(mf) else {})
    H = [r for rs in ALL_NW.values() for r in rs]
    body = []
    body += ["## T1", "",
             test_line("Afternoon: ETR (in force) against ADP", None, "pm", lambda: TS.compare("pm", [1], TS.PROJ, TS.ADP), True, "order afternoon T1 by ADP", rd),
             test_line("Morning: ADP (in force) against our projection", None, "am", lambda: TS.compare("am", [1], TS.ADP, TS.PROJ), True, "order morning T1 by our projection", rd),
             "- **The elite cut**: " + elite_right() + ".", ""]
    body += ["## T2", "",
             test_line("Morning: straight ADP (in force) against our projection", "t2-am-adp", "am", lambda: TS.compare("am", [2], TS.ADP, TS.PROJ), True, "order morning T2 by our projection", rd),
             test_line("Afternoon: the elite break (in force) against straight ADP", "t2-pm-elite-break", "pm", lambda: TS.compare("pm", [2], TS.elite_break, TS.ADP), True, "go back to straight ADP in afternoon T2", rd),
             test_line("Afternoon: the elite break (in force) against straight ETR", "t2-pm-elite-break", "pm", lambda: TS.compare("pm", [2], TS.elite_break, TS.PROJ), True, "order afternoon T2 by ETR straight", rd),
             test_line("Is the re-tuned morning projection ready for the morning elite break? Straight ADP (in force) against the break",
                       "proj-box-3-days", "am", lambda: TS.compare("am", [2], TS.ADP, TS.elite_break), True, "use the elite break in morning T2", rd),
             "", "**Turn lines and roster pairings** (the contest side's card_decisions, season):", ""]
    mt = json.load(open(os.path.join(REP, "money_tiers.json"))) if os.path.exists(os.path.join(REP, "money_tiers.json")) else None
    body += [l for l in RS.turn_lines(mt, (mt or {}).get("night"))]
    for c in (mt or {}).get("card_decisions") or []:
        if "turn" not in c["decision"]:
            s = c["season"]
            body.append("- **%s**: you %s of teams, the field %s; %.2fx the field's top-1%% rate and %.2fx its top-10%% on the season." % (
                c["decision"], RS.pct(s["mine"]["share"]), RS.pct(s["field"]["share"]), s["vs_field_top1"], s["vs_field_top10"]))
    body += money("t2-turns") + money("t2-elite-break")
    body += ["", "## T3 and T4", ""]
    for t in (3, 4):
        body.append(test_line("T%d afternoon: the shared sort (in force) against ADP" % t, "t34-pm-etr-groups", "pm",
                              lambda t=t: TS.compare("pm", [t], TS.shared, TS.ADP), True, "order afternoon T%d by ADP" % t, rd))
        body.append(test_line("T%d morning: by ADP in each group (in force) against the projection in each group" % t, "t34-am-adp-groups", "am",
                              lambda t=t: TS.compare("am", [t], am_groups_adp, TS.shared), True, "order morning T%d by our projection in each group" % t, rd))
    for w in ("am", "pm"):
        # both came from contest results, which stay their main grade (the contest side's read): points show, don't propose
        body.append(test_line("%s: T3 PRICEY ahead of T4 VALUE (in force), on points; the main grade is contest results" % RS.W[w].capitalize(),
                              "t3-pricey-over-t4-value", w, lambda w=w: TS.boundary(w, TS.t4_value, TS.t3_pricey), False, None, rd))
        body.append(test_line("%s: T4 PRICEY right after T5's top 3 (in force) against ahead of them, on points; the main grade is contest results" % RS.W[w].capitalize(),
                              "t4-pricey-to-t5", w, lambda w=w: TS.boundary(w, dropped, t5_top3), False, None, rd))
    body += money("t3t4-boundaries")
    body += ["- **Where the T4/T5 line fell** (night-windows): " + t4_lines() + ".", ""]
    body += ["## T5", "", "**The 60% line**, on contest results:", ""] + RS.t5_contest(H, mt)
    body += ["- **The drafted% curve**: " + curve_accuracy() + ".",
             "- **4-drafter nights**: no line, T5 by projection, until a Friday shows a line that works (the contest side reads a 40% line "
             "in t5-drafted); " + str(sum(1 for k in ALL_NW if ALL_NW[k][0]["podv"] == 4) // 2) + " four-drafter nights on file.",
             "- **The minutes floor against T5 duds** (round-6 ADP players, dud = under half his projection; floor 20): " + floor_duds() + "."]
    body += money("t5-drafted") + money("t5-operator-order") + [""]
    body += ["## Questionable tags", ""]
    try:
        import nba_q_rules_test as Q
        _, R = Q.run()
        for w in ("am", "pm"):
            for alt, words in (("b", "two tiers back"), ("c", "no higher than the top of T4"), ("d", "the bottom of the list")):
                s = R.get((w, "a", alt))
                if s and s["nights"]:
                    body.append("- %s, keeps his tier (in force) against %s: %d-%d-%d nights, ahead in %d%% of resamples, %+.1f points a pair (points; the "
                                "main grade is contest results, the contest side's)." % (RS.W[w].capitalize(), words, s["won"], s["lost"], s["even"],
                                                                                        round(100 * s["a_share"]), s["ppp"]))
    except Exception as e:
        body.append("- The Q rules on points: not read (%s)." % e)
    qcase = collections.Counter()
    for r in H:
        if r["date"] >= "2026-11-13" and (r["tag"] or "")[:1].lower() == "q":
            qcase["T1 to T2" if r["a_tier"] == "1" else "below the cut (ADP fell 6+)" if r["tier"] == "6" and r["a_tier"] != "5" else "kept his tier"] += 1
    body.append("- Since the Q rules went in: %s." % (", ".join("%s %d" % kv for kv in qcase.items()) or "no Questionable players yet"))
    body += money("q-tags")
    try:
        import nba_swap_grade
        body.append("- " + nba_swap_grade.season_line())
    except Exception as e:
        body.append("- Swap button: not graded (%s)." % e)
    body += money("swap-button")
    body += ["", "## Your takes", ""]
    for t in (2, 3, 4):
        body.append("- " + RS.moves(H, "", t)[-2])
    body += ["", "## Morning projection against ETR", "", "- " + proj_vs_etr(today) + ".", "",
             "## ETR against the box score, and Gallagher's arrows", "",
             "- ETR's final against the box score: " + etr_vs_box() + ".",
             "- Gallagher's Bad-matchup arrows (published before your lock): " + gallagher() + ".", ""]
    if today.day <= 7:
        body += ["## Monthly", "", "- First Friday of the month: rerun where winners are made and dud tolerance (the contest side's reads).", ""]
    body += ["## Data", ""]
    try:
        import nba_tier_report as T
        _, _, _, latest = T.today_slate(a.mirror)
        bad = T.problems(T.health(a.mirror, today.isoformat(), latest))
        body.append("- " + ("; ".join(bad) if bad else "Everything came in on time this week."))
    except Exception as e:
        body.append("- Not read (%s)." % e)
    body += ["", "Contest-result reads from the contest side: money_friday.json (%s)." % (
        "generated %s, %d nights" % (MF["generated"], len(MF.get("nights") or [])) if MF else "not on file")]
    md = ["# NBA Friday report, %s" % today.strftime("%A %-m/%-d"), "",
          "*The standing rules: [the rulebook](rulebook.md). Each test reads since its rule went in (rule_dates.json) and on the season.*", "",
          "## What should change this week", ""]
    md += (["- " + p for p in PROPOSALS] if PROPOSALS else ["Nothing."]) + [""]
    if WATCHING:
        md += ["Watching (80-90%): " + "; ".join(WATCHING) + ".", ""]
    mp = (MF.get("proposals") or {}).get("proposals") or []
    md += ["**From the contest side** (register verdicts): " + ("none." if MF else "money_friday.json not on file."), ""] if not mp else \
          ["**From the contest side** (register verdicts):", ""] + ["- %s: %s" % (x["id"], x["reason"]) for x in mp] + [""]
    md += ["Nothing moves without your yes.", ""] + body
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
