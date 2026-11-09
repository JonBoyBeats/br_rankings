"""NBA morning report by tier, built for a phone: today's decisions first, then the shadow scoreboard and last night's
grades by tier, then the season. Writes analysis/nba/report/today.md and prints it.

  Today       today's main slate read at report time: the ladders on ADP now and the morning projection file (the
              board's own Proj isn't on the server, so this is a directional read: press Tiers on the board for the real
              build), each tier's switch for the AM and PM windows with its status (leans.json), today's Q-tagged players
              with their tier move (AM: no push; PM: two tiers back) and our calibrated chance they play, VALUE flags,
              beneficiaries to watch (cheap teammates of a tagged player) and the swap board reminder
  Shadow      each provisional switch against the rule it replaced, and each candidate, forward nights so far (shadow.md)
  Last night  the last slate in tier_history.csv: your board against the window's projection and ADP by tier, the flags,
              your takes, and the scratches with what their swaps scored
  Season      the adopted leans and rules with their evidence, the Q lane, the swaps

  python3 scripts/nba_tier_report.py --mirror ../br-adp-mirror
"""
import argparse, collections, csv, datetime as dt, json, math, os, re, sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_history as T    # noqa: E402
import nba_tier_grade as G      # noqa: E402
import nba_q_lane as Q          # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = G.REP
OUT = os.path.join(REP, "today.md")
PT = ZoneInfo("America/Los_Angeles")
QT = re.compile(r"^(q|d|g)", re.I)
num = G.num
SWITCHES = [   # (tier, AM switch, PM switch, the leans.json ids that give their status)
    (1, "ADP (2: Boom)", "ETR", []),
    (2, "ADP", "ADP (2: ETR)", ["pm-t2-adp-etr-2"]),
    (3, "Proj (3: ADP)", "ETR (ties: ADP, Boom)", []),
    (4, "Proj (3: ADP)", "ADP (2: ETR)", ["pm-t4-adp-etr-2"]),
    (5, "the button's order", "ADP", ["am-t5-button-order", "pm-t5-adp-value-up"]),
]


def norm(s):
    return T.re.sub(r"[^a-z ]", "", (s or "").lower().replace("-", " ").replace(".", "")).strip()


def today_slate(mirror):
    latest = json.load(open(os.path.join(mirror, "nba_latest.json")))
    now = dt.datetime.now(dt.timezone.utc)
    day = now.astimezone(PT).date().isoformat()
    for s in latest.get("slates", []):
        lock = dt.datetime.fromisoformat(s["cutoff"].replace("Z", "+00:00"))
        if s["label"].endswith("_main") and lock.astimezone(PT).date().isoformat() == day and isinstance(s.get("players"), list) and s["players"]:
            return s, lock, day
    return None, None, day


def calibrated_play(H):
    cal = [dict(p=float(r["play"]), y=int(r["played"]), tagged=bool(QT.match(r["tag"] or ""))) for r in H if r["play"] != "" and r["played"] != ""]
    a, b, c = Q.fit(cal)
    return lambda p, tagged: 1 / (1 + math.exp(-(a + b * Q.logit(p) + (c if tagged else 0))))


def f1(v):
    return "%+.1f (%d)" % (sum(v) / len(v), len(v)) if v else "-"


