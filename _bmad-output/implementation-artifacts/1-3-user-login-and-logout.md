# Story 1.3: User Login & Logout

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a registered user,
I want to log in and out of my account,
so that my data is accessible only to me.

## Acceptance Criteria

1. **Given** I am on `/auth/login` with valid credentials **When** I submit the form **Then** I am logged in via Flask-Login and redirected to `/dashboard/`, **And** my session persists for 30 days of inactivity (`PERMANENT_SESSION_LIFETIME`).

2. **Given** I submit incorrect credentials **When** the form is submitted **Then** I see an `error` flash: "Invalid email or password." (no indication of which field is wrong), **And** I remain on the login page.

3. **Given** I am logged in and click Logout **When** `/auth/logout` is visited **Then** my session is cleared (cookie deleted), **And** I am redirected to `/auth/login` with an `info` flash: "You have been logged out."

4. **Given** I try to access a `@login_required` route while logged out **When** the request is made **Then** I am redirected to `/auth/login` with the original URL preserved as `next` parameter.

## Tasks / Subtasks

- [ ] Task 1: Create the `LoginForm` WTForms class (AC: 1, 2)
  - [ ] Add `LoginForm(FlaskForm)` to existing `app/blueprints/auth/forms.py`
  - [ ] Fields: `email` (StringField, DataRequired, Email, Length max=255), `password` (PasswordField, DataRequired), `submit` (SubmitField 'Log In')
  - [ ] No custom validators on the form — credential check happens in the route handler

- [ ] Task 2: Add login route handler (AC: 1, 2, 4)
  - [ ] In `app/blueprints/auth/routes.py` add `@auth_bp.route('/login', methods=['GET', 'POST'])`
  - [ ] On GET: if `current_user.is_authenticated` redirect to `dashboard.index`; else render `auth/login.html` with empty `LoginForm`
  - [ ] On POST valid form: query `User.query.filter_by(email=form.email.data.lower()).first()`
  - [ ] If user exists AND `user.check_password(form.password.data)`: call `login_user(user)`, handle `next` param redirect, else flash `error` "Invalid email or password." and re-render template
  - [ ] `next` redirect security: use `url_parse(next_page).netloc == ''` (from `urllib.parse import urlparse as url_parse`) to reject open redirects — only redirect to relative URLs
  - [ ] Default post-login redirect: `url_for('dashboard.index')`

- [ ] Task 3: Add logout route handler (AC: 3)
  - [ ] In `app/blueprints/auth/routes.py` add `@auth_bp.route('/logout')` with `@login_required`
  - [ ] Call `logout_user()`, then `flash('You have been logged out.', 'info')`, then `redirect(url_for('auth.login'))`

- [ ] Task 4: Verify `login_manager.login_view` is set (AC: 4)
  - [ ] In `app/extensions.py` (or `app/__init__.py`) confirm `login_manager.login_view = 'auth.login'` is set — this ensures `@login_required` redirects to `/auth/login?next=<original_url>`
  - [ ] If missing, add it in `extensions.py` after `login_manager = LoginManager()` or in `create_app()` after `login_manager.init_app(app)`

- [ ] Task 5: Create the login HTML template (AC: 1, 2, 4)
  - [ ] Create `app/templates/auth/login.html` extending `base.html`
  - [ ] Form `action="{{ url_for('auth.login') }}"` with `method="POST"` and `novalidate`
  - [ ] Include `{{ form.hidden_tag() }}` (CSRF token)
  - [ ] Render `email` and `password` fields with `<label>` and adjacent `auth-form__error` spans
  - [ ] Submit button with class `auth-form__submit`
  - [ ] Link to `/auth/register` for new users
  - [ ] Link to `/auth/forgot-password` for password reset (Story 1.4 will implement the route — use the URL directly or `url_for('auth.forgot_password')` stub)
  - [ ] Mobile-first layout: touch targets ≥ 44px, single-column, BEM classes (`auth-form`, `auth-form__field`, `auth-form__input`, `auth-form__error`)

- [ ] Task 6: Write tests for login and logout (AC: 1, 2, 3, 4)
  - [ ] Extend existing `tests/test_auth.py`
  - [ ] Test: successful login redirects to dashboard, user is authenticated
  - [ ] Test: wrong password → error flash "Invalid email or password.", not redirected
  - [ ] Test: unknown email → error flash "Invalid email or password.", not redirected
  - [ ] Test: login with valid credentials then logout → session cleared, redirected to `/auth/login`, info flash shown
  - [ ] Test: `@login_required` route while logged out → redirected to `/auth/login` with `next` in query string
  - [ ] Test: already-authenticated user visiting `/auth/login` → redirected to dashboard (not shown form again)
  - [ ] All tests use `test_db` fixture for DB isolation; `WTF_CSRF_ENABLED=False` already in TestingConfig

