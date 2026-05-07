---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/architecture.md"
workflowType: 'epics-and-stories'
project_name: 'GymTrack'
---

# GymTrack - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for GymTrack, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Users can register a new account with email and password
FR2: Users can log in to their account
FR3: Users can log out of their account
FR4: Users can reset their password via email link
FR5: Users can view and edit their profile information
FR6: Each user can only access their own data — no cross-user data visibility
FR7: Users can browse a curated library of exercises
FR8: Users can search the exercise library by name
FR9: Users can filter exercises by muscle group
FR10: Administrators can add exercises to the shared library
FR11: Administrators can edit or remove exercises from the shared library
FR12: Users can create a named workout plan (routine)
FR13: Users can add exercises to a plan, specifying target sets and reps
FR14: Users can edit a plan (add, remove, reorder exercises)
FR15: Users can delete a workout plan
FR16: Users can view a list of all their saved workout plans
FR17: Users can start a session from an existing plan
FR18: Users can start an ad-hoc session without a plan
FR19: Users can log sets per exercise, recording weight and reps
FR20: Each logged set is auto-saved immediately upon entry
FR21: Users can resume a partially completed session if interrupted
FR22: Users can mark a session as complete
FR23: Users can view a history of all past sessions
FR24: The system detects a new personal record when a session is saved
FR25: The system detects when a user matches (without exceeding) a previous personal record
FR26: Users see a PR notification on the post-workout summary screen
FR27: Users can view all current personal records per exercise
FR28: Users can view a strength progression chart per exercise (best weight over time)
FR29: Users can view a workout frequency chart (sessions per week/month)
FR30: Users can view a volume trend chart (total weight lifted per week)
FR31: Users can filter progress charts by time period (last 4 weeks, 3 months, all time)
FR32: Users see a dashboard on login summarizing recent activity
FR33: The dashboard displays the user's current workout streak
FR34: The dashboard highlights the user's most recent personal records
FR35: Users inactive ≥ 2 weeks see their last session and a resume prompt on login
FR36: Administrators can view a list of registered users
FR37: Administrators can trigger a password reset for any user account
FR38: Administrators can manage the shared exercise library (add, edit, remove)
FR39: Administrators can view platform health metrics (active user count, error rate)

### NonFunctional Requirements

NFR1: Initial page load < 2 seconds on standard broadband (Lighthouse measurement)
NFR2: Workout set save response < 500ms (must feel instant during in-gym logging)
NFR3: Dashboard and chart pages render < 1 second after data load
NFR4: Application remains responsive under 100 concurrent active users
NFR5: Passwords stored as bcrypt hashes (cost factor ≥ 12); plaintext storage prohibited
NFR6: All client-server transmission encrypted via HTTPS/TLS 1.2+
NFR7: Sessions expire after 30 days of inactivity; tokens invalidated on logout
NFR8: No API endpoint may return another user's data under any conditions
NFR9: Password reset tokens expire within 1 hour and are single-use
NFR10: Account deletion permanently removes all associated user data from the database
NFR11: Architecture supports 5,000 MAU on a single server without rearchitecting
NFR12: Database schema supports multi-user from day 1; no schema migrations required to add users
NFR13: Static assets served with cache-control headers to minimize repeated server requests
NFR14: Platform achieves 99.5% uptime (planned maintenance excluded)
NFR15: Every logged set is persisted before the UI confirms success — no silent data loss
NFR16: Server errors are handled gracefully — users see a friendly error page, never a raw stack trace
NFR17: All interactive elements are keyboard-navigable with visible focus indicators
NFR18: Text contrast ratio ≥ 4.5:1 for body text and ≥ 3:1 for large text (WCAG 2.1 AA)
NFR19: All form inputs have associated `<label>` elements; error messages are descriptive and actionable

### Additional Requirements

