# Story 6.3: Volume Trend Chart

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to see my total volume lifted (weight × reps) per week,
so that I can track the overall load of my training.

## Acceptance Criteria

1. **Given** I navigate to `/progress/volume/`
   **When** the page loads
   **Then** a Chart.js line chart is rendered showing total volume (`sum of weight_kg × reps` across all sets) per week for the last 12 weeks
   **And** each data point represents one week (label = `Mon DD` of the week start) with the summed volume as the value
   **And** weeks with zero volume render as zero-height points (not omitted)
   **And** chart data is passed from the Flask view as `json.dumps([{"week": "...", "volume": ...}, ...])` in a `data-*` attribute — no separate API call
   **And** the chart renders within 1 second (NFR3)
   **And** only my own completed sessions and sets are counted (filtered by `WorkoutSession.user_id == current_user.id` and `is_complete == True`)

2. **Given** I have fewer than 2 weeks with non-zero volume in the last 12 weeks
   **When** the page loads
   **Then** I see: "Not enough data yet. Log sessions across at least 2 weeks to see a volume trend."
   **And** no chart canvas is rendered

3. **Given** another user is logged in
   **When** they access `/progress/volume/`
   **Then** only their own volume is counted — never another user's (data isolation enforced via `WorkoutSession.user_id` filter)

## Tasks / Subtasks

