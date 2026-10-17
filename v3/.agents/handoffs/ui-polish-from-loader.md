# loader → ui-polish (2026-09-12)

JOB_PAGE now has thumb row (64px rounded img + filename + elapsed timer), `#ncdn` fallback line, Cancel/Retry ghost buttons (inline styles copying `.btn.ghost`).

## Request: tokens for loader
- `thumbrow` / `#thumb` style to match landing `.thumb` style (landing owns it — I inlined, please replace with shared token).
- Ghost-button token reuse for `#cancel`/`#retry` (I duplicated `.btn.ghost` inline since CSS is integrator/landing-owned).
- `#pct` / `.stages` colors already use `var(--ink)/--dim/--lime` — fine as-is.

No action needed urgently; inline styles work. Just fold into your shared-CSS pass when ready.
