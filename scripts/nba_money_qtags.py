"""Q-tag study (asked 2026-11-13), results only. Writes analysis/nba/report/money_qtag_study.md.

Same matching as the season studies (scripts/nba_money_season2.py): every night on file, multiples of top-1%, top-10% and cash
finishes over the whole field in the same contest and price quintile, with counts and an 80% range from resampling nights.

  tags          Underdog's own injury tag on each priced player, from the ADP mirror's hourly snapshots (nba_latest.json,
                about :23 past each hour). Each team's draft hour is the snapshot whose ADPs best match its picks
                (nba_contests.draft_times, cached in contests/windows/), so "tagged when the team drafted" is that
                snapshot's tag. Q pick: Questionable, Doubtful or GTD then.
  tier          the ADP tier (a_tier) at the team's window in tier_history.csv: where he was being taken, before any
                Questionable push
  played / sat  his minutes in the night's record (sat: none)
  fall          his ADP at the team's draft hour minus his ADP in the last snapshot before he was first tagged that slate
                (unknown when he was tagged from the slate's first snapshot)
  turn          the team's turn picks read from rosters (nba_money.turn_teams)
  crowd swap    a swapped-in player whose share of pods after swaps is 15+ points above his share at the draft (about the
                top 12% of swap targets); compared with other swap targets in the same contest within 6 projected points
  beneficiary   a player the team drafted in T1-T4 (ADP tier) whose NBA teammate was Q-tagged at the team's draft hour

  python3 scripts/nba_money_qtags.py --mirror ../br-adp-mirror
"""
import argparse, collections, os, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M            # noqa: E402
import nba_money_season as S     # noqa: E402
import nba_money_season2 as S2   # noqa: E402

OUT = os.path.join(M.REP, "money_qtag_study.md")
num = M.num
QTAGS = ("Questionable", "Doubtful", "GTD")
CROWD = 15          # points of pod share, after swaps over the draft
WITHIN = 6          # projected points, crowd swap against other swap targets
HEAD = S2.HEAD3


def snaps_of(N, mirror):
    """{date: [(iso time, {player id: (adp, tag, NBA team)})]} oldest first, from the mirror's history."""
    m = M.D.Mirror(mirror)
    out = {}
    for n in N:
        c = n["contests"][0]
        ss = m.snapshots({"slate_id": c["slate_id"], "lock": M.F.iso(c["cutoff"])})
        out[n["date"]] = [(t.isoformat(), {p["player_id"]: (p.get("adp"), p.get("injury"), p.get("team")) for p in ps}) for t, ps in ss]
    return out


def pre_tag(snaps):
    """{player: ADP in the last snapshot before his first Q tag that slate} (None: tagged from the first snapshot)."""
    out, last = {}, {}
    for _, tab in snaps:
        for p, (adp, tag, _) in tab.items():
            if p in out:
                continue
            if tag in QTAGS:
                out[p] = last.get(p)
            elif adp is not None:
                last[p] = adp
    return out


def sat(n, p):
    r = n["rec"].get(p)
    return r is not None and not (num(r["min"]) or 0) > 0


