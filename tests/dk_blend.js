// The source blend's page test (2026-11-28): Load source files reads a Gajewski-style TSV and a RotoWire-style CSV in
// the browser (made-up numbers on the 2026-11-16 fixture slate: no paid data in this public repo), blends each player's
// Proj (median; two: mean), keeps ours on an in/out split with the split tag, leaves the field's ownership alone, records
// only a summary in the build, and Clear sources puts every Proj back exactly.
//
//   node tests/dk_blend.js
const { chromium } = require("playwright");
const fs = require("fs"), os = require("os"), path = require("path");
const B = require("../dk_blend.js");

const ROOT = path.join(__dirname, ".."), FIX = path.join(__dirname, "dk_fixture");
const fails = [], passes = [];
function check(name, ok, detail) { (ok ? passes : fails).push(name + (ok || !detail ? "" : ": " + detail)); }

// the rule itself, no page
check("rule: three projections -> median", B.blendOne({ min: 25, fp: 20 }, [{ min: 30, fp: 30 }, { min: 28, fp: 24 }]).fp === 24);
check("rule: two -> mean", B.blendOne({ min: 25, fp: 20 }, [{ min: 30, fp: 26 }]).fp === 23);
check("rule: ours alone -> ours", B.blendOne({ min: 25, fp: 20 }, []).fp === 20);
const sp = B.blendOne({ min: 25, fp: 20 }, [{ min: 0, fp: 0 }, { min: 30, fp: 26 }]);
check("rule: in/out split (under 8 vs 10+ minutes) -> ours, flagged", sp.fp === 20 && sp.split === true);
check("rule: Out -> ours", B.blendOne({ min: 25, fp: 20 }, [{ min: 30, fp: 40 }], true).fp === 20);

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "blend-"));
const gj = path.join(tmp, "2026-11-16_gajewski.tsv"), rw = path.join(tmp, "rotowire-projections.csv");
fs.writeFileSync(gj, ["Player\tTeam\tPos\tSalary\tOpp\tTTL Min\tFPTs",
  "Milan Momcilovic\tUK\tF\t8600\tGRAM\t30\t31.8",
  "Malachi Moreno\tUK\tF\t8200\tGRAM\t0\t0",
  "Ousmane N'Diaye\tUK\tF\t5300\tGRAM\t20\t21.7"].join("\n") + "\n");
fs.writeFileSync(rw, [",,,,Projected Stats,,,,,,,", "Name,Team,Opp,Pos,MIN,PTS,REB,AST,STL,BLK,3PM,TO",
  "Milan Momcilovic,Kentucky,vs Grambling,F,30.0,25.8,0,0,0,0,0,0",
  "Malachi Moreno,Kentucky,vs Grambling,F,30.0,20.0,0,0,0,0,0,0",
  "Justin McBride,Kentucky,vs Grambling,F,15.0,15.3,0,0,0,0,0,0",
  "Braydon Hawthorne,Kentucky,vs Grambling,F,13.0,13.3,0,0,0,0,0,0",
  "Somebody Else,Elsewhere State,vs Nobody,G,30.0,20.0,0,0,0,0,0,0"].join("\n") + "\n");
const A = "44942812", M = "44942816", N = "44942846";

