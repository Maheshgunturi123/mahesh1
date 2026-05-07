# Story 7.5: Admin Platform Health Dashboard

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an administrator,
I want to view platform health metrics,
so that I can monitor the health of GymTrack and respond to issues quickly.

## Acceptance Criteria

1. **Given** I am an admin at `/admin/health/`
   **When** the page loads
   **Then** I see: total registered users, active users in last 7 days, total sessions logged, total sets logged, and a link to the Sentry error dashboard

2. **Given** a non-admin user tries to access `/admin/health/`
   **When** the request is made
   **Then** they receive a 403 Forbidden response

3. **Given** the page data is fetched
   **When** rendered
   **Then** all metrics are scoped to platform-wide data (admin queries — not filtered by `current_user.id`)

## Tasks / Subtasks

- [ ] Task 1: Add `get_platform_health_stats()` to `app/services/stats.py` (AC: 1, 3)
  - [ ] UPDATE `gymtrack/app/services/stats.py` — APPEND new function at end of file (do NOT modify existing functions)
  - [ ] Add imports at top of file if missing: `from app.models.workout_set import WorkoutSet` and `from datetime import timedelta`
  - [ ] Implement:
    ```python
    def get_platform_health_stats() -> dict:
        """Return platform-wide health metrics for the admin health dashboard.

        Admin-only aggregation — intentionally NOT scoped to current_user.id.
        """
        now = datetime.datetime.utcnow()
        seven_days_ago = now - datetime.timedelta(days=7)

        total_users = User.query.count()
        active_users_7d = (
            User.query
            .filter(User.last_login_at >= seven_days_ago)
            .count()
        )
        total_sessions = WorkoutSession.query.count()
        total_sets = WorkoutSet.query.count()

        return {
            'total_users': total_users,
            'active_users_7d': active_users_7d,
            'total_sessions': total_sessions,
            'total_sets': total_sets,
        }
    ```
  - [ ] Verify `User` is already imported in `stats.py` — if not, add `from app.models.user import User`
  - [ ] Verify `WorkoutSession` is already imported — it is (used by `get_dashboard_stats`), so no new import needed
  - [ ] Add `from app.models.workout_set import WorkoutSet` at the top import block (not already present)

- [ ] Task 2: Add `SENTRY_DASHBOARD_URL` to config (AC: 1)
  - [ ] UPDATE `gymtrack/config.py` — add `SENTRY_DASHBOARD_URL` to the base `Config` class:
    ```python
    SENTRY_DASHBOARD_URL = os.environ.get('SENTRY_DASHBOARD_URL')
    ```
    Place it after the `MAIL_DEFAULT_SENDER` line. It defaults to `None`; when set via env var, the template renders a clickable link.
  - [ ] Do NOT add it to `TestingConfig` — it inherits `None` from `Config` which is correct

