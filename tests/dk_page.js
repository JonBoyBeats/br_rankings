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
  await pg.click(`.row[data-id="${lockId}"] .lock`);
  await pg.click(`.row[data-id="${exclId}"] .excl`);
  await pg.fill(`.row[data-id="${capId}"] .cap`, "25");
  await pg.press(`.row[data-id="${capId}"] .cap`, "Tab");
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
  check("tiles: one per team, slate line shown", (await pg.$$eval(".tile", t => t.length)) === TEAMS.teams.length &&
        /games · \d+ spreads? of 15\+/.test(await pg.textContent("#slateLine")), await pg.textContent("#slateLine"));
  check("tiles: in verdict order, each with its reason", JSON.stringify(await pg.$$eval(".tile .verdict", v => v.map(x => x.textContent))) ===
        JSON.stringify(TEAMS.teams.map(t => t.verdict)));
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
    await pg.click(`${tsel} button[data-act="${act}"]`);
    const R = await rulesNow();
    check(`tile button ${act} writes its rule${R.length > 1 ? "s" : ""}`, R.length === (act === "stack" ? 2 : 1), JSON.stringify(R.map(r => r.label)));
    await buildAudit("tile " + act);
  }
  // the #1 player's shortcuts, and editing one after
  await clearRules();
  await pg.click(`${tsel} button[data-act="pivot"]`);
  await pg.click(`${tsel} button[data-act="bring"]`);
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
  await pg.click(`.row[data-id="${p1}"] .lock`);
  let L2 = await buildAudit("template 1, condition met (he's locked)");
  check("template 1: met in every lineup", L2.every(l => l.ids.includes(p1)));
  await pg.click(`.row[data-id="${p1}"] .excl`);
  L2 = await buildAudit("template 1, condition not met (he's excluded)");
  check("template 1: not met, lineups free of it", L2.every(l => !l.ids.includes(p1)));
  // 2. if NOT P then 1+ of his team's #2/#3
  await clearRules();
  await addRule("ifnot", async () => { await pg.selectOption("#rtP", p1); await pg.dispatchEvent("#rtP", "change"); await pg.fill("#rtN", "1"); });
  R = await rulesNow();
  check("template 2: list starts as his team's #2 and #3", R[0] && R[0].set.length === 2 && R[0].set.every(id => P[id].team === P[p1].team && id !== p1), JSON.stringify(R));
  await pg.click(`.row[data-id="${p1}"] .excl`);
  L2 = await buildAudit("template 2, condition met (he's excluded)");
  await pg.click(`.row[data-id="${p1}"] .lock`);
  L2 = await buildAudit("template 2, condition not met (he's locked)");
  check("template 2: not met in every lineup", L2.every(l => l.ids.includes(p1)));
  // 3. if 2+ from team then 1+ from its opponent
  await clearRules();
  await addRule("ifteam", async () => { await pg.selectOption("#rtTeam", t2.team); await pg.fill("#rtN", "2"); await pg.fill("#rtM", "1"); });
  await pg.click(`.tile[data-team="${t2.team}"] button[data-act="min2"]`);
  L2 = await buildAudit("template 3, condition met (a Min 2 from the team)");
  await pg.evaluate(() => { state.rules.pop(); save(); renderRules(); });
  await pg.click(`.tile[data-team="${t2.team}"] button[data-act="excl"]`);
  L2 = await buildAudit("template 3, condition not met (the team excluded)");
  // 4. never P with Q
  await clearRules();
  await addRule("never", async () => { await pg.selectOption("#rtP", p1); await pg.selectOption("#rtQ", p2); });
  await pg.click(`.row[data-id="${p1}"] .lock`);
  L2 = await buildAudit("template 4, one of them locked");
  check("template 4: never the other with him", L2.every(l => !l.ids.includes(p2)));
  await pg.click(`.row[data-id="${p2}"] .lock`);
  await set(Object.assign({}, base, { nLineups: 3 }));
  const imp = await run("#build");
  check("template 4: both locked is refused, not broken", /no lineup left fits the rules|a locked player/.test(imp) && (await lineups()).length === 0, imp);

  // Sim & pick under rules: every lineup obeys, the pass counts are shown
  await clearRules();
  await pg.click(`${tsel} button[data-act="pivot"]`);
  await pg.click(`${tsel} button[data-act="bring"]`);
  await addRule("never", async () => { await pg.selectOption("#rtP", p1); await pg.selectOption("#rtQ", p2); });
  await set(base); await pg.fill("#nCand", "150"); await pg.fill("#nSims", "500");
  const smsg = await run("#simPick");
  L2 = await lineups(); R = await rulesNow();
  check("Sim & pick under rules: every lineup obeys every rule", L2.length > 0 && L2.every(l => R.every(r => obeys(r, l.ids))), smsg);
  check("Sim & pick under rules: says how many candidates pass each", /Rules: .* of \d+ pass; all of them: \d+ of \d+/.test(smsg), smsg);
  check("rules list shows the pass counts", (await pg.$$eval(".rule .pc", x => x.length)) === R.length);
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
        saved.auto.length >= 18 && String(saved.draft_group) === String(slate.draft_group_id), JSON.stringify({ pool: saved.pool.length, hand: saved.hand.length, auto: saved.auto.length }));
  check("builder: Auto-fill says why when it stops short", picks.length === 20 || /stopped at \d+/.test(await pg.textContent("#bpStatus")));
  audit("builder: the saved auto-pick", saved.auto.map(k => ({ ids: saved.pool[k], slots: saved.pool[k] })).map(l => ({ ids: l.ids, slots: picksSlots(l.ids) })), rulesOf(base));

  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("PASS " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(`${passes.length} passed, ${fails.length} failed`);
  process.exit(fails.length ? 1 : 0);
})();
