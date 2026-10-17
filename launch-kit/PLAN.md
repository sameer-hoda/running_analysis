# mynextpr Launch Plan (v6 mock UI, pre-launch)

Status: DRAFTS ONLY. Nothing here is posted, scheduled, or published. The app is a pre-launch mock. The v6 `Connect with Strava` button only flips preview text. Production will use the official Strava OAuth flow with server-side token exchange. Do not claim a live product anywhere.

## 1. Positioning

One-liner: mynextpr writes a race countdown into your Strava activity descriptions, automatically, after every run you log.

What makes it defensible: restraint. Description-only writes. Your activity titles are never touched. Minimum OAuth scopes (`read` + `activity:write`). Only your own activities, only after explicit consent. Brand label is `Compatible with Strava`. No endorsement claimed, no Strava logo.

Proof points from the actual product (use these in copy, never invent others):
- Three taps: distance, month, race. Then connect and forget about it.
- Connect stays disabled until an upcoming race is picked. Past races stay unconnectable. Race day itself stays connectable.
- Description template: `15 days to go for Delhi Half Marathon. Easy run.` Goal variant appends `Target sub-2.` last.
- Singular handled: `1 day to go for Vedanta Delhi Half Marathon.` Race-day edge: `Race day for Delhi Half Marathon. Easy run.` Past race: no line written, ever.
- Run kinds fixed to Easy, Tempo, Long, Recovery, Intervals. Default Easy when unsure.
- Three manage styles: Days to go (default), Motivational (rotates `One run closer.` / `Stack the miles.` / `Trust the buildup.` / `Keep showing up.`), Auto run classification (kind first).
- Every written description ends with its own `— countdown by mynextpr` attribution line.
- Race data: MyNextBib feed snapshot, 104 events, generated 2026-10-10. Example races: Delhi Half Marathon (2026-10-18), Mysuru Marathon 26 (2026-12-12).
- No testimonials, customers, benchmarks, pricing, or licensing claims exist. Never fabricate them.

## 2. Core message

CORE (use everywhere first): "Every run you log carries its countdown in its Strava description. Your titles stay yours."

Backup A (mechanism-forward): "Pick your race in three taps. Every run after that shows the days left."
Backup B (goal-forward): "Set the target. Chase it every run. The countdown and the goal sit in the description, side by side."

## 3. Content pillars

1. Build in public (40%). Mock screenshots, decisions, restraint choices. E.g. why Connect is gated, why titles are sacred.
2. Runner mechanics (30%). Countdown examples with real race names and numbers, singular and race-day edges, run-kind classification.
3. Trust and scopes (20%). What `read` + `activity:write` means in plain words, own-activities-only, disconnect behavior.
4. Ask and listen (10%). Questions to running communities, feedback requests, no links unless asked.

## 4. Channel plan

- X: build-in-public thread fragments, one screenshot per post, reply to running-tech conversations. 5 drafts in posts/.
- Instagram: carousel or single image plus caption. On-image text max 3 words. 3 drafts in posts/.
- LinkedIn: founder story plus a scope-restraint engineering post. 2 drafts in posts/.
- Reddit: r/SideProject allows self-promo builder stories (POST). r/running Rule 3 bans all self-promo including blogs and social links (COMMENT-FIRST, never post the app). r/AdvancedRunning Rule 7 bans ads and self-promo (COMMENT-FIRST, never post the app). Full per-sub notes in each reddit file.
- Strava clubs: one club announcement draft, to be posted by hand by a club owner after launch. Not posted now.

## 5. Two-week posting calendar (drafts queued, none scheduled)

Week 1:
- Mon: X-01 (what it does, with example line)
- Tue: IG-01 (countdown visual)
- Wed: X-02 (titles-are-sacred restraint post)
- Thu: LinkedIn-01 (founder story)
- Fri: X-03 (three-tap flow)
- Sat: Reddit r/SideProject post (builder story, with disclosure)
- Sun: rest, reply to comments only

Week 2:
- Mon: X-04 (race-day and past-race edges)
- Tue: IG-02 (goal variant)
- Wed: LinkedIn-02 (minimal scopes engineering post)
- Thu: X-05 (manage styles)
- Fri: IG-03 (run kinds)
- Sat: Strava club announcement (hand-post after launch)
- Sun: review metrics, pick one winner to repeat

Reddit comment-first work (r/running, r/AdvancedRunning): 2 to 3 genuine, link-free answers per week in training and Strava threads. Link only if someone asks directly. Comment drafts in posts/reddit-02 and posts/reddit-03.

## 6. Success metrics (first 30 days after launch)

- Waitlist or connect-intent signups: 100.
- X: 10+ meaningful replies from runners (not likes).
- Reddit: r/SideProject post score above 20, zero removals anywhere.
- Instagram: saves over likes; target 50 saves across 3 posts.
- LinkedIn: 5+ comments from builders or runners per post.
- Strava club: 20 members joined from the announcement.
- Kill rule: if two weeks produce zero signup intent, rewrite the core message before posting more.

## 7. Research grounding (GitHub topics)

Fetched https://github.com/topics/digital-marketing, https://github.com/topics/marketing-tools, and https://github.com/topics/marketing-skills (each also tried with ?o=desc&s=stars ordering). Most useful repos and playbooks for this indie launch:

1. [marketingtoolslist/awesome-marketing](https://github.com/marketingtoolslist/awesome-marketing) (from digital-marketing + marketing-tools topics). Tactic used: treat the "awesome list" pattern as distribution. After launch, submit mynextpr to curated running-tool and marketing-tool lists instead of buying ads. Source of the Week 2 "submit to 5 curated lists" task.
2. [marketinguys/awesome-gtm-engineering](https://github.com/marketinguys/awesome-gtm-engineering) (from marketing-tools topic). Tactics used: UTM discipline on every outbound link (`utm.io` convention noted in that repo) and minimal-stack attribution. Source of the metrics section: track one funnel (post click to connect intent) with UTM-tagged links, no bloated stack.
3. [paulbradish/awesome-digital-marketing](https://github.com/paulbradish/awesome-digital-marketing) (from digital-marketing topic). Tactic used: owned-list-first sequencing. Source of the calendar rule that every rented-platform post points toward an owned signup surface, and the "build in public" pillar weighting.
4. [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (surfaced via the `social` skill's tools registry reference; consistent with the marketing-skills topic). Tactic used: content atomization. Source of the repurposing rule: each pillar demo (e.g. the three-tap flow) ships once, then becomes one X post, one Reel caption, and one LinkedIn paragraph.
5. [mautic/mautic](https://github.com/mautic/mautic) (top-starred marketing automation project on the marketing-tools topic). Tactic used negatively: do not self-host a mail stack pre-launch. Source of the decision to keep email to a simple waitlist form until 500 signups.

## 8. Image status: RENDERED

All three PNGs were rendered with Gemini 2.5 Flash Image (nano banana) and visually checked: images/x-card.png (16:9 dawn runner, India Gate), images/ig-45.png (4:5 stride close-up, "15 days to go" overlay), images/hero.png (16:9 shoe-tying, negative space left). Prompts live in images/*.txt. Note: the X-card bib carries tiny illegible glyph marks at full size; fine at card sizes, regenerate if a large crop is needed.

## 9. Compliance reminders

- Strava brand: `Compatible with Strava` only. Never "powered by", "partnered", or "endorsed". No Strava logo in copy or images.
- Reddit: r/running and r/AdvancedRunning get comments only, never posts. r/SideProject post must disclose builder status in the first lines.
- Every claim must trace to v6/PRODUCT.md or v6/hero-copy.md. Pre-launch status must stay visible.
