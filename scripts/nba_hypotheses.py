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
than the base projection, his usual minutes times his usual rate on ETR's scale. A rule can name
its own reference instead (the spread rules use the base plus tonight's matchup term, the way the
board's morning Proj is built, since the blowout study found the effect net of the opponent). The 80% range
comes from resampling nights. Adoption needs FORWARD_DAYS nights and MIN_N players, then a 90% range above 0
and a gain that survives taking out any single player (bar raised 2026-11-02; stricter than the 80% range it
replaced, so it can't help a rule already under test pass). The script proposes; the status changes are the user's call,
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


def base_m(row):
    """The base plus tonight's matchup term (the board's matchup row, in box-score points, on ETR's scale)."""
    return base(row) + L.BOX_TO_ETR[0] * (row.get("mtch") or 0)


# ---------------------------------------------------------------- rules
# rule(row, past) -> (projection, tag[, reference]) when the rule would move him, else None.
# The reference (default: base) is what the rule is scored against.
# past: his earlier graded nights, oldest first. Only what was known before tip (spread: the
# day-of line as of lock; see analysis/nba/report/blowout_study.md).

def minutes_trend(row, past):
    """H1: when his last 3 games averaged 4+ minutes off his usual, project him at his last-3 minutes."""
    if len(past) < 3:
        return None
    last3 = sum(p["min"] for p in past[-3:]) / 3
    if abs(last3 - row["usual_min"]) < 4:
        return None
    return base(row, last3), "up" if last3 > row["usual_min"] else "down"


def fav_star(row):
    return row.get("spread") is not None and row["spread"] <= -10 and row["usual_min"] >= 30


def blowout_trim(row, past):
    """H2, the board's NBA_BLOWOUT: a 30+ minute player whose team is favored by 10+ loses a point."""
    if not fav_star(row):
        return None
    ref = base_m(row)
    return ref - 1, "fav 13+" if row["spread"] <= -13 else "fav 10-12.5", ref


def blowout_slide(row, past):
    """H4: the same, sliding: -1 at 10-12.5, -2 at 13+."""
    if not fav_star(row):
        return None
    ref = base_m(row)
    return ref - (2 if row["spread"] <= -13 else 1), "fav 13+" if row["spread"] <= -13 else "fav 10-12.5", ref


def dog_bench(row, past):
    """H3: a bench player (under 20 usual minutes) whose team is a 10+ point underdog gains 2 points."""
    if row.get("spread") is None or row["spread"] < 10 or row["usual_min"] >= 20:
        return None
    ref = base_m(row)
    return ref + 2, "dog 13+" if row["spread"] >= 13 else "dog 10-12.5", ref


RULES = {"minutes_trend": minutes_trend, "blowout_trim": blowout_trim, "blowout_slide": blowout_slide, "dog_bench": dog_bench}


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
                    p1, tag = got[:2]
                    ref = got[2] if len(got) > 2 else base(r)
                    out[date].append((abs(ref - r["actual"]) - abs(p1 - r["actual"]), tag, r["key"]))
        for r in rows:
            if rep.graded(r):
                past[r["key"]].append(r)
    return out


def summary(by_night):
    flat = [g for gs in by_night.values() for g, _, _ in gs]
    if not flat:
        return None
    nights_ = [gs for gs in by_night.values() if gs]
    rng = rng90 = None
    if len(nights_) >= 3:
        rnd = random.Random(7)
        ms = sorted(sum(g for gs in s for g, _, _ in gs) / sum(len(gs) for gs in s)
                    for s in ([rnd.choice(nights_) for _ in nights_] for _ in range(300)))
        rng, rng90 = (ms[30], ms[269]), (ms[15], ms[284])
    tags = defaultdict(list)
    for gs in by_night.values():
        for g, t, _ in gs:
            tags[t].append(g)
    # the mean with each single player's nights taken out: a rule one player carries isn't a rule
    keys = {k for gs in by_night.values() for _, _, k in gs}
    drop = [(lambda f: sum(f) / len(f) if f else None)([g for gs in by_night.values() for g, _, k2 in gs if k2 != k]) for k in keys]
    drop = [d for d in drop if d is not None]
    return {"n": len(flat), "nights": len(nights_), "mean": sum(flat) / len(flat), "closer": sum(1 for g in flat if g > 0) / len(flat),
            "range": rng, "range90": rng90, "drop": (min(drop), max(drop)) if drop else None,
            "tags": {t: (len(v), sum(v) / len(v)) for t, v in tags.items()}}


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
        lo90 = (fwd["range90"] or (fwd["mean"], fwd["mean"]))[0]
        if lo90 > 0 and fwd["drop"] and fwd["drop"][0] > 0:
            return "**adopt?** beat the base model on its forward test"
        if lo > 0:
            return "inconclusive: the 80% range is above 0, but not the 90% range or with every single player taken out"
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
