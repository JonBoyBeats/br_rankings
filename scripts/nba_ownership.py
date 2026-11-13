"""NBA composite ownership at the lock (a build, not wired into the board yet).

How often each player gets drafted in a night's flagship contest, built up hour by hour instead of read off one
closing-ADP curve:

  ownership (drafted%, the share of pods that take him) = pod x [ sum over hours already drafted of
      (share of teams drafted that hour x chance a team drafting then took him, given his ADP at that hour)
      + (share of teams still to draft x chance at his latest ADP) ]

  chance given ADP   calibrated on past contests by pod size (4 and 6): for every team whose draft hour the contest
                     side matched (each team's nearest hourly ADP snapshot to the ADPs its picks went at), every
                     player priced in that snapshot, did the team take him (a pick carrying a draft ADP; a swapped-in
                     pick carries none). Binned by ADP, made non-increasing.
  teams by hour      the mirror's hourly entry counts for the contest (Underdog's lobby, polled with the ADP; on file
                     from 2026-11-05); before that, and for the teams still to come, a typical fill curve: the share of
                     a night's teams drafted by each hour before the lock, from past nights' matched draft times.

Backcheck: every night with contests on file, at 2pm PT (the final-ranks time; the lock if earlier), against the
actual pre-swap drafted% from the rosters (pods where a pick of his carries a draft ADP), for every player who
played (one ruled out after the lock was swapped off every roster: his pre-swap share can't be counted). Each night
is scored with the curve and fill shape fitted on the other nights. The current model (field_model.json: drafted% by
ADP rank, now read at 2pm's ADP) is scored beside it, as stored and refitted the same leave-one-night-out way.

  python3 scripts/nba_ownership.py extract [--mirror ../br-adp-mirror]   per-night inputs -> analysis/nba/contests/ownership_inputs.json.gz
  python3 scripts/nba_ownership.py backcheck                               -> analysis/nba/report/ownership_backcheck.md
"""
import argparse, bisect, collections, csv, datetime as dt, gzip, json, math, os, sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_contests as C   # noqa: E402
import nba_daily as daily   # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INPUTS = os.path.join(HERE, "analysis", "nba", "contests", "ownership_inputs.json.gz")
OUT = os.path.join(HERE, "analysis", "nba", "report", "ownership_backcheck.md")
TIERS = os.path.join(HERE, "analysis", "nba", "report", "tier_history.csv")
PT = ZoneInfo("America/Los_Angeles")
UTC = dt.timezone.utc
CHECK_AT = 14            # 2pm PT, the final-ranks time
BIN = {6: 0.5, 4: 1.0}   # ADP bin width of the chance curve
CAP = {6: 36.0, 4: 24.0}


def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def extract(mirror_path):
    mirror = daily.Mirror(mirror_path)
    out = []
    for date in sorted({c["date"] for c in C.load_contests()}):
        contests, teams = C.load_night(date)
        if not contests:
            continue
        flag = max(contests, key=lambda c: int(c["entries"]))
        pod, cutoff = int(flag["pod_size"]), iso(flag["cutoff"])
        info = C.players_on(date, flag["slate"])
        slate = next((s for s in mirror.main_slates(cutoff - dt.timedelta(days=1), cutoff + dt.timedelta(days=1))
                      if s["slate_id"] == flag["slate_id"]), None)
        if not slate:
            print("%s: slate not in the mirror" % date)
            continue
        snaps = mirror.snapshots(slate)
        ts = teams[flag["contest_id"]]
        times = C.draft_times(ts, snaps)
        # the lobby's hourly entry counts for this contest, as the last snapshot before the lock had them
        counts = None
        for _, sha in reversed(mirror.versions(mirror.latest, slate["lock"] - dt.timedelta(hours=48), slate["lock"])):
            for s in mirror.show(sha, mirror.latest).get("slates", []):
                for c in s.get("contests") or []:
                    if c.get("id") == flag["contest_id"] and c.get("counts"):
                        counts = c["counts"]
            if counts:
                break
        by_snap = collections.defaultdict(lambda: [0, collections.Counter()])
        for t in ts:
            if id(t) in times:
                k = times[id(t)].isoformat()
                by_snap[k][0] += 1
                by_snap[k][1].update(p for p, a in zip(t["picks"], t["adps"]) if a is not None)
        pods = collections.defaultdict(set)
        for t in ts:
            pods[t["draft_id"]].update(p for p, a in zip(t["picks"], t["adps"]) if a is not None)
        npods = len(pods)
        actual = collections.Counter(p for s in pods.values() for p in s)
        out.append({"date": date, "contest": flag["contest_id"], "pod": pod, "cutoff": cutoff.isoformat(),
                    "entries": len(ts), "matched": sum(v[0] for v in by_snap.values()), "counts": counts,
                    "snaps": [[t.isoformat(), {p["player_id"]: p["adp"] for p in ps if p.get("adp") is not None}] for t, ps in snaps],
                    "taken": {k: [v[0], dict(v[1])] for k, v in by_snap.items()},
                    "actual": {p: k / npods for p, k in actual.items()},
                    "played": [p for p, r in info.items() if r["played"]], "names": {p: r["name"] for p, r in info.items()}})
        print("%s pod %d: %d teams, %d matched to an hour, %d snapshots, hourly counts %s" % (
            date, pod, len(ts), out[-1]["matched"], len(snaps), "yes (%d)" % len(counts) if counts else "no"))
    with gzip.open(INPUTS, "wt") as f:
        json.dump(out, f)


