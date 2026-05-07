# Story 1.4: Password Reset via Email

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user who has forgotten their password,
I want to request a password reset link sent to my email,
so that I can regain access to my account.

## Acceptance Criteria

1. **Given** I am on `/auth/forgot-password` and submit a registered email **When** the form is submitted **Then** a signed `itsdangerous.URLSafeTimedSerializer` token (expires in 1 hour) is generated **And** a reset email is sent via Flask-Mail to the submitted address containing the reset link **And** I see: "If that email is registered, a reset link has been sent." (no email enumeration — same message regardless of whether email exists).

2. **Given** I click a valid, unexpired reset link (`/auth/reset-password/<token>`) **When** I submit a new password (≥ 8 characters) **Then** my password is updated as a new bcrypt hash (work factor 12) **And** I am redirected to `/auth/login` with a `success` flash: "Password updated. Please log in."

3. **Given** I click an expired or already-used reset link **When** the page loads (GET) **Then** I see an `error` flash: "This reset link has expired or is invalid." **And** I am redirected to `/auth/forgot-password`.

## Tasks / Subtasks

- [ ] Task 1: Install Flask-Mail and update extensions (AC: 1)
  - [ ] Add `Flask-Mail` to `requirements.txt` (if file exists) or install it
  - [ ] In `app/extensions.py`, add `from flask_mail import Mail` and `mail = Mail()`
  - [ ] In `app/__init__.py` `create_app()`, call `mail.init_app(app)` alongside existing `db.init_app(app)`, `login_manager.init_app(app)`, etc.
  - [ ] Add mail config to `config.py` in both `DevelopmentConfig` and `ProductionConfig`:
    ```python
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@gymtrack.app')
    ```
  - [ ] Add `MAIL_SUPPRESS_SEND = True` to `TestingConfig` to suppress actual email delivery in tests

- [ ] Task 2: Create token utility functions in `app/blueprints/auth/utils.py` (AC: 1, 2, 3)
  - [ ] Create `app/blueprints/auth/utils.py` (new file — per blueprint convention for helpers)
  - [ ] Implement `generate_reset_token(user)` — embeds `user.email` and `user.password_hash` so token is auto-invalidated after password change:
    ```python
    from flask import current_app
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    from app.models import User

    def generate_reset_token(user):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(
            {'email': user.email, 'password': user.password_hash},
            salt='password-reset'
        )

    def verify_reset_token(token, max_age=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset', max_age=max_age)
        except (SignatureExpired, BadSignature):
            return None
        user = User.query.filter_by(email=data['email']).first()
        if user and user.password_hash == data['password']:
            return user
        return None  # password already changed → token is single-use
    ```

- [ ] Task 3: Create `ForgotPasswordForm` and `ResetPasswordForm` in `app/blueprints/auth/forms.py` (AC: 1, 2)
  - [ ] ADD `ForgotPasswordForm` to existing `forms.py` (do NOT replace `RegistrationForm` or `LoginForm`):
    ```python
    class ForgotPasswordForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
        submit = SubmitField('Send Reset Link')
    ```
  - [ ] ADD `ResetPasswordForm` to existing `forms.py`:
    ```python
    from wtforms.validators import EqualTo
    class ResetPasswordForm(FlaskForm):
        new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match.')])
        submit = SubmitField('Update Password')
    ```

- [ ] Task 4: Add route handlers in `app/blueprints/auth/routes.py` (AC: 1, 2, 3)
  - [ ] Add `forgot_password` route handler:
    ```python
    import logging
    from flask_mail import Message
    from app.extensions import mail
    from app.blueprints.auth.utils import generate_reset_token, verify_reset_token
    from app.blueprints.auth.forms import ForgotPasswordForm, ResetPasswordForm

    logger = logging.getLogger(__name__)

    @auth_bp.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user:
                token = generate_reset_token(user)
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                msg = Message(
                    subject='GymTrack — Reset Your Password',
                    recipients=[user.email],
                    body=f'Click the link below to reset your password (valid for 1 hour):\n\n{reset_url}\n\nIf you did not request a password reset, ignore this email.'
                )
                mail.send(msg)
            else:
                logger.warning('Password reset requested for unknown email: %s', form.email.data.lower())
            flash('If that email is registered, a reset link has been sent.', 'info')
            return redirect(url_for('auth.forgot_password'))
        return render_template('auth/forgot_password.html', form=form)
    ```
  - [ ] Add `reset_password` route handler:
    ```python
    @auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        user = verify_reset_token(token)
        if user is None:
            flash('This reset link has expired or is invalid.', 'error')
            return redirect(url_for('auth.forgot_password'))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.set_password(form.new_password.data)
            from app.extensions import db
            db.session.commit()
            flash('Password updated. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        return render_template('auth/reset_password.html', form=form, token=token)
    ```
  - [ ] Verify `user.set_password()` method exists on `User` model (from Story 1.2) — it calls `bcrypt.generate_password_hash` with work factor 12. Do NOT reimplement — reuse the existing model method.

