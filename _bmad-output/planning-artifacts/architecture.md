---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/product-brief-gym-tracker.md"
workflowType: 'architecture'
project_name: 'GymTrack'
user_name: 'Gunturi.Mahesh'
date: '2026-05-04'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
39 FRs across 8 capability areas: User Management (FR1–6), Exercise Library (FR7–11), Workout Planning (FR12–16), Workout Logging (FR17–23), PR Detection (FR24–27), Progress Tracking & Charts (FR28–31), Personal Dashboard (FR32–35), Administration & Operations (FR36–39). Core loop: plan → log → detect PR → show progress.

**Non-Functional Requirements:**
19 NFRs across 5 categories. Architecturally significant:
- Performance: page load <2s, set save <500ms, chart render <1s (NFR1–3)
- Security: bcrypt pw hashing, HTTPS, strict per-user data isolation (NFR5–8)
- Scalability: 5,000 MAU on a single server, multi-user schema from day 1 (NFR11–12)
- Reliability: 99.5% uptime, every set persisted before UI confirms (NFR14–15)
- Accessibility: WCAG 2.1 AA keyboard nav, color contrast, labeled inputs (NFR17–19)

**Scale & Complexity:**

- Primary domain: Full-stack web (MPA, server-rendered, PWA-compatible)
- Complexity level: Low-Medium
- Estimated architectural components: ~8 domain modules + 2 infrastructure layers

### Technical Constraints & Dependencies

- Stack locked: Flask (Python) + Jinja2 + vanilla HTML/CSS + Chart.js
- Database: SQLite (dev) / PostgreSQL (prod); schema must be multi-user from day 1
- Auth: Flask-Login session-based; no OAuth or SSO in V1
- No WebSockets/SSE — PR notification via server-side computation at save time
- Solo developer — zero-ops-overhead deployment required
- PWA manifest + Service Worker for home screen install and offline read access

### Cross-Cutting Concerns Identified

- **User data isolation:** Every DB query must be scoped to `current_user.id` — no shared data objects, no admin queries leaking into user context
- **Auto-save write path:** FR20/NFR2 demand a minimal, fast endpoint for set logging; must not block on PR detection computation
- **PR detection engine:** Domain-critical logic isolated as a pure function / service; called synchronously post-save but independently testable
- **Error handling:** NFR16 requires graceful degradation at every layer — Flask error handlers, no raw tracebacks exposed to users
- **Accessibility:** Semantic HTML, ARIA roles, keyboard nav, and color contrast must be consistent across all templates (Jinja2 base template enforcement)

## Starter Template Evaluation

### Primary Technology Domain

Full-stack Python web application — MPA (server-rendered), Flask backend, Jinja2 templates, PostgreSQL database. Stack confirmed in PRD; no alternative stack evaluation required.

### Starter Options Considered

No third-party scaffold CLI evaluated — Flask's official Application Factory + Blueprints pattern is the de facto standard for production Flask apps and requires no external scaffold. All Flask documentation, extensions, and community patterns align to this structure.

### Selected Pattern: Flask Application Factory + Blueprints

**Rationale:** Stack is locked in PRD (Flask + Jinja2 + PostgreSQL + Flask-Login). The Application Factory pattern is Flask's own recommended structure for any non-trivial app. It provides testability, config isolation, and clean Blueprint modularization with zero added complexity or learning curve.

**Initialization Commands:**

```bash
# Create virtualenv and install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install flask flask-sqlalchemy flask-migrate flask-login \
            flask-wtf python-dotenv psycopg2-binary gunicorn
```

**Architectural Decisions Provided by Pattern:**

**Language & Runtime:**
Python 3.11+ with virtual environment isolation (venv). Environment variables via python-dotenv (.env file, .env.example committed to repo).

**ORM & Database:**
Flask-SQLAlchemy (SQLAlchemy 2.x) for model declaration and queries. Flask-Migrate (Alembic) for schema versioning — every schema change is a tracked migration file. SQLite for development, PostgreSQL for production (same ORM code, different connection string).

