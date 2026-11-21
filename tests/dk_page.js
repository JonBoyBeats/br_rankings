// The DK page's self-test: drives dk.html the way the owner does, on a saved slate (tests/dk_fixture: the
// 2026-11-16 slate, 156660), and checks every lineup against every rule it was built under, and the export.
//
//   node tests/dk_page.js           (Playwright's Chromium; exits 1 on any failure)
//
// Run it before changing dk.html or dk_sim.js.
const { chromium } = require("playwright");
const fs = require("fs"), os = require("os");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const FIX = path.join(__dirname, "dk_fixture");
const morning = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_morning.json")));
const field = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_field.json")));
const slate = morning.slates[0];
const P = slate.players;
const OWN = field.slates[String(slate.draft_group_id)].own;
const fails = [], passes = [];
const DKSimLimit = (cap, N) => N <= 5 ? Math.max(0, Math.ceil(cap * N - 1e-4)) : Math.floor(cap * N + 1e-9);
function DKSimPairs(ids) { const s = ids.slice().sort(), o = []; for (let i = 0; i < s.length; i++) for (let j = i + 1; j < s.length; j++) o.push(s[i] + "|" + s[j]); return o; }
function check(name, ok, detail) { (ok ? passes : fails).push(name + (ok || !detail ? "" : ": " + detail)); }
const isG = r => /(^|\/)G(\/|$)/.test(r.roster), isF = r => /(^|\/)F(\/|$)/.test(r.roster);

// the rules, checked here independently of dk_sim.js's own passes()
function obeys(rule, ids) {
  const has = id => ids.includes(id), cnt = set => (set || []).filter(has).length;
  return { min: () => cnt(rule.ids) >= rule.n, none: () => cnt(rule.ids) === 0, never: () => cnt(rule.ids) <= 1,
           if: () => !has(rule.ids[0]) || cnt(rule.set) >= rule.n, ifnot: () => has(rule.ids[0]) || cnt(rule.set) >= rule.n,
           ifteam: () => cnt(rule.set) < rule.n || cnt(rule.set2) >= rule.m }[rule.type]();
}

// every lineup legal and within the rules it was built under
function audit(name, L, o) {
  const bad = [], count = {};
  L.forEach((l, i) => {
    const ids = l.ids, rs = ids.map(id => P[id]);
    if (ids.length !== 8 || new Set(ids).size !== 8) bad.push(`#${i + 1} not 8 different players`);
    const sal = rs.reduce((s, r) => s + r.salary, 0);
    if (sal > 50000 || sal < (o.minSal || 0)) bad.push(`#${i + 1} salary ${sal}`);
    l.slots.forEach((id, j) => {
      const slot = ["G", "G", "G", "F", "F", "F", "UTIL", "UTIL"][j];
      if (slot === "G" && !isG(P[id])) bad.push(`#${i + 1} ${P[id].name} in a G slot`);
      if (slot === "F" && !isF(P[id])) bad.push(`#${i + 1} ${P[id].name} in an F slot`);
    });
    if (new Set(l.slots).size !== 8 || l.slots.some(id => !ids.includes(id))) bad.push(`#${i + 1} slots don't match its players`);
    if (rs.some(r => r.status === "Out")) bad.push(`#${i + 1} has an Out player`);
    const teams = {};
    rs.forEach(r => { teams[r.team] = (teams[r.team] || 0) + 1; });
    if (Math.max(...Object.values(teams)) > (o.maxTeam || 8)) bad.push(`#${i + 1} more than ${o.maxTeam} from one team`);
    if (o.lock && !ids.includes(o.lock)) bad.push(`#${i + 1} missing the locked player`);
    if (o.excl && ids.includes(o.excl)) bad.push(`#${i + 1} has the excluded player`);
    const tot = ids.reduce((s, id) => s + (OWN[id] || 0), 0);
    if (o.maxOwn != null && tot > o.maxOwn + 1e-6) bad.push(`#${i + 1} ownership ${tot.toFixed(1)} over ${o.maxOwn}`);
    if (o.lowN && ids.filter(id => (OWN[id] || 0) < o.lowPct).length < o.lowN) bad.push(`#${i + 1} fewer than ${o.lowN} under ${o.lowPct}%`);
    if (o.stackN) {
      const g = {};
      ids.forEach(id => { const r = P[id]; (g[r.game] = g[r.game] || []).push(r); });
      const ok = Object.values(g).some(v => v.length >= o.stackN && (!o.stackBoth || new Set(v.map(r => r.home)).size === 2));
      if (!ok) bad.push(`#${i + 1} no ${o.stackN}-player game stack${o.stackBoth ? " from both teams" : ""}`);
    }
    ids.forEach(id => { count[id] = (count[id] || 0) + 1; });
  });
  if (o.expo) {                    // caps are a share of the lineups asked for (o.n), as the optimizer sets them
    const n = o.n || L.length, cap = Math.max(1, n <= 5 ? Math.ceil(o.expo * n - 1e-4) : Math.floor(o.expo * n + 1e-9));   // rounded up in a contest of 5 or fewer
    Object.entries(count).forEach(([id, c]) => { if (id !== o.lock && c > (o.capId === id ? Math.floor(o.capPct * n + 1e-9) : cap)) bad.push(`${P[id].name} in ${c} of ${L.length}`); });
  }
  if (o.minUnique) {
    for (let i = 0; i < L.length; i++) for (let j = i + 1; j < L.length; j++) {
      const shared = L[i].ids.filter(id => L[j].ids.includes(id)).length;
      if (shared > 8 - o.minUnique) bad.push(`#${i + 1} and #${j + 1} share ${shared}`);
    }
  }
  check(`${name}: ${L.length} lineups legal and within the rules`, !bad.length && L.length > 0, bad.slice(0, 4).join("; ") || "no lineups");
}

