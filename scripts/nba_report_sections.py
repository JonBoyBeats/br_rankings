"""The morning report's sections after the 2026-11-13 redesign (C in the redesign brief), used by nba_tier_report.py.

  rule_change        one line at the top when a rule went live on the board last night (rule_dates.json)
  decided            what decided the night: the 4-5 players whose holders' results moved the contest most, your share
                     against the field's, which of your moves faded them, one verdict line
  bets_and_fades     your biggest overweights (cut at the natural gap) and, in T1-T3, underweights: why, what the close
                     did after your lock (ETR's final, the late ADP), the result, sound/shaky and won/lost
  theme, night_line  each tier's theme and rules in two or three lines; T1/T2's night in one line (where ADP and the
                     projection disagreed, which one the night sided with, which one you sided with)
  moves              each move against the button, graded on the pair it changed (Q moves left out), and one season line
  turn_lines         T2: the turns from the contest side's card_decisions
  t5_menu            T5 graded on contest results: your share of round-6 picks drafted in under 60% of pods against the
                     field's, and how each group's holders did, last night and season
  contest            a tier's contest view: outsized holders, what the top-10% teams held that you were light on, and in
                     T3/T4 your VALUE share against the field's
  q_section          last night's Questionable players, your Q moves, the Swap button, the chance-to-play tracker, today's
  back               the morning projection against ETR, ETR against the box score, Gallagher's arrows, data notes
  gallagher_log      analysis/nba/report/gallagher_arrows.csv: every Bad-matchup arrow published before your lock, with the
                     player's result against ETR's final (for the Friday report)
"""
import collections, csv, datetime as dt, glob, json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G   # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = G.REP
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
TAKES = os.path.join(HERE, "analysis", "nba", "takes")
num = G.num
W = {"am": "morning", "pm": "afternoon"}

THEME = {
    1: ["**T1, the elite.** The players every pod takes first; the order is the decision. Morning: ADP, the higher Boom first "
        "within 2 picks. Afternoon: ETR. A Questionable player here drops to the top of T2."],
    2: ["**T2, the stars.** Morning: straight ADP. Afternoon: ADP with ETR breaking ties within 2 picks up to the elite break "
        "(pick 13 minus the elites with 6 drafters, 9 with 4), then ETR. The turns are where your share differs from the field's."],
    3: ["**T3, the middle.** VALUE first, then the rest, PRICEY last; morning by ADP, afternoon by ETR (ADP, then Boom, on "
        "exact ties). T3 PRICEY stays ahead of T4 VALUE."],
    4: ["**T4, to round 6.** The same sort as T3; it ends at the start of round 6 (earlier at a 2-pick ADP gap), never holds a "
        "round-6 player, sends its PRICEY players to T5 and borrows from the bottom of T3 when short of 4."],
    5: ["**T5, round 6.** Players drafted in under 60% of pods (50-60% at the bottom), projected for 20+ minutes, by projection, "
        "to your cut; everyone else below it by projection. Graded on contest results."],
}


def short(n):
    n = n.replace(" Jr.", "").replace(" III", "").replace(" II", "")
    return n.split(" ", 1)[-1] if " " in n else n


def pct(x):
    return "%d%%" % round(100 * x)


class _ByKey(dict):
    """A name lookup that also finds "P.J. Washington" under "PJ Washington" (nba_ledger's key)."""
    def get(self, k, d=None):
        import nba_ledger as L
        return dict.get(self, L.key_of(k), d)


def ledger(night):
    import nba_ledger as L
    p = os.path.join(HERE, "analysis", "nba", "ledger.csv")
    return _ByKey({L.key_of(r["name"]): r for r in csv.DictReader(open(p)) if r["date"] == night})


def daily_rows(night):
    for p in glob.glob(os.path.join(DAILY, "%s_*_main.csv" % night)):
        return {r["name"]: r for r in csv.DictReader(open(p))}
    return {}


