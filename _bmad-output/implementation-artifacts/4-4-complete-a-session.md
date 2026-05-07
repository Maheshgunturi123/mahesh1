# Story 4.4: Complete a Session

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to mark my workout session as complete,
so that it is recorded in my history and triggers PR detection.

## Acceptance Criteria

1. **Given** I am on an active session log page
   **When** I click "Complete Workout"
   **Then** `workout_sessions.is_complete` is set to `True` and `completed_at` (UTC) is recorded
   **And** I am redirected to `/workouts/sessions/<id>/complete` (post-workout summary)
   **And** the summary shows all exercises and sets logged in this session

2. **Given** the session has zero sets logged
   **When** I try to complete it
   **Then** I see a `warning` flash: "Log at least one set before completing."
   **And** the session remains open (redirected back to session log)

## Tasks / Subtasks

- [ ] Task 1: Add `completed_at` column to `WorkoutSession` model (AC: 1)
  - [ ] UPDATE `gymtrack/app/models/workout_session.py`
  - [ ] Add: `completed_at = db.Column(db.DateTime, nullable=True)` after `is_complete` column
  - [ ] Do NOT set a default value — it stays `None` until the session is explicitly completed
  - [ ] Result model:
    ```python
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    ```

- [ ] Task 2: Create Alembic migration for `completed_at` column (AC: 1)
  - [ ] CREATE new migration file in `gymtrack/migrations/versions/`
  - [ ] Migration adds `completed_at` column to `workout_sessions` table:
    ```python
    def upgrade():
        op.add_column('workout_sessions',
            sa.Column('completed_at', sa.DateTime(), nullable=True)
        )

    def downgrade():
        op.drop_column('workout_sessions', 'completed_at')
    ```
  - [ ] Set `down_revision` to `'a6c7a4f16c9d'` (the `add_workout_sets_table` migration, which is the most recent)
  - [ ] Use a descriptive message: `add_completed_at_to_workout_sessions`

- [ ] Task 3: Add `CompleteSessionForm` to `forms.py` (AC: 1)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/forms.py`
  - [ ] ADD at the end:
    ```python
    class CompleteSessionForm(FlaskForm):
        pass  # no fields; validate_on_submit() checks CSRF only
    ```

- [ ] Task 4: Implement `POST /workouts/sessions/<id>/complete` route (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Add import for `CompleteSessionForm` in the imports block
  - [ ] Add the route AFTER the existing `session_log` route:
    ```python
    @workouts_bp.route('/sessions/<int:id>/complete', methods=['POST'])
    @login_required
    def session_complete_post(id):
        workout_session = WorkoutSession.query.filter_by(
            id=id, user_id=current_user.id
        ).first_or_404()
        form = CompleteSessionForm()
        if form.validate_on_submit():
            set_count = WorkoutSet.query.filter_by(session_id=workout_session.id).count()
            if set_count == 0:
                flash('Log at least one set before completing.', 'warning')
                return redirect(url_for('workouts.session_log', id=workout_session.id))
            workout_session.is_complete = True
            workout_session.completed_at = datetime.utcnow()
            db.session.commit()
            logger.info('Workout session completed: user=%d session_id=%d',
                        current_user.id, workout_session.id)
            return redirect(url_for('workouts.session_complete', id=workout_session.id))
        return redirect(url_for('workouts.session_log', id=workout_session.id))
    ```

- [ ] Task 5: Implement `GET /workouts/sessions/<id>/complete` route — post-workout summary (AC: 1)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Add the route AFTER `session_complete_post`:
    ```python
    @workouts_bp.route('/sessions/<int:id>/complete', methods=['GET'])
    @login_required
    def session_complete(id):
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
            plan = WorkoutPlan.query.get(workout_session.plan_id)
            plan_name = plan.name if plan else None
        return render_template(
            'workouts/session_complete.html',
            session=workout_session,
            sets_by_exercise=sets_by_exercise,
            exercise_map=exercise_map,
            plan_name=plan_name,
        )
    ```
  - [ ] Note: `is_complete=True` in the filter ensures only completed sessions are accessible at this URL (incomplete sessions return 404)

- [ ] Task 6: Add "Complete Workout" button to `session_log.html` (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/templates/workouts/session_log.html`
  - [ ] Add import of `CompleteSessionForm` in the route that renders this template — already handled via Task 4/5
  - [ ] In the `session_log` route (existing), instantiate and pass `complete_form`:
    - UPDATE `gymtrack/app/blueprints/workouts/routes.py` — in `session_log` view, add:
      ```python
      complete_form = CompleteSessionForm()
      ```
      and pass `complete_form=complete_form` to `render_template`
  - [ ] In `session_log.html`, add "Complete Workout" section AFTER `</section>` (closing sessions exercises) and BEFORE `</div>` (closing session-log div):
    ```html
    {% if not session.is_complete %}
    <div class="session-log__actions">
      <form method="POST"
            action="{{ url_for('workouts.session_complete_post', id=session.id) }}">
        {{ complete_form.hidden_tag() }}
        <button class="session-log__complete-btn btn btn--success" type="submit">
          Complete Workout
        </button>
      </form>
    </div>
    {% endif %}
    ```

