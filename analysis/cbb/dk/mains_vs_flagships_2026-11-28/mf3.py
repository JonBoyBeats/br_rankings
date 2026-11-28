"""Noise check: what a uniformly random finish would pay in these exact contests, and how many big cashes it implies."""
import json, math, statistics as S, sys, os, random
sys.path.insert(0, "/home/user/br_rankings/scripts"); import dk_eval as E
R = json.load(open(__import__("os").environ.get("ROWS","mf_rows.json")))
SUP = json.load(open("/home/user/br_rankings/analysis/cbb/dk/contests_supplement.json"))["contests"]
M = E.Mirror("/home/user/br-adp-mirror")
def table(cid):
    if cid in SUP: return E.pay_table(SUP[cid]["payouts"])
    _, s, _ = E.slate_for(M, cid); c = next(c for c in s["contests"] if str(c["id"]) == cid); return E.pay_table(c.get("payouts"))
for t in ("flagship", "main", "qualifier/small"):
    rs = [r for r in R if r["type"] == t]
    exp_back = 0; lam = 0; obs = 0; fees = 0; sims = []
    tabs = {r["cid"]: table(r["cid"]) for r in rs}
    for r in rs:
        tb = tabs[r["cid"]]; n = r["n"]; k = r["k"]
        exp_back += k * sum(tb.values()) / n
        big = sum(1 for p in tb.values() if p >= 5 * r["fee"])   # places paying 5x+ fee
        lam += k * big / n
        obs += sum(p >= 5 * r["fee"] for p in r["pays"])
        fees += r["fees"]
    # simulate ROI of uniformly random finishes for our exact entry counts (no correlation between our entries: optimistic spread)
    rng = random.Random(5)
    for _ in range(4000):
        b = 0
        for r in rs:
            tb = tabs[r["cid"]]
            for _ in range(r["k"]): b += tb.get(rng.randint(1, r["n"]), 0)
        sims.append((b - fees) / fees)
    sims.sort()
    real = (sum(r["back"] for r in rs) - fees) / fees
    print(f"{t:16s} random-finish ROI {exp_back/fees-1:+.1%} (90% of random-finish outcomes in [{sims[200]:+.0%}, {sims[3800]:+.0%}]); "
          f"real {real:+.1%} sits at the {sum(s < real for s in sims)/40:.0f}th pct of random-finish outcomes | "
          f"5x+-fee cashes expected {lam:.2f}, observed {obs}, P(obs or fewer | random) {sum(math.exp(-lam)*lam**i/math.factorial(i) for i in range(obs+1)):.2f}")
