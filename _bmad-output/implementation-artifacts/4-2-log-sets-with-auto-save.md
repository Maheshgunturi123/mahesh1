# Story 4.2: Log Sets with Auto-Save

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user at the gym,
I want to log each set (weight and reps) with immediate auto-save,
so that my data is never lost even if my session is interrupted.

## Acceptance Criteria

1. **Given** I am on the session log page and enter weight and reps for a set
   **When** I tap/click "Save Set"
   **Then** `set-logger.js` sends `POST /api/sessions/<id>/sets` with `{"exercise_id": N, "set_number": M, "weight_kg": X, "reps": Y}`
   **And** the server responds within 500ms with `{"status": "ok", "set_id": N, "pr_detected": false}`
   **And** a `workout_sets` row is persisted: `session_id`, `exercise_id`, `set_number`, `weight_kg`, `reps`, `logged_at` (UTC)
   **And** the UI confirms the save visually without a full page reload

2. **Given** the network request fails
   **When** the save is attempted
   **Then** the UI shows an inline error: "Set not saved — check your connection." and does not clear the input

3. **Given** I log multiple sets for the same exercise
   **When** each is saved
   **Then** `set_number` increments correctly (1, 2, 3…) for that exercise within the session (calculated server-side)

## Tasks / Subtasks

- [ ] Task 1: Create `WorkoutSet` SQLAlchemy model (AC: 1, 3)
  - [ ] CREATE `gymtrack/app/models/workout_set.py`
  - [ ] Define `WorkoutSet(db.Model)` with `__tablename__ = 'workout_sets'`:
    - `id`: `db.Column(db.Integer, primary_key=True)`
    - `session_id`: `db.Column(db.Integer, db.ForeignKey('workout_sessions.id'), nullable=False)`
    - `exercise_id`: `db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)`
    - `set_number`: `db.Column(db.Integer, nullable=False)`
    - `weight_kg`: `db.Column(db.Float, nullable=False)`
    - `reps`: `db.Column(db.Integer, nullable=False)`
    - `logged_at`: `db.Column(db.DateTime, default=datetime.utcnow, nullable=False)`
  - [ ] Import `datetime` from `datetime` and `db` from `app.extensions`
  - [ ] Add `__repr__` returning `f'<WorkoutSet {self.id} session={self.session_id} exercise={self.exercise_id} set={self.set_number}>'`

- [ ] Task 2: Register `WorkoutSet` model in `app/models/__init__.py` (AC: 1)
  - [ ] UPDATE `gymtrack/app/models/__init__.py` — ADD import line after `WorkoutSession`:
    ```python
    from app.models.workout_set import WorkoutSet  # noqa: F401
    ```
  - [ ] Do NOT remove any existing imports (`User`, `Exercise`, `WorkoutPlan`, `PlanExercise`, `WorkoutSession`)

- [ ] Task 3: Generate and apply Flask-Migrate migration (AC: 1)
  - [ ] Run `flask db migrate -m "add workout_sets table"` to generate migration
  - [ ] Verify the generated migration creates `workout_sets` with all columns and FK constraints to `workout_sessions` and `exercises`
  - [ ] Run `flask db upgrade` to apply the migration

- [ ] Task 4: Add CSRF meta tag to `base.html` (AC: 1)
  - [ ] UPDATE `gymtrack/app/templates/base.html` — ADD inside `<head>` block, after charset meta:
    ```html
    <meta name="csrf-token" content="{{ csrf_token() }}">
    ```
  - [ ] This enables `set-logger.js` to read the CSRF token without a form element
  - [ ] Do NOT modify any other part of `base.html`

