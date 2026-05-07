# Story 7.4: Admin User Management

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an administrator,
I want to view all registered users and trigger password resets on their behalf,
so that I can support users who are locked out of their accounts.

## Acceptance Criteria

1. **Given** I am an admin at `/admin/users/`
   **When** the page loads
   **Then** I see a list of all users showing: email, registration date, last login, `is_admin` status
   **And** non-admin users cannot access this page (403 response)

2. **Given** I click "Send Password Reset" for a user
   **When** the action is confirmed
   **Then** a password reset email is sent to that user's email address using the same `itsdangerous` token flow as Story 1.4
   **And** I see a `success` flash: "Password reset email sent to [email]."

## Tasks / Subtasks

- [ ] Task 1: Add `last_login_at` to the `User` model and create a migration (AC: 1)
  - [ ] UPDATE `gymtrack/app/models/user.py` — add `last_login_at` column:
    ```python
    last_login_at = db.Column(db.DateTime, nullable=True, default=None)
    ```
    Place it after `created_at`. It is nullable so existing users without a recorded login show `None`.
  - [ ] Run `flask db migrate -m "add last_login_at to users"` to generate a migration file in `gymtrack/migrations/versions/`
  - [ ] Run `flask db upgrade` to apply the migration to the dev database
  - [ ] Do NOT set a default timestamp for existing rows — `NULL` is the correct initial value; the template will render it as "Never"

- [ ] Task 2: Record `last_login_at` on every successful login (AC: 1)
  - [ ] UPDATE `gymtrack/app/blueprints/auth/routes.py` — in the `login()` route handler, after `login_user(user)` (line 47), add:
    ```python
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    ```
  - [ ] Add `from app.extensions import db` if not already imported at the top of `routes.py`
  - [ ] Verify `datetime` is already imported or add `from datetime import datetime`
  - [ ] This must be inserted **after** `login_user(user)` and **before** `flask_session.permanent = True`

- [ ] Task 3: Add `user_list` route to admin blueprint (AC: 1, 2)
  - [ ] UPDATE `gymtrack/app/blueprints/admin/routes.py` — ADD new routes at the end of the file
  - [ ] Add imports: `from app.models.user import User` and `from flask_mail import Message` and `from app.extensions import mail` and `from app.blueprints.auth.utils import generate_reset_token`
  - [ ] Route `GET /users/`: list all users ordered by `created_at` desc:
    ```python
    @admin_bp.route('/users/')
    @login_required
    @admin_required
    def user_list():
        users = User.query.order_by(User.created_at.desc()).all()
        delete_form = DeleteForm()
        return render_template('admin/user_list.html', users=users, delete_form=delete_form)
    ```
  - [ ] Route `POST /users/<int:id>/send-reset`: trigger password reset email:
    ```python
    @admin_bp.route('/users/<int:id>/send-reset', methods=['POST'])
    @login_required
    @admin_required
    def send_user_reset(id):
        delete_form = DeleteForm()
        if delete_form.validate_on_submit():
            user = User.query.get_or_404(id)
            token = generate_reset_token(user)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message(
                subject='GymTrack — Password Reset Request',
                recipients=[user.email],
                body=(
                    f'An administrator has requested a password reset for your account.\n\n'
                    f'Click the link below to reset your password (valid for 1 hour):\n\n'
                    f'{reset_url}\n\n'
                    f'If you did not expect this email, you can ignore it.'
                )
            )
            mail.send(msg)
            logger.info('Admin %s sent password reset for user id=%d email=%s', current_user.email, user.id, user.email)
            flash(f'Password reset email sent to {user.email}.', 'success')
        return redirect(url_for('admin.user_list'))
    ```
  - [ ] Verify `request` and `url_for` are already imported from `flask` at the top of `routes.py`