def meta_of(night):
    m = json.load(open(os.path.join(DAILY, "meta.json")))
    return next((v for k, v in m.items() if k.startswith(night) and k.endswith("_main.csv")), {})


def takes_on(night):
    tk = [r for r in csv.DictReader(open(os.path.join(REP, "takes_history.csv"))) if r["date"] == night]
    return tk


def is_q(r):
    return bool(r) and (r.get("tag") or "")[:1].lower() == "q"


# ---------------------------------------------------------------- top
def rule_change(night):
    p = os.path.join(REP, "rule_dates.json")
    if not os.path.exists(p):
        return []
    rd = {k: v for k, v in json.load(open(p)).items() if not k.startswith("_")}
    new = [v["what"] for v in rd.values() if v.get("since") == night or (v.get("windows") or {}).get("pm") == night]
    if not new:
        return []
    return ["**New on the board last night:** " + "; ".join(new[:3]) + ("; and %d more (rulebook)." % (len(new) - 3) if len(new) > 3 else "."), ""]


def exposure(mt, night):
    """{name: {mine, field, lift, tier, window}} pooled over both windows, from the contest side's money_tiers.json."""
    if not mt or mt.get("night") != night:
        return {}
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
                    acc.setdefault(x["name"], {})[w] = dict(x, tier=int(k))
    if not den:
        return {}
    my_n, f_n = sum(m for m, _ in den.values()), sum(f for _, f in den.values())
    out = {}
    for name, by in acc.items():
        heavy = max(by, key=lambda w: by[w]["mine"])
        out[name] = {"mine": sum(by[w]["mine"] * den[w][0] for w in by) / my_n,
                     "field": sum(by[w]["field"] * den[w][1] for w in by) / f_n,
                     "lift": by[heavy].get("lift10"), "tier": by[heavy]["tier"], "window": heavy, "flag": by[heavy].get("flag")}
    return out


def decided(mt, night):
    ex = exposure(mt, night)
    rows = [(x["field"] * abs((x["lift"] or 1) - 1), n, x) for n, x in ex.items() if x["lift"] is not None and x["field"] >= 0.05]
    rows.sort(reverse=True)
    top = [r for r in rows[:5] if r[0] > 0.02]
    if not top:
        return []
    led, tk = ledger(night), takes_on(night)
    md = ["## What decided the night, and where you stood", ""]
    right = 0
    for _, n, x in top:
        l = led.get(n) or {}
        faded = [t for t in tk if t["button_first"] == n]
        backed = [t for t in tk if t["you_first"] == n]
        good = x["lift"] > 1
        right += (x["mine"] > x["field"]) == good
        bits = ["**%s** (%s): your %s against the field's %s; holders made the top 10%% %.1f times the field's rate." % (
            n, (l.get("actual") or "?"), pct(x["mine"]), pct(x["field"]), x["lift"])]
        if faded:
            bits.append("You faded him: %s." % "; ".join("%s ahead of him (%s)" % (short(t["you_first"]), W[t["window"]]) for t in faded[:3]))
        if backed:
            bits.append("You backed him: ahead of %s." % ", ".join(short(t["button_first"]) for t in backed[:3]))
        md.append("- " + " ".join(bits))
    md += ["", "Verdict: you were on the right side of %d of these %d (over the field where his holders beat it, under where they didn't)." % (
        right, len(top)), ""]
    return md


def natural_cut(vals, lo=3, hi=5):
    """How many to keep: the biggest drop between consecutive values after the lo-th, up to hi."""
    if len(vals) <= lo:
        return len(vals)
    best, k = -1, lo
    for i in range(lo, min(hi, len(vals) - 1) + 1):
        if vals[i - 1] - vals[i] > best:
            best, k = vals[i - 1] - vals[i], i
    return k


