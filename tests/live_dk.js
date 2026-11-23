// The Live page on a DraftKings slate: the DK page's fixture slate (tests/dk_fixture), the saved build for it
// (analysis/cbb/dk/builds), and one made-up ESPN box line, checking the exposure column and DraftKings points.
//
//   node tests/live_dk.js [screenshot.png]
const { chromium } = require("playwright"), fs = require("fs"), path = require("path");
const R = path.join(__dirname, ".."), FIX = R + "/tests/dk_fixture";
const morning = JSON.parse(fs.readFileSync(FIX + "/dk_cbb_morning.json")), sl = morning.slates[0];
const bank = JSON.parse(fs.readFileSync(R + "/analysis/cbb/dk/builds/dk_bank_2026-11-16_156660.json"));
// expected exposure, from the saved build
const cnt = {}; let n = 0;
Object.values(bank.portfolios).forEach(a => a.forEach(k => { n++; bank.pool[k].forEach(id => cnt[id] = (cnt[id] || 0) + 1); }));
const top = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])[0];
const P = sl.players[top];
// a live game for him: 22 pts (4-7 3PT), 11 reb, 3 ast, 1 stl, 0 blk, 2 TO, 30 min -> DK 22+2+13.75+4.5+2-1+1.5 = 44.75
const box = { boxscore: { players: [{ team: { abbreviation: "X" }, statistics: [{ keys: ["MIN", "FG", "3PT", "FT", "REB", "AST", "STL", "BLK", "TO", "PTS"],
  athletes: [{ athlete: { id: P.espn, displayName: P.name }, stats: ["30", "8-14", "4-7", "2-2", "11", "3", "1", "0", "2", "22"] }] }] }] } };
const board = { events: [{ id: P.event, date: "2026-11-17T00:00Z", status: { period: 2, displayClock: "10:00", type: { state: "in", name: "STATUS_IN_PROGRESS" } },
  competitions: [{ competitors: [{ homeAway: "home", team: { abbreviation: "AAA" } }, { homeAway: "away", team: { abbreviation: "BBB" } }] }] }] };
