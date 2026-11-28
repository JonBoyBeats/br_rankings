"""Correction 2026-11-28: section 11 (results by contest type and slate type) re-cut on the unified contest types
(scripts/dk_contest_type.py). The owner's real entries (eval.csv, who = mine), under the OLD by-size split (entries
as the size, as the review did) and the NEW page profile (the lobby size, field_lineups.csv's size, as the page reads it)."""
import csv, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "scripts"))
import dk_contest_type as T
D = os.path.join(HERE, "..")
R = [r for r in csv.DictReader(open(os.path.join(D, "eval.csv"))) if r["who"] == "mine"]
lobby = {}
for r in csv.DictReader(open(os.path.join(D, "field_lineups.csv"))):
    lobby.setdefault(r["contest_id"], int(r["size"]))
def old(name, n):
    if re.search("qualifier|satellite", name, re.I) or n < 100: return "qualifier / small"
    if re.search("pull up jumper", name, re.I) or 100 <= n < 800: return "flagship"
    return "main"
def new(r):
    t = T.contest_type(r["contest"], lobby.get(r["contest_id"]) or int(r["entries"]))
    return "qualifier / small" if t == "qualifier" else t
groups = defaultdict(set)
for r in R: groups[r["date"]].add(r["draft_group"])
def slate_type(r):
    gs = sorted(groups[r["date"]])
    return "single-slate day" if len(gs) == 1 else ("early" if r["draft_group"] == gs[0] else "main")
def table(label, key):
    agg = defaultdict(lambda: [0.0, 0.0, 0, set()])
    for r in R:
        a = agg[key(r)]; a[0] += float(r["fees"]); a[1] += float(r["dollars_back"]); a[2] += int(r["lineups"]); a[3].add(r["draft_group"])
    print("== " + label)
    for k, (f, b, n, s) in sorted(agg.items()):
        print("  %-18s fees $%8.2f  back $%8.2f  net %+9.2f  ROI %+6.1f%%  entries %4d  slates %2d" % (k, f, b, b - f, 100 * (b - f) / f, n, len(s)))
table("by contest type, OLD (by size)", lambda r: old(r["contest"], int(r["entries"])))
table("by contest type, NEW (page profile)", new)
table("by slate type (unchanged by the re-label)", slate_type)
moved = sorted({(r["contest"], int(r["entries"]), old(r["contest"], int(r["entries"])), new(r)) for r in R if old(r["contest"], int(r["entries"])) != new(r)})
print("our contests that change type: %d" % len(moved))
for m in moved: print("   ", m)
