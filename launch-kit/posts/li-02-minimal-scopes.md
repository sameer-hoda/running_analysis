# LinkedIn post 2 (DRAFT, not posted) — minimal scopes

A note on restraint in integrations, from building mynextpr.

My app needs exactly two Strava scopes: `read` and `activity:write`. Sign-in happens on strava.com, which never shows this page a password. Writes go to the activity description only, never the title, on the authenticated user's own activities, only after consent. Disconnecting stops future updates and stored tokens are deleted. Past runs stay as they are.

The product decision I am proudest of is a disabled button. Connect stays off until an upcoming race is picked, and a race whose date passed keeps it off. One afternoon of work, and it removes a whole class of wrong-countdown bugs.

Pre-launch mock. If you build on third-party APIs, I would argue the narrowest scope that does the job is a feature, not a limitation.