- [ ] Task 4: Create `admin/user_list.html` template (AC: 1, 2)
  - [ ] Create `gymtrack/app/templates/admin/user_list.html` — NEW file
  - [ ] Extends `base.html`; BEM block class `admin-user-list`
  - [ ] Heading: "Admin — User Management"
  - [ ] Table with `aria-label="Registered users"` and columns: Email, Registered, Last Login, Admin, Actions
  - [ ] Per-row data:
    - Email: `{{ user.email }}`
    - Registered: `{{ user.created_at | strftime('%b %d, %Y') }}`
    - Last Login: `{{ user.last_login_at | strftime('%b %d, %Y') if user.last_login_at else 'Never' }}`
    - Admin: `{{ 'Yes' if user.is_admin else 'No' }}`
    - Actions: a POST form with CSRF (`{{ delete_form.hidden_tag() }}`) submitting to `url_for('admin.send_user_reset', id=user.id)` with a "Send Password Reset" submit button
  - [ ] Flash message display block (reuse existing pattern from other admin templates)
  - [ ] All form inputs and buttons must have accessible `<label>` or `aria-label` attributes (NFR19)
  - [ ] Empty state: "No users registered yet." (unlikely in practice but required for completeness)
  - [ ] Sample structure:
    ```html
    {% extends 'base.html' %}
    {% block title %}User Management — GymTrack Admin{% endblock %}
    {% block content %}
    <div class="admin-user-list">
      <h1 class="admin-user-list__heading">Admin — User Management</h1>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, message in messages %}
            <p class="flash flash--{{ category }}">{{ message }}</p>
          {% endfor %}
        {% endif %}
      {% endwith %}
      {% if users %}
      <table class="admin-user-list__table" aria-label="Registered users">
        <thead>
          <tr>
            <th scope="col">Email</th>
            <th scope="col">Registered</th>
            <th scope="col">Last Login</th>
            <th scope="col">Admin</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for user in users %}
          <tr>
            <td>{{ user.email }}</td>
            <td>{{ user.created_at | strftime('%b %d, %Y') }}</td>
            <td>{{ user.last_login_at | strftime('%b %d, %Y') if user.last_login_at else 'Never' }}</td>
            <td>{{ 'Yes' if user.is_admin else 'No' }}</td>
            <td>
              <form method="POST" action="{{ url_for('admin.send_user_reset', id=user.id) }}">
                {{ delete_form.hidden_tag() }}
                <button type="submit" class="admin-user-list__reset-btn"
                        aria-label="Send password reset to {{ user.email }}">
                  Send Password Reset
                </button>
              </form>
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% else %}
      <p class="admin-user-list__empty">No users registered yet.</p>
      {% endif %}
    </div>
    {% endblock %}
    ```

- [ ] Task 5: Add CSS for user list admin panel (AC: 1)
  - [ ] UPDATE `gymtrack/app/static/css/style.css` — APPEND admin user list BEM classes at end of file
  - [ ] Add `admin-user-list` block with `__heading`, `__table`, `__reset-btn`, `__empty` elements
  - [ ] `admin-user-list__reset-btn` must have min touch target ≥ 44px (NFR17)
  - [ ] Do NOT create a new CSS file — only append to existing `style.css`

- [ ] Task 6: Extend `tests/test_admin.py` with user management tests (AC: 1, 2)
  - [ ] UPDATE `gymtrack/tests/test_admin.py` — APPEND new tests, do NOT replace existing tests
  - [ ] Add helper at the top or alongside existing helpers:
    ```python
    def make_regular_user_with_email(db, email='other@example.com'):
        """Creates a non-admin user for testing reset targeting."""
        u = User(email=email, is_admin=False)
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
        return u
    ```
  - [ ] Test: unauthenticated GET `/admin/users/` → 302 redirect to `/auth/login`
  - [ ] Test: non-admin authenticated GET `/admin/users/` → 403
  - [ ] Test: admin GET `/admin/users/` → 200, response contains users' email addresses and "Send Password Reset" button
  - [ ] Test: admin GET `/admin/users/` shows `last_login_at` as "Never" for a user who has never logged in
  - [ ] Test: admin POST `/admin/users/<id>/send-reset` → mocks `mail.send`, verifies flash contains "Password reset email sent to", redirects to user list
  - [ ] Test: non-admin POST `/admin/users/<id>/send-reset` → 403
  - [ ] Test: `last_login_at` is set on successful login — POST to `/auth/login` with valid credentials, then query user from DB; assert `user.last_login_at is not None`
  - [ ] Use `unittest.mock.patch('app.blueprints.admin.routes.mail')` to mock mail.send
  - [ ] Reuse existing `make_admin`, `make_regular_user` (or `make_regular_user_with_email`) and `login_as` helpers already in `test_admin.py`

