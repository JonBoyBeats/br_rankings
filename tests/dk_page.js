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

  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("PASS " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(`${passes.length} passed, ${fails.length} failed`);
  process.exit(fails.length ? 1 : 0);
})();
