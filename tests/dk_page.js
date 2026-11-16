// The DK page's self-test: drives dk.html the way the owner does, on a saved slate (tests/dk_fixture: the
// 2026-11-16 slate, 156660), and checks every lineup against every rule it was built under, and the export.
//
//   node tests/dk_page.js           (Playwright's Chromium; exits 1 on any failure)
//
// Run it before changing dk.html or dk_sim.js.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const FIX = path.join(__dirname, "dk_fixture");
const morning = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_morning.json")));
const field = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_field.json")));
const slate = morning.slates[0];
const P = slate.players;
const OWN = field.slates[String(slate.draft_group_id)].own;
const fails = [], passes = [];
function check(name, ok, detail) { (ok ? passes : fails).push(name + (ok || !detail ? "" : ": " + detail)); }
const isG = r => /(^|\/)G(\/|$)/.test(r.roster), isF = r => /(^|\/)F(\/|$)/.test(r.roster);

// the rules, checked here independently of dk_sim.js's own passes()
function obeys(rule, ids) {
  if (rule.share != null || rule.maxShare != null) return true;     // a set rule: checked by shareOk
  const has = id => ids.includes(id), cnt = set => (set || []).filter(has).length;
  return { min: () => cnt(rule.ids) >= rule.n, none: () => cnt(rule.ids) === 0, never: () => cnt(rule.ids) <= 1,
           if: () => !has(rule.ids[0]) || cnt(rule.set) >= rule.n, ifnot: () => has(rule.ids[0]) || cnt(rule.set) >= rule.n,
           ifteam: () => cnt(rule.set) < rule.n || cnt(rule.set2) >= rule.m }[rule.type]();
}

