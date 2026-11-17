/* The site's navigation, one definition for every page (this repo, the home page and the survivor book).
   A page puts <nav id="sitenav" data-sport="nba" data-page="results"></nav> where the tabs go and loads this script
   right after it. Row 1: Home, one tab per sport, Live (red, last). Row 2: the current sport's pages.
   The board can move the current tab as its slate changes (NFL <-> CFB): SiteNav.set("cfb", "board"). */
(function () {
  var B = "/br_rankings/";
  var SPORTS = [
    { key: "nfl", label: "NFL", pages: [{ key: "board", label: "Board", href: B + "?league=nfl" }, { key: "analysis", label: "Analysis", href: B + "analysis.html" },
                                        { key: "survivor", label: "Survivor", href: "/survivor/" }] },
    { key: "nba", label: "NBA", pages: [{ key: "board", label: "Board", href: B + "nba.html" }, { key: "results", label: "Results", href: B + "nba_results.html" }] },
    { key: "cbb", label: "CBB", pages: [{ key: "board", label: "Board", href: B + "cbb.html" }, { key: "dk", label: "DK", href: B + "dk.html" }] },
    { key: "cfb", label: "CFB", pages: [{ key: "board", label: "Board", href: B + "?league=cfb" }] }
  ];
  var LIVE = B + "nba_live.html";

  var css = ".sitenav{display:flex;flex-direction:column;gap:6px;align-self:center}" +
    ".sitenav .tabs{display:inline-flex;flex-wrap:wrap;border:1px solid #2a3140;border-radius:8px;overflow:hidden;align-self:flex-start}" +
    ".sitenav a{font:600 12.5px/1 \"Archivo\",system-ui,-apple-system,\"Segoe UI\",sans-serif;padding:7px 12px;color:#8b94a4;text-decoration:none}" +
    ".sitenav .tabs a:hover{color:inherit}" +
    ".sitenav .tabs a[aria-current=page]{background:#fff;color:#080b11}" +
    ".sitenav .tabs a.live{background:#b9443b;color:#fff}" +
    ".sitenav .tabs a.live:hover{background:#d03b3b}" +
    ".sitenav .tabs a.live[aria-current=page]{background:#d03b3b;box-shadow:inset 0 0 0 2px #fff}" +
    ".sitenav .sub{display:flex;flex-wrap:wrap;gap:4px}" +
    ".sitenav .sub a{font-size:12px;padding:5px 10px;border-radius:6px;border:1px solid transparent}" +
    ".sitenav .sub a:hover{color:inherit;border-color:#8b94a4}" +
    ".sitenav .sub a[aria-current=page]{color:inherit;border-color:currentColor}" +
    ".sitenav a:focus-visible{outline:2px solid #fff;outline-offset:1px}" +
    "@media (max-width:560px){.sitenav a{padding:6px 8px;font-size:12px}}";
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  var nav = document.getElementById("sitenav");
  if (!nav) return;
  nav.className = (nav.className ? nav.className + " " : "") + "sitenav";
  nav.setAttribute("aria-label", "Site");

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
