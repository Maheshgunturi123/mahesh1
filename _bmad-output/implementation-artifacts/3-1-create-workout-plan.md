# Story 3.1: Create Workout Plan

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to create a named workout plan,
so that I have a reusable routine to follow at the gym.

## Acceptance Criteria

1. **Given** I am on `/workouts/plans/new`
   **When** I submit a valid plan name
   **Then** a new `workout_plans` row is created with `user_id=current_user.id`, `name`, `created_at`
   **And** I am redirected to the plan detail page with a `success` flash: "Plan created."
   **And** the plan is only visible to me — no other user can access it

2. **Given** I submit a blank plan name
   **When** the form is submitted
   **Then** I see a field-level error: "Plan name is required."
   **And** no record is created

## Tasks / Subtasks

- [ ] Task 1: Create `WorkoutPlan` model (AC: 1)
  - [ ] Create `gymtrack/app/models/workout_plan.py` — NEW file
  - [ ] Define `WorkoutPlan(db.Model)` with `__tablename__ = 'workout_plans'`
  - [ ] Columns: `id` (Integer, PK), `user_id` (Integer, FK `users.id`, `nullable=False`), `name` (String 200, `nullable=False`), `created_at` (DateTime, default `datetime.utcnow`)
  - [ ] Add `__repr__` returning `<WorkoutPlan {self.id}: {self.name}>`
  - [ ] Import model in `gymtrack/app/models/__init__.py` (UPDATE to add import)

- [ ] Task 2: Generate and apply database migration (AC: 1)
  - [ ] Run `flask db migrate -m "add workout_plans table"` to generate migration file in `migrations/`
  - [ ] Run `flask db upgrade` to apply the migration
  - [ ] Verify `workout_plans` table exists with correct columns in dev SQLite DB

- [ ] Task 3: Create `WorkoutPlanForm` in `forms.py` (AC: 1, 2)
  - [ ] Create `gymtrack/app/blueprints/workouts/forms.py` — NEW file (check if exists first; if the workouts blueprint already has `forms.py`, ADD to it; do NOT replace)
  - [ ] Import `FlaskForm` from `flask_wtf`, `StringField`, `SubmitField` from `wtforms`, `DataRequired`, `Length` from `wtforms.validators`
  - [ ] Define `WorkoutPlanForm(FlaskForm)` with:
    - `name`: `StringField('Plan Name', validators=[DataRequired(message='Plan name is required.'), Length(max=200)])`
    - `submit`: `SubmitField('Create Plan')`
  - [ ] Do NOT set `csrf = False` — CSRF is enabled by default via Flask-WTF

- [ ] Task 4: Create workouts blueprint with plan routes (AC: 1, 2)
  - [ ] **Check if `gymtrack/app/blueprints/workouts/` already exists** — if yes, update `routes.py`; if not, create the full blueprint structure
  - [ ] Ensure `gymtrack/app/blueprints/workouts/__init__.py` defines `workouts_bp = Blueprint('workouts', __name__, url_prefix='/workouts')`
  - [ ] UPDATE (or CREATE) `gymtrack/app/blueprints/workouts/routes.py`:
    - [ ] Imports: `logging`, `flash`, `redirect`, `render_template`, `url_for` from `flask`; `login_required`, `current_user` from `flask_login`; `workouts_bp` from `__init__`; `WorkoutPlanForm` from `forms`; `db` from `app.extensions`; `WorkoutPlan` from `app.models.workout_plan`; `datetime` from `datetime`
    - [ ] Add `logger = logging.getLogger(__name__)`
    - [ ] Route `GET /workouts/plans/new` and `POST /workouts/plans/new`:
      ```python
      @workouts_bp.route('/plans/new', methods=['GET', 'POST'])
      @login_required
      def new_plan():
          form = WorkoutPlanForm()
          if form.validate_on_submit():
              plan = WorkoutPlan(
                  user_id=current_user.id,
                  name=form.name.data.strip(),
                  created_at=datetime.utcnow()
              )
              db.session.add(plan)
              db.session.commit()
              logger.info('Workout plan created: user=%d plan_id=%d name=%s',
                          current_user.id, plan.id, plan.name)
              flash('Plan created.', 'success')
              return redirect(url_for('workouts.plan_detail', id=plan.id))
          return render_template('workouts/plan_form.html', form=form)

      @workouts_bp.route('/plans/<int:id>/')
      @login_required
      def plan_detail(id):
          plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
          return render_template('workouts/plan_detail.html', plan=plan)
      ```

- [ ] Task 5: Register workouts blueprint in `create_app()` (AC: 1)
  - [ ] UPDATE `gymtrack/app/__init__.py`
  - [ ] Import `workouts_bp` from `app.blueprints.workouts`
  - [ ] Register with `app.register_blueprint(workouts_bp)` — check if already registered and skip if so

