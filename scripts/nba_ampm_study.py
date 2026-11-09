"""Your AM against PM teams, by pod size: is a weaker AM tail a weaker draft or the night's luck?

Each of your teams in every contest on file (the measures' my_teams), placed AM or PM by the lock nearest its draft
time (scripts/nba_field.py's window; no Lock AM that night: PM). Per team, summed over its six picks, by closing-ADP
round band that night (band = ceil(closing ADP / pod size)):

  ETR value   ETR's last number before lock minus the band's average ETR number: how good the picks were on the
              projection, known before tip
  FPOE        actual points minus the band's average actual points: how they scored
  ADP gained  morning ADP minus closing ADP: how far the picks went earlier by lock (closing line value)
  Q at AM     picks Questionable or otherwise tagged at Lock AM

Equal ETR value with lower FPOE reads as the night's scoring, not the draft. The 2026-11-09 run is in
analysis/nba/report/field_studies.md (section 7).

  python3 scripts/nba_ampm_study.py
"""
import collections, csv, glob, math, os, statistics as st, sys

sys.path.insert(0, os.path.dirname(__file__))
import nba_field as F   # noqa: E402  the measures, the lock times and the AM/PM window, as the Field section reads them


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    rows = collections.defaultdict(list)
    for d in F.nights():
        am, pm = F.locks(d)
        paths = glob.glob(os.path.join(F.R.DAILY, "%s_*_main.csv" % d))
        if not paths:
            continue
        rec = {r["player_id"]: r for r in csv.DictReader(open(paths[0]))}
        for c in F.measures(d)["contests"]:
            pod, n = c["pod_size"], c["entries"]
            band = lambda r: math.ceil(num(r["adp_close"]) / pod)
            act, etr = collections.defaultdict(list), collections.defaultdict(list)
            for r in rec.values():
                if num(r["adp_close"]) is None:
                    continue
                if num(r["actual"]) is not None:
                    act[band(r)].append(num(r["actual"]))
                if num(r["etr_last"]) is not None:
                    etr[band(r)].append(num(r["etr_last"]))
            for t in c.get("my_teams") or []:
                ps = [rec[p] for p in t["picks"] if p in rec and num(rec[p]["adp_close"]) is not None]
                rows[(pod, F.window(F.iso(t["drafted_at"]), am, pm))].append({
                    "night": d, "top10": t["place"] <= math.ceil(n / 10), "top1": t["place"] <= math.ceil(n / 100),
                    "fpoe": sum(num(r["actual"] or 0) - st.mean(act[band(r)]) for r in ps if act[band(r)]),
                    "etr": sum(num(r["etr_last"]) - st.mean(etr[band(r)]) for r in ps if num(r["etr_last"]) is not None and etr[band(r)]),
                    "clv": sum(num(r["adp_am"]) - num(r["adp_close"]) for r in ps if num(r["adp_am"]) is not None),
                    "q": sum(1 for r in ps if r["injury_am"])})
    print("| Drafters | Window | Teams | Nights | Top 10% (x field) | Top 1% (x field) | ETR value | FPOE | ADP gained | Q at AM |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for (pod, w), v in sorted(rows.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
        m = lambda k: st.mean(x[k] for x in v)
        print("| %d | %s | %d | %d | %.2f | %.2f | %+.1f | %+.1f | %+.1f | %.2f |" % (
            pod, w.upper(), len(v), len({x["night"] for x in v}), m("top10") / 0.10, m("top1") / 0.01, m("etr"), m("fpoe"), m("clv"), m("q")))


if __name__ == "__main__":
    main()
