"""The shadow lab's grade (scripts/dk_eval.py lab): python3 tests/dk_lab.py

A made-up night in a temporary folder: three teams, a bank with each experiment's treatment and control lineups
(one lineup drawn under both a Draw the 9 cell and its L0 U0, for the shared credit), one graded contest of 150
entries scoring 0..149. Each arm's paired difference is recomputed here from the definitions, not read back."""
import csv, json, os, shutil, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_eval as E  # noqa: E402

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or not info else "  " + str(info)))
    ok += bool(cond)
    bad += not cond


tmp = tempfile.mkdtemp()
try:
    for k in ("builds", "standings"):
        os.makedirs(os.path.join(tmp, k))
    E.DK, E.BUILDS, E.STANDINGS = tmp, os.path.join(tmp, "builds"), os.path.join(tmp, "standings")
    E.EVAL, E.LAB, E.LAB_EVAL = os.path.join(tmp, "eval.csv"), os.path.join(tmp, "lab.json"), os.path.join(tmp, "lab_eval.csv")
    reg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "cbb", "dk", "lab.json")))
    for e in reg["experiments"]:
        e.pop("results", None)
    json.dump(reg, open(E.LAB, "w"))
    team = {}
    for i in range(1, 25):
        team[str(i)] = "A" if i <= 8 else "B" if i <= 16 else "C"
    pts = {str(i): float(i) for i in range(1, 25)}           # player i scores i
    A, B, Cc = [str(i) for i in range(1, 9)], [str(i) for i in range(9, 17)], [str(i) for i in range(17, 25)]
    pool = [A[:5] + B[:3],          # 0 STACK A@B 2+1 (2 A)       score 1..5 + 9..11 = 45
            A[3:8] + Cc[:3],        # 1 game group: 2+ from A      4..8 + 17..19 = 84
            Cc[:8],                 # 2 SCANFLOOR                  17..24 = 164
            B[:8],                  # 3 at least 3 of (group)       9..16 = 100
            A[:4] + Cc[4:8],        # 4 I L0 U0                    1..4 + 21..24 = 100
            B[4:8] + Cc[:4],        # 5 I L0.1 U0                  13..16 + 17..20 = 132
            A[4:8] + B[:4],         # 6 both I L0 U0 and I L0.1 U0 5..8 + 9..12 = 68
            B[2:6] + Cc[2:6],       # 7 GREENS A@B (its rule is a template-5 'at least N of')  11..14 + 19..22 = 130
            A[:5] + Cc[5:8],        # 8 variant of #1: shares 5 with its parent, lineup 0 (the tag resolves)
            A[:3] + Cc[4:8] + B[7:8],   # 9 variant of #3, its parent stored (variant_of): lineup 4
            A[5:8] + B[3:8]]        # 10 variant of #2: shares under 5 with lineup 1, nothing stored: no parent
    tags = [["STACK A@B 2+1 (2 A)"], ["At least 2 from A"], ["SCANFLOOR"], ["at least 3 of X, Y, Z"], ["I L0 U0"], ["I L0.1 U0"], ["I L0 U0", "I L0.1 U0"], ["salary >= 49000 + GREENS A@B"], ["variant of #1"], ["variant of #3"], ["variant of #2"]]
    settings = {"At least 2 from A": {"conds": [{"type": "min", "ids": A, "n": 2, "label": "At least 2 from A"}]},
                "at least 3 of X, Y, Z": {"conds": [{"type": "min", "ids": B[:3], "n": 3, "label": "at least 3 of X, Y, Z"}]},
                "salary >= 49000 + GREENS A@B": {"conds": [{"type": "min", "ids": B[2:6], "n": 2, "label": "at least 2 of P11, P12, P13, P14", "greens": {"game": "A@B", "tag": "GREENS A@B"}}]},
                "STACK A@B 2+1 (2 A)": {"conds": [{"type": "min", "ids": A, "n": 2, "stackq": {"shape": "2+1"}}, {"type": "min", "ids": B, "n": 1, "stackq": {"shape": "2+1"}}]}}
    score = [sum(pts[i] for i in L) for L in pool]
    n, field = 150, list(range(150))                        # the field scores 0..149
    pct = lambda s: 100.0 * (n - sum(f > s for f in field)) / n
    cols = ["date", "draft_group", "contest_id", "contest", "who"]
    with open(E.EVAL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for day, g, cid in (("2026-11-20", "900", "11"), ("2026-11-24", "901", "12"), ("2026-11-25", "902", "13")):
            w.writerow({"date": day, "draft_group": g, "contest_id": cid, "contest": "Test contest", "who": "mine"})
            keep = list(range(len(pool)))       # top tenth: the best 10 of 11 by board value, lineup 10 the worst
            json.dump({"day": day, "draft_group": g, "pool": pool, "tags": tags, "final": keep, "tag_settings": settings, "saved_at": day, "variant_of": {"9": 4},
                       "cut_state": {"keep": keep, "board": {"values": [100 - k for k in keep]}, "variantRounds": 1}},
                      open(os.path.join(E.BUILDS, "dk_bank_%s_%s.json" % (day, g)), "w"))
            with open(os.path.join(tmp, "%s_%s.csv" % (day, g)), "w", newline="") as rf:
                rw = csv.DictWriter(rf, fieldnames=["date", "draft_group", "dk_id", "name", "team", "actual_dk"])
                rw.writeheader()
                for i in range(1, 25):
                    rw.writerow({"date": day, "draft_group": g, "dk_id": str(i), "name": "P%d" % i, "team": team[str(i)], "actual_dk": pts[str(i)]})
            with open(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid), "w", newline="") as sf:
                sw = csv.DictWriter(sf, fieldnames=["Rank", "EntryId", "EntryName", "Points", "Lineup"])
                sw.writeheader()
                for k, p in enumerate(sorted(field, reverse=True)):
                    sw.writerow({"Rank": k + 1, "EntryId": str(1000 + k), "EntryName": "u%d" % k, "Points": p, "Lineup": ""})
    E.lab()
    out = json.load(open(E.LAB))
    ex = {e["id"]: e["results"]["arms"] for e in out["experiments"]}
    want_a = pct(score[0]) - (pct(score[1]) + pct(score[3])) / 2       # 3 is a game group too (B's players); 7, GREENS, is out of the control
    want_b = pct(score[2]) - pct(score[3])                              # b: 'at least N of' rules, GREENS lineups out
    want_d = pct(score[7]) - pct(score[3])                              # d: the hand-picked group rule only
    want_ep = (pct(score[8]) + pct(score[9])) / 2 - (pct(score[0]) + pct(score[4])) / 2      # e: variant against its own parent (10 has none)
    want_er = (pct(score[8]) + pct(score[9]) + pct(score[10])) / 3 - sum(pct(score[k]) for k in range(8)) / 8      # e: every variant against the top tenth's others
    want_c = (pct(score[5]) + pct(score[6])) / 2 - (pct(score[4]) + pct(score[6])) / 2      # lineup 6 in both: shared credit
    a, b, c, d = ex["a"]["all"], ex["b"]["all"], ex["c"]["L0.1 U0"], ex["d"]["all"]
    ep, er = ex["e"]["vs parents"], ex["e"]["vs rest of top tenth"]
    check("e vs parents: each variant against its own parent, the stored link first, else the tag's #N when it shares 5+ players; an unresolved one left out",
          ep["slates"] and abs(ep["slates"][0]["diff"] - round(want_ep, 2)) < 1e-9 and ep["slates"][0]["t_n"] == 2 and ep["slates"][0]["c_n"] == 2, (ep, want_ep))
    check("e vs rest of top tenth: every kept variant against the top tenth's non-variants (the board's best max(10, 10%))",
          er["slates"] and abs(er["slates"][0]["diff"] - round(want_er, 2)) < 1e-9 and er["slates"][0]["t_n"] == 3 and er["slates"][0]["c_n"] == 8, (er, want_er))
    n0 = ep["slates"][0]
    check("e per night: rounds run, variants kept, the top tenth's size, its variants and their share, how the parent was found",
          (n0["rounds"], n0["variants_kept"], n0["top_tenth"], n0["top_tenth_variants"], n0["top_tenth_share"], n0["parent_link"]) == (1, 3, 10, 2, 0.2, "stored"), n0)
    check("a: STACK lineups against the same game's game-group lineups (2+ from A; 3 of B's players), paired by slate", a["slates"] and abs(a["slates"][0]["diff"] - round(want_a, 2)) < 1e-9, (a, want_a))
    check("b: SCANFLOOR lineups against group-rule ('at least N of') lineups", b["slates"] and abs(b["slates"][0]["diff"] - round(want_b, 2)) < 1e-9, (b, want_b))
    check("a and b: a GREENS lineup (its rule an 'at least N of' over one game's players) is in neither control", a["slates"][0]["c_n"] == 2 and b["slates"][0]["c_n"] == 1,
          (a["slates"][0]["c_n"], b["slates"][0]["c_n"]))
    check("c: each cell against the same idea's L0 U0; a lineup under both counts for both (shared credit)",
          c["slates"] and abs(c["slates"][0]["diff"] - round(want_c, 2)) < 1e-9 and c["slates"][0]["t_n"] == 2 and c["slates"][0]["c_n"] == 2, (c, want_c))
    check("d: GREENS lineups against the operator's own group rules (no GREENS / STACK / SCANFLOOR in the tag)", d["slates"] and abs(d["slates"][0]["diff"] - round(want_d, 2)) < 1e-9 and d["slates"][0]["c_n"] == 1, (d, want_d))
    check("slates before registration are a look-back, not counted: 2 counted (11-24, 11-25), 1 look-back (11-20)",
          all(x["nights"] == 2 and len(x["lookback"]) == 1 and x["lookback"][0]["date"] == "2026-11-20" for x in (a, b, c, d, ep, er)), [(x["nights"], len(x["lookback"])) for x in (a, b, c, d, ep, er)])
    check("the registry's definitions are kept as written; only results and updated_at change",
          [{k: v for k, v in e.items() if k != "results"} for e in out["experiments"]] == reg["experiments"] and out["method"] == reg["method"])
    rows = list(csv.DictReader(open(E.LAB_EVAL)))
    check("lab_eval.csv: a row per slate, experiment arm and contest (3 slates x 6 arms)", len(rows) == 18 and sum(r["counted"] == "1" for r in rows) == 12, len(rows))
    # the verdict
    bar = {"ahead_nights": 7, "of": 10, "pooled_over_noise": 2}
    mk = lambda ds: [{"diff": d, "top10_diff": 0.0} for d in ds]
    p = E.lab_summary(mk([3, 4, 2, 5, 3, -1, 4, 3, -2, 4]), 10, bar)
    f1 = E.lab_summary(mk([3, 4, 2, 5, 3, -1, 4, -3, -2, -4]), 10, bar)        # 6 ahead: fails the count
    f2 = E.lab_summary(mk([1, 1, 1, 1, 1, 1, 1, -9, -9, 20]), 10, bar)         # 8 ahead, but the mean under 2 x noise
    r = E.lab_summary(mk([3, 4]), 10, bar)
    check("verdict: ahead on 7+ of 10 and the mean over 2 x SE passes; 6 of 10 fails; 8 of 10 with the mean inside the noise fails; under 10 slates runs",
          p["verdict"] == "pass" and p["ahead"] == 8 and f1["verdict"] == "fail" and f2["verdict"] == "fail" and f2["ahead"] == 8 and r["verdict"] == "running", (p, f1, f2, r))
    v = E.lab_summary(mk([3, 4, 2, 5, 3, -1, 4, 3, -2, 4, -50]), 10, bar)
    check("verdict on the first 10 slates; an 11th is counted in nights but doesn't change it", v["verdict"] == "pass" and v["nights"] == 11 and v["counted_for_verdict"] == 10, v)
finally:
    shutil.rmtree(tmp)
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