- Project scaffolding: Initialize Flask Application Factory project structure (virtualenv, pip install, config.py, create_app(), extensions.py, Blueprint registration) — this is Epic 1 Story 1
- Multi-user data isolation enforced at service layer: ALL queries on user-owned models MUST use `.filter_by(user_id=current_user.id)` — no exceptions
- Password hashing: flask-bcrypt with work factor 12 — applied at registration and password reset
- Session storage: Flask client-side encrypted cookies, `PERMANENT_SESSION_LIFETIME = timedelta(days=30)`, `SESSION_COOKIE_SECURE=True` in production
- CSRF protection: Flask-WTF on all POST/PUT/DELETE forms via `{{ form.hidden_tag() }}`
- Password reset tokens: `itsdangerous.URLSafeTimedSerializer`, expire in 1 hour, single-use
- Auto-save JSON endpoint: `POST /api/sessions/<id>/sets` — minimal hot path, must complete <500ms; PR detection NOT triggered on this path
- PR detection: pure function `detect_prs(user_id, session_id)` in `app/services/pr_detection.py`, called ONCE at session completion only
- Deployment: Railway — Git push deploys, Gunicorn WSGI (`wsgi.py`), PostgreSQL add-on, env vars via Railway UI
- Error monitoring: Sentry (Flask SDK, initialized in `create_app()`) + Python `logging` module
- CI/CD: GitHub Actions — flake8 + pytest on PR/push, deploy to Railway on merge to main
- PWA: `manifest.json` + Service Worker for home screen installability
- Chart.js: CDN-loaded in templates that need charts (progress, dashboard); data passed via `json.dumps()` in `<script>` tag — no separate API call for initial render
- Flask-Mail with SMTP for password reset emails (env vars: MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD)
- Error handlers: `@app.errorhandler` for 400, 403, 404, 500 — HTML pages for page routes, JSON for `/api/*`
- SQLite for development, PostgreSQL for production — same ORM code, different connection string

### UX Design Requirements

No UX design document was found. UX requirements are derived from PRD and Architecture:

- UX-DR1: Mobile-first responsive CSS — gym logging optimized for 375px+ screens; touch targets ≥ 44px
- UX-DR2: Desktop layout for planning and dashboard review at 1024px+
- UX-DR3: Single `style.css` with BEM naming (`block__element--modifier`) — no preprocessor
- UX-DR4: Flash message UI categories: `success`, `error`, `info`, `warning` (rendered in `base.html`)
- UX-DR5: Workout session log page loads `set-logger.js` for AJAX auto-save without page refresh
- UX-DR6: Progress and dashboard pages load Chart.js from CDN and initialize via `charts.js`
- UX-DR7: Post-workout summary shows PR banner notification when new/matched PRs detected
- UX-DR8: Returning-user dashboard (inactive ≥ 2 weeks) shows last session with resume prompt
- UX-DR9: Semantic HTML + ARIA roles across all templates; keyboard navigation with visible focus indicators
- UX-DR10: All form inputs have `<label>` elements; error messages are descriptive and placed adjacent to fields

### FR Coverage Map

FR1: Epic 1 — User registration
FR2: Epic 1 — User login
FR3: Epic 1 — User logout
FR4: Epic 1 — Password reset via email
FR5: Epic 1 — View/edit profile
FR6: Epic 1 — Per-user data isolation
FR7: Epic 2 — Browse exercise library
FR8: Epic 2 — Search exercises by name
FR9: Epic 2 — Filter by muscle group
FR10: Epic 2 — Admin: add exercises
FR11: Epic 2 — Admin: edit/remove exercises
FR12: Epic 3 — Create workout plan
FR13: Epic 3 — Add exercises to plan
FR14: Epic 3 — Edit plan
FR15: Epic 3 — Delete plan
FR16: Epic 3 — List all plans
FR17: Epic 4 — Start plan-based session
FR18: Epic 4 — Start ad-hoc session
FR19: Epic 4 — Log sets (weight + reps)
FR20: Epic 4 — Auto-save each set
FR21: Epic 4 — Resume interrupted session
FR22: Epic 4 — Complete session
FR23: Epic 4 — View session history
FR24: Epic 5 — Detect new PR
FR25: Epic 5 — Detect matched PR
FR26: Epic 5 — PR notification on post-workout screen
FR27: Epic 5 — View all PRs per exercise
FR28: Epic 6 — Strength progression chart
FR29: Epic 6 — Workout frequency chart
FR30: Epic 6 — Volume trend chart
FR31: Epic 6 — Filter charts by time period
FR32: Epic 7 — Dashboard: recent activity summary
FR33: Epic 7 — Dashboard: workout streak
FR34: Epic 7 — Dashboard: recent PRs
FR35: Epic 7 — Re-engagement prompt for inactive users
FR36: Epic 7 — Admin: user list
FR37: Epic 7 — Admin: trigger password reset
FR38: Epic 7 — Admin: manage exercise library
FR39: Epic 7 — Admin: platform health metrics

## Epic List

### Epic 1: Project Foundation & User Authentication
Users can register, log in, log out, and reset their password. The project scaffold is fully operational with security hardening, CI/CD pipeline, deployment to Railway, and error monitoring in place.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6
**Also covers:** Project scaffold (Flask Application Factory), flask-bcrypt, Flask-Login, Flask-WTF CSRF, itsdangerous password reset tokens, Flask-Mail, Railway deployment, GitHub Actions CI/CD, Sentry + Python logging, error handlers (400/403/404/500), SQLite (dev) / PostgreSQL (prod), PWA manifest

