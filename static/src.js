// Remembers, for this browser tab only, which website sent the visitor here and the first page they
// opened, so the report form can say how people find the site. Only the referring site's domain is kept,
// never the full address or search terms. Stored in sessionStorage, which clears when the tab closes.
(function () {
  try {
    if (sessionStorage.getItem("sal_src")) return;
    var host = "";
    try { if (document.referrer) host = new URL(document.referrer).hostname.replace(/^www\./, ""); } catch (e) {}
    if (host === location.hostname.replace(/^www\./, "")) host = "";
    var utm = new URLSearchParams(location.search).get("utm_source") || "";
    var src = host || (utm ? "utm: " + utm.slice(0, 60) : "direct or unknown");
    if (host && utm) src += " (utm: " + utm.slice(0, 60) + ")";
    sessionStorage.setItem("sal_src", JSON.stringify({ from: src, landing: location.pathname.slice(0, 200) }));
  } catch (e) {}
})();
