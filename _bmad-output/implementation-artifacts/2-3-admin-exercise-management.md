# Story 2.3: Admin Exercise Management

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an administrator,
I want to add, edit, and remove exercises from the shared library,
so that the exercise list stays accurate and comprehensive.

## Acceptance Criteria

1. **Given** I am an admin at `/admin/exercises/`
   **When** the page loads
   **Then** I see the full exercise list with Add, Edit, and Delete controls per row.

2. **Given** I submit the Add Exercise form with a valid name and muscle group
   **When** the form is submitted
   **Then** the new exercise appears in the library for all users
   **And** I see a `success` flash: "Exercise added."

3. **Given** I edit an existing exercise and submit valid changes
   **When** the form is submitted
   **Then** the exercise is updated in the database and the change is visible to all users.

4. **Given** I delete an exercise
   **When** deletion is confirmed via POST
   **Then** the exercise is removed from the library
   **And** I see a `success` flash: "Exercise removed."

5. **Given** a non-admin authenticated user tries to access `/admin/*`
   **When** the request is made
   **Then** they receive a 403 Forbidden response (renders `errors/403.html`).

6. **Given** an unauthenticated user tries to access `/admin/*`
   **When** the request is made
   **Then** they are redirected to `/auth/login`.

## Tasks / Subtasks

- [ ] Task 1: Create `admin_required` decorator in `utils.py` (AC: 5, 6)
  - [ ] Create `gymtrack/app/blueprints/admin/utils.py` — NEW file
  - [ ] Import `functools`, `abort` from `flask`, and `current_user` from `flask_login`
  - [ ] Define `admin_required(f)` decorator using `@functools.wraps(f)` that calls `abort(403)` if `not current_user.is_admin`
  - [ ] Note: `@login_required` must ALWAYS precede `@admin_required` on every route so unauthenticated users are redirected before the admin check runs

- [ ] Task 2: Create `ExerciseForm` in `forms.py` (AC: 2, 3)
  - [ ] Create `gymtrack/app/blueprints/admin/forms.py` — NEW file
  - [ ] Define `ExerciseForm(FlaskForm)` with CSRF enabled (default — do NOT set `csrf = False`)
  - [ ] Fields: `name` (`StringField`, `DataRequired()`, max length 200), `muscle_group` (`StringField`, `DataRequired()`, max length 100), `description` (`TextAreaField`, `Optional()`), `submit` (`SubmitField`)
  - [ ] Single form class is used for both Add and Edit routes

- [ ] Task 3: Replace admin routes placeholder with full exercise CRUD (AC: 1–6)
  - [ ] UPDATE `gymtrack/app/blueprints/admin/routes.py` — replace the entire file content
  - [ ] Import: `logging`, `abort`, `flash`, `redirect`, `render_template`, `url_for`, `request` from `flask`; `login_required`, `current_user` from `flask_login`; `admin_bp` from blueprint; `ExerciseForm` from `forms`; `admin_required` from `utils`; `db` from `app.extensions`; `Exercise` from `app.models.exercise`
  - [ ] Route `GET /admin/exercises/`: list all exercises ordered by name; `@login_required @admin_required`
  - [ ] Route `GET /POST /admin/exercises/new`: add form; on valid POST create `Exercise`, commit, flash "Exercise added.", redirect to `admin.exercise_list`
  - [ ] Route `GET /POST /admin/exercises/<int:id>/edit`: load exercise by id (`.get_or_404()`), populate form, on valid POST update fields, commit, flash "Exercise updated.", redirect to `admin.exercise_list`
  - [ ] Route `POST /admin/exercises/<int:id>/delete`: load exercise by id, delete, commit, flash "Exercise removed.", redirect to `admin.exercise_list`
  - [ ] Add `logger = logging.getLogger(__name__)` and log admin actions at INFO level

