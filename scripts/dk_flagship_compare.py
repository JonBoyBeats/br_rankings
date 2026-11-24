"""Flagship comparison driver (2026-11-24, contest profiles; in-sim only): for each saved build (analysis/cbb/dk/builds),
the slate and the simulated field as they stood at lock (the mirror's dk_cbb_morning.json and dk_cbb_field.json), then
scripts/dk_flagship_compare.js on them (the flagships filled together against each apart). Writes
analysis/cbb/dk/fill_profiles_2026-11-24/flagship_joint.jsonl. (flagship_compare*.jsonl there: the earlier "win"
objective comparison, from this script's version at commit 577892c.)

  python3 scripts/dk_flagship_compare.py --mirror ../br-adp-mirror [--sims 3000]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from dk_eval import DK, Mirror, at_lock, iso, slate_for  # noqa: E402

OUT = os.path.join(DK, "fill_profiles_2026-11-24", "flagship_joint.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--sims", default="3000")
    a = ap.parse_args()
    mirror, lines = Mirror(a.mirror), []
    for bf in sorted(glob.glob(os.path.join(DK, "builds", "dk_bank_*.json"))):
        B = json.load(open(bf))
        g = str(B.get("draft_group"))
        slate = start = None
        for cid in (B.get("portfolios") or {}):
            _, slate, start = slate_for(mirror, cid)
            if slate and str(slate["draft_group_id"]) == g:
                break
            slate = None
        if not slate:          # no night record yet (the newest night): the mirror's slate by the build's day
            import datetime as dt
            day = iso(B["day"] + "T00:00:00Z")
            for _, sha in reversed(mirror.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
                s0 = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
                if s0 and iso(s0["start"]) > dt.datetime.fromtimestamp(0, dt.timezone.utc):
                    slate, start = s0, iso(s0["start"])
                    break
        if not slate:
            print("%s: no slate at lock" % os.path.basename(bf))
            continue
        fd = at_lock(mirror, "dk_cbb_field.json", start, g)
        F = ((fd or {}).get("slates") or {}).get(g)
        if not F or not F.get("field"):
            print("%s: no simulated field saved before lock" % os.path.basename(bf))
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump({"slate": slate, "field": {"field": F["field"], "own": F.get("own") or {}}, "z": fd.get("z")}, t)
        r = subprocess.run(["node", os.path.join(os.path.dirname(__file__), "dk_flagship_compare.js"), t.name, bf, "--sims", a.sims],
                           capture_output=True, text=True)
        os.unlink(t.name)
        if r.returncode:
            print("%s: %s" % (os.path.basename(bf), r.stderr.strip()[-300:]))
            continue
        got = [l for l in r.stdout.splitlines() if l.strip()]
        print("%s: %d flagship contest(s)" % (os.path.basename(bf), len(got)))
        lines += got
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    print("%d rows to %s" % (len(lines), OUT))


if __name__ == "__main__":
    sys.exit(main())
