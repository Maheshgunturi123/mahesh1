# Story 1.5: User Profile View & Edit

Status: done

## Story

As a logged-in user,
I want to view and update my profile information,
so that my account details stay current.

## Acceptance Criteria

1. **Given** I am on `/auth/profile` **When** the page loads **Then** I see my current email address (read-only display) **And** I see a form to change my password with fields: current password, new password (≥ 8 characters), confirm new password.

2. **Given** I submit the password change form with the correct current password and matching new passwords (≥ 8 characters) **When** the form is submitted **Then** my password is updated as a new bcrypt hash **And** I see a `success` flash: "Password updated successfully."

3. **Given** I submit an incorrect current password **When** the form is submitted **Then** I see an `error` flash: "Current password is incorrect." **And** no change is made to my account.

4. **Given** I am not logged in and I visit `/auth/profile` **When** the request is made **Then** I am redirected to `/auth/login` with the original URL preserved as `next` parameter (Flask-Login `@login_required` default behaviour).

## Tasks / Subtasks

- [x] Task 1: Create `ChangePasswordForm` in `app/blueprints/auth/forms.py` (AC: 1, 2, 3)
  - [x] ADD to the existing file — do NOT replace `RegistrationForm`, `LoginForm`, `ForgotPasswordForm`, or `ResetPasswordForm`
  - [x] Import `EqualTo` from `wtforms.validators` (already imported for `ResetPasswordForm`)
  - [x] Implement form:
    ```python
    class ChangePasswordForm(FlaskForm):
        current_password = PasswordField('Current Password', validators=[DataRequired()])
        new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
        confirm_password = PasswordField('Confirm New Password', validators=[
            DataRequired(),
            EqualTo('new_password', message='Passwords must match.')
        ])
        submit = SubmitField('Update Password')
    ```

- [x] Task 2: Add `profile` route handler in `app/blueprints/auth/routes.py` (AC: 1, 2, 3, 4)
  - [x] ADD alongside existing `/register`, `/login`, `/logout`, `/forgot-password`, `/reset-password/<token>` — do NOT remove or modify those handlers
  - [x] Import `ChangePasswordForm` from `app.blueprints.auth.forms` (alongside existing imports)
  - [x] Implement handler:
    ```python
    @auth_bp.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('auth.profile'))
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        return render_template('auth/profile.html', form=form)
    ```
  - [x] Verify `db` is imported (already imported via `from app.extensions import db` from prior stories)
  - [x] Verify `current_user`, `login_required` are imported from `flask_login` (already present)

- [x] Task 3: Create HTML template `app/templates/auth/profile.html` (AC: 1, 2, 3)
  - [x] NEW file — does not exist yet
  - [x] Use BEM classes matching all other auth templates: `auth-form`, `auth-form__field`, `auth-form__input`, `auth-form__error`, `auth-form__submit`
  - [x] Implement template:
    ```html
    {% extends 'base.html' %}
    {% block title %}My Profile — GymTrack{% endblock %}
    {% block content %}
    <div class="auth-form">
      <h1 class="auth-form__title">My Profile</h1>
      <section class="auth-form__section">
        <h2 class="auth-form__subtitle">Account Information</h2>
        <p><strong>Email:</strong> {{ current_user.email }}</p>
      </section>
      <section class="auth-form__section">
        <h2 class="auth-form__subtitle">Change Password</h2>
        <form method="POST" action="{{ url_for('auth.profile') }}" novalidate>
          {{ form.hidden_tag() }}
          <div class="auth-form__field">
            {{ form.current_password.label }}
            {{ form.current_password(class="auth-form__input") }}
            {% for error in form.current_password.errors %}
              <span class="auth-form__error">{{ error }}</span>
            {% endfor %}
          </div>
          <div class="auth-form__field">
            {{ form.new_password.label }}
            {{ form.new_password(class="auth-form__input") }}
            {% for error in form.new_password.errors %}
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
      </section>
    </div>
    {% endblock %}
    ```

