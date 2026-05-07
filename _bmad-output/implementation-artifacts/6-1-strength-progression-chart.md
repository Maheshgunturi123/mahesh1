# Story 6.1: Strength Progression Chart

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to see a chart of my best weight over time for a specific exercise,
so that I can visualize my strength progression.

## Acceptance Criteria

1. **Given** I navigate to `/progress/exercise/<id>/`
   **When** the page loads
   **Then** a Chart.js line chart is rendered showing my best `weight_kg` per session date for that exercise
   **And** chart data is passed from the Flask view as `json.dumps([{"date": "...", "weight": ...}, ...])` in a `<script>` tag — no separate API call
   **And** the chart renders within 1 second (NFR3)
   **And** only my own sets are included (filtered via `WorkoutSession.user_id == current_user.id`)

2. **Given** I have fewer than 2 data points for the selected exercise
   **When** the page loads
   **Then** I see: "Not enough data yet. Log at least 2 sessions with this exercise to see a trend."

3. **Given** another user tries to access my progress URL
   **When** the request is made
   **Then** only their own data is returned — never mine (data isolation enforced via `WorkoutSession.user_id` filter)

## Tasks / Subtasks

- [x] Task 1: Add `exercise_chart` route to `progress/routes.py` (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [x] Add imports: `import json`, `from sqlalchemy import func`, `from app.extensions import db`, `from app.models.workout_set import WorkoutSet`, `from app.models.workout_session import WorkoutSession`
  - [x] Add route `GET /exercise/<int:exercise_id>/` with `@login_required`
  - [x] Fetch `exercise = Exercise.query.get_or_404(exercise_id)`
  - [x] Build the aggregation query (see Dev Notes for exact query)
  - [x] Pass `exercise`, `chart_data_json`, and `has_enough_data` to template
  - [x] Render `progress/exercise_chart.html`
  - [x] Do NOT remove or modify the existing `index()` or `pr_list()` routes

- [x] Task 2: Create `progress/exercise_chart.html` template (AC: 1, 2)
  - [x] CREATE `gymtrack/app/templates/progress/exercise_chart.html`
  - [x] Extend `base.html`; set `{% block title %}{{ exercise.name }} Progression — GymTrack{% endblock %}`
  - [x] Load Chart.js from CDN inside `{% block scripts %}` (see Dev Notes)
  - [x] When `has_enough_data` is True: render `<canvas id="strength-progress-chart">` and pass `chart_data_json` via `data-chart-data` attribute
  - [x] When `has_enough_data` is False: render `<p class="exercise-chart__empty">Not enough data yet. Log at least 2 sessions with this exercise to see a trend.</p>`
  - [x] Load `charts.js` after Chart.js CDN script (see Dev Notes for script order)
  - [x] Use BEM class naming: block `exercise-chart`, elements `exercise-chart__heading`, `exercise-chart__canvas-wrapper`, `exercise-chart__canvas`, `exercise-chart__empty`

- [x] Task 3: Implement strength chart initialization in `charts.js` (AC: 1)
  - [x] UPDATE `gymtrack/app/static/js/charts.js`
  - [x] Add `DOMContentLoaded` listener that finds `#strength-progress-chart` element
  - [x] Parse `chartData` from `element.dataset.chartData`
  - [x] Initialize `new Chart(...)` as a line chart (see Dev Notes for exact config)
  - [x] Do NOT remove any existing chart initialization code in the file (guard with `if (element)` check)

- [x] Task 4: Add CSS for `exercise-chart` component (AC: 1, 2)
  - [x] UPDATE `gymtrack/app/static/css/style.css`
  - [x] Add BEM styles for `.exercise-chart`, `.exercise-chart__heading`, `.exercise-chart__canvas-wrapper`, `.exercise-chart__canvas`, `.exercise-chart__empty`
  - [x] Canvas wrapper: `max-width: 800px; margin: 0 auto;` — keeps chart readable at all breakpoints

- [x] Task 5: Update `test_progress.py` with new tests (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/tests/test_progress.py` — ADD imports, helpers, and test functions; do NOT remove existing tests or fixtures
  - [x] Add imports: `WorkoutSet`, `WorkoutSession` from their respective model modules
  - [x] Add helper functions: `make_workout_session`, `make_workout_set` (see Dev Notes)
  - [x] Add `test_exercise_chart_unauthenticated` (AC: 3 — redirect to login)
  - [x] Add `test_exercise_chart_fewer_than_2_datapoints` (AC: 2 — empty state message)
  - [x] Add `test_exercise_chart_shows_best_weight_per_session` (AC: 1 — chart data in response)
  - [x] Add `test_exercise_chart_data_isolation` (AC: 3 — only own data returned)
  - [x] See full test specs in Dev Notes

## Dev Notes

### Current State of `progress/routes.py`

After Story 5.4, the file looks like this (DO NOT REMOVE OR MODIFY existing routes):

```python
from flask import render_template
from flask_login import current_user, login_required

from app.blueprints.progress import progress_bp
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord


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
```

After Task 1, the full imports section and the new route should look like this:

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

**IMPORTANT — Data Isolation:** `WorkoutSet` has no `user_id` column. User isolation is enforced by joining through `WorkoutSession` and filtering `WorkoutSession.user_id == current_user.id`. Never query `WorkoutSet` without this join + filter.

**IMPORTANT — `func.date()` compatibility:** SQLite returns a plain string (e.g. `"2026-05-04"`); PostgreSQL returns a Python `datetime.date` object. Always use `str(row.date)` when building `chart_data` to ensure JSON serialisation works on both databases.

**IMPORTANT — `is_complete` filter:** Only include sets from completed sessions. An in-progress session's sets should not appear on the chart because the session may be discarded or edited before completion.

### `WorkoutSet` Model (read-only — DO NOT MODIFY)

Location: `gymtrack/app/models/workout_set.py`

```python
class WorkoutSet(db.Model):
    __tablename__ = 'workout_sets'

    id          = db.Column(db.Integer, primary_key=True)
    session_id  = db.Column(db.Integer, db.ForeignKey('workout_sessions.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    set_number  = db.Column(db.Integer, nullable=False)
    weight_kg   = db.Column(db.Float, nullable=False)
    reps        = db.Column(db.Integer, nullable=False)
    logged_at   = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
```

No `user_id` on `WorkoutSet` — always join through `WorkoutSession` for user scoping.

### `WorkoutSession` Model (read-only — DO NOT MODIFY)

Location: `gymtrack/app/models/workout_session.py`

```python
class WorkoutSession(db.Model):
    __tablename__ = 'workout_sessions'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id     = db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=True)
    started_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
```

Use `started_at` as the session date (grouped via `func.date(WorkoutSession.started_at)`).

### Template Structure for `progress/exercise_chart.html`

```html
{% extends 'base.html' %}
{% block title %}{{ exercise.name }} Progression — GymTrack{% endblock %}
{% block content %}
<div class="exercise-chart">
  <h1 class="exercise-chart__heading">{{ exercise.name }} — Strength Progression</h1>
  {% if has_enough_data %}
    <div class="exercise-chart__canvas-wrapper">
      <canvas id="strength-progress-chart"
              class="exercise-chart__canvas"
              data-chart-data="{{ chart_data_json | e }}">
      </canvas>
    </div>
  {% else %}
    <p class="exercise-chart__empty">Not enough data yet. Log at least 2 sessions with this exercise to see a trend.</p>
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
- Chart.js CDN script MUST be loaded **before** `charts.js` so `Chart` is available when `charts.js` runs.
- The `{% block scripts %}` + `{{ super() }}` pattern assumes `base.html` defines a `scripts` block at the bottom of `<body>`. If `base.html` does not define this block, add `<script>` tags at the bottom of `{% block content %}` instead — check `base.html` before implementing.
- Do NOT add Chart.js CDN to `base.html` globally; it should only load on chart pages.

### `charts.js` Implementation for Task 3

Current state of `gymtrack/app/static/js/charts.js` — likely a stub comment. Add or replace with:

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

**Note:** Use `var` and ES5 function syntax (no arrow functions, no `const`/`let`) for maximum browser compatibility. Do NOT wrap in a module. Chart.js 4.x is loaded from the CDN; no bundler is used.

### Test Specifications for Task 5

Update `gymtrack/tests/test_progress.py` — **ADD** the following to the existing file. Do NOT remove the existing Story 5.4 tests or fixtures.

**New imports to add at the top:**
```python
import datetime
from app.models.workout_set import WorkoutSet
from app.models.workout_session import WorkoutSession
```
(Only add what isn't already imported — `datetime` is likely already there from Story 5.4.)

**New helper functions (add after the existing helpers):**
```python
def make_workout_session(db, user_id, is_complete=True):
    session = WorkoutSession(
        user_id=user_id,
        plan_id=None,
        started_at=datetime.datetime.utcnow(),
        is_complete=is_complete,
    )
    db.session.add(session)
    db.session.commit()
    return session


def make_workout_set(db, session_id, exercise_id, weight_kg, reps=5, set_number=1):
    ws = WorkoutSet(
        session_id=session_id,
        exercise_id=exercise_id,
        set_number=set_number,
        weight_kg=weight_kg,
        reps=reps,
        logged_at=datetime.datetime.utcnow(),
    )
    db.session.add(ws)
    db.session.commit()
    return ws
```

**New test cases (add at the end of the file under a `# ─── Story 6.1 ───` comment):**

```python
# ─── Story 6.1 — Strength Progression Chart ───

def test_exercise_chart_unauthenticated(client, app):
    """AC 3: unauthenticated GET → redirect to login."""
    with app.app_context():
        exercise = make_exercise(_db, name='Squat', muscle_group='Legs')
        response = client.get(f'/progress/exercise/{exercise.id}/')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']


def test_exercise_chart_fewer_than_2_datapoints(client, app):
    """AC 2: fewer than 2 data points → empty state message shown."""
    with app.app_context():
        user = make_user(_db)
        exercise = make_exercise(_db, name='Deadlift', muscle_group='Back')
        # Only 1 completed session
        session = make_workout_session(_db, user.id, is_complete=True)
        make_workout_set(_db, session.id, exercise.id, weight_kg=100.0)
        login_as(client, 'user@example.com', 'password123')
        response = client.get(f'/progress/exercise/{exercise.id}/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Not enough data yet' in html
        assert 'strength-progress-chart' not in html


def test_exercise_chart_shows_best_weight_per_session(client, app):
    """AC 1: chart data JSON contains best weight per session date."""
    with app.app_context():
        user = make_user(_db)
        exercise = make_exercise(_db, name='Bench Press', muscle_group='Chest')
        # Session 1 with two sets — best is 90 kg
        s1 = make_workout_session(_db, user.id, is_complete=True)
        make_workout_set(_db, s1.id, exercise.id, weight_kg=80.0, set_number=1)
        make_workout_set(_db, s1.id, exercise.id, weight_kg=90.0, set_number=2)
        # Session 2 (different date via manual started_at) — best is 95 kg
        s2 = WorkoutSession(
            user_id=user.id,
            plan_id=None,
            started_at=datetime.datetime.utcnow() + datetime.timedelta(days=7),
            is_complete=True,
        )
        _db.session.add(s2)
        _db.session.commit()
        make_workout_set(_db, s2.id, exercise.id, weight_kg=95.0)
        login_as(client, 'user@example.com', 'password123')
        response = client.get(f'/progress/exercise/{exercise.id}/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'strength-progress-chart' in html
        assert '90.0' in html
        assert '95.0' in html
        assert 'Not enough data yet' not in html


def test_exercise_chart_data_isolation(client, app):
    """AC 3: logged-in user only sees their own data — not another user's."""
    with app.app_context():
        user_a = make_user(_db, email='usera@example.com')
        user_b = make_user(_db, email='userb@example.com')
        exercise = make_exercise(_db, name='Pull-up', muscle_group='Back')
        # user_b has 2 sessions
        sb1 = make_workout_session(_db, user_b.id, is_complete=True)
        make_workout_set(_db, sb1.id, exercise.id, weight_kg=50.0)
        sb2 = WorkoutSession(
            user_id=user_b.id,
            plan_id=None,
            started_at=datetime.datetime.utcnow() + datetime.timedelta(days=7),
            is_complete=True,
        )
        _db.session.add(sb2)
        _db.session.commit()
        make_workout_set(_db, sb2.id, exercise.id, weight_kg=55.0)
        # user_a has no sessions — logs in and accesses the same exercise URL
        login_as(client, 'usera@example.com', 'password123')
        response = client.get(f'/progress/exercise/{exercise.id}/')
        assert response.status_code == 200
        html = response.data.decode()
        # user_a sees empty state — does NOT see user_b's weights
        assert 'Not enough data yet' in html
        assert '50.0' not in html
        assert '55.0' not in html
```

### Project Structure Notes

- Blueprint: `app/blueprints/progress/` — `__init__.py` (has `progress_bp`, `url_prefix='/progress'`), `routes.py`
- Template directory: `gymtrack/app/templates/progress/` — already exists and contains `prs.html` (Story 5.4); create `exercise_chart.html` here
- Static JS: `gymtrack/app/static/js/charts.js` — already exists as a stub; update with Chart.js initialization
- Static CSS: `gymtrack/app/static/css/style.css` — single file; append `.exercise-chart` BEM component styles
- Chart.js CDN: loaded per-page (in the template `{% block scripts %}`), NOT in `base.html`

### What NOT to Change

- Do NOT modify `WorkoutSet` or `WorkoutSession` models or their schemas — created in Epics 4 and are correct
- Do NOT modify `PersonalRecord` model or `pr_list()` route — this story is independent of PR data
- Do NOT remove or modify the `index()` placeholder route in `progress/routes.py` — future Epic 6/7 stories will implement it
- Do NOT add Chart.js to `base.html` globally — only load on chart pages to keep page weight low
- Do NOT call PR detection from this route — charts are read-only display of existing set data
- Do NOT add forms or POST routes — this is a GET-only read page

### References

- Strength progression chart requirements: [Source: _bmad-output/planning-artifacts/epics.md#Story-6.1]
- FR28: Users can view a strength progression chart per exercise (best weight over time): [Source: _bmad-output/planning-artifacts/epics.md#FR28]
- NFR3: Chart render < 1 second: [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-Overview]
- Chart.js CDN integration pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- Data isolation pattern (mandatory): [Source: _bmad-output/planning-artifacts/architecture.md#Process-Patterns]
- WorkoutSet model definition: [Source: _bmad-output/implementation-artifacts/4-2-log-sets-with-auto-save.md#Task-1]
- WorkoutSession model definition: [Source: _bmad-output/implementation-artifacts/4-1-start-a-workout-session.md#Task-1]
- Progress blueprint current state (after Story 5.4): [Source: _bmad-output/implementation-artifacts/5-4-view-all-personal-records.md#Current-State]
- Test fixture pattern (local fixtures, not conftest): [Source: _bmad-output/implementation-artifacts/5-4-view-all-personal-records.md#Test-Specifications]
- URL convention `/progress/exercise/<id>/`: [Source: _bmad-output/planning-artifacts/epics.md#Story-6.1]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- ✅ Task 1: Added `exercise_chart` route to `progress/routes.py` with correct aggregation query, `is_complete` filter, and user isolation via `WorkoutSession.user_id`.
- ✅ Task 2: Created `progress/exercise_chart.html` template with conditional chart/empty-state, BEM classes, and per-page Chart.js CDN loading.
- ✅ Task 3: Implemented `charts.js` with DOMContentLoaded listener, `if (element)` guard, and Chart.js 4.x line chart config using ES5 syntax.
- ✅ Task 4: Appended `.exercise-chart` BEM component CSS to `style.css` with `max-width: 800px` canvas wrapper.
- ✅ Task 5: Added 4 new tests (AC 1/2/3) to `test_progress.py` — all pass. Full suite: 134/134 passed, no regressions.

### File List

- gymtrack/app/blueprints/progress/routes.py (modified)
- gymtrack/app/templates/progress/exercise_chart.html (created)
- gymtrack/app/static/js/charts.js (modified)
- gymtrack/app/static/css/style.css (modified)
- gymtrack/tests/test_progress.py (modified)

### Change Log

- 2026-05-05: Implemented Story 6.1 — Strength Progression Chart. Added `exercise_chart` route, `exercise_chart.html` template, Chart.js initialization in `charts.js`, BEM CSS component, and 4 new tests covering AC 1/2/3.
