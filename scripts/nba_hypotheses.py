"""NBA hypotheses: what we think we learned, tested before it touches the projection model and
re-tested after it does, so nothing stale lingers.

The registry is analysis/nba/report/hypotheses.json; each hypothesis moves through:

  watching  a pattern in the misses log, with no rule yet
  testing   a rule (RULES below) that moves a player's projection using only what was known
            before tip. The nights before it was `opened` are its backtest (the same nights that
            suggested it, so only a first look); the nights from `opened` on are its forward
            test, which decides it
  adopted   built into the projection model; still re-tested on the last RECHECK_DAYS nights
  rejected  failed its forward test
  retired   was adopted, then stopped beating the model on its rolling re-test

A rule is scored on every graded rotation player it would have moved, hits and misses alike
(the misses log alone would flatter it): how many points closer to his actual score it lands
than the base projection, his usual minutes times his usual rate on ETR's scale. The 80% range
comes from resampling nights. The script proposes; the status changes are the user's call,
recorded in the JSON with the date.

  python3 scripts/nba_hypotheses.py
"""
import glob, json, os, random, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import nba_ledger as L   # noqa: E402  box files, usual rate, ETR scale, name keys
import nba_report as rep   # noqa: E402

REGISTRY = os.path.join(os.path.dirname(__file__), "..", "analysis", "nba", "report", "hypotheses.json")
FORWARD_DAYS = 14      # nights of forward test before a verdict
MIN_N = 40             # and player-nights the rule moved
RECHECK_DAYS = 14      # an adopted rule's rolling re-test


def base(row, minutes=None):
    """The base projection: minutes (his usual unless given) times his usual rate, on ETR's scale."""
    m = row["usual_min"] if minutes is None else minutes
    return max(0.0, L.BOX_TO_ETR[0] * m * L.usual_rate(row) + L.BOX_TO_ETR[1])


# ---------------------------------------------------------------- rules
# rule(row, past) -> (projection, tag) when the rule would move him, else None.
# past: his earlier graded nights, oldest first. Only what was known before tip.

def minutes_trend(row, past):
    """H1: when his last 3 games averaged 4+ minutes off his usual, project him at his last-3 minutes."""
    if len(past) < 3:
        return None
    last3 = sum(p["min"] for p in past[-3:]) / 3
    if abs(last3 - row["usual_min"]) < 4:
        return None
    return base(row, last3), "up" if last3 > row["usual_min"] else "down"


RULES = {"minutes_trend": minutes_trend}


# ---------------------------------------------------------------- scoring
def nights():
    """[(date, [graded rows with a usual line])] for every night with a box file, oldest first,
    and each player's history."""
    out = []
    for path in sorted(glob.glob(os.path.join(rep.DAILY, "*_box.csv"))):
        date = os.path.basename(path)[:10]
        rows = [r for r in L.load_box(date) if r["fp_pm"] and r["usual_min"] is not None]
        for r in rows:
            r["key"], r["date"] = L.key_of(r["name"]), date
        out.append((date, rows))
    return out


def gains(rule, history, since=None, until=None):
    """{date: [(points closer than base, tag)]} for the nights in [since, until)."""
    past = defaultdict(list)
    out = defaultdict(list)
    for date, rows in history:
        for r in rows:
            if rep.graded(r) and (since is None or date >= since) and (until is None or date < until):
                got = rule(r, past[r["key"]])
                if got:
                    p1, tag = got
                    out[date].append((abs(base(r) - r["actual"]) - abs(p1 - r["actual"]), tag))
        for r in rows:
            if rep.graded(r):
                past[r["key"]].append(r)
    return out


def summary(by_night):
    flat = [g for gs in by_night.values() for g, _ in gs]
    if not flat:
        return None
    nights_ = [gs for gs in by_night.values() if gs]
    rng = None
    if len(nights_) >= 3:
        rnd = random.Random(7)
        ms = sorted(sum(g for gs in s for g, _ in gs) / sum(len(gs) for gs in s)
                    for s in ([rnd.choice(nights_) for _ in nights_] for _ in range(300)))
        rng = (ms[30], ms[269])
    tags = defaultdict(list)
    for gs in by_night.values():
        for g, t in gs:
            tags[t].append(g)
    return {"n": len(flat), "nights": len(nights_), "mean": sum(flat) / len(flat), "closer": sum(1 for g in flat if g > 0) / len(flat),
            "range": rng, "tags": {t: (len(v), sum(v) / len(v)) for t, v in tags.items()}}


def fmt(s):
    if not s:
        return "the rule hasn't fired on these nights"
    out = "%d players, %d nights: %+.2f pts closer (%d%% closer)" % (s["n"], s["nights"], s["mean"], round(100 * s["closer"]))
    if s["range"]:
        out += ", range %+.2f to %+.2f" % s["range"]
    if len(s["tags"]) > 1:
        out += "; " + ", ".join("%s %d at %+.2f" % (t, n, m) for t, (n, m) in sorted(s["tags"].items()))
    return out


def proposal(h, fwd, recheck):
    st = h["status"]
    if st == "watching":
        return "needs a rule before it can be tested"
    if st == "testing":
        days = fwd["nights"] if fwd else 0
        if days < FORWARD_DAYS or (fwd or {}).get("n", 0) < MIN_N:
            return "forward test: %d of %d nights, %d of %d players" % (days, FORWARD_DAYS, (fwd or {}).get("n", 0), MIN_N)
        lo, hi = fwd["range"] or (fwd["mean"], fwd["mean"])
        if lo > 0:
            return "**adopt?** beat the base model on its forward test"
        if hi < 0 or fwd["mean"] <= 0:
            return "**reject?** didn't beat the base model forward"
        return "inconclusive: extend the forward test, or reject"
    if st == "adopted":
        if recheck and recheck["n"] >= MIN_N and recheck["mean"] <= 0:
            return "**retire?** no longer beating the base model over the last %d nights" % RECHECK_DAYS
        return "holding" if recheck else "no recent nights to re-test"
    return st


def main():
    reg = json.load(open(REGISTRY))
    slates = rep.load()
    L.fit_scale(slates)
    history = nights()
    dates = [d for d, _ in history]
    print("# Hypotheses\n")
    print("Scored on every graded rotation player a rule would move: points closer to his actual score "
          "than the base projection (usual minutes x usual rate), with an 80% range over nights.\n")
    for hid, h in reg.items():
        rule = RULES.get(h.get("rule", ""))
        print("## %s: %s" % (hid, h["title"]))
        print("%s · %s since %s%s" % (h["label"], h["status"], h.get("since") or h["opened"],
                                      " · " + h["notes"] if h.get("notes") else ""))
        if not rule:
            print("- " + proposal(h, None, None) + "\n")
            continue
        back = summary(gains(rule, history, until=h["opened"]))
        fwd = summary(gains(rule, history, since=h["opened"]))
        recent = dates[-RECHECK_DAYS:] if dates else []
        recheck = summary(gains(rule, history, since=recent[0])) if h["status"] == "adopted" and recent else None
        print("- backtest (nights before %s): %s" % (h["opened"], fmt(back)))
        print("- forward (from %s): %s" % (h["opened"], fmt(fwd)))
        if h["status"] == "adopted":
            print("- last %d nights: %s" % (RECHECK_DAYS, fmt(recheck)))
        print("- " + proposal(h, fwd, recheck) + "\n")


if __name__ == "__main__":
    main()
