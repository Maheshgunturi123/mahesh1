# Story 2.2: Exercise Search & Filter

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to search exercises by name and filter by muscle group,
so that I can quickly find the exercise I need.

## Acceptance Criteria

1. **Given** I am on `/exercises/` and type a search term in the search input **When** I submit the search form **Then** the list shows only exercises whose name contains the search term (case-insensitive) **And** the search term is preserved in the search input field after submission.

2. **Given** I select a muscle group from the filter dropdown **When** the filter is applied **Then** the list shows only exercises matching that muscle group **And** the selected muscle group is preserved in the dropdown after submission.

3. **Given** I enter a search term AND select a muscle group **When** the filter is applied **Then** both criteria are combined — only exercises matching name AND muscle group are shown.

4. **Given** no exercises match the search/filter criteria **When** the page renders **Then** I see: "No exercises found matching your search."

5. **Given** the filtered result set spans multiple pages **When** I navigate to the next/previous page **Then** the search term and muscle group filter are preserved in the URL and applied to the subsequent page.

## Tasks / Subtasks

- [x] Task 1: Create `ExerciseFilterForm` in `forms.py` (AC: 1, 2, 3)
  - [x] Create `gymtrack/app/blueprints/exercises/forms.py` — NEW file
  - [x] Define `ExerciseFilterForm(FlaskForm)` with `class Meta: csrf = False` (GET form — CSRF not required)
  - [x] Fields: `search` (`StringField`, `Optional()`), `muscle_group` (`SelectField`, `Optional()`, `choices=[]`), `submit` (`SubmitField('Search')`)
  - [x] Do NOT hardcode muscle group choices — they are populated dynamically from the DB in the route

- [x] Task 2: Update `index` route to support search and filter (AC: 1, 2, 3, 4, 5)
  - [x] Update `gymtrack/app/blueprints/exercises/routes.py`
  - [x] Import `ExerciseFilterForm` from `app.blueprints.exercises.forms` and `db` from `app.extensions`
  - [x] Instantiate form with `ExerciseFilterForm(request.args)` to prepopulate from GET params
  - [x] Build distinct muscle group list: `db.session.query(Exercise.muscle_group).distinct().order_by(Exercise.muscle_group).all()` — set `form.muscle_group.choices = [('', 'All Muscle Groups')] + [(m, m) for m in muscle_groups]`
  - [x] Read `search = request.args.get('search', '').strip()` and `muscle_group_filter = request.args.get('muscle_group', '').strip()`
  - [x] Build query: start with `Exercise.query.order_by(Exercise.name)`
  - [x] Apply name filter if `search`: `.filter(Exercise.name.ilike(f'%{search}%'))`
  - [x] Apply muscle group filter if `muscle_group_filter`: `.filter(Exercise.muscle_group == muscle_group_filter)`
  - [x] Paginate as before: `.paginate(page=page, per_page=20, error_out=False)`
  - [x] Pass to template: `exercises`, `form`, `search`, `muscle_group` (for pagination link construction)

- [x] Task 3: Update exercise list template (AC: 1, 2, 3, 4, 5)
  - [x] Update `gymtrack/app/templates/exercises/index.html`
  - [x] Add search/filter form above the table using GET method: `<form method="GET" action="{{ url_for('exercises.index') }}">`
  - [x] Add labeled text input for search: `<label for="search">Search</label>` + `{{ form.search(id="search", value=search) }}`
  - [x] Add labeled select for muscle group: `<label for="muscle_group">Muscle Group</label>` + `{{ form.muscle_group(id="muscle_group") }}`
  - [x] Add submit button: `{{ form.submit() }}`
  - [x] Change empty-state message to: "No exercises found matching your search." when search or filter is active; keep "No exercises found." when no filters applied
  - [x] Update pagination links to pass `search` and `muscle_group` query params so filters persist across pages: `url_for('exercises.index', page=exercises.prev_num, search=search, muscle_group=muscle_group)`
  - [x] Use BEM CSS classes for the form: `exercise-filter`, `exercise-filter__field`, `exercise-filter__label`, `exercise-filter__input`, `exercise-filter__select`, `exercise-filter__submit`
  - [x] All form inputs MUST have `<label>` elements (UX-DR10 / NFR17 accessibility)
  - [x] Add `aria-label` to the form for screen reader clarity

