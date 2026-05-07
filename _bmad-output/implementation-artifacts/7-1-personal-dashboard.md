# Story 7.1: Personal Dashboard

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to see a dashboard summarizing my recent activity when I log in,
so that I get an instant snapshot of my fitness progress.

## Acceptance Criteria

1. **Given** I log in and am redirected to `/dashboard/`
   **When** the page loads
   **Then** I see: my current workout streak, my 3 most recent PRs (exercise name + weight), and a workout frequency mini-chart (last 4 weeks)
   **And** all data is scoped to `current_user.id` — no other user's data is visible
   **And** the page renders within 1 second (NFR3); `get_dashboard_stats(user_id)` in `app/services/stats.py` handles aggregation

2. **Given** I have no workout history
   **When** the dashboard loads
   **Then** streak shows "0 weeks", PR section shows "No PRs yet — complete a workout!", frequency chart shows empty bars

## Tasks / Subtasks

- [ ] Task 1: Create `app/services/streak.py` — pure `calculate_streak(user_id)` function (AC: 1, 2)
  - [ ] NEW `gymtrack/app/services/streak.py`
  - [ ] Implement `calculate_streak(user_id: int) -> int` as a pure function (no Flask context required)
  - [ ] Query `WorkoutSession` where `user_id=user_id` and `is_complete=True`, ordered by `started_at`
  - [ ] A "week" is a calendar week (Monday–Sunday); `current_user` has a streak of N if they logged ≥ 1 session in each of the N consecutive weeks ending with the current week
  - [ ] If no sessions exist → return 0
  - [ ] See Dev Notes for full implementation

- [ ] Task 2: Create `app/services/stats.py` — `get_dashboard_stats(user_id)` aggregation (AC: 1, 2)
  - [ ] NEW `gymtrack/app/services/stats.py`
  - [ ] Implement `get_dashboard_stats(user_id: int) -> dict` — returns all data needed by the dashboard in one call
  - [ ] Calls `calculate_streak(user_id)` from `streak.py`
  - [ ] Queries 3 most recent `PersonalRecord` rows for the user, joined with `Exercise` for names — ordered by `created_at DESC`, limit 3
  - [ ] Queries frequency mini-chart: session counts per week for last 4 calendar weeks (same week-bucket logic as `frequency_chart`)
  - [ ] All queries filtered by `user_id` — no `current_user` in service layer
  - [ ] See Dev Notes for full implementation and return shape

- [ ] Task 3: Create dashboard Blueprint (AC: 1)
  - [ ] NEW `gymtrack/app/blueprints/dashboard/__init__.py` — `dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')`
  - [ ] NEW `gymtrack/app/blueprints/dashboard/routes.py`
  - [ ] Route `GET /dashboard/` decorated with `@login_required`
  - [ ] Call `get_dashboard_stats(current_user.id)` and pass results to template
  - [ ] Pass `freq_chart_json=json.dumps(stats['freq_chart'])` so Chart.js can render inline
  - [ ] See Dev Notes for full route implementation

- [ ] Task 4: Register dashboard Blueprint in `create_app()` (AC: 1)
  - [ ] UPDATE `gymtrack/app/__init__.py`
  - [ ] Import `dashboard_bp` from `app.blueprints.dashboard`
  - [ ] Register with `app.register_blueprint(dashboard_bp)` — same pattern as existing blueprints
  - [ ] Do NOT touch any other blueprint registrations

- [ ] Task 5: Create dashboard template (AC: 1, 2)
  - [ ] NEW `gymtrack/app/templates/dashboard/index.html`
  - [ ] Extend `base.html`; block title: "Dashboard"
  - [ ] Section 1 — Streak card: display `{{ streak }}` weeks; show "0 weeks" when `streak == 0`
  - [ ] Section 2 — Recent PRs: iterate `recent_prs`; show "No PRs yet — complete a workout!" when list is empty
  - [ ] Section 3 — Mini frequency chart: `<canvas id="freqChart">` only when `has_freq_data` is true; show empty-state (empty bars already visible via Chart.js zero data) otherwise render chart
  - [ ] Load Chart.js from CDN **only** in this template (`{% block scripts %}` or inline at bottom of body); do NOT add it to `base.html`
  - [ ] Initialize Chart.js bar chart inline via `<script>` reading `freq_chart_json` passed from route
  - [ ] See Dev Notes for exact template structure and Chart.js initialization snippet
  - [ ] WCAG: all `<canvas>` tags need `aria-label` and `role="img"`; PR list uses `<ul>` with `<li>` items; streak in `<p>` or `<span>` with visible label

