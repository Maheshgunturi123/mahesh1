# Story 2.1: Exercise Library Browse

Status: done

## Story

As a logged-in user,
I want to browse the full exercise library,
So that I can discover exercises to add to my workouts.

## Acceptance Criteria

1. **Given** I navigate to `/exercises/` **When** the page loads **Then** I see a paginated list of all exercises, each showing name, muscle group, and description.

2. **Given** the exercises page loads **Then** the `exercises` table has columns: `id`, `name`, `muscle_group`, `description`, `created_at`.

3. **Given** the exercises page loads **Then** exercises are sorted alphabetically by name by default.

4. **Given** I am an unauthenticated user trying to access `/exercises/` **When** the request is made **Then** I am redirected to `/auth/login`.

5. **Given** I am a logged-in user on `/exercises/` **When** the library has more exercises than fit on one page **Then** pagination controls are shown (next/previous page links).

## Tasks / Subtasks

- [ ] Task 1: Create `Exercise` model (AC: 2)
  - [ ] Create `gymtrack/app/models/exercise.py` — NEW file
  - [ ] Define `Exercise(db.Model)` with `__tablename__ = 'exercises'`
  - [ ] Columns: `id` (Integer PK), `name` (String(200), unique, nullable=False), `muscle_group` (String(100), nullable=False), `description` (Text, nullable=True), `created_at` (DateTime, default=datetime.utcnow, nullable=False)
  - [ ] Update `gymtrack/app/models/__init__.py` to import `Exercise` (so SQLAlchemy registers it)

- [ ] Task 2: Generate and apply database migration (AC: 2)
  - [ ] Run `flask db migrate -m "add exercises table"` from `gymtrack/` directory
  - [ ] Verify generated migration creates `exercises` table with correct columns
  - [ ] Run `flask db upgrade` to apply migration

- [ ] Task 3: Implement exercises blueprint route (AC: 1, 3, 4, 5)
  - [ ] Replace placeholder route in `gymtrack/app/blueprints/exercises/routes.py`
  - [ ] Add `@login_required` decorator to the index route
  - [ ] Query exercises sorted alphabetically: `Exercise.query.order_by(Exercise.name).paginate(page=page, per_page=20, error_out=False)`
  - [ ] Pass `exercises` (pagination object) and `page` to template
  - [ ] Use `request.args.get('page', 1, type=int)` to read current page
  - [ ] Add `import logging; logger = logging.getLogger(__name__)` at top of routes.py

- [ ] Task 4: Create exercise list template (AC: 1, 3, 5)
  - [ ] Create `gymtrack/app/templates/exercises/index.html` — NEW file
  - [ ] Extend `base.html`, set `{% block title %}Exercise Library – GymTrack{% endblock %}`
  - [ ] Render `<h1>` heading "Exercise Library"
  - [ ] Render an exercise list/table: one row per exercise showing `name`, `muscle_group`, `description`
  - [ ] Use BEM CSS classes: `exercise-list`, `exercise-list__item`, `exercise-list__name`, `exercise-list__muscle`, `exercise-list__desc`
  - [ ] Add pagination controls: Previous / Next links using `exercises.prev_num` and `exercises.next_num`; disable links on first/last page
  - [ ] Show "No exercises found." when `exercises.total == 0`
  - [ ] All form inputs (if any) must have `<label>` elements (UX-DR10)
  - [ ] Accessible: semantic `<table>` or `<ul>` with proper ARIA if needed (NFR17)

- [ ] Task 5: Write tests (AC: 1, 3, 4, 5)
  - [ ] Create `gymtrack/tests/test_exercises.py` — NEW file
  - [ ] Test: unauthenticated GET `/exercises/` → 302 redirect to login
  - [ ] Test: authenticated GET `/exercises/` with empty library → 200, "No exercises found."
  - [ ] Test: authenticated GET `/exercises/` with exercises → 200, exercise names visible, sorted alphabetically
  - [ ] Test: pagination — when more than `per_page` exercises exist, pagination links appear
  - [ ] Use `test_client` and `test_db` fixtures from `conftest.py`
  - [ ] Helper to create an `Exercise` record: `Exercise(name=..., muscle_group=..., description=...)`

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**Exercise model — `exercises` is a shared library (NOT user-owned):**
- The `exercises` table has NO `user_id` column — it is a shared, admin-curated library visible to all users.
- Do NOT add user_id to Exercise model. This is intentional. Queries are NOT scoped to `current_user.id`.
- The user isolation rule (`filter_by(user_id=current_user.id)`) applies to user-owned data only (plans, sessions, sets, PRs). Exercise is shared content.

**Existing code state — READ BEFORE IMPLEMENTING:**
- `gymtrack/app/blueprints/exercises/__init__.py` — Blueprint already defined as `exercises_bp`, already registered in `create_app()`. Do NOT redefine or re-register.
- `gymtrack/app/blueprints/exercises/routes.py` — Contains a single placeholder route `GET /` returning plain text. REPLACE this route completely.
- `gymtrack/app/models/user.py` — Established `User` model pattern; follow same column style for `Exercise`.
- `gymtrack/app/models/__init__.py` — Currently only imports `User`. Add `Exercise` import so Alembic detects the model.
- `gymtrack/app/templates/base.html` — Already has `<a href="{{ url_for('exercises.index') }}">Exercises</a>` in nav. The view function must be named `index` to match.
- `gymtrack/tests/conftest.py` — Provides `test_app`, `test_client`, `test_db` fixtures. The `test_db` fixture calls `db.create_all()` and `db.drop_all()` per function — your `Exercise` model import in `models/__init__.py` ensures the table is included.

