"""The NBA results dashboard's data (asked 2026-11-17): analysis/nba/dashboard.json, read by nba_results.html.

It replaces the morning report's grading over time. One night per entry, so the page reads last night, the last 7 nights
or the season; the night is the unit. Definitions are fixed here (DEFS) and change only through the Friday report.

The common measure is the TOP-1% MULTIPLE: the share of top-1% lineups holding X over the share of all lineups holding X
(the top-10% one beside it; points as the backup). Player and group multiples come from the contest side
(money_tiers.json "player_multiples" and "groups_by_night", drafted picks only, swaps apart); until they're there, those
charts carry null and the page says it's waiting. Everything else is read from files already on disk: the contest
rosters and teams (nba_money.load), the button's tiers at each lock (tier_history.csv), your moves against the button
(takes_history.csv) and your swaps against your PM list (nba_swap_grade).

Pairs are a tally: a win or loss at PUSH+ points apart, a push under (nba_tier_season_tests.PUSH).

  python3 scripts/nba_dashboard.py --mirror ../br-adp-mirror
"""
import argparse, collections, csv, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M                 # noqa: E402  contests, teams, windows, drafted picks
import nba_swap_grade as SG           # noqa: E402  your swaps against your PM list
from nba_tier_season_tests import PUSH  # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = os.path.join(HERE, "analysis", "nba", "report")
OUT = os.path.join(HERE, "analysis", "nba", "dashboard.json")
num = M.num

DEFS = {
    "measure": "Top-1% multiple: share of top-1% lineups holding X / share of all lineups holding X (1.00 is the field). "
               "Top-10% beside it; points as the backup. Drafted picks only, swaps apart. Season reads: the night is the unit.",
    "header": "Your entries, cash rate, top-10% and top-1% finishes against expected (10% and 1% of your entries), and ROI "
              "((won - fees) / fees). Field cash rate: share of all entries that cashed.",
    "finish": "Each lineup's finish as a percentile of its contest (place / entries). Season: share of your lineups in each 1% "
              "band (the field is 1% in every band). Then how often you reached each line, the "
              "cash line to the top 0.1%: your finishes there over what the field's rate gives (1.00x is the field; cash uses each "
              "night's field cash rate).",
    "t1": "Afternoon T1 (the button's tier at the PM lock). Every pair ETR's order and ADP's order put differently: the top-1% "
          "multiple of ETR's first minus ADP's first, averaged for the night. Marker: the side your PM board took. Tally on "
          "points, pushes under 3.",
    "t2": "Afternoon T2, the same ETR-vs-ADP pairs. Elite-break teams (contest side's t2-elite-break) against the rest. "
          "Your 1/2 and 2/3 turn decisions: your share against the field's, each with its top-1% multiple.",
    "pod": "The main read on whether your moves help. Every real pod and seat replayed off your locked list and off each other "
           "list, placed in the real standings (contest side's pod replay). Each bar: your list's top-10% (or top-1%) rate minus "
           "that list's, in percentage points, with its 80% range from resampling nights; right of zero, your list did better. "
           "Season, and since the list's rules went live (rule_dates.json). Below it, PM only: which ETR version the PM should "
           "use (the ETR-tier button, pure ETR, ETR with the button's T5 rule; each row the first minus the second, since the "
           "PM button went to ETR tiers), and top 1% at your real seats against your list there. Each tier's own read (your "
           "moves in it, its ETR order) opens that tier's card below.",
    "t34": "Secondary to the pod replay. Your moves against the button in the tier (takes_history.csv, Q-tagged pairs left out): for each move, the top-1% "
           "multiple of the player you moved up minus the player you moved down, in that window; summed for the night, "
           "with a running total. Tally on points, pushes under 3. VALUE / normal / PRICEY: your share of lineups holding "
           "one against the field's, each group's top-1% multiple.",
    "t5": "Drafted picks only. Lineups holding a T5 pick drafted in under 60% of pods, one at or over 60%, and (their own group) "
          "a T4 PRICEY player the button dropped into T5 (its tier before the T5 rules; left out of the two 60% groups so "
          "those read T5 leverage only): your share of lineups against the field's, each group's top-1% multiple. Second: your round-6 pick (each lineup's latest-ADP drafted pick, played) against the field's "
          "average round-6 pick, in points. Swaps apart: your swap list's player against the one your PM list would have "
          "taken, in points.",
}