## Dev Notes

### Critical Architecture Requirements (MUST NOT deviate)

**Flask-Login Session Pattern:**
```python
# app/blueprints/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlparse as url_parse
from flask_login import login_user, logout_user, current_user, login_required
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.models import User

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', form=form)
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        return redirect(next_page)
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
```

**`login_manager.login_view` — Non-Negotiable:**
- Must be set to `'auth.login'` for `@login_required` to redirect correctly
- Without this setting, `@login_required` raises a 401 instead of redirecting to login
- Set it in `app/extensions.py` after `login_manager = LoginManager()`:
```python
# app/extensions.py
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'  # optional: flash category for auto-message
```

**Open Redirect Prevention (Security Critical):**
- Always validate the `next` parameter before redirecting
- `url_parse(next_page).netloc != ''` means the URL has a domain → potential open redirect → reject it
- Only allow relative paths (no domain/scheme): `netloc == ''` is safe
- This pattern is from Flask's official documentation and Miguel Grinberg's Flask Mega-Tutorial

**Session Lifetime:**
- `PERMANENT_SESSION_LIFETIME` is already set in `config.py` from Story 1.1 scaffold
- Flask-Login's `login_user(user)` does NOT automatically make the session permanent
- To honor the 30-day lifetime: call `login_user(user, remember=True)` OR set `session.permanent = True` before or after `login_user()`
- Recommended: use `login_user(user)` and set `session.permanent = True` explicitly (no "Remember Me" checkbox needed for V1):
```python
from flask import session as flask_session
login_user(user)
flask_session.permanent = True
```

**Flash Message Categories — ONLY these 4:**
- `success` — account creation, password reset confirmation
- `error` — invalid credentials (this story)
- `info` — logout confirmation (this story), login_manager auto-message
- `warning` — general warnings
- NEVER use: `ok`, `danger`, `primary`, `secondary`

**CSRF:**
- `{{ form.hidden_tag() }}` MUST be in the login form template
- `WTF_CSRF_ENABLED=False` only in `TestingConfig` (already configured in Story 1.1)

### LoginForm Definition

```python
# Add to app/blueprints/auth/forms.py (do not replace existing RegistrationForm)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
```

### Template Structure

```html
<!-- app/templates/auth/login.html -->
{% extends 'base.html' %}
{% block title %}Log In — GymTrack{% endblock %}
{% block content %}
<div class="auth-form">
  <h1 class="auth-form__title">Log In</h1>
  <form method="POST" action="{{ url_for('auth.login') }}" novalidate>
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

    {{ form.submit(class="auth-form__submit") }}
  </form>
  <p>Don't have an account? <a href="{{ url_for('auth.register') }}">Register</a></p>
  <p><a href="/auth/forgot-password">Forgot your password?</a></p>
</div>
{% endblock %}
```

### Files Being Modified

The following files from Stories 1.1 & 1.2 are being extended (NOT replaced):

| File | Change Type | What Changes |
|------|-------------|--------------|
| `app/blueprints/auth/routes.py` | UPDATE | Add `/login` and `/logout` route handlers |
| `app/blueprints/auth/forms.py` | UPDATE | Add `LoginForm` class (keep `RegistrationForm`) |
| `app/extensions.py` | VERIFY/UPDATE | Confirm `login_manager.login_view = 'auth.login'` is set |
| `tests/test_auth.py` | UPDATE | Add login/logout test cases |

New files created by this story:

| File | Change Type |
|------|-------------|
| `app/templates/auth/login.html` | NEW |

### Previous Story Intelligence (Story 1.2)

From Story 1.2 patterns already established:
- `User` model is in `app/models/user.py`, exported from `app/models/__init__.py`
- `User.check_password(plain)` already implemented — uses `bcrypt.check_password_hash`
- `app/blueprints/auth/__init__.py` defines `auth_bp = Blueprint('auth', __name__, url_prefix='/auth')`
- `app/blueprints/auth/forms.py` already exists with `RegistrationForm` — ADD `LoginForm` alongside it
- `app/blueprints/auth/routes.py` already has `/register` handler — ADD login/logout alongside it
- Template BEM classes established: `auth-form`, `auth-form__field`, `auth-form__input`, `auth-form__error`, `auth-form__submit`
- `tests/test_auth.py` already exists — extend it, do not replace
- `tests/conftest.py` has `test_app`, `test_client`, `test_db` fixtures; `WTF_CSRF_ENABLED=False` in TestingConfig
- `login_user()` was already imported in routes.py for Story 1.2 (after register, auto-login) — also import `logout_user`, `login_required`
- `url_for('dashboard.index')` is the valid post-login redirect — confirmed in Story 1.2