- [ ] Task 6: Create Jinja2 templates (AC: 1, 2)
  - [ ] Create directory `gymtrack/app/templates/workouts/` if it does not exist
  - [ ] Create `gymtrack/app/templates/workouts/plan_form.html` — NEW template:
    - [ ] `{% extends 'base.html' %}` — uses site-wide base template
    - [ ] BEM block class `workout-plan-form`
    - [ ] Page title and `<h1>`: "Create Workout Plan"
    - [ ] `{{ form.hidden_tag() }}` for CSRF protection — **mandatory**
    - [ ] Render `form.name` field with `<label>` linked to input via `for`/`id` attributes (WCAG 2.1 AA / NFR17–19)
    - [ ] Show field-level errors: `{% for error in form.name.errors %}<span class="form-error">{{ error }}</span>{% endfor %}`
    - [ ] Submit button and "Cancel" link back to plans list `url_for('workouts.plan_list')`
  - [ ] Create `gymtrack/app/templates/workouts/plan_detail.html` — NEW template:
    - [ ] `{% extends 'base.html' %}`
    - [ ] BEM block class `workout-plan-detail`
    - [ ] Display `{{ plan.name }}` as page heading
    - [ ] Display `{{ plan.created_at | strftime('%b %d, %Y') }}` (use the existing Jinja2 `strftime` filter from base)
    - [ ] Placeholder section for exercises (empty state: "No exercises yet. Add exercises in the next step.")
    - [ ] Back link to `url_for('workouts.plan_list')`

