"""The field by contest size, with the ownership rules inside it (2026-11-23, the operator's approval of the lock review:
"retest inside the field"). Builds on scripts/dk_field_study.py (its measures, real fields and cached builds).

Each band's field: the field study's fitted chalk style (DraftKings' average, noise .08) at the band's share (Large
0.2, Medium 0.3, Small 0.4: Small the operator's prior, unfitted), the no-punt pool, and two ownership rules baked in:
  casual   a style share at noise CASUAL_NOISE (w 0.5): lifts the players we project near 0 (the floor: real ownership
           under 5% ran ~2x ours), fitted per band held out by night on the ownership bands
  big      "coming off a big game" x1.22 on the field projection (battle-royale-research dk_cbb_field.big_game)

The realism bar (the operator's, 2026-11-23): a change is accepted when each targeted measure (duplication, the under-5%
ratio, punts under $3.5k, the top trio and trio lift, salary at the cap, 3+ from a team) moves toward the real fields on
most nights (Large 6+ of 9; Medium most of its nights; Small report only), the 5-20% and 20%+ ratios are not worse on
most nights, and same-seed rule-free banks cut against it are not worse than against the current field.

  python3 scripts/dk_field_bands.py build --brr ../battle-royale-research --cache DIR     (fields, cached with the study's)
  python3 scripts/dk_field_bands.py score --brr ../battle-royale-research --cache DIR     (measures, fit, the bar)
  python3 scripts/dk_field_bands.py owner --brr ../battle-royale-research --cache DIR --casual X  (the owner's duplication, real vs fields)
  python3 scripts/dk_field_bands.py banks --brr ../battle-royale-research --cache DIR --casual X  (the bank test, Large)
"""
import argparse, json, math, os, statistics as S, sys
from collections import defaultdict
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E                    # noqa: E402
import dk_field_study as FS            # noqa: E402

CHALK = {"Large": 0.2, "Medium": 0.3, "Small": 0.4}
CASUAL = (0.0, 0.04, 0.08, 0.12)
CASUAL_NOISE = 0.8


def styles(ca, cs):
    st = [{"share": ca, "w": 0.0, "noise": 0.08, "min_sal": 0}]
    if cs:
        st.append({"share": cs, "w": 0.5, "noise": CASUAL_NOISE, "min_sal": 0})
    st.append({"share": round(1 - ca - cs, 4), "w": 0.5, "noise": 0.25, "min_sal": 0})
    return st


def label(b, cs):
    return "band %s chalk%.1f cas%.2f big nopunt" % (b, CHALK[b], cs)


def _job(args):
    brr, date, g, lab, st, q = args
    sys.path.insert(0, os.path.join(brr, "scripts"))
    import numpy as np
    import dk_cbb_field as fld
    players, _, _ = FS.load_night(brr, date, g)
    L, _ = fld.field(players, np.random.default_rng(7), st, n=1000, q=q, punts=False, big=True)
    return "|".join((date, g, lab)), [sorted(x) for x in L]


def build(a):
    R = FS.real_fields(FS.nights(), a.brr)
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import dk_cbb_field as fld
    q = fld.q_factor(os.path.join(FS.DK, "gate.json"))
    nb = defaultdict(set)
    for (d, g, cid), x in R.items():
        nb[x["band"]].add((d, g))
    path = os.path.join(a.cache, "bands_fields.json")
    have = json.load(open(path)) if os.path.exists(path) else {}
    jobs = [(a.brr, d, g, label(b, cs), styles(CHALK[b], cs), q) for b in CHALK for cs in CASUAL for d, g in sorted(nb[b])]
    todo = [j for j in jobs if "|".join((j[1], j[2], j[3])) not in have]
    print("%d builds (%d cached)" % (len(todo), len(jobs) - len(todo)), file=sys.stderr)
    with Pool(min(4, os.cpu_count() or 1)) as P:
        for k, L in P.imap_unordered(_job, todo):
            have[k] = L
            json.dump(have, open(path, "w"))
            print("built " + k, file=sys.stderr, flush=True)


def fields(a):
    out = json.load(open(os.path.join(a.cache, "fields.json")))          # the study's (its "current" per night)
    out.update(json.load(open(os.path.join(a.cache, "bands_fields.json"))))
    return out


