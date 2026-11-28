"""Candidate pool for one slate: battle-royale-research dk_cbb_field.field() on the lock-time slate, n = FIELD_N x
RAKE_POOL (1,500, as the live run draws), seed 7 per slate, the saved field's Questionable factor; then today's ownership
correction (own_fix, total 800). Writes <data>/<slate>_pool.json {pool, own_raw, own}.
python3 gen.py --brr ../battle-royale-research --data <dir> <slate file> ..."""
import argparse, json, os, sys, time
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--brr"); ap.add_argument("--data"); ap.add_argument("files", nargs="+"); ap.add_argument("--n", type=int, default=0)
ap.add_argument("--noise-x", type=float, default=0, help="R4: every build style's noise times this; writes _pool_r4.json")
a = ap.parse_args()
sys.path.insert(0, os.path.join(a.brr, "scripts"))
import dk_cbb_field as FLD
for f in a.files:
    t = time.time()
    s = json.load(open(f))
    q = ((s.get("prev_params") or {}).get("questionable")) or 1.0
    n = a.n or int(FLD.FIELD_N * FLD.RAKE_POOL)
    styles = [dict(st, noise=st["noise"] * a.noise_x) for st in FLD.FIELD_STYLES] if a.noise_x else None
    pool, own_raw = FLD.field(s["players"], np.random.default_rng(FLD.SEED), styles=styles, n=n, q=q)
    own = FLD.own_fix(s["players"], own_raw, total=800.0)
    out = f.replace(".json", "_pool_r4.json" if a.noise_x else "_pool.json") if not a.n else f.replace(".json", "_pooltest.json")
    json.dump({"pool": pool, "own_raw": own_raw, "own": own, "q": q, "n": len(pool)}, open(out, "w"))
    print(os.path.basename(f), len(pool), "lineups", round(time.time() - t, 1), "s", flush=True)