### Testing Pattern

```python
# tests/test_auth.py — extend existing file

import pytest
from app.models import User

# Helper to register a user first (reuse or create fixture)
def register_user(client, email='user@example.com', password='testpass123'):
    client.post('/auth/register', data={
        'email': email,
        'password': password,
        'confirm_password': password,
    })

def test_login_success(test_client, test_db):
    register_user(test_client)
    response = test_client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'testpass123',
    }, follow_redirects=True)
    assert response.status_code == 200
    # Should reach dashboard (or its placeholder)
    assert b'Invalid email or password' not in response.data

def test_login_wrong_password(test_client, test_db):
    register_user(test_client)
    response = test_client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'wrongpassword',
    })
    assert b'Invalid email or password.' in response.data
    assert response.status_code == 200  # re-renders form

def test_login_unknown_email(test_client, test_db):
    response = test_client.post('/auth/login', data={
        'email': 'nobody@example.com',
        'password': 'anypassword',
    })
    assert b'Invalid email or password.' in response.data

def test_logout(test_client, test_db):
    register_user(test_client)
    test_client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'testpass123',
    })
    response = test_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data

def test_login_required_redirect(test_client, test_db):
    # Access a @login_required route without being logged in
    # Example: /dashboard/ or any protected route from Story 1.1 stub
    response = test_client.get('/dashboard/')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']
    assert 'next' in response.headers['Location']

def test_already_authenticated_redirected_from_login(test_client, test_db):
    register_user(test_client)
    test_client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'testpass123',
    })
    response = test_client.get('/auth/login')
    assert response.status_code == 302
    assert 'dashboard' in response.headers['Location']
```

### Non-Functional Requirements for this Story

- **NFR7:** Sessions expire after 30 days of inactivity — enforced via `PERMANENT_SESSION_LIFETIME` + `session.permanent = True`
- **NFR5:** Passwords never logged or compared in plaintext — `check_password()` delegates to bcrypt
- **NFR6:** HTTPS at platform level (Railway) — `SESSION_COOKIE_SECURE=True` already in `ProductionConfig`
- **NFR17:** All form inputs have `<label>` elements — enforced in template using WTForms label rendering
- **NFR18:** Text contrast ≥ 4.5:1 — use existing `style.css` color variables
- **NFR19:** Error messages descriptive and adjacent to fields — match pattern from `register.html`

### Project Structure Notes

- Alignment with unified project structure: all files follow established `app/blueprints/auth/` pattern
- No new directories created by this story — all files go into existing directories
- `url_for('auth.login')` is the string endpoint used by `login_manager.login_view` — **must match** the function name `def login()` inside the `auth` blueprint

### References

- Acceptance criteria source: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- Flask-Login session pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- NFR7 session expiry: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- Security open redirect: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- Template BEM classes: [Source: _bmad-output/implementation-artifacts/1-2-user-registration.md#Template Structure]
- Extension patterns: [Source: _bmad-output/implementation-artifacts/1-2-user-registration.md#Critical Architecture Requirements]
- Blueprint structure: [Source: _bmad-output/planning-artifacts/architecture.md#Code Organization]
- URL conventions: [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- Validation run by Amelia (claude-sonnet-4.6) on 2026-05-05.
- All 6 tasks verified implemented. All 4 ACs covered. All 6 test cases present.
- `login_manager.login_view = 'auth.login'` confirmed in `app/extensions.py:13`.
- `session.permanent = True` set in `app/blueprints/auth/routes.py:43` (NFR7 ✅).
- Open redirect guard (`netloc != ''`) present at `routes.py:45` (security ✅).
- `PERMANENT_SESSION_LIFETIME` defined only in `ProductionConfig` (not DevelopmentConfig) — Flask default (~31 days) covers dev; not a blocker.
- Full test run executed (2026-05-05): all 6 Story 1.3 tests PASS. 2 pre-existing Story 1.2 test failures unrelated to this story remain.
- Test infrastructure fixes applied: `config.py` TestingConfig → `sqlite://` + StaticPool; `tests/conftest.py` all fixtures changed to `scope='function'` to eliminate cross-test session/DB contamination.

### File List

- `app/blueprints/auth/routes.py` — added `/login` and `/logout` handlers
- `app/blueprints/auth/forms.py` — added `LoginForm`
- `app/extensions.py` — `login_manager.login_view` confirmed set
- `app/templates/auth/login.html` — new template
- `tests/test_auth.py` — added 6 login/logout test cases
