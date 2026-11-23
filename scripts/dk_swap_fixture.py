"""The late-swap tool's test fixtures (tests/swap_fixture/), from the 11-18 main slate (157033) at the study's break 2
(analysis/cbb/dk/lateswap_2026-11-21.md: the 00:30Z and 01:00Z games started, the decision at the 02:00Z tip):
  cards_157033.json            the lock card's players (the fields the swap tool reads), the field's projected
                               ownership at lock (own) and its outcome shape (z)
  plays_<event>.json           ESPN's play-by-play (trimmed) for the two games started by 02:00Z
  standings_157033_break2.csv  the contest's real standings (analysis/cbb/dk/standings) as at the tip: the players
                               still to play hidden (LOCKED in the Lineup cell, their ownership rows dropped), points blank
  DKEntries_fake.csv           three entries in DraftKings' entries-file format with made-up entry ids (never a real
                               entries file: those carry the owner's entry ids), lineups taken from the standings, the
                               started players' cells marked (LOCKED) as DraftKings writes them

  replay_157033_break2.json    the study's own inputs and picks for that contest at break 2 (scripts/dk_lateswap_study.py
                               load / nights / knowledge / test1 / test2, S nights, M imputations): the simulated nights,
                               each other entry's hidden imputations, our started players' points so far and share left,
                               every entry's lineup, ours marked, the payout table and the study's top-1% / EV picks. The
                               late-swap proposer must reproduce the picks from these inputs

  python3 scripts/dk_swap_fixture.py --mirror ../br-adp-mirror [--replay]
"""
import argparse, csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_sit as K       # noqa: E402  (lock_doc)