def bets_and_fades(mt, night, H):
    ex = exposure(mt, night)
    if not ex:
        return []
    rec, led, tk = daily_rows(night), ledger(night), takes_on(night)
    th = {(r["window"], r["name"]): r for r in H if r["date"] == night}
    notes = collections.defaultdict(list)
    for f, who in (("etr_matchups", "ETR"), ("zakarian", "Bagel")):
        p = os.path.join(TAKES, "%s_%s.csv" % (night, f))
        if os.path.exists(p):
            for t in csv.DictReader(open(p)):
                notes[t["player"]].append("%s %s" % (who, t["stance"]))

    def why(n, x, bet):
        mv = [t for t in tk if (t["you_first"] if bet else t["button_first"]) == n]
        if mv:
            src = mv[0]["source"] or "OTHER"
            return {"NEWS": "a news judgment", "OTHER": "your own read"}.get(src, "a %s note" % src.replace("+", " and "))
        r = th.get((x["window"], n)) or {}
        if notes.get(n):
            return notes[n][0]
        return {"VALUE": "VALUE (the button had him a tier up on the projection)", "PRICEY": "PRICEY"}.get(r.get("flag") or "", "the button's order")

    def close(n, x, bet):
        r = rec.get(n) or {}
        if x["window"] == "pm":
            e0, a0 = num(r.get("etr_pm")), num(r.get("adp_pm")) or num(r.get("adp_etr"))
        else:
            e0, a0 = num(r.get("etr_first")), num(r.get("adp_am"))
        e1, a1 = num(r.get("etr_last")), num(r.get("adp_close"))
        sgn, parts, score = (1 if bet else -1), [], 0
        if e0 is not None and e1 is not None and abs(e1 - e0) >= 0.5:
            parts.append("ETR %.1f to %.1f" % (e0, e1))
            score += sgn * (1 if e1 > e0 else -1)
        if a0 is not None and a1 is not None and abs(a1 - a0) >= 0.5:
            parts.append("ADP %.1f to %.1f" % (a0, a1))
            score += sgn * (1 if a1 < a0 else -1)
        if not parts:
            return "the close didn't move", 0
        return "%s: %s" % (", ".join(parts), "toward you" if score > 0 else "away from you" if score < 0 else "mixed"), score

    def line(n, x, bet):
        l = led.get(n) or {}
        txt, score = close(n, x, bet)
        won = (x["lift"] or 1) >= 1 if bet else (x["lift"] or 1) < 1
        sound = "sound" if score > 0 else "shaky" if score < 0 else "sound" if (x["lift"] is None) else "shaky"
        if score == 0:
            sound = "sound" if bet == ((num(l.get("gap")) or 0) >= 0) else "shaky"
        return "- **%s** (T%d): your %s against the field's %s; why: %s. At the close: %s. Result: %s%s. **%s and %s.**" % (
            n, x["tier"], pct(x["mine"]), pct(x["field"]), why(n, x, bet), txt, (l.get("note") or l.get("draft") or "no box line").rstrip("."),
            "; holders %.1f times the field at the top 10%%" % x["lift"] if x["lift"] is not None else "", sound.capitalize(), "won" if won else "lost")
    played = lambda n: (rec.get(n) or {}).get("min") not in ("", "0", "0.0", None)
    bets = sorted([(x["mine"] - x["field"], n, x) for n, x in ex.items() if x["mine"] > x["field"] and played(n)], reverse=True)
    fades = sorted([(x["field"] - x["mine"], n, x) for n, x in ex.items() if x["field"] > x["mine"] and x["tier"] <= 3 and played(n)], reverse=True)
    bets = bets[:natural_cut([b[0] for b in bets[:6]])]
    fades = fades[:natural_cut([f[0] for f in fades[:6]])]
    md = ["## Your biggest bets and fades", "", "**Bets.**", ""] + [line(n, x, True) for _, n, x in bets]
    md += ["", "**Fades (T1-T3).**", ""] + ([line(n, x, False) for _, n, x in fades] or ["None worth naming."])
    md += ["", "*Sound: the close moved toward your side after your lock (ETR's final, the late ADP); shaky: away. Won: holders beat "
           "the field's top-10% rate (bets) or didn't (fades). Players ruled out after the lock are left out.*", ""]
    return md


