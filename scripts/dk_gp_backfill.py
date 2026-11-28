"""Games played at lock for the night records written before cbb_daily.py logged a gp column (2026-11-28, tooling only).

Reads each graded night record's lock file (battle-royale-research data/dk/cbb/<date>_<draft group>_proj.json, its "gp")
and writes analysis/cbb/dk/gp_at_lock.csv: slate, dk_id, gp. The scorecard's games-played split reads a record's own gp
column first and this file second. Rerunnable; it rewrites the file whole.

  python3 scripts/dk_gp_backfill.py [--brr ../battle-royale-research]
"""
import argparse, csv, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
OUT = os.path.join(DK, "gp_at_lock.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brr", default=os.path.join(HERE, "..", "..", "battle-royale-research"))
    a = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        slate = os.path.basename(f)[:-4]
        pj = os.path.join(a.brr, "data", "dk", "cbb", slate + "_proj.json")
        if not os.path.exists(pj):
            print("  no lock file for %s" % slate)
            continue
        P = json.load(open(pj))
        for r in csv.DictReader(open(f)):
            gp = (P.get(r["dk_id"]) or {}).get("gp")
            if gp not in (None, "", "None"):
                rows.append({"slate": slate, "dk_id": r["dk_id"], "gp": int(float(gp))})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slate", "dk_id", "gp"])
        w.writeheader()
        w.writerows(rows)
    print("gp_at_lock.csv: %d rows on %d slates" % (len(rows), len({r["slate"] for r in rows})))


if __name__ == "__main__":
    main()
