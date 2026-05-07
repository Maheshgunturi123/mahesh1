# Story 1.2: User Registration

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a new visitor,
I want to register an account with my email and password,
so that I can access GymTrack's features.

## Acceptance Criteria

1. **Given** I am on `/auth/register` **When** I submit a valid email and password (≥ 8 characters) **Then** my account is created with the password stored as a bcrypt hash (cost factor 12) — never plaintext, **And** I am redirected to the dashboard with a `success` flash: "Account created. Welcome to GymTrack!", **And** a `users` table row is created with `created_at` (UTC), `is_admin=False`.

2. **Given** I submit an email that already exists **When** the form is submitted **Then** I see a field-level error: "An account with this email already exists." **And** no duplicate record is created.

3. **Given** I submit an invalid email or password shorter than 8 characters **When** the form is submitted **Then** Flask-WTF validation errors are displayed adjacent to the relevant field **And** the form retains my previously entered values.

## Tasks / Subtasks

- [ ] Task 1: Create the `User` SQLAlchemy model (AC: 1)
  - [ ] Create `app/models/user.py` with `User` class
  - [ ] Define columns: `id` (PK), `email` (unique, nullable=False, 255), `password_hash` (nullable=False, 255), `is_admin` (Boolean, default=False), `created_at` (DateTime, default=datetime.utcnow)
  - [ ] Implement `set_password(plain)` method — uses `bcrypt.generate_password_hash(plain, rounds=12).decode('utf-8')`
  - [ ] Implement `check_password(plain)` method — uses `bcrypt.check_password_hash(self.password_hash, plain)`
  - [ ] Add Flask-Login mixin: `class User(UserMixin, db.Model)`
  - [ ] Register `user_loader` callback on `login_manager` in `app/models/user.py` or in `create_app()`
  - [ ] Export `User` from `app/models/__init__.py`
  - [ ] Create migration: `flask db migrate -m "add users table"` and `flask db upgrade`

- [ ] Task 2: Create the registration WTForms form (AC: 1, 2, 3)
  - [ ] Create `app/blueprints/auth/forms.py`
  - [ ] Define `RegistrationForm(FlaskForm)` with fields: `email` (EmailField, DataRequired, Email, Length max=255), `password` (PasswordField, DataRequired, Length min=8), `confirm_password` (PasswordField, DataRequired, EqualTo('password'))
  - [ ] Add custom validator `validate_email` that checks `User.query.filter_by(email=field.data).first()` — if found, raise `ValidationError("An account with this email already exists.")`
  - [ ] Add `submit` (SubmitField)

- [ ] Task 3: Create the registration route handler (AC: 1, 2, 3)
  - [ ] In `app/blueprints/auth/routes.py` add `@auth_bp.route('/register', methods=['GET', 'POST'])`
  - [ ] On GET: render `auth/register.html` with empty `RegistrationForm`
  - [ ] On POST valid form: create `User` instance, call `user.set_password(form.password.data)`, `db.session.add(user)`, `db.session.commit()`
  - [ ] After commit: `login_user(user)` then `flash('Account created. Welcome to GymTrack!', 'success')` then `redirect(url_for('dashboard.index'))`
  - [ ] On POST invalid form: re-render template (form errors retained automatically by Flask-WTF)
  - [ ] Add `@login_required` redirect for already-logged-in users: redirect to dashboard before rendering form

- [ ] Task 4: Create the registration HTML template (AC: 1, 2, 3)
  - [ ] Create `app/templates/auth/register.html` extending `base.html`
  - [ ] Form must include `{{ form.hidden_tag() }}` (CSRF token)
  - [ ] Render each field with `<label>` and adjacent inline error messages from `form.<field>.errors`
  - [ ] Retain previously entered values automatically (Flask-WTF re-populates on validation failure)
  - [ ] Mobile-first layout — touch targets ≥ 44px, single-column form
  - [ ] Link to `/auth/login` for users who already have an account
  - [ ] Use BEM CSS classes consistent with `style.css` (`auth-form`, `auth-form__field`, `auth-form__error`)

- [ ] Task 5: Write tests for registration (AC: 1, 2, 3)
  - [ ] Create/extend `tests/test_auth.py`
  - [ ] Test: successful registration creates user, redirects to dashboard, shows success flash
  - [ ] Test: duplicate email shows field-level error, no new user created
  - [ ] Test: password < 8 chars shows validation error, form retained
  - [ ] Test: invalid email format shows validation error
  - [ ] Test: password hash is NOT the same as plaintext (`user.password_hash != 'password'`)
  - [ ] Test: `user.is_admin` defaults to `False`
  - [ ] Test: `user.created_at` is set and is a UTC datetime
  - [ ] All tests use `test_db` fixture to isolate DB state per test