- [ ] Task 7: Create `session_complete.html` template (AC: 1)
  - [ ] CREATE `gymtrack/app/templates/workouts/session_complete.html`
  - [ ] Extend `base.html`, use BEM class names
  - [ ] Show heading "Workout Complete! 🎉"
  - [ ] Show session metadata: date (`started_at`), plan name (or "Ad-hoc")
  - [ ] For each exercise in `sets_by_exercise`, render a group with exercise name and each set (weight × reps)
  - [ ] Link back to `/workouts/sessions/` ("View All Sessions")
  - [ ] WCAG: All content readable without color dependency
  - [ ] Template structure:
    ```html
    {% extends 'base.html' %}
    {% block title %}Workout Complete — GymTrack{% endblock %}
    {% block content %}
    <div class="session-complete">
      <h1 class="session-complete__heading">Workout Complete! 🎉</h1>
      <div class="session-complete__meta">
        <span class="session-complete__date">{{ session.started_at | strftime('%b %d, %Y at %H:%M') }}</span>
        <span class="session-complete__plan">{{ plan_name if plan_name else 'Ad-hoc' }}</span>
      </div>
      <section class="session-complete__summary">
        <h2 class="session-complete__summary-heading">Sets Logged</h2>
        {% for exercise_id, sets in sets_by_exercise.items() %}
        <div class="session-complete__exercise-group">
          <h3 class="session-complete__exercise-name">{{ exercise_map[exercise_id].name }}</h3>
          <ul class="session-complete__set-list">
            {% for ws in sets %}
            <li class="session-complete__set-item">
              Set {{ ws.set_number }}: {{ ws.weight_kg }}kg &times; {{ ws.reps }} reps
            </li>
            {% endfor %}
          </ul>
        </div>
        {% endfor %}
      </section>
      <a class="session-complete__back-link btn btn--secondary"
         href="{{ url_for('workouts.session_list') }}">View All Sessions</a>
    </div>
    {% endblock %}
    ```

