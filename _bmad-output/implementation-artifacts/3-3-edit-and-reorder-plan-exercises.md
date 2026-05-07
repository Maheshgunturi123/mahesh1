# Story 3.3: Edit & Reorder Plan Exercises

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to edit my plan by updating, reordering, or removing exercises,
so that I can refine my routine over time.

## Acceptance Criteria

1. **Given** I am editing a plan at `/workouts/plans/<id>/edit`
   **When** I change the target sets or reps for an exercise and save
   **Then** the `plan_exercises` row is updated with the new values
   **And** I see a `success` flash: "Exercise updated."

2. **Given** I remove an exercise from the plan
   **When** the removal is confirmed (POST submit)
   **Then** the `plan_exercises` row is deleted and the exercise no longer appears in the plan
   **And** I see a `success` flash: "Exercise removed."

3. **Given** I reorder exercises using up/down controls
   **When** the order change is saved
   **Then** `order_index` values are swapped and exercises render in the new order

4. **Given** I try to edit, remove, or move an exercise on another user's plan via URL manipulation
   **When** the request is made
   **Then** I receive a 404 response (isolation enforced via `WorkoutPlan.filter_by(id, user_id)`)

## Tasks / Subtasks

- [ ] Task 1: Add `EditExerciseForm`, `RemoveExerciseForm`, and `MoveExerciseForm` to `forms.py` (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/forms.py` — ADD to existing file (do NOT replace `WorkoutPlanForm` or `AddExerciseForm`)
  - [ ] Import `HiddenField` from `wtforms` (add to existing import line)
  - [ ] Define `EditExerciseForm(FlaskForm)`:
    - `target_sets`: `IntegerField('Target Sets', validators=[DataRequired(), NumberRange(min=1, max=20, message='Sets must be between 1 and 20.')])`
    - `target_reps`: `IntegerField('Target Reps', validators=[DataRequired(), NumberRange(min=1, max=100, message='Reps must be between 1 and 100.')])`
    - `submit`: `SubmitField('Save')`
  - [ ] Define `RemoveExerciseForm(FlaskForm)`: no fields — used only for CSRF validation on remove POST
  - [ ] Define `MoveExerciseForm(FlaskForm)`: no fields — used only for CSRF validation on move POST (direction read from `request.form`)

- [ ] Task 2: Add `plan_edit`, `update_exercise`, `remove_exercise`, `move_exercise` routes to `routes.py` (AC: 1, 2, 3, 4)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Update imports: add `EditExerciseForm, MoveExerciseForm, RemoveExerciseForm` to forms import line
  - [ ] Add `plan_edit` view:
    ```python
    @workouts_bp.route('/plans/<int:id>/edit')
    @login_required
    def plan_edit(id):
        plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        plan_exercises = PlanExercise.query.filter_by(plan_id=plan.id).order_by(PlanExercise.order_index).all()
        exercises = Exercise.query.order_by(Exercise.name).all()
        exercise_map = {e.id: e for e in exercises}
        edit_forms = {pe.id: EditExerciseForm(obj=pe, prefix=f'pe-{pe.id}') for pe in plan_exercises}
        action_form = RemoveExerciseForm()
        return render_template('workouts/plan_edit.html', plan=plan,
                               plan_exercises=plan_exercises, exercise_map=exercise_map,
                               edit_forms=edit_forms, action_form=action_form)
    ```
    - `EditExerciseForm(obj=pe, prefix=f'pe-{pe.id}')` pre-populates each form with the existing values and uses a unique prefix to avoid field name collisions in the page HTML
    - `action_form = RemoveExerciseForm()` is one shared instance — reused for remove and move button forms (session-based CSRF token is the same)

  - [ ] Add `update_exercise` route:
    ```python
    @workouts_bp.route('/plans/<int:id>/exercises/<int:pe_id>/update', methods=['POST'])
    @login_required
    def update_exercise(id, pe_id):
        plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        pe = PlanExercise.query.filter_by(id=pe_id, plan_id=plan.id).first_or_404()
        form = EditExerciseForm(prefix=f'pe-{pe.id}')
        if form.validate_on_submit():
            pe.target_sets = form.target_sets.data
            pe.target_reps = form.target_reps.data
            db.session.commit()
            logger.info('Plan exercise updated: user=%d plan_id=%d pe_id=%d sets=%d reps=%d',
                        current_user.id, plan.id, pe.id, pe.target_sets, pe.target_reps)
            flash('Exercise updated.', 'success')
        return redirect(url_for('workouts.plan_edit', id=plan.id))
    ```
    - `prefix=f'pe-{pe.id}'` MUST match the prefix used in `plan_edit` so field names align with posted form data

  - [ ] Add `remove_exercise` route:
    ```python
    @workouts_bp.route('/plans/<int:id>/exercises/<int:pe_id>/remove', methods=['POST'])
    @login_required
    def remove_exercise(id, pe_id):
        plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        pe = PlanExercise.query.filter_by(id=pe_id, plan_id=plan.id).first_or_404()
        form = RemoveExerciseForm()
        if form.validate_on_submit():
            db.session.delete(pe)
            db.session.commit()
            logger.info('Exercise removed from plan: user=%d plan_id=%d pe_id=%d',
                        current_user.id, plan.id, pe_id)
            flash('Exercise removed.', 'success')
        return redirect(url_for('workouts.plan_edit', id=plan.id))
    ```

  - [ ] Add `move_exercise` route:
    ```python
    @workouts_bp.route('/plans/<int:id>/exercises/<int:pe_id>/move', methods=['POST'])
    @login_required
    def move_exercise(id, pe_id):
        plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        pe = PlanExercise.query.filter_by(id=pe_id, plan_id=plan.id).first_or_404()
        form = MoveExerciseForm()
        if form.validate_on_submit():
            direction = request.form.get('direction')
            if direction == 'up':
                neighbour = PlanExercise.query.filter_by(
                    plan_id=plan.id, order_index=pe.order_index - 1).first()
            elif direction == 'down':
                neighbour = PlanExercise.query.filter_by(
                    plan_id=plan.id, order_index=pe.order_index + 1).first()
            else:
                neighbour = None
            if neighbour:
                pe.order_index, neighbour.order_index = neighbour.order_index, pe.order_index
                db.session.commit()
                logger.info('Exercise moved: user=%d plan_id=%d pe_id=%d direction=%s',
                            current_user.id, plan.id, pe.id, direction)
        return redirect(url_for('workouts.plan_edit', id=plan.id))
    ```
    - If `direction` is not 'up' or 'down', or no neighbour exists (already at boundary), silently redirect with no change

- [ ] Task 3: Create `plan_edit.html` template (AC: 1, 2, 3)
  - [ ] CREATE `gymtrack/app/templates/workouts/plan_edit.html` — NEW file
  - [ ] Extend `base.html`; block title: `Edit {{ plan.name }} — GymTrack`
  - [ ] `<h1 class="plan-edit__heading">Edit {{ plan.name }}</h1>`
  - [ ] If `plan_exercises` is empty: show `<p class="plan-edit__empty">No exercises to edit. <a href="{{ url_for('workouts.plan_detail', id=plan.id) }}">Add exercises first.</a></p>`
  - [ ] For each exercise — render an exercise row `<div class="plan-edit__exercise">`:
    - Exercise name heading: `<span class="plan-edit__exercise-name">{{ exercise_map[pe.exercise_id].name }}</span>`
    - **Edit form** (sets/reps update):
      ```html
      <form class="plan-edit__update-form" method="POST"
            action="{{ url_for('workouts.update_exercise', id=plan.id, pe_id=pe.id) }}">
        {{ edit_forms[pe.id].hidden_tag() }}
        <label for="{{ edit_forms[pe.id].target_sets.id }}">Sets</label>
        {{ edit_forms[pe.id].target_sets(type="number", min=1, max=20) }}
        {% for error in edit_forms[pe.id].target_sets.errors %}
          <span class="form-error">{{ error }}</span>
        {% endfor %}
        <label for="{{ edit_forms[pe.id].target_reps.id }}">Reps</label>
        {{ edit_forms[pe.id].target_reps(type="number", min=1, max=100) }}
        {% for error in edit_forms[pe.id].target_reps.errors %}
          <span class="form-error">{{ error }}</span>
        {% endfor %}
        {{ edit_forms[pe.id].submit(class="btn btn--primary") }}
      </form>
      ```
    - **Remove form**: one button, POST to `remove_exercise`, uses `action_form.hidden_tag()` for CSRF:
      ```html
      <form class="plan-edit__remove-form" method="POST"
            action="{{ url_for('workouts.remove_exercise', id=plan.id, pe_id=pe.id) }}">
        {{ action_form.hidden_tag() }}
        <button type="submit" class="btn btn--danger plan-edit__remove-btn">Remove</button>
      </form>
      ```
    - **Move Up form** (show only if `not loop.first`):
      ```html
      {% if not loop.first %}
      <form class="plan-edit__move-form" method="POST"
            action="{{ url_for('workouts.move_exercise', id=plan.id, pe_id=pe.id) }}">
        {{ action_form.hidden_tag() }}
        <input type="hidden" name="direction" value="up">
        <button type="submit" class="btn btn--icon plan-edit__move-btn"
                aria-label="Move {{ exercise_map[pe.exercise_id].name }} up">&#8593;</button>
      </form>
      {% endif %}
      ```
    - **Move Down form** (show only if `not loop.last`):
      ```html
      {% if not loop.last %}
      <form class="plan-edit__move-form" method="POST"
            action="{{ url_for('workouts.move_exercise', id=plan.id, pe_id=pe.id) }}">
        {{ action_form.hidden_tag() }}
        <input type="hidden" name="direction" value="down">
        <button type="submit" class="btn btn--icon plan-edit__move-btn"
                aria-label="Move {{ exercise_map[pe.exercise_id].name }} down">&#8595;</button>
      </form>
      {% endif %}
      ```
  - [ ] Footer links:
    ```html
    <div class="plan-edit__actions">
      <a class="plan-edit__back" href="{{ url_for('workouts.plan_detail', id=plan.id) }}">&larr; Back to plan</a>
    </div>
    ```
  - [ ] CSRF note: `action_form.hidden_tag()` is reused across multiple forms — this is intentional and correct because Flask-WTF's CSRF token is session-scoped (same value per request)

- [ ] Task 4: Update `plan_detail.html` to add Edit Plan link (AC: 1)
  - [ ] UPDATE `gymtrack/app/templates/workouts/plan_detail.html`
  - [ ] Replace the existing `<a class="workout-plan-detail__back" href="#">&larr; Back to plans</a>` with:
    ```html
    <a class="workout-plan-detail__edit-link btn btn--secondary"
       href="{{ url_for('workouts.plan_edit', id=plan.id) }}">Edit Plan</a>
    <a class="workout-plan-detail__back" href="#">&larr; Back to plans</a>
    ```
  - [ ] Do NOT remove or change any other existing content in `plan_detail.html`

- [ ] Task 5: Add BEM CSS classes for plan-edit page to `style.css` (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/static/css/style.css` — ADD new BEM classes only
  - [ ] Add `.plan-edit` container, `.plan-edit__heading`, `.plan-edit__empty`
  - [ ] Add `.plan-edit__exercise` row (flex layout: name, forms, action buttons)
  - [ ] Add `.plan-edit__exercise-name`, `.plan-edit__update-form`, `.plan-edit__remove-form`, `.plan-edit__move-form`
  - [ ] Add `.plan-edit__remove-btn` (danger/destructive button styling), `.plan-edit__move-btn` (icon button)
  - [ ] Add `.plan-edit__actions` footer, `.plan-edit__back`
  - [ ] Touch targets ≥ 44px for all buttons (NFR17)
  - [ ] Do NOT create a new CSS file — add only to `style.css`

- [ ] Task 6: Add Story 3.3 tests to `test_workouts.py` (AC: 1, 2, 3, 4)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py` — ADD new tests (do NOT remove any existing tests from Stories 3.1/3.2)
  - [ ] Helper to add a plan exercise directly (reuse `make_exercise` and `make_plan` already in file):
    ```python
    def make_plan_exercise(db, plan_id, exercise_id, sets=3, reps=10, order_index=0):
        pe = PlanExercise(plan_id=plan_id, exercise_id=exercise_id,
                          target_sets=sets, target_reps=reps, order_index=order_index)
        db.session.add(pe)
        db.session.commit()
        return pe
    ```
  - [ ] Test: GET `/workouts/plans/<id>/edit` → 200, exercise names and set/rep values shown
  - [ ] Test: GET edit page for another user's plan → 404 (data isolation)
  - [ ] Test: POST `update_exercise` with valid sets/reps → 302 redirect; `PlanExercise` row updated
  - [ ] Test: POST `update_exercise` with invalid sets (0) → redirect; row NOT updated (validation prevents it)
  - [ ] Test: POST `update_exercise` on another user's plan → 404
  - [ ] Test: POST `remove_exercise` → 302 redirect; `PlanExercise` row deleted from DB
  - [ ] Test: POST `remove_exercise` on another user's plan → 404
  - [ ] Test: POST `move_exercise` with `direction=down` → 302 redirect; `order_index` values swapped between exercise and its lower neighbour
  - [ ] Test: POST `move_exercise` with `direction=up` → 302 redirect; `order_index` values swapped between exercise and its upper neighbour
  - [ ] Test: POST `move_exercise` on first exercise with `direction=up` → 302 redirect; `order_index` unchanged (no upper neighbour)
  - [ ] Test: POST `move_exercise` on last exercise with `direction=down` → 302 redirect; `order_index` unchanged (no lower neighbour)

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**Data isolation — MANDATORY on every plan and plan_exercise query:**
```python
# ✅ Always scope WorkoutPlan to current_user.id first
plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()

# ✅ Then scope PlanExercise to plan.id (inherited isolation — plan already user-scoped)
pe = PlanExercise.query.filter_by(id=pe_id, plan_id=plan.id).first_or_404()

# ❌ Never query PlanExercise without going through WorkoutPlan isolation
pe = PlanExercise.query.get(pe_id)  # vulnerable
```

**`EditExerciseForm` prefix — MUST be consistent between `plan_edit` and `update_exercise`:**
```python
# plan_edit view (GET) — pre-populate with obj=pe
edit_forms = {pe.id: EditExerciseForm(obj=pe, prefix=f'pe-{pe.id}') for pe in plan_exercises}

# update_exercise view (POST) — same prefix so field names match posted data
form = EditExerciseForm(prefix=f'pe-{pe.id}')  # reads request.form['pe-42-target_sets'] etc.
```
The prefix generates field name attributes like `pe-42-target_sets` instead of `target_sets`. Without a matching prefix, `form.validate_on_submit()` will always fail because the posted field names won't match.

**`action_form.hidden_tag()` reuse is safe and intentional:**
```python
# plan_edit view
action_form = RemoveExerciseForm()  # one instance, shared across all remove/move button forms in template

# Flask-WTF CSRF tokens are session-scoped — all instances produce the same valid token
# Reusing one form instance for multiple <form> blocks in the template is correct here
```

**Swap `order_index` atomically — never set to a temporary value:**
```python
# ✅ Pythonic tuple swap — SQLAlchemy tracks both changes in one commit
pe.order_index, neighbour.order_index = neighbour.order_index, pe.order_index
db.session.commit()

# ❌ Don't use a temp variable and two commits — could corrupt order if interrupted
```

**`RemoveExerciseForm` and `MoveExerciseForm` have no fields — validate CSRF only:**
```python
class RemoveExerciseForm(FlaskForm):
    pass  # no fields needed; validate_on_submit() checks CSRF only

class MoveExerciseForm(FlaskForm):
    pass  # direction is read from request.form.get('direction') after CSRF validation
```

**Move direction — read from `request.form` AFTER CSRF validation via `validate_on_submit()`:**
```python
if form.validate_on_submit():  # CSRF check
    direction = request.form.get('direction')  # safe to read raw form data after CSRF passes
```

**Blueprint routing in `routes.py` only — never in `__init__.py`.**

**Flash message categories — ONLY `success` or `error`:**
```python
flash('Exercise updated.', 'success')   # ✅
flash('Exercise removed.', 'success')   # ✅
```

**CSRF on ALL POST forms — mandatory:**
```html
<!-- edit form uses edit_forms[pe.id].hidden_tag() -->
<!-- remove/move forms use action_form.hidden_tag() -->
<!-- Both are valid — session-based token is the same -->
```

**New URL endpoints (follow existing `/workouts/plans/<id>/` pattern):**
```
GET  /workouts/plans/<int:id>/edit                               → plan_edit
POST /workouts/plans/<int:id>/exercises/<int:pe_id>/update       → update_exercise
POST /workouts/plans/<int:id>/exercises/<int:pe_id>/remove       → remove_exercise
POST /workouts/plans/<int:id>/exercises/<int:pe_id>/move         → move_exercise
```

**`HiddenField` import — needed for completeness but not strictly required since `RemoveExerciseForm` and `MoveExerciseForm` have no fields. Only add to the import if actually used.**

### Project Structure Notes

**Files to create (NEW):**
- `gymtrack/app/templates/workouts/plan_edit.html` — NEW edit-page template

**Files to update (UPDATE):**
- `gymtrack/app/blueprints/workouts/forms.py` — ADD `EditExerciseForm`, `RemoveExerciseForm`, `MoveExerciseForm`
- `gymtrack/app/blueprints/workouts/routes.py` — ADD `plan_edit`, `update_exercise`, `remove_exercise`, `move_exercise`
- `gymtrack/app/templates/workouts/plan_detail.html` — ADD "Edit Plan" link button in actions div
- `gymtrack/app/static/css/style.css` — ADD plan-edit BEM classes
- `gymtrack/tests/test_workouts.py` — ADD Story 3.3 tests (keep all existing tests)

**Alignment with architecture directory structure:**
```
app/blueprints/workouts/routes.py   ← all routes in routes.py [Source: architecture.md#Blueprint Internal Structure]
app/blueprints/workouts/forms.py    ← all forms in forms.py [Source: architecture.md#Blueprint Internal Structure]
app/templates/workouts/plan_edit.html ← snake_case matching view function name [Source: architecture.md#Template File Naming]
tests/test_workouts.py              ← one test file per blueprint [Source: architecture.md#Test Structure]
```

**No new DB model or migration needed:**
This story modifies and deletes existing `plan_exercises` rows — no schema change required.

**`plan_edit.html` is a NEW template — do NOT modify or replace `plan_detail.html` contents (other than adding the edit link):**
- `plan_detail.html` → view/add exercises (existing, Story 3.1/3.2)
- `plan_edit.html` → edit/reorder/remove exercises (new, Story 3.3)

### Previous Story Intelligence (from Story 3.2)

**What Story 3.2 established (ALREADY EXISTS — do not recreate):**
- `PlanExercise` model at `gymtrack/app/models/plan_exercise.py` with columns: `id`, `plan_id`, `exercise_id`, `target_sets`, `target_reps`, `order_index`
- `plan_detail` route at `GET /workouts/plans/<int:id>/` — fully implemented with exercises list + AddExerciseForm
- `add_exercise` route at `POST /workouts/plans/<int:id>/exercises/add`
- `AddExerciseForm` and `WorkoutPlanForm` in `forms.py` — ADD to same file, do NOT replace
- `plan_detail.html` template fully renders exercises and add-exercise form — only ADD the edit-plan link
- `exercise_map` dict pattern (`{e.id: e for e in exercises}`) — reuse exact same pattern in `plan_edit`
- `make_user`, `login_as`, `make_plan`, `make_exercise` helpers in `test_workouts.py` — reuse all
- `logger = logging.getLogger(__name__)` already at top of `routes.py` — do NOT re-declare

**Count-based `order_index` from Story 3.2:**
- `order_index` is 0-based (0, 1, 2, ...)
- After a remove, indices may have a gap (e.g., 0, 2 if index 1 was deleted) — this is acceptable
- Move swap works correctly on any integer values (not just contiguous), as long as swapping with the exact neighbour
- Do NOT re-normalize indices after remove — leave gaps as-is (Story 3.3 only swaps, never renumbers)

**Pattern from `routes.py` to follow (error logging):**
```python
logger = logging.getLogger(__name__)  # already declared in routes.py — do NOT add again
logger.info('Plan exercise updated: user=%d plan_id=%d pe_id=%d sets=%d reps=%d',
            current_user.id, plan.id, pe.id, pe.target_sets, pe.target_reps)
```

**Test file pattern to follow (wrap in `with app.app_context()`):**
```python
def test_update_exercise_updates_row(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan.id, exercise.id, sets=3, reps=10)
        response = client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe.id}/update',
            data={f'pe-{pe.id}-target_sets': 5, f'pe-{pe.id}-target_reps': 12},
            follow_redirects=False,
        )
        assert response.status_code == 302
        updated = PlanExercise.query.get(pe.id)
        assert updated.target_sets == 5
        assert updated.target_reps == 12
```
Note the prefixed field names `pe-{pe.id}-target_sets` in test POST data — they must match the `prefix=f'pe-{pe.id}'` used in the form.

### Testing Standards

```python
# Full set of tests to add to gymtrack/tests/test_workouts.py

def make_plan_exercise(db, plan_id, exercise_id, sets=3, reps=10, order_index=0):
    pe = PlanExercise(plan_id=plan_id, exercise_id=exercise_id,
                      target_sets=sets, target_reps=reps, order_index=order_index)
    db.session.add(pe)
    db.session.commit()
    return pe


# Story 3.3 — AC 1: GET /workouts/plans/<id>/edit → 200, shows exercise names and inputs
def test_plan_edit_get_authenticated(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        exercise = make_exercise(_db, name='Bench Press')
        make_plan_exercise(_db, plan.id, exercise.id, sets=3, reps=8)
        response = client.get(f'/workouts/plans/{plan.id}/edit')
        assert response.status_code == 200
        assert b'Bench Press' in response.data
        assert b'target_sets' in response.data
        assert b'target_reps' in response.data


# Story 3.3 — AC 4: GET edit page for another user's plan → 404
def test_plan_edit_isolation(client, app):
    with app.app_context():
        _db.create_all()
        user_a = make_user(_db, email='a@example.com')
        user_b = make_user(_db, email='b@example.com')
        plan_b = make_plan(_db, user_b.id)
        login_as(client, 'a@example.com', 'password123')
        response = client.get(f'/workouts/plans/{plan_b.id}/edit')
        assert response.status_code == 404


# Story 3.3 — AC 1: POST update_exercise with valid data → 302, row updated
def test_update_exercise_updates_row(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan.id, exercise.id, sets=3, reps=10)
        response = client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe.id}/update',
            data={f'pe-{pe.id}-target_sets': 5, f'pe-{pe.id}-target_reps': 12},
            follow_redirects=False,
        )
        assert response.status_code == 302
        updated = PlanExercise.query.get(pe.id)
        assert updated.target_sets == 5
        assert updated.target_reps == 12


# Story 3.3 — AC 1: POST update_exercise with invalid sets → redirect, row NOT changed
def test_update_exercise_invalid_sets_not_saved(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan.id, exercise.id, sets=3, reps=10)
        client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe.id}/update',
            data={f'pe-{pe.id}-target_sets': 0, f'pe-{pe.id}-target_reps': 10},
        )
        unchanged = PlanExercise.query.get(pe.id)
        assert unchanged.target_sets == 3  # unchanged