# ---------------------------------------------------------------- tiers
def night_line(H, night, t):
    """Where ADP and the projection disagreed in this tier, which one the night sided with, which one you did."""
    out = []
    for w in ("am", "pm"):
        rs = [r for r in H if r["date"] == night and r["window"] == w and r["tier"] == str(t) and r["played"] == "1"]
        dis = night_ = you = 0
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                x, y = rs[i], rs[j]
                px, py, ax, ay = num(x["proj"]), num(y["proj"]), G.adp(x), G.adp(y)
                if None in (px, py) or px == py or ax == ay or (px > py) == (ax < ay):
                    continue
                dis += 1
                pf = x if px > py else y
                af = y if pf is x else x
                night_ += (pf["slot"] or 0) > (af["slot"] or 0)
                ux, uy = num(x["your_rank"]), num(y["your_rank"])
                if ux is not None and uy is not None:
                    you += (pf is x) == (ux < uy)
        if dis:
            src = "ETR" if w == "pm" else "our projection"
            out.append("%s: ADP and %s split %d pair%s; the night sided with %s on %d, and you sided with %s on %d." % (
                W[w].capitalize(), src, dis, "" if dis == 1 else "s", src, night_, src, you))
    return " ".join(out) or "ADP and the projection agreed on every pair here last night."


def moves(H, night, t):
    """Each move against the button in this tier (Q moves left out), graded on the pair it changed; one season line."""
    th = {(r["date"], r["window"], r["name"]): r for r in H}
    tk = [r for r in csv.DictReader(open(os.path.join(REP, "takes_history.csv"))) if int(r["tier"]) == t]
    noq = [r for r in tk if not is_q(th.get((r["date"], r["window"], r["you_first"]))) and not is_q(th.get((r["date"], r["window"], r["button_first"])))]
    md = []
    for r in [r for r in noq if r["date"] == night]:
        g = float(r["gain"])
        md.append("- %s: you went against the button, **%s** ahead of **%s**; %s by %.0f point%s." % (
            W[r["window"]].capitalize(), short(r["you_first"]), short(r["button_first"]),
            "it helped" if g > 0 else "it hurt" if g < 0 else "even", abs(g), "" if abs(g) == 1 else "s"))
    by = collections.defaultdict(list)
    for r in noq:
        by[r["date"]].append(float(r["gain"]))
    allg = [g for v in by.values() for g in v]
    if len(by) < 5 or len(allg) < 15:
        season = "too early (%d move%s on %d night%s)" % (len(allg), "" if len(allg) == 1 else "s", len(by), "" if len(by) == 1 else "s")
    else:
        ds, rnd, up = list(by), random.Random(3), 0
        for _ in range(1000):
            v = [g for d in (rnd.choice(ds) for _ in ds) for g in by[d]]
            up += sum(v) > 0
        share = up / 1000
        season = ("keep doing what you're doing" if share >= 0.8 else "press the button" if share <= 0.2 else "too early") + \
            " (%d moves on %d nights, %d%% right, %+.1f points a move; ahead in %d%% of night-resamples)" % (
                len(allg), len(by), round(100 * sum(g > 0 for g in allg) / len(allg)), sum(allg) / len(allg), round(100 * share))
    return (md or ["No moves against the button here last night."]) + ["", "Season, your moves in T%d: %s." % (t, season), ""]


