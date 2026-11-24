"""The ownership grade's chalk band and the late-swap standings logger (scripts/dk_eval.py owngrade / ownsync):
python3 tests/dk_own_grade.py

Hand-made numbers: the chalk band's MAE, off-by-10+ share and bias recomputed here; a made-up night of three games
whose late-swap standings reveal two games (left for later), then all three (logged once, with entries), and a
second file added at the same moment as the whole one (logged too)."""
import csv, io, os, shutil, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_eval as E  # noqa: E402

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or not info else "  " + str(info)))
    ok += bool(cond)
    bad += not cond


# 1. the chalk band: max(ours, actual) >= 15 picks (20, 40), (31, 20), (10, 16); (3, 1) and (8, 12) stay out
pairs = [(20, 40), (31, 20), (10, 16), (3, 1), (8, 12)]
c = E.chalk_stats(pairs)
errs = [20, 11, 6]
check("chalk band: the players with max(ours, actual) 15+, MAE, off by 10+, bias and its share of all error",
      c["n"] == 3 and c["all"] == 5 and abs(c["mae"] - sum(errs) / 3) < 1e-9 and abs(c["off"] - 2 / 3) < 1e-9 and
      abs(c["off20"] - 1 / 3) < 1e-9 and abs(c["bias"] - (20 - 11 + 6) / 3) < 1e-9 and abs(c["err_share"] - 37 / 43) < 1e-9, c)
check("chalk band: none in the band gives None", E.chalk_stats([(3, 1), (8, 12)]) is None)
rows = [dict(date="2026-11-30", draft_group="1", contest_id=str(i // 5), p=p, a=a, n=n)
        for i, ((p, a), n) in enumerate(zip(pairs * 2, [500] * 5 + [20] * 5))]
lines = E.own_grade_lines(rows)
check("the grade's lines lead with the chalk band, then by size (Large, Small here), by slate, the secondary lens and the rule",
      lines[0].startswith("Ownership grade, the chalk band") and any(x.strip().startswith("Large") for x in lines) and
      any(x.strip().startswith("Small") for x in lines) and not any(x.strip().startswith("Medium") for x in lines) and
      any("secondary:" in x for x in lines) and "held out by slate" in lines[-1], "\n".join(lines))

# 2. ownsync: three games played; a file revealing two is left, one revealing all three is logged
rec = [{"date": "2026-11-30", "draft_group": "1", "dk_id": str(k), "name": nm, "game": g, "salary": "5000", "own": str(o), "min": m}
       for k, (nm, g, o, m) in enumerate([("A One", "X@Y", 30, "30"), ("B Two", "X@Y", 10, "25"), ("C Three", "Z@W", 20, "28"),
                                          ("D Four", "Q@R", 15, "31"), ("E Five", "Q@R", 5, "0")])]


def stand(players, n=3):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Rank", "EntryId", "EntryName", "TimeRemaining", "Points", "Lineup", "", "Player", "Roster Position", "%Drafted", "FPTS"])
    names = list(players.items())
    for i in range(max(n, len(names) * 2)):
        entry = [str(i + 1), str(1000 + i), "user%d" % i, "0", str(100 - i), "G A One"] if i < n else [""] * 6
        if i < 2 * len(names):
            nm, pct = names[i // 2]
            entry += ["", nm, "G" if i % 2 == 0 else "UTIL", "%.2f%%" % (pct / 2), "10"]
        w.writerow(entry)
    return out.getvalue()


partial = {"stand": [{"name": "contest-standings-198000111.csv", "at": 1000, "text": stand({"A One": 40, "C Three": 22})}]}
have = set()
r0, n0 = E.ownsync_rows(partial, rec, have)
check("ownsync: standings from before every game started (2 of 3 games) are left for later", not r0 and "198000111" not in have and "2 of 3" in n0[0], n0)
whole = {"stand": [{"name": "contest-standings-198000111.csv", "at": 5000, "text": stand({"A One": 40, "C Three": 22, "D Four": 9, "E Five": 1}, n=7)},
                   {"name": "contest-standings-198000222.csv", "at": 5030, "text": stand({"A One": 50}, n=4)}]}
r1, n1 = E.ownsync_rows(whole, rec, have)
by = {(r["contest_id"], r["name"]): r for r in r1}
check("ownsync: once every game is revealed, each player's G + UTIL ownership is logged with the contest's entries and our projection",
      by.get(("198000111", "A One"), {}).get("own_actual") == 40 and by[("198000111", "A One")]["entries"] == 7 and by[("198000111", "D Four")]["own_proj"] == "15"
      and len([r for r in r1 if r["contest_id"] == "198000111"]) == 4, r1)
check("ownsync: a file added at the same moment as a whole one is logged too (its own players only)",
      [r["name"] for r in r1 if r["contest_id"] == "198000222"] == ["A One"] and by[("198000222", "A One")]["entries"] == 4, r1)
r2, _ = E.ownsync_rows(whole, rec, have)
check("ownsync: a contest already logged is not appended again", not r2)

# 3. the file round trip: ownsync's rows written, then nightly's own_done set reads them
tmp = tempfile.mkdtemp()
try:
    E.OWN_EVAL = os.path.join(tmp, "own_eval.csv")
    with open(E.OWN_EVAL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=E.OWN_COLS)
        w.writeheader()
        w.writerows(r1)
    back = E.read(E.OWN_EVAL)
    check("own_eval.csv carries the entries column and the contests ownsync logged",
          {r["contest_id"] for r in back} == {"198000111", "198000222"} and all(r["entries"] for r in back) and E.OWN_COLS[-1] == "entries")
finally:
    shutil.rmtree(tmp)

print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