(async () => {
  const b = await chromium.launch(), pg = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = []; pg.on("pageerror", e => errors.push(e.message));
  await pg.route(/fonts\.(googleapis|gstatic)/, r => r.abort());
  for (const [re, f] of [[/dk_cbb_morning/, "dk_cbb_morning.json"], [/dk_cbb_field/, "dk_cbb_field.json"], [/cbb_news/, "cbb_news.json"], [/dk_cbb_teams/, "dk_cbb_teams.json"]])
    await pg.route(re, r => r.fulfill({ path: path.join(FIX, f), contentType: "application/json" }));
  await pg.route(/dk_cbb_writeups|gate\.json|own_watch\.json|field_fit\.json|lab\.json/, r => r.fulfill({ status: 404, body: "" }));
  await pg.goto("file://" + path.join(ROOT, "dk.html"));
  await pg.waitForSelector(".row");
  const snap = () => pg.evaluate(() => { const p = {}, o = {}; rows.forEach(r => { p[r.id] = proj(r); o[r.id] = own(r); }); return { p, o, line: $("srcLine").textContent, lineHidden: $("srcLine").hidden }; });
  const s0 = await snap();
  check("no files loaded: no source line, build says not loaded", s0.lineHidden && (await pg.evaluate(() => JSON.stringify(blendSummary()))) === '{"loaded":false}');
  await pg.setInputFiles("#srcFiles", [gj, rw]);
  await pg.waitForFunction(() => !$("srcLine").hidden);
  const s1 = await snap();
  check("the source line: each source's matches", /Gajewski 3 of 3 matched/.test(s1.line) && /RotoWire 4 of 5 matched/.test(s1.line) && /1 split/.test(s1.line), s1.line);
  const close = (a, b) => Math.abs(a - b) < 1e-6;
  check("three projections: Proj scaled to the median (ours 21.8, theirs 31.8 / 25.8 -> 25.8)", close(s1.p[A], s0.p[A] * 25.8 / 21.8), s1.p[A] + " vs " + s0.p[A]);
  check("two projections: Proj scaled to the mean (ours 15.7, Gajewski 21.7 -> 18.7)", close(s1.p[N], s0.p[N] * 18.7 / 15.7), s1.p[N] + " vs " + s0.p[N]);
  check("in/out split: Proj stays ours", close(s1.p[M], s0.p[M]));
  const tag = await pg.evaluate(id => { renderPlayers(); const r = document.querySelector('#players .row[data-id="' + id + '"] .srcsplit'); return r ? r.title : null; }, M);
  check("in/out split: tagged on his row", /sources split on whether he plays/.test(tag || ""), String(tag));
  check("players no source has: Proj unchanged", Object.keys(s0.p).filter(id => ![A, M, N].includes(id)).every(id => close(s0.p[id], s1.p[id])));
  check("the field's ownership reads ours: unchanged by the blend", Object.keys(s0.o).every(id => s0.o[id] === s1.o[id]));
  const bd = await pg.evaluate(() => JSON.stringify(blendSummary()));
  const bdo = JSON.parse(bd);
  check("the build records only a summary (loaded, sources, counts): no per-player value", bdo.loaded === true && bdo.changed === 2 && bdo.splits === 1 &&
        Object.keys(bdo).sort().join() === "at,changed,loaded,sources,splits" && !/25\.8|18\.7|31\.8|21\.7/.test(bd), bd);
  const stored = await pg.evaluate(() => Object.keys(localStorage).filter(k => k.indexOf("dkcbb-src:") === 0));
  check("the files are kept in this browser only (localStorage dkcbb-src:<group>)", stored.length === 1, JSON.stringify(stored));
  // a reload recomputes the blend from the kept files
  await pg.reload(); await pg.waitForSelector(".row");
  const s2 = await snap();
  check("a reload keeps the blend", close(s2.p[A], s1.p[A]) && !s2.lineHidden);
  await pg.click("#srcClear");
  const s3 = await snap();
  check("Clear sources: every Proj back exactly as before, the line gone", Object.keys(s0.p).every(id => s0.p[id] === s3.p[id]) && s3.lineHidden &&
        (await pg.evaluate(() => Object.keys(localStorage).filter(k => k.indexOf("dkcbb-src:") === 0).length)) === 0);
  check("no page errors", !errors.length, errors.join("; "));
  await b.close();
  passes.forEach(p => console.log("ok   " + p));
  fails.forEach(f => console.log("FAIL " + f));
  console.log(passes.length + " passed, " + fails.length + " failed");
  process.exit(fails.length ? 1 : 0);
})();