def turn_lines(mt, night):
    cd = (mt or {}).get("card_decisions") or []
    if not cd or (mt or {}).get("night") != night:
        return ["No turn data for last night.", ""]
    md, groups = [], collections.defaultdict(list)
    for c in cd:
        if "turn" not in c["decision"]:
            continue
        turn = c["decision"].split(":")[0]
        groups[turn].append(c)
    for turn, cs in groups.items():
        tot = sum(c["season"]["field"]["teams"] for c in cs)
        avg1 = sum(c["season"]["vs_field_top1"] * c["season"]["field"]["teams"] for c in cs) / tot if tot else None
        parts = []
        for c in cs:
            what = c["decision"].split(":", 1)[1].strip()
            ln, s = c["last_night"], c["season"]
            parts.append("%s: you %s (season %s), field %s; on the season %.2fx the field's top-1%% rate" % (
                what, pct(ln["mine"]["share"]), pct(s["mine"]["share"]), pct(ln["field"]["share"]), s["vs_field_top1"]))
        md.append("- **%s** (the turn's own average: %.2fx): %s." % (turn, avg1 or 0, "; ".join(parts)))
    return md + [""]


def mult(m, k="top10"):
    """"1.12x (0.9-1.4; 812 teams)" from a contest-side field_multiple: k's multiple of the whole field's rate."""
    if not m or not m.get(k) or m[k][0] is None:
        return "-"
    r = m.get("range80_top10") if k == "top10" else None
    return "%.2fx (%s%d teams)" % (m[k][0], "%.2f-%.2f; " % tuple(r) if r else "", m["teams"])


def t5_contest(H, mt):
    """Your T5 picks against the line, and how teams holding one did, from the contest side's money_tiers.json
    "t5_drafted" (ADP tier 5; top-10% multiples of the whole field in the same contest and price quintile)."""
    t5 = (mt or {}).get("t5_drafted")
    if not t5:
        return ["The contest side's T5 read (money_tiers.json t5_drafted) isn't on file yet.", ""]
    md = []
    for w in ("am", "pm"):
        x = t5.get(w)
        if not x:
            continue
        su, ho = x["share_under"], x["holders"]
        sh = lambda v: "%s of %d" % (pct(v["share"]), v["picks"]) if v.get("picks") else "-"
        md.append("- **%s** (line %d%%): your ADP-T5 picks under the line %s last night (field %s), %s on the season (field %s). "
                  "Teams holding one under it, season: top 10%% at %s the field's rate, yours %s; at or over it: %s, yours %s." % (
                      W[w].capitalize(), x["line"], sh(su["last_night"]["mine"]), pct(su["last_night"]["field"]["share"]),
                      sh(su["season"]["mine"]), pct(su["season"]["field"]["share"]),
                      mult(ho["season"]["under"]["field"]), mult(ho["season"]["under"]["mine"]),
                      mult(ho["season"]["over"]["field"]), mult(ho["season"]["over"]["mine"])))
    return md + [""]


def contest(t, mt):
    blk = ((mt or {}).get("tiers") or {}).get(str(t)) or {}
    ex = [(w, e) for w, e in (blk.get("exposure") or {}).items() if e and e.get("my_teams")]
    if not ex:
        return ["No contest data for this tier last night.", ""]
    w, e = max(ex, key=lambda x: x[1]["my_teams"])
    ps = [x for x in e.get("players", []) if x.get("mine") is not None and x.get("lift10") is not None]
    s = []
    paid = sorted([x for x in ps if x["lift10"] >= 1.3], key=lambda x: -x["lift10"])[:2]
    if paid:
        s.append("Outsized holders: %s (top 10%% at %s the field's rate)." % (" and ".join(x["name"] for x in paid),
                                                                            " and ".join("%.1fx" % x["lift10"] for x in paid)))
    gap = [dict(x, top=x["field"] * x["lift10"]) for x in ps]
    light = max(gap, key=lambda x: x["top"] - x["mine"], default=None)
    if light and light["top"] - light["mine"] >= 0.05:
        s.append("In your %s window the top-10%% teams held %s on %s against your %s." % (W[w], light["name"], pct(light["top"]), pct(light["mine"])))
    kd = (e.get("kinds") or {}).get("VALUE")
    if t in (3, 4) and kd and kd.get("mine") is not None:
        s.append("Your VALUE share: %s of your %s teams held one, the field %s." % (pct(kd["mine"]), W[w], pct(kd["field"])))
    return [" ".join(s) or "Nothing stood out in this tier's contest results last night.", ""]