- [ ] Task 5: Implement `set-logger.js` AJAX auto-save (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/static/js/set-logger.js` — replace stub comment with full implementation
  - [ ] Read CSRF token from `<meta name="csrf-token">`:
    ```js
    function getCsrfToken() {
      const meta = document.querySelector('meta[name="csrf-token"]');
      return meta ? meta.getAttribute('content') : '';
    }
    ```
  - [ ] Implement `saveSet(sessionId, exerciseId, weightKg, reps, buttonEl, errorEl)` function:
    - Set button to disabled state with "Saving…" text during request
    - Clear any previous inline error in `errorEl`
    - `fetch` `POST /api/sessions/<sessionId>/sets` with headers:
      - `Content-Type: application/json`
      - `X-CSRFToken: <csrf_token>`
    - Body: `JSON.stringify({exercise_id: exerciseId, weight_kg: weightKg, reps: reps})`
    - On success (response `status === "ok"`): show visual "Saved ✓" confirmation, restore button
    - On network failure or non-ok status: show inline error "Set not saved — check your connection." in `errorEl`, restore button, do NOT clear inputs
  - [ ] Attach event listeners via `DOMContentLoaded`:
    ```js
    document.addEventListener('DOMContentLoaded', function() {
      document.querySelectorAll('.set-logger__save-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
          const form = btn.closest('.set-logger__form');
          const sessionId = form.dataset.sessionId;
          const exerciseId = form.dataset.exerciseId;
          const weightInput = form.querySelector('.set-logger__weight');
          const repsInput = form.querySelector('.set-logger__reps');
          const errorEl = form.querySelector('.set-logger__error');
          const weightKg = parseFloat(weightInput.value);
          const reps = parseInt(repsInput.value, 10);
          if (!weightKg || !reps || weightKg <= 0 || reps <= 0) {
            errorEl.textContent = 'Enter valid weight and reps.';
            return;
          }
          saveSet(sessionId, exerciseId, weightKg, reps, btn, errorEl);
        });
      });
    });
    ```
  - [ ] NOTE: `set_number` is NOT sent by client — it is calculated server-side (count of existing sets for that exercise+session + 1)

- [ ] Task 6: Add API endpoint `POST /api/sessions/<id>/sets` (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/api/routes.py`
  - [ ] Add all required imports:
    ```python
    import logging
    from datetime import datetime
    from flask import request
    from flask_login import current_user, login_required
    from app.extensions import db
    from app.models.workout_session import WorkoutSession
    from app.models.workout_set import WorkoutSet
    ```
  - [ ] Add logger: `logger = logging.getLogger(__name__)`
  - [ ] ADD route `POST /api/sessions/<int:id>/sets` decorated with `@login_required`:
    ```python
    @api_bp.route('/sessions/<int:id>/sets', methods=['POST'])
    @login_required
    def log_set(id):
        workout_session = WorkoutSession.query.filter_by(
            id=id, user_id=current_user.id
        ).first_or_404()
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON body"}), 400
        exercise_id = data.get('exercise_id')
        weight_kg = data.get('weight_kg')
        reps = data.get('reps')
        if not exercise_id or weight_kg is None or reps is None:
            return jsonify({"status": "error", "message": "exercise_id, weight_kg, and reps are required"}), 400
        if weight_kg <= 0 or reps <= 0:
            return jsonify({"status": "error", "message": "weight_kg and reps must be positive"}), 400
        # Auto-calculate set_number server-side (AC 3)
        set_number = WorkoutSet.query.filter_by(
            session_id=workout_session.id, exercise_id=exercise_id
        ).count() + 1
        workout_set = WorkoutSet(
            session_id=workout_session.id,
            exercise_id=exercise_id,
            set_number=set_number,
            weight_kg=float(weight_kg),
            reps=int(reps),
            logged_at=datetime.utcnow(),
        )
        db.session.add(workout_set)
        db.session.commit()
        logger.info('Set logged: user=%d session=%d exercise=%d set=%d weight=%.1f reps=%d',
                    current_user.id, workout_session.id, exercise_id, set_number, weight_kg, reps)
        return jsonify({"status": "ok", "set_id": workout_set.id, "pr_detected": False}), 201
    ```
  - [ ] PRESERVE existing `/health` route — do NOT remove it
  - [ ] PR detection is NOT called here (hot path requirement <500ms)

- [ ] Task 7: Update `session_log` route to pass logged sets and all exercises (AC: 1)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Add import: `from app.models.workout_set import WorkoutSet`
  - [ ] Update `session_log` view to also query and pass:
    - `logged_sets`: `WorkoutSet.query.filter_by(session_id=workout_session.id).order_by(WorkoutSet.exercise_id, WorkoutSet.set_number).all()`
    - `all_exercises`: `Exercise.query.order_by(Exercise.name).all()` — needed for ad-hoc session set-logging
    - Group sets by `exercise_id` for easy template rendering: `sets_by_exercise = {}` dict keyed by `exercise_id`
  - [ ] Pass `logged_sets`, `sets_by_exercise`, and `all_exercises` to `render_template`
  - [ ] Do NOT modify any other routes

