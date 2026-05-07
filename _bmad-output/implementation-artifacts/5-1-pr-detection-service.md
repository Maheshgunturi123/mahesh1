# Story 5.1: PR Detection Service

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want the system to automatically detect personal records when I complete a session,
So that my achievements are surfaced without any manual effort.

## Acceptance Criteria

1. **Given** I complete a workout session
   **When** `POST /workouts/sessions/<id>/complete` is processed
   **Then** `detect_prs(user_id=current_user.id, session_id=session.id)` is called **once**, after `is_complete = True` and `db.session.commit()` have run
   **And** the function compares each `workout_sets` row in that session against the `personal_records` table for the same `user_id` + `exercise_id`
   **And** if `weight_kg` in the session set **exceeds** the stored PR, a new `personal_records` row is upserted (insert or update) with the new `weight_kg`, `reps`, and `achieved_at` set to UTC now
   **And** `detect_prs` is a **pure function** in `app/services/pr_detection.py` — no Flask context required, independently testable

2. **Given** the session contains sets for 3 different exercises
   **When** PR detection runs
   **Then** each exercise is evaluated independently and only exercises with a new PR produce a result entry

3. **Given** the user has no prior PR for an exercise
   **When** a set is logged for that exercise and the session is completed
   **Then** the first set that beats zero creates a new `personal_records` row (first occurrence is always a PR)

4. **Given** PR detection is NOT called on the auto-save endpoint `POST /api/sessions/<id>/sets`
   **When** a set is auto-saved mid-session
   **Then** no PR computation occurs and the auto-save endpoint response time remains <500ms (NFR2)

5. **Given** two users each complete sessions for the same exercise
   **When** PR detection runs for each
   **Then** User A's PR does not affect User B's PR (strict `user_id` scoping on all queries)

6. **Given** a session set weight equals (not exceeds) the stored PR
   **When** `detect_prs` runs
   **Then** the existing `personal_records` row is NOT overwritten and the result entry marks `is_new=False` (matched PR — foundation for Story 5.2)

## Tasks / Subtasks

- [ ] Task 1: Create `PersonalRecord` model (AC: 1, 3, 5)
  - [ ] CREATE `gymtrack/app/models/personal_record.py`
  - [ ] Define `PersonalRecord` SQLAlchemy model with columns: `id`, `user_id`, `exercise_id`, `weight_kg`, `reps`, `achieved_at`, `created_at`, `updated_at`
  - [ ] Add `UniqueConstraint('user_id', 'exercise_id', name='uq_user_exercise_pr')` — one PR row per user per exercise
  - [ ] Add indices: `idx_pr_user_id` on `user_id`, `idx_pr_user_exercise` on `(user_id, exercise_id)`
  - [ ] UPDATE `gymtrack/app/models/__init__.py` to import `PersonalRecord`
  - [ ] Model definition:
    ```python
    from datetime import datetime
    from app.extensions import db
    from sqlalchemy import UniqueConstraint

    class PersonalRecord(db.Model):
        __tablename__ = 'personal_records'
        __table_args__ = (
            UniqueConstraint('user_id', 'exercise_id', name='uq_user_exercise_pr'),
        )

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
        exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
        weight_kg = db.Column(db.Float, nullable=False)
        reps = db.Column(db.Integer, nullable=False)
        achieved_at = db.Column(db.DateTime, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow, nullable=False)

        user = db.relationship('User', backref=db.backref('personal_records', lazy='dynamic'))
        exercise = db.relationship('Exercise', backref=db.backref('personal_records', lazy='dynamic'))
    ```

- [ ] Task 2: Generate and apply migration (AC: 1)
  - [ ] Run `flask db migrate -m "add personal_records table"` from the `gymtrack/` directory
  - [ ] Verify the generated migration creates `personal_records` table, the unique constraint, and the two indices
  - [ ] Run `flask db upgrade` to apply
  - [ ] Migration must include `downgrade()` that drops the table and indices

