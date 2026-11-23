/* DraftKings college basketball: late swap (2026-11-21, the operator's approval of the late-swap study,
 * analysis/cbb/dk/lateswap_2026-11-21.md). Shared by the DK page's Swap step (dk.html) and the tests (tests/dk_swap.js);
 * no page code here. Built in pieces, behind the Swap step, the export off until the 11-18 replay passes and one
 * read-only live night:
 *   1. parsers     parseStandings (a contest standings export at a tip), parseEntries (DraftKings' entries file),
 *                  matchNames (standings names -> card ids, refusing ambiguity)
 *   2. the rules   validate (DraftKings' late-swap rules: a started player stays in the exact slot he started in;
 *                  unstarted slots change only to unstarted, slot-eligible players; salary; no duplicates), arrangeOpen
 *                  (the unstarted part re-seated with the latest tips in UTIL where the positions allow)
 *   3. live points soFar (a started game's DraftKings points from ESPN's play-by-play before a moment, and the share of
 *                  regulation left: scripts/dk_lateswap_study.py so_far, ported line for line), liveState (every
 *                  started player's points so far and his game's share left)
 *   4. the hidden field hiddenMass / hiddenOwn (the players still to play: our projected ownership scaled to the mass the
 *                  standings leave hidden, the study's best piece), fieldDraw (one real entry's hidden slots drawn
 *                  from that ownership: slot-eligible, no player twice, within the salary it has left; after
 *                  DRAW_TRIES failures, without the salary limit, counted)
 * Later pieces: the proposer, the export.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.DKSwap = factory();
})(this, function () {
  var CAP = 50000, SLOTS = ["G", "G", "G", "F", "F", "F", "UTIL", "UTIL"];

  function parseCsv(text) {       // RFC 4180-ish (as dk.html parseCsv): quoted fields, doubled quotes
    var out = [], row = [], f = "", q = false;
    text = String(text || "").replace(/^﻿/, "");
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (q) { if (ch === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += ch; }
      else if (ch === '"') q = true;
      else if (ch === ",") { row.push(f); f = ""; }
      else if (ch === "\n" || ch === "\r") { if (ch === "\r" && text[i + 1] === "\n") i++; row.push(f); out.push(row); row = []; f = ""; }
      else f += ch;
    }
    if (f || row.length) { row.push(f); out.push(row); }
    return out;
  }
  function csvCell(v) { v = String(v == null ? "" : v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }

  // --- 1. parsers ---------------------------------------------------------------------------------------------------
  /* A contest standings export: {entries: [{entryId, user, points, timeLeft, slots: [{slot, name}]}], own: {name: %},
     fpts: {name: points}}. A Lineup cell reads "F Name F Name ... G Name ... UTIL Name"; at a tip the players still to
     play are hidden (a slot reading LOCKED, blank or missing): their name is null. A player's ownership is the sum of
     his rows (one per roster slot he was drafted in, as dk_eval.standings reads it). */
  function parseStandings(text) {
    var t = parseCsv(text), h = (t[0] || []).map(function (x) { return x.trim(); });
    var col = function (name) { return h.indexOf(name); };
    var iR = col("Rank"), iE = col("EntryId"), iN = col("EntryName"), iT = col("TimeRemaining"), iP = col("Points"), iL = col("Lineup");
    var iPl = col("Player"), iPct = col("%Drafted"), iF = col("FPTS");
    if (iE < 0 || iL < 0 || iP < 0) return { error: "That isn't a DraftKings contest standings file (Rank, EntryId, EntryName, ..., Lineup)." };
    var entries = [], own = {}, fpts = {};
    t.slice(1).forEach(function (r) {
      if (r[iE] && /^\d+$/.test(r[iE].trim())) {
        entries.push({ entryId: r[iE].trim(), rank: +r[iR] || null, user: (r[iN] || "").replace(/\s*\(\d+\/\d+\)\s*$/, "").trim(),
                       points: r[iP] === "" ? null : +r[iP], timeLeft: iT >= 0 && r[iT] !== "" ? +r[iT] : null, slots: lineupSlots(r[iL] || "") });
      }
      if (iPl >= 0 && r[iPl] && r[iPl].trim()) {
        var nm = r[iPl].trim(), pct = parseFloat(String(r[iPct] || "").replace("%", ""));
        own[nm] = (own[nm] || 0) + (isFinite(pct) ? pct : 0);
        if (iF >= 0 && r[iF] !== "" && isFinite(+r[iF])) fpts[nm] = +r[iF];
      }
    });
    return { entries: entries, own: own, fpts: fpts };
  }
  function lineupSlots(s) {         // [{slot, name or null}] from a Lineup cell
    var parts = (" " + String(s).trim()).split(/(?:^|\s)(G|F|UTIL)(?=\s|$)/), out = [];
    for (var i = 1; i < parts.length; i += 2) {
      var nm = (parts[i + 1] || "").trim();
      out.push({ slot: parts[i], name: !nm || /^LOCKED$/i.test(nm) ? null : nm });
    }
    return out;
  }

  /* DraftKings' entries file: {header, rows: [{entryId, contestName, contestId, fee, cells, ids, locked}], extra}. A slot
     cell is "Name (id)", "Name (id) (LOCKED)" once his game has started, or a bare id; ids[k] null for an empty or
     unreadable cell. The file's other columns (instructions, the player list beside the entries) are left as they were
     read, in extra, for the export to write back unchanged. */
  function parseEntries(text) {
    var t = parseCsv(text), header = t[0] || [];
    if ((header[0] || "").trim() !== "Entry ID" || (header[4] || "").trim() !== "G" || (header[11] || "").trim() !== "UTIL")
      return { error: "That isn't DraftKings' entries file (Entry ID, Contest Name, Contest ID, Entry Fee, G ... UTIL)." };
    var rows = [], extra = [];
    t.slice(1).forEach(function (r, k) {
      if (!/^\d+$/.test((r[0] || "").trim())) { extra.push({ at: k + 1, row: r }); return; }
      var cells = r.slice(4, 12).map(function (x) { return (x || "").trim(); });
      rows.push({ entryId: r[0].trim(), contestName: (r[1] || "").trim(), contestId: (r[2] || "").trim(), fee: (r[3] || "").trim(),
                  cells: cells, ids: cells.map(cellId), locked: cells.map(function (c) { return /\(LOCKED\)\s*$/i.test(c); }), rest: r.slice(12) });
    });
    return { header: header, rows: rows, extra: extra };
  }
  function cellId(c) {
    var m = /\((\d+)\)(?:\s*\(LOCKED\))?\s*$/i.exec(c || "") || /^(\d+)$/.exec((c || "").trim());
    return m ? m[1] : null;
  }

  /* Standings names -> card ids: {name: id} for names one card holds (exact, else on a normalized form: case, accents,
     punctuation, Jr. / II / III), and the names it could not place: {ids, unknown: [names], ambiguous: [names]}. */
  function norm(s) {
    return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\b(jr|sr|ii|iii|iv|v)\b\.?/g, "")
      .replace(/[^a-z0-9]+/g, " ").trim();
  }
  function matchNames(names, rows) {
    var exact = {}, loose = {};
    rows.forEach(function (r) { (exact[r.name] = exact[r.name] || []).push(r.id); var n = norm(r.name); (loose[n] = loose[n] || []).push(r.id); });
    var ids = {}, unknown = [], ambiguous = [];
    names.forEach(function (nm) {
      var c = exact[nm] && exact[nm].length ? exact[nm] : loose[norm(nm)] || [];
      if (c.length === 1) ids[nm] = c[0]; else (c.length ? ambiguous : unknown).push(nm);
    });
    return { ids: ids, unknown: unknown, ambiguous: ambiguous };
  }

  // --- 2. the rules -------------------------------------------------------------------------------------------------
  function isG(r) { return /(^|\/)G(\/|$)/.test(r.roster || r.position || ""); }
  function isF(r) { return /(^|\/)F(\/|$)/.test(r.roster || r.position || ""); }
  function fits(slot, r) { return slot === "UTIL" ? (isG(r) || isF(r)) : slot === "G" ? isG(r) : isF(r); }

  /* Would DraftKings take this edit? before / after: 8 ids in SLOTS order; by: {id: card}; started(id): his game has
     begun. {ok, errors: [text]}. A started player must stay in the exact slot he was in (DraftKings refuses the upload
     otherwise); a changed slot takes only a player whose game hasn't started; every player once; each slot's position;
     salary within the cap. */
  function validate(before, after, by, started) {
    var errors = [];
    if (!after || after.length !== 8) return { ok: false, errors: ["a lineup needs 8 players"] };
    var seen = {}, sal = 0;
    after.forEach(function (id, k) {
      var r = id && by[id];
      if (!r) { errors.push(SLOTS[k] + " " + (k + 1) + ": unknown player " + (id || "(empty)")); return; }
      if (seen[id]) errors.push(r.name + " is in the lineup twice");
      seen[id] = 1; sal += r.salary || 0;
      if (!fits(SLOTS[k], r)) errors.push(r.name + " can't play " + SLOTS[k]);
    });
    before.forEach(function (id, k) {
      if (id && started(id) && after[k] !== id) errors.push((by[id] ? by[id].name : id) + " has started: he must stay in " + SLOTS[k] + " " + (k + 1));
    });
    after.forEach(function (id, k) {
      if (id && id !== before[k] && started(id)) errors.push((by[id] ? by[id].name : id) + " has started: he can't move into " + SLOTS[k] + " " + (k + 1));
    });
    if (sal > CAP) errors.push("salary $" + sal.toLocaleString() + " is over $" + CAP.toLocaleString());
    return { ok: !errors.length, errors: errors };
  }

  /* The unstarted part re-seated: the started players keep their slots, the unstarted ones fill the other slots in the
     legal arrangement with the latest tips in UTIL (the earlier of the two first, then their sum; the higher salary on
     equal tips, as DKSim.lateSlots), G and F slots by salary. null if no legal arrangement. ids: 8 ids, SLOTS order. */
  function arrangeOpen(ids, by, started) {
    var open = [], movers = [];
    ids.forEach(function (id, k) { if (started(id)) return; open.push(k); movers.push(id); });
    if (!open.length) return ids.slice();
    var tip = function (id) { return Date.parse((by[id] || {}).game_start || "") || 0; }, best = null, bestKey = null;
    permute(movers, function (p) {
      for (var i = 0; i < p.length; i++) if (!fits(SLOTS[open[i]], by[p[i]] || {})) return;
      var u = [], gf = 0;
      p.forEach(function (id, i) { if (SLOTS[open[i]] === "UTIL") u.push(id); else gf += (by[id] || {}).salary * (open[i] < 3 ? 3 - open[i] : 6 - open[i]); });
      var key = [u.length ? Math.min.apply(null, u.map(tip)) : 0, u.reduce(function (t, id) { return t + tip(id); }, 0),
                 u.reduce(function (t, id) { return t + ((by[id] || {}).salary || 0); }, 0), gf];
      for (var j = 0; j < key.length; j++) {
        if (bestKey && key[j] < bestKey[j]) return;
        if (!bestKey || key[j] > bestKey[j]) break;
      }
      bestKey = key; best = p.slice();
    });
    if (!best) return null;
    var out = ids.slice();
    open.forEach(function (k, i) { out[k] = best[i]; });
    return out;
  }
  function permute(a, f) {           // every order of a (up to 8! = 40,320)
    var n = a.length, c = new Array(n).fill(0), x = a.slice(), i = 0;
    f(x);
    while (i < n) {
      if (c[i] < i) { var j = i % 2 ? c[i] : 0, t = x[j]; x[j] = x[i]; x[i] = t; f(x); c[i]++; i = 0; }
      else { c[i] = 0; i++; }
    }
  }

  // --- 3. live points ----------------------------------------------------------------------------------------------
  // ESPN's summary for a game (sports/basketball/mens-college-basketball/summary?event=<card event>) carries its plays,
  // each with wallclock, period, clock, type, scoringPlay / scoreValue and participants (the page fetches it).
  function elapsed(p) {             // game minutes gone at a play: two 20-minute halves, then 5-minute overtimes
    var per = (p.period && p.period.number) || 1, c = ((p.clock && p.clock.displayValue) || "0:00").split(":");
    var left = (+c[0] || 0) + (+(c[1] || 0) / 60);
    return per <= 2 ? (per - 1) * 20 + (20 - left) : 40 + (per - 3) * 5 + (5 - left);
  }
  /* {pts: {dk id: DraftKings points from the plays before untilMs}, left: the game's share of regulation left, done}.
     Points 1, a made three +0.5, rebound 1.25, assist 1.5, steal 2, block 2, turnover -0.5, a double-double +1.5 once
     reached (DraftKings' college scoring, as the study). espn2dk: {ESPN athlete id: DK id}. */
  function soFar(plays, untilMs, espn2dk) {
    var st = {}, last = null, done = false;
    var add = function (a, k, v) { (st[a] = st[a] || { pts: 0, tpm: 0, reb: 0, ast: 0, stl: 0, blk: 0, tov: 0 })[k] += v; };
    (plays || []).forEach(function (p) {
      if (!p.wallclock || Date.parse(p.wallclock) >= untilMs) return;
      last = p;
      var t = (p.type && p.type.text) || "";
      if (t === "End Game") done = true;
      var who = (p.participants || []).map(function (x) { return String((x.athlete || {}).id); });
      if (p.scoringPlay && who.length) {
        add(who[0], "pts", p.scoreValue || 0);
        if (p.scoreValue === 3) add(who[0], "tpm", 1);
        if (who.length > 1 && t !== "MadeFreeThrow") add(who[1], "ast", 1);
      } else if (who.length && t.indexOf("Rebound") >= 0) add(who[0], "reb", 1);
      else if (who.length && t === "Steal") add(who[0], "stl", 1);
      else if (who.length && t === "Block Shot") add(who[0], "blk", 1);
      else if (who.length && t.indexOf("Turnover") >= 0) add(who[0], "tov", 1);
    });
    var pts = {};
    Object.keys(st).forEach(function (a) {
      if (!(a in espn2dk)) return;
      var x = st[a], dd = ["pts", "reb", "ast", "stl", "blk"].filter(function (k) { return x[k] >= 10; }).length >= 2;
      pts[espn2dk[a]] = x.pts + 0.5 * x.tpm + 1.25 * x.reb + 1.5 * x.ast + 2 * x.stl + 2 * x.blk - 0.5 * x.tov + (dd ? 1.5 : 0);
    });
    var left = done ? 0 : last === null ? 1 : elapsed(last) < 40 ? Math.max(0, (40 - elapsed(last)) / 40) : 0.03;
    return { pts: pts, left: left, done: done };
  }
  /* Every started player's points so far and his game's share left, at untilMs: by {dk id: card (espn, event,
     game_start)}; plays {event: plays or null}. A started game without play-by-play: its players' points unknown (null)
     and its share left 1, so the sim plays their whole game (the study's rule). {pts, left, unknown: [events]}. */
  function liveState(by, plays, untilMs) {
    var e2d = {}, ev = {}, out = { pts: {}, left: {}, unknown: [] };
    Object.keys(by).forEach(function (id) {
      var r = by[id];
      if (r.espn) e2d[String(r.espn)] = id;
      // started strictly before the moment: a game tipping at it is the decision's own swap deadline, still open
      if (r.event && Date.parse(r.game_start || "") < untilMs) (ev[r.event] = ev[r.event] || []).push(id);
    });
    Object.keys(ev).forEach(function (e) {
      var pl = plays[e];
      if (!pl || !pl.length) { out.unknown.push(e); ev[e].forEach(function (id) { out.pts[id] = null; out.left[id] = 1; }); return; }
      var g = soFar(pl, untilMs, e2d);
      ev[e].forEach(function (id) { out.pts[id] = g.pts[id] || 0; out.left[id] = g.left; });
    });
    return out;
  }

  // --- 4. the hidden field ------------------------------------------------------------------------------------------
  // The study's draw (scripts/dk_lateswap_study.py impute_one): G and F slots first, UTIL last, each pick weighted by
  // ownership among the players who fit the slot, aren't in the entry yet and leave MIN_SAL for every slot still to
  // fill; a draw leaving over LEFT_OK unspent is kept LEFT_KEEP of the time (real entries: 98.7% leave $1,000 or less).
  var LEFT_OK = 1000, LEFT_KEEP = 0.1, MIN_SAL = 3000, DRAW_TRIES = 25;
  function hiddenMass(entries) {     // the ownership still hidden: 100 x hidden slots / entries (800 at lock, 0 at the end)
    var h = 0; entries.forEach(function (e) { e.slots.forEach(function (x) { if (x.name === null) h++; }); });
    return entries.length ? 100 * h / entries.length : 0;
  }
  function hiddenOwn(pre, hidden, mass) {    // {id: %}: our projected ownership of the hidden players, scaled to the mass
    var sp = hidden.reduce(function (t, id) { return t + (pre[id] || 0); }, 0) || 1, out = {};
    hidden.forEach(function (id) { out[id] = (pre[id] || 0) * mass / sp; });
    return out;
  }
  /* One real entry's hidden slots: ids in open-slot order, or null when even the fallback can't fill them. open: slot
     labels; left: 50k less the revealed salaries; pool: the hidden players' cards; w: {id: weight} (hiddenOwn);
     stats: {draws, fallback} counted. */
  function fieldDraw(random, open, left, pool, w, stats) {
    var order = open.map(function (s, k) { return { s: s, k: k }; }).sort(function (a, b) { return (a.s === "UTIL") - (b.s === "UTIL"); });
    var pick = function (cands) {
      var tot = 0; cands.forEach(function (r) { tot += Math.max(w[r.id] || 0, 1e-6); });
      var x = random() * tot;
      for (var i = 0; i < cands.length; i++) { x -= Math.max(w[cands[i].id] || 0, 1e-6); if (x <= 0) return cands[i]; }
      return cands[cands.length - 1];
    };
    var once = function (capped) {
      var used = {}, sal = 0, out = new Array(open.length);
      for (var n = 0; n < order.length; n++) {
        var reserve = MIN_SAL * (order.length - n - 1);
        var c = pool.filter(function (r) { return !used[r.id] && fits(order[n].s, r) && (!capped || r.salary + sal + reserve <= left); });
        if (!c.length) return null;
        var r = pick(c); used[r.id] = 1; sal += r.salary; out[order[n].k] = r.id;
      }
      return { ids: out, sal: sal };
    };
    if (stats) stats.draws = (stats.draws || 0) + 1;
    var got = null;
    for (var t = 0; t < DRAW_TRIES; t++) {
      var d = once(true);
      if (!d) continue;
      got = d.ids;
      if (left - d.sal <= LEFT_OK || random() < LEFT_KEEP) return d.ids;
    }
    if (got) return got;
    if (stats) stats.fallback = (stats.fallback || 0) + 1;    // no fill within the salary left: drawn without the limit
    var f = once(false);
    return f ? f.ids : null;
  }

  return { CAP: CAP, SLOTS: SLOTS, LEFT_OK: LEFT_OK, MIN_SAL: MIN_SAL, hiddenMass: hiddenMass, hiddenOwn: hiddenOwn, fieldDraw: fieldDraw, elapsed: elapsed, soFar: soFar, liveState: liveState, parseCsv: parseCsv, csvCell: csvCell, parseStandings: parseStandings, lineupSlots: lineupSlots,
           parseEntries: parseEntries, cellId: cellId, norm: norm, matchNames: matchNames, fits: fits, validate: validate,
           arrangeOpen: arrangeOpen };
});