### Epic 2: Exercise Library
Users can browse, search, and filter a curated exercise library. Admins can add, edit, and remove exercises from the shared library.
**FRs covered:** FR7, FR8, FR9, FR10, FR11

### Epic 3: Workout Planning
Users can create named workout routines, add and reorder exercises with target sets and reps, edit plans, delete plans, and view all their plans.
**FRs covered:** FR12, FR13, FR14, FR15, FR16
**Depends on:** Epic 2 (exercises assigned to plans)

### Epic 4: Workout Logging & Auto-Save
Users can start plan-based or ad-hoc sessions, log sets with weight and reps (auto-saved per set to a JSON endpoint), resume interrupted sessions, mark sessions complete, and view all past sessions.
**FRs covered:** FR17, FR18, FR19, FR20, FR21, FR22, FR23
**Also covers:** UX-DR5 (set-logger.js AJAX auto-save), auto-save hot path <500ms
**Depends on:** Epic 2 (exercises), Epic 3 (plans)

### Epic 5: Personal Record Detection & Notifications
The system automatically detects new and matched PRs when a session is completed, shows a PR notification banner on the post-workout summary, and lets users view all their current PRs per exercise.
**FRs covered:** FR24, FR25, FR26, FR27
**Also covers:** UX-DR7 (PR banner on session complete screen)
**Depends on:** Epic 4 (sessions and sets data)

### Epic 6: Progress Tracking & Charts
Users can view per-exercise strength progression, workout frequency, and volume trend charts with time-period filters (4 weeks / 3 months / all time).
**FRs covered:** FR28, FR29, FR30, FR31
**Also covers:** UX-DR6 (Chart.js CDN, charts.js initialization)
**Depends on:** Epic 4 (set data), Epic 5 (PR data)

### Epic 7: Dashboard, Admin & Operations
Users see a personal dashboard with workout streak, recent PRs, and a re-engagement prompt when inactive ≥ 2 weeks. Admins can manage users, manage the exercise library, and view platform health metrics.
**FRs covered:** FR32, FR33, FR34, FR35, FR36, FR37, FR38, FR39
**Also covers:** UX-DR8 (returning-user resume prompt), services/streak.py, services/stats.py
**Depends on:** Epics 1–6 (aggregates all user and platform data)

---

## Epic 1: Project Foundation & User Authentication

Users can register, log in, log out, and reset their password. The project scaffold is fully operational with security hardening, CI/CD pipeline, deployment to Railway, and error monitoring in place.

### Story 1.1: Project Scaffold & Base Configuration

As a developer,
I want a fully initialized Flask project structure with Application Factory, config, extensions, base template, and error handlers,
So that all subsequent stories can be built on a consistent, production-ready foundation.

**Acceptance Criteria:**

**Given** a new empty repository
**When** the developer runs the initialization commands
**Then** the project structure matches the architecture spec (`gymtrack/app/`, `blueprints/`, `models/`, `services/`, `static/`, `templates/`, `tests/`, `migrations/`, `config.py`, `wsgi.py`)
**And** `create_app()` factory in `app/__init__.py` registers all extensions via `extensions.py` (db, login_manager, migrate, bcrypt)
**And** `DevelopmentConfig` uses SQLite; `ProductionConfig` uses `DATABASE_URL` env var for PostgreSQL
**And** `base.html` renders flash messages using categories: `success`, `error`, `info`, `warning`
**And** Flask error handlers for 400, 403, 404, 500 return custom HTML pages (no raw tracebacks)
**And** `requirements.txt` lists: flask, flask-sqlalchemy, flask-migrate, flask-login, flask-wtf, flask-bcrypt, flask-mail, python-dotenv, psycopg2-binary, gunicorn, sentry-sdk
**And** `.env.example` documents all required environment variables (`SECRET_KEY`, `DATABASE_URL`, `MAIL_SERVER`, etc.)
**And** `pytest` runs with zero errors on an empty test suite

### Story 1.2: User Registration

As a new visitor,
I want to register an account with my email and password,
So that I can access GymTrack's features.

**Acceptance Criteria:**

**Given** I am on `/auth/register`
**When** I submit a valid email and password (≥ 8 characters)
**Then** my account is created with the password stored as a bcrypt hash (cost factor 12) — never plaintext
**And** I am redirected to the dashboard with a `success` flash: "Account created. Welcome to GymTrack!"
**And** a `users` table row is created with `created_at` (UTC), `is_admin=False`

**Given** I submit an email that already exists
**When** the form is submitted
**Then** I see a field-level error: "An account with this email already exists."
**And** no duplicate record is created

**Given** I submit an invalid email or password shorter than 8 characters
**When** the form is submitted
**Then** Flask-WTF validation errors are displayed adjacent to the relevant field
**And** the form retains my previously entered values