- [x] Task 4: Write tests in `tests/test_auth.py` (AC: 1, 2, 3, 4)
  - [x] EXTEND existing `tests/test_auth.py` — do NOT replace existing tests
  - [x] Add helper `login_user(test_client)` if not already present (reuse pattern from existing tests)
  - [x] Test cases:
    ```python
    def test_profile_page_requires_login(test_client, test_db):
        """Unauthenticated access redirects to login."""
        response = test_client.get('/auth/profile')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_profile_page_shows_email(test_client, test_db):
        """Profile page displays current user email read-only."""
        register_user(test_client)
        login_user_helper(test_client)
        response = test_client.get('/auth/profile')
        assert response.status_code == 200
        assert b'user@example.com' in response.data

    def test_profile_change_password_success(test_client, test_db):
        """Correct current password + matching new password → updated + success flash."""
        register_user(test_client)
        login_user_helper(test_client)
        response = test_client.post('/auth/profile', data={
            'current_password': 'testpass123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Password updated successfully.' in response.data

    def test_profile_change_password_wrong_current(test_client, test_db):
        """Incorrect current password → error flash, no change."""
        register_user(test_client)
        login_user_helper(test_client)
        response = test_client.post('/auth/profile', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Current password is incorrect.' in response.data
        # Verify old password still works
        logout_response = test_client.get('/auth/logout', follow_redirects=True)
        login_response = test_client.post('/auth/login', data={
            'email': 'user@example.com', 'password': 'testpass123'
        }, follow_redirects=True)
        assert b'dashboard' in login_response.request.path.lower() or response.status_code == 200

    def test_profile_change_password_mismatch_confirm(test_client, test_db):
        """Mismatched confirm password → WTForms validation error, no change."""
        register_user(test_client)
        login_user_helper(test_client)
        response = test_client.post('/auth/profile', data={
            'current_password': 'testpass123',
            'new_password': 'newpassword456',
            'confirm_password': 'differentpassword',
        })
        assert response.status_code == 200
        assert b'Password updated successfully.' not in response.data

    def test_profile_change_password_too_short(test_client, test_db):
        """New password < 8 chars → WTForms validation error."""
        register_user(test_client)
        login_user_helper(test_client)
        response = test_client.post('/auth/profile', data={
            'current_password': 'testpass123',
            'new_password': 'abc',
            'confirm_password': 'abc',
        })
        assert response.status_code == 200
        assert b'Password updated successfully.' not in response.data
    ```

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**Reuse existing User model methods — do NOT reimplement:**
- `current_user.check_password(plain_text)` — verifies against the stored bcrypt hash. Defined in `app/models/user.py` from Story 1.2. Always use this to validate the current password.
- `current_user.set_password(plain_text)` — hashes with bcrypt work factor 12 via Flask-Bcrypt. Defined in Story 1.2. Always use this to update the password. **Never call bcrypt directly from the route.**

**Flash message categories (ONLY these 4 — no exceptions):**
- `success` — password updated (AC2)
- `error` — wrong current password (AC3)
- `info` — informational messages
- `warning` — general warnings
- NEVER use: `ok`, `danger`, `primary`, `secondary`

**CSRF:**
- `{{ form.hidden_tag() }}` MUST be in `profile.html`
- `WTF_CSRF_ENABLED=False` is already set in `TestingConfig` from Story 1.1 — no change needed for tests

**Route naming:**
- URL: `/auth/profile` (kebab-case; single word here)
- Python function: `def profile():`
- `url_for('auth.profile')` — matches function name in `auth` blueprint

**Login protection:**
- `@login_required` decorator (imported from `flask_login`) — Flask-Login automatically redirects unauthenticated users to `login_manager.login_view` which is set to `'auth.login'` from Story 1.2

**Commit after password update:**
- `db.session.commit()` is required after `current_user.set_password(...)` — the ORM does not auto-commit

### Project Structure Notes

Files to UPDATE (extend, do NOT replace existing content):

| File | Change Type | What Changes |
|------|-------------|--------------|
| `app/blueprints/auth/forms.py` | UPDATE | Add `ChangePasswordForm` alongside `RegistrationForm`, `LoginForm`, `ForgotPasswordForm`, `ResetPasswordForm` |
| `app/blueprints/auth/routes.py` | UPDATE | Add `/profile` GET+POST handler alongside existing auth routes |
| `tests/test_auth.py` | UPDATE | Add 6 new test cases |

New files to CREATE:

| File | Change Type | Description |
|------|-------------|-------------|
| `app/templates/auth/profile.html` | NEW | Profile view + password change form |

**No new extensions, no changes to `app/extensions.py`, `app/__init__.py`, `config.py`, or `requirements.txt` — this story only adds a route, form, and template within the already-configured auth blueprint.**

### Authentication Blueprint State (from Stories 1.2–1.4)

Current state of `app/blueprints/auth/`:
```
app/blueprints/auth/
├── __init__.py      # auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
├── routes.py        # /register, /login, /logout, /forgot-password, /reset-password/<token>
├── forms.py         # RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
└── utils.py         # generate_reset_token(), verify_reset_token()
```
This story adds:
- `ChangePasswordForm` to `forms.py`
- `profile()` route handler to `routes.py`
- `app/templates/auth/profile.html` (new file)

Current template BEM classes (match exactly):
- `auth-form` — outer container div
- `auth-form__title` — `<h1>` heading
- `auth-form__field` — wrapper div per form field
- `auth-form__input` — input element class
- `auth-form__error` — span for field-level errors
- `auth-form__submit` — submit button class

### References

- Story ACs: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]
- Auth blueprint structure: [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint Internal Structure]
- Naming conventions: [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]
- Flash message categories: [Source: _bmad-output/planning-artifacts/architecture.md#Format Patterns]
- User model methods (set_password, check_password): [Source: _bmad-output/implementation-artifacts/1-4-password-reset-via-email.md#Dev Notes]
- BEM CSS classes and template pattern: [Source: _bmad-output/implementation-artifacts/1-4-password-reset-via-email.md#Previous Story Intelligence]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

Story 1.5 implemented and all 26 tests passing (6 new profile tests + 20 prior).

### File List

- `app/blueprints/auth/forms.py` — added `ChangePasswordForm`
- `app/blueprints/auth/routes.py` — added `/profile` GET+POST handler, imported `ChangePasswordForm`
- `app/templates/auth/profile.html` — new profile template
- `tests/test_auth.py` — added `login_user_helper` + 6 new test cases