- [x] Task 4: Update CSS for search form styles (AC: 1, 2)
  - [x] Update `gymtrack/app/static/css/style.css` — ADD exercise-filter BEM classes
  - [x] Do NOT create a new CSS file; add to the existing `style.css`
  - [x] Ensure touch targets ≥ 44px for all form controls (UX-DR1, mobile-first)

- [x] Task 5: Update tests for search and filter (AC: 1, 2, 3, 4, 5)
  - [x] Update `gymtrack/tests/test_exercises.py` — ADD new test functions
  - [x] Test: search by name (partial, case-insensitive) → only matching exercises returned
  - [x] Test: filter by muscle group → only matching exercises returned
  - [x] Test: combined search + filter → only exercises matching both are returned
  - [x] Test: no matches → 200 response, "No exercises found matching your search." in body
  - [x] Test: pagination preserves search param (create > 20 exercises, request page 2 with search)
  - [x] Keep all existing tests intact — do NOT remove or modify existing tests in this file

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**Search/filter uses GET, not POST — no CSRF token needed:**
- Search and filter are read-only operations; the form MUST use `method="GET"`.
- Flask-WTF's CSRF protection applies to state-changing endpoints only (POST/PUT/DELETE).
- Disable CSRF on the form class with `class Meta: csrf = False`.
- Do NOT add `{{ form.hidden_tag() }}` to the search form (it would inject an unnecessary hidden field into GET params).

**Existing `index` route — UPDATE, do not replace entirely:**
- Current state: `gymtrack/app/blueprints/exercises/routes.py` has a single `index()` route querying all exercises with `Exercise.query.order_by(Exercise.name).paginate(...)`.
- Story 2.2 extends this route by adding search/filter query param handling before the `.paginate()` call.
- The `@login_required` decorator and pagination logic MUST be preserved.
- The route MUST remain at `GET /` — no route URL change.

**Existing template `index.html` — UPDATE, do not recreate:**
- Current state: renders a paginated table + pagination nav. BEM classes already in place.
- Story 2.2 prepends a search/filter form and updates: the empty-state message, the pagination link `url_for()` calls.
- Do NOT rename or move the template file.
- Preserve all existing BEM classes; only ADD new `exercise-filter__*` classes.

**Muscle group choices — dynamically populated from DB:**
- Do NOT hardcode a list of muscle groups in `forms.py`.
- The `SelectField.choices` must be set in the route handler AFTER querying distinct values from the DB: `db.session.query(Exercise.muscle_group).distinct().order_by(Exercise.muscle_group).all()`
- This ensures the filter always reflects the actual data in the library.

**Case-insensitive search — use `ilike`:**
- SQLAlchemy's `.ilike()` maps to SQL `ILIKE` on PostgreSQL (native) and `LIKE` with `LOWER()` on SQLite.
- Pattern: `Exercise.name.ilike(f'%{search}%')` — wraps the term with `%` wildcards for substring match.
- Never use Python-side filtering; push filter to the DB query.

**Pagination URL construction with filters:**
- When rendering pagination next/previous links, pass all active filter params to preserve search state:
  ```jinja2
  {{ url_for('exercises.index', page=exercises.prev_num, search=search, muscle_group=muscle_group) }}
  ```
- If `search` or `muscle_group` are empty strings, Flask's `url_for` omits them from the URL automatically.

**No new imports beyond what's already available:**
- `db` is already in `app.extensions` — import it in `routes.py`: `from app.extensions import db`
- `request` is already imported in `routes.py`
- `SelectField`, `StringField`, `SubmitField` from `wtforms`; `Optional` from `wtforms.validators`; `FlaskForm` from `flask_wtf`

**Blueprint structure — forms.py is NEW for this blueprint:**
- Story 2.1 explicitly noted: "This story requires no form — do NOT create `forms.py` for story 2.1 (that belongs to story 2.2+)."
- Create `gymtrack/app/blueprints/exercises/forms.py` as a NEW file in this story.
- Only form definition logic goes in `forms.py`; all route logic stays in `routes.py`.

### Previous Story Learnings (from Story 2.1)

