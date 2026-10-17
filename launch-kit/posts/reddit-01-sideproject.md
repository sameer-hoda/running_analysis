# Reddit post 1 (DRAFT, not posted)

Target subreddit: r/SideProject
Rule check: r/SideProject exists for sharing projects. Self-promo builder stories are allowed. No promo-day restriction found. Multiple launch guides list it as self-promo OK with story plus demo.
Compliance: POST allowed. Disclose builder status in the opening lines (done below). One post only, no cross-posting identical text elsewhere. Flair as appropriate.
Decision: POST.

---

Title: I built a tiny app that writes my race countdown into my Strava run descriptions

I am the builder, and this is pre-launch with a mock UI. No signup link yet.

I am training for a half marathon and I kept losing count of the days left. So I built mynextpr: pick a race in three taps (distance, month, race), optionally set a target finish, connect Strava, and every run you log afterward gets a countdown line added to its Strava activity description. Example: `15 days to go for Delhi Half Marathon. Easy run. Target sub-2.`

Three decisions I would like feedback on:

1. It writes descriptions only, never titles. My title stays mine.
2. It asks for `read` + `activity:write` only, own activities, consent first.
3. Connect stays disabled until an upcoming race is picked. Past races stay unconnectable, so it can never count down to a race that already happened.

Edge cases handled: `1 day to go` singular, `Race day for Delhi Half Marathon. Easy run.` on the day, and nothing written once the date passes. Five run kinds (Easy, Tempo, Long, Recovery, Intervals), default Easy when unsure.

What I want to know: would you trust an app to write into your activity descriptions, and what would the line need to carry for you?