**Authentication:**
Flask-Login for session management. User loader, `login_required` decorator, `current_user` proxy. Passwords hashed with bcrypt (via Flask-Bcrypt or passlib).

**Forms & CSRF:**
Flask-WTF wraps WTForms — form validation and CSRF protection on all state-changing endpoints by default.

**Code Organization:**

```
gymtrack/
├── app/
│   ├── __init__.py          # create_app() factory
│   ├── extensions.py        # db, login_manager, migrate (instantiated without app)
│   ├── models/              # SQLAlchemy models per domain
│   ├── blueprints/
│   │   ├── auth/            # login, logout, register, password reset
│   │   ├── exercises/       # exercise library browse/search
│   │   ├── workouts/        # plan builder + session logger
│   │   ├── progress/        # charts and PR views
│   │   ├── dashboard/       # user dashboard
│   │   └── admin/           # admin panel
│   ├── services/
│   │   └── pr_detection.py  # isolated PR detection engine
│   ├── static/              # CSS, JS, Chart.js
│   └── templates/           # Jinja2 templates (base.html + per-blueprint)
├── migrations/              # Alembic migration files
├── tests/
├── config.py                # DevelopmentConfig / ProductionConfig
├── .env.example
└── wsgi.py                  # Gunicorn entry point
```

**Development Experience:**
Flask development server with `--debug` for auto-reload. Pytest for testing with `app.testing = True` config. Flask shell for REPL access to app context.

**Note:** Project initialization (virtualenv + pip install + scaffold creation) should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Data isolation pattern (every query scoped to `current_user.id`)
- Password hashing library (flask-bcrypt)
- Session storage approach (client-side cookies, single-device logout)
- Auto-save endpoint design (JSON API)

**Important Decisions (Shape Architecture):**
- Deployment platform (Railway)
- Error monitoring (Sentry + Python logging)
- PR detection isolation pattern

**Deferred Decisions (Post-MVP):**
- Multi-device session invalidation (server-side sessions)
- Redis caching layer (not needed until >5k MAU)
- CDN for static assets (Railway handles basic static serving)

---

### Data Architecture

**Multi-User Isolation Pattern:**
Every SQLAlchemy query against user-owned data filters by `current_user.id`. No shared model objects. Pattern enforced at the service layer — no raw queries in routes. Admin queries use explicit admin-only blueprints with separate access checks.

```python
# Standard pattern for all user-owned data
WorkoutPlan.query.filter_by(user_id=current_user.id).all()
```

**Schema Strategy:**
Multi-user schema from day 1 (NFR12). All user-owned tables include `user_id` FK to `users.id` with `nullable=False`. No single-user assumptions anywhere in the data model.

**Migration Approach:**
Flask-Migrate (Alembic). Every schema change produces a versioned migration file committed to the repo. Migrations run explicitly (`flask db upgrade`) — no auto-apply on startup.

**Caching:**
No caching layer in V1. PostgreSQL query performance is sufficient for <5k MAU. Revisit with Redis if read-heavy dashboard queries become a bottleneck post-MVP.

---

### Authentication & Security

**Password Hashing:**
`flask-bcrypt` — bcrypt with work factor 12 (NFR5). Passwords hashed on registration and password reset; never stored or logged in plaintext.

**Session Storage:**
Flask default client-side encrypted cookies (`SECRET_KEY` signed via itsdangerous). Sufficient for V1 single-device logout (cookie deletion on logout). `PERMANENT_SESSION_LIFETIME = timedelta(days=30)` for inactivity expiry (NFR7). Server-side sessions deferred to post-MVP.

**CSRF Protection:**
Flask-WTF on all POST/PUT/DELETE forms and state-changing routes. CSRF token included in all HTML forms via `{{ form.hidden_tag() }}`.

**Password Reset Tokens:**
`itsdangerous.URLSafeTimedSerializer` — tokens expire in 1 hour (NFR9), signed with `SECRET_KEY`, single-use enforced by token timestamp validation.

