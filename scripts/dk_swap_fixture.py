"""The late-swap tool's test fixtures (tests/swap_fixture/), from the 11-18 main slate (157033) at the study's break 2
(analysis/cbb/dk/lateswap_2026-11-21.md: the 00:30Z and 01:00Z games started, the decision at the 02:00Z tip):
  cards_157033.json            the lock card's players (the fields the swap tool reads)
  standings_157033_break2.csv  the contest's real standings (analysis/cbb/dk/standings) as at the tip: the players
                               still to play hidden (LOCKED in the Lineup cell, their ownership rows dropped), points blank
  DKEntries_fake.csv           three entries in DraftKings' entries-file format with made-up entry ids (never a real
                               entries file: those carry the owner's entry ids), lineups taken from the standings, the
                               started players' cells marked (LOCKED) as DraftKings writes them

  python3 scripts/dk_swap_fixture.py --mirror ../br-adp-mirror
"""
import argparse, csv, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_sit as K       # noqa: E402  (lock_doc)

DATE, G, CONTEST, TIP = "2026-11-18", "157033", "197938363", "2026-11-19T02:00Z"
OUT = os.path.join(HERE, "..", "tests", "swap_fixture")
KEEP = ["name", "team", "game", "roster", "position", "salary", "game_start", "event", "espn", "fp_dk", "miss_dk", "status", "min", "dk_avg"]
SLOTS = ["G", "G", "G", "F", "F", "F", "UTIL", "UTIL"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror")); a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    sl, _ = K.lock_doc(a.mirror, "dk_cbb_morning.json", DATE, G)
    cards = {i: {k: c.get(k) for k in KEEP} for i, c in sl["players"].items()}
    json.dump({"draft_group": G, "date": DATE, "tip": TIP, "players": cards}, open(os.path.join(OUT, "cards_%s.json" % G), "w"), indent=0, sort_keys=True)
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


if __name__ == "__main__":
    main()