### Story 1.3: User Login & Logout

As a registered user,
I want to log in and out of my account,
So that my data is accessible only to me.

**Acceptance Criteria:**

**Given** I am on `/auth/login` with valid credentials
**When** I submit the form
**Then** I am logged in via Flask-Login and redirected to `/dashboard/`
**And** my session persists for 30 days of inactivity (`PERMANENT_SESSION_LIFETIME`)

**Given** I submit incorrect credentials
**When** the form is submitted
**Then** I see an `error` flash: "Invalid email or password." (no indication of which field is wrong)
**And** I remain on the login page

**Given** I am logged in and click Logout
**When** `/auth/logout` is visited
**Then** my session is cleared (cookie deleted)
**And** I am redirected to `/auth/login` with an `info` flash: "You have been logged out."

**Given** I try to access a `@login_required` route while logged out
**When** the request is made
**Then** I am redirected to `/auth/login` with the original URL preserved as `next` parameter

### Story 1.4: Password Reset via Email

As a user who has forgotten their password,
I want to request a password reset link sent to my email,
So that I can regain access to my account.

**Acceptance Criteria:**

**Given** I am on `/auth/forgot-password` and submit a registered email
**When** the form is submitted
**Then** a signed `itsdangerous.URLSafeTimedSerializer` token (expires in 1 hour) is generated
**And** a reset email is sent via Flask-Mail to the submitted address containing the reset link
**And** I see: "If that email is registered, a reset link has been sent." (no email enumeration)

**Given** I click a valid, unexpired reset link (`/auth/reset-password/<token>`)
**When** I submit a new password (≥ 8 characters)
**Then** my password is updated as a new bcrypt hash
**And** I am redirected to `/auth/login` with a `success` flash: "Password updated. Please log in."

**Given** I click an expired or already-used reset link
**When** the page loads
**Then** I see an `error` flash: "This reset link has expired or is invalid."
**And** I am redirected to `/auth/forgot-password`

### Story 1.5: User Profile View & Edit

As a logged-in user,
I want to view and update my profile information,
So that my account details stay current.

**Acceptance Criteria:**

**Given** I am on `/auth/profile`
**When** the page loads
**Then** I see my current email address (read-only display)
**And** I see a form to change my password (current password + new password + confirm)

**Given** I submit the password change form with correct current password and matching new passwords
**When** the form is submitted
**Then** my password is updated as a new bcrypt hash
**And** I see a `success` flash: "Password updated successfully."

**Given** I submit an incorrect current password
**When** the form is submitted
**Then** I see an `error` flash: "Current password is incorrect."
**And** no change is made to my account

### Story 1.6: CI/CD Pipeline, Deployment & Error Monitoring

As a developer,
I want automated testing, deployment to Railway, and error monitoring configured,
So that every code push is validated and production errors are captured.

**Acceptance Criteria:**

**Given** a push or PR is made to any branch
**When** GitHub Actions CI runs
**Then** `flake8` lints the codebase (zero errors required to pass)
**And** `pytest` runs all tests (zero failures required to pass)

**Given** a merge to `main` branch
**When** GitHub Actions deploy job runs
**Then** the application deploys to Railway automatically

**Given** the application is running in production (`FLASK_ENV=production`)
**When** `create_app()` is called
**Then** Sentry SDK is initialized with the `SENTRY_DSN` env var
**And** unhandled exceptions are automatically reported to Sentry
**And** structured logging via `logging.getLogger(__name__)` is active in all modules

**Given** `FLASK_ENV=development`
**When** `create_app()` is called
**Then** Sentry is NOT initialized (no dev noise in Sentry dashboard)

---

## Epic 2: Exercise Library

Users can browse, search, and filter a curated exercise library. Admins can add, edit, and remove exercises from the shared library.

### Story 2.1: Exercise Library Browse

As a logged-in user,
I want to browse the full exercise library,
So that I can discover exercises to add to my workouts.

**Acceptance Criteria:**

**Given** I navigate to `/exercises/`
**When** the page loads
**Then** I see a paginated list of all exercises, each showing name, muscle group, and description
**And** the `exercises` table has columns: `id`, `name`, `muscle_group`, `description`, `created_at`
**And** exercises are sorted alphabetically by name by default
**And** the page is accessible to all logged-in users; unauthenticated users are redirected to login

### Story 2.2: Exercise Search & Filter

As a logged-in user,
I want to search exercises by name and filter by muscle group,
So that I can quickly find the exercise I need.

**Acceptance Criteria:**

**Given** I am on `/exercises/` and type a search term
**When** I submit the search form
**Then** the list shows only exercises whose name contains the search term (case-insensitive)
**And** the search term is preserved in the search input field

