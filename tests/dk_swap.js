// Late swap (dk_swap.js), the pieces without a page: the parsers, the slot-lock and validation rules.
// Fixtures: tests/swap_fixture (scripts/dk_swap_fixture.py: the 11-18 main slate, 157033, at the study's break 2, the
// decision at the 02:00Z tip with the 00:30Z and 01:00Z games started).
//   node tests/dk_swap.js
const fs = require("fs"), path = require("path");
const W = require(path.join(__dirname, "..", "dk_swap.js"));
const FIX = path.join(__dirname, "swap_fixture");
const C = JSON.parse(fs.readFileSync(path.join(FIX, "cards_157033.json"), "utf8"));
const by = {}; Object.entries(C.players).forEach(([id, r]) => { by[id] = Object.assign({ id }, r); });
const rows = Object.values(by), TIP = C.tip, started = id => (by[id] && by[id].game_start || "9") < TIP;
const passes = [], fails = [];
function check(name, ok, detail) { (ok ? passes : fails).push(name + (ok || !detail ? "" : ": " + detail)); }

// --- 1. parsers ---
const st = W.parseStandings(fs.readFileSync(path.join(FIX, "standings_157033_break2.csv"), "utf8"));
const e1 = st.entries[0];
check("standings: every entry, 8 slots each, the hidden players null, the user without the (k/n) count",
      st.entries.length === 528 && st.entries.every(e => e.slots.length === 8) && e1.user === "dbaggot3" && e1.entryId === "5343857091" &&
      e1.slots.filter(s => s.name === null).length === 2 && e1.slots.every(s => s.name === null || started(rows.find(r => r.name === s.name).id)),
      JSON.stringify(e1));
const ownNames = Object.keys(st.own);
check("standings: ownership for started players only, summed over a player's slot rows",
      ownNames.length > 0 && ownNames.every(n => started(rows.find(r => r.name === n).id)) && Math.abs(st.own["William Berg"] - (69.89 + 6.06)) < 0.01,
      JSON.stringify(ownNames.slice(0, 5)));
check("standings: a file that isn't one is refused", !!W.parseStandings("a,b\n1,2").error);
check("lineup cell: LOCKED, blank and missing slots read as hidden",
      JSON.stringify(W.lineupSlots("F A B F LOCKED G C D UTIL")) === JSON.stringify([{ slot: "F", name: "A B" }, { slot: "F", name: null }, { slot: "G", name: "C D" }, { slot: "UTIL", name: null }]));
const en = W.parseEntries(fs.readFileSync(path.join(FIX, "DKEntries_fake.csv"), "utf8"));
check("entries file: rows, contest, the 8 ids in slot order, DraftKings' (LOCKED) read as started",
      !en.error && en.rows.length === 3 && en.rows[0].contestId === "197938363" && en.rows.every(r => r.ids.every(id => by[id])) &&
      en.rows.every(r => r.ids.every((id, k) => r.locked[k] === started(id))), JSON.stringify(en.rows[0]));
check("entries file: a bare id and a name (id) cell both read; another file is refused",
      W.cellId("44995190") === "44995190" && W.cellId("Miles Sadler (44995190) (LOCKED)") === "44995190" && W.cellId("") === null && !!W.parseEntries("x,y\n").error);
const names = [...new Set(st.entries.flatMap(e => e.slots.map(s => s.name)).filter(Boolean))];
const mt = W.matchNames(names, rows);
check("names: every revealed standings name matches one card", mt.unknown.length === 0 && mt.ambiguous.length === 0 && Object.keys(mt.ids).length === names.length,
      JSON.stringify([mt.unknown, mt.ambiguous]));
const twin = rows.concat([{ id: "x1", name: "William Berg", team: "ZZZ" }]);
const mt2 = W.matchNames(["William Berg", "Nobody Here", "colben  landrew"], twin);
check("names: two cards with the name -> ambiguous (refused), none -> unknown, case / spacing -> matched",
      mt2.ambiguous[0] === "William Berg" && mt2.unknown[0] === "Nobody Here" && mt2.ids["colben  landrew"] === rows.find(r => r.name === "Colben Landrew").id, JSON.stringify(mt2));

