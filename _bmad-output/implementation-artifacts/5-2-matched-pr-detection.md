# Story 5.2: Matched PR Detection

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want the system to detect when I match (tie) a previous personal record,
so that I know I've maintained my peak performance after a gap.

## Acceptance Criteria

1. **Given** my current session includes a set where `weight_kg` equals (not exceeds) my stored `personal_records.weight_kg` for that exercise
   **When** `detect_prs` runs at session completion
   **Then** the result includes a matched PR entry with `is_new=False`
   **And** the existing `personal_records` row is NOT overwritten (matched PRs don't replace new PRs)

2. **Given** both a new PR and a matched PR are detected in the same session
   **When** `detect_prs` returns results
   **Then** both are included in the returned list — the new PR entry has `is_new=True` and the matched PR entry has `is_new=False`

## Tasks / Subtasks

- [ ] Task 1: Add matched PR log line to `detect_prs` (AC: 1)
  - [ ] UPDATE `gymtrack/app/services/pr_detection.py`
  - [ ] In the `elif session_weight == existing.weight_kg:` branch, add **before** `results.append(...)`:
    ```python
    logger.info('PR matched: user=%d exercise=%d weight=%.1f',
                user_id, exercise_id, session_weight)
    ```
  - [ ] This brings matched PR logging to parity with new (`PR detected (new)`) and improved (`PR detected (improved)`) branches
  - [ ] Do NOT change any other logic in `detect_prs` — the detection and return contract are correct

- [ ] Task 2: Add mixed-session unit test (AC: 2)
  - [ ] UPDATE `gymtrack/tests/test_pr_detection.py`
  - [ ] Add test `test_detect_prs_mixed_session_new_and_matched` after the existing `test_detect_prs_matched_record` test
  - [ ] Scenario: session contains 2 exercises — one produces a new PR, one produces a matched PR
  - [ ] Full test:
    ```python
    def test_detect_prs_mixed_session_new_and_matched(app):
        """AC: session with one new PR and one matched PR → both in results with correct is_new flags."""
        with app.app_context():
            user = make_user(_db)
            e1 = make_exercise(_db, name='Squat')
            e2 = make_exercise(_db, name='Bench Press', muscle_group='Chest')

            # e1: prior PR at 70kg; session set at 80kg → new/improved PR
            make_pr(_db, user.id, e1.id, weight_kg=70.0, reps=5)
            # e2: prior PR at 60kg; session set at 60kg → matched PR
            make_pr(_db, user.id, e2.id, weight_kg=60.0, reps=8)

            session = make_completed_session(_db, user.id)
            make_workout_set(_db, session.id, e1.id, weight_kg=80.0, reps=4)
            make_workout_set(_db, session.id, e2.id, weight_kg=60.0, reps=10)

            results = detect_prs(user_id=user.id, session_id=session.id)

            assert len(results) == 2

            e1_result = next(r for r in results if r['exercise_id'] == e1.id)
            assert e1_result['is_new'] is True
            assert e1_result['weight_kg'] == 80.0

            e2_result = next(r for r in results if r['exercise_id'] == e2.id)
            assert e2_result['is_new'] is False
            assert e2_result['weight_kg'] == 60.0

            # e1 PR row updated; e2 PR row unchanged
            pr_e1 = PersonalRecord.query.filter_by(user_id=user.id, exercise_id=e1.id).first()
            assert pr_e1.weight_kg == 80.0

            pr_e2 = PersonalRecord.query.filter_by(user_id=user.id, exercise_id=e2.id).first()
            assert pr_e2.weight_kg == 60.0
            assert pr_e2.reps == 8  # NOT updated to 10 — matched PRs never overwrite the row
    ```

- [ ] Task 3: Add integration test to `test_workouts.py` (AC: 1, 2)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py`
  - [ ] Add section header comment `# ─── Story 5.2 — Matched PR Detection Integration ───`
  - [ ] Add test `test_complete_session_with_matched_pr_does_not_overwrite_row`:
    - Set up: user has existing PR at 80kg for exercise
    - Create a session with a set at 80kg (same weight = matched)
    - POST to `POST /workouts/sessions/<id>/complete`
    - Verify: session completes (302 redirect), PR row `weight_kg` still equals 80kg, and row count remains 1 (no duplicate row inserted)
  - [ ] Test outline:
    ```python
    # ─── Story 5.2 — Matched PR Detection Integration ───

    def test_complete_session_with_matched_pr_does_not_overwrite_row(client, app):
        """Completing a session where session weight == stored PR weight must not overwrite the PR row."""
        with app.app_context():
            from app.extensions import db as _db
            from app.models.personal_record import PersonalRecord
            # create user, login via client
            # create exercise, existing PR at 80kg, session with set at 80kg
            # POST /workouts/sessions/<id>/complete
            # assert redirect (302)
            # assert PersonalRecord count == 1
            # assert PersonalRecord.weight_kg == 80.0 (unchanged)
    ```

## Dev Notes

### Story 5.2 Scope

Story 5.1 (done) already implemented the matched PR detection branch in `detect_prs`. The detection logic and return contract are complete and correct. Story 5.2 has a **narrow, targeted scope**:

1. **Add matched PR logging** — the `elif session_weight == existing.weight_kg` branch currently has no `logger.info(...)` call, unlike the new-PR and improved-PR branches. This is an observable gap that breaks log-based monitoring (Sentry traces new/improved PRs but misses matched ones).
2. **Add the mixed-session test** — no existing test covers a session that produces both a new PR and a matched PR simultaneously (Story 5.1's `test_detect_prs_multiple_exercises` covers new + below, not new + matched).
3. **Add integration test** — verify the no-overwrite invariant through the full HTTP stack.

### What Story 5.1 Already Delivered (DO NOT re-implement)

`gymtrack/app/services/pr_detection.py` already contains:
```python
elif session_weight == existing.weight_kg:
    results.append({'exercise_id': exercise_id, 'weight_kg': session_weight,
                     'reps': reps, 'is_new': False})
# session_weight < existing.weight_kg → no entry
```

`gymtrack/tests/test_pr_detection.py` already contains:
- `test_detect_prs_matched_record` — single matched PR scenario (row unchanged, is_new=False)

Do NOT re-create or duplicate these. Story 5.2 adds to them, not replaces them.

### The Only Code Change: One `logger.info` Line

Task 1 is a one-line addition inside `detect_prs`. After the `elif session_weight == existing.weight_kg:` line, insert:

```python
logger.info('PR matched: user=%d exercise=%d weight=%.1f',
            user_id, exercise_id, session_weight)
```

The resulting matched PR branch becomes:
```python
elif session_weight == existing.weight_kg:
    logger.info('PR matched: user=%d exercise=%d weight=%.1f',
                user_id, exercise_id, session_weight)
    results.append({'exercise_id': exercise_id, 'weight_kg': session_weight,
                     'reps': reps, 'is_new': False})
```

### `detect_prs` Return Contract (unchanged)

The return value contract Story 5.3 consumes is already correct:
```python
[
    {'exercise_id': 1, 'weight_kg': 80.0, 'reps': 5, 'is_new': True},   # new/improved PR
    {'exercise_id': 2, 'weight_kg': 60.0, 'reps': 3, 'is_new': False},  # matched PR
]
```
Story 5.3 will iterate this list and render banners: `is_new=True` → "🏆 New PR" banner, `is_new=False` → "💪 Matched PR" banner.

### `personal_records` Row Invariant

One row per `(user_id, exercise_id)` pair — enforced by `UniqueConstraint('user_id', 'exercise_id', name='uq_user_exercise_pr')`. Matched PRs NEVER upsert — the row always retains the highest `weight_kg` ever achieved.

### matched PR `reps` in Return Dict

The `reps` value in a matched PR result dict reflects the reps from the **current session's best set** at the matched weight — NOT the stored PR's reps. This is intentional: it tells the user "you lifted 60kg × 10 reps today, matching your PR". Story 5.3's banner uses this reps value for display.

The existing `personal_records` row's `reps` column is NOT updated (confirmed by `test_detect_prs_matched_record` which asserts `pr.reps == 5` when session set was `reps=8`).

### No New Files, No New Migrations

Story 5.2 touches two existing files only:
- `gymtrack/app/services/pr_detection.py` — +1 logger line
- `gymtrack/tests/test_pr_detection.py` — +1 new test function
- `gymtrack/tests/test_workouts.py` — +1 integration test

No model changes, no migrations, no new routes, no template changes.

### Testing Standards

- Unit tests run `detect_prs` inside `with app.app_context()` directly (no HTTP)
- Integration test uses the `client` fixture from `conftest.py` and the `app` fixture for DB assertions
- All DB helpers (`make_user`, `make_exercise`, `make_completed_session`, `make_workout_set`, `make_pr`) are already defined in `test_pr_detection.py` — reuse them or import from conftest if refactored

### Project Structure Notes

**Files to UPDATE (only):**
- `gymtrack/app/services/pr_detection.py` — add 1 `logger.info` line in matched PR branch
- `gymtrack/tests/test_pr_detection.py` — add `test_detect_prs_mixed_session_new_and_matched`
- `gymtrack/tests/test_workouts.py` — add Story 5.2 integration test section

**Files NOT to touch:**
- `gymtrack/app/models/personal_record.py` — no schema changes
- `gymtrack/app/blueprints/workouts/routes.py` — no route changes (detect_prs already called in session_complete_post)
- `gymtrack/app/templates/workouts/session_complete.html` — Story 5.3 owns this
- Any migration files — no DB changes

### References

- Story 5.2 ACs: `_bmad-output/planning-artifacts/epics.md` → Epic 5 → Story 5.2
- Story 5.1 implementation (foundation): `_bmad-output/implementation-artifacts/5-1-pr-detection-service.md`
- Existing `detect_prs` function: `gymtrack/app/services/pr_detection.py`
- Existing unit tests: `gymtrack/tests/test_pr_detection.py`
- Architecture Service Layer: `_bmad-output/planning-artifacts/architecture.md` → Structure Patterns → Service Layer
- Architecture Error Logging Pattern: `_bmad-output/planning-artifacts/architecture.md` → Format Patterns → Error Logging Pattern
- Architecture PR Detection Invocation: `_bmad-output/planning-artifacts/architecture.md` → Process Patterns → PR Detection Service Invocation

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List