# Story 3.3 — AC 4: POST update_exercise on another user's plan → 404
def test_update_exercise_isolation(client, app):
    with app.app_context():
        _db.create_all()
        user_a = make_user(_db, email='a@example.com')
        user_b = make_user(_db, email='b@example.com')
        plan_b = make_plan(_db, user_b.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan_b.id, exercise.id)
        login_as(client, 'a@example.com', 'password123')
        response = client.post(
            f'/workouts/plans/{plan_b.id}/exercises/{pe.id}/update',
            data={f'pe-{pe.id}-target_sets': 5, f'pe-{pe.id}-target_reps': 8},
        )
        assert response.status_code == 404


# Story 3.3 — AC 2: POST remove_exercise → 302, row deleted
def test_remove_exercise_deletes_row(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan.id, exercise.id)
        pe_id = pe.id
        response = client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe_id}/remove',
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert PlanExercise.query.get(pe_id) is None


# Story 3.3 — AC 4: POST remove_exercise on another user's plan → 404
def test_remove_exercise_isolation(client, app):
    with app.app_context():
        _db.create_all()
        user_a = make_user(_db, email='a@example.com')
        user_b = make_user(_db, email='b@example.com')
        plan_b = make_plan(_db, user_b.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan_b.id, exercise.id)
        login_as(client, 'a@example.com', 'password123')
        response = client.post(
            f'/workouts/plans/{plan_b.id}/exercises/{pe.id}/remove',
        )
        assert response.status_code == 404