- `flask db init` was required before migrations; the migrations directory and `alembic.ini` are now in place — do NOT re-run `flask db init`.
- Pre-existing failing test: `test_config.py::test_testing_config_uses_in_memory_sqlite` — NOT related to exercises; do not attempt to fix it in this story.
- `Exercise` model is already imported in `app/models/__init__.py`; no model changes needed for this story.
- `exercises_bp` is already registered in `create_app()` — do not re-register.
- `login_manager.login_view = 'auth.login'` is set in `app/extensions.py` — `@login_required` redirects automatically.
- Test helper pattern established in Story 2.1:
  ```python
  def make_exercise(db, name='Bench Press', muscle_group='Chest', description='Flat barbell press'):
      ex = Exercise(name=name, muscle_group=muscle_group, description=description)
      db.session.add(ex)
      db.session.commit()
      return ex
  ```
  Reuse this helper; do not duplicate it.

### Project Structure — Files to Create/Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `gymtrack/app/blueprints/exercises/forms.py` | NEW | `ExerciseFilterForm` WTForms class with CSRF disabled |
| `gymtrack/app/blueprints/exercises/routes.py` | UPDATE | Add search/filter query param handling to `index()` route |
| `gymtrack/app/templates/exercises/index.html` | UPDATE | Add search form, update empty state message, update pagination links |
| `gymtrack/app/static/css/style.css` | UPDATE | Add `exercise-filter__*` BEM classes |
| `gymtrack/tests/test_exercises.py` | UPDATE | Add search and filter test functions |

### Code Reference — ExerciseFilterForm

```python
# gymtrack/app/blueprints/exercises/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import Optional


class ExerciseFilterForm(FlaskForm):
    class Meta:
        csrf = False  # GET form — CSRF not required

    search = StringField('Search by Name', validators=[Optional()])
    muscle_group = SelectField('Muscle Group', validators=[Optional()], choices=[])
    submit = SubmitField('Search')
```

### Code Reference — Updated Route

```python
# gymtrack/app/blueprints/exercises/routes.py
import logging
from flask import render_template, request
from flask_login import login_required
from app.blueprints.exercises import exercises_bp
from app.blueprints.exercises.forms import ExerciseFilterForm
from app.extensions import db
from app.models.exercise import Exercise

logger = logging.getLogger(__name__)


@exercises_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    muscle_group_filter = request.args.get('muscle_group', '').strip()

    # Build muscle group choices dynamically from DB
    muscle_groups = [
        m[0] for m in
        db.session.query(Exercise.muscle_group).distinct().order_by(Exercise.muscle_group).all()
    ]
    form = ExerciseFilterForm(request.args)
    form.muscle_group.choices = [('', 'All Muscle Groups')] + [(m, m) for m in muscle_groups]

    query = Exercise.query.order_by(Exercise.name)
    if search:
        query = query.filter(Exercise.name.ilike(f'%{search}%'))
    if muscle_group_filter:
        query = query.filter(Exercise.muscle_group == muscle_group_filter)

    exercises = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'exercises/index.html',
        exercises=exercises,
        form=form,
        search=search,
        muscle_group=muscle_group_filter,
    )
```

### Code Reference — Template Changes (key sections)

```jinja2
{# Search/filter form — add ABOVE the existing table/empty-state block #}
<form class="exercise-filter" method="GET" action="{{ url_for('exercises.index') }}" aria-label="Search and filter exercises">
  <div class="exercise-filter__field">
    <label class="exercise-filter__label" for="search">Search by Name</label>
    <input class="exercise-filter__input" type="text" id="search" name="search" value="{{ search }}">
  </div>
  <div class="exercise-filter__field">
    <label class="exercise-filter__label" for="muscle_group">Muscle Group</label>
    <select class="exercise-filter__select" id="muscle_group" name="muscle_group">
      {% for value, label in form.muscle_group.choices %}
        <option value="{{ value }}" {% if value == muscle_group %}selected{% endif %}>{{ label }}</option>
      {% endfor %}
    </select>
  </div>
  <button class="exercise-filter__submit" type="submit">Search</button>
</form>

{# Updated empty-state logic #}
{% if exercises.total == 0 %}
  {% if search or muscle_group %}
    <p class="exercise-library__empty">No exercises found matching your search.</p>
  {% else %}
    <p class="exercise-library__empty">No exercises found.</p>
  {% endif %}

{# Updated pagination links (example for prev link) #}
<a href="{{ url_for('exercises.index', page=exercises.prev_num, search=search, muscle_group=muscle_group) }}" ...>← Previous</a>
```