def recap_order(H, night, t, recap_lines):
    """The recap in the button's default order (its PM build, else AM), before your moves."""
    built = {}
    for w in ("am", "pm"):
        for r in H:
            if r["date"] == night and r["window"] == w and r["built"]:
                built[r["name"]] = int(r["built"])
    def key(line):
        n = line.split("**")[1] if "**" in line else ""
        return min((v for k, v in built.items() if short(k) == n or k == n), default=999)
    items = [l for l in recap_lines if l.startswith("- ")]
    return sorted(items, key=key) + [l for l in recap_lines if not l.startswith("- ")]


# ---------------------------------------------------------------- Questionable
def q_section(H, night, today_pool, tracker, mt=None):
    pool, ben = today_pool
    sw = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        if r["date"] == night:
            sw[r["out_id"]].append(r)
    md = ["## Questionable", ""]
    qs = {}
    for r in H:
        if r["date"] == night and is_q(r):
            qs.setdefault(r["player_id"], {})[r["window"]] = r
    if qs:
        md += ["**Last night's Questionable players at the lock.**", ""]
        for pid, by in qs.items():
            r = by.get("pm") or by.get("am")
            where = "; ".join("%s %s, %s on the button" % (W[w], "T" + x["tier"] if x["tier"] != "6" else "below the cut", "#" + x["built"] if x["built"] else "-")
                              for w, x in sorted(by.items()))
            if r["scratched"] == "1":
                xs = sorted(sw.get(pid, []), key=lambda x: -int(x["teams"]))[:2]
                res = "sat; swaps went to %s" % (" and ".join("%s (%.0f)" % (short(x["swap"]), float(x["swap_fp"])) for x in xs) or "no credited swaps")
            else:
                res = "played: %.0f points against a projection of %.0f" % (num(r["actual"]) or 0, num(r["proj"]) or 0)
            md.append("- **%s** (%s): %s; %s." % (r["name"], r["tag"], where, res))
        md.append("")
    th = {(r["date"], r["window"], r["name"]): r for r in H}
    qm = [t for t in takes_on(night) if is_q(th.get((night, t["window"], t["you_first"]))) or is_q(th.get((night, t["window"], t["button_first"])))]
    md += ["**Your Q moves.** " + ("; ".join("%s: %s ahead of %s, %s by %.0f" % (
        W[t["window"]].capitalize(), short(t["you_first"]), short(t["button_first"]), "helped" if float(t["gain"]) > 0 else "hurt", abs(float(t["gain"])))
        for t in qm) + "." if qm else "None last night."), ""]
    try:
        import nba_swap_grade
        md += [nba_swap_grade.season_line(), ""]
    except Exception as e:
        md += ["Swap button: not graded (%s)." % e, ""]
    if tracker:
        md += [tracker[0], ""]
    qp = ((mt or {}).get("q_picks") or {}).get("groups") or {}
    if qp:
        md += ["**Q picks on contest results, season** (top 10%% against the field's rate): %s." % "; ".join(
            "%s %s" % (k, mult(qp[k])) for k in ("no Q pick", "any Q pick", "played", "sat", "T1", "T2", "T3", "T4", "T5") if k in qp), ""]
    today = [r for r in (pool or []) if (r.get("tag") or "")[:1].lower() == "q" and r.get("drafted")]
    bmap = collections.defaultdict(list)
    for r, tg in (ben or []):
        bmap[tg["name"]].append(r["name"])
    if today:
        md += ["**Today's Questionable players.** " + "; ".join(
            "%s (T%d on the ladders, %s to play)%s" % (r["name"], r["c"], pct(r["play"]),
                                                       ": if he sits, " + ", ".join(bmap[r["name"]][:3]) if bmap.get(r["name"]) else "")
            for r in today).replace("..", ".") + ".", ""]
    elif pool is None:
        md += ["Today's slate isn't on the mirror yet.", ""]
    return md