# Story 3.3 — AC 3: POST move_exercise direction=down → order_index swapped
def test_move_exercise_down_swaps_order_index(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        e1 = make_exercise(_db, name='Squat')
        e2 = make_exercise(_db, name='Deadlift')
        pe1 = make_plan_exercise(_db, plan.id, e1.id, order_index=0)
        pe2 = make_plan_exercise(_db, plan.id, e2.id, order_index=1)
        response = client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe1.id}/move',
            data={'direction': 'down'},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert PlanExercise.query.get(pe1.id).order_index == 1
        assert PlanExercise.query.get(pe2.id).order_index == 0


# Story 3.3 — AC 3: POST move_exercise direction=up → order_index swapped
def test_move_exercise_up_swaps_order_index(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        e1 = make_exercise(_db, name='Squat')
        e2 = make_exercise(_db, name='Deadlift')
        pe1 = make_plan_exercise(_db, plan.id, e1.id, order_index=0)
        pe2 = make_plan_exercise(_db, plan.id, e2.id, order_index=1)
        response = client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe2.id}/move',
            data={'direction': 'up'},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert PlanExercise.query.get(pe2.id).order_index == 0
        assert PlanExercise.query.get(pe1.id).order_index == 1


# Story 3.3 — AC 3: move first exercise up → no change (boundary guard)
def test_move_first_exercise_up_is_noop(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        exercise = make_exercise(_db)
        pe = make_plan_exercise(_db, plan.id, exercise.id, order_index=0)
        client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe.id}/move',
            data={'direction': 'up'},
        )
        assert PlanExercise.query.get(pe.id).order_index == 0  # unchanged


