/* The site's navigation, one definition for every page (this repo, the home page and the survivor book).
   A page puts <nav id="sitenav" data-sport="nba" data-page="results"></nav> where the tabs go and loads this script
   right after it. It draws one bar at the top of the body: Home, one tab per sport, Live (red, last), then the current sport's pages.
   The board can move the current tab as its slate changes (NFL <-> CFB): SiteNav.set("cfb", "board"). */
(function () {
  var B = "/br_rankings/";
  var SPORTS = [
    { key: "nfl", label: "NFL", pages: [{ key: "board", label: "Board", href: B + "?league=nfl" }, { key: "analysis", label: "Analysis", href: B + "analysis.html" },
                                        { key: "playoffs", label: "Playoffs", href: B + "nfl_playoffs.html" },
                                        { key: "survivor", label: "Survivor", href: "/survivor/" }] },
    { key: "nba", label: "NBA", pages: [{ key: "board", label: "Board", href: B + "nba.html" }, { key: "results", label: "Results", href: B + "nba_results.html" }] },
    { key: "cbb", label: "CBB", pages: [{ key: "board", label: "Board", href: B + "cbb.html" }, { key: "dk", label: "DK", href: B + "dk.html" }] },
    { key: "cfb", label: "CFB", pages: [{ key: "board", label: "Board", href: B + "?league=cfb" }, { key: "cfp", label: "CFP", href: B + "cfp.html" }] }
  ];
  var LIVE = B + "nba_live.html";

  // One bar across the top of every page, dark on every page (the survivor book is light), in the board's font.
  var css = ".sitebar{background:#080b11;border-bottom:1px solid #2a3140;padding:10px 20px;margin:0;box-sizing:border-box;width:100%}" +
    ".sitenav{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px}" +
    ".sitenav .tabs{display:inline-flex;flex-wrap:wrap;border:1px solid #2a3140;border-radius:8px;overflow:hidden}" +
    ".sitenav a{font:600 12.5px/1 \"Archivo\",system-ui,-apple-system,\"Segoe UI\",sans-serif;padding:7px 12px;color:#8b94a4;text-decoration:none}" +
    ".sitenav .tabs a:hover{color:#fff}" +
    ".sitenav .tabs a[aria-current=page]{background:#fff;color:#080b11}" +
    ".sitenav .tabs a.live{background:#b9443b;color:#fff}" +
    ".sitenav .tabs a.live:hover{background:#d03b3b}" +
    ".sitenav .tabs a.live[aria-current=page]{background:#d03b3b;box-shadow:inset 0 0 0 2px #fff}" +
    ".sitenav .sub{display:flex;flex-wrap:wrap;gap:4px}" +
    ".sitenav .sub a{font-size:12px;padding:6px 10px;border-radius:6px;border:1px solid transparent}" +
    ".sitenav .sub a:hover{color:#fff;border-color:#2a3140}" +
    ".sitenav .sub a[aria-current=page]{color:#fff;border-color:#fff}" +
    ".sitenav a:focus-visible{outline:2px solid #fff;outline-offset:1px}" +
    "@media (max-width:560px){.sitebar{padding:8px 12px}.sitenav a{padding:6px 8px;font-size:12px}}";
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);
  if (!document.querySelector('link[href*="family=Archivo"]')) {
    var f = document.createElement("link");
    f.rel = "stylesheet";
    f.href = "https://fonts.googleapis.com/css2?family=Archivo:wght@600&display=swap";
    document.head.appendChild(f);
  }

  var nav = document.getElementById("sitenav");
  if (!nav) return;
  nav.className = (nav.className ? nav.className + " " : "") + "sitenav";
  nav.setAttribute("aria-label", "Site");
  // Wherever the page put the placeholder, the bar goes first in the body, so it sits in the same place everywhere.
  var bar = document.createElement("header");
  bar.className = "sitebar";
  bar.appendChild(nav);
  document.body.insertBefore(bar, document.body.firstChild);

  function link(parent, label, href, current, cls) {
    var a = document.createElement("a");
    a.textContent = label;
    a.href = href;
    if (cls) a.className = cls;
    if (current) a.setAttribute("aria-current", "page");
    parent.appendChild(a);
    return a;
  }

  function render(sport, page) {
    nav.textContent = "";
    nav.dataset.sport = sport || "";
    nav.dataset.page = page || "";
    var tabs = document.createElement("div");
    tabs.className = "tabs";
    nav.appendChild(tabs);
    link(tabs, "Home", "/", page === "home");
    SPORTS.forEach(function (s) { link(tabs, s.label, s.pages[0].href, sport === s.key); });
    link(tabs, "Live", LIVE, page === "live", "live");
    var cur = SPORTS.filter(function (s) { return s.key === sport; })[0];
    if (cur && cur.pages.length > 1) {
      var sub = document.createElement("div");
      sub.className = "sub";
      nav.appendChild(sub);
      cur.pages.forEach(function (p) { link(sub, p.label, p.href, p.key === page); });
    }
  }

  // The board is one page for every sport: it says which by its query, until its slate says otherwise.
  var sport = nav.dataset.sport, page = nav.dataset.page;
  if (sport === "board") {
    var q = new URLSearchParams(location.search);
    sport = q.get("sport") === "nba" ? "nba" : q.get("sport") === "cbb" ? "cbb" : q.get("league") === "cfb" ? "cfb" : "nfl";
  }
  render(sport, page);
  window.SiteNav = { set: render, sports: SPORTS };
})();