- [ ] Task 6: Add dashboard CSS BEM component to style.css (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/static/css/style.css`
  - [ ] APPEND new `.dashboard-*` BEM blocks at end of file — do NOT modify any existing CSS blocks
  - [ ] See Dev Notes for required CSS component names and minimal styles

- [ ] Task 7: Redirect login success to `/dashboard/` (AC: 1)
  - [ ] UPDATE `gymtrack/app/blueprints/auth/routes.py`
  - [ ] After successful login, `redirect(url_for('dashboard.index'))` instead of any current placeholder
  - [ ] Verify existing tests for login still pass after this change

- [ ] Task 8: Write tests for dashboard (AC: 1, 2)
  - [ ] NEW `gymtrack/tests/test_dashboard.py`
  - [ ] `test_dashboard_requires_login` — unauthenticated GET /dashboard/ → 302 to /auth/login
  - [ ] `test_dashboard_loads_for_authenticated_user` — authenticated GET /dashboard/ → 200, contains "streak"
  - [ ] `test_dashboard_shows_zero_streak_with_no_sessions` — no sessions → streak "0"
  - [ ] `test_dashboard_shows_recent_prs` — user with 2 PRs → PR exercise names visible in response
  - [ ] `test_dashboard_shows_no_pr_empty_state` — no PRs → "No PRs yet" in response
  - [ ] `test_dashboard_data_isolation` — user A cannot see user B's PRs or streak on dashboard
  - [ ] NEW `gymtrack/tests/test_streak.py` — unit tests for pure `calculate_streak`:
    - [ ] `test_streak_zero_when_no_sessions`
    - [ ] `test_streak_one_when_only_this_week`
    - [ ] `test_streak_resets_when_week_missed`
    - [ ] `test_streak_counts_consecutive_weeks`
  - [ ] See Dev Notes for fixture patterns matching existing `conftest.py`

## Dev Notes

### Architecture Compliance

- Dashboard blueprint follows the exact same internal layout as all other blueprints:
  ```
  app/blueprints/dashboard/
  ├── __init__.py      # Blueprint definition only
  └── routes.py        # Route handlers
  ```
- Services are **pure functions** — no Flask `current_user`, no `request` context. Accept `user_id: int`.
- `calculate_streak` and `get_dashboard_stats` live in `app/services/` alongside `pr_detection.py` (existing).
- Chart.js loaded from CDN per architecture rule: "Chart.js loaded from CDN in templates that need charts (progress, dashboard only). Data passed from Flask view as `json.dumps()` in `<script>` tag — no separate API call needed for initial chart render."

### `calculate_streak(user_id)` — Full Implementation

```python
# gymtrack/app/services/streak.py
import datetime
from app.extensions import db
from app.models.workout_session import WorkoutSession


def calculate_streak(user_id: int) -> int:
    """Return the number of consecutive calendar weeks (Mon–Sun) ending
    with the current week in which the user logged ≥ 1 completed session."""
    rows = (
        db.session.query(WorkoutSession.started_at)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.is_complete == True,
        )
        .all()
    )
    if not rows:
        return 0

    today = datetime.date.today()
    current_monday = today - datetime.timedelta(days=today.weekday())

    # Collect the set of week-start dates the user has sessions in
    weeks_with_sessions = set()
    for row in rows:
        d = row.started_at.date() if hasattr(row.started_at, 'date') else row.started_at
        week_start = d - datetime.timedelta(days=d.weekday())
        weeks_with_sessions.add(week_start)

    # Walk backwards from current week counting consecutive streak
    streak = 0
    check_week = current_monday
    while check_week in weeks_with_sessions:
        streak += 1
        check_week -= datetime.timedelta(weeks=1)

    return streak
```

### `get_dashboard_stats(user_id)` — Full Implementation

```python
# gymtrack/app/services/stats.py
import datetime
import json

from sqlalchemy import func

from app.extensions import db
from app.models.personal_record import PersonalRecord
from app.models.exercise import Exercise
from app.models.workout_session import WorkoutSession
from app.services.streak import calculate_streak