# Story 3.3 — AC 3: move last exercise down → no change (boundary guard)
def test_move_last_exercise_down_is_noop(client, app):
    with app.app_context():
        _db.create_all()
        user = make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        plan = make_plan(_db, user.id)
        e1 = make_exercise(_db, name='Squat')
        e2 = make_exercise(_db, name='Deadlift')
        pe1 = make_plan_exercise(_db, plan.id, e1.id, order_index=0)
        pe2 = make_plan_exercise(_db, plan.id, e2.id, order_index=1)
        client.post(
            f'/workouts/plans/{plan.id}/exercises/{pe2.id}/move',
            data={'direction': 'down'},
        )
        assert PlanExercise.query.get(pe2.id).order_index == 1  # unchanged
```

### References

- Story requirements: [Source: epics.md#Story 3.3: Edit & Reorder Plan Exercises]
- `PlanExercise` model structure: [Source: 3-2-add-exercises-to-a-plan.md#Critical Architecture Requirements]
- Data isolation pattern: [Source: architecture.md#Multi-User Isolation Pattern]
- Blueprint structure: [Source: architecture.md#Blueprint Internal Structure]
- URL conventions: [Source: architecture.md#URL Conventions]
- Flash message categories: [Source: architecture.md#HTML Page Routes — Flash Messages]
- CSRF requirement: [Source: architecture.md#CSRF Protection]
- Error logging pattern: [Source: 3-1-create-workout-plan.md#Dev Notes]
- BEM CSS naming: [Source: architecture.md#CSS Class Naming]
- Template file naming: [Source: architecture.md#Template File Naming]
- Test structure: [Source: architecture.md#Test Structure]
- Previous story patterns: [Source: 3-2-add-exercises-to-a-plan.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List

- `gymtrack/app/templates/workouts/plan_edit.html` — NEW
- `gymtrack/app/blueprints/workouts/forms.py` — UPDATED (add EditExerciseForm, RemoveExerciseForm, MoveExerciseForm)
- `gymtrack/app/blueprints/workouts/routes.py` — UPDATED (add plan_edit, update_exercise, remove_exercise, move_exercise)
- `gymtrack/app/templates/workouts/plan_detail.html` — UPDATED (add Edit Plan link)
- `gymtrack/app/static/css/style.css` — UPDATED (add plan-edit BEM classes)
- `gymtrack/tests/test_workouts.py` — UPDATED (add Story 3.3 tests)
