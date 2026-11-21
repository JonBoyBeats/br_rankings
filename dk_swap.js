/* DraftKings college basketball: late swap (2026-11-21, the operator's approval of the late-swap study,
 * analysis/cbb/dk/lateswap_2026-11-21.md). Shared by the DK page's Swap step (dk.html) and the tests (tests/dk_swap.js);
 * no page code here. Built in pieces, behind the Swap step, the export off until the 11-18 replay passes and one
 * read-only live night:
 *   1. parsers     parseStandings (a contest standings export at a tip), parseEntries (DraftKings' entries file),
 *                  matchNames (standings names -> card ids, refusing ambiguity)
 *   2. the rules   validate (DraftKings' late-swap rules: a started player stays in the exact slot he started in;
 *                  unstarted slots change only to unstarted, slot-eligible players; salary; no duplicates), arrangeOpen
 *                  (the unstarted part re-seated with the latest tips in UTIL where the positions allow)
 * Later pieces: live points (soFar, from ESPN's play-by-play), hidden ownership and the feasible field draws, the
 * proposer, the export.
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

  return { CAP: CAP, SLOTS: SLOTS, parseCsv: parseCsv, csvCell: csvCell, parseStandings: parseStandings, lineupSlots: lineupSlots,
           parseEntries: parseEntries, cellId: cellId, norm: norm, matchNames: matchNames, fits: fits, validate: validate,
           arrangeOpen: arrangeOpen };
});