**Given** I select a muscle group from the filter dropdown
**When** the filter is applied
**Then** the list shows only exercises matching that muscle group
**And** search and filter can be combined (e.g., "press" + "Chest")

**Given** no exercises match the search/filter criteria
**When** the page renders
**Then** I see: "No exercises found matching your search."

### Story 2.3: Admin Exercise Management

As an administrator,
I want to add, edit, and remove exercises from the shared library,
So that the exercise list stays accurate and comprehensive.

**Acceptance Criteria:**

**Given** I am an admin at `/admin/exercises/`
**When** the page loads
**Then** I see the full exercise list with Add, Edit, and Delete controls per row

**Given** I submit the Add Exercise form with a valid name and muscle group
**When** the form is submitted
**Then** the new exercise appears in the library for all users
**And** I see a `success` flash: "Exercise added."

**Given** I edit an existing exercise and submit valid changes
**When** the form is submitted
**Then** the exercise is updated in the database and the change is visible to all users

**Given** I delete an exercise
**When** deletion is confirmed
**Then** the exercise is removed from the library
**And** I see a `success` flash: "Exercise removed."

**Given** a non-admin user tries to access `/admin/*`
**When** the request is made
**Then** they receive a 403 Forbidden response

---

## Epic 3: Workout Planning

Users can create named workout routines, add and reorder exercises with target sets and reps, edit plans, delete plans, and view all their plans.

### Story 3.1: Create Workout Plan

As a logged-in user,
I want to create a named workout plan,
So that I have a reusable routine to follow at the gym.

**Acceptance Criteria:**

**Given** I am on `/workouts/plans/new`
**When** I submit a valid plan name
**Then** a new `workout_plans` row is created with `user_id=current_user.id`, `name`, `created_at`
**And** I am redirected to the plan detail page with a `success` flash: "Plan created."
**And** the plan is only visible to me — no other user can access it

**Given** I submit a blank plan name
**When** the form is submitted
**Then** I see a field-level error: "Plan name is required."
**And** no record is created

### Story 3.2: Add Exercises to a Plan

As a logged-in user,
I want to add exercises to my workout plan with target sets and reps,
So that I have a structured routine to follow.

**Acceptance Criteria:**

**Given** I am on the plan detail page `/workouts/plans/<id>/`
**When** I add an exercise by selecting from the library and entering target sets and reps
**Then** a `plan_exercises` row is created: `plan_id`, `exercise_id`, `target_sets`, `target_reps`, `order_index`
**And** the exercise appears in the plan in the order it was added

**Given** I add a second exercise
**When** it is saved
**Then** it appears below the first, with `order_index` incremented

**Given** I try to access or modify another user's plan via URL manipulation
**When** the request is made
**Then** I receive a 404 response (`.filter_by(id=plan_id, user_id=current_user.id).first_or_404()`)

### Story 3.3: Edit & Reorder Plan Exercises

As a logged-in user,
I want to edit my plan by updating, reordering, or removing exercises,
So that I can refine my routine over time.

**Acceptance Criteria:**

**Given** I am editing a plan at `/workouts/plans/<id>/edit`
**When** I change the target sets or reps for an exercise and save
**Then** the `plan_exercises` row is updated with the new values

**Given** I remove an exercise from the plan
**When** the removal is confirmed
**Then** the `plan_exercises` row is deleted and the exercise no longer appears in the plan

**Given** I reorder exercises using up/down controls
**When** the order change is saved
**Then** `order_index` values are updated and exercises render in the new order

### Story 3.4: Delete Plan & View All Plans

As a logged-in user,
I want to delete plans I no longer need and see all my plans in one place,
So that I can keep my routine list clean and organized.

**Acceptance Criteria:**

**Given** I am on `/workouts/plans/`
**When** the page loads
**Then** I see all my workout plans listed with name, exercise count, and date created
**And** only my own plans are shown (filtered by `user_id=current_user.id`)

**Given** I delete a plan
**When** deletion is confirmed
**Then** the `workout_plans` row and all associated `plan_exercises` rows are deleted
**And** I see a `success` flash: "Plan deleted."
**And** I remain on `/workouts/plans/`

**Given** I have no plans yet
**When** `/workouts/plans/` loads
**Then** I see: "No workout plans yet. Create your first plan."

---

## Epic 4: Workout Logging & Auto-Save

Users can start plan-based or ad-hoc sessions, log sets with weight and reps (auto-saved per set to a JSON endpoint), resume interrupted sessions, mark sessions complete, and view all past sessions.

### Story 4.1: Start a Workout Session

