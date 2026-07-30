# SteadyFit — Product Roadmap

Post-cohort product direction. Capstone Tasks 1–7, eval evidence, and Demo Day
keep-list live in **README.md** (Tasks 1–7) and **IMPROVEMENTS_LOG.md**. This
file is the forward-looking roadmap only.

> **Note (Jul 2026):** `ROADMAP.md` was not present in the repo when founder-mode
> retention notes were merged in. Phase 1 bullets below are consolidated from
> Task 7 “Change or improve post-cohort” / IMPROVEMENTS_LOG “Still future.”
> Phase 2 and Standing Principles include the Jul 2026 retention reflection.

---

## Standing Principles

- **A miss is information, not failure.** Tone stays warm and non-punishing;
  plan changes bend around life instead of shaming the user for slipping.
- **Meet people where their attention already is.** Every high-leverage
  retention feature shares one shape: reduce what the user has to remember to
  do *inside* the app, and surface value where they’re already looking (texts,
  their real calendar, wearables they already use) rather than asking them to
  build a new habit of opening SteadyFit.
- **Anti-pattern — no gamification** (streaks-as-scoreboard, badges,
  leaderboards). That playbook directly contradicts the product thesis. A streak
  counter is a shame mechanic in a different costume. Resist adding it even
  though it’s the standard fitness-app engagement move — it’s the wrong
  playbook for SteadyFit specifically.
- **Anti-pattern — no social feed / community for v1.** Feels valuable; is
  actually a distraction and a moderation burden for a busy-person audience
  with no spare attention for a feed.

---

## Phase 1 (near-term / stretch)

Items carried from Task 7 post-cohort / IMPROVEMENTS_LOG “still future”:

- **Real auth (Clerk/Auth0)** instead of `X-User-Id` / try-profile switcher —
  deprioritised while switcher + try-profiles already prove multi-tenancy.
- **Google Calendar OAuth (read)** — replace `mock_calendar.json` so the
  Scheduler sees real conflicts. (Write-back is Phase 2 — see below.)
- **Streaming UI responses** — polish, not product.
- **Meal swap / diet adherence tracking** — explicitly out of Phase 1 diet
  scope; still a near-term product gap after TDEE + planned meals shipped.
- **Faithfulness improvement** — explicit citation instructions in agent
  prompts to close the hybrid-retrieval faithfulness gap.

### Pulled forward (shipped this week — not Phase 2)

- **“I have 10 minutes” instant-workout button** — persistent chat chip + Plan
  page CTA; deterministic 10-minute session from profile modes/constraints,
  no week re-plan / HITL (`app/graph/micro_workout.py`).

---

## Phase 2 — Retention without requiring an app visit

Busy-person retention is less about richer in-app features and more about
reaching people who did **not** open SteadyFit first.

- **Proactive channel — SMS / WhatsApp text nudges first** (web-push PWA and/or
  Telegram remain secondary options). Priority is text-based delivery over push
  notifications: push gets muted within a week; busy people still read texts.
  The Adherence agent’s output is only valuable if it reaches someone who
  didn’t have to open the app first.
- **Write to calendar, not just read from it** — once real Google Calendar
  OAuth lands (Phase 1 stretch), the Scheduler should also **write** workout
  blocks onto the user’s real calendar, not only read conflicts. A calendar
  block reads as a commitment in a way an app notification doesn’t.
- **Passive workout logging via Apple Health / Google Fit sync** — reduce
  manual logging further (photo meal logging already does this for food). A
  workout done via Strava / Peloton / gym check-in should auto-count without
  the user re-entering it in SteadyFit.
- **Zero-tap weekly digest via email / text** — the Sunday weekly review
  already generates a strong summary internally; today that value only lands
  if someone opens the app. Send the digest passively instead of requiring a
  visit.