- [ ] Task 3: Create `detect_prs` pure function in `app/services/pr_detection.py` (AC: 1, 2, 3, 5, 6)
  - [ ] CREATE `gymtrack/app/services/pr_detection.py`
  - [ ] Implement `detect_prs(user_id: int, session_id: int) -> list[dict]`
  - [ ] Function must NOT import from `flask` (no `current_user`, no `g`, no `request`) — pure, testable without app context
  - [ ] Logic: for each distinct exercise in the session's sets, find the max `weight_kg` logged; compare against stored PR
    - If no existing PR → insert new row (`is_new=True`)
    - If set weight > stored PR weight → update row (`is_new=True`)
    - If set weight == stored PR weight → no update, include in results as `is_new=False` (matched)
    - If set weight < stored PR → skip (no result entry)
  - [ ] Each result dict: `{'exercise_id': int, 'weight_kg': float, 'reps': int, 'is_new': bool}`
  - [ ] Use `db.session` directly (imported from `app.extensions`) — not Flask context-bound
  - [ ] Log each new PR with `logger.info('PR detected: user=%d exercise=%d weight=%.1f', ...)`
  - [ ] Implementation sketch:
    ```python
    import logging
    from datetime import datetime
    from sqlalchemy import func
    from app.extensions import db
    from app.models.workout_set import WorkoutSet
    from app.models.personal_record import PersonalRecord

    logger = logging.getLogger(__name__)

    def detect_prs(user_id: int, session_id: int) -> list[dict]:
        """Detect new or matched personal records for all exercises in a completed session.

        Pure function — no Flask context required. Call after session.is_complete = True
        and db.session.commit() in the session_complete_post route.

        Returns:
            List of dicts: [{'exercise_id': int, 'weight_kg': float, 'reps': int, 'is_new': bool}]
            Only exercises with a new or matched PR are included.
        """
        # Get best set per exercise in this session (max weight_kg)
        best_sets = (
            db.session.query(
                WorkoutSet.exercise_id,
                func.max(WorkoutSet.weight_kg).label('best_weight'),
            )
            .filter_by(session_id=session_id)
            .group_by(WorkoutSet.exercise_id)
            .all()
        )

        results = []
        for row in best_sets:
            exercise_id = row.exercise_id
            session_weight = row.best_weight

            # Get reps for the best set
            best_set = (
                WorkoutSet.query
                .filter_by(session_id=session_id, exercise_id=exercise_id, weight_kg=session_weight)
                .order_by(WorkoutSet.set_number)
                .first()
            )
            reps = best_set.reps if best_set else 0

            existing = PersonalRecord.query.filter_by(
                user_id=user_id, exercise_id=exercise_id
            ).first()

            if existing is None:
                # First ever PR for this exercise
                pr = PersonalRecord(
                    user_id=user_id,
                    exercise_id=exercise_id,
                    weight_kg=session_weight,
                    reps=reps,
                    achieved_at=datetime.utcnow(),
                )
                db.session.add(pr)
                db.session.commit()
                logger.info('PR detected (new): user=%d exercise=%d weight=%.1f',
                            user_id, exercise_id, session_weight)
                results.append({'exercise_id': exercise_id, 'weight_kg': session_weight,
                                 'reps': reps, 'is_new': True})

            elif session_weight > existing.weight_kg:
                # New PR — update existing row
                existing.weight_kg = session_weight
                existing.reps = reps
                existing.achieved_at = datetime.utcnow()
                db.session.commit()
                logger.info('PR detected (improved): user=%d exercise=%d weight=%.1f',
                            user_id, exercise_id, session_weight)
                results.append({'exercise_id': exercise_id, 'weight_kg': session_weight,
                                 'reps': reps, 'is_new': True})

            elif session_weight == existing.weight_kg:
                # Matched PR — do NOT update row, surface as matched
                results.append({'exercise_id': exercise_id, 'weight_kg': session_weight,
                                 'reps': reps, 'is_new': False})

            # session_weight < existing.weight_kg → no entry

        return results
    ```

