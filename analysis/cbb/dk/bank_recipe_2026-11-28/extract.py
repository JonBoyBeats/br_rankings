"""Lock-time nights for every graded slate with standings (the slate, the simulated field's ownership and outcome shape
z as they stood before the first lock), from the mirror; written to a work dir, not committed (mirror data).
  python3 extract.py --out WORK"""
import argparse, csv, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True)
ap.add_argument("--mirror", default=os.path.join(os.path.dirname(ROOT), "br-adp-mirror")); a = ap.parse_args()
if not os.path.isdir(a.mirror):
    a.mirror = "/home/user/br-adp-mirror"
M = E.Mirror(a.mirror); os.makedirs(a.out, exist_ok=True)
by = {}
for r in E.read(E.EVAL):
    if os.path.exists(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % r["contest_id"])):
        by.setdefault((r["date"], r["draft_group"]), r["contest_id"])
for (date, g), cid in sorted(by.items()):
    _, slate, start = E.slate_for(M, cid)
    if not slate:
        print("no slate", date, g); continue
    fd = E.at_lock(M, "dk_cbb_field.json", start, g)
    Fd = ((fd or {}).get("slates") or {}).get(g)
    if not Fd:
        print("no field", date, g); continue
    json.dump({"date": date, "g": g, "slate": slate, "field": {"own": Fd.get("own") or {}, "field": Fd.get("field") or []}, "z": fd.get("z")},
              open(os.path.join(a.out, "%s_%s.json" % (date, g)), "w"))
    print(date, g, len(slate["players"]), "players", len(Fd.get("field") or []), "field lineups", len(fd.get("z") or []), "z")