def rows(a):
    """Per contest and field: the measures (real and sim), and the ownership band ratios real / the field's own."""
    R = FS.real_fields(FS.nights(), a.brr)
    F = fields(a)
    out = []
    for (date, g, cid), x in sorted(R.items()):
        players, _, _ = FS.load_night(a.brr, date, g)
        n = min(len(x["L"]), 1000)
        rm, rown = FS.measures(x["L"], x["U"], players, n)
        for lab in ["current"] + [label(x["band"], cs) for cs in CASUAL]:
            key = "|".join((date, g, lab))
            if key not in F:
                continue
            sm, sown = FS.measures([tuple(v) for v in F[key]], None, players, n)
            gaps, mae = FS.player_gaps(rown, sown, players)
            out.append({"date": date, "g": g, "cid": cid, "band": x["band"], "entries": x["entries"], "label": "current" if lab == "current" else "cas%.2f" % float(lab.split("cas")[1].split()[0]),
                        "real": rm, "sim": sm, "u5": gaps.get("own <5"), "m": gaps.get("own 5-20"), "t": gaps.get("own 20+"), "own_mae": mae})
    return out


TARGET = [("dup", "duplication %"), ("u5", "under-5% real/field (to 1)"), ("punt1", "a sub-$3.5k punt %"), ("trio1", "most common trio %"),
          ("lift_trios", "top-20 trio lift"), ("at_cap", "at the cap %"), ("team3", "3+ from a team %")]
OTHER = [("m", "5-20% real/field (to 1)"), ("t", "20%+ real/field (to 1)")]          # not to be worse


def dist(r, k):
    if k in ("u5", "m", "t"):
        return abs(math.log(r[k])) if r.get(k) else None
    return abs((r["sim"].get(k) or 0) - (r["real"].get(k) or 0))


def own_err(xs):
    v = [abs(math.log(x[k])) for x in xs for k in ("u5", "m", "t") if x.get(k)]
    return S.mean(v) if v else 9