# T5's groups (contest side's groups_by_night keys): T5 leverage under / at-over the 60% line, and the T4 PRICEY players the
# button drops into T5 on their own (the button's tier before its T5 rules, as nba_friday.dropped; 2026-11-17)
T5_GROUPS = (("under", "T5 under"), ("over", "T5 over"), ("dropped", "T4 PRICEY (dropped into T5)"))


def mult(pm, date, window, pid, k="top1"):
    x = ((pm.get(date) or {}).get(window) or {}).get(pid)
    return x[k][0] if x and x.get(k) and x[k][0] is not None else None


def tally(diffs):
    return [sum(d >= PUSH for d in diffs), sum(d <= -PUSH for d in diffs), sum(abs(d) < PUSH for d in diffs)]


def etr_adp_pairs(n, tier, pm, window="pm"):
    """Pairs in the button's tier that the window's projection (afternoon ETR, morning ours) and ADP order differently;
    "etr" names the projection's first either way."""
    rows = [r for r in (n["tiers"].get(window) or {}).values() if r.get("sample", "primary") == "primary" and r["tier"] == str(tier)
            and num(r["proj"]) is not None and num(r["adp"]) is not None and r["played"] == "1" and num(r["actual"]) is not None]
    out = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            pa, pb, aa, ab = num(a["proj"]), num(b["proj"]), num(a["adp"]), num(b["adp"])
            if pa == pb or aa == ab or (pa > pb) == (aa < ab):
                continue
            e, d = (a, b) if pa > pb else (b, a)                    # ETR's first, ADP's first
            me = None
            if num(e.get("your_rank")) is not None and num(d.get("your_rank")) is not None:
                me = "etr" if num(e["your_rank"]) < num(d["your_rank"]) else "adp"
            me_m, ad_m = mult(pm, n["date"], window, e["player_id"]), mult(pm, n["date"], window, d["player_id"])
            out.append({"etr": e["name"], "adp": d["name"], "mine": me,
                        "mult": round(me_m - ad_m, 3) if me_m is not None and ad_m is not None else None,
                        "pts": round(num(e["actual"]) - num(d["actual"]), 1)})
    return out


def pair_block(pairs):
    ms = [p["mult"] for p in pairs if p["mult"] is not None]
    return {"pairs": pairs, "value": round(sum(ms) / len(ms), 3) if ms and len(ms) == len(pairs) else None,
            "tally": tally([p["pts"] for p in pairs]), "mine_etr": sum(p["mine"] == "etr" for p in pairs),
            "mine_adp": sum(p["mine"] == "adp" for p in pairs)}


def moves(date, tier, pm, takes, tags):
    out = []
    for r in takes:
        if r["date"] != date or r["tier"] != str(tier):
            continue
        if tags.get((date, r["window"], r["you_first_id"])) or tags.get((date, r["window"], r["button_first_id"])):
            continue
        a, b = mult(pm, date, r["window"], r["you_first_id"]), mult(pm, date, r["window"], r["button_first_id"])
        out.append({"window": r["window"], "up": r["you_first"], "down": r["button_first"], "pts": float(r["gain"]),
                    "mult": round(a - b, 3) if a is not None and b is not None else None})
    ms = [x["mult"] for x in out if x["mult"] is not None]
    return {"moves": out, "value": round(sum(ms), 3) if out and len(ms) == len(out) else (0.0 if not out else None),
            "tally": tally([x["pts"] for x in out])}


def round6(n):
    """Your lineups' round-6 pick (latest-ADP drafted pick, played) against the field's, in points."""
    pts = {p: num(r["actual"]) for p, r in n["rec"].items() if num(r.get("min")) and num(r["actual"]) is not None}
    mine, field = [], []
    for ts in n["teams"].values():
        for t in ts:
            drafted = [(a, p) for p, a in zip(t["picks"], t["adps"]) if a is not None]
            if len(drafted) < 6:
                continue
            p = max(drafted)[1]
            if p in pts:
                field.append(pts[p])
                if t["mine"]:
                    mine.append(pts[p])
    avg = lambda v: round(sum(v) / len(v), 2) if v else None
    return {"mine": avg(mine), "field": avg(field), "mine_n": len(mine)}


