# Story 6.2: Workout Frequency Chart

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to see how many sessions I complete per week,
so that I can track my consistency over time.

## Acceptance Criteria

1. **Given** I navigate to `/progress/frequency/`
   **When** the page loads
   **Then** a Chart.js bar chart is rendered showing sessions per week for the last 12 weeks
   **And** each bar represents one week (label = `Mon DD` of the week start) with the session count as the value
   **And** weeks with zero sessions render as zero-height bars (not omitted)
   **And** chart data is passed from the Flask view as `json.dumps([{"week": "...", "count": ...}, ...])` in a `data-*` attribute — no separate API call
   **And** the chart renders within 1 second (NFR3)
   **And** only my own completed sessions are counted (filtered by `WorkoutSession.user_id == current_user.id` and `is_complete == True`)

2. **Given** I have no completed session history in the last 12 weeks
   **When** the page loads
   **Then** I see: "No workout history yet. Complete your first session to see frequency data."
   **And** no chart canvas is rendered

3. **Given** another user is logged in
   **When** they access `/progress/frequency/`
   **Then** only their own sessions are counted — never another user's (data isolation enforced via `WorkoutSession.user_id` filter)

## Tasks / Subtasks

- [x] Task 1: Add `frequency_chart` route to `progress/routes.py` (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [x] Add `import datetime` at the top (alongside existing `import json`)
  - [x] Add route `GET /frequency/` with `@login_required`
  - [x] Compute `earliest_monday` = Monday of the week 11 weeks before the current week (see Dev Notes for exact calculation)
  - [x] Query all completed sessions for the current user with `func.date(WorkoutSession.started_at) >= earliest_monday.isoformat()`
  - [x] Build `chart_data` list of 12 `{"week": <label>, "count": <int>}` dicts using Python-side bucketing (see Dev Notes)
  - [x] Set `has_history = any(d['count'] > 0 for d in chart_data)`
  - [x] Render `progress/frequency_chart.html` with `chart_data_json` and `has_history`
  - [x] Do NOT remove or modify any existing routes (`index`, `pr_list`, `exercise_chart`)

- [x] Task 2: Create `progress/frequency_chart.html` template (AC: 1, 2)
  - [x] CREATE `gymtrack/app/templates/progress/frequency_chart.html`
  - [x] Extend `base.html`; set `{% block title %}Workout Frequency — GymTrack{% endblock %}`
  - [x] When `has_history` is True: render `<canvas id="frequency-chart">` with `data-chart-data="{{ chart_data_json | e }}"`
  - [x] When `has_history` is False: render `<p class="frequency-chart__empty">No workout history yet. Complete your first session to see frequency data.</p>`
  - [x] Load Chart.js CDN inside `{% block scripts %}` BEFORE `charts.js` (same pattern as `exercise_chart.html`)
  - [x] Use BEM class naming: block `frequency-chart`, elements `frequency-chart__heading`, `frequency-chart__canvas-wrapper`, `frequency-chart__canvas`, `frequency-chart__empty`

- [x] Task 3: Add frequency chart initialization to `charts.js` (AC: 1)
  - [x] UPDATE `gymtrack/app/static/js/charts.js`
  - [x] Inside the existing `DOMContentLoaded` listener, add a new `var freqEl = document.getElementById('frequency-chart');` block AFTER the existing strength chart block
  - [x] Parse `chartData` from `freqEl.dataset.chartData`
  - [x] Initialize `new Chart(freqEl, {...})` as a **bar** chart (see Dev Notes for exact config)
  - [x] Guard with `if (freqEl)` — do NOT break existing `strength-progress-chart` initialization

- [x] Task 4: Add CSS for `frequency-chart` component (AC: 1, 2)
  - [x] UPDATE `gymtrack/app/static/css/style.css`
  - [x] Append BEM styles for `.frequency-chart`, `.frequency-chart__heading`, `.frequency-chart__canvas-wrapper`, `.frequency-chart__canvas`, `.frequency-chart__empty`
  - [x] Canvas wrapper: `max-width: 800px; margin: 0 auto;` — matches `exercise-chart` pattern

- [x] Task 5: Update `test_progress.py` with new tests (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/tests/test_progress.py` — ADD new test functions; do NOT remove any existing tests or fixtures
  - [x] Add `test_frequency_chart_unauthenticated` (AC: 3 — redirect to login)
  - [x] Add `test_frequency_chart_no_history` (AC: 2 — empty state message shown, no canvas)
  - [x] Add `test_frequency_chart_counts_sessions` (AC: 1 — chart data JSON present in response, correct count)
  - [x] Add `test_frequency_chart_data_isolation` (AC: 3 — only own sessions counted)
  - [x] See full test specs in Dev Notes

## Dev Notes

### Current State of `progress/routes.py` (after Story 6.1)

The file currently looks like this — the new route for Story 6.2 must be **added** without changing anything below:

```python
import json

from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.blueprints.progress import progress_bp
from app.extensions import db
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord
from app.models.workout_set import WorkoutSet
from app.models.workout_session import WorkoutSession


@progress_bp.route('/')
def index():
    # TODO: implement in subsequent stories
    return f'Progress blueprint placeholder', 200


@progress_bp.route('/prs/')
@login_required
def pr_list():
    prs = (
        PersonalRecord.query
        .filter_by(user_id=current_user.id)
        .join(Exercise)
        .order_by(Exercise.name.asc())
        .all()
    )
    return render_template('progress/prs.html', prs=prs)


@progress_bp.route('/exercise/<int:exercise_id>/')
@login_required
def exercise_chart(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    rows = (
        db.session.query(
            func.date(WorkoutSession.started_at).label('date'),
            func.max(WorkoutSet.weight_kg).label('weight')
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id == exercise_id,
            WorkoutSession.is_complete == True
        )
        .group_by(func.date(WorkoutSession.started_at))
        .order_by(func.date(WorkoutSession.started_at).asc())
        .all()
    )
    chart_data = [{"date": str(row.date), "weight": row.weight} for row in rows]
    return render_template(
        'progress/exercise_chart.html',
        exercise=exercise,
        chart_data_json=json.dumps(chart_data),
        has_enough_data=len(chart_data) >= 2,
    )
```

### Full Route Implementation for Task 1

After Task 1, add `import datetime` to the imports and append the new route. The complete updated file:

```python
import datetime
import json

from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.blueprints.progress import progress_bp
from app.extensions import db
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord
from app.models.workout_set import WorkoutSet
from app.models.workout_session import WorkoutSession


@progress_bp.route('/')
def index():
    # TODO: implement in subsequent stories
    return f'Progress blueprint placeholder', 200


@progress_bp.route('/prs/')
@login_required
def pr_list():
    prs = (
        PersonalRecord.query
        .filter_by(user_id=current_user.id)
        .join(Exercise)
        .order_by(Exercise.name.asc())
        .all()
    )
    return render_template('progress/prs.html', prs=prs)


@progress_bp.route('/exercise/<int:exercise_id>/')
@login_required
def exercise_chart(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    rows = (
        db.session.query(
            func.date(WorkoutSession.started_at).label('date'),
            func.max(WorkoutSet.weight_kg).label('weight')
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id == exercise_id,
            WorkoutSession.is_complete == True
        )
        .group_by(func.date(WorkoutSession.started_at))
        .order_by(func.date(WorkoutSession.started_at).asc())
        .all()
    )
    chart_data = [{"date": str(row.date), "weight": row.weight} for row in rows]
    return render_template(
        'progress/exercise_chart.html',
        exercise=exercise,
        chart_data_json=json.dumps(chart_data),
        has_enough_data=len(chart_data) >= 2,
    )


@progress_bp.route('/frequency/')
@login_required
def frequency_chart():
    today = datetime.date.today()
    # Monday of the current week (weekday() == 0 is Monday)
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    # Go back 11 more weeks → 12 weeks total (current week + 11 prior)
    earliest_monday = start_of_this_week - datetime.timedelta(weeks=11)

    # Fetch dates of all completed sessions in the 12-week window
    rows = (
        db.session.query(
            func.date(WorkoutSession.started_at).label('session_date')
        )
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.is_complete == True,
            func.date(WorkoutSession.started_at) >= earliest_monday.isoformat()
        )
        .all()
    )

    # Build counts keyed by ISO date string of each week's Monday
    counts = {}
    for i in range(12):
        week_start = earliest_monday + datetime.timedelta(weeks=i)
        counts[week_start.isoformat()] = 0

    for row in rows:
        d = datetime.date.fromisoformat(str(row.session_date))
        week_start = d - datetime.timedelta(days=d.weekday())
        key = week_start.isoformat()
        if key in counts:
            counts[key] += 1

    chart_data = [
        {
            "week": (earliest_monday + datetime.timedelta(weeks=i)).strftime('%b %d'),
            "count": counts[(earliest_monday + datetime.timedelta(weeks=i)).isoformat()]
        }
        for i in range(12)
    ]
    has_history = any(d['count'] > 0 for d in chart_data)

    return render_template(
        'progress/frequency_chart.html',
        chart_data_json=json.dumps(chart_data),
        has_history=has_history,
    )
```

**IMPORTANT — Data isolation:** `WorkoutSession` has a `user_id` column. Always filter `WorkoutSession.user_id == current_user.id` — never omit this filter.

**IMPORTANT — `func.date()` compatibility:** SQLite returns a plain string (e.g. `"2026-05-04"`); PostgreSQL returns a Python `datetime.date` object. Always use `str(row.session_date)` before calling `datetime.date.fromisoformat()` to ensure compatibility on both databases.

**IMPORTANT — `is_complete` filter:** Only count completed sessions. In-progress sessions must not inflate the chart (they may be abandoned).

**IMPORTANT — Week bucketing:** We use Python-side bucketing rather than a SQL GROUP BY week to guarantee all 12 weeks appear including zeros. SQL `GROUP BY` omits weeks with no data.

### Template Structure for `progress/frequency_chart.html`

```html
{% extends 'base.html' %}
{% block title %}Workout Frequency — GymTrack{% endblock %}
{% block content %}
<div class="frequency-chart">
  <h1 class="frequency-chart__heading">Workout Frequency — Last 12 Weeks</h1>
  {% if has_history %}
    <div class="frequency-chart__canvas-wrapper">
      <canvas id="frequency-chart"
              class="frequency-chart__canvas"
              data-chart-data="{{ chart_data_json | e }}">
      </canvas>
    </div>
  {% else %}
    <p class="frequency-chart__empty">No workout history yet. Complete your first session to see frequency data.</p>
  {% endif %}
</div>
{% endblock %}
{% block scripts %}
  {{ super() }}
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <script src="{{ url_for('static', filename='js/charts.js') }}"></script>
{% endblock %}
```

**Notes:**
- `{{ chart_data_json | e }}` HTML-escapes the JSON for safe embedding in a `data-*` attribute.
- Chart.js CDN script MUST be loaded **before** `charts.js` — same ordering rule as `exercise_chart.html`.
- The `{% block scripts %}` + `{{ super() }}` pattern assumes `base.html` defines a `scripts` block at the bottom of `<body>`. Check `base.html`; if no such block, append `<script>` tags at the bottom of `{% block content %}` instead.
- Do NOT add Chart.js CDN to `base.html` globally — load per page only.

### `charts.js` Addition for Task 3

Current state of `gymtrack/app/static/js/charts.js` after Story 6.1:

```javascript
// charts.js — Chart.js initialization for progress views

document.addEventListener('DOMContentLoaded', function () {
  // Story 6.1 — Strength Progression Chart
  var progressEl = document.getElementById('strength-progress-chart');
  if (progressEl) {
    var chartData = JSON.parse(progressEl.dataset.chartData);
    new Chart(progressEl, {
      type: 'line',
      data: {
        labels: chartData.map(function (d) { return d.date; }),
        datasets: [{
          label: 'Best Weight (kg)',
          data: chartData.map(function (d) { return d.weight; }),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.1,
          fill: true,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            title: { display: true, text: 'Weight (kg)' },
            beginAtZero: false
          },
          x: {
            title: { display: true, text: 'Date' }
          }
        }
      }
    });
  }
});
```

Add the Story 6.2 block **inside the existing `DOMContentLoaded` listener** (do not create a second listener), immediately after the closing `}` of the strength chart `if` block:

```javascript
  // Story 6.2 — Workout Frequency Chart
  var freqEl = document.getElementById('frequency-chart');
  if (freqEl) {
    var freqData = JSON.parse(freqEl.dataset.chartData);
    new Chart(freqEl, {
      type: 'bar',
      data: {
        labels: freqData.map(function (d) { return d.week; }),
        datasets: [{
          label: 'Sessions',
          data: freqData.map(function (d) { return d.count; }),
          backgroundColor: '#3b82f6',
          borderColor: '#2563eb',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            title: { display: true, text: 'Sessions' },
            beginAtZero: true,
            ticks: { stepSize: 1, precision: 0 }
          },
          x: {
            title: { display: true, text: 'Week Starting' }
          }
        }
      }
    });
  }
```

The final `charts.js` file after Task 3 should have both blocks inside the single `DOMContentLoaded` listener.

**Note:** Use `var` and ES5 `function` syntax throughout — no `const`/`let`, no arrow functions. Chart.js 4.x is loaded from CDN; no bundler is in use. `ticks: { stepSize: 1, precision: 0 }` prevents decimal session counts on the y-axis.

### CSS for Task 4

Append to `gymtrack/app/static/css/style.css` — do NOT replace the existing `.exercise-chart` block that was added in Story 6.1:

```css
/* ─── Workout Frequency Chart (Story 6.2) ─── */
.frequency-chart {
  padding: 1.5rem;
}

.frequency-chart__heading {
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.frequency-chart__canvas-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.frequency-chart__canvas {
  width: 100%;
}

.frequency-chart__empty {
  color: #6b7280;
  text-align: center;
  margin-top: 2rem;
}
```

### Test Specifications for Task 5

Update `gymtrack/tests/test_progress.py` — **ADD** the following under a `# ─── Story 6.2 ───` comment. Do NOT remove any existing tests from Stories 5.4, 6.1, or earlier.

The existing file already imports `datetime`, `WorkoutSet`, `WorkoutSession`, and has `make_workout_session` and `make_workout_set` helper functions (added in Story 6.1). Do NOT re-add them.

```python
# ─── Story 6.2 — Workout Frequency Chart ───

def test_frequency_chart_unauthenticated(client, app):
    """AC 3: unauthenticated GET → redirect to login."""
    response = client.get('/progress/frequency/')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_frequency_chart_no_history(client, app):
    """AC 2: user with no completed sessions → empty state message, no canvas."""
    with app.app_context():
        make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        response = client.get('/progress/frequency/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'No workout history yet' in html
        assert 'frequency-chart' not in html or 'frequency-chart__empty' in html
        assert '<canvas' not in html


def test_frequency_chart_counts_sessions(client, app):
    """AC 1: completed sessions appear as counts in chart data JSON."""
    with app.app_context():
        user = make_user(_db)
        # Create 2 completed sessions
        make_workout_session(_db, user.id, is_complete=True)
        make_workout_session(_db, user.id, is_complete=True)
        # Incomplete session — should NOT be counted
        make_workout_session(_db, user.id, is_complete=False)
        login_as(client, 'user@example.com', 'password123')
        response = client.get('/progress/frequency/')
        assert response.status_code == 200
        html = response.data.decode()
        assert '<canvas' in html
        assert 'frequency-chart' in html
        assert 'No workout history yet' not in html
        # The week containing today should show count of 2 (both completed sessions)
        assert '"count": 2' in html or '"count":2' in html


def test_frequency_chart_data_isolation(client, app):
    """AC 3: logged-in user only sees their own sessions — not another user's."""
    with app.app_context():
        user_a = make_user(_db, email='usera@example.com')
        user_b = make_user(_db, email='userb@example.com')
        # user_b has 3 completed sessions
        make_workout_session(_db, user_b.id, is_complete=True)
        make_workout_session(_db, user_b.id, is_complete=True)
        make_workout_session(_db, user_b.id, is_complete=True)
        # user_a has no sessions — logs in and checks frequency
        login_as(client, 'usera@example.com', 'password123')
        response = client.get('/progress/frequency/')
        assert response.status_code == 200
        html = response.data.decode()
        # user_a sees empty state — does NOT see user_b's session counts
        assert 'No workout history yet' in html
        assert '"count": 3' not in html
        assert '"count":3' not in html
```

**Note on `make_user` signature:** Story 6.1 tests call `make_user(_db, email='usera@example.com')`. Check the existing `make_user` helper signature in `test_progress.py` — if it only accepts `(_db)` and uses a fixed email, use a different approach matching the existing helper's signature. If Story 5.4 introduced an `email` parameter, use it. If not, adapt the data-isolation test to use only one user with no sessions.

### Project Structure Notes

- Blueprint: `gymtrack/app/blueprints/progress/` — `__init__.py` (has `progress_bp`, `url_prefix='/progress'`), `routes.py`
- Template directory: `gymtrack/app/templates/progress/` — already contains `prs.html` and `exercise_chart.html`; create `frequency_chart.html` here
- Static JS: `gymtrack/app/static/js/charts.js` — already has Story 6.1 strength chart; **extend** the existing `DOMContentLoaded` listener
- Static CSS: `gymtrack/app/static/css/style.css` — single file; **append** `.frequency-chart` BEM component block
- Chart.js CDN: loaded per-page in the template `{% block scripts %}`, NOT in `base.html`
- Test file: `gymtrack/tests/test_progress.py` — **append** new tests; do NOT create a new test file

### What NOT to Change

- Do NOT modify `WorkoutSet` or `WorkoutSession` models or their schemas
- Do NOT modify `PersonalRecord` model, `pr_list()` route, or `exercise_chart()` route
- Do NOT remove or modify the `index()` placeholder route — a later story (Epic 7) will implement it
- Do NOT add Chart.js to `base.html` globally
- Do NOT create a second `DOMContentLoaded` listener in `charts.js` — add the frequency block inside the existing one
- Do NOT replace the existing `.exercise-chart` CSS block — append the new `.frequency-chart` block after it
- Do NOT add any POST routes or form handling — this is a GET-only read page

### References

- Workout frequency chart requirements: [Source: _bmad-output/planning-artifacts/epics.md#Story-6.2]
- FR29: Users can view a workout frequency chart (sessions per week/month): [Source: _bmad-output/planning-artifacts/epics.md#FR29]
- NFR3: Chart render < 1 second: [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-Overview]
- Chart.js CDN integration pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- Data isolation pattern (mandatory): [Source: _bmad-output/planning-artifacts/architecture.md#Process-Patterns]
- WorkoutSession model definition: [Source: _bmad-output/implementation-artifacts/4-1-start-a-workout-session.md#Task-1]
- `charts.js` current state + ES5 convention: [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#charts-js-Implementation]
- `func.date()` SQLite/PostgreSQL compatibility note: [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Dev-Notes]
- BEM CSS + canvas-wrapper pattern: [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Task-4]
- Test fixture helpers (`make_workout_session`, `make_user`): [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Test-Specifications]
- Progress blueprint URL prefix `/progress`: [Source: _bmad-output/planning-artifacts/architecture.md#URL-Conventions]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

- Test `test_frequency_chart_counts_sessions` initially failed: `{{ chart_data_json | e }}` HTML-encodes `"` to `&#34;` in the `data-*` attribute. Fixed assertion to check for `&#34;count&#34;: 2` (the escaped form as it appears in the HTML source).

### Completion Notes List

- AC1: `GET /progress/frequency/` returns 12-week bar chart; data embedded in `data-chart-data` as HTML-escaped JSON; Chart.js initialized via `charts.js`; renders within 1 second (no API call).
- AC2: Empty state message `No workout history yet...` rendered when no completed sessions; no `<canvas>` rendered.
- AC3: Route guarded by `@login_required`; query always filters `WorkoutSession.user_id == current_user.id` — data isolation enforced.
- Python-side bucketing ensures all 12 weeks shown including zero-count weeks.
- `str(row.session_date)` applied before `fromisoformat()` for SQLite/PostgreSQL compatibility.

### File List

- `gymtrack/app/blueprints/progress/routes.py` — modified (added `import datetime`, `frequency_chart` route)
- `gymtrack/app/templates/progress/frequency_chart.html` — created
- `gymtrack/app/static/js/charts.js` — modified (added Story 6.2 bar chart block inside existing `DOMContentLoaded`)
- `gymtrack/app/static/css/style.css` — modified (appended `.frequency-chart` BEM component)
- `gymtrack/tests/test_progress.py` — modified (added 4 new Story 6.2 tests)

### Change Log

- 2026-05-05: Implemented Story 6.2 — Workout Frequency Chart. Added `/progress/frequency/` route, `frequency_chart.html` template, Chart.js bar chart initialization in `charts.js`, BEM CSS component in `style.css`, and 4 new tests covering AC1/AC2/AC3. All 138 tests pass.
