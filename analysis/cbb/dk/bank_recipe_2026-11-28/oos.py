"""Out-of-sample check: the shipped checks weights were fit on the graded slates through 2026-11-23 (checks_weights_2026-11-24),
so 1a and 1b on those slates are partly in-sample. Re-reads greens_player.out and score.out and splits the slates."""
import re, statistics as St, math
def ms(v): return "%+.3f ± %.3f (%d slates, ahead %d)" % (St.mean(v), St.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 0 for x in v)) if len(v) > 1 else str(v)
rows = [l.split() for l in open("greens_player.out") if re.match(r"2026-11-\d\d_\d+ ", l) and "no matched" not in l]
for lab, test in (("fit slates (to 11-23)", lambda d: d <= "2026-11-23"), ("after the fit (11-24 on)", lambda d: d >= "2026-11-24")):
    R = [r for r in rows if test(r[0][:10])]
    print("1a", lab, "| 5x", ms([float(r[5]) for r in R]), "| act-proj", ms([float(r[6]) for r in R]), "| DK/$1k", ms([float(r[7]) for r in R]))
per = {}
for l in open("score.out"):
    m = re.match(r"\s+(2026-11-\d\d) (\d+) .* ([-\d.]+)$", l)
    if m:
        per.setdefault((m.group(1), m.group(2)), []).append(float(m.group(3)))
for lab, test in (("fit slates (to 11-23)", lambda d: d <= "2026-11-23"), ("after the fit (11-24 on)", lambda d: d >= "2026-11-24")):
    print("1b", lab, "| GREENS - plain finish pct", ms([St.mean(v) for (d, g), v in per.items() if test(d)]))
