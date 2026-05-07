# Story 4.3: Resume an Interrupted Session

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to resume a partially completed session after an interruption,
so that I don't lose previously logged sets.

## Acceptance Criteria

1. **Given** I have an incomplete session (`is_complete=False`)
   **When** I navigate to `/workouts/sessions/<id>/log`
   **Then** all previously saved sets are displayed, grouped by exercise
   **And** I can continue adding new sets from where I left off

2. **Given** I close the browser mid-session and reopen GymTrack
   **When** I visit `/workouts/sessions/`
   **Then** I see the incomplete session at the top with a "Resume" link

3. **Given** another user tries to access my session URL
   **When** the request is made
   **Then** they receive a 404 (`.filter_by(id=session_id, user_id=current_user.id).first_or_404()`)

## Tasks / Subtasks

- [ ] Task 1: Update `session_log.html` to display previously logged sets for ad-hoc sessions (AC: 1)
  - [ ] UPDATE `gymtrack/app/templates/workouts/session_log.html`
  - [ ] In the `{% else %}` (ad-hoc) branch, add a section that iterates over exercises that already have logged sets (`sets_by_exercise`), displaying all logged sets before the add-new-set form:
    ```html
    {% if sets_by_exercise %}
    <div class="session-log__prior-sets">
      <h3 class="session-log__prior-heading">Previously Logged Sets</h3>
      {% for exercise_id, sets in sets_by_exercise.items() %}
      {% set ex = all_exercises | selectattr('id', 'equalto', exercise_id) | first %}
      <div class="session-log__exercise-group">
        <h4 class="session-log__exercise-name">{{ ex.name if ex else 'Unknown Exercise' }}</h4>
        <ul class="set-logger__set-list">
          {% for ws in sets %}
          <li class="set-logger__set-item">Set {{ ws.set_number }}: {{ ws.weight_kg }}kg &times; {{ ws.reps }} reps</li>
          {% endfor %}
        </ul>
      </div>
      {% endfor %}
    </div>
    {% endif %}
    ```
  - [ ] Place this block immediately before the ad-hoc set-logger form div
  - [ ] Do NOT modify the plan-based `{% if plan_exercises %}` branch (already displays sets correctly)
  - [ ] Do NOT modify the set-logger form itself

- [ ] Task 2: Create `GET /workouts/sessions/` route — session list view (AC: 2)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Add import for `WorkoutPlan` (already present) — verify it is imported
  - [ ] ADD route before the existing `session_new` route:
    ```python
    @workouts_bp.route('/sessions/')
    @login_required
    def session_list():
        all_sessions = WorkoutSession.query.filter_by(
            user_id=current_user.id
        ).order_by(WorkoutSession.is_complete.asc(), WorkoutSession.started_at.desc()).all()
        plan_ids = {s.plan_id for s in all_sessions if s.plan_id}
        plans = WorkoutPlan.query.filter(WorkoutPlan.id.in_(plan_ids)).all() if plan_ids else []
        plan_map = {p.id: p for p in plans}
        return render_template(
            'workouts/session_list.html',
            sessions=all_sessions,
            plan_map=plan_map,
        )
    ```
  - [ ] Ordering: `is_complete ASC` puts `False` (0) before `True` (1) → incomplete sessions appear first
  - [ ] Do NOT modify any other routes

