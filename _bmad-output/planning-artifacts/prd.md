---
stepsCompleted: ["step-01-init", "step-02-discovery", "step-02b-vision", "step-02c-executive-summary", "step-03-success", "step-04-journeys", "step-05-domain", "step-06-innovation", "step-07-project-type", "step-08-scoping", "step-09-functional", "step-10-nonfunctional", "step-11-polish"]
releaseMode: phased
inputDocuments:
  - "_bmad-output/planning-artifacts/product-brief-gym-tracker.md"
briefCount: 1
researchCount: 0
brainstormingCount: 0
projectDocsCount: 0
workflowType: 'prd'
classification:
  projectType: web_app
  domain: fitness/wellness
  complexity: low-medium
  projectContext: greenfield
---

# Product Requirements Document — GymTrack

**Author:** Gunturi.Mahesh
**Date:** 2026-05-04

---

## Executive Summary

GymTrack is a free, web-based multi-user fitness tracking platform for casual gym-goers who want to stay consistent without fighting their tools. It addresses a high-frequency failure pattern: users begin training with motivation, lose visibility into their progress, and quit — not from lack of effort, but from lack of feedback.

GymTrack makes progress visible at the moment it matters most. Users plan workouts, log sessions with minimal friction, and receive automatic personal record (PR) detection — a "you just hit your best bench press ever" notification that turns effort into measurable improvement. The PR signal is the north-star experience: the moment a casual gym-goer realizes they're actually getting stronger.

The platform is web-first and PWA-compatible — accessible from any device and browser without installation. All core features (workout planning, session logging, progress tracking, dashboards) are free with no paywalled analytics. This contrasts directly with Hevy, Jefit, and Strong — mobile-only, cluttered, or subscription-locked.

**Target User:** Casual gym-goers (3x/week, non-competitive) who have churned from existing apps due to complexity or paywall friction.

**Core Outcome:** A user who logs consistently for 30 days and can identify at least one measurable strength improvement surfaced automatically by the app.

### What Makes This Special

The fitness tracking market has optimized for serious athletes and recurring revenue — leaving the majority of casual users underserved. GymTrack's differentiation is structural:

- **Free forever** — PR detection, progress charts, and dashboards are the product, not premium upsells
- **Web-first / PWA** — full-featured on any screen without a download; closes the planning-on-desktop / logging-on-phone gap competitors ignore
- **Radical simplicity** — UI designed for 30-second workout logging; every element earns its presence
- **Automatic PR detection** — the highest-value motivational signal, surfaced without configuration

The durable competitive advantage is execution discipline: simplicity requires constant restraint.

## Project Classification

| Field | Value |
|---|---|
| **Project Type** | Web App — MPA (Flask + HTML/CSS), PWA-compatible |
| **Domain** | Fitness & Wellness (general — no regulatory requirements) |
| **Complexity** | Low-Medium — standard auth, CRUD data model, charting/analytics |
| **Project Context** | Greenfield — new product, no existing codebase |
| **Team** | Solo developer |

---

## Success Criteria

### User Success

- **Retention signal:** ≥ 40% of new users return within 7 days of signup
- **Engagement depth:** Active users log ≥ 2 workouts per week
- **PR moment:** ≥ 60% of users who log ≥ 5 sessions receive at least one automatic PR notification
- **Onboarding success:** Users complete their first workout log within 10 minutes of signup

### Business Success

- **3-month target:** 500 monthly active users (MAU)
- **12-month target:** 5,000 MAU
- **30-day retention:** ≥ 30% of users active after 30 days
- **90-day retention:** ≥ 20% of users active after 90 days

### Measurable Outcomes

- **North-star:** Workouts logged per user per week (target ≥ 2 for active users)
- **Health metric:** 7-day return rate ≥ 40%
- **Growth metric:** MAU growth month-over-month

---

## User Journeys

### Journey 1: Alex — First-Time User (Happy Path)

