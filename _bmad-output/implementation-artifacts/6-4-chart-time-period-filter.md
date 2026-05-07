# Story 6.4: Chart Time-Period Filter

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to filter all progress charts by time period,
so that I can focus on recent progress or view my full history.

## Acceptance Criteria

1. **Given** I am on any progress chart page (`/progress/exercise/<id>/`, `/progress/frequency/`, `/progress/volume/`)
   **When** I select a time period filter (Last 4 Weeks / Last 3 Months / All Time)
   **Then** the page reloads and the chart shows only data within the selected period
   **And** the selected filter option is visually highlighted with the `chart-filter__btn--active` CSS modifier

2. **Given** I select "Last 4 Weeks" and have no data in that window
   **When** the filter is applied
   **Then** the chart shows the appropriate empty state message for that chart (not enough data / no history)
   **And** no chart canvas is rendered

3. **Given** the page loads for the first time (no `?period` query param)
   **When** the page renders
   **Then** "Last 3 Months" is the default selected filter

## Tasks / Subtasks

- [ ] Task 1: Add `request` import and update `exercise_chart` route to support `?period` filter (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [ ] Change `from flask import render_template` → `from flask import render_template, request`
  - [ ] In `exercise_chart(exercise_id)`: read `period = request.args.get('period', '3m')`
  - [ ] Compute `start_date` based on `period` (see Dev Notes — Full Route Implementations)
  - [ ] Apply `func.date(WorkoutSession.started_at) >= start_date.isoformat()` filter when `start_date` is not `None`
  - [ ] Add `current_period=period` to the `render_template` call
  - [ ] Do NOT change any other existing routes

- [ ] Task 2: Update `frequency_chart` route to support `?period` filter (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [ ] In `frequency_chart()`: read `period = request.args.get('period', '3m')`
  - [ ] Compute `num_weeks` and `earliest_monday` based on `period` (see Dev Notes — Full Route Implementations)
  - [ ] For `period='all'`: query `MIN(started_at)` to find the user's earliest completed session and derive `num_weeks` dynamically
  - [ ] Pass `current_period=period` to the template
  - [ ] The existing logic (bucketing, has_history) stays — only the date window changes

- [ ] Task 3: Update `volume_chart` route to support `?period` filter (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [ ] Apply identical `period`-based `num_weeks`/`earliest_monday` logic as `frequency_chart`
  - [ ] Pass `current_period=period` to the template
  - [ ] `has_enough_data` check, bucketing, and JSON serialization remain unchanged

- [ ] Task 4: Add `.chart-filter` UI to all three chart templates (AC: 1, 3)
  - [ ] UPDATE `gymtrack/app/templates/progress/exercise_chart.html`
    - [ ] Insert the `.chart-filter` block immediately after the `<h1>` heading, before the chart/empty state section
    - [ ] All three `<a>` hrefs use relative query-string only: `href="?period=4w"`, `href="?period=3m"`, `href="?period=all"`
    - [ ] Active class set with Jinja2: `class="chart-filter__btn{% if current_period == '4w' %} chart-filter__btn--active{% endif %}"`
    - [ ] See Dev Notes for exact HTML snippet
  - [ ] UPDATE `gymtrack/app/templates/progress/frequency_chart.html`
    - [ ] Same `.chart-filter` block pattern; active check uses `current_period`
  - [ ] UPDATE `gymtrack/app/templates/progress/volume_chart.html`
    - [ ] Same `.chart-filter` block pattern; active check uses `current_period`

- [ ] Task 5: Add `.chart-filter` CSS BEM component (AC: 1, 3)
  - [ ] UPDATE `gymtrack/app/static/css/style.css`
  - [ ] APPEND the `.chart-filter` block at the end of the file (after `.volume-chart` block from Story 6.3)
  - [ ] Do NOT remove or modify any existing CSS blocks
  - [ ] See Dev Notes for exact CSS

- [ ] Task 6: Update `test_progress.py` with period filter tests (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/tests/test_progress.py` — ADD new tests under a `# ─── Story 6.4 ───` comment; do NOT remove any existing tests
  - [ ] Add `test_chart_period_defaults_to_3m` (AC: 3)
  - [ ] Add `test_frequency_chart_period_4w_excludes_old_data` (AC: 1)
  - [ ] Add `test_frequency_chart_period_all_includes_old_data` (AC: 1)
  - [ ] Add `test_frequency_chart_period_4w_empty_state_no_recent_data` (AC: 2)
  - [ ] Add `test_chart_active_filter_class_rendered` (AC: 1 — active CSS class present)
  - [ ] See Dev Notes for full test specifications

## Dev Notes

### Current State of `progress/routes.py` (after Story 6.3)

The file currently looks exactly as below. Story 6.4 modifies `exercise_chart`, `frequency_chart`, and `volume_chart` — it does NOT touch `index()` or `pr_list()`.

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


@progress_bp.route('/volume/')
@login_required
def volume_chart():
    today = datetime.date.today()
    start_of_this_week = today - datetime.timedelta(days=today.weekday())
    earliest_monday = start_of_this_week - datetime.timedelta(weeks=11)

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
    has_enough_data = sum(1 for d in chart_data if d['volume'] > 0) >= 2

    return render_template(
        'progress/volume_chart.html',
        chart_data_json=json.dumps(chart_data),
        has_enough_data=has_enough_data,
    )
```

### Full Route Implementations for Story 6.4

Replace each of the three routes with the implementations below. The `index()` and `pr_list()` routes are **not touched**.

#### Updated `exercise_chart` route

```python
@progress_bp.route('/exercise/<int:exercise_id>/')
@login_required
def exercise_chart(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    period = request.args.get('period', '3m')
    today = datetime.date.today()

    if period == '4w':
        start_date = today - datetime.timedelta(weeks=4)
    elif period == '3m':
        start_date = today - datetime.timedelta(weeks=12)
    else:  # 'all'
        start_date = None

    base_filter = [
        WorkoutSession.user_id == current_user.id,
        WorkoutSet.exercise_id == exercise_id,
        WorkoutSession.is_complete == True,
    ]
    if start_date is not None:
        base_filter.append(func.date(WorkoutSession.started_at) >= start_date.isoformat())

    rows = (
        db.session.query(
            func.date(WorkoutSession.started_at).label('date'),
            func.max(WorkoutSet.weight_kg).label('weight')
        )
        .join(WorkoutSession, WorkoutSet.session_id == WorkoutSession.id)
        .filter(*base_filter)
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
        current_period=period,
    )
```

#### Updated `frequency_chart` route

```python
@progress_bp.route('/frequency/')
@login_required
def frequency_chart():
    period = request.args.get('period', '3m')
    today = datetime.date.today()
    start_of_this_week = today - datetime.timedelta(days=today.weekday())

    if period == '4w':
        num_weeks = 4
        earliest_monday = start_of_this_week - datetime.timedelta(weeks=3)
    elif period == '3m':
        num_weeks = 12
        earliest_monday = start_of_this_week - datetime.timedelta(weeks=11)
    else:  # 'all'
        earliest_val = (
            db.session.query(func.min(func.date(WorkoutSession.started_at)))
            .filter(
                WorkoutSession.user_id == current_user.id,
                WorkoutSession.is_complete == True,
            )
            .scalar()
        )
        if earliest_val is None:
            num_weeks = 1
            earliest_monday = start_of_this_week
        else:
            earliest_date = datetime.date.fromisoformat(str(earliest_val))
            earliest_monday = earliest_date - datetime.timedelta(days=earliest_date.weekday())
            num_weeks = max(1, (start_of_this_week - earliest_monday).days // 7 + 1)

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
    for i in range(num_weeks):
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
        for i in range(num_weeks)
    ]
    has_history = any(d['count'] > 0 for d in chart_data)

    return render_template(
        'progress/frequency_chart.html',
        chart_data_json=json.dumps(chart_data),
        has_history=has_history,
        current_period=period,
    )
```

**Important — `period='4w'` window:** `earliest_monday = start_of_this_week - timedelta(weeks=3)` gives 4 weeks total (current week + 3 prior). This is consistent with `period='3m'` where `weeks=11` gives 12 weeks total.

#### Updated `volume_chart` route

```python
@progress_bp.route('/volume/')
@login_required
def volume_chart():
    period = request.args.get('period', '3m')
    today = datetime.date.today()
    start_of_this_week = today - datetime.timedelta(days=today.weekday())

    if period == '4w':
        num_weeks = 4
        earliest_monday = start_of_this_week - datetime.timedelta(weeks=3)
    elif period == '3m':
        num_weeks = 12
        earliest_monday = start_of_this_week - datetime.timedelta(weeks=11)
    else:  # 'all'
        earliest_val = (
            db.session.query(func.min(func.date(WorkoutSession.started_at)))
            .filter(
                WorkoutSession.user_id == current_user.id,
                WorkoutSession.is_complete == True,
            )
            .scalar()
        )
        if earliest_val is None:
            num_weeks = 1
            earliest_monday = start_of_this_week
        else:
            earliest_date = datetime.date.fromisoformat(str(earliest_val))
            earliest_monday = earliest_date - datetime.timedelta(days=earliest_date.weekday())
            num_weeks = max(1, (start_of_this_week - earliest_monday).days // 7 + 1)

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

    week_volumes = {}
    for i in range(num_weeks):
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
        for i in range(num_weeks)
    ]
    has_enough_data = sum(1 for d in chart_data if d['volume'] > 0) >= 2

    return render_template(
        'progress/volume_chart.html',
        chart_data_json=json.dumps(chart_data),
        has_enough_data=has_enough_data,
        current_period=period,
    )
```

### Filter UI HTML Snippet (Task 4)

Insert this block **after the `<h1>` heading** and **before the chart/empty-state conditional** in each of the three chart templates:

```html
<div class="chart-filter">
  <span class="chart-filter__label">Period:</span>
  <a href="?period=4w"
     class="chart-filter__btn{% if current_period == '4w' %} chart-filter__btn--active{% endif %}">
    Last 4 Weeks
  </a>
  <a href="?period=3m"
     class="chart-filter__btn{% if current_period == '3m' %} chart-filter__btn--active{% endif %}">
    Last 3 Months
  </a>
  <a href="?period=all"
     class="chart-filter__btn{% if current_period == 'all' %} chart-filter__btn--active{% endif %}">
    All Time
  </a>
</div>
```

**Notes:**
- `href="?period=4w"` is a relative query string — it replaces only the `?period` param while preserving the path (including `<exercise_id>` in the exercise chart URL). This works correctly for all three routes.
- The active class uses `{% if current_period == '...' %}` (Jinja2). There is no space before `chart-filter__btn--active` in the class string when inactive — the space is inside the `{% if %}` block to avoid a leading space.
- Do NOT use form/POST for filtering — these are plain GET links.

### Current State of Each Chart Template (after Stories 6.1–6.3)

**`exercise_chart.html`** — abbreviated structure:
```html
{% extends 'base.html' %}
{% block title %}{{ exercise.name }} Progression — GymTrack{% endblock %}
{% block content %}
<div class="exercise-chart">
  <h1 class="exercise-chart__heading">{{ exercise.name }} — Strength Progression</h1>
  {# ← INSERT chart-filter block here #}
  {% if has_enough_data %}
    <div class="exercise-chart__canvas-wrapper">
      <canvas id="strength-progress-chart" class="exercise-chart__canvas"
              data-chart-data="{{ chart_data_json | e }}"></canvas>
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

**`frequency_chart.html`** — abbreviated structure:
```html
{% extends 'base.html' %}
{% block title %}Workout Frequency — GymTrack{% endblock %}
{% block content %}
<div class="frequency-chart">
  <h1 class="frequency-chart__heading">Workout Frequency</h1>
  {# ← INSERT chart-filter block here #}
  {% if has_history %}
    <div class="frequency-chart__canvas-wrapper">
      <canvas id="frequency-chart" class="frequency-chart__canvas"
              data-chart-data="{{ chart_data_json | e }}"></canvas>
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

**`volume_chart.html`** — abbreviated structure:
```html
{% extends 'base.html' %}
{% block title %}Volume Trend — GymTrack{% endblock %}
{% block content %}
<div class="volume-chart">
  <h1 class="volume-chart__heading">Volume Trend — Last 12 Weeks</h1>
  {# ← INSERT chart-filter block here #}
  {% if has_enough_data %}
    <div class="volume-chart__canvas-wrapper">
      <canvas id="volume-trend-chart" class="volume-chart__canvas"
              data-chart-data="{{ chart_data_json | e }}"></canvas>
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

**Note on `volume_chart.html` heading:** The `<h1>` text currently reads "Volume Trend — Last 12 Weeks". After Story 6.4, you may update it to "Volume Trend" (removing the hardcoded "Last 12 Weeks") since the period is now dynamic — but this is optional cosmetic cleanup.

### CSS for Task 5

Append to `gymtrack/app/static/css/style.css` **after** the `.volume-chart` block (added in Story 6.3):

```css
/* ─── Chart Time-Period Filter (Story 6.4) ─── */
.chart-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.chart-filter__label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-right: 0.25rem;
}

.chart-filter__btn {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
  text-decoration: none;
  background: #ffffff;
  transition: background 0.15s, border-color 0.15s;
}

.chart-filter__btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.chart-filter__btn--active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
  font-weight: 600;
}

.chart-filter__btn--active:hover {
  background: #2563eb;
  border-color: #2563eb;
}
```

### `charts.js` — No Changes Required

`charts.js` reads chart data from `data-chart-data` on the canvas element and initializes Chart.js. Since Story 6.4's filter changes happen server-side (the Flask route computes a different date window and serialises a different `chart_data` JSON), the JS receives the already-filtered data through the same `data-*` attribute. **Do NOT modify `charts.js`.**

### Test Specifications for Task 6

Append to `gymtrack/tests/test_progress.py` under `# ─── Story 6.4 ───`. Use existing helpers (`make_user`, `make_workout_session`, `make_workout_set`, `make_exercise`, `login_as`) — do NOT redefine them.

The `make_workout_session` helper must accept a `started_at` keyword argument (added in Story 6.3; verify it exists before writing tests).

```python
# ─── Story 6.4 — Chart Time-Period Filter ───

def test_chart_period_defaults_to_3m(client, app):
    """AC 3: loading /progress/frequency/ with no ?period renders 'Last 3 Months' as active."""
    with app.app_context():
        user = make_user(_db)
        login_as(client, user.email, 'password123')
        response = client.get('/progress/frequency/')
        assert response.status_code == 200
        html = response.data.decode()
        # The '3m' button must carry the active modifier; 4w and all must not
        assert 'chart-filter__btn--active' in html
        # Verify '3m' link has active class and '4w' does not
        assert '?period=4w" class="chart-filter__btn"' in html or '?period=4w"\n     class="chart-filter__btn"' in html
        assert 'chart-filter__btn chart-filter__btn--active' in html or 'chart-filter__btn--active' in html


def test_frequency_chart_period_4w_excludes_old_data(client, app):
    """AC 1: data from 5 weeks ago is not counted when period=4w."""
    with app.app_context():
        user = make_user(_db)
        today = datetime.date.today()
        start_of_this_week = today - datetime.timedelta(days=today.weekday())
        # Session 5 weeks ago — should be EXCLUDED in 4w window
        old_dt = datetime.datetime.combine(
            start_of_this_week - datetime.timedelta(weeks=5), datetime.time(10, 0)
        )
        # Session in current week — should be INCLUDED
        recent_dt = datetime.datetime.combine(start_of_this_week, datetime.time(10, 0))
        make_workout_session(_db, user.id, is_complete=True, started_at=old_dt)
        make_workout_session(_db, user.id, is_complete=True, started_at=recent_dt)
        login_as(client, user.email, 'password123')
        response = client.get('/progress/frequency/?period=4w')
        assert response.status_code == 200
        html = response.data.decode()
        # Only 1 session in window → "2" should NOT appear as a count; chart still renders (has_history=True)
        assert '<canvas' in html
        # The JSON should show max count of 1 per week, not 2
        import json as _json
        # Extract chart_data_json from data-chart-data attribute
        start = html.find('data-chart-data="') + len('data-chart-data="')
        end = html.find('"', start)
        chart_json = html[start:end].replace('&quot;', '"').replace('&#34;', '"')
        chart_data = _json.loads(chart_json)
        assert max(d['count'] for d in chart_data) == 1


def test_frequency_chart_period_all_includes_old_data(client, app):
    """AC 1: period=all shows a session from 20 weeks ago that period=3m would exclude."""
    with app.app_context():
        user = make_user(_db)
        today = datetime.date.today()
        start_of_this_week = today - datetime.timedelta(days=today.weekday())
        # Session 20 weeks ago — excluded by 3m (12 weeks), included by all
        old_dt = datetime.datetime.combine(
            start_of_this_week - datetime.timedelta(weeks=20), datetime.time(10, 0)
        )
        make_workout_session(_db, user.id, is_complete=True, started_at=old_dt)
        login_as(client, user.email, 'password123')
        # period=3m should show empty (no data in last 12 weeks)
        resp_3m = client.get('/progress/frequency/?period=3m')
        assert 'No workout history yet' in resp_3m.data.decode()
        # period=all should show the data
        resp_all = client.get('/progress/frequency/?period=all')
        assert '<canvas' in resp_all.data.decode()


def test_frequency_chart_period_4w_empty_state_no_recent_data(client, app):
    """AC 2: no data in last 4 weeks → empty state message shown, no canvas."""
    with app.app_context():
        user = make_user(_db)
        today = datetime.date.today()
        start_of_this_week = today - datetime.timedelta(days=today.weekday())
        # Session from 8 weeks ago — outside the 4w window
        old_dt = datetime.datetime.combine(
            start_of_this_week - datetime.timedelta(weeks=8), datetime.time(10, 0)
        )
        make_workout_session(_db, user.id, is_complete=True, started_at=old_dt)
        login_as(client, user.email, 'password123')
        response = client.get('/progress/frequency/?period=4w')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'No workout history yet' in html
        assert '<canvas' not in html


def test_chart_active_filter_class_rendered(client, app):
    """AC 1: selecting ?period=4w renders 4w button with chart-filter__btn--active class."""
    with app.app_context():
        user = make_user(_db)
        login_as(client, user.email, 'password123')
        response = client.get('/progress/frequency/?period=4w')
        assert response.status_code == 200
        html = response.data.decode()
        assert 'chart-filter__btn--active' in html
        # The active class must be on the 4w button's href region
        idx_4w = html.find('?period=4w')
        idx_active = html.find('chart-filter__btn--active')
        # Active class appears in close proximity to the 4w href
        assert abs(idx_4w - idx_active) < 200
```

**Note on `user.email`:** If `make_user` doesn't store the email on the returned object but you need the email for `login_as`, use `'user@example.com'` (the default email from the helper — verify in the test file). Update accordingly.

### Project Structure Notes

- Blueprint: `gymtrack/app/blueprints/progress/` — modifying `routes.py` only
- Templates to update: `gymtrack/app/templates/progress/exercise_chart.html`, `frequency_chart.html`, `volume_chart.html`
- Static JS: `gymtrack/app/static/js/charts.js` — **no changes**
- Static CSS: `gymtrack/app/static/css/style.css` — **append** `.chart-filter` block after `.volume-chart`
- Test file: `gymtrack/tests/test_progress.py` — **append** new Story 6.4 tests
- `charts.js` reads `data-chart-data` attribute and initializes Chart.js — server-side filtering means no JS changes needed

### What NOT to Change

- Do NOT modify `index()`, `pr_list()`, or any other routes outside this story
- Do NOT add Chart.js to `base.html` globally
- Do NOT create a second `DOMContentLoaded` listener in `charts.js`
- Do NOT remove or modify existing `.exercise-chart`, `.frequency-chart`, or `.volume-chart` CSS blocks
- Do NOT add a POST endpoint — period selection is a GET query parameter
- Do NOT modify any models (`WorkoutSession`, `WorkoutSet`, `Exercise`, `PersonalRecord`)
- Do NOT add `current_period` to the `pr_list()` route — it has no chart

### References

- FR31 — filter charts by time period: [Source: `_bmad-output/planning-artifacts/epics.md#FR31`]
- Story 6.4 acceptance criteria: [Source: `_bmad-output/planning-artifacts/epics.md#Story-6.4`]
- NFR3 — chart render < 1 second: [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-Overview`]
- BEM CSS conventions: [Source: `_bmad-output/planning-artifacts/architecture.md#CSS-Class-Naming`]
- JS conventions (ES5, var, no bundler): [Source: `_bmad-output/implementation-artifacts/6-3-volume-trend-chart.md#charts-js-Addition-for-Task-3`]
- `func.date()` SQLite/PostgreSQL compatibility (`str(row.x)` before `fromisoformat`): [Source: `_bmad-output/implementation-artifacts/6-3-volume-trend-chart.md#Dev-Notes`]
- `func.min` scalar query pattern: consistent with `func.sum` usage in `_bmad-output/implementation-artifacts/6-3-volume-trend-chart.md`
- Weekly bucketing pattern (Python-side, all weeks including zeros): [Source: `_bmad-output/implementation-artifacts/6-2-workout-frequency-chart.md#Full-Route-Implementation`]
- Data isolation pattern (`WorkoutSession.user_id == current_user.id`): [Source: `_bmad-output/planning-artifacts/architecture.md#Data-Architecture`]
- `charts.js` current state (after Stories 6.1–6.3): [Source: `_bmad-output/implementation-artifacts/6-3-volume-trend-chart.md#charts-js-Addition-for-Task-3`]
- Test helpers (`make_user`, `make_workout_session`, `make_workout_set`, `login_as`): [Source: `_bmad-output/implementation-artifacts/6-1-strength-progression-chart.md#Test-Specifications`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List

- `gymtrack/app/blueprints/progress/routes.py`
- `gymtrack/app/templates/progress/exercise_chart.html`
- `gymtrack/app/templates/progress/frequency_chart.html`
- `gymtrack/app/templates/progress/volume_chart.html`
- `gymtrack/app/static/css/style.css`
- `gymtrack/tests/test_progress.py`