- [ ] Task 3: Create `session_list.html` template (AC: 2)
  - [ ] CREATE `gymtrack/app/templates/workouts/session_list.html`
  - [ ] Extend `base.html`, use BEM class names
  - [ ] Show page heading "My Workout Sessions"
  - [ ] If `sessions` is empty, show: "No sessions yet. Start your first workout!"
  - [ ] For each session, render a card with:
    - Date: `{{ s.started_at | strftime('%b %d, %Y at %H:%M') }}`
    - Plan: `{{ plan_map[s.plan_id].name if s.plan_id in plan_map else 'Ad-hoc' }}`
    - Status badge: "In Progress" (if `not s.is_complete`) or "Complete" (if `s.is_complete`)
    - **"Resume" link** for incomplete sessions: `href="{{ url_for('workouts.session_log', id=s.id) }}"`
  - [ ] Incomplete sessions appear first (ensured by route ordering — no extra template logic needed)
  - [ ] WCAG: All interactive elements keyboard accessible; status communicated via text (not color alone)
  - [ ] Example template structure:
    ```html
    {% extends 'base.html' %}
    {% block title %}My Sessions — GymTrack{% endblock %}
    {% block content %}
    <div class="session-list">
      <h1 class="session-list__heading">My Workout Sessions</h1>
      {% if sessions %}
        {% for s in sessions %}
        <div class="session-list__item{% if not s.is_complete %} session-list__item--active{% endif %}">
          <div class="session-list__meta">
            <span class="session-list__date">{{ s.started_at | strftime('%b %d, %Y at %H:%M') }}</span>
            <span class="session-list__plan">{{ plan_map[s.plan_id].name if s.plan_id in plan_map else 'Ad-hoc' }}</span>
            <span class="session-list__status">{% if s.is_complete %}Complete{% else %}In Progress{% endif %}</span>
          </div>
          {% if not s.is_complete %}
          <a class="session-list__resume-link btn btn--primary"
             href="{{ url_for('workouts.session_log', id=s.id) }}">Resume</a>
          {% endif %}
        </div>
        {% endfor %}
      {% else %}
        <p class="session-list__empty">No sessions yet. Start your first workout!</p>
      {% endif %}
    </div>
    {% endblock %}
    ```

