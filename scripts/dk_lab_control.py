"""Lab d's control (2026-11-28, the operator, Section 7): the night's plain L0 U0 draw replayed at lock, saved as
analysis/cbb/dk/lab_controls/<date>_<draft group>.json for dk_eval.py lab. For every saved build without one: the slate
and the simulated field as they stood before the first lock (the mirror), then 600 lineups from DKSim.poolDraw with
no rules (Leverage 0, Under 0, Bank noise 0.35, the deep bench out, a fixed seed per draft group;
analysis/cbb/dk/bank_recipe_2026-11-28/recipe.js --only plain600). Run by hand after a night with green batches; --recipe d9 runs in dk_eval.py nightly (bankprev).

--recipe d9 (2026-11-28, batch item 2, the bank arm's PREVIOUS): the night's Draw-the-9 replay at lock instead (the 9
cells L{0, .1, .2} x U{0, 1, 2}, equal shares, 600 lineups; recipe.js --only d9 --total 600), saved as
analysis/cbb/dk/bank_prev/<date>_<draft group>.json and graded against the live bank by the scorecard's bank line.

  python3 scripts/dk_lab_control.py [--mirror ../br-adp-mirror] [--redo] [--recipe plain600|d9] [--group G]
"""
import argparse, glob, json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_eval as E  # noqa: E402

RECIPE = os.path.join(E.DK, "bank_recipe_2026-11-28", "recipe.js")
BANK_PREV = os.path.join(E.DK, "bank_prev")
HOW = {"plain600": "plain L0 U0, Bank noise 0.35, deep bench out, seeded by draft group, 600 lineups (recipe.js plain600)",
       "d9": "Draw the 9 (L{0,.1,.2} x U{0,1,2}, equal shares), Bank noise 0.35, deep bench out, seeded by draft group, 600 lineups (recipe.js d9 --total 600)"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "br-adp-mirror"))
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--recipe", default="plain600", choices=sorted(HOW))
    ap.add_argument("--group", default=None)
    ap.add_argument("--since", default=None, help="only builds of this day or later")
    a = ap.parse_args(argv)
    M = E.Mirror(a.mirror)
    dest = E.LAB_CONTROLS if a.recipe == "plain600" else BANK_PREV
    os.makedirs(dest, exist_ok=True)
    for bf in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        B = json.load(open(bf))
        day, g = B.get("day"), str(B.get("draft_group"))
        if (a.group and g != a.group) or (a.since and (day or "") < a.since):
            continue
        out = os.path.join(dest, "%s_%s.json" % (day, g))
        if os.path.exists(out) and not a.redo:
            continue
        slate = start = None
        for cid in (B.get("portfolios") or {}):
            _, slate, start = E.slate_for(M, cid)
            if slate and str(slate["draft_group_id"]) == g:
                break
            slate = None
        if not slate:
            print(day, g, "no lock-time slate on the mirror; skipped")
            continue
        fd = E.at_lock(M, "dk_cbb_field.json", start, g)
        Fd = ((fd or {}).get("slates") or {}).get(g)
        if not Fd:
            print(day, g, "no lock-time field; skipped")
            continue
        with tempfile.TemporaryDirectory() as t:
            nf, of, gf = os.path.join(t, "night.json"), os.path.join(t, "out.json"), os.path.join(t, "greens.json")
            json.dump({"date": day, "g": g, "slate": slate, "field": {"own": Fd.get("own") or {}, "field": Fd.get("field") or []}, "z": fd.get("z")}, open(nf, "w"))
            json.dump({}, open(gf, "w"))
            subprocess.run(["node", RECIPE, nf, gf, of, "--only", a.recipe] + (["--total", "600"] if a.recipe == "d9" else []), check=True)
            R = json.load(open(of))["recipes"][a.recipe]
        json.dump({"date": day, "draft_group": g, "how": HOW[a.recipe], "lineups": R["bank"]}, open(out, "w"))
        print(day, g, len(R["bank"]), a.recipe, "lineups ->", os.path.relpath(out, E.DK))


if __name__ == "__main__":
    main()