**HTTPS:**
Enforced at the platform level (Railway auto-provisions TLS). Flask `SESSION_COOKIE_SECURE = True` and `SESSION_COOKIE_HTTPONLY = True` in production config.

---

### API & Communication Patterns

**Route Architecture:**
Server-rendered HTML for all page routes (Jinja2 templates). Minimal JSON API for AJAX operations only — specifically the auto-save set logger path.

**Auto-Save Endpoint (Hot Path — NFR2: <500ms):**
```
POST /api/sessions/<session_id>/sets
Content-Type: application/json
Body: {"exercise_id": 1, "set_number": 2, "weight_kg": 70, "reps": 5}
Response: {"status": "ok", "set_id": 123, "pr_detected": false}
```
PR detection triggered server-side at session completion save, not on individual set saves (keeps the hot path minimal).

**Error Handling:**
Flask `@app.errorhandler` registered for 400, 403, 404, 500. All handlers return user-friendly HTML error pages (NFR16) — no raw tracebacks exposed. JSON error responses for `/api/*` routes only.

**URL Conventions:**
Blueprint-prefixed routes:
- `/auth/` — login, logout, register, password reset
- `/exercises/` — library browse/search
- `/workouts/` — plan builder + session logger
- `/progress/` — charts and PR history
- `/dashboard/` — user home
- `/admin/` — admin panel (login_required + admin_required)
- `/api/` — AJAX endpoints only

---

### Frontend Architecture

**CSS Organization:**
Single `app/static/css/style.css` with BEM-like naming. Base template (`base.html`) loads it globally. No CSS preprocessor — vanilla CSS with custom properties for theming. Mobile-first breakpoints at 375px, 768px, 1024px.

**JavaScript:**
Minimal inline JS in templates for progressive enhancement. Two dedicated JS files:
- `set-logger.js` — auto-save AJAX calls for workout session logger
- `charts.js` — Chart.js initialization for progress views

No JS framework, no bundler. Scripts loaded at bottom of `<body>`.

**Chart.js Integration:**
Chart.js loaded from CDN in templates that need charts (progress, dashboard only). Data passed from Flask view as `json.dumps()` in `<script>` tag — no separate API call needed for initial chart render.

---

### Infrastructure & Deployment

**Hosting Platform: Railway**
Git push deploys from GitHub. Gunicorn WSGI server (`wsgi.py` entry point). PostgreSQL add-on (one-click provision). Environment variables managed via Railway UI. Auto-deploy on push to `main`.

**Gunicorn Config:**
```
gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT
```
2 workers sufficient for V1 load. Scale workers before any other optimization.

**Error Monitoring:**
- **Sentry** (free tier, 5k errors/month) — Flask SDK, automatic exception capture, performance monitoring. Initialized in `create_app()`.
- **Python `logging`** — Structured app events (user actions, PR detections, admin actions) via `logging.getLogger(__name__)` in each module.

**CI/CD:**
GitHub Actions — lint (flake8) + test (pytest) on every push to main and PR. Deploy to Railway on merge to main.

**Environment Config:**
`config.py` with `DevelopmentConfig` (SQLite, DEBUG=True, no Sentry) and `ProductionConfig` (PostgreSQL, DEBUG=False, Sentry enabled). `FLASK_ENV` environment variable selects config.

---

### Decision Impact Analysis

**Implementation Sequence:**
1. Scaffold project structure + config.py + create_app()
2. User model + flask-bcrypt + Flask-Login setup
3. Auth blueprint (register, login, logout, password reset)
4. Exercise model + exercise library blueprint
5. Workout plan model + plan builder blueprint
6. Workout session model + session logger (with auto-save JSON endpoint)
7. PR detection service (pure function, fully tested)
8. Progress charts blueprint (Chart.js integration)
9. Dashboard blueprint
10. Admin blueprint
11. PWA manifest + Service Worker
12. Sentry + logging integration

