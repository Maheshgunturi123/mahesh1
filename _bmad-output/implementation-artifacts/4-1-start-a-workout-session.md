# Story 4.1: Start a Workout Session

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to start a workout session from a plan or ad-hoc,
so that I can begin logging my sets immediately.

## Acceptance Criteria

1. **Given** I am on a plan detail page (`/workouts/plans/<id>/`) and click "Start Session"
   **When** the POST request is processed
   **Then** a `workout_sessions` row is created with `user_id=current_user.id`, `plan_id=<id>`, `started_at` (UTC), `is_complete=False`
   **And** I am redirected to the session log page `/workouts/sessions/<id>/log`
   **And** the session log page pre-populates exercises from the plan in `order_index` order

2. **Given** I navigate to `/workouts/sessions/new` (ad-hoc session)
   **When** I click "Start Ad-hoc Session" without selecting a plan
   **Then** a `workout_sessions` row is created with `plan_id=NULL`, `user_id=current_user.id`, `started_at` (UTC), `is_complete=False`
   **And** I am redirected to the session log page `/workouts/sessions/<id>/log`
   **And** the session log page shows an empty exercise list with an "Add Exercise" prompt

3. **Given** I already have an incomplete session (`is_complete=False`) in `workout_sessions`
   **When** I try to start a new session (either plan-based or ad-hoc)
   **Then** I see an `info` flash: "You have an unfinished session. Resume it or discard it first."
   **And** I am NOT redirected to a new session — no new row is created
   **And** I remain on the current page (or am redirected to the existing session log)

## Tasks / Subtasks

- [x] Task 1: Create `WorkoutSession` SQLAlchemy model (AC: 1, 2)
  - [x] CREATE `gymtrack/app/models/workout_session.py`
  - [x] Define `WorkoutSession(db.Model)` with `__tablename__ = 'workout_sessions'`:
    - `id`: `db.Column(db.Integer, primary_key=True)`
    - `user_id`: `db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)`
    - `plan_id`: `db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=True)` — NULL for ad-hoc
    - `started_at`: `db.Column(db.DateTime, default=datetime.utcnow, nullable=False)`
    - `is_complete`: `db.Column(db.Boolean, default=False, nullable=False)`
  - [x] Import `datetime` from `datetime` and `db` from `app.extensions`
  - [x] Add `__repr__` returning `f'<WorkoutSession {self.id} user={self.user_id} complete={self.is_complete}>'`

- [x] Task 2: Register `WorkoutSession` model in `app/models/__init__.py` (AC: 1, 2)
  - [x] UPDATE `gymtrack/app/models/__init__.py` — ADD import line after `PlanExercise`:
    ```python
    from app.models.workout_session import WorkoutSession  # noqa: F401
    ```
  - [x] Do NOT remove any existing imports (`User`, `Exercise`, `WorkoutPlan`, `PlanExercise`)

- [x] Task 3: Generate and apply Flask-Migrate migration (AC: 1, 2)
  - [x] Run `flask db migrate -m "add workout_sessions table"` to generate migration
  - [x] Verify the generated migration creates `workout_sessions` with all columns and correct FK constraints
  - [x] Run `flask db upgrade` to apply the migration

