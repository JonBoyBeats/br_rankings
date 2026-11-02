"""NBA Field: the morning report's section on the contests themselves (full fields, from scripts/nba_contests.py),
joined to the nightly record's locked-board columns (analysis/nba/daily/<date>_<day>_main.csv).

For the night's flagship contest (the most entries), and running over every night on file:

  1 Cut lines     the score it took to win and to reach the top 1/5/10/20%, the median, top 1% over the median
  2 Ownership     where drafted% (pods he was drafted in / pods) leaves 100%: the 60-99.5% and 10-60% players,
                  and any priced player under 10% (news, not a fade), with his tag at Lock AM and your tiers
  3 Pairs, cores  the field's 5 most-owned pairs and 3 cores, with estimated rounds and lift. Flags: a turn pair
                  (rounds 1/2 or 2/3), same-position teammates, opposing stars in a 10+ spread game (the two
                  relationships analysis/nba/report/residual_correlations.md finds move together)
  4 Tiers         how many of each top-1% team's picks came from each of your tiers, against the field's average
                  team; each team read with the tiers of the lock nearest its draft time
  5 Questionable  the field's drafted% for players Questionable at Lock AM, your teams carrying one, who sat
  6 Takes         each take on your locked board (a tier-rule break between two untagged players): the one you
                  put first and the other, their drafted% and ADP. With the field: the field took yours earlier
  7 Uniqueness    the share of the field holding 4+ of your 6, exact dupes, repeats of your own, your most-used
                  pairs and cores beside the field's share of them
  8 Your results  per contest: teams, median finish, tail ratios (share of your teams in the top X% over X), AM
                  and PM teams split by your own lock times; running, with ranges from resampling nights
  9 Value         fantasy points over the ADP band average, and breakers, for the top 1% against the field: a
                  description of what won, not a rule

Pick order isn't public, so rounds are estimated (see nba_contests.py); draft times are the nearest hourly ADP
snapshot. 4-drafter small slates are kept apart in every running table. The first weeks are noise.

  python3 scripts/nba_field.py [--date YYYY-MM-DD] [--mirror ../br-adp-mirror]

--mirror gives every field team its draft time, for part 4; without it every team is read with your PM tiers.
"""
import argparse, csv, datetime as dt, glob, json, math, os, random, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import nba_contests as C   # noqa: E402
import nba_daily as D      # noqa: E402
import nba_report as R     # noqa: E402

GROUP = {"PG": "G", "SG": "G", "G": "G", "SF": "F", "PF": "F", "F": "F", "C": "C"}
TURNS = ("1/2", "2/3")


def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def nights():
    return sorted({c["date"] for c in C.load_contests() if os.path.exists(os.path.join(C.OUT, "%s_measures.json" % c["date"]))})


def measures(date):
    return json.load(open(os.path.join(C.OUT, "%s_measures.json" % date)))


def flagship(m):
    return max(m["contests"], key=lambda c: c["entries"])


def record(date):
    """The night's record rows by player id, and by name; {} if the record isn't on file."""
    s = next((x for x in R.load() if x["date"] == date), None)
    rows = s["rows"] if s else []
    return s, {r["player_id"]: r for r in rows}, {r["name"]: r for r in rows}


def box(date):
    """{name: box row} for the night: team, opponent, spread, and star (one of his team's top two by ETR's median)."""
    path = next(iter(glob.glob(os.path.join(R.DAILY, "%s_*_box.csv" % date))), None)
    if not path:
        return {}
    rows = list(csv.DictReader(open(path)))
    out = {}
    for team in {r["team"] for r in rows}:
        mine = sorted((r for r in rows if r["team"] == team), key=lambda r: -(R.num(r["etr_median"]) or 0))
        for i, r in enumerate(mine):
            out[r["name"]] = dict(r, star=i < 2 and R.num(r["etr_median"]) is not None, spread=R.num(r["spread"]))
    return out


def locks(date):
    """(Lock AM time, Lock PM time) from the record's meta, or Nones."""
    meta = json.load(open(os.path.join(R.DAILY, "meta.json"))) if os.path.exists(os.path.join(R.DAILY, "meta.json")) else {}
    m = next((v for k, v in meta.items() if k.startswith(date) and k.endswith("_main.csv")), {})
    return iso((m.get("am") or {}).get("at")), iso((m.get("pm") or {}).get("at"))