- [ ] Task 4: Integrate `detect_prs` into `session_complete_post` route (AC: 1, 4)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Add import at top of file: `from app.services.pr_detection import detect_prs`
  - [ ] In `session_complete_post`, after `db.session.commit()` and before the `return redirect(...)`, add:
    ```python
    try:
        detect_prs(user_id=current_user.id, session_id=workout_session.id)
    except Exception as e:
        logger.error('PR detection failed for session %d: %s', workout_session.id, str(e))
        # PR detection failure must never block session completion
    ```
  - [ ] The `return redirect(url_for('workouts.session_complete', id=workout_session.id))` remains unchanged
  - [ ] **Do NOT add** any PR detection call to `POST /api/sessions/<id>/sets` — the auto-save endpoint must remain untouched

- [ ] Task 5: Write unit tests for `detect_prs` service (AC: 1, 2, 3, 4, 5, 6)
  - [ ] CREATE `gymtrack/tests/test_pr_detection.py`
  - [ ] Tests must use the app context fixture (no Flask context in the service itself but tests need DB)
  - [ ] Reuse `make_user`, `make_exercise`, `make_completed_session`, `make_workout_set` helpers from `test_workouts.py` (or import from conftest if refactored)
  - [ ] Tests to write:
    - `test_detect_prs_new_record` — no prior PR; set at 80kg; detect_prs returns `[{..., is_new=True}]` and inserts PR row
    - `test_detect_prs_improved_record` — prior PR at 70kg; session set at 80kg; detect_prs returns `is_new=True`, updates existing row
    - `test_detect_prs_matched_record` — prior PR at 80kg; session set at 80kg; detect_prs returns `is_new=False`, existing row unchanged
    - `test_detect_prs_below_record` — prior PR at 80kg; session set at 70kg; detect_prs returns `[]`
    - `test_detect_prs_multiple_exercises` — session with 3 exercises; each evaluated independently; results include only exercises at or above PR
    - `test_detect_prs_user_isolation` — user A has PR at 100kg; user B completes session at 90kg; detect_prs for user B creates 90kg PR, user A's 100kg row untouched
    - `test_detect_prs_returns_empty_for_empty_session` — session with no sets; returns `[]`
  - [ ] Example test structure:
    ```python
    # gymtrack/tests/test_pr_detection.py

    import pytest
    from app.services.pr_detection import detect_prs
    from app.models.personal_record import PersonalRecord

    # ─────────────────────────────────────────────
    # Helpers (replicate or import from test_workouts.py)
    # ─────────────────────────────────────────────

    def test_detect_prs_new_record(app):
        with app.app_context():
            from app.extensions import db as _db
            _db.create_all()
            # setup: make user, exercise, completed session with one set
            ...
            results = detect_prs(user_id=user.id, session_id=session.id)
            assert len(results) == 1
            assert results[0]['is_new'] is True
            assert results[0]['weight_kg'] == 80.0
            pr = PersonalRecord.query.filter_by(user_id=user.id, exercise_id=exercise.id).first()
            assert pr is not None
            assert pr.weight_kg == 80.0

    def test_detect_prs_user_isolation(app):
        with app.app_context():
            from app.extensions import db as _db
            _db.create_all()
            # user A has existing PR at 100kg
            # user B completes session at 90kg
            results = detect_prs(user_id=user_b.id, session_id=session_b.id)
            # User B gets their own PR at 90kg
            assert len(results) == 1
            assert results[0]['weight_kg'] == 90.0
            # User A's PR at 100kg is untouched
            pr_a = PersonalRecord.query.filter_by(user_id=user_a.id, exercise_id=exercise.id).first()
            assert pr_a.weight_kg == 100.0
    ```

