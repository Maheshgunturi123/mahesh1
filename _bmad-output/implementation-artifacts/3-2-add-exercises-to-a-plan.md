# Story 3.2: Add Exercises to a Plan

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to add exercises to my workout plan with target sets and reps,
so that I have a structured routine to follow.

## Acceptance Criteria

1. **Given** I am on the plan detail page `/workouts/plans/<id>/`
   **When** I add an exercise by selecting from the library and entering target sets and reps
   **Then** a `plan_exercises` row is created: `plan_id`, `exercise_id`, `target_sets`, `target_reps`, `order_index`
   **And** the exercise appears in the plan in the order it was added

2. **Given** I add a second exercise
   **When** it is saved
   **Then** it appears below the first, with `order_index` incremented (next consecutive integer)

3. **Given** I try to access or modify another user's plan via URL manipulation
   **When** the request is made
   **Then** I receive a 404 response (`.filter_by(id=plan_id, user_id=current_user.id).first_or_404()`)

## Tasks / Subtasks

- [ ] Task 1: Create `PlanExercise` model (AC: 1, 2)
  - [ ] Create `gymtrack/app/models/plan_exercise.py` — NEW file
  - [ ] Define `PlanExercise(db.Model)` with `__tablename__ = 'plan_exercises'`
  - [ ] Columns: `id` (Integer, PK), `plan_id` (Integer, FK `workout_plans.id`, `nullable=False`), `exercise_id` (Integer, FK `exercises.id`, `nullable=False`), `target_sets` (Integer, `nullable=False`), `target_reps` (Integer, `nullable=False`), `order_index` (Integer, `nullable=False`)
  - [ ] Add `__repr__` returning `<PlanExercise plan={self.plan_id} exercise={self.exercise_id} order={self.order_index}>`
  - [ ] Import model in `gymtrack/app/models/__init__.py` (UPDATE to add `from app.models.plan_exercise import PlanExercise`)

- [ ] Task 2: Generate and apply database migration (AC: 1)
  - [ ] Run `flask db migrate -m "add plan_exercises table"` from `gymtrack/` directory
  - [ ] Verify generated migration creates `plan_exercises` table with correct columns and foreign keys
  - [ ] Run `flask db upgrade` to apply migration