DATE, G, CONTEST, TIP = "2026-11-18", "157033", "197938363", "2026-11-19T02:00Z"
OUT = os.path.join(HERE, "..", "tests", "swap_fixture")
KEEP = ["name", "team", "game", "roster", "position", "salary", "game_start", "event", "espn", "fp_dk", "fp_gate", "miss_dk", "status", "min", "dk_avg"]
SLOTS = ["G", "G", "G", "F", "F", "F", "UTIL", "UTIL"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    ap.add_argument("--replay", action="store_true"); ap.add_argument("--S", type=int, default=300); ap.add_argument("--M", type=int, default=6)
    a = ap.parse_args()
    if a.replay:
        return replay(a)
    os.makedirs(OUT, exist_ok=True)
    sl, start = K.lock_doc(a.mirror, "dk_cbb_morning.json", DATE, G)
    cards = {i: {k: c.get(k) for k in KEEP} for i, c in sl["players"].items()}
    fl, _ = K.lock_doc(a.mirror, "dk_cbb_field.json", DATE, G, start)      # our projected ownership at lock (the field's)
    if not (fl or {}).get("z"):                                             # the outcome shape z sits on the field doc's top level
        from nba_daily import Mirror, iso
        Mi = Mirror(a.mirror); import datetime as dt
        v = [sha for t, sha in Mi.versions("dk_cbb_field.json", iso(DATE + "T00:00:00Z") - dt.timedelta(days=1), start) if t < start]
        _ = Mi.show(v[-1], "dk_cbb_field.json") if v else {}
    own = {i: round(v, 3) for i, v in ((fl or {}).get("own") or {}).items()}
    con = [{k: c.get(k) for k in ("id", "name", "size", "entry_fee", "max_per_user", "payouts")} for c in sl.get("contests", []) if str(c.get("id")) == CONTEST]
    json.dump({"draft_group": G, "date": DATE, "tip": TIP, "players": cards, "own": own, "z": (fl or {}).get("z") or (_ or {}).get("z"), "contests": con}, open(os.path.join(OUT, "cards_%s.json" % G), "w"), indent=0, sort_keys=True)
    started = lambda nm: any(c["name"] == nm and (c.get("game_start") or "9") < TIP for c in cards.values())
    src = os.path.join(HERE, "..", "analysis", "cbb", "dk", "standings", "contest-standings-%s.csv" % CONTEST)
    rows = list(csv.reader(open(src, encoding="utf-8-sig")))
    h = rows[0]; iL, iP, iPl = h.index("Lineup"), h.index("Points"), h.index("Player")
    out, lineups = [h], []
    for r in rows[1:]:
        r = r + [""] * (len(h) - len(r))
        if r[iL]:
            parts = re.split(r"(?:^|\s)(G|F|UTIL)\s", " " + r[iL].strip())
            pairs = [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]
            lineups.append(pairs)
            r[iL] = " ".join("%s %s" % (s, n if started(n) else "LOCKED") for s, n in pairs)
            r[iP] = ""
        if r[iPl] and not started(r[iPl].strip()):
            r[iPl:] = [""] * (len(h) - iPl)
        if any(x.strip() for x in r):
            out.append(r)
    with open(os.path.join(OUT, "standings_%s_break2.csv" % G), "w", newline="") as f:
        csv.writer(f, lineterminator="\r\n").writerows(out)
    byname = {c["name"]: i for i, c in cards.items()}
    ent = [["Entry ID", "Contest Name", "Contest ID", "Entry Fee"] + SLOTS + ["", "Instructions"]]
    for k, pairs in enumerate([p for p in lineups if all(n in byname for _, n in p)][:3]):
        g = [n for s, n in pairs if s == "G"]; f_ = [n for s, n in pairs if s == "F"]; u = [n for s, n in pairs if s == "UTIL"]
        cells = ["%s (%s)%s" % (n, byname[n], " (LOCKED)" if started(n) else "") for n in g + f_ + u]
        ent.append([str(9000000001 + k), "CBB $7K Pull Up Jumper [$2K to 1st]", CONTEST, "$15"] + cells + ["", ""])
    with open(os.path.join(OUT, "DKEntries_fake.csv"), "w", newline="") as f:
        csv.writer(f, lineterminator="\r\n").writerows(ent)
    print("fixtures: %d cards, %d standings entries, %d fake entries" % (len(cards), len(lineups), len(ent) - 1))


def replay(a):
    import tempfile
    import numpy as np
    import dk_lateswap_study as L
    rng = np.random.default_rng(20261121)
    sl = next(x for x in L.load(a.mirror) if x["g"] == G)
    c = next(x for x in sl["contests"] if x["id"] == CONTEST)
    k = 1                                                     # break 2: the decision at tips[2], 02:00Z
    ids, NIGHT = L.nights(sl, a.S, int(G))
    cache = os.path.join(tempfile.gettempdir(), "dk_lateswap_pbp"); os.makedirs(cache, exist_ok=True)
    base, left, _ = L.knowledge(sl, k, cache)
    _, imps, started, hidden = L.test1(sl, c, k, a.M, rng, None)
    t2 = L.test2(sl, c, k, imps, started, hidden, ids, NIGHT, rng, base, left)
    mine = sorted(int(e) for e in t2["picks"]["ev"])
    byent = {}
    for e, m, got in imps:
        byent.setdefault(int(e), []).append(list(got))
    table, fee = L.pay_of(c)
    doc = {"date": DATE, "g": G, "contest": CONTEST, "decision": sl["tips"][k + 1], "S": a.S, "M": a.M, "ids": ids,
           "nights": [[round(float(v), 2) for v in row] for row in NIGHT], "started": sorted(started), "hidden": sorted(hidden),
           "base": {i: round(float(v), 2) for i, v in base.items()}, "left": {i: round(float(v), 4) for i, v in left.items()},
           "lineups": [[[s_, i] for s_, i in lu] for lu in c["L"]], "mine": mine, "imps": {str(e): v for e, v in byent.items()},
           "table": {str(p): v for p, v in (table or {}).items()}, "fee": fee,
           "cards": {i: {"salary": r["salary"], "roster": r["roster"], "status": r["status"]} for i, r in sl["R"].items()},
           "picks": {pol: {str(e): {"ids": v[0], "swap": list(v[1]) if v[1] else None} for e, v in t2["picks"][pol].items()} for pol in ("top1", "ev")},
           "cands": {str(e): [{"swap": list(w) if w else None, "top1": sc[0], "cash": sc[1], "ev": sc[2]} for w, sc in v] for e, v in t2["picks"]["cands"].items()}}
    json.dump(doc, open(os.path.join(OUT, "replay_%s_break2.json" % G), "w"), separators=(",", ":"))
    sw = sum(1 for v in doc["picks"]["ev"].values() if v["swap"])
    print("replay fixture: %d entries (%d ours, %d swapped under EV), %d nights x %d players, %d imputed entries" % (
        len(doc["lineups"]), len(mine), sw, len(doc["nights"]), len(ids), len(doc["imps"])))


if __name__ == "__main__":
    main()
