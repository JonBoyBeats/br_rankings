"""B.3, the shared-lineup cut credit (2026-11-23 lock review): score the two cuts scripts/dk_shared_credit_study.js
made of each saved build (today's credit, a lineup to the idea that drew it first; the proposal, a shared lineup to the
idea where it ranks best) on real results. For every contest the night was entered in: each kept lineup's real points
(the graded slate file), its percentile among the real entries, top 10% and cash (the contest's payout places), then
entries-weighted over the contests. Also the lineups only one cut kept, which is where any difference lives.

  python3 scripts/dk_shared_credit_study.py --dir DIR       (DIR: the tier study's night files and the .js outputs)
"""
import argparse, bisect, csv, glob, json, math, os, statistics as S, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_eval as E    # noqa: E402

DK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "cbb", "dk")


def score(pool, idx, act, contests):
    """Entries-weighted {pctl, top10, cash, n} of the lineups idx over the contests [(n, field points sorted, t10, cash)]."""
    if not idx:
        return None
    pts = [sum(act.get(str(x), 0.0) for x in pool[i]) for i in idx]
    W = sum(c[0] for c in contests); out = {"pctl": 0.0, "top10": 0.0, "cash": 0.0, "n": len(idx)}
    for n, field, t10, cash in contests:
        out["pctl"] += n / W * S.mean(bisect.bisect_left(field, p) / len(field) for p in pts)
        out["top10"] += n / W * S.mean(p >= t10 for p in pts)
        out["cash"] += n / W * S.mean(p >= cash for p in pts)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); a = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(a.dir, "b3_*.json"))):
        R = json.load(open(f)); key = R["key"]
        N = json.load(open(os.path.join(a.dir, key + ".json")))
        B = json.load(open(os.path.join(DK, "builds", "dk_bank_%s.json" % key)))
        act = {r["dk_id"]: float(r["actual_dk"] or 0) for r in csv.DictReader(open(os.path.join(DK, "%s.csv" % key)))}
        cs = []
        for x in N["contests"]:
            c = x["contest"]; p = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c["id"])
            if not os.path.exists(p):
                continue
            ents, _ = E.standings(p)
            field = sorted(e["points"] for e in ents)
            desc = field[::-1]
            t10 = desc[max(0, math.ceil(0.1 * len(desc)) - 1)]
            paid = max(E.pay_table(c["payouts"])) if c.get("payouts") else max(1, int(0.2 * len(desc)))
            cs.append((x["n"], field, t10, desc[min(paid, len(desc)) - 1]))
        A, Bk = set(R["keepA"]), set(R["keepB"])
        sa, sb = score(B["pool"], R["keepA"], act, cs), score(B["pool"], R["keepB"], act, cs)
        oa, ob = score(B["pool"], sorted(A - Bk), act, cs), score(B["pool"], sorted(Bk - A), act, cs)
        rows.append((key, R, sa, sb, oa, ob, len(cs)))
    print("B.3: the cut with today's credit (first idea) vs the proposal (a shared lineup to the idea where it ranks best),")
    print("same nights; kept pools on real results, entries-weighted over the night's entered contests. Thin: %d nights." % len(rows))
    print("| Night | Bank | Shared | Moved | Kept (A / B) | Overlap | Percentile A -> B | Top 10% A -> B | Cash A -> B | Only-A vs only-B lineups (n, percentile) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    better = 0
    for key, R, sa, sb, oa, ob, nc in rows:
        f = lambda x, k: "%.1f" % (100 * x[k]) if x else "–"
        better += sb["pctl"] > sa["pctl"] + 1e-9
        print("| %s | %d | %d | %d | %d / %d | %d | %s -> %s | %s -> %s | %s -> %s | %s (%s) vs %s (%s) |" % (
            key, R["bank"], R["shared"], R["moved"], len(R["keepA"]), len(R["keepB"]), R["overlap"], f(sa, "pctl"), f(sb, "pctl"),
            f(sa, "top10"), f(sb, "top10"), f(sa, "cash"), f(sb, "cash"), oa["n"] if oa else 0, f(oa, "pctl"), ob["n"] if ob else 0, f(ob, "pctl")))
    if rows:
        m = lambda i, k: S.mean(r[i][k] for r in rows)
        print("\nPooled (nights equal): percentile %.1f -> %.1f, top 10%% %.1f -> %.1f, cash %.1f -> %.1f; the proposal's percentile higher on %d of %d nights" % (
            100 * m(2, "pctl"), 100 * m(3, "pctl"), 100 * m(2, "top10"), 100 * m(3, "top10"), 100 * m(2, "cash"), 100 * m(3, "cash"), better, len(rows)))


if __name__ == "__main__":
    main()
