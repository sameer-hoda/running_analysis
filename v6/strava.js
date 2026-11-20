/* Shared Strava connect helper (v6).
   Loads clientId/redirectUri/scopes from strava-config.js (local-only,
   git-ignored, generated from .env). No secrets live in this file.
   Minimal scopes: read (identity) + activity:read (find the new run) +
   activity:write (update description only). */
(function () {
  "use strict";
  function cfg() {
    return window.MYNEXTPR_STRAVA || {};
  }
  function oauthState(state) {
    var nonce = "";
    try {
      var m = document.cookie.match(/(?:^|;\s*)mnp_oauth=([^;]*)/);
      nonce = m ? decodeURIComponent(m[1]) : "";
    } catch (e) {}
    var obj = null;
    try { obj = JSON.parse(state); } catch (e) { obj = null; }
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
      obj = { next: state };
    }
    obj.nonce = nonce;
    return JSON.stringify(obj);
  }
  function authorizeUrl(state) {
    var c = cfg();
    var u = new URL("https://www.strava.com/oauth/authorize");
    u.searchParams.set("client_id", c.clientId || "");
    u.searchParams.set("redirect_uri", c.redirectUri || "http://localhost:8123/callback.html");
    u.searchParams.set("response_type", "code");
    u.searchParams.set("scope", c.scopes || "read,activity:read,activity:write");
    u.searchParams.set("approval_prompt", "auto");
    if (state) u.searchParams.set("state", oauthState(state));
    return u.toString();
  }
  function ready() {
    var c = cfg();
    return !!(c.clientId && c.redirectUri);
  }
  window.MyNextPRStrava = { config: cfg, authorizeUrl: authorizeUrl, ready: ready };
})();