- [ ] Task 3: Create `AddExerciseForm` in `forms.py` (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/forms.py` — ADD to existing file (do NOT replace `WorkoutPlanForm`)
  - [ ] Import `SelectField`, `IntegerField` from `wtforms`; `DataRequired`, `NumberRange` from `wtforms.validators`
  - [ ] Define `AddExerciseForm(FlaskForm)` with:
    - `exercise_id`: `SelectField('Exercise', coerce=int, validators=[DataRequired()])`
    - `target_sets`: `IntegerField('Target Sets', validators=[DataRequired(), NumberRange(min=1, max=20, message='Sets must be between 1 and 20.')])`
    - `target_reps`: `IntegerField('Target Reps', validators=[DataRequired(), NumberRange(min=1, max=100, message='Reps must be between 1 and 100.')])`
    - `submit`: `SubmitField('Add Exercise')`
  - [ ] Do NOT set `csrf = False` — CSRF is enabled by default via Flask-WTF (this is a POST form)
  - [ ] Note: `exercise_id` choices populated dynamically in the route (not in the form class)

- [ ] Task 4: Update `plan_detail` route and add `add_exercise` route (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/app/blueprints/workouts/routes.py`
  - [ ] Update imports: add `request` from `flask`; `Exercise` from `app.models.exercise`; `PlanExercise` from `app.models.plan_exercise`; `AddExerciseForm` from `forms`
  - [ ] Update existing `plan_detail` view to:
    - Load plan with user isolation: `WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()`
    - Load plan exercises ordered: `PlanExercise.query.filter_by(plan_id=plan.id).order_by(PlanExercise.order_index).all()`
    - Populate `AddExerciseForm` with all exercises: `Exercise.query.order_by(Exercise.name).all()`; set `form.exercise_id.choices = [(e.id, e.name) for e in exercises]`
    - Build a lookup dict: `exercise_map = {e.id: e for e in exercises}` for template use
    - Pass `plan`, `plan_exercises`, `form`, `exercise_map` to template
  - [ ] Add new `add_exercise` route: `POST /workouts/plans/<int:id>/exercises/add` (within `workouts_bp`)
    ```python
    @workouts_bp.route('/plans/<int:id>/exercises/add', methods=['POST'])
    @login_required
    def add_exercise(id):
        plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        exercises = Exercise.query.order_by(Exercise.name).all()
        form = AddExerciseForm()
        form.exercise_id.choices = [(e.id, e.name) for e in exercises]
        if form.validate_on_submit():
            next_order = db.session.query(db.func.count(PlanExercise.id)).filter_by(plan_id=plan.id).scalar()
            pe = PlanExercise(
                plan_id=plan.id,
                exercise_id=form.exercise_id.data,
                target_sets=form.target_sets.data,
                target_reps=form.target_reps.data,
                order_index=next_order
            )
            db.session.add(pe)
            db.session.commit()
            logger.info('Exercise added to plan: user=%d plan_id=%d exercise_id=%d order=%d',
                        current_user.id, plan.id, pe.exercise_id, pe.order_index)
            flash('Exercise added.', 'success')
        return redirect(url_for('workouts.plan_detail', id=plan.id))
    ```
  - [ ] `order_index` uses COUNT of existing rows (0-based): first exercise gets 0, second gets 1, etc.

- [ ] Task 5: Update `plan_detail.html` template (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/templates/workouts/plan_detail.html` — replace the placeholder exercises section
  - [ ] Section 1 — Exercise list:
    - [ ] `<h2>Exercises</h2>` with BEM class `workout-plan-detail__exercises-heading`
    - [ ] If `plan_exercises` is empty: show `<p class="workout-plan-detail__empty">No exercises yet.</p>`
    - [ ] If exercises exist: render ordered list `<ol class="exercise-list">` with each item showing:
      - `{{ exercise_map[pe.exercise_id].name }}` — exercise name (BEM: `exercise-list__name`)
      - `{{ pe.target_sets }} sets × {{ pe.target_reps }} reps` (BEM: `exercise-list__targets`)
  - [ ] Section 2 — Add exercise form:
    - [ ] `<h2>Add Exercise</h2>` with BEM class `workout-plan-detail__add-heading`
    - [ ] `<form method="POST" action="{{ url_for('workouts.add_exercise', id=plan.id) }}">`
    - [ ] `{{ form.hidden_tag() }}` for CSRF — **mandatory**
    - [ ] Labeled `exercise_id` select: `<label for="exercise_id">Exercise</label>` + `{{ form.exercise_id(id="exercise_id") }}`
    - [ ] Labeled `target_sets` input: `<label for="target_sets">Target Sets</label>` + `{{ form.target_sets(id="target_sets", type="number", min=1, max=20) }}`
    - [ ] Labeled `target_reps` input: `<label for="target_reps">Target Reps</label>` + `{{ form.target_reps(id="target_reps", type="number", min=1, max=100) }}`
    - [ ] Show field errors for each field: `{% for error in form.field.errors %}<span class="form-error">{{ error }}</span>{% endfor %}`
    - [ ] Submit button: `{{ form.submit() }}`
  - [ ] Add flash messages display (using base.html flash block if available, otherwise add inline)

- [ ] Task 6: Add CSS for plan exercises section (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/static/css/style.css` — ADD new BEM classes only
  - [ ] Add `.exercise-list` ordered list styles, `.exercise-list__name`, `.exercise-list__targets`
  - [ ] Add `.workout-plan-detail__add-heading`, `.workout-plan-detail__empty`
  - [ ] Touch targets ≥ 44px for all form inputs/buttons (NFR17)
  - [ ] Do NOT create a new CSS file — add only to `style.css`

- [ ] Task 7: Update `tests/test_workouts.py` with story 3.2 test coverage (AC: 1, 2, 3)
  - [ ] UPDATE `gymtrack/tests/test_workouts.py` — ADD new tests (do NOT remove existing tests from Story 3.1)
  - [ ] Add helper: `make_exercise(db, name='Squat', muscle_group='Legs')` — creates and returns an `Exercise`
  - [ ] Test: GET `/workouts/plans/<id>/` shows `AddExerciseForm` — select, sets, reps inputs visible
  - [ ] Test: POST `/workouts/plans/<id>/exercises/add` with valid data → 302 redirect to plan detail; `PlanExercise` row created with correct `plan_id`, `exercise_id`, `target_sets`, `target_reps`, `order_index=0`
  - [ ] Test: add two exercises → second has `order_index=1`; response shows both in order
  - [ ] Test: POST to another user's plan → 404
  - [ ] Test: POST with invalid sets (0) → redirect back to plan detail, no row created (form validation fails)
  - [ ] Test: POST with invalid reps (0) → redirect back to plan detail, no row created

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**`PlanExercise` model — MANDATORY column names and types:**
```python
# gymtrack/app/models/plan_exercise.py — NEW file
from app.extensions import db

class PlanExercise(db.Model):
    __tablename__ = 'plan_exercises'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plans.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    target_sets = db.Column(db.Integer, nullable=False)
    target_reps = db.Column(db.Integer, nullable=False)
    order_index = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<PlanExercise plan={self.plan_id} exercise={self.exercise_id} order={self.order_index}>'
```
- Table name MUST be `plan_exercises` (plural snake_case — architecture naming rule)
- FK references MUST use string table names: `'workout_plans.id'` and `'exercises.id'`
- No `user_id` column on this model — isolation is enforced at the `WorkoutPlan` level
- No `created_at` on this model — not required by epics

**Data isolation — MANDATORY on every plan query:**
```python
# ✅ ALWAYS scope WorkoutPlan to current_user.id
plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()

# PlanExercise rows are child records of WorkoutPlan — isolation is inherited via the plan ownership check above
# Do NOT add user_id filter to PlanExercise queries directly
```

**`order_index` calculation — use COUNT, not MAX:**
```python
# ✅ Correct — works even if previous entries are deleted later (Story 3.3 concern)
next_order = db.session.query(db.func.count(PlanExercise.id)).filter_by(plan_id=plan.id).scalar()

# ❌ Avoid MAX(order_index) — returns None if no rows exist, requires None-check
```
First exercise gets `order_index=0`, second gets `1`, etc.

**`exercises` table is shared (no `user_id`) — do NOT filter by user:**
```python
# ✅ Correct — Exercise is an admin-curated shared library
exercises = Exercise.query.order_by(Exercise.name).all()

# ❌ Wrong — Exercise has no user_id column
exercises = Exercise.query.filter_by(user_id=current_user.id).all()
```
[Source: 2-1-exercise-library-browse.md#Dev Notes]

**`plan_detail` route MUST become GET + maintain all existing behavior:**
- The existing `plan_detail` view only loads the plan — this story ADDS exercises + form loading
- Do NOT change the route URL or function name (`plan_detail`) — other routes already reference `url_for('workouts.plan_detail', id=...)`
- The add-exercise action uses a SEPARATE route `add_exercise` at `/plans/<id>/exercises/add`

**`add_exercise` route accepts POST only:**
```python
@workouts_bp.route('/plans/<int:id>/exercises/add', methods=['POST'])
@login_required
def add_exercise(id):
    ...
    return redirect(url_for('workouts.plan_detail', id=plan.id))
```
On success AND on form validation failure, redirect to `plan_detail`. Do NOT re-render the template from `add_exercise`.

**Flash message category — use ONLY `success` or `error`:**
```python
flash('Exercise added.', 'success')   # ✅ correct
flash('Exercise added.', 'ok')        # ❌ wrong category
```

**CSRF on all POST forms — mandatory:**
```html
<form method="POST" action="{{ url_for('workouts.add_exercise', id=plan.id) }}">
    {{ form.hidden_tag() }}
    ...
</form>
```

**Blueprint routing in `routes.py` only — never in `__init__.py`:**
All route handlers go in `gymtrack/app/blueprints/workouts/routes.py`. The `__init__.py` only holds the blueprint definition.

### Project Structure Notes

**Files to create (NEW):**
- `gymtrack/app/models/plan_exercise.py`
- Migration file in `migrations/versions/` (auto-generated by `flask db migrate`)

**Files to update (UPDATE):**
- `gymtrack/app/models/__init__.py` — add `PlanExercise` import
- `gymtrack/app/blueprints/workouts/forms.py` — add `AddExerciseForm` (keep `WorkoutPlanForm`)
- `gymtrack/app/blueprints/workouts/routes.py` — update `plan_detail`, add `add_exercise`
- `gymtrack/app/templates/workouts/plan_detail.html` — replace placeholder with exercises list + form
- `gymtrack/app/static/css/style.css` — add exercise-list and add-exercise BEM classes
- `gymtrack/tests/test_workouts.py` — add Story 3.2 tests (keep Story 3.1 tests intact)

**Alignment with architecture directory structure:**
```
app/models/plan_exercise.py        ← per-domain model [Source: architecture.md#Code Organization]
app/blueprints/workouts/routes.py  ← all routes in routes.py [Source: architecture.md#Blueprint Internal Structure]
app/blueprints/workouts/forms.py   ← all forms in forms.py [Source: architecture.md#Blueprint Internal Structure]
app/templates/workouts/plan_detail.html ← updated stub [Source: architecture.md#Template File Naming]
tests/test_workouts.py             ← one test file per blueprint [Source: architecture.md#Test Structure]
```

**Epic 3 context — future stories to NOT implement here:**
- Story 3.3 adds edit/reorder/remove exercise functionality — do NOT add edit or delete routes for `PlanExercise`
- Story 3.4 adds plan list and plan delete — do NOT add those routes
- The `order_index` numbering chosen (COUNT-based) is compatible with Story 3.3's reorder requirement

### Previous Story Intelligence (from Story 3.1)

**What Story 3.1 established (ALREADY EXISTS — do not recreate):**
- `WorkoutPlan` model at `gymtrack/app/models/workout_plan.py` with `__tablename__ = 'workout_plans'`
- `workouts_bp = Blueprint('workouts', __name__, url_prefix='/workouts')` already registered in `create_app()`
- `plan_detail` route stub already exists at `GET /workouts/plans/<int:id>/` — UPDATE it, do NOT recreate
- `plan_detail.html` template stub already exists — UPDATE it, do NOT recreate
- `WorkoutPlanForm` already in `gymtrack/app/blueprints/workouts/forms.py` — ADD `AddExerciseForm` to same file
- `gymtrack/tests/test_workouts.py` already has Story 3.1 tests — ADD to it, do NOT delete existing tests
- `strftime` Jinja2 filter already registered in `create_app()` — do NOT add it again

**Pattern from Story 3.1 to follow:**
```python
# Error logging pattern — match this exactly
logger = logging.getLogger(__name__)
logger.info('Exercise added to plan: user=%d plan_id=%d exercise_id=%d order=%d',
            current_user.id, plan.id, pe.exercise_id, pe.order_index)
```

**Test helpers available from Story 3.1 (reuse them):**
```python
# Already in test_workouts.py
def make_user(db, email='user@example.com', password='password123'): ...
def login_as(client, email, password): ...
def make_plan(db, user_id, name='My Plan'): ...
```

### Testing Standards

```python
# gymtrack/tests/test_workouts.py — add to existing file
from app.models.exercise import Exercise
from app.models.plan_exercise import PlanExercise

def make_exercise(db, name='Squat', muscle_group='Legs', description=''):
    exercise = Exercise(name=name, muscle_group=muscle_group, description=description)
    db.session.add(exercise)
    db.session.commit()
    return exercise

def test_add_exercise_creates_plan_exercise_row(client, test_db):
    user = make_user(test_db)
    login_as(client, 'user@example.com', 'password123')
    plan = make_plan(test_db, user.id)
    exercise = make_exercise(test_db)
    response = client.post(
        f'/workouts/plans/{plan.id}/exercises/add',
        data={'exercise_id': exercise.id, 'target_sets': 3, 'target_reps': 10},
        follow_redirects=False
    )
    assert response.status_code == 302
    pe = PlanExercise.query.filter_by(plan_id=plan.id).first()
    assert pe is not None
    assert pe.exercise_id == exercise.id
    assert pe.target_sets == 3
    assert pe.target_reps == 10
    assert pe.order_index == 0

def test_second_exercise_gets_incremented_order_index(client, test_db):
    user = make_user(test_db)
    login_as(client, 'user@example.com', 'password123')
    plan = make_plan(test_db, user.id)
    e1 = make_exercise(test_db, name='Squat')
    e2 = make_exercise(test_db, name='Deadlift')
    client.post(f'/workouts/plans/{plan.id}/exercises/add',
                data={'exercise_id': e1.id, 'target_sets': 3, 'target_reps': 10})
    client.post(f'/workouts/plans/{plan.id}/exercises/add',
                data={'exercise_id': e2.id, 'target_sets': 4, 'target_reps': 8})
    pes = PlanExercise.query.filter_by(plan_id=plan.id).order_by(PlanExercise.order_index).all()
    assert len(pes) == 2
    assert pes[0].order_index == 0
    assert pes[1].order_index == 1

def test_add_exercise_to_other_users_plan_returns_404(client, test_db):
    user_a = make_user(test_db, email='a@example.com')
    user_b = make_user(test_db, email='b@example.com')
    login_as(client, 'b@example.com', 'password123')
    plan_a = make_plan(test_db, user_a.id)
    exercise = make_exercise(test_db)
    response = client.post(
        f'/workouts/plans/{plan_a.id}/exercises/add',
        data={'exercise_id': exercise.id, 'target_sets': 3, 'target_reps': 10}
    )
    assert response.status_code == 404
```

### References

- Story requirements: [Source: epics.md#Story 3.2: Add Exercises to a Plan]
- `PlanExercise` model structure: [Source: epics.md#Story 3.2 — plan_exercises columns]
- `Exercise` model (shared library, no user_id): [Source: 2-1-exercise-library-browse.md#Dev Notes]
- Data isolation pattern: [Source: architecture.md#Multi-User Isolation Pattern]
- Database naming conventions: [Source: architecture.md#Database Naming Conventions]
- Blueprint structure: [Source: architecture.md#Blueprint Internal Structure]
- URL conventions: [Source: architecture.md#URL Conventions]
- Flash message categories: [Source: architecture.md#HTML Page Routes — Flash Messages]
- CSRF requirement: [Source: architecture.md#CSRF Protection]
- Error logging pattern: [Source: 3-1-create-workout-plan.md#Dev Notes]
- Test structure: [Source: architecture.md#Test Structure]
- Previous story patterns: [Source: 3-1-create-workout-plan.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List

- `gymtrack/app/models/plan_exercise.py` — NEW
- `gymtrack/app/models/__init__.py` — UPDATED (add PlanExercise import)
- `gymtrack/app/blueprints/workouts/forms.py` — UPDATED (add AddExerciseForm)
- `gymtrack/app/blueprints/workouts/routes.py` — UPDATED (update plan_detail, add add_exercise)
- `gymtrack/app/templates/workouts/plan_detail.html` — UPDATED (add exercises list + form)
- `gymtrack/app/static/css/style.css` — UPDATED (add exercise-list BEM classes)
- `gymtrack/tests/test_workouts.py` — UPDATED (add Story 3.2 tests)
- `gymtrack/migrations/versions/<hash>_add_plan_exercises_table.py` — NEW (auto-generated)