- [ ] Task 1: Add `volume_chart` route to `progress/routes.py` (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [ ] `import datetime` and `import json` already present — do NOT add duplicates
  - [ ] Add route `GET /volume/` with `@login_required`
  - [ ] Compute `earliest_monday` = Monday of the week 11 weeks before the current week (same pattern as `frequency_chart`)
  - [ ] Query per-day volume: `db.session.query(func.date(WorkoutSession.started_at).label('session_date'), func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).label('volume'))` joined on `WorkoutSet.session_id == WorkoutSession.id` — see Dev Notes for exact query
  - [ ] Filter: `WorkoutSession.user_id == current_user.id`, `WorkoutSession.is_complete == True`, `func.date(WorkoutSession.started_at) >= earliest_monday.isoformat()`
  - [ ] Group by `func.date(WorkoutSession.started_at)` and execute `.all()`
  - [ ] Python-side bucketing: build `week_volumes` dict keyed by ISO date of each week's Monday, default 0.0; aggregate `float(row.volume or 0)` per session into its week bucket
  - [ ] Build `chart_data` list of 12 `{"week": <label>, "volume": <float>}` dicts
  - [ ] Set `has_enough_data = sum(1 for d in chart_data if d['volume'] > 0) >= 2`
  - [ ] Render `progress/volume_chart.html` with `chart_data_json` and `has_enough_data`
  - [ ] Do NOT remove or modify any existing routes (`index`, `pr_list`, `exercise_chart`, `frequency_chart`)

- [ ] Task 2: Create `progress/volume_chart.html` template (AC: 1, 2)
  - [ ] CREATE `gymtrack/app/templates/progress/volume_chart.html`
  - [ ] Extend `base.html`; set `{% block title %}Volume Trend — GymTrack{% endblock %}`
  - [ ] When `has_enough_data` is True: render `<canvas id="volume-trend-chart">` with `data-chart-data="{{ chart_data_json | e }}"`
  - [ ] When `has_enough_data` is False: render `<p class="volume-chart__empty">Not enough data yet. Log sessions across at least 2 weeks to see a volume trend.</p>`
  - [ ] Load Chart.js CDN inside `{% block scripts %}` BEFORE `charts.js` (same pattern as `exercise_chart.html` and `frequency_chart.html`)
  - [ ] Use BEM class naming: block `volume-chart`, elements `volume-chart__heading`, `volume-chart__canvas-wrapper`, `volume-chart__canvas`, `volume-chart__empty`

- [ ] Task 3: Add volume chart initialization to `charts.js` (AC: 1)
  - [ ] UPDATE `gymtrack/app/static/js/charts.js`
  - [ ] Inside the existing `DOMContentLoaded` listener, add a new `var volEl = document.getElementById('volume-trend-chart');` block AFTER the existing frequency chart block
  - [ ] Parse `chartData` from `volEl.dataset.chartData`
  - [ ] Initialize `new Chart(volEl, {...})` as a **line** chart (see Dev Notes for exact config)
  - [ ] Guard with `if (volEl)` — do NOT break existing `strength-progress-chart` or `frequency-chart` initialization

- [ ] Task 4: Add CSS for `volume-chart` component (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/static/css/style.css`
  - [ ] Append BEM styles for `.volume-chart`, `.volume-chart__heading`, `.volume-chart__canvas-wrapper`, `.volume-chart__canvas`, `.volume-chart__empty`
  - [ ] Canvas wrapper: `max-width: 800px; margin: 0 auto;` — matches `exercise-chart` and `frequency-chart` pattern

- [ ] Task 5: Update `test_progress.py` with new tests (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/tests/test_progress.py` — ADD new test functions; do NOT remove any existing tests or fixtures
  - [ ] Add `test_volume_chart_unauthenticated` (AC: 3 — redirect to login)
  - [ ] Add `test_volume_chart_not_enough_weeks` (AC: 2 — only 1 week of data → empty state)
  - [ ] Add `test_volume_chart_with_data` (AC: 1 — 2+ weeks of data → chart rendered with volume values)
  - [ ] Add `test_volume_chart_data_isolation` (AC: 3 — only own sets counted)
  - [ ] See full test specs in Dev Notes

## Dev Notes

### Current State of `progress/routes.py` (after Story 6.2)

The file currently looks like this — the new route for Story 6.3 must be **added** without changing anything below:

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
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    earliest_monday = start_of_this_week - datetime.timedelta(weeks=11)

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

### Full Route Implementation for Task 1

After Task 1, append the new route. The complete `volume_chart` function to add:

```python
@progress_bp.route('/volume/')
@login_required
def volume_chart():
    today = datetime.date.today()
    # Monday of the current week
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    # Go back 11 more weeks → 12 weeks total
    earliest_monday = start_of_this_week - datetime.timedelta(weeks=11)

    # Fetch per-day total volume (weight_kg × reps) for all completed sessions
    rows = (
        db.session.query(
            func.date(WorkoutSession.started_at).label('session_date'),
            func.sum(WorkoutSet.weight_kg * WorkoutSet.reps).label('volume')
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSession.is_complete == True,
            func.date(WorkoutSession.started_at) >= earliest_monday.isoformat()
        )
        .group_by(func.date(WorkoutSession.started_at))
        .all()
    )

    # Python-side bucketing: initialise all 12 weeks to 0.0
    week_volumes = {}
    for i in range(12):
        week_start = earliest_monday + datetime.timedelta(weeks=i)
        week_volumes[week_start.isoformat()] = 0.0

    for row in rows:
        d = datetime.date.fromisoformat(str(row.session_date))
        week_start = d - datetime.timedelta(days=d.weekday())
        key = week_start.isoformat()
        if key in week_volumes:
            week_volumes[key] += float(row.volume or 0)

    chart_data = [
        {
            "week": (earliest_monday + datetime.timedelta(weeks=i)).strftime('%b %d'),
            "volume": week_volumes[(earliest_monday + datetime.timedelta(weeks=i)).isoformat()]
        }
        for i in range(12)
    ]
    # Require at least 2 distinct weeks with data to render the chart
    has_enough_data = sum(1 for d in chart_data if d['volume'] > 0) >= 2

    return render_template(
        'progress/volume_chart.html',
        chart_data_json=json.dumps(chart_data),
        has_enough_data=has_enough_data,
    )
```

**IMPORTANT — `func.sum` on product:** SQLAlchemy compiles `WorkoutSet.weight_kg * WorkoutSet.reps` to `weight_kg * reps` in SQL. Always guard with `float(row.volume or 0)` — `func.sum` returns `None` (not 0) when there are no rows.

**IMPORTANT — `func.date()` compatibility:** SQLite returns a plain string; PostgreSQL returns a `datetime.date` object. Always use `str(row.session_date)` before `datetime.date.fromisoformat()`.

**IMPORTANT — data isolation:** Always filter `WorkoutSession.user_id == current_user.id`. Never query `WorkoutSet` without this join — a set could belong to any user's session.

**IMPORTANT — `is_complete` filter:** Only count completed sessions. The join to `WorkoutSession` ensures all filtered sets belong to completed sessions.

**IMPORTANT — Week bucketing:** Python-side bucketing ensures all 12 weeks appear including zeros. SQL `GROUP BY` would omit weeks with no data.

### Template Structure for `progress/volume_chart.html`

```html
{% extends 'base.html' %}
{% block title %}Volume Trend — GymTrack{% endblock %}
{% block content %}
<div class="volume-chart">
  <h1 class="volume-chart__heading">Volume Trend — Last 12 Weeks</h1>
  {% if has_enough_data %}
    <div class="volume-chart__canvas-wrapper">
      <canvas id="volume-trend-chart"
              class="volume-chart__canvas"
              data-chart-data="{{ chart_data_json | e }}">
      </canvas>
    </div>
  {% else %}
    <p class="volume-chart__empty">Not enough data yet. Log sessions across at least 2 weeks to see a volume trend.</p>
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
- Chart.js CDN script MUST be loaded **before** `charts.js`.
- Do NOT add Chart.js CDN to `base.html` globally — load per page only.

### Current State of `charts.js` (after Story 6.2)

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
        plugins: { legend: { display: false } },
        scales: {
          y: { title: { display: true, text: 'Weight (kg)' }, beginAtZero: false },
          x: { title: { display: true, text: 'Date' } }
        }
      }
    });
  }

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
        plugins: { legend: { display: false } },
        scales: {
          y: { title: { display: true, text: 'Sessions' }, beginAtZero: true, ticks: { stepSize: 1, precision: 0 } },
          x: { title: { display: true, text: 'Week Starting' } }
        }
      }
    });
  }
});
```

### `charts.js` Addition for Task 3

Add the Story 6.3 block **inside the existing `DOMContentLoaded` listener** (do NOT create a second listener), immediately after the closing `}` of the frequency chart `if` block:

```javascript
  // Story 6.3 — Volume Trend Chart
  var volEl = document.getElementById('volume-trend-chart');
  if (volEl) {
    var volData = JSON.parse(volEl.dataset.chartData);
    new Chart(volEl, {
      type: 'line',
      data: {
        labels: volData.map(function (d) { return d.week; }),
        datasets: [{
          label: 'Volume (kg × reps)',
          data: volData.map(function (d) { return d.volume; }),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.1,
          fill: true,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            title: { display: true, text: 'Volume (kg × reps)' },
            beginAtZero: true
          },
          x: {
            title: { display: true, text: 'Week Starting' }
          }
        }
      }
    });
  }
```

**Note:** Use `var` and ES5 `function` syntax throughout — no `const`/`let`, no arrow functions. Chart.js 4.x is loaded from CDN; no bundler is in use.

### CSS for Task 4

Append to `gymtrack/app/static/css/style.css` — do NOT replace the existing `.exercise-chart` or `.frequency-chart` blocks:

```css
/* ─── Volume Trend Chart (Story 6.3) ─── */
.volume-chart {
  padding: 1.5rem;
}

.volume-chart__heading {
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.volume-chart__canvas-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.volume-chart__canvas {
  width: 100%;
}

.volume-chart__empty {
  color: #6b7280;
  text-align: center;
  margin-top: 2rem;
}
```

### Test Specifications for Task 5

Update `gymtrack/tests/test_progress.py` — **ADD** the following under a `# ─── Story 6.3 ───` comment. Do NOT remove any existing tests from Stories 6.1, 6.2, or earlier.

The existing file already imports `datetime`, `WorkoutSet`, `WorkoutSession`, and has `make_workout_session` and `make_workout_set` helper functions. Do NOT re-add them.

`make_workout_set(_db, session_id, exercise_id, weight_kg, reps)` — call this to create sets for volume tests.

To put a session in a specific week, pass a `started_at` keyword to `make_workout_session` (verify the helper signature in the file; add `started_at` parameter if missing, defaulting to `datetime.datetime.utcnow()`).

```python
# ─── Story 6.3 — Volume Trend Chart ───

def test_volume_chart_unauthenticated(client, app):
    """AC 3: unauthenticated GET → redirect to login."""
    response = client.get('/progress/volume/')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_volume_chart_not_enough_weeks(client, app):
    """AC 2: only 1 week of data → empty state message, no canvas."""
    with app.app_context():
        user = make_user(_db)
        # All sessions in the current week → only 1 week with data
        session = make_workout_session(_db, user.id, is_complete=True)
        exercise = Exercise.query.first() or make_exercise(_db)
        make_workout_set(_db, session.id, exercise.id, weight_kg=100.0, reps=5)
        login_as(client, 'user@example.com', 'password123')
        response = client.get('/progress/volume/')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'Not enough data yet' in html
        assert '<canvas' not in html


def test_volume_chart_with_data(client, app):
    """AC 1: 2+ weeks of data → line chart rendered with volume values."""
    with app.app_context():
        user = make_user(_db)
        today = datetime.date.today()
        start_of_this_week = today - datetime.timedelta(days=today.weekday())
        # Week 1: current week
        week1_dt = datetime.datetime.combine(start_of_this_week, datetime.time(10, 0))
        # Week 2: two weeks ago
        week2_dt = datetime.datetime.combine(start_of_this_week - datetime.timedelta(weeks=2), datetime.time(10, 0))
        session1 = make_workout_session(_db, user.id, is_complete=True, started_at=week1_dt)
        session2 = make_workout_session(_db, user.id, is_complete=True, started_at=week2_dt)
        exercise = Exercise.query.first() or make_exercise(_db)
        # 100 kg × 5 reps = 500 volume per session
        make_workout_set(_db, session1.id, exercise.id, weight_kg=100.0, reps=5)
        make_workout_set(_db, session2.id, exercise.id, weight_kg=100.0, reps=5)
        login_as(client, 'user@example.com', 'password123')
        response = client.get('/progress/volume/')
        assert response.status_code == 200
        html = response.data.decode()
        assert '<canvas' in html
        assert 'volume-trend-chart' in html
        assert 'Not enough data yet' not in html
        assert '500' in html  # volume value present in JSON


def test_volume_chart_data_isolation(client, app):
    """AC 3: logged-in user only sees their own volume — not another user's."""
    with app.app_context():
        user_a = make_user(_db, email='usera@example.com')
        user_b = make_user(_db, email='userb@example.com')
        today = datetime.date.today()
        start_of_this_week = today - datetime.timedelta(days=today.weekday())
        week1_dt = datetime.datetime.combine(start_of_this_week, datetime.time(10, 0))
        week2_dt = datetime.datetime.combine(start_of_this_week - datetime.timedelta(weeks=2), datetime.time(10, 0))
        # user_b has 2 weeks of data
        s1 = make_workout_session(_db, user_b.id, is_complete=True, started_at=week1_dt)
        s2 = make_workout_session(_db, user_b.id, is_complete=True, started_at=week2_dt)
        exercise = Exercise.query.first() or make_exercise(_db)
        make_workout_set(_db, s1.id, exercise.id, weight_kg=200.0, reps=5)
        make_workout_set(_db, s2.id, exercise.id, weight_kg=200.0, reps=5)
        # user_a has no sessions — logs in and checks volume
        login_as(client, 'usera@example.com', 'password123')
        response = client.get('/progress/volume/')
        assert response.status_code == 200
        html = response.data.decode()
        # user_a sees empty state — does NOT see user_b's volume
        assert 'Not enough data yet' in html
        assert '1000' not in html  # user_b's 200×5=1000 must not appear
```

**Note on `make_workout_session` with `started_at`:** The existing helper may not accept a `started_at` kwarg. Inspect the helper in `test_progress.py` before writing the test. If `started_at` is not yet a parameter, add it with `started_at=None` default: `session.started_at = started_at or datetime.datetime.utcnow()`. Do NOT break existing callers.

**Note on `make_exercise`:** If the test file doesn't have a `make_exercise` helper, use `Exercise.query.first()` and ensure the database has at least one exercise seeded via the app fixture, or create one inline using the SQLAlchemy model directly.

**Note on `make_user` signature:** Check whether `make_user` in `test_progress.py` accepts an `email` keyword argument (it was verified to do so in Story 6.2). If it does, use `make_user(_db, email='usera@example.com')`.

### Project Structure Notes

- Blueprint: `gymtrack/app/blueprints/progress/` — `__init__.py` (has `progress_bp`, `url_prefix='/progress'`), `routes.py`
- Template directory: `gymtrack/app/templates/progress/` — already contains `prs.html`, `exercise_chart.html`, `frequency_chart.html`; create `volume_chart.html` here
- Static JS: `gymtrack/app/static/js/charts.js` — already has Story 6.1 and 6.2 blocks; **extend** the existing `DOMContentLoaded` listener
- Static CSS: `gymtrack/app/static/css/style.css` — single file; **append** `.volume-chart` BEM component block after `.frequency-chart`
- Chart.js CDN: loaded per-page in the template `{% block scripts %}`, NOT in `base.html`
- Test file: `gymtrack/tests/test_progress.py` — **append** new tests; do NOT create a new test file

### What NOT to Change

- Do NOT modify `WorkoutSet`, `WorkoutSession`, or any other models
- Do NOT modify `PersonalRecord` model, `pr_list()` route, `exercise_chart()` route, or `frequency_chart()` route
- Do NOT remove or modify the `index()` placeholder route — a later story (Epic 7) will implement it
- Do NOT add Chart.js to `base.html` globally
- Do NOT create a second `DOMContentLoaded` listener in `charts.js` — add the volume block inside the existing one
- Do NOT replace the existing `.exercise-chart` or `.frequency-chart` CSS blocks — append the new `.volume-chart` block after them
- Do NOT add any POST routes or form handling — this is a GET-only read page

### References

- Volume trend chart requirements: [Source: _bmad-output/planning-artifacts/epics.md#Story-6.3]
- FR30: Users can view a volume trend chart (total weight lifted per week): [Source: _bmad-output/planning-artifacts/epics.md#FR30]
- NFR3: Chart render < 1 second: [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-Overview]
- Chart.js CDN integration pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- Data isolation pattern (mandatory): [Source: _bmad-output/planning-artifacts/architecture.md#Process-Patterns]
- WorkoutSet model (`weight_kg`, `reps`, `session_id`, `exercise_id`): [Source: _bmad-output/implementation-artifacts/4-2-log-sets-with-auto-save.md]
- WorkoutSession model (`user_id`, `is_complete`, `started_at`): [Source: _bmad-output/implementation-artifacts/4-1-start-a-workout-session.md]
- `charts.js` current state + ES5 convention: [Source: _bmad-output/implementation-artifacts/6-2-workout-frequency-chart.md#charts-js-Addition-for-Task-3]
- `func.date()` SQLite/PostgreSQL compatibility note: [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Dev-Notes]
- `func.sum` returns None guard (`or 0`): [Source: _bmad-output/implementation-artifacts/6-3-volume-trend-chart.md#Full-Route-Implementation]
- BEM CSS + canvas-wrapper pattern: [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Task-4]
- Python-side bucketing (all 12 weeks including zeros): [Source: _bmad-output/implementation-artifacts/6-2-workout-frequency-chart.md#Full-Route-Implementation]
- Test fixture helpers (`make_workout_session`, `make_workout_set`, `make_user`): [Source: _bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Test-Specifications]
- Progress blueprint URL prefix `/progress`: [Source: _bmad-output/planning-artifacts/architecture.md#URL-Conventions]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List
