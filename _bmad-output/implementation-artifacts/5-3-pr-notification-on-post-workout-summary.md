# Story 5.3: PR Notification on Post-Workout Summary

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to see a PR notification banner after completing a workout,
so that I get immediate positive feedback when I hit a personal best.

## Acceptance Criteria

1. **Given** `detect_prs` returned one or more new PRs
   **When** the post-workout summary page `/workouts/sessions/<id>/complete` renders
   **Then** a prominent PR banner is displayed: "🏆 New PR — [Exercise Name]: [weight]kg × [reps] reps. Your best ever."
   **And** one banner appears per PR detected in this session

2. **Given** `detect_prs` returned one or more matched PRs
   **When** the summary page renders
   **Then** a banner is displayed: "💪 Matched PR — [Exercise Name]: [weight]kg × [reps] reps. Strength holds."

3. **Given** no PRs were detected
   **When** the summary page renders
   **Then** no PR banner is shown (no empty banner element in the DOM)

## Tasks / Subtasks

- [x] Task 1: Capture `detect_prs` return value and store PR results across the PRG redirect (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [x] Add `session` to flask import line: `from flask import flash, redirect, render_template, request, session, url_for`
  - [x] In `session_complete_post`: capture return value `pr_results = detect_prs(user_id=current_user.id, session_id=workout_session.id)` (replaces bare call that discards result)
  - [x] After capture, enrich results with exercise names by querying `Exercise.query.filter(Exercise.id.in_([r['exercise_id'] for r in pr_results])).all()` and building an `exercise_map`
  - [x] Build enriched list: `[{'exercise_name': exercise_map[r['exercise_id']].name, 'weight_kg': r['weight_kg'], 'reps': r['reps'], 'is_new': r['is_new']} for r in pr_results if r['exercise_id'] in exercise_map]`
  - [x] Store in Flask cookie session under key `f'pr_results_{workout_session.id}'` (only if non-empty)
  - [x] Wrap the enrichment in the same `try/except` block as `detect_prs` so PR detection failure still does NOT block session completion

- [x] Task 2: Retrieve PR results in GET handler and pass to template (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [x] In `session_complete` GET handler: pop PR results from Flask session: `pr_results = session.pop(f'pr_results_{id}', [])`
  - [x] Pass `pr_results=pr_results` to `render_template('workouts/session_complete.html', ...)`
  - [x] Note: `session.pop` is safe — returns empty list if key absent (e.g. user navigates back to the page after first load)

- [x] Task 3: Update `session_complete.html` template to render PR banners (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/app/templates/workouts/session_complete.html`
  - [x] Add PR banners section **above** `<section class="session-complete__summary">` (so it appears first, prominently)
  - [x] Only render the section when `pr_results` is non-empty: `{% if pr_results %}`
  - [x] For each PR result in `pr_results`, render:
    - `is_new=True` → `<div class="pr-banner pr-banner--new" role="alert">🏆 New PR — {{ r.exercise_name }}: {{ r.weight_kg }}kg × {{ r.reps }} reps. Your best ever.</div>`
    - `is_new=False` → `<div class="pr-banner pr-banner--matched" role="alert">💪 Matched PR — {{ r.exercise_name }}: {{ r.weight_kg }}kg × {{ r.reps }} reps. Strength holds.</div>`
  - [x] No wrapper div rendered at all when `pr_results` is empty (AC 3: no empty banner element)

- [x] Task 4: Add integration tests in `test_workouts.py` (AC: 1, 2, 3)
  - [x] UPDATE `gymtrack/tests/test_workouts.py`
  - [x] Add section header comment: `# ─── Story 5.3 — PR Notification on Post-Workout Summary ───`
  - [x] Add `test_session_complete_shows_new_pr_banner` (AC 1)
  - [x] Add `test_session_complete_shows_matched_pr_banner` (AC 2)
  - [x] Add `test_session_complete_no_pr_no_banner` (AC 3)
  - [x] See full test specs in Dev Notes below

## Dev Notes

### Core Implementation Context

The POST → GET (PRG) flow for session completion:
1. `POST /workouts/sessions/<id>/complete` (`session_complete_post`) — marks session complete, calls `detect_prs`, **redirects** to GET
2. `GET /workouts/sessions/<id>/complete` (`session_complete`) — renders the summary page

PR results from `detect_prs` must cross the redirect boundary. The project uses Flask's default client-side cookie session (itsdangerous-signed, see architecture "Session Storage" section). Use `flask.session` (the cookie-based session dict) to carry the enriched PR list from POST to GET via `session[key] = value` / `session.pop(key, default)`.

### Current State of `session_complete_post` (Lines 298–320)

```python
@workouts_bp.route('/sessions/<int:id>/complete', methods=['POST'])
@login_required
def session_complete_post(id):
    ...
    try:
        detect_prs(user_id=current_user.id, session_id=workout_session.id)  # ← return value DISCARDED
    except Exception as e:
        logger.error('PR detection failed for session %d: %s', workout_session.id, str(e))
    return redirect(url_for('workouts.session_complete', id=workout_session.id))
```

The `try/except` block must be expanded to also enrich and store results. The structure after Task 1:

```python
try:
    pr_results = detect_prs(user_id=current_user.id, session_id=workout_session.id)
    if pr_results:
        exercise_ids = [r['exercise_id'] for r in pr_results]
        exercises = Exercise.query.filter(Exercise.id.in_(exercise_ids)).all()
        ex_map = {e.id: e for e in exercises}
        enriched = [
            {
                'exercise_name': ex_map[r['exercise_id']].name,
                'weight_kg': r['weight_kg'],
                'reps': r['reps'],
                'is_new': r['is_new'],
            }
            for r in pr_results if r['exercise_id'] in ex_map
        ]
        if enriched:
            session[f'pr_results_{workout_session.id}'] = enriched
except Exception as e:
    logger.error('PR detection failed for session %d: %s', workout_session.id, str(e))
return redirect(url_for('workouts.session_complete', id=workout_session.id))
```

### Current State of `session_complete` GET handler (Lines 323–347)

```python
@workouts_bp.route('/sessions/<int:id>/complete', methods=['GET'])
@login_required
def session_complete(id):
    ...
    return render_template(
        'workouts/session_complete.html',
        session=workout_session,
        sets_by_exercise=sets_by_exercise,
        exercise_map=exercise_map,
        plan_name=plan_name,
    )
```

Add `pr_results = session.pop(f'pr_results_{id}', [])` before `render_template` and pass it as `pr_results=pr_results`.

**Important**: `session` here is `flask.session` (the cookie dict) — distinct from `workout_session` (the SQLAlchemy model). After adding `session` to the flask import, the local variable `workout_session` (renamed from `session` by convention in the code) avoids the name collision. Check the existing code: the route uses `workout_session` as the local variable name, so there is no collision.

### `detect_prs` Return Contract (from Story 5.2 dev notes)

```python
[
    {'exercise_id': 1, 'weight_kg': 80.0, 'reps': 5, 'is_new': True},   # new/improved PR
    {'exercise_id': 2, 'weight_kg': 60.0, 'reps': 3, 'is_new': False},  # matched PR
]
```

- `is_new=True` — new or improved PR (weight exceeds previous best, or no previous record existed)
- `is_new=False` — matched PR (weight equals previous best exactly)
- Exercises where session weight < stored PR are NOT included
- `reps` in a matched PR result reflects **current session's reps** at the matched weight, not the stored PR row's reps

### Template Structure After Task 3

`session_complete.html` currently has this structure:
```html
<div class="session-complete">
  <h1 class="session-complete__heading">Workout Complete! 🎉</h1>
  <div class="session-complete__meta">...</div>
  <section class="session-complete__summary">...</section>
  <a class="session-complete__back-link btn btn--secondary" ...>View All Sessions</a>
</div>
```

Insert the PR banners block between `__meta` and `__summary`:
```html
{% if pr_results %}
<div class="pr-banners">
  {% for r in pr_results %}
    {% if r.is_new %}
    <div class="pr-banner pr-banner--new" role="alert">
      🏆 New PR — {{ r.exercise_name }}: {{ r.weight_kg }}kg &times; {{ r.reps }} reps. Your best ever.
    </div>
    {% else %}
    <div class="pr-banner pr-banner--matched" role="alert">
      💪 Matched PR — {{ r.exercise_name }}: {{ r.weight_kg }}kg &times; {{ r.reps }} reps. Strength holds.
    </div>
    {% endif %}
  {% endfor %}
</div>
{% endif %}
```

The CSS classes `pr-banners`, `pr-banner`, `pr-banner--new`, `pr-banner--matched` follow BEM convention (architecture: block names match component — `pr-banner` is the block, `--new` / `--matched` are modifiers). Add styles to `app/static/css/style.css`.

### What NOT to Change

- Do NOT modify `detect_prs` service (`pr_detection.py`) — Story 5.1 and 5.2 already completed its implementation and tests
- Do NOT modify `personal_records` DB schema or `PersonalRecord` model
- Do NOT add flash messages for PRs — flash is for ephemeral feedback; PR banners are a dedicated UI element per UX-DR7
- Do NOT re-implement PR detection logic in the route — `detect_prs` is the canonical source
- Do NOT pass the raw `detect_prs` dict (with `exercise_id`) to the template — enrich with names in the route

### Test Specifications for Task 4

All tests go in `gymtrack/tests/test_workouts.py`, using the existing `client`, `app`, `make_user`, `login_as`, `make_exercise`, `make_session`, `make_workout_set`, and `make_completed_session` helpers (already defined in the file).

```python
# ─── Story 5.3 — PR Notification on Post-Workout Summary ───

def test_session_complete_shows_new_pr_banner(client, app):
    """AC 1: completing a session with a new PR → GET /complete shows 🏆 New PR banner."""
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        exercise = make_exercise(_db, name='Deadlift')
        login_as(client, 'user@example.com', 'password123')
        session = make_session(_db, user.id, is_complete=False)
        make_workout_set(_db, session.id, exercise.id, weight_kg=100.0, reps=5)
        # POST to complete — triggers detect_prs (no prior PR → new PR created)
        client.post(
            f'/workouts/sessions/{session.id}/complete',
            data={'submit': 'Complete Workout'},
            follow_redirects=False,
        )
        # GET summary page — should show PR banner
        response = client.get(f'/workouts/sessions/{session.id}/complete')
        assert response.status_code == 200
        assert '🏆 New PR'.encode() in response.data
        assert b'Deadlift' in response.data
        assert b'100.0' in response.data
        assert b'5' in response.data
        assert b'Your best ever' in response.data


def test_session_complete_shows_matched_pr_banner(client, app):
    """AC 2: completing a session that matches existing PR → GET /complete shows 💪 Matched PR banner."""
    from app.models.personal_record import PersonalRecord
    import datetime
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        exercise = make_exercise(_db, name='Squat')
        # Pre-create PR at 80kg
        pr = PersonalRecord(
            user_id=user.id, exercise_id=exercise.id,
            weight_kg=80.0, reps=5, achieved_at=datetime.datetime.utcnow(),
        )
        _db.session.add(pr)
        _db.session.commit()
        login_as(client, 'user@example.com', 'password123')
        session = make_session(_db, user.id, is_complete=False)
        make_workout_set(_db, session.id, exercise.id, weight_kg=80.0, reps=8)
        # POST to complete — matched PR (same weight)
        client.post(
            f'/workouts/sessions/{session.id}/complete',
            data={'submit': 'Complete Workout'},
            follow_redirects=False,
        )
        response = client.get(f'/workouts/sessions/{session.id}/complete')
        assert response.status_code == 200
        assert '💪 Matched PR'.encode() in response.data
        assert b'Squat' in response.data
        assert b'Strength holds' in response.data


def test_session_complete_no_pr_no_banner(client, app):
    """AC 3: completing a session below existing PR → GET /complete has no PR banner element."""
    from app.models.personal_record import PersonalRecord
    import datetime
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        exercise = make_exercise(_db, name='Bench Press')
        # Pre-create PR at 100kg; session set at 70kg → no PR
        pr = PersonalRecord(
            user_id=user.id, exercise_id=exercise.id,
            weight_kg=100.0, reps=5, achieved_at=datetime.datetime.utcnow(),
        )
        _db.session.add(pr)
        _db.session.commit()
        login_as(client, 'user@example.com', 'password123')
        session = make_session(_db, user.id, is_complete=False)
        make_workout_set(_db, session.id, exercise.id, weight_kg=70.0, reps=10)
        client.post(
            f'/workouts/sessions/{session.id}/complete',
            data={'submit': 'Complete Workout'},
            follow_redirects=False,
        )
        response = client.get(f'/workouts/sessions/{session.id}/complete')
        assert response.status_code == 200
        assert b'pr-banner' not in response.data
        assert b'New PR' not in response.data
        assert b'Matched PR' not in response.data
```

### Files to Modify (No New Files, No Migrations)

| File | Change Type | Description |
|------|-------------|-------------|
| `gymtrack/app/blueprints/workouts/routes.py` | UPDATE | Add `session` import; capture and store PR results in POST; pop and pass in GET |
| `gymtrack/app/templates/workouts/session_complete.html` | UPDATE | Add PR banners block above summary section |
| `gymtrack/app/static/css/style.css` | UPDATE | Add `.pr-banner`, `.pr-banner--new`, `.pr-banner--matched` BEM styles |
| `gymtrack/tests/test_workouts.py` | UPDATE | Add 3 integration tests under Story 5.3 section header |

### Project Structure Notes

- Blueprint: `app/blueprints/workouts/` — routes, forms, `__init__.py`
- Template: `app/templates/workouts/session_complete.html` (already exists, 28 lines)
- CSS: `app/static/css/style.css` — single file, BEM naming, vanilla CSS (no preprocessor)
- Test file: `gymtrack/tests/test_workouts.py` — local `app`/`client` fixtures (NOT from `conftest.py`); helpers `make_user`, `login_as`, `make_session`, `make_workout_set`, `make_exercise` are defined at top of file

### Testing Standards

- Integration tests use `client` + `app` fixtures defined locally in `test_workouts.py` (lines 10–22)
- POST to complete with `data={'submit': 'Complete Workout'}` (CompleteSessionForm CSRF disabled in testing config)
- After POST (no `follow_redirects`), GET the summary URL to test banner rendering
- `session` (flask cookie session) is transparent in test client — PRG flow is tested end-to-end as the browser would do it

### References

- [Source: epics.md, Story 5.3 — PR Notification on Post-Workout Summary]
- [Source: epics.md, UX-DR7 — Post-workout summary shows PR banner notification when new/matched PRs detected]
- [Source: architecture.md, Session Storage — Flask client-side cookies (itsdangerous)]
- [Source: architecture.md, Frontend Architecture — BEM CSS naming, `pr-badge` example block in architecture]
- [Source: 5-2-matched-pr-detection.md, Dev Notes — `detect_prs` return contract and `is_new` semantics]
- [Source: gymtrack/app/blueprints/workouts/routes.py, lines 298–347 — POST/GET handlers being modified]
- [Source: gymtrack/app/templates/workouts/session_complete.html — template being extended]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- ✅ AC 1: New PR banner renders with 🏆 icon, exercise name, weight, reps, "Your best ever" — verified by `test_session_complete_shows_new_pr_banner`
- ✅ AC 2: Matched PR banner renders with 💪 icon, exercise name, "Strength holds" — verified by `test_session_complete_shows_matched_pr_banner`
- ✅ AC 3: No `pr-banner` element in DOM when no PRs detected — verified by `test_session_complete_no_pr_no_banner`
- `session` added to flask imports in `routes.py`; no name collision with `workout_session` local variable
- PR enrichment wrapped in existing `try/except` — detection failure still does not block session completion
- Flask cookie session (`session[key]`/`session.pop`) used for PRG boundary transfer
- BEM CSS classes `pr-banner--new` (gold) and `pr-banner--matched` (purple) added to `style.css`
- 3 new tests added; full suite: **126 passed, 0 failed**

### File List

- `gymtrack/app/blueprints/workouts/routes.py` — added `session` import; captured/enriched `detect_prs` result in POST; popped and passed `pr_results` in GET
- `gymtrack/app/templates/workouts/session_complete.html` — added PR banners block above `__summary` section
- `gymtrack/app/static/css/style.css` — added `.pr-banners`, `.pr-banner`, `.pr-banner--new`, `.pr-banner--matched` styles
- `gymtrack/tests/test_workouts.py` — added 3 integration tests for AC 1, 2, 3

### Change Log

- 2026-05-05: Story 5.3 implemented — PR notification banners on post-workout summary (AC 1/2/3 satisfied)