## Dev Notes

### Critical Architecture Requirements (MUST NOT deviate)

**User Model Location and Structure:**
- Model file: `app/models/user.py`
- Export from: `app/models/__init__.py` — `from app.models.user import User`
- Table name: `users` (plural snake_case — see architecture.md#Naming Patterns)
- NEVER call the table `user` or `User` — Flask-SQLAlchemy reserves `user`

**Flask-Login Integration:**
```python
# app/models/user.py
from flask_login import UserMixin
from app.extensions import db, bcrypt, login_manager
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, plain_password):
        self.password_hash = bcrypt.generate_password_hash(plain_password, rounds=12).decode('utf-8')

    def check_password(self, plain_password):
        return bcrypt.check_password_hash(self.password_hash, plain_password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

**Password Hashing — Non-Negotiable:**
- Library: `flask-bcrypt` (already in `requirements.txt` from Story 1.1)
- Work factor: `rounds=12` (NFR5)
- NEVER store or log plaintext passwords
- `bcrypt` instance is imported from `app.extensions` — already initialized there

**Blueprint File Pattern (from Story 1.1):**
```
app/blueprints/auth/
├── __init__.py    # auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
├── routes.py      # ALL route handlers (including register route)
├── forms.py       # RegistrationForm and other forms — CREATE THIS FILE
└── utils.py       # optional
```
Story 1.1 created blueprint stub. This story ADDS `forms.py` and populates `routes.py`.

**Route Handler Pattern:**
```python
# app/blueprints/auth/routes.py
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, login_required
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import RegistrationForm
from app.models import User
from app.extensions import db

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created. Welcome to GymTrack!', 'success')
        return redirect(url_for('dashboard.index'))
    return render_template('auth/register.html', form=form)
```

**Form Definition Pattern:**
```python
# app/blueprints/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                      validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('An account with this email already exists.')
```

**Dashboard Blueprint Dependency:**
- Story 1.1 created a stub `dashboard` blueprint with a placeholder route
- The redirect `url_for('dashboard.index')` requires that stub to remain in place
- Do NOT change the dashboard blueprint — just confirm the route name `dashboard.index` exists in the stub

**Flash Message Categories — ONLY these 4:**
- `success` — confirmation messages (used in this story: account created)
- `error` — error messages
- `info` — informational
- `warning` — warnings
- NEVER use: `ok`, `danger`, `primary`, `secondary`

**CSRF:**
- `{{ form.hidden_tag() }}` MUST be in every form POST template
- WTF_CSRF_ENABLED=True in dev/prod, False only in TestingConfig (already set in Story 1.1)

### Database Migration

After creating `User` model:
```bash
flask db migrate -m "add users table"
flask db upgrade
```
- Migrations live in `migrations/` — committed to repo
- Never hand-edit migration files
- The `migrations/` directory was initialized in Story 1.1 via `flask db init`

### Template Structure

```html
<!-- app/templates/auth/register.html -->
{% extends 'base.html' %}
{% block title %}Register — GymTrack{% endblock %}
{% block content %}
<div class="auth-form">
  <h1 class="auth-form__title">Create Account</h1>
  <form method="POST" action="{{ url_for('auth.register') }}" novalidate>
    {{ form.hidden_tag() }}

    <div class="auth-form__field">
      {{ form.email.label }}
      {{ form.email(class="auth-form__input") }}
      {% for error in form.email.errors %}
        <span class="auth-form__error">{{ error }}</span>
      {% endfor %}
    </div>

    <div class="auth-form__field">
      {{ form.password.label }}
      {{ form.password(class="auth-form__input") }}
      {% for error in form.password.errors %}
        <span class="auth-form__error">{{ error }}</span>
      {% endfor %}
    </div>

    <div class="auth-form__field">
      {{ form.confirm_password.label }}
      {{ form.confirm_password(class="auth-form__input") }}
      {% for error in form.confirm_password.errors %}
        <span class="auth-form__error">{{ error }}</span>
      {% endfor %}
    </div>

    {{ form.submit(class="auth-form__submit") }}
  </form>
  <p>Already have an account? <a href="{{ url_for('auth.login') }}">Log in</a></p>
</div>
{% endblock %}
```

### Files Being Modified (from Story 1.1 scaffold)

The following files from Story 1.1 are being extended (NOT replaced):

| File | Change Type | What Changes |
|------|-------------|--------------|
| `app/blueprints/auth/routes.py` | UPDATE | Add `/register` route handler |
| `app/models/__init__.py` | UPDATE | Export `User` |
| `app/extensions.py` | VERIFY | `bcrypt` and `login_manager` already there |
| `app/__init__.py` | VERIFY | `login_manager.init_app(app)` already called |

New files created by this story:

| File | Change Type |
|------|-------------|
| `app/models/user.py` | NEW |
| `app/blueprints/auth/forms.py` | NEW |
| `app/templates/auth/register.html` | NEW |
| `tests/test_auth.py` | NEW |

### Previous Story Intelligence (Story 1.1)

From Story 1.1 scaffold:
- `app/extensions.py` already has `db`, `login_manager`, `bcrypt` instantiated without app
- `app/__init__.py` `create_app()` already calls `db.init_app(app)`, `login_manager.init_app(app)`, `bcrypt.init_app(app)`
- `app/blueprints/auth/__init__.py` already defines `auth_bp = Blueprint('auth', __name__, url_prefix='/auth')`
- `tests/conftest.py` already has `test_app`, `test_client`, `test_db` fixtures with `WTF_CSRF_ENABLED=False` in TestingConfig
- `requirements.txt` already includes `flask-bcrypt>=1.0`, `flask-wtf>=1.2`, `flask-login>=0.6`
- Story 1.1 established: routes NEVER in `__init__.py`, forms NEVER in `routes.py`
- Blueprint url_prefix for auth is `/auth` — routes in this story will be `/auth/register`

### Testing Pattern

```python
# tests/test_auth.py
import pytest
from app.models import User

def test_register_success(test_client, test_db):
    response = test_client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created. Welcome to GymTrack!' in response.data
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.password_hash != 'securepass123'
    assert user.is_admin is False
    assert user.created_at is not None

def test_register_duplicate_email(test_client, test_db):
    # First registration
    test_client.post('/auth/register', data={
        'email': 'dup@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    })
    # Second with same email
    response = test_client.post('/auth/register', data={
        'email': 'dup@example.com',
        'password': 'anotherpass123',
        'confirm_password': 'anotherpass123',
    })
    assert b'An account with this email already exists.' in response.data
    assert User.query.filter_by(email='dup@example.com').count() == 1

def test_register_short_password(test_client, test_db):
    response = test_client.post('/auth/register', data={
        'email': 'short@example.com',
        'password': 'short',
        'confirm_password': 'short',
    })
    assert response.status_code == 200  # re-renders form
    assert User.query.filter_by(email='short@example.com').first() is None
```

### Non-Functional Requirements for this Story

- NFR5: bcrypt hash with work factor 12 — enforced via `rounds=12` in `set_password()`
- NFR6: HTTPS enforced at Railway platform level — no code change needed
- NFR17: All form inputs have `<label>` elements — enforced in template (use WTForms label rendering)
- NFR18: Text contrast ≥ 4.5:1 — use existing `style.css` color variables
- NFR19: Error messages descriptive and adjacent to fields — enforced in template pattern above

### Project Structure Notes

- Alignment: all files follow the architecture spec from `architecture.md`
- `app/models/` directory was created (empty) in Story 1.1 — add `user.py` here
- `app/blueprints/auth/` was scaffolded in Story 1.1 — extend only, do not reorganize
- Dashboard blueprint stub from Story 1.1 (`url_for('dashboard.index')`) must exist before this story's redirect works — confirm stub route exists

### References

- [Source: epics.md#Story 1.2: User Registration] — User story and acceptance criteria
- [Source: architecture.md#Authentication & Security] — bcrypt work factor 12, Flask-Login session, CSRF
- [Source: architecture.md#Naming Patterns] — `users` table name, column naming conventions
- [Source: architecture.md#Blueprint Internal Structure] — forms.py pattern, routes.py pattern
- [Source: architecture.md#Format Patterns] — flash message categories
- [Source: architecture.md#Enforcement Guidelines] — mandatory query scoping, anti-patterns
- [Source: architecture.md#Structure Patterns] — service layer, test structure
- [Source: story 1-1-project-scaffold-and-base-configuration.md] — existing extensions, fixtures, config patterns

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

- Flask 3.x reuses parent app context for test requests → `g._login_user` persists; fixed by pushing fresh `app_context()` per test
- Template `url_for('auth.login')` needed stub route (Story 1.3 placeholder added)
- `test_register_duplicate_email` needed direct DB insert to avoid login side-effect from first POST

### Completion Notes List

- All 7 AC tests pass; 11/11 suite green
- Stub `/auth/login` added to routes.py (Story 1.3 will replace)
- Migrations initialized and applied; `users` table created

### File List

- `app/models/user.py` — NEW
- `app/models/__init__.py` — UPDATED
- `app/blueprints/auth/forms.py` — NEW
- `app/blueprints/auth/routes.py` — UPDATED
- `app/templates/auth/register.html` — NEW
- `tests/test_auth.py` — NEW
- `migrations/` — INITIALIZED + migration `9953be62afb7_add_users_table.py`