## Dev Notes

### ⚠️ Critical: User Model Missing `last_login_at`

The `User` model (`gymtrack/app/models/user.py`) currently has:
```python
id, email, password_hash, is_admin, created_at
```
There is **no `last_login_at` field**. The AC requires showing "last login" — this story MUST add it.

- Add `last_login_at = db.Column(db.DateTime, nullable=True, default=None)` to `User` model
- Generate and apply a Flask-Migrate migration
- Update `login()` route in `app/blueprints/auth/routes.py` to set `user.last_login_at = datetime.utcnow()` after `login_user(user)` and commit

### Admin Blueprint — Current State (from Story 2.3)

Files already exist and are stable:

| File | Current State | This Story's Change |
|------|--------------|---------------------|
| `gymtrack/app/blueprints/admin/utils.py` | `admin_required` decorator | **No change** |
| `gymtrack/app/blueprints/admin/forms.py` | `ExerciseForm`, `DeleteForm` | **No change** — reuse `DeleteForm` for CSRF on reset POST |
| `gymtrack/app/blueprints/admin/routes.py` | Exercise CRUD (`exercise_list`, `add_exercise`, `edit_exercise`, `delete_exercise`) | **ADD** `user_list` and `send_user_reset` routes |
| `gymtrack/app/templates/admin/exercise_list.html` | Exercise list template | **No change** |
| `gymtrack/app/templates/admin/exercise_form.html` | Exercise form template | **No change** |
| `gymtrack/app/static/css/style.css` | Has `admin-exercise-list` and `admin-exercise-form` BEM blocks | **APPEND** `admin-user-list` BEM block |
| `gymtrack/tests/test_admin.py` | Exercise CRUD tests | **APPEND** user management tests |

**DO NOT** modify `utils.py`, `forms.py`, or exercise templates/routes. Only append to routes and tests.

### Architecture Compliance