# ---------------------------------------------------------------- back page
def gallagher_log():
    """Every Bad-matchup arrow from Gallagher's column published before your lock (PM lock, else the slate's), with the
    player's result against ETR's final: analysis/nba/report/gallagher_arrows.csv. Returns its rows."""
    meta = json.load(open(os.path.join(DAILY, "meta.json")))
    out = []
    for f in sorted(glob.glob(os.path.join(TAKES, "*_etr_matchups.csv"))):
        d = os.path.basename(f)[:10]
        m = next((v for k, v in meta.items() if k.startswith(d) and k.endswith("_main.csv")), None)
        if not m:
            continue
        lock = (m.get("pm") or {}).get("at") or m.get("lock")
        rec = {}
        for p in glob.glob(os.path.join(DAILY, "%s_*_box.csv" % d)):
            rec = {r["name"]: r for r in csv.DictReader(open(p))}
        for t in csv.DictReader(open(f)):
            if t["stance"] != "Bad":
                continue
            at = t.get("at") or ""
            before = bool(at and lock and dt.datetime.fromisoformat(at.replace("Z", "+00:00")) <= dt.datetime.fromisoformat(lock.replace("Z", "+00:00")))
            b = rec.get(t["player"]) or {}
            e, a = num(b.get("etr_median")), num(b.get("actual"))
            out.append({"date": d, "player": t["player"], "team": t["team"], "published": at, "lock": lock, "counted": int(before),
                        "etr_final": "" if e is None else e, "actual": "" if a is None else a,
                        "vs_etr": "" if e is None or a is None else round(a - e, 1), "played": int(bool(b) and (num(b.get("min")) or 0) > 0)})
    path = os.path.join(REP, "gallagher_arrows.csv")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "player", "team", "published", "lock", "counted", "etr_final", "actual", "vs_etr", "played"])
        w.writeheader()
        w.writerows(out)
    return out


def back(night, health_problems):
    md = ["## Back page", ""]
    try:
        import nba_etr_match as EM
        ss = EM.slates(set(), target="etr_last")
        allp = [p for _, _, ps in ss for p in ps]
        lastp = [p for d, _, ps in ss if d == night for p in ps]
        ms, ml = EM.measures(allp), EM.measures(lastp) if lastp else None
        gap = lambda ps: sum(abs(p["etr"] - p["ours"]) for p in ps) / len(ps)
        md.append("**Our morning projection against ETR's final.** %sSeason: %.2f points apart on average (against ADP), "
                  "correlation %.2f, %d%% 3+ apart (%d slates)." % (
                      ("Last night: %.2f apart, correlation %.2f. " % (gap(lastp), ml["corr"])) if ml else "Last night isn't graded (no Lock AM before ETR's first file). ",
                      gap(allp), ms["corr"], round(100 * ms["big"] / ms["n"]), len(ss)))
    except Exception as e:
        md.append("Our morning projection against ETR: not read (%s)." % e)
    res = collections.defaultdict(list)
    for p in glob.glob(os.path.join(DAILY, "*_box.csv")):
        for r in csv.DictReader(open(p)):
            e, a = num(r["etr_median"]), num(r["actual"])
            if e is not None and a is not None and (num(r["min"]) or 0) > 0:
                res[r["date"]].append(a - e)
    if res:
        allr = [x for v in res.values() for x in v]
        ln = res.get(night, [])
        md.append("**ETR's final against the box score.** %sSeason: %+.2f on average, off by %.1f (%d player-nights)." % (
            ("Last night: %+.2f on average, off by %.1f a player. " % (sum(ln) / len(ln), sum(abs(x) for x in ln) / len(ln))) if ln else "",
            sum(allr) / len(allr), sum(abs(x) for x in allr) / len(allr), len(allr)))
    try:
        rows = [r for r in gallagher_log() if r["counted"] and r["played"] and r["vs_etr"] != ""]
        ln = [r for r in rows if r["date"] == night]
        if rows:
            md.append("**Gallagher's Bad-matchup arrows** (published before your lock). %sSeason: %d arrows, %+.1f against ETR's final on "
                      "average, %d%% under it." % (
                          ("Last night: %s. " % "; ".join("%s %+.1f" % (short(r["player"]), r["vs_etr"]) for r in ln)) if ln else "",
                          len(rows), sum(r["vs_etr"] for r in rows) / len(rows), round(100 * sum(r["vs_etr"] < 0 for r in rows) / len(rows))))
    except Exception as e:
        md.append("Gallagher's arrows: not read (%s)." % e)
    md.append("**Data.** " + ("; ".join(health_problems) + "." if health_problems else "Everything for last night came in, and today's inputs were ready on time."))
    out = []
    for l in md:
        out += [l, ""]
    return out