- [ ] Task 8: Add tests for session completion (AC: 1, 2)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py`
  - [ ] Add section header comment: `# Story 4.4 — Complete a Session`
  - [ ] Add helper `make_workout_set(db, session_id, exercise_id, set_number=1, weight_kg=60.0, reps=10)`:
    ```python
    def make_workout_set(db, session_id, exercise_id, set_number=1, weight_kg=60.0, reps=10):
        from datetime import datetime
        ws = WorkoutSet(
            session_id=session_id,
            exercise_id=exercise_id,
            set_number=set_number,
            weight_kg=weight_kg,
            reps=reps,
        )
        db.session.add(ws)
        db.session.commit()
        return ws
    ```
  - [ ] `test_complete_session_unauthenticated`: POST `/workouts/sessions/1/complete` without login → 302 to login
  - [ ] `test_complete_session_sets_is_complete_and_redirects`: create session + 1 set, POST → 302, `is_complete=True`, `completed_at` is not None, redirect location contains `/complete`
  - [ ] `test_complete_session_zero_sets_flashes_warning`: create session with no sets, POST → 302 redirect back to session log, `is_complete` remains `False`, flash contains "Log at least one set"
  - [ ] `test_complete_session_isolation`: create session for user B, login as user A, POST → 404
  - [ ] `test_session_complete_summary_renders`: complete a session with 1 exercise + 1 set, GET `/workouts/sessions/<id>/complete` → 200, response contains exercise name, "Workout Complete"
  - [ ] `test_session_complete_incomplete_session_returns_404`: GET `/workouts/sessions/<id>/complete` for an incomplete session → 404
  - [ ] Example test for AC 1:
    ```python
    def test_complete_session_sets_is_complete_and_redirects(client, app):
        with app.app_context():
            _db.create_all()
            user = make_user(_db)
            exercise = make_exercise(_db, name='Squat')
            session = make_session(_db, user.id, is_complete=False)
            make_workout_set(_db, session.id, exercise.id)
            login_as(client, 'user@example.com', 'password123')
            response = client.post(
                f'/workouts/sessions/{session.id}/complete',
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert f'/workouts/sessions/{session.id}/complete' in response.headers['Location']
            updated = WorkoutSession.query.get(session.id)
            assert updated.is_complete is True
            assert updated.completed_at is not None
    ```

## Dev Notes

### Model Change Required — `completed_at` Column

`WorkoutSession` currently has no `completed_at` column (only `started_at` and `is_complete`). This story adds it. Both the model AND a new Alembic migration are required. The column is nullable — existing rows remain valid with `completed_at=None`.

```python
# gymtrack/app/models/workout_session.py — final shape
class WorkoutSession(db.Model):
    __tablename__ = 'workout_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
```

### Route Naming — Two Methods on Same URL

Use separate view functions to avoid method ambiguity and keep each function clean:
- `session_complete_post` handles `POST /workouts/sessions/<id>/complete`
- `session_complete` handles `GET /workouts/sessions/<id>/complete`

Do NOT use `methods=['GET', 'POST']` on a single function — the business logic differs too much between the two.

### User Data Isolation (MANDATORY)

```python
# POST route — must filter by user_id
WorkoutSession.query.filter_by(id=id, user_id=current_user.id).first_or_404()

# GET summary route — must filter by user_id AND is_complete=True
WorkoutSession.query.filter_by(id=id, user_id=current_user.id, is_complete=True).first_or_404()
```

The `is_complete=True` filter on the GET route means an incomplete session accessed at `/complete` returns 404 — this is correct behaviour and also tested.

### CSRF on Complete Workout Button

The "Complete Workout" button submits a form (not a link). Use `CompleteSessionForm` (CSRF-only form, same pattern as `RemoveExerciseForm`). The `session_log` route must instantiate and pass `complete_form` to the template.

```python
# In session_log route — add before render_template call:
complete_form = CompleteSessionForm()
# pass complete_form=complete_form to render_template
```

In the template, use `{{ complete_form.hidden_tag() }}` inside the form tag.

### Variable Naming Conventions (Inherited from 4.1–4.3)

- Use `workout_session` (not `session`) for SQLAlchemy `WorkoutSession` objects — avoids collision with Flask's `session` cookie proxy
- Pass as `session=workout_session` to templates (templates already use `session.id`, `session.is_complete`, etc.)

### Flash Category — Warning for Zero Sets

Per architecture conventions, use only these flash categories: `success`, `error`, `info`, `warning`.
The zero-sets guard uses `warning` exactly as specified in the AC:
```python
flash('Log at least one set before completing.', 'warning')
```

### PR Detection — Not Implemented in This Story

The epic summary mentions that completing a session "triggers PR detection." This is implemented in Epic 5 (Story 5.1: PR Detection Service). In this story, do NOT call any PR detection function. Story 5.1 will add the `detect_prs` call to `session_complete_post` once the service exists.

### Session History (Story 4.5) Dependency