- [ ] Task 4: Create admin templates (AC: 1, 2, 3, 4)
  - [ ] Create `gymtrack/app/templates/admin/` directory (new subdirectory)
  - [ ] Create `gymtrack/app/templates/admin/exercise_list.html` — NEW template
    - [ ] Extends `base.html`; BEM block class `admin-exercise-list`
    - [ ] Heading: "Admin — Exercise Library"
    - [ ] "Add Exercise" link button pointing to `admin.add_exercise`
    - [ ] Table with columns: Name, Muscle Group, Description, Actions
    - [ ] Per-row: Edit link → `admin.edit_exercise(id=exercise.id)` and a Delete POST form with CSRF token and confirm button
    - [ ] Empty state: "No exercises in the library yet."
    - [ ] All form inputs must have `<label>` elements; table must have `aria-label`
  - [ ] Create `gymtrack/app/templates/admin/exercise_form.html` — NEW template
    - [ ] Extends `base.html`; BEM block class `admin-exercise-form`
    - [ ] Dynamic heading: "Add Exercise" (new) or "Edit Exercise" (edit)
    - [ ] Render `{{ form.hidden_tag() }}` for CSRF protection
    - [ ] Fields: name, muscle_group, description — each with `<label>` and associated input
    - [ ] Submit button and "Cancel" link back to `admin.exercise_list`
    - [ ] Show WTForms field errors inline using `{% for error in field.errors %}<span class="form-error">{{ error }}</span>{% endfor %}`

- [ ] Task 5: Add CSS for admin panel (AC: 1)
  - [ ] UPDATE `gymtrack/app/static/css/style.css` — ADD admin BEM classes
  - [ ] Add `admin-exercise-list` and `admin-exercise-form` BEM blocks
  - [ ] Touch targets ≥ 44px for all admin action buttons/links (NFR17 / mobile-first)
  - [ ] Do NOT create a new CSS file — only add to existing `style.css`