As a logged-in user,
I want to start a workout session from a plan or ad-hoc,
So that I can begin logging my sets immediately.

**Acceptance Criteria:**

**Given** I am on a plan detail page and click "Start Session"
**When** the request is processed
**Then** a `workout_sessions` row is created: `user_id=current_user.id`, `plan_id`, `started_at` (UTC), `is_complete=False`
**And** I am redirected to the session log page `/workouts/sessions/<id>/log`
**And** the page pre-populates exercises from the plan in order

**Given** I am on `/workouts/sessions/new` (ad-hoc)
**When** I start a session without selecting a plan
**Then** a `workout_sessions` row is created with `plan_id=NULL`
**And** I can add any exercise from the library on the fly

**Given** I already have an incomplete session
**When** I try to start a new session
**Then** I see a prompt: "You have an unfinished session. Resume it or discard it first."

### Story 4.2: Log Sets with Auto-Save

As a logged-in user at the gym,
I want to log each set (weight and reps) with immediate auto-save,
So that my data is never lost even if my session is interrupted.

**Acceptance Criteria:**

**Given** I am on the session log page and enter weight and reps for a set
**When** I tap/click "Save Set"
**Then** `set-logger.js` sends `POST /api/sessions/<id>/sets` with `{"exercise_id": N, "set_number": M, "weight_kg": X, "reps": Y}`
**And** the server responds within 500ms with `{"status": "ok", "set_id": N}`
**And** a `workout_sets` row is persisted: `session_id`, `exercise_id`, `set_number`, `weight_kg`, `reps`, `logged_at` (UTC)
**And** the UI confirms the save visually without a full page reload

**Given** the network request fails
**When** the save is attempted
**Then** the UI shows an inline error: "Set not saved — check your connection." and does not clear the input

**Given** I log multiple sets for the same exercise
**When** each is saved
**Then** `set_number` increments correctly (1, 2, 3…) for that exercise within the session

### Story 4.3: Resume an Interrupted Session

As a logged-in user,
I want to resume a partially completed session after an interruption,
So that I don't lose previously logged sets.

**Acceptance Criteria:**

**Given** I have an incomplete session (`is_complete=False`)
**When** I navigate to `/workouts/sessions/<id>/log`
**Then** all previously saved sets are displayed, grouped by exercise
**And** I can continue adding new sets from where I left off

**Given** I close the browser mid-session and reopen GymTrack
**When** I visit `/workouts/sessions/`
**Then** I see the incomplete session at the top with a "Resume" link

**Given** another user tries to access my session URL
**When** the request is made
**Then** they receive a 404 (`.filter_by(id=session_id, user_id=current_user.id).first_or_404()`)

### Story 4.4: Complete a Session

As a logged-in user,
I want to mark my workout session as complete,
So that it is recorded in my history and triggers PR detection.

**Acceptance Criteria:**

**Given** I am on an active session log page
**When** I click "Complete Workout"
**Then** `workout_sessions.is_complete` is set to `True` and `completed_at` (UTC) is recorded
**And** I am redirected to `/workouts/sessions/<id>/complete` (post-workout summary)
**And** the summary shows all exercises and sets logged in this session

**Given** the session has zero sets logged
**When** I try to complete it
**Then** I see a `warning` flash: "Log at least one set before completing."
**And** the session remains open

### Story 4.5: Session History

As a logged-in user,
I want to view a list of all my past completed sessions,
So that I can track my workout frequency and review past logs.

**Acceptance Criteria:**

**Given** I navigate to `/workouts/sessions/`
**When** the page loads
**Then** I see all my completed sessions listed, sorted by most recent first
**And** each entry shows: date, plan name (or "Ad-hoc"), exercise count, total sets

**Given** I click on a past session
**When** the detail page loads
**Then** I see all exercises and every set logged (weight, reps, set number)

**Given** I have no completed sessions
**When** the page loads
**Then** I see: "No completed sessions yet. Start your first workout!"

---

## Epic 5: Personal Record Detection & Notifications

The system automatically detects new and matched PRs when a session is completed, shows a PR notification banner on the post-workout summary, and lets users view all their current PRs per exercise.

### Story 5.1: PR Detection Service

As a logged-in user,
I want the system to automatically detect personal records when I complete a session,
So that my achievements are surfaced without any manual effort.

**Acceptance Criteria:**

**Given** I complete a workout session
**When** `POST /workouts/sessions/<id>/complete` is processed
**Then** `detect_prs(user_id=current_user.id, session_id=session.id)` is called once (after session is marked complete)
**And** the function compares each `workout_sets` row in the session against the `personal_records` table for the same `user_id` + `exercise_id`
**And** if `weight_kg` in the session set exceeds the stored PR, a new `personal_records` row is upserted with the new weight, reps, and `achieved_at` (UTC)
**And** `detect_prs` is a pure function in `app/services/pr_detection.py` — no Flask context required, independently testable

