"""Pick method vs pool: the fill's entered portfolios vs 1,000 random fills from the same kept pool, as ROI, by type and era (fr_fill.json)."""
import json
R = json.load(open(__import__("os").environ.get("FILL","fr_fill.json")))
for t in ("flagship", "main", "qualifier/small"):
    for era, f in (("all", lambda r: True), ("pre 11-24", lambda r: r["day"] < "2026-11-24"), ("11-24 on", lambda r: r["day"] >= "2026-11-24")):
        rs = [r for r in R if r["type"] == t and f(r)]
        if not rs: continue
        fees = sum(r["fee"] * r["k"] for r in rs)
        ent = sum(r["ent_d"] for r in rs); rnd = sum(r["rand"][0] for r in rs)
        print(f"{t:16s} {era:9s} contests {len(rs):2d} slates {len({r['g'] for r in rs}):2d} fees ${fees:7.2f} | entered ROI {ent/fees-1:+.0%} | random kept fills ROI {rnd/fees-1:+.0%} | gap {(ent-rnd)/fees:+.0%}")
