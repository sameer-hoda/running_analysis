# LinkedIn post 1 (DRAFT, not posted) — founder story

I am training for a half marathon and I kept forgetting how many days were left, so I started building mynextpr: a small web app that writes the race countdown into each run's Strava activity description.

The flow is deliberately tiny. Three taps (distance, month, race), an optional target finish like sub-2, then Connect with Strava. After that every logged run carries a line such as `15 days to go for Delhi Half Marathon. Easy run. Target sub-2.` Race-day runs read `Race day for Delhi Half Marathon. Easy run.` Past races write nothing.

Two constraints shaped everything. The app writes descriptions only and never touches activity titles. It requests the minimum Strava scopes, `read` plus `activity:write`, on the user's own activities, after explicit consent.

It is a pre-launch mock today. The Connect button flips preview text; production uses the official Strava OAuth flow. I am sharing the build notes as I go and I want critical feedback from runners on what the description line should carry.