Story 4.5 (`session_list` shows completed sessions with exercise count + total sets) will reuse the `session_list` route and `session_list.html` template. This story must NOT modify the `session_list` route or template — that is 4.5's scope.

### What Is Already Implemented (DO NOT Re-implement)

- `GET /workouts/sessions/` (`session_list` route) — added in Story 4.3
- `session_list.html` — shows "Resume" link for incomplete sessions — added in Story 4.3
- `session_log.html` — renders plan-based and ad-hoc sets — Story 4.3 added prior-sets display for ad-hoc sessions
- `GET /workouts/sessions/<id>/log` — fully implemented, passes `sets_by_exercise`, `all_exercises`, `logged_sets`
- `WorkoutSet` model — `session_id`, `exercise_id`, `set_number`, `weight_kg`, `reps`, `logged_at`
- `make_session` helper in `test_workouts.py` — reuse it, do not redefine

### Architecture Compliance

- Routes in `gymtrack/app/blueprints/workouts/routes.py` ✅
- New form class in `gymtrack/app/blueprints/workouts/forms.py` ✅
- Templates in `gymtrack/app/templates/workouts/` ✅
- BEM CSS class names in new template ✅
- User isolation enforced via `filter_by(user_id=current_user.id)` ✅
- Flash messages use only: `success`, `error`, `info`, `warning` ✅
- Tests in `gymtrack/tests/test_workouts.py` ✅
- SQLAlchemy variable named `workout_session` (not `session`) ✅

### Project Structure Notes

- Files to UPDATE:
  - `gymtrack/app/models/workout_session.py` — add `completed_at` column
  - `gymtrack/app/blueprints/workouts/forms.py` — add `CompleteSessionForm`
  - `gymtrack/app/blueprints/workouts/routes.py` — add 2 new routes + update `session_log` to pass `complete_form`
  - `gymtrack/app/templates/workouts/session_log.html` — add "Complete Workout" form button
  - `gymtrack/tests/test_workouts.py` — add Story 4.4 tests
- Files to CREATE:
  - `gymtrack/migrations/versions/<hash>_add_completed_at_to_workout_sessions.py`
  - `gymtrack/app/templates/workouts/session_complete.html`
- No new JavaScript required
- No new models required (only column addition to existing model)

### References

- Story 4.4 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 4 → Story 4.4
- Architecture User Isolation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → User Data Isolation
- Architecture Flash Messages: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → HTML Page Routes — Flash Messages
- Architecture Blueprint Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Blueprint Internal Structure
- Architecture CSS/BEM: `_bmad-output/planning-artifacts/architecture.md` → Frontend Architecture → CSS Organization
- Architecture Test Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Test Structure
- Previous story (4.3) dev notes: `_bmad-output/implementation-artifacts/4-3-resume-an-interrupted-session.md`
- WorkoutSession model: `gymtrack/app/models/workout_session.py`
- WorkoutSet model: `gymtrack/app/models/workout_set.py`
- Existing workout routes: `gymtrack/app/blueprints/workouts/routes.py`
- Existing forms: `gymtrack/app/blueprints/workouts/forms.py`
- Existing session_log template: `gymtrack/app/templates/workouts/session_log.html`
- Existing tests + helpers: `gymtrack/tests/test_workouts.py`
- Latest migration (parent): `gymtrack/migrations/versions/a6c7a4f16c9d_add_workout_sets_table.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

None.

### Completion Notes List

All 8 tasks completed. 43 tests pass (6 new Story 4.4 tests green).

### File List

- UPDATED: gymtrack/app/models/workout_session.py
- UPDATED: gymtrack/app/blueprints/workouts/forms.py
- UPDATED: gymtrack/app/blueprints/workouts/routes.py
- UPDATED: gymtrack/app/templates/workouts/session_log.html
- UPDATED: gymtrack/tests/test_workouts.py
- CREATED: gymtrack/migrations/versions/b3e5f2a9c1d8_add_completed_at_to_workout_sessions.py
- CREATED: gymtrack/app/templates/workouts/session_complete.html