- [ ] Task 6: Create `tests/test_admin.py` with full test coverage (AC: 1–6)
  - [ ] Create `gymtrack/tests/test_admin.py` — NEW file
  - [ ] Helper `make_admin(db)` — creates a `User(email='admin@example.com', is_admin=True)` and returns it
  - [ ] Helper `make_regular_user(db)` — creates `User(email='user@example.com', is_admin=False)`
  - [ ] Helper `login_as(client, db, email, password)` — POSTs to `/auth/login`
  - [ ] Re-use `make_exercise()` pattern from `test_exercises.py` (duplicate locally — do NOT import across test files)
  - [ ] Test: unauthenticated GET `/admin/exercises/` → 302 redirect to `/auth/login`
  - [ ] Test: non-admin authenticated GET `/admin/exercises/` → 403
  - [ ] Test: admin GET `/admin/exercises/` → 200, contains exercise names and Add/Edit/Delete controls
  - [ ] Test: admin POST `/admin/exercises/new` valid data → 302 redirect, exercise exists in DB
  - [ ] Test: admin POST `/admin/exercises/new` missing name → 200 (form re-rendered with error)
  - [ ] Test: admin GET `/admin/exercises/<id>/edit` → 200, form pre-populated with exercise data
  - [ ] Test: admin POST `/admin/exercises/<id>/edit` valid data → 302 redirect, DB updated
  - [ ] Test: admin POST `/admin/exercises/<id>/delete` → 302 redirect, exercise gone from DB
  - [ ] Test: non-admin POST `/admin/exercises/new` → 403

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**`admin_required` decorator — define in `utils.py`, not `routes.py`:**
- Per architecture, blueprint-local helpers go in `utils.py`
- The decorator MUST use `functools.wraps` to preserve the wrapped function's metadata
- Route decoration order MUST be: `@login_required` first, then `@admin_required`. Flask-Login's `@login_required` handles unauthenticated users (redirect to login); `@admin_required` then handles authenticated non-admins (abort 403).
```python
# gymtrack/app/blueprints/admin/utils.py
import functools
from flask import abort
from flask_login import current_user


def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

**`User.is_admin` field already exists — do NOT add migrations:**
- `User` model in `gymtrack/app/models/user.py` already has `is_admin = db.Column(db.Boolean, default=False, nullable=False)`
- No `flask db migrate` needed for this story
- The `is_admin` field defaults to `False` for all existing users

**Exercise model columns (do NOT change schema):**
```python
# gymtrack/app/models/exercise.py — READ ONLY, no changes
id, name (unique, max 200), muscle_group (max 100), description (Text, nullable), created_at
```

**CSRF protection on all admin POST forms:**
- Add, Edit, and Delete are all POST operations that MUST include `{{ form.hidden_tag() }}`
- Delete uses its own minimal `FlaskForm` or the same `ExerciseForm` for CSRF token only — simplest approach is a dedicated small `DeleteExerciseForm(FlaskForm): pass` or use Flask-WTF's `validate_csrf()` directly
- **Simplest recommended approach**: pass `form=ExerciseForm()` to the list template and use `{{ form.hidden_tag() }}` in each delete form. The form is not rendered for input but its hidden CSRF token is valid and sufficient.
- Alternatively, create a `DeleteForm(FlaskForm): pass` with no fields — just CSRF token
- Never expose a delete action via GET (GET is idempotent; destructive actions require POST)

**Route naming — use descriptive endpoint names:**
```python
@admin_bp.route('/exercises/', methods=['GET'])         # endpoint: admin.exercise_list
@admin_bp.route('/exercises/new', methods=['GET', 'POST'])  # endpoint: admin.add_exercise
@admin_bp.route('/exercises/<int:id>/edit', methods=['GET', 'POST'])  # endpoint: admin.edit_exercise
@admin_bp.route('/exercises/<int:id>/delete', methods=['POST'])  # endpoint: admin.delete_exercise
```

**Flash message categories — MUST be one of: `success`, `error`, `info`, `warning`:**
```python
flash('Exercise added.', 'success')       # after add
flash('Exercise updated.', 'success')     # after edit
flash('Exercise removed.', 'success')     # after delete
```

**Error logging at INFO level for admin actions:**
```python
logger.info('Admin %s added exercise: %s', current_user.email, exercise.name)
logger.info('Admin %s updated exercise id=%d', current_user.email, exercise.id)
logger.info('Admin %s deleted exercise id=%d name=%s', current_user.email, exercise.id, exercise.name)
```

**Exercise.name uniqueness constraint:**
- `name` column is `unique=True` in the DB schema
- If admin tries to add/edit with a duplicate name, SQLAlchemy will raise `IntegrityError`
- Handle with try/except around `db.session.commit()` for add and edit, flash `'error'` category message: "An exercise with that name already exists."
- `db.session.rollback()` must be called in the except block to reset the session state

**`.get_or_404()` for edit and delete routes:**
```python
exercise = Exercise.query.get_or_404(id)  # returns 404 if not found
```

### Previous Story Learnings (from Story 2.2)

- `flask db init` was run in Story 1.1 — migrations dir and `alembic.ini` are in place; do NOT re-run `flask db init`
- Pre-existing failing test: `test_config.py::test_testing_config_uses_in_memory_sqlite` — NOT related to admin; do not attempt to fix it
- `Exercise` model is already imported in `app/models/__init__.py`; no model changes needed
- `exercises_bp` (and all other blueprints including `admin_bp`) are already registered in `create_app()` — do not re-register
- Test helper pattern from Story 2.1 (reuse in test_admin.py with local copy):
  ```python
  def make_exercise(db, name='Bench Press', muscle_group='Chest', description='Flat barbell press'):
      ex = Exercise(name=name, muscle_group=muscle_group, description=description)
      db.session.add(ex)
      db.session.commit()
      return ex
  ```
- BEM CSS in `style.css` only — no new CSS files
- All inputs must have `<label>` elements (NFR19 accessibility)

### Project Structure — Files to Create/Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `gymtrack/app/blueprints/admin/utils.py` | NEW | `admin_required` decorator |
| `gymtrack/app/blueprints/admin/forms.py` | NEW | `ExerciseForm` and `DeleteForm` WTForms classes |
| `gymtrack/app/blueprints/admin/routes.py` | UPDATE | Full exercise CRUD replacing placeholder |
| `gymtrack/app/templates/admin/exercise_list.html` | NEW | Admin exercise list with Add/Edit/Delete |
| `gymtrack/app/templates/admin/exercise_form.html` | NEW | Add/Edit exercise form |
| `gymtrack/app/static/css/style.css` | UPDATE | Add `admin-exercise-list` and `admin-exercise-form` BEM classes |
| `gymtrack/tests/test_admin.py` | NEW | Full test coverage for admin exercise CRUD |

### Code Reference — forms.py

```python
# gymtrack/app/blueprints/admin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ExerciseForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    muscle_group = StringField('Muscle Group', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Exercise')