def score(a):
    X = rows(a)
    json.dump(X, open(os.path.join(a.cache, "bands_rows.json"), "w"), default=str)
    L = []
    for b in ("Large", "Medium", "Small"):
        xb = [x for x in X if x["band"] == b]
        nts = sorted({(x["date"], x["g"]) for x in xb})
        L.append("## %s: %d contests, %d nights%s" % (b, len({x["cid"] for x in xb}), len(nts), " (thin: report only; chalk 0.4 is the operator's prior)" if b == "Small" else ""))
        # the casual share held out by night: chosen on the other nights' ownership bands
        chosen = {}
        for nt in nts:
            other = [x for x in xb if (x["date"], x["g"]) != nt and x["label"] != "current"]
            chosen[nt] = min(CASUAL, key=lambda cs: own_err([x for x in other if x["label"] == "cas%.2f" % cs])) if other else 0.04
        pooled = min(CASUAL, key=lambda cs: own_err([x for x in xb if x["label"] == "cas%.2f" % cs]))
        L.append("Casual share held out by night: %s; on all nights: %.2f." % (", ".join("%s %.2f" % (d[5:], c) for (d, g), c in zip(nts, [chosen[n] for n in nts])), pooled))
        # the bar: the held-out choice per night against the current field
        tw = {k: [0, 0, 0] for k, _ in TARGET + OTHER}
        per = []
        for nt in nts:
            cur = [x for x in xb if (x["date"], x["g"]) == nt and x["label"] == "current"]
            new = [x for x in xb if (x["date"], x["g"]) == nt and x["label"] == "cas%.2f" % chosen[nt]]
            if not cur or not new:
                continue
            line = []
            for k, _ in TARGET + OTHER:
                dc = [dist(x, k) for x in cur]; dn = [dist(x, k) for x in new]
                dc = [v for v in dc if v is not None]; dn = [v for v in dn if v is not None]
                if not dc or not dn:
                    continue
                c_, n_ = S.mean(dc), S.mean(dn)
                tw[k][0 if n_ < c_ - 1e-9 else 1 if n_ > c_ + 1e-9 else 2] += 1
                line.append(k)
            per.append(nt)
        L.append("")
        L.append("| Measure | toward real | away | same | real / current / new (band means) |")
        L.append("|---|---|---|---|---|")
        allnew = [x for x in xb if x["label"] == "cas%.2f" % pooled]
        for k, name in TARGET + OTHER:
            cur = [x for x in xb if x["label"] == "current"]
            if k in ("u5", "m", "t"):
                rc = S.mean(x[k] for x in cur if x.get(k)); rn = S.mean(x[k] for x in allnew if x.get(k)) if allnew else float("nan")
                vals = "1.00 / %.2f / %.2f" % (rc, rn)
            else:
                vals = "%.2f / %.2f / %.2f" % (S.mean(x["real"][k] or 0 for x in cur), S.mean(x["sim"][k] or 0 for x in cur), S.mean(x["sim"][k] or 0 for x in allnew) if allnew else float("nan"))
            L.append("| %s%s | %d | %d | %d | %s |" % (name, "" if (k, name) in TARGET else " (not targeted)", tw[k][0], tw[k][1], tw[k][2], vals))
        need = 6 if b == "Large" else max(1, len(per) // 2 + 1)
        ok_t = all(tw[k][0] >= need for k, _ in TARGET)
        ok_o = all(tw[k][1] < need for k, _ in OTHER)
        L.append("")
        L.append("Bar (%d nights, need %d toward real on each targeted measure, and no other measure worse on %d+): targeted %s; others %s." % (
            len(per), need, need, "PASS" if ok_t else "FAIL (" + ", ".join(n for k, n in TARGET if tw[k][0] < need) + ")",
            "PASS" if ok_o else "FAIL (" + ", ".join(n for k, n in OTHER if tw[k][1] >= need) + ")"))
        L.append("")
    open(os.path.join(a.cache, "bands_score.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def owner(a):
    """The owner's real entries: how often another user held the same 8, against each field's chance of a copy in a
    contest of that size (1 - (1 - f)^(entries - 1), f the lineup's share of the 1,000-lineup field)."""
    R = FS.real_fields(FS.nights(), a.brr)
    F = fields(a)
    out = defaultdict(lambda: [0, 0.0, 0.0, 0])
    for (date, g, cid), x in sorted(R.items()):
        mine = [i for i, u in enumerate(x["U"]) if (u or "").lower().startswith(E.USER)]
        if not mine:
            continue
        cnt = defaultdict(set)
        for L_, u in zip(x["L"], x["U"]):
            cnt[L_].add((u or "").lower())
        sims = {"current": F.get("|".join((date, g, "current"))), "new": F.get("|".join((date, g, label(x["band"], a.casual))))}
        fr = {k: defaultdict(int) for k in sims}
        for k, v in sims.items():
            for L_ in v or []:
                fr[k][tuple(sorted(L_))] += 1
        for i in mine:
            L_ = x["L"][i]
            real = any(u for u in cnt[L_] if not u.startswith(E.USER))
            o = out[(x["band"])]
            o[0] += 1; o[3] += real
            for j, k in enumerate(("current", "new")):
                if sims[k]:
                    f = fr[k][tuple(sorted(L_))] / len(sims[k])
                    o[1 + j] += 1 - (1 - f) ** max(0, x["entries"] - 1)
    for b, (n, ec, en, real) in out.items():
        print("%s: the owner's entries %d; duplicated by another user, real %d (%.1f%%); expected in the current field %.1f (%.1f%%), in the new %.1f (%.1f%%)" % (
            b, n, real, 100 * real / n, ec, 100 * ec / n, en, 100 * en / n))


def banks(a):
    """The field study's bank test (scripts/dk_field_study.py banks: each night's largest graded contest with a payout
    table, one rule-free bank cut against each field, the kept lineups on real results), the current field against
    the Large band's new one (every such contest is Large)."""
    d = os.path.join(a.cache, "banks_bands_%.2f" % a.casual)
    os.makedirs(d, exist_ok=True)
    F = fields(a)
    lab = label("Large", a.casual)
    sub = {k: v for k, v in F.items() if k.endswith("|current") or k.endswith("|" + lab)}
    json.dump(sub, open(os.path.join(d, "fields.json"), "w"))
    ns = argparse.Namespace(out=d, brr=a.brr, mirror=a.mirror, labels="Large=" + lab, bank=2000, keep=200, nights=500, cut=0.25)
    FS.banks(ns)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("build", "score", "owner", "banks"):
        p = sub.add_parser(c); p.add_argument("--brr", default=os.path.join(HERE, "..", "..", "battle-royale-research")); p.add_argument("--cache", required=True)
        p.add_argument("--casual", type=float, default=0.04); p.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    a = ap.parse_args()
    {"build": build, "score": score, "owner": owner, "banks": banks}[a.cmd](a)