// slots for a lineup saved as ids only (Save build): guards to G first, forwards to F, the rest to UTIL
function picksSlots(ids) {
  const ps = ids.map(id => P[id]).sort((a, b) => b.salary - a.salary);
  const g = ps.filter(r => isG(r) && !isF(r)), f = ps.filter(r => isF(r) && !isG(r)), gf = ps.filter(r => isG(r) && isF(r));
  const G = g.splice(0, 3), F = f.splice(0, 3);
  while (G.length < 3) G.push(gf.shift());
  while (F.length < 3) F.push(gf.shift());
  return G.concat(F, g, f, gf).slice(0, 8).map(r => Object.keys(P).find(id => P[id] === r));
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
    const n = o.n || L.length, cap = Math.floor(o.expo * n + 1e-9);
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
  const errors = [];
  pg.on("pageerror", e => errors.push(e.message));
  await pg.route(/fonts\.(googleapis|gstatic)/, r => r.abort());
  await pg.route(/dk_cbb_morning/, r => r.fulfill({ path: path.join(FIX, "dk_cbb_morning.json"), contentType: "application/json" }));
  await pg.route(/dk_cbb_field/, r => r.fulfill({ path: path.join(FIX, "dk_cbb_field.json"), contentType: "application/json" }));
  await pg.route(/cbb_news/, r => r.fulfill({ path: path.join(FIX, "cbb_news.json"), contentType: "application/json" }));
  await pg.route(/dk_cbb_teams/, r => r.fulfill({ path: path.join(FIX, "dk_cbb_teams.json"), contentType: "application/json" }));
  let gate = null;
  await pg.route(/gate\.json/, r => gate ? r.fulfill({ body: JSON.stringify(gate), contentType: "application/json" }) : r.fulfill({ status: 404, body: "" }));
  await pg.goto("file://" + path.join(ROOT, "dk.html"));
  await pg.waitForSelector(".row");
  check("page loads the slate", (await pg.$$eval(".row", r => r.length)) === Object.keys(P).length);
  check("gate shows closed with no gate file", /Projection gate: closed/.test(await pg.textContent("#status")));

  const set = async (vals) => {
    for (const [id, v] of Object.entries(vals)) {
      if (typeof v === "boolean") await (v ? pg.check("#" + id) : pg.uncheck("#" + id));
      else await pg.fill("#" + id, String(v));
    }
  };
  const lineups = () => pg.evaluate(() => built.map(L => ({ ids: L.ids, slots: L.slots, sim: L.sim })));
  const run = async (button) => {
    await pg.click(button);
    await pg.waitForFunction(() => /^(Built|Sim:|only|no |pick a|Build failed|Sim failed)/.test(document.getElementById("buildStatus").textContent), null, { timeout: 300000 });
    return pg.textContent("#buildStatus");
  };
  const base = { nLineups: 20, maxExpo: 60, minUnique: 3, rand: 15, minSal: 48500, maxTeam: 5, stackN: 0, stackBoth: false, maxOwn: "", lowN: 0, lowPct: 10 };
  const rulesOf = v => ({ n: v.nLineups, minSal: v.minSal, maxTeam: v.maxTeam, expo: v.maxExpo / 100, minUnique: v.minUnique, stackN: v.stackN, stackBoth: v.stackBoth,
                          maxOwn: v.maxOwn === "" ? null : +v.maxOwn, lowN: v.lowN, lowPct: v.lowPct });

  // Build only, under each rule
  for (const [name, extra] of [["defaults", {}], ["game stack 3, both teams", { stackN: 3, stackBoth: true }], ["max total own 150%", { maxOwn: 150 }],
                               ["2 players under 10% owned", { lowN: 2 }], ["all three", { stackN: 3, stackBoth: true, maxOwn: 150, lowN: 2 }]]) {
    const v = Object.assign({}, base, extra);
    await set(v);
    const msg = await run("#build");
    audit("Build only, " + name, await lineups(), rulesOf(v));
    if (!/^Built 20 lineups/.test(msg)) check("Build only, " + name + ": built all 20", false, msg);
  }

  // locks, excludes and a player cap
  const ids = Object.keys(P).filter(id => P[id].status !== "Out").sort((a, c) => P[c].fp_dk / P[c].salary - P[a].fp_dk / P[a].salary);
  const lockId = ids[3], exclId = ids[0], capId = ids[1];
  await set(base);
  await pg.click(`#players .row[data-id="${lockId}"] .lock`);
  await pg.click(`#players .row[data-id="${exclId}"] .excl`);
  await pg.fill(`#players .row[data-id="${capId}"] .cap`, "25");
  await pg.press(`#players .row[data-id="${capId}"] .cap`, "Tab");
  await run("#build");
  audit("Build only, a lock, an exclude and a 25% cap", await lineups(), Object.assign(rulesOf(base), { lock: lockId, excl: exclId, capId: capId, capPct: 0.25 }));
  await pg.click("#clearLx");

  // Sim & pick (fewer candidates and nights, for speed): rules held, numbers and the stability readout shown
  await set(Object.assign({}, base, { stackN: 3, stackBoth: true, lowN: 2 }));
  await pg.fill("#nCand", "150"); await pg.fill("#nSims", "1000");
  const jukebox = await pg.$$eval("#contest option", o => o.find(x => /Jukebox/.test(x.textContent)).value);
  await pg.selectOption("#contest", jukebox);
  const msg = await run("#simPick");
  const L = await lineups();
  audit("Sim & pick, stack and low-owned", L, rulesOf(Object.assign({}, base, { stackN: 3, stackBoth: true, lowN: 2 })));
  check("Sim & pick reports stability and cut lines", /Stability: .* kept \d+% of the value/.test(msg) && /winning score \d+/.test(msg), msg);
  check("Sim & pick gives every lineup its numbers", L.length === 20 && L.every(l => l.sim && l.sim.e >= 0 && l.sim.cash >= 0 && l.sim.cash <= 1));

  // Export: DraftKings' upload file, the lineups as built, slot for slot
  const [dl] = await Promise.all([pg.waitForEvent("download"), pg.click("#export")]);
  const lines = fs.readFileSync(await dl.path(), "utf8").trim().split("\n");
  check("export header is G,G,G,F,F,F,UTIL,UTIL", lines[0] === "G,G,G,F,F,F,UTIL,UTIL", lines[0]);
  check("export rows are the built lineups, slot for slot", lines.length === L.length + 1 && lines.slice(1).every((l, i) => l === L[i].slots.join(",")));

  // the projection gate: an open band blends DraftKings' average into Proj
  gate = { nights: 9, bands: [{ lo: 6000, hi: 99999, open: true, w: 0.6 }, { lo: 0, hi: 5999, open: false, w: 1 }] };
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate: OPEN/.test(document.getElementById("status").textContent));
  const pick = Object.keys(P).find(id => P[id].salary >= 6000 && P[id].dk_avg > 0 && P[id].status !== "Out");
  const cheap = Object.keys(P).find(id => P[id].salary < 6000 && P[id].dk_avg > 0 && P[id].status !== "Out");
  const shown = await pg.evaluate(([a, c]) => [proj(rows.find(r => r.id === a)), proj(rows.find(r => r.id === c))], [pick, cheap]);
  check("gate blends where open", Math.abs(shown[0] - (0.6 * P[pick].fp_dk + 0.4 * P[pick].dk_avg)) < 1e-9, JSON.stringify(shown));
  check("gate leaves closed bands alone", Math.abs(shown[1] - P[cheap].fp_dk) < 1e-9);

  // --- team tiles and rules -----------------------------------------------------------------------------
  const TEAMS = JSON.parse(fs.readFileSync(path.join(FIX, "dk_cbb_teams.json"))).slates[String(slate.draft_group_id)];
  gate = null;
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate: closed/.test(document.getElementById("status").textContent));
  const openTeam = async team => {
    if (!(await pg.$(`#teamPanel .tile[data-team="${team}"]`))) await pg.click(`#teamBar button[data-team="${team}"]`);
    await pg.waitForSelector(`#teamPanel .tile[data-team="${team}"]`);
  };
  check("team bar: one button per team, slate line shown", (await pg.$$eval("#teamBar button", t => t.length)) === TEAMS.teams.length &&
        /games · \d+ spreads? of 15\+/.test(await pg.textContent("#slateLine")), await pg.textContent("#slateLine"));
  check("team bar: in quadrant order", JSON.stringify(await pg.$$eval("#teamBar button", v => v.map(x => x.className))) === JSON.stringify(TEAMS.teams.map(t => t.verdict)));
  await openTeam(TEAMS.teams[0].team);
  const panel = await pg.evaluate(() => [...document.querySelectorAll("#teamPanel .tile")].map(t => t.dataset.team));
  const opp0 = TEAMS.teams.find(t => t.team !== TEAMS.teams[0].team && TEAMS.teams[0].game === t.game);
  check("team panel: the team's tile, then its opponent's", JSON.stringify(panel) === JSON.stringify([TEAMS.teams[0].team, opp0 && opp0.team]), JSON.stringify(panel));
  const pprojs = await pg.$$eval("#teamPanel .teamside:first-child .row:not(.out) input.proj", x => x.map(i => +i.value));
  check("team panel: its players by projection, highest first", pprojs.length > 3 && pprojs.every((v, i) => i === 0 || pprojs[i - 1] >= v), JSON.stringify(pprojs));
  check("news: collapsed by default", !(await pg.$eval("#newsBox", d => d.open)));
  const clearRules = () => pg.evaluate(() => { state.rules = []; state.lock = {}; state.excl = {}; save(); renderRules(); renderPlayers(); });
  const rulesNow = () => pg.evaluate(() => state.rules.slice());
  const buildAudit = async (name, extra) => {
    await set(Object.assign({}, base, { nLineups: 12, minUnique: 2 }, extra || {}));
    const msg = await run("#build");
    const L = await lineups(), R = await rulesNow();
    const bad = [];
    L.forEach((l, i) => R.forEach(r => { if (!obeys(r, l.ids)) bad.push(`#${i + 1} breaks "${r.label}"`); }));
    check(`rules, ${name}: ${L.length} lineups obey every rule`, L.length > 0 && !bad.length, bad.slice(0, 3).join("; ") || msg);
    return L;
  };
  const tile = TEAMS.teams.find(t => t.top && t.top.length >= 3 && t.verdict !== "FADE");
  const tsel = `.tile[data-team="${tile.team}"]`;
  const mates = id => Object.keys(P).filter(x => P[x].team === P[id].team);

  // the tile buttons
  for (const act of ["min2", "min3", "stack", "excl"]) {
    await clearRules();
    await openTeam(tile.team); await pg.click(`${tsel} button[data-act="${act}"]`);
    const R = await rulesNow();
    check(`tile button ${act} writes its rule${R.length > 1 ? "s" : ""}`, R.length === (act === "stack" ? 2 : 1), JSON.stringify(R.map(r => r.label)));
    await buildAudit("tile " + act);
  }
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
  await buildAudit("pivot and bring-back (edited)");

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
  await pg.click(`#players .row[data-id="${p1}"] .lock`);
  let L2 = await buildAudit("template 1, condition met (he's locked)");
  check("template 1: met in every lineup", L2.every(l => l.ids.includes(p1)));
  await pg.click(`#players .row[data-id="${p1}"] .excl`);
  L2 = await buildAudit("template 1, condition not met (he's excluded)");
  check("template 1: not met, lineups free of it", L2.every(l => !l.ids.includes(p1)));
  // 2. if NOT P then 1+ of his team's #2/#3
  await clearRules();
  await addRule("ifnot", async () => { await pg.selectOption("#rtP", p1); await pg.dispatchEvent("#rtP", "change"); await pg.fill("#rtN", "1"); });
  R = await rulesNow();
  check("template 2: list starts as his team's #2 and #3", R[0] && R[0].set.length === 2 && R[0].set.every(id => P[id].team === P[p1].team && id !== p1), JSON.stringify(R));
  await pg.click(`#players .row[data-id="${p1}"] .excl`);
  L2 = await buildAudit("template 2, condition met (he's excluded)");
  await pg.click(`#players .row[data-id="${p1}"] .lock`);
  L2 = await buildAudit("template 2, condition not met (he's locked)");
  check("template 2: not met in every lineup", L2.every(l => l.ids.includes(p1)));
  // 3. if 2+ from team then 1+ from its opponent
  await clearRules();
  await addRule("ifteam", async () => { await pg.selectOption("#rtTeam", t2.team); await pg.fill("#rtN", "2"); await pg.fill("#rtM", "1"); });
  await openTeam(t2.team); await pg.click(`.tile[data-team="${t2.team}"] button[data-act="min2"]`);
  L2 = await buildAudit("template 3, condition met (a Min 2 from the team)");
  await pg.evaluate(() => { state.rules.pop(); save(); renderRules(); });
  await openTeam(t2.team); await pg.click(`.tile[data-team="${t2.team}"] button[data-act="excl"]`);
  L2 = await buildAudit("template 3, condition not met (the team excluded)");
  // 4. never P with Q
  await clearRules();
  await addRule("never", async () => { await pg.selectOption("#rtP", p1); await pg.selectOption("#rtQ", p2); });
  await pg.click(`#players .row[data-id="${p1}"] .lock`);
  L2 = await buildAudit("template 4, one of them locked");
  check("template 4: never the other with him", L2.every(l => !l.ids.includes(p2)));
  await pg.click(`#players .row[data-id="${p2}"] .lock`);
  await set(Object.assign({}, base, { nLineups: 3 }));
  const imp = await run("#build");
  check("template 4: both locked is refused, not broken", /no lineup left fits the rules|a locked player/.test(imp) && (await lineups()).length === 0, imp);

  // the quadrant: scores on every tile, and each quadrant's button
  check("tiles: Quality and Leverage on the tile, and what they're ranked against",
        (await pg.$$eval("#teamPanel .tile .scores", x => x.length)) >= 1 && /ranks against tonight's \d+ teams/.test(await pg.textContent("#slateLine")));
  const shareOk = (L, R, n) => R.filter(r => r.share != null || r.maxShare != null).every(r => {
    const have = L.filter(l => r.ids.filter(id => l.ids.includes(id)).length >= r.n).length;
    return r.share != null ? have >= Math.ceil(r.share * n - 1e-9) : have <= Math.floor(r.maxShare * n + 1e-9);
  });
  for (const q of ["FOCUS", "CHALK", "LEVERAGE"]) {
    const t = TEAMS.teams.find(x => x.verdict === q);
    if (!t) continue;
    await clearRules();
    await openTeam(t.team); await pg.click(`.tile[data-team="${t.team}"] button[data-act="quad"]`);
    const RQ = await rulesNow();
    const want = { FOCUS: r => r.length === 1 && r[0].share === 0.75 && r[0].n === 2,
                   CHALK: r => r.length === 1 && r[0].maxShare === 0.5 && r[0].n === 1,
                   LEVERAGE: r => r.length === 1 && r[0].share === 0.25 && r[0].n === 2 }[q];
    check(`quadrant ${q} button writes its rules`, want(RQ), JSON.stringify(RQ.map(r => r.label)));
    await set(Object.assign({}, base, { nLineups: 20 }));
    const msg = await run("#build");
    const LQ = await lineups();
    check(`quadrant ${q}: Build only's 20 lineups meet it as a set`, LQ.length === 20 && shareOk(LQ, RQ, 20) && LQ.every(l => RQ.every(r => obeys(r, l.ids) || r.share != null || r.maxShare != null)), msg);
    if (q === "CHALK") {
      const cap1 = await pg.evaluate(id => state.cap[id], t.top[0].id);
      check("quadrant CHALK caps the #1 at 25% and the set holds it", cap1 === 25 && LQ.filter(l => l.ids.includes(t.top[0].id)).length <= 5, String(cap1));
      await pg.evaluate(() => { state.cap = {}; save(); renderPlayers(); });
    }
  }
  const fadeRules = await pg.evaluate(t => QUAD.FADE.rules(t), TEAMS.teams[0]);
  check("quadrant FADE button excludes the team", fadeRules.length === 1 && fadeRules[0].type === "none");
  // a share rule edited in place, then held by Sim & pick
  await clearRules();
  const lev = TEAMS.teams.find(x => x.verdict === "LEVERAGE"), foc = TEAMS.teams.find(x => x.verdict !== "LEVERAGE");
  await openTeam(lev.team); await pg.click(`.tile[data-team="${lev.team}"] button[data-act="quad"]`);
  await pg.fill('.rule[data-i="0"] input.rs', "40"); await pg.press('.rule[data-i="0"] input.rs', "Tab");
  let RS = await rulesNow();
  check("share rule edits in place", RS[0].share === 0.4 && /in 40% of lineups/.test(RS[0].label), JSON.stringify(RS));
  await openTeam(foc.team); await pg.click(`.tile[data-team="${foc.team}"] button[data-act="min2"]`);
  await pg.evaluate(t => { state.rules.push({ type: "min", ids: teamIds(t), n: 1, maxShare: 0.5, label: t + " in at most 50% of lineups" }); save(); renderRules(); }, TEAMS.teams.find(x => x.team !== lev.team && x.team !== foc.team).team);
  RS = await rulesNow();
  await set(base); await pg.fill("#nCand", "150"); await pg.fill("#nSims", "500");
  const smsg2 = await run("#simPick");
  const LS = await lineups();
  check("Sim & pick holds share rules as a set (and every per-lineup rule)", LS.length === 20 && shareOk(LS, RS, 20) &&
        LS.every(l => RS.every(r => obeys(r, l.ids) || r.share != null || r.maxShare != null)), smsg2);
  await clearRules();

  // Sim & pick under rules: every lineup obeys, the pass counts are shown
  await clearRules();
  await openTeam(tile.team); await pg.click(`${tsel} button[data-act="pivot"]`);
  await openTeam(tile.team); await pg.click(`${tsel} button[data-act="bring"]`);
  await addRule("never", async () => { await pg.selectOption("#rtP", p1); await pg.selectOption("#rtQ", p2); });
  await set(base); await pg.fill("#nCand", "150"); await pg.fill("#nSims", "500");
  const smsg = await run("#simPick");
  L2 = await lineups(); R = await rulesNow();
  check("Sim & pick under rules: every lineup obeys every rule", L2.length > 0 && L2.every(l => R.every(r => obeys(r, l.ids))), smsg);
  check("Sim & pick under rules: says how many candidates pass each", /Rules: .* of \d+ pass; all of them: \d+ of \d+/.test(smsg), smsg);
  check("rules list shows the pass counts", (await pg.$$eval(".rule .pc:not(.cost)", x => x.length)) === R.length);
  check("Sim & pick prices the rules: all against none, and each removed", /What the rules cost .* with all of them, .* with none .*Removing one at a time:/.test(smsg), smsg);
  check("rules list shows each rule's cost", (await pg.$$eval(".rule .cost", x => x.length)) === R.length);
  check("team bar marks borderline quadrants", (await pg.$$eval("#teamBar button", v => v.filter(x => /\*$/.test(x.textContent)).length)) ===
        TEAMS.teams.filter(t => t.borderline).length);
  const [dl4] = await Promise.all([pg.waitForEvent("download"), pg.click("#saveEntries")]);
  const ent = JSON.parse(fs.readFileSync(await dl4.path(), "utf8"));
  check("Save lineups + rules writes both", ent.kind === "entries" && ent.rule_set.length === R.length && ent.lineups.length === L2.length);
  await clearRules();

  // the portfolio builder (a small pool, for speed): adding a lineup raises the set's expected payout by exactly its
  // Added value, remove undoes it, auto-fill stays within the rules, the picks export, Save build writes a gradable file
  gate = null;
  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate: closed/.test(document.getElementById("status").textContent));
  await set(base);
  await pg.selectOption("#contest", jukebox);
  await pg.fill("#poolSize", "300"); await pg.fill("#nSims", "1000");
  await pg.click("#bpBuild");
  await pg.waitForFunction(() => /Re-scored every lineup/.test(document.getElementById("bpStatus").textContent) || /failed|Only/.test(document.getElementById("bpStatus").textContent), null, { timeout: 300000 });
  check("builder: pool built and scored", (await pg.$$eval("#bpTable tr", r => r.length)) > 100, await pg.textContent("#bpStatus"));
  const step = await pg.evaluate(() => {
    const b = BP.b, out = [];
    for (const k of [0, 5, 40]) {
      const before = b.total(), v = BP.scores[k] ? BP.scores[k].value : null;
      bpAdd(k);
      out.push(Math.abs(b.total() - before - v));
    }
    bpRemove(5);
    return { gaps: out, picked: b.picked.slice() };
  });
  check("builder: Added value is the set's payout with it minus without", step.gaps.every(g => g < 1e-9), JSON.stringify(step.gaps));
  check("builder: Remove takes a pick out", JSON.stringify(step.picked) === JSON.stringify([0, 40]), JSON.stringify(step.picked));
  await pg.click("#bpClear");
  await pg.click("#bpAuto");
  await pg.waitForFunction(() => /re-scored every lineup/i.test(document.getElementById("bpStatus").textContent) && BP.b.picked.length >= 20 || /stopped/.test(document.getElementById("bpStatus").textContent), null, { timeout: 300000 });
  const picks = await pg.evaluate(() => BP.b.picked.map(k => ({ ids: BP.pool[k].ids, slots: BP.pool[k].slots })));
  audit("builder: Auto-fill", picks, rulesOf(base));
  check("builder: summary shows coverage and diversity", /of nights one reaches the top 1%/.test(await pg.textContent("#bpSummary")) && /distinct cores/.test(await pg.textContent("#bpSummary")));
  await pg.click("#bpUse");
  const [dl2] = await Promise.all([pg.waitForEvent("download"), pg.click("#export")]);
  const rows2 = fs.readFileSync(await dl2.path(), "utf8").trim().split("\n").slice(1);
  check("builder: Use as my lineups exports the picks", rows2.length === picks.length && rows2.every((l, i) => l === picks[i].slots.join(",")));
  const [dl3] = await Promise.all([pg.waitForEvent("download"), pg.click("#bpSave")]);
  const saved = JSON.parse(fs.readFileSync(await dl3.path(), "utf8"));
  // a 300-lineup pool can run out of lineups that fit the caps short of 20 (the page says so); 1,000 fills
  check("builder: Save build writes the pool, the hand-built set and an auto-pick", saved.pool.length >= 250 && saved.hand.length === picks.length &&
        saved.auto.length >= 15 && String(saved.draft_group) === String(slate.draft_group_id), JSON.stringify({ pool: saved.pool.length, hand: saved.hand.length, auto: saved.auto.length }));
  check("builder: Auto-fill says why when it stops short", picks.length === 20 || /stopped at \d+/.test(await pg.textContent("#bpStatus")));
  audit("builder: the saved auto-pick", saved.auto.map(k => ({ ids: saved.pool[k], slots: saved.pool[k] })).map(l => ({ ids: l.ids, slots: picksSlots(l.ids) })), rulesOf(base));

  // the bank, the entries file, the cut, the portfolios, review and the DraftKings export. The entries file is
  // synthetic (made-up entry IDs, in DraftKings' layout), never a real one.
  const bankDraw = async (n) => {
    await pg.fill("#bankN", String(n));
    await pg.click("#bankDraw");
    await pg.waitForFunction(() => /^Banked|failed|Infeasible|no lineup/.test(document.getElementById("buildStatus").textContent), null, { timeout: 300000 });
    return pg.textContent("#buildStatus");
  };
  await set(base);
  const m1 = await bankDraw(60);
  await set(Object.assign({}, base, { stackN: 3, stackBoth: true }));
  const m2 = await bankDraw(60);
  await set(base);
  await pg.click("#bankBuilt");                        // the lineups on the page, banked twice: kept once
  const nb = await pg.evaluate(() => built.length);
  await pg.click("#bankBuilt");
  const m3 = await pg.textContent("#buildStatus");
  const bank = await pg.evaluate(() => BANK);
  const keys = bank.lineups.map(L => L.ids.slice().sort().join(","));
  check("bank: duplicates dropped", new Set(keys).size === keys.length && nb > 0 && m3 === "Banked 0 new lineups (" + nb + " already in the bank)." &&
        bank.lineups.length <= 120 + nb, [m1, m2, m3].join(" | "));
  check("bank: each lineup tagged with the rules it was built under", bank.tags.length === bank.lineups.length && bank.tags.every(t => t.length >= 1) &&
        JSON.stringify(Object.keys(bank.tagRules).sort()) === JSON.stringify(["3-stack + bring-back", "no rules"]), JSON.stringify(Object.keys(bank.tagRules)));
  bank.lineups.forEach((L, i) => { if (bank.tags[i].includes("3-stack + bring-back") && bank.tags[i].length === 1) audit("bank: stack-tagged lineup", [L], rulesOf(Object.assign({}, base, { stackN: 3, stackBoth: true, nLineups: 1, maxExpo: 100 }))); });
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

  await pg.fill("#cutKeep", "100"); await pg.fill("#cutPct", "25"); await pg.fill("#cutNights", "300");
  await pg.click("#cutRun");
  await pg.waitForFunction(() => /^Cut |failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const cmsg = await pg.textContent("#cutStatus"), cut = await pg.evaluate(() => CUT);
  check("cut: down to Keep, rounds shrinking by Cut %", cut && cut.keep.length === 100 && new Set(cut.keep).size === 100 &&
        cut.rounds.every((r, i) => i === 0 || r.survivors < cut.rounds[i - 1].survivors), cmsg);
  check("cut: ranked against each contest with entries", cut && JSON.stringify(cut.contests.slice().sort()) === JSON.stringify(["197791872", "197791874", "197791877"]), cmsg);
  const ths = await pg.$$eval("#bankBox th", t => t.map(x => x.textContent));
  check("cut: survivors by rule tag after each round", ths.includes("After the cut") && ths.filter(t => /^Round \d+$/.test(t)).length === cut.rounds.length, JSON.stringify(ths));

  await pg.click("#pfRun");
  await pg.waitForFunction(() => /^Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const pf = await pg.evaluate(() => PF);
  const pmsg = await pg.textContent("#cutStatus"), size = { "197791872": 1, "197791874": 5, "197791877": 1 };
  check("portfolios: one per contest, from the final pool", Object.keys(size).every(c => pf[c] && pf[c].length >= 1 && pf[c].length <= size[c] && pf[c].every(i => cut.keep.includes(i)) &&
        new Set(pf[c]).size === pf[c].length), JSON.stringify(pf));
  check("portfolios: each fills its entries, or says what stops it", Object.keys(size).every(c => pf[c].length === size[c]) || /short: .* stops it|runs out/.test(pmsg), pmsg);
  await pg.click('button[data-review="197791874"]');
  await pg.waitForFunction(() => BP && BP.review === "197791874");
  check("review: opens the contest's portfolio in the builder", JSON.stringify(await pg.evaluate(() => BP.b.picked.map(k => BP.idx[k]))) === JSON.stringify(pf["197791874"]) &&
        !(await pg.$eval("#bpKeep", x => x.hidden)));
  await pg.evaluate(() => bpRemove(BP.b.picked[0]));
  await pg.click("#bpKeep");
  const pf2 = await pg.evaluate(() => PF["197791874"]);
  check("review: Keep replaces the contest's portfolio", pf2.length === pf["197791874"].length - 1 && pf2.every(i => pf["197791874"].includes(i)), JSON.stringify(pf2));

  const [dl5] = await Promise.all([pg.waitForEvent("download"), pg.click("#pfExport")]);
  const out = fs.readFileSync(await dl5.path(), "utf8").trim().split(/\r?\n/).map(l => l.split(","));
  check("export: DraftKings' header, first 12 columns", out[0].join(",") === "Entry ID,Contest Name,Contest ID,Entry Fee,G,G,G,F,F,F,UTIL,UTIL", out[0].join(","));
  const rowsOut = out.slice(1), byId = {};
  rowsOut.forEach(r => byId[r[0]] = r);
  check("export: only the entries with a lineup (the off-slate one and any past a short portfolio left out)",
        rowsOut.length === pf["197791872"].length + pf["197791877"].length + pf2.length && !byId["9000000008"] && !byId["9000000007"], rowsOut.map(r => r[0]).join(" "));
  const finalPf = Object.assign({}, pf, { "197791874": pf2 });
  const want = {};
  ["197791872", "197791877", "197791874"].forEach(cid => fake.filter(r => String(r[2]) === cid).slice(0, finalPf[cid].length).forEach((r, k) => want[r[0]] = bank.lineups[finalPf[cid][k]].slots));
  check("export: each entry ID keeps its contest and gets its portfolio's lineup, slot for slot",
        Object.keys(want).every(id => byId[id] && byId[id].slice(4).join(",") === want[id].join(",") && fake.some(f => String(f[0]) === id && String(f[2]) === byId[id][2])));
  ["197791872", "197791874", "197791877"].forEach(cid => {             // the same lineup may go in two contests, not twice in one
    const L = rowsOut.filter(r => r[2] === cid).map(r => ({ ids: r.slice(4), slots: r.slice(4) }));
    audit("export: " + cid + "'s lineups", L, rulesOf(Object.assign({}, base, { nLineups: L.length, maxExpo: 100, minUnique: 1 })));
  });

  const [dl6] = await Promise.all([pg.waitForEvent("download"), pg.click("#bankSave")]);
  const bs = JSON.parse(fs.readFileSync(await dl6.path(), "utf8"));
  check("Save build (bank): the pool, its tags, the final cut and the portfolios", bs.kind === "build" && bs.pool.length === bank.lineups.length && bs.tags.length === bs.pool.length &&
        JSON.stringify(bs.final) === JSON.stringify(cut.keep) && bs.portfolios["197791874"].length === pf2.length && /^dk_bank_/.test(dl6.suggestedFilename()), dl6.suggestedFilename());

  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("PASS " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(`${passes.length} passed, ${fails.length} failed`);
  process.exit(fails.length ? 1 : 0);
})();