# Pod replay (contest side's nba_pod_replay.py): (a) my locked list against each list through the real pods and seats.
# Season comes from its file as written; "since" re-pools its by-night rates from the first night the list's rules were
# live (rule_dates.json), with the same night resampling (M.boot_range). In percentage points, (a) minus the list.
POD_KEYS = ("top10", "top1")
POD_RULES = {"b": None, "d": None, "e": None, "f": None, "g": None,   # the button's whole rule set
             "c1": ("elite-", "q-t1-"), "c2": ("t2-",), "c3": ("t34-", "t3-"), "c4": ("t34-", "t4-"), "c5": ("t5-", "q-t5-")}
POD_RULES.update({"f%d" % k: POD_RULES["c%d" % k] for k in range(1, 6)})   # one tier in ETR's order (PM): that tier's rules
POD_ETR = ("f-e", "g-f", "g-e", "fn-f", "fn-e")    # which ETR version for the PM: the ETR-tier button, pure ETR, ETR with the button's T5 rule


def pod_since(rd, lst):
    """First night every one of the list's ranking rules was live, per window (the latest of their dates)."""
    out = {}
    for k, v in rd.items():
        if k.startswith("_") or not v.get("windows"):
            continue                                            # rules without per-window dates aren't the button's ranking
        if POD_RULES[lst] and not k.startswith(POD_RULES[lst] + ("tiers-",)):     # "tiers-": the whole ladder, every tier
            continue
        for w, d in v["windows"].items():
            out[w] = max(out.get(w, d), d)
    return out


def pod_paired(rows, w, y, key, since=None, last=None):
    """(a) minus y, seat-weighted over the night-windows where both ran (on or after since[window], or only the last `last`
    nights they both ran); nights resampled."""
    by = collections.defaultdict(list)
    for r in rows:
        if r["window"] in (("am", "pm") if w == "both" else (w,)) and r.get("a") and r.get(y) \
                and (not since or r["date"] >= since.get(r["window"], "9999")):
            by[r["date"]].append(r)
    cells = [by[d] for d in sorted(by)][-last:] if last else [by[d] for d in sorted(by)]

    def fn(ns):
        flat = [r for c in ns for r in c]
        tot = sum(r["a"]["seats"] for r in flat)
        return sum(r["a"]["seats"] * (r["a"][key] - r[y][key]) for r in flat) / tot if tot else None
    v = fn(cells) if cells else None
    rng = M.boot_range(cells, fn) if v is not None else None
    r100 = lambda x: None if x is None else round(100 * x, 3)
    return {"nights": len(cells), "diff": r100(v), "lo": r100(rng[0]) if rng else None, "hi": r100(rng[1]) if rng else None}