RULEBOOK = """# The rulebook

The standing rules behind the morning report (linked once at its top). Each rule's first night on the board is in
rule_dates.json; the Friday report reads "since the rule went in" and "season" from there.

## The button (from 2026-11-13; the morning window from 11-14)

- A player's tier is his ADP tier, moved at most one tier toward his projection's; VALUE is a tier better on the
  projection, PRICEY a tier worse. The projection is ours in the morning, ETR's in the afternoon.
- T1: morning ADP, the higher Boom first within 2 picks; afternoon ETR. The elite cut: T1's top at the biggest projection
  gap among its top 3-4 (1 to 3 players).
- T2: morning straight ADP; afternoon ADP with ETR breaking ties within 2 picks up to the elite break (pick 13 minus the
  elites with 6 drafters, 9 minus them with 4), ETR from there.
- T3 and T4: VALUE, the rest, PRICEY; morning by ADP, afternoon by ETR (ADP, then Boom, on exact ties). T3 PRICEY stays
  ahead of T4 VALUE.
- T4 ends at the start of round 6 (after pick 30; 20 with 4 drafters), earlier at an ADP gap of 2+ picks just before it;
  round-6 players are never in T4; T4 PRICEY players drop into T5; T4 short of 4 borrows the bottom of T3.
- T5: round 6 and the dropped T4 PRICEY players drafted in under 60% of pods and projected for 20+ minutes (box-score
  minutes in the morning, ETR-implied in the afternoon), by projection, 50-60% at the bottom, to your cut. Everyone else
  below the cut by projection. VALUE shows, doesn't sort; Boom isn't used.
- Questionable at the lock: keeps his tier (both windows); in T1 he drops to the top of T2; one whose ADP fell 6+ picks
  since the tag (the poller's pre-tag ADP) goes below the cut; a T1-T4 teammate gets the tiebreak in his group; T5's rule
  holds for T5's Q players.
- Swaps, after your last draft fills: T1-T4 exactly as at your PM lock; everyone else (T5 and below the line) by the
  latest projection, the top 16 as T5 and the line under them (~44-46 ranked); the green Swap lock saves it as its own
  lock (the PM lock stays the draft list).

## How things are graded

- T1-T4 on points: every pair in the tier the two orders put differently, the night as the unit (nights won and lost,
  the share of night-resamples each order comes out ahead, points per pair).
- T5, Questionable tags and swaps on contest results (top-10% and top-1% rates against the field's).
- A proposal needs 90%+ of night-resamples on its main grade and the other grade not against it; 80-90% is "watching".
  Nothing moves without your yes. Proposals come in the Friday report.

## Words the report uses

- VALUE / PRICEY: a tier better / worse on the projection than on ADP.
- A close call: two players in the same tier within 4 picks of ADP.
- Sound / shaky (bets and fades): the close moved toward / away from your side after your lock.
- Gray zone: drafted in 50-70% of pods, where the drafted% curve misses by about 8 points.
"""


def write_rulebook():
    open(os.path.join(REP, "rulebook.md"), "w").write(RULEBOOK)