def section(title, groups, R, order=None, note=None):
    L = ["### " + title, ""] + ([note, ""] if note else []) + ["| Group | " + HEAD + " |", "|---|---|---|---|---|"]
    for g in (order or sorted(groups)):
        if g in groups:
            L.append("| %s | %s |" % (g, S2.m3(S2.multiple(groups[g], R))))
    return L + [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(M.HERE, "..", "br-adp-mirror"))
    a = ap.parse_args()
    M.MIRROR_PATH = a.mirror
    N = [n for n in M.load(a.mirror) if n["tiers"]["am"] or n["tiers"]["pm"]]
    dates = [n["date"] for n in N]
    TT = S.teams_of(N)
    R = S2.rates(TT)
    SN = snaps_of(N, a.mirror)
    PRE = {d: pre_tag(v) for d, v in SN.items()}
    at_snap = {d: dict(v) for d, v in SN.items()}
    gaps = [(M.F.iso(v[i + 1][0]) - M.F.iso(v[i][0])).total_seconds() / 3600 for v in SN.values() for i in range(len(v) - 1)]

    # each team's Q picks and the Q players on the slate at its draft hour
    q_of, q_slate, matched = {}, {}, 0
    for i, (n, t) in enumerate(TT):
        tab = at_snap[n["date"]].get(t["at"]) if t["at"] else None
        if tab is None:
            continue
        matched += 1
        q_slate[i] = {p: v for p, v in tab.items() if v[1] in QTAGS}
        q_of[i] = [p for p in M.drafted_by(t) if p in q_slate[i]]
    rows_at = lambda n, t: n["tiers"][t["window"]]
    a_tier = lambda n, t, p: (rows_at(n, t).get(p) or {}).get("a_tier") or "?"

    # 1-2. the whole bet
    g1, g2, gfall, gturn, g_sat = (collections.defaultdict(list) for _ in range(5))
    for i, (n, t) in enumerate(TT):
        if i not in q_of:
            continue
        qs = q_of[i]
        if not qs:
            g1["no Q pick"].append((n, t))
            continue
        g1["any Q pick"].append((n, t))
        seen = set()
        for p in qs:
            k = "T" + a_tier(n, t, p)
            s = "sat" if sat(n, p) else "played"
            pre = PRE[n["date"]].get(p)
            now = q_slate[i][p][0]
            fall = None if pre is None or now is None else now - pre
            fb = "tagged from the first snapshot" if fall is None else "rose" if fall < 0 else "0-3 picks" if fall < 3 else "3-6 picks" if fall < 6 else "6+ picks"
            for key, grp in ((k, g1), ("Q pick " + s, g_sat), (k + ", " + s, g2), ("fell " + fb, gfall)):
                if (key, id(grp)) not in seen:
                    seen.add((key, id(grp)))
                    grp[key].append((n, t))
    TI = {id(t): i for i, (_, t) in enumerate(TT)}
    for n, t, info in M.turn_teams(N):
        i = TI.get(id(t))
        if i is None or i not in q_of:
            continue
        has = any(p in q_of[i] for p in info["picks"])
        gturn["%s turn, a turn pick Q-tagged" % info["turn"] if has else "%s turn, no Q at the turn" % info["turn"]].append((n, t))
    tiers = ["T1", "T2", "T3", "T4", "T5", "T?"]
    L1 = (section("By the tier the Q pick was taken in", g1, R, ["no Q pick", "any Q pick"] + tiers) +
          section("By his final status", g_sat, R, ["Q pick played", "Q pick sat"]) +
          section("By how far he fell past his pre-tag ADP (ADP at the team's draft hour minus the last ADP before the tag)", gfall, R,
                  ["fell rose", "fell 0-3 picks", "fell 3-6 picks", "fell 6+ picks", "fell tagged from the first snapshot"]) +
          section("By turn (the Q pick among the team's two turn picks)", gturn, R,
                  ["1/2 turn, a turn pick Q-tagged", "1/2 turn, no Q at the turn", "2/3 turn, a turn pick Q-tagged", "2/3 turn, no Q at the turn"]))
    L2 = section("Teams whose Q pick sat, and played, by tier", g2, R, [k + ", " + s for k in tiers for s in ("sat", "played")])

    # 3. swap crowding
    groups3 = collections.defaultdict(list)
    w3A, w3B = {}, {}
    nights_out, n_targets, n_crowd = set(), 0, 0
    for n in N:
        for cid, ts in n["teams"].items():
            pods = collections.defaultdict(list)
            for t in ts:
                pods[t["draft_id"]].append(t)
            dr, af = collections.Counter(), collections.Counter()
            swapped = collections.defaultdict(list)          # target -> teams that swapped him in
            for ps in pods.values():
                dr.update(set().union(*(M.drafted_by(t) for t in ps)))
                af.update(set().union(*(set(t["picks"]) for t in ps)))
                for t in ps:
                    for p, x in zip(t["picks"], t["adps"]):
                        if x is None:
                            swapped[p].append(t)
            if not swapped:
                continue
            nights_out.add(n["date"])
            k = len(pods)
            crowd = {p for p in swapped if 100 * (af[p] - dr[p]) / k >= CROWD}
            n_targets += len(swapped)
            n_crowd += len(crowd)
            proj = lambda p: num((n["tiers"]["pm"].get(p) or n["tiers"]["am"].get(p) or {}).get("proj"))
            for c in crowd:
                for o in set(swapped) - crowd:
                    pc, po = proj(c), proj(o)
                    if pc is None or po is None or abs(pc - po) > WITHIN:
                        continue
                    for t in swapped[c]:
                        if id(t) in TI:
                            w3A[TI[id(t)]] = 1
                    for t in swapped[o]:
                        if id(t) in TI:
                            w3B[TI[id(t)]] = 1
            for p, tl in swapped.items():
                for t in tl:
                    if id(t) in TI:
                        groups3["crowd swap" if p in crowd else "other swap"].append(TT[TI[id(t)]])
    for g in groups3:
        groups3[g] = list({id(t): (n, t) for n, t in groups3[g]}.values())
    groups3["crowd swap, with an other target within %d projected points" % WITHIN] = [TT[i] for i in w3A]
    groups3["other swap, with a crowd target within %d projected points" % WITHIN] = [TT[i] for i in w3B]
    lift3 = S2.weighted_lift(TT, w3A, w3B)
    f = lambda v: "%.2f" % v if v is not None else "-"
    L3 = ["%d nights with swaps, %d swap targets across contests, %d crowd swaps (after-swap share of pods %d+ points above the "
          "draft's)." % (len(nights_out), n_targets, n_crowd, CROWD), ""] + section(
          "Swap targets against the field", groups3, R,
          ["crowd swap", "other swap", "crowd swap, with an other target within %d projected points" % WITHIN,
           "other swap, with a crowd target within %d projected points" % WITHIN]) + [
          "Crowd swap against other swap targets within %d projected points, same contest and price quintile: top 1%% %s, cash %s, "
          "top 10%% %s (80%% range %.2f-%.2f; %.0f%% of resamples above 1); %d / %d teams, %d slates." % (
              WITHIN, f(lift3[1]), f(lift3["cash"]), f(lift3[10]), *(lift3["r10"] or (0, 0)), 100 * (lift3["above"] or 0),
              lift3["nA"], lift3["nB"], lift3["slates"]), ""]

    # 4. beneficiaries before news
    g4 = collections.defaultdict(list)
    for i, (n, t) in enumerate(TT):
        if i not in q_slate:
            continue
        qteams = collections.defaultdict(list)
        for p, (_, _, team) in q_slate[i].items():
            qteams[team].append(p)
        rows = rows_at(n, t)
        found = set()
        for p in M.drafted_by(t):
            r = rows.get(p)
            if not r or r["a_tier"] not in ("1", "2", "3", "4"):
                continue
            mates = [q for q in qteams.get(r["team"], []) if q != p]
            for q in mates:
                found.add("T%s beneficiary, Q teammate %s" % (r["a_tier"], "sat" if sat(n, q) else "played"))
        for k in found:
            g4[k].append((n, t))
        if not found:
            g4["no beneficiary"].append((n, t))
    L4 = section("Teams holding a T1-T4 teammate of a Q-tagged player, against the field", g4, R,
                 ["no beneficiary"] + ["T%s beneficiary, Q teammate %s" % (k, s) for k in "1234" for s in ("sat", "played")])

    head = ["# Q-tag study: drafting Q-tagged players, their swaps and their teammates, in contest results", "",
            "Written by scripts/nba_money_qtags.py (definitions in its docstring), %s to %s: %d nights, %d teams with a draft "
            "window and price, %d of them matched to the snapshot they drafted at. Multiples are against the same contest and "
            "price quintile (the field averages 1.0). Results only: no rule changes." % (dates[0], dates[-1], len(N), len(TT), matched), "",
            "Tag history: Underdog's tag on each priced player in the ADP mirror's snapshots, %d snapshots over these slates, "
            "median %.1f hours apart (90%% within %.1f hours); a team's draft hour is matched to one of them." % (
                sum(len(v) for v in SN.values()), st.median(gaps), sorted(gaps)[int(0.9 * len(gaps))]), "",
            "## Summary", "", "(written by hand from the tables below when the file is published)", ""]
    body = (["## 1. The whole bet", ""] + L1 + ["## 2. Cost of an out", ""] + L2 + ["## 3. Swap crowding", ""] + L3 +
            ["## 4. Beneficiaries before the news", ""] + L4)
    open(OUT, "w").write("\n".join(head + body) + "\n")
    print("\n".join(head + body))


if __name__ == "__main__":
    main()