- [ ] Task 3: Add `platform_health` route to admin blueprint (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/admin/routes.py` — APPEND new route at the end of the file
  - [ ] Add import: `from app.services.stats import get_platform_health_stats` (add to existing import block at top)
  - [ ] Add import: `from flask import current_app` (add to existing `from flask import ...` line)
  - [ ] Route `GET /health/`:
    ```python
    @admin_bp.route('/health/')
    @login_required
    @admin_required
    def platform_health():
        stats = get_platform_health_stats()
        sentry_url = current_app.config.get('SENTRY_DASHBOARD_URL')
        return render_template('admin/health.html', stats=stats, sentry_url=sentry_url)
    ```
  - [ ] Decoration order: `@login_required` first, then `@admin_required` — same pattern as all other admin routes
  - [ ] No form needed — this is a GET-only read page; no state-changing action, no CSRF form required
  - [ ] Do NOT modify any existing routes

- [ ] Task 4: Create `admin/health.html` template (AC: 1, 2, 3)
  - [ ] Create `gymtrack/app/templates/admin/health.html` — NEW file
  - [ ] Extends `base.html`; BEM block class `admin-health`
  - [ ] Title block: "Platform Health — GymTrack Admin"
  - [ ] Heading: "Admin — Platform Health"
  - [ ] Flash messages block (same pattern as `user_list.html` and `exercise_list.html`)
  - [ ] Metrics section with `aria-label="Platform health metrics"`:
    - Total Users: `{{ stats.total_users }}`
    - Active Users (Last 7 Days): `{{ stats.active_users_7d }}`
    - Total Sessions Logged: `{{ stats.total_sessions }}`
    - Total Sets Logged: `{{ stats.total_sets }}`
  - [ ] Sentry link section — only render when `sentry_url` is set:
    ```html
    {% if sentry_url %}
    <p class="admin-health__sentry-link">
      <a href="{{ sentry_url }}" target="_blank" rel="noopener noreferrer"
         class="admin-health__sentry-anchor">View Sentry Error Dashboard →</a>
    </p>
    {% else %}
    <p class="admin-health__sentry-note">
      Sentry dashboard URL not configured. Set <code>SENTRY_DASHBOARD_URL</code> env var to enable.
    </p>
    {% endif %}
    ```
  - [ ] Full sample template:
    ```html
    {# gymtrack/app/templates/admin/health.html #}
    {% extends 'base.html' %}

    {% block title %}Platform Health — GymTrack Admin{% endblock %}

    {% block content %}
    <div class="admin-health">
      <h1 class="admin-health__heading">Admin — Platform Health</h1>

      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, message in messages %}
            <p class="flash flash--{{ category }}">{{ message }}</p>
          {% endfor %}
        {% endif %}
      {% endwith %}

      <dl class="admin-health__metrics" aria-label="Platform health metrics">
        <div class="admin-health__metric">
          <dt class="admin-health__metric-label">Total Registered Users</dt>
          <dd class="admin-health__metric-value">{{ stats.total_users }}</dd>
        </div>
        <div class="admin-health__metric">
          <dt class="admin-health__metric-label">Active Users (Last 7 Days)</dt>
          <dd class="admin-health__metric-value">{{ stats.active_users_7d }}</dd>
        </div>
        <div class="admin-health__metric">
          <dt class="admin-health__metric-label">Total Sessions Logged</dt>
          <dd class="admin-health__metric-value">{{ stats.total_sessions }}</dd>
        </div>
        <div class="admin-health__metric">
          <dt class="admin-health__metric-label">Total Sets Logged</dt>
          <dd class="admin-health__metric-value">{{ stats.total_sets }}</dd>
        </div>
      </dl>

      <div class="admin-health__sentry">
        {% if sentry_url %}
        <p class="admin-health__sentry-link">
          <a href="{{ sentry_url }}" target="_blank" rel="noopener noreferrer"
             class="admin-health__sentry-anchor">View Sentry Error Dashboard →</a>
        </p>
        {% else %}
        <p class="admin-health__sentry-note">
          Sentry dashboard URL not configured.
          Set <code>SENTRY_DASHBOARD_URL</code> environment variable to enable this link.
        </p>
        {% endif %}
      </div>
    </div>
    {% endblock %}
    ```

- [ ] Task 5: Add CSS for health admin panel (AC: 1)
  - [ ] UPDATE `gymtrack/app/static/css/style.css` — APPEND admin health BEM classes at end of file
  - [ ] Add `admin-health` block with `__heading`, `__metrics`, `__metric`, `__metric-label`, `__metric-value`, `__sentry`, `__sentry-link`, `__sentry-anchor`, `__sentry-note` elements
  - [ ] Use a `<dl>` layout with `admin-health__metric` displayed as a stat card (flex row or grid)
  - [ ] Do NOT create a new CSS file — only append to existing `style.css`

- [ ] Task 6: Append platform health tests to `tests/test_admin.py` (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/tests/test_admin.py` — APPEND new test section at end of file, do NOT modify existing tests
  - [ ] Add section header comment: `# ── Platform Health Tests (Story 7.5) ─────────────────────────────────────────`
  - [ ] Tests to add:
    - `test_health_unauthenticated_redirects`: GET `/admin/health/` without login → 302 to `/auth/login`
    - `test_health_non_admin_gets_403`: GET `/admin/health/` as regular user → 403
    - `test_health_admin_sees_metrics`: Admin GET `/admin/health/` → 200, response contains metric labels (b'Total Registered Users', b'Total Sets Logged', b'Total Sessions Logged', b'Active Users')
    - `test_health_counts_correct`: Create known data (1 admin + 1 regular user, 1 session, 2 sets), GET `/admin/health/` → verify counts appear in response
    - `test_health_no_sentry_url_shows_note`: With no `SENTRY_DASHBOARD_URL` configured → response contains b'SENTRY_DASHBOARD_URL'
    - `test_health_sentry_url_shows_link`: With `app.config['SENTRY_DASHBOARD_URL'] = 'https://sentry.io/test'` → response contains b'View Sentry Error Dashboard'
  - [ ] Reuse existing `make_admin`, `make_regular_user`, `login_as` helpers already in `test_admin.py`
  - [ ] For `test_health_counts_correct`, create sessions and sets directly via model factories:
    ```python
    from app.models.workout_session import WorkoutSession
    from app.models.workout_set import WorkoutSet
    from app.models.exercise import Exercise

    def make_session_with_sets(db, user):
        session = WorkoutSession(user_id=user.id, is_complete=True)
        db.session.add(session)
        db.session.flush()
        ex = Exercise(name='Squat', muscle_group='Legs')
        db.session.add(ex)
        db.session.flush()
        s1 = WorkoutSet(session_id=session.id, exercise_id=ex.id, set_number=1, weight_kg=100, reps=5)
        s2 = WorkoutSet(session_id=session.id, exercise_id=ex.id, set_number=2, weight_kg=100, reps=5)
        db.session.add_all([s1, s2])
        db.session.commit()
        return session
    ```
  - [ ] For Sentry URL test, use `test_app` fixture to temporarily override config:
    ```python
    def test_health_sentry_url_shows_link(test_client, test_app, test_db):
        make_admin(test_db)
        test_app.config['SENTRY_DASHBOARD_URL'] = 'https://sentry.io/organizations/test/issues/'
        login_as(test_client, 'admin@example.com', 'adminpass123')
        resp = test_client.get('/admin/health/')
        assert resp.status_code == 200
        assert b'View Sentry Error Dashboard' in resp.data
    ```

## Dev Notes

### Admin Blueprint — Current State After Story 7.4

All four files in `gymtrack/app/blueprints/admin/` are stable post Story 7.4:

| File | Current State | This Story's Change |
|------|--------------|---------------------|
| `gymtrack/app/blueprints/admin/utils.py` | `admin_required` decorator | **No change** |
| `gymtrack/app/blueprints/admin/forms.py` | `ExerciseForm`, `DeleteForm` | **No change** — health page is GET-only, no form needed |
| `gymtrack/app/blueprints/admin/routes.py` | Exercise CRUD + `user_list` + `send_user_reset` | **APPEND** `platform_health` route |
| `gymtrack/app/templates/admin/exercise_list.html` | Exercise list | **No change** |
| `gymtrack/app/templates/admin/exercise_form.html` | Exercise form | **No change** |
| `gymtrack/app/templates/admin/user_list.html` | User management table | **No change** |
| `gymtrack/app/static/css/style.css` | Has `admin-exercise-list`, `admin-exercise-form`, `admin-user-list` BEM blocks | **APPEND** `admin-health` BEM block |
| `gymtrack/tests/test_admin.py` | Exercise CRUD + user management tests | **APPEND** health dashboard tests |

**DO NOT** modify `utils.py`, `forms.py`, or any existing templates/routes.

### Architecture Compliance

- `admin_required` decorator is in `utils.py` — already imported at top of `routes.py`, do NOT re-import [Source: `gymtrack/app/blueprints/admin/routes.py` line 8]
- Route decoration order: `@login_required` first, then `@admin_required` — critical for correct redirect (302) vs 403 behavior [Source: Story 2.3 / all admin routes in routes.py]
- Admin queries **intentionally** do NOT filter by `current_user.id` — the health page shows platform-wide data. This is the only permitted exception to the per-user isolation rule [Source: `_bmad-output/planning-artifacts/architecture.md#Multi-User Isolation Pattern`]
- No form, no CSRF protection needed — read-only GET endpoint only, no state changes
- Flash categories must be one of: `success`, `error`, `info`, `warning` [Source: `_bmad-output/planning-artifacts/architecture.md#Flash Messages`]
- Routes in `routes.py` only, never in `__init__.py` [Source: `_bmad-output/planning-artifacts/architecture.md#Blueprint Internal Structure`]
- CSS BEM only, append to `style.css` — do NOT create new CSS files [Source: Story 2.3 dev notes]
- Logging: `logger = logging.getLogger(__name__)` already defined at top of `routes.py` — no logging needed for a read endpoint, but if needed, reuse `logger`
- Service functions are pure (no Flask context) — `get_platform_health_stats()` uses SQLAlchemy queries that require app context but are called within a route; this is correct [Source: `_bmad-output/planning-artifacts/architecture.md#Service Layer`]

### `get_platform_health_stats()` — Key Design Notes

- **Active users (last 7 days)**: Uses `User.last_login_at >= seven_days_ago`. Note: users who registered within 7 days but never logged in have `last_login_at = None` and correctly return `False` in the filter (NULL comparisons in SQL are false), so they are NOT counted as active. This is intentional — "active" means logged in, not just registered.
- **Total sessions**: Counts ALL sessions (complete and incomplete), not just `is_complete=True`. This represents all session logging activity including in-progress ones.
- **Total sets**: Counts all rows in `workout_sets` — platform-wide. No `user_id` filter.
- **Existing imports in `stats.py`** (line 1-11): `datetime`, `func` from sqlalchemy, `db`, `Exercise`, `PersonalRecord`, `WorkoutPlan`, `WorkoutSession`, `calculate_streak`. Missing: `User` and `WorkoutSet` — both must be added.

### Current `stats.py` Import Block (add to it)

```python
# Current top of gymtrack/app/services/stats.py:
import datetime
from sqlalchemy import func
from app.extensions import db
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord
from app.models.workout_plan import WorkoutPlan
from app.models.workout_session import WorkoutSession
from app.services.streak import calculate_streak

# ADD these two lines to existing import block:
from app.models.user import User
from app.models.workout_set import WorkoutSet
```

### Current `routes.py` Import Block (add to it)

```python
# Current top of gymtrack/app/blueprints/admin/routes.py (lines 1-14):
import logging
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy.exc import IntegrityError
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import ExerciseForm, DeleteForm
from app.blueprints.admin.utils import admin_required
from app.blueprints.auth.utils import generate_reset_token
from app.extensions import db, mail
from app.models.exercise import Exercise
from app.models.user import User

# ADD these two lines:
from flask import current_app  # add to the existing flask import line
from app.services.stats import get_platform_health_stats
```

Note: `current_app` should be added to the existing `from flask import ...` line, not as a separate import.

### `SENTRY_DASHBOARD_URL` Config Behavior

- **Not set (default, dev/test)**: `current_app.config.get('SENTRY_DASHBOARD_URL')` returns `None`. Template shows the "not configured" note.
- **Set in production**: Admin sets `SENTRY_DASHBOARD_URL=https://sentry.io/organizations/<org>/issues/` as Railway env var. Template renders the anchor link.
- **TestingConfig**: Inherits `None` from `Config` base — no override needed; test for "not configured" message passes naturally.

### Project Structure — Files to Create/Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `gymtrack/config.py` | UPDATE | Add `SENTRY_DASHBOARD_URL = os.environ.get('SENTRY_DASHBOARD_URL')` to `Config` base class |
| `gymtrack/app/services/stats.py` | UPDATE | Append `get_platform_health_stats()` function; add `User` and `WorkoutSet` imports |
| `gymtrack/app/blueprints/admin/routes.py` | UPDATE | Append `platform_health` route; add `current_app` and `get_platform_health_stats` imports |
| `gymtrack/app/templates/admin/health.html` | NEW | Health dashboard template with `<dl>` metrics and conditional Sentry link |
| `gymtrack/app/static/css/style.css` | UPDATE | Append `admin-health` BEM classes |
| `gymtrack/tests/test_admin.py` | UPDATE | Append platform health tests section |

### References

- Admin blueprint routes: `gymtrack/app/blueprints/admin/routes.py` — existing routes reference and import patterns
- Admin utils: `gymtrack/app/blueprints/admin/utils.py` — `admin_required` decorator (already imported)
- Admin forms: `gymtrack/app/blueprints/admin/forms.py` — `DeleteForm` (not needed for health, GET only)
- User model: `gymtrack/app/models/user.py` — has `last_login_at`, `is_admin`, `created_at`
- WorkoutSession model: `gymtrack/app/models/workout_session.py` — has `user_id`, `is_complete`
- WorkoutSet model: `gymtrack/app/models/workout_set.py` — has `session_id`, `exercise_id`, `weight_kg`, `reps`
- Stats service: `gymtrack/app/services/stats.py` — existing `get_dashboard_stats()` and `get_re_engagement_data()` patterns
- App config: `gymtrack/config.py` — `SENTRY_DSN` pattern already present; `SENTRY_DASHBOARD_URL` follows same pattern
- Architecture patterns: `_bmad-output/planning-artifacts/architecture.md` — BEM CSS, service layer, admin isolation exception, blueprint structure
- Previous story 7.4: `_bmad-output/implementation-artifacts/7-4-admin-user-management.md` — admin blueprint context, `last_login_at` field now exists
- User list template: `gymtrack/app/templates/admin/user_list.html` — flash message pattern, BEM class pattern to follow

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

### Completion Notes List

### File List

- `gymtrack/app/services/stats.py` — added `User`, `WorkoutSet` imports + `get_platform_health_stats()`
- `gymtrack/config.py` — added `SENTRY_DASHBOARD_URL` to `Config`
- `gymtrack/app/blueprints/admin/routes.py` — added `current_app`, `get_platform_health_stats` imports + `platform_health` route
- `gymtrack/app/templates/admin/health.html` — new template
- `gymtrack/app/static/css/style.css` — appended `admin-health` BEM classes
- `gymtrack/tests/test_admin.py` — appended 6 platform health tests (all passing)