def get_dashboard_stats(user_id: int) -> dict:
    """Aggregate all data needed by the personal dashboard."""
    streak = calculate_streak(user_id)

    # 3 most recent PRs
    recent_prs = (
        db.session.query(PersonalRecord, Exercise.name.label('exercise_name'))
        .join(Exercise, PersonalRecord.exercise_id == Exercise.id)
        .filter(PersonalRecord.user_id == user_id)
        .order_by(PersonalRecord.created_at.desc())
        .limit(3)
        .all()
    )
    pr_list = [
        {'exercise_name': name, 'weight_kg': pr.weight_kg}
        for pr, name in recent_prs
    ]

    # Frequency mini-chart: last 4 calendar weeks (Mon–Sun buckets)
    today = datetime.date.today()
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    earliest_monday = start_of_this_week - datetime.timedelta(weeks=3)

    rows = (
        db.session.query(
            func.date(WorkoutSession.started_at).label('session_date')
        )
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.is_complete == True,
            func.date(WorkoutSession.started_at) >= earliest_monday.isoformat()
        )
        .all()
    )

    counts = {}
    for i in range(4):
        week_start = earliest_monday + datetime.timedelta(weeks=i)
        counts[week_start.isoformat()] = 0
    for row in rows:
        d = datetime.date.fromisoformat(str(row.session_date))
        week_start = d - datetime.timedelta(days=d.weekday())
        key = week_start.isoformat()
        if key in counts:
            counts[key] += 1

    freq_chart = [
        {
            'week': (earliest_monday + datetime.timedelta(weeks=i)).strftime('%b %d'),
            'count': counts[(earliest_monday + datetime.timedelta(weeks=i)).isoformat()]
        }
        for i in range(4)
    ]

    return {
        'streak': streak,
        'recent_prs': pr_list,
        'freq_chart': freq_chart,
        'has_freq_data': any(w['count'] > 0 for w in freq_chart),
    }
```

### Dashboard Blueprint — Full Route Implementation

```python
# gymtrack/app/blueprints/dashboard/routes.py
import json
import logging

from flask import render_template
from flask_login import current_user, login_required

from app.blueprints.dashboard import dashboard_bp
from app.services.stats import get_dashboard_stats

logger = logging.getLogger(__name__)


@dashboard_bp.route('/')
@login_required
def index():
    stats = get_dashboard_stats(current_user.id)
    logger.info('Dashboard loaded: user=%d streak=%d', current_user.id, stats['streak'])
    return render_template(
        'dashboard/index.html',
        streak=stats['streak'],
        recent_prs=stats['recent_prs'],
        freq_chart_json=json.dumps(stats['freq_chart']),
        has_freq_data=stats['has_freq_data'],
    )
```

```python
# gymtrack/app/blueprints/dashboard/__init__.py
from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from app.blueprints.dashboard import routes  # noqa: E402, F401
```

### Dashboard Template — Exact Structure

```html
{# gymtrack/app/templates/dashboard/index.html #}
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="dashboard">

  {# Streak card #}
  <section class="dashboard__section dashboard__streak">
    <h2 class="dashboard__section-title">Workout Streak</h2>
    <p class="dashboard__streak-value">
      {% if streak == 0 %}
        0 weeks
      {% else %}
        🔥 {{ streak }}-week streak
      {% endif %}
    </p>
  </section>

  {# Recent PRs #}
  <section class="dashboard__section dashboard__prs">
    <h2 class="dashboard__section-title">Recent Personal Records</h2>
    {% if recent_prs %}
      <ul class="dashboard__pr-list">
        {% for pr in recent_prs %}
          <li class="dashboard__pr-item">
            <span class="dashboard__pr-exercise">{{ pr.exercise_name }}</span>
            <span class="dashboard__pr-weight">{{ pr.weight_kg }} kg</span>
          </li>
        {% endfor %}
      </ul>
    {% else %}
      <p class="dashboard__empty">No PRs yet — complete a workout!</p>
    {% endif %}
  </section>

  {# Frequency mini-chart #}
  <section class="dashboard__section dashboard__freq">
    <h2 class="dashboard__section-title">Last 4 Weeks</h2>
    <canvas id="freqChart"
            aria-label="Workout frequency chart for the last 4 weeks"
            role="img"
            class="dashboard__chart"></canvas>
  </section>

</div>
{% endblock %}

{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
  (function () {
    var data = {{ freq_chart_json | safe }};
    var labels = data.map(function(d) { return d.week; });
    var counts = data.map(function(d) { return d.count; });
    new Chart(document.getElementById('freqChart'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Sessions',
          data: counts,
          backgroundColor: 'rgba(59, 130, 246, 0.6)'
        }]
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        plugins: { legend: { display: false } }
      }
    });
  })();
</script>
{% endblock %}
```

**Note:** `{% block scripts %}` must be defined in `base.html`. If it doesn't exist yet, add `{% block scripts %}{% endblock %}` just before `</body>` in `base.html` and then include the CDN/script tags inside that block in the dashboard template.

### CSS — Append at End of `style.css`

```css
/* ─── Dashboard ─────────────────────────────────────────── */
.dashboard {
  display: grid;
  gap: 1.5rem;
  max-width: 860px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.dashboard__section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.25rem 1.5rem;
}

.dashboard__section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.75rem;
  color: #374151;
}

.dashboard__streak-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1d4ed8;
  margin: 0;
}

