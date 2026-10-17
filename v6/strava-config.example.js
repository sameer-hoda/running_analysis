// Local-only Strava web config. NOT committed (see .gitignore).
// Copy to strava-config.js and fill in, or regenerate from .env:
//   python3 -c "from dotenv import ..."  (see MAINTENANCE.md)
window.MYNEXTPR_STRAVA = {
  clientId: "",
  redirectUri: "http://localhost:8123/callback.html",
  scopes: "read,activity:read,activity:write"
};