def tier_sections(H, last):
    """Last night read tier by tier (6-drafter or 4, whatever ran): T1 the elite, T2 the Q lane and ADP drift, T3/T4 your
    takes, T5 drafted% and swap targets, then late news (tag changes AM to PM and scratches) by tier."""
    w = {x: {r["player_id"]: r for r in H if r["date"] == last and r["window"] == x} for x in ("am", "pm")}
    base = w["pm"] or w["am"]
    tier = lambda r: int(r["tier"])
    drafted = lambda r: num(r["adp"]) is not None and num(r["adp"]) < G.cap(r)
    def move(pid):
        a, p = w["am"].get(pid), w["pm"].get(pid)
        return "ADP %s to %s" % (a["adp"] or "-", p["adp"] or "-") if a and p and a["adp"] != p["adp"] else "ADP %s" % ((p or a)["adp"] or "-")
    md = ["## Last night tier by tier: %s" % last, ""]
    t1 = sorted([r for r in base.values() if tier(r) == 1], key=G.adp)
    md.append("**T1** (Boom tiebreak in the AM): " + "; ".join("%s %s, Boom %s, scored %s" % (
        r["name"], move(r["player_id"]), "%.0f%%" % (100 * num(r["boom"])) if num(r["boom"]) is not None else "-", r["actual"] or "-") for r in t1))
    t2 = sorted([r for r in base.values() if tier(r) == 2], key=G.adp)
    q2 = [r for r in t2 if QT.match(r["tag"] or "")]
    def drift(pid):
        a, p = w["am"].get(pid), w["pm"].get(pid)
        return abs(num(a["adp"]) - num(p["adp"])) if a and p and num(a["adp"]) is not None and num(p["adp"]) is not None else 0
    dr = [r for r in t2 if drift(r["player_id"]) >= 1]
    md.append("**T2** (Q lane, ADP drift of a pick or more AM to PM): " + ("; ".join("%s %s, scored %s" % (r["name"], move(r["player_id"]), r["actual"] or "-") for r in dr) or "none of %d moved a pick" % len(t2)) +
              (". Tagged: " + "; ".join("%s %s, %s" % (r["name"], r["tag"], "sat" if r["played"] == "0" else "played") for r in q2) if q2 else ". No tags."))
    tk = [r for r in csv.DictReader(open(os.path.join(REP, "takes_history.csv"))) if r["date"] == last and r["tier"] in ("3", "4")]
    md.append("**T3/T4** (sources above; your takes against the button): " + (", ".join(
        "%s %s" % (x.upper(), f1([float(r["gain"]) for r in tk if r["window"] == x])) for x in ("am", "pm") if any(r["window"] == x for r in tk)) or "no takes"))
    t5 = sorted([r for r in base.values() if tier(r) == 5 and drafted(r)], key=lambda r: -(num(r["drafted"]) or 0))[:5]
    sw = collections.Counter()
    fp = {}
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        if r["date"] == last:
            sw[r["swap"]] += int(r["teams"])
            fp[r["swap"]] = r["swap_fp"]
    md.append("**T5** (most drafted; swap targets): " + "; ".join("%s %s%%, scored %s" % (r["name"], r["drafted"] or "-", r["actual"] or "-") for r in t5) +
              ". Swaps landed on: " + ("; ".join("%s (%d teams, %s)" % (k, v, fp[k]) for k, v in sw.most_common(4)) or "none credited"))
    news = []
    for pid, r in base.items():
        a, p = w["am"].get(pid), w["pm"].get(pid)
        ta, tp = (a or {}).get("tag") or "-", (p or {}).get("tag") or "-"
        if (a and p and ta != tp) or r["scratched"] == "1":
            news.append((tier(r), "T%d %s: %s%s" % (tier(r), r["name"], "%s to %s" % (ta, tp) if ta != tp else ta, ", scratched" if r["scratched"] == "1" else "")))
    md += ["**Late news by tier** (tag at the AM lock to the PM lock; scratched: scored through the swap): " +
           ("; ".join(x for _, x in sorted(news)) or "none"), ""]
    return md


