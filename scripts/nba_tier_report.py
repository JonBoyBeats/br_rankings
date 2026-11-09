"""NBA morning report by tier, built for a phone. Writes analysis/nba/report/today.md and prints it.

  Top        pipeline health (a line per input: contests, results, swaps credited, ETR, Lock AM and PM with any fallback,
             ADP snapshots, and today's inputs due by 4:30am PT); Monday proposals (computed every day, decided Mondays);
             the monthly re-check when it's due; today's playbook: the switches, the draft card, today's Q-tags and how
             they're handled, VALUE flags, beneficiaries, the swap board, changes this week
  By tier    T1, T2, T3/T4, T5, each in four blocks: last night (your board against ETR, ours and ADP on decision pairs,
             AM and PM; your takes by source; the flags; breakers, scratches and swaps), keep doing (the rules in force,
             points and money), testing (provisional switches and ideas under test: forward nights x/14, the shadow so
             far, money), worth a look (the biggest misses and their causes); then the contest side's block for the tier
             (analysis/nba/report/money_tiers.json, {"tiers": {"T1": [lines], "T2": [...], "T3/T4": [...], "T5": [...]}}
             or the tier keys at the top level; a tier's value may also be {"lines": [...]}; "contest block pending"
             until it exists)
  Season     one table per tier and window, takes by source and tier, the adopted leans and rules

Today's slate is read at report time (ADP now, the morning projection file): a directional read, since the board's own
Proj isn't on the server; the real build is the Tiers button.

  python3 scripts/nba_tier_report.py --mirror ../br-adp-mirror
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
RECHECK = os.path.join(REP, "recheck.json")      # {"last": "YYYY-MM"}: the month of the last monthly re-check
PT = ZoneInfo("America/Los_Angeles")
QT = re.compile(r"^(q|d|g)", re.I)
num = G.num
FORWARD_NIGHTS = 14
GROUPS = [("T1", {1}), ("T2", {2}), ("T3/T4", {3, 4}), ("T5", {5})]
SWITCHES = [   # (tier, AM switch, PM switch, the decision_register.csv ids of the AM and PM switch)
    (1, "ADP (2: Boom)", "ETR", ["kept-am-t1", "kept-pm-t1"]),
    (2, "ADP", "ADP (2: ETR)", ["kept-am-t2", "pm-t2-adp-etr2"]),
    (3, "Proj (3: ADP)", "ETR (ties: ADP, Boom)", ["kept-am-middle", "kept-pm-t3"]),
    (4, "Proj (3: ADP)", "ADP (2: ETR)", ["kept-am-middle", "pm-t4-adp-etr2"]),
    (5, "the button's order, then the less drafted within 2 pts", "ADP, then the less drafted within 2 pts",
     ["am-t5-button-order", "pm-t5-adp-value"]),
]
TIEBREAKS = {5: "ownership-tiebreak-t5"}    # a provisional tiebreak on top of the tier's switches, by register id
DRAFT_CARD = [   # in-draft rules, money-backed (contest side, 2026-11-09; register rows card-*); index.html #draftCard
    ("2/3 turn: reach toward the higher projection", "card-turn23-reach-higher-proj"),
    ("1/2 turn: don't reach unless a top player falls (reaching:", "card-turn12-reach"),
    ("Fallers: always take them", "card-fallers"),
    ("Avoid same-position teammates (holding them:", "card-same-position-teammates"),
    ("Opposing stars from the same game: a plus", "card-opposing-stars"),
]
SHORT = {   # leans.json ids, as the phone shows them
    "am-t5-button-order": "AM T5: the button's order (your moves off it are takes)",
    "value-up-middle-t5": "VALUE first in the tier (T3-T5)",
    "pm-questionable-back-two": "PM: a Questionable player two tiers back",
    "am-questionable-no-push": "AM: no push for a Questionable player",
    "pm-t5-beneficiary-picks": "PM T5: beneficiary picks",
    "pm-t2-adp-etr-2": "PM T2: ADP (2: ETR)",
    "pm-t4-adp-etr-2": "PM T4: ADP (2: ETR)",
    "pm-t5-adp-value-up": "PM T5: ADP, VALUE first",
    "keep-one-tier-cap": "the one-tier cap",
    "t5-less-drafted-within-2": "T5: the less drafted within 2 pts",
}
SHADOW_REG = {"t5-less-drafted-am": "ownership-tiebreak-t5", "t5-less-drafted-pm": "ownership-tiebreak-t5",
              "pm-t5-vs-old-etr": "pm-t5-adp-value"}     # shadow.json ids whose money verdict sits on another register row
MONEY_NOTE = ("Everything adopted or kept is provisional until its money verdict (top finishes and dollars, from the contest "
              "side: decision_register.csv) is in, and may be changed by it.")


def norm(s):
    return T.re.sub(r"[^a-z ]", "", (s or "").lower().replace("-", " ").replace(".", "")).strip()


def iso(t):
    return dt.datetime.fromisoformat(str(t).replace("Z", "+00:00"))


def hm(t):
    return iso(t).astimezone(PT).strftime("%-I:%M%p").lower() if t else "-"


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


# ---------------------------------------------------------------- Monday proposals and the monthly re-check
def proposals(shadow, hyp, reg, leans):
    """What the evidence says to decide (nothing changes without a yes). Switches and ideas at 14 forward nights by
    their drop rule and bar; ideas leaning against early; a free test slot with a queued idea; money against an adopted
    rule under money_policy."""
    out = []
    for c in shadow:
        n, fv = c["forward_nights"], c["forward"]
        lab = fv.get("label") or ""
        if c["kind"] == "switch" and c.get("drop_if") and n >= FORWARD_NIGHTS:
            won, lost = lab.startswith(("LEAN +", "RULE +")), lab.startswith(("LEAN -", "RULE -"))
            if c["drop_if"] == "loss":
                out.append("%s: %s after %d nights (%s)" % (c["name"], "drop: it lost to the old rule" if lost else "keep, adopt for good", n, fv["text"]))
            else:
                out.append("%s: %s after %d nights (%s)" % (c["name"], "keep, adopt for good" if won else "drop: it didn't beat the old rule", n, fv["text"]))
        if c["kind"] == "candidate":
            if n >= FORWARD_NIGHTS:
                won = lab.startswith(("LEAN +", "RULE +"))
                m = (reg.get((hyp.get(c["id"]) or {}).get("register"), {}) or {}).get("money_verdict", "pending")
                against = "against" in m.split(" (")[0]
                out.append("%s: %s after %d nights (%s; money %s)" % (c["name"], "adopt" if won and not against else "drop", n, fv["text"], m.split(" (")[0]))
            elif lab.startswith(("LEAN -", "RULE -")) and fv.get("n", 0) >= 40:
                out.append("%s: leaning against forward (%s, %d nights): drop early?" % (c["name"], fv["text"], n))
    testing = collections.Counter(t for h in hyp.values() if h.get("status") == "testing" for t in h["tiers"])
    for k, h in hyp.items():
        if h.get("status") == "queued" and all(testing[t] < 3 for t in h["tiers"]):
            out.append("%s: a test slot is free in T%s: start testing \"%s\"?" % (k, "/T".join(map(str, h["tiers"])), h["idea"]))
    for x in leans.get("adopted", []):
        m = (reg.get(x.get("register")) or {}).get("money_verdict", "pending").split(" (")[0]
        if "against" in m:            # money_policy: a money LEAN can't overturn a points RULE; a MONEY RULE can
            points_rule = x.get("basis") == "RULE" or ", RULE)" in x.get("evidence", "")
            if m.startswith("RULE") or not points_rule:
                out.append("%s: money is %s, points %s: drop? (money_policy)" % (SHORT.get(x["id"], x["id"]), m, x.get("basis")))
    return out


def recheck_due(today):
    last = json.load(open(RECHECK)).get("last") if os.path.exists(RECHECK) else None
    return last != today[:7]


# ---------------------------------------------------------------- today's playbook
def playbook(mirror, H, reg, by_reg, money, leans, hyp, today):
    md = []
    s, lock, day, latest = today_slate(mirror)
    md += ["## Today's playbook", "", MONEY_NOTE, ""]
    if s:
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
        md += ["**%s, lock %s PT, %d-drafter pods**" % (s["label"].replace("nba_", "").replace("_", " ").title(),
                                                        lock.astimezone(PT).strftime("%-I:%M %p"), pod), "", "**Switches by tier** (AM · PM)"]
        for t, am, pm, ids in SWITCHES:
            st = "; ".join("%s %s, %s" % (w, by_reg.get(i, "kept"), money(i)) for w, i in zip(("AM", "PM"), ids))
            if t in TIEBREAKS:
                st += "; tiebreak %s, %s" % (by_reg.get(TIEBREAKS[t], "kept"), money(TIEBREAKS[t]))
            md.append("- T%d: AM %s · PM %s (%s)" % (t, am, pm, st))
        md += ["- Everywhere: VALUE first in the tier, PRICEY last; the one-tier cap; PM Questionable two tiers back; AM Questionable no push.", ""]
        if pod == 4:
            md += ["Small slate: the switches were chosen on 6-drafter slates; nothing is adopted for 4-drafter pods yet.", ""]
        md += ["**Draft card**"] + ["- %s %s)" % (txt, money(rid)) if txt.endswith(":") else "- %s (%s)" % (txt, money(rid))
                                    for txt, rid in DRAFT_CARD] + [""]
        tagged = sorted([r for r in pool if QT.match(r["tag"]) and r["adp"] is not None and r["adp"] < cap], key=adp)
        md.append("**Q-tags and their handling** (calibrated chance to play; AM: no push; PM: two tiers back)")
        md += ["- %s %s, %s, %d%%: T%d · AM stays T%d · PM to T%d" % (
            r["name"], r["team"], r["tag"], round(100 * r["play"]), r["c"], r["c"], min(5, r["c"] + 2) if r["tag"].lower().startswith("q") else r["c"])
            for r in tagged] or ["- none drafted on this slate"]
        val = sorted([r for r in pool if r["flag"] == "VALUE" and r["c"] >= 3 and r["adp"] is not None and r["adp"] < cap], key=adp)
        md += ["", "**VALUE flags, T3-T5**: " + (", ".join("%s (T%d, ADP %.1f)" % (r["name"], r["c"], r["adp"]) for r in val) or "none")]
        ben = []
        for tg in tagged + [r for r in pool if r["tag"].lower().startswith("o")]:
            for r in pool:
                if r["team"] == tg["team"] and r is not tg and (r["adp"] is None or r["adp"] >= cap - 6) and (r["proj"] or 0) >= 15:
                    ben.append("%s (%s, %s) if %s sits" % (r["name"], r["team"], "undrafted" if r["adp"] is None or r["adp"] >= cap else
                                                            "ADP %.1f" % r["adp"], tg["name"]))
        md += ["", "**Beneficiaries to watch**: " + ("; ".join(ben[:8]) or "none"),
               "", "**Swap board**: after drafting, open Swaps on the board (leverage is the default) and Apply, then your round-6 "
               "shuffle in the app. Swaps are graded from the contest data, not from any lock.", ""]
    else:
        md += ["No main slate today on the mirror yet.", ""]
    week = (dt.date.fromisoformat(today) - dt.timedelta(days=7)).isoformat()
    ad = [x for x in leans.get("adopted", []) if x.get("adopted", "") >= week]
    ch = ["%s: %s" % (lab, ", ".join(SHORT.get(x["id"], x["id"]) for x in ad if bool(x.get("provisional")) == prov))
          for lab, prov in (("Adopted", False), ("Provisional", True)) if any(bool(x.get("provisional")) == prov for x in ad)]
    ch += ["Reinstated: " + ", ".join("%s (%s)" % (x["id"], x["on"]) for x in leans.get("reinstated", []) if x.get("on", "") >= week)] \
        if any(x.get("on", "") >= week for x in leans.get("reinstated", [])) else []
    ih = [k for k, h in hyp.items() if h.get("written", "") >= week]
    ch += ["Ideas under test: " + ", ".join(ih)] if ih else []
    md += ["**Changes this week**"] + ["- " + c for c in ch] + ([] if ch else ["- none"]) + [""]
    return md


# ---------------------------------------------------------------- by tier
def tier_blocks(H, last, gname, tiers, shadow, reg, leans, hyp, money, money_tiers):
    md = ["## %s" % gname, ""]
    # last night
    md.append("**Last night (%s)**, points per pair (pairs); positive: your board won" % last)
    for w in ("am", "pm"):
        rn = [r for r in H if r["date"] == last and r["window"] == w]
        if not rn:
            md.append("- %s: no board" % w.upper())
            continue
        res = G.grade(H, rn[0]["pod"], w, None, [(gname, tiers, None)])[0]
        _, _, h2h, _, brk, flags, _ = res
        srcs = [s for s, _ in G.sources(w)]
        md.append("- %s%s: %s · VALUE %s · PRICEY %s" % (
            w.upper(), " (fallback)" if "fallback" in rn[0]["board"] else "", " · ".join("vs %s %s" % (s, f1(h2h[s][0].get(last, []))) for s in srcs),
            f1(flags["VALUE"].get(last, [])), f1(flags["PRICEY"].get(last, []))))
    tk = [r for r in csv.DictReader(open(os.path.join(REP, "takes_history.csv"))) if r["date"] == last and int(r["tier"]) in tiers]
    by_src = collections.defaultdict(list)
    for r in tk:
        by_src[r.get("source") or "OTHER"].append(float(r["gain"]))
    md.append("- Your takes by source: " + ("; ".join("%s %s" % (k, f1(v)) for k, v in sorted(by_src.items())) or "none"))
    pm = [r for r in H if r["date"] == last and r["window"] == "pm" and int(r["tier"]) in tiers] or \
         [r for r in H if r["date"] == last and r["window"] == "am" and int(r["tier"]) in tiers]
    brk = [r["name"] for r in pm if r["breaker"] == "1"]
    scr = [r for r in pm if r["scratched"] == "1"]
    sw = collections.defaultdict(lambda: [0, 0.0])
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        if r["date"] == last:
            sw[r["out"]][0] += int(r["teams"])
            sw[r["out"]][1] += int(r["teams"]) * float(r["swap_fp"])
    md.append("- Breakers: %s. Scratches: %s" % (", ".join(brk) or "none", "; ".join(
        "%s (%s)" % (r["name"], "swaps averaged %.1f over %d" % (sw[r["name"]][1] / sw[r["name"]][0], sw[r["name"]][0]) if sw[r["name"]][0] else "no swaps credited")
        for r in scr) or "none"))
    # keep doing
    md += ["", "**Keep doing** (points · money)"]
    for t, am, pm_, ids in SWITCHES:
        if t in tiers:
            md.append("- T%d switches: AM %s (%s) · PM %s (%s)" % (t, am, money(ids[0]), pm_, money(ids[1])))
    for x in leans.get("adopted", []):
        xt = x.get("tier")
        hit = xt in tiers if isinstance(xt, int) else any(int(c) in tiers for c in re.findall(r"\d", str(xt))) if xt not in (None, "all") else True
        if hit:
            md.append("- %s%s · points %s · %s" % ("provisional: " if x.get("provisional") else "", SHORT.get(x["id"], x["statement"][:70]),
                                                 x.get("basis", "lean"), money(x.get("register"))))
    # testing
    md += ["", "**Testing** (forward nights of %d · shadow · money)" % FORWARD_NIGHTS]
    rows = [c for c in shadow if c["kind"] in ("switch", "candidate") and (c.get("drop_if") or c["kind"] == "candidate")
            and set(c["tiers"]) & tiers]
    for c in rows:
        rid = (hyp.get(c["id"]) or {}).get("register") or SHADOW_REG.get(c["id"], c["id"])
        md.append("- %s: %d/%d · season %s · forward %s · %s" % (c["name"], min(c["forward_nights"], FORWARD_NIGHTS), FORWARD_NIGHTS,
                                                                c["season"]["text"], c["forward"]["text"], money(rid)))
    if not rows:
        md.append("- nothing under test")
    # worth a look
    md += ["", "**Worth a look**"]
    names = {r["name"] for r in H if r["date"] == last and int(r["tier"]) in tiers}
    mi = [r for r in csv.DictReader(open(os.path.join(REP, "misses.csv"))) if r["date"] == last and r["player"] in names
          and r["kind"] in ("miss", "split")]
    if mi:
        mi.sort(key=lambda r: -abs((num(r["ours"]) or 0) - (num(r["actual"]) or 0)))
        md += ["- %s: ours %s, actual %s, %s%s" % (r["player"], r["ours"], r["actual"], r["cause"], (": " + r["note"]) if r["note"] else "") for r in mi[:4]]
    elif any(r["date"] == last for r in csv.DictReader(open(os.path.join(REP, "misses.csv")))):
        md.append("- no logged misses in this tier")
    else:
        md.append("- misses not logged yet for %s (the skill's steps 3-4)" % last)
    # the contest side's block
    md += ["", "**Contest side**"]
    blk = money_tiers.get(gname) if money_tiers else None
    if blk is None:
        md.append("- contest block pending")
    elif isinstance(blk, list):
        md += ["- " + str(x) for x in blk]
    elif isinstance(blk, dict):
        md += ["- " + str(x) for x in blk.get("lines", [])] or ["- %s: %s" % (k, v) for k, v in blk.items()]
    else:
        md.append("- " + str(blk))
    return md + [""]


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
    money_tiers = json.load(open(mt_path)) if os.path.exists(mt_path) else None
    if money_tiers and isinstance(money_tiers.get("tiers"), dict):
        money_tiers = money_tiers["tiers"]
    today = dt.datetime.now(dt.timezone.utc).astimezone(PT).date().isoformat()
    _, _, _, latest = today_slate(a.mirror)
    last = max(r["date"] for r in H)
    md = ["# NBA morning report, %s (last night: %s)" % (today, last), "", "## Pipeline health", ""] + health(a.mirror, today, latest) + [""]
    props = proposals(shadow, hyp, reg, leans)
    md += ["## Monday proposals %s" % ("(today: decide)" if dt.date.fromisoformat(today).weekday() == 0 else "(as of today; decided Monday)"), ""]
    md += ["- " + p for p in props] or ["- none ripe"]
    if recheck_due(today):
        md.append("- Monthly re-check due for %s (the morning-report skill, step 1b); mark it done in recheck.json" % today[:7])
    md += [""]
    md += playbook(a.mirror, H, reg, by_reg, money, leans, hyp, today)
    for gname, tiers in GROUPS:
        md += tier_blocks(H, last, gname, tiers, shadow, reg, leans, hyp, money, money_tiers)
    md += ["## Season", ""] + season_tables(H)
    md += ["", "**Adopted and rules** (leans.json; points status, money verdict). " + MONEY_NOTE]
    for x in leans["adopted"]:
        md.append("- %s, %s: %s" % (status[x["id"]], money(x.get("register")), x["statement"]))
    md += ["", "**Paused**: " + ("; ".join(x["statement"] for x in leans.get("paused", [])) or "none"), "",
           "Full tables: tier_grade.md, tier_rules.md, q_lane.md, shadow.md, swap_board.md, my_swaps.md, money_points.md, decision_register.csv."]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
