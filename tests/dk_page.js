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
  const base = { rand: 20, minSal: 48500, maxTeam: 5, stackN: 0, stackBoth: false, maxOwn: "", lowN: 0, lowPct: 10 };
  const rulesOf = v => ({ minSal: v.minSal, maxTeam: v.maxTeam, stackN: v.stackN, stackBoth: v.stackBoth, maxOwn: v.maxOwn === "" ? null : +v.maxOwn, lowN: v.lowN, lowPct: v.lowPct });

  // the page reads top to bottom: the draw's settings, then the cut and the pick's (Max exposure, Min unique)
  const order = await pg.evaluate(() => ["rand", "maxOwn", "ruleList", "bankDraw", "entriesFile", "cutRun", "maxExpo", "minUnique", "pfRun", "pfExport", "bpTable"]
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
  // Max exposure and Min unique don't touch the draw
  await set(base); await pg.fill("#maxExpo", "5"); await pg.fill("#minUnique", "8");
  const { L: Lx, msg: mx } = await draw(15);
  check("Max exposure and Min unique don't limit the draw", Lx.length >= 12, mx);
  await pg.fill("#maxExpo", "60"); await pg.fill("#minUnique", "3");

  // locks and excludes: in the draw, and in the tag
  const ids = Object.keys(P).filter(id => P[id].status !== "Out").sort((a, c) => P[c].fp_dk / P[c].salary - P[a].fp_dk / P[a].salary);
  const lockId = ids[3], exclId = ids[0];
  await set(base);
  await pg.click(`#players .row[data-id="${lockId}"] .lock`);
  await pg.click(`#players .row[data-id="${exclId}"] .excl`);
  const { L: Ll, msg: ml } = await draw(15);
  audit("Draw & bank, a lock and an exclude", Ll, Object.assign(rulesOf(base), { lock: lockId, excl: exclId }));
  check("a lock and an exclude are in the tag", /lock .* \+ no /.test(ml), ml);
  await pg.click("#clearLx");

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
  await pg.click(`#players .row[data-id="${p1}"] .lock`);
  let L2 = await drawAudit("template 1, condition met (he's locked)");
  check("template 1: met in every lineup", L2.every(l => l.ids.includes(p1)));
  await pg.click(`#players .row[data-id="${p1}"] .excl`);
  L2 = await drawAudit("template 1, condition not met (he's excluded)");
  check("template 1: not met, lineups free of it", L2.every(l => !l.ids.includes(p1)));
  // 2. if NOT P then 1+ of his team's #2/#3
  await clearRules();
  await addRule("ifnot", async () => { await pg.selectOption("#rtP", p1); await pg.dispatchEvent("#rtP", "change"); await pg.fill("#rtN", "1"); });
  R = await rulesNow();
  check("template 2: list starts as his team's #2 and #3", R[0] && R[0].set.length === 2 && R[0].set.every(id => P[id].team === P[p1].team && id !== p1), JSON.stringify(R));
  await pg.click(`#players .row[data-id="${p1}"] .excl`);
  L2 = await drawAudit("template 2, condition met (he's excluded)");
  await pg.click(`#players .row[data-id="${p1}"] .lock`);
  L2 = await drawAudit("template 2, condition not met (he's locked)");
  check("template 2: not met in every lineup", L2.every(l => l.ids.includes(p1)));
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
  await pg.click(`#players .row[data-id="${p1}"] .lock`);
  L2 = await drawAudit("template 4, one of them locked");
  check("template 4: never the other with him", L2.every(l => !l.ids.includes(p2)));
  await pg.click(`#players .row[data-id="${p2}"] .lock`);
  const { L: Limp, msg: imp } = await draw(3);
  check("template 4: both locked is refused, not broken", Limp.length === 0 && /Only 0 of 3: .*(no lineup left fits the rules|a locked player)/.test(imp), imp);

  // the quadrant: scores on every tile, and each quadrant's button is a rule for the draw
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
  await pg.waitForFunction(() => /Projection gate/.test(document.getElementById("status").textContent));
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

  await pg.fill("#cutKeep", "100"); await pg.fill("#cutPct", "25"); await pg.fill("#cutNights", "300"); await pg.fill("#cutProtect", "30");
  await pg.click("#cutRun");
  await pg.waitForFunction(() => /^Cut |failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const cmsg = await pg.textContent("#cutStatus"), cut = await pg.evaluate(() => CUT);
  check("cut: down to Keep, rounds shrinking by Cut %", cut && cut.keep.length === 100 && new Set(cut.keep).size === 100 &&
        cut.rounds.every((r, i) => i === 0 || r.survivors < cut.rounds[i - 1].survivors), cmsg);
  const tagN = idx => { const o = {}; idx.forEach(k => bank.tags[k].forEach(t => o[t] = (o[t] || 0) + 1)); return o; };
  const allN = tagN(bank.lineups.map((L, k) => k)), keptN = tagN(cut.keep);
  check("cut: Protect 30% keeps at least 30% of every tag", Object.keys(allN).every(t => (keptN[t] || 0) >= Math.ceil(0.3 * allN[t])) && /Protect 30% a tag: \d+ lineups held/.test(cmsg),
        JSON.stringify({ allN, keptN }) + " " + cmsg);
  check("cut: ranked against each contest with entries", cut && JSON.stringify(cut.contests.slice().sort()) === JSON.stringify(["197791872", "197791874", "197791877"]), cmsg);
  const ths = await pg.$$eval("#bankBox th", t => t.map(x => x.textContent));
  check("cut: survivors by rule tag after each round", ths.includes("After the cut") && ths.filter(t => /^Round \d+$/.test(t)).length === cut.rounds.length, JSON.stringify(ths));

  await pg.fill("#nSims", "1000");
  await pg.click("#pfRun");
  await pg.waitForFunction(() => /^Portfolios from|failed/.test(document.getElementById("cutStatus").textContent), null, { timeout: 300000 });
  const pf = await pg.evaluate(() => PF);
  const pmsg = await pg.textContent("#cutStatus"), size = { "197791872": 1, "197791874": 5, "197791877": 1 };
  check("portfolios: one per contest, from the final pool", Object.keys(size).every(c => pf[c] && pf[c].length >= 1 && pf[c].length <= size[c] && pf[c].every(i => cut.keep.includes(i)) &&
        new Set(pf[c]).size === pf[c].length), JSON.stringify(pf));
  const pfAll = Object.values(pf).flat();
  check("portfolios: each lineup in one contest only, the largest stake first", new Set(pfAll).size === pfAll.length &&
        /the largest stake first: CBB \$6K Pull Up Jumper/.test(pmsg), pmsg);
  check("portfolios: each fills its entries, or says what stops it", Object.keys(size).every(c => pf[c].length === size[c]) || /short: .* stops it|runs out/.test(pmsg), pmsg);
  Object.keys(size).forEach(c => audit("portfolio " + c + " within Max exposure 60% and Min unique 3", pf[c].map(i => bank.lineups[i]),
    Object.assign(rulesOf(base), { n: size[c], expo: Math.max(0.6, 1 / size[c]), minUnique: 3 })));

  // review: the contest's set in the builder; Added value is exact, Remove undoes Add, Auto-fill keeps the pick's settings, Keep replaces the set
  await pg.click('button[data-review="197791874"]');
  await pg.waitForFunction(() => BP && BP.review === "197791874");
  check("review: other contests' lineups aren't on offer", await pg.evaluate(o => BP.idx.every(bi => !o.includes(bi)), pf["197791872"].concat(pf["197791877"])));
  check("review: opens the contest's portfolio in the builder", JSON.stringify(await pg.evaluate(() => BP.b.picked.map(k => BP.idx[k]))) === JSON.stringify(pf["197791874"]) &&
        !(await pg.$eval("#bpKeep", x => x.hidden)) && (await pg.$$eval("#bpTable tr", r => r.length)) > 50);
  const cols = await pg.$$eval("#bpTable th", t => t.map(x => x.textContent.replace(/[↓↑ ]+$/, "")));
  const qc = await pg.evaluate(() => ({ q: BP.qual.slice(0, 5), c: BP.core.slice(0, 5), n: BP.qual.length, k: BP.pool.length }));
  check("review: Quality and Core % beside the sim value, from the sim", ["Quality", "Core %", "Alone", "Added"].every(c => cols.includes(c)) &&
        qc.n === qc.k && qc.q.every(Number.isFinite) && qc.c.every(v => v >= 0 && v <= 1), JSON.stringify({ cols, qc }));
  await pg.click("#bpClear");
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
  check("review: Added value is the set's payout with it minus without", step.gaps.every(g => g < 1e-9), JSON.stringify(step.gaps));
  check("review: Remove takes a pick out", JSON.stringify(step.picked) === JSON.stringify([0, 40]), JSON.stringify(step.picked));
  await pg.click("#bpClear");
  await pg.click("#bpAuto");
  await pg.waitForFunction(() => BP.b.picked.length >= 5 || /stopped/.test(document.getElementById("bpStatus").textContent), null, { timeout: 300000 });
  const auto = await pg.evaluate(() => BP.b.picked.map(k => ({ ids: BP.pool[k].ids, slots: BP.pool[k].slots })));
  audit("review: Auto-fill within Max exposure and Min unique", auto, Object.assign(rulesOf(base), { n: 5, expo: 0.6, minUnique: 3 }));
  check("review: summary shows coverage and diversity", /of nights one reaches the top 1%/.test(await pg.textContent("#bpSummary")) && /distinct cores/.test(await pg.textContent("#bpSummary")));
  await pg.evaluate(() => bpRemove(BP.b.picked[0]));
  await pg.click("#bpKeep");
  const pf2 = await pg.evaluate(() => PF["197791874"]), kept = await pg.evaluate(() => BP.b.picked.map(k => BP.idx[k]));
  check("review: Keep replaces the contest's portfolio", JSON.stringify(pf2) === JSON.stringify(kept) && pf2.length === auto.length - 1, JSON.stringify(pf2));

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
  ["197791872", "197791874", "197791877"].forEach(cid => {
    const L = rowsOut.filter(r => r[2] === cid).map(r => ({ ids: r.slice(4), slots: r.slice(4) }));
    audit("export: " + cid + "'s lineups", L, Object.assign(rulesOf(base), { minUnique: 1 }));
  });
  const outKeys = rowsOut.map(r => r.slice(4).slice().sort().join(","));
  check("export: no lineup twice across the night's contests", new Set(outKeys).size === outKeys.length, outKeys.length + " rows, " + new Set(outKeys).size + " distinct");

  const [dl6] = await Promise.all([pg.waitForEvent("download"), pg.click("#bankSave")]);
  const bs = JSON.parse(fs.readFileSync(await dl6.path(), "utf8"));
  check("Save build (bank): the pool, its tags, the final cut and the portfolios", bs.kind === "build" && bs.pool.length === bank.lineups.length && bs.tags.length === bs.pool.length &&
        JSON.stringify(bs.final) === JSON.stringify(cut.keep) && bs.portfolios["197791874"].length === pf2.length && /^dk_bank_/.test(dl6.suggestedFilename()) &&
        bs.rule_set.length === 0 && bs.tag_settings["3-stack + bring-back"].stackN === 3 && bs.cut && bs.cut.protect === 30 && bs.cut.keep === 100,
        dl6.suggestedFilename() + " " + JSON.stringify(bs.cut));

  await pg.click("#reload");
  await pg.waitForFunction(() => /Projection gate/.test(document.getElementById("status").textContent));
  check("portfolios survive a reload (the Live page reads them for your exposures)",
        JSON.stringify(await pg.evaluate(() => PF["197791874"])) === JSON.stringify(pf2) && !(await pg.$eval("#pfExport", x => x.disabled)));

  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("PASS " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(`${passes.length} passed, ${fails.length} failed`);
  process.exit(fails.length ? 1 : 0);
})();