- [ ] Task 6: Write integration tests for `session_complete_post` + PR detection (AC: 1, 4)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py`
  - [ ] Add section header `# ─── Story 5.1 — PR Detection Integration ───`
  - [ ] Tests to add:
    - `test_complete_session_creates_pr` — complete a session with one set; GET `/workouts/sessions/<id>/complete` → 200 (confirm no error); verify PR row exists in DB
    - `test_pr_detection_not_called_on_auto_save` — POST to `/api/sessions/<id>/sets`; verify no `PersonalRecord` row created
    - `test_complete_session_pr_detection_failure_does_not_block_completion` — monkey-patch `detect_prs` to raise; POST complete → still redirects to summary (302), session remains complete

## Dev Notes

### What Story 5.1 Changes

This story introduces the **Personal Record detection engine** — the first piece of Epic 5. It:
1. Adds a new `personal_records` DB table (new model + migration)
2. Creates `app/services/pr_detection.py` (pure function, no Flask context)
3. Hooks `detect_prs()` into the existing `session_complete_post` route (Task 4) — the ONLY place PR detection is ever called

**Files NOT to touch:**
- `POST /api/sessions/<id>/sets` — auto-save endpoint must remain PR-detection-free (NFR2: <500ms)
- The GET `session_complete` route — Story 5.3 adds the PR banner to the summary page; this story only persists the data
- Any other blueprint — PR detection is self-contained in services layer

### Integration Point: `session_complete_post`

Story 4.4 established this route. Its current end-of-handler sequence is:
```python
workout_session.is_complete = True
workout_session.completed_at = datetime.utcnow()
db.session.commit()
logger.info('Workout session completed: user=%d session_id=%d', ...)
return redirect(url_for('workouts.session_complete', id=workout_session.id))
```

Story 5.1 inserts the `detect_prs()` call **after** `db.session.commit()`:
```python
workout_session.is_complete = True
workout_session.completed_at = datetime.utcnow()
db.session.commit()
logger.info('Workout session completed: user=%d session_id=%d', ...)
try:
    detect_prs(user_id=current_user.id, session_id=workout_session.id)
except Exception as e:
    logger.error('PR detection failed for session %d: %s', workout_session.id, str(e))
return redirect(url_for('workouts.session_complete', id=workout_session.id))
```

The `try/except` wrapper ensures PR detection failures never prevent session completion — the user's data is safe.

### `detect_prs` Return Contract

The function returns a `list[dict]` consumed by Story 5.3 (PR banner on summary page). Even though Story 5.1 does not yet display these results in any template, the return value must match the contract Story 5.3 expects:

```python
[
    {'exercise_id': 1, 'weight_kg': 80.0, 'reps': 5, 'is_new': True},   # new PR
    {'exercise_id': 2, 'weight_kg': 60.0, 'reps': 3, 'is_new': False},  # matched PR
]
```

Only exercises with `weight_kg >= stored PR weight` are included. Exercises with `weight_kg < stored PR` are silently omitted.

### `personal_records` Table Design

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK | Auto-increment |
| `user_id` | INTEGER | FK `users.id`, NOT NULL, indexed | User isolation |
| `exercise_id` | INTEGER | FK `exercises.id`, NOT NULL | Composite unique with user_id |
| `weight_kg` | FLOAT | NOT NULL | Best weight ever for this user+exercise |
| `reps` | INTEGER | NOT NULL | Reps at the best weight |
| `achieved_at` | DATETIME | NOT NULL | UTC timestamp of PR achievement |
| `created_at` | DATETIME | NOT NULL, default=utcnow | Row creation |
| `updated_at` | DATETIME | NOT NULL, default/onupdate=utcnow | Last update |

**UniqueConstraint `uq_user_exercise_pr`** on `(user_id, exercise_id)` — one row per user per exercise. PR updates are in-place updates to this row, not inserts.

**Design decision:** one row per user+exercise (the best ever). Stories 5.2-5.4 and Epic 6 all read from this table. Do NOT store one row per session — that would be a different table (`pr_history`) and is not in scope.

### Pure Function Requirement

`detect_prs` must not import anything Flask-context-bound (`flask.g`, `flask.request`, `flask_login.current_user`). It receives `user_id` and `session_id` as plain integers. It uses `db.session` imported from `app.extensions` — this is safe because SQLAlchemy's scoped session works without the request context when an app context is active (which it always is when called from a route handler).