**Who:** Alex, 28, office worker, gym 3x/week. Tried Hevy (didn't stick) and a notes app (messy).

**Scene:** Monday evening, Alex opens GymTrack on a laptop to plan the week. Signup: email, password, done in 45 seconds. No onboarding questionnaire. No paywall.

Alex searches "bench press" in the exercise library — instant result. Builds "Push Day A" with bench press, shoulder press, and tricep dips. Takes 4 minutes. Saved.

Tuesday at the gym: Alex opens GymTrack on the phone browser. Logs 3 sets of bench press — weight and reps, one tap per set. Clean, fast, distraction-free.

**Climax:** After the third session, GymTrack surfaces: *"New PR — Bench Press: 70kg × 5 reps. Your best ever."* Alex opens the progress chart — a visible upward line over 3 weeks. Takes a screenshot. The habit is forming.

**Capabilities revealed:** Exercise library search, workout plan builder, in-session logging, PR detection, per-exercise progress chart, personal dashboard.

---

### Journey 2: Alex — Edge Case (Interrupted Workout + Progress Review)

**Scene:** Mid-workout, 2 of 3 exercises logged, phone battery dies.

Alex charges the phone, reopens GymTrack — session is there, partial log preserved. Completes the remaining exercise.

Later that week, Alex opens the dashboard: workout frequency shows 11 sessions in 4 weeks vs. 7 last month. Volume trend is up 18%.

**Climax:** The app is not just a log — it's a mirror. Alex shows the progress dashboard to a gym buddy: "What app is that?"

**Capabilities revealed:** Auto-save per set (no data loss), session resume, workout history, period-comparative analytics.

---

### Journey 3: Platform Admin / Ops

**Who:** GymTrack internal ops (1–2 people).

**Scene:** Signup spike after a Reddit post. Admin checks the ops dashboard: active users, avg page load time, error rate — all green. A user submitted feedback: "Exercise library is missing Romanian Deadlift." Admin adds it in 2 minutes.

Three weeks later, a user reports login failure. Admin locates the account, triggers password reset. Resolved in under 5 minutes.

**Capabilities revealed:** Admin panel (exercise library management, user account management), system health dashboard, manual password reset.

---

### Journey 4: Returning User — Long Gap

**Who:** Sam, 34. Used GymTrack for 6 weeks, then stopped (holiday). Returns 8 weeks later.

**Scene:** Sam logs back in. Dashboard shows the last workout and a quiet prompt: *"Welcome back. Pick up where you left off?"* Sam resumes the routine. Progress chart shows the gap — and the progress made before it. Not shame, just data.

**Climax:** Sam completes a session and matches a pre-gap PR. GymTrack: *"Matched your pre-break PR on Squat. Strength holds."*

**Capabilities revealed:** Returning-user re-engagement state, gap-aware dashboard visualization, matched-PR detection.

---

### Journey Requirements Traceability

| Capability | Journeys |
|---|---|
| Exercise library (search, filter, curate) | J1, J3 |
| Workout plan builder | J1 |
| In-session logging (fast, mobile-optimized) | J1, J2 |
| Auto-save / data persistence per set | J2 |
| Automatic PR detection (new + matched) | J1, J4 |
| Per-exercise progress charts | J1, J2 |
| Dashboard (frequency, volume, streaks) | J2, J4 |
| Returning-user re-engagement state | J4 |
| Admin panel (exercise mgmt, user mgmt) | J3 |
| Ops health monitoring | J3 |

---

## Web App Technical Requirements

**Architecture:** Server-rendered MPA — Flask (Python) backend serving Jinja2-templated HTML pages; vanilla HTML5/CSS3 frontend; minimal JavaScript for interactive elements (set logger, Chart.js for charts).

**Stack rationale:** Deliberate simplicity — no framework overhead, fast to build, easy to maintain solo.

### Browser Support

| Browser | Support |
|---|---|
| Chrome (latest 2 versions) | ✅ Full |
| Firefox (latest 2 versions) | ✅ Full |
| Safari (latest 2 versions) | ✅ Full |
| Edge (latest 2 versions) | ✅ Full |
| Chrome Mobile / Safari iOS | ✅ Full (primary gym-floor experience) |
| IE11 / legacy browsers | ❌ Not supported |

### Responsive Design

- Mobile-first CSS — gym logging optimized for 375px+ screens; touch targets ≥ 44px
- Desktop layout for planning and dashboard review at 1024px+
- PWA manifest for home screen installability on iOS and Android

### Architecture Constraints

- No WebSockets or server-sent events in V1 — standard request/response sufficient
- PR detection computed server-side at workout save; surfaced on next page load
- No public-facing pages requiring SEO in V1 (logged-in app; marketing page gets basic meta tags only)
- Auth: Flask-Login session-based; SQLite for development, PostgreSQL for production

---

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Experience MVP — ship the complete core loop (planning → logging → PR detection → progress visibility) so early users experience the full value proposition from day one.

**Constraint:** Every feature must directly support workout planning, logging, PR detection, or progress visibility — or it waits.

### Phase 1 — MVP

**Journeys supported:** J1, J2, J4

**Must-have capabilities:**
- User authentication (signup, login, logout, password reset)
- Curated exercise library (≥ 50 exercises, searchable, muscle group filter)
- Workout plan builder (create, edit, delete, reuse routines)
- Workout session logger (plan-based or ad-hoc; auto-save each set)
- PR detection engine (new PRs + matched PRs, server-side at save time)
- PR notification on post-workout summary and dashboard
- Per-exercise strength progression chart (Chart.js)
- Personal dashboard (recent workouts, streak, PR highlights, frequency chart)
- Multi-user data isolation
- Responsive HTML/CSS — mobile-first

**Nice-to-have (ship if time permits):**
- Workout history list (all past sessions)
- Volume trend chart (total weight per week)
- PWA manifest

### Phase 2 — Growth

- Social layer (share workouts, public profiles, follow friends)
- Community workout templates (browse and fork)
- Advanced analytics (body part volume balance, weekly tonnage)
- Streak reminders and inactivity nudge notifications
- Coach-athlete program assignment

### Phase 3 — Vision

- Nutrition tracking integration
- Native iOS/Android apps
- B2B gym chain partnerships
- Premium analytics tier
- Wearable device integrations

### Risk Mitigation

| Risk | Mitigation |
|---|---|
| Solo dev scope creep | No Phase 2 feature touches MVP branch until Phase 1 ships |
| PR detection complexity | Build as isolated, independently testable service function |
| Chart performance | Chart.js (lightweight); complex visualizations deferred to Phase 2 |
| Data model inflexibility | Multi-user schema from day 1; social layer requires no rearchitecting |
| Market risk | Ship MVP to r/fitness and r/gainit; iterate on feedback before Phase 2 |

---

## Functional Requirements

### User Management

- **FR1:** Users can register a new account with email and password
- **FR2:** Users can log in to their account
- **FR3:** Users can log out of their account
- **FR4:** Users can reset their password via email link
- **FR5:** Users can view and edit their profile information
- **FR6:** Each user can only access their own data — no cross-user data visibility

### Exercise Library

- **FR7:** Users can browse a curated library of exercises
- **FR8:** Users can search the exercise library by name
- **FR9:** Users can filter exercises by muscle group
- **FR10:** Administrators can add exercises to the shared library
- **FR11:** Administrators can edit or remove exercises from the shared library

### Workout Planning

- **FR12:** Users can create a named workout plan (routine)
- **FR13:** Users can add exercises to a plan, specifying target sets and reps
- **FR14:** Users can edit a plan (add, remove, reorder exercises)
- **FR15:** Users can delete a workout plan
- **FR16:** Users can view a list of all their saved workout plans

### Workout Logging

- **FR17:** Users can start a session from an existing plan
- **FR18:** Users can start an ad-hoc session without a plan
- **FR19:** Users can log sets per exercise, recording weight and reps
- **FR20:** Each logged set is auto-saved immediately upon entry
- **FR21:** Users can resume a partially completed session if interrupted
- **FR22:** Users can mark a session as complete
- **FR23:** Users can view a history of all past sessions

### Personal Record (PR) Detection

- **FR24:** The system detects a new personal record when a session is saved
- **FR25:** The system detects when a user matches (without exceeding) a previous personal record
- **FR26:** Users see a PR notification on the post-workout summary screen
- **FR27:** Users can view all current personal records per exercise

### Progress Tracking & Charts

- **FR28:** Users can view a strength progression chart per exercise (best weight over time)
- **FR29:** Users can view a workout frequency chart (sessions per week/month)
- **FR30:** Users can view a volume trend chart (total weight lifted per week)
- **FR31:** Users can filter progress charts by time period (last 4 weeks, 3 months, all time)

### Personal Dashboard

- **FR32:** Users see a dashboard on login summarizing recent activity
- **FR33:** The dashboard displays the user's current workout streak
- **FR34:** The dashboard highlights the user's most recent personal records
- **FR35:** Users inactive ≥ 2 weeks see their last session and a resume prompt on login

### Administration & Operations

- **FR36:** Administrators can view a list of registered users
- **FR37:** Administrators can trigger a password reset for any user account
- **FR38:** Administrators can manage the shared exercise library (add, edit, remove)
- **FR39:** Administrators can view platform health metrics (active user count, error rate)

---

## Non-Functional Requirements

### Performance

- **NFR1:** Initial page load < 2 seconds on standard broadband (Lighthouse measurement)
- **NFR2:** Workout set save response < 500ms (must feel instant during in-gym logging)
- **NFR3:** Dashboard and chart pages render < 1 second after data load
- **NFR4:** Application remains responsive under 100 concurrent active users

### Security

- **NFR5:** Passwords stored as bcrypt hashes (cost factor ≥ 12); plaintext storage prohibited
- **NFR6:** All client-server transmission encrypted via HTTPS/TLS 1.2+
- **NFR7:** Sessions expire after 30 days of inactivity; tokens invalidated on logout
- **NFR8:** No API endpoint may return another user's data under any conditions
- **NFR9:** Password reset tokens expire within 1 hour and are single-use
- **NFR10:** Account deletion permanently removes all associated user data from the database

### Scalability

- **NFR11:** Architecture supports 5,000 MAU on a single server without rearchitecting
- **NFR12:** Database schema supports multi-user from day 1; no schema migrations required to add users
- **NFR13:** Static assets served with cache-control headers to minimize repeated server requests

### Reliability

- **NFR14:** Platform achieves 99.5% uptime (planned maintenance excluded)
- **NFR15:** Every logged set is persisted before the UI confirms success — no silent data loss
- **NFR16:** Server errors are handled gracefully — users see a friendly error page, never a raw stack trace

### Accessibility

- **NFR17:** All interactive elements are keyboard-navigable with visible focus indicators
- **NFR18:** Text contrast ratio ≥ 4.5:1 for body text and ≥ 3:1 for large text (WCAG 2.1 AA)
- **NFR19:** All form inputs have associated `<label>` elements; error messages are descriptive and actionable