- [ ] Task 4: Add tests for session list and resume behaviour (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py`
  - [ ] Add helper `make_session(db, user_id, plan_id=None, is_complete=False)`:
    ```python
    def make_session(db, user_id, plan_id=None, is_complete=False):
        from datetime import datetime
        from app.models.workout_session import WorkoutSession
        s = WorkoutSession(user_id=user_id, plan_id=plan_id,
                           started_at=datetime.utcnow(), is_complete=is_complete)
        db.session.add(s)
        db.session.commit()
        return s
    ```
  - [ ] `test_session_list_unauthenticated`: `GET /workouts/sessions/` without login → 302 redirect to login
  - [ ] `test_session_list_empty`: authenticated user with no sessions → 200, contains "No sessions yet"
  - [ ] `test_session_list_shows_incomplete_first`: create one complete and one incomplete session → response HTML contains "Resume" → incomplete entry appears before complete entry (check HTML order)
  - [ ] `test_session_list_shows_resume_link`: create incomplete session → 200, response contains "Resume" and `url_for('workouts.session_log', id=session.id)` path
  - [ ] `test_session_list_no_resume_for_complete`: create only complete session → 200, response does NOT contain "Resume"
  - [ ] `test_session_log_shows_prior_sets_adhoc`: create ad-hoc session, add a `WorkoutSet` row directly to db, GET `/workouts/sessions/<id>/log` → 200, response contains `Set 1` (previously logged set visible)
  - [ ] `test_session_log_404_other_user`: create session for user A, login as user B, GET session A's log URL → 404
  - [ ] Import `WorkoutSession` and `WorkoutSet` at top of test additions

## Dev Notes

### What's Already Implemented (DO NOT re-implement)

- `GET /workouts/sessions/<id>/log` (`session_log` route) already:
  - Queries all `WorkoutSet` rows for the session: `WorkoutSet.query.filter_by(session_id=...).order_by(...)` 
  - Builds `sets_by_exercise` dict keyed by `exercise_id`
  - Passes `logged_sets`, `sets_by_exercise`, `all_exercises` to template
  - Enforces user isolation via `.filter_by(id=id, user_id=current_user.id).first_or_404()` — **AC 3 is already satisfied**
- For plan-based sessions, `session_log.html` already renders all previously logged sets per exercise using `sets_by_exercise.get(pe.exercise_id, [])` — **AC 1 is already satisfied for plan-based sessions**
- **Only ad-hoc sessions are missing the prior-sets display** — this is Task 1

### User Data Isolation (MANDATORY)

```python
# session_list route MUST filter by user_id
WorkoutSession.query.filter_by(user_id=current_user.id)...

# session_log already does this — do NOT weaken it
WorkoutSession.query.filter_by(id=id, user_id=current_user.id).first_or_404()
```

### Ordering for Session List (AC 2)

SQLAlchemy ascending sort on boolean: `is_complete ASC` sorts `False` (0) before `True` (1), putting incomplete sessions first without any template-level sorting logic.

```python
WorkoutSession.query.filter_by(user_id=current_user.id).order_by(
    WorkoutSession.is_complete.asc(),
    WorkoutSession.started_at.desc()
).all()
```

### Plan Name Lookup (No ORM Relationship)

`WorkoutSession` has no lazy-loaded `plan` relationship. Build a `plan_map` dict in the route:

```python
plan_ids = {s.plan_id for s in all_sessions if s.plan_id}
plans = WorkoutPlan.query.filter(WorkoutPlan.id.in_(plan_ids)).all() if plan_ids else []
plan_map = {p.id: p for p in plans}
```

In the template, use: `plan_map[s.plan_id].name if s.plan_id in plan_map else 'Ad-hoc'`

### Variable Naming (Inherited from 4.1 / 4.2)

- Use `workout_session` (not `session`) for `WorkoutSession` SQLAlchemy objects to avoid collision with Flask's `session` cookie proxy
- In `session_list` route, use `all_sessions` (not `sessions_list`) as the local variable, pass as `sessions` to the template

### Ad-hoc Session Sets Display (Task 1)

For ad-hoc sessions, `plan_exercises` is empty so the template goes to the `{% else %}` branch. The route already builds `sets_by_exercise` for all sessions (plan-based or not), so the data is available — only the template display is missing.

Use Jinja2 `selectattr` filter to resolve exercise names from `all_exercises`:
```html
{% set ex = all_exercises | selectattr('id', 'equalto', exercise_id) | first %}
```

### Architecture Compliance

- Route defined in `routes.py` (never in `__init__.py`) ✅
- User isolation enforced via `filter_by(user_id=current_user.id)` ✅
- Flash messages use only: `success`, `error`, `info`, `warning` ✅
- BEM CSS class names in templates ✅
- New template at `app/templates/workouts/session_list.html` (matches `session_list` view function name) ✅
- Tests in `test_workouts.py` (mirrors blueprint structure) ✅

### Project Structure Notes

- Files to UPDATE:
  - `gymtrack/app/blueprints/workouts/routes.py` — add `session_list` route
  - `gymtrack/app/templates/workouts/session_log.html` — add prior-sets display for ad-hoc sessions
  - `gymtrack/tests/test_workouts.py` — add session list and resume tests
- Files to CREATE:
  - `gymtrack/app/templates/workouts/session_list.html`
- No new models, no migrations, no new JS required for this story

### References

- Architecture User Isolation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → User Data Isolation
- Architecture DB Naming: `_bmad-output/planning-artifacts/architecture.md` → Naming Patterns → Database Naming Conventions
- Architecture URL Conventions: `_bmad-output/planning-artifacts/architecture.md` → Naming Patterns → URL Conventions
- Architecture Blueprint Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Blueprint Internal Structure
- Architecture Test Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Test Structure
- Architecture CSS: `_bmad-output/planning-artifacts/architecture.md` → Frontend Architecture → CSS Organization
- Epic 4 Story 4.3 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 4 → Story 4.3
- Existing workout routes (state to preserve): `gymtrack/app/blueprints/workouts/routes.py`
- Existing session_log template (partial update): `gymtrack/app/templates/workouts/session_log.html`
- WorkoutSession model: `gymtrack/app/models/workout_session.py`
- WorkoutSet model: `gymtrack/app/models/workout_set.py`
- WorkoutPlan model: `gymtrack/app/models/workout_plan.py`
- Previous story (4.2) dev notes: `_bmad-output/implementation-artifacts/4-2-log-sets-with-auto-save.md`
- Test fixture patterns: `gymtrack/tests/test_workouts.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- AC 1: `session_log.html` updated — ad-hoc sessions now display previously logged sets via `sets_by_exercise` (data already passed by route).
- AC 2: `session_list` route added to `routes.py`; `session_list.html` template created — incomplete sessions appear first.
- AC 3: Already satisfied by existing `filter_by(id=id, user_id=current_user.id).first_or_404()` in `session_log` route.
- 7 new tests added to `test_workouts.py`; all 37 tests pass.

### File List

- `gymtrack/app/templates/workouts/session_log.html` — UPDATED
- `gymtrack/app/blueprints/workouts/routes.py` — UPDATED
- `gymtrack/app/templates/workouts/session_list.html` — CREATED
- `gymtrack/tests/test_workouts.py` — UPDATED