# ---------------------------------------------------------------- the model
def ranked(adps):
    """{player: his rank by ADP in one snapshot} (1 = earliest)."""
    return {p: i + 1 for i, p in enumerate(sorted(adps, key=lambda q: adps[q]))}


def key_of(adps, by):
    return ranked(adps) if by == "rank" else adps


def chance_curve(nights, pod, by="adp"):
    """[(bin start, chance a team takes him)] from the nights given: pooled, then made non-increasing.
    by "adp": his ADP at that hour (0.5-pick bins, 1 on 4-drafter slates); by "rank": his ADP rank at that hour."""
    num, den = collections.Counter(), collections.Counter()
    w = BIN[pod] if by == "adp" else 1.0
    for n in nights:
        played = set(n["played"])
        snaps = dict((t, key_of(adp, by)) for t, adp in n["snaps"])
        for t, (k, got) in n["taken"].items():
            for p, a in snaps.get(t, {}).items():
                if p not in played:
                    continue                      # ruled out later: swapped off, his pre-swap picks can't be seen
                b = math.floor(min(a, CAP[pod] + 4) / w) if by == "adp" else int(a)
                den[b] += k
                num[b] += got.get(p, 0)
    bins = sorted(den)
    vals = [num[b] / den[b] for b in bins]
    for i in range(1, len(vals)):              # pool adjacent violators: never rises with ADP
        if vals[i] > vals[i - 1]:
            j, tot, cnt = i, num[bins[i]] + num[bins[i - 1]], den[bins[i]] + den[bins[i - 1]]
            vals[i] = vals[i - 1] = tot / cnt
            while j > 1 and vals[j - 1] > vals[j - 2]:
                j -= 1
                vals[j - 1] = vals[j]
    return [(b * w, v) for b, v in zip(bins, vals)]


def chance(curve, a):
    xs = [b for b, _ in curve]
    i = max(0, bisect.bisect_right(xs, a) - 1)
    return curve[i][1] if curve else 0.0


