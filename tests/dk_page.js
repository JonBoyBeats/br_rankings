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
  await pg.route(/dk_cbb_writeups/, r => r.fulfill({ status: 404, body: "" }));      // the write-up test injects its own
  let gate = null;
  await pg.route(/gate\.json/, r => gate ? r.fulfill({ body: JSON.stringify(gate), contentType: "application/json" }) : r.fulfill({ status: 404, body: "" }));
  await pg.route(/own_watch\.json/, r => r.fulfill({ contentType: "application/json", body: JSON.stringify({ patterns: [
    { pattern: "coming off a big game", status: "confirmed", ratio: 1.4, player_nights: 40, nights: 6, same_direction: "5 of 6" },
    { pattern: "blue bloods", status: "emerging", ratio: 1.2, player_nights: 90, nights: 4, same_direction: "3 of 4" }] }) }));
  await pg.route(/field_fit\.json/, r => r.fulfill({ contentType: "application/json", body: JSON.stringify({ nights: ["a", "b"], bands: {
    Large: { contests: 3, dup: { real: 13.4, sim: 7.03 }, punt: { real: 7.32, sim: 21.29 } }, Small: { contests: 0 } } }) }));
  // the shadow lab's scoreboard (2026-11-24): one decided experiment, one running with a look-back, one Draw the 9 cell
  const labDoc = { registered: "2026-11-24", updated_at: "2026-12-06T12:00:00Z", experiments: [
    { id: "a", name: "STACK vs the plain game-group tags", planned_nights: 10, results: { arms: { all: { nights: 10, planned: 10, diff: 4.21, noise: 1.3, ahead: 8, behind: 2, top10_diff: 0.031, verdict: "pass", lookback: [] } } } },
    { id: "b", name: "Scan floors vs group rules", planned_nights: 10, results: { arms: { all: { nights: 3, planned: 10, diff: -1.5, noise: 2.2, ahead: 1, behind: 2, top10_diff: -0.01, verdict: "running", lookback: [] } } } },
    { id: "c", name: "Draw the 9 cells vs L0 U0", planned_nights: 10, results: { arms: { "L0.1 U1": { nights: 0, planned: 10, diff: null, noise: null, ahead: 0, behind: 0, top10_diff: null, verdict: "running",
      lookback: [{ date: "2026-11-20", diff: -2.28, t_n: 170, c_n: 535 }] } } } }] };
  await pg.route(/lab\.json/, r => r.fulfill({ contentType: "application/json", body: JSON.stringify(labDoc) }));
  await pg.goto("file://" + path.join(ROOT, "dk.html"));
  await pg.waitForSelector(".row");
  await pg.waitForFunction(() => /experiments/.test(document.getElementById("labSum").textContent), null, { timeout: 20000 });
  const lab = await pg.evaluate(() => ({ sum: $("labSum").textContent, rows: [...document.querySelectorAll("#labTable tr")].slice(1).map(tr => [...tr.cells].map(td => td.textContent.replace(/[\s\u00a0]+/g, " ").trim()).join(" | ")),
    inBank: !!document.getElementById("labBox").closest("#stepBank"), none: (renderLab(null), $("labSum").textContent) }));
  await pg.evaluate(d => renderLab(d), labDoc);
  check("shadow lab scoreboard: one row per experiment (a cell per Draw the 9 cell under its heading), slates of planned, the paired difference with its noise, ahead / behind, top-10% difference, verdict, the look-back marked; in the Bank step",
        lab.inBank && /3 experiments, 3 scoreboard rows, 1 decided · graded 2026-12-06/.test(lab.sum) && lab.rows.length === 4 &&
        lab.rows[0] === "a. STACK vs the plain game-group tags | 10/10 | +4.2 ±1.3 | 8 / 2 | +3.1 | pass" && lab.rows[1] === "b. Scan floors vs group rules | 3/10 | -1.5 ±2.2 | 1 / 2 | -1.0 | running" &&
        lab.rows[2] === "c. Draw the 9 cells vs L0 U0" && lab.rows[3] === "L0.1 U1look-back 11-20 -2.3 (170 vs 535) | 0/10 | – | – | – | running" && /no scoreboard yet/.test(lab.none), JSON.stringify(lab));
  // Auto top-up (on by default) breaks caps on purpose; the fill tests below check the fill's own caps, so it is off
  // for them and on only where its own tests (and Finish for me) run
  const tuDefaultOn = await pg.evaluate(() => { const x = document.getElementById("autoTopUp"), on = x.defaultChecked && x.checked; x.checked = false; x.dispatchEvent(new Event("change")); return on; });
  const ff = await pg.evaluate(() => ({ hidden: $("fieldFit").hidden, text: $("fieldFit").textContent }));
  check("field fit line: real vs simulated dupes and punts by band, bands with no contests left out",
        !ff.hidden && /Large \(3 contests\) dupes 13\.4% vs 7\.0%, sub-\$3\.5k punts 7\.3% vs 21\.3%/.test(ff.text) && !/Small/.test(ff.text), JSON.stringify(ff));
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
    document.querySelector(`#players .row[data-id="${r.id}"] .excl`).click();      // X is the one pool toggle (2026-11-23)
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
    document.querySelector(`#players .row[data-id="${r.id}"] .excl`).click(); const back = !r.deepOut && usable(r);
    state.deepIn = {}; r.min_avg = was.min_avg; applyOuts(); renderPlayers();
    return { def, news, back };
  });
  check("no punts without news: under 15 projected minutes out by default (page and sim); a teammate out raising him past his average lets him in; Use brings him back",
        pu.def.punt && pu.def.out && !pu.def.usable && pu.def.sim === false && (pu.news.min > pu.news.avg ? !pu.news.punt : true) && pu.back, JSON.stringify(pu));
  // X is the one pool toggle (2026-11-23): on when he's out of the pool for any reason (a Questionable player out by
  // default too); one tap in, one tap out; the row has no separate use / drop button
  const xt = await pg.evaluate(() => {
    const r = rows.find(x => x.status !== "Out" && x._status0 === "Questionable") || rows.find(x => x.status !== "Out");
    state.excl = {}; state.deepIn = {}; const keep = state.deepIn;
    const deep = deepIds(); deep[r.id] = 1; const was = deepIds; deepIds = function () { return deep; };
    applyOuts(); view.panel = null; renderTiles(); renderPlayers();
    const x = () => document.querySelector(`#players .row[data-id="${r.id}"] .excl`);
    const x2 = (y) => document.querySelector(`#players .row[data-id="${y.id}"] .excl`);
    const o = { def: r.deepOut && x().getAttribute("aria-pressed") === "true", noUse: !document.querySelector(`#players .row[data-id="${r.id}"] .deepin`) };
    x().click(); o.in = usable(r) && x().getAttribute("aria-pressed") === "false";
    x().click(); o.out = !usable(r) && x().getAttribute("aria-pressed") === "true" && !state.excl[r.id];
    x().click(); x().click(); o.mine = !usable(r) && !!state.excl[r.id] === false;
    deepIds = was; state.deepIn = {}; state.excl = {}; applyOuts(); renderPlayers();
    // a flip saved under an older default: a player in by default with a stale state.deepIn is out; X brings him in
    const q = rows.find(y => y.status !== "Out" && !y.deepOut && usable(y) && y.id !== r.id);
    state.deepIn[q.id] = 1; applyOuts(); renderPlayers();
    o.stale = usable(q) && !state.deepIn[q.id] && x2(q).getAttribute("aria-pressed") === "false";   // the stale flip is dropped: he stays in
    state.deepIn = {}; applyOuts(); renderPlayers();
    return o;
  });
  check("X is the one pool toggle: on for a player out by default (a Q player too), one tap in, one tap back out; no use / drop button",
        Object.values(xt).every(Boolean), JSON.stringify(xt));
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
  // size bands (2026-11-23 lock): a contest is simmed against its band's field (300+ large, 30-299 medium, under 30 small),
  // else the one field; a Mark out rebuilds each band's field too
  const fband = await pg.evaluate(() => {
    const F0 = fieldOf(), had = F0.bands, med = F0.field.slice(0, 300), sm = F0.field.slice(300, 500);
    F0.bands = { medium: { field: med }, small: { field: sm } };
    const out = { large: fieldFor({ size: 500 }) === F0.field, medium: fieldFor({ size: 100 }) === med, small: fieldFor({ size: 10 }) === sm,
                  edge: fieldFor({ size: 300 }) === F0.field && fieldFor({ size: 30 }) === med && fieldFor({ size: 29 }) === sm };
    const q = rows.filter(r => r.status !== "Out").sort((a, b) => (F0.own[b.id] || 0) - (F0.own[a.id] || 0))[0];
    state.outs[q.id] = 1; applyOuts();
    const m = fieldFor({ size: 100 }), s = fieldFor({ size: 10 });
    out.outGone = m !== med && s !== sm && m.every(L => L.indexOf(q.id) < 0) && s.every(L => L.indexOf(q.id) < 0) && m.length > 250;
    delete state.outs[q.id]; applyOuts(); out.restored = fieldFor({ size: 100 }) === med;
    if (had) F0.bands = had; else delete F0.bands;
    out.none = fieldFor({ size: 10 }) === fieldOf().field;
    return out;
  });
  check("size bands: each contest simmed against its band's field (300+ / 30-299 / under 30), the one field without bands; a Mark out rebuilds the bands",
        Object.values(fband).every(Boolean), JSON.stringify(fband));
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
    const heads = [...document.querySelectorAll("#players .head span[data-sort]")].map(x => x.firstChild.textContent.replace(/ [↓↑]$/, ""));     // the label, not Bank's all / base toggle
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
    check("tag line shows the next draw's idea, " + name, (await pg.textContent("#tagNow")) === "Banking as: " + tag, await pg.textContent("#tagNow"));
    const { L, msg } = await draw(20);
    audit("Draw & bank, " + name, L, rulesOf(v));
    if (L.length < 15) check("Draw & bank, " + name + ": drew 15+ new", false, msg);
    check("Draw & bank, " + name + ": tagged with its idea", new RegExp('tagged "' + tag.replace(/[+]/g, "\\+") + '"').test(msg), msg);
  }
  // the idea name (2026-11-23): typed before drawing, the draw banks under it (grouped), the rules' tag kept underneath;
  // the tag line says what it banks as; Clear players empties template 5's set
  await pg.fill("#ideaName", "My idea");
  const tagShown = await pg.textContent("#tagNow");
  const { L: Lidea, msg: mIdea } = await draw(5);
  const idg = await pg.evaluate(() => { const tags = Object.keys(BANK.groups || {}).filter(t => BANK.groups[t] === "My idea");
    const o = Array.from($("rtList").options).slice(0, 3); o.forEach(x => { x.selected = true; }); rtChips(); const before = $("rtList").selectedOptions.length;
    $("rtClear").click(); return { tags: tags.length, kept: state.idea, before, after: $("rtList").selectedOptions.length, chips: $("rtChips").children.length }; });
  check("idea name: the draw banks under it (grouped, its rules' tag underneath), the tag line and status say so, kept for the slate; Clear players empties the set",
        tagShown === "Banking as: My idea" && Lidea.length > 0 && idg.tags >= 1 && /as \u201cMy idea\u201d/.test(mIdea) && idg.kept === "My idea" && idg.before === 3 && idg.after === 0 && idg.chips === 0,
        JSON.stringify([tagShown, mIdea.slice(0, 80), idg]));
  await pg.fill("#ideaName", ""); await pg.evaluate(() => { state.idea = ""; save(); });
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
  const satM = /Banked (\d+) new · (\d+) repeats · (\d+) near-copies \(7 of 8 shared with a banked lineup\)/.exec(m0);
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
        /^Draw the 4: \d+ new, \d+ repeats as .+/.test(sw.msg) && /4 batches banked under/.test(sw.msg), JSON.stringify(sw));
  // template-5 spread (2026-11-21): "3 of these 6" with each of the 6 in at least 10% of the draw, topped up like Min%;
  // off leaves no floors; Draw the 9 applies it per batch and records it in each tag's rules; Quick sim's draw honours it
  const spr = await pg.evaluate(async () => {
    const R0 = state.rules, F0 = JSON.stringify(state.floor || {}), keepN = $("bankN").value, out = {};
    const pool = rows.filter(r => usable(r) && proj(r) >= DKSim.MIN_PROJ).sort((a, b) => proj(b) - proj(a));
    const six = pool.slice(0, 3).concat(pool.slice(25, 28)).map(r => r.id);
    const rule = { type: "min", ids: six, n: 3, label: "at least 3 of " + six.map(id => shortName(byId(id).name)).join(", ") };
    state.rules = [rule]; renderRules();
    const shares = L => six.map(id => L.filter(x => x.ids.indexOf(id) >= 0).length / L.length);
    out.field = !!document.querySelector("#ruleList .rule .spreadIn") && document.querySelector("#ruleList .rule .spreadIn").value === "10";
    rule.spread = 0; let r0 = await drawBank(ctx(), drawRules(), 50); out.off = shares(r0.lineups).map(x => +x.toFixed(2)); out.offTxt = r0.spreadTxt || "";
    delete rule.spread; const dr = drawRules(); out.map = dr.spread;
    let r1 = await drawBank(ctx(), dr, 50); out.on = shares(r1.lineups).map(x => +x.toFixed(2)); out.n1 = r1.lineups.length; out.txt = r1.spreadTxt || "";
    out.all3 = r1.lineups.every(L => six.filter(id => L.ids.indexOf(id) >= 0).length >= 3);
    // a rule's field changes its spread; off: no floors, none written to the Min% boxes
    const inp = document.querySelector("#ruleList .rule .spreadIn"); inp.value = "20"; inp.dispatchEvent(new Event("change", { bubbles: true }));
    out.edited = rule.spread === 20 && Object.values(drawRules().spread).every(v => v === 20);
    rule.spread = 10; rule.off = true; out.offMap = Object.keys(drawRules().spread).length; out.floorSame = JSON.stringify(state.floor || {}) === F0; delete rule.off;
    // Draw the 9 (2 x 1 here): each batch's own lineups hold the floor; each tag's rules record the spread
    $("bankN").value = "20"; $("sweepLev").value = "0, 0.1"; $("sweepLow").value = "0"; $("levW").value = "0"; $("lowN").value = "0";
    const idea = tagNow(); await drawSweep();
    out.batches = ["L0 U0", "L0.1 U0"].map(x => { const t = idea + " " + x, L = BANK.lineups.filter((_, i) => BANK.tags[i][0] === t);
      return { n: L.length, min: L.length ? Math.min.apply(null, shares(L)) : 0, rec: !!(BANK.tagRules[t] && BANK.tagRules[t].spread && BANK.tagRules[t].spread[six[5]] === 10) }; });
    out.msg9 = $("buildStatus").textContent;
    $("bankN").value = keepN; $("sweepLev").value = "0, 0.1, 0.2"; $("sweepLow").value = "0, 1, 2"; $("sweepLev").dispatchEvent(new Event("change"));
    // Quick sim: its 10x draw honours the floors (5 kept: 50 drawn), and its note names the spread
    $("quickN").value = "5"; await quickSim(); const q = QSIM;
    out.quick = q ? { drawn: q.drawn, note: /spread 6 players \u226510%/.test($("quickBox").textContent), txt: q.spreadTxt } : null;
    $("quickN").value = "20"; QSIM = null; renderQuick();
    state.rules = R0; renderRules();
    return out;
  });
  check("spread: a 3-of-6 rule with each of the 6 in at least 10% of a 50-lineup draw (topped up), every lineup still 3 of 6; the rule's field defaults to 10 and edits its spread; a status line",
        spr.field && spr.n1 >= 45 && spr.on.every(x => x >= 0.1) && spr.all3 && spr.edited && /^spread: 6 players \u226510%, /.test(spr.txt) && spr.offTxt === "", JSON.stringify(spr));
  check("spread: the rule off leaves no floors (nothing written to Min%)", spr.offMap === 0 && spr.floorSame, JSON.stringify([spr.offMap, spr.floorSame]));
  check("spread: Draw the 9 applies it per batch (each batch's six at 10%+) and records it in each tag's rules; the status names it",
        spr.batches.every(b => b.n >= 10 && b.min >= 0.1 && b.rec) && /Spread, each batch: 6 players \u226510%/.test(spr.msg9), JSON.stringify([spr.batches, spr.msg9]));
  check("spread: Quick sim's 10x draw honours it and its note names it", !!spr.quick && spr.quick.drawn >= 45 && spr.quick.note && /^spread: 6 players/.test(spr.quick.txt), JSON.stringify(spr.quick));
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
  // 2026-11-23: the projection keeps a Q player whole (factor 1), the field fades him (field_factor); the note says so
  gate = { nights: 9, bands: [{ lo: 6000, hi: 99999, open: true, w: 0.6 }, { lo: 0, hi: 5999, open: false, w: 1 }],
           questionable: { factor: 1.0, field_factor: 0.333, n: 10, actual: 30, projected: 150 } };
  await pg.click("#reload");
  await pg.waitForFunction(() => /Questionable players keep their full projection.*fades them at x0\.33/.test(document.getElementById("statusInfo").textContent));
  const qw = await pg.evaluate(q => proj(rows.find(r => r.id === q)), qid);
  check("questionable kept whole: his full projection, the Q tag only; the field's fade noted", Math.abs(qw - qBase) < 1e-9, JSON.stringify([qw, qBase]));

  // --- team tiles and rules -----------------------------------------------------------------------------
  const TEAMS = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_teams.json"))).slates[String(slate.draft_group_id)];
  gate = null;
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate: closed/.test(document.getElementById("statusInfo").textContent));
  const openTeam = async team => {
    if (!(await pg.$(`#teamPanel .tile[data-team="${team}"]`))) await pg.click(`#teamBar button[data-team="${team}"]`);
    await pg.waitForSelector(`#teamPanel .tile[data-team="${team}"]`);
  };
  // the game view (2026-11-23) keeps only Min 1 / 2 / 3 and Stack on the tile; the other shortcuts' rules (exclude,
  // pivot, bring-back, platoon, quadrant) stay in tileRules and are tested through it
  const tileAct = (team, act, k) => pg.evaluate(([tm, a, kk]) => addRules(tileRules(a, teamsOf().teams.find(t => t.team === tm), kk)), [team, act, k]);
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
    // the write-up (2026-11-23: replaced the rotation table and its tags): prose with bold, its table, Use / Drop chips (the X action)
    const keepWu = wuDoc;
    wuDoc = { slates: { [String(slate.draft_group_id)]: { [t.team]: { games: 5, paras: [["Bottom line.", "Core: " + mates[0].name + ". Fade: **" + mates[1].name + "**."], ["", "A player line."]],
      table: [{ id: mates[0].id, name: mates[0].name, starts: 5, gp: 5, season_mpg: 31.6, last3: 32, proj_min: 32.9, dk_pg: 30.6, dk_pm: 0.97, hits: 3, ceil: 1, floor: 0, obpr: 3.59, obpr_rank: 1, form: "in line", pool_out: false },
              { id: mates[1].id, name: mates[1].name, starts: 4, gp: 5, season_mpg: 15.6, last3: 15.3, proj_min: 14.4, dk_pg: 14.4, dk_pm: 0.92, hits: 0, ceil: 0, floor: 2, obpr: 1.85, obpr_rank: 5, form: null, pool_out: true }] } } } };
    renderTeamPanel();
    const el = () => document.querySelector('#teamPanel details.card[data-card="' + t.team + '"]');
    const a = el().textContent, html = el().innerHTML, rot = el().querySelectorAll("table.rot").length;
    const wrows = [...el().querySelectorAll(".wu .wt tr[data-id]")].map(tr => tr.dataset.id);
    const poolTag = !!el().querySelector('.wu .wt tr[data-id="' + mates[1].id + '"] .tag');
    const chip = () => el().querySelector('.wuchip[data-id="' + mates[1].id + '"]');
    const c0 = chip().textContent; chip().click();
    const dropped = !!state.excl[mates[1].id], c1 = chip().textContent; chip().click();
    const used = !state.excl[mates[1].id];
    state.outs[sit.id] = 1; applyOuts(); renderTeamPanel();
    const b = el().textContent, firstOut = el().querySelector("summary").nextElementSibling, tbl = !!el().querySelector("table:not(.rot)");
    delete state.outs[sit.id]; t.card = keep; wuDoc = null; renderTeamPanel();
    const none = el().textContent; wuDoc = keepWu; applyOuts(); renderTeamPanel();
    return { a, html, rot, wrows, poolTag, c0, c1, dropped, used, none, first: firstOut && firstOut.textContent, tbl };
  });
  check("team card: the write-up replaces the rotation table: its prose (bold kept), its numbers table, a pool tag, no rotation table or tag lines; an Out player's with / without table first",
        /Team card · 5 games/.test(card.a) && /<b>Bottom line\.<\/b>/.test(card.html) && /Fade: <b>/.test(card.html) && card.rot === 0 && card.wrows.length === 2 && card.poolTag &&
        !/swingy/.test(card.a) && card.tbl && /is out tonight; when he sat before \(1 of 5 games\)/.test(card.first || "") && /No write-up for this team yet/.test(card.none), JSON.stringify(card));
  // the default pool follows the write-up's pool rule (2026-11-23): out / in per player, the deep bench in with a 5x, one tap flips it
  const dpool = await pg.evaluate(() => {
    const t = teamsOf().teams[0], mates = rows.filter(r => r.team === t.team && r.status !== "Out" && r.min > 0).sort((a, b) => b.min - a.min);
    const hi = mates[0], lo = mates[mates.length - 1], dId = ((t.card && t.card.deep) || [])[0], keepWu = wuDoc, keepDeep = Object.assign({}, state.deepIn);
    state.deepIn = {};
    const pool = { [hi.id]: { pool: "out", why: "no 5x game in his last 5 and projected under 20 minutes", deep: false },
                   [lo.id]: { pool: "in", why: "the pool rule doesn't fire", deep: false } };
    if (dId) pool[dId] = { pool: "in", why: "deep bench, but a 5x game in his last 5", deep: true };
    wuDoc = { slates: { [String(slate.draft_group_id)]: { [t.team]: { paras: [], table: [{ id: hi.id, name: hi.name, starts: 5, gp: 5, hits: 0, ceil: 0, floor: 0, pool_out: true }], pool } } } };
    applyOuts(); renderTeamPanel();
    const out = { hiOut: hi.deepOut, loIn: !lo.deepOut, deepIn: dId ? !byId(dId).deepOut : true, usable: !usable(hi) && usable(lo) };
    const chip = () => document.querySelector('.wuchip[data-id="' + hi.id + '"]');
    out.chip0 = chip() && chip().textContent; chip().click();
    out.flipped = !byId(hi.id).deepOut && !!state.deepIn[hi.id] && /^Drop /.test(chip().textContent);
    // the news exception: a teammate Out and his projection above his season average lets a pool-out player in
    state.deepIn = {}; const avg = hi.min_avg; hi.min_avg = 0; state.outs[lo.id] = 1; applyOuts();
    out.news = !byId(hi.id).deepOut; delete state.outs[lo.id]; hi.min_avg = avg;
    // no write-ups file: the old rule (punts and the deep bench out)
    wuDoc = null; applyOuts(); out.fallback = byId(lo.id).deepOut === ((lo.min || 0) < PUNT_MIN || !!deepIds()[lo.id]);
    wuDoc = keepWu; state.deepIn = keepDeep; applyOuts(); renderTeamPanel();
    return out;
  });
  check("default pool: the write-up's verdicts (out / in, the deep bench in with a 5x), the chip shows the real state and one tap flips it, the news exception, the old rule without the file",
        dpool.hiOut && dpool.loIn && dpool.deepIn && dpool.usable && /^Use /.test(dpool.chip0 || "") && dpool.flipped && dpool.news && dpool.fallback, JSON.stringify(dpool));
  check("team card: the write-up's Drop / Use chips are the X action (state.excl) and stay reachable",
        /^Drop /.test(card.c0) && card.dropped && /^Use /.test(card.c1) && card.used, JSON.stringify([card.c0, card.c1, card.dropped, card.used]));
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
        an.chip === null && /writeup: Game writeup text/.test(an.first || "") && an.notes && an.noNews, JSON.stringify(an));    // 2026-11-23: no chip on the tile (Min / Stack only)
  check("game view: the clicked team's tile only (a toggle for the other)", JSON.stringify(panel) === JSON.stringify([TEAMS.teams[0].team]), JSON.stringify(panel));
  const gv = await pg.evaluate(() => {
    const ids = [...document.querySelectorAll("#teamPanel .plist .row")].map(r => r.dataset.id), teams = new Set(ids.map(id => byId(id).team));
    const t = teamsOf().teams.find(x => x.team === view.panel), grp = {};
    const ckm = checksMap();     // 2026-11-24: boxes met, then projection (was salary)
    ids.map(id => byId(id)).filter(r => r.status !== "Out").forEach(r => { (grp[r.team] = grp[r.team] || []).push(ckm[r.id].hit * 1000 + proj(r)); });
    const order = ids.map(id => byId(id).team).filter((x, i, a) => i === 0 || a[i - 1] !== x);
    return { teams: [...teams].sort(), want: [t.team, oppOf(t.team)].sort(), sorted: Object.values(grp).every(v => v.every((x, i) => i === 0 || v[i - 1] >= x)), split: order.length === 2,
             tabs: [...document.querySelectorAll("#teamPanel .ptab")].map(b => b.dataset.team).sort(), lists: document.querySelectorAll("#teamPanel .plist").length,
             pressed: [...document.querySelectorAll("#teamBar button[aria-pressed=true]")].map(b => b.dataset.team).sort(), head: !!document.querySelector("#teamPanel .gamehead"),
             heads: [...document.querySelectorAll("#teamPanel .plist .head span[data-sort]")].length,
             blank: !scanNow() && [...document.querySelectorAll("#teamPanel .scanblk")].length === 1 && [...document.querySelectorAll("#teamPanel .scanblk")].every(b => /–/.test(b.textContent) && b.querySelector("a.scanlink")) };
  });
  check("game view: the header, a toggle for the two teams and one team's card with its Scan block (– and a Scan the slate link before a scan); each team's players in its own list, by boxes met then projection by default; both chips pressed",
        gv.head && gv.blank && gv.lists === 1 && gv.split && JSON.stringify(gv.tabs) === JSON.stringify(gv.want) && JSON.stringify(gv.teams) === JSON.stringify(gv.want) && gv.sorted && gv.heads >= 13 && JSON.stringify(gv.pressed) === JSON.stringify(gv.want), JSON.stringify(gv));
  const gs2 = await pg.evaluate(() => {
    const t = view.panel, o = oppOf(t);
    document.querySelector('#teamBar button[data-team="' + o + '"]').click();
    const a = [...document.querySelectorAll("#teamPanel .tile")].map(x => x.dataset.team);
    document.querySelector('#teamPanel .plist .head [data-sort="proj"]').click();
    const grp = {}; [...document.querySelectorAll("#teamPanel .plist .row")].map(r => byId(r.dataset.id)).filter(r => r.status !== "Out").forEach(r => { (grp[r.team] = grp[r.team] || []).push(proj(r)); });
    const p = Object.values(grp), mainSort = view.sort;
    view.psort = null; view.pdir = null;
    document.querySelector('#teamBar button[data-team="' + t + '"]').click();
    return { a, want: [o], sortedProj: p.length === 2 && p.every(v => v.every((x, i) => i === 0 || v[i - 1] >= x)), mainKept: mainSort === "value", back: view.panel === t };
  });
  check("game view: the other team's chip opens the game on that team; a header click sorts each team's list on its own (the main list's sort untouched)",
        JSON.stringify(gs2.a) === JSON.stringify(gs2.want) && gs2.sortedProj && gs2.mainKept && gs2.back, JSON.stringify(gs2));
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
  for (const act of ["min1", "min2", "min3", "stack", "excl"]) {
    await clearRules();
    await openTeam(tile.team); if (act === "excl") await tileAct(tile.team, act); else await pg.click(`${tsel} button[data-act="${act}"]`);
    const R = await rulesNow();
    check(`tile button ${act} writes its rule${R.length > 1 ? "s" : ""}`, R.length === (act === "stack" ? 2 : 1), JSON.stringify(R.map(r => r.label)));
    await drawAudit("tile " + act);
  }
  check("rules stay in the box after a draw", (await rulesNow()).length === 1);
  check("rules list shows the pass counts after a draw", (await pg.$$eval(".rule .pc", x => x.length)) === 1);
  // the #1 player's shortcuts, and editing one after
  await clearRules();
  await tileAct(tile.team, "pivot"); await tileAct(tile.team, "bring");
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
  check("platoon: off the game view's tile (2026-11-23: Min 1 / 2 / 3 and Stack only)", await pg.$$eval(pb, b => b.length) === 0);
  await tileAct(plat.team, "platoon", 0);
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
    check("tile: Min 1 / 2 / 3 and Stack only (no platoon line)", !/Platoon/.test(await pg.textContent(`.tile[data-team="${noPlat.team}"]`)) &&
      JSON.stringify(await pg.$$eval(`.tile[data-team="${noPlat.team}"] button`, b => b.map(x => x.dataset.act))) === JSON.stringify(["min1", "min2", "min3", "stack"]));
  }
  const heavy = TEAMS.teams.find(t => t.heavy_fav), notHeavy = TEAMS.teams.find(t => !t.heavy_fav);
  // 2026-11-23: the tile's BENCH flag went with the other tile flags (the write-up replaced them)
  await openTeam(heavy.team);
  check("platoon: no BENCH flag on the tile now (the tile flags are gone)", !/garbage time/.test(await pg.textContent(`.tile[data-team="${heavy.team}"]`)));
  await openTeam(notHeavy.team);
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
  await tileAct(t2.team, "excl");
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
  // 2026-11-23: the tiles' headings and flags are gone (verdict, Quality / Leverage, reason, BEST BET / FRAGILE / BENCH); the actions stay
  check("tiles: no verdict heading, scores, reason or flags; the slate line without the quadrant note; the actions kept",
        (await pg.$$eval("#teamPanel .tile .scores, #teamPanel .tile .verdict, #teamPanel .tile .why, #teamPanel .tile .flags", x => x.length)) === 0 &&
        !/Quality and Leverage/.test(await pg.textContent("#slateLine")) && (await pg.$$eval("#teamPanel .tile button[data-act]", x => x.length)) >= 4);
  for (const q of ["FOCUS", "CHALK", "LEVERAGE"]) {
    const t = TEAMS.teams.find(x => x.verdict === q);
    if (!t) continue;
    await clearRules();
    await tileAct(t.team, "quad");
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
    const taSum = cells.reduce((t, c) => t + (+c[5] || 0), 0), T = topTenth();
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
  check("cut step: one idea table (Idea, Banked, Kept, Share, Top tenth, Sim ROI, Top 10%, Top 1%, Cash, Avg own, Cores), best Sim ROI first and sortable; the top tenth by idea sums to at least the top tenth; the bank line and the entries summary",
        JSON.stringify(it.heads) === JSON.stringify(["Idea", "Banked", "Shared", "Kept", "Share", "Top tenth", "Sim ROI", "Top 10%", "Top 1%", "Cash", "Avg own", "Cores"]) && it.taSum >= it.T && it.keptOk && it.roiOrder && it.keptSorted &&
        /^Whole bank [\d,]+ · \d+ pts (under|over) the field · own \d+% vs \d+% · field's \d+(st|nd|rd|th) pct.* \| Kept [\d,]+ · \d+ pts (under|over) the field · own \d+% vs \d+%/.test(it.line) &&
        it.far === (/far below the field/.test(it.line) && /far below the field/.test(it.check)) && it.far === (it.kn ? (it.kpct != null && it.kpct < 15) || it.fp - it.kp >= 5 : (it.pct != null && it.pct < 15) || it.fp - it.bp >= 5) && /^Top tenth by sim value: \d+ lineup/.test(it.tier) && /^8 entries · 4 contests$/.test(it.sum) && it.info, JSON.stringify(it));
  const ta = await pg.evaluate(() => { const T = topTenth(), v = CUT.board.values, el = document.getElementById("tierA");
    const best = T.ks.map(k => v[k]), rest = v.filter((x, k) => T.ks.indexOf(k) < 0);
    return { n: T.n, ideas: T.ideas, want: Math.min(CUT.keep.length, Math.max(10, Math.ceil(0.1 * CUT.keep.length))), nv: v.length, keep: CUT.keep.length,
             ordered: Math.min(...best) >= Math.max(...rest.concat([-1e9])), txt: el ? el.textContent : "" }; });
  check("the top tenth by sim value after the cut (2026-11-23: the tiers de-emphasized): max(10, 10%) of the kept, the best by value, its ideas and top idea's share shown, no red flag; each kept lineup's value saved",
        ta.n === ta.want && ta.ordered && ta.ideas >= 1 && ta.nv === ta.keep && new RegExp("^Top tenth by sim value: " + ta.n + " lineup").test(ta.txt) && !/Red flag/.test(ta.txt), JSON.stringify(ta));
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
  check("portfolios: each lineup in one contest only, the flagship first (its profile named)", new Set(pfAll).size === pfAll.length &&
        /the flagships first \(together\), then the main contests, then the rest by stake: CBB \$6K Pull Up Jumper \[\$2K to 1st\] \[Flagship \(top-1% coverage\)\]: 1 of 1, top 1% \d+\.\d%, P\(1st\) \d+\.\d% \(at 2 \/ 3 \/ 4: .+; the flagships together: one of them in its top 1% on \d+\.\d% of nights/.test(pmsg), pmsg);
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
  // 2026-11-21: each kept lineup's tier and cut value with the board's sigma, and the operator's state at save
  const est = bs.cut_state && bs.cut_state.est, estN = bs.cut_state && bs.cut_state.estNights, opSt = bs.operator || {};
  check("Save build: each kept lineup's tier (aligned with final) and cut value per contest with its nights; the board's sigma; the operator's state (proj, locks, excludes, Min% / Max%, rules, spread, lock mode) and the gate",
        bs.idea_board && typeof bs.idea_board.tiers === "string" && bs.idea_board.tiers.length === bs.final.length && /^[ABC]+$/.test(bs.idea_board.tiers) && bs.idea_board.tierA && bs.idea_board.tierA.sigma != null &&
        Array.isArray(est) && est.length === bs.final.length && est.every(e => Array.isArray(e) && e.length === bs.cut_state.contests.length) && estN.length === est.length && estN.every(x => x > 0) &&
        ["proj", "lock", "excl", "floor", "cap", "deep_in", "rules", "spread", "lock_fill"].every(k => k in opSt) && "outs" in bs && "ins" in bs && "gate" in bs,
        JSON.stringify({ tiers: bs.idea_board && bs.idea_board.tiers && bs.idea_board.tiers.length, final: bs.final.length, est: est && est.length, op: Object.keys(opSt) }));
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
  // Auto top-up off (as set at load): the seats stay open with the stranded-seat line
  await pg.fill("#maxNight", "15");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed|^Filled/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const st0 = await pg.evaluate(() => { const open = nbContests().reduce((t, x) => t + Math.max(0, x.n - (PF[String(x.c.id)] || []).length), 0), b = document.querySelector("#strandBox .strandAdd");
    return { open, shown: !$("strandBox").hidden, text: $("strandBox").textContent, btn: !!b, cid: b && b.dataset.cid, n: b ? (PF[b.dataset.cid] || []).length : null }; });
  if (st0.btn) await pg.click("#strandBox .strandAdd");
  const st1 = await pg.evaluate(c => ({ n: c ? (PF[c] || []).length : null }), st0.cid);
  check("stranded seats: a fill left short names the cap that blocked (Night cap blocked: players at 15%) and offers a one-tap add of the lineup that breaks the caps least; nothing added by itself",
        st0.open > 0 && st0.shown && /Open seats: .*\d+ open\. .*Night cap blocked: .+ at 15%/.test(st0.text) && st0.btn && st1.n === st0.n + 1, JSON.stringify([st0, st1]));
  check("auto top-up off: the seats stay open (no top-up note), the setting kept and shown in the settings line",
        st0.open > 0 && !/auto top-up/.test(await pg.textContent("#cutStatus")) && (await pg.evaluate(() => localStorage.getItem("dkcbb:autoTopUp"))) === "false" &&
        /fill short off$/.test(await pg.textContent("#fillSetSum")));
  // Auto top-up on (the default, caps_backtest_2026-11-24 (e)): the same tight night cap, every seat filled with the
  // lineup that breaks the caps least, one at a time, and the note names each over-cap add
  await pg.check("#autoTopUp");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed|^Filled/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const tu = await pg.evaluate(() => {
    const st = document.getElementById("cutStatus").textContent, open = nbContests().reduce((t, x) => t + Math.max(0, x.n - (PF[String(x.c.id)] || []).length), 0);
    const named = [...st.matchAll(/(?:breaks |, )(?!breaks )([^,;.]+?) \+(\d+) (night|contest)/g)].map(m => [m[1], +m[2], m[3]]), used = nightUsed(null), nl = nightLimit();
    const overNight = named.filter(x => x[2] === "night").every(x => Object.keys(used).some(id => shortName(byId(id).name) === x[0] && used[id] > nl));
    const seats = [...st.matchAll(/ (\d+) seats?(?=, | \(|,|;|\.)/g)].reduce((t, m) => t + +m[1], 0), unique = Object.keys(PF).every(k => new Set(PF[k]).size === PF[k].length);
    return { open, note: (st.match(/auto top-up: [^]*?\.(?= |$)/) || [""])[0], named: named.length, overNight, seats, unique, strandHidden: $("strandBox").hidden };
  });
  check("auto top-up: on by default; a fill left short at a 15% night cap fills every seat with the lineup that breaks the caps least, and the note lists each over-cap add (\"auto top-up: <contest> N seats, breaks <player> +n night\")",
        tuDefaultOn && tu.open === 0 && /^auto top-up: .+ \d+ seats?, breaks .+ \+\d+ (night|contest)/.test(tu.note) && tu.named > 0 && tu.overNight && tu.seats > 0 && tu.unique && tu.strandHidden, JSON.stringify(tu));
  await pg.uncheck("#autoTopUp");
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
    return { has: !!u, ok, t: t.slice(0, 200), shown: !u || (["p", "st", "pr"].some(k => u[k].length) ? /^Under-exposed against the top tenth by sim value/.test(t) : t === "") }; });
  check("fill: the Under-exposed list (players, team stacks, pairs held 15+ points under their share of the top tenth by sim value)", und.has && und.ok && und.shown, JSON.stringify(und));
  await pg.fill("#maxExpo", "60"); await pg.fill("#maxNight", "40");
  await pg.fill("#maxNight", "60");
  // contest profiles (2026-11-24): each contest recognised by name and size, overridable per slate, filled for its job
  const pr0 = await pg.evaluate(() => {
    const by = id => slate.contests.find(c => String(c.id) === id), late = (size, name) => profileAuto({ name: name || "CBB Late Add", size });
    const kotb = slate.contests.find(c => /King of the Bracket Qualifier/.test(c.name) && c.size >= 10);
    return { puj: profileOf(by("197791872")), and1: profileOf(by("197791874")), qj: profileOf(by("197791875")), dime: profileOf(by("197873654")),
             q: profileOf(kotb), ticket: !!kotb.ticket && JSON.stringify(kotb.payouts) === JSON.stringify([[1, 1, kotb.prizes]]),
             late: [late(50), late(300), late(1000)], du: profileOf(slate.contests.find(c => c.name === "CBB $5 Double Up" && c.size === 46)) };
  });
  check("profiles: recognised by name (Pull Up Jumper flagship, And-One and Quarter Jukebox the main block, Dime Time the lab, qualifiers / satellites max ROI on a ticket table) and a late add by size (<100 qualifier, 100-800 flagship, 800+ main)",
        pr0.puj === "flagship" && pr0.and1 === "main" && pr0.qj === "main" && pr0.dime === "lab" && pr0.q === "qualifier" && pr0.ticket &&
        JSON.stringify(pr0.late) === JSON.stringify(["qualifier", "flagship", "main"]) && pr0.du === "qualifier", JSON.stringify(pr0));
  const pr1 = await pg.evaluate(() => {
    renderProfiles();
    const rowsP = [...document.querySelectorAll("#profList .prow")].map(r => r.dataset.cid), sel = document.querySelector('#profList select[data-cid="197791874"]');
    const first = rowsP[0], sum = $("profSum").textContent, stat = (document.querySelector('#profList .prow[data-cid="197791872"] .pstat') || {}).textContent || "", joint = ($("profJoint") || {}).textContent || "";
    sel.value = "qualifier"; sel.dispatchEvent(new Event("change", { bubbles: true }));
    const over = profileOf(slate.contests.find(c => String(c.id) === "197791874")), kept = (store(profKey()) || {})["197791874"];
    const sel2 = document.querySelector('#profList select[data-cid="197791874"]'); sel2.value = ""; sel2.dispatchEvent(new Event("change", { bubbles: true }));
    return { rowsP, first, sum, stat, joint, over, kept, back: profileOf(slate.contests.find(c => String(c.id) === "197791874")), keptAfter: (store(profKey()) || {})["197791874"] || null };
  });
  check("profiles screen: each entered contest with its recognised profile (the flagship first) and a dropdown; an override is kept for the slate and Auto puts it back; after a fill each flagship shows its top-1% coverage and P(1st) (at 2 / 3 / 4 lineups) on fresh nights, and the flagships' joint coverage",
        pr1.rowsP.length === 3 && pr1.first === "197791872" && /^Contest profiles: Flagship \(top-1% coverage\) 2 · Main \(max ROI\) 1$/.test(pr1.sum) && /^Top 1%: \d+\.\d% of nights · P\(1st\) \d+\.\d% with your 1 · P\(1st\) at 2 \/ 3 \/ 4 lineups: (\d+\.\d%|–) \/ (\d+\.\d%|–) \/ (\d+\.\d%|–) \(fresh nights, in-sim\)$/.test(pr1.stat) &&
        /^The flagships together: one of their lineups in its top 1% on \d+\.\d% of nights/.test(pr1.joint) &&
        pr1.over === "qualifier" && pr1.kept === "qualifier" && pr1.back === "main" && pr1.keptAfter === null, JSON.stringify(pr1));
  // the flagships' joint coverage: the PUJ and the High Five picked together on the same nights; the first pick is the
  // (contest, lineup) reaching its top 1% on the most nights; the joint mask is the union of each set's own top-1% nights
  const jt = await pg.evaluate(() => {
    const cs2 = ["197791872", "197791877"].map(id => slate.contests.find(x => String(x.id) === id)), pool = finalIdx().map(bi => BANK.lineups[bi]), seed = 12345;
    const sims = cs2.map(c => DKSim.simulate(Object.assign(ctx(), { random: DKSim.seeded(seed) }), pool, fieldFor(c), fieldDoc.z, c, 2, 1000));
    const ns = [2, 1], o = Object.assign(pickRules(2), { minUnique: 1 }), r = DKSim.pickJoint(ctx(), o, pool, sims, cs2, ns);
    let want = null, wv = -Infinity;
    cs2.forEach((c, ci) => { const b = DKSim.builder(sims[ci], c), z = new Uint8Array(1000); for (let k = 0; k < pool.length; k++) { const sc = b.score(k, z), v = sc.joint * 1e9 + sc.value; if (v > wv) { wv = v; want = ci + ":" + k; } } });
    const firstPick = (() => { for (let ci = 0; ci < 2; ci++) if (r.into[ci].length && (ci + ":" + r.into[ci][0]) === want) return want; return "none"; })();
    const masks = r.builders.map(b => b.cover1()), uni = masks[0].map((v, a) => v || masks[1][a] ? 1 : 0), same = uni.every((v, a) => v === r.covered[a]);
    const jc = r.covered.reduce((t, v) => t + v, 0) / 1000, own = r.builders.map(b => b.coverage().top1);
    return { sizes: r.into.map(x => x.length), want, firstPick, same, jc, own };
  });
  check("flagships: joint top-1% coverage picks the PUJ and the High Five together (the first pick the most top-1% nights alone); the joint nights are the union of each set's (" + (100 * jt.jc).toFixed(1) + "% of nights, each alone " + jt.own.map(x => (100 * x).toFixed(1) + "%").join(" / ") + ")",
        JSON.stringify(jt.sizes) === "[2,1]" && jt.firstPick === jt.want && jt.same && jt.jc >= Math.max(...jt.own) - 1e-12, JSON.stringify(jt));
  // the main contests: And-One, Quarter Jukebox and Dime Time each filled by its own Max ROI (no shared block); a lineup
  // in up to 3 contests (the flagships' included) under the night cap; a test idea only in Dime Time. A qualifier
  // (winner-take-all) against the chalk field, its lineups' own sum shown against that field's median.
  const blk0 = await pg.evaluate(() => {
    const keep = {}; document.querySelectorAll("#entriesBox input[data-cid]").forEach(i => { keep[i.dataset.cid] = i.value; });
    const set = (cid, v) => { const i = document.querySelector('#entriesBox input[data-cid="' + cid + '"]'); i.value = String(v); };
    set("197791874", 4); set("197791875", 4); set("197873654", 3); set("197873655", 2);
    const g = Object.entries(ideaCounts(finalIdx())).sort((a, b) => a[1] - b[1]).map(x => x[0]).find(x => !/Variants of the top/.test(x));   // the smallest idea
    BANK.test = { [g]: true }; bankSaveState(); renderBank(); renderEntries(); QUAL_CHALK_N = 60;     // the qualifier's chalk batch: 60 here, for time
    return { keep, g, pf: JSON.stringify(PF), maxUse: $("maxUse").value, bankN: BANK.lineups.length };
  });
  await pg.fill("#maxUse", "3");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const blk = await pg.evaluate(g => {
    QUAL_CHALK_N = 200;
    const A = PF["197791874"] || [], Q = PF["197791875"] || [], D = PF["197873654"] || [], st = document.getElementById("cutStatus").textContent;
    const uses = {}; Object.values(PF).forEach(v => v.forEach(bi => { uses[bi] = (uses[bi] || 0) + 1; }));
    const testIn = bi => lineupGroups(bi).includes(g), used = nightUsed(null), lk = fillLock();
    const flag = (PF["197791872"] || []).concat(PF["197791877"] || []);
    return { A: A.length, Q: Q.length, D: D.length, testOut: !A.concat(Q, flag).some(testIn), maxUses: Math.max(...Object.values(uses)),
             nightMax: Math.max(...Object.keys(used).filter(id => !lk[id]).map(id => used[id])), nightLim: nightLimit(),
             own: /\$1\.25K And-One \[Main \(max ROI\)\]: \d of 4/.test(st) && /Quarter Jukebox \[Main \(max ROI\)\]: \d of 4/.test(st) && /Dime Time \[Just \$0\.10!\] \[Main · lab\]: \d of 3/.test(st),
             lab: (document.querySelector('#profList .prow[data-cid="197873654"] .pstat') || {}).textContent || "" };
  }, blk0.g);
  check("main contests: And-One, Quarter Jukebox and Dime Time each by its own Max ROI; a lineup in up to 3 contests; a test idea never outside Dime Time; no player past the night cap",
        blk.A >= 3 && blk.Q >= 3 && blk.D >= 1 && blk.own && blk.testOut && blk.maxUses <= 3 && blk.nightMax <= blk.nightLim && /^Test ideas: /.test(blk.lab), JSON.stringify(blk));
  const chk = await pg.evaluate(async () => {      // the chalk batch: near the top projections (above the kept pool on projection and ownership)
    const n0 = QUAL_CHALK_N, noise = QUAL_NOISE; QUAL_CHALK_N = 60;
    const L = await qualChalk(), med = a => { const v = a.slice().sort((x, y) => x - y); return v[Math.floor(v.length / 2)]; };
    const pj = ids => ids.reduce((t, id) => t + proj(byId(id)), 0), kept = finalIdx().map(bi => BANK.lineups[bi].ids);
    return { def: n0, noise, n: L.length, projC: med(L.map(x => pj(x.ids))), projK: med(kept.map(pj)), ownC: med(L.map(x => ownSum(x.ids))), ownK: med(kept.map(ownSum)),
             legal: L.every(x => x.ids.length === 8 && x.ids.every(id => usable(byId(id)))) };
  });
  check("qualifier chalk batch: 200 by default at low noise (0.15), no leverage or rules; its lineups project above the kept pool's and own more (" + Math.round(chk.ownC) + "% vs " + Math.round(chk.ownK) + "%)",
        chk.def === 200 && chk.noise === 0.15 && chk.n >= 30 && chk.legal && chk.projC > chk.projK && chk.ownC > chk.ownK, JSON.stringify(chk));
  const bankN0 = await pg.evaluate(() => ({ n: BANK.lineups.length, keep: CUT && CUT.keep ? CUT.keep.length : null }));
  const mnQ = await pg.evaluate(() => { const v = $("maxNight").value; $("maxNight").value = ""; QUAL_CHALK_N = 60; return v; });   // the fixture's 15-entry night: the cap can shut the qualifier out
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  await pg.evaluate(v => { $("maxNight").value = v; QUAL_CHALK_N = 200; }, mnQ);
  const qf = await pg.evaluate(() => {
    const q = slate.contests.find(c => String(c.id) === "197873655"), m = slate.contests.find(c => String(c.id) === "197791874"), F = fieldOf();
    const stat = (document.querySelector('#profList .prow[data-cid="197873655"] .pstat') || {}).textContent || "", nm = (document.querySelector('#profList .prow[data-cid="197873655"] .pname') || {}).textContent || "";
    const fq = fieldFor(q), fm = fieldFor(m), dup = fq.length - new Set(fq.map(L => L.slice().sort().join())).size;
    return { prof: profileOf(q), wta: JSON.stringify(q.payouts) === JSON.stringify([[1, 1, q.prizes]]), n: (PF["197873655"] || []).length, size: fq.length === fm.length,
             medQ: fieldOwnMedian(fq), medM: fieldOwnMedian(fm), dup, stat, nm, pstats: PROF_STATS["197873655"],
             msg: (document.getElementById("cutStatus").textContent.match(/Qualifier Satellite \[[^;]*/) || [""])[0], ns: entriesN()["197873655"],
             note: ($("profQual") || {}).textContent || "", inBank: (PF["197873655"] || []).filter(bi => (BANK.tags[bi] || []).includes("Qualifier chalk")).length,
             chalkKept: (PF["197873655"] || []).filter(bi => (BANK.tags[bi] || []).includes("Qualifier chalk") && CUT && CUT.keep.includes(bi)).length,
             cut: !!(CUT && CUT.keep), bankN: BANK.lineups.length, keepN: CUT && CUT.keep ? CUT.keep.length : null };
  });
  check("qualifier: winner-take-all (one ticket to 1st), simulated against the chalk field (the slate's field reweighted to its top fifth by DraftKings average: a higher own-sum median, repeated lineups); Max ROI from the chalk batch and the kept pool; its lineups' own sum against that median, P(1st), and where they came from; a chosen chalk lineup joins the bank, not the kept pool, the cut kept; the assumed-style note",
        qf.prof === "qualifier" && qf.wta && qf.n === 2 && qf.size && qf.medQ > qf.medM && qf.dup > 0 && /winner-take-all \(1 ticket\)/.test(qf.nm) && !/assumed/.test(qf.nm) &&
        /^Own sum \d+% \/ \d+% vs the chalk field's median \d+% · P\(1st\) \d+\.\d% \(fresh nights, in-sim\) · \d from the chalk batch, \d from the kept pool$/.test(qf.stat) &&
        qf.pstats.chalk + qf.pstats.kept === 2 && qf.inBank === qf.pstats.chalk && qf.chalkKept === 0 && qf.cut && qf.keepN === bankN0.keep && qf.bankN >= bankN0.n && qf.bankN <= bankN0.n + qf.pstats.chalk &&
        /^The qualifier field is an assumed chalk style until field_users\.csv has enough real qualifier fields to refit it/.test(qf.note), JSON.stringify(qf));
  // the bank's test toggle on an idea row: one tap marks it (kept with the bank), another clears it
  const tt = await pg.evaluate(g => {
    showStep("bank"); renderBank();
    const btn = () => document.querySelector('#bankBox button[data-test="' + CSS.escape(g) + '"]');
    const on0 = btn().getAttribute("aria-pressed"); btn().click(); const off = !BANK.test[g] && btn().getAttribute("aria-pressed") === "false";
    btn().click(); const on = !!BANK.test[g] && bankUnpack(bankPack(BANK)).test[g] === true; showStep("fill");
    return { on0, off, on };
  }, blk0.g);
  check("bank: a test toggle on each idea row, kept with the bank", tt.on0 === "true" && tt.off && tt.on, JSON.stringify(tt));
  // the Swap step: the flagship's contest first
  const soP = await pg.evaluate(() => swapFlagFirst([{ name: "contest-standings-197791874.csv" }, { name: "contest-standings-197791877.csv" }, { name: "contest-standings-197791872.csv" }], f => swapCid(f.name)).map(f => swapCid(f.name)));
  check("swap step: the flagship profile's contests first in the order (the rest as they were)", JSON.stringify(soP) === JSON.stringify(["197791877", "197791872", "197791874"]), JSON.stringify(soP));
  await pg.evaluate(b => { BANK.test = {}; BANK.lineups.length = b.bankN; BANK.tags.length = b.bankN; delete BANK.tagRules["Qualifier chalk"]; if (CUT) { CUT.bankN = b.bankN; cutSave(); } bankSaveState(); renderBank(); Object.keys(b.keep).forEach(cid => { const i = document.querySelector('#entriesBox input[data-cid="' + cid + '"]'); if (i) i.value = b.keep[cid]; }); PF = JSON.parse(b.pf); pfSave(); renderEntries(); }, blk0);
  await pg.fill("#maxUse", blk0.maxUse);
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
    showStep(null);
    ["bank", "cut", "fill"].forEach(st => { document.querySelector('#stepBar button[data-step="' + st + '"]').click();
      seen[st] = [...document.querySelectorAll("section.step")].filter(x => !x.hidden).map(x => x.dataset.step).join(",") + "|" + document.querySelector("#stepBar button[aria-pressed=true]").dataset.step; });
    const kept = JSON.parse(localStorage.getItem(key())).step === undefined, labels = [...document.querySelectorAll("#stepBar button")].map(b => b.textContent);
    const bankHas = ["bankDraw", "bankN", "ruleList", "bankCheck", "bankBox", "levW"].every(id => document.getElementById(id) && document.getElementById(id).closest("#stepBank"));
    const cutHas = ["cutRun", "cutKeep", "varRun", "entriesFile"].every(id => document.getElementById(id).closest("#stepCut"));
    const fillHas = ["pfRun", "maxExpo", "entriesBox", "nb", "classic3"].every(id => document.getElementById(id).closest("#stepFill"));
    const order = [...document.querySelectorAll("#stepFill, #newsBox, #scanBox, #teamBar, #playersSec")].map(x => x.id);
    const last = document.getElementById("playersSec").compareDocumentPosition(document.getElementById("stepFill")) & Node.DOCUMENT_POSITION_PRECEDING;
    const after = JSON.stringify([BANK.lineups.length, CUT && CUT.keep && CUT.keep.length, PF]);
    document.querySelector('#stepBar button[data-step="fill"]').click();      // a second tap closes it
    const closed = stepNow() === null && [...document.querySelectorAll("section.step")].every(x => x.hidden) && !document.querySelector("#stepBar button[aria-pressed=true]");
    // Quick sim (2026-11-24): a 5th tab holding Quick lineup / Quick sim / the count / the contest; nothing else between the tabs and step 1 but the page's status line
    const quickHas = ["quickRun", "quickSim", "quickN", "quickContest", "quickBox"].every(id => document.getElementById(id).closest("#stepQuick")), quickClosed = document.getElementById("stepQuick").hidden;
    const between = []; for (let e = document.getElementById("stepBar").parentElement.nextElementSibling; e && e.id !== "stepBank"; e = e.nextElementSibling) between.push(e.id);
    document.querySelector('#stepBar button[data-step="quick"]').click(); const qOpen = !document.getElementById("stepQuick").hidden && document.getElementById("stepBank").hidden; showStep(null);
    return { seen, kept, labels, bankHas, cutHas, fillHas, order, last: !!last, same: before === after, dflt: stepNow(), closed, quickHas, quickClosed, between, qOpen };
  });
  check("step bar: a 5th tab, Quick sim (after Swap), holds Quick lineup, Quick sim, the count and the contest; closed by default; nothing between the tabs and step 1 but the page's status",
        sb.labels[4] === "Quick sim" && sb.labels.length === 5 && sb.quickHas && sb.quickClosed && JSON.stringify(sb.between) === JSON.stringify(["cutStatus"]) && sb.qOpen, JSON.stringify(sb));
  check("step bar: Bank / Cut / Fill show one panel each (kept with the slate), with live counts; switching leaves the bank, cut and picks alone; none open by default and a second tap closes (2026-11-23)",
        sb.seen.bank === "bank|bank" && sb.seen.cut === "cut|cut" && sb.seen.fill === "fill|fill" && sb.kept && sb.closed && /^Bank [\d,]+$/.test(sb.labels[0]) && /^Cut [\d,]+ kept$/.test(sb.labels[1]) && /^Fill \d+\/\d+$/.test(sb.labels[2]) &&
        sb.same && sb.dflt === null, JSON.stringify(sb));
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
    const keep0 = CUT.keep.slice(), n0 = BANK.lineups.length, r0 = CUT.variantRounds || 0;
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
    // Lab e (2026-11-24): each variant's parent stored at creation (bank index, the tag's #N resolved) and in Save build; the round counted
    const vo = buildDoc().variant_of, link = added.every(i => { const m = /variant of #(\d+)/.exec(BANK.tags[i][0]); return BANK.lineups[i].parent === keep0[+m[1] - 1] && vo[i] === keep0[+m[1] - 1]; }),
          rounds = CUT.variantRounds === r0 + 1 && buildDoc().cut_state.variantRounds === r0 + 1;
    const row = document.querySelector('#ideaTable tr[data-idea="Variants of the top"]');
    return { def, six, each: CUT.variants.each, ks: CUT.variants.keepSets, msg, added: added.length, bankGrew: BANK.lineups.length - n0, legal, near, parent, grouped, link, rounds, bankN: CUT.bankN === BANK.lineups.length, tierA: !!CUT.board.tierA,
             res: document.getElementById("varResult").textContent, row: row ? [...row.cells].map(c => c.textContent) : null };
  });
  check("variants: the result line under the row (new, joined) and a Variants of the top row in the idea table, after the cut in Banked",
        new RegExp("^\\d+ new, " + vr.added + " joined$").test(vr.res || "") && vr.row && vr.row[1] === "after the cut" && +vr.row[3] === vr.added, JSON.stringify([vr.res, vr.row]));
  check("variants of the top: legal, near their parent (5+ of 8), none sharing 7+ with a kept lineup, in the kept pool, tagged and grouped; the scoreboard redone",
        !vr.skipped && vr.added === vr.bankGrew && vr.legal && vr.near && vr.parent && vr.grouped && vr.bankN && vr.tierA && vr.added > 0 && /^Variants of the top 1 by sim value /.test(vr.msg), JSON.stringify(vr));
  check("variants (Lab e): each variant stores its parent's bank index at creation (the tag's #N), carried in Save build's variant_of; the cut counts the rounds run",
        !vr.skipped && vr.added > 0 && vr.link && vr.rounds, JSON.stringify({ link: vr.link, rounds: vr.rounds, added: vr.added }));
  check("variants (C3): every K-of-8 keep-set is the default, 56 each at K 5 (Variants each follows K), and the run used every set once",
        vr.def && vr.def.sets === "all" && vr.def.M === "56" && vr.def.Mdis && vr.def.note === "Variants: every 5-of-8 keep-set, 56 each" &&
        vr.six.M === "28" && /every 6-of-8 keep-set, 28 each/.test(vr.six.note) && vr.each === 28 && vr.ks === "all" && /every keep-set, 28 draws each/.test(vr.msg), JSON.stringify(vr));
  // --- the slate scan ------------------------------------------------------------------------------------
  await pg.fill("#scanN", "20"); await pg.fill("#scanP", "20");
  await pg.click("#scanRun");
  await pg.waitForFunction(() => /^Scanned|failed/.test(document.getElementById("scanStatus").textContent), null, { timeout: 600000 });
  // players only (2026-11-24): no team or game stack batches, rows or tables; the plain batch stays as the baseline
  const sc = await pg.evaluate(() => ({ rows: SCAN.rows.length, plainN: SCAN.plainN, plainDrawn: SCAN.plain.drawn, players: SCAN.players.length,
    stackSections: [...document.querySelectorAll("#scanTable th[colspan]")].map(t => t.textContent).filter(t => /stacks/i.test(t)), stackBtns: document.querySelectorAll('#scanTable .scanBank[data-i]').length,
    msg: document.getElementById("scanStatus").textContent, note: document.querySelector("#scanAll .note").textContent }));
  check("slate scan: players only, no team or game stack rows, tables or Bank this buttons; the plain batch (Plain lineups, at least 100) is the players' baseline",
        sc.rows === 0 && sc.plainN === 100 && sc.plainDrawn === 100 && sc.players > 20 && !sc.stackSections.length && sc.stackBtns === 0 &&
        /^Scanned \d+ players \(20 lineups each\) against 100 plain lineups in/.test(sc.msg) && /Players only: the scan has no team or game stacks/.test(sc.note), JSON.stringify(sc));
  // fixed nights: the same scan again gives the same numbers and order
  const first = await pg.evaluate(() => SCAN.players.map(r => r.key + ":" + r.g_t1.toFixed(8)).join("|"));
  await pg.click("#scanRun");
  await pg.waitForFunction(() => /^Scanned|failed/.test(document.getElementById("scanStatus").textContent) && !document.getElementById("scanRun").disabled, null, { timeout: 600000 });
  check("slate scan: on the slate's own nights, a rerun repeats exactly (and shows the players' noise)",
        (await pg.evaluate(() => SCAN.players.map(r => r.key + ":" + r.g_t1.toFixed(8)).join("|"))) === first && (await pg.evaluate(() => /±/.test(document.getElementById("scanTable").textContent))));
  // the reads strip: the leverage players, each opening its game; the team rollup in a closed All scan rows fold
  const trd = await pg.evaluate(() => {
    const b = [...document.querySelectorAll("#scanTable .topread")], fold = document.getElementById("scanAll");
    const lev = b.filter(x => x.classList.contains("read-leverage")).length, wantLev = SCAN.players.filter(r => !r.thin && r.read === "leverage").length;
    let opened = true;
    if (b[0]) { b[0].click(); opened = view.panel === b[0].dataset.team && !!document.querySelector('#teamPanel .tile[data-team="' + b[0].dataset.team + '"]'); }
    view.panel = null; renderTiles(); renderPlayers();
    return { n: b.length, lev, wantLev, closed: fold && !fold.open, roll: !!fold.querySelector("#scanPlayers"), opened, label: (document.querySelector("#scanTable .topreads b") || {}).textContent || "", focusGone: !document.getElementById("focusBank") && !document.querySelector("#scanTable .sfopts") };
  });
  check("slate scan: a Reads strip of the leverage players only (no stack buttons), each opening its game; the team rollup in a closed All scan rows fold",
        trd.n === trd.lev && trd.lev === trd.wantLev && trd.closed && trd.roll && trd.opened && (trd.wantLev ? trd.label === "Reads" : trd.label === "") && trd.focusGone, JSON.stringify(trd));
  // the game view's scan block: the team's core and leverage players, no stack rows; an old saved scan's stack rows are ignored
  const gsc = await pg.evaluate(() => {
    const t = teamsOf().teams[0]; view.panel = t.team; view.pside = t.team; renderTiles();
    const blk = document.querySelector('#teamPanel .tvl .scanblk'), sr = blk.querySelectorAll(".sr").length, bank = blk.querySelectorAll(".scanBank").length;
    const names = [...blk.querySelectorAll(".read-core, .read-leverage")].map(x => x.textContent.replace(/ \((core|leverage)\)$/, "")).sort();
    const wantN = SCAN.players.filter(r => r.team === t.team && !r.thin && (r.read === "core" || r.read === "leverage")).map(r => r.key).sort();
    const keep = SCAN.rows, errs0 = 0;
    SCAN.rows = [{ key: t.team + " 3+", kind: "team", team: t.team, n: 3, g_t1: 0.5, t1: 0.5, field: 0.1, read: "strong, field light", thin: false, distinct: 99 },
                 { key: gameOf(t.team) + " 3+", kind: "game", game: gameOf(t.team), n: 3, g_t1: 0.4, t1: 0.4, field: 0.1, read: "weak", thin: false, distinct: 99 }];
    renderScan(); renderTeamPanel();
    const old = !/strong, field light|Team stacks|Game stacks/.test(document.getElementById("scanTable").textContent + document.getElementById("teamPanel").textContent) &&
      !document.querySelector("#teamPanel table.gstk") && !document.querySelector('#scanTable .scanBank[data-i]');
    SCAN.rows = keep; renderScan();
    view.panel = null; renderTiles(); renderPlayers();
    return { sr, bank, names, wantN, old };
  });
  check("game view: the team's Scan block lists its core / leverage players with no stack rows; an old saved scan's stack rows load and are ignored",
        gsc.sr === 1 && gsc.bank === 0 && JSON.stringify(gsc.names) === JSON.stringify(gsc.wantN) && gsc.old, JSON.stringify(gsc));
  // the player scan, at the top: a row for every player in the pool, gains over the same plain
  // batch, Read on the players' own noise and their median field ownership, the team rollup from those reads
  const ps = await pg.evaluate(() => {
    const want = rows.filter(r => usable(r)).map(r => r.id).sort(), P = SCAN.players, m = SCAN.pownMedian;
    const ids = P.map(r => r.id).sort(), bar = SCAN.pbar;
    const reads = bar > 0 && P.every(r => r.read === (r.g_t1 > bar ? (r.fown >= m ? "core" : "leverage") : r.g_t1 < -bar ? (r.fown >= m && r.fown >= 15 ? "fade" : "skip") : r.g_t1 > 0 ? (r.fown >= m ? "lean core" : "lean leverage") : "even"));
    const gains = P.every(r => Math.abs(r.g_t1 - (r.t1 - SCAN.plain.t1)) < 1e-12 && Math.abs(r.g_cash - (r.cash - SCAN.plain.cash)) < 1e-12);
    const noOut = P.every(r => { const x = byId(r.id); return x.status !== "Out" && !x.deepOut; });
    const first = document.querySelector("#scanTable table").id === "scanPlayers" && !document.querySelector('#scanTable th[data-skind="player"]');
    const roll = SCAN.teamRoll.every(t => t.core.every(r => r.read === "core" && r.team === t.team) && t.lev.every(r => r.read === "leverage" && r.team === t.team) && t.n >= 1 && !("st" in t));
    const rollAll = P.filter(r => !r.thin && (r.read === "core" || r.read === "leverage")).every(r => SCAN.teamRoll.some(t => t.ids.includes(r.id)));
    return { n: P.length, same: JSON.stringify(ids) === JSON.stringify(want), reads, gains, noOut, first, roll, rollAll, sum: SCAN.players.reduce((o, r) => (o[r.read] = (o[r.read] || 0) + 1, o), {}) };
  });
  check("player scan: a row for every player in the pool (none Out, Doubtful or deep bench), gains over the plain batch, Read core/leverage/fade/skip/even from its own noise and the median field own (fade also 15%+ owned); no Players table of its own in the scan (the Players list carries it), the team rollup first",
        ps.n > 20 && ps.same && ps.reads && ps.gains && ps.noOut && ps.first, JSON.stringify(ps));
  check("player scan: the team rollup lists each team's core and leverage players (no best team stack)", ps.roll && ps.rollAll, JSON.stringify(ps));
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
        c[1].textContent.replace(/\u25ae$/, "") === x.read && c[1].querySelector(".read-" + x.read.replace(/ /g, "-")) && !!c[2].querySelector(".pbank") &&
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
  check("player table: with a scan the scan columns show (no-scan layout off)", await pg.evaluate(() => { renderPlayers(); const c = document.querySelector("#players .row .rdc");
    return !$("players").classList.contains("noscan") && !!c && getComputedStyle(c).display !== "none"; }));
  const c1 = await pg.evaluate(() => {
    renderPlayers(); const bs = bankShare(), mk = c => [...document.querySelectorAll("#players .row .rdc .gapm." + c)].map(e => e.closest(".row").dataset.id), rowsIn = mk("in"), rowsOut = mk("out");
    const onRow = !document.querySelector("#players .row.bankgap-in, #players .row.bankgap-out") && [...document.querySelectorAll("#players .gapm")].every(m => m.previousElementSibling && /^read-/.test(m.previousElementSibling.className) && !!m.title);
    // the rule by hand (2026-11-24: the scan floors' own, from the Floors fold): floor core 1.1 / leverage 1.75 / lean 1.0 x own (at most 60), cap fade 0.6 x own (at least 1), skip a flat skipPct; under 2% owned, thin or not in the pool: none
    const o = sfOpts(), lim = (x, r) => { if (!r || x.thin || !usable(r)) return null; const fo = own(r); if (!(fo > 0) || (fo < 2 && !o.low)) return null;
      const m = { core: o.core, leverage: o.leverage, "lean core": o.lean, "lean leverage": o.lean, fade: o.fade }[x.read];
      if (x.read === "skip") return { cap: Math.max(1, Math.round(+o.skipPct)) }; if (m == null) return null;
      return x.read === "fade" ? { cap: Math.max(1, Math.round(m * fo)) } : Math.min(60, Math.round(m * fo)) > 0 ? { floor: Math.min(60, Math.round(m * fo)) } : null; };
    const flag = x => { const r = byId(String(x.id)), l = lim(x, r), b = 100 * (bs[x.id] || 0); return !l ? "" : l.floor != null ? (b < l.floor ? "in" : "") : (b > l.cap ? "out" : ""); };
    const inOk = rowsIn.every(id => flag(scanRowOf(id)) === "in"), outOk = rowsOut.every(id => flag(scanRowOf(id)) === "out");
    const want = SCAN.players.filter(x => byId(x.id).status !== "Out" && flag(x) && document.querySelector('#players .row[data-id="' + x.id + '"]')).length;
    // the tooltips, on a real player with a made-up read and bank share
    const pr = rows.filter(r => usable(r) && own(r) >= 5).sort((a, b) => own(b) - own(a))[0], fo = own(pr), sc = rd => ({ id: pr.id, read: rd, thin: false });
    const tips = [bankGap(pr, 0, sc("core")), bankGap(pr, 0.6, sc("core")), bankGap(pr, 0.6, sc("skip")), bankGap(pr, 0.6, sc("fade")), bankGap(pr, 0.6, sc("even")), bankGap(pr, 0, sc("lean leverage"))].map(g => g && g.tip);
    const wantTips = ["core: bank 0% vs floor 1.1\u00d7 field " + Math.round(fo) + "% = " + Math.min(60, Math.round(1.1 * fo)) + "%", null, "skip: bank 60% vs cap " + Math.max(1, Math.round(+o.skipPct)) + "%",
                      0.6 * 100 > Math.max(1, Math.round(0.6 * fo)) ? "fade: bank 60% vs cap 0.6\u00d7 field " + Math.round(fo) + "% = " + Math.max(1, Math.round(0.6 * fo)) + "%" : null, null,
                      "lean leverage: bank 0% vs floor 1\u00d7 field " + Math.round(fo) + "% = " + Math.min(60, Math.round(fo)) + "%"];
    const f0 = state.floor[pr.id]; state.floor[pr.id] = 25; const handTip = bankGap(pr, 0, sc("core")).tip; if (f0 == null) delete state.floor[pr.id]; else state.floor[pr.id] = f0;
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
    return { focusIds: SCAN.focus || [], pre, tips, wantTips, handTip, onRow, focusOk, leanCls, inOk, outOk, shown: rowsIn.length + rowsOut.length, want, rule: rule && { type: rule.type, n: rule.n, k: rule.ids.length, same: JSON.stringify(rule.ids.slice().sort()) === JSON.stringify((SCAN.focus || []).slice().sort()) }, hasBtn: !!b, focus: (SCAN.focus || []).length };
  });
  check("bank helpers (C1, on the scan floors' rule): under the floor the scan would set (core 1.1x, leverage 1.75x, lean 1.0x own) or over its cap (fade 0.6x own, skip flat); even none; the tooltip names the rule and a hand Min%",
        JSON.stringify(c1.tips) === JSON.stringify(c1.wantTips) && /^core: bank 0% vs floor .* \(your Min%: 25%\)$/.test(c1.handTip), JSON.stringify(c1));
  check("lean reads: the focus set takes strong core / leverage first, then lean by gain; lean reads in their own colour class", c1.focusOk && c1.leanCls, JSON.stringify([c1.focusOk, c1.leanCls]));
  check("bank helpers (C1): the Players list marks, right after the Read word (not the row's edge), a player banked under his scan floor (green) or over his cap (red); the strip's focus button is gone (2026-11-24)",
        c1.inOk && c1.outOk && c1.onRow && c1.shown === c1.want && !c1.hasBtn, JSON.stringify(c1));
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
  // scan floors (2026-11-24): one tap sets Min% / Max% from each player's Read x his field ownership; hand entries stay
  const sf = await pg.evaluate(() => {
    try { localStorage.removeItem("dkcbb:scanfloor"); } catch (e) {}
    renderScan();
    const was = { floor: Object.assign({}, state.floor), cap: Object.assign({}, state.cap) };
    const M = { core: 1.1, leverage: 1.75, "lean core": 1, "lean leverage": 1, fade: 0.6, skip: "flat" };
    const elig = SCAN.players.filter(x => !x.thin && M[x.read] != null && usable(byId(String(x.id))) && own(byId(String(x.id))) >= 2);
    const low = SCAN.players.filter(x => !x.thin && M[x.read] != null && usable(byId(String(x.id))) && own(byId(String(x.id))) > 0 && own(byId(String(x.id))) < 2).map(x => String(x.id));
    const fl = elig.filter(x => !/fade|skip/.test(x.read)), cp = elig.filter(x => /fade|skip/.test(x.read));
    const handF = fl[0] && String(fl[0].id), handC = cp[0] && String(cp[0].id);
    if (handF) state.floor[handF] = 7; if (handC) state.cap[handC] = 33;
    save(); renderPlayers();
    document.getElementById("sfSet").click();
    const exp = id => { const x = SCAN.players.find(p => String(p.id) === id), f = own(byId(id)), raw = x.read === "skip" ? 10 : M[x.read] * f;
      return /fade|skip/.test(x.read) ? ["cap", Math.max(1, Math.round(raw))] : ["floor", Math.min(60, Math.round(raw))]; };
    const right = elig.map(x => String(x.id)).filter(id => id !== handF && id !== handC).every(id => { const [k, v] = exp(id); return v <= 0 && k === "floor" || state[k][id] === v && !!byScan(k, id); });
    const handKept = (!handF || (state.floor[handF] === 7 && !byScan("floor", handF))) && (!handC || (state.cap[handC] === 33 && !byScan("cap", handC)));
    const lowNone = low.every(id => !byScan("floor", id) && !byScan("cap", id));
    const marked = document.querySelectorAll("#players input.byscan").length;
    const wantMarked = [...document.querySelectorAll("#players .row")].filter(e => byScan("floor", e.dataset.id) || byScan("cap", e.dataset.id)).reduce((t, e) => t + !!byScan("floor", e.dataset.id) + !!byScan("cap", e.dataset.id), 0);
    const handBox = handF ? !document.querySelector(`#players .row[data-id="${handF}"] input.floor`).classList.contains("byscan") : true;
    const tagged = /SCANFLOOR/.test(tagNow()), tagRules = (() => { const t0 = BANK.tagRules; return true; })();
    // clamps: an extreme core multiplier holds floors at 60%; a 0 skip cap holds caps at 1%
    const ext = scanFloorPlan({ core: 100, leverage: 100, lean: 100, fade: 0, skipPct: 0, low: false });
    const clamp = ext.every(p => p.kind === "floor" ? p.v <= 60 : p.v >= 1) && ext.some(p => p.kind === "floor" && p.v === 60);
    // a hand edit on a scan box makes it a hand entry; Clear floors removes only the scan's
    const ids = Object.keys(state.scanSet.floor), edited = ids[0];
    let editOk = true;
    if (edited) { const inp = document.querySelector(`#players .row[data-id="${edited}"] input.floor`);
      if (inp) { inp.value = "12"; inp.dispatchEvent(new Event("change", { bubbles: true })); editOk = state.floor[edited] === 12 && !byScan("floor", edited); } }
    const nScan = Object.keys(state.scanSet.floor).filter(id => byScan("floor", id)).length + Object.keys(state.scanSet.cap).filter(id => byScan("cap", id)).length;
    const clearBtn = !document.getElementById("sfClear").hidden && !!document.getElementById("sfClear").closest(".filters, .opts, div") && !document.getElementById("sfSet").closest("#scanTable");
    document.getElementById("sfClear").click();
    const cleared = !scanFloorsOn() && !/SCANFLOOR/.test(tagNow()) && (!handF || state.floor[handF] === 7) && (!handC || state.cap[handC] === 33) && (!edited || state.floor[edited] === 12) &&
      elig.map(x => String(x.id)).filter(id => id !== handF && id !== handC && id !== edited).every(id => state.floor[id] == null && state.cap[id] == null);
    // the multipliers are fixed (2026-11-24): a value left in dkcbb:scanfloor is ignored; no Floors fold; Clear floors hidden once none are set
    try { localStorage.setItem("dkcbb:scanfloor", JSON.stringify({ core: 1.3 })); } catch (e) {}
    const kept = sfOpts().core === 1.1 && sfOpts().skipPct === 10 && !document.querySelector("#scanTable .sfopts, #scanTable .sfm") && document.getElementById("sfClear").hidden;
    try { localStorage.removeItem("dkcbb:scanfloor"); } catch (e) {}
    state.floor = was.floor; state.cap = was.cap; state.scanSet = { floor: {}, cap: {} }; save(); renderRules(); renderPlayers(); renderScan();
    return { n: elig.length, floors: fl.length, caps: cp.length, right, handKept, lowNone, low: low.length, marked, wantMarked, handBox, tagged, clamp, editOk, nScan, clearBtn, cleared, kept };
  });
  check("scan floors: Set floors from scan puts Read x field own in Min% (core 1.1, leverage 1.75, lean 1.0) / Max% (fade 0.6x, skip a flat 10%), under-2% owned skipped, dashed 'set by scan' boxes, hand entries untouched, draws tagged SCANFLOOR",
        sf.n > 5 && sf.right && sf.handKept && sf.lowNone && sf.marked === sf.wantMarked && sf.marked > 0 && sf.handBox && sf.tagged, JSON.stringify(sf));
  check("scan floors: floors held to 60% and caps to 1%; typing in a scan box makes it a hand entry; Clear floors (Players toolbar, shown only while scan floors are set) removes only the scan's; the multipliers fixed",
        sf.clamp && sf.editOk && sf.clearBtn && sf.cleared && sf.kept, JSON.stringify(sf));
  // stack quick buttons (2026-11-24): per game 2+1 either side, 2+2, 3+2 either side; two min rules, the batch tagged STACK <game> <shape>
  const sq = await pg.evaluate(async () => {
    const n0 = state.rules.length, rules0 = JSON.stringify(state.rules);
    const g = rows.find(r => r.game && r.game.indexOf("@") > 0 && usable(r)).game, [A, H] = g.split("@");
    view.panel = A; view.pside = A; renderTiles(); renderPlayers(); renderTeamPanel();
    const btns = [...document.querySelectorAll("#teamPanel .stackq button[data-shape]")].map(b => b.dataset.a + " " + b.dataset.x + "+" + b.dataset.y);
    const click = (a, x, y) => document.querySelector(`#teamPanel .stackq button[data-a="${a}"][data-x="${x}"][data-y="${y}"]`).click();
    click(H, 2, 1);
    const r1 = state.rules.slice(n0), ids = t => rows.filter(r => r.team === t).map(r => r.id).sort().join(",");
    const one = r1.length === 2 && r1[0].type === "min" && r1[0].n === 2 && r1[0].ids.slice().sort().join(",") === ids(H) && r1[1].n === 1 && r1[1].ids.slice().sort().join(",") === ids(A);
    const tag1 = tagNow(), tagOk = tag1.indexOf("STACK " + g + " 2+1 (2 " + H + ")") >= 0 && tag1.indexOf(": 2+ from") < 0;
    const pressed = document.querySelector(`#teamPanel .stackq button[data-a="${H}"][data-x="2"]`).getAttribute("aria-pressed") === "true";
    click(A, 3, 2);
    const r2 = state.rules.slice(n0), msg2 = document.getElementById("stackMsg").textContent, repl = r2.length === 2 && r2[0].n === 3 && r2[0].ids.slice().sort().join(",") === ids(A) && r2[1].n === 2 && /in place of/.test(msg2);
    // a draw under it: every lineup 3+ from the away side and 2+ from the home side (nothing banked)
    const res = await drawBank(ctx(), drawRules(), 20, { noBank: true });
    const cnt = (L, t) => L.ids.filter(id => byId(id).team === t).length;
    const drawn = res.lineups.length > 0 && res.lineups.every(L => cnt(L, A) >= 3 && cnt(L, H) >= 2);
    // the batch's saved rules carry the shape (dk_eval idea_kind: "quick stack 3+2"); Remove on either row takes both
    const conds = drawRules().conds.filter(r => r.stackq), saved = conds.length === 2 && conds.every(r => r.stackq.shape === "3+2" && r.stackq.tag === "STACK " + g + " 3+2 (3 " + A + ")");
    renderRules();
    const rm = document.querySelector(`#ruleList .rule[data-i="${n0}"] button[data-act="rm"]`); rm.click();
    const gone = state.rules.length === n0 && !/STACK/.test(tagNow());
    click(A, 2, 2); click(A, 2, 2);            // the same button again takes it off
    const toggled = state.rules.length === n0;
    state.rules = JSON.parse(rules0); save(); renderRules(); view.panel = null; renderTiles(); renderPlayers(); renderTeamPanel();
    return { g, btns, one, tagOk, tag1, pressed, repl, msg2, drawn, n: res.lineups.length, saved, gone, toggled };
  });
  check("stack quick buttons: each game offers 2+1 either side, 2+2, 3+2 either side; a click adds n from one team and m from the other, names the batch STACK <game> <shape>, replaces that game's earlier shape, and the draw obeys it",
        sq.btns.length === 5 && sq.one && sq.tagOk && sq.pressed && sq.repl && sq.drawn && sq.saved && sq.gone && sq.toggled, JSON.stringify(sq));
  // per-game floors (2026-11-24): Clear this game holds the game's Min% (scan-set and typed) and empties them;
  // Restore floors puts them back (the scan marker too) where the box is still empty; other games and Max% untouched
  const gfl = await pg.evaluate(() => {
    const fl0 = JSON.stringify(state.floor), cap0 = JSON.stringify(state.cap), ss0 = JSON.stringify(state.scanSet);
    const g = rows.find(r => r.game && r.game.indexOf("@") > 0 && usable(r)).game, [A, H] = g.split("@");
    const inG = rows.filter(r => r.game === g && usable(r)), other = rows.find(r => r.game && r.game !== g && usable(r));
    const a = inG[0].id, b = inG[1].id, c = inG[2].id;
    state.floor = { [a]: 20, [b]: 15, [other.id]: 10 }; state.cap = { [c]: 5 };
    state.scanSet = { floor: { [a]: { v: 20, note: "core 1.1x" } }, cap: {} };
    save(); view.panel = A; view.pside = A; renderTiles(); renderPlayers(); renderTeamPanel();
    const btn = document.querySelector("#teamPanel .gfClear"), label = btn && btn.textContent;
    btn.click();
    const cleared = state.floor[a] == null && state.floor[b] == null && state.floor[other.id] === 10 && state.cap[c] == null && !byScan("floor", a);
    const held = state.gameFloors[g] && state.gameFloors[g].floor[a] === 20 && state.gameFloors[g].floor[b] === 15 && state.gameFloors[g].cap[c] === 5;
    const rb = document.querySelector("#teamPanel .gfRestore"), rlabel = rb && rb.textContent, noClear = !document.querySelector("#teamPanel .gfClear");
    state.floor[b] = 30; save();                // typed in since: Restore leaves it
    rb.click();
    const back = state.floor[a] === 20 && state.floor[b] === 30 && state.cap[c] === 5 && !!byScan("floor", a) && !state.gameFloors[g] && !document.querySelector("#teamPanel .gfRestore");
    const msg = document.getElementById("stackMsg").textContent;
    state.floor = JSON.parse(fl0); state.cap = JSON.parse(cap0); state.scanSet = JSON.parse(ss0); delete state.gameFloors;
    save(); view.panel = null; renderTiles(); renderPlayers(); renderTeamPanel();
    return { g, label, cleared, held, rlabel, noClear, back, msg };
  });
  check("per-game floors: Clear this game empties and holds the game's Min% and Max% (scan and typed; other games stay); Restore puts them back, the scan mark too, leaving boxes typed in since",
        /Clear this game \(3\)/.test(gfl.label) && gfl.cleared && gfl.held && /Restore floors \(3\)/.test(gfl.rlabel) && gfl.noClear && gfl.back && /Restored 1 Min% and 1 Max%.*1 box typed/.test(gfl.msg), JSON.stringify(gfl));
  // checks (2026-11-24): boxes met per player in a game, badge + shading, sort, Set greens (GREENS <game>) beside Draw the 9
  const ckt = await pg.evaluate(() => {
    const keys = ["min_avg", "gp", "obpr", "bpr_rank", "dk_avg", "last5", "p_play", "status"], was = rows.map(r => keys.map(k => r[k]));
    const n0 = state.rules.length, rules0 = JSON.stringify(state.rules), wu0 = wuDoc;
    try { localStorage.removeItem("dkcbb:checks"); } catch (e) {}
    // a spread of made-up season lines so every box has a pool
    rows.forEach((r, i) => { r.min_avg = 16 + (i % 12); r.gp = 5; r.obpr = (i % 10) / 2; r.bpr_rank = 3 + (i % 5); r.dk_avg = r.min_avg * (0.5 + (i % 7) / 20);
      const sal = r.salary / 1000; r.last5 = [0, 1, 2, 3, 4].map(k => ["d" + k, r.min_avg, sal * (2 + ((i + k) % 4))]); r.p_play = 1; });
    const G = rows.find(r => r.game && r.game.indexOf("@") > 0 && usable(r) && r.status !== "Out").game, ids = gameIds(G).map(byId).filter(r => usable(r) && !isQ(r) && r.status !== "Out" && !sitRisk(r));
    const P = ids[0], W = ids[1], Q = ids[2], S = ids[3];
    const top = r => { r.obpr = 9; r.bpr_rank = 1; r.min_avg = 36; r.dk_avg = 36 * 2; r.last5 = [0, 1, 2, 3, 4].map(k => ["d" + k, 36, r.salary / 1000 * 6]); };
    top(P); top(Q); top(S);
    W.obpr = 0; W.bpr_rank = 9; W.min_avg = 16; W.dk_avg = 16 * 0.3; W.last5 = [0, 1, 2, 3, 4].map(k => ["d" + k, 16, W.salary / 1000 * 1.5]);
    Q.status = "Questionable"; S.p_play = 0.4;
    const m = checksMap(), five = c => c.boxes.slice(0, 5).filter(x => x.ok).length;
    const hasBank = !!(BANK && BANK.lineups && BANK.lineups.length), hasScan = rows.some(r => !!scanRowOf(r.id));
    const boxes = { P: five(m[P.id]), W: five(m[W.id]), avail: m[P.id].avail, want: 5 + hasBank + hasScan, Plevel: m[P.id].level, Qgrey: m[Q.id].grey, Qlevel: m[Q.id].level, Sgrey: m[S.id].grey, Slevel: m[S.id].level };
    // the game view: a badge on every row, the shade, the sort (most boxes first), the hover
    view.panel = P.team; view.pside = P.team; view._ckGame = null; renderTiles(); renderPlayers(); renderTeamPanel();
    const rowsV = [...document.querySelectorAll("#teamPanel .plist .row")], badges = rowsV.every(e => { const b = e.querySelector(".ck"), c = m[e.dataset.id]; return b && b.textContent === c.hit + "/" + c.avail; });
    const shade = rowsV.every(e => { const c = m[e.dataset.id]; return e.classList.contains("ckg") === (c.level === "g") && e.classList.contains("ckl") === (c.level === "l"); });
    const firstOfP = rowsV.map(e => byId(e.dataset.id)).filter(r => r.team === P.team && r.status !== "Out")[0];
    const sortOk = view.psort === "checks" && firstOfP && m[firstOfP.id].hit === Math.max(...rowsV.map(e => byId(e.dataset.id)).filter(r => r.team === P.team && r.status !== "Out").map(r => m[r.id].hit));
    const pb = document.querySelector(`#teamPanel .row[data-id="${P.id}"] .ck`), tip = pb && pb.title, qb = document.querySelector(`#teamPanel .row[data-id="${Q.id}"] .ck`);
    const hover = /boxes/.test(tip) && /✓ OBPR: 9\.00/.test(tip) && /✓ MPG: 36\.0/.test(tip) && /✓ 5x rate: 100%/.test(tip), greyed = !qb || (qb.classList.contains("ck-x") && /Never green: Questionable/.test(qb.title));
    // Set greens: one template-5 rule over the game's greens, N 3 for 5+ else 2, the spread on, the batch named GREENS <game>
    const greens = greensOf(G), setB = document.getElementById("ckSet"), d9 = document.getElementById("ckDraw9");
    setB.click();
    const r1 = state.rules.slice(n0), rule = r1[0];
    const setOk = r1.length === 1 && rule.type === "min" && JSON.stringify(rule.ids) === JSON.stringify(greens) && rule.n === Math.min(greens.length, greens.length >= 5 ? 3 : 2) &&
      rule.greens.tag === "GREENS " + G && (greens.length < 2 || (isT5(rule) && greens.every(id => drawRules().spread[id] === 10)));
    const tag = tagNow(), tagOk = tag.indexOf("GREENS " + G) >= 0 && tag.indexOf(rule.label) < 0, pressed = document.getElementById("ckSet").getAttribute("aria-pressed") === "true",
          beside = !!d9 && d9.previousElementSibling && d9.previousElementSibling.id === "ckSet", msg = document.getElementById("ckMsg").textContent;
    document.getElementById("ckSet").click();
    const cleared = state.rules.length === n0 && !/GREENS/.test(tagNow());
    // the Boxes fold: a threshold edited is remembered and re-reads the boxes
    const inp = document.querySelector('#teamPanel .ckm[data-k="mpgAbs"]'); inp.value = "40"; inp.dispatchEvent(new Event("change", { bubbles: true }));
    const remembered = ckOpts().mpgAbs === 40 && document.querySelector('#teamPanel .ckm[data-k="mpgAbs"]').value === "40";
    try { localStorage.removeItem("dkcbb:checks"); } catch (e) {}
    // the write-up's player line carries his badge
    wuDoc = { slates: { [String(slate.draft_group_id)]: { [P.team]: { paras: [["", "**" + P.name + "** ($9,000) averages 36 minutes."]], table: [{ id: P.id, name: P.name, starts: 5, gp: 5 }] } } } };
    renderTeamPanel();
    const wuB = document.querySelector("#teamPanel .wu p .ck"), wuOk = !!wuB && wuB.textContent === m[P.id].hit + "/" + m[P.id].avail;
    wuDoc = wu0; rows.forEach((r, i) => keys.forEach((k, j) => { r[k] = was[i][j]; })); state.rules = JSON.parse(rules0); save(); renderRules(); view.panel = null; renderTiles(); renderPlayers(); renderTeamPanel();
    return { G, boxes, badges, shade, sortOk, hover, greyed, nGreens: greens.length, setOk, tagOk, pressed, beside, msg, cleared, remembered, wuOk };
  });
  check("checks: five boxes from the slate's own pools (a top player meets all five, a weak one none); bank and scan boxes counted only once they exist; Questionable and sit risk never green",
        ckt.boxes.P === 5 && ckt.boxes.W === 0 && ckt.boxes.avail === ckt.boxes.want && ckt.boxes.Plevel === "g" && /Questionable/.test(ckt.boxes.Qgrey) && ckt.boxes.Qlevel === "" && ckt.boxes.Sgrey === "sit risk" && ckt.boxes.Slevel === "", JSON.stringify(ckt));
  check("checks: the game view shows a hit/available badge on every row (hover: each box with its value; greyed with the reason), green rows shaded, most boxes first by default; the write-up's player line carries it too",
        ckt.badges && ckt.shade && ckt.sortOk && ckt.hover && ckt.greyed && ckt.wuOk, JSON.stringify(ckt));
  check("checks: Set greens adds at least N of the game's greens (N 3 for 5+, else 2; 10% spread), names the batch GREENS <game>, sits beside Draw the 9; again clears it; the Boxes thresholds are remembered",
        ckt.nGreens >= 1 && ckt.setOk && ckt.tagOk && ckt.pressed && ckt.beside && /GREENS/.test(ckt.msg) && ckt.cleared && ckt.remembered, JSON.stringify(ckt));
  // Play for a Questionable player (2026-11-24): confirmed playing, "Q · playing", counted in the checks; projection and ownership untouched
  const qp = await pg.evaluate(() => {
    const r = rows.find(x => x.status === "Questionable" && !isDoubtful(x) && !state.outs[x.id]);
    if (!r) return { none: true };
    view.pool = "all"; view.q = ""; view.team = null; view.pos = null; renderPlayers();
    const rowEl = () => document.querySelector(`#players .row[data-id="${r.id}"]`);
    const btns0 = [...rowEl().querySelectorAll(".lx button.act")].map(b => b.textContent), grey0 = checksMap()[r.id].grey, p0 = proj(r), o0 = own(r);
    rowEl().querySelector(".qplay").click();
    const tag = rowEl().querySelector(".tag.qp"), btns1 = [...rowEl().querySelectorAll(".lx button.act")].map(b => b.textContent), c1 = checksMap()[r.id];
    const saved = !!(store(key()).qplay || {})[r.id], built = !!(buildDoc().q_play || {})[r.id], same = proj(r) === p0 && own(r) === o0 && r.status === "Questionable";
    view.panel = r.team; view.pside = r.team; view.showAll = true; renderTiles(); renderTeamPanel();
    const inGame = !!document.querySelector(`#teamPanel .row[data-id="${r.id}"] .tag.qp`);
    view.showAll = false; view.panel = null; renderTiles(); renderPlayers();
    rowEl().querySelector(".qplay").click();          // undo
    const back = !state.qplay[r.id] && !rowEl().querySelector(".tag.qp") && !!rowEl().querySelector(".tag.q") && /Questionable/.test(checksMap()[r.id].grey);
    rowEl().querySelector(".qout").click();           // Mark out as before
    const out = r.status === "Out" && !!state.outs[r.id] && [...rowEl().querySelectorAll(".lx button.act")].map(b => b.textContent).join(",") === "undo";
    rowEl().querySelector(".qout").click();
    const restored = r.status === "Questionable" && !state.outs[r.id];
    return { name: r.name, btns0, grey0, tag: tag && tag.textContent, btns1, grey1: c1.grey, saved, built, same, inGame, back, out, restored };
  });
  check("Q Play: an unresolved Q shows play and out; play tags him 'Q · playing' (list and game view), ungreys him in the checks, saves with the slate and Save build, and leaves his projection and ownership; undo returns plain Q; Mark out works as before",
        qp.none || (JSON.stringify(qp.btns0) === JSON.stringify(["play", "out"]) && /Questionable/.test(qp.grey0) && qp.tag === "Q · playing" && JSON.stringify(qp.btns1) === JSON.stringify(["undo"]) &&
        !/Questionable/.test(qp.grey1) && qp.saved && qp.built && qp.same && qp.inGame && qp.back && qp.out && qp.restored), JSON.stringify(qp));
  // checks box 6 on the BASE bank (2026-11-24): base tags matched, frozen, hand pick, no-base fallback, the Bank column's base option
  const cb6 = await pg.evaluate(() => {
    const B0 = BANK, cb0 = state.ckBase, ids = rows.filter(r => usable(r)).map(r => r.id), mk = k => ({ ids: ids.slice(k, k + 8), slots: ids.slice(k, k + 8) });
    BANK = { lineups: [mk(0), mk(1), mk(2), mk(3), mk(10), mk(11)], tags: [["no rules"], ["X L0 U0"], ["X L0.1 U1"], ["salary ≥ 49000 + STACK A@B 2+1 (2 A)"], ["X L0 U0", "UK group"], ["UK group"]],
             tagRules: {}, groups: { "no rules": "BASE", "X L0 U0": "base", "X L0.1 U1": "base", "salary ≥ 49000 + STACK A@B 2+1 (2 A)": "UK", "UK group": "Kentucky" } };
    bankShareMemo = null; delete state.ckBase;
    const auto = autoBaseTags(), bb = baseBank(), want = {};
    [0, 1, 4].forEach(i => BANK.lineups[i].ids.forEach(id => { want[id] = (want[id] || 0) + 1 / 3; }));
    const shareOk = bb && bb.n === 3 && Object.keys(want).every(id => Math.abs(bb.share[id] - want[id]) < 1e-12) && Object.keys(bb.share).length === Object.keys(want).length;
    const pid = BANK.lineups[0].ids[0], c6 = checksMap()[pid].boxes.find(x => x.k === "bank/field"), hover = /^base bank share \d+% vs field \d+%/.test(c6.v);
    // a later base batch doesn't move the frozen numbers
    BANK.lineups.push(mk(20)); BANK.tags.push(["Y L0 U0"]); BANK.groups["Y L0 U0"] = "BASE"; bankShareMemo = null;
    const frozen = baseBank().n === 3 && baseBank().at === bb.at;
    // the Boxes fold: which tags, a hand pick recomputes, Refreeze takes the auto match as it is now
    const g = rows.find(r => r.game && r.game.indexOf("@") > 0).game; view.panel = g.split("@")[0]; view.pside = view.panel; renderTiles(); renderTeamPanel();
    const fold = document.querySelector("#teamPanel .ckbase").textContent, foldOk = /3 lineups from .*no rules.*X L0 U0/.test(fold) && /frozen/.test(fold);
    const box = document.querySelector('#teamPanel .ckbt[data-tag="UK group"]'); box.checked = true; box.dispatchEvent(new Event("change", { bubbles: true }));
    const picked = baseBank().src === "pick" && baseBank().n === 2 && JSON.stringify(state.ckBase.pick) === JSON.stringify(["UK group"]);
    const box2 = document.querySelector('#teamPanel .ckbt[data-tag="UK group"]'); box2.checked = false; box2.dispatchEvent(new Event("change", { bubbles: true }));
    document.getElementById("ckRefreeze").click();
    const refrozen = baseBank().src === "auto" && baseBank().n === 4 && JSON.stringify(baseBank().tags) === JSON.stringify(["X L0 U0", "Y L0 U0", "no rules"]);
    // the Bank column: whole bank by default, base on the toggle
    view.panel = null; renderTiles(); view.bankBase = false; renderPlayers();
    const hdr0 = document.querySelector('#players .head [data-sort="bank"]').textContent;
    document.querySelector("#players .head .bbtog").click();
    const cell = document.querySelector(`#players .row[data-id="${pid}"] .col-bank`), colOk = view.bankBase && /^Base/.test(document.querySelector('#players .head [data-sort="bank"]').textContent) &&
      cell.textContent === Math.round(100 * baseBank().share[pid]) + "%" && /of the base bank \(4 lineups\)/.test(cell.title) && view.sort !== "bank";
    document.querySelector("#players .head .bbtog").click();
    const colBack = !view.bankBase && /^Bank/.test(hdr0) && document.querySelector(`#players .row[data-id="${pid}"] .col-bank`).textContent === Math.round(100 * bankShare()[pid]) + "%";
    // no base: the whole bank, labelled
    BANK = { lineups: [mk(0), mk(1)], tags: [["salary ≥ 49000"], ["UK group"]], tagRules: {}, groups: { "UK group": "Kentucky" } }; bankShareMemo = null; delete state.ckBase;
    const nb = baseBank() === null && /^\(whole bank: no base yet\) bank share/.test(checksMap()[pid].boxes.find(x => x.k === "bank/field").v);
    const words = [isBaseTag("x"), (BANK.groups["baseline idea"] = "baseline", isBaseTag("baseline idea")), (BANK.groups["Q L0 U0"] = "Base", isBaseTag("Q L0 U0")), (BANK.groups["Q L0.2 U0"] = "Base", isBaseTag("Q L0.2 U0")), isBaseTag("BASE + no McIver")];
    BANK = B0; bankShareMemo = null; if (cb0) state.ckBase = cb0; else delete state.ckBase; save(); renderPlayers();
    return { auto, shareOk, hover, c6: c6.v, frozen, foldOk, fold, picked, refrozen, colOk, colBack, nb, words };
  });
  check("checks box 6 reads the base bank: tags or ideas named base (a whole word, any case), of Draw the 9 only L0 U0; each player's share of those lineups; hover 'base bank share x% vs field y%'",
        JSON.stringify(cb6.auto) === JSON.stringify(["X L0 U0", "no rules"]) && cb6.shareOk && cb6.hover && JSON.stringify(cb6.words) === JSON.stringify([false, false, true, false, true]), JSON.stringify(cb6));
  check("checks base: frozen once found (a later base batch doesn't move it); the Boxes fold names its tags; a hand pick recomputes; Refreeze takes the match as it is; no base: the whole bank, labelled",
        cb6.frozen && cb6.foldOk && cb6.picked && cb6.refrozen && cb6.nb, JSON.stringify(cb6));
  check("Bank column: whole bank by default, a base toggle beside its header shows the base bank's share (hover says so) without sorting",
        cb6.colOk && cb6.colBack, JSON.stringify(cb6));
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
  check("fill step: one set of buttons (Fill all contests, Auto-fill the rest, Undo fill, Swap one in, New nights, Export DK entries, Save build, Load build), Variants only in Cut, Clear bank only in Bank, the settings one line, no side pane",
        fb.ids.length === 0 && JSON.stringify(fb.buttons) === JSON.stringify(["Fill all contests", "Export DK entries", "Save build", "Auto-fill the rest", "Undo fill", "Swap one in", "New nights", "Load build"]) && fb.clear === "stepBank" &&
        fb.varIn === "stepCut" && fb.folded && /^Fill: contest 60% · night 60% · unique 3 · core 15% · max 3 contests · locks: draws only · Max ROI · \d+ nights( · fill short off)?$/.test(fb.sum) &&
        ["Here", "Tonight", "Room"].every(h => fb.heads.includes(h)), JSON.stringify(fb));
  // the Fill tab cleanup (2026-11-24): settings and profiles behind red / green buttons (Confirm inside, a change turns them red), the top-up renamed, three buttons and a More fold
  const fc4 = await pg.evaluate(() => {
    const st0 = { f: state.cfgFill, p: state.cfgProf }, mx0 = $("maxExpo").value; delete state.cfgFill; delete state.cfgProf; cfgRender();
    const red0 = !$("fillSetChip").classList.contains("ok") && !$("profChip").classList.contains("ok") && getComputedStyle($("fillSetChip")).backgroundColor !== getComputedStyle($("fillSetChip").parentElement).backgroundColor;
    $("fillSetOk").click(); const fOk = $("fillSetChip").classList.contains("ok") && store(key()).cfgFill === fillSig() && !$("fillSet").open;
    $("maxExpo").value = "55"; $("maxExpo").dispatchEvent(new Event("input", { bubbles: true })); const fRed = !$("fillSetChip").classList.contains("ok");
    $("maxExpo").value = mx0; $("maxExpo").dispatchEvent(new Event("input", { bubbles: true })); const fBack = $("fillSetChip").classList.contains("ok");
    $("profOk").click(); const pOk = $("profChip").classList.contains("ok") && store(key()).cfgProf === profSig();
    const sel = document.querySelector("#profList select[data-cid]"); let pRed = null;
    if (sel) { const v0 = sel.value; sel.value = [...sel.options].map(o => o.value).find(v => v && v !== profileOf(nbContests().find(x => String(x.c.id) === sel.dataset.cid).c)); sel.dispatchEvent(new Event("change", { bubbles: true }));
      pRed = !$("profChip").classList.contains("ok"); const s2 = document.querySelector('#profList select[data-cid="' + sel.dataset.cid + '"]'); s2.value = v0; s2.dispatchEvent(new Event("change", { bubbles: true })); }
    const label = document.getElementById("autoTopUp").closest("label").textContent.trim(), hint = /Fill short contests: when a fill still leaves seats open/.test($("fillSet").textContent);
    const vis = [...document.querySelectorAll("#fillButtons > button")].map(b => b.textContent), more = [...document.querySelectorAll("#fillMore .fmore > div")].map(d => d.querySelector("button").textContent + "|" + !!d.querySelector(".mut"));
    state.cfgFill = st0.f; state.cfgProf = st0.p; if (st0.f == null) delete state.cfgFill; if (st0.p == null) delete state.cfgProf; save(); cfgRender();
    return { red0, fOk, fRed, fBack, pOk, pRed, label, hint, vis, more, profOpen: $("profBox").open };
  });
  check("fill tab: Fill settings and Contest profiles behind one button each, red until confirmed for the slate, green after; a change turns them red again (and back on undoing it)",
        fc4.red0 && fc4.fOk && fc4.fRed && fc4.fBack && fc4.pOk && fc4.pRed !== false, JSON.stringify(fc4));
  check("fill tab: Auto top-up reads 'Fill short contests (break caps least)' with a one-line hint; Fill all contests, Export DK entries and Save build visible, the rest in More with a line each",
        fc4.label === "Fill short contests (break caps least)" && fc4.hint && JSON.stringify(fc4.vis) === JSON.stringify(["Fill all contests", "Export DK entries", "Save build"]) &&
        fc4.more.length === 6 && fc4.more.every(x => /\|true$/.test(x)), JSON.stringify(fc4));
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
  check("one screen: the live summary, this contest and tonight (ROI, top 10%, top 1%, cash), and the top tenth by sim value", /Tonight: \d+ entr/.test(nb_sum1) && /ROI/.test(nb_sum1) && /top 10%/.test(nb_sum1) && /top 1%/.test(nb_sum1) && /cash/.test(nb_sum1) && /Top tenth by sim value: \d+ lineup/.test(nb_sum1), nb_sum1);
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
  // guided fill: Next best pinned on top (the unpicked, unfiltered lineup adding the most under every cap) with its computed
  // reason; one tap adds it, the list re-scores and the next appears; the header: filled / total, ROI, top 1%, cash and the
  // core players against their caps here and tonight; Finish for me fills the rest
  const pf0 = await pg.evaluate(() => JSON.stringify(PF));      // put back after the guided fill and swap tests
  const mn1 = await pg.evaluate(() => { const v = [$("maxNight").value, $("maxExpo").value]; $("maxNight").value = ""; $("maxExpo").value = "100"; review(BP.review); return v; });   // the fixture's 7 entries leave little under the caps
  const gd = await pg.evaluate(() => {
    while (BP.b.picked.length >= BP.o.n - 1 && BP.b.picked.length) { BP.b.remove(BP.b.picked[BP.b.picked.length - 1]); bpRescore(); bpCommit(); }
    bpRender();
    const want = (() => { let best = -1; for (let k = 0; k < BP.pool.length; k++) { if (BP.b.picked.includes(k) || bpHidden(k) || !BP.scores[k] || bpBlocks(k).length) continue; if (best < 0 || BP.scores[k].value > BP.scores[best].value) best = k; } return best; })();
    const g = document.getElementById("nbGuide"), btn = g && g.querySelector(".nbNext .bpAdd"), why = g && g.querySelector(".nbWhy"), top = document.getElementById("nbList").firstElementChild === g;
    const k = btn ? +btn.dataset.k : null, before = BP.b.picked.length, sum = document.getElementById("nbSum").textContent, core = document.getElementById("nbCore");
    const capRow = g && g.querySelector(".nbCapped"), capOk = !capRow || /capped: .+ at (the night cap )?\d+%|capped: (Min unique \d|Max core \d+%)/.test(capRow.textContent);
    btn && btn.click();
    const g2 = document.getElementById("nbGuide"), k2 = g2.querySelector(".nbNext .bpAdd") ? +g2.querySelector(".nbNext .bpAdd").dataset.k : null;
    return { want, k, top, why: why && why.textContent, before, after: BP.b.picked.length, inPF: PF[BP.review].includes(BP.idx[k]), k2, sum, n: BP.o.n,
             core: core && core.textContent, nightOn: nightLimit() < Infinity, capOk };
  });
  check("guided fill: Next best pinned atop the list is the lineup adding the most under every cap, with its reason (+$ added: top 1% on nights your set misses (no <most-held player>)); one tap adds it and the next appears",
        gd.top && gd.k === gd.want && /^\+\$[\d,]+\.\d\d added(: (top 1% on|cashes on) \d+\.\d% of nights your set (misses|doesn't))?( \(no [^)]+\))?$/.test(gd.why) &&
        gd.after === gd.before + 1 && gd.inPF && gd.k2 != null && gd.k2 !== gd.k && gd.capOk, JSON.stringify(gd));
  check("guided fill: the header shows filled / total, ROI, top 1% and cash, and the core players' exposure against their caps (contest and night)",
        new RegExp(gd.before + "/" + gd.n + " filled · ROI .+ top 1% .+ cash").test(gd.sum) && /^core: [^,]+ \d+\/\d+( \(night \d+\/\d+\))?(, [^,]+ \d+\/\d+( \(night \d+\/\d+\))?)*$/.test(gd.core) && (!gd.nightOn || /\(night \d+\/\d+\)/.test(gd.core)), JSON.stringify(gd));
  await pg.evaluate(() => { document.getElementById("autoTopUp").checked = true; });
  await pg.click("#nbGuide .nbFinish");
  await pg.waitForFunction(() => BP.b.picked.length >= BP.o.n || /stopped at/.test(document.getElementById("bpStatus").textContent), null, { timeout: 120000 });
  const fin = await pg.evaluate(() => { const r = { n: BP.b.picked.length, of: BP.o.n, pf: PF[BP.review].length, full: /Set full/.test(document.getElementById("nbGuide").textContent) };
    document.getElementById("autoTopUp").checked = false; return r; });
  await pg.evaluate(([v, p]) => { $("maxNight").value = v[0]; $("maxExpo").value = v[1]; PF = JSON.parse(p); pfSave(); renderEntries(); review(BP.review); }, [mn1, pf0]);
  check("guided fill: Finish for me fills the rest (Auto-fill, then Auto top-up), and the guide says the set is full", fin.n === fin.of && fin.pf === fin.of && fin.full, JSON.stringify(fin));
  // Swap one in: the rule (template 5, +set) on tonight's most-held player, put at the night cap, so bringing him in
  // breaks it. Off: no swap leaves a contest over a cap it wasn't over (contest, night, Min unique, Max contests per
  // lineup); Break cap: the swaps that break one name it. Apply puts the lineup in; Undo restores the exact portfolios.
  const swp = await pg.evaluate(async () => {
    const used = nightUsed(null), hot = Object.keys(used).sort((a, b) => used[b] - used[a])[0], mn0 = $("maxNight").value;
    $("maxNight").value = "";            // first pass: the night cap off (the fixture's 7 entries leave it binding everywhere); contest, Min unique, uses, core on
    const type0 = $("rtType").value, sel0 = [...$("rtList").selectedOptions].map(o => o.value), inKept = {};
    finalIdx().forEach(bi => BANK.lineups[bi].ids.forEach(id => { inKept[id] = (inKept[id] || 0) + 1; }));
    const roomy = Object.keys(inKept).filter(id => id !== hot).sort((a, b) => inKept[b] - inKept[a])[0];   // in the most kept lineups
    [...$("rtList").options].forEach(o => { o.selected = false; }); rtSet([roomy], 1);
    const viol = (pf) => {         // every player / lineup past a cap in a set of portfolios: "kind:cid:key" -> how far
      const v = {}, nu = {}, uses = {}, nl = nightLimit(), mu = maxUses(), minU = Math.max(1, +$("minUnique").value || 1);
      Object.keys(pf).forEach(cid => pf[cid].forEach(bi => { uses[bi] = (uses[bi] || 0) + 1; BANK.lineups[bi].ids.forEach(id => { nu[id] = (nu[id] || 0) + 1; }); }));
      Object.keys(nu).forEach(id => { if (nu[id] > nl) v["night::" + id] = nu[id] - nl; });
      Object.keys(uses).forEach(bi => { if (uses[bi] > mu) v["uses::" + bi] = uses[bi] - mu; });
      nbContests().forEach(x => { const cid = String(x.c.id), c = {}, L = pf[cid] || [], o = pickRules(x.n);
        L.forEach(bi => BANK.lineups[bi].ids.forEach(id => { c[id] = (c[id] || 0) + 1; }));
        Object.keys(c).forEach(id => { const lim = DKSim.expoLimit(Math.min(o.maxExpo, state.cap[id] != null && state.cap[id] !== "" ? +state.cap[id] / 100 : 1), x.n); if (c[id] > lim) v["contest:" + cid + ":" + id] = c[id] - lim; });
        L.forEach((a, i) => L.forEach((b, j) => { if (j > i && BANK.lineups[a].ids.filter(id => BANK.lineups[b].ids.includes(id)).length > 8 - minU) v["unique:" + cid + ":" + a + "|" + b] = 1; }));
      });
      return v;
    };
    const after = s => { const pf = JSON.parse(JSON.stringify(PF)); pf[s.cid] = s.out == null ? (pf[s.cid] || []).concat([s.inn]) : pf[s.cid].map(bi => bi === s.out ? s.inn : bi); return pf; };
    const worse = s => { const v0 = viol(PF), v1 = viol(after(s)); return Object.keys(v1).filter(k => v1[k] > (v0[k] || 0)); };
    document.getElementById("swinOpen").click();
    for (let t = 0; t < 600 && SWIN.list == null && !/Set the rule|No kept|No swap|failed/.test($("swinBox").textContent); t++) await new Promise(r => setTimeout(r, 100));
    const off = (SWIN.list || []).map(s => ({ brk: s.brk.length, worse: worse(s), hasHot: BANK.lineups[s.inn].ids.includes(hot), outHot: s.out != null && BANK.lineups[s.out].ids.includes(hot) }));
    const rowsOff = document.querySelectorAll("#swinBox .swr").length, boldHot = [...document.querySelectorAll("#swinBox .swr b")].some(b => b.textContent === shortName(byId(roomy).name));
    $("maxNight").value = String(Math.max(1, Math.floor(100 * used[hot] / nightEntries())));     // second pass: tonight's most-held player at the night cap
    const offHot = (await (async () => { [...$("rtList").options].forEach(o => { o.selected = false; }); rtSet([hot], 1); await swinFind();     // the at-cap player, Break cap off
      return (SWIN.list || []).map(s => ({ brk: s.brk.length, worse: worse(s), hasHot: BANK.lineups[s.inn].ids.includes(hot), outHot: s.out != null && BANK.lineups[s.out].ids.includes(hot) })); })());
    document.getElementById("swinBreak").click();       // Break cap on: re-runs
    for (let t = 0; t < 600 && !(SWIN.brk && SWIN.list != null) && !/No swap|failed/.test($("swinBox").textContent); t++) await new Promise(r => setTimeout(r, 100));
    const on = (SWIN.list || []).map(s => ({ brk: s.brk, worse: worse(s).length, outHot: s.out != null && BANK.lineups[s.out].ids.includes(hot) }));
    const named = on.filter(s => !s.outHot).every(s => s.brk.some(b => b === shortName(byId(hot).name) + " night " + $("maxNight").value + "%"));
    const shown = [...document.querySelectorAll("#swinBox .swr")].map(x => x.textContent);
    // apply the first, then undo
    const snap = JSON.stringify(PF), s0 = SWIN.list && SWIN.list[0];
    document.querySelector("#swinBox .swinApply") && document.querySelector("#swinBox .swinApply").click();
    const applied = !!s0 && PF[s0.cid].includes(s0.inn) && (s0.out == null || !PF[s0.cid].includes(s0.out)) && JSON.stringify(PF) !== snap && !document.getElementById("swinUndo").disabled;
    const stored = !!s0 && JSON.stringify(store("dkcbb-pf:" + slate.draft_group_id)) === JSON.stringify(PF);
    document.getElementById("swinUndo").click();
    const back = JSON.stringify(PF) === snap && JSON.stringify(store("dkcbb-pf:" + slate.draft_group_id)) === snap && document.getElementById("swinUndo").disabled;
    SWIN.brk = false; $("maxNight").value = mn0;
    [...$("rtList").options].forEach(o => { o.selected = sel0.includes(o.value); }); $("rtType").value = type0; rtChips();
    return { box: $("swinBox").textContent.slice(0, 300), hot: shortName(byId(hot).name), roomy: shortName(byId(roomy).name), off, offHot, rowsOff, boldHot, on: on.length, named, shown: shown.slice(0, 2), applied, stored, back, rule: SWIN.rule && SWIN.rule.label };
  });
  check("swap one in: with Break cap off, the best (up to 5) swaps across the night, none leaving a contest over a cap it wasn't over (contest, night, Min unique, Max contests per lineup); the at-cap player comes in only by taking him out; the rule's players in bold",
        swp.off.length > 0 && swp.off.concat(swp.offHot).every(x => x.brk === 0 && x.worse.length === 0) && swp.offHot.every(x => !x.hasHot || x.outHot) &&
        swp.rowsOff === swp.off.length && swp.rowsOff <= 5 && swp.boldHot, JSON.stringify(swp));
  check("swap one in: Break cap lists the swaps that break one, each naming the cap (\"<player> night <n>%\"), with EV and ROI change",
        swp.on > 0 && swp.named && swp.shown.every(t => /→ .+ · EV [+-]\$[\d,]+\.\d\d/.test(t)), JSON.stringify(swp));
  check("swap one in: Apply puts the lineup in (saved), Undo restores the exact portfolios", swp.applied && swp.stored && swp.back, JSON.stringify(swp));
  check("swap one in keeps clear of Late swap: one #swapBox (in the Swap step), Late swap's SWAP state intact",
        await pg.evaluate(() => document.querySelectorAll("#swapBox").length === 1 && !!document.getElementById("swapBox").closest("#stepSwap") &&
          Array.isArray(SWAP.stand) && "use" in SWAP && !("brk" in SWAP) && !!document.getElementById("swinBox").closest("#stepFill")));
  await pg.evaluate(p => { PF = JSON.parse(p); pfSave(); renderEntries(); review(BP.review); }, pf0);
  // the Cut tab's Players list (2026-11-24): Own / Bank / Cut (▲▼ at 5+ points off Bank) / Δ own, no Min, every column sorts, Cut high to low by default; the Bank tab's list untouched
  const ctl = await pg.evaluate(() => {
    const step0 = stepNow(), cs0 = view.cutSort, cd0 = view.cutDir; delete view.cutSort; delete view.cutDir;
    showStep("bank"); renderPlayers(); const bankHeads = [...document.querySelectorAll("#players .head span[data-sort]")].map(x => x.firstChild.textContent.replace(/ [↓↑]$/, ""));
    showStep("cut"); const p = document.getElementById("players");
    const heads = [...p.querySelectorAll(".head span[data-sort]")].map(x => x.firstChild.textContent.replace(/ [↓↑]$/, "")), kc = cutKeptShare(), bk = bankShare();
    const rowsC = [...p.querySelectorAll(".row")].map(e => byId(e.dataset.id)).filter(r => r.status !== "Out");
    const sorted = rowsC.every((r, i) => i === 0 || (kc[rowsC[i - 1].id] || 0) >= (kc[r.id] || 0) - 1e-12);
    const cellsOk = [...p.querySelectorAll(".row")].slice(0, 40).every(e => { const r = byId(e.dataset.id), c = kc[r.id] || 0, d = Math.round(100 * c - own(r)), cut = e.querySelector(".col-cut"), dn = e.querySelector(".col-down");
      const arrow = Math.abs(c - (bk[r.id] || 0)) >= 0.05 ? (c > (bk[r.id] || 0) ? "▲" : "▼") : "";
      return cut.textContent === Math.round(100 * c) + "%" + arrow && dn.textContent === (d > 0 ? "+" : "") + d && dn.classList.contains("up") === (d > 0) && dn.classList.contains("dn") === (d < 0) && !e.querySelector(".col-min"); });
    const arrows = [...p.querySelectorAll(".row .col-cut .ar")].length;
    p.querySelector('.head [data-sort="down"]').click();
    const dsorted = (() => { const r2 = [...p.querySelectorAll(".row")].map(e => byId(e.dataset.id)).filter(r => r.status !== "Out"); return r2.every((r, i) => i === 0 || 100 * (kc[r2[i - 1].id] || 0) - own(r2[i - 1]) >= 100 * (kc[r.id] || 0) - own(r) - 1e-9); })();
    p.querySelector('.head [data-sort="maxp"]').click(); const maxSorts = view.cutSort === "maxp";
    const bankSort = view.sort;
    const fits = [...p.querySelectorAll(".row")][0].getBoundingClientRect().width <= p.getBoundingClientRect().width + 1 || getComputedStyle(p).overflowX === "auto";
    view.cutSort = cs0; view.cutDir = cd0; if (cs0 == null) delete view.cutSort; if (cd0 == null) delete view.cutDir;
    showStep("bank"); const bankAfter = [...document.querySelectorAll("#players .head span[data-sort]")].map(x => x.firstChild.textContent.replace(/ [↓↑]$/, ""));
    showStep(step0); renderPlayers();
    return { bankHeads, heads, sorted, cellsOk, arrows, dsorted, maxSorts, bankSort, bankAfter, fits };
  });
  check("Cut tab Players list: Own, Bank, Cut (▲/▼ at 5+ points off Bank), Δ own (green / red), no Min; Cut high to low by default; Δ own and Min% / Max% sort; the Bank tab's list unchanged",
        ctl.heads.join("|") === "Player|Pos|Team|Opp|Sal|Proj|Val|Own|Bank|Cut|Δ own|MPG|OBPR|DK avg|Cash|Read|Min%|Max%" && ctl.sorted && ctl.cellsOk && ctl.dsorted && ctl.maxSorts &&
        ctl.bankHeads.includes("Min") && !ctl.bankHeads.includes("Cut") && JSON.stringify(ctl.bankHeads) === JSON.stringify(ctl.bankAfter) && ctl.fits, JSON.stringify(ctl));
  // fill against the cut, on the Fill tab (2026-11-24, moved from the Cut tables): the contest table, its expanded row's lineups and flags, the scorecard scoped to it, a flagged row into Swap one in; the Cut tables as before
  const fc = await pg.evaluate(async () => {
    const pfSnap = JSON.stringify(PF), mn0 = $("maxNight").value, cs = nbContests(), cid = String(BP.review), open0 = view.ftOpen, step0 = stepNow();
    showStep("fill"); view.ftOpen = null;
    const cutHeads = () => ({ idea: [...document.querySelectorAll("#ideaTable th")].map(t => t.textContent.replace(/ [↓↑]$/, "").replace(/ \(i\)$/, "")), pl: [...document.querySelectorAll("#cutShares table th")].map(t => t.textContent), toggle: !!document.querySelector(".fcscope") });
    // no entries: no scorecard; the Cut tables as before
    PF = {}; pfSave(); renderCut(); const none = { card: !!document.getElementById("fcIdeaTable"), cut: cutHeads() };
    // a hand-built set: this contest takes the biggest idea's kept lineups only (8), another contest 4 of the rest
    const kc = ideaCounts(CUT.keep), big = Object.keys(kc).sort((a, b) => kc[b] - kc[a])[0];
    const mine = CUT.keep.filter(bi => lineupGroups(bi).includes(big)).slice(0, 8), rest = CUT.keep.filter(bi => !lineupGroups(bi).includes(big)).slice(0, 4);
    const other = cs.map(x => String(x.c.id)).find(c => c !== cid);
    PF = { [cid]: mine }; if (other) PF[other] = rest; pfSave(); renderCut();
    const cutWith = cutHeads();
    // the contest table: a row a contest, ours / entries and the fill status
    const ct = [...document.querySelectorAll("#fillContests tr[data-ftc]")].map(tr => ({ cid: tr.dataset.ftc, ours: tr.cells[1].textContent, fill: tr.cells[7].textContent }));
    const ctOk = ct.length === cs.length && cs.every(x => { const r = ct.find(y => y.cid === String(x.c.id)), h = (PF[String(x.c.id)] || []).length; return r && r.ours === h + "/" + x.n && (h ? (h >= x.n ? /^full/.test(r.fill) : r.fill === "short " + (x.n - h)) : r.fill === "empty"); });
    const ents = mine.concat(other ? rest : []), E = ents.length, ec = ideaCounts(ents), st = fcIdeaStats();
    const row = [...document.querySelectorAll("#fcIdeaTable tr[data-idea]")].find(tr => tr.dataset.idea === big), cells = row ? [...row.cells].map(c => c.textContent) : [];
    const ks = kc[big] / CUT.keep.length, want = { ent: ec[big] + " (" + Math.round(100 * ec[big] / E) + "%)", vs: (Math.round(100 * (ec[big] / E - ks)) > 0 ? "+" : "") + Math.round(100 * (ec[big] / E - ks)) };
    const entOk = st.E === E && st.by[big].ent === ec[big] && cells[1] === Math.round(100 * ks) + "%" && cells[2] === want.ent && cells[3] === want.vs && cells[4] === (fcFlag(ec[big], ks, E) || "") &&
      /Whole night · \d+ entries/.test(document.querySelector("#fillTable .ftscope").textContent);
    // the flag rule: 5+ points AND 2+ entries off expected (both edges inclusive)
    const flags = [fcFlag(3, 0.5, 10), fcFlag(4, 0.5, 10), fcFlag(18, 0.1, 20), fcFlag(2, 0.06, 100), fcFlag(3, 0.125, 40), fcFlag(7, 0.125, 40), fcFlag(6, 0.125, 40)];
    // expanding a contest row: its lineups inline, the scorecard scoped to it (the label says so), collapsing goes back to the night
    document.querySelector(`#fillContests tr[data-ftc="${cid}"]`).click();
    const exp = { lineups: document.querySelectorAll("#fillTable .ftx .ftl").length, E: fcIdeaStats().E, scope: document.querySelector("#fillTable .ftscope").textContent, builder: !!document.querySelector("#fillTable .ftx .ftBuild") };
    document.querySelector(`#fillContests tr[data-ftc="${cid}"]`).click();
    const back = fcIdeaStats().E === E && /Whole night/.test(document.querySelector("#fillTable .ftscope").textContent);
    // a player at the night cap: Why "night cap" on his light row
    const pk = {}; CUT.keep.forEach(bi => BANK.lineups[bi].ids.forEach(id => { pk[id] = (pk[id] || 0) + 1; }));
    const P = Object.keys(pk).sort((a, b) => pk[b] - pk[a])[0], withP = CUT.keep.filter(bi => BANK.lineups[bi].ids.includes(P)), noP = CUT.keep.filter(bi => !BANK.lineups[bi].ids.includes(P));
    PF = { [cid]: [withP[0]].concat(noP.slice(0, 9)) }; $("maxNight").value = "1"; pfSave();
    const prow = document.querySelector(`#fcPlayerTable tr[data-id="${P}"]`), pc = prow ? [...prow.cells].map(c => c.textContent) : [];
    const capWhy = fcPlayerWhy(P), capOk = capWhy === "night cap" && prow && prow.dataset.flag === "light" && pc[pc.length - 1] === "night cap";
    const absSorted = (() => { const v = [...document.querySelectorAll("#fcPlayerTable tr[data-id]")].map(tr => Math.abs(parseFloat(tr.cells[3].textContent))); return v.every((x, i) => i === 0 || v[i - 1] >= x); })();
    $("maxNight").value = mn0;
    // a light idea row: Swap one in on that idea's kept lineups, the swap-out the weakest entry of the heaviest idea, within the caps
    const tgt = Object.keys(kc).sort((a, b) => kc[b] - kc[a]).find(g => CUT.keep.filter(bi => !lineupGroups(bi).includes(g)).length >= 8);
    PF = { [cid]: CUT.keep.filter(bi => !lineupGroups(bi).includes(tgt)).slice(0, Math.max(8, cs.find(x => String(x.c.id) === cid).n)) }; pfSave();
    const lightRow = document.querySelector('#fcIdeaTable tr[data-flag="light"]');
    let swap = null;
    if (lightRow) {
      const g = lightRow.dataset.idea, val = fcVal(), heavyIdea = fcIdeaStats().list.filter(x => x.flag === "heavy").sort((a, b) => b.vs - a.vs)[0];
      lightRow.click();
      for (let t = 0; t < 600 && SWIN.list == null && !/Nothing|failed/.test($("swinBox").textContent); t++) await new Promise(r => setTimeout(r, 100));
      const nu = {}; Object.keys(PF).forEach(c => PF[c].forEach(bi => BANK.lineups[bi].ids.forEach(id => { nu[id] = (nu[id] || 0) + 1; })));
      const L = SWIN.list || [], out = SWIN.ctx && SWIN.ctx.out;
      const uniqE = Object.keys(PF).reduce((a, c) => a.concat(PF[c]), []).filter((b, i, a) => a.indexOf(b) === i);
      const weakOk = out == null || (heavyIdea ? lineupGroups(out).includes(heavyIdea.idea) : true) && uniqE.filter(bi => !lineupGroups(bi).includes(g) && (!heavyIdea || lineupGroups(bi).includes(heavyIdea.idea))).every(bi => (val[bi] || 0) >= (val[out] || 0));
      const inOk = L.every(s => lineupGroups(s.inn).includes(g) && s.out === out && s.brk.length === 0);
      const capsOk = L.every(s => { const pf = JSON.parse(JSON.stringify(PF)); pf[s.cid] = pf[s.cid].map(bi => bi === s.out ? s.inn : bi); const o = pickRules(cs.find(x => String(x.c.id) === s.cid).n), c = {};
        pf[s.cid].forEach(bi => BANK.lineups[bi].ids.forEach(id => { c[id] = (c[id] || 0) + 1; }));
        const nb = {}; Object.keys(pf).forEach(k => pf[k].forEach(bi => BANK.lineups[bi].ids.forEach(id => { nb[id] = (nb[id] || 0) + 1; })));
        return Object.keys(c).every(id => c[id] <= DKSim.expoLimit(Math.min(o.maxExpo, state.cap[id] != null && state.cap[id] !== "" ? +state.cap[id] / 100 : 1), o.n) || c[id] <= (PF[s.cid].filter(bi => BANK.lineups[bi].ids.includes(id)).length)) &&
          Object.keys(nb).every(id => nightLimit() === Infinity || nb[id] <= nightLimit() || nb[id] <= (nu[id] || 0)); });
      const box = $("swinBox").textContent;
      let applied = null;
      if (L.length) { const before = fcIdeaStats().by[g].ent; document.querySelector("#swinBox .swinApply").click(); applied = fcIdeaStats().by[g].ent > before && [...document.querySelectorAll("#fcIdeaTable tr[data-idea]")].some(tr => tr.dataset.idea === g) &&
        document.querySelector(`#fillContests tr[data-ftc="${L[0].cid}"]`) != null; document.getElementById("swinUndo").click(); }
      swap = { g, n: L.length, weakOk, inOk, capsOk, applied, msg: L.length ? "" : box.slice(0, 160), label: SWIN.ctx && SWIN.ctx.label };
    }
    PF = JSON.parse(pfSnap); view.ftOpen = open0; save(); pfSave(); renderEntries(); review(BP.review); renderCut(); $("swinBox").hidden = true; SWIN.ctx = null; showStep(step0);
    return { none, cutWith, ct, ctOk, entOk, want, flags, exp, back, capWhy, capOk, absSorted, swap, big, mineN: mine.length };
  });
  const cutWas = "Idea|Banked|Shared|Kept|Share|Top tenth|Sim ROI|Top 10%|Top 1%|Cash|Avg own|Cores", plWas = "Player|Sal|Field own|Bank|Kept|Change";
  check("fill against the cut moved to the Fill tab: the Cut step's idea table and Players: bank against the cut are exactly as before, with or without entries (no Entered / vs cut / Flag / Why, no scope toggle)",
        fc.none.cut.idea.join("|") === cutWas && fc.cutWith.idea.join("|") === cutWas && fc.none.cut.pl.join("|") === plWas && fc.cutWith.pl.join("|") === plWas && !fc.cutWith.toggle && !fc.none.card, JSON.stringify(fc));
  check("fill tab contest table: a row a contest with ours / entries and the fill status (full / short N / empty)", fc.ctOk, JSON.stringify(fc.ct));
  check("fill tab scorecard: ideas against the cut (Kept, Entered with its share, vs cut, Flag) match a hand-built set, whole night with no contest expanded",
        fc.entOk, JSON.stringify(fc));
  check("fill against the cut: the flag needs 5+ points AND 2+ entries off expected (light under, heavy over, both edges inclusive)",
        JSON.stringify(fc.flags) === JSON.stringify(["light", "", "heavy", "", "light", "heavy", ""]), JSON.stringify(fc.flags));
  check("fill tab: expanding a contest row shows its entered lineups inline (and Open in builder), scopes the scorecard to it with its name; collapsing goes back to the whole night",
        fc.exp.lineups === fc.mineN && fc.exp.E === fc.mineN && !/Whole night/.test(fc.exp.scope) && fc.exp.builder && fc.back, JSON.stringify(fc.exp));
  check("fill tab scorecard: a light player held by the night cap says so (Why: night cap); players sorted by |vs cut|", fc.capOk && fc.absSorted, JSON.stringify(fc));
  check("fill tab scorecard: a light idea row opens Swap one in on that idea's kept lineups, the swap-out the weakest entry of the heaviest idea, every swap within the caps (or one line saying what blocks); Apply moves the scorecard and the contest table",
        !!fc.swap && (fc.swap.n > 0 ? fc.swap.weakOk && fc.swap.inOk && fc.swap.capsOk && fc.swap.applied : /^.*(Nothing fits: |Nothing to swap)/.test(fc.swap.msg)), JSON.stringify(fc.swap));
  // remove part of the bank (2026-11-24): an idea's Remove / a fold's Remove ticked; a lineup goes only when all its tags go; entries and the cut remapped, the cut stale
  dialogs = [];
  const rmv = await pg.evaluate(() => {
    const snap = JSON.stringify({ B: BANK, C: CUT, P: PF }), n0 = BANK.lineups.length, step0 = stepNow();
    showStep("bank");
    const ui = { rm: document.querySelectorAll("#bankBox button[data-rmgroup]").length, rows: document.querySelectorAll("#bankBox button[data-test]").length,
                 ticked: [...document.querySelectorAll("#bankBox details[data-fold-group] .rmTicked")].length, folds: document.querySelectorAll("#bankBox details[data-fold-group]").length };
    const cnt = {}; BANK.tags.forEach(ts => ts.forEach(t => { cnt[t] = (cnt[t] || 0) + 1; }));
    const T1 = Object.keys(cnt).filter(t => cnt[t] >= 3).sort((a, b) => cnt[a] - cnt[b])[0];
    const mine = BANK.tags.map((ts, i) => ts.includes(T1) ? i : -1).filter(i => i >= 0), other = Object.keys(cnt).find(t => t !== T1);
    const shared = mine[0]; BANK.tags[shared] = BANK.tags[shared].concat([other]);          // drawn under T1 and another: stays
    const goneIdx = mine.filter(i => BANK.tags[i].every(t => t === T1)), sharedIds = BANK.lineups[shared].ids.join(",");
    const cid = Object.keys(PF).find(k => PF[k].length) || String(nbContests()[0].c.id);
    PF[cid] = [goneIdx[0]].concat((PF[cid] || []).filter(bi => !goneIdx.includes(bi)).slice(0, 3));
    const keptIds = CUT && CUT.keep ? CUT.keep.filter(bi => !goneIdx.includes(bi)).map(bi => BANK.lineups[bi].ids.join(",")) : [];
    const entIds = Object.keys(PF).reduce((a, k) => a.concat(PF[k].filter(bi => !goneIdx.includes(bi)).map(bi => k + ":" + BANK.lineups[bi].ids.join(","))), []).sort();
    const entGone = Object.keys(PF).reduce((t, k) => t + PF[k].filter(bi => goneIdx.includes(bi)).length, 0);
    bankRemoveAsk([T1]);
    const after = { n: BANK.lineups.length, sharedKept: BANK.lineups.some((L, i) => L.ids.join(",") === sharedIds && !BANK.tags[i].includes(T1) && BANK.tags[i].includes(other)),
      noT1: !BANK.tags.some(ts => ts.includes(T1)), pfValid: Object.keys(PF).every(k => PF[k].every(bi => BANK.lineups[bi])),
      ents: Object.keys(PF).reduce((a, k) => a.concat(PF[k].map(bi => k + ":" + BANK.lineups[bi].ids.join(","))), []).sort(),
      keep: CUT && CUT.keep ? CUT.keep.map(bi => BANK.lineups[bi].ids.join(",")) : [], vals: CUT && CUT.board && CUT.board.values ? CUT.board.values.length : null,
      stale: !!(CUT && CUT.stale), note: !!document.getElementById("cutStale") || (showStep("cut"), !!document.getElementById("cutStale")), msg: $("cutStatus").textContent };
    BANK = JSON.parse(snap).B; CUT = JSON.parse(snap).C; PF = JSON.parse(snap).P; bankSaveState(); cutSave(); pfSave(); renderBank(); renderEntries(); review(BP && BP.review || cid); showStep(step0);
    return { ui, T1, gone: goneIdx.length, n0, entGone, after, keptSame: JSON.stringify(after.keep) === JSON.stringify(keptIds), entSame: JSON.stringify(after.ents) === JSON.stringify(entIds) };
  });
  check("remove part of the bank: each idea row has Remove, each tags fold Remove ticked; one confirm with the counts and the entries among them",
        rmv.ui.rm === rmv.ui.rows && rmv.ui.rm > 0 && rmv.ui.ticked === rmv.ui.folds && dialogs.length === 1 &&
        new RegExp("^Remove 1 tag, " + rmv.gone + " lineups\\? " + rmv.entGone + " of your contest entr").test(dialogs[0]) && /The cut will need re-running/.test(dialogs[0]), JSON.stringify([rmv, dialogs]));
  check("remove part of the bank: a lineup goes only when every tag it carries is removed (one also drawn under a kept tag stays, without the removed tag); entries out of the portfolios, the rest and the kept pool remapped exactly; the cut marked stale",
        rmv.after.n === rmv.n0 - rmv.gone && rmv.after.sharedKept && rmv.after.noT1 && rmv.after.pfValid && rmv.entSame && rmv.keptSame && rmv.after.vals === rmv.after.keep.length &&
        rmv.after.stale && rmv.after.note && /Removed \d+ of [\d,]+ lineups \(1 tag\), \d+ entr(y|ies) out of the portfolios\. The cut is stale/.test(rmv.after.msg), JSON.stringify(rmv));
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
    const L0 = state.lock, X0 = state.excl, wait = async () => { for (let t = 0; t < 6000 && document.getElementById("quickRun").disabled; t++) await new Promise(r => setTimeout(r, 30)); };
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
    const sim = { opts, simRows, roiOrder, allLocked, tapped, topA: q && q.tier[q.order[0]] === "A", distinct: q && new Set(q.L.map(L => L.ids.slice().sort().join())).size, contest: q && q.c.id, drawn: q && q.drawn, rounds: q && q.rounds, allN: q && q.allN, RN: q && q.RN, S: q && q.S };
    state.lock = L0; state.excl = X0; state.rules = R0; PANEL.forEach((id, i) => { document.getElementById(id).value = pv[i]; }); document.getElementById("stackBoth").checked = sb;
    QUICK = []; QSIM = null; renderQuick();
    return { ruled, sim, n: a.ids.length, locked: lk.every(id => a.ids.indexOf(id) >= 0), rowsShown, slotsOk, sal, differs, notBetter, gone, hidden: document.getElementById("quickMore").hidden };
  });
  check("Quick lineup: 8 players with both locks, legal slots and salary, shown in a table; Another differs and is no better; an exclude takes effect; nothing kept after",
        ql.n === 8 && ql.locked && ql.rowsShown === 8 && ql.slotsOk && ql.sal <= 50000 && ql.differs && ql.notBetter && ql.gone && ql.hidden, JSON.stringify(ql));
  check("Quick lineup follows the draw panel: a never rule and a Min salary hold, and the note lists them", ql.ruled, JSON.stringify(ql));
  check("Quick sim: 200 drawn and cut in waves to 20 distinct lineups under the locks and excludes, best ROI first with the top in tier A, ROI over every round's nights; a tap shows that lineup's card",
        ql.sim.opts > 0 && ql.sim.simRows === 20 && ql.sim.simRows === ql.sim.distinct && ql.sim.drawn > 100 && ql.sim.rounds >= 2 && ql.sim.allN === ql.sim.rounds * ql.sim.RN + ql.sim.S && ql.sim.roiOrder && ql.sim.allLocked && ql.sim.topA && ql.sim.tapped, JSON.stringify(ql.sim));
  // the quick card in DraftKings' order with the latest tips in UTIL: one late-game player and two same-game players at
  // different salaries -> the late one first in UTIL, the higher-salary same-game one in the other UTIL
  const qlate = await pg.evaluate(async () => {
    const wait = async () => { for (let t = 0; t < 400 && document.getElementById("quickRun").disabled; t++) await new Promise(r => setTimeout(r, 30)); };
    const L0 = state.lock, X0 = state.excl, R0 = state.rules; state.lock = {}; state.excl = {}; state.rules = [];
    document.getElementById("quickRun").click(); await wait();
    const ids = QUICK[0].ids, by = id => byId(id), saved = rows.map(r => [r, r.game_start]);
    const legal = (u) => { const rest = ids.filter(id => u.indexOf(id) < 0).map(by);
      return rest.filter(r => DKSim.isG(r) && !DKSim.isF(r)).length <= 3 && rest.filter(r => DKSim.isF(r) && !DKSim.isG(r)).length <= 3; };
    let pick = null;
    for (const late of ids) for (const a of ids) for (const b of ids) {
      if (pick || late === a || late === b || a >= b || by(a).salary === by(b).salary) continue;
      const hi = by(a).salary > by(b).salary ? a : b, lo = hi === a ? b : a;
      if (legal([late, hi]) && legal([late, lo])) pick = { late, hi, lo };
    }
    if (!pick) { state.lock = L0; state.excl = X0; state.rules = R0; QUICK = []; renderQuick(); return { skipped: true }; }
    const t0 = Date.parse("2026-11-22T17:00:00Z");
    rows.forEach(r => { if (ids.indexOf(r.id) >= 0) r.game_start = new Date(t0).toISOString(); });
    by(pick.late).game_start = new Date(t0 + 3 * 3600e3).toISOString();
    by(pick.hi).game_start = by(pick.lo).game_start = new Date(t0 + 3600e3).toISOString();
    renderQuick();
    const cells = [...document.querySelectorAll("#quickBox table.quick tbody tr")].map(tr => [tr.children[0].textContent, tr.children[1].childNodes[0].textContent.replace(/ \(L\)$/, "").trim()]);
    const out = { util: cells.slice(6).map(c => c[0]).join(), names: cells.slice(6).map(c => c[1]), want: [by(pick.late).name, by(pick.hi).name], slots: cells.map(c => c[0]).join() };
    saved.forEach(([r, g]) => { r.game_start = g; }); state.lock = L0; state.excl = X0; state.rules = R0; QUICK = []; renderQuick();
    return out;
  });
  check("quick card: the latest tip and, of two same-game players, the higher salary in UTIL (DraftKings' slot order kept)",
        !qlate.skipped && qlate.slots === "G,G,G,F,F,F,UTIL,UTIL" && JSON.stringify(qlate.names) === JSON.stringify(qlate.want), JSON.stringify(qlate));
  // zero-games players (2026-11-21): a card scaled by zero_gp shows "0 games" with the hover, is a punt at his scaled
  // minutes, "back" restores his unadjusted numbers in one tap (kept in the slate's settings), the dimmed tag re-applies;
  // a Questionable zero-games card takes no Q factor on top (gatedProj)
  const zg = await pg.evaluate(() => {
    const r = rows.filter(x => usable(x) && !x.status && (x.min || 0) >= 20).sort((a, b) => (b.fp_dk || 0) - (a.fp_dk || 0))[0];
    const keep = JSON.stringify(slate.players[r.id]), Z0 = JSON.stringify(state.zeroBack || {});
    const orig = {}; ZERO_FIELDS.forEach(k => { if (r[k] != null) orig[k] = r[k]; });
    ZERO_FIELDS.forEach(k => { if (r[k] != null) r[k] = Math.round(r[k] * 0.041 * 10) / 10; });
    r.zero_gp = { team_games: 5, f: 0.041, orig }; delete r._zero; state.zeroBack = {};
    zeroApply(); applyOuts(); renderPlayers();
    const tag = () => document.querySelector('#players .row[data-id="' + r.id + '"] .tag.zero');
    const out = { title: tag() && tag().getAttribute("title"), on: tag() && !tag().classList.contains("off"), punt: !usable(r), fp: r.fp_dk, back: !!document.querySelector('#players .row[data-id="' + r.id + '"] .zback') };
    document.querySelector('#players .row[data-id="' + r.id + '"] .zback').click();
    out.restored = r.fp_dk === orig.fp_dk && r.min === orig.min && !r.zero_gp && tag().classList.contains("off") && !!state.zeroBack[r.id] && usable(r);
    tag().click();
    out.again = r.zero_gp && r.fp_dk === Math.round(orig.fp_dk * 0.041 * 10) / 10 && !state.zeroBack[r.id];
    const q = Object.assign({}, r, { status: "Questionable" });
    out.noQ = DKSim.gatedProj(q, gate) === DKSim.gatedProj(Object.assign({}, r, { status: "" }), gate);
    // put the row back as the card had it
    Object.keys(r).forEach(k => { if (k !== "id") delete r[k]; }); Object.assign(r, JSON.parse(keep)); r._status0 = r.status; state.zeroBack = JSON.parse(Z0); applyOuts(); renderPlayers();
    return out;
  });
  check("0 games: the tag and hover on a scaled card, a punt at his scaled minutes; back restores his unadjusted numbers in one tap (in the pool again), the dimmed tag re-applies; no Q factor on top",
        zg.title === "Has played 0 of his team's 5 games: projected at \u00d70.04. Bring back if news says he's active." && zg.on && zg.punt && zg.back && zg.restored && zg.again && zg.noQ, JSON.stringify(zg));
  // sit risk (2026-11-21): the card's p_play under 0.70 on an in-pool player with no Q / D / Out gets the tag, its hover
  // the chance and the why; Q / Out / X'd players don't; Show: sit risk lists exactly the flagged
  const sr = await pg.evaluate(() => {
    const live = rows.filter(r => usable(r) && !r.status && !isDoubtful(r)).sort((a, b) => proj(b) - proj(a));
    const a = live[0], b = live[1], c = live[2], q = rows.find(r => r.status === "Questionable"), X0 = state.excl, P0 = view.pool;
    const saved = rows.map(r => [r, r.p_play, r.p_play_why]);
    a.p_play = 0.42; a.p_play_why = "missed 2 of last 5 · last game 9 days ago"; b.p_play = 0.69; c.p_play = 0.70;
    if (q) q.p_play = 0.2;
    renderPlayers();
    const tagOf = r => { const el = document.querySelector('#players .row[data-id="' + r.id + '"] .tag.sit'); return el ? el.getAttribute("title") : null; };
    const out = { a: tagOf(a), b: !!tagOf(b), c: !!tagOf(c), q: q ? !!tagOf(q) : false };
    view.pool = "sit"; renderPlayers();
    out.listed = [...document.querySelectorAll("#players .row")].map(x => x.dataset.id).sort().join() === [a.id, b.id].sort().join();
    out.option = !!document.querySelector('#poolShow option[value="sit"]');
    state.excl = Object.assign({}, X0, { [a.id]: true }); view.pool = "all"; renderPlayers(); out.xGone = !tagOf(a);
    state.excl = X0; view.pool = P0; saved.forEach(([r, p, w]) => { if (p == null) delete r.p_play; else r.p_play = p; if (w == null) delete r.p_play_why; else r.p_play_why = w; }); renderPlayers();
    return out;
  });
  check("sit risk: the tag on an in-pool, no-status player under 0.70 with the chance and why on hover; none at 0.70, on a Q or an X'd player; Show: sit risk lists only them",
        sr.a === "Sit risk: 42% to play \u2014 missed 2 of last 5 · last game 9 days ago. Check news before lock." && sr.b && !sr.c && !sr.q && sr.listed && sr.option && sr.xGone, JSON.stringify(sr));
  // the player list on a phone: scrolls sideways under a fixed L / X and name; Sal straight after the name
  await pg.setViewportSize({ width: 390, height: 844 });
  const mob = await pg.evaluate(async () => {
    renderPlayers(); const p = document.getElementById("players"), row = p.querySelector(".row");
    const at = sel => row.querySelector(sel).getBoundingClientRect().left;
    const who0 = at(".who"), lx0 = at(".lx"), third = [...row.children].filter(c => getComputedStyle(c).display !== "none").sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left)[2].textContent;
    p.scrollLeft = 300; await new Promise(r => requestAnimationFrame(r));
    const r = { scrolls: p.scrollWidth > p.clientWidth + 100, page: document.documentElement.scrollWidth <= 390, nameW: row.querySelector(".who").getBoundingClientRect().width,
                whoMoved: Math.abs(at(".who") - who0), lxMoved: Math.abs(at(".lx") - lx0), third, moved: p.scrollLeft };
    p.scrollLeft = 0;
    // +set in the pinned L / X group on one line with L and X, the scan's + hidden; a tap adds him to the set and says so
    const sr = [...p.querySelectorAll(".row")].find(x => x.querySelector(".setadd") && !x.querySelector(".act")), sb = sr.querySelector(".setadd");
    const sel0 = [...document.getElementById("rtList").selectedOptions].map(o => o.value), type0 = document.getElementById("rtType").value;
    r.setTop = Math.abs(sb.getBoundingClientRect().top - sr.querySelector(".lock").getBoundingClientRect().top) < 3;
    r.setIn = sb.getBoundingClientRect().right <= sr.querySelector(".who").getBoundingClientRect().left + 1 && getComputedStyle(sb).display !== "none";
    const pb = p.querySelector(".pbank"); r.pbHidden = !pb || getComputedStyle(pb).display === "none";
    sb.click();
    const t = document.getElementById("setToast"), id = sr.dataset.id, nSel = document.getElementById("rtList").selectedOptions.length;
    r.toast = !!t && !t.hidden && t.textContent.indexOf(byId(id).name) >= 0 && t.textContent.indexOf(nSel + " player") >= 0;
    r.inSet = [...document.getElementById("rtList").selectedOptions].some(o => o.value === id);
    [...document.getElementById("rtList").options].forEach(o => { o.selected = sel0.indexOf(o.value) >= 0; }); document.getElementById("rtType").value = type0; rtChips(); showEditor();
    return r;
  });
  // the Fill step's new pieces on a phone: the guide atop the list, the swap box and the top-up setting inside 390px
  const mobFill = await pg.evaluate(async () => {
    const st0 = OPEN_STEP, nb0 = NB.on; showStep("fill"); document.getElementById("fillSet").open = true; if (!nb0) nbSet(true);
    let rm = null; if (NB.on && BP && BP.review) { if (BP.b.picked.length >= BP.o.n) { rm = BP.b.picked[0]; BP.b.remove(rm); bpRescore(); } nbRender(); }
    swinRender("phone check"); await new Promise(r => requestAnimationFrame(r));
    const right = id => { const e = document.getElementById(id); return e && !e.hidden ? Math.round(e.getBoundingClientRect().right) : null; };
    renderProfiles(); document.getElementById("profBox").open = true;
    const r = { page: document.documentElement.scrollWidth, guide: right("nbGuide"), swap: right("swinBox"), top: document.getElementById("autoTopUp").getBoundingClientRect().right,
                prof: right("profList"), profSel: Math.max(0, ...[...document.querySelectorAll("#profList select")].map(x => Math.round(x.getBoundingClientRect().right))), profRows: document.querySelectorAll("#profList .prow").length };
    if (rm != null) { BP.b.add(rm); bpRescore(); nbRender(); }
    $("swinBox").hidden = true; document.getElementById("fillSet").open = false; if (!nb0) nbSet(false); showStep(st0);
    return r;
  });
  check("phone (390px): the guide, the swap box, the Auto top-up setting and the Contest profiles fit without sideways page scroll",
        mobFill.page <= 390 && mobFill.guide > 0 && mobFill.guide <= 390 && mobFill.prof > 0 && mobFill.prof <= 390 && mobFill.profSel <= 390 && mobFill.profRows > 0 && mobFill.swap != null && mobFill.swap <= 390 && mobFill.top <= 390, JSON.stringify(mobFill));
  await pg.setViewportSize({ width: 1100, height: 900 });
  const desk = await pg.evaluate(() => { renderPlayers(); const sb = document.querySelector("#players .row .setadd"), t = document.getElementById("setToast");
    return { set: !!sb && getComputedStyle(sb).display !== "none", lxW: document.querySelector("#players .row .lx").getBoundingClientRect().width, toastHidden: !t || t.hidden || true }; });
  check("phone: +set beside L and X in the pinned group, the scan's + hidden; a tap adds him to template 5's set and a toast gives the set's size",
        mob.setTop && mob.setIn && mob.pbHidden && mob.toast && mob.inSet, JSON.stringify(mob));
  check("desktop: +set where it was (the L / X group at its full width)", desk.set && desk.lxW >= 120, JSON.stringify(desk));
  check("phone: the player list scrolls sideways, L / X and the name stay put, the name 150px, Sal next, the page itself no wider",
        mob.scrolls && mob.page && mob.nameW >= 149 && mob.whoMoved <= 10 && mob.lxMoved <= 5 && /k$/.test(mob.third.trim()) && mob.moved > 0, JSON.stringify(mob));
  // the Swap step (late swap v1): standings at a tip + the entries file -> a card per entry with its proposal, accept boxes,
  // Export off (SWAP_EXPORT) until the read-only night; turned on, the export is valid with the started cells as read
  await pg.route(/site\.api\.espn\.com\/.*summary/, r => r.fulfill({ contentType: "application/json", body: JSON.stringify({ plays: [] }) }));
  const swIn = await pg.evaluate(() => {
    const at = Date.parse("2026-11-17T01:30Z"), started = id => Date.parse(byId(id).game_start || "") < at;
    const F = fieldOf().field.slice(0, 60), c = slate.contests.find(x => x.payouts);
    const lines = ["Rank,EntryId,EntryName,TimeRemaining,Points,Lineup,,Player,Roster Position,%Drafted,FPTS"];
    F.forEach((ids, k) => { const sl = DKSim.assign(ctx(), ids), lab = DKSwap.SLOTS;
      lines.push([k + 1, 9100000001 + k, "user" + k, 0, "", sl.map((id, j) => lab[j] + " " + (started(id) ? byId(id).name : "LOCKED")).join(" ")].join(",")); });
    const ours = DKSim.assign(ctx(), F[0]);
    const ent = "Entry ID,Contest Name,Contest ID,Entry Fee,G,G,G,F,F,F,UTIL,UTIL\r\n" + ["9100000001", '"' + c.name + '"', c.id, "$1"]
      .concat(ours.map(id => '"' + byId(id).name + " (" + id + ")" + (started(id) ? " (LOCKED)" : "") + '"')).join(",") + "\r\n";
    const d = new Date(at), pad = x => String(x).padStart(2, "0");
    return { stand: lines.join("\r\n") + "\r\n", ent, cid: String(c.id), local: d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + "T" + pad(d.getHours()) + ":" + pad(d.getMinutes()), ours, started: ours.filter(started) };
  });
  await pg.evaluate(() => { SWAP_EXPORT = false; showStep("swap"); });      // the read-only checks first; Export on below
  await pg.setInputFiles("#swapStand", { name: "contest-standings-" + swIn.cid + ".csv", mimeType: "text/csv", buffer: Buffer.from(swIn.stand) });
  await pg.setInputFiles("#swapEnt", { name: "DKEntries.csv", mimeType: "text/csv", buffer: Buffer.from(swIn.ent) });
  await pg.fill("#swapAt", swIn.local); await pg.fill("#swapNights", "300");
  await pg.waitForFunction(() => DKSwap && SWAP.ent && SWAP.stand.length === 1, null, { timeout: 10000 });
  await pg.click("#swapRun");
  await pg.waitForFunction(() => !document.getElementById("swapRun").disabled && /entr/.test(document.getElementById("swapStatus").textContent), null, { timeout: 120000 });
  const sw1 = await pg.evaluate(() => ({ status: document.getElementById("swapStatus").textContent, cards: document.querySelectorAll("#swapBox .swapcard").length,
    res: SWAP.res.map(p => ({ steps: p.steps.length, next: p.next, entryId: p.entryId })), exportOff: document.getElementById("swapExport").disabled,
    acc: document.querySelectorAll("#swapBox .swapAcc:checked").length, label: document.querySelector('#stepBar button[data-step="swap"]').textContent }));
  check("Swap: standings + entries file -> one card for the entry with its proposal (or keep), the status naming the contest, field and draws; Export off; the step label counts",
        sw1.cards === 1 && sw1.res.length === 1 && /60 entries \(0 unmatched\)/.test(sw1.status) && sw1.exportOff && /Swap/.test(sw1.label) &&
        sw1.res[0].next.length === 8 && swIn.started.every(id => sw1.res[0].next[swIn.ours.indexOf(id)] === id), JSON.stringify(sw1));
  // kept in the browser: a reload (the slate loaded again) restores the standings and the entries file; the card shows
  // the live points at the button's moment
  const swKeep = await pg.evaluate(async () => {
    await new Promise(r => setTimeout(r, 300));
    const nS = SWAP.stand.length, nE = SWAP.ent.rows.length, res = SWAP.res;
    SWAP.stand = []; SWAP.ent = null; await swapRestore();
    const out = { stand: SWAP.stand.length === nS, ent: !!SWAP.ent && SWAP.ent.rows.length === nE, msg: document.getElementById("swapStatus").textContent,
                  now: typeof res[0].now === "number" && /pts now/.test(document.querySelector("#swapBox .swapcard .hd") ? document.querySelector("#swapBox .swapcard .hd").textContent : "") };
    SWAP.res = res; renderSwap(); out.now = out.now || /pts now/.test(document.querySelector("#swapBox .swapcard .hd").textContent);
    return out;
  });
  check("Swap: the standings and the entries file are kept in this browser for the slate (a reload restores them); the card shows the live points now",
        swKeep.stand && swKeep.ent && /Restored from this browser/.test(swKeep.msg) && swKeep.now, JSON.stringify(swKeep));
  // the night so far (2026-11-24): the entries' expected payout now, the fees, the accepted swaps' gain
  const swEV = await pg.evaluate(() => ({ hidden: document.getElementById("swapEV").hidden, txt: document.getElementById("swapEV").textContent,
    want: SWAP.res.reduce((t, p) => t + p.cur.ev, 0) }));
  check("Swap: P&L expected with its 10th-90th range and chance of profit, night by night; the entries' expected payout now, the fees, the accepted swaps' gain",
        !swEV.hidden && /^P&L [+−]\$[\d.]+ expected · range [+−]\$[\d.]+ to [+−]\$[\d.]+ \(10th–90th\) · profit \d+% of nights/.test(swEV.txt) && new RegExp("Your 1 entry now: expected payout \\$" + swEV.want.toFixed(2).replace(".", "\\.")).test(swEV.txt) && /in the money \d+%/.test(swEV.txt), JSON.stringify(swEV));
  // the phone (2026-11-23): a swap pack saved here loads elsewhere (standings and entries file back); the Contest
  // picker lists the loaded contests; the order control re-sorts the cards
  const [dlP] = await Promise.all([pg.waitForEvent("download"), pg.click("#swapPackSave")]);
  const packTxt = fs.readFileSync(await dlP.path(), "utf8");
  const pk0 = await pg.evaluate(() => { const n = [SWAP.stand.length, SWAP.ent.rows.length]; SWAP.stand = []; SWAP.ent = null; SWAP.entText = null; renderSwapList(); return n; });
  await pg.setInputFiles("#swapPackLoad", { name: "swap-pack.json", mimeType: "application/json", buffer: Buffer.from(packTxt) });
  await pg.waitForFunction(() => SWAP.stand.length > 0 && SWAP.ent, null, { timeout: 10000 });
  const pk = await pg.evaluate(() => ({ stand: SWAP.stand.length, ent: SWAP.ent.rows.length, opts: [...document.querySelectorAll("#swapOnly option")].map(o => o.value),
    msg: document.getElementById("swapStatus").textContent }));
  check("Swap: a swap pack carries the standings and entries file to another device; the Contest picker lists the loaded contests",
        JSON.parse(packTxt).kind === "dk-swap-pack" && pk.stand === pk0[0] && pk.ent === pk0[1] && pk.opts.length === pk0[0] + 1 && pk.opts[0] === "" && /Swap pack loaded/.test(pk.msg), JSON.stringify([pk0, pk]));
  // the two field assumptions differing: both answers on the card, a radio picks which one is used (and accepted)
  const swAlt = await pg.evaluate(() => {
    const p = SWAP.res[0], keep = p.alt;
    p.alt = { entryId: p.entryId, ids: p.ids, cur: p.cur, steps: [], next: p.ids.slice(), chalk: 2 }; p.chalk = 1; SWAP.use = {}; renderSwap();
    const radios = document.querySelectorAll("#swapBox .swapUse").length, hasBoth = /field as projected/.test(document.getElementById("swapBox").textContent) && /field on the chalk/.test(document.getElementById("swapBox").textContent);
    const alt = document.querySelector('#swapBox .swapUse[value="alt"]'); alt.checked = true; alt.dispatchEvent(new Event("change", { bubbles: true }));
    const used = SWAP.use[p.entryId] === "alt" && swapPick(p) === p.alt && !SWAP.acc[p.entryId];
    const main = document.querySelector('#swapBox .swapUse[value="main"]'); main.checked = true; main.dispatchEvent(new Event("change", { bubbles: true }));
    const back = swapPick(p) === p && (!p.steps.length || !!SWAP.acc[p.entryId]);
    p.alt = keep; SWAP.use = {}; renderSwap();
    return { radios, hasBoth, used, back };
  });
  check("Swap: when the field assumptions differ the card shows both answers, and the radio picks the one used (its keep unaccepts, back again re-accepts)",
        swAlt.radios === 2 && swAlt.hasBoth && swAlt.used && swAlt.back, JSON.stringify(swAlt));
  // Export on (the switch after the read-only night): the file is valid, started cells as read
  const swEx = await pg.evaluate(() => { SWAP_EXPORT = true; SWAP.acc = {}; SWAP.res.forEach(p => { SWAP.acc[p.entryId] = 1; }); renderSwap(); return !document.getElementById("swapExport").disabled; });
  let swOut = null;
  if (sw1.res[0].steps) {
    const [dlS] = await Promise.all([pg.waitForEvent("download"), pg.click("#swapExport")]);
    const txt = fs.readFileSync(await dlS.path(), "utf8");
    swOut = await pg.evaluate(t => { const p = DKSwap.parseEntries(t); return { ids: p.rows[0].ids, cells: p.rows[0].cells }; }, txt);
  }
  const origCells = swIn.ent.split("\r\n")[1];
  check("Swap: with Export on, the edited entries file is the proposal, its started players' cells exactly as read (or nothing to export when it keeps)",
        swEx && (!sw1.res[0].steps || (swOut && swOut.ids.join() === sw1.res[0].next.join() && swIn.started.every(id => swOut.cells[swIn.ours.indexOf(id)].indexOf("(LOCKED)") > 0))),
        JSON.stringify(swOut));
  // the chalk assumption fitted per contest: revealed slots that pile onto the top-owned players fit power 2, slots
  // spread as projected fit power 1; under SWAP_FIT_MIN revealed players, as projected
  const swFit = await pg.evaluate(() => {
    const own = {}, ps = rows.filter(r => r.status !== "Out").slice(0, 8);
    ps.forEach((r, i) => { own[r.id] = 40 - 4 * i; });
    const mk = pw => { const tot = ps.reduce((t, r) => t + Math.pow(own[r.id], pw), 0), entries = [];
      ps.forEach(r => { const n = Math.round(400 * Math.pow(own[r.id], pw) / tot); for (let k = 0; k < n; k++) entries.push({ slots: [{ slot: "UTIL", name: r.name }] }); });
      return { entries }; };
    const few = { entries: ps.slice(0, 3).map(r => ({ slots: [{ slot: "G", name: r.name }] })) };
    return { chalk: swapChalkFit(mk(2), own).p, flat: swapChalkFit(mk(1), own).p, few: swapChalkFit(few, own), auto: document.getElementById("swapChalk").value };
  });
  check("Swap: the chalk assumption is fitted per contest from its revealed slots (chalk-heavy -> 2, as projected -> 1, too few -> 1), Auto by default",
        swFit.chalk === 2 && swFit.flat === 1 && swFit.few.p === 1 && swFit.few.n === 0 && swFit.auto === "auto", JSON.stringify(swFit));
  // the standings add up, one pick at a time; the same contest picked again replaces its file; the list names them
  const swList = await pg.evaluate(() => ({ n: SWAP.stand.length, txt: document.getElementById("swapList").textContent }));
  await pg.setInputFiles("#swapStand", { name: "contest-standings-999999991.csv", mimeType: "text/csv", buffer: Buffer.from(swIn.stand) });
  await pg.setInputFiles("#swapStand", { name: "contest-standings-" + swIn.cid + ".csv", mimeType: "text/csv", buffer: Buffer.from(swIn.stand) });
  await pg.waitForFunction(() => SWAP.stand.length === 2, null, { timeout: 10000 });
  const swList2 = await pg.evaluate(() => ({ n: SWAP.stand.length, txt: document.getElementById("swapList").textContent }));
  check("Swap: standings add up one pick at a time (a contest picked again replaced), the list names each with your entries in it",
        swList.n === 1 && /Standings loaded \(1\)/.test(swList.txt) && /1 of your entries/.test(swList.txt) && swList2.n === 2 && /Standings loaded \(2\)/.test(swList2.txt) && /not on this slate/.test(swList2.txt),
        JSON.stringify([swList, swList2]));
  // a big contest's standings come as a .zip: its CSV is read from inside, named as in the zip
  const zipBuf = require("child_process").execSync("python3 -c \"import io,sys,zipfile; b=io.BytesIO(); z=zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED); z.writestr('contest-standings-999999992.csv', sys.stdin.read()); z.close(); sys.stdout.buffer.write(b.getvalue())\"", { input: swIn.stand });
  await pg.setInputFiles("#swapStand", { name: "contest-standings-999999992.zip", mimeType: "application/zip", buffer: zipBuf });
  await pg.waitForFunction(() => SWAP.stand.length === 3, null, { timeout: 10000 });
  const swZip = await pg.evaluate(() => { const f = SWAP.stand.find(x => /999999992/.test(x.name)); return { name: f && f.name, same: f && f.text.length };} );
  check("Swap: a zipped standings file (DraftKings' big contests) is read from inside the zip and added",
        swZip.name === "contest-standings-999999992.csv" && swZip.same === swIn.stand.length, JSON.stringify(swZip));
  await pg.evaluate(() => { SWAP_EXPORT = true; SWAP.stand = []; renderSwapList(); showStep("bank"); });
  // the sync (2026-11-24): with a token, the page writes the slate's marks, late swap files and lineups to the sync repo
  // (a fake GitHub here) and, on a slate open, takes the repo's newer marks; without a token it writes nothing
  const gh = {}, puts = [];
  await pg.route(/api\.github\.com\/repos\/[^/]+\/[^/]+\/contents\//, r => {
    const path = decodeURIComponent(r.request().url().split("/contents/")[1].split("?")[0]);
    if (r.request().method() === "PUT") { const b = JSON.parse(r.request().postData()); gh[path] = { content: b.content, sha: "s" + (puts.length + 1) }; puts.push(path);
      return r.fulfill({ contentType: "application/json", body: JSON.stringify({ content: { sha: gh[path].sha } }) }); }
    return gh[path] ? r.fulfill({ contentType: "application/json", body: JSON.stringify({ content: gh[path].content, sha: gh[path].sha }) }) : r.fulfill({ status: 404, body: "{}" });
  });
  const sy = await pg.evaluate(async () => {
    const dg = String(slate.draft_group_id), wait = ms => new Promise(r => setTimeout(r, ms));
    localStorage.removeItem("dkcbb:sync"); const id0 = rows.find(r => r.status !== "Out").id;
    state.proj[id0] = 33.3; save(); await wait(3500);
    const offWrote = Object.keys(SYNC.last).length;
    localStorage.setItem("dkcbb:sync", JSON.stringify({ repo: "me/dk-sync", token: "t" })); syncSumText();
    state.proj[id0] = 44.4; save(); swapSave(); await wait(3800);
    const sum = document.getElementById("syncSum").textContent;
    return { dg, id0, offWrote, sum };
  });
  await pg.waitForTimeout(500);
  const decode = b64 => Buffer.from(b64, "base64").toString("utf8");
  const mk = gh["cbb/" + sy.dg + "/marks.json"], swf = gh["cbb/" + sy.dg + "/swap.json"];
  check("sync: with a token the slate's marks (Proj edits, outs) and late swap files go to the sync repo; without one nothing is written; the box says so",
        sy.offWrote === 0 && !!mk && JSON.parse(decode(mk.content)).proj[sy.id0] === 44.4 && !!swf && /Sync: on \(me\/dk-sync\)/.test(sy.sum), JSON.stringify([sy, Object.keys(gh)]));
  // another device's newer marks: a slate open takes them
  gh["cbb/" + sy.dg + "/marks.json"] = { content: Buffer.from(JSON.stringify({ at: Date.now() + 60000, outs: { [sy.id0]: 1 }, ins: {}, proj: {}, idea: "from phone" })).toString("base64"), sha: "x9" };
  const pulled = await pg.evaluate(async id0 => { await syncPull(); return { out: !!state.outs[id0], idea: document.getElementById("ideaName").value, status: rows.find(r => r.id === id0).status }; }, sy.id0);
  check("sync: a newer copy from another device is taken when the slate opens (outs, Proj edits, idea name)", pulled.out && pulled.idea === "from phone" && pulled.status === "Out", JSON.stringify(pulled));
  await pg.evaluate(id0 => { localStorage.removeItem("dkcbb:sync"); delete state.outs[id0]; state.proj = {}; state.idea = ""; save(); applyOuts(); syncSumText(); }, sy.id0);
  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("PASS " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(`${passes.length} passed, ${fails.length} failed`);
  process.exit(fails.length ? 1 : 0);
})();