- [ ] Task 7: Add CSS for workout plan pages (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/static/css/style.css` — ADD workout plan BEM blocks
  - [ ] Add `.workout-plan-form` block and `.workout-plan-detail` block styles
  - [ ] Touch targets ≥ 44px for all buttons/links (NFR17 / mobile-first)
  - [ ] Do NOT create a new CSS file — add only to the existing `style.css`

- [ ] Task 8: Create `tests/test_workouts.py` with story 3.1 test coverage (AC: 1, 2)
  - [ ] Create `gymtrack/tests/test_workouts.py` — NEW file (or extend if it exists)
  - [ ] Helpers:
    - `make_user(db)` — creates `User(email='user@example.com', password_hash=...)`, returns user
    - `login_as(client, email, password)` — POSTs to `/auth/login`, returns response
    - `make_plan(db, user_id, name='My Plan')` — creates and returns a `WorkoutPlan`
  - [ ] Test: unauthenticated GET `/workouts/plans/new` → 302 redirect to `/auth/login`
  - [ ] Test: authenticated GET `/workouts/plans/new` → 200, contains "Create Workout Plan" and `name` field
  - [ ] Test: authenticated POST `/workouts/plans/new` with valid name → 302 redirect to plan detail page; `WorkoutPlan` row exists in DB with correct `user_id` and `name`
  - [ ] Test: authenticated POST `/workouts/plans/new` with blank name → 200 (form re-rendered), "Plan name is required." error visible
  - [ ] Test: authenticated GET `/workouts/plans/<id>/` → 200, plan name displayed; user_id matches current_user
  - [ ] Test: user A cannot access user B's plan — GET `/workouts/plans/<B_plan_id>/` as user A → 404
  - [ ] Test: plan `created_at` is set and is a `datetime` object (UTC)

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**`WorkoutPlan` model — MANDATORY column names and types:**
```python
# gymtrack/app/models/workout_plan.py — NEW file
from datetime import datetime
from app.extensions import db

class WorkoutPlan(db.Model):
    __tablename__ = 'workout_plans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WorkoutPlan {self.id}: {self.name}>'
```
- Table name MUST be `workout_plans` (plural snake_case — architecture naming rule)
- `user_id` is non-nullable FK — data isolation is enforced at the model level
- `created_at` stores UTC; no timezone suffix in column name

**Data isolation — MANDATORY on every query:**
```python
# ✅ ALWAYS scope to current_user.id
plan = WorkoutPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()

# ❌ NEVER query without user scope — exposes any user's data
plan = WorkoutPlan.query.get(id)
```
This is the single most important security rule in the entire codebase.

**Flash message category — use ONLY `success` or `error`:**
```python
flash('Plan created.', 'success')   # ✅ correct
flash('Plan created.', 'ok')        # ❌ wrong category
```

**Blueprint routing in `routes.py` only — never in `__init__.py`:**
```python
# gymtrack/app/blueprints/workouts/__init__.py — ONLY blueprint definition
from flask import Blueprint
workouts_bp = Blueprint('workouts', __name__, url_prefix='/workouts')
from . import routes  # noqa: E402 — import routes to register them
```

**CSRF on all POST forms — mandatory:**
```html
<!-- workouts/plan_form.html -->
<form method="POST">
    {{ form.hidden_tag() }}
    ...
</form>
```

**URL conventions for the workouts blueprint:**
```
GET  /workouts/plans/            → plan_list (Story 3.4)
GET  /workouts/plans/new         → new_plan (THIS STORY)
POST /workouts/plans/new         → new_plan (THIS STORY)
GET  /workouts/plans/<int:id>/   → plan_detail (THIS STORY — stub for Story 3.2)
```
Note: plan_list route does NOT exist yet; "Cancel" link in plan_form.html should only point to `url_for('workouts.plan_list')` once that route exists — for this story, use `#` or omit cancel if plan_list is not yet registered.

**`strftime` Jinja2 filter:**
The architecture requires `{{ plan.created_at | strftime('%b %d, %Y') }}`. Verify `strftime` is registered as a custom Jinja2 filter in `create_app()`. If it is NOT registered yet, add it:
```python
# gymtrack/app/__init__.py — inside create_app()
app.jinja_env.filters['strftime'] = lambda dt, fmt: dt.strftime(fmt) if dt else ''
```

### Project Structure Notes

**Files to create (NEW):**
- `gymtrack/app/models/workout_plan.py`
- `gymtrack/app/blueprints/workouts/__init__.py` (if workouts blueprint does not exist)
- `gymtrack/app/blueprints/workouts/routes.py` (if workouts blueprint does not exist)
- `gymtrack/app/blueprints/workouts/forms.py`
- `gymtrack/app/templates/workouts/plan_form.html`
- `gymtrack/app/templates/workouts/plan_detail.html`
- `gymtrack/tests/test_workouts.py`
- Migration file in `migrations/versions/` (auto-generated by `flask db migrate`)

**Files to update (UPDATE):**
- `gymtrack/app/models/__init__.py` — add `WorkoutPlan` import
- `gymtrack/app/__init__.py` — register `workouts_bp` and add `strftime` filter if missing
- `gymtrack/app/static/css/style.css` — add workout plan BEM classes

**Alignment with architecture directory structure:**
```
app/blueprints/workouts/    ← blueprint per architecture [Source: architecture.md#Code Organization]
app/models/workout_plan.py  ← per-domain model files [Source: architecture.md#Code Organization]
app/templates/workouts/     ← template location convention [Source: architecture.md#Template File Naming]
tests/test_workouts.py      ← mirrors blueprint structure [Source: architecture.md#Test Structure]
```

**Epic 3 context — future stories to avoid premature implementation:**
- Story 3.2 adds `plan_exercises` table (do NOT create it here)
- Story 3.3 adds edit/reorder functionality (do NOT add edit routes)
- Story 3.4 adds plan list and plan delete (do NOT add those routes yet)
- The `plan_detail` template is a stub for this story — full exercise list added in Story 3.2

### Testing Standards

```python
# gymtrack/tests/test_workouts.py
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.workout_plan import WorkoutPlan

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def make_user(db, email='user@example.com', password='password123'):
    from flask_bcrypt import Bcrypt
    bcrypt = Bcrypt()
    user = User(email=email, password_hash=bcrypt.generate_password_hash(password).decode('utf-8'))
    db.session.add(user)
    db.session.commit()
    return user

def login_as(client, email, password):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=False)
```

### References

- Story requirements: [Source: epics.md#Story 3.1: Create Workout Plan]
- Data isolation pattern: [Source: architecture.md#Multi-User Isolation Pattern]
- WorkoutPlan model naming: [Source: architecture.md#Database Naming Conventions]
- Blueprint structure: [Source: architecture.md#Blueprint Internal Structure]
- URL conventions: [Source: architecture.md#URL Conventions]
- Flash message categories: [Source: architecture.md#HTML Page Routes — Flash Messages]
- Form validation pattern: [Source: architecture.md#Form Validation Pattern]
- Template naming: [Source: architecture.md#Template File Naming]
- Test structure: [Source: architecture.md#Test Structure]
- Error logging pattern: [Source: architecture.md#Error Logging Pattern]
- CSRF requirement: [Source: architecture.md#CSRF Protection]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List

- `gymtrack/app/models/workout_plan.py` — NEW
- `gymtrack/app/blueprints/workouts/forms.py` — NEW
- `gymtrack/app/blueprints/workouts/routes.py` — UPDATED
- `gymtrack/app/models/__init__.py` — UPDATED
- `gymtrack/app/__init__.py` — UPDATED (strftime filter)
- `gymtrack/app/templates/workouts/plan_form.html` — NEW
- `gymtrack/app/templates/workouts/plan_detail.html` — NEW
- `gymtrack/app/static/css/style.css` — UPDATED
- `gymtrack/tests/test_workouts.py` — NEW
- `gymtrack/migrations/versions/dffb1d312398_add_workout_plans_table.py` — NEW