**Given** the session contains sets for 3 different exercises
**When** PR detection runs
**Then** each exercise is evaluated independently and only exercises with a new or matched PR produce a result

**Given** PR detection is NOT called on the auto-save endpoint `POST /api/sessions/<id>/sets`
**When** a set is auto-saved mid-session
**Then** no PR computation occurs (hot path stays <500ms)

### Story 5.2: Matched PR Detection

As a logged-in user,
I want the system to detect when I match (tie) a previous personal record,
So that I know I've maintained my peak performance after a gap.

**Acceptance Criteria:**

**Given** my current session includes a set where `weight_kg` equals (not exceeds) my stored `personal_records.weight_kg` for that exercise
**When** `detect_prs` runs at session completion
**Then** the result includes a matched PR entry with `is_new=False`
**And** the existing `personal_records` row is NOT overwritten (matched PRs don't replace new PRs)

**Given** both a new PR and a matched PR are detected in the same session
**When** `detect_prs` returns results
**Then** both are included in the returned list and both are displayed to the user

### Story 5.3: PR Notification on Post-Workout Summary

As a logged-in user,
I want to see a PR notification banner after completing a workout,
So that I get immediate positive feedback when I hit a personal best.

**Acceptance Criteria:**

**Given** `detect_prs` returned one or more new PRs
**When** the post-workout summary page `/workouts/sessions/<id>/complete` renders
**Then** a prominent PR banner is displayed: "🏆 New PR — [Exercise Name]: [weight]kg × [reps] reps. Your best ever."
**And** one banner appears per PR detected in this session

**Given** `detect_prs` returned one or more matched PRs
**When** the summary page renders
**Then** a banner is displayed: "💪 Matched PR — [Exercise Name]: [weight]kg × [reps] reps. Strength holds."

**Given** no PRs were detected
**When** the summary page renders
**Then** no PR banner is shown (no empty banner element in the DOM)

### Story 5.4: View All Personal Records

As a logged-in user,
I want to view a list of all my current personal records per exercise,
So that I can see my peak performance across all movements.

**Acceptance Criteria:**

**Given** I navigate to `/progress/prs/`
**When** the page loads
**Then** I see a list of all exercises for which I have a PR, showing: exercise name, best weight (kg), reps at that weight, date achieved
**And** only my own PRs are shown (filtered by `user_id=current_user.id`)
**And** the list is sorted alphabetically by exercise name

**Given** I have no PRs yet
**When** the page loads
**Then** I see: "No personal records yet. Complete a workout to start tracking PRs."

---

## Epic 6: Progress Tracking & Charts

Users can view per-exercise strength progression, workout frequency, and volume trend charts with time-period filters (last 4 weeks / 3 months / all time).

### Story 6.1: Strength Progression Chart

As a logged-in user,
I want to see a chart of my best weight over time for a specific exercise,
So that I can visualize my strength progression.

**Acceptance Criteria:**

**Given** I navigate to `/progress/exercise/<id>/`
**When** the page loads
**Then** a Chart.js line chart is rendered showing my best `weight_kg` per session date for that exercise
**And** chart data is passed from the Flask view as `json.dumps([{"date": "...", "weight": ...}, ...])` in a `<script>` tag — no separate API call
**And** the chart renders within 1 second (NFR3)
**And** only my own sets are included (filtered by `user_id=current_user.id`)

**Given** I have fewer than 2 data points for the selected exercise
**When** the page loads
**Then** I see: "Not enough data yet. Log at least 2 sessions with this exercise to see a trend."

**Given** another user tries to access my progress URL
**When** the request is made
**Then** only their own data is returned — never mine (data isolation enforced)

### Story 6.2: Workout Frequency Chart

As a logged-in user,
I want to see how many sessions I complete per week or month,
So that I can track my consistency over time.

**Acceptance Criteria:**

**Given** I navigate to `/progress/frequency/`
**When** the page loads
**Then** a Chart.js bar chart shows sessions per week for the last 12 weeks
**And** each bar represents one week with the session count as the value
**And** weeks with zero sessions render as zero-height bars (not omitted)

**Given** I have no session history
**When** the page loads
**Then** I see: "No workout history yet. Complete your first session to see frequency data."

### Story 6.3: Volume Trend Chart

As a logged-in user,
I want to see my total volume lifted (weight × reps) per week,
So that I can track the overall load of my training.

**Acceptance Criteria:**

**Given** I navigate to `/progress/volume/`
**When** the page loads
**Then** a Chart.js line chart shows total volume (sum of `weight_kg × reps` across all sets) per week
**And** volume is calculated server-side in the view and passed as JSON to `charts.js`

**Given** I have fewer than 2 weeks of data
**When** the page loads
**Then** I see: "Not enough data yet. Log sessions across at least 2 weeks to see a volume trend."

### Story 6.4: Chart Time-Period Filter

As a logged-in user,
I want to filter all progress charts by time period,
So that I can focus on recent progress or view my full history.

**Acceptance Criteria:**

**Given** I am on any progress chart page
**When** I select a time period filter (Last 4 Weeks / Last 3 Months / All Time)
**Then** the chart re-renders showing only data within the selected period
**And** the selected filter option is visually active/highlighted

**Given** I select "Last 4 Weeks" and have no data in that window
**When** the filter is applied
**Then** the chart shows an empty state message for the selected period

**Given** the default period on first load
**When** the page renders
**Then** "Last 3 Months" is the default selected filter

---

## Epic 7: Dashboard, Admin & Operations

Users see a personal dashboard with workout streak, recent PRs, and a re-engagement prompt when inactive ≥ 2 weeks. Admins can manage users, manage the exercise library, and view platform health metrics.

### Story 7.1: Personal Dashboard

As a logged-in user,
I want to see a dashboard summarizing my recent activity when I log in,
So that I get an instant snapshot of my fitness progress.

**Acceptance Criteria:**

**Given** I log in and am redirected to `/dashboard/`
**When** the page loads
**Then** I see: my current workout streak, my 3 most recent PRs (exercise name + weight), and a workout frequency mini-chart (last 4 weeks)
**And** all data is scoped to `current_user.id` — no other user's data is visible
**And** the page renders within 1 second (NFR3); `get_dashboard_stats(user_id)` in `app/services/stats.py` handles aggregation

**Given** I have no workout history
**When** the dashboard loads
**Then** streak shows "0 weeks", PR section shows "No PRs yet — complete a workout!", frequency chart shows empty bars

### Story 7.2: Workout Streak Display

As a logged-in user,
I want to see my current workout streak on the dashboard,
So that I'm motivated to maintain my consistency.

**Acceptance Criteria:**

**Given** I have logged at least one session in the current week
**When** the dashboard loads
**Then** streak shows the count of consecutive weeks (ending with the current week) where I logged ≥ 1 session
**And** `calculate_streak(user_id)` in `app/services/streak.py` computes this as a pure function

**Given** I missed the previous week entirely
**When** the dashboard loads
**Then** my streak resets to 1 if I've logged this week, or 0 if I haven't logged yet this week

**Given** I have a 5-week streak
**When** the dashboard renders
**Then** I see: "🔥 5-week streak"

### Story 7.3: Re-Engagement Prompt for Inactive Users

As a user returning after a long absence,
I want to see my last session and a prompt to get back on track,
So that I feel welcomed back rather than judged.

**Acceptance Criteria:**

**Given** my most recent completed session was ≥ 14 days ago
**When** I log in and the dashboard loads
**Then** I see a re-engagement card: "Welcome back! Your last workout was [date]. Pick up where you left off?" with a "Resume Routine" button linking to my most recent plan

**Given** my last session was fewer than 14 days ago
**When** the dashboard loads
**Then** the re-engagement card is NOT shown

**Given** I have never logged a session
**When** the dashboard loads
**Then** I see a getting-started prompt: "Ready to start? Create your first workout plan."

### Story 7.4: Admin User Management

As an administrator,
I want to view all registered users and trigger password resets on their behalf,
So that I can support users who are locked out of their accounts.

**Acceptance Criteria:**

**Given** I am an admin at `/admin/users/`
**When** the page loads
**Then** I see a list of all users showing: email, registration date, last login, `is_admin` status
**And** non-admin users cannot access this page (403 response)

**Given** I click "Send Password Reset" for a user
**When** the action is confirmed
**Then** a password reset email is sent to that user's email address using the same `itsdangerous` token flow as Story 1.4
**And** I see a `success` flash: "Password reset email sent to [email]."

### Story 7.5: Admin Platform Health Dashboard

As an administrator,
I want to view platform health metrics,
So that I can monitor the health of GymTrack and respond to issues quickly.

**Acceptance Criteria:**

**Given** I am an admin at `/admin/health/`
**When** the page loads
**Then** I see: total registered users, active users in last 7 days, total sessions logged, total sets logged, and a link to the Sentry error dashboard

**Given** a non-admin user tries to access `/admin/health/`
**When** the request is made
**Then** they receive a 403 Forbidden response

**Given** the page data is fetched
**When** rendered
**Then** all metrics are scoped to platform-wide data (admin queries — not filtered by `current_user.id`)