Unit tests run `detect_prs` inside `with app.app_context()` — no test client needed.

### Auto-Save Endpoint: Do Not Touch

`POST /api/sessions/<id>/sets` currently returns:
```json
{"status": "ok", "set_id": 123, "pr_detected": false}
```
The `pr_detected: false` field is already in the response (from Story 4.2). Do NOT change this to `True` based on individual set saves. It will remain `false` until a session is completed. The field is a placeholder for potential future enhancement — do not remove it.

### First-Time PR Logic

When a user has no prior PR for an exercise, the first completion creates the initial row. This means `session_weight > 0 > existing` — but since `existing` is `None`, the code path is `existing is None` → insert. The "exceeds stored PR" logic only applies when a prior row exists.

### Error Handling

PR detection failure must never block session completion. The `try/except` in the route handler is mandatory. Log the error with `logger.error(...)` — Sentry will capture it automatically in production. Do NOT re-raise.

### Project Structure Notes

**Files to CREATE:**
- `gymtrack/app/models/personal_record.py` — new model
- `gymtrack/app/services/pr_detection.py` — new service (note: `services/` directory may not exist yet — create it)
- `gymtrack/tests/test_pr_detection.py` — new unit test file
- `gymtrack/migrations/versions/<hash>_add_personal_records_table.py` — auto-generated by `flask db migrate`

**Files to UPDATE:**
- `gymtrack/app/models/__init__.py` — add `from app.models.personal_record import PersonalRecord`
- `gymtrack/app/blueprints/workouts/routes.py` — add `detect_prs` import and call in `session_complete_post`
- `gymtrack/tests/test_workouts.py` — add Story 5.1 integration tests

**Files NOT to touch:**
- `gymtrack/app/blueprints/workouts/routes.py` `session_complete` GET route — Story 5.3 adds banner
- `gymtrack/app/templates/workouts/session_complete.html` — Story 5.3 adds banner
- Any auto-save route or `set-logger.js`

### Dependencies

- **Depends on:** Epic 4 complete (specifically Story 4.4 for `session_complete_post` route and Story 4.2 for `WorkoutSet` model with `weight_kg` and `reps` columns)
- **Blocks:** Story 5.2 (matched PR detection refinement), Story 5.3 (PR banner on summary), Story 5.4 (view all PRs), Epic 6 (progress charts use `personal_records`)

### Testing Standards

- Unit tests in `test_pr_detection.py` test the pure function directly (no HTTP)
- Integration tests in `test_workouts.py` test the route-to-service pipeline via test client
- All tests use `app.app_context()` for DB operations
- Test helper `make_workout_set` must support `weight_kg` and `reps` kwargs (already established in 4.5)
- Test helper `make_completed_session` already exists in `test_workouts.py`

### References

- Story 5.1 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 5 → Story 5.1
- Architecture Service Layer: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Service Layer
- Architecture PR Detection Invocation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → PR Detection Service Invocation
- Architecture Data Isolation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → User Data Isolation (MANDATORY)
- Architecture DB Naming: `_bmad-output/planning-artifacts/architecture.md` → Naming Patterns → Database Naming Conventions
- Architecture Auto-Save Endpoint spec: `_bmad-output/planning-artifacts/architecture.md` → API & Communication Patterns → Auto-Save Endpoint
- Story 4.4 `session_complete_post` route: `_bmad-output/implementation-artifacts/4-4-complete-a-session.md` → Task 4
- Story 4.2 `WorkoutSet` model (weight_kg, reps): `_bmad-output/implementation-artifacts/4-2-log-sets-with-auto-save.md`
- `WorkoutSet` model: `gymtrack/app/models/workout_set.py`
- Existing workouts routes: `gymtrack/app/blueprints/workouts/routes.py`
- Test helpers: `gymtrack/tests/test_workouts.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List