// --- 2. the rules ---
const L = en.rows[0].ids.slice(), openK = L.map((id, k) => started(id) ? -1 : k).filter(k => k >= 0);
const v0 = W.validate(L, L, by, started);
check("rules: the entry as it stands is valid", v0.ok, JSON.stringify(v0.errors));
// an unstarted, eligible, affordable player for one open slot
const sal = ids => ids.reduce((t, id) => t + by[id].salary, 0);
const k0 = openK[0], room = W.CAP - sal(L) + by[L[k0]].salary;
const sub = rows.find(r => !started(r.id) && L.indexOf(r.id) < 0 && W.fits(W.SLOTS[k0], r) && r.salary <= room);
const L1 = L.slice(); L1[k0] = sub.id;
check("rules: an unstarted slot swapped for an unstarted, eligible player within the cap is valid", W.validate(L, L1, by, started).ok,
      JSON.stringify(W.validate(L, L1, by, started).errors));
const ks = L.findIndex(started), L2 = L.slice(); L2[ks] = sub.id;
check("rules: swapping out a started player is refused", !W.validate(L, L2, by, started).ok && /must stay/.test(W.validate(L, L2, by, started).errors.join()));
const L3 = L.slice(), ks2 = L.findIndex((id, k) => started(id) && k !== ks && W.fits(W.SLOTS[ks], by[id]) && W.fits(W.SLOTS[k], by[L[ks]]));
if (ks2 >= 0) { L3[ks] = L[ks2]; L3[ks2] = L[ks]; }
check("rules: two started players trading slots is refused (each must stay in his exact slot)", ks2 >= 0 && !W.validate(L, L3, by, started).ok, String(ks2));
const inStarted = rows.find(r => started(r.id) && L.indexOf(r.id) < 0 && W.fits(W.SLOTS[k0], r)), L4 = L.slice(); L4[k0] = inStarted.id;
check("rules: a started player brought into an open slot is refused", !W.validate(L, L4, by, started).ok && /can't move into/.test(W.validate(L, L4, by, started).errors.join()));
const dear = rows.filter(r => !started(r.id) && L.indexOf(r.id) < 0 && W.fits(W.SLOTS[k0], r)).sort((a, b) => b.salary - a.salary)[0], L5 = L.slice(); L5[k0] = dear.id;
const v5 = W.validate(L, L5, by, started);
check("rules: over the cap is refused", sal(L5) <= W.CAP || (!v5.ok && /over \$50,000/.test(v5.errors.join())), sal(L5) + " " + JSON.stringify(v5.errors));
const L6 = L.slice(); L6[openK[0]] = L[openK[1]];
check("rules: a player twice is refused", openK.length > 1 && !W.validate(L, L6, by, started).ok && /twice/.test(W.validate(L, L6, by, started).errors.join()));
const gSlot = openK.find(k => W.SLOTS[k] === "G") ?? openK.find(k => W.SLOTS[k] === "F");
const misfit = rows.find(r => !started(r.id) && L.indexOf(r.id) < 0 && !W.fits(W.SLOTS[gSlot], r)), L7 = L.slice(); L7[gSlot] = misfit.id;
check("rules: a player in a slot he can't play is refused", !W.validate(L, L7, by, started).ok && /can't play/.test(W.validate(L, L7, by, started).errors.join()));
check("rules: an unknown id and a short lineup are refused", !W.validate(L, L.slice(0, 7), by, started).ok && !W.validate(L, L.slice(0, 7).concat(["123"]), by, started).ok);
// arrangeOpen: started players keep their slots; the latest-tipping unstarted players go to UTIL where positions allow
const A = W.arrangeOpen(L, by, started);
const utilOpen = [6, 7].filter(k => !started(L[k]));
const tip = id => Date.parse(by[id].game_start);
const lateOK = A && utilOpen.every(k => A.every((id, j) => started(id) || j >= 6 || tip(id) <= tip(A[k]) || !W.fits(W.SLOTS[k], by[id])));
check("rules: arrangeOpen keeps every started player in his slot, stays valid, and puts the latest tips in the open UTIL slots",
      !!A && L.every((id, k) => !started(id) || A[k] === id) && W.validate(L, A, by, started).ok && lateOK, JSON.stringify(A));
const Lg = L.slice(); const nonG = rows.filter(r => !started(r.id) && L.indexOf(r.id) < 0 && !/(^|\/)G(\/|$)/.test(r.roster)).slice(0, 8);
check("rules: arrangeOpen gives null when the open players can't fill the open slots",
      W.arrangeOpen(Lg.map((id, k) => started(id) ? id : null).map((id, k) => id || (W.SLOTS[k] === "G" && nonG[k] ? nonG[k].id : Lg[k])), by, started) === null ||
      !openK.some(k => W.SLOTS[k] === "G"), "");

passes.forEach(p => console.log("PASS " + p));
fails.forEach(f => console.log("FAIL " + f));
console.log(`${passes.length} passed, ${fails.length} failed`);
process.exit(fails.length ? 1 : 0);
