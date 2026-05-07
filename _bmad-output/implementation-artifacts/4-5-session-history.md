# Story 4.5: Session History

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to view a list of all my past completed sessions,
so that I can track my workout frequency and review past logs.

## Acceptance Criteria

1. **Given** I navigate to `/workouts/sessions/`
   **When** the page loads
   **Then** I see all my completed sessions listed, sorted by most recent first
   **And** each entry shows: date, plan name (or "Ad-hoc"), exercise count, total sets

2. **Given** I click on a past session
   **When** the detail page loads
   **Then** I see all exercises and every set logged (weight, reps, set number)

3. **Given** I have no completed sessions
   **When** the page loads
   **Then** I see: "No completed sessions yet. Start your first workout!"

## Tasks / Subtasks

- [ ] Task 1: Update `session_list` route to show only completed sessions with exercise count and total sets (AC: 1, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Rewrite the `session_list` view to filter only `is_complete=True` sessions ordered by `completed_at.desc()`
  - [ ] Compute per-session stats (exercise count, total sets) using a single aggregated query
  - [ ] Pass `sessions`, `plan_map`, and `session_stats` to the template
  - [ ] New route implementation:
    ```python
    @workouts_bp.route('/sessions/')
    @login_required
    def session_list():
        from sqlalchemy import func
        sessions = WorkoutSession.query.filter_by(
            user_id=current_user.id, is_complete=True
        ).order_by(WorkoutSession.completed_at.desc()).all()
        plan_ids = {s.plan_id for s in sessions if s.plan_id}
        plans = WorkoutPlan.query.filter(WorkoutPlan.id.in_(plan_ids)).all() if plan_ids else []
        plan_map = {p.id: p for p in plans}
        session_ids = [s.id for s in sessions]
        session_stats = {}
        if session_ids:
            rows = db.session.query(
                WorkoutSet.session_id,
                func.count(func.distinct(WorkoutSet.exercise_id)).label('exercise_count'),
                func.count(WorkoutSet.id).label('total_sets'),
            ).filter(WorkoutSet.session_id.in_(session_ids)).group_by(WorkoutSet.session_id).all()
            session_stats = {r.session_id: {'exercise_count': r.exercise_count, 'total_sets': r.total_sets}
                             for r in rows}
        return render_template(
            'workouts/session_list.html',
            sessions=sessions,
            plan_map=plan_map,
            session_stats=session_stats,
        )
    ```

- [ ] Task 2: Update `session_list.html` to display new data and empty state (AC: 1, 3)
  - [ ] UPDATE `gymtrack/app/templates/workouts/session_list.html`
  - [ ] Show completed sessions with date, plan name, exercise count, total sets, and a link to detail
  - [ ] Change empty state message to: "No completed sessions yet. Start your first workout!"
  - [ ] Remove the "Resume" link and "In Progress" status (incomplete sessions no longer shown here)
  - [ ] Link each session entry to `url_for('workouts.session_detail', id=s.id)`
  - [ ] New template:
    ```html
    {% extends 'base.html' %}
    {% block title %}Session History — GymTrack{% endblock %}
    {% block content %}
    <div class="session-list">
      <h1 class="session-list__heading">Session History</h1>
      {% if sessions %}
        {% for s in sessions %}
        {% set stats = session_stats.get(s.id, {'exercise_count': 0, 'total_sets': 0}) %}
        <a class="session-list__item session-list__item--link"
           href="{{ url_for('workouts.session_detail', id=s.id) }}">
          <div class="session-list__meta">
            <span class="session-list__date">{{ s.completed_at | strftime('%b %d, %Y at %H:%M') }}</span>
            <span class="session-list__plan">{{ plan_map[s.plan_id].name if s.plan_id in plan_map else 'Ad-hoc' }}</span>
          </div>
          <div class="session-list__stats">
            <span class="session-list__exercises">{{ stats.exercise_count }} exercise{{ 's' if stats.exercise_count != 1 else '' }}</span>
            <span class="session-list__sets">{{ stats.total_sets }} set{{ 's' if stats.total_sets != 1 else '' }}</span>
          </div>
        </a>
        {% endfor %}
      {% else %}
        <p class="session-list__empty">No completed sessions yet. Start your first workout!</p>
      {% endif %}
    </div>
    {% endblock %}
    ```

- [ ] Task 3: Add `session_detail` route for viewing individual past completed sessions (AC: 2)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Add route AFTER `session_list`:
    ```python
    @workouts_bp.route('/sessions/<int:id>/')
    @login_required
    def session_detail(id):
        workout_session = WorkoutSession.query.filter_by(
            id=id, user_id=current_user.id, is_complete=True
        ).first_or_404()
        logged_sets = WorkoutSet.query.filter_by(
            session_id=workout_session.id
        ).order_by(WorkoutSet.exercise_id, WorkoutSet.set_number).all()
        sets_by_exercise = {}
        for ws in logged_sets:
            sets_by_exercise.setdefault(ws.exercise_id, []).append(ws)
        all_exercises = Exercise.query.order_by(Exercise.name).all()
        exercise_map = {e.id: e for e in all_exercises}
        plan_name = None
        if workout_session.plan_id:
            plan = WorkoutPlan.query.filter_by(id=workout_session.plan_id).first()
            plan_name = plan.name if plan else None
        return render_template(
            'workouts/session_detail.html',
            session=workout_session,
            sets_by_exercise=sets_by_exercise,
            exercise_map=exercise_map,
            plan_name=plan_name,
        )
    ```
  - [ ] Note: `is_complete=True` in the filter means incomplete sessions return 404 — correct behaviour

- [ ] Task 4: Create `session_detail.html` template (AC: 2)
  - [ ] CREATE `gymtrack/app/templates/workouts/session_detail.html`
  - [ ] Extend `base.html`, use BEM class names
  - [ ] Show heading with date and plan name (or "Ad-hoc")
  - [ ] For each exercise in `sets_by_exercise`, render a group with exercise name and each set (weight, reps, set number)
  - [ ] Link back to `/workouts/sessions/` ("Back to Session History")
  - [ ] WCAG: All content readable without color dependency; use `<ul>` for set lists, semantic headings
  - [ ] Template:
    ```html
    {% extends 'base.html' %}
    {% block title %}Session Detail — GymTrack{% endblock %}
    {% block content %}
    <div class="session-detail">
      <h1 class="session-detail__heading">
        {{ session.completed_at | strftime('%b %d, %Y') }}
        — {{ plan_name if plan_name else 'Ad-hoc' }}
      </h1>
      <section class="session-detail__summary">
        {% for exercise_id, sets in sets_by_exercise.items() %}
        <div class="session-detail__exercise-group">
          <h2 class="session-detail__exercise-name">{{ exercise_map[exercise_id].name }}</h2>
          <ul class="session-detail__set-list">
            {% for ws in sets %}
            <li class="session-detail__set-item">
              Set {{ ws.set_number }}: {{ ws.weight_kg }}kg &times; {{ ws.reps }} reps
            </li>
            {% endfor %}
          </ul>
        </div>
        {% endfor %}
      </section>
      <a class="session-detail__back-link btn btn--secondary"
         href="{{ url_for('workouts.session_list') }}">Back to Session History</a>
    </div>
    {% endblock %}
    ```

- [ ] Task 5: Add Story 4.5 tests (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py`
  - [ ] Add section header: `# ─────────────────────────────────────────────`
    `# Story 4.5 — Session History`
  - [ ] Add the `sqlalchemy` import for `func` at the top of the new section if needed (already available via `db.session.query`)
  - [ ] Tests to add:
    - `test_session_list_shows_only_completed` — create 1 complete + 1 incomplete session; GET `/workouts/sessions/` → 200, complete session appears, incomplete does NOT appear, no "Resume" button
    - `test_session_list_shows_exercise_count_and_sets` — create completed session with 2 exercises (1 set each); GET → 200, response contains "2 exercises" and "2 sets"
    - `test_session_list_no_completed_sessions` — create 0 complete sessions; GET → 200, contains "No completed sessions yet"
    - `test_session_list_sorted_most_recent_first` — create 2 complete sessions at different times; GET → 200, more recent completed_at appears first in HTML
    - `test_session_detail_renders` — create completed session with 1 exercise + 1 set; GET `/workouts/sessions/<id>/` → 200, contains exercise name, weight, reps
    - `test_session_detail_incomplete_returns_404` — GET `/workouts/sessions/<id>/` for incomplete session → 404
    - `test_session_detail_isolation` — create session for user B; login as user A; GET → 404
    - `test_session_detail_unauthenticated` — GET `/workouts/sessions/<id>/` without login → 302 to login
  - [ ] Example tests:
    ```python
    # ─────────────────────────────────────────────
    # Story 4.5 — Session History
    # ─────────────────────────────────────────────

    def make_completed_session(db, user_id, plan_id=None, completed_at=None):
        from datetime import datetime
        now = completed_at or datetime.utcnow()
        s = WorkoutSession(
            user_id=user_id,
            plan_id=plan_id,
            started_at=now,
            is_complete=True,
            completed_at=now,
        )
        db.session.add(s)
        db.session.commit()
        return s

    def test_session_list_shows_only_completed(client, app):
        with app.app_context():
            _db.create_all()
            user = make_user(_db)
            login_as(client, 'user@example.com', 'password123')
            complete_s = make_completed_session(_db, user.id)
            incomplete_s = make_session(_db, user.id, is_complete=False)
            response = client.get('/workouts/sessions/')
            assert response.status_code == 200
            html = response.data.decode()
            assert f'/workouts/sessions/{complete_s.id}/' in html
            assert f'/workouts/sessions/{incomplete_s.id}/log' not in html
            assert 'Resume' not in html

    def test_session_list_no_completed_sessions(client, app):
        with app.app_context():
            _db.create_all()
            make_user(_db)
            login_as(client, 'user@example.com', 'password123')
            response = client.get('/workouts/sessions/')
            assert response.status_code == 200
            assert b'No completed sessions yet' in response.data

    def test_session_list_shows_exercise_count_and_sets(client, app):
        with app.app_context():
            _db.create_all()
            user = make_user(_db)
            e1 = make_exercise(_db, name='Squat')
            e2 = make_exercise(_db, name='Deadlift')
            session = make_completed_session(_db, user.id)
            make_workout_set(_db, session.id, e1.id, set_number=1)
            make_workout_set(_db, session.id, e2.id, set_number=1)
            login_as(client, 'user@example.com', 'password123')
            response = client.get('/workouts/sessions/')
            assert response.status_code == 200
            assert b'2 exercises' in response.data
            assert b'2 sets' in response.data

    def test_session_detail_renders(client, app):
        with app.app_context():
            _db.create_all()
            user = make_user(_db)
            exercise = make_exercise(_db, name='Bench Press')
            session = make_completed_session(_db, user.id)
            make_workout_set(_db, session.id, exercise.id, weight_kg=80.0, reps=8)
            login_as(client, 'user@example.com', 'password123')
            response = client.get(f'/workouts/sessions/{session.id}/')
            assert response.status_code == 200
            assert b'Bench Press' in response.data
            assert b'80.0' in response.data
            assert b'8' in response.data

    def test_session_detail_incomplete_returns_404(client, app):
        with app.app_context():
            _db.create_all()
            user = make_user(_db)
            session = make_session(_db, user.id, is_complete=False)
            login_as(client, 'user@example.com', 'password123')
            response = client.get(f'/workouts/sessions/{session.id}/')
            assert response.status_code == 404

    def test_session_detail_isolation(client, app):
        with app.app_context():
            _db.create_all()
            make_user(_db, email='a@example.com')
            user_b = make_user(_db, email='b@example.com')
            session_b = make_completed_session(_db, user_b.id)
            login_as(client, 'a@example.com', 'password123')
            response = client.get(f'/workouts/sessions/{session_b.id}/')
            assert response.status_code == 404

    def test_session_detail_unauthenticated(client, app):
        with app.app_context():
            _db.create_all()
            response = client.get('/workouts/sessions/1/')
            assert response.status_code == 302
            assert '/auth/login' in response.headers['Location']
    ```

## Dev Notes

### What Story 4.5 Changes in the `session_list` Route

The `session_list` route at `GET /workouts/sessions/` was established in Story 4.3 to support the "Resume" flow for incomplete sessions. Story 4.5 repurposes this URL as the session history page — it now **only shows completed sessions**. Incomplete sessions are excluded from this view entirely.

**Before (Story 4.3):** All sessions, ordered incomplete-first, with a "Resume" link for active sessions.
**After (Story 4.5):** Only completed sessions, ordered by `completed_at` descending, with exercise count and total sets, and a link to the session detail page.

The "Resume" flow for incomplete sessions remains accessible through the guard in `start_session` and `session_new` routes — users are redirected to their active session when they try to start a new one.

### Story 4.3 Tests That Will Break

The following Story 4.3 tests in `test_workouts.py` assert behaviours that Story 4.5 explicitly replaces. They should be **removed** when implementing this story:
- `test_session_list_shows_incomplete_first` — incomplete sessions no longer shown
- `test_session_list_shows_resume_link` — "Resume" link removed from this page
- `test_session_list_no_resume_for_complete` — logic no longer relevant

The `test_session_list_empty` test checks for `"No sessions yet"` — this must be updated to check for `"No completed sessions yet"` instead (or removed and replaced by the new `test_session_list_no_completed_sessions`).

The `test_session_list_unauthenticated` test remains valid — unauthenticated GET still redirects to login.

### Computing Exercise Count and Total Sets Efficiently

Use a single aggregated query against all session IDs at once — do NOT loop and query individually (N+1 problem):

```python
from sqlalchemy import func

session_ids = [s.id for s in sessions]
if session_ids:
    rows = db.session.query(
        WorkoutSet.session_id,
        func.count(func.distinct(WorkoutSet.exercise_id)).label('exercise_count'),
        func.count(WorkoutSet.id).label('total_sets'),
    ).filter(WorkoutSet.session_id.in_(session_ids)).group_by(WorkoutSet.session_id).all()
    session_stats = {r.session_id: {'exercise_count': r.exercise_count, 'total_sets': r.total_sets}
                     for r in rows}
else:
    session_stats = {}
```

Sessions with zero sets will not appear in the `session_stats` dict — use `.get(s.id, {'exercise_count': 0, 'total_sets': 0})` in the template.

### User Data Isolation (MANDATORY)

Both `session_list` and `session_detail` must scope all queries to `current_user.id`:
```python
# session_list — filter by user
WorkoutSession.query.filter_by(user_id=current_user.id, is_complete=True)

# session_detail — filter by user AND is_complete
WorkoutSession.query.filter_by(id=id, user_id=current_user.id, is_complete=True).first_or_404()
```

An incomplete session accessed at `GET /workouts/sessions/<id>/` returns 404 — this is correct.

### `session_detail` Route URL Pattern

The detail URL is `/workouts/sessions/<int:id>/` (trailing slash, no action suffix). This follows the resource URL pattern established in the architecture for collection/item pattern:
- Collection: `/workouts/sessions/`
- Item: `/workouts/sessions/<id>/`

### Variable Naming Conventions (Inherited from 4.1–4.4)

- Use `workout_session` (not `session`) for the SQLAlchemy `WorkoutSession` object in the route — avoids collision with Flask's `session` cookie proxy
- Pass as `session=workout_session` to templates — templates already reference `session.id`, `session.completed_at`, etc.

### Date Display

The session list uses `completed_at` for sorting and display (completed sessions always have `completed_at` set by Story 4.4's implementation). The `session_detail` heading also uses `completed_at`.

Use the `strftime` Jinja2 filter per architecture:
```jinja2
{{ s.completed_at | strftime('%b %d, %Y at %H:%M') }}
```

### No New Models, No New Migrations

This story adds zero schema changes — it reads from existing `workout_sessions` and `workout_sets` tables with no structural modifications.

### `sqlalchemy.func` Import

The `session_list` route uses `from sqlalchemy import func` for the aggregated query. Add this import inside the function body (not at module level) to avoid polluting the module namespace, consistent with how other routes use `from datetime import datetime`.

### Architecture Compliance

- Routes in `gymtrack/app/blueprints/workouts/routes.py` ✅
- No new forms needed (read-only views) ✅
- Templates in `gymtrack/app/templates/workouts/` ✅
- BEM CSS class names (`session-list__*`, `session-detail__*`) ✅
- User isolation enforced via `filter_by(user_id=current_user.id)` on every query ✅
- No flash messages needed (read-only views) ✅
- Tests in `gymtrack/tests/test_workouts.py` ✅
- SQLAlchemy variable named `workout_session` (not `session`) ✅

### Project Structure Notes

**Files to UPDATE:**
- `gymtrack/app/blueprints/workouts/routes.py` — rewrite `session_list`, add `session_detail`
- `gymtrack/app/templates/workouts/session_list.html` — update to history view
- `gymtrack/tests/test_workouts.py` — remove obsolete 4.3 session_list tests, add 4.5 tests

**Files to CREATE:**
- `gymtrack/app/templates/workouts/session_detail.html`

**No new files needed:**
- No new models
- No new migrations
- No new forms
- No new JS

### References

- Story 4.5 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 4 → Story 4.5
- Previous story (4.4) dev notes: `_bmad-output/implementation-artifacts/4-4-complete-a-session.md`
- Architecture User Isolation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → User Data Isolation
- Architecture Blueprint Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Blueprint Internal Structure
- Architecture CSS/BEM: `_bmad-output/planning-artifacts/architecture.md` → Frontend Architecture → CSS Organization
- Architecture Test Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Test Structure
- Architecture Date/Time: `_bmad-output/planning-artifacts/architecture.md` → Format Patterns → Date/Time Handling
- `WorkoutSession` model: `gymtrack/app/models/workout_session.py`
- `WorkoutSet` model: `gymtrack/app/models/workout_set.py`
- Existing workout routes: `gymtrack/app/blueprints/workouts/routes.py`
- Existing session_list template: `gymtrack/app/templates/workouts/session_list.html`
- Existing tests + helpers: `gymtrack/tests/test_workouts.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List
