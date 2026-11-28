/* The source blend (2026-11-28, the operator; PROVISIONAL on the projection arm, analysis/cbb/dk/ideas.md).
 *
 * The operator's outside projection files (Gajewski's TSV, RotoWire's CSV) are picked in the browser and read here,
 * never uploaded or fetched: they are paid content and this page is public. Each player's blended DraftKings points:
 *   - the MEDIAN of the projections he has (ours fp_dk, each source's DK points); with two, their mean; ours alone: ours;
 *   - an in/out split (a projection under 8 minutes while another is at 10+): ours, flagged "news: sources split on
 *     whether he plays" (an out is never averaged with a 25-minute projection);
 *   - Out players: ours.
 * The page scales its projection by blend / fp_dk (the Questionable gate and Mark-out minutes stay as they are); the
 * field's ownership keeps reading ours.
 *
 * The parsing and matching mirror battle-royale-research scripts/dk_source.py (read_source, match, match_nosalary),
 * whose blend() is this rule in Python; its tests check both give the same blend on the banked files.
 */
(function (root) {
  "use strict";
  var G5_LOW = 8, G5_HIGH = 10;
  var COLS = { name: ["player", "name", "playername"], team: ["team", "teamabbrev", "tm"], salary: ["salary", "sal", "dksalary"],
    pos: ["pos", "position"], opp: ["opp", "opponent"],
    fp: ["fpts", "fp", "dkpts", "dkfpts", "proj", "projection", "projpts", "points"], min: ["ttlmin", "min", "mins", "minutes", "projmin"],
    own: ["own", "ownpct", "pown", "projown", "ownership", "projectedownership"],
    pts: ["pts"], tov: ["tov", "to", "turnovers"], blk: ["blk", "blocks"], stl: ["stl", "steals"], reb: ["trb", "reb", "rebounds"],
    ast: ["ast", "assists"], tpm: ["3pt", "3pm", "tpm", "threes"] };
  var CATS = ["pts", "reb", "ast", "stl", "blk", "tov", "tpm"];
  var DKW = { pts: 1.0, tpm: 0.5, reb: 1.25, ast: 1.5, stl: 2.0, blk: 2.0, tov: -0.5 };

  function joinInitials(w) {
    var out = [], buf = "";
    w.forEach(function (x) {
      if (x.length === 1 && /[a-z]/.test(x)) { buf += x; return; }
      if (buf) { out.push(buf); buf = ""; }
      out.push(x);
    });
    if (buf) out.push(buf);
    return out;
  }
  function norm(s) {
    s = String(s == null ? "" : s).normalize("NFKD").replace(/[^\x00-\x7f]/g, "").toLowerCase();
    s = s.replace(/[^a-z0-9 ]+/g, " ").replace(/\b(jr|sr|ii|iii|iv|v)\b/g, " ");
    return joinInitials(s.split(/\s+/).filter(Boolean)).join(" ");
  }
  function key(h) { return String(h).toLowerCase().replace(/%/g, "pct").replace(/[^a-z0-9]+/g, ""); }
  function num(v) {
    if (v == null) return null;
    var t = String(v).replace(/%/g, "").replace(/,/g, "").trim();
    if (t === "") return null;
    var x = Number(t);
    return isFinite(x) ? x : null;
  }
  // a CSV line (quoted fields allowed) or a tab-split line
  function splitLine(l, d) {
    if (d === "\t") return l.split("\t");
    var out = [], cur = "", q = false;
    for (var i = 0; i < l.length; i++) {
      var c = l[i];
      if (q) { if (c === '"') { if (l[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
      else if (c === '"') q = true;
      else if (c === ",") { out.push(cur); cur = ""; }
      else cur += c;
    }
    out.push(cur);
    return out;
  }
  function readSource(text) {
    var lines = String(text).replace(/^﻿/, "").split(/\r\n|\r|\n/);
    while (lines.length && lines[lines.length - 1] === "") lines.pop();
    var head = lines.slice(0, 5).join("\n"), tabs = (head.match(/\t/g) || []).length, commas = (head.match(/,/g) || []).length;
    var d = tabs >= commas ? "\t" : ",";
    var rows = lines.map(function (l) { return splitLine(l, d); });
    var known = {}; Object.keys(COLS).forEach(function (f) { COLS[f].forEach(function (n) { known[n] = 1; }); });
    var h0 = 0;
    for (var i = 0; i < Math.min(10, rows.length); i++) {
      var r = rows[i], hasName = r.some(function (c) { return COLS.name.indexOf(key(c)) >= 0; }),
          nk = r.filter(function (c) { return known[key(c)]; }).length;
      if (hasName && nk >= 3) { h0 = i; break; }
    }
    rows = rows.slice(h0);
    var hdr = (rows[0] || []).map(key), col = {};
    Object.keys(COLS).forEach(function (f) {
      for (var j = 0; j < hdr.length; j++) if (COLS[f].indexOf(hdr[j]) >= 0 && col[f] == null) { col[f] = j; break; }
    });
    var out = [];
    rows.slice(1).forEach(function (r) {
      if (!r.length || !r.some(function (x) { return String(x).trim(); })) return;
      var g = function (f) { return col[f] != null && col[f] < r.length ? r[col[f]] : null; };
      var o = { name: g("name"), team: String(g("team") || "").trim(), salary: num(g("salary")), fp: num(g("fp")), min: num(g("min")), own: num(g("own")) };
      CATS.forEach(function (c) { o[c] = num(g(c)); });
      if (o.fp == null && o.pts != null) {
        var s = 0; Object.keys(DKW).forEach(function (c) { s += DKW[c] * (o[c] || 0); });
        o.fp = Math.round(s * 100) / 100; o.fp_from = "categories";
      }
      out.push(o);
    });
    return { rows: out, col: col };
  }

  // ids: [[dk id, normalized name, team, salary]]
  function teamAlias(src, ids) {
    var byName = {};
    ids.forEach(function (x) { (byName[x[1]] = byName[x[1]] || {})[x[2]] = 1; });
    var votes = {};
    src.forEach(function (r) {
      var ts = byName[norm(r.name)], k = ts && Object.keys(ts);
      if (k && k.length === 1) { var v = votes[r.team] = votes[r.team] || {}; v[k[0]] = (v[k[0]] || 0) + 1; }
    });
    var out = {};
    Object.keys(votes).forEach(function (st) {
      var best = null, n = 0;
      Object.keys(votes[st]).forEach(function (t) { if (votes[st][t] > n) { n = votes[st][t]; best = t; } });
      if (n >= 2) out[st] = best;
    });
    return out;
  }
  function matchNoSalary(src, ids) {
    var alias = teamAlias(src, ids), nt = {}, nm = {}, byTeam = {};
    ids.forEach(function (x) { nt[x[1] + "|" + x[2]] = x[0]; (nm[x[1]] = nm[x[1]] || []).push(x[0]); (byTeam[x[2]] = byTeam[x[2]] || []).push([x[0], x[1]]); });
    var out = {}, how = { "name+team": 0, "last name + initial, team": 0, "name only": 0, none: 0 };
    src.forEach(function (r) {
      var n = norm(r.name), t = alias[r.team], i = nt[n + "|" + t];
      if (!i && t && n) {
        var last = n.split(" ").pop(), c = (byTeam[t] || []).filter(function (p) { return p[1].split(" ").pop() === last && p[1][0] === n[0]; });
        i = c.length === 1 ? c[0][0] : null;
        if (i) { how["last name + initial, team"]++; out[i] = r; return; }
      }
      if (i) how["name+team"]++;
      else {
        var c2 = nm[n] || [];
        i = c2.length === 1 && !(r.team in alias) ? c2[0] : null;
        how[i ? "name only" : "none"]++;
      }
      if (i) out[i] = r;
    });
    return { map: out, how: how };
  }
  function match(src, ids) {
    if (!src.some(function (r) { return r.salary; })) return matchNoSalary(src, ids);
    var full = {}, loose = {};
    ids.forEach(function (x) { full[x[1] + "|" + x[2] + "|" + x[3]] = x[0]; (loose[x[1] + "|" + x[3]] = loose[x[1] + "|" + x[3]] || []).push(x[0]); });
    var out = {}, how = { full: 0, "name+salary": 0, none: 0 };
    src.forEach(function (r) {
      var n = norm(r.name), i = full[n + "|" + String(r.team).toUpperCase() + "|" + r.salary];
      if (i) how.full++;
      else { var c = loose[n + "|" + r.salary] || []; i = c.length === 1 ? c[0] : null; how[i ? "name+salary" : "none"]++; }
      if (i) out[i] = r;
    });
    return { map: out, how: how };
  }

  // a file's label: RotoWire by its name, else Gajewski when it carries DK points and salaries, else RotoWire-like
  function labelOf(fileName, parsed) {
    if (/rotowire/i.test(fileName || "")) return "rotowire";
    if (/gajewski|gaj/i.test(fileName || "")) return "gajewski";
    return parsed.col.fp != null && parsed.col.salary != null ? "gajewski" : "rotowire";
  }

  function median(v) { var s = v.slice().sort(function (a, b) { return a - b; }), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }
  // one player's blend: us = {min, fp}; srcs = [{min, fp}] (the sources that have him)
  function blendOne(us, srcs, out) {
    if (out) return { fp: us.fp, split: false };
    var all = [us].concat(srcs.filter(function (s) { return s.fp != null; }));
    var ms = all.map(function (s) { return s.min; }).filter(function (m) { return m != null; });
    if (ms.length >= 2 && Math.min.apply(null, ms) < G5_LOW && Math.max.apply(null, ms) >= G5_HIGH) return { fp: us.fp, split: true };
    if (all.length === 1) return { fp: us.fp, split: false };
    return { fp: Math.round(median(all.map(function (s) { return s.fp; })) * 100) / 100, split: false };
  }

  // rows: the page's players [{id, name, team, salary, min, fp_dk, status}]; files: [{name, text}]
  function build(rows, files) {
    var ids = rows.map(function (r) { return [String(r.id), norm(r.name), String(r.team || "").toUpperCase(), r.salary == null ? null : +r.salary]; });
    var bySrc = {}, report = [];
    (files || []).forEach(function (f) {
      var p = readSource(f.text), lab = labelOf(f.name, p), m = match(p.rows.map(function (r) { return Object.assign({}, r); }), ids);
      bySrc[lab] = m.map;
      report.push({ source: lab, file: f.name || "", rows: p.rows.length, matched: Object.keys(m.map).length, how: m.how });
    });
    var blend = {}, split = {}, changed = 0;
    rows.forEach(function (r) {
      if (r.fp_dk == null) return;
      var srcs = [];
      Object.keys(bySrc).sort().forEach(function (s) { var x = bySrc[s][String(r.id)]; if (x) srcs.push({ min: x.min, fp: x.fp }); });
      var b = blendOne({ min: r.min == null ? null : +r.min, fp: +r.fp_dk }, srcs, r.status === "Out");
      if (b.split) split[r.id] = 1;
      if (Math.abs(b.fp - r.fp_dk) >= 0.005) { blend[r.id] = b.fp; changed++; }
    });
    return { sources: report, blend: blend, split: split, changed: changed, splits: Object.keys(split).length };
  }

  var api = { norm: norm, readSource: readSource, match: match, blendOne: blendOne, build: build, labelOf: labelOf, G5_LOW: G5_LOW, G5_HIGH: G5_HIGH };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DKBlend = api;
})(this);