**Cross-Component Dependencies:**
- All blueprints depend on User model + Flask-Login setup (step 2)
- Session logger depends on Exercise + Plan models (steps 4–5)
- PR detection service depends on WorkoutSet model (step 6)
- Progress charts depend on WorkoutSet + PR history (steps 6–7)
- Dashboard aggregates data from sessions, streaks, PRs (steps 6–7)

## Implementation Patterns & Consistency Rules

### Critical Conflict Points

9 areas where AI agents could independently make different choices without explicit guidance. All agents MUST follow these patterns exactly.

---

### Naming Patterns

**Database Naming Conventions:**
- Table names: plural snake_case (`users`, `workout_plans`, `workout_sets`)
- Column names: singular snake_case (`user_id`, `exercise_name`, `weight_kg`)
- Foreign keys: `<table_singular>_id` (`user_id`, `exercise_id`, `plan_id`)
- Primary keys: always `id` (integer, auto-increment)
- Timestamps: `created_at`, `updated_at` (UTC, no timezone suffix in column name)
- Boolean columns: prefix with `is_` or `has_` (`is_admin`, `is_complete`)

```python
# ✅ Correct
class WorkoutPlan(db.Model):
    __tablename__ = 'workout_plans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ❌ Wrong
class WorkoutPlan(db.Model):
    __tablename__ = 'WorkoutPlan'
    planId = db.Column(db.Integer, primary_key=True)
```

**URL Conventions:**
- Blueprint prefixes: singular nouns (`/auth`, `/workout`, `/exercise`, `/progress`)
- Resource URLs: plural for collections (`/workouts/plans/`, `/exercises/`)
- Kebab-case for multi-word segments (`/workout-sessions/`, not `/workout_sessions/`)
- IDs in URLs: `<int:id>` (always integer, never UUID in V1)

```
/auth/login
/auth/register
/workouts/plans/
/workouts/plans/<int:id>/
/workouts/sessions/<int:id>/log/
/api/sessions/<int:id>/sets    # AJAX only
```

**Python Code Naming:**
- Functions: `snake_case` verbs (`get_user_plans`, `detect_personal_records`)
- Classes: `PascalCase` nouns (`WorkoutPlan`, `PRDetectionService`)
- Constants: `UPPER_SNAKE_CASE` (`MAX_SETS_PER_EXERCISE = 20`)
- Blueprint variables: `snake_case` matching blueprint name (`auth_bp`, `workouts_bp`)
- Template variables: `snake_case` passed from view (`workout_plan`, `exercise_list`)

**Template File Naming:**
- Location: `app/templates/<blueprint_name>/<action>.html`
- Names: `snake_case` matching view function name

```
app/templates/
├── base.html
├── auth/
│   ├── login.html
│   ├── register.html
│   └── reset_password.html
├── workouts/
│   ├── plan_list.html
│   ├── plan_detail.html
│   └── session_log.html
```

**CSS Class Naming:**
- BEM methodology: `block__element--modifier`
- Block names match page/component (`workout-card`, `exercise-row`, `pr-badge`)
- No JavaScript-specific classes prefixed with `js-` for behavior hooks

---

### Structure Patterns

**Blueprint Internal Structure:**
Every blueprint follows the same internal layout:
```
app/blueprints/<name>/
├── __init__.py      # Blueprint definition only (bp = Blueprint(...))
├── routes.py        # All route handlers for this blueprint
├── forms.py         # WTForms form classes (if blueprint has forms)
└── utils.py         # Blueprint-local helpers (optional)
```
Routes are NEVER defined in `__init__.py`. Forms are NEVER defined in `routes.py`.

**Service Layer:**
Domain logic that spans blueprints lives in `app/services/`:
```
app/services/
├── pr_detection.py   # Pure function: detect_prs(user_id, session_id) -> list[PR]
├── streak.py         # Pure function: calculate_streak(user_id) -> int
└── stats.py          # Aggregation helpers for dashboard
```
Services are pure functions (no Flask context required) — importable and testable without an app instance.