def season_tables(H):
    """One table per tier: the season's pairs by window, your board against the window's projection and ADP, and VALUE
    against its partners (6-drafter pods, primary sample)."""
    md = []
    groups = [(n, t, None) for n, t in (("T1", {1}), ("T2", {2}), ("T3/T4", {3, 4}), ("T5", {5}))]
    res = {x: G.grade(H, "6", x, "primary", groups) for x in ("am", "pm")}
    for i, (gname, _, _) in enumerate(groups):
        md += ["**%s**" % gname, "", "| Window | vs projection | vs ADP | VALUE vs partners |", "|---|---|---|---|"]
        for x, src in (("am", "Ours"), ("pm", "ETR")):
            _, nights, h2h, _, _, flags, _ = res[x][i]
            flat = lambda d: [v for vs in d.values() for v in vs]
            md.append("| %s (%d nights) | %s | %s | %s |" % (x.upper(), nights if isinstance(nights, int) else len(nights), f1(flat(h2h[src][0])), f1(flat(h2h["ADP"][0])), f1(flat(flags["VALUE"]))))
        md.append("")
    md.append("Points per pair (pairs); positive: your board won, or VALUE beat its partners. The verdicts and policy labels are in tier_grade.md.")
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "br-adp-mirror"))
    a = ap.parse_args()
    H = G.load()
    leans = json.load(open(os.path.join(REP, "leans.json")))
    status = {x["id"]: ("provisional" if x.get("provisional") else "RULE" if x.get("basis") == "RULE" else "adopted") for x in leans["adopted"]}
    pcal = calibrated_play(H)
    md = []
    # ---------------- today
    s, lock, day = today_slate(a.mirror)
    if s:
        players = [p for p in s["players"] if p.get("player_id")]
        pod = 4 if max((p.get("adp") or 0) for p in players) <= 28 else 6
        cap = 24 if pod == 4 else 36
        mo = {norm(r["name"]): r for r in json.load(open(os.path.join(a.mirror, "nba_morning.json"))).get("players", [])}
        sit_doc = json.load(open(os.path.join(a.mirror, "nba_sit.json")))
        sit_day = sit_doc if sit_doc.get("date") == day else (sit_doc.get("days") or {}).get(day) or {}
        sit = {norm(k): v for k, v in (sit_day.get("players") or {}).items()}
        rows = []
        for p in players:
            name = (p.get("first_name") or "") + " " + (p.get("last_name") or "")
            m = mo.get(norm(name)) or {}
            rows.append({"p": p, "name": name, "team": p.get("team") or "", "adp": p.get("adp"), "proj": m.get("fp"),
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
        md += ["# Today: %s, lock %s PT, %d-drafter pods" % (s["label"].replace("nba_", "").replace("_", " ").title(),
                                                                 lock.astimezone(PT).strftime("%-I:%M %p"), pod), "",
               "## Today's decisions", "", "**Switches by tier** (AM window · PM window)"]
        for t, am, pm, ids in SWITCHES:
            st = ", ".join("%s %s" % (i.split("-")[0].upper(), status.get(i, "kept")) for i in ids) or "kept"
            md.append("- T%d: AM %s · PM %s (%s)" % (t, am, pm, st))
        md += ["- Everywhere: VALUE first in the tier (adopted), PRICEY last; the one-tier cap (adopted); "
               "PM Questionable two tiers back (adopted); AM Questionable no push (adopted). Ownership tiebreak in T5: paused.", ""]
        if pod == 4:
            md += ["Small slate: the switches above were chosen on 6-drafter slates; nothing is adopted for 4-drafter pods yet.", ""]
        tagged = sorted([r for r in pool if QT.match(r["tag"]) and r["adp"] is not None and r["adp"] < cap], key=adp)
        md.append("**Q-tags** (calibrated chance to play; tier at the morning read)")
        if tagged:
            for r in tagged:
                md.append("- %s %s, %s, %d%% to play: T%d · AM stays T%d · PM to T%d" % (
                    r["name"], r["team"], r["tag"], round(100 * r["play"]), r["c"], r["c"], min(5, r["c"] + 2) if r["tag"].lower().startswith("q") else r["c"]))
        else:
            md.append("- none drafted on this slate")
        val = sorted([r for r in pool if r["flag"] == "VALUE" and r["c"] >= 3 and r["adp"] is not None and r["adp"] < cap], key=adp)
        md += ["", "**VALUE flags, T3-T5** (first in their tier): " + (", ".join("%s (T%d, ADP %.1f)" % (r["name"], r["c"], r["adp"]) for r in val) or "none")]
        ben = []
        for tg in tagged + [r for r in pool if r["tag"].lower().startswith("o")]:
            for r in pool:
                if r["team"] == tg["team"] and r is not tg and (r["adp"] is None or r["adp"] >= cap - 6) and (r["proj"] or 0) >= 15:
                    ben.append("%s (%s, %s) if %s sits (%d%% to play)" % (r["name"], r["team"], "undrafted" if r["adp"] is None or r["adp"] >= cap else "ADP %.1f" % r["adp"],
                                                                         tg["name"], round(100 * tg["play"])))
        md += ["", "**Beneficiaries to watch** (cheap teammates of a tagged player; PM T5 beneficiary picks are adopted): " + ("; ".join(ben[:8]) or "none"),
               "", "**Swap board**: once you're done drafting, open Swaps on the board (leverage is the default) and Apply, then do your "
               "round-6 shuffle in the app. Your app order is graded from the contest rosters (my_swaps.md).", ""]
    else:
        md += ["# Today", "", "No main slate today on the mirror yet.", ""]
    # ---------------- shadow scoreboard
    md += ["## Shadow scoreboard (forward from 2026-11-10)", ""]
    sh = open(os.path.join(REP, "shadow.md")).read().splitlines()
    md += [l for l in sh if l.startswith("|")]
    # ---------------- last night
    last = max(r["date"] for r in H)
    md += ["", "## Last night by tier: %s" % last, ""]
    for w, src in (("am", "Ours"), ("pm", "ETR")):
        rows_n = [r for r in H if r["date"] == last and r["window"] == w]
        if not rows_n:
            continue
        pod_n = rows_n[0]["pod"]
        res = G.grade(H, pod_n, w, None, [(n, t, None) for n, t in (("T1", {1}), ("T2", {2}), ("T3/T4", {3, 4}), ("T5", {5}))])
        lines = []
        for gname, nights, h2h, hits, brk, flags, fpl in res:
            per = h2h[src][0].get(last, [])
            pa = h2h["ADP"][0].get(last, [])
            vf = flags["VALUE"].get(last, [])
            lines.append("- %s: vs %s %s · vs ADP %s · VALUE %s" % (
                gname, src, "%+.1f (%d)" % (sum(per) / len(per), len(per)) if per else "-",
                "%+.1f (%d)" % (sum(pa) / len(pa), len(pa)) if pa else "-", "%+.1f (%d)" % (sum(vf) / len(vf), len(vf)) if vf else "-"))
        md += ["**%s** (%s; points per pair, pairs; positive: your board won / VALUE beat its partners)" % (w.upper(), rows_n[0]["board"])] + lines + [""]
    sw = [r for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))) if r["date"] == last]
    outs = collections.defaultdict(lambda: [0, 0.0, ""])
    for r in sw:
        o = outs[r["out"]]
        o[0] += int(r["teams"])
        o[1] += int(r["teams"]) * float(r["swap_fp"])
        o[2] = r["out_tier_pm"] or r["out_tier_am"]
    md += ["**Scratches and their swaps**: " + ("; ".join("%s (T%s): %d swaps averaging %.1f" % (k, v[2], v[0], v[1] / v[0]) for k, v in outs.items()) or "none credited"), ""]
    # ---------------- last night, tier by tier
    md += tier_sections(H, last)
    # ---------------- season
    md += ["## Season", ""] + season_tables(H) + ["", "**Adopted and rules** (leans.json)"]
    for x in leans["adopted"]:
        md.append("- %s: %s %s" % (status[x["id"]], x["statement"], "(" + x["evidence"].split(";")[0] + ")"))
    md += ["", "**Paused**: " + "; ".join(x["statement"] for x in leans.get("paused", [])), "",
           "Full tables: tier_grade.md (by tier and window), tier_rules.md, q_lane.md, swap_board.md, my_swaps.md, backtest_rest.md, "
           "decision_register.csv."]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