(async () => {
  const b = await chromium.launch(), pg = await b.newPage({ viewport: { width: 900, height: 900 } });
  const errs = []; pg.on("pageerror", e => errs.push(e.message));
  await pg.route(/fonts\.(googleapis|gstatic)/, r => r.abort());
  await pg.route(/br-adp-mirror/, r => {
    const u = r.request().url();
    if (/dk_cbb_morning/.test(u)) return r.fulfill({ path: FIX + "/dk_cbb_morning.json", contentType: "application/json" });
    if (/nba_tonight/.test(u)) return r.fulfill({ body: JSON.stringify({ slates: [{ slate_id: "nba1", label: "nba_mon_main", title: "Main Slate", sport: "nba", cutoff: sl.start,
      players: [{ player_id: "p1", appearance_id: "a1", first_name: "Test", last_name: "Guard", team: "LAL", adp: 1.5 }] }] }), contentType: "application/json" });
    return r.fulfill({ body: JSON.stringify({ slates: [], players: {} }), contentType: "application/json" });
  });
  await pg.route(/expo\.json/, r => r.fulfill({ body: "{}", contentType: "application/json" }));
  await pg.route(/dk_bank_/, r => r.fulfill({ path: R + "/analysis/cbb/dk/builds/dk_bank_2026-11-16_156660.json", contentType: "application/json" }));
  await pg.route(/espn\.com/, r => r.fulfill({ body: JSON.stringify(/summary/.test(r.request().url()) ? box : board), contentType: "application/json" }));
  await pg.clock.setFixedTime(new Date(new Date(sl.start).getTime() + 2 * 3600e3));   // the fixture slate's night: the page lists slates within hours of now
  await pg.goto("file://" + R + "/nba_live.html");
  await pg.waitForFunction(() => /Updated/.test(document.getElementById("status").textContent), null, { timeout: 30000 });
  const dkOpt = await pg.$$eval("#slate option", o => o.find(x => /DK Classic/.test(x.textContent)).value);
  if (await pg.inputValue("#slate") !== dkOpt) {      // with the NBA slate there too, open the DK one
    await pg.selectOption("#slate", dkOpt);
    await pg.waitForFunction(() => /Updated/.test(document.getElementById("status").textContent), null, { timeout: 30000 });
  }
  await pg.evaluate(d => { state.dkBuilds["156660"] = d; render(); }, bank);   // what the repo fetch gives on the site
  await pg.selectOption("#sort", "expo");
  const first = await pg.$eval("#list .row", el => el.innerText.replace(/\s+/g, " "));
  const head = await pg.$eval("#list .head", el => el.innerText.replace(/\s+/g, " "));
  const status = await pg.textContent("#status");
  const want = Math.round(100 * cnt[top] / n) + "%";
  const ok = [
    ["a DK Classic slate in the list", /DK Classic/.test(await pg.$eval("#slate", s => s.selectedOptions[0].textContent))],
    ["the first column is Exp, not ADP", /^EXP PLAYER/.test(head)],
    ["the most-used player first, at his exposure", first.startsWith(want + " " + P.name)],
    ["DraftKings points with the double-double bonus", / 44\.8 /.test(first + " ")],
    ["his value so far after the points: points per $1,000", first.endsWith("44.8 " + (44.75 / (P.salary / 1000)).toFixed(1) + "x")],
    ["the value cell shaded green", await pg.$eval("#list .row .val", e => /rgba\(46, 170, 96/.test(getComputedStyle(e).backgroundColor))],
    ["players without points show no value", (await pg.$$eval("#list .row .val.none", e => e.length)) === (await pg.$$eval("#list .row", e => e.length)) - 1],
    ["the status names the entries counted", /exposure: 46 DraftKings entries \(the saved build\)/.test(status)],
  ];
  await pg.selectOption("#sort", "val");
  ok.push(["sort by Value: the one with points first", (await pg.$eval("#list .row", el => el.innerText.replace(/\s+/g, " "))).includes(P.name)]);
  await pg.selectOption("#sort", "expo");
  // the sport buttons beside the title: there with the controls hidden; NBA goes to the NBA slate, CBB back to DK Classic
  await pg.click("#fold");
  const btns = await pg.$$eval("#sportBtns button", b => b.map(x => x.textContent + ":" + x.getAttribute("aria-pressed") + ":" + (x.offsetParent !== null)));
  ok.push(["sport buttons, shown with the controls hidden, CBB pressed", JSON.stringify(btns) === JSON.stringify(["NBA:false:true", "CBB:true:true"])]);
  await pg.click('#sportBtns [data-sport="nba"]');
  ok.push(["NBA button: the NBA slate", /^NBA/.test(await pg.$eval("#slate", s => s.selectedOptions[0].textContent)) &&
    (await pg.getAttribute('#sportBtns [data-sport="nba"]', "aria-pressed")) === "true"]);
  await pg.click('#sportBtns [data-sport="cbb"]');
  ok.push(["CBB button: back to DK Classic", /DK Classic/.test(await pg.$eval("#slate", s => s.selectedOptions[0].textContent))]);
  // each kind of slate keeps its own sort: Value on DK Classic, UD points on NBA, through the buttons both ways
  await pg.click("#fold"); await pg.selectOption("#sort", "val"); await pg.click("#fold");     // controls hidden between
  await pg.click('#sportBtns [data-sport="nba"]');
  await pg.click("#fold"); await pg.selectOption("#sort", "fp"); await pg.click("#fold");
  await pg.click('#sportBtns [data-sport="cbb"]');
  const dkSort = await pg.inputValue("#sort");
  await pg.click('#sportBtns [data-sport="nba"]');
  const nbaSort = await pg.inputValue("#sort");
  await pg.click('#sportBtns [data-sport="cbb"]');
  ok.push(["each slate kind keeps its sort (DK Value, NBA UD points)", dkSort === "val" && nbaSort === "fp" && await pg.inputValue("#sort") === "val"]);
  await pg.click("#fold");
  await pg.selectOption("#sort", "expo");
  await pg.waitForFunction(() => /Updated/.test(document.getElementById("status").textContent));
  await pg.evaluate(d => { state.dkBuilds["156660"] = d; render(); }, bank);
  await pg.click("#mine");
  ok.push(["Mine only: the players in your lineups", (await pg.$$eval("#list .row", r => r.length)) === Object.keys(cnt).length]);
  // 2026-11-23: your entries as entered (the DK page's late-swap entries file) win over the build; the field's real
  // ownership from a contest's standings loaded for late swap shows beside each name
  const live2 = await pg.evaluate(async ([dg, top, name]) => {
    localStorage.setItem("dkcbb-mylu:" + dg, JSON.stringify({ at: Date.now(), lineups: [[top], [top], ["zz"]] }));
    const stand = "Rank,EntryId,EntryName,TimeRemaining,Points,Lineup,,Player,Roster Position,%Drafted,FPTS\r\n1,111,someone,0,10,G " + name + ",," + name + ",G,37.5%,10\r\n";
    await new Promise(ok => { const q = indexedDB.open("dkswap", 1); q.onupgradeneeded = () => q.result.createObjectStore("files", { keyPath: "slate" });
      q.onsuccess = () => { const tx = q.result.transaction("files", "readwrite"); tx.objectStore("files").put({ slate: String(dg), stand: [{ name: "contest-standings-1.csv", text: stand, contest: "CBB $5 Pull Up Jumper" }], saved: Date.now() }); tx.oncomplete = ok; }; });
    state.dkActual = {}; render();
    await new Promise(r => setTimeout(r, 400));
    const row = [...document.querySelectorAll("#list .row")].find(x => x.innerText.includes(name));
    return { status: document.getElementById("status").textContent, row: row && row.innerText.replace(/\s+/g, " "), title: row && (row.querySelector(".name .tm:last-child") || {}).title };
  }, [String(sl.draft_group_id), top, P.name]);
  ok.push(["exposure from your entries as entered (late swaps included) over the build", /3 DraftKings entries \(your entries as entered, late swaps included\)/.test(live2.status) && /^67%/.test(live2.row || "")]);
  ok.push(["the field's real ownership beside the name, from the Pull Up Jumper standings", /field 38%/.test(live2.row || "") && /Pull Up Jumper/.test(live2.title || "")]);
  ok.push(["no page errors", !errs.length]);
  if (process.argv[2]) await pg.screenshot({ path: process.argv[2] });
  ok.forEach(([name, pass]) => console.log((pass ? "PASS " : "FAIL ") + name));
  if (ok.some(x => !x[1])) { console.log(first, "|", status); process.exitCode = 1; }
  await b.close();
})();
