# Story 5.4: View All Personal Records

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to view a list of all my current personal records per exercise,
so that I can see my peak performance across all movements.

## Acceptance Criteria

1. **Given** I navigate to `/progress/prs/`
   **When** the page loads
   **Then** I see a list of all exercises for which I have a PR, showing: exercise name, best weight (kg), reps at that weight, date achieved
   **And** only my own PRs are shown (filtered by `user_id=current_user.id`)
   **And** the list is sorted alphabetically by exercise name

2. **Given** I have no PRs yet
   **When** the page loads
   **Then** I see: "No personal records yet. Complete a workout to start tracking PRs."

## Tasks / Subtasks

- [ ] Task 1: Add `/prs/` route to the progress blueprint (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/blueprints/progress/routes.py`
  - [ ] Add imports: `from flask_login import current_user, login_required`, `from app.models.personal_record import PersonalRecord`, `from app.models.exercise import Exercise`
  - [ ] Add route `GET /prs/` with `@login_required`
  - [ ] Query: `PersonalRecord.query.filter_by(user_id=current_user.id).join(Exercise).order_by(Exercise.name.asc()).all()`
  - [ ] Pass `prs=prs` to `render_template('progress/prs.html', prs=prs)`

- [ ] Task 2: Create `progress/prs.html` template (AC: 1, 2)
  - [ ] CREATE `gymtrack/app/templates/progress/prs.html`
  - [ ] Extend `base.html`; set `{% block title %}Personal Records — GymTrack{% endblock %}`
  - [ ] When `prs` is non-empty: render a list where each item shows `pr.exercise.name`, `pr.weight_kg`, `pr.reps`, `pr.achieved_at | strftime('%b %d, %Y')`
  - [ ] When `prs` is empty: render `<p class="pr-list__empty">No personal records yet. Complete a workout to start tracking PRs.</p>`
  - [ ] Use BEM class naming: block `pr-list`, elements `pr-list__heading`, `pr-list__items`, `pr-list__item`, `pr-list__exercise`, `pr-list__weight`, `pr-list__reps`, `pr-list__date`, `pr-list__empty`

- [ ] Task 3: Add CSS for `pr-list` component (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/static/css/style.css`
  - [ ] Add BEM styles for `.pr-list`, `.pr-list__heading`, `.pr-list__items`, `.pr-list__item`, `.pr-list__exercise`, `.pr-list__weight`, `.pr-list__reps`, `.pr-list__date`, `.pr-list__empty`
  - [ ] Mobile-first layout; items should be readable at 375px, in a card or row format

- [ ] Task 4: Create `test_progress.py` with integration tests (AC: 1, 2)
  - [ ] CREATE `gymtrack/tests/test_progress.py`
  - [ ] Add local `app` and `client` fixtures (same pattern as `test_workouts.py`)
  - [ ] Add helper functions: `make_user`, `login_as`, `make_exercise`, `make_personal_record`
  - [ ] Add `test_pr_list_unauthenticated` (AC: 1 — redirect to login)
  - [ ] Add `test_pr_list_shows_records_alphabetically` (AC: 1 — PRs listed, sorted by exercise name)
  - [ ] Add `test_pr_list_empty_state` (AC: 2 — empty state message shown)
  - [ ] Add `test_pr_list_data_isolation` (AC: 1 — only own PRs shown, not other user's)
  - [ ] See full test specs in Dev Notes below

## Dev Notes

### Current State of `progress/routes.py`

The progress blueprint has a **placeholder** index route only:

```python
from app.blueprints.progress import progress_bp


@progress_bp.route('/')
def index():
    # TODO: implement in subsequent stories
    return f'Progress blueprint placeholder', 200
```

This file must have the `/prs/` route **appended** (do NOT replace or remove the existing `index()` route — it will be implemented in Epic 6). Add the new route below the existing one.

After Task 1, the file should look like:

```python
from flask_login import current_user, login_required

from app.blueprints.progress import progress_bp
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord


@progress_bp.route('/')
def index():
    # TODO: implement in subsequent stories
    return f'Progress blueprint placeholder', 200


@progress_bp.route('/prs/')
@login_required
def pr_list():
    prs = (
        PersonalRecord.query
        .filter_by(user_id=current_user.id)
        .join(Exercise)
        .order_by(Exercise.name.asc())
        .all()
    )
    return render_template('progress/prs.html', prs=prs)
```

**Important**: Add `from flask import render_template` to the import line. The full imports after Task 1:

```python
from flask import render_template
from flask_login import current_user, login_required

from app.blueprints.progress import progress_bp
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord
```

### `PersonalRecord` Model (read-only — DO NOT MODIFY)

Location: `gymtrack/app/models/personal_record.py`

```python
class PersonalRecord(db.Model):
    __tablename__ = 'personal_records'
    __table_args__ = (
        UniqueConstraint('user_id', 'exercise_id', name='uq_user_exercise_pr'),
    )

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    weight_kg   = db.Column(db.Float, nullable=False)
    reps        = db.Column(db.Integer, nullable=False)
    achieved_at = db.Column(db.DateTime, nullable=False)  # UTC

    exercise = db.relationship('Exercise', backref=db.backref('personal_records', lazy='dynamic'))
```

One row per `(user_id, exercise_id)` — there is **at most one** PR per exercise per user (the `detect_prs` service upserts to update the existing row when a new PR is broken). Access exercise name via `pr.exercise.name`.

### Template Structure for `progress/prs.html`

The project uses BEM CSS with a single `style.css`. Follow the exact same pattern as `session_list.html`:

```html
{% extends 'base.html' %}
{% block title %}Personal Records — GymTrack{% endblock %}
{% block content %}
<div class="pr-list">
  <h1 class="pr-list__heading">Personal Records</h1>
  {% if prs %}
    <ul class="pr-list__items">
      {% for pr in prs %}
      <li class="pr-list__item">
        <span class="pr-list__exercise">{{ pr.exercise.name }}</span>
        <span class="pr-list__weight">{{ pr.weight_kg }}kg</span>
        <span class="pr-list__reps">&times; {{ pr.reps }} reps</span>
        <span class="pr-list__date">{{ pr.achieved_at | strftime('%b %d, %Y') }}</span>
      </li>
      {% endfor %}
    </ul>
  {% else %}
    <p class="pr-list__empty">No personal records yet. Complete a workout to start tracking PRs.</p>
  {% endif %}
</div>
{% endblock %}
```

The `strftime` Jinja2 filter is registered in `app/__init__.py` line 37:
```python
app.jinja_env.filters['strftime'] = lambda dt, fmt: dt.strftime(fmt) if dt else ''
```
Use `pr.achieved_at | strftime('%b %d, %Y')` — no custom filter registration needed.

### Query Pattern — Data Isolation (MANDATORY)

```python
# ✅ CORRECT — filters by current_user.id + joins Exercise for sorting
prs = (
    PersonalRecord.query
    .filter_by(user_id=current_user.id)
    .join(Exercise)
    .order_by(Exercise.name.asc())
    .all()
)

# ❌ WRONG — no user_id filter (exposes all users' PRs)
prs = PersonalRecord.query.all()

# ❌ WRONG — no join, no sort
prs = PersonalRecord.query.filter_by(user_id=current_user.id).all()
```

The `.join(Exercise)` is required for the `.order_by(Exercise.name.asc())` to work. SQLAlchemy will use the FK relationship defined in the model.

### Template Directory

The `progress/` template directory does not yet have any `.html` files:
```
gymtrack/app/templates/
├── base.html
├── auth/          ← existing html files
├── workouts/      ← existing html files
├── exercises/     ← existing html files
├── dashboard/     ← existing html files
├── admin/         ← existing html files
├── errors/        ← existing html files
└── progress/      ← EMPTY — create prs.html here (NEW)
```

The directory `gymtrack/app/templates/progress/` already exists (Flask will find it automatically). Just create `prs.html` inside it.

### Test Specifications for Task 4

Create `gymtrack/tests/test_progress.py` with local fixtures (same pattern as `test_workouts.py` — NOT using `conftest.py` fixtures):

```python
import datetime
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.exercise import Exercise
from app.models.personal_record import PersonalRecord
from app.models.user import User


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
    return client.post('/auth/login', data={'email': email, 'password': password},
                       follow_redirects=False)


def make_exercise(db, name='Squat', muscle_group='Legs'):
    exercise = Exercise(name=name, muscle_group=muscle_group)
    db.session.add(exercise)
    db.session.commit()
    return exercise


def make_personal_record(db, user_id, exercise_id, weight_kg=100.0, reps=5,
                          achieved_at=None):
    if achieved_at is None:
        achieved_at = datetime.datetime.utcnow()
    pr = PersonalRecord(
        user_id=user_id,
        exercise_id=exercise_id,
        weight_kg=weight_kg,
        reps=reps,
        achieved_at=achieved_at,
    )
    db.session.add(pr)
    db.session.commit()
    return pr


# ─── Story 5.4 — View All Personal Records ───

def test_pr_list_unauthenticated(client, app):
    """AC 1: unauthenticated GET /progress/prs/ → redirect to login."""
    with app.app_context():
        response = client.get('/progress/prs/')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']


def test_pr_list_shows_records_alphabetically(client, app):
    """AC 1: PRs are listed with exercise name, weight, reps, date — sorted A→Z."""
    with app.app_context():
        user = make_user(_db)
        squat = make_exercise(_db, name='Squat', muscle_group='Legs')
        bench = make_exercise(_db, name='Bench Press', muscle_group='Chest')
        deadlift = make_exercise(_db, name='Deadlift', muscle_group='Back')
        make_personal_record(_db, user.id, squat.id, weight_kg=120.0, reps=5)
        make_personal_record(_db, user.id, bench.id, weight_kg=80.0, reps=8)
        make_personal_record(_db, user.id, deadlift.id, weight_kg=150.0, reps=3)
        login_as(client, 'user@example.com', 'password123')
        response = client.get('/progress/prs/')
        assert response.status_code == 200
        html = response.data.decode()
        # All three exercises present
        assert 'Squat' in html
        assert 'Bench Press' in html
        assert 'Deadlift' in html
        # Values present
        assert '120.0' in html
        assert '80.0' in html
        assert '150.0' in html
        # Alphabetical order: Bench Press < Deadlift < Squat
        assert html.index('Bench Press') < html.index('Deadlift') < html.index('Squat')
        # No empty-state message
        assert 'No personal records yet' not in html


def test_pr_list_empty_state(client, app):
    """AC 2: user with no PRs sees the empty-state message."""
    with app.app_context():
        make_user(_db)
        login_as(client, 'user@example.com', 'password123')
        response = client.get('/progress/prs/')
        assert response.status_code == 200
        assert b'No personal records yet. Complete a workout to start tracking PRs.' in response.data


def test_pr_list_data_isolation(client, app):
    """AC 1: only the logged-in user's PRs are shown — not other users' PRs."""
    with app.app_context():
        user_a = make_user(_db, email='usera@example.com')
        user_b = make_user(_db, email='userb@example.com')
        exercise = make_exercise(_db, name='Pull-up', muscle_group='Back')
        # user_b has a PR; user_a has none
        make_personal_record(_db, user_b.id, exercise.id, weight_kg=90.0, reps=10)
        login_as(client, 'usera@example.com', 'password123')
        response = client.get('/progress/prs/')
        assert response.status_code == 200
        # user_a sees empty state — does NOT see user_b's PR
        assert b'No personal records yet' in response.data
        assert b'Pull-up' not in response.data
        assert b'90.0' not in response.data
```

### What NOT to Change

- Do NOT modify `PersonalRecord` model or its schema — already correct from Epic 5 prior stories
- Do NOT modify `detect_prs` service — this story is read-only display of already-stored PRs
- Do NOT remove or modify the `index()` placeholder route in `progress/routes.py` — Epic 6 stories will implement it
- Do NOT add Chart.js to the PRs page — this is a simple list, not a chart (charts are Epic 6)
- Do NOT flash messages for any action — this is a GET-only read page

### Project Structure Notes

- Blueprint: `app/blueprints/progress/` — `__init__.py` (has `progress_bp`, url_prefix `/progress`), `routes.py`
- Template dir: `app/templates/progress/` (exists but empty — create `prs.html` here)
- CSS: `app/static/css/style.css` — single file, BEM naming, vanilla CSS
- Test file: `gymtrack/tests/test_progress.py` — NEW file with local fixtures (no conftest.py sharing)
- Nav: `base.html` already has `url_for('progress.index')` link — no nav change needed for this story; the `/prs/` route is accessible via the existing Progress nav item navigating to the index or direct URL

### References

- [Source: epics.md, Story 5.4 — View All Personal Records (lines 690–707)]
- [Source: epics.md, FR27 — Users can view all current personal records per exercise]
- [Source: architecture.md, Code Organization — `blueprints/progress/` path and blueprint structure]
- [Source: architecture.md, Data Architecture — Multi-User Isolation Pattern, filter by `current_user.id`]
- [Source: architecture.md, Frontend Architecture — BEM CSS, single style.css, strftime Jinja filter]
- [Source: architecture.md, Enforcement Guidelines — routes in routes.py, snake_case, user_id filter mandatory]
- [Source: gymtrack/app/models/personal_record.py — PersonalRecord model fields and relationships]
- [Source: gymtrack/app/blueprints/progress/routes.py — current placeholder state]
- [Source: gymtrack/app/templates/workouts/session_list.html — BEM list template pattern to follow]
- [Source: gymtrack/tests/test_workouts.py — local fixture pattern for test files]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

Ultimate context engine analysis completed — comprehensive developer guide created.

### File List

- `gymtrack/tests/test_progress.py` — CREATED
- `gymtrack/app/blueprints/progress/routes.py` — UPDATED
- `gymtrack/app/templates/progress/prs.html` — CREATED
- `gymtrack/app/static/css/style.css` — UPDATED