- [ ] Task 8: Update `session_log.html` with set-logging forms and logged sets display (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/templates/workouts/session_log.html`
  - [ ] For plan-based sessions (when `plan_exercises` is non-empty): for each `pe` in `plan_exercises`, render a set-logging form:
    ```html
    <div class="set-logger__form"
         data-session-id="{{ session.id }}"
         data-exercise-id="{{ pe.exercise_id }}">
      <h3 class="set-logger__exercise-name">{{ exercise_map[pe.exercise_id].name }}</h3>
      <p class="set-logger__targets">Target: {{ pe.target_sets }} × {{ pe.target_reps }}</p>
      <!-- Display already-logged sets for this exercise -->
      <ul class="set-logger__set-list" id="sets-{{ pe.exercise_id }}">
        {% for ws in sets_by_exercise.get(pe.exercise_id, []) %}
        <li class="set-logger__set-item">Set {{ ws.set_number }}: {{ ws.weight_kg }}kg × {{ ws.reps }} reps</li>
        {% endfor %}
      </ul>
      <!-- New set input row -->
      <div class="set-logger__inputs">
        <label class="set-logger__label" for="weight-{{ pe.exercise_id }}">Weight (kg)</label>
        <input class="set-logger__weight" id="weight-{{ pe.exercise_id }}" type="number" step="0.5" min="0" placeholder="0.0">
        <label class="set-logger__label" for="reps-{{ pe.exercise_id }}">Reps</label>
        <input class="set-logger__reps" id="reps-{{ pe.exercise_id }}" type="number" min="1" placeholder="0">
        <button class="set-logger__save-btn btn btn--primary" type="button">Save Set</button>
      </div>
      <p class="set-logger__error" role="alert" aria-live="polite"></p>
    </div>
    ```
  - [ ] For ad-hoc sessions (when `plan_exercises` is empty): render a single set-logging form with an exercise selector:
    ```html
    <div class="set-logger__form"
         data-session-id="{{ session.id }}"
         data-exercise-id="">
      <select class="set-logger__exercise-select" aria-label="Select exercise">
        <option value="">— Select exercise —</option>
        {% for ex in all_exercises %}
        <option value="{{ ex.id }}">{{ ex.name }}</option>
        {% endfor %}
      </select>
      <div class="set-logger__inputs">
        <input class="set-logger__weight" type="number" step="0.5" min="0" placeholder="Weight (kg)">
        <input class="set-logger__reps" type="number" min="1" placeholder="Reps">
        <button class="set-logger__save-btn btn btn--primary" type="button">Save Set</button>
      </div>
      <p class="set-logger__error" role="alert" aria-live="polite"></p>
    </div>
    ```
    NOTE: For ad-hoc forms, `set-logger.js` must read the selected exercise from the dropdown (update `data-exercise-id` or read from select) before calling `saveSet`. The JS event listener should handle this by reading `.set-logger__exercise-select` value if present.
  - [ ] Remove the static placeholder text "Set logging will be added in the next story."
  - [ ] BEM class names applied throughout
  - [ ] WCAG: All inputs must have `<label>` elements or `aria-label` attributes; error container uses `role="alert"` and `aria-live="polite"`
  - [ ] Do NOT add another `<script>` tag for `set-logger.js` — it is already globally loaded in `base.html`

- [ ] Task 9: Create `tests/test_api.py` with API endpoint tests (AC: 1, 2, 3)
  - [ ] CREATE `gymtrack/tests/test_api.py`
  - [ ] Follow same fixture pattern as `test_workouts.py` (`app` + `client` fixtures, `make_user`, `login_as` helpers)
  - [ ] Import `WorkoutSession`, `WorkoutSet` for assertions
  - [ ] `test_log_set_creates_row`: POST valid JSON → assert 201 → assert `WorkoutSet` row exists with correct `session_id`, `exercise_id`, `weight_kg`, `reps`, `set_number=1`
  - [ ] `test_log_set_response_format`: assert response JSON has `status="ok"`, `set_id` (int), `pr_detected=False`
  - [ ] `test_log_set_increments_set_number`: POST two sets for same exercise in same session → assert `set_number` values are 1 and 2
  - [ ] `test_log_set_separate_set_numbers_per_exercise`: POST sets for two different exercises → each has `set_number=1`
  - [ ] `test_log_set_missing_fields`: POST JSON missing `reps` → assert 400 response
  - [ ] `test_log_set_invalid_values`: POST `weight_kg=0` or `reps=0` → assert 400 response
  - [ ] `test_log_set_requires_auth`: POST without login → assert 401 or redirect to login
  - [ ] `test_log_set_session_isolation`: POST to another user's session → assert 404

## Dev Notes

### WorkoutSet Model
- `__tablename__ = 'workout_sets'` — plural snake_case per architecture
- `session_id` FK to `workout_sessions.id` — NOT to `users.id` directly (user isolation enforced via session ownership check in the API route)
- `exercise_id` FK to `exercises.id` — nullable=False (every set must be associated with an exercise)
- `weight_kg` is `Float` — supports decimal weights like 22.5 kg
- `set_number` is `Integer` — auto-calculated server-side, never trusted from client input
- `logged_at` uses `datetime.utcnow` — UTC, no timezone info in column (per architecture DateTime convention)

### Auto-Save Hot Path: <500ms Requirement (NFR2)
- **PR detection MUST NOT be called on `POST /api/sessions/<id>/sets`** — this is architecturally mandated
- The endpoint only does: session ownership check + count existing sets + insert one row + commit
- No aggregation queries, no external calls
- This keeps the hot path minimal (expected <50ms for SQLite dev, <200ms for PostgreSQL prod)

### User Data Isolation Pattern
- API route MUST use: `WorkoutSession.query.filter_by(id=id, user_id=current_user.id).first_or_404()`
- `WorkoutSet` does NOT have a `user_id` column — isolation is enforced through session ownership
- NEVER query WorkoutSet directly by `id` without first verifying session ownership

### set_number Calculation (AC 3)
- `set_number` is determined server-side:
  ```python
  set_number = WorkoutSet.query.filter_by(
      session_id=session.id, exercise_id=exercise_id
  ).count() + 1
  ```
- This is per-exercise within a session (not global across all exercises in the session)
- Client does NOT send `set_number` — the API body is `{exercise_id, weight_kg, reps}` only

### CSRF with AJAX
- `base.html` does NOT currently have a CSRF meta tag — Task 4 adds it
- `set-logger.js` reads `<meta name="csrf-token">` and sends `X-CSRFToken` header
- Flask-WTF validates this header for AJAX requests — no form token needed

### API Response Format (Architecture Compliance)
Architecture specifies the auto-save response:
```json
{"status": "ok", "set_id": 123, "pr_detected": false}
```
- HTTP 201 for resource created (per architecture HTTP Status Codes)
- `pr_detected` always `false` on this endpoint (detection only at session completion)
- Error format: `{"status": "error", "message": "Human-readable error description"}`

### Variable Naming Caution (Inherited from Story 4.1)
- Flask's `session` (cookie-based) vs `WorkoutSession` SQLAlchemy object
- Current `routes.py` uses `workout_session` for the SQLAlchemy instance — continue this pattern
- In `api/routes.py`, also use `workout_session` (not `session`) to avoid ambiguity with Flask's `session`

### set-logger.js is Already Loaded Globally
- `base.html` line 54: `<script src="{{ url_for('static', filename='js/set-logger.js') }}"></script>`
- Do NOT add another `<script>` tag in `session_log.html`
- The JS file currently contains only a stub comment — Task 5 replaces it with full implementation

### Ad-hoc Session Set Logging
- For ad-hoc sessions, `plan_exercises` is empty (no pre-populated exercises)
- The `session_log.html` ad-hoc form requires an exercise selector (all_exercises list)
- The `set-logger.js` event handler must read the selected `exercise_id` from `.set-logger__exercise-select` when present (overrides `data-exercise-id`)
- Example JS logic for ad-hoc form:
  ```js
  let exerciseId = form.dataset.exerciseId;
  const select = form.querySelector('.set-logger__exercise-select');
  if (select) exerciseId = select.value;
  if (!exerciseId) { errorEl.textContent = 'Select an exercise first.'; return; }
  ```

### Testing Pattern (test_api.py)
- Follow same pattern as `test_workouts.py`:
  - `app` fixture: `create_app('testing')`, `_db.create_all()`, yield, `_db.drop_all()`
  - `client` fixture: `app.test_client()`
  - `make_user`, `login_as` helpers
- For API tests: post JSON with `content_type='application/json'`
- CSRF is disabled in testing config — do NOT add CSRF token to test requests
- Example:
  ```python
  rv = client.post(
      f'/api/sessions/{session_id}/sets',
      json={'exercise_id': ex.id, 'weight_kg': 70.0, 'reps': 5},
  )
  assert rv.status_code == 201
  ```

### Project Structure Notes
- New model file: `gymtrack/app/models/workout_set.py`
- Updated model registry: `gymtrack/app/models/__init__.py`
- New migration: `gymtrack/migrations/versions/<hash>_add_workout_sets_table.py`
- Updated API routes: `gymtrack/app/api/routes.py` (add log_set endpoint)
- Updated workout routes: `gymtrack/app/blueprints/workouts/routes.py` (update session_log view)
- Updated JS: `gymtrack/app/static/js/set-logger.js` (implement auto-save logic)
- Updated template: `gymtrack/app/templates/workouts/session_log.html` (add set forms + logged sets display)
- Updated template: `gymtrack/app/templates/base.html` (add CSRF meta tag)
- New test file: `gymtrack/tests/test_api.py`

### References
- Architecture Auto-Save Endpoint: `_bmad-output/planning-artifacts/architecture.md` → API & Communication Patterns → Auto-Save Endpoint
- Architecture DB Naming: `_bmad-output/planning-artifacts/architecture.md` → Naming Patterns → Database Naming Conventions
- Architecture User Isolation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → User Data Isolation
- Architecture JSON Response Format: `_bmad-output/planning-artifacts/architecture.md` → Format Patterns → JSON API Response Format
- Architecture HTTP Status Codes: `_bmad-output/planning-artifacts/architecture.md` → Format Patterns → HTTP Status Codes
- Architecture PR Detection: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → PR Detection Service Invocation
- Architecture JS Files: `_bmad-output/planning-artifacts/architecture.md` → Frontend Architecture → JavaScript
- Architecture Test Structure: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Test Structure
- Epic 4 Story 4.2 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 4 → Story 4.2
- Previous Story (4.1) Dev Notes: `_bmad-output/implementation-artifacts/4-1-start-a-workout-session.md`
- Existing workout routes (state to preserve): `gymtrack/app/blueprints/workouts/routes.py`
- Existing session_log template (state to update): `gymtrack/app/templates/workouts/session_log.html`
- Existing API blueprint: `gymtrack/app/api/__init__.py`, `gymtrack/app/api/routes.py`
- base.html (globally loads set-logger.js): `gymtrack/app/templates/base.html`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

- Added `CSRFProtect` to extensions and `create_app()` — `csrf_token()` Jinja2 global was not available without it.

### Completion Notes List

- All 9 tasks completed. 8 new tests in `test_api.py`, all passing. Full suite: 93 passed.

### File List

- `gymtrack/app/models/workout_set.py` (created)
- `gymtrack/app/models/__init__.py` (updated)
- `gymtrack/app/extensions.py` (updated — added CSRFProtect)
- `gymtrack/app/__init__.py` (updated — init csrf)
- `gymtrack/app/templates/base.html` (updated — CSRF meta tag)
- `gymtrack/app/static/js/set-logger.js` (updated — full implementation)
- `gymtrack/app/api/routes.py` (updated — log_set endpoint)
- `gymtrack/app/blueprints/workouts/routes.py` (updated — session_log view)
- `gymtrack/app/templates/workouts/session_log.html` (updated — set-logging forms)
- `gymtrack/migrations/versions/a6c7a4f16c9d_add_workout_sets_table.py` (generated)
- `gymtrack/tests/test_api.py` (created)