- `admin_required` decorator is in `utils.py` — import it, do NOT redefine [Source: docs/architecture.md#Blueprint Internal Structure]
- Route decoration order: `@login_required` first, then `@admin_required` — this is critical for correct redirect vs 403 behavior [Source: Story 2.3 dev notes]
- `DeleteForm` (CSRF-only) from `forms.py` is reused to protect the `send-reset` POST action — no new form class needed
- `generate_reset_token(user)` is in `app/blueprints/auth/utils.py` — import from there, do NOT reimplement [Source: Story 1.4]
- `mail` extension is in `app.extensions` — `from app.extensions import mail` [Source: Story 1.4]
- Admin queries do NOT filter by `current_user.id` — admin blueprint intentionally queries ALL users (platform-wide). This is the only place where filtering by user_id is explicitly NOT required. [Source: docs/architecture.md#Multi-User Isolation Pattern]
- Flash category `'success'` — use for reset confirmation. Category MUST be one of: `success`, `error`, `info`, `warning` [Source: docs/architecture.md#Flash Messages]
- Routes in `routes.py` only, never in `__init__.py` [Source: docs/architecture.md#Blueprint Internal Structure]
- CSS BEM only, append to `style.css` — do NOT create new CSS files [Source: Story 2.3 dev notes]
- Logging: `logger = logging.getLogger(__name__)` already defined at top of `routes.py` — reuse it

### Password Reset Flow — Exact Reuse from Story 1.4

```python
# In admin/routes.py — generate token and send email exactly like auth/routes.py
from app.blueprints.auth.utils import generate_reset_token
from flask_mail import Message
from app.extensions import mail

token = generate_reset_token(user)
reset_url = url_for('auth.reset_password', token=token, _external=True)
msg = Message(
    subject='GymTrack — Password Reset Request',
    recipients=[user.email],
    body=f'An administrator has requested a password reset...\n\n{reset_url}'
)
mail.send(msg)
flash(f'Password reset email sent to {user.email}.', 'success')
```

The token uses `itsdangerous.URLSafeTimedSerializer` with the user's `email` + `password_hash` embedded — valid for 1 hour, auto-invalidated after use.

### `last_login_at` Update in Login Route

Current `app/blueprints/auth/routes.py` login handler (lines ~42–52):
```python
if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data.lower()).first()
    if user and user.check_password(form.password.data):
        login_user(user)           # ← line 47 (existing)
        flask_session.permanent = True  # ← line 48 (existing)
        ...
```

Change to add after `login_user(user)`:
```python
login_user(user)
user.last_login_at = datetime.utcnow()   # ADD THIS
db.session.commit()                       # ADD THIS
flask_session.permanent = True
```

Verify `from datetime import datetime` is in the imports (it likely is — used in model). Add `from app.extensions import db` if not already imported.

### Test Mocking Pattern for Mail

```python
from unittest.mock import patch

def test_admin_send_user_reset(test_client, test_db):
    admin = make_admin(test_db)
    target_user = make_regular_user_with_email(test_db, 'target@example.com')
    login_as(test_client, test_db, 'admin@example.com', 'adminpass')
    with patch('app.blueprints.admin.routes.mail') as mock_mail:
        response = test_client.post(
            f'/admin/users/{target_user.id}/send-reset',
            data={'csrf_token': _get_csrf_token(test_client)},
            follow_redirects=True
        )
    assert response.status_code == 200
    assert b'Password reset email sent to target@example.com' in response.data
    mock_mail.send.assert_called_once()
```

### Project Structure — Files to Create/Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `gymtrack/app/models/user.py` | UPDATE | Add `last_login_at = db.Column(db.DateTime, nullable=True, default=None)` |
| `gymtrack/migrations/versions/<hash>_add_last_login_at_to_users.py` | NEW (auto-generated) | Flask-Migrate migration file |
| `gymtrack/app/blueprints/auth/routes.py` | UPDATE | Set `user.last_login_at = datetime.utcnow()` + `db.session.commit()` after `login_user(user)` |
| `gymtrack/app/blueprints/admin/routes.py` | UPDATE | Append `user_list` + `send_user_reset` routes; add new imports |
| `gymtrack/app/templates/admin/user_list.html` | NEW | User list table with Send Password Reset button per row |
| `gymtrack/app/static/css/style.css` | UPDATE | Append `admin-user-list` BEM classes |
| `gymtrack/tests/test_admin.py` | UPDATE | Append user management tests |

### References

- User model: `gymtrack/app/models/user.py` — columns confirmed: `id`, `email`, `password_hash`, `is_admin`, `created_at`
- Admin blueprint utils: `gymtrack/app/blueprints/admin/utils.py` — `admin_required` decorator
- Admin blueprint forms: `gymtrack/app/blueprints/admin/forms.py` — `DeleteForm` (CSRF-only, reuse for send-reset POST)
- Admin blueprint routes: `gymtrack/app/blueprints/admin/routes.py` — existing exercise CRUD
- Password reset token: `gymtrack/app/blueprints/auth/utils.py` — `generate_reset_token(user)`, `verify_reset_token(token)`
- Auth routes login flow: `gymtrack/app/blueprints/auth/routes.py` — `login_user(user)` at line 47
- Architecture patterns: `_bmad-output/planning-artifacts/architecture.md` — BEM CSS, pure services, blueprint structure, flash categories
- Story 1.4 (Password Reset): `_bmad-output/implementation-artifacts/1-4-password-reset-via-email.md` — mail send pattern
- Story 2.3 (Admin Exercise Mgmt): `_bmad-output/implementation-artifacts/2-3-admin-exercise-management.md` — admin blueprint foundation

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Completion Notes List

- Tasks 1 & 2 (model + migration + login recording) were already implemented in a prior session.
- Task 3: Added `user_list` and `send_user_reset` routes to `admin/routes.py`; updated imports.
- Task 4: Created `app/templates/admin/user_list.html` with full table, flash messages, empty state, and CSRF-protected reset forms.
- Task 5: Appended `admin-user-list` BEM CSS block (including 44px touch target on reset button) to `style.css`.
- Task 6: Appended 7 new tests to `tests/test_admin.py`; all 17 admin tests pass.

### File List

- `app/blueprints/admin/routes.py` — updated (new routes + imports)
- `app/templates/admin/user_list.html` — created
- `app/static/css/style.css` — updated (appended BEM block)
- `tests/test_admin.py` — updated (appended 7 tests)