- [ ] Task 5: Create HTML templates (AC: 1, 2)
  - [ ] Create `app/templates/auth/forgot_password.html`:
    ```html
    {% extends 'base.html' %}
    {% block title %}Forgot Password — GymTrack{% endblock %}
    {% block content %}
    <div class="auth-form">
      <h1 class="auth-form__title">Forgot Password</h1>
      <p>Enter your email address and we'll send you a reset link.</p>
      <form method="POST" action="{{ url_for('auth.forgot_password') }}" novalidate>
        {{ form.hidden_tag() }}
        <div class="auth-form__field">
          {{ form.email.label }}
          {{ form.email(class="auth-form__input", placeholder="you@example.com") }}
          {% for error in form.email.errors %}
            <span class="auth-form__error">{{ error }}</span>
          {% endfor %}
        </div>
        {{ form.submit(class="auth-form__submit") }}
      </form>
      <p><a href="{{ url_for('auth.login') }}">Back to Log In</a></p>
    </div>
    {% endblock %}
    ```
  - [ ] Create `app/templates/auth/reset_password.html` (already listed in architecture):
    ```html
    {% extends 'base.html' %}
    {% block title %}Reset Password — GymTrack{% endblock %}
    {% block content %}
    <div class="auth-form">
      <h1 class="auth-form__title">Reset Password</h1>
      <form method="POST" action="{{ url_for('auth.reset_password', token=token) }}" novalidate>
        {{ form.hidden_tag() }}
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
    </div>
    {% endblock %}
    ```

- [ ] Task 6: Write tests in `tests/test_auth.py` (AC: 1, 2, 3)
  - [ ] Extend existing `tests/test_auth.py` — do NOT replace existing tests
  - [ ] Import and mock Flask-Mail: use `app.extensions.mail` with `mail.testing = True` or capture `outbox` via `mail.record_messages()` context manager
  - [ ] Test cases:
    ```python
    from unittest.mock import patch
    from app.blueprints.auth.utils import generate_reset_token, verify_reset_token

    def test_forgot_password_registered_email_sends_mail(test_client, test_db):
        """Registered email: mail sent, generic success message shown."""
        register_user(test_client)
        with patch('app.blueprints.auth.routes.mail') as mock_mail:
            response = test_client.post('/auth/forgot-password', data={
                'email': 'user@example.com',
            }, follow_redirects=True)
        assert response.status_code == 200
        assert b'If that email is registered, a reset link has been sent.' in response.data
        mock_mail.send.assert_called_once()

    def test_forgot_password_unknown_email_no_enumeration(test_client, test_db):
        """Unknown email: same generic message shown, no mail sent."""
        with patch('app.blueprints.auth.routes.mail') as mock_mail:
            response = test_client.post('/auth/forgot-password', data={
                'email': 'nobody@example.com',
            }, follow_redirects=True)
        assert response.status_code == 200
        assert b'If that email is registered, a reset link has been sent.' in response.data
        mock_mail.send.assert_not_called()

    def test_reset_password_valid_token(test_client, test_db):
        """Valid token: password updated, success flash, redirected to login."""
        register_user(test_client)
        from app.models import User
        with test_client.application.app_context():
            user = User.query.filter_by(email='user@example.com').first()
            token = generate_reset_token(user)
        response = test_client.post(f'/auth/reset-password/{token}', data={
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Password updated. Please log in.' in response.data

    def test_reset_password_token_invalid(test_client, test_db):
        """Invalid/garbage token: error flash, redirect to forgot-password."""
        response = test_client.get('/auth/reset-password/invalid-token-xyz', follow_redirects=True)
        assert response.status_code == 200
        assert b'This reset link has expired or is invalid.' in response.data

    def test_reset_password_already_used_token_rejected(test_client, test_db):
        """After password is changed, same token is rejected (single-use)."""
        register_user(test_client)
        from app.models import User
        with test_client.application.app_context():
            user = User.query.filter_by(email='user@example.com').first()
            token = generate_reset_token(user)
        # First use: valid
        test_client.post(f'/auth/reset-password/{token}', data={
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        # Second use: token now invalid because password_hash changed
        response = test_client.get(f'/auth/reset-password/{token}', follow_redirects=True)
        assert b'This reset link has expired or is invalid.' in response.data

    def test_reset_password_short_password_rejected(test_client, test_db):
        """New password < 8 chars fails form validation."""
        register_user(test_client)
        from app.models import User
        with test_client.application.app_context():
            user = User.query.filter_by(email='user@example.com').first()
            token = generate_reset_token(user)
        response = test_client.post(f'/auth/reset-password/{token}', data={
            'new_password': 'abc',
            'confirm_password': 'abc',
        })
        assert response.status_code == 200
        assert b'Password updated. Please log in.' not in response.data

    def test_forgot_password_authenticated_user_redirected(test_client, test_db):
        """Authenticated user visiting /forgot-password is redirected to dashboard."""
        register_user(test_client)
        test_client.post('/auth/login', data={
            'email': 'user@example.com',
            'password': 'testpass123',
        })
        response = test_client.get('/auth/forgot-password')
        assert response.status_code == 302
        assert 'dashboard' in response.headers['Location']
    ```