**Test Structure:**
```
tests/
├── conftest.py          # pytest fixtures (test app, test client, test db)
├── test_auth.py         # Auth blueprint tests
├── test_workouts.py     # Workouts blueprint tests
├── test_exercises.py    # Exercise blueprint tests
├── test_pr_detection.py # PR detection service unit tests
└── test_api.py          # AJAX endpoint tests
```
Tests mirror blueprint structure. Each blueprint gets one test file. Unit tests for services are separate from blueprint integration tests.

---

### Format Patterns

**HTML Page Routes — Flash Messages:**
Categories MUST be one of: `success`, `error`, `info`, `warning`

```python
# ✅ Correct
flash('Workout saved.', 'success')
flash('Invalid password.', 'error')

# ❌ Wrong
flash('Workout saved.', 'ok')
flash('Invalid password.', 'danger')
```

**JSON API Response Format (`/api/*` routes only):**
```json
// Success
{"status": "ok", "data": { ... }}

// Error
{"status": "error", "message": "Human-readable error description"}
```
No nested `errors` arrays. No `result` key. Always `status` + `data` or `status` + `message`.

**HTTP Status Codes:**
- `200` — successful GET or action
- `201` — resource created (POST)
- `400` — validation error / bad input
- `401` — not authenticated
- `403` — authenticated but unauthorized
- `404` — resource not found
- `500` — unexpected server error

**Date/Time Handling:**
- Database: store all timestamps as UTC `datetime` (no timezone info in column)
- Templates: format via Jinja2 filter `{{ workout.created_at | strftime('%b %d, %Y') }}`
- JSON API: ISO 8601 strings (`"2026-05-04T10:30:00Z"`)
- NEVER pass raw datetime objects to templates expecting strings

---

### Process Patterns

**User Data Isolation (MANDATORY on every user-owned query):**
```python
# ✅ Every query for user-owned data MUST include user_id filter
plans = WorkoutPlan.query.filter_by(user_id=current_user.id).all()
plan = WorkoutPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()

# ❌ NEVER query without user scope
plan = WorkoutPlan.query.get(plan_id)  # vulnerable — exposes any user's data
```

**PR Detection Service Invocation:**
PR detection is called ONCE at session completion — never on individual set save.
```python
# ✅ Call in the "complete session" route handler only
from app.services.pr_detection import detect_prs
new_prs = detect_prs(user_id=current_user.id, session_id=session.id)
```

**Form Validation Pattern:**
All form submissions use Flask-WTF. Validation in route handler, never in model.
```python
@workouts_bp.route('/plans/new', methods=['GET', 'POST'])
@login_required
def new_plan():
    form = WorkoutPlanForm()
    if form.validate_on_submit():
        # process valid form
        ...
    return render_template('workouts/plan_form.html', form=form)
```

**Error Logging Pattern:**
```python
import logging
logger = logging.getLogger(__name__)

# INFO: significant user actions
logger.info('PR detected: user=%d exercise=%d weight=%.1f', user_id, ex_id, weight)

# WARNING: recoverable issues
logger.warning('Password reset requested for unknown email: %s', email)

# ERROR: unexpected failures (also captured by Sentry)
logger.error('PR detection failed for session %d: %s', session_id, str(e))
```

---

### Enforcement Guidelines

**All AI Agents MUST:**
- Filter every user-owned query by `current_user.id` — no exceptions
- Define routes in `routes.py`, never in blueprint `__init__.py`
- Use `snake_case` for all DB columns, Python variables, and URL segments
- Use `kebab-case` for URL path segments (not underscores)
- Return flash messages with only: `success`, `error`, `info`, `warning`
- Call PR detection only at session completion, never on set save
- Define all services as pure functions in `app/services/`
- Write tests in `tests/test_<blueprint_name>.py` matching blueprint structure

**Anti-Patterns to Reject:**
- Querying `Model.query.get(id)` without `user_id` filter on user-owned models
- Business logic in route handlers (move to `app/services/`)
- Direct SQL strings (use SQLAlchemy ORM only)
- Any `print()` for logging (use `logging.getLogger(__name__)`)
- Storing secrets in `config.py` (use environment variables only)