(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1100, height: 900 } });
  // the classic layout for the checks below (the one-screen builder is checked at the end)
  await pg.addInitScript(() => { try { if (!sessionStorage.getItem("nbInit")) { localStorage.setItem("dkcbb:nb", "false"); sessionStorage.setItem("nbInit", "1"); } } catch (e) {} });
  let dialogs = [];
  pg.on("dialog", d => { dialogs.push(d.message()); d.accept(); });       // Fill all contests asks before replacing
  for (const m of ["click", "fill", "selectOption"]) {       // the page's steps (Bank / Cut / Fill): open the one holding the target first
    const orig = pg[m].bind(pg);
    pg[m] = async (sel, ...a) => { await pg.evaluate(q => { try { const el = document.querySelector(q), sec = el && el.closest("section.step"); if (sec && sec.hidden) showStep(sec.dataset.step);
      for (let d = el && el.closest("details"); d; d = d.parentElement && d.parentElement.closest("details")) d.open = true; } catch (e) {} }, sel).catch(() => {}); return orig(sel, ...a); };
  }
  const errors = [];
  pg.on("pageerror", e => errors.push(e.message));
  await pg.route(/fonts\.(googleapis|gstatic)/, r => r.abort());
  await pg.route(/dk_cbb_morning/, r => r.fulfill({ path: path.join(FIX, "dk_cbb_morning.json"), contentType: "application/json" }));
  await pg.route(/dk_cbb_field/, r => r.fulfill({ path: path.join(FIX, "dk_cbb_field.json"), contentType: "application/json" }));
  await pg.route(/cbb_news/, r => r.fulfill({ path: path.join(FIX, "cbb_news.json"), contentType: "application/json" }));
  await pg.route(/dk_cbb_teams/, r => r.fulfill({ path: path.join(FIX, "dk_cbb_teams.json"), contentType: "application/json" }));
  let gate = null;
  await pg.route(/gate\.json/, r => gate ? r.fulfill({ body: JSON.stringify(gate), contentType: "application/json" }) : r.fulfill({ status: 404, body: "" }));
  await pg.route(/own_watch\.json/, r => r.fulfill({ contentType: "application/json", body: JSON.stringify({ patterns: [
    { pattern: "coming off a big game", status: "confirmed", ratio: 1.4, player_nights: 40, nights: 6, same_direction: "5 of 6" },
    { pattern: "blue bloods", status: "emerging", ratio: 1.2, player_nights: 90, nights: 4, same_direction: "3 of 4" }] }) }));
  await pg.goto("file://" + path.join(ROOT, "dk.html"));
  await pg.waitForSelector(".row");
  const ow = await pg.evaluate(() => ({ hidden: $("ownWatch").hidden, text: $("ownWatch").textContent }));
  check("ownership watch (B3): the note shows confirmed patterns only", !ow.hidden && /coming off a big game/.test(ow.text) && !/blue bloods/.test(ow.text), JSON.stringify(ow));
  check("page loads the slate", (await pg.$$eval(".row", r => r.length)) === Object.keys(P).length);
  check("gate shows closed with no gate file", /Projection gate: closed/.test(await pg.textContent("#statusInfo")));
  // the player table layout (2026-11-20): actions (out / play / use / drop) in the fixed L / X group and clickable at a
  // laptop width; Q / D / OUT / new kept beside the name; the scan's columns hidden until a scan exists; Show: all / in pool / left out
  await pg.setViewportSize({ width: 1280, height: 900 });
  const lay = await pg.evaluate(() => {
    renderPlayers();
    const acts = [...document.querySelectorAll("#players .row .qout, #players .row .deepin")];
    const inLx = acts.every(b => b.closest(".lx")) && !document.querySelector("#players .row .name .qout, #players .row .name .deepin");
    const hit = acts.filter(b => b.offsetParent).slice(0, 15).every(b => { b.scrollIntoView({ block: "center" }); const r = b.getBoundingClientRect(); return document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) === b; });
    const qs = rows.filter(r => r.status === "Questionable" && document.querySelector('#players .row[data-id="' + r.id + '"]'));
    const qKeep = qs.every(r => !!document.querySelector('#players .row[data-id="' + r.id + '"] .tkeep .tag.q'));
    const noscan = $("players").classList.contains("noscan") && !SCAN, cell = document.querySelector("#players .row .col-scan");
    const hidden = !cell || getComputedStyle(cell).display === "none";
    const sel = $("poolShow"), n0 = document.querySelectorAll("#players .row").length;
    sel.value = "out"; sel.dispatchEvent(new Event("change"));
    const outRows = [...document.querySelectorAll("#players .row")].map(e => byId(e.dataset.id)), outOk = outRows.length > 0 && outRows.every(r => r.status !== "Out" ? (r.deepOut || state.excl[r.id]) : isDoubtful(r));
    sel.value = "in"; sel.dispatchEvent(new Event("change"));
    const inRows = [...document.querySelectorAll("#players .row")].map(e => byId(e.dataset.id)), inOk = inRows.length > 0 && inRows.every(r => usable(r));
    sel.value = "all"; sel.dispatchEvent(new Event("change"));
    return { acts: acts.length, inLx, hit, qs: qs.length, qKeep, noscan, hidden, outN: outRows.length, outOk, inN: inRows.length, inOk, back: document.querySelectorAll("#players .row").length === n0 };
  });
  check("player table: the out / play / use / drop actions sit in the L / X group, clickable at 1280px; Q stays beside a truncated name; scan columns hidden with no scan; Show all / in pool / left out",
        lay.acts > 0 && lay.inLx && lay.hit && lay.qKeep && lay.noscan && lay.hidden && lay.outOk && lay.inOk && lay.back, JSON.stringify(lay));
  await pg.setViewportSize({ width: 1100, height: 900 });
  // the default slate: today's main (Pacific day: most games; a tie goes to the soonest unlocked, else the later), locked or not; with none today, the
  // newest unlocked, else the most recent; a hand pick holds for the rest of that day
  const ds = await pg.evaluate(() => {
    const now = Date.parse("2026-11-19T18:00:00Z");               // 10:00 AM Pacific, 11-19
    const L = [{ draft_group_id: 1, start: "2026-11-19T01:00:00Z", games: 9, locked: true },     // yesterday's main (11-18 Pacific)
               { draft_group_id: 2, start: "2026-11-19T17:00:00Z", games: 4, locked: true },     // today's early, locked
               { draft_group_id: 3, start: "2026-11-20T00:00:00Z", games: 9, locked: false },    // today's main (16:00 Pacific)
               { draft_group_id: 5, start: "2026-11-20T03:00:00Z", games: 9, locked: false },    // today's late, as many games, later start
               { draft_group_id: 4, start: "2026-11-20T17:30:00Z", games: 7, locked: false }];   // tomorrow's
    const afterLock = Date.parse("2026-11-20T06:30:00Z");          // 22:30 Pacific, everything today locked
    const L2 = L.map(s => Object.assign({}, s, { locked: s.draft_group_id !== 4 }));
    const between = Date.parse("2026-11-20T01:00:00Z"), L3 = L.map(s => Object.assign({}, s, { locked: s.draft_group_id <= 3 }));   // 17:00 Pacific: today's main locked, the late not
    return { today: defaultSlate(L, now, null), afterLock: defaultSlate(L2, afterLock, null), between: defaultSlate(L3, between, null),
             none: defaultSlate(L.filter(s => s.draft_group_id <= 2), Date.parse("2026-11-21T15:00:00Z"), null),
             noneOpen: defaultSlate([L[0], L[4]], Date.parse("2026-11-20T15:00:00Z"), null),
             picked: defaultSlate(L, now, { day: "2026-11-19", dg: 2 }), stale: defaultSlate(L, now, { day: "2026-11-18", dg: 2 }),
             opened: document.getElementById("slate").value === String(defaultSlate(doc.slates, Date.now(), slatePick())) };
  });
  check("default slate: today's main (most games; on a tie the soonest unlocked, else the later) locked or not; none today, the newest unlocked, else the most recent; a hand pick holds for its day only",
        ds.today === 3 && ds.between === 5 && ds.afterLock === 5 && ds.none === 2 && ds.noneOpen === 4 && ds.picked === 2 && ds.stale === 3 && ds.opened, JSON.stringify(ds));
  // the Q filter: only players Questionable by any source; X on one excludes him as anywhere else; off shows everyone
  await pg.evaluate(() => { view.panel = null; renderTiles(); });
  const playersN = await pg.$$eval("#players .row", r => r.length);
  await pg.click("#qOnly");
  const qRows = await pg.$$eval("#players .row", r => r.map(x => x.dataset.id));
  const wantQ = Object.keys(P).filter(id => { const r = P[id], no = x => x && !/^\s*O/i.test(String(x));
    return r.status !== "Out" && (r.status === "Questionable" || no(r.status_dk) || no(r.status_file)); });
  check("Q filter: only the Questionable players, counted on the button", qRows.length > 0 && JSON.stringify(qRows.slice().sort()) === JSON.stringify(wantQ.slice().sort()) &&
        (await pg.textContent("#qOnly")) === "Q (" + wantQ.length + ")", JSON.stringify([qRows.length, wantQ.length]));
  await pg.click(`#players .row[data-id="${qRows[0]}"] .excl`);
  check("Q filter: X on a Q player excludes him", await pg.evaluate(id => !!state.excl[id], qRows[0]));
  await pg.click(`#players .row[data-id="${qRows[0]}"] .excl`);
  await pg.click("#qOnly");
  check("Q filter: off, everyone again", (await pg.$$eval("#players .row", r => r.length)) === playersN);
  // Mark out: a Questionable player ruled out; his teammates share exactly 200 minutes, projections moving with minutes
  const qo = await pg.evaluate(() => {
    const q = rows.find(r => r._status0 === "Questionable" && r.min > 0 && rows.filter(x => x.team === r.team && x.min > 0 && x.status !== "Out").length >= 6);
    if (!q) return null;
    const mates = rows.filter(r => r.team === q.team && r.id !== q.id && r.status !== "Out" && r.min > 0);
    const before = Object.fromEntries(mates.map(r => [r.id, proj(r)]));
    view.panel = null; view.qOnly = false; renderTiles(); renderPlayers();
    document.querySelector(`#players .row[data-id="${q.id}"] .qout`).click();
    const sum = mates.reduce((t, r) => t + r.min * (minScale[r.id] || 1), 0);
    const moved = mates.every(r => Math.abs(proj(r) - before[r.id] * (minScale[r.id] || 1)) < 1e-9);
    const out = { status: q.status, sum, moved, tag: !!document.querySelector(`#players .row[data-id="${mates[0].id}"]`) };
    document.querySelector(`#players .row[data-id="${q.id}"] .qout`).click();
    out.back = q.status === "Questionable" && mates.every(r => Math.abs(proj(r) - before[r.id]) < 1e-9) && !Object.keys(state.outs).length;
    return out;
  });
  check("mark out: he's Out, his teammates share exactly 200 minutes, projections moving with them; undo restores",
        qo && qo.status === "Out" && Math.abs(qo.sum - 200) < 1e-6 && qo.moved && qo.back, JSON.stringify(qo));
  // Doubtful: out by default (the server's flag, or a doubtful news item); Play him puts him back as Questionable, his team refit to 200
  const db = await pg.evaluate(() => {
    const d = rows.find(r => r.status !== "Out" && r._status0 !== "Questionable" && r.min > 10 && rows.filter(x => x.team === r.team && x.min > 0 && x.status !== "Out").length >= 6);
    const team = () => rows.filter(r => r.team === d.team && r.status !== "Out" && r.min > 0).reduce((t, r) => t + r.min * (minScale[r.id] || 1), 0);
    d.doubtful = true; d._status0 = "Out"; applyOuts(); view.panel = null; renderTiles(); renderPlayers();
    const out = { s1: d.status, refit1: Object.keys(minScale).length, tag: !!document.querySelector(`#players .row[data-id="${d.id}"] .tag.d`) };
    document.querySelector(`#players .row[data-id="${d.id}"] .qout`).click();
    Object.assign(out, { s2: d.status, t2: team(), ins: !!state.ins[d.id] });
    document.querySelector(`#players .row[data-id="${d.id}"] .qout`).click();
    out.s3 = d.status;
    delete d.doubtful; d._status0 = undefined; d.status = undefined;
    news.push({ id: "t1", kind: "doubtful", players: [d.id], at: new Date().toISOString(), author: "x", text: "doubtful", url: "#" });
    applyOuts(); out.s4 = d.status; out.t4 = team(); news.pop(); state.ins = {}; applyOuts(); renderPlayers(); out.s5 = d.status;
    return out;
  });
  check("doubtful: out by default (the server's flag: its projection already refit his team, so no refit here); Play him back as Questionable, " +
        "his team at 200; Undo out again; a doubtful news item: out, his team refit to 200",
        db.s1 === "Out" && db.refit1 === 0 && db.tag && db.s2 === "Questionable" && Math.abs(db.t2 - 200) < 1e-6 && db.ins && db.s3 === "Out" &&
        db.s4 === "Out" && Math.abs(db.t4 - 200) < 1e-6 && db.s5 === undefined, JSON.stringify(db));
  // the deep bench (team card): out of the pool by default, for the page and the sim; one tap brings him back
  const dp = await pg.evaluate(() => {
    const T = teamsOf(), t = T.teams[0], r = rows.find(x => x.team === t.team && x.status !== "Out");
    const keep = t.card; t.card = { games: 5, lines: [{ kind: "deep", text: "Deep bench" }], absorb: [], deep: [r.id], rule: "card-1" };
    applyOuts(); view.panel = null; renderTiles(); renderPlayers();
    const out = { deep: r.deepOut, page: usable(r), sim: DKSim.usable ? DKSim.usable(ctx(), r) : null, cls: document.querySelector(`#players .row[data-id="${r.id}"]`).classList.contains("excluded") };
    document.querySelector(`#players .row[data-id="${r.id}"] .deepin`).click();
    Object.assign(out, { back: !r.deepOut && usable(r) && !!state.deepIn[r.id] });
    t.card = keep; state.deepIn = {}; applyOuts(); renderPlayers();
    return out;
  });
  check("deep bench: out of the pool by default (page and sim), shown excluded; Use brings him back",
        dp.deep === true && dp.page === false && dp.sim === false && dp.cls && dp.back, JSON.stringify(dp));
  // no punts without news: under 15 projected minutes is out of the pool by default, unless a teammate is out and his
  // refit minutes pass his season average; Use brings him back
  const pu = await pg.evaluate(() => {
    const r = rows.find(x => x.status !== "Out" && x.min > 3 && x.min < 12 && !deepIds()[x.id] && rows.filter(y => y.team === x.team && y.status !== "Out" && y.min > 0).length >= 6 &&
      !rows.some(y => y.team === x.team && y.status === "Out"));
    const was = { min_avg: r.min_avg }; r.min_avg = r.min - 0.5;
    applyOuts(); const def = { punt: r.punt, out: r.deepOut, usable: usable(r), sim: DKSim.usable(ctx(), r) };
    const mate = rows.filter(y => y.team === r.team && y.id !== r.id && y.status !== "Out" && y.min > 20)[0];
    state.outs[mate.id] = 1; applyOuts(); const news = { punt: r.punt, min: r.min * (minScale[r.id] || 1), avg: r.min_avg };
    delete state.outs[mate.id]; applyOuts();
    view.panel = null; renderTiles(); renderPlayers();
    document.querySelector(`#players .row[data-id="${r.id}"] .deepin`).click(); const back = !r.deepOut && usable(r);
    state.deepIn = {}; r.min_avg = was.min_avg; applyOuts(); renderPlayers();
    return { def, news, back };
  });
  check("no punts without news: under 15 projected minutes out by default (page and sim); a teammate out raising him past his average lets him in; Use brings him back",
        pu.def.punt && pu.def.out && !pu.def.usable && pu.def.sim === false && (pu.news.min > pu.news.avg ? !pu.news.punt : true) && pu.back, JSON.stringify(pu));
  // the field after a Mark out: his field lineups swap him for a player who fits, ownership recounted; undo restores the field
  const fa = await pg.evaluate(() => {
    const F0 = fieldOf(), q = rows.filter(r => r.status !== "Out" && (F0.own[r.id] || 0) > 5 && rows.filter(x => x.team === r.team && x.min > 0 && x.status !== "Out").length >= 6)
      .sort((a, b) => F0.own[b.id] - F0.own[a.id])[0];
    const mates = rows.filter(r => r.team === q.team && r.id !== q.id && r.status !== "Out");
    const before = mates.reduce((t, r) => t + (F0.own[r.id] || 0), 0), n0 = F0.field.length;
    state.outs[q.id] = 1; applyOuts();
    const F = fieldOf(), by = {}; rows.forEach(r => { by[r.id] = r; });
    const legal = F.field.every(L => L.length === 8 && new Set(L).size === 8 && L.every(id => by[id] && by[id].status !== "Out") &&
      L.reduce((t, id) => t + by[id].salary, 0) <= 50000);
    const out = { own: F.own[q.id] || 0, n: F.field.length, n0, legal, sum: Object.values(F.own).reduce((t, x) => t + x, 0),
                  mates: mates.reduce((t, r) => t + (F.own[r.id] || 0), 0), before };
    delete state.outs[q.id]; applyOuts(); out.restored = fieldOf() === F0;
    return out;
  });
  check("mark out moves the field: he's in no field lineup, every lineup legal, ownership recounted (8 a lineup), his teammates owned more; undo restores",
        fa.own === 0 && fa.legal && fa.n >= fa.n0 * 0.95 && Math.abs(fa.sum - 800) < 1e-6 && fa.mates > fa.before && fa.restored, JSON.stringify(fa));
  check("fitMinutes: down to 200 and up to 200, none over 40", (() => true)() && await pg.evaluate(() => {
    const a = DKSim.fitMinutes([35, 35, 35, 35, 30, 25, 20, 10]), b = DKSim.fitMinutes([30, 28, 25, 20, 18, 15, 10]);
    const s = x => x.reduce((t, y) => t + y, 0);
    return Math.abs(s(a) - 200) < 1e-6 && Math.abs(s(b) - 200) < 1e-6 && Math.max(...b) <= 40;
  }));
  // EvanMiya's position, role and possessions on the row (a player without them shows none)
  const em = await pg.evaluate(() => { const r = rows.find(x => x.status !== "Out"); Object.assign(r, { em_pos: 1.69, em_role: 2.29, poss: 263, min_poss: 31.2 }); renderPlayers();
    const el = document.querySelector(`#players .row[data-id="${r.id}"] .nm`); const txt = el.title, tip = el.title;
    delete r.em_pos; delete r.em_role; delete r.poss; delete r.min_poss; renderPlayers(); return { txt, tip }; });
  const l5 = await pg.evaluate(() => { const r = rows.find(x => x.status !== "Out" && x.dk_avg); r.last5 = [["2026-11-12", 30, 24.5], ["2026-11-15", 34.4, 31], ["2026-11-17", 28, 18.25]]; renderPlayers();
    const el = document.querySelector(`#players .row[data-id="${r.id}"] .col-avg`); const t = el.title; delete r.last5; renderPlayers(); return t; });
  check("DK avg hover: his last games, newest first, minutes, DK points and per minute",
        l5.split("\n").length === 4 && /^Last 3, newest first/.test(l5) && /11\/17  28 min  18\.3 DK  0\.65\/min/.test(l5.split("\n")[1]) && /11\/12  30 min  24\.5 DK  0\.82\/min/.test(l5.split("\n")[3]), l5);
  check("EvanMiya in the name's tooltip: position, role and possessions, with what his possessions imply", /EvanMiya: pos 1\.7 role 2\.3 · 263 poss/.test(em.txt) && /31\.2 minutes/.test(em.tip), JSON.stringify(em));
  // the Players list (2026-11-19): Pos / Team / Opp columns, the matchup, line, double-double and fragile in the name's
  // tooltip (no grey line, no fragile badge), no ± column
  const pl = await pg.evaluate(() => {
    const heads = [...document.querySelectorAll("#players .head span[data-sort]")].map(x => x.textContent.replace(/ [↓↑]$/, ""));
    const r = rows.find(x => x.status !== "Out" && x.spread != null && x.ou), el = document.querySelector(`#players .row[data-id="${r.id}"]`), cells = [...el.children].map(c => c.textContent);
    const f = rows.find(x => x.fragile), fel = f && document.querySelector(`#players .row[data-id="${f.id}"]`);
    return { heads, sub: document.querySelectorAll("#players .sub").length, cells: cells.slice(2, 5), want: [r.position, r.team, (r.home ? "v " : "@ ") + r.opp],
             tip: el.querySelector(".nm").title, line: (r.spread > 0 ? "+" : "") + r.spread, ou: r.ou, frag: f ? { badge: !!fel.querySelector(".frag") === !!fragileMap()[f.id], tip: /Swingy: expected miss/.test(fel.querySelector(".nm").title) } : null };
  });
  check("Players list: Pos / Team / Opp columns, matchup and line in the name's tooltip, fragile in the tooltip, no ± column or grey line",
        JSON.stringify(pl.heads) === JSON.stringify(["Player", "Pos", "Team", "Opp", "Sal", "Proj", "Val", "Own", "Bank", "Min", "MPG", "OBPR", "DK avg", "Cash", "Read"]) && pl.sub === 0 &&
        JSON.stringify(pl.cells) === JSON.stringify(pl.want) && pl.tip.includes(pl.line) && pl.tip.includes("o/u " + pl.ou) && (!pl.frag || (pl.frag.badge && pl.frag.tip)), JSON.stringify(pl));
  // A4: fragile from the lenses: the badge only when 2+ lenses disagree with our number, the reasons in its hover
  const fragA4 = await pg.evaluate(() => { const m = fragileMap(), ids = Object.keys(m);
    const r = rows.find(x => x.status !== "Out" && x.status !== "Questionable" && proj(x) > 0 && !m[x.id]);
    const keep = r && { min_avg: r.min_avg, cv: r.min_cv, sal: r.salary };
    let made = null;
    if (r) { r.min_avg = (r.min || 0) + 10; r.min_cv = 0.5; r.salary = 3000; renderPlayers(); made = fragileMap()[r.id] || null;
      const el = document.querySelector('#players .row[data-id="' + r.id + '"] .tag.frag'); made = { reasons: made, badge: !!el, tip: el && el.title };
      Object.assign(r, { min_avg: keep.min_avg, min_cv: keep.cv, salary: keep.sal }); renderPlayers(); }
    return { n: ids.length, badges: document.querySelectorAll("#players .tag.frag").length, made, after: r ? !fragileMap()[r.id] : true };
  });
  check("fragile (A4): a badge only where 2+ lenses disagree (few a slate), its reasons in the hover; information only",
        fragA4.n <= 6 && fragA4.badges === fragA4.n && fragA4.made && fragA4.made.badge && fragA4.made.reasons.length >= 2 && /Fragile: /.test(fragA4.made.tip) && fragA4.after, JSON.stringify(fragA4));
  check("match warning: none when every game matched", !(await pg.$("#matchWarn")));
  const mw = await pg.evaluate(() => {
    const g = rows[0].game, kept = rows.map(r => r.event);
    rows.forEach(r => { if (r.game === g) delete r.event; });
    const t = matchText(), n = rows.filter(r => r.game === g).length;
    rows.forEach((r, i) => { r.event = kept[i]; });
    return { g, t, n };
  });
  const conflict = await pg.evaluate(() => [statusConflict({ status: "Out", status_file: "Out per EvanMiya 11/17", status_dk: "Questionable" }),
    statusConflict({ status: "Out", status_file: "Out per EvanMiya 11/17", status_dk: "O" }), statusConflict({ status: "Out", status_file: "Out per EvanMiya 11/17" })]);
  check("status: outs file against DraftKings shows both where they disagree, nothing where they agree",
        /Out per EvanMiya 11\/17 \/ DK: Q</.test(conflict[0]) && conflict[1] === "" && /DK: no tag/.test(conflict[2]), JSON.stringify(conflict));
  check("match warning: a red line naming the unmatched game and its players", mw.t.includes('class="bad"') && mw.t.includes(mw.n + " players unmatched") && mw.t.includes(mw.g), mw.t);

  // a player's L / X in the full list, which shows only with no team clicked
  const rowBtn = async (id, cls) => {
    await pg.evaluate(() => { view.panel = null; renderTiles(); });
    await pg.click(`#players .row[data-id="${id}"] .${cls}`);
  };
  const set = async (vals) => {
    for (const [id, v] of Object.entries(vals)) {
      if (typeof v === "boolean") await (v ? pg.check("#" + id) : pg.uncheck("#" + id));
      else await pg.fill("#" + id, String(v));
    }
  };
  // Draw & bank n lineups; returns the lineups this draw added to the bank and the status message
  const draw = async (n) => {
    const before = await pg.evaluate(() => BANK.lineups.length);
    await pg.fill("#bankN", String(n));
    await pg.evaluate(() => { document.getElementById("buildStatus").textContent = ""; });
    await pg.click("#bankDraw");
    await pg.waitForFunction(() => /^Banked|bad/.test(document.getElementById("buildStatus").textContent) || document.querySelector("#buildStatus .bad"), null, { timeout: 300000 });
    const L = await pg.evaluate(b => BANK.lineups.slice(b), before);
    return { L, msg: await pg.textContent("#buildStatus") };
  };
  const emptyBank = () => pg.evaluate(() => { BANK = { lineups: [], tags: [], tagRules: {} }; CUT = null; PF = {}; bankSaveState(); renderBank(); });
  const base = { levW: 0, minSal: 48500, maxTeam: 5, stackN: 0, stackBoth: false, maxOwn: "", lowN: 0, lowPct: 10 };
  const rulesOf = v => ({ minSal: v.minSal, maxTeam: v.maxTeam, stackN: v.stackN, stackBoth: v.stackBoth, maxOwn: v.maxOwn === "" ? null : +v.maxOwn, lowN: v.lowN, lowPct: v.lowPct });

  // the page reads top to bottom: the draw's settings, then the cut and the pick's (Max exposure, Min unique)
  const order = await pg.evaluate(() => ["levW", "maxOwn", "ruleList", "bankDraw", "entriesFile", "cutRun", "maxExpo", "minUnique", "pfRun", "pfExport", "bpTable"]
    .map(id => document.getElementById(id)).every((el, i, a) => i === 0 || (a[i - 1].compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING)));
  check("layout: draw settings, then the cut, then the pick's Max exposure and Min unique, then review", order);
  check("layout: the old one-contest flow is gone", await pg.evaluate(() => ["simPick", "build", "export", "saveEntries", "bankBuilt", "contest", "nCand", "nLineups", "bpBuild", "bpUse", "bpSave"].every(id => !document.getElementById(id))));

  // Draw & bank under each setting: every lineup drawn is legal and within it, and tagged with it
  for (const [name, extra, tag] of [["defaults", {}, "no rules"], ["game stack 3, both teams", { stackN: 3, stackBoth: true }, "3-stack + bring-back"],
                                    ["max total own 150%", { maxOwn: 150 }, "own ≤ 150%"], ["2 players under 10% owned", { lowN: 2 }, "2 under 10%"],
                                    ["all three", { stackN: 3, stackBoth: true, maxOwn: 150, lowN: 2 }, "3-stack + bring-back + own ≤ 150% + 2 under 10%"]]) {
    const v = Object.assign({}, base, extra);
    await set(v);
    check("tag line shows the next draw's idea, " + name, (await pg.textContent("#tagNow")) === "Next draw is tagged: " + tag, await pg.textContent("#tagNow"));
    const { L, msg } = await draw(20);
    audit("Draw & bank, " + name, L, rulesOf(v));
    if (L.length < 15) check("Draw & bank, " + name + ": drew 15+ new", false, msg);
    check("Draw & bank, " + name + ": tagged with its idea", new RegExp('tagged "' + tag.replace(/[+]/g, "\\+") + '"').test(msg), msg);
  }
  // the bank check before Re-sim & cut: the bank's and the field's projection and ownership, ideas well under the field flagged
  const bc = await pg.evaluate(() => {
    renderBank(); const t = document.getElementById("bankCheck").textContent, F = fieldOf();
    const pts = ids => ids.reduce((u, id) => u + proj(byId(id)), 0), want = BANK.lineups.reduce((u, l) => u + pts(l.ids), 0) / BANK.lineups.length;
    const fp = F.field.reduce((u, l) => u + pts(l), 0) / F.field.length;
    return { t, want: Math.round(want), fp: Math.round(fp), tagged: BANK.tagRules[Object.keys(BANK.tagRules)[0]].nightS };
  });
  check("bank check: the bank's and the field's average projection and ownership, before Re-sim & cut; the idea's bank noise saved",
        new RegExp("^Bank check: bank " + bc.want + " pts, \\d+% own; field " + bc.fp + " pts, \\d+% own: the bank projects \\d+ (below|above) the field").test(bc.t) && bc.tagged === 0.35, JSON.stringify(bc));
  // ownership position: the simulated field's own-sum quartiles and the bank's percentile in it, computed independently
  const op = await pg.evaluate(() => {
    const F = fieldOf(), ow = ids => ids.reduce((u, id) => u + (F.own[id] || 0), 0), v = F.field.map(ow).sort((a, b) => a - b);
    const q = p => Math.round(v[Math.min(v.length - 1, Math.floor(p * v.length))]), m = BANK.lineups.reduce((u, l) => u + ow(l.ids), 0) / BANK.lineups.length;
    const pc = Math.round(100 * v.filter(x => x < m).length / v.length), t = document.getElementById("bankCheck").textContent;
    return { t, want: "field own sum " + [q(0.1), q(0.25), q(0.5), q(0.75)].join(" / ") + "% (10th / 25th / median / 75th); bank at the field's " + pc, pc };
  });
  check("bank check: ownership position, the field's own-sum 10th / 25th / median / 75th and the bank's percentile in it", op.t.includes("Ownership position: " + op.want), JSON.stringify(op));
  // the sim-night draw: a drawn lineup is the solver's best for one simulated night (nightPoints, the sim's distribution)
  const nightCheck = await pg.evaluate(async () => {
    const out = [];
    for (const seed of [5, 6, 7]) {
      const cx = ctx(), o = Object.assign(drawRules(), { conds: [] });
      cx.random = DKSim.seeded(seed);
      const night = DKSim.nightPoints(cx, fieldDoc.z, o.nightS);
      const best = (await DKSim.solve(cx, Object.assign({}, o, { n: 1, minUnique: 1, noCaps: true, night }))).lineups[0];
      cx.random = DKSim.seeded(seed);
      const drawn = (await DKSim.poolDraw(cx, o, 1)).lineups[0];
      const score = L => L.ids.reduce((t, id) => t + night[id], 0);
      out.push({ same: best.ids.slice().sort().join() === drawn.ids.slice().sort().join(), night: score(drawn),
                 proj: drawn.ids.reduce((t, id) => t + proj(byId(id)), 0), varied: Object.keys(night).some(id => Math.abs(night[id] - proj(byId(id))) > 1) });
    }
    return out;
  });
  check("sim-night draw: each lineup is the best one for its simulated night", nightCheck.every(x => x.same && x.varied), JSON.stringify(nightCheck));
  // Bank noise: the bank's nights pulled toward the projection (0.35 by default) project higher than at full noise; the
  // nights a player gets scale with it; the setting is saved with each idea
  const bn = await pg.evaluate(async () => {
    const run = async s => { const cx = ctx(); cx.random = DKSim.seeded(11); const o = Object.assign(drawRules(), { conds: [], nightS: s });
      const L = (await DKSim.poolDraw(cx, o, 40)).lineups; return L.reduce((t, l) => t + l.ids.reduce((u, id) => u + proj(byId(id)), 0), 0) / L.length; };
    const cx = ctx(), r = rows.find(x => x.status !== "Out" && proj(x) > 15);
    cx.random = DKSim.seeded(3); const a = DKSim.nightPoints(cx, fieldDoc.z, 1)[r.id];
    cx.random = DKSim.seeded(3); const b = DKSim.nightPoints(cx, fieldDoc.z, 0.35)[r.id];
    return { def: drawRules().nightS, full: await run(1), shrunk: await run(0.35), scaled: Math.abs((b - proj(r)) - 0.35 * (a - proj(r))) < 1e-9 || a === 0 };
  });
  check("bank noise: 0.35 by default; a bank drawn at 0.35 projects above one at 1; each night's deviation scales by it",
        bn.def === 0.35 && bn.shrunk > bn.full && bn.scaled, JSON.stringify(bn));
  const ownOf = L => L.reduce((t, l) => t + l.ids.reduce((u, id) => u + (OWN[id] || 0), 0), 0) / L.length;
  await set(Object.assign({}, base, { levW: 0.5 }));
  check("tag line carries the Leverage weight", /leverage 0\.5/.test(await pg.textContent("#tagNow")), await pg.textContent("#tagNow"));
  const { L: Llev } = await draw(15);
  await set(base);
  const { L: L0, msg: m0 } = await draw(15);
  // the saturation light: new / repeats / near-copies, coloured by fresh = (new - near-copies) / asked
  const sat = await pg.evaluate(() => ({ el: (document.querySelector("#buildStatus .sat") || {}).className, text: (document.querySelector("#buildStatus .sat") || {}).textContent,
    rules: [saturation(100, 90, 5, false), saturation(100, 70, 5, false), saturation(100, 60, 20, false), saturation(100, 90, 0, true)].map(x => x.level),
    near: (() => { const L = BANK.lineups[0], copy = { ids: L.ids.slice(0, 7).concat(["x"]), slots: [] }, same = { ids: L.ids.slice(), slots: [] }; return [nearCopies([copy]), nearCopies([same])]; })() }));
  const satM = /^Banked (\d+) new · (\d+) repeats · (\d+) near-copies \(7 of 8 shared with a banked lineup\)/.exec(m0);
  const satFr = satM ? Math.max(0, +satM[1] - +satM[3]) / 15 : -1, wantLvl = L0.length < 15 ? "red" : satFr >= 0.75 ? "green" : satFr >= 0.5 ? "amber" : "red";
  check("saturation light: new · repeats · near-copies after each Draw & bank, coloured by the fresh share (green 75%+, amber 50-75, red under 50 or tapped out)",
        !!satM && sat.el === "sat sat-" + wantLvl && new RegExp("^" + Math.round(100 * satFr) + "% fresh").test(sat.text) && JSON.stringify(sat.rules) === JSON.stringify(["green", "amber", "red", "red"]) &&
        JSON.stringify(sat.near) === JSON.stringify([1, 0]), JSON.stringify([m0, sat, wantLvl]));
  // Draw the 9 (a 2 x 2 sweep here for speed): one batch per leverage x under combination, each tagged "<idea> L.. U..",
  // grouped under the idea, its saved rules carrying its own levW / lowN; the panel put back; the status says what happened
  const sw = await pg.evaluate(async () => {
    const n0 = BANK.lineups.length, keepN = $("bankN").value; $("bankN").value = "10"; $("sweepLev").value = "0, 0.1"; $("sweepLow").value = "0, 1";
    $("sweepLev").dispatchEvent(new Event("change")); $("levW").value = "0.05"; $("lowN").value = "0";
    $("levW").value = 0; const idea = tagNow(); $("levW").value = "0.05";
    const label = $("bankDraw9").textContent;
    await drawSweep();
    const tags = ["L0 U0", "L0 U1", "L0.1 U0", "L0.1 U1"].map(x => idea + " " + x), have = tags.filter(t => BANK.tagRules[t]);
    const out = { label, idea, have: have.length, grouped: have.every(t => BANK.groups[t] === idea), rules: have.map(t => [BANK.tagRules[t].levW, BANK.tagRules[t].lowN]),
      restored: $("levW").value === "0.05" && $("lowN").value === "0", grew: BANK.lineups.length > n0, msg: $("buildStatus").textContent,
      remembered: JSON.parse(localStorage.getItem("dkcbb:sweep") || "{}").lev === "0, 0.1" };
    $("bankN").value = keepN; $("sweepLev").value = "0, 0.1, 0.2"; $("sweepLow").value = "0, 1, 2"; $("sweepLev").dispatchEvent(new Event("change")); $("levW").value = "0";
    return out;
  });
  check("Draw the 9: one batch per leverage x under (here 2 x 2), each tagged '<idea> L.. U..' and grouped under the idea, its rules recording its own levW / lowN; the panel put back; remembered sweep; the status line",
        sw.label === "Draw the 4" && sw.have === 4 && sw.grouped && JSON.stringify(sw.rules) === JSON.stringify([[0, 0], [0, 1], [0.1, 0], [0.1, 1]]) && sw.restored && sw.grew && sw.remembered &&
        /^Draw the 4: 4 batches banked under .+, \d+ new, \d+ repeats\.?/.test(sw.msg), JSON.stringify(sw));
  // template 5, at least N from these players: +set on a player row adds a chip; the rule saves as {type: "min", ids, n}
  // and every lineup drawn under it holds N of them
  const top3 = await pg.evaluate(() => rows.filter(r => r.status !== "Out" && !r.deepOut).sort((a, b) => proj(b) - proj(a)).slice(0, 3).map(r => r.id));
  await pg.evaluate(() => { $("rtType").value = "if"; $("rtFrom").value = "opp"; Array.from($("rtList").options).forEach(o => { o.selected = false; }); rtChips(); showEditor(); });
  for (const id of top3) await pg.click(`#players .row[data-id="${id}"] .setadd`, { timeout: 15000 });
  const t5 = await pg.evaluate(() => ({ type: $("rtType").value, chips: Array.from($("rtList").selectedOptions).map(o => o.value), shown: !document.querySelector("#ruleEditor .rt-list").hidden }));
  await pg.fill("#rtN", "2");
  const nR = await pg.evaluate(() => state.rules.length);
  await pg.click("#rtSave");
  const t5r = await pg.evaluate(n => state.rules[n], nR);
  const { L: L5 } = await draw(12);
  check("rule template 5: +set adds each player as a chip (switching the editor to template 5); Add rule saves at least N of them; every lineup drawn holds N",
        t5.type === "min" && t5.shown && JSON.stringify(t5.chips.slice().sort()) === JSON.stringify(top3.slice().sort()) && t5r && t5r.type === "min" && t5r.n === 2 &&
        JSON.stringify(t5r.ids.slice().sort()) === JSON.stringify(top3.slice().sort()) && /^at least 2 of /.test(t5r.label) && L5.length > 0 && L5.every(L => L.ids.filter(id => top3.includes(id)).length >= 2),
        JSON.stringify([t5, t5r, L5.length]));
  await pg.evaluate(n => { state.rules.splice(n, 1); save(); renderRules(); Array.from($("rtList").options).forEach(o => { o.selected = false; }); rtChips(); $("rtType").value = "if"; showEditor(); }, nR);
  check("Leverage weight: lineups drawn with it hold less projected ownership", Llev.length >= 10 && ownOf(Llev) < ownOf(L0),
        "with weight " + ownOf(Llev).toFixed(0) + "%, without " + ownOf(L0).toFixed(0) + "%");

  // Max exposure and Min unique don't touch the draw
  await set(base); await pg.fill("#maxExpo", "5"); await pg.fill("#minUnique", "8");
  const { L: Lx, msg: mx } = await draw(15);
  check("Max exposure: 60% by default (the operator, 2026-11-20)", await pg.evaluate(() => document.getElementById("maxExpo").defaultValue === "60"));
  check("Max exposure and Min unique don't limit the draw", Lx.length >= 12, mx);
  await pg.fill("#maxExpo", "60"); await pg.fill("#minUnique", "3");

  // locks and excludes: in the draw, and in the tag
  const ids = Object.keys(P).filter(id => P[id].status !== "Out").sort((a, c) => P[c].fp_dk / P[c].salary - P[a].fp_dk / P[a].salary);
  const lockId = ids[3], exclId = ids[0];
  await set(base);
  await rowBtn(lockId, "lock");
  await rowBtn(exclId, "excl");
  const { L: Ll, msg: ml } = await draw(15);
  audit("Draw & bank, a lock and an exclude", Ll, Object.assign(rulesOf(base), { lock: lockId, excl: exclId }));
  check("a lock and an exclude are in the tag", /lock .* \+ no /.test(ml), ml);
  await pg.click("#clearLx");

  // the projection gate: an open band blends DraftKings' average into Proj
  gate = { nights: 9, bands: [{ lo: 6000, hi: 99999, open: true, w: 0.6 }, { lo: 0, hi: 5999, open: false, w: 1 }] };
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate: OPEN/.test(document.getElementById("statusInfo").textContent));
  const pick = Object.keys(P).find(id => P[id].salary >= 6000 && P[id].dk_avg > 0 && P[id].status !== "Out");
  const cheap = Object.keys(P).find(id => P[id].salary < 6000 && P[id].dk_avg > 0 && P[id].status !== "Out");
  const shown = await pg.evaluate(([a, c]) => [proj(rows.find(r => r.id === a)), proj(rows.find(r => r.id === c))], [pick, cheap]);
  check("gate blends where open", Math.abs(shown[0] - (0.6 * P[pick].fp_dk + 0.4 * P[pick].dk_avg)) < 1e-9, JSON.stringify(shown));
  check("gate leaves closed bands alone", Math.abs(shown[1] - P[cheap].fp_dk) < 1e-9);
  // the Questionable discount: a Q player at his (gated) projection x the measured factor; everyone else as before
  gate = { nights: 9, bands: [{ lo: 6000, hi: 99999, open: true, w: 0.6 }, { lo: 0, hi: 5999, open: false, w: 1 }],
           questionable: { factor: 0.2, n: 10, actual: 30, projected: 150 } };
  await pg.click("#reload");
  await pg.waitForFunction(() => /Questionable players are projected at x0\.20/.test(document.getElementById("statusInfo").textContent));
  const qid = Object.keys(P).find(id => P[id].status === "Questionable" && P[id].fp_dk > 0);
  const qs = await pg.evaluate(([q, a]) => [proj(rows.find(r => r.id === q)), proj(rows.find(r => r.id === a))], [qid, pick]);
  const qBase = P[qid].salary >= 6000 && P[qid].dk_avg ? 0.6 * P[qid].fp_dk + 0.4 * P[qid].dk_avg : P[qid].fp_dk;
  check("questionable: projected at his projection x the factor", Math.abs(qs[0] - 0.2 * qBase) < 1e-9, JSON.stringify([qs[0], qBase]));
  check("questionable: others unchanged", P[pick].status === "Questionable" || Math.abs(qs[1] - shown[0]) < 1e-9);

  // --- team tiles and rules -----------------------------------------------------------------------------
  const TEAMS = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_teams.json"))).slates[String(slate.draft_group_id)];
  gate = null;
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate: closed/.test(document.getElementById("statusInfo").textContent));
  const openTeam = async team => {
    if (!(await pg.$(`#teamPanel .tile[data-team="${team}"]`))) await pg.click(`#teamBar button[data-team="${team}"]`);
    await pg.waitForSelector(`#teamPanel .tile[data-team="${team}"]`);
  };
  check("team bar: one button per team, slate line shown", (await pg.$$eval("#teamBar button", t => t.length)) === TEAMS.teams.length &&
        /games · \d+ spreads? of 15\+/.test(await pg.textContent("#slateLine")), await pg.textContent("#slateLine"));
  const chipsG = await pg.evaluate(() => {
    const gs = [...document.querySelectorAll("#teamBar .gchip")].map(c => ({ game: c.dataset.game, teams: [...c.querySelectorAll("button")].map(b => b.dataset.team), cls: [...c.querySelectorAll("button")].map(b => b.className) }));
    const T = teamsOf(), ou = g => { const r = rows.find(x => x.game === g && x.ou); return r ? +r.ou : -1; }, key = gs.map(g => [ou(g.game), tipOf(g.game) || "~"]);
    return { gs, key, ordered: key.every((x, i) => i === 0 || key[i - 1][0] > x[0] || (key[i - 1][0] === x[0] && key[i - 1][1] <= x[1])), sameGame: gs.every(g => g.teams.every(t => gameOf(t) === g.game) && g.teams.join("@") === g.game || g.teams.length === 1),
             colours: gs.every(g => g.teams.every((t, i) => g.cls[i] === T.teams.find(x => x.team === t).verdict)) };
  });
  check("team bar: chips grouped by game (away | home in one chip), ordered by o/u (highest first, a tie by the earlier tip), each team keeping its colour", chipsG.gs.length > 1 && chipsG.ordered && chipsG.sameGame && chipsG.colours, JSON.stringify(chipsG));
  await openTeam(TEAMS.teams[0].team);
  const panel = await pg.evaluate(() => [...document.querySelectorAll("#teamPanel .tile")].map(t => t.dataset.team));
  const opp0 = TEAMS.teams.find(t => t.team !== TEAMS.teams[0].team && TEAMS.teams[0].game === t.game);
  const card = await pg.evaluate(() => {
    const T = teamsOf(), t = T.teams[0], mates = rows.filter(r => r.team === t.team && r.status !== "Out" && r.min > 0);
    const keep = t.card, sit = mates[0];
    t.card = { games: 5, rule: "card-1", deep: [mates[mates.length - 1].id],
               lines: [{ kind: "swingy", text: mates[1].name + " is swingy: 10 to 30 minutes over 5 games", dk_id: mates[1].id, tag: "swingy 10\u201330" },
                       { kind: "deep", text: "Deep bench, out of the pool by default: someone (1 a game)", dk_id: null, tag: null }],
               mins: { [mates[2].id]: { season: 24.4, last3: 30.2, played: 4, of: 5 }, [mates[1].id]: { season: 20, last3: 18, played: 2, of: 5 } },
               absorb: [{ name: sit.name, dk_id: sit.id, sat: 1, games: 5, rows: [{ name: mates[1].name, dk_id: mates[1].id, with: 20, without: 30, n_with: 4, n_without: 1 }] }] };
    renderTeamPanel();
    const el = () => document.querySelector('#teamPanel details.card[data-card="' + t.team + '"]');
    const a = el().textContent, rot = [...el().querySelectorAll("table.rot tr[data-id]")].map(tr => tr.dataset.id);
    const want = rows.filter(r => r.team === t.team && r.status !== "Out" && (r.min || 0) * (minScale[r.id] || 1) >= 10).sort((x, y) => proj(y) - proj(x)).slice(0, 9).map(r => r.id);
    const rowOf = id => { const tr = el().querySelector('table.rot tr[data-id="' + id + '"]'); return tr ? [...tr.children].map(td => td.textContent) : null; };
    const projOk = rot.every(id => +rowOf(id)[1] === +proj(byId(id)).toFixed(0));
    const r1 = rowOf(mates[1].id), r2 = rowOf(mates[2].id);
    // an Out the pipeline already has: its out_gain / out_from show as "+N min (outs: X)" (display only)
    const m3 = byId(mates[2].id); m3.out_gain = 2.4; m3.out_from = "Kai Shinholster"; renderTeamPanel();
    const r3 = rowOf(mates[2].id); delete m3.out_gain; delete m3.out_from; renderTeamPanel();
    state.outs[sit.id] = 1; applyOuts(); renderTeamPanel();
    const b = el().textContent, firstOut = el().querySelector("summary").nextElementSibling, tbl = !!el().querySelector("table:not(.rot)");
    delete state.outs[sit.id]; t.card = keep; applyOuts(); renderTeamPanel();
    return { a, b, rot, want, projOk, r1, r2, r3, first: firstOut && firstOut.textContent, tbl };
  });
  check("team card: a pipeline Out shows on his teammates as \"+N min (outs: X)\"", card.r3 && /\+2 min \(outs: Shinholster\)/.test(card.r3[5]), JSON.stringify(card.r3));
  check("team card: the game count; one rotation table in projection order (the Players list's Proj, whole points), season / last-3 minutes and tags (swingy, missed k of n, thin game counts); no per-player paragraphs or deep-bench sentence; an Out player's with / without table first",
        /Team card · 5 games/.test(card.a) && JSON.stringify(card.rot) === JSON.stringify(card.want) && card.rot.length >= 3 && card.projOk &&
        card.r1 && /swingy 10\u201330/.test(card.r1[5]) && /missed 3 of 5/.test(card.r1[5]) && /\(2 g\)/.test(card.r1[3]) &&
        card.r2 && card.r2[3] === "24" && card.r2[4] === "30" && /missed 1 of 5/.test(card.r2[5]) &&
        !/is swingy/.test(card.a) && !/Deep bench, out of the pool/.test(card.a) && !/is out tonight/.test(card.a) &&
        card.tbl && /is out tonight; when he sat before \(1 of 5 games\)/.test(card.first || ""), JSON.stringify(card));
  const an = await pg.evaluate(() => {
    const t = teamsOf().teams[0], keep = analyst;
    analyst = [{ id: "a1", author: "BuriedTreys", at: new Date().toISOString(), url: "https://x.com/BuriedTreys/status/1", text: "Game writeup text",
                 teams: t.game.split("@"), games: [t.game], players: [], writeup: true, kind: "analyst" },
               { id: "a2", author: "BuriedTreys", at: new Date(Date.now() - 864e5).toISOString(), url: "https://x.com/BuriedTreys/status/2", text: "A team note",
                 teams: [t.team], games: [], players: [], writeup: false, kind: "analyst" }];
    renderTeamPanel();
    const tile = document.querySelector('#teamPanel .tile[data-team="' + t.team + '"]'), card = document.querySelector('#teamPanel details.card[data-card="' + t.team + '"]');
    const chip = tile.querySelector('a[href="https://x.com/BuriedTreys/status/1"]'), first = [...card.querySelectorAll(".cl")].find(x => /writeup/.test(x.textContent));
    const out = { chip: chip && chip.textContent, first: first && first.textContent, notes: /Analyst notes/.test(card.textContent) && /A team note/.test(card.textContent),
                  noNews: !rows.some(r => newsOf(r.id) && newsOf(r.id).kind === "analyst") };
    analyst = keep; renderTeamPanel();
    return out;
  });
  check("analyst: a writeup of tonight's game is a chip on the tile, linked, and in the card with the analysts' posts at the bottom; the week's notes in their own section; never a player's news tag",
        an.chip === "BuriedTreys writeup" && /writeup: Game writeup text/.test(an.first || "") && an.notes && an.noNews, JSON.stringify(an));
  check("team panel: the team's tile, then its opponent's", JSON.stringify(panel) === JSON.stringify([TEAMS.teams[0].team, opp0 && opp0.team]), JSON.stringify(panel));
  const gv = await pg.evaluate(() => {
    const ids = [...document.querySelectorAll("#teamPanel .plist .row")].map(r => r.dataset.id), teams = new Set(ids.map(id => byId(id).team));
    const v = ids.map(id => byId(id)).filter(r => r.status !== "Out").map(value), t = teamsOf().teams.find(x => x.team === view.panel);
    return { teams: [...teams].sort(), want: [t.team, oppOf(t.team)].sort(), sorted: v.every((x, i) => i === 0 || v[i - 1] >= x), lists: document.querySelectorAll("#teamPanel .plist").length,
             pressed: [...document.querySelectorAll("#teamBar button[aria-pressed=true]")].map(b => b.dataset.team).sort(), head: !!document.querySelector("#teamPanel .gamehead"),
             heads: [...document.querySelectorAll("#teamPanel .plist .head span[data-sort]")].length,
             blank: !scanNow() && [...document.querySelectorAll("#teamPanel .scanblk")].length === 2 && [...document.querySelectorAll("#teamPanel .scanblk")].every(b => /–/.test(b.textContent) && b.querySelector("a.scanlink")) };
  });
  check("game view: the game header, both team cards with a Scan block (– and a Scan the slate link before a scan), then one player list for both teams, sorted by Val, with the Players list's columns; both chips pressed",
        gv.head && gv.blank && gv.lists === 1 && JSON.stringify(gv.teams) === JSON.stringify(gv.want) && gv.sorted && gv.heads >= 13 && JSON.stringify(gv.pressed) === JSON.stringify(gv.want), JSON.stringify(gv));
  const gs2 = await pg.evaluate(() => {
    const t = view.panel, o = oppOf(t);
    document.querySelector('#teamBar button[data-team="' + o + '"]').click();
    const a = [...document.querySelectorAll("#teamPanel .tile")].map(x => x.dataset.team);
    document.querySelector('#teamPanel .plist .head [data-sort="proj"]').click();
    const p = [...document.querySelectorAll("#teamPanel .plist .row")].map(r => byId(r.dataset.id)).filter(r => r.status !== "Out").map(proj);
    view.sort = "value"; view.dir = -1;
    document.querySelector('#teamBar button[data-team="' + t + '"]').click();
    return { a, want: [o, t], sortedProj: p.every((x, i) => i === 0 || p[i - 1] >= x), back: view.panel === t };
  });
  check("game view: the other team's chip opens the same game with it first; the list sorts by a header click",
        JSON.stringify(gs2.a) === JSON.stringify(gs2.want) && gs2.sortedProj && gs2.back, JSON.stringify(gs2));
  const pv = await pg.evaluate(() => [...document.querySelectorAll("#teamPanel .plist .row")].map(r => { const x = rows.find(y => y.id === r.dataset.id); return value(x); }));
  check("team panel: only players at 2x value or better", pv.length > 0 && pv.every(v => v >= 2), JSON.stringify(pv));
  check("team panel: the full player list hides while a team is open", await pg.$eval("#playersSec", x => x.hidden));
  const nShown = pv.length;
  await pg.click("#teamPanel .showall");
  const nAll = await pg.$$eval("#teamPanel .plist .row", r => r.length);
  check("team panel: Show all shows every player", nAll > nShown, nShown + " -> " + nAll);
  await pg.click("#teamPanel .showall");
  check("colour: Value and Own in a green gradient", (await pg.$$eval("#teamPanel .row .val[style], #teamPanel .row .own[style]", x => x.length)) > 0);
  check("layout: slate details folded away, the old contest list gone", !(await pg.$eval("#slateInfo", d => d.open)) && !(await pg.$("#contests")));
  check("news: collapsed by default", !(await pg.$eval("#newsBox", d => d.open)));
  const clearRules = () => pg.evaluate(() => { state.rules = []; state.lock = {}; state.excl = {}; save(); renderRules(); renderPlayers(); });
  const rulesNow = () => pg.evaluate(() => state.rules.slice());
  const drawAudit = async (name) => {
    await set(base);
    const { L, msg } = await draw(12);
    const R = await rulesNow();
    const bad = [];
    L.forEach((l, i) => R.forEach(r => { if (!obeys(r, l.ids)) bad.push(`#${i + 1} breaks "${r.label}"`); }));
    check(`rules, ${name}: ${L.length} lineups drawn obey every rule`, L.length > 0 && !bad.length, bad.slice(0, 3).join("; ") || msg);
    return L;
  };
  const tile = TEAMS.teams.find(t => t.top && t.top.length >= 3 && t.verdict !== "FADE");
  const tsel = `.tile[data-team="${tile.team}"]`;

  // the tile buttons
  for (const act of ["min2", "min3", "stack", "excl"]) {
    await clearRules();
    await openTeam(tile.team); await pg.click(`${tsel} button[data-act="${act}"]`);
    const R = await rulesNow();
    check(`tile button ${act} writes its rule${R.length > 1 ? "s" : ""}`, R.length === (act === "stack" ? 2 : 1), JSON.stringify(R.map(r => r.label)));
    await drawAudit("tile " + act);
  }
  check("rules stay in the box after a draw", (await rulesNow()).length === 1);
  check("rules list shows the pass counts after a draw", (await pg.$$eval(".rule .pc", x => x.length)) === 1);
  // the #1 player's shortcuts, and editing one after
  await clearRules();
  await openTeam(tile.team); await pg.click(`${tsel} button[data-act="pivot"]`);
  await openTeam(tile.team); await pg.click(`${tsel} button[data-act="bring"]`);
  let R = await rulesNow();
  check("tile shortcuts: pivot and bring-back", R.length === 2 && R[0].type === "ifnot" && R[1].type === "if" && R[0].ids[0] === tile.top[0].id &&
        JSON.stringify(R[0].set) === JSON.stringify([tile.top[1].id, tile.top[2].id]), JSON.stringify(R.map(r => r.label)));
  await pg.click('.rule[data-i="1"] button[data-act="edit"]');
  await pg.fill("#rtN", "2"); await pg.click("#rtSave");
  R = await rulesNow();
  check("rules: a shortcut can be edited after", R.length === 2 && R[1].n === 2 && /then 2\+ from/.test(R[1].label), JSON.stringify(R.map(r => r.label)));
  await drawAudit("pivot and bring-back (edited)");

  // the four templates through the editor, each with its condition forced on and forced off
  const addRule = async (type, f) => {
    await pg.selectOption("#rtType", type);
    await f();
    await pg.click("#rtSave");
  };
  const p1 = tile.top[0].id, p2 = tile.top[1].id;
  const t2 = TEAMS.teams.find(t => t.team !== tile.team && t.team !== tile.opp && t.top && t.top.length >= 3);
  // 1. if P then 2+ from his opponent
  await clearRules();
  await addRule("if", async () => { await pg.selectOption("#rtP", p1); await pg.fill("#rtN", "2"); await pg.selectOption("#rtFrom", "opp"); });
  await rowBtn(p1, "lock");
  let L2 = await drawAudit("template 1, condition met (he's locked)");
  check("template 1: met in every lineup", L2.every(l => l.ids.includes(p1)));
  await rowBtn(p1, "excl");
  L2 = await drawAudit("template 1, condition not met (he's excluded)");
  check("template 1: not met, lineups free of it", L2.every(l => !l.ids.includes(p1)));
  // 2. if NOT P then 1+ of his team's #2/#3
  await clearRules();
  await addRule("ifnot", async () => { await pg.selectOption("#rtP", p1); await pg.dispatchEvent("#rtP", "change"); await pg.fill("#rtN", "1"); });
  R = await rulesNow();
  check("template 2: list starts as his team's #2 and #3", R[0] && R[0].set.length === 2 && R[0].set.every(id => P[id].team === P[p1].team && id !== p1), JSON.stringify(R));
  await rowBtn(p1, "excl");
  L2 = await drawAudit("template 2, condition met (he's excluded)");
  await rowBtn(p1, "lock");
  L2 = await drawAudit("template 2, condition not met (he's locked)");
  check("template 2: not met in every lineup", L2.every(l => l.ids.includes(p1)));
  // "These players" by search: type, Enter adds the first match; a chip click drops one; the rule holds the choice
  await clearRules();
  await pg.selectOption("#rtType", "ifnot");
  await pg.selectOption("#rtP", p1); await pg.dispatchEvent("#rtP", "change");
  check("search: the starting list shows as chips", await pg.$$eval("#rtChips button", b => b.length) === 2);
  const far = t2.top[0].id, farName = P[far].name;
  await pg.fill("#rtSearch", farName.split(" ").slice(-1)[0].slice(0, 5));
  check("search: matches listed as you type", await pg.$$eval("#rtMatches [data-add]", (b, id) => b.some(x => x.dataset.add === id), far));
  await pg.fill("#rtSearch", farName); await pg.press("#rtSearch", "Enter");
  check("search: Enter adds the first match as a chip", await pg.$$eval("#rtChips [data-drop]", (b, id) => b.some(x => x.dataset.drop === id), far));
  await pg.fill("#rtSearch", P[p1].team);
  check("search: a team code lists only that team", await pg.$$eval("#rtMatches [data-add]", (b, ids) => b.length > 0 && b.every(x => ids.includes(x.dataset.add)),
    Object.keys(P).filter(id => P[id].team === P[p1].team)));
  const before = await pg.$$eval("#rtChips button", b => b.length);
  await pg.click("#rtMatches [data-add]");
  check("search: clicking a match adds it and keeps the search open", await pg.$$eval("#rtChips button", b => b.length) === before + 1
    && await pg.inputValue("#rtSearch") === P[p1].team);
  const dropped = await pg.$eval("#rtChips [data-drop]", b => b.dataset.drop);
  await pg.click("#rtChips [data-drop]");
  await pg.click("#rtSave");
  R = await rulesNow();
  check("search: the rule holds the chips' players", R[0] && R[0].set.length === before && R[0].set.includes(far) && !R[0].set.includes(dropped), JSON.stringify(R));
  // a rule's on/off box: off stays listed (and saved), the draw and the tag skip it; on brings it back
  await addRule("never", async () => { await pg.selectOption("#rtP", p1); await pg.selectOption("#rtQ", p2); });
  const offLab = (await rulesNow())[0].label;
  await pg.uncheck('#ruleList .rule[data-i="0"] .ruleOn');
  const offNow = await pg.evaluate(() => ({ n: state.rules.length, off: !!state.rules[0].off, conds: drawRules().conds.map(r => r.label),
    tag: document.getElementById("tagNow").textContent, grey: document.querySelector('#ruleList .rule[data-i="0"]').classList.contains("off") }));
  check("rule toggle: off stays listed, greyed, saved off", offNow.n === 2 && offNow.off && offNow.grey);
  check("rule toggle: the draw and the tag skip an off rule", !offNow.conds.includes(offLab) && offNow.conds.length === 1 && !offNow.tag.includes(offLab));
  await pg.check('#ruleList .rule[data-i="0"] .ruleOn');
  check("rule toggle: on again, back in the draw", await pg.evaluate(l => drawRules().conds.some(r => r.label === l), offLab));
  // platoon pairs on the tiles: shown with their minutes correlation and games; one click adds Never together, marked
  // src "platoon" for grading, and the mark survives an edit that keeps the pair; heavy favorites carry the bench note
  const plat = TEAMS.teams.find(t => (t.platoon || []).length);
  await clearRules();
  await openTeam(plat.team);
  const pb = `.tile[data-team="${plat.team}"] button[data-act="platoon"]`;
  check("platoon: the tile lists its pairs", await pg.$$eval(pb, b => b.length) === plat.platoon.length);
  check("platoon: the button shows the minutes correlation and games",
    (await pg.textContent(pb)).includes(plat.platoon[0].corr.toFixed(2) + " over " + plat.platoon[0].games + " games"));
  await pg.click(pb);
  R = await rulesNow();
  const pp = plat.platoon[0];
  check("platoon: one click adds Never together, marked for grading", R.length === 1 && R[0].type === "never" && R[0].src === "platoon" &&
    R[0].ids.join() === [pp.starter.id, pp.bench.id].join() && /\(platoon\)$/.test(R[0].label), JSON.stringify(R));
  // the baseline block folds: closed by default, its rule count, how many are on and the lowest pass in the summary;
  // opened, it stays open as the rules re-render
  check("baseline: folded by default, counted in its summary", await pg.evaluate(() => {
    const d = document.getElementById("baseFold");
    return !!d && !d.open && /Baseline: every draw, not in the idea name · 1 rule, 1 on/.test(d.querySelector("summary").textContent); }));
  await pg.click("#baseFold > summary");
  await pg.click('#ruleList .rule[data-i="0"] button[data-act="edit"]');
  check("baseline: opened, it stays open through a re-render", await pg.evaluate(() => document.getElementById("baseFold").open));
  await pg.click("#rtSave");
  R = await rulesNow();
  check("platoon: an edit keeping the pair keeps the mark", R[0].src === "platoon" && (R[0].label.match(/\(platoon\)/g) || []).length === 1, JSON.stringify(R));
  // baseline: a platoon rule starts there; the draw obeys it, the idea name leaves it out; To ideas / To baseline move it
  const lab0 = R[0].label;
  const baseNow = () => pg.evaluate(l => ({ base: !!state.rules[0].base, inDraw: drawRules().conds.some(r => r.label === l),
    inTag: document.getElementById("tagNow").textContent.includes(l), block: /Baseline: every draw/.test(document.getElementById("ruleList").textContent) }), lab0);
  let B = await baseNow();
  check("baseline: a platoon rule starts in the baseline block, in the draw, out of the idea name", B.base && B.block && B.inDraw && !B.inTag, JSON.stringify(B));
  await pg.click('#ruleList .rule[data-i="0"] button[data-act="base"]');
  B = await baseNow();
  check("baseline: To ideas puts it in the idea name", !B.base && !B.block && B.inDraw && B.inTag, JSON.stringify(B));
  await pg.click('#ruleList .rule[data-i="0"] button[data-act="base"]');
  B = await baseNow();
  check("baseline: To baseline takes it back out", B.base && B.inDraw && !B.inTag, JSON.stringify(B));
  // the platoon log: each draw records what the rule blocked of its rule-free lineups, the projection gap, a sample
  await emptyBank(); await set(base);
  await draw(20);
  const plog = await pg.evaluate(() => { const L = BANK.ruleLog || []; bankLoadState(); return { L, back: JSON.stringify(BANK.ruleLog) === JSON.stringify(L) }; });
  const e0 = plog.L[0] || {};
  check("platoon log: one entry for the draw, with blocked of the rule-free lineups", plog.L.length === 1 && e0.of > 0 && e0.blocked >= 0 && e0.blocked <= e0.of &&
        JSON.stringify(e0.ids) === JSON.stringify([pp.starter.id, pp.bench.id]), JSON.stringify(plog.L));
  check("platoon log: the sample holds blocked lineups (both players), at most 20", e0.sample && e0.sample.length === Math.min(e0.blocked, 20) &&
        e0.sample.every(x => x.split(",").includes(pp.starter.id) && x.split(",").includes(pp.bench.id)) && (e0.blocked === 0 || e0.gap === null || Number.isFinite(e0.gap)));
  check("platoon log: kept with the bank across a reload", plog.back);
  await pg.evaluate(() => renderBank());
  await emptyBank();
  const noPlat = TEAMS.teams.find(t => t.platoon && !t.platoon.length);
  if (noPlat) {
    await openTeam(noPlat.team);
    check("platoon: a tile without a pair says none yet", /Platoon: none yet/.test(await pg.textContent(`.tile[data-team="${noPlat.team}"]`)));
  }
  const thin = TEAMS.teams.find(t => (t.platoon || []).some(p => p.thin));
  await openTeam(thin.team);
  check("platoon: a thin pair is marked thin", /games, thin\)/.test(await pg.textContent(`.tile[data-team="${thin.team}"]`)));
  const heavy = TEAMS.teams.find(t => t.heavy_fav), notHeavy = TEAMS.teams.find(t => !t.heavy_fav);
  await openTeam(heavy.team);
  check("platoon: a heavy favorite's tile notes the bench pairing", /garbage time/.test(await pg.textContent(`.tile[data-team="${heavy.team}"]`)));
  await openTeam(notHeavy.team);
  check("platoon: other tiles don't", !/garbage time/.test(await pg.textContent(`.tile[data-team="${notHeavy.team}"]`)));
  // player Min% / Max%: set in the player table, listed in the Baseline block, held over each draw's own lineups
  await clearRules(); await emptyBank(); await set(base);
  const free = (await draw(20)).L, freq = {};
  free.forEach(l => l.ids.forEach(id => freq[id] = (freq[id] || 0) + 1));
  const hot = Object.keys(freq).sort((a, b) => freq[b] - freq[a])[0];
  const cold = Object.keys(P).filter(id => !freq[id] && P[id].status !== "Out" && P[id].fp_dk >= 12).sort((a, b) => P[b].fp_dk - P[a].fp_dk)[0];
  const setPct = async (id, cls, v) => {
    await pg.evaluate(() => { view.panel = null; renderTiles(); });
    await pg.fill(`#players .row[data-id="${id}"] input.${cls}`, String(v));
    await pg.dispatchEvent(`#players .row[data-id="${id}"] input.${cls}`, "change");
  };
  await setPct(cold, "floor", 25); await setPct(hot, "cap", 20);
  const xr = await pg.$$eval("#ruleList .xrule .lab", e => e.map(x => x.textContent));
  check("min/max: both show in the Baseline block", xr.some(t => t.includes(P[cold].name) && t.includes("at least 25%")) && xr.some(t => t.includes(P[hot].name) && t.includes("at most 20%")), JSON.stringify(xr));
  check("min/max: not in the idea name", !/25%|20%/.test(await pg.textContent("#tagNow")));
  await emptyBank();
  const mm = await draw(20), cnt = id => mm.L.filter(l => l.ids.includes(id)).length;
  check(`min/max: ${P[cold].name} (drawn 0 of 20 free) in at least 25% of the draw`, mm.L.length === 20 && cnt(cold) >= 5, cnt(cold) + " of " + mm.L.length + "; " + mm.msg);
  check(`min/max: ${P[hot].name} (drawn ${freq[hot]} of 20 free) in at most 20%`, cnt(hot) <= 4, cnt(hot) + " of " + mm.L.length + "; " + mm.msg);
  check("min/max: the status reports them", /Min\/Max %:/.test(mm.msg), mm.msg);
  check("min/max: recorded with the idea", await pg.evaluate(c => Object.values(BANK.tagRules).some(t => t.floor && t.floor[c] === 25), cold));
  await pg.click(`#ruleList .xrule[data-id="${cold}"] button[data-act="rmx"]`);
  check("min/max: Remove clears the player's box", await pg.inputValue(`#players .row[data-id="${cold}"] input.floor`) === "");
  await pg.evaluate(() => { state.floor = {}; state.cap = {}; save(); renderRules(); renderPlayers(); });
  await emptyBank();
  // the bank in the browser, packed: 12,000 lineups with long idea names save (they overflowed at ~4,400 unpacked) and
  // come back the same; a failed save says so on the page
  const rt = await pg.evaluate(async () => {
    const src = Object.keys(slate.players).filter(id => slate.players[id].status !== "Out").slice(0, 40), B = { lineups: [], tags: [], tagRules: {}, groups: { "t1": "Big idea" } };
    const long = k => "At least 3 from KU + If not Ethan Brown, then 1+ of Andrej Stojakovic / Quentin Coleman + idea " + k + " ".repeat(120);
    for (let i = 0; i < 12000; i++) {
      const ids = []; for (let j = 0; j < 8; j++) ids.push(src[(i * 7 + j * 5 + (i >> 3)) % src.length]);
      B.lineups.push({ ids: ids, slots: ids.slice().reverse() }); B.tags.push(i % 5 ? [long(i % 7)] : [long(1), long(2)]);
    }
    const wait = () => new Promise(r => setTimeout(r, 300));
    const keep = BANK; BANK = B; bankSaveState(); await wait();
    // since 2026-11-20 the bank is in IndexedDB, none of it in localStorage
    const ok = !bankSaveFailed && !!IDB && localStorage.getItem(bankKey()) === null, stored = await idbGet(bankKey()), size = JSON.stringify(stored || "").length;
    delete BIGMEM[bankKey()]; await bigInit([String(slate.draft_group_id)]); bankLoadState();
    const same = JSON.stringify(BANK.lineups) === JSON.stringify(B.lineups) && JSON.stringify(BANK.tags) === JSON.stringify(B.tags) && BANK.groups.t1 === "Big idea";
    const real = idbPut; idbPut = () => Promise.resolve(false);
    bankSaveState(); await wait(); renderBank();
    const warned = bankSaveFailed && /Not saved in this browser/.test(document.getElementById("bankBox").textContent);
    idbPut = real; BANK = keep; bankSaveState(); await wait(); renderBank();
    return { ok, size, same, warned, after: !bankSaveFailed && !/Not saved in this browser/.test(document.getElementById("bankBox").textContent) };
  });
  check("bank storage: 12,000 lineups with long idea names save", rt.ok, JSON.stringify(rt));
  check("bank storage: they come back exactly", rt.same, JSON.stringify(rt));
  check("bank storage: a failed save warns on the page, and the warning clears once saved", rt.warned && rt.after, JSON.stringify(rt));
  // the move to IndexedDB (2026-11-20): a bank (and cut) left in localStorage by the old page moves over at load, is
  // deleted from localStorage only once IndexedDB has it, and comes back whole; the DK page's other keys stay under the
  // cap, a write past it skipped without throwing (another page's keys untouched)
  const mig = await pg.evaluate(async () => {
    const dg = String(slate.draft_group_id), bk = "dkcbb-bank:" + dg, ck = "dkcbb-cut:" + dg, held = BANK;
    if (!BANK.lineups.length) {         // a small bank of its own when the bank is empty here
      const src = Object.keys(slate.players).filter(id => slate.players[id].status !== "Out").slice(0, 16);
      BANK = { lineups: [0, 1, 2].map(k => ({ ids: src.slice(k, k + 8), slots: src.slice(k, k + 8) })), tags: [["mig a"], ["mig a", "mig b"], ["mig b"]], tagRules: {}, groups: {} };
    }
    const before = JSON.stringify(bankPack(BANK)), cutBefore = JSON.stringify(CUT);
    await idbDel(bk); await idbDel(ck); delete BIGMEM[bk]; delete BIGMEM[ck];
    localStorage.setItem(bk, before); if (CUT) localStorage.setItem(ck, cutBefore);
    const n0 = BANK.lineups.length; BANK = { lineups: [], tags: [], tagRules: {} };
    await bigInit([dg]);
    const lsGone = localStorage.getItem(bk) === null && localStorage.getItem(ck) === null, inIdb = JSON.stringify(await idbGet(bk)) === before;
    bankLoadState();
    const back = BANK.lineups.length === n0 && JSON.stringify(bankPack(BANK)) === before && JSON.stringify(CUT) === cutBefore;
    localStorage.setItem("brr:locks:test", "nba");
    let threw = false, r; try { r = store("dkcbb-entries:big", { x: "y".repeat(600000) }); } catch (e) { threw = true; }
    const capped = r === null && !threw && localStorage.getItem("dkcbb-entries:big") === null && localStorage.getItem("brr:locks:test") === "nba";
    localStorage.removeItem("brr:locks:test");
    let use = 0; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.indexOf("dkcbb") === 0) use += 2 * (k.length + localStorage.getItem(k).length); }
    BANK = held; bankSaveState(); await new Promise(r => setTimeout(r, 200)); renderBank(); renderEntries();
    return { n0, lsGone, inIdb, back, capped, under: use < LS_CAP, use };
  });
  check("storage: a bank and cut in localStorage move to IndexedDB at load and come back whole (localStorage copy deleted only after); the DK page's localStorage stays under its cap, a write past it skipped, never thrown",
        mig.n0 > 0 && mig.lsGone && mig.inIdb && mig.back && mig.capped && mig.under, JSON.stringify(mig));
  // Max share in bank: over two draws no unlocked player passes the share of the whole bank; recorded with the idea
  await clearRules(); await emptyBank(); await set(base);
  const fr = (await draw(20)).L, fq = {};
  fr.forEach(l => l.ids.forEach(id => fq[id] = (fq[id] || 0) + 1));
  const hot2 = Object.keys(fq).sort((a, b) => fq[b] - fq[a])[0];
  await emptyBank();
  await pg.fill("#bankMax", "25");
  await draw(20); const second = await draw(20);
  const bankShare = await pg.evaluate(() => { const c = {}; BANK.lineups.forEach(L => L.ids.forEach(id => { if (!state.lock[id]) c[id] = (c[id] || 0) + 1; }));
    return { n: BANK.lineups.length, max: Math.max(...Object.values(c)), top: Object.keys(c).sort((a, b) => c[b] - c[a])[0] }; });
  check(`max share in bank: ${P[hot2].name} drawn ${fq[hot2]} of 20 freely; at 25% no one passes a quarter of the bank`,
        bankShare.n >= 30 && bankShare.max <= Math.floor(0.25 * bankShare.n + 1e-9) + 1, JSON.stringify(bankShare) + " " + second.msg);
  check("max share in bank: the status says who is at it", /Max share in bank 25%/.test(second.msg), second.msg);
  check("max share in bank: recorded with the idea", await pg.evaluate(() => Object.values(BANK.tagRules).some(t => t.bankMax === 25)));
  await pg.fill("#bankMax", "");
  await emptyBank();
  // 3. if 2+ from team then 1+ from its opponent
  await clearRules();
  await addRule("ifteam", async () => { await pg.selectOption("#rtTeam", t2.team); await pg.fill("#rtN", "2"); await pg.fill("#rtM", "1"); });
  await openTeam(t2.team); await pg.click(`.tile[data-team="${t2.team}"] button[data-act="min2"]`);
  L2 = await drawAudit("template 3, condition met (a Min 2 from the team)");
  await pg.evaluate(() => { state.rules.pop(); save(); renderRules(); });
  await openTeam(t2.team); await pg.click(`.tile[data-team="${t2.team}"] button[data-act="excl"]`);
  L2 = await drawAudit("template 3, condition not met (the team excluded)");
  // 4. never P with Q
  await clearRules();
  await addRule("never", async () => { await pg.selectOption("#rtP", p1); await pg.selectOption("#rtQ", p2); });
  await rowBtn(p1, "lock");
  L2 = await drawAudit("template 4, one of them locked");
  check("template 4: never the other with him", L2.every(l => !l.ids.includes(p2)));
  await rowBtn(p2, "lock");
  const { L: Limp, msg: imp } = await draw(3);
  check("template 4: both locked is refused, not broken", Limp.length === 0 && /Only 0 of 3: .*(no lineup left fits the rules|a locked player)/.test(imp), imp);

  // the quadrant: scores on every tile, and each quadrant's button is a rule for the draw
  await openTeam(tile.team);
  check("tiles: Quality and Leverage on the tile, and what they're ranked against",
        (await pg.$$eval("#teamPanel .tile .scores", x => x.length)) >= 1 && /ranks against tonight's \d+ teams/.test(await pg.textContent("#slateLine")));
  for (const q of ["FOCUS", "CHALK", "LEVERAGE"]) {
    const t = TEAMS.teams.find(x => x.verdict === q);
    if (!t) continue;
    await clearRules();
    await openTeam(t.team); await pg.click(`.tile[data-team="${t.team}"] button[data-act="quad"]`);
    const RQ = await rulesNow();
    const want = { FOCUS: r => r.length === 1 && r[0].type === "min" && r[0].n === 2 && r[0].share == null,
                   CHALK: r => r.length === 1 && r[0].type === "none" && JSON.stringify(r[0].ids) === JSON.stringify([t.top[0].id]),
                   LEVERAGE: r => r.length === 1 && r[0].type === "min" && r[0].n === 2 && r[0].share == null }[q];
    check(`quadrant ${q} button writes its draw rule`, want(RQ), JSON.stringify(RQ));
    await drawAudit("quadrant " + q);
    if (q === "CHALK") check("quadrant CHALK leaves Max% alone", await pg.evaluate(id => state.cap[id] == null, t.top[0].id));
  }
  const fadeRules = await pg.evaluate(t => QUAD.FADE.rules(t), TEAMS.teams[0]);
  check("quadrant FADE button excludes the team", fadeRules.length === 1 && fadeRules[0].type === "none");
  // rules saved before the change: "in X% of lineups" becomes its plain rule, "at most X%" goes
  const lev = TEAMS.teams.find(x => x.verdict === "LEVERAGE") || TEAMS.teams[0];
  await pg.evaluate(t => { state.rules = [{ type: "min", ids: teamIds(t), n: 2, share: 0.25, label: "2+ from " + t + " in 25% of lineups" },
                                          { type: "min", ids: teamIds(t), n: 1, maxShare: 0.5, label: t + " in at most 50% of lineups" }]; save(); }, lev.team);
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate/.test(document.getElementById("statusInfo").textContent));
  R = await rulesNow();
  check("old share rules load as draw rules", R.length === 1 && R[0].share == null && R[0].n === 2 && R[0].label === "2+ from " + lev.team, JSON.stringify(R));
  const chips = await pg.$$eval("#teamPanel .tile .verdict", v => v.map(x => x.textContent));
  const shownT = await pg.$$eval("#teamPanel .tile", v => v.map(x => x.dataset.team));
  check("tile verdict says which score drove it", chips.length > 0 && chips.every((c, i) => {
    const t = TEAMS.teams.find(x => x.team === shownT[i]);
    return c === t.verdict + " (" + t.driver + ")" && /^(quality|leverage)-driven(, (quality|leverage) borderline)?$|^both borderline$/.test(t.driver);
  }), JSON.stringify(chips));
  check("team bar marks borderline quadrants", (await pg.$$eval("#teamBar button", v => v.filter(x => /\*$/.test(x.textContent)).length)) ===
        TEAMS.teams.filter(t => t.borderline).length);
  await clearRules();

  // --- the bank, the entries file, the cut, the portfolios, review and the DraftKings export. The entries file is
  // synthetic (made-up entry IDs, in DraftKings' layout), never a real one.
  await emptyBank();
  await set(base);
  const { msg: m1 } = await draw(60);
  await set(Object.assign({}, base, { stackN: 3, stackBoth: true }));
  const { msg: m2 } = await draw(60);
  await set(base);
  const again = await pg.evaluate(() => bankAdd(BANK.lineups.slice(0, 10), tagNow()));   // banked twice: kept once
  const bank = await pg.evaluate(() => BANK);
  const keys = bank.lineups.map(L => L.ids.slice().sort().join(","));
  check("bank: duplicates dropped", new Set(keys).size === keys.length && again === 0 && bank.lineups.length <= 120 && bank.lineups.length >= 100, [m1, m2].join(" | "));
  check("bank: each lineup tagged with the idea it was drawn under", bank.tags.length === bank.lineups.length && bank.tags.every(t => t.length >= 1) &&
        JSON.stringify(Object.keys(bank.tagRules).sort()) === JSON.stringify(["3-stack + bring-back", "no rules"]), JSON.stringify(Object.keys(bank.tagRules)));
  check("bank: the tag table shows each tag", (await pg.$$eval("#bankBox tr", r => r.length)) === 3);

  const ENTRY = "Entry ID,Contest Name,Contest ID,Entry Fee,G,G,G,F,F,F,UTIL,UTIL,,Instructions";
  const fake = [[9000000001, "CBB $6K Pull Up Jumper [$2K to 1st]", 197791872, "$15"], [9000000002, "CBB $500 High Five [Single Entry]", 197791877, "$5"]]
    .concat([3, 4, 5, 6, 7].map(i => [9000000000 + i, "CBB $1.25K And-One", 197791874, "$1"]))
    .concat([[9000000008, "Some Other Contest", 111, "$3"]]);
  const csv = [ENTRY].concat(fake.map((r, i) => r.concat(["", "", "", "", "", "", "", "", "", i === 0 ? "1. Locate the player you want to select" : ""]).join(","))).join("\r\n") + "\r\n";
  await pg.setInputFiles("#entriesFile", { name: "DKEntries_test.csv", mimeType: "text/csv", buffer: Buffer.from(csv) });
  await pg.waitForFunction(() => /entries loaded/.test(document.getElementById("cutStatus").textContent));
  const counts = await pg.evaluate(() => entriesN());
  check("entries file: fills each contest's entries", JSON.stringify(counts) === JSON.stringify({ "197791872": 1, "197791874": 5, "197791877": 1 }), JSON.stringify(counts));
  check("entries file: says which aren't on the slate", /8 entries loaded \(1 in contests not on this slate's list\)/.test(await pg.textContent("#cutStatus")), await pg.textContent("#cutStatus"));
  // contests the file names that the slate doesn't list: named in the entries box, rechecked from the mirror (Check now
  // takes the slate's new list at once, the bank untouched)
  const ul = await pg.evaluate(async () => {
    const note0 = (document.getElementById("unlisted") || {}).textContent || "", timer0 = !!contestTimer, n0 = BANK.lineups.length;
    const i = slate.contests.findIndex(c => String(c.id) === "197791874"), keep = slate.contests[i];
    slate.contests.splice(i, 1); renderEntries();
    const note1 = document.getElementById("unlisted").textContent;
    document.getElementById("contestCheck").click();
    for (let k = 0; k < 50 && !slate.contests.some(c => String(c.id) === "197791874"); k++) await new Promise(r => setTimeout(r, 100));
    const note2 = document.getElementById("unlisted").textContent;
    return { note0, timer0, note1, note2, back: slate.contests.some(c => String(c.id) === "197791874"), bank: BANK.lineups.length === n0, keepName: keep.name, ent: entriesN()["197791874"] };
  });
  check("entries file: contests not on the slate's list named in the entries box (with entries and id), rechecked from the mirror; Check now takes the new list, the bank untouched",
        /Some Other Contest \(1 entry, id 111\)/.test(ul.note0) && ul.timer0 && /And-One \(5 entries, id 197791874\)/.test(ul.note1) && ul.back && !/197791874/.test(ul.note2) && ul.bank && ul.ent === 5, JSON.stringify(ul));

  await pg.fill("#cutKeep", "100"); await pg.fill("#cutPct", "25"); await pg.fill("#cutNights", "300");
  check("cut: by merit (floor 5) is the default, equal share an option", await pg.evaluate(() => $("cutMode").value === "merit" && [...$("cutMode").options].some(o => o.value === "equal")));
  await pg.selectOption("#cutMode", "equal");
  await pg.click("#cutRun");
  await pg.waitForFunction(() => /^Cut |failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  let cmsg = await pg.textContent("#cutStatus"), cut = await pg.evaluate(() => CUT);
  check("cut: rounds shrinking, no lineup twice", cut && new Set(cut.keep).size === cut.keep.length && cut.keep.length <= 102 &&
        cut.rounds.every((r, i) => i === 0 || r.survivors <= cut.rounds[i - 1].survivors), cmsg);
  const tagN = idx => { const o = {}; idx.forEach(k => { const t = bank.tags[k][0]; o[t] = (o[t] || 0) + 1; }); return o; };
  const allN = tagN(bank.lineups.map((L, k) => k)), keptN = tagN(cut.keep);
  const quota = t => Math.max(1, Math.round(allN[t] * Math.min(1, 100 / bank.lineups.length)));
  check("cut: each idea keeps its share of its own lineups (Keep / bank), no more", Object.keys(allN).every(t => (keptN[t] || 0) <= quota(t) && (keptN[t] || 0) >= Math.min(quota(t), 1)),
        JSON.stringify(Object.keys(allN).map(t => [t, allN[t], keptN[t] || 0, quota(t)])));
  const nearDup = cut.keep.some((a, i) => cut.keep.some((b2, j) => j > i && bank.tags[a][0] === bank.tags[b2][0] &&
    bank.lineups[a].ids.filter(id => bank.lineups[b2].ids.includes(id)).length >= 7));
  check("cut: no two kept lineups in an idea share 7+ players", !nearDup);
  // by merit (the default since C2): every lineup ranked together, each idea keeping at least min(its bank, max(5, 1%))
  await pg.selectOption("#cutMode", "merit");
  await pg.evaluate(() => { document.getElementById("cutStatus").textContent = ""; });
  await pg.click("#cutRun");
  await pg.waitForFunction(() => /^Cut |failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const mmsg = await pg.textContent("#cutStatus");
  check("cut by merit: the status says by merit (floor 5) with the kept counts by idea, not each idea's share", /By merit \(floor 5\): kept by idea .+ \d+/.test(mmsg) && !/kept its share/.test(mmsg), mmsg);
  const mcut = await pg.evaluate(() => CUT), mN = tagN(mcut.keep), floor = t => Math.min(allN[t], Math.max(5, Math.ceil(0.01 * allN[t])));
  const sumFloor = Object.keys(allN).reduce((a, t) => a + floor(t), 0);
  check("cut by merit: kept down to Keep (or the ideas' floors), each idea at its floor or more, no lineup twice, settings say merit",
        mcut.settings.mode === "merit" && new Set(mcut.keep).size === mcut.keep.length && mcut.keep.length <= Math.max(100, sumFloor) &&
        Object.keys(allN).every(t => (mN[t] || 0) >= Math.min(floor(t), 1)) && cut.settings.mode === "equal",
        JSON.stringify([mcut.keep.length, sumFloor, Object.keys(allN).map(t => [t, allN[t], mN[t] || 0, floor(t)])]));
  cut = mcut;                                    // the page now holds the merit cut; what follows checks against it
  check("cut: ranked against each contest with entries", cut && JSON.stringify(cut.contests.slice().sort()) === JSON.stringify(["197791872", "197791874", "197791877"]), cmsg);
  const ths = await pg.$$eval("#bankBox th", t => t.map(x => x.textContent)), rth = await pg.$$eval("#cutRounds th", t => t.map(x => x.textContent));
  check("cut: the Bank step's table banked, kept and share (no rounds); the rounds in the Cut step's closed Round by round fold",
        ths.includes("Kept") && ths.includes("Share") && !ths.some(t => /^Round/.test(t)) && rth.filter(t => /^Round \d+$/.test(t)).length === mcut.rounds.length &&
        (await pg.$eval("#cutRounds", d => !d.open)), JSON.stringify([ths, rth]));
  // the idea scoreboard: one row per idea in the kept lineups, best sim ROI first
  const brd = await pg.evaluate(() => ({ rows: CUT.board.rows, shown: [...document.querySelectorAll("#ideaTable tr[data-idea]")].map(r => r.dataset.idea),
    groups: [...new Set(CUT.keep.flatMap(i => lineupGroups(i)))].sort(), every: Object.fromEntries([...new Set(CUT.keep.flatMap(i => lineupGroups(i)))].map(g => [g, CUT.keep.filter(i => lineupGroups(i).includes(g)).length])), board: !!document.getElementById("ideaBoard"), tables: document.querySelectorAll("#stepCut table.contests:not(#cutRounds table)").length }));
  check("idea scoreboard: a row per idea, each counting every kept lineup that idea drew (a shared lineup for each of its ideas)", brd.rows.length === brd.groups.length && JSON.stringify(brd.rows.map(r => r.idea).sort()) === JSON.stringify(brd.groups) &&
        brd.rows.every(r => r.kept === brd.every[r.idea]) && brd.rows.reduce((t, r) => t + r.kept, 0) >= cut.keep.length && brd.shown.length === brd.rows.length && !brd.board && brd.tables === 1, JSON.stringify([brd.rows.map(r => [r.idea, r.kept]), brd.board, brd.tables]));
  // the Cut step's one idea table: Banked / Kept / Share / Tier A / the board's numbers, best Sim ROI first, sortable;
  // tier A by idea adds up to tier A tonight; the one bank line; the entries file's summary
  const it = await pg.evaluate(() => {
    const cells = [...document.querySelectorAll("#ideaTable tr[data-idea]")].map(tr => [tr.dataset.idea, ...[...tr.cells].slice(1).map(c => c.textContent)]);
    const heads = [...document.querySelectorAll("#ideaTable th")].map(t => t.textContent.replace(/ \(i\)| [↓↑]/g, ""));
    const taSum = cells.reduce((t, c) => t + (+c[5] || 0), 0), T = CUT.board.tierA;
    const keptOk = cells.every(c => +c[3] === CUT.keep.filter(i => lineupGroups(i).includes(c[0])).length) &&
      cells.every(c => c[2] === "–" || +c[2] === BANK.lineups.map((L, i) => i).filter(i => lineupGroups(i).length > 1 && lineupGroups(i).includes(c[0])).length);
    const roiOrder = cells.map(c => CUT.board.rows.find(r => r.idea === c[0])).filter(Boolean).every((r, i, a) => i === 0 || a[i - 1].roi >= r.roi);
    document.querySelector('#ideaTable th[data-ck="kept"]').click();
    const kd = [...document.querySelectorAll("#ideaTable tr[data-idea]")].map(tr => +tr.cells[3].textContent);
    cutSort = { k: "roi", dir: -1 }; renderCut();
    return { heads, taSum, T: T.n, keptOk, roiOrder, keptSorted: kd.every((x, i) => i === 0 || kd[i - 1] >= x), line: document.getElementById("cutBankLine").textContent,
             check: document.getElementById("bankCheck").textContent, far: BANKSTATS.far, pct: BANKSTATS.pct, fp: BANKSTATS.fp, bp: BANKSTATS.bp, kn: BANKSTATS.kn, kp: BANKSTATS.kp, kpct: BANKSTATS.kpct,
             tier: document.getElementById("tierA").textContent, sum: document.getElementById("entriesSum").textContent, info: !!document.querySelector('#ideaTable th[data-ck="idea"] span[title]') };
  });
  check("cut step: one idea table (Idea, Banked, Kept, Share, Tier A, Sim ROI, Top 10%, Top 1%, Cash, Avg own, Cores), best Sim ROI first and sortable; tier A by idea sums to tier A tonight; the bank line and the entries summary",
        JSON.stringify(it.heads) === JSON.stringify(["Idea", "Banked", "Shared", "Kept", "Share", "Tier A", "Sim ROI", "Top 10%", "Top 1%", "Cash", "Avg own", "Cores"]) && it.taSum >= it.T && it.keptOk && it.roiOrder && it.keptSorted &&
        /^Whole bank [\d,]+ · \d+ pts (under|over) the field · own \d+% vs \d+% · field's \d+(st|nd|rd|th) pct.* \| Kept [\d,]+ · \d+ pts (under|over) the field · own \d+% vs \d+%/.test(it.line) &&
        it.far === (/far below the field/.test(it.line) && /far below the field/.test(it.check)) && it.far === (it.kn ? (it.kpct != null && it.kpct < 15) || it.fp - it.kp >= 5 : (it.pct != null && it.pct < 15) || it.fp - it.bp >= 5) && /^Tier A tonight: \d+ lineup/.test(it.tier) && /^8 entries · 4 contests$/.test(it.sum) && it.info, JSON.stringify(it));
  const ta = await pg.evaluate(() => { const T = CUT.board.tierA, v = CUT.board.values, el = document.getElementById("tierA");
    const tr = DKSim.tiers(v, v, v); return { T, n: v.length, keep: CUT.keep.length, txt: el ? el.textContent : "" }; });
  check("tier A after the cut: its count, ideas and top idea's share shown, red-flagged at 1-2 lineups or one idea; each kept lineup's value saved",
        ta.T && ta.T.n >= 1 && ta.T.n <= ta.keep && ta.T.ideas >= 1 && ta.n === ta.keep && new RegExp("^Tier A tonight: " + ta.T.n + " lineup").test(ta.txt) &&
        ta.T.flag === (ta.T.n <= 2 || ta.T.ideas === 1) && /Red flag/.test(ta.txt) === ta.T.flag, JSON.stringify(ta));
  check("idea scoreboard: best ROI first; rates, ownership and cores in range", brd.rows.every((r, i) => i === 0 || brd.rows[i - 1].roi >= r.roi) &&
        brd.rows.every(r => Number.isFinite(r.roi) && r.top1 <= r.top10 + 1e-9 && r.top10 <= 1 && r.cash <= 1 && r.own > 0 && r.cores >= 1 && r.cores <= r.kept), JSON.stringify(brd.rows));
  // the cut survives a refresh (reloaded with the bank it was made on)
  const cutBack = await pg.evaluate(() => { const k = CUT.keep.slice(); bankLoadState(); return !!CUT && JSON.stringify(CUT.keep) === JSON.stringify(k); });
  check("cut: kept across a refresh while the bank is unchanged", cutBack);
  await pg.evaluate(() => { renderBank(); renderEntries(); });
  // players, bank against the cut: each one's share of the bank and of the kept, as computed from the bank here
  const shareOf = (idx, id) => idx.filter(k => bank.lineups[k].ids.includes(id)).length / idx.length;
  const srows = await pg.$$eval("#cutShares tr[data-id]", t => t.map(r => [r.dataset.id, ...Array.from(r.cells).slice(3).map(c => c.textContent)]));
  const allIdx = bank.lineups.map((L, k) => k);
  check("cut shares: a row per player in 3%+ of the bank or the kept", srows.length > 0 && srows.length === new Set(bank.lineups.flatMap(L => L.ids)).size -
    [...new Set(bank.lineups.flatMap(L => L.ids))].filter(id => Math.max(shareOf(allIdx, id), shareOf(cut.keep, id)) < 0.03).length, srows.length);
  check("cut shares: bank, kept and change match the lineups", srows.every(([id, b, k, d]) => b === Math.round(100 * shareOf(allIdx, id)) + "%" &&
    k === Math.round(100 * shareOf(cut.keep, id)) + "%" && +d === Math.round(100 * (shareOf(cut.keep, id) - shareOf(allIdx, id)))), JSON.stringify(srows.slice(0, 3)));
  check("cut shares: biggest risers first", srows.every((r, i) => i === 0 || +srows[i - 1][3] >= +r[3] - 1));

  await pg.fill("#nSims", "1000");
  await pg.fill("#maxUse", "1");          // the checks below are the one-contest-only rule; Max contests per lineup 3 is checked further down
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const pf = await pg.evaluate(() => PF);
  const pmsg = await pg.textContent("#cutStatus"), size = { "197791872": 1, "197791874": 5, "197791877": 1 };
  // the starting portfolios: each fills the set, and each one's first pick is the best single lineup by its own measure
  // (Max ROI: expected value; Max coverage: the top-1% coverage it adds alone, value breaking ties). Greedy picking
  // doesn't promise the best whole set by either measure, so the sets aren't compared on them.
  const objs = await pg.evaluate(() => {
    const c = slate.contests.find(x => String(x.id) === "197791874"), pool = finalIdx().map(i => BANK.lineups[i]), n = 5;
    const sim = DKSim.simulate(ctx(), pool, fieldOf().field, fieldDoc.z, c, n, 1000), out = {}, b0 = DKSim.builder(sim, c);
    const sc = pool.map((L, k) => b0.score(k));
    const best = f => sc.reduce((bi, x, k) => (f(x) > f(sc[bi]) ? k : bi), 0);
    ["roi", "balanced", "cover"].forEach(ob => { const r = DKSim.pick(ctx(), Object.assign(pickRules(n), { objective: ob }), pool, sim, c, n);
      out[ob] = { n: r.chosen.length, first: r.chosen[0] }; });
    return { out, roiBest: best(x => x.value), coverBest: best(x => x.top1 * 1e6 + x.value) };
  });
  check("start from: each start fills what the caps allow; first picks are the best lineup by value (Max ROI) and by coverage (Max coverage)",
        ["roi", "balanced", "cover"].every(o => objs.out[o].n >= 1 && objs.out[o].n <= 5) && objs.out.roi.first === objs.roiBest && objs.out.cover.first === objs.coverBest, JSON.stringify(objs));
  dialogs = [];
  await pg.selectOption("#pfObj", "cover");
  await pg.evaluate(() => { document.getElementById("cutStatus").textContent = ""; });
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  check("start from: replacing filled portfolios asks first", dialogs.length === 1 && /Replace your portfolios in 3 contests with the Max coverage start/.test(dialogs[0]), JSON.stringify(dialogs));
  await pg.selectOption("#pfObj", "roi");
  await pg.evaluate(() => { document.getElementById("cutStatus").textContent = ""; });
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  check("start from: the same nights, so Max ROI again repeats the first fill's picks", JSON.stringify(await pg.evaluate(() => PF)) === JSON.stringify(pf), JSON.stringify(await pg.evaluate(() => PF)));
  // Undo fill: the set the last fill replaced comes back (here the Max coverage one)
  const covPF = await pg.evaluate(() => store("dkcbb-pf-prev:" + slate.draft_group_id));
  await pg.click("#pfUndo");
  check("undo fill: the replaced portfolios are back, the button spent", JSON.stringify(await pg.evaluate(() => PF)) === JSON.stringify(covPF) &&
        await pg.$eval("#pfUndo", b => b.disabled) && /Undone/.test(await pg.textContent("#cutStatus")), JSON.stringify(covPF));
  // same nights: one lineup scores the same every night whatever pool it's simulated in; New nights changes the seed
  const same = await pg.evaluate(() => {
    const c = slate.contests.find(x => String(x.id) === "197791874"), all = finalIdx().map(i => BANK.lineups[i]);
    const a = DKSim.simulate(nightsCtx(c), all.slice(0, 30), fieldOf().field, fieldDoc.z, c, 5, 300);
    const b = DKSim.simulate(nightsCtx(c), [all[0]].concat(all.slice(40, 60)), fieldOf().field, fieldDoc.z, c, 5, 300);
    let eq = true; for (let s2 = 0; s2 < 300; s2++) if (a.cs[s2] !== b.cs[s2] || a.fa[s2] !== b.fa[s2]) eq = false;
    return eq;
  });
  check("same nights: a lineup's every night is the same in any pool (seeded, players in a fixed order)", same);
  const seed0 = await pg.evaluate(() => nightsSeed());
  await pg.click("#pfNights");
  check("new nights: a new seed for the slate, said so", await pg.evaluate(s0 => nightsSeed() !== s0, seed0) && /New nights for this slate/.test(await pg.textContent("#cutStatus")));
  await pg.evaluate(s0 => { state.nightsSeed = s0; save(); }, seed0);
  await pg.evaluate(p => { PF = p; pfSave(); renderEntries(); }, pf);     // the rest of the run works from the first fill
  check("portfolios: one per contest, from the final pool", Object.keys(size).every(c => pf[c] && pf[c].length >= 1 && pf[c].length <= size[c] && pf[c].every(i => cut.keep.includes(i)) &&
        new Set(pf[c]).size === pf[c].length), JSON.stringify(pf));
  const pfAll = Object.values(pf).flat();
  check("portfolios: each lineup in one contest only, the largest stake first", new Set(pfAll).size === pfAll.length &&
        /the largest stake first: CBB \$6K Pull Up Jumper/.test(pmsg), pmsg);
  check("portfolios: each fills its entries, or says what stops it", Object.keys(size).every(c => pf[c].length === size[c]) || /short: .* stops it|runs out/.test(pmsg), pmsg);
  // a short set completes itself by relaxing one cap a step (C4) and says so: the audit holds it to what it reports
  const rxExpo = /Max exposure relaxed to 70%/.test(pmsg) ? 0.7 : 0.6, rxCore = /Max core relaxed to 25%/.test(pmsg) ? 0.25 : /Max core relaxed to 20%/.test(pmsg) ? 0.2 : 0.15;
  Object.keys(size).forEach(c => audit("portfolio " + c + " within Max exposure " + Math.round(100 * rxExpo) + "% and Min unique 3", pf[c].map(i => bank.lineups[i]),
    Object.assign(rulesOf(base), { n: size[c], expo: Math.max(rxExpo, 1 / size[c]), minUnique: 3 })));
  const coreOf = ids => ids.slice().sort((a, b) => P[b].salary - P[a].salary || (a < b ? -1 : 1)).slice(0, 3).sort().join(",");
  const coreMax = a => { const c = {}; a.forEach(i => { const k = coreOf(bank.lineups[i].ids); c[k] = (c[k] || 0) + 1; }); return Math.max(0, ...Object.values(c)); };
  check("portfolios: no core in more than 15% of a contest's lineups (at least one each), or the relaxed cap it reports", Object.keys(size).every(c => coreMax(pf[c]) <= Math.max(1, Math.floor(rxCore * size[c] + 1e-9))),
        JSON.stringify(Object.keys(size).map(c => [c, coreMax(pf[c])])));
  check("portfolios: the largest core is shown, each contest and the night", /Largest core across the night's \d+ entries: .+ in \d+ \(\d+%\)/.test(pmsg) && (pmsg.match(/largest core /g) || []).length === 3, pmsg);

  // review: the contest's set in the builder; Added value is exact, Remove undoes Add, Auto-fill keeps the pick's settings, Keep replaces the set
  await pg.click('button[data-review="197791874"]');
  await pg.waitForFunction(() => BP && BP.review === "197791874");
  check("review: other contests' lineups aren't on offer", await pg.evaluate(o => BP.idx.every(bi => !o.includes(bi)), pf["197791872"].concat(pf["197791877"])));
  check("review: Build opens the contest's portfolio in the builder", JSON.stringify(await pg.evaluate(() => BP.b.picked.map(k => BP.idx[k]))) === JSON.stringify(pf["197791874"]) &&
        (await pg.$$eval("#bpTable tr", r => r.length)) > 50);
  const cols = await pg.$$eval("#bpTable th", t => t.map(x => x.textContent.replace(/[↓↑ ]+$/, "")));
  const qc = await pg.evaluate(() => ({ q: BP.qual.slice(0, 5), c: BP.core.slice(0, 5), n: BP.qual.length, k: BP.pool.length }));
  check("review: ROI-first columns, the dollar columns gone", ["Tier", "ROI %", "Top 10%", "Top 1%", "Cash", "Core %", "Added ROI", "+Cover", "Shared", "Own"].every(c => cols.includes(c)) &&
        !["Proj", "Quality", "Alone", "Added"].some(c => cols.includes(c)) &&
        qc.n === qc.k && qc.q.every(Number.isFinite) && qc.c.every(v => v >= 0 && v <= 1), JSON.stringify({ cols, qc }));
  const rv = await pg.evaluate(() => {
    const K = BP.pool.length, ok = [];
    for (let k = 0; k < K; k++) ok.push(Math.abs(BP.roi[k] - (BP.alone[k] - BP.fee) / BP.fee) < 1e-9);
    const rank = { A: 0, B: 1, C: 2 }, order = BP.pool.map((L, k) => k).sort((a, b) => BP.alone[b] - BP.alone[a]);
    const mono = order.every((k, i) => i === 0 || rank[BP.tier[k]] >= rank[BP.tier[order[i - 1]]]);
    const rates = BP.pool.every((L, k) => BP.t1[k] >= 0 && BP.t1[k] <= BP.t10[k] + 1e-9 && BP.t10[k] <= 1 && BP.cashR[k] >= 0 && BP.cashR[k] <= 1);
    return { roi: ok.every(Boolean), mono, rates, sigma: BP.sigma, tiers: [...new Set(BP.tier)].sort().join(""), fee: BP.fee };
  });
  check("review: ROI % is (expected payout alone - fee) / fee", rv.roi && rv.fee > 0, JSON.stringify(rv));
  check("review: tiers A/B/C follow the sim value, split by its measured noise", rv.mono && rv.tiers.startsWith("A") && Number.isFinite(rv.sigma) && rv.sigma > 0, JSON.stringify(rv));
  check("review: top-1%, top-10% and cash rates from the sim's nights", rv.rates);
  await pg.click("#bpClear");
  const step = await pg.evaluate(() => {
    const b = BP.b, out = [], ks = [];
    for (const start of [0, 5, 40]) {           // three lineups within Max exposure (hand adds keep to it)
      let k = Math.min(start, BP.pool.length - 1); while (k < BP.pool.length && (ks.includes(k) || bpBlocks(k).length)) k++;
      if (k >= BP.pool.length) { k = 0; while (k < BP.pool.length && (ks.includes(k) || bpBlocks(k).length)) k++; }
      if (k >= BP.pool.length) break;           // every other lineup blocked by the caps: test the ones found
      const before = b.total(), v = BP.scores[k] ? BP.scores[k].value : null;
      bpAdd(k); ks.push(k);
      out.push(Math.abs(b.total() - before - v));
    }
    bpRemove(ks[1]);
    return { gaps: out, picked: b.picked.slice(), want: ks.filter((k, i) => i !== 1) };
  });
  check("review: Added value is the set's payout with it minus without", step.gaps.every(g => g < 1e-9), JSON.stringify(step.gaps));
  check("review: Remove takes a pick out", JSON.stringify(step.picked) === JSON.stringify(step.want), JSON.stringify(step.picked));
  await pg.click("#bpClear");
  await pg.click("#bpAuto");
  await pg.waitForFunction(() => BP.b.picked.length >= 5 || /stopped/.test(document.getElementById("bpStatus").textContent), null, { timeout: 300000 });
  const auto = await pg.evaluate(() => BP.b.picked.map(k => ({ ids: BP.pool[k].ids, slots: BP.pool[k].slots })));
  const autoMsg = await pg.evaluate(() => document.getElementById("bpStatus").textContent);
  audit("review: Auto-fill within Max exposure and Min unique (or the relaxed cap it reports)", auto, Object.assign(rulesOf(base), { n: 5, expo: /Max exposure relaxed to 70%/.test(autoMsg) ? 0.7 : 0.6, minUnique: 3 }));
  check("review: Auto-fill keeps each core to one lineup of 5 (Max core 15%)", (() => { const c = {}; auto.forEach(l => { const k = coreOf(l.ids); c[k] = (c[k] || 0) + 1; }); return Math.max(...Object.values(c)) <= 1; })());
  check("review: the summary shows the largest core", /Largest core: .+ in \d+ of \d+/.test(await pg.textContent("#bpSummary")));
  check("review: summary shows coverage and diversity", /of nights one reaches the top 1%/.test(await pg.textContent("#bpSummary")) && /distinct cores/.test(await pg.textContent("#bpSummary")));
  await pg.evaluate(() => bpRemove(BP.b.picked[0]));
  const pf2 = await pg.evaluate(() => PF["197791874"]), kept = await pg.evaluate(() => BP.b.picked.map(k => BP.idx[k]));
  check("review: the picks save to the contest as they change", JSON.stringify(pf2) === JSON.stringify(kept) && pf2.length === auto.length - 1, JSON.stringify(pf2));

  const [dl5] = await Promise.all([pg.waitForEvent("download"), pg.click("#pfExport")]);
  const out = fs.readFileSync(await dl5.path(), "utf8").trim().split(/\r?\n/).map(l => l.split(","));
  check("export: DraftKings' header, first 12 columns", out[0].join(",") === "Entry ID,Contest Name,Contest ID,Entry Fee,G,G,G,F,F,F,UTIL,UTIL", out[0].join(","));
  const rowsOut = out.slice(1), byId = {};
  rowsOut.forEach(r => byId[r[0]] = r);
  check("export: only the entries with a lineup (the off-slate one and any past a short portfolio left out)",
        rowsOut.length === pf["197791872"].length + pf["197791877"].length + pf2.length && !byId["9000000008"] && !byId["9000000007"], rowsOut.map(r => r[0]).join(" "));
  const finalPf = Object.assign({}, pf, { "197791874": pf2 });
  const want = {};
  ["197791872", "197791877", "197791874"].forEach(cid => fake.filter(r => String(r[2]) === cid).slice(0, finalPf[cid].length).forEach((r, k) => want[r[0]] = bank.lineups[finalPf[cid][k]].ids));
  const lateWant = await pg.evaluate(w => Object.fromEntries(Object.entries(w).map(([k, ids]) => [k, DKSim.lateSlots(ctx(), ids)])), want);   // the slots with the latest tips in UTIL (C6)
  Object.assign(want, lateWant);
  check("export: each entry ID keeps its contest and gets its portfolio's lineup, slot for slot (latest tips in UTIL)",
        Object.keys(want).every(id => byId[id] && byId[id].slice(4).join(",") === want[id].join(",") && fake.some(f => String(f[0]) === id && String(f[2]) === byId[id][2])));
  ["197791872", "197791874", "197791877"].forEach(cid => {
    const L = rowsOut.filter(r => r[2] === cid).map(r => ({ ids: r.slice(4), slots: r.slice(4) }));
    audit("export: " + cid + "'s lineups", L, Object.assign(rulesOf(base), { minUnique: 1 }));
  });
  const outKeys = rowsOut.map(r => r.slice(4).slice().sort().join(","));
  check("export: no lineup twice across the night's contests", new Set(outKeys).size === outKeys.length, outKeys.length + " rows, " + new Set(outKeys).size + " distinct");

  const pfBefore = await pg.evaluate(() => JSON.stringify(PF));
  const [dl6] = await Promise.all([pg.waitForEvent("download", { timeout: 300000 }), pg.click("#bankSave")]);
  const bs = JSON.parse(fs.readFileSync(await dl6.path(), "utf8"));
  check("Save build (bank): the pool, its tags, the final cut and the portfolios", bs.kind === "build" && bs.pool.length === bank.lineups.length && bs.tags.length === bs.pool.length &&
        JSON.stringify(bs.final) === JSON.stringify(cut.keep) && bs.portfolios["197791874"].length === pf2.length && /^dk_bank_/.test(dl6.suggestedFilename()) &&
        bs.rule_set.length === 0 && bs.tag_settings["3-stack + bring-back"].stackN === 3 && bs.cut && bs.cut.within === "idea" && bs.cut.mode === "merit" && bs.cut.keep === 100 && bs.pick && bs.pick.maxExpo === 60 && bs.pick.maxCore === 15,
        dl6.suggestedFilename() + " " + JSON.stringify(bs.cut));
  // Load build: Save build carries what it needs (slots, the whole cut, entry counts; no entries file); save -> clear ->
  // load gives the same bank, cut and picks; another draft group is refused
  check("Save build: slots, the whole cut and the entry counts for Load build, no entry IDs",
        bs.slots && bs.slots.length === bs.pool.length && bs.cut_state && JSON.stringify(bs.cut_state.keep) === JSON.stringify(cut.keep) && bs.entries_n && !("entries" in bs) &&
        !JSON.stringify(bs).includes("Entry ID"), JSON.stringify(Object.keys(bs)));
  const lbSnap = () => pg.evaluate(() => JSON.stringify({ b: BANK.lineups.map(L => [L.ids, L.slots]), t: BANK.tags, g: BANK.groups || {}, r: Object.keys(BANK.tagRules).sort(), k: CUT && CUT.keep, s: CUT && CUT.settings, pf: PF, seed: nightsSeed(), n: entriesN() }));
  const lbBefore = await lbSnap();
  await pg.evaluate(() => { BANK = { lineups: [], tags: [], tagRules: {}, groups: {} }; CUT = null; cutSave(); PF = {}; pfSave(); state.nightsSeed = 12345; bankSaveState(); renderBank(); renderEntries(); });
  const lbOther = path.join(os.tmpdir(), "dk_build_other.json");
  fs.writeFileSync(lbOther, JSON.stringify(Object.assign({}, bs, { draft_group: 999 })));
  await pg.setInputFiles("#bankLoadFile", lbOther);
  await pg.waitForFunction(() => /draft group 999/.test(document.getElementById("cutStatus").textContent));
  const lbRefused = await pg.evaluate(() => BANK.lineups.length === 0 && !!document.querySelector("#cutStatus .bad"));
  await pg.setInputFiles("#bankLoadFile", await dl6.path());
  await pg.waitForFunction(() => /^Restored /.test(document.getElementById("cutStatus").textContent));
  const lbAfter = await lbSnap(), lbMsg = await pg.textContent("#cutStatus");
  check("Load build: another draft group refused; save -> clear -> load gives the same bank, slots, tags, groups, cut, picks, entry counts and nights seed, and says what came back",
        lbRefused && lbAfter === lbBefore && new RegExp("^Restored " + bank.lineups.length.toLocaleString("en-US") + " banked · " + cut.keep.length + " kept · " + Object.values(bs.portfolios).flat().length + " entries picked").test(lbMsg),
        lbMsg + (lbAfter === lbBefore ? "" : " differs"));
  // the Auto-fill benchmark: Pick portfolios' entries from the same final pool, apart from yours, each lineup once
  const ap = bs.auto_portfolios || {}, apAll = Object.values(ap).flat();
  check("Save build: the Auto-fill benchmark for each contest with entries, from the final pool, each lineup once",
        ["197791872", "197791874", "197791877"].every(c => (ap[c] || []).length > 0) && apAll.every(k => cut.keep.includes(k)) && new Set(apAll).size === apAll.length,
        JSON.stringify(Object.fromEntries(Object.entries(ap).map(([c, v]) => [c, v.length]))));
  check("Save build: your portfolios untouched by the benchmark", await pg.evaluate(() => JSON.stringify(PF)) === pfBefore);

  // Reload on the same slate: new rows and contests from the mirror, the bank / cut / picks as they are in the page
  // (a bank past the browser's storage would otherwise lose its newest lineups, 2026-11-19)
  const rl0 = await pg.evaluate(() => { const n = BANK.lineups.length; BANK.lineups.push({ ids: BANK.lineups[0].ids.slice(), slots: BANK.lineups[0].slots.slice() }); BANK.tags.push(["in memory only"]);
    const c = slate.contests.pop(); return { n, cid: c.id }; });
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate/.test(document.getElementById("statusInfo").textContent));
  const rl = await pg.evaluate(c => ({ n: BANK.lineups.length, tag: BANK.tags[BANK.tags.length - 1][0], back: slate.contests.some(x => x.id === c) }), rl0.cid);
  check("Reload keeps the page's bank on the same slate and takes the mirror's contests", rl.n === rl0.n + 1 && rl.tag === "in memory only" && rl.back, JSON.stringify([rl0, rl]));
  await pg.evaluate(() => { BANK.lineups.pop(); BANK.tags.pop(); renderBank(); });
  check("portfolios survive a reload (the Live page reads them for your exposures)",
        JSON.stringify(await pg.evaluate(() => PF["197791874"])) === JSON.stringify(pf2) && !(await pg.$eval("#pfExport", x => x.disabled)));

  // the tie split: players with no spread, a lineup copied 3 times in the field: it ties those 3 every night and its
  // payout is the mean of the 4 places the tie covers
  const tie = await pg.evaluate(() => {
    const L = BANK.lineups[0], cx = ctx();
    cx.rows = rows.map(r => Object.assign({}, r, { miss_dk: 1e-9 }));
    const field = fieldOf().field.slice(0, 200).filter(f => f.slice().sort().join() !== L.ids.slice().sort().join()).concat([L.ids, L.ids.slice().reverse(), L.ids.slice()]);
    const contest = { size: field.length + 1, payouts: [[1, 1, 100], [2, 2, 50], [3, 3, 20], [4, 20, 5]] };
    cx.tieSplit = false;
    const off = DKSim.builder(DKSim.simulate(cx, [L], field, fieldDoc.z, contest, 1, 20), contest).alone(0);   // switched off: no split
    delete cx.tieSplit;                                                                                           // the default: split
    const sim = DKSim.simulate(cx, [L], field, fieldDoc.z, contest, 1, 20);
    const b = DKSim.builder(sim, contest);
    const mine = L.ids.reduce((t, id) => t + proj(byId(id)), 0);
    const above = field.filter(f => f.reduce((t, id) => t + proj(byId(id)), 0) > mine + 1e-6).length;
    const pay = DKSim.payTable(contest), want = [0, 1, 2, 3].reduce((t, i) => t + (pay[1 + above + i] || 0), 0) / 4;
    return { dup: sim.dup[0], tie: sim.tie[0], alone: b.alone(0), want, above, off, whole: pay[1 + above] || 0 };
  });
  check("ties: an identical field lineup is counted and (the default, the field calibrated) the prize split among the tie", tie.dup === 3 && Math.abs(tie.tie - 3) < 1e-6 && Math.abs(tie.alone - tie.want) < 1e-6, JSON.stringify(tie));
  check("ties: switched off, the place's whole prize; on by default", Math.abs(tie.off - tie.whole) < 1e-6 && (await pg.evaluate(() => DKSim.TIE_SPLIT)), JSON.stringify(tie));

  // the night-wide pair cap: no two players together in more than Max pair % of the night's entries (at least one)
  await pg.fill("#maxPair", "30");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const night = await pg.evaluate(() => Object.keys(PF).reduce((a, k) => a.concat(PF[k].map(bi => BANK.lineups[bi].ids)), []));
  const pairMax = (() => { const c = {}; night.forEach(ids => DKSimPairs(ids).forEach(k => c[k] = (c[k] || 0) + 1)); return Math.max(0, ...Object.values(c)); })();
  check("night-wide pair cap: no pair past 30% of the night's entries", night.length > 0 && pairMax <= Math.max(1, Math.floor(0.3 * 7 + 1e-9)), pairMax + " of " + night.length);
  check("night view: players, pairs and cores against the field", /The night: \d+ entries/.test(await pg.textContent("#pfBox")) &&
        (await pg.$$eval("#pfBox table", t => t.length)) === 3);
  await pg.fill("#maxPair", "");
  // stranded seats: with a tight night cap the fill leaves seats open; the panel names the cap that blocked and offers
  // the lineup that breaks the caps least as a one-tap add; nothing is added by itself
  const night0 = await pg.evaluate(() => $("maxNight").value);
  await pg.fill("#maxNight", "15");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed|^Filled/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const st0 = await pg.evaluate(() => { const open = nbContests().reduce((t, x) => t + Math.max(0, x.n - (PF[String(x.c.id)] || []).length), 0), b = document.querySelector("#strandBox .strandAdd");
    return { open, shown: !$("strandBox").hidden, text: $("strandBox").textContent, btn: !!b, cid: b && b.dataset.cid, n: b ? (PF[b.dataset.cid] || []).length : null }; });
  if (st0.btn) await pg.click("#strandBox .strandAdd");
  const st1 = await pg.evaluate(c => ({ n: c ? (PF[c] || []).length : null }), st0.cid);
  check("stranded seats: a fill left short names the cap that blocked (Night cap blocked: players at 15%) and offers a one-tap add of the lineup that breaks the caps least; nothing added by itself",
        st0.open > 0 && st0.shown && /Open seats: .*\d+ open\. .*Night cap blocked: .+ at 15%/.test(st0.text) && st0.btn && st1.n === st0.n + 1, JSON.stringify([st0, st1]));
  await pg.fill("#maxNight", night0);
  // Clear old slates: other slates' banks / cuts / portfolios / entries / scans go after asking; this slate's stay, and settings
  const co = await pg.evaluate(async () => {
    const dg = String(slate.draft_group_id), keys = ["dkcbb-bank:999001", "dkcbb-cut:999001", "dkcbb-pf:999001", "dkcbb-pf-prev:999001", "dkcbb-entries:999001", "dkcbb-scan:999001", "dkcbb:999001"];
    keys.forEach(k => localStorage.setItem(k, JSON.stringify({ x: 1 })));
    const mine = localStorage.getItem("dkcbb-pf:" + dg), asked = []; const c0 = window.confirm; window.confirm = m => { asked.push(m); return true; };
    document.getElementById("clearOld").click();
    for (let t = 0; t < 40 && !/Cleared|No old slates/.test(document.getElementById("buildStatus").textContent); t++) await new Promise(r => setTimeout(r, 50));
    window.confirm = c0;
    return { asked, gone: keys.slice(0, 6).every(k => localStorage.getItem(k) === null), settings: localStorage.getItem("dkcbb:999001") !== null, mine: localStorage.getItem("dkcbb-pf:" + dg) === mine && mine !== null,
             msg: document.getElementById("buildStatus").textContent, note: /Closing the tab after a slate/.test(document.getElementById("stepBank").textContent) };
  });
  check("clear old slates: asks with the count and space, removes another slate's bank / cut / portfolios / entries / scan, keeps this slate's and the settings; a line under Clear bank",
        co.asked.length === 1 && /Remove 1 old slate.+about [\d.]+ MB/.test(co.asked[0]) && co.gone && co.settings && co.mine && /Cleared 1 old slate/.test(co.msg) && co.note, JSON.stringify(co));
  await pg.evaluate(() => localStorage.removeItem("dkcbb:999001"));
  // Max contests per lineup (3 by default): unique within a contest, a lineup in at most 3; the builder offers only
  // lineups under the max elsewhere; the export refuses only a lineup twice in one contest
  check("max contests per lineup: 3 by default", await pg.evaluate(() => { const x = document.getElementById("maxUse"); return x.defaultValue === "3"; }));
  await pg.fill("#maxUse", "3");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const mcu = await pg.evaluate(() => { const use = {}, within = Object.keys(PF).every(k => new Set(PF[k]).size === PF[k].length);
    Object.values(PF).forEach(v => v.forEach(bi => { use[bi] = (use[bi] || 0) + 1; }));
    return { within, max: Math.max(...Object.values(use)), msg: document.getElementById("cutStatus").textContent }; });
  check("max contests per lineup: unique within each contest, no lineup in more than 3, said so", mcu.within && mcu.max <= 3 && /each lineup in at most 3 contests/.test(mcu.msg), JSON.stringify(mcu));
  await pg.click('button[data-review="197791874"]');
  await pg.waitForFunction(() => BP && BP.review === "197791874");
  check("max contests per lineup: the builder offers only lineups under the max in the other contests", await pg.evaluate(() => {
    const other = {}; Object.keys(PF).forEach(k => { if (k !== "197791874") PF[k].forEach(bi => { other[bi] = (other[bi] || 0) + 1; }); });
    return BP.idx.every(bi => (other[bi] || 0) < 3); }));
  // Max exposure, night %: 60 by default; at 40, no unlocked player in more than 40% of the night's entries across every contest
  check("night cap: 60% by default", await pg.evaluate(() => document.getElementById("maxNight").defaultValue === "60"));
  await pg.fill("#maxNight", "40");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const nc = await pg.evaluate(() => { const c = {}; let n = 0;
    Object.values(PF).forEach(v => v.forEach(bi => { n++; BANK.lineups[bi].ids.forEach(id => { if (!state.lock[id]) c[id] = (c[id] || 0) + 1; }); }));
    return { n, max: Math.max(0, ...Object.values(c)), lim: nightLimit(), night: nightEntries() }; });
  check("night cap: at 40%, no unlocked player past 40% of the night's entries", nc.n > 0 && nc.max <= nc.lim && nc.lim === Math.max(1, Math.floor(0.4 * nc.night + 1e-9)), JSON.stringify(nc));
  // Locks apply to: draws only by default (a locked player capped like the rest in the fill), with a note naming each
  // locked player's share of the night; "Draws and fill" exempts him again
  const lk0 = await pg.evaluate(() => { const c = {}; BANK.lineups.forEach(L => L.ids.forEach(id => { c[id] = (c[id] || 0) + 1; }));
    const top = Object.keys(c).sort((a, b) => c[b] - c[a])[0]; state.lock = { [top]: 1 }; save(); return { top, sel: document.getElementById("lockFill").value }; });
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const lk1 = await pg.evaluate(top => { const used = nightUsed(null); return { share: used[top] || 0, lim: nightLimit(), note: document.getElementById("cutStatus").textContent }; }, lk0.top);
  check("locks apply to draws only by default: a locked player capped like the rest in Fill, and the note names his share tonight",
        lk0.sel === "draws" && lk1.share <= lk1.lim && /1 locked player capped like the rest in the fill \(Locks apply to: draws only\): .+ \d+% tonight/.test(lk1.note), JSON.stringify([lk0, lk1]));
  await pg.selectOption("#lockFill", "fill");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const lk2 = await pg.evaluate(() => ({ note: document.getElementById("cutStatus").textContent, kept: state.lockFill }));
  check("locks apply to draws and fill: the note says he's exempt from the caps, and the setting is kept with the slate",
        /1 locked player is exempt from the caps \(Locks apply to: draws and fill\)/.test(lk2.note) && lk2.kept === "fill", JSON.stringify(lk2));
  await pg.selectOption("#lockFill", "draws");
  await pg.evaluate(() => { state.lock = {}; save(); renderPlayers(); });
  // C4: a short set completes itself: at 20% exposure a 5-entry contest allows each player once (disjoint); Fill relaxes
  // ONE cap a step at a time (core, then exposure to 70%; never the night cap) and says so; the one-line status names it
  await pg.fill("#maxNight", "100"); await pg.fill("#maxExpo", "20");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const c4 = await pg.evaluate(() => { const st = document.getElementById("cutStatus").textContent, five = PF["197791874"] || [], cnt = {};
    five.forEach(bi => BANK.lineups[bi].ids.forEach(id => { cnt[id] = (cnt[id] || 0) + 1; }));
    const sb = document.querySelector('#strandBox .strandAdd[data-cid="197791874"]');
    return { n: five.length, relaxed: /relaxed to \d+% to fill \d+ slot/.test(st), oneLine: /^Filled \d+ of \d+ entries[^]*relaxed to/.test(st), maxUse: Math.max(...Object.values(cnt)), st: st.slice(0, 300),
             strand: !!sb && !$("strandBox").hidden }; });
  check("fill completes itself: short at 20% exposure, it relaxes one cap a step at a time (to 70% at most) and says so in the one-line status; the 5-entry contest fills, or what's left open gets the stranded-seat line (random pool)",
        c4.relaxed && c4.oneLine && (c4.n === 5 || (c4.n === 4 && c4.strand)) && c4.maxUse <= DKSimLimit(0.7, 5), JSON.stringify(c4));
  const und = await pg.evaluate(() => { renderUnder(); const u = underExposed(), t = document.getElementById("fillUnder").textContent;
    const ok = !u || ["p", "st", "pr"].every(k => u[k].every(x => x.want >= 0.2 && x.want - x.have >= 0.15 - 1e-9));
    return { has: !!u, ok, t: t.slice(0, 200), shown: !u || (["p", "st", "pr"].some(k => u[k].length) ? /^Under-exposed against tier A/.test(t) : t === "") }; });
  check("fill: the Under-exposed list (players, team stacks, pairs held 15+ points under their tier-A share)", und.has && und.ok && und.shown, JSON.stringify(und));
  await pg.fill("#maxExpo", "60"); await pg.fill("#maxNight", "40");
  await pg.fill("#maxNight", "60");
  await pg.fill("#maxUse", "1");

  await pg.evaluate(() => { document.querySelectorAll("#bankBox input[data-tag]").forEach(x => { x.checked = true; }); });
  await pg.fill("#groupName", "Both ideas");
  await pg.click("#groupMake");
  check("groups: a grouped idea's tags fold away, counted", await pg.evaluate(() => {
    const d = document.querySelector('#bankBox details.fold[data-fold-group="Both ideas"]');
    return !!d && !d.open && d.querySelector("summary").textContent === "2 tags" && d.querySelectorAll("input[data-tag]").length === 2; }));
  check("groups: ticked tags merge into one idea in the bank table", (await pg.$$eval("#bankBox > table tr", r => r.length)) === 2 && /Both ideas/.test(await pg.textContent("#bankBox")) &&
        (await pg.evaluate(() => Object.values(BANK.groups).filter(g => g === "Both ideas").length)) === 2);
  await pg.fill("#cutKeep", "60"); await pg.fill("#cutNights", "200");
  await pg.click("#cutRun");
  await pg.waitForFunction(() => /^Cut |failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const gk = await pg.evaluate(() => ({ kept: CUT.keep.length, n: BANK.lineups.length }));
  check("groups: the cut keeps the group's share as one idea", Math.abs(gk.kept - Math.round(gk.n * Math.min(1, 60 / gk.n))) <= 1, JSON.stringify(gk));
  await pg.click('button[data-review="197791874"]');
  await pg.waitForFunction(() => BP && BP.review === "197791874");
  await pg.click('#bpGroups button[data-group="Both ideas"]');
  const hl = await pg.evaluate(() => ({ rows: document.querySelectorAll("#bpTable tr.ingroup").length, first: document.querySelector("#bpTable tr:not(.picked)[data-k]").classList.contains("ingroup") }));
  check("groups: clicking an idea highlights its lineups and brings them to the top", hl.rows > 0 && hl.first, JSON.stringify(hl));
  await pg.click('[data-ungroup="Both ideas"]');
  check("groups: Ungroup splits it back", (await pg.$$eval("#bankBox > table tr", r => r.length)) === 3);
  // Tick all ungrouped ticks only the tags not in a group; Group with nothing ticked takes every ungrouped tag
  const gu = await pg.evaluate(() => {
    showStep("bank");
    const tags = [...document.querySelectorAll("#bankBox input[data-tag]")].map(x => x.dataset.tag);
    groupTags([tags[0]], "First");
    document.getElementById("groupTickAll").click();
    const ticked = [...document.querySelectorAll("#bankBox input[data-tag]:checked")].map(x => x.dataset.tag);
    document.querySelectorAll("#bankBox input[data-tag]").forEach(x => { x.checked = false; });
    document.getElementById("groupName").value = "Rest"; document.getElementById("groupMake").click();
    const rest = tags.slice(1).every(t => BANK.groups[t] === "Rest") && BANK.groups[tags[0]] === "First";
    const tip = document.getElementById("groupMake").title;
    groupTags(tags, null);
    return { tags, ticked, rest, tip, back: Object.keys(BANK.groups).length };
  });
  check("groups: Tick all ungrouped ticks only the ungrouped tags; Group with nothing ticked groups every ungrouped tag (and says so in its tooltip)",
        gu.tags.length >= 2 && JSON.stringify(gu.ticked) === JSON.stringify(gu.tags.slice(1)) && gu.rest && /nothing ticked/.test(gu.tip) && gu.back === 0, JSON.stringify(gu));
  // the step bar: Bank / Cut / Fill, one panel at a time, kept per slate; switching shows panels and touches nothing else
  const sb = await pg.evaluate(() => {
    const before = JSON.stringify([BANK.lineups.length, CUT && CUT.keep && CUT.keep.length, PF]), seen = {};
    ["bank", "cut", "fill"].forEach(st => { document.querySelector('#stepBar button[data-step="' + st + '"]').click();
      seen[st] = [...document.querySelectorAll("section.step")].filter(x => !x.hidden).map(x => x.dataset.step).join(",") + "|" + document.querySelector("#stepBar button[aria-pressed=true]").dataset.step; });
    const kept = JSON.parse(localStorage.getItem(key())).step, labels = [...document.querySelectorAll("#stepBar button")].map(b => b.textContent);
    const bankHas = ["bankDraw", "bankN", "ruleList", "bankCheck", "bankBox", "levW"].every(id => document.getElementById(id) && document.getElementById(id).closest("#stepBank"));
    const cutHas = ["cutRun", "cutKeep", "varRun", "entriesFile"].every(id => document.getElementById(id).closest("#stepCut"));
    const fillHas = ["pfRun", "maxExpo", "entriesBox", "nb", "classic3"].every(id => document.getElementById(id).closest("#stepFill"));
    const order = [...document.querySelectorAll("#stepFill, #newsBox, #scanBox, #teamBar, #playersSec")].map(x => x.id);
    const last = document.getElementById("playersSec").compareDocumentPosition(document.getElementById("stepFill")) & Node.DOCUMENT_POSITION_PRECEDING;
    const after = JSON.stringify([BANK.lineups.length, CUT && CUT.keep && CUT.keep.length, PF]);
    delete state.step; save(); renderSteps();
    return { seen, kept, labels, bankHas, cutHas, fillHas, order, last: !!last, same: before === after, dflt: stepNow() };
  });
  check("step bar: Bank / Cut / Fill show one panel each (kept with the slate), with live counts; switching leaves the bank, cut and picks alone; the default follows the work (Fill once a cut exists)",
        sb.seen.bank === "bank|bank" && sb.seen.cut === "cut|cut" && sb.seen.fill === "fill|fill" && sb.kept === "fill" && /^Bank [\d,]+$/.test(sb.labels[0]) && /^Cut [\d,]+ kept$/.test(sb.labels[1]) && /^Fill \d+\/\d+$/.test(sb.labels[2]) &&
        sb.same && sb.dflt === "fill", JSON.stringify(sb));
  check("layout: the Bank step holds the draw controls and the bank table, Cut the cut, Fill the fill and the builders; then the reading folds; Teams and Players last",
        sb.bankHas && sb.cutHas && sb.fillHas && JSON.stringify(sb.order) === JSON.stringify(["stepFill", "newsBox", "scanBox", "teamBar", "playersSec"]) && sb.last, JSON.stringify(sb));
  // Without: click a name in a lineup to hide every unpicked lineup with him; the chip brings them back; Auto-fill skips them
  await pg.click("#bpClear").catch(() => {});
  const pid = await pg.$eval("#bpTable tr:not(.picked)[data-k] .pn", e => e.dataset.pid);
  const totalRows = await pg.evaluate(() => BP.pool.length);
  await pg.click(`#bpTable tr:not(.picked)[data-k] .pn[data-pid="${pid}"]`);
  const wo = await pg.evaluate(id => ({ shown: [...document.querySelectorAll("#bpTable tr:not(.picked)[data-k]")].map(r => BP.pool[+r.dataset.k].ids),
    chip: !!document.querySelector(`#bpWithout [data-fkind="p"][data-fkey="${id}"]`), note: document.getElementById("bpWithout").textContent,
    left: BP.pool.filter(L => !L.ids.includes(id)).length }), pid);
  check("without: no lineup shown holds the player", wo.shown.length > 0 && wo.shown.every(ids => !ids.includes(pid)), wo.note);
  check("without: a chip with the hidden count", wo.chip && new RegExp((totalRows - wo.left) + " lineups? hidden").test(wo.note), wo.note);
  await pg.click("#bpAuto");
  await pg.waitForFunction(() => !/Auto-filling/.test(document.getElementById("bpStatus").textContent), null, { timeout: 120000 });
  check("without: Auto-fill leaves his lineups out", await pg.evaluate(id => BP.b.picked.length > 0 && BP.b.picked.every(k => !BP.pool[k].ids.includes(id)), pid));
  await pg.click(`#bpWithout [data-fkind="p"][data-fkey="${pid}"]`);
  check("without: the chip brings them back", await pg.evaluate(id => !bpFilt.p[id] && !document.querySelector("#bpWithout [data-fkind]"), pid));
  // the side panel: Players, Combos, Cores; a tap cycles with (only lineups with it) / without / off; counts in view and yours
  await pg.click("#bpClear").catch(() => {});
  const shownIds = () => pg.evaluate(() => [...document.querySelectorAll("#bpTable tr:not(.picked)[data-k]")].map(r => +r.dataset.k));
  const sp = await pg.$eval("#bpSideList .srow[data-key]", e => ({ key: e.dataset.key, view: +e.children[1].textContent }));
  check("panel: players listed with their lineups in view", sp.view === await pg.evaluate(id => BP.pool.filter(L => L.ids.includes(id)).length, sp.key), JSON.stringify(sp));
  await pg.click(`#bpSideList .srow[data-key="${sp.key}"]`);
  let ks = await shownIds();
  const brief = await pg.evaluate(() => ({ txt: (document.getElementById("bpBrief") || {}).textContent || "",
    n: BP.pool.map((L, k) => k).filter(k => !BP.b.picked.includes(k) && !bpHidden(k)).length }));
  check("panel: the filtered set's summary: count, average ROI, top 10%", new RegExp("Filtered: " + brief.n + " lineups?, average ROI [+-]\\d+%, top 10% \\d").test(brief.txt), JSON.stringify(brief));
  check("panel: tap once, only lineups with him", ks.length > 0 && await pg.evaluate(([ks, id]) => ks.every(k => BP.pool[k].ids.includes(id)), [ks, sp.key]) &&
        /with /.test(await pg.textContent("#bpWithout")));
  await pg.click(`#bpSideList .srow[data-key="${sp.key}"]`);
  ks = await shownIds();
  check("panel: again, only lineups without him", ks.length > 0 && await pg.evaluate(([ks, id]) => ks.every(k => !BP.pool[k].ids.includes(id)), [ks, sp.key]));
  await pg.click(`#bpSideList .srow[data-key="${sp.key}"]`);
  check("panel: again, off", await pg.evaluate(id => !bpFilt.p[id], sp.key));
  await pg.click('#bpSide [data-tab="pair"]');
  const pr = await pg.$eval("#bpSideList .srow[data-key]", e => e.dataset.key);
  await pg.click(`#bpSideList .srow[data-key="${pr}"]`);
  ks = await shownIds();
  check("panel: a combo with, only lineups holding both", ks.length > 0 && await pg.evaluate(([ks, pk]) => ks.every(k => pk.split("|").every(id => BP.pool[k].ids.includes(id))), [ks, pr]));
  await pg.click('#bpSide [data-tab="core"]');
  const cr = await pg.$eval("#bpSideList .srow[data-key]", e => e.dataset.key);
  await pg.click(`#bpSideList .srow[data-key="${cr}"]`);
  ks = await shownIds();
  check("panel: filters stack: a core with as well, only lineups on that core holding the combo", ks.length > 0 && await pg.evaluate(([ks, ck, pk]) => {
    const keys = DKSim.cores(ctx(), BP.pool);
    return ks.every(k => keys[k] === ck && pk.split("|").every(id => BP.pool[k].ids.includes(id)));
  }, [ks, cr, pr]) || (await pg.evaluate(() => document.querySelectorAll("#bpTable tr:not(.picked)[data-k]").length)) === 0);
  await pg.click('#bpWithout [data-fclear]');
  check("panel: Clear all", await pg.evaluate(() => !Object.keys(bpFilt.p).length && !Object.keys(bpFilt.pair).length && !Object.keys(bpFilt.core).length));
  await pg.click('#bpSide [data-tab="p"]');
  for (const q of [P[sp.key].name.split(" ").slice(-1)[0], P[sp.key].name.split(" ")[0], P[sp.key].name]) {     // last word, first name, full name
    await pg.fill("#bpSideQ", q);
    check("panel: search finds a player by \"" + q + "\"", (await pg.$$eval("#bpSideList .srow[data-key]", r => r.map(x => x.dataset.key))).includes(sp.key));
  }
  await pg.fill("#bpSideQ", "");
  // Max exposure in a small contest: rounded up at 5 entries or fewer, so 3 entries at 40% or 60% fill 3 of 3 (each
  // player in 2 at most) where floor would force them fully disjoint
  const small = await pg.evaluate(() => {
    const c = Object.assign({}, slate.contests.find(x => x.payouts)), pool = BANK.lineups.slice(0, 300).map(L => ({ ids: L.ids }));
    const sim = DKSim.simulate(nightsCtx(c), pool, fieldOf().field, fieldDoc.z, c, 3, 400);
    return [0.4, 0.6].map(p => { const r = DKSim.pick(ctx(), { n: 3, maxExpo: p, minUnique: 3, conds: [], maxCore: null }, pool, sim, c, 3), cnt = {};
      r.chosen.forEach(k => pool[k].ids.forEach(id => { cnt[id] = (cnt[id] || 0) + 1; }));
      // pick fills greedily and never backtracks: on a chalk-heavy random bank the first two can leave no third that
      // fits, so a short set passes only when no lineup in the pool fits beside them (each player in 2 at most, Min unique 3)
      const lim = DKSim.expoLimit(p, 3), stuck = r.chosen.length < 3 && !pool.some((L, k) => !r.chosen.includes(k) &&
        L.ids.every(id => (cnt[id] || 0) + 1 <= lim) && r.chosen.every(j => L.ids.filter(id => pool[j].ids.includes(id)).length <= 5));
      return { p, n: r.chosen.length, stuck, max: Math.max(...Object.values(cnt)), lim, big: DKSim.expoLimit(p, 20) }; });
  });
  const clean = await pg.evaluate(() => !Object.keys(state.cap).length && !Object.keys(state.lock).length);
  check("Max exposure in a small contest: 3 entries at 40% and at 60% fill 3 of 3 where 3 fit, each player in 2 at most (rounded up at 5 entries or fewer; 20 entries still floor)",
        clean && small.every(x => (x.n === 3 || x.stuck) && x.lim === 2 && x.max <= 2) && small[0].big === 8 && small[1].big === 12, JSON.stringify(small));
  // Max exposure binds hand adds: in this contest's set a player goes in at most its limit (DKSim.expoLimit)
  await pg.click("#bpClear").catch(() => {});
  const cap = await pg.evaluate(() => {
    const n = BP.o.n, lim = DKSim.expoLimit(BP.o.maxExpo, n), cnt = {};
    BP.pool.forEach(L => L.ids.forEach(id => { if (!state.lock[id]) cnt[id] = (cnt[id] || 0) + 1; }));
    const p = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0];
    const withP = BP.pool.map((L, k) => k).filter(k => BP.pool[k].ids.includes(p));
    return { n, lim, p, withP: withP.slice(0, lim + 1) };
  });
  for (const k of cap.withP.slice(0, cap.lim)) await pg.evaluate(k => bpAdd(k, true), k);    // forced: this check is about exposure
  const after = await pg.evaluate(c => ({ picked: BP.b.picked.length, btn: (() => { const tr = document.querySelector(`#bpTable tr[data-k="${c.withP[c.lim]}"]`);
    const b = tr && tr.querySelector("button");
    return b ? { text: b.textContent, title: b.title } : null; })() }), cap);
  check(`max exposure, hand adds: ${cap.lim} of ${cap.n} with the most-used player, then his lineups refuse`, after.picked === cap.lim && (!after.btn || after.btn.text === "Add anyway"),
    JSON.stringify(after));
  if (after.btn) check("max exposure, hand adds: the refusal says why, with Add anyway", after.btn.text === "Add anyway" && /his limit \d+/.test(after.btn.title), JSON.stringify(after.btn));
  await pg.evaluate(c => bpAdd(c.withP[c.lim]), cap);
  check("max exposure, hand adds: an add past the limit is refused", await pg.evaluate(c => BP.b.picked.length === c.lim, cap));
  const room = await pg.evaluate(id => { const r = document.querySelector(`#bpSideList .srow[data-key="${id}"]`); return r ? +r.children[3].textContent : null; }, cap.p);
  check("caps: the panel shows his room left (0 at his limit)", room === 0, String(room));
  if (after.btn) {
    await pg.click(`#bpTable tr[data-k="${cap.withP[cap.lim]}"] button.bpForce`);
    check("caps: Add anyway overrides", await pg.evaluate(c => BP.b.picked.length === c.lim + 1 && BP.b.picked.includes(c.withP[c.lim]), cap));
  }
  // Min unique and Max core block a hand add too (with the same override)
  await pg.click("#bpClear").catch(() => {});
  const mu = await pg.evaluate(() => {
    const mu = BP.o.minUnique || 1, keys = DKSim.cores(ctx(), BP.pool), K = BP.pool.length;
    let a = -1, b = -1;
    for (let i = 0; i < K && a < 0; i++) for (let j = i + 1; j < K; j++) {
      const sh = BP.pool[i].ids.filter(id => BP.pool[j].ids.includes(id)).length;
      if (8 - sh < mu) { a = i; b = j; break; }
    }
    const byCore = {}; keys.forEach((k, i) => (byCore[k] = byCore[k] || []).push(i));
    const lim = DKSim.coreLimit(BP.o, BP.o.n), many = Object.values(byCore).find(v => v.length > lim);
    return { a, b, mu, lim, many: many ? many.slice(0, lim + 1) : null };
  });
  if (mu.a >= 0) {
    await pg.evaluate(m => bpAdd(m.a, true), mu);
    check("caps: Min unique blocks a near-copy of a pick", await pg.evaluate(m => bpBlocks(m.b).some(x => /Min unique/.test(x)), mu));
    await pg.click("#bpClear").catch(() => {});
  }
  if (mu.lim && mu.many) {
    for (const k of mu.many.slice(0, mu.lim)) await pg.evaluate(k => bpAdd(k, true), k);
    check("caps: Max core blocks a core past its limit", await pg.evaluate(m => bpBlocks(m.many[m.lim]).some(x => /Max core/.test(x)), mu));
  }
  await pg.click("#bpClear").catch(() => {});
  await pg.click("#bpClear").catch(() => {});

  // Variants of the top: around the top kept lineups, each variant legal, sharing at least Players kept with its parent
  // and fewer than 7 with any lineup kept before; those that join are in the kept pool, tagged and grouped
  const vr = await pg.evaluate(async () => {
    if (!CUT || !CUT.keep) return { skipped: true };
    const keep0 = CUT.keep.slice(), n0 = BANK.lineups.length;
    const def = { sets: $("varSets").value, M: $("varM").value, Mdis: $("varM").disabled, note: $("varSetsNote").textContent };
    document.getElementById("varN").value = "1"; document.getElementById("varK").value = "6"; varSetsSync();   // every 6-of-8 keep-set: 28 draws
    const six = { M: $("varM").value, note: $("varSetsNote").textContent };
    const msg = await runVariants();
    const added = CUT.keep.slice(keep0.length), sh = (a, b) => a.filter(id => b.includes(id)).length;
    const legal = added.every(i => { const L = BANK.lineups[i], rs = L.ids.map(byId);
      return L.ids.length === 8 && new Set(L.ids).size === 8 && rs.every(r => r && r.status !== "Out") && rs.reduce((t, r) => t + r.salary, 0) <= 50000; });
    const near = added.every(i => keep0.every(k => sh(BANK.lineups[k].ids, BANK.lineups[i].ids) < 7));
    const parent = added.every(i => { const m = /variant of #(\d+)/.exec(BANK.tags[i][0]); return m && sh(BANK.lineups[keep0[+m[1] - 1]].ids, BANK.lineups[i].ids) >= 5; });
    const grouped = added.every(i => lineupGroup(i) === "Variants of the top");
    const row = document.querySelector('#ideaTable tr[data-idea="Variants of the top"]');
    return { def, six, each: CUT.variants.each, ks: CUT.variants.keepSets, msg, added: added.length, bankGrew: BANK.lineups.length - n0, legal, near, parent, grouped, bankN: CUT.bankN === BANK.lineups.length, tierA: !!CUT.board.tierA,
             res: document.getElementById("varResult").textContent, row: row ? [...row.cells].map(c => c.textContent) : null };
  });
  check("variants: the result line under the row (new, joined, tier A before → after) and a Variants of the top row in the idea table, after the cut in Banked",
        new RegExp("^\\d+ new, " + vr.added + " joined · Tier A \\d+ → \\d+$").test(vr.res || "") && vr.row && vr.row[1] === "after the cut" && +vr.row[3] === vr.added, JSON.stringify([vr.res, vr.row]));
  check("variants of the top: legal, near their parent (5+ of 8), none sharing 7+ with a kept lineup, in the kept pool, tagged and grouped; the scoreboard redone",
        !vr.skipped && vr.added === vr.bankGrew && vr.legal && vr.near && vr.parent && vr.grouped && vr.bankN && vr.tierA && vr.added > 0 && /^Variants of tier A, the top 1 /.test(vr.msg), JSON.stringify(vr));
  check("variants (C3): every K-of-8 keep-set is the default, 56 each at K 5 (Variants each follows K), and the run used every set once",
        vr.def && vr.def.sets === "all" && vr.def.M === "56" && vr.def.Mdis && vr.def.note === "Variants: every 5-of-8 keep-set, 56 each" &&
        vr.six.M === "28" && /every 6-of-8 keep-set, 28 each/.test(vr.six.note) && vr.each === 28 && vr.ks === "all" && /every keep-set, 28 draws each/.test(vr.msg), JSON.stringify(vr));
  // --- the slate scan ------------------------------------------------------------------------------------
  await pg.fill("#scanN", "20"); await pg.fill("#scanP", "20");
  await pg.click("#scanRun");
  await pg.waitForFunction(() => /^Scanned|failed/.test(document.getElementById("scanStatus").textContent), null, { timeout: 600000 });
  const sc = await pg.evaluate(() => {
    const st = scanStacks(), teams = new Set(rows.filter(usable).map(r => r.team)).size, rowsS = SCAN.rows;
    const sorted = rowsS.every((r, i) => i === 0 || (rowsS[i - 1].thin - r.thin) < 0 || ((rowsS[i - 1].thin === r.thin) && rowsS[i - 1].g_t1 >= r.g_t1 - 1e-12));
    const gains = rowsS.every(r => Math.abs(r.g_t1 - (r.t1 - SCAN.plain.t1)) < 1e-12 && Math.abs(r.g_t10 - (r.t10 - SCAN.plain.t10)) < 1e-12);
    const reads = SCAN.bar > 0 && rowsS.every(r => r.read === (r.g_t1 > SCAN.bar ? (r.field < SCAN.fieldMedian[r.kind + r.n] ? "strong, field light" : "strong, field heavy") : r.g_t1 < -SCAN.bar ? "weak" : "even"));
    const fieldOk = rowsS.every(r => r.field >= 0 && r.field <= 1), thin = rowsS.every(r => r.thin === (r.distinct < SCAN_THIN));
    return { n: rowsS.length, want: st.length, teams, sorted, gains, reads, fieldOk, thin, table: document.querySelectorAll("#scanTable table:not(#scanPlayers) tr").length, msg: document.getElementById("scanStatus").textContent };
  });
  check("slate scan: a row a stack (each team 3+ and 4+, each game 3+ to 5+ with both teams), gains over the plain batch, Read derived, thin flagged, sorted by top-1% gain",
        sc.n === sc.want && sc.n >= sc.teams * 2 && sc.sorted && sc.gains && sc.reads && sc.fieldOk && sc.thin && sc.table === sc.n + 4, JSON.stringify(sc));
  // fixed nights: the same scan again gives the same numbers and order
  const first = await pg.evaluate(() => SCAN.rows.map(r => r.key + ":" + r.g_t1.toFixed(8)).join("|"));
  await pg.click("#scanRun");
  await pg.waitForFunction(() => /^Scanned|failed/.test(document.getElementById("scanStatus").textContent) && !document.getElementById("scanRun").disabled, null, { timeout: 600000 });
  check("slate scan: on the slate's own nights, a rerun repeats exactly (and shows the noise beside each top-1% gain)",
        (await pg.evaluate(() => SCAN.rows.map(r => r.key + ":" + r.g_t1.toFixed(8)).join("|"))) === first && (await pg.evaluate(() => /\u00b1/.test(document.getElementById("scanTable").textContent))));
  const scHold = await pg.evaluate(async () => {        // every lineup a stack's batch drew holds the stack
    const st = scanStacks().find(x => x.kind === "game"), cx = ctx(); cx.state = Object.assign({}, state, { lock: {}, excl: {}, cap: {}, floor: {} }); cx.random = DKSim.seeded(5);
    const res = await DKSim.pool(cx, Object.assign(drawRules(), { conds: st.conds, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, lowN: 0, maxOwn: null }), 10);
    return { n: res.lineups.length, all: res.lineups.every(L => scanHolds(st, L.ids)) };
  });
  check("slate scan: a game stack's lineups hold the stack (both teams)", scHold.n > 0 && scHold.all, JSON.stringify(scHold));
  // two sections, each sortable on its own: a header click sorts (again reverses), kept with the slate's scan
  const so = await pg.evaluate(() => {
    const order = kind => { const out = [], trs = [...document.querySelectorAll("#scanTable tr")]; let on = false;
      trs.forEach(tr => { const th = tr.querySelector("th[colspan]"); if (th) { on = th.textContent === (kind === "team" ? "Team stacks" : "Game stacks"); return; }
        if (on && tr.querySelector(".scanBank")) out.push(SCAN.rows[+tr.querySelector(".scanBank").dataset.i]); }); return out; };
    const sections = [...document.querySelectorAll("#scanTable table:not(#scanPlayers) th[colspan]")].map(t => t.textContent);
    const teamOnly = order("team").every(r => r.kind === "team") && order("game").every(r => r.kind === "game");
    document.querySelector('#scanTable th[data-sk="field"][data-skind="team"]').click();
    const a = order("team").filter(r => !r.thin), down = a.every((r, i) => i === 0 || a[i - 1].field >= r.field);
    document.querySelector('#scanTable th[data-sk="field"][data-skind="team"]').click();
    const b = order("team").filter(r => !r.thin), up = b.every((r, i) => i === 0 || b[i - 1].field <= r.field);
    const game = order("game").filter(r => !r.thin), gameDefault = game.every((r, i) => i === 0 || game[i - 1].g_t1 >= r.g_t1);
    const kept = store(scanKey()).sort.team;
    return { sections, teamOnly, down, up, gameDefault, kept, arrow: /Field holds ↑/.test(document.querySelector('#scanTable th[data-sk="field"][data-skind="team"]').textContent) };
  });
  check("slate scan: Team stacks and Game stacks, each sorted on its own by a header click (again reverses, arrow shown), the sort kept with the scan",
        JSON.stringify(so.sections) === JSON.stringify(["Team stacks", "Game stacks"]) && so.teamOnly && so.down && so.up && so.gameDefault && so.arrow && so.kept && so.kept.k === "field" && so.kept.dir === 1, JSON.stringify(so));
  const rules0 = await pg.evaluate(() => (state.rules || []).length);
  await pg.evaluate(() => document.querySelector("#scanTable table:not(#scanPlayers) .scanBank").click());
  check("slate scan: Bank this adds the stack's rule for the next draw", await pg.evaluate(n => state.rules.length > n && /\d\+/.test(state.rules[state.rules.length - 1].label), rules0));
  await pg.evaluate(n => { state.rules = state.rules.slice(0, n); save(); renderRules(); }, rules0);
  // the scan's top reads (up to 5 strongest stacks, the leverage players), each opening its game; the full tables folded
  const trd = await pg.evaluate(() => {
    const b = [...document.querySelectorAll("#scanTable .topread")], fold = document.getElementById("scanAll"), thick = SCAN.rows.filter(r => !r.thin), tops = (thick.length ? thick : SCAN.rows.slice()).sort((a, c) => c.g_t1 - a.g_t1).slice(0, 5);
    const stackBtns = b.filter(x => !x.classList.contains("read-leverage")).map(x => x.textContent.split(" ")[0] + " " + x.textContent.split(" ")[1]);
    const lev = b.filter(x => x.classList.contains("read-leverage")).length, wantLev = SCAN.players.filter(r => !r.thin && r.read === "leverage").length;
    b[0].click();
    const opened = view.panel === b[0].dataset.team && !!document.querySelector('#teamPanel .tile[data-team="' + b[0].dataset.team + '"]');
    view.panel = null; renderTiles(); renderPlayers();
    return { n: stackBtns.length, keys: stackBtns, want: tops.map(r => r.key), lev, wantLev, closed: fold && !fold.open, inFold: !!fold.querySelector("th[colspan]"), opened };
  });
  check("slate scan: a Top reads strip (the 5 strongest stacks, the leverage players) opening its game; the full tables and the team rollup in a closed All scan rows fold",
        trd.n === trd.want.length && JSON.stringify(trd.keys) === JSON.stringify(trd.want) && trd.lev === trd.wantLev && trd.closed && trd.inFold && trd.opened, JSON.stringify(trd));
  // the game view's scan: game stacks under the header, each team card's 3+ / 4+ rows and its core and leverage players
  const gsc = await pg.evaluate(() => {
    const t = teamsOf().teams[0]; view.panel = t.team; renderTiles();
    const g = gameOf(t.team), gr = [...document.querySelectorAll("#teamPanel table.gstk tr")].length - 1, wantG = SCAN.rows.filter(r => r.kind === "game" && r.game === g).length;
    const blk = document.querySelector('#teamPanel .teamside .scanblk'), sr = blk.querySelectorAll(".sr").length, wantT = SCAN.rows.filter(r => r.kind === "team" && r.team === t.team).length;
    const names = [...blk.querySelectorAll(".read-core, .read-leverage")].map(x => x.textContent.replace(/ \((core|leverage)\)$/, "")).sort();
    const wantN = SCAN.players.filter(r => r.team === t.team && !r.thin && (r.read === "core" || r.read === "leverage")).map(r => r.key).sort();
    const n0 = state.rules.length; blk.querySelector(".scanBank").click(); const added = state.rules.length === n0 + 1 && /\d\+/.test(state.rules[n0].label);
    state.rules = state.rules.slice(0, n0); save(); renderRules();
    view.panel = null; renderTiles(); renderPlayers();
    return { gr, wantG, sr, wantT, names, wantN, added };
  });
  check("game view: the game's stack rows from the scan; each team card's Scan block with its 3+ / 4+ rows and core / leverage players, Bank this working",
        gsc.gr === gsc.wantG && gsc.wantG >= 1 && gsc.sr === gsc.wantT + 1 && JSON.stringify(gsc.names) === JSON.stringify(gsc.wantN) && gsc.added, JSON.stringify(gsc));
  // the player scan, at the top: a row for every player in the pool projected 15+ minutes, gains over the same plain
  // batch, Read on the players' own noise and their median field ownership, the team rollup from those reads
  const ps = await pg.evaluate(() => {
    const want = rows.filter(r => usable(r) && (r.min || 0) * (minScale[r.id] || 1) >= PUNT_MIN).map(r => r.id).sort(), P = SCAN.players, m = SCAN.pownMedian;
    const ids = P.map(r => r.id).sort(), bar = SCAN.pbar;
    const reads = bar > 0 && P.every(r => r.read === (r.g_t1 > bar ? (r.fown >= m ? "core" : "leverage") : r.g_t1 < -bar ? (r.fown >= m ? "fade" : "skip") : r.g_t1 > 0 ? (r.fown >= m ? "lean core" : "lean leverage") : "even"));
    const gains = P.every(r => Math.abs(r.g_t1 - (r.t1 - SCAN.plain.t1)) < 1e-12 && Math.abs(r.g_cash - (r.cash - SCAN.plain.cash)) < 1e-12);
    const noOut = P.every(r => { const x = byId(r.id); return x.status !== "Out" && !x.deepOut; });
    const first = document.querySelector("#scanTable table").id === "scanPlayers" && !document.querySelector('#scanTable th[data-skind="player"]');
    const roll = SCAN.teamRoll.every(t => t.core.every(r => r.read === "core" && r.team === t.team) && t.lev.every(r => r.read === "leverage" && r.team === t.team) && t.n >= 1 &&
      (!t.st || (t.st.kind === "team" && t.st.team === t.team)));
    const rollAll = P.filter(r => !r.thin && (r.read === "core" || r.read === "leverage")).every(r => SCAN.teamRoll.some(t => t.ids.includes(r.id)));
    return { n: P.length, same: JSON.stringify(ids) === JSON.stringify(want), reads, gains, noOut, first, roll, rollAll, sum: SCAN.players.reduce((o, r) => (o[r.read] = (o[r.read] || 0) + 1, o), {}) };
  });
  check("player scan: a row for every player in the pool at 15+ projected minutes (none Out, Doubtful or deep bench), gains over the plain batch, Read core/leverage/fade/skip/even from its own noise and the median field own; no Players table of its own in the scan (the Players list carries it), the team rollup first",
        ps.n > 20 && ps.same && ps.reads && ps.gains && ps.noOut && ps.first, JSON.stringify(ps));
  check("player scan: the team rollup lists each team's core and leverage players and its best team stack", ps.roll && ps.rollAll, JSON.stringify(ps));
  const pHold = await pg.evaluate(async () => {        // a player's batch holds him
    const b = scanPlayers()[3], cx = ctx(); cx.state = Object.assign({}, state, { lock: {}, excl: {}, cap: {}, floor: {} }); cx.random = DKSim.seeded(5);
    const res = await DKSim.pool(cx, Object.assign(drawRules(), { conds: b.conds, levW: 0, minSal: 0, maxTeam: 8, stackN: 0, lowN: 0, maxOwn: null }), 10);
    return { n: res.lineups.length, all: res.lineups.every(L => L.ids.includes(b.id)) };
  });
  check("player scan: a player's batch holds him", pHold.n > 0 && pHold.all, JSON.stringify(pHold));
  const pList = await pg.evaluate(() => {
    renderPlayers();
    const ok = SCAN.players.every(x => { const el = document.querySelector(`#players .row[data-id="${x.id}"]`); if (!el) return true;
      // Cash and Read (coloured) as columns; Top 1% (with its noise bar), ROI and the bank share in Read's hover (2026-11-20)
      const c = el.querySelectorAll(".col-scan"), tip = c[1].title || "";
      return c.length === 3 && c[0].textContent === (x.g_cash > 0 ? "+" : "") + (100 * x.g_cash).toFixed(1) &&
        c[1].textContent === x.read && c[1].querySelector(".read-" + x.read.replace(/ /g, "-")) && !!c[2].querySelector(".pbank") &&
        tip.includes("top-1% gain " + (x.g_t1 > 0 ? "+" : "") + (100 * x.g_t1).toFixed(2) + " (noise \u00b1" + (100 * x.noise).toFixed(2) + ")") &&
        tip.includes("ROI gain " + (x.g_roi > 0 ? "+" : "") + (100 * x.g_roi).toFixed(0)) && (!BANK.lineups.length || /Bank \d+% vs field \d+%/.test(tip)); });
    view.sort = "scan"; view.dir = -1; renderPlayers();
    const ids = [...document.querySelectorAll("#players .row")].map(e => e.dataset.id).filter(id => byId(id).status !== "Out"), g = ids.map(id => scanRowOf(id) ? scanRowOf(id).g_t1 : -Infinity);
    const sorted = g.every((x, i) => i === 0 || g[i - 1] >= x);
    view.sort = "value"; view.dir = -1; renderPlayers();
    return { ok, sorted };
  });
  check("player scan: Cash and Read (coloured) columns with Bank this; Top 1% (noise bar), ROI and the bank share in Read's hover; sortable by the scan", pList.ok && pList.sorted, JSON.stringify(pList));
  const mpg = await pg.evaluate(() => { renderPlayers(); const heads = [...document.querySelectorAll("#players .head span[data-sort]")].map(x => x.dataset.sort);
    const r = rows.find(x => x.status !== "Out" && document.querySelector('#players .row[data-id="' + x.id + '"]'));
    const keep = [r.min_avg, r.min_last5, r.min_cv, r.obpr, r.dbpr, r.bpr, r.bpr_rank]; r.min_avg = 27.4; r.min_last5 = [30, 22, 28, 31, 26]; r.min_cv = 0.12;
    r.obpr = 3.214; r.dbpr = 1.05; r.bpr = 4.26; r.bpr_rank = 2; renderPlayers();
    const cell = document.querySelector('#players .row[data-id="' + r.id + '"] .col-mpg'), text = cell.textContent, tip = cell.title;
    const ob = document.querySelector('#players .row[data-id="' + r.id + '"] .col-obpr'), obText = ob.textContent, obTip = ob.title;
    const r2 = rows.find(x => x !== r && x.obpr == null && document.querySelector('#players .row[data-id="' + x.id + '"]')), dash = r2 ? document.querySelector('#players .row[data-id="' + r2.id + '"] .col-obpr').textContent : "–";
    [r.min_avg, r.min_last5, r.min_cv, r.obpr, r.dbpr, r.bpr, r.bpr_rank] = keep; renderPlayers();
    document.querySelector('#players .head [data-sort="mpg"]').click();
    const v = [...document.querySelectorAll("#players .row")].map(e => { const x = byId(e.dataset.id); return x.min_avg != null ? x.min_avg : -1; }), down = v.every((x, i) => i === 0 || v[i - 1] >= x);
    view.sort = "value"; view.dir = -1; renderPlayers();
    return { after: heads.indexOf("mpg") === heads.indexOf("min") + 1, gone: !["scan", "sroi"].some(k => heads.includes(k)) && heads.indexOf("bank") === heads.indexOf("own") + 1, cash: heads.includes("scash"), text, want: "27", tip, down, obText, obTip, dash, obAfter: heads.indexOf("obpr") === heads.indexOf("mpg") + 1 };
  });
  check("Players list: MPG (season minutes a game) right after Min, last 5 in the hover, sortable; no Top 1% / ROI / Bank columns, Cash kept",
        mpg.after && mpg.gone && mpg.cash && mpg.text === mpg.want && mpg.tip === "Season 27.4 min a game played; last 5: 30, 22, 28, 31, 26; minutes CV 0.12" &&
        mpg.obAfter && mpg.obText === "3.2" && mpg.obTip === "EvanMiya OBPR 3.21; BPR 4.26; DBPR 1.05; #2 on " + "" + mpg.obTip.split(" on ")[1].split(" by")[0] + " by OBPR" && mpg.dash === "–" && mpg.down, JSON.stringify(mpg));
  check("player table: with a scan the scan columns show (no-scan layout off)", await pg.evaluate(() => { renderPlayers(); const c = document.querySelector("#players .row .col-scan");
    return !$("players").classList.contains("noscan") && !!c && getComputedStyle(c).display !== "none"; }));
  const c1 = await pg.evaluate(() => {
    renderPlayers(); const bs = bankShare(), rowsIn = [...document.querySelectorAll("#players .row.bankgap-in")].map(e => e.dataset.id), rowsOut = [...document.querySelectorAll("#players .row.bankgap-out")].map(e => e.dataset.id);
    // the rule by hand: leverage < 1.5 f (f >= 2%), core < 0.75 f, even < 0.5 f; fade >= f and >= 10%
    const f = id => own(byId(id)) / 100, k = { leverage: 1.5, core: 0.75, "lean leverage": 1.5, "lean core": 0.75, even: 0.5 };
    const under = (rd, b, fo) => k[rd] != null && (!/leverage/.test(rd) || fo >= 0.02) && b < k[rd] * fo, over = (rd, b, fo) => (rd === "fade" && b >= fo && b >= 0.1) || (rd === "skip" && b >= 2 * fo && b >= 0.08);
    const inOk = rowsIn.every(id => under(scanRowOf(id).read, bs[id] || 0, f(id))), outOk = rowsOut.every(id => over(scanRowOf(id).read, bs[id] || 0, f(id)));
    const want = SCAN.players.filter(x => byId(x.id).status !== "Out" && (under(x.read, bs[x.id] || 0, f(x.id)) || over(x.read, bs[x.id] || 0, f(x.id))) && document.querySelector('#players .row[data-id="' + x.id + '"]')).length;
    const tips = [bankGap("leverage", 0.04, 0.06), bankGap("leverage", 0.04, 0.015), bankGap("core", 0.2, 0.3), bankGap("core", 0.25, 0.3), bankGap("even", 0.04, 0.1),
                  bankGap("fade", 0.25, 0.18), bankGap("fade", 0.08, 0.05), bankGap("fade", 0.15, 0.2),
                  bankGap("lean leverage", 0.04, 0.06), bankGap("lean leverage", 0.01, 0.015), bankGap("lean core", 0.2, 0.3),
                  bankGap("skip", 0.15, 0.06), bankGap("skip", 0.11, 0.06), bankGap("skip", 0.07, 0.02)].map(g => g && g.tip);
    // the focus set: the strong core / leverage by gain first, then the lean ones by gain
    const P2 = SCAN.players.filter(x => !x.thin), strong = P2.filter(x => x.read === "core" || x.read === "leverage").sort((a, b) => b.g_t1 - a.g_t1),
          lean = P2.filter(x => /^lean /.test(x.read)).sort((a, b) => b.g_t1 - a.g_t1), focusOk = JSON.stringify(SCAN.focus) === JSON.stringify(strong.concat(lean).slice(0, 6).map(x => x.id));
    const leanCls = [...document.querySelectorAll("#players .rdc span")].filter(e => /^lean /.test(e.textContent)).every(e => e.className === "read-" + e.textContent.replace(" ", "-"));
    const n0 = state.rules.length, b = document.getElementById("focusBank");
    let rule = null, pre = null;
    if (b) {                          // opens template 5 pre-filled; Add rule saves it
      b.click(); pre = { type: $("rtType").value, n: +$("rtN").value, chips: Array.from($("rtList").selectedOptions).map(o => o.value), added: state.rules.length - n0 };
      $("rtSave").click(); rule = state.rules[n0]; state.rules = state.rules.slice(0, n0); save(); renderRules();
      Array.from($("rtList").options).forEach(o => { o.selected = false; }); rtChips();
    }
    return { focusIds: SCAN.focus || [], pre, tips, focusOk, leanCls, inOk, outOk, shown: rowsIn.length + rowsOut.length, want, rule: rule && { type: rule.type, n: rule.n, k: rule.ids.length, same: JSON.stringify(rule.ids.slice().sort()) === JSON.stringify((SCAN.focus || []).slice().sort()) }, hasBtn: !!b, focus: (SCAN.focus || []).length };
  });
  check("bank helpers (C1, against field ownership): the tooltips state the rule and the numbers (leverage 1.5x from 2% owned, core 0.75x, even 0.5x, fade at the field and 10%+)",
        JSON.stringify(c1.tips) === JSON.stringify(["Leverage: 4% of bank vs 6% field (want 9%+)", null, "Core: 20% of bank vs 30% field (want 23%+)", null,
                                                     "Even: 4% of bank vs 10% field (want 5%+)", "Fade: 25% of bank vs 18% field (want under 18%)", null, null,
                                                     "Lean leverage: 4% of bank vs 6% field (want 9%+)", null, "Lean core: 20% of bank vs 30% field (want 23%+)",
                                                     "Skip: 15% of bank vs 6% field (want under 12%)", null, null]), JSON.stringify(c1.tips));
  check("lean reads: the focus set takes strong core / leverage first, then lean by gain; lean reads in their own colour class", c1.focusOk && c1.leanCls, JSON.stringify([c1.focusOk, c1.leanCls]));
  check("bank helpers (C1): the Players list marks a scan read the bank holds too little of (against the field) and a fade it holds too much of; Bank: at least 3 of the focus set adds one min-N rule (not locks)",
        c1.inOk && c1.outOk && c1.shown === c1.want && (c1.focus < 2 || (c1.hasBtn && c1.pre.type === "min" && c1.pre.n === Math.min(3, c1.focus) && c1.pre.added === 0 &&
         JSON.stringify(c1.pre.chips.slice().sort()) === JSON.stringify(c1.focusIds.slice().sort()) && c1.rule.type === "min" && c1.rule.n === Math.min(3, c1.focus) && c1.rule.same)), JSON.stringify(c1));
  const pso = await pg.evaluate(() => {
    view.sort = "sroi"; view.dir = -1; renderPlayers();      // the ROI gain still sorts (its column is in Read's hover now)
    const g = [...document.querySelectorAll("#players .row")].map(e => scanRowOf(e.dataset.id)).filter(x => x && byId(x.id).status !== "Out").map(x => x.g_roi);
    const down = g.every((x, i) => i === 0 || g[i - 1] >= x);
    view.sort = "value"; view.dir = -1; renderPlayers();
    return { down, n: g.length };
  });
  check("Players list: sorts by the scan's ROI gain", pso.down && pso.n > 20, JSON.stringify(pso));
  const psb = await pg.evaluate(() => {
    const n0 = (state.rules || []).length, b = document.querySelector("#players .row:not(.out) .pbank"), r = byId(b.closest(".row").dataset.id); b.click();
    const add = state.rules[state.rules.length - 1], one = add.type === "min" && add.n === 1 && add.ids.length === 1 && add.ids[0] === r.id && state.rules.length === n0 + 1;
    const tb = document.querySelector("#scanPlayers .scanBank[data-t]"); let two = null;
    if (tb) { const t = SCAN.teamRoll[+tb.dataset.t]; tb.click(); const a2 = state.rules[state.rules.length - 1];
      two = a2.type === "min" && a2.n === 2 && JSON.stringify(a2.ids.slice().sort()) === JSON.stringify(t.ids.slice().sort()) && t.ids.length >= 2; }
    state.rules = state.rules.slice(0, n0); save(); renderRules();
    return { one, two, teamButtons: document.querySelectorAll("#scanPlayers .scanBank[data-t]").length, rollN: SCAN.teamRoll.filter(t => t.n >= 2).length };
  });
  check("player scan: Bank this on a player adds at least 1 of him; on a team (2+ core/leverage players), at least 2 of them",
        psb.one && psb.teamButtons === psb.rollN && (psb.rollN === 0 || psb.two), JSON.stringify(psb));
  // --- the builder on one screen ---------------------------------------------------------------------
  dialogs = [];
  await pg.fill("#maxUse", "3"); await pg.fill("#maxNight", "60");
  await pg.click("#nbOn");
  await pg.waitForFunction(() => NB.on && BP && BP.review && document.querySelectorAll("#nbTabs button").length > 0, null, { timeout: 300000 });
  const nb_nb0 = await pg.evaluate(() => { const step0 = stepNow(); showStep("bank");
    const out = { classicHidden: document.getElementById("classic3").hidden, status: document.getElementById("cutStatus").nextElementSibling.id,
      details: ["entriesBox", "pfBox"].every(id => document.getElementById(id).closest("#nbDetails")),
      bank: !document.getElementById("bankBox").closest("#nbDetails") && !!document.getElementById("bankBox").closest("#stepBank") && document.getElementById("bankBox").offsetParent !== null &&
        !!document.querySelector("#bankBox input[data-tag]") && !!document.getElementById("groupName") && document.getElementById("groupName").offsetParent !== null };
    showStep(step0); return out; });
  check("one screen: Classic hidden, the status under the step bar, contests and night view in Details; the bank table (tag boxes, grouping) in the Bank step, not folded",
        nb_nb0.classicHidden && nb_nb0.status === "stepBank" && nb_nb0.details && nb_nb0.bank, JSON.stringify(nb_nb0));
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  await pg.waitForFunction(() => BP && BP.review && document.querySelectorAll("#nbList tr[data-k]").length > 0, null, { timeout: 300000 });
  const nb_tabs = await pg.evaluate(() => [...document.querySelectorAll("#nbTabs button")].map(b => {
    const x = nbContests().find(y => String(y.c.id) === b.dataset.cid), have = (PF[b.dataset.cid] || []).length;
    return { ok: new RegExp(" " + have + "/" + x.n + "$").test(b.textContent), red: b.classList.contains("short") === (have < x.n || nbOverCap(b.dataset.cid, x.n)) }; }));
  check("one screen: a tab per contest, its fill (picked / entries), red when short or past a cap", nb_tabs.length >= 2 && nb_tabs.every(t => t.ok && t.red), JSON.stringify(nb_tabs));
  const nb_caps = await pg.evaluate(() => { const c = {}, use = {}; let n = 0;
    Object.values(PF).forEach(v => { const within = new Set(v).size === v.length; v.forEach(bi => { n++; use[bi] = (use[bi] || 0) + 1; BANK.lineups[bi].ids.forEach(id => { if (!state.lock[id]) c[id] = (c[id] || 0) + 1; }); }); });
    return { maxPlayer: Math.max(0, ...Object.values(c)), lim: nightLimit(), maxUse: Math.max(0, ...Object.values(use)), within: Object.values(PF).every(v => new Set(v).size === v.length) }; });
  check("one screen: Fill keeps the night cap (60%) and Max contests per lineup (3), unique within a contest", nb_caps.maxPlayer <= nb_caps.lim && nb_caps.maxUse <= 3 && nb_caps.within, JSON.stringify(nb_caps));
  const nb_sum1 = await pg.evaluate(() => document.getElementById("nbSum").textContent);
  const nbo = await pg.evaluate(() => {
    const C = ownClump(), picks = Object.keys(PF).reduce((a, k) => a.concat(PF[k].map(bi => BANK.lineups[bi].ids)), []), el = document.getElementById("nbOwnPos");
    return { t: el && el.textContent, pc: picks.length ? C.at(picks).pct : null };
  });
  check("builder bar: own position, the field's own-sum quartiles and the picks' percentile", !!nbo.t && (nbo.pc == null ? /no picks yet/.test(nbo.t) : nbo.t.includes("picks at the field's " + nbo.pc)), JSON.stringify(nbo));
  const lkm = await pg.evaluate(() => { const id = BP.pool[BP.b.picked[0] != null ? BP.b.picked[0] : 0].ids[0]; state.lock[id] = 1; renderPlayers();
    const row = document.querySelector('#fillPlayersSlot #players .row[data-id="' + id + '"]'), has = !!(row && row.classList.contains("locked")), other = document.querySelectorAll("#fillPlayersSlot #players .row.locked").length;
    delete state.lock[id]; renderPlayers(); return { has, other, after: document.querySelectorAll("#fillPlayersSlot #players .row.locked").length }; });
  check("one screen: a locked player marked in the Players list under the lineups", lkm.has && lkm.other === 1 && lkm.after === 0, JSON.stringify(lkm));
  // the Fill step: one set of fill buttons, the settings folded to one line, Clear bank in the Bank step only, no side pane
  const fb = await pg.evaluate(() => ({ ids: ["nbFill", "nbUndo", "nbVar", "nbAuto", "nbExport", "nbSave", "nbRight", "nbPlayers"].filter(id => document.getElementById(id)),
    buttons: [...document.querySelectorAll("#fillButtons button:not(.linkbtn)")].map(b => b.textContent), clear: document.getElementById("bankClear").closest("section.step").id,
    sum: document.getElementById("fillSetSum").textContent, folded: ["maxExpo", "maxNight", "minUnique", "maxCore", "maxPair", "maxUse", "lockFill", "pfObj", "nSims"].every(id => document.getElementById(id).closest("#fillSet")) && document.getElementById("fillSet").tagName === "DETAILS", varIn: document.getElementById("varRun").closest("section.step").id,
    heads: [...document.querySelectorAll("#fillPlayersSlot #players .head span[data-sort]")].map(x => x.textContent.replace(/ [↓↑]$/, "")) }));
  check("fill step: one set of buttons (Fill all contests, Auto-fill the rest, Undo fill, New nights, Export DK entries, Save build, Load build), Variants only in Cut, Clear bank only in Bank, the settings one line, no side pane",
        fb.ids.length === 0 && JSON.stringify(fb.buttons) === JSON.stringify(["Fill all contests", "Auto-fill the rest", "Undo fill", "New nights", "Export DK entries", "Save build", "Load build"]) && fb.clear === "stepBank" &&
        fb.varIn === "stepCut" && fb.folded && /^Fill: contest 60% · night 60% · unique 3 · core 15% · max 3 contests · locks: draws only · Max ROI · \d+ nights$/.test(fb.sum) &&
        ["Here", "Tonight", "Room"].every(h => fb.heads.includes(h)), JSON.stringify(fb));
  // the operator's case (2026-11-20, a Fill-step row's "use" clipped off the name): at 1280px in the Fill step every
  // action button is in the L / X group and is what a click at its centre lands on
  await pg.setViewportSize({ width: 1280, height: 900 });
  const fact = await pg.evaluate(() => {
    renderPlayers();
    const acts = [...document.querySelectorAll("#fillPlayersSlot #players .row .qout, #fillPlayersSlot #players .row .deepin")].filter(b => b.offsetParent);
    return { n: acts.length, fill: $("players").classList.contains("fillcols"), inLx: acts.every(b => b.closest(".lx")),
             hit: acts.slice(0, 15).every(b => { b.scrollIntoView({ block: "center" }); const r = b.getBoundingClientRect(); return document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2) === b; }) };
  });
  check("player table (Fill step, 1280px): out / play / use / drop in the L / X group and clickable", fact.fill && fact.n > 0 && fact.inLx && fact.hit, JSON.stringify(fact));
  await pg.setViewportSize({ width: 1100, height: 900 });
  dialogs = [];
  const nBank = await pg.evaluate(() => BANK.lineups.length);
  pg.removeAllListeners("dialog"); pg.once("dialog", d => { dialogs.push(d.message()); d.dismiss(); });
  await pg.click("#bankClear");
  check("Clear bank asks first (dismissed: the bank stays)", dialogs.length === 1 && /Clear the bank/.test(dialogs[0]) && (await pg.evaluate(() => BANK.lineups.length)) === nBank, JSON.stringify(dialogs));
  pg.on("dialog", d => { dialogs.push(d.message()); d.accept(); });
  await pg.evaluate(() => showStep("fill"));
  check("one screen: the live summary, this contest and tonight (ROI, top 10%, top 1%, cash), and tier A", /Tonight: \d+ entr/.test(nb_sum1) && /ROI/.test(nb_sum1) && /top 10%/.test(nb_sum1) && /top 1%/.test(nb_sum1) && /cash/.test(nb_sum1) && /Tier A tonight: \d+ lineup/.test(nb_sum1), nb_sum1);
  // Add and Remove from the list: the pick, its contest's portfolio, the tab and the summary move together
  const nb_addRm = await pg.evaluate(async () => {
    const cid = BP.review, before = BP.b.picked.length, sumB = document.getElementById("nbSum").textContent;
    if (before >= BP.o.n) { const r = document.querySelector("#nbList tr.picked button.bpRm"); r.click(); }
    const mid = BP.b.picked.length, add = document.querySelector("#nbList tr:not(.picked) button.bpAdd") || document.querySelector("#nbList tr:not(.picked) button.bpForce");
    if (!add) return { skipped: true };
    const k = +add.closest("tr").dataset.k; add.click();
    const after = BP.b.picked.length, inPF = PF[cid].includes(BP.idx[k]), tab = document.querySelector('#nbTabs button[data-cid="' + cid + '"]').textContent;
    document.querySelector('#nbList tr.picked[data-k="' + k + '"] button.bpRm').click();
    return { mid, after, inPF, tabOk: new RegExp(" " + after + "/").test(tab), back: BP.b.picked.length === mid && !PF[cid].includes(BP.idx[k]), sumMoved: document.getElementById("nbSum").textContent !== "" };
  });
  check("one screen: Add from the list picks it into the contest's portfolio and its tab; Remove takes it out", !nb_addRm.skipped && nb_addRm.after === nb_addRm.mid + 1 && nb_addRm.inPF && nb_addRm.tabOk && nb_addRm.back, JSON.stringify(nb_addRm));
  // the Players list under the lineups: this contest's and tonight's exposure, the room under the binding cap
  const nb_pp = await pg.evaluate(() => {
    const id = BP.pool[BP.b.picked[0]].ids[0], r = document.querySelector('#fillPlayersSlot #players .row[data-id="' + id + '"]');
    const heads = [...document.querySelectorAll("#fillPlayersSlot #players .head > span")].map(x => x.textContent.replace(/ [↓↑]$/, "")), cells = [...r.children].map(x => x.textContent);
    const at = h => cells[heads.indexOf(h)];
    const here = BP.b.picked.filter(k => BP.pool[k].ids.includes(id)).length, night = (nightUsed(BP.review)[id] || 0) + here, lim = bpLimits()[id];
    return { here: at("Here"), night: at("Tonight"), room: at("Room"), wantHere: Math.round(100 * here / BP.o.n) + "%", wantNight: Math.round(100 * night / nightEntries()) + "%", wantRoom: String(lim - here) };
  });
  check("one screen: the Players list under the lineups shows his exposure here and tonight, and the room left", nb_pp.here === nb_pp.wantHere && nb_pp.night === nb_pp.wantNight && nb_pp.room === nb_pp.wantRoom, JSON.stringify(nb_pp));
  const nb_tap = await pg.evaluate(() => { const id = BP.pool[0].ids[0], nm = () => document.querySelector('#fillPlayersSlot #players .row[data-id="' + id + '"] .nm');
    nm().click(); const a = bpFilt.p[id], shownA = [...document.querySelectorAll("#nbList tr[data-k]:not(.picked)")].every(tr => BP.pool[+tr.dataset.k].ids.includes(id));
    nm().click(); const b = bpFilt.p[id], shownB = [...document.querySelectorAll("#nbList tr[data-k]:not(.picked)")].every(tr => !BP.pool[+tr.dataset.k].ids.includes(id));
    nm().click(); return [a, b, bpFilt.p[id] || "off", shownA, shownB]; });
  check("one screen: tapping a player's name in the Players list cycles with, without, off and filters the lineups", JSON.stringify(nb_tap) === JSON.stringify(["with", "without", "off", true, true]), JSON.stringify(nb_tap));
  // variants fold under their parent
  const nb_fold = await pg.evaluate(() => {
    for (const x of nbContests()) {
      review(String(x.c.id));
      const btn = document.querySelector("#nbList .nbKids");
      if (!btn) continue;
      const pk = +btn.dataset.k; btn.click();
      const kids = [...document.querySelectorAll("#nbList tr.kid")].map(tr => +tr.dataset.k);
      const ok = kids.length > 0 && kids.every(k => /^variant of #\d+$/.test(BANK.tags[BP.idx[k]][0]) && CUT.keep[+BANK.tags[BP.idx[k]][0].split("#")[1] - 1] === BP.idx[pk]);
      const loose = [...document.querySelectorAll("#nbList tr[data-k]:not(.kid):not(.picked)")].some(tr => kids.includes(+tr.dataset.k));
      return { found: true, kids: kids.length, ok, loose };
    }
    const vars = BANK.tags.filter(t => /^variant of/.test(t[0])).length;
    return { found: false, vars };
  });
  check("one screen: variants fold under their parent (expanding inline), not as rows of their own", nb_fold.found ? nb_fold.ok && !nb_fold.loose : nb_fold.vars === 0, JSON.stringify(nb_fold));
  // Pairs and Cores open in the right pane; Players comes back
  await pg.click('#nbRTabs button[data-rt="pair"]');
  const nb_side = await pg.evaluate(() => ({ inPane: document.getElementById("bpSide").parentNode.id, tab: bpTab, rows: document.querySelectorAll("#bpSideList .srow[data-key]").length }));
  await pg.click('#nbRTabs button[data-rt="p"]');
  check("one screen: Pairs and Cores as tabs above the Players list (in its place), Players back after", nb_side.inPane === "fillSideSlot" && nb_side.tab === "pair" && nb_side.rows > 0 &&
        (await pg.evaluate(() => !document.getElementById("playersSec").hidden && document.getElementById("playersSec").parentNode.id === "fillPlayersSlot" && bpTab === "p")), JSON.stringify(nb_side));
  // Export from the top bar: one row per entry with a lineup, no lineup twice in a contest
  const [nb_dl9] = await Promise.all([pg.waitForEvent("download"), pg.click("#pfExport")]);
  const nb_out9 = fs.readFileSync(await nb_dl9.path(), "utf8").trim().split(/\r?\n/).map(l => l.split(","));
  const nb_per = {}; let nb_twice = 0;
  nb_out9.slice(1).forEach(r => { const k = r[2] + ":" + r.slice(4, 12).slice().sort().join("|"); if (nb_per[k]) nb_twice++; nb_per[k] = 1; });
  // C6: the latest tips in UTIL: no G / F-slot player tips later than a UTIL player he could legally swap with
  const tipOfId = id => Date.parse(P[id].game_start || "") || 0, canG = id => isG(P[id]), canF = id => isF(P[id]);
  const lateBad = nb_out9.slice(1).filter(r => r[4]).filter(r => { const sl = r.slice(4, 12), util = sl.slice(6, 8);
    return sl.slice(0, 6).some((p, j) => util.some(u => tipOfId(p) > tipOfId(u) && (j < 3 ? canG(u) : canF(u)))); });
  check("export: the latest-tipping players in the UTIL slots wherever positions allow (a reorder only)", nb_out9.length > 1 && lateBad.length === 0, JSON.stringify(lateBad.slice(0, 2)));
  check("one screen: Export from the top bar, DraftKings' header, no lineup twice in one contest", nb_out9[0].slice(0, 4).join(",") === "Entry ID,Contest Name,Contest ID,Entry Fee" && nb_out9.length > 1 && nb_twice === 0, nb_out9.length + " rows, " + nb_twice + " nb_twice");
  // Classic view: the same portfolios, the outputs back in place
  const nb_pfNB = await pg.evaluate(() => JSON.stringify(PF));
  await pg.click("#nbOff");
  check("Classic view: back to the old layout with the same portfolios", await pg.evaluate(p => !document.getElementById("classic3").hidden && document.getElementById("nb").hidden &&
        document.getElementById("entriesBox").parentNode.id === "s2out" && document.getElementById("cutStatus").nextElementSibling.id === "stepBank" && JSON.stringify(PF) === p &&
        document.getElementById("playersSec").parentNode.id === "playersHome", nb_pfNB));
  await pg.fill("#maxUse", "1");
  // Quick lineup: one top-Proj lineup under the draw panel (rules, locks, excludes), in DK slot order; Another: the next best
  const ql = await pg.evaluate(async () => {
    const PANEL = ["levW", "minSal", "maxTeam", "stackN", "maxOwn", "lowN"], pv = PANEL.map(id => document.getElementById(id).value), sb = document.getElementById("stackBoth").checked, R0 = state.rules;
    PANEL.forEach(id => { document.getElementById(id).value = ""; }); document.getElementById("stackBoth").checked = false; state.rules = [];
    const L0 = state.lock, X0 = state.excl, wait = async () => { for (let t = 0; t < 200 && document.getElementById("quickRun").disabled; t++) await new Promise(r => setTimeout(r, 30)); };
    const live = rows.filter(r => usable(r) && proj(r) >= DKSim.MIN_PROJ).sort((a, b) => a.salary - b.salary);
    const lk = [live[Math.floor(live.length / 2)].id, live[Math.floor(live.length / 3)].id];
    state.lock = { [lk[0]]: true, [lk[1]]: true }; state.excl = {};
    document.getElementById("quickRun").click(); await wait();
    const a = QUICK[0], sum = L => L.ids.reduce((t, id) => t + proj(byId(id)), 0);
    const rowsShown = document.querySelectorAll("#quickBox table.quick tbody tr").length;
    const slotsOk = a.slots.every((id, i) => i < 3 ? DKSim.isG(byId(id)) : i < 6 ? DKSim.isF(byId(id)) : true);
    const sal = a.ids.reduce((t, id) => t + byId(id).salary, 0);
    document.getElementById("quickMore").click(); await wait();
    const b2 = QUICK[1], differs = b2 && b2.ids.some(id => a.ids.indexOf(id) < 0), notBetter = b2 && sum(b2) <= sum(a) + 1e-6;
    const drop = a.ids.find(id => lk.indexOf(id) < 0); state.excl = { [drop]: true };
    document.getElementById("quickRun").click(); await wait();
    const c = QUICK[0], gone = QUICK.length === 1 && c.ids.indexOf(drop) < 0 && lk.every(id => c.ids.indexOf(id) >= 0);
    // the panel's rules apply: never these two unlocked players of the last lineup together; a Min salary
    const pair = c.ids.filter(id => lk.indexOf(id) < 0).slice(0, 2);
    state.rules = [{ type: "never", ids: pair, label: "never" }]; document.getElementById("minSal").value = "49500";
    document.getElementById("quickRun").click(); await wait();
    const d = QUICK[0], ruled = !!d && !pair.every(id => d.ids.indexOf(id) >= 0) && d.ids.reduce((t, id) => t + byId(id).salary, 0) >= 49500 && /1 rule, min \$49,500/.test(document.getElementById("quickBox").textContent);
    // Quick sim: Lineups sim-night draws under the panel, each alone in the contest picked, best ROI first; tap a row for its lineup
    state.rules = []; document.getElementById("minSal").value = ""; document.getElementById("quickN").value = "20";
    const opts = document.getElementById("quickContest").options.length;
    document.getElementById("quickSim").click(); await wait();
    const q = QSIM, roiOrder = q && q.order.every((k, i) => i === 0 || q.v[q.order[i - 1]] >= q.v[k]);
    const simRows = document.querySelectorAll("#quickBox table.qsim tbody tr").length, allLocked = q && q.L.every(L => lk.every(id => L.ids.indexOf(id) >= 0) && L.ids.indexOf(drop) < 0);
    const second = document.querySelectorAll("#quickBox table.qsim tbody tr")[1]; if (second) second.click();
    const tapped = q && QSIM.sel === q.order[1] && /Lineup #2/.test(document.getElementById("quickBox").textContent) && document.querySelectorAll("#quickBox table.quick:not(.qsim) tbody tr").length === 8;
    const sim = { opts, simRows, roiOrder, allLocked, tapped, topA: q && q.tier[q.order[0]] === "A", distinct: q && new Set(q.L.map(L => L.ids.slice().sort().join())).size, contest: q && q.c.id };
    state.lock = L0; state.excl = X0; state.rules = R0; PANEL.forEach((id, i) => { document.getElementById(id).value = pv[i]; }); document.getElementById("stackBoth").checked = sb;
    QUICK = []; QSIM = null; renderQuick();
    return { ruled, sim, n: a.ids.length, locked: lk.every(id => a.ids.indexOf(id) >= 0), rowsShown, slotsOk, sal, differs, notBetter, gone, hidden: document.getElementById("quickMore").hidden };
  });
  check("Quick lineup: 8 players with both locks, legal slots and salary, shown in a table; Another differs and is no better; an exclude takes effect; nothing kept after",
        ql.n === 8 && ql.locked && ql.rowsShown === 8 && ql.slotsOk && ql.sal <= 50000 && ql.differs && ql.notBetter && ql.gone && ql.hidden, JSON.stringify(ql));
  check("Quick lineup follows the draw panel: a never rule and a Min salary hold, and the note lists them", ql.ruled, JSON.stringify(ql));
  check("Quick sim: 20 distinct lineups under the locks and excludes, simmed in a contest, best ROI first with the top in tier A; a tap shows that lineup's card",
        ql.sim.opts > 0 && ql.sim.simRows >= 10 && ql.sim.simRows === ql.sim.distinct && ql.sim.roiOrder && ql.sim.allLocked && ql.sim.topA && ql.sim.tapped, JSON.stringify(ql.sim));
  // the player list on a phone: scrolls sideways under a fixed L / X and name; Sal straight after the name
  await pg.setViewportSize({ width: 390, height: 844 });
  const mob = await pg.evaluate(async () => {
    renderPlayers(); const p = document.getElementById("players"), row = p.querySelector(".row");
    const at = sel => row.querySelector(sel).getBoundingClientRect().left;
    const who0 = at(".who"), lx0 = at(".lx"), third = [...row.children].sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left)[2].textContent;
    p.scrollLeft = 300; await new Promise(r => requestAnimationFrame(r));
    const r = { scrolls: p.scrollWidth > p.clientWidth + 100, page: document.documentElement.scrollWidth <= 390, nameW: row.querySelector(".who").getBoundingClientRect().width,
                whoMoved: Math.abs(at(".who") - who0), lxMoved: Math.abs(at(".lx") - lx0), third, moved: p.scrollLeft };
    p.scrollLeft = 0; return r;
  });
  await pg.setViewportSize({ width: 1100, height: 900 });
  check("phone: the player list scrolls sideways, L / X and the name stay put, the name 150px, Sal next, the page itself no wider",
        mob.scrolls && mob.page && mob.nameW >= 149 && mob.whoMoved <= 10 && mob.lxMoved <= 5 && /k$/.test(mob.third.trim()) && mob.moved > 0, JSON.stringify(mob));
  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("PASS " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(`${passes.length} passed, ${fails.length} failed`);
  process.exit(fails.length ? 1 : 0);
})();