.dashboard__pr-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dashboard__pr-item {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.dashboard__pr-item:last-child {
  border-bottom: none;
}

.dashboard__pr-exercise {
  color: #111827;
  font-weight: 500;
}

.dashboard__pr-weight {
  color: #6b7280;
}

.dashboard__empty {
  color: #6b7280;
  font-style: italic;
  margin: 0;
}

.dashboard__chart {
  max-height: 180px;
}
```

### Auth Redirect After Login

In `gymtrack/app/blueprints/auth/routes.py`, locate the successful login redirect. Change it to:
```python
return redirect(url_for('dashboard.index'))
```
If there is a `next` parameter pattern already (Flask-Login `login_required` redirect), keep that; this only changes the *default* fallback redirect.

### Test Fixture Pattern (matching `conftest.py`)

Look at the existing `conftest.py` for the test `app`, `client`, and `auth_client` fixtures. Follow the same pattern. Typical fixture usage:

```python
# gymtrack/tests/test_dashboard.py
import pytest


def test_dashboard_requires_login(client):
    resp = client.get('/dashboard/')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_dashboard_loads_for_authenticated_user(auth_client):
    resp = auth_client.get('/dashboard/')
    assert resp.status_code == 200
    assert b'streak' in resp.data.lower()


def test_dashboard_shows_zero_streak_with_no_sessions(auth_client):
    resp = auth_client.get('/dashboard/')
    assert b'0 weeks' in resp.data


def test_dashboard_shows_no_pr_empty_state(auth_client):
    resp = auth_client.get('/dashboard/')
    assert b'No PRs yet' in resp.data
```

For isolation test, create two users via the fixture, add sessions/PRs for one, and assert the other's dashboard doesn't show the first user's data.

### Project Structure Notes

- `gymtrack/app/services/streak.py` — NEW (no existing file to check)
- `gymtrack/app/services/stats.py` — NEW (no existing file to check)
- `gymtrack/app/blueprints/dashboard/` — NEW blueprint directory
- `gymtrack/tests/test_dashboard.py` — NEW test file
- `gymtrack/tests/test_streak.py` — NEW unit test file for pure streak service
- `gymtrack/app/__init__.py` — UPDATE: register `dashboard_bp` (touch only the blueprint registration block)
- `gymtrack/app/blueprints/auth/routes.py` — UPDATE: change post-login redirect to `url_for('dashboard.index')`
- `gymtrack/app/static/css/style.css` — UPDATE: append `.dashboard-*` block at end
- `gymtrack/app/templates/dashboard/index.html` — NEW template

### Performance Note (NFR3)

Dashboard must render < 1 second. `get_dashboard_stats` makes 3 DB queries (streak, PRs, freq). All queries are indexed via `user_id` FK. No N+1 risk — PRs are joined with Exercise in a single query.

### References

- Story requirements: [Source: _bmad-output/planning-artifacts/epics.md#Story 7.1]
- Stats service location: [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer]
- Blueprint structure: [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint Internal Structure]
- Chart.js CDN pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- FR32–FR35: [Source: _bmad-output/planning-artifacts/epics.md#Requirements Inventory]
- NFR3 (< 1 second render): [Source: _bmad-output/planning-artifacts/epics.md#NonFunctional Requirements]
- User data isolation pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- Frequency chart bucketing logic (4-week variant): [Source: _bmad-output/implementation-artifacts/6-4-chart-time-period-filter.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

None.

### Completion Notes List

- Auth routes already redirected to `dashboard.index` — Task 7 was pre-complete.
- Dashboard blueprint and `__init__.py` registration were already scaffolded — Tasks 3/4 required route implementation only.
- `base.html` already had `{% block scripts %}` — no changes needed there.
- All 10 new tests pass; full suite 157/157 green.

### File List

- `gymtrack/app/services/streak.py` — NEW
- `gymtrack/app/services/stats.py` — NEW
- `gymtrack/app/blueprints/dashboard/routes.py` — UPDATED
- `gymtrack/app/templates/dashboard/index.html` — UPDATED
- `gymtrack/app/static/css/style.css` — UPDATED (appended `.dashboard-*` BEM blocks)
- `gymtrack/tests/test_dashboard.py` — NEW
- `gymtrack/tests/test_streak.py` — NEW
