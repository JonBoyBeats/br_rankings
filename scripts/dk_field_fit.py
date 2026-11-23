"""The field fit, nightly (2026-11-23, the operator's approval of the lock review): every graded contest's real field
against the simulated field as it stood at lock (the contest's band field from the mirror's dk_cbb_field.json, else
its one field), so the page can say how far the field is from what people play, and the Friday review can refit it.

Rows (analysis/cbb/dk/field_fit_rows.csv, one per graded contest, kept across runs: the nightly workflow's mirror
holds a week) and the summary (analysis/cbb/dk/field_fit.json) over the last WINDOW graded nights, per contest-size
band (Large 300+ entries, Medium 30-299, Small under 30):

  {"generated_at", "window_nights", "nights": [date_draftgroup...],
   "bands": {"Large": {"contests", "nights", "dup": {"real", "sim"}, "punt": {"real", "sim"}, "u5": real / field
             ownership of the players the field had under 5%, "trio_lift": {"real", "sim"}, "field": the field's
             label at lock ("band" or "one")}, "Medium": {...}, "Small": {...}}}

dup: % of entries holding a lineup another user entered; punt: % of entries with a sub-$3,500 player; trio_lift: the
top-20 trios' co-occurrence over the product of their players' ownership (dk_field_study.lifts).

  python3 scripts/dk_field_fit.py --mirror ../br-adp-mirror
"""
import argparse, csv, datetime as dt, json, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E                    # noqa: E402
import dk_field_study as FS            # noqa: E402
import dk_sit as K                     # noqa: E402  (lock_doc)

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
ROWS, OUT = os.path.join(DK, "field_fit_rows.csv"), os.path.join(DK, "field_fit.json")
WINDOW = 14
COLS = ["date", "draft_group", "contest_id", "band", "entries", "field", "dup_real", "dup_sim", "punt_real", "punt_sim", "u5", "trio_lift_real", "trio_lift_sim"]


def players_at_lock(sl):
    return {k: dict(v) for k, v in (sl.get("players") or {}).items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror")); a = ap.parse_args()
    old = list(csv.DictReader(open(ROWS))) if os.path.exists(ROWS) else []
    have = {r["contest_id"] for r in old}
    new = []
    for (date, g), cids in FS.nights().items():
        todo = {c: n for c, n in cids.items() if c not in have and os.path.exists(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c))}
        if not todo:
            continue
        sl, start = K.lock_doc(a.mirror, "dk_cbb_morning.json", date, g)
        fd, _ = K.lock_doc(a.mirror, "dk_cbb_field.json", date, g, start)
        if not sl or not fd or not fd.get("field"):
            print("field fit: no lock-time field for %s %s on the mirror; skipped" % (date, g)); continue
        players = players_at_lock(sl)
        names = {}
        for k, r in players.items():
            names.setdefault(r.get("name"), []).append(k)
        byname = {nm: v[0] for nm, v in names.items() if len(v) == 1}
        for cid in todo:
            L, U, total = E.real_field(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid), byname)
            if len(L) < 2:
                continue
            b = FS.band(total)
            bf = (fd.get("bands") or {}).get(b.lower())
            F, own, lab = (bf["field"], bf["own"], "band") if bf and bf.get("field") else (fd["field"], fd.get("own") or {}, "one")
            n = min(len(L), 1000)
            rm, rown = FS.measures(L, U, players, n)
            sm, _ = FS.measures([tuple(sorted(x)) for x in F], None, players, n)
            gaps, _ = FS.player_gaps(rown, own, players)
            new.append({"date": date, "draft_group": g, "contest_id": cid, "band": b, "entries": total, "field": lab,
                        "dup_real": round(rm["dup"], 2), "dup_sim": round(sm["dup"], 2), "punt_real": round(rm["punt1"], 2), "punt_sim": round(sm["punt1"], 2),
                        "u5": gaps.get("own <5") if gaps.get("own <5") is not None else "", "trio_lift_real": round(rm["lift_trios"] or 0, 3), "trio_lift_sim": round(sm["lift_trios"] or 0, 3)})
            print("field fit: %s %s %s (%s, %d entries): dup %.1f / %.1f%%, punt %.1f / %.1f%%" % (date, g, cid, b, total, rm["dup"], sm["dup"], rm["punt1"], sm["punt1"]))
    rows = old + new
    if new:
        with open(ROWS, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    nights = sorted({(r["date"], r["draft_group"]) for r in rows})[-WINDOW:]
    keep = [r for r in rows if (r["date"], r["draft_group"]) in set(nights)]
    num = lambda v: float(v) if v not in ("", None) else None
    bands = {}
    for b, _, _ in FS.BANDS:
        xs = [r for r in keep if r["band"] == b]
        if not xs:
            continue
        m = lambda k: round(S.mean(num(r[k]) for r in xs if num(r[k]) is not None), 2) if any(num(r[k]) is not None for r in xs) else None
        bands[b] = {"contests": len(xs), "nights": len({(r["date"], r["draft_group"]) for r in xs}),
                    "dup": {"real": m("dup_real"), "sim": m("dup_sim")}, "punt": {"real": m("punt_real"), "sim": m("punt_sim")},
                    "u5": m("u5"), "trio_lift": {"real": m("trio_lift_real"), "sim": m("trio_lift_sim")},
                    "field": "band" if any(r["field"] == "band" for r in xs) else "one"}
    json.dump({"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "window_nights": WINDOW,
               "nights": ["%s_%s" % n for n in nights], "bands": bands}, open(OUT, "w"), indent=1)
    print("field fit: %d contests on file, %d new; field_fit.json over %d nights" % (len(rows), len(new), len(nights)))


if __name__ == "__main__":
    main()
