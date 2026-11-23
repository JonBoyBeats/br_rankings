"""The field by contest size, with the ownership rules inside it (2026-11-23, the operator's approval of the lock review:
"retest inside the field"). Builds on scripts/dk_field_study.py (its measures, real fields and cached builds).

Each band's field: the field study's fitted chalk style (DraftKings' average, noise .08) at the band's share (Large
0.2, Medium 0.3, Small 0.4: Small the operator's prior, unfitted), the rest the original style, and per variant:
  casual   a style share at noise CASUAL_NOISE (w 0.5): lifts the players we project near 0 (the floor: real ownership
           under 5% ran ~2x ours), fitted per band held out by night on the ownership bands over CASUAL, and over
           CASUAL + CASUAL_EXT when the pooled choice sits on CASUAL's edge
  big      "coming off a big game" x1.22 on the field projection (battle-royale-research dk_cbb_field.big_game)
  nopunt   the no-punt pool (dk_cbb_field.no_punts)
Variants (VARIANTS): "nopunt" casual + big + no-punt pool (the first retest, cc6f552: failed); the clean retest with
punts kept in the pool: "a" casual only, "b" big only, "c" both, "d" the band's chalk only (the baseline).

The realism bar (the operator's, 2026-11-23): a change is accepted when each targeted measure (duplication, the under-5%
ratio, punts under $3.5k, the top trio and trio lift, salary at the cap, 3+ from a team) moves toward the real fields on
most nights (Large 6+ of 9; Medium most of its nights; Small report only), the 5-20% and 20%+ ratios are not worse on
most nights, and same-seed rule-free banks cut against it are not worse than against the current field.

  python3 scripts/dk_field_bands.py build --cache DIR [--variants a,b,c,d]     (fields, cached with the study's)
  python3 scripts/dk_field_bands.py score --cache DIR [--variants ...]         (measures, fit, the bar; the choices)
  python3 scripts/dk_field_bands.py owner --cache DIR [--variants ...]         (the owner's duplication, real vs fields)
  python3 scripts/dk_field_bands.py banks --cache DIR [--variants ...]         (the bank test, Large)
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
CASUAL_EXT = (0.16, 0.20)
CASUAL_NOISE = 0.8
VARIANTS = {"nopunt": {"big": True, "punts": False, "casual": True, "ext": False, "name": "casual + big-game, no-punt pool (cc6f552)"},
            "a": {"big": False, "punts": True, "casual": True, "ext": True, "name": "(a) casual only"},
            "b": {"big": True, "punts": True, "casual": False, "ext": False, "name": "(b) big-game only"},
            "c": {"big": True, "punts": True, "casual": True, "ext": True, "name": "(c) casual + big-game"},
            "d": {"big": False, "punts": True, "casual": False, "ext": False, "name": "(d) band chalk only"}}


def styles(ca, cs):
    st = [{"share": ca, "w": 0.0, "noise": 0.08, "min_sal": 0}]
    if cs:
        st.append({"share": cs, "w": 0.5, "noise": CASUAL_NOISE, "min_sal": 0})
    st.append({"share": round(1 - ca - cs, 4), "w": 0.5, "noise": 0.25, "min_sal": 0})
    return st


def label(b, cs, big=True, punts=False):
    return "band %s chalk%.1f cas%.2f%s%s" % (b, CHALK[b], cs, " big" if big else "", "" if punts else " nopunt")


def grid(v, ext=True):
    V = VARIANTS[v]
    return (CASUAL + (CASUAL_EXT if V["ext"] and ext else ())) if V["casual"] else (0.0,)


def vlabels(v, b, ext=True):
    V = VARIANTS[v]
    return [label(b, cs, V["big"], V["punts"]) for cs in grid(v, ext)]


def _job(args):
    brr, date, g, lab, st, q, punts, big = args
    sys.path.insert(0, os.path.join(brr, "scripts"))
    import numpy as np
    import dk_cbb_field as fld
    players, _, _ = FS.load_night(brr, date, g)
    L, _ = fld.field(players, np.random.default_rng(7), st, n=1000, q=q, punts=punts, big=big)
    return "|".join((date, g, lab)), [sorted(x) for x in L]


def band_nights(R):
    nb = defaultdict(set)
    for (d, g, cid), x in R.items():
        nb[x["band"]].add((d, g))
    return nb


def build(a):
    R = FS.real_fields(FS.nights(), a.brr)
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import dk_cbb_field as fld
    q = fld.q_factor(os.path.join(FS.DK, "gate.json"))
    nb = band_nights(R)
    path = os.path.join(a.cache, "bands_fields.json")
    have = json.load(open(path)) if os.path.exists(path) else {}
    jobs, seen = [], set()
    for v in a.variants:
        V = VARIANTS[v]
        for cs in grid(v):
            for b in CHALK:
                for d, g in sorted(nb[b]):
                    k = "|".join((d, g, label(b, cs, V["big"], V["punts"])))
                    if k not in have and k not in seen:
                        seen.add(k)
                        jobs.append((cs, (a.brr, d, g, label(b, cs, V["big"], V["punts"]), styles(CHALK[b], cs), q, V["punts"], V["big"])))
    todo = [j for _, j in sorted(jobs, key=lambda t: t[0])]          # the base grid first, the extension last
    print("%d builds" % len(todo), file=sys.stderr)
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
        labs = ["current"] + sorted({lab for v in VARIANTS for lab in vlabels(v, x["band"])})
        for lab in labs:
            key = "|".join((date, g, lab))
            if key not in F:
                continue
            sm, sown = FS.measures([tuple(v) for v in F[key]], None, players, n)
            gaps, mae = FS.player_gaps(rown, sown, players)
            out.append({"date": date, "g": g, "cid": cid, "band": x["band"], "entries": x["entries"], "label": lab,
                        "real": rm, "sim": sm, "u5": gaps.get("own <5"), "m": gaps.get("own 5-20"), "t": gaps.get("own 20+"), "own_mae": mae})
    return out


TARGET = [("dup", "duplication %"), ("u5", "under-5% real/field (to 1)"), ("punt1", "a sub-$3.5k punt %"), ("trio1", "most common trio %"),
          ("lift_trios", "top-20 trio lift"), ("at_cap", "at the cap %"), ("team3", "3+ from a team %")]
OTHER = [("m", "5-20% real/field (to 1)"), ("t", "20%+ real/field (to 1)")]          # not to be worse
SHORT = {"dup": "dup", "u5": "u5", "punt1": "punt", "trio1": "trio", "lift_trios": "lift", "at_cap": "cap", "team3": "3tm", "m": "5-20", "t": "20+"}


def dist(r, k):
    if k in ("u5", "m", "t"):
        return abs(math.log(r[k])) if r.get(k) else None
    return abs((r["sim"].get(k) or 0) - (r["real"].get(k) or 0))


def own_err(xs):
    v = [abs(math.log(x[k])) for x in xs for k in ("u5", "m", "t") if x.get(k)]
    return S.mean(v) if v else 9


def score_variant(v, X, L, summ, choice):
    V = VARIANTS[v]
    L.append("# %s" % V["name"])
    L.append("")
    for b in ("Large", "Medium", "Small"):
        xb = [x for x in X if x["band"] == b]
        nts = sorted({(x["date"], x["g"]) for x in xb})
        have = {x["label"] for x in xb}
        base = [cs for cs, lab in zip(grid(v, False), vlabels(v, b, False)) if lab in have]
        if not base:
            continue
        lab_of = dict(zip(grid(v), vlabels(v, b)))
        pick = lambda xs, G: min(G, key=lambda cs: own_err([x for x in xs if x["label"] == lab_of[cs]]))
        G = base
        pooled = pick(xb, G)
        full = [cs for cs in grid(v) if lab_of[cs] in have]
        edge = len(G) > 1 and pooled == G[-1] and len(full) > len(G)
        if edge:                                         # on the base grid's edge: extend
            G = full
            pooled = pick(xb, G)
        choice.setdefault(v, {})[b] = pooled
        chosen = {}
        for nt in nts:
            other = [x for x in xb if (x["date"], x["g"]) != nt]
            chosen[nt] = pick(other, G) if other else pooled
        L.append("## %s: %d contests, %d nights%s" % (b, len({x["cid"] for x in xb}), len(nts), " (thin: report only; chalk 0.4 is the operator's prior)" if b == "Small" else ""))
        if V["casual"]:
            L.append("Casual share over %s%s, held out by night: %s; on all nights: %.2f." % (
                "/".join("%.2f" % c for c in G), " (extended: .12 was the edge)" if edge else "", ", ".join("%s %.2f" % (d[5:], chosen[(d, g)]) for d, g in nts), pooled))
        tw = {k: [0, 0, 0] for k, _ in TARGET + OTHER}
        per = []
        for nt in nts:
            cur = [x for x in xb if (x["date"], x["g"]) == nt and x["label"] == "current"]
            new = [x for x in xb if (x["date"], x["g"]) == nt and x["label"] == lab_of[chosen[nt]]]
            if not cur or not new:
                continue
            for k, _ in TARGET + OTHER:
                dc = [d for d in (dist(x, k) for x in cur) if d is not None]
                dn = [d for d in (dist(x, k) for x in new) if d is not None]
                if not dc or not dn:
                    continue
                c_, n_ = S.mean(dc), S.mean(dn)
                tw[k][0 if n_ < c_ - 1e-9 else 1 if n_ > c_ + 1e-9 else 2] += 1
            per.append(nt)
        L.append("")
        L.append("| Measure | toward real | away | same | real / current / new (band means) |")
        L.append("|---|---|---|---|---|")
        cur = [x for x in xb if x["label"] == "current"]
        allnew = [x for x in xb if x["label"] == lab_of[pooled]]
        for k, name in TARGET + OTHER:
            if k in ("u5", "m", "t"):
                vals = "1.00 / %.2f / %.2f" % (S.mean(x[k] for x in cur if x.get(k)), S.mean(x[k] for x in allnew if x.get(k)))
            else:
                vals = "%.2f / %.2f / %.2f" % (S.mean(x["real"][k] or 0 for x in cur), S.mean(x["sim"][k] or 0 for x in cur), S.mean(x["sim"][k] or 0 for x in allnew))
            L.append("| %s%s | %d | %d | %d | %s |" % (name, "" if (k, name) in TARGET else " (not to be worse)", tw[k][0], tw[k][1], tw[k][2], vals))
        need = 6 if b == "Large" else max(1, len(per) // 2 + 1)
        miss_t = [SHORT[k] for k, _ in TARGET if tw[k][0] < need]
        miss_o = [SHORT[k] for k, _ in OTHER if tw[k][1] >= need]
        L.append("")
        L.append("Bar (%d nights, need %d toward real on each targeted measure, and neither ownership band worse on %d+): targeted %s; others %s." % (
            len(per), need, need, "PASS" if not miss_t else "FAIL (" + ", ".join(miss_t) + ")", "PASS" if not miss_o else "FAIL (" + ", ".join(miss_o) + ")"))
        L.append("")
        summ.append({"variant": v, "band": b, "nights": len(per), "need": need, "casual": pooled if V["casual"] else None, "edge": edge,
                     "toward": {SHORT[k]: tw[k][0] for k, _ in TARGET}, "worse": {SHORT[k]: tw[k][1] for k, _ in OTHER},
                     "pass": not miss_t and not miss_o, "miss": miss_t + ["%s worse" % m for m in miss_o]})


def score(a):
    path = os.path.join(a.cache, "bands_rows.json")
    X = rows(a)
    json.dump(X, open(path, "w"), default=str)
    L, summ, choice = [], [], {}
    for v in a.variants:
        score_variant(v, X, L, summ, choice)
    L.append("# Summary")
    L.append("")
    L.append("| Variant | Band | Casual | Toward real (dup u5 punt trio lift cap 3tm) | 5-20 / 20+ worse | Bar |")
    L.append("|---|---|---|---|---|---|")
    for s in summ:
        L.append("| %s | %s | %s | %s of %d (need %d) | %d / %d | %s |" % (
            VARIANTS[s["variant"]]["name"], s["band"], "-" if s["casual"] is None else "%.2f%s" % (s["casual"], " (ext)" if s["edge"] else ""),
            " ".join(str(s["toward"][k]) for k in ("dup", "u5", "punt", "trio", "lift", "cap", "3tm")), s["nights"], s["need"],
            s["worse"]["5-20"], s["worse"]["20+"], "PASS" if s["pass"] else "FAIL: " + ", ".join(s["miss"])))
    json.dump({"choice": choice, "summary": summ}, open(os.path.join(a.cache, "bands_choice.json"), "w"), indent=1)
    open(os.path.join(a.cache, "bands_score.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def chosen_label(a, v, b):
    C = json.load(open(os.path.join(a.cache, "bands_choice.json")))["choice"]
    V = VARIANTS[v]
    return label(b, C[v][b] if V["casual"] else 0.0, V["big"], V["punts"])


def owner(a):
    """The owner's real entries: how often another user held the same 8, against each field's chance of a copy in a
    contest of that size (1 - (1 - f)^(entries - 1), f the lineup's share of the 1,000-lineup field)."""
    R = FS.real_fields(FS.nights(), a.brr)
    F = fields(a)
    cols = ["current"] + list(a.variants)
    out = defaultdict(lambda: {"n": 0, "real": 0, **{c: 0.0 for c in cols}})
    for (date, g, cid), x in sorted(R.items()):
        mine = [i for i, u in enumerate(x["U"]) if (u or "").lower().startswith(E.USER)]
        if not mine:
            continue
        cnt = defaultdict(set)
        for L_, u in zip(x["L"], x["U"]):
            cnt[L_].add((u or "").lower())
        sims = {c: F.get("|".join((date, g, "current" if c == "current" else chosen_label(a, c, x["band"])))) for c in cols}
        fr = {}
        for c, v in sims.items():
            fr[c] = defaultdict(int)
            for L_ in v or []:
                fr[c][tuple(sorted(L_))] += 1
        o = out[x["band"]]
        for i in mine:
            L_ = x["L"][i]
            o["n"] += 1
            o["real"] += any(u for u in cnt[L_] if not u.startswith(E.USER))
            for c in cols:
                if sims[c]:
                    f = fr[c][tuple(sorted(L_))] / len(sims[c])
                    o[c] += 1 - (1 - f) ** max(0, x["entries"] - 1)
    L = ["| Band | Owner entries | Real | " + " | ".join("current" if c == "current" else VARIANTS[c]["name"] for c in cols) + " |", "|---" * (len(cols) + 3) + "|"]
    for b in ("Large", "Medium", "Small"):
        if b not in out:
            continue
        o = out[b]
        L.append("| %s | %d | %d (%.1f%%) | %s |" % (b, o["n"], o["real"], 100 * o["real"] / o["n"], " | ".join("%.1f%%" % (100 * o[c] / o["n"]) for c in cols)))
    open(os.path.join(a.cache, "bands_owner.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def banks(a):
    """The field study's bank test (scripts/dk_field_study.py banks: each night's largest graded contest with a payout
    table, one rule-free bank cut against each field, the kept lineups on real results), the current field against
    each variant's Large band field at its chosen casual share (every such contest is Large)."""
    F = fields(a)
    for v in a.variants:
        lab = chosen_label(a, v, "Large")
        d = os.path.join(a.cache, "banks_%s" % lab.replace(" ", "_"))
        os.makedirs(d, exist_ok=True)
        json.dump({k: x for k, x in F.items() if k.endswith("|current") or k.endswith("|" + lab)}, open(os.path.join(d, "fields.json"), "w"))
        ns = argparse.Namespace(out=d, brr=a.brr, mirror=a.mirror, labels="Large=" + lab, bank=2000, keep=200, nights=500, cut=0.25)
        FS.banks(ns)
        print("BANKS %s (%s)" % (v, lab))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("build", "score", "owner", "banks"):
        p = sub.add_parser(c); p.add_argument("--brr", default=os.path.join(HERE, "..", "..", "battle-royale-research")); p.add_argument("--cache", required=True)
        p.add_argument("--variants", default="nopunt,a,b,c,d"); p.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    a = ap.parse_args()
    a.variants = [v for v in a.variants.split(",") if v]
    {"build": build, "score": score, "owner": owner, "banks": banks}[a.cmd](a)