- [x] Task 4: Add `StartSessionForm` to `forms.py` (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/blueprints/workouts/forms.py` — ADD to existing file
  - [x] Add import for `SubmitField` if not already present (check existing imports first)
  - [x] Define `StartSessionForm(FlaskForm)` — no data fields, CSRF-only:
    ```python
    class StartSessionForm(FlaskForm):
        submit = SubmitField('Start Session')
    ```
  - [x] Do NOT modify or remove existing form classes (`WorkoutPlanForm`, `AddExerciseForm`, `EditExerciseForm`, `RemoveExerciseForm`, `MoveExerciseForm`)

- [x] Task 5: Add session routes to `routes.py` (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [x] Add imports:
    - Add `StartSessionForm` to the existing forms import line
    - Add `WorkoutSession` to models imports: `from app.models.workout_session import WorkoutSession`
  - [x] Add `_get_incomplete_session(user_id)` helper at module level (before routes):
    ```python
    def _get_incomplete_session(user_id):
        return WorkoutSession.query.filter_by(
            user_id=user_id, is_complete=False
        ).first()
    ```
  - [x] Add `start_session` route (plan-based)
  - [x] Add `session_new` route (ad-hoc)
  - [x] Add `session_log` route
  - [x] Variable name `workout_session` used for WorkoutSession instance (no Flask session shadowing)

- [x] Task 6: Update `plan_detail.html` to add "Start Session" button (AC: 1, 3)
  - [x] UPDATE `gymtrack/app/templates/workouts/plan_detail.html`
  - [x] Pass `start_form = StartSessionForm()` from `plan_detail` view to template
  - [x] Add Start Session form ABOVE the "Edit Plan" link in `workout-plan-detail__actions` section
  - [x] Preserve all existing template content

- [x] Task 7: Create `session_new.html` template for ad-hoc session (AC: 2)
  - [x] CREATE `gymtrack/app/templates/workouts/session_new.html`
  - [x] Extend `base.html`
  - [x] Show page title "Start Ad-hoc Session"
  - [x] Show `StartSessionForm` with hidden CSRF tag and submit button
  - [x] Include a back link
  - [x] BEM class names applied

- [x] Task 8: Create `session_log.html` template (AC: 1, 2)
  - [x] CREATE `gymtrack/app/templates/workouts/session_log.html`
  - [x] Extend `base.html`
  - [x] Show page title with started_at formatted
  - [x] Show plan exercises if plan-based session
  - [x] Show empty message if ad-hoc session
  - [x] Show session status
  - [x] BEM class names applied
  - [x] No set-logging form (Story 4.2 scope)

- [x] Task 9: Add tests to `tests/test_workouts.py` (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/tests/test_workouts.py` — ADD test functions; do NOT remove existing tests
  - [x] Import `WorkoutSession` from `app.models.workout_session`
  - [x] `test_start_plan_session_creates_row`: POST, assert 302, assert WorkoutSession row
  - [x] `test_start_adhoc_session_creates_row`: POST, assert WorkoutSession row with `plan_id=None`
  - [x] `test_session_log_loads`: GET, assert 200, assert plan exercises shown
  - [x] `test_incomplete_session_guard_plan`: no new row, flash message contains "unfinished"
  - [x] `test_incomplete_session_guard_adhoc`: redirect to existing session log
  - [x] `test_session_isolation`: GET another user's session → 404

## Dev Notes

### WorkoutSession Model
- `__tablename__ = 'workout_sessions'` — follows plural snake_case convention
- `plan_id` is **nullable** (FK to `workout_plans.id`) — NULL for ad-hoc sessions
- `started_at` uses `datetime.utcnow` (no timezone info in column, per architecture)
- `is_complete` Boolean — prefix `is_` per architecture boolean naming convention
- Multi-user isolation: ALL queries MUST include `user_id=current_user.id` filter — NEVER query by session `id` alone

### Variable Naming Caution
- Flask imports `session` from `flask` for cookie-based auth sessions. The `WorkoutSession` SQLAlchemy instance must NOT be named `session` if `from flask import session` is ever in scope.
- Current `routes.py` does NOT import Flask's `session` — safe to use `session` as local variable. Verify before committing.

### Incomplete Session Guard — Single Active Session Rule
- A user may only have ONE incomplete `WorkoutSession` at a time
- The guard checks `WorkoutSession.query.filter_by(user_id=current_user.id, is_complete=False).first()`
- If found: flash `info` message and abort session creation — do NOT create a second row
- Flash category MUST be `'info'` (not `'warning'` or `'error'`) per architecture flash categories

### Route Structure
- Plan-based start: `POST /workouts/plans/<int:id>/start-session` → blueprint prefix `/workouts` → full URL `/workouts/plans/<id>/start-session`
- Ad-hoc start: `GET/POST /workouts/sessions/new` → full URL `/workouts/sessions/new`
- Session log: `GET /workouts/sessions/<int:id>/log` → full URL `/workouts/sessions/<id>/log`
- These are all under the `workouts_bp` blueprint (registered at `/workouts/`)

### Session Log Page Scope (Story 4.1 Only)
- `session_log.html` is a SCAFFOLD — it shows the plan exercises as a reference list but does NOT include set-logging forms or AJAX interactions
- Set logging (weight, reps input + auto-save) is Story 4.2 scope
- Do NOT pre-emptively build the set logger — it will break the clean story boundary

### Migration
- This story introduces the first migration in the workout logging domain
- File: `migrations/versions/<hash>_add_workout_sessions_table.py`
- Must create `workout_sessions` with all columns and FK constraints to `users` and `workout_plans`
- Run `flask db upgrade` after generating — verify with `flask shell`: `from app.models.workout_session import WorkoutSession; WorkoutSession.query.all()`

### plan_detail Route Update
- The existing `plan_detail` view in `routes.py` must be updated to instantiate and pass `start_form`:
  ```python
  from app.blueprints.workouts.forms import ..., StartSessionForm
  
  @workouts_bp.route('/plans/<int:id>/')
  @login_required
  def plan_detail(id):
      ...
      start_form = StartSessionForm()
      return render_template('workouts/plan_detail.html', ..., start_form=start_form)
  ```

### Project Structure Notes
- New model file: `gymtrack/app/models/workout_session.py`
- Updated model registry: `gymtrack/app/models/__init__.py`
- New migration: `gymtrack/migrations/versions/<hash>_add_workout_sessions_table.py`
- Updated forms: `gymtrack/app/blueprints/workouts/forms.py` (add `StartSessionForm`)
- Updated routes: `gymtrack/app/blueprints/workouts/routes.py` (add 3 routes + helper, update `plan_detail`)
- Updated template: `gymtrack/app/templates/workouts/plan_detail.html` (add Start Session form)
- New templates: `gymtrack/app/templates/workouts/session_log.html`, `session_new.html`
- Updated tests: `gymtrack/tests/test_workouts.py`

### References
- Architecture DB Naming: `architecture.md` → Naming Patterns → Database Naming Conventions
- Architecture URL Conventions: `architecture.md` → Naming Patterns → URL Conventions (`/workouts/sessions/<int:id>/log/`)
- Architecture Blueprint Structure: `architecture.md` → Structure Patterns → Blueprint Internal Structure
- Architecture Multi-User Isolation: `architecture.md` → Process Patterns → User Data Isolation
- Architecture Flash Categories: `architecture.md` → Format Patterns → Flash Messages (`success`, `error`, `info`, `warning`)
- Architecture DateTime: `architecture.md` → Format Patterns → Date/Time Handling (UTC, `datetime.utcnow`)
- Existing WorkoutPlan model: `gymtrack/app/models/workout_plan.py`
- Existing PlanExercise model: `gymtrack/app/models/plan_exercise.py`
- Existing workouts routes: `gymtrack/app/blueprints/workouts/routes.py`
- Existing plan_detail template: `gymtrack/app/templates/workouts/plan_detail.html`
- Epic 4 Story 4.1 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 4 → Story 4.1
- Story 3.3 (most recent prior story, same blueprint): `_bmad-output/implementation-artifacts/3-3-edit-and-reorder-plan-exercises.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- All 9 tasks complete. 6 new Story 4.1 tests added; full suite 85/85 passed (zero regressions).
- `WorkoutSession` model created with nullable `plan_id` for ad-hoc support.
- `_get_incomplete_session` helper enforces single-active-session rule (AC 3).
- Local variable named `workout_session` (not `session`) to avoid Flask session shadowing.
- Migration `6cc83401f0b1_add_workout_sessions_table.py` generated and applied.
- `session_log.html` is a scaffold — no set-logging form (Story 4.2 scope).

### File List

- gymtrack/app/models/workout_session.py (created)
- gymtrack/app/models/__init__.py (modified)
- gymtrack/migrations/versions/6cc83401f0b1_add_workout_sessions_table.py (created)
- gymtrack/app/blueprints/workouts/forms.py (modified)
- gymtrack/app/blueprints/workouts/routes.py (modified)
- gymtrack/app/templates/workouts/plan_detail.html (modified)
- gymtrack/app/templates/workouts/session_new.html (created)
- gymtrack/app/templates/workouts/session_log.html (created)
- gymtrack/tests/test_workouts.py (modified)