def pod_replay():
    p, q = os.path.join(REP, "pod_replay.json"), os.path.join(REP, "rule_dates.json")
    if not os.path.exists(p):
        return None
    pr, rd = json.load(open(p)), json.load(open(q)) if os.path.exists(q) else {}
    out = {"generated": pr.get("generated"), "labels": pr.get("labels"), "through": (pr.get("nights") or [None])[-1],
           "mine": {w: {k: (pr["season"].get(w, {}).get("a") or {}).get(k) for k in POD_KEYS + ("nights",)} for w in pr.get("season", {})},
           "since": {}, "rows": {}}
    for y in POD_RULES:
        out["since"][y] = pod_since(rd, y)
        for w, ys in (pr.get("paired") or {}).items():
            if y not in ys:
                continue
            out["rows"].setdefault(w, {})[y] = {k: {"season": ys[y].get(k),
                                                    "since": pod_paired(pr["by_night"], w, y, k, out["since"][y]) if out["since"][y] else None,
                                                    "last": pod_paired(pr["by_night"], w, y, k, last=1),       # the newest night it ran
                                                    "last7": pod_paired(pr["by_night"], w, y, k, last=7)}      # its last 7 nights
                                                for k in POD_KEYS}
    eb = pr.get("pm_etr_button") or {}
    out["etr"] = {"since": eb.get("since"), "f_vs_board": eb.get("f_vs_board"), "nodrop_touched": {k: v for k, v in (eb.get("nodrop_touched") or {}).items() if k != "by_night"},
                  "rows": {y: {k: {"season": ((pr.get("paired") or {}).get("pm") or {}).get(y, {}).get(k),
                                   "since": (eb.get("pairs") or {}).get(y, {}).get(k)} for k in POD_KEYS}
                           for y in POD_ETR if ((pr.get("paired") or {}).get("pm") or {}).get(y)}}
    out["my_seats"] = pr.get("my_seats_top1")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "br-adp-mirror"))
    a = ap.parse_args()
    M.MIRROR_PATH = a.mirror
    N = M.load(a.mirror)
    mt = json.load(open(os.path.join(REP, "money_tiers.json"))) if os.path.exists(os.path.join(REP, "money_tiers.json")) else {}
    pm = mt.get("player_multiples") or {}
    gb = mt.get("groups_by_night") or {}
    cards = mt.get("card_decisions_by_night") or {}
    takes = list(csv.DictReader(open(os.path.join(REP, "takes_history.csv"))))
    tags = {}
    for r in csv.DictReader(open(os.path.join(REP, "tier_history.csv"))):
        tags[(r["date"], r["window"], r["player_id"])] = (r["tag"] or "")[:1].lower() == "q"
    swaps = collections.defaultdict(list)
    try:
        for s in SG.grade():
            swaps[s["date"]].append({k: s[k] for k in ("underdog", "swap_list", "pm_list", "pts_swap", "pts_pm", "differs", "matched")})
    except Exception as e:
        print("swaps not graded: %s" % e, file=sys.stderr)
    nights = []
    for n in N:
        if not n["contests"]:
            continue
        mine = [t for ts in n["teams"].values() for t in ts if t["mine"]]
        allt = [t for ts in n["teams"].values() for t in ts]
        fees, won = sum(t["contest"]["fee"] for t in mine), sum(t["payout"] for t in mine)
        night = {"date": n["date"], "pod": n["pod"],
                 "header": {"entries": len(mine), "am": sum(t["window"] == "am" for t in mine), "pm": sum(t["window"] == "pm" for t in mine),
                            "fees": round(fees, 2), "won": round(won, 2), "cashed": sum(t["payout"] > 0 for t in mine),
                            "top10": sum(t["top"][10] for t in mine), "top1": sum(t["top"][1] for t in mine),
                            "field_cash_rate": round(sum(t["payout"] > 0 for t in allt) / len(allt), 4) if allt else None},
                 "finish": sorted(round(t["fin"], 4) for t in mine)}
        night["t1"] = pair_block(etr_adp_pairs(n, 1, pm))
        night["t1am"] = pair_block(etr_adp_pairs(n, 1, pm, "am"))     # morning T1: our Proj's first against ADP's (asked 2026-11-18)
        night["t2"] = pair_block(etr_adp_pairs(n, 2, pm))
        g = gb.get(n["date"]) or {}
        night["t2"]["elite"] = {w: {k: (g.get(w) or {}).get(k) for k in ("elite-break teams", "other teams")} for w in ("am", "pm")} if g else None
        night["t2"]["turns"] = cards.get(n["date"]) or ([{"decision": c["decision"], **c["last_night"], "vs_field_top1": c.get("vs_field_top1"),
                                                         "vs_field_top10": c.get("vs_field_top10")} for c in (mt.get("card_decisions") or [])
                                                        if "turn" in c["decision"]] if mt.get("night") == n["date"] else None)
        for t in (3, 4):
            night["t%d" % t] = moves(n["date"], t, pm, takes, tags)
            night["t%d" % t]["flags"] = {w: {f: (g.get(w) or {}).get("T%d %s" % (t, f)) for f in ("VALUE", "normal", "PRICEY")}
                                        for w in ("am", "pm")} if g else None
        night["t5"] = {"groups": {w: {k: (g.get(w) or {}).get(src) for k, src in T5_GROUPS} for w in ("am", "pm")} if g else None,
                       "round6": round6(n), "swaps": swaps.get(n["date"], [])}
        nights.append(night)
    out = {"generated": M.dt.datetime.now(M.PT).isoformat(timespec="minutes"), "defs": DEFS, "push": PUSH,
           "contest_side": {"player_multiples": bool(pm), "groups_by_night": bool(gb), "card_decisions_by_night": bool(cards)},
           # the contest side's last-night and season reads as they stand (turns, T5 under/over), until the by-night keys land
           "latest": {"night": mt.get("night"), "card_decisions": mt.get("card_decisions"), "t5_drafted": mt.get("t5_drafted")},
           "pod_replay": pod_replay(), "nights": nights}
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    print("dashboard.json: %d nights, through %s; contest side: %s" % (len(nights), nights[-1]["date"] if nights else "-",
                                                                      ", ".join(k for k, v in out["contest_side"].items() if v) or "waiting"))


if __name__ == "__main__":
    main()