class DeleteForm(FlaskForm):
    """CSRF-only form used to protect the delete action."""
    pass
```

### Code Reference — routes.py

```python
# gymtrack/app/blueprints/admin/routes.py
import logging
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import ExerciseForm, DeleteForm
from app.blueprints.admin.utils import admin_required
from app.extensions import db
from app.models.exercise import Exercise

logger = logging.getLogger(__name__)


@admin_bp.route('/exercises/')
@login_required
@admin_required
def exercise_list():
    exercises = Exercise.query.order_by(Exercise.name).all()
    delete_form = DeleteForm()
    return render_template('admin/exercise_list.html', exercises=exercises, delete_form=delete_form)


@admin_bp.route('/exercises/new', methods=['GET', 'POST'])
@login_required
@admin_required
def add_exercise():
    form = ExerciseForm()
    if form.validate_on_submit():
        exercise = Exercise(
            name=form.name.data.strip(),
            muscle_group=form.muscle_group.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
        )
        db.session.add(exercise)
        try:
            db.session.commit()
            logger.info('Admin %s added exercise: %s', current_user.email, exercise.name)
            flash('Exercise added.', 'success')
            return redirect(url_for('admin.exercise_list'))
        except IntegrityError:
            db.session.rollback()
            flash('An exercise with that name already exists.', 'error')
    return render_template('admin/exercise_form.html', form=form, title='Add Exercise')