**Blueprint structure rules:**
- Routes defined ONLY in `routes.py`, never in `__init__.py`.
- This story requires no form — do NOT create `forms.py` for story 2.1 (that belongs to story 2.2+).
- No `utils.py` needed for this story.

**Pagination:**
- Use Flask-SQLAlchemy's built-in `.paginate()` — already available, no new dependency.
- Default `per_page=20` is a reasonable starting point; do not make it configurable in V1.
- Use `error_out=False` so out-of-range page numbers return an empty list rather than 404.

**Template CSS pattern:**
- Single `app/static/css/style.css` with BEM naming. Add exercise-specific classes to this file.
- Do NOT create a new CSS file. Do NOT use inline styles.
- Mobile-first, touch targets ≥ 44px for any interactive elements (UX-DR1).

**Login redirect:**
- `@login_required` (from `flask_login`) automatically redirects unauthenticated users to `login_manager.login_view`.
- `login_manager.login_view = 'auth.login'` is already set in `app/extensions.py` (established in Story 1.1).
- No manual redirect logic needed.

**Logging:**
- Add `import logging; logger = logging.getLogger(__name__)` at the top of `routes.py` (after imports).
- No log events required for the browse view in this story (no user actions to record), but the logger must be present per architecture standards.

### Project Structure — Files to Create/Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `gymtrack/app/models/exercise.py` | NEW | `Exercise` SQLAlchemy model |
| `gymtrack/app/models/__init__.py` | UPDATE | Add `from app.models.exercise import Exercise` |
| `gymtrack/app/blueprints/exercises/routes.py` | UPDATE | Replace placeholder with real paginated browse route |
| `gymtrack/app/templates/exercises/index.html` | NEW | Paginated exercise library list template |
| `gymtrack/tests/test_exercises.py` | NEW | Exercise blueprint integration tests |
| `gymtrack/migrations/versions/<hash>_add_exercises_table.py` | NEW | Alembic migration (auto-generated) |

### Code Reference — Exercise Model

```python
# gymtrack/app/models/exercise.py
from datetime import datetime
from app.extensions import db


class Exercise(db.Model):
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    muscle_group = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
```

### Code Reference — Route Pattern

```python
# gymtrack/app/blueprints/exercises/routes.py
import logging
from flask import render_template, request
from flask_login import login_required
from app.blueprints.exercises import exercises_bp
from app.models.exercise import Exercise

logger = logging.getLogger(__name__)


@exercises_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    exercises = Exercise.query.order_by(Exercise.name).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('exercises/index.html', exercises=exercises)
```

### Code Reference — Test Pattern

```python
# gymtrack/tests/test_exercises.py
import pytest
from app.models.exercise import Exercise


def make_exercise(db, name='Bench Press', muscle_group='Chest', description='Flat barbell press'):
    ex = Exercise(name=name, muscle_group=muscle_group, description=description)
    db.session.add(ex)
    db.session.commit()
    return ex


def login(client, db):
    from app.models.user import User
    u = User(email='test@example.com')
    u.set_password('password123')
    db.session.add(u)
    db.session.commit()
    client.post('/auth/login', data={'email': 'test@example.com', 'password': 'password123'})


def test_unauthenticated_redirects_to_login(test_client):
    resp = test_client.get('/exercises/')
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']


def test_empty_library(test_client, test_db):
    login(test_client, test_db)
    resp = test_client.get('/exercises/')
    assert resp.status_code == 200
    assert b'No exercises found' in resp.data


def test_exercises_listed_alphabetically(test_client, test_db):
    login(test_client, test_db)
    make_exercise(test_db, name='Squat', muscle_group='Legs')
    make_exercise(test_db, name='Bench Press', muscle_group='Chest')
    resp = test_client.get('/exercises/')
    assert resp.status_code == 200
    assert resp.data.index(b'Bench Press') < resp.data.index(b'Squat')
```

### References

- Story acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#Story-2.1]
- Blueprint structure rules: [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint-Internal-Structure]
- Naming conventions: [Source: _bmad-output/planning-artifacts/architecture.md#Naming-Patterns]
- User data isolation note (exercises exempt): [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture]
- Login required / Flask-Login: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication]
- Logging pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Error-Logging-Pattern]
- Test structure: [Source: _bmad-output/planning-artifacts/architecture.md#Test-Structure]
- Prior story codebase state (extensions, models, blueprints): Stories 1.1–1.6 implementation artifacts

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

None.

### Completion Notes List

- Task 2: `flask db init` required first (migrations dir was empty); generated initial migration creates both `users` and `exercises` tables (first-ever migration for this project).
- Pre-existing test failure: `test_config.py::test_testing_config_uses_in_memory_sqlite` — `config.py` uses `sqlite://` but test expects `sqlite:///:memory:`. Not related to Story 2.1.

### File List

- `gymtrack/app/models/exercise.py` — NEW
- `gymtrack/app/models/__init__.py` — UPDATED (added Exercise import)
- `gymtrack/app/blueprints/exercises/routes.py` — UPDATED (replaced placeholder with paginated browse route)
- `gymtrack/app/templates/exercises/index.html` — NEW
- `gymtrack/app/static/css/style.css` — UPDATED (added exercise-list and pagination BEM classes)
- `gymtrack/tests/test_exercises.py` — NEW
- `gymtrack/migrations/alembic.ini` — NEW (flask db init)
- `gymtrack/migrations/env.py` — NEW (flask db init)
- `gymtrack/migrations/script.py.mako` — NEW (flask db init)
- `gymtrack/migrations/versions/9d374b8d7f0c_add_exercises_table.py` — NEW (flask db migrate)