def window(at, am, pm):
    """"am" or "pm": the lock nearest the draft time (PM when there's no AM lock or no time)."""
    if at is None or am is None:
        return "pm"
    if pm is None:
        return "am"
    return "am" if abs((at - am).total_seconds()) < abs((at - pm).total_seconds()) else "pm"


def pct(v, spec="%.0f%%"):
    return "-" if v is None else spec % v


def drafted(teams):
    d, _ = C.drafted(teams, None)
    return {p: 100 * v for p, v in d.items()}


# ---------------------------------------------------------------- the parts
def cut_lines(dates, date):
    out = ["### 1. Cut lines (flagship contest each night)", "",
           "| Night | Contest | Teams | Pods | Win | Top 1% | Top 5% | Top 10% | Top 20% | Median | Top 1% over median |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in dates:
        c = flagship(measures(d))
        cl = c["cut_lines"]
        out.append("| %s%s | %s | %d | %d of %d | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | +%.1f |" % (
            "**%s**" % d if d == date else d, "" if c["pod_size"] == 6 else " (4-drafter)", c["contest"], c["entries"], c["pods"],
            c["pod_size"], cl["win"], cl["top1"], cl["top5"], cl["top10"], cl["top20"], cl["median"], cl["top1_over_median"]))
    return out + [""]


def ownership(own, by_id, pile, pod):
    tier = lambda r: "%s/%s" % (int(r["am_tier"]) if r.get("am_tier") else "-", int(r["pm_tier"]) if r.get("pm_tier") else "-")
    rows = [(p, v, by_id[p]) for p, v in own.items() if p in by_id and by_id[p]["adp_close"] is not None]
    for p, r in by_id.items():                       # priced but drafted in no pod at all
        if p not in own and r["adp_close"] is not None and r["adp_close"] < pile:
            rows.append((p, 0.0, r))
    first = min((r["adp_close"] for _, v, r in rows if v < 99.5 and r["adp_close"] < pile), default=None)
    out = ["### 2. Field ownership (flagship)", "",
           "Drafted%% leaves 100%% at ADP %s. Tag: at Lock AM / at lock. Tiers: yours at Lock AM / Lock PM." % pct(first, "%.1f"), "",
           "| Player | ADP at lock | Drafted | Band | Tag | Tiers | Actual |", "|---|---|---|---|---|---|---|"]
    for p, v, r in sorted(rows, key=lambda x: x[2]["adp_close"]):
        # under 10%: news when he was tagged at lock or priced before the last round, else just the end of the board
        news = v < 10 and r["adp_close"] < pile and (r["injury"] or r["adp_close"] <= 5 * pod)
        b = "60-99.5" if 60 <= v < 99.5 else "10-60" if 10 <= v < 60 else "under 10 (news?)" if news else None
        if b:
            out.append("| %s | %.1f | %.1f%% | %s | %s / %s | %s | %s |" % (r["name"], r["adp_close"], v, b, r.get("injury_am") or "-",
                                                                     r["injury"] or "-", tier(r), R.fmt(r["actual"], "%.1f")))
    return out + [""]


def pairs_cores(c, by_name, bx):
    def flags(names):
        rs = [bx.get(n) or by_name.get(n) or {} for n in names]
        fl = []
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                if not a or not b:
                    continue
                if a.get("team") == b.get("team") and GROUP.get(a.get("pos")) and GROUP.get(a.get("pos")) == GROUP.get(b.get("pos")):
                    sp = abs(a.get("spread") or 0)
                    fl.append("same-position teammates%s" % (" (spread %g: worse at 5+)" % sp if sp >= 5 else ""))
                if a.get("opp") == b.get("team") and a.get("star") and b.get("star") and abs(a.get("spread") or 0) >= 10:
                    fl.append("opposing stars, spread %g" % abs(a["spread"]))
        return fl
    out = ["### 3. Most-owned pairs and cores (flagship)", "",
           "Lift: against a pod dealt at random, so the snake's turns are part of it (turn pairs run about 2-3x). Flags from "
           "analysis/nba/report/residual_correlations.md: same-position teammates slightly cannibalize (more at spread 5+); "
           "opposing stars in a 10+ spread game tend to be quiet together.", "",
           "| Pair | Rounds (est.) | Share of teams | Lift | Flags |", "|---|---|---|---|---|"]
    for p in c["pairs"][:5]:
        fl = (["turn pair"] if p["rounds"] in TURNS else []) + flags(p["pair"].split(" + "))
        out.append("| %s | %s | %.1f%% | %.1fx | %s |" % (p["pair"], p["rounds"], p["share"], p["lift"], ", ".join(fl) or "-"))
    out += ["", "| Core (a team's 3 earliest picks) | Share of teams | Flags |", "|---|---|---|"]
    for k in c["cores"][:3]:
        out.append("| %s | %.1f%% | %s |" % (k["core"], k["share"], ", ".join(flags(k["core"].split(" + "))) or "-"))
    return out + [""]


def tiers_vs_winners(teams, by_id, times, am, pm):
    have = any(r.get("am_tier") or r.get("pm_tier") for r in by_id.values())
    out = ["### 4. Your tiers in the top 1% (flagship)", ""]
    if not have:
        return out + ["No tier lines on this night's locks (they start with the 2026-11-02 slate).", ""]
    def count(t):
        w = window(times.get(id(t)), am, pm)
        c = Counter()
        for p in t["picks"]:
            v = (by_id.get(p) or {}).get(w + "_tier")
            c["T%d" % v if v else "past your line"] += 1
        return c
    n = len(teams)
    top = [t for t in teams if t["place"] <= math.ceil(n / 100)]
    field, best = Counter(), Counter()
    for t in teams:
        field.update(count(t))
    for t in top:
        best.update(count(t))
    keys = ["T%d" % i for i in range(1, 6)] + ["past your line"]
    out += ["Picks per team from each of your tiers (each team read with the tiers of the lock nearest its draft time%s)." % (
        "" if times else "; no --mirror, so every team with your PM tiers"), "",
        "| | " + " | ".join(keys) + " |", "|---" * (len(keys) + 1) + "|",
        "| Top 1%% (%d teams) | " % len(top) + " | ".join("%.2f" % (best[k] / len(top)) for k in keys) + " |",
        "| Field (%d teams) | " % n + " | ".join("%.2f" % (field[k] / n) for k in keys) + " |"]
    return out + [""]


def questionable(own, by_id, mine):
    q = [r for r in by_id.values() if r.get("injury_am") == "Questionable"]
    out = ["### 5. Questionable at Lock AM: the field and you", ""]
    if not q:
        return out + ["Nobody was Questionable at Lock AM.", ""]
    out += ["| Player | ADP at Lock AM | Tag at lock | Played | Field drafted | Your teams with him |", "|---|---|---|---|---|---|"]
    for r in sorted(q, key=lambda r: r["adp_am"] if r["adp_am"] is not None else 99):
        k = sum(1 for t in mine if r["player_id"] in t["picks"])
        out.append("| %s | %s | %s | %s | %s | %d of %d |" % (r["name"], R.fmt(r["adp_am"], "%.1f"), r["injury"] or "-",
                                                     "yes" if (r["min"] or 0) > 0 else "**sat**", pct(own.get(r["player_id"], 0.0), "%.1f%%"), k, len(mine)))
    return out + [""]


def takes(s, own):
    out = ["### 6. Your takes against the field", ""]
    if not s:
        return out + ["No record for this night.", ""]
    rows = []
    for half in ("am", "pm"):
        bar = R.TIER_HALVES[half][0]
        for t, v in R.tier_nights(s["rows"], bar, half).items():
            for up, down, right, pu, pd in v["off"]:
                ru, rd = next(r for r in s["rows"] if r["player_id"] == pu), next(r for r in s["rows"] if r["player_id"] == pd)
                rows.append((half.upper(), t, ru, rd, right, bar["adp"]))
    if not rows:
        return out + ["No takes on this night's locked boards (or no tier lines on them yet).", ""]
    def field_side(ru, rd, a):
        """+1: the field took the one you put first earlier (ADP, or drafted% when their ADPs are level), -1 later, 0 even."""
        if abs(ru[a] - rd[a]) > 0.05:
            return 1 if ru[a] < rd[a] else -1
        du, dd = own.get(ru["player_id"], 0.0), own.get(rd["player_id"], 0.0)
        return 0 if abs(du - dd) < 1 else 1 if du > dd else -1
    groups = defaultdict(lambda: [0, 0, 0, 0])          # takes, with the field, against it, you right
    for half, t, ru, rd, right, a in rows:
        g = groups[(half, t)]
        side = field_side(ru, rd, a)
        g[0] += 1; g[1] += side > 0; g[2] += side < 0; g[3] += right
    out += ["%d takes. With the field: the field took the one you put first earlier (by ADP at that lock, or drafted%% when "
            "level)." % len(rows), "", "| Lock | Tier | Takes | With the field | Against it | You were right |", "|---|---|---|---|---|---|"]
    for (half, t), g in sorted(groups.items()):
        out.append("| %s | T%d | %d | %d | %d | %d |" % (half, t, *g))
    out += ["", "The 10 furthest from ADP:", "",
            "| Lock | Tier | You put first | Over | ADP | Drafted | Actual | Right |", "|---|---|---|---|---|---|---|---|"]
    for half, t, ru, rd, right, a in sorted(rows, key=lambda x: -(x[2][x[5]] - x[3][x[5]]))[:10]:
        out.append("| %s | T%d | %s | %s | %.1f / %.1f | %s / %s | %s / %s | %s |" % (
            half, t, ru["name"], rd["name"], ru[a], rd[a], pct(own.get(ru["player_id"], 0.0), "%.0f%%"),
            pct(own.get(rd["player_id"], 0.0), "%.0f%%"), R.fmt(ru["actual"], "%.1f"), R.fmt(rd["actual"], "%.1f"), "yes" if right else "no"))
    return out + [""]


def uniqueness(c, teams):
    u = c.get("uniqueness")
    out = ["### 7. Your uniqueness (flagship)", ""]
    if not u:
        return out + ["No teams of yours in it.", ""]
    field = [t for t in teams if t["username"] != C.ME]
    share = lambda names: 100 * sum(1 for t in field if all(x in t["names"] for x in names)) / len(field)
    out += ["Your %d teams: the share of the field holding 4+ of your 6 is %.2f%% at the median (max %.2f%%); %d have an exact "
            "duplicate in the field, %d repeat another of your own." % (u["teams"], u["share4_median"], u["share4_max"],
                                                                      u["teams_with_dupes"], u["repeats_of_mine"]), "",
            "| Your most-used | Your teams | Field share |", "|---|---|---|"]
    for k, v in u["top_pairs"][:3] + u["top_cores"][:2]:
        out.append("| %s | %d | %.1f%% |" % (k, v, share(k.split(" + "))))
    return out + [""]


def my_rows(date):
    """[(contest, pod size, entries, [(place, window)])] for my teams, each placed by my lock times."""
    am, pm = locks(date)
    out = []
    for c in measures(date)["contests"]:
        mt = c.get("my_teams") or []
        if mt:
            out.append((c["contest"], c["pod_size"], c["entries"], [(t["place"], window(iso(t["drafted_at"]), am, pm)) for t in mt]))
    return out


def tails(teams):
    """{X: tail ratio} for [(place, entries)]."""
    return {x: sum(1 for p, n in teams if p <= math.ceil(x * n / 100)) / len(teams) / (x / 100) for x in C.TOPS} if teams else {}


def results(dates, date):
    out = ["### 8. Your results", "", "Tail ratio: the share of your teams in the top X% over X (1.0 is the field's rate). "
           "AM and PM split by your own lock times. The first weeks are noise.", "",
           "| Contest | Teams | Median finish | Top 1% | Top 5% | Top 10% | Top 20% | AM teams (top 10%) | PM teams (top 10%) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for name, pod, n, mine in my_rows(date):
        ts = [(p, n) for p, _ in mine]
        tl = tails(ts)
        sub = lambda w: [(p, n) for p, x in mine if x == w]
        out.append("| %s%s | %d | top %.0f%% | %.2f | %.2f | %.2f | %.2f | %d (%s) | %d (%s) |" % (
            name, "" if pod == 6 else " (4-drafter)", len(mine), 100 * sorted(p for p, _ in mine)[len(mine) // 2] / n,
            tl[1], tl[5], tl[10], tl[20], len(sub("am")), R.fmt(tails(sub("am")).get(10), "%.2f"),
            len(sub("pm")), R.fmt(tails(sub("pm")).get(10), "%.2f")))
    out += ["", "**Running (every contest, by pod size)**", "",
            "| Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | AM top 10% | PM top 10% |", "|---|---|---|---|---|---|---|---|---|"]
    per = defaultdict(dict)       # pod size -> night -> [(place, entries, window)]
    for d in dates:
        for _, pod, n, mine in my_rows(d):
            per[pod].setdefault(d, []).extend((p, n, w) for p, w in mine)
    rnd = random.Random(7)
    for pod in sorted(per, reverse=True):
        ds = sorted(per[pod])
        def cell(x, w=None):
            f = lambda xs: tails([(p, n) for d in xs for p, n, ww in per[pod][d] if w in (None, ww)]).get(x)
            v = f(ds)
            if v is None:
                return "-"
            if len(ds) < 5:
                return "%.2f" % v
            bs = sorted(b for b in (f([rnd.choice(ds) for _ in ds]) for _ in range(500)) if b is not None)
            return "%.2f (%.2f-%.2f)" % (v, bs[len(bs) // 10], bs[len(bs) * 9 // 10])
        out.append("| %d | %d | %d | %s | %s | %s | %s | %s | %s |" % (
            pod, len(ds), sum(len(v) for v in per[pod].values()), cell(1), cell(5), cell(10), cell(20), cell(10, "am"), cell(10, "pm")))
    if all(len(v) < 5 for v in per.values()):
        out += ["", "Ranges (80%, resampling nights) appear from 5 nights."]
    return out + [""]


def value(dates, date):
    out = ["### 9. What won (flagship; a description, not a rule)", "",
           "FPOE: fantasy points over the average for his ADP round band, summed over a team's six. Breakers: picks at the 90th "
           "percentile of their round band that night.", "",
           "| Night | FPOE: top 1% / field | Breakers: top 1% / field |", "|---|---|---|"]
    for d in dates:
        c = flagship(measures(d))
        v = c["value"]
        out.append("| %s%s | %+.1f / %+.1f | %.2f / %.2f |" % ("**%s**" % d if d == date else d, "" if c["pod_size"] == 6 else " (4-drafter)",
                                                            v["top1_fpoe"], v["field_fpoe"], v["top1_breakers"], v["field_breakers"]))
    return out + [""]


def field(date, mirror=None):
    dates = [d for d in nights() if d <= date]
    if date not in dates:
        return ["## Field", "", "No contests on file for %s (the nightly Contests step pulls them after the record)." % date, ""]
    m = measures(date)
    c = flagship(m)
    contests, teams_by = C.load_night(date)
    teams = teams_by[c["contest_id"]]
    s, by_id, by_name = record(date)
    for t in teams:
        t["names"] = {(by_id.get(p) or {}).get("name", p) for p in t["picks"]}
    own = drafted(teams)
    pile = max((r["adp_close"] or 0) for r in by_id.values()) if by_id else 99
    am, pm = locks(date)
    times = {}
    if mirror:
        lock = next((x for x in D.Mirror(mirror).main_slates(iso(date + "T00:00:00Z") - dt.timedelta(days=1), iso(date + "T00:00:00Z") + dt.timedelta(days=2))
                     if x["slate_id"] == contests[0]["slate_id"]), None)
        times = C.draft_times(teams, D.Mirror(mirror).snapshots(lock)) if lock else {}
    mine = [t for ts in teams_by.values() for t in ts if t["username"] == C.ME]
    out = ["## Field: %s, %d contests (flagship %s, %d teams in %d-drafter pods)" % (date, len(contests), c["contest"], c["entries"], c["pod_size"]), ""]
    out += cut_lines(dates, date)
    out += ownership(own, by_id, pile, c["pod_size"]) if by_id else ["### 2. Field ownership", "", "No record for this night.", ""]
    out += pairs_cores(c, by_name, box(date))
    out += tiers_vs_winners(teams, by_id, times, am, pm)
    out += questionable(own, by_id, mine)
    out += takes(s, own)
    out += uniqueness(c, teams)
    out += results(dates, date)
    out += value(dates, date)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="the night (default: the newest with contests on file)")
    ap.add_argument("--mirror", help="a clone of br-adp-mirror, for each field team's draft time (part 4)")
    a = ap.parse_args()
    ds = nights()
    if not ds:
        print("No contests on file yet.")
        return
    R.MIRROR = a.mirror
    print("\n".join(field(a.date or ds[-1], a.mirror)))


if __name__ == "__main__":
    main()
