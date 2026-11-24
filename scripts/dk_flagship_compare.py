"""Flagship comparison driver (2026-11-24, contest profiles; in-sim only): for each saved build (analysis/cbb/dk/builds),
the slate and the simulated field as they stood at lock (the mirror's dk_cbb_morning.json and dk_cbb_field.json), then
scripts/dk_flagship_compare.js on them (the flagships filled together against each apart). Appends each new build's
row to analysis/cbb/dk/flagship_joint.csv (the nightly grading runs it: dk_eval.py nightly / flagjoint); with --all,
every build again and analysis/cbb/dk/fill_profiles_2026-11-24/flagship_joint.jsonl. (flagship_compare*.jsonl there: the earlier "win"
objective comparison, from this script's version at commit 577892c.)

  python3 scripts/dk_flagship_compare.py --mirror ../br-adp-mirror [--sims 3000] [--all]
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
CSV = os.path.join(DK, "flagship_joint.csv")       # one row per saved build, appended as builds come in (the grading's record)
CSV_COLS = ["date", "draft_group", "flagships", "entries", "sims", "cov_joint", "cov_separate", "cov_diff", "ev_joint", "ev_separate", "ev_diff",
            "cov_joint_in", "cov_separate_in", "ev_joint_in", "ev_separate_in", "cov_entered", "ev_entered"]


def csv_row(r):
    j, sp, e = r["joint"], r["separate"], r["entered"]["out"]
    f = lambda x, d=4: round(x, d)
    return {"date": r["day"], "draft_group": r["draft_group"], "flagships": " + ".join(c["name"] for c in r["contests"]),
            "entries": " + ".join(str(c["n"]) for c in r["contests"]), "sims": r["sims"],
            "cov_joint": f(j["out"]["joint"]), "cov_separate": f(sp["out"]["joint"]), "cov_diff": f(j["out"]["joint"] - sp["out"]["joint"]),
            "ev_joint": f(j["out"]["ev"], 2), "ev_separate": f(sp["out"]["ev"], 2), "ev_diff": f(j["out"]["ev"] - sp["out"]["ev"], 2),
            "cov_joint_in": f(j["in"]["joint"]), "cov_separate_in": f(sp["in"]["joint"]), "ev_joint_in": f(j["in"]["ev"], 2), "ev_separate_in": f(sp["in"]["ev"], 2),
            "cov_entered": f(e["joint"]), "ev_entered": f(e["ev"], 2)}


def run(mirror, sims="3000", only_new=True, jsonl=None):
    """Each saved build's flagships, joint against separate (dk_flagship_compare.js) on the slate and field at lock.
    only_new: the builds not yet in CSV (appended); jsonl: also write every row there. Returns the rows found."""
    import csv
    import datetime as dt
    done = set()
    if only_new and os.path.exists(CSV):
        done = {(r["date"], str(r["draft_group"])) for r in csv.DictReader(open(CSV))}
    lines = []
    for bf in sorted(glob.glob(os.path.join(DK, "builds", "dk_bank_*.json"))):
        B = json.load(open(bf))
        g = str(B.get("draft_group"))
        if (B.get("day"), g) in done:
            continue
        slate = start = None
        for cid in (B.get("portfolios") or {}):
            _, slate, start = slate_for(mirror, cid)
            if slate and str(slate["draft_group_id"]) == g:
                break
            slate = None
        if not slate:          # no night record yet (the newest night): the mirror's slate by the build's day
            day = iso(B["day"] + "T00:00:00Z")
            for _, sha in reversed(mirror.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
                s0 = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
                if s0:
                    slate, start = s0, iso(s0["start"])
                    break
        if not slate:
            print("  flagships %s: no slate at lock" % os.path.basename(bf))
            continue
        fd = at_lock(mirror, "dk_cbb_field.json", start, g)
        F = ((fd or {}).get("slates") or {}).get(g)
        if not F or not F.get("field"):
            print("  flagships %s: no simulated field saved before lock" % os.path.basename(bf))
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump({"slate": slate, "field": {"field": F["field"], "own": F.get("own") or {}}, "z": fd.get("z")}, t)
        r = subprocess.run(["node", os.path.join(os.path.dirname(__file__), "dk_flagship_compare.js"), t.name, bf, "--sims", str(sims)],
                           capture_output=True, text=True)
        os.unlink(t.name)
        if r.returncode:
            print("  flagships %s: %s" % (os.path.basename(bf), r.stderr.strip()[-300:]))
            continue
        lines += [l for l in r.stdout.splitlines() if l.strip()]
    rows = [json.loads(l) for l in lines]
    if jsonl:
        os.makedirs(os.path.dirname(jsonl), exist_ok=True)
        with open(jsonl, "w") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
    import csv
    new = not os.path.exists(CSV)
    keep = [r for r in rows if (r["day"], str(r["draft_group"])) not in done]
    if keep or new:
        with open(CSV, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS, lineterminator="\n")
            if new:
                w.writeheader()
            w.writerows(csv_row(r) for r in keep)
    for r in keep:
        c = csv_row(r)
        print("  flagships %s (%s): joint top-1%% coverage %.2f%% vs separate %.2f%% (%+.2f points), expected payout $%.2f vs $%.2f (%+.2f), fresh nights"
              % (c["date"], c["flagships"], 100 * c["cov_joint"], 100 * c["cov_separate"], 100 * c["cov_diff"], c["ev_joint"], c["ev_separate"], c["ev_diff"]))
    print("  flagships: %d new build(s) to %s" % (len(keep), CSV))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--sims", default="3000")
    ap.add_argument("--all", action="store_true", help="every build again (and the jsonl), not only the new ones")
    a = ap.parse_args()
    run(Mirror(a.mirror), a.sims, only_new=not a.all, jsonl=OUT if a.all else None)


if __name__ == "__main__":
    sys.exit(main())
