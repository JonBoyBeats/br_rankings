"""Save one night for scripts/live_audit.js: the slate as it stood before lock (ADP), the morning
file's usual points as of then (both from a clone of br-adp-mirror's history), and each player's final
points and stints from battle-royale-research's nightly box archive.

  python3 scripts/live_audit_fixture.py 2026-10-27 nba_tue_main \\
      --mirror ../br-adp-mirror --box ../battle-royale-research/nba/box/2026-27/2026-10-27.json
"""
import argparse, json, os, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("day"); ap.add_argument("label")
ap.add_argument("--mirror", required=True, help="a full clone of br-adp-mirror (its history has each hour's files)")
ap.add_argument("--box", required=True, help="the night's file from battle-royale-research nba/box/<season>/")
a = ap.parse_args()


def at(path, before):
    h = subprocess.run(["git", "-C", a.mirror, "log", "-1", "--format=%H", "--before=" + before, "--", path],
                       capture_output=True, text=True).stdout.strip()
    return json.loads(subprocess.run(["git", "-C", a.mirror, "show", h + ":" + path], capture_output=True, text=True).stdout) if h else None


slate = None
for t in ("T18:00:00Z", "T20:00:00Z", "T22:00:00Z", "T23:30:00Z"):        # the latest copy with the slate's players still on it
    s = [x for x in (at("nba_latest.json", a.day + t) or {}).get("slates", []) if x["label"] == a.label]
    if s and s[0]["players"]:
        slate = s[0]
morning = at("nba_morning.json", a.day + "T23:00:00Z")
box = json.load(open(a.box))
if not slate or not morning or not box.get("complete"):
    raise SystemExit("Need the slate, the morning file and a complete box day for %s." % a.day)
fix = {"day": a.day, "label": a.label,
       "players": [{k: p[k] for k in ("first_name", "last_name", "team", "adp")} for p in slate["players"] if p.get("adp") is not None],
       "morning": [{"name": r["name"], "fp": r["fp"]} for r in morning["players"]],
       "games": [{"id": g["id"], "name": g["name"], "len": g.get("len")} for g in box["games"] if g.get("flow")],
       "box": [{k: r[k] for k in ("name", "team", "gid", "dnp", "fp", "st") if k in r} for r in box["players"]]}
out = os.path.join(os.path.dirname(__file__), "..", "tests", "live_audit", a.day + ".json")
json.dump(fix, open(out, "w"), separators=(",", ":"))
print("%s: %d players, %d games -> %s" % (a.day, len(fix["players"]), len(fix["games"]), os.path.relpath(out)))