@admin_bp.route('/exercises/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_exercise(id):
    exercise = Exercise.query.get_or_404(id)
    form = ExerciseForm(obj=exercise)
    if form.validate_on_submit():
        exercise.name = form.name.data.strip()
        exercise.muscle_group = form.muscle_group.data.strip()
        exercise.description = form.description.data.strip() if form.description.data else None
        try:
            db.session.commit()
            logger.info('Admin %s updated exercise id=%d', current_user.email, exercise.id)
            flash('Exercise updated.', 'success')
            return redirect(url_for('admin.exercise_list'))
        except IntegrityError:
            db.session.rollback()
            flash('An exercise with that name already exists.', 'error')
    return render_template('admin/exercise_form.html', form=form, title='Edit Exercise')


@admin_bp.route('/exercises/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exercise(id):
    delete_form = DeleteForm()
    if delete_form.validate_on_submit():
        exercise = Exercise.query.get_or_404(id)
        exercise_name = exercise.name
        db.session.delete(exercise)
        db.session.commit()
        logger.info('Admin %s deleted exercise id=%d name=%s', current_user.email, id, exercise_name)
        flash('Exercise removed.', 'success')
    return redirect(url_for('admin.exercise_list'))
```

### Code Reference — exercise_list.html

```jinja2
{# gymtrack/app/templates/admin/exercise_list.html #}
{% extends 'base.html' %}

{% block title %}Admin — Exercise Library – GymTrack{% endblock %}

{% block content %}
<div class="admin-exercise-list">
  <div class="admin-exercise-list__header">
    <h1 class="admin-exercise-list__heading">Admin — Exercise Library</h1>
    <a href="{{ url_for('admin.add_exercise') }}" class="admin-exercise-list__add-btn">Add Exercise</a>
  </div>

  {% if exercises %}
    <table class="admin-exercise-table" aria-label="Admin Exercise Management">
      <thead>
        <tr>
          <th scope="col" class="admin-exercise-table__header">Name</th>
          <th scope="col" class="admin-exercise-table__header">Muscle Group</th>
          <th scope="col" class="admin-exercise-table__header">Description</th>
          <th scope="col" class="admin-exercise-table__header">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for exercise in exercises %}
        <tr class="admin-exercise-table__row">
          <td class="admin-exercise-table__name">{{ exercise.name }}</td>
          <td class="admin-exercise-table__muscle">{{ exercise.muscle_group }}</td>
          <td class="admin-exercise-table__desc">{{ exercise.description or '—' }}</td>
          <td class="admin-exercise-table__actions">
            <a href="{{ url_for('admin.edit_exercise', id=exercise.id) }}" class="admin-exercise-table__edit-link">Edit</a>
            <form method="POST" action="{{ url_for('admin.delete_exercise', id=exercise.id) }}" class="admin-exercise-table__delete-form" style="display:inline;">
              {{ delete_form.hidden_tag() }}
              <button type="submit" class="admin-exercise-table__delete-btn" onclick="return confirm('Delete {{ exercise.name }}?')">Delete</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p class="admin-exercise-list__empty">No exercises in the library yet.</p>
  {% endif %}
</div>
{% endblock %}
```

### Code Reference — exercise_form.html

```jinja2
{# gymtrack/app/templates/admin/exercise_form.html #}
{% extends 'base.html' %}

{% block title %}{{ title }} – GymTrack{% endblock %}

{% block content %}
<div class="admin-exercise-form">
  <h1 class="admin-exercise-form__heading">{{ title }}</h1>

  <form method="POST" class="admin-exercise-form__form">
    {{ form.hidden_tag() }}

    <div class="admin-exercise-form__field">
      {{ form.name.label(class="admin-exercise-form__label") }}
      {{ form.name(class="admin-exercise-form__input") }}
      {% for error in form.name.errors %}
        <span class="form-error">{{ error }}</span>
      {% endfor %}
    </div>

    <div class="admin-exercise-form__field">
      {{ form.muscle_group.label(class="admin-exercise-form__label") }}
      {{ form.muscle_group(class="admin-exercise-form__input") }}
      {% for error in form.muscle_group.errors %}
        <span class="form-error">{{ error }}</span>
      {% endfor %}
    </div>

    <div class="admin-exercise-form__field">
      {{ form.description.label(class="admin-exercise-form__label") }}
      {{ form.description(class="admin-exercise-form__textarea", rows=3) }}
      {% for error in form.description.errors %}
        <span class="form-error">{{ error }}</span>
      {% endfor %}
    </div>

    <div class="admin-exercise-form__actions">
      {{ form.submit(class="admin-exercise-form__submit") }}
      <a href="{{ url_for('admin.exercise_list') }}" class="admin-exercise-form__cancel">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}
```

### Code Reference — test_admin.py (key tests)

```python
# gymtrack/tests/test_admin.py
import pytest
from app.models.user import User
from app.models.exercise import Exercise


def make_exercise(db, name='Bench Press', muscle_group='Chest', description='Flat barbell press'):
    ex = Exercise(name=name, muscle_group=muscle_group, description=description)
    db.session.add(ex)
    db.session.commit()
    return ex


def make_admin(db):
    u = User(email='admin@example.com', is_admin=True)
    u.set_password('adminpass123')
    db.session.add(u)
    db.session.commit()
    return u


def make_regular_user(db):
    u = User(email='user@example.com', is_admin=False)
    u.set_password('userpass123')
    db.session.add(u)
    db.session.commit()
    return u


def login_as(client, email, password):
    client.post('/auth/login', data={'email': email, 'password': password})


def test_unauthenticated_redirects_to_login(test_client):
    resp = test_client.get('/admin/exercises/')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_non_admin_gets_403(test_client, test_db):
    make_regular_user(test_db)
    login_as(test_client, 'user@example.com', 'userpass123')
    resp = test_client.get('/admin/exercises/')
    assert resp.status_code == 403


def test_admin_sees_exercise_list(test_client, test_db):
    make_admin(test_db)
    make_exercise(test_db, name='Squat', muscle_group='Legs')
    login_as(test_client, 'admin@example.com', 'adminpass123')
    resp = test_client.get('/admin/exercises/')
    assert resp.status_code == 200
    assert b'Squat' in resp.data
    assert b'Edit' in resp.data
    assert b'Delete' in resp.data


def test_admin_add_exercise_success(test_client, test_db):
    make_admin(test_db)
    login_as(test_client, 'admin@example.com', 'adminpass123')
    resp = test_client.post('/admin/exercises/new', data={
        'name': 'Pull-Up', 'muscle_group': 'Back', 'description': '',
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert Exercise.query.filter_by(name='Pull-Up').first() is not None


def test_admin_add_exercise_missing_name(test_client, test_db):
    make_admin(test_db)
    login_as(test_client, 'admin@example.com', 'adminpass123')
    resp = test_client.post('/admin/exercises/new', data={
        'name': '', 'muscle_group': 'Back',
    })
    assert resp.status_code == 200  # form re-rendered


def test_admin_edit_exercise(test_client, test_db):
    make_admin(test_db)
    ex = make_exercise(test_db, name='Old Name', muscle_group='Chest')
    login_as(test_client, 'admin@example.com', 'adminpass123')
    resp = test_client.post(f'/admin/exercises/{ex.id}/edit', data={
        'name': 'New Name', 'muscle_group': 'Back', 'description': '',
    }, follow_redirects=False)
    assert resp.status_code == 302
    updated = Exercise.query.get(ex.id)
    assert updated.name == 'New Name'


def test_admin_delete_exercise(test_client, test_db):
    make_admin(test_db)
    ex = make_exercise(test_db)
    ex_id = ex.id
    login_as(test_client, 'admin@example.com', 'adminpass123')
    resp = test_client.post(f'/admin/exercises/{ex_id}/delete', follow_redirects=False)
    assert resp.status_code == 302
    assert Exercise.query.get(ex_id) is None


def test_non_admin_post_add_gets_403(test_client, test_db):
    make_regular_user(test_db)
    login_as(test_client, 'user@example.com', 'userpass123')
    resp = test_client.post('/admin/exercises/new', data={
        'name': 'Hack Squat', 'muscle_group': 'Legs',
    })
    assert resp.status_code == 403
```

### References

- Story acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#Story-2.3]
- FR10, FR11, FR38: [Source: _bmad-output/planning-artifacts/epics.md#Requirements-Inventory]
- `is_admin` field on User model: [Source: gymtrack/app/models/user.py]
- Admin blueprint structure: [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint-Internal-Structure]
- `admin_required` decorator pattern: [Source: _bmad-output/planning-artifacts/architecture.md#URL-Conventions (`/admin/` requires login_required + admin_required)]
- CSRF on all POST forms: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication-&-Security]
- Form validation pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Form-Validation-Pattern]
- Error logging pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Error-Logging-Pattern]
- Flash message categories: [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- BEM CSS / single style.css: [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- 403 error handler already registered: [Source: gymtrack/app/__init__.py]
- Test structure mirror: [Source: _bmad-output/planning-artifacts/architecture.md#Test-Structure]
- Previous story file list + learnings: [Source: _bmad-output/implementation-artifacts/2-2-exercise-search-and-filter.md#Dev-Agent-Record]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List