### Code Reference — Test Additions

```python
# gymtrack/tests/test_exercises.py  (additions only — keep existing tests)

def test_search_by_name_partial_match(test_client, test_db):
    login(test_client, test_db)
    make_exercise(test_db, name='Bench Press', muscle_group='Chest')
    make_exercise(test_db, name='Overhead Press', muscle_group='Shoulders')
    make_exercise(test_db, name='Squat', muscle_group='Legs')
    resp = test_client.get('/exercises/?search=press')
    assert resp.status_code == 200
    assert b'Bench Press' in resp.data
    assert b'Overhead Press' in resp.data
    assert b'Squat' not in resp.data


def test_search_case_insensitive(test_client, test_db):
    login(test_client, test_db)
    make_exercise(test_db, name='Bench Press', muscle_group='Chest')
    resp = test_client.get('/exercises/?search=BENCH')
    assert resp.status_code == 200
    assert b'Bench Press' in resp.data


def test_filter_by_muscle_group(test_client, test_db):
    login(test_client, test_db)
    make_exercise(test_db, name='Bench Press', muscle_group='Chest')
    make_exercise(test_db, name='Squat', muscle_group='Legs')
    resp = test_client.get('/exercises/?muscle_group=Chest')
    assert resp.status_code == 200
    assert b'Bench Press' in resp.data
    assert b'Squat' not in resp.data


def test_combined_search_and_filter(test_client, test_db):
    login(test_client, test_db)
    make_exercise(test_db, name='Bench Press', muscle_group='Chest')
    make_exercise(test_db, name='Cable Fly', muscle_group='Chest')
    make_exercise(test_db, name='Overhead Press', muscle_group='Shoulders')
    resp = test_client.get('/exercises/?search=press&muscle_group=Chest')
    assert resp.status_code == 200
    assert b'Bench Press' in resp.data
    assert b'Cable Fly' not in resp.data
    assert b'Overhead Press' not in resp.data


def test_no_match_shows_search_empty_message(test_client, test_db):
    login(test_client, test_db)
    make_exercise(test_db, name='Squat', muscle_group='Legs')
    resp = test_client.get('/exercises/?search=nonexistent')
    assert resp.status_code == 200
    assert b'No exercises found matching your search.' in resp.data
```

### References

- Story acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#Story-2.2]
- Blueprint structure (forms.py): [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint-Internal-Structure]
- Flask-WTF CSRF pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication-&-Security]
- Form validation pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Form-Validation-Pattern]
- Naming conventions: [Source: _bmad-output/planning-artifacts/architecture.md#Naming-Patterns]
- CSS / BEM pattern: [Source: _bmad-output/planning-artifacts/architecture.md#CSS-Organization]
- Logging pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Error-Logging-Pattern]
- Test structure: [Source: _bmad-output/planning-artifacts/architecture.md#Test-Structure]
- Previous story implementation notes: [Source: _bmad-output/implementation-artifacts/2-1-exercise-library-browse.md#Dev-Agent-Record]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

None — clean run.

### Completion Notes List

- `forms.py` created new as specified; CSRF disabled via `class Meta: csrf = False`.
- Route updated: dynamic muscle group choices from DB, ilike search, paginated with filter params passed to template.
- Template updated: search/filter form prepended, empty-state conditional, pagination links preserve `search` and `muscle_group` params.
- CSS updated: `exercise-filter__*` BEM classes added with `min-height: 44px` touch targets on all controls.
- 6 new tests added; all 10 tests pass (4 pre-existing + 6 new).

### File List

- `gymtrack/app/blueprints/exercises/forms.py` — CREATED
- `gymtrack/app/blueprints/exercises/routes.py` — UPDATED
- `gymtrack/app/templates/exercises/index.html` — UPDATED
- `gymtrack/app/static/css/style.css` — UPDATED
- `gymtrack/tests/test_exercises.py` — UPDATED
