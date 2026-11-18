/* mynextpr analytics consent (v6).
   Google Analytics 4 (G-B63L6BJZLY) loads ONLY after an explicit opt-in.
   - Choice persists in localStorage under "mnp.analytics" ("granted"/"denied").
   - Before opt-in: no analytics script, no analytics storage, no network.
   - After opt-in: page views only, with the URL query and hash stripped so
     OAuth codes (callback.html?code=...) can never reach analytics.
   - Never sends Strava athlete/activity data, tokens, identifiers, or
     personal data: this file makes no gtag("event") calls at all.
   - Essential login (mnp_athlete cookie, mynextpr.connected flag) never
     consults this file and works identically when analytics is rejected.
   - Change the choice any time on privacy.html (mnpConsent.grant/deny). */
(function () {
  "use strict";
  var MEASUREMENT_ID = "G-B63L6BJZLY";
  var STORE_KEY = "mnp.analytics";
  var loaded = false;

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  function readChoice() {
    try { return window.localStorage.getItem(STORE_KEY); }
    catch (e) { return null; }
  }
  function writeChoice(value) {
    try { window.localStorage.setItem(STORE_KEY, value); }
    catch (e) { /* private mode: choice lasts this visit; still no tracking */ }
  }
  /* Query/hash-free location: code, state, and error params stay local. */
  function cleanLocation() {
    try {
      return window.location.origin + window.location.pathname;
    } catch (e) { return "/"; }
  }
  function loadAnalytics() {
    if (loaded) return;
    loaded = true;
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
    document.head.appendChild(s);
    gtag("js", new Date());
    gtag("config", MEASUREMENT_ID, { page_location: cleanLocation() });
  }
  function hideBanner() {
    var b = document.getElementById("mnp-consent");
    if (b && b.parentNode) b.parentNode.removeChild(b);
  }
  function showBanner() {
    if (document.getElementById("mnp-consent")) return;
    var b = document.createElement("div");
    b.id = "mnp-consent";
    b.setAttribute("role", "dialog");
    b.setAttribute("aria-label", "Analytics consent");
    b.style.cssText = "position:fixed;left:12px;right:12px;bottom:12px;z-index:9999;" +
      "background:#16130F;color:#F6F2EA;border-radius:12px;padding:14px 16px;" +
      "font:400 14px/1.5 system-ui,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.35);";
    var p = document.createElement("p");
    p.style.margin = "0 0 10px";
    p.textContent = "Can we count visits with Google Analytics (page views on " +
      "mynextpr.com only)? No Strava data is ever sent to analytics. " +
      "You can change this anytime on the Privacy page.";
    var row = document.createElement("div");
    row.style.cssText = "display:flex;gap:10px;";
    var accept = document.createElement("button");
    accept.type = "button";
    accept.textContent = "Accept";
    accept.style.cssText = "flex:1;padding:10px;border-radius:8px;border:0;" +
      "background:#FC5200;color:#fff;font-weight:700;cursor:pointer;";
    accept.onclick = function () { window.mnpConsent.grant(); };
    var reject = document.createElement("button");
    reject.type = "button";
    reject.textContent = "Reject";
    reject.style.cssText = "flex:1;padding:10px;border-radius:8px;border:1px solid #8C8475;" +
      "background:transparent;color:#F6F2EA;font-weight:700;cursor:pointer;";
    reject.onclick = function () { window.mnpConsent.deny(); };
    row.appendChild(accept);
    row.appendChild(reject);
    b.appendChild(p);
    b.appendChild(row);
    document.body.appendChild(b);
  }
  window.mnpConsent = {
    state: function () { return readChoice(); },
    grant: function () {
      writeChoice("granted");
      hideBanner();
      loadAnalytics();
      if (typeof document !== "undefined") {
        var ev = null;
        try { ev = new CustomEvent("mnp:consent", { detail: "granted" }); }
        catch (e) { ev = null; }
        if (ev) document.dispatchEvent(ev);
      }
    },
    deny: function () {
      writeChoice("denied");
      hideBanner();
      if (typeof document !== "undefined") {
        var ev = null;
        try { ev = new CustomEvent("mnp:consent", { detail: "denied" }); }
        catch (e) { ev = null; }
        if (ev) document.dispatchEvent(ev);
      }
    }
  };
  /* Page boot: honor a stored opt-in; otherwise show the banner and wait. */
  function boot() {
    if (readChoice() === "granted") {
      loadAnalytics();
      return;
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", showBanner);
    } else {
      showBanner();
    }
  }
  boot();
})();