def fill_shape(nights):
    """{hours before the lock (int, 0 = the last hour): share of a night's teams drafted then}, pooled over nights."""
    tot = collections.Counter()
    for n in nights:
        cut = iso(n["cutoff"])
        k = sum(v[0] for v in n["taken"].values())
        for t, (c, _) in n["taken"].items():
            tot[max(0, int((cut - iso(t)).total_seconds() // 3600))] += c / k / len(nights)
    return dict(tot)


def adp_at(n, t):
    """The snapshot at or before t (else the first)."""
    best = n["snaps"][0]
    for s in n["snaps"]:
        if iso(s[0]) <= t:
            best = s
    return best


def model(n, curve, shape, at, live=True, by="adp"):
    """{player: modeled drafted%} at time `at`: hours already drafted (live counts if on file, else the fill shape)
    at each hour's ADP, the rest at the latest ADP."""
    cut, pod = iso(n["cutoff"]), n["pod"]
    hrs_left = (cut - at).total_seconds() / 3600
    # share of teams by hour (as hours before the lock), from the fill shape
    done_shape = {h: s for h, s in shape.items() if h >= hrs_left}
    rest = max(0.0, 1 - sum(done_shape.values()))
    hours = []                                        # (time, share of the night's teams)
    if live and n["counts"]:
        cs = sorted((iso(t), c) for t, c in n["counts"] if iso(t) <= at)
        now = cs[-1][1] if cs else 0
        made = sum(done_shape.values())
        final = now / made if made > 0.05 else n["entries"]   # the night's size, extrapolated from the count so far
        prev = 0
        for t, c in cs:
            if c > prev:
                hours.append((t - dt.timedelta(minutes=30), (c - prev) / final))
                prev = c
        rest = max(0.0, 1 - now / final)
    else:
        for h, s in done_shape.items():
            hours.append((cut - dt.timedelta(hours=h + 0.5), s))
    latest = adp_at(n, at)[1]
    out = collections.Counter()
    for t, s in hours:
        for p, a in key_of(adp_at(n, t)[1], by).items():
            out[p] += s * chance(curve, a)
    for p, a in key_of(latest, by).items():
        out[p] += rest * chance(curve, a)
    return {p: min(1.0, pod * v) for p, v in out.items()}, latest


def current(n, rank_curve, latest):
    """field_model's drafted% by ADP rank, read at the ADP of the check time."""
    order = sorted(latest, key=lambda p: latest[p])
    return {p: (rank_curve[i] / 100 if i < len(rank_curve) else 0.0) for i, p in enumerate(order)}


def rank_curve_from(nights, pod):
    """field_model's curve refitted on the nights given: the average drafted% at each closing-ADP rank (players who played)."""
    by = collections.defaultdict(list)
    for n in nights:
        last = n["snaps"][-1][1]
        played = set(n["played"])
        for i, p in enumerate(sorted(last, key=lambda q: last[q])):
            if p in played:
                by[i].append(n["actual"].get(p, 0.0))
    return [100 * sum(by[i]) / len(by[i]) if by[i] else 0.0 for i in range(max(by) + 1)] if by else []


def backcheck():
    with gzip.open(INPUTS, "rt") as f:
        N = json.load(f)
    tiers = {}
    for r in csv.DictReader(open(TIERS)):
        if r["window"] == "pm":
            tiers[(r["date"], r["player_id"])] = int(r["tier"])
    stored = json.load(open(os.path.join(HERE, "analysis", "nba", "contests", "field_model.json")))["drafted"]
    rows = []
    for n in N:
        others = [m for m in N if m["date"] != n["date"] and m["pod"] == n["pod"]]
        if len(others) < 2:
            continue
        curve, shape = chance_curve(others, n["pod"]), fill_shape(others)
        at = min(iso(n["cutoff"]), dt.datetime.fromisoformat(n["date"] + "T%02d:00:00" % CHECK_AT).replace(tzinfo=PT).astimezone(UTC))
        comp, latest = model(n, curve, shape, at)
        flat, _ = model(n, curve, shape, at, live=False)
        rcurve = chance_curve(others, n["pod"], "rank")
        comp_r, _ = model(n, rcurve, shape, at, by="rank")
        flat_r, _ = model(n, rcurve, shape, at, live=False, by="rank")
        cur_s = current(n, stored[str(n["pod"])], latest)
        cur_l = current(n, rank_curve_from(others, n["pod"]), latest)
        for p in n["played"]:
            if p not in latest:
                continue
            rows.append({"date": n["date"], "pod": n["pod"], "p": p, "name": n["names"].get(p, p[:8]), "adp": latest[p],
                         "tier": tiers.get((n["date"], p)), "act": n["actual"].get(p, 0.0), "comp": comp.get(p, 0.0),
                         "flat": flat.get(p, 0.0), "comp_r": comp_r.get(p, 0.0), "flat_r": flat_r.get(p, 0.0), "cur_s": cur_s.get(p, 0.0), "cur_l": cur_l.get(p, 0.0),
                         "live": bool(n["counts"])})
    return N, rows


def mae(rows, k):
    return 100 * sum(abs(r[k] - r["act"]) for r in rows) / len(rows) if rows else float("nan")


def bias(rows, k):
    return 100 * sum(r[k] - r["act"] for r in rows) / len(rows) if rows else float("nan")


def report(N, rows):
    L = ["# Composite ownership: backcheck", "",
         "**Read (2026-11-13):** the composite doesn't beat the current curve at 2pm. ADP is itself a running average of "
         "where the field has been drafting a player, so its rank at 2pm already carries what the hour-by-hour build adds "
         "up, and the build adds noise from earlier hours' ADPs. Keyed to ADP values it misses most late (a slate's "
         "length moves what an ADP of 34 means); keyed to rank it comes within 0.3 points overall but loses in the "
         "10-90% band, where ownership matters. The live hourly counts change nothing (by rank: 2.2 with or without "
         "them). Not wired in.", "",
         "Every night with contests on file, the flagship contest, at 2pm PT. Actual: pre-swap drafted% from the rosters "
         "(the share of pods that took him; picks carrying a draft ADP), players who played. Each night scored with the "
         "chance curve and fill shape fitted on the other nights of its pod size. Errors in percentage points of drafted% "
         "(mean absolute; bias = modeled minus actual).", "",
         "- composite: the new build as specified, the chance keyed to his ADP at each hour (live hourly counts where on file, else the fill shape)",
         "- composite by rank: the same, the chance keyed to his ADP rank at each hour",
         "- by rank, fill shape only: that with the typical fill shape on every night (no live counts)",
         "- current, as stored: field_model.json's drafted% by ADP rank (fitted on every night, these included)",
         "- current, refitted: the same curve refitted without the night", ""]
    nights = collections.Counter((r["date"], r["pod"], r["live"]) for r in rows)
    L.append("%d nights (%d six-drafter, %d four-drafter; %d with live hourly counts), %d player-nights." % (
        len(nights), sum(1 for k in nights if k[1] == 6), sum(1 for k in nights if k[1] == 4), sum(1 for k in nights if k[2]), len(rows)))
    HEAD = "| %s | n | composite | composite by rank | by rank, fill shape only | current, as stored | current, refitted |"
    SEP = "|---|---|---|---|---|---|---|"
    L += ["", HEAD % "", SEP]

    def row(lab, g):
        if not g:
            return
        L.append("| %s | %d | %s |" % (lab, len(g), " | ".join("%.1f (%+.1f)" % (mae(g, k), bias(g, k))
                                                              for k in ("comp", "comp_r", "flat_r", "cur_s", "cur_l"))))
    row("**all**", rows)
    for pod in (6, 4):
        row("%d-drafter" % pod, [r for r in rows if r["pod"] == pod])
    row("nights with live counts", [r for r in rows if r["live"]])
    row("actual 10-90% (where it matters)", [r for r in rows if 0.1 <= r["act"] < 0.9])
    L += ["", "**By tier (the button's afternoon tier)**", "", HEAD % "tier", SEP]
    for t in range(1, 6):
        row("T%d" % t, [r for r in rows if r["tier"] == t])
    row("no tier (unpriced at the PM lock)", [r for r in rows if r["tier"] is None])
    L += ["", "**By actual drafted%**", "", HEAD % "band", SEP]
    for lo, hi, lab in ((0.995, 2, "99.5%+"), (0.9, 0.995, "90-99.5%"), (0.6, 0.9, "60-90%"), (0.3, 0.6, "30-60%"), (0.1, 0.3, "10-30%"), (0.0, 0.1, "under 10%")):
        row(lab, [r for r in rows if lo <= r["act"] < hi])
    mid = collections.defaultdict(list)
    for r in rows:
        if 0.1 <= r["act"] < 0.9:
            mid[r["date"]].append(r)
    L += ["", "In the 10-90%% band, night by night, the composite by rank was closer than the refitted current curve on %d of "
          "%d nights (by ADP: %d)." % (sum(1 for g in mid.values() if mae(g, "comp_r") < mae(g, "cur_l")), len(mid),
                                      sum(1 for g in mid.values() if mae(g, "comp") < mae(g, "cur_l")))]
    L += ["", "**Biggest misses, composite (last 3 nights)**", "", "| night | player | ADP at 2pm | actual | composite | by rank | current |", "|---|---|---|---|---|---|---|"]
    last3 = sorted({r["date"] for r in rows})[-3:]
    for r in sorted([r for r in rows if r["date"] in last3], key=lambda r: -abs(r["comp"] - r["act"]))[:12]:
        L.append("| %s | %s | %.1f | %.0f%% | %.0f%% | %.0f%% | %.0f%% |" % (r["date"], r["name"], r["adp"], 100 * r["act"], 100 * r["comp"],
                                                                         100 * r["comp_r"], 100 * r["cur_s"]))
    open(OUT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "backcheck"])
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "br-adp-mirror"))
    a = ap.parse_args()
    if a.cmd == "extract":
        extract(a.mirror)
    else:
        report(*backcheck())


if __name__ == "__main__":
    main()