## Dev Notes

### Critical Architecture Requirements (MUST NOT deviate)

**Single-Use Token Pattern (Non-Negotiable):**
The token MUST embed the user's current `password_hash`. After `set_password()` is called, the bcrypt hash changes, so any token generated before the reset is automatically invalidated. This is the only reliable single-use mechanism without a server-side token store.

```python
# Token generation — includes password_hash as state
def generate_reset_token(user):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(
        {'email': user.email, 'password': user.password_hash},
        salt='password-reset'
    )

# Token verification — checks both expiry AND password_hash match
def verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='password-reset', max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    user = User.query.filter_by(email=data['email']).first()
    if user and user.password_hash == data['password']:
        return user
    return None  # password already changed → single-use enforced
```

**No Email Enumeration (Security Critical):**
Always show "If that email is registered, a reset link has been sent." regardless of whether the email exists in the database. Never expose whether an email is registered. Log unknown email attempts internally (`logger.warning`) but NEVER surface that info to the user.

**Flask-Mail Extension Setup:**
Add `mail = Mail()` to `app/extensions.py` following the exact same pattern as `db`, `bcrypt`, and `login_manager` (instantiate without app, bind in `create_app()` via `mail.init_app(app)`).

**Password Hashing on Reset:**
Use `user.set_password(form.new_password.data)` — this method already exists from Story 1.2 and calls `bcrypt.generate_password_hash` with work factor 12. **Do NOT call bcrypt directly** from the route — always go through the model method.

**Flash Message Categories — ONLY these 4:**
- `success` — password updated confirmation (AC2)
- `error` — expired/invalid token (AC3)
- `info` — forgot-password submission confirmation (AC1)
- `warning` — general warnings
- NEVER use: `ok`, `danger`, `primary`, `secondary`

**Route Naming Convention:**
- URLs use `kebab-case`: `/auth/forgot-password`, `/auth/reset-password/<token>`
- Python function names use `snake_case`: `def forgot_password():`, `def reset_password(token):`
- `url_for('auth.forgot_password')` — matches function name inside `auth` blueprint
- The link in `login.html` (Story 1.3) already points to `/auth/forgot-password` — this story implements that route

**CSRF:**
- `{{ form.hidden_tag() }}` MUST be in both `forgot_password.html` and `reset_password.html`
- `WTF_CSRF_ENABLED=False` is already set in `TestingConfig` from Story 1.1 — no change needed

### Form Definitions

```python
# Add to app/blueprints/auth/forms.py (do NOT replace RegistrationForm or LoginForm)
from wtforms.validators import EqualTo

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Update Password')
```

### Mail Config in config.py

```python
# Add to DevelopmentConfig and ProductionConfig base class or both
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@gymtrack.app')

# In TestingConfig — suppresses actual email sends during tests
MAIL_SUPPRESS_SEND = True
```

### Files Being Modified

The following existing files are EXTENDED by this story (NOT replaced):

| File | Change Type | What Changes |
|------|-------------|--------------|
| `app/extensions.py` | UPDATE | Add `from flask_mail import Mail` and `mail = Mail()` |
| `app/__init__.py` | UPDATE | Add `mail.init_app(app)` in `create_app()` |
| `config.py` | UPDATE | Add `MAIL_*` config keys; add `MAIL_SUPPRESS_SEND = True` to `TestingConfig` |
| `app/blueprints/auth/forms.py` | UPDATE | Add `ForgotPasswordForm` and `ResetPasswordForm` |
| `app/blueprints/auth/routes.py` | UPDATE | Add `/forgot-password` and `/reset-password/<token>` handlers |
| `tests/test_auth.py` | UPDATE | Add 7 new test cases |

New files created by this story:

| File | Change Type | Description |
|------|-------------|-------------|
| `app/blueprints/auth/utils.py` | NEW | `generate_reset_token()` and `verify_reset_token()` |
| `app/templates/auth/forgot_password.html` | NEW | Request reset email form |
| `app/templates/auth/reset_password.html` | NEW | Enter new password form (listed in architecture) |

### Previous Story Intelligence (Story 1.3)

From Story 1.3 patterns already established:
- `User.set_password(plain)` exists in `app/models/user.py` — hashes with bcrypt work factor 12 — **reuse, do not reimplement**
- `User.check_password(plain)` also exists — used in login; not needed here
- `app/blueprints/auth/__init__.py` defines `auth_bp = Blueprint('auth', __name__, url_prefix='/auth')`
- `app/blueprints/auth/forms.py` has `RegistrationForm` + `LoginForm` — ADD new forms alongside them
- `app/blueprints/auth/routes.py` has `/register`, `/login`, `/logout` — ADD new handlers alongside them
- Template BEM classes established: `auth-form`, `auth-form__field`, `auth-form__input`, `auth-form__error`, `auth-form__submit`
- `tests/test_auth.py` exists with 6+ tests — extend it, never replace
- `tests/conftest.py` fixtures are `scope='function'` for DB isolation (fixed in Story 1.3)
- `TestingConfig` uses `sqlite://` + StaticPool for in-memory test DB
- `WTF_CSRF_ENABLED=False` already set in `TestingConfig`
- Login template (`app/templates/auth/login.html`) already has `<a href="/auth/forgot-password">Forgot your password?</a>` — this story implements that route
- `app/extensions.py` already imports: `db`, `bcrypt`, `login_manager` — add `mail` following the same pattern
- Story 1.3 completion notes confirm: `app/extensions.py:13` has `login_manager.login_view = 'auth.login'`

### Testing Notes

The `mail` extension needs to be mocked in tests. The recommended approach is `unittest.mock.patch`:

```python
from unittest.mock import patch

def test_forgot_password_registered_email_sends_mail(test_client, test_db):
    register_user(test_client)
    with patch('app.blueprints.auth.routes.mail') as mock_mail:
        response = test_client.post('/auth/forgot-password', data={
            'email': 'user@example.com',
        }, follow_redirects=True)
    assert b'If that email is registered, a reset link has been sent.' in response.data
    mock_mail.send.assert_called_once()
```

Alternatively, if `MAIL_SUPPRESS_SEND = True` is set in `TestingConfig`, Flask-Mail silently no-ops `mail.send()` without raising exceptions, which also works for tests that only verify the flash message.

### Non-Functional Requirements for this Story

- **NFR5:** Passwords hashed with bcrypt work factor 12 on reset — enforced via `user.set_password()`
- **NFR9:** Password reset tokens expire within 1 hour — enforced by `max_age=3600` in `verify_reset_token()`
- **NFR9 (single-use):** Token auto-invalidated after use because `password_hash` embedded in token payload changes after `set_password()`
- **NFR6:** HTTPS at platform level (Railway) ensures reset links are transmitted securely
- **NFR17:** All form inputs have `<label>` elements — enforced in templates using WTForms label rendering
- **NFR19:** Error messages descriptive and adjacent to fields — match BEM pattern from `register.html` and `login.html`

### Project Structure Notes

- `app/blueprints/auth/utils.py` is a new file — the architecture spec explicitly allows an optional `utils.py` per blueprint for local helpers
- All templates go into `app/templates/auth/` — `forgot_password.html` is new; `reset_password.html` is listed in the architecture template tree
- `url_for('auth.forgot_password')` must resolve — function name in `routes.py` MUST be `forgot_password` (no alias)
- No new `app/models/` files needed — `User` model already has `set_password()` from Story 1.2
- No new blueprints or DB migrations required — this story only adds routes and logic within the existing `auth` blueprint

### References

- Acceptance criteria source: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- Token pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security — Password Reset Tokens]
- Flask-Mail requirement: [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- Password hashing: [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- NFR9 token expiry: [Source: _bmad-output/planning-artifacts/epics.md#NonFunctional Requirements]
- Error logging pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Error Logging Pattern]
- Blueprint structure: [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint Internal Structure]
- Template naming: [Source: _bmad-output/planning-artifacts/architecture.md#Template File Naming]
- BEM CSS pattern: [Source: _bmad-output/implementation-artifacts/1-3-user-login-and-logout.md#Template Structure]
- Extension patterns: [Source: _bmad-output/implementation-artifacts/1-2-user-registration.md#Critical Architecture Requirements]
- Forgot-password link stub: [Source: _bmad-output/implementation-artifacts/1-3-user-login-and-logout.md#Task 5]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

### File List
