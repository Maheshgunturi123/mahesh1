# Story 1.1: Project Scaffold & Base Configuration

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a fully initialized Flask project structure with Application Factory, config, extensions, base template, and error handlers,
so that all subsequent stories can be built on a consistent, production-ready foundation.

## Acceptance Criteria

1. The project directory structure matches the architecture specification: `gymtrack/app/`, `blueprints/`, `models/`, `services/`, `static/`, `templates/`, `tests/`, `migrations/`, `config.py`, `wsgi.py`
2. `create_app()` factory in `app/__init__.py` registers all extensions from `extensions.py` (db, login_manager, migrate, bcrypt)
3. `DevelopmentConfig` uses SQLite (`sqlite:///gymtrack_dev.db`); `ProductionConfig` reads `DATABASE_URL` env var for PostgreSQL
4. `base.html` renders flash messages using categories: `success`, `error`, `info`, `warning` — no other categories
5. Flask error handlers for 400, 403, 404, 500 are registered and return custom HTML error pages — never raw tracebacks
6. `requirements.txt` lists all production dependencies: flask, flask-sqlalchemy, flask-migrate, flask-login, flask-wtf, flask-bcrypt, flask-mail, python-dotenv, psycopg2-binary, gunicorn, sentry-sdk
7. `.env.example` documents all required environment variables: SECRET_KEY, DATABASE_URL, FLASK_ENV, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_USE_TLS, SENTRY_DSN
8. `pytest` runs with zero errors and zero warnings on the initial empty test suite (conftest.py provides `test_app`, `test_client`, `test_db` fixtures)

## Tasks / Subtasks

- [x] Task 1: Initialize project directory structure (AC: 1)
  - [x] Create root `gymtrack/` directory with all subdirectories per architecture spec
  - [x] Create `app/__init__.py`, `app/extensions.py`, `config.py`, `wsgi.py`
  - [x] Create blueprint directories: `app/blueprints/auth/`, `exercises/`, `workouts/`, `progress/`, `dashboard/`, `admin/`, `api/`
  - [x] Create `app/models/__init__.py`, `app/services/`, `app/static/css/`, `app/static/js/`, `app/static/icons/`
  - [x] Create `app/templates/` with subdirs: `auth/`, `exercises/`, `workouts/`, `progress/`, `dashboard/`, `admin/`, `errors/`
  - [x] Create `tests/` directory with `conftest.py` stub
  - [x] Create `migrations/` directory (empty, managed by flask-migrate)
  - [x] Create `docs/` directory with empty `deployment.md`

- [x] Task 2: Create config.py with DevelopmentConfig and ProductionConfig (AC: 3)
  - [x] Define `Config` base class with shared settings (SECRET_KEY from env, SQLALCHEMY_TRACK_MODIFICATIONS=False, WTF_CSRF_ENABLED=True)
  - [x] Define `DevelopmentConfig(Config)`: DEBUG=True, SQLALCHEMY_DATABASE_URI='sqlite:///gymtrack_dev.db', SENTRY_DSN=None
  - [x] Define `ProductionConfig(Config)`: DEBUG=False, SQLALCHEMY_DATABASE_URI from DATABASE_URL env, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, PERMANENT_SESSION_LIFETIME=timedelta(days=30)
  - [x] Add config selector dict: `config = {'development': DevelopmentConfig, 'production': ProductionConfig, 'default': DevelopmentConfig}`

- [x] Task 3: Create extensions.py and create_app() factory (AC: 2)
  - [x] In `app/extensions.py`: instantiate db (SQLAlchemy), login_manager (LoginManager), migrate (Migrate), bcrypt (Bcrypt) WITHOUT passing app
  - [x] In `app/__init__.py`: implement `create_app(config_name=None)` factory
  - [x] Factory reads `FLASK_ENV` env var to select config if `config_name` not provided
  - [x] Factory calls `db.init_app(app)`, `login_manager.init_app(app)`, `migrate.init_app(app, db)`, `bcrypt.init_app(app)`
  - [x] Factory registers all blueprints (placeholders for now — each blueprint `__init__.py` must exist)
  - [x] In production config: initialize Sentry SDK with `sentry_sdk.init(dsn=app.config['SENTRY_DSN'])` — skip if SENTRY_DSN is None
  - [x] Create `wsgi.py`: `from app import create_app; app = create_app('production')`

- [x] Task 4: Register error handlers (AC: 5)
  - [x] Register `@app.errorhandler(400)` → renders `errors/400.html`
  - [x] Register `@app.errorhandler(403)` → renders `errors/403.html`
  - [x] Register `@app.errorhandler(404)` → renders `errors/404.html`
  - [x] Register `@app.errorhandler(500)` → renders `errors/500.html`
  - [x] Create `app/templates/errors/400.html`, `403.html`, `404.html`, `500.html` extending `base.html`
  - [x] JSON error handler for `/api/*` prefix routes (returns `{"status": "error", "message": "..."}`)

- [x] Task 5: Create base.html template (AC: 4)
  - [x] Create `app/templates/base.html` with: DOCTYPE, `<head>` (charset, viewport, title block, CSS link), `<body>` (nav block, flash messages, content block, footer, JS block)
  - [x] Flash messages loop renders ONLY these categories: `success` (green), `error` (red), `info` (blue), `warning` (yellow)
  - [x] Create `app/static/css/style.css` with: CSS custom properties for colors, BEM base styles, mobile-first breakpoints (375px, 768px, 1024px), flash message category styles
  - [x] Stub `app/static/js/set-logger.js` and `charts.js` (empty files, will be populated in later stories)
  - [x] Create `app/static/manifest.json` PWA manifest stub

- [x] Task 6: Create requirements files and environment config (AC: 6, 7)
  - [x] Create `requirements.txt` with pinned versions: flask>=3.0, flask-sqlalchemy>=3.1, flask-migrate>=4.0, flask-login>=0.6, flask-wtf>=1.2, flask-bcrypt>=1.0, flask-mail>=0.10, python-dotenv>=1.0, psycopg2-binary>=2.9, gunicorn>=21.2, sentry-sdk[flask]>=1.40
  - [x] Create `requirements-dev.txt`: pytest>=8.0, pytest-flask>=1.3, flake8>=7.0, coverage>=7.4
  - [x] Create `.env.example` with all required vars (no real values): SECRET_KEY, DATABASE_URL, FLASK_ENV, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_USE_TLS, SENTRY_DSN
  - [x] Create `.gitignore` (venv/, .env, __pycache__/, *.pyc, instance/, *.db, .pytest_cache/, .coverage)

- [x] Task 7: Create test infrastructure and verify pytest passes (AC: 8)
  - [x] Create `tests/conftest.py` with fixtures: `test_app()` (creates app with TestingConfig), `test_client()` (app.test_client()), `test_db()` (creates/drops all tables)
  - [x] Add `TestingConfig(Config)` to `config.py`: TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', WTF_CSRF_ENABLED=False
  - [x] Create `tests/test_config.py` with smoke tests: app creates successfully, DevelopmentConfig sets DEBUG=True, TestingConfig uses in-memory SQLite
  - [x] Run `pytest tests/` — all tests must pass with zero errors

- [x] Task 8: Create blueprint stubs for all 7 blueprints (AC: 1, 2)
  - [x] For each blueprint (auth, exercises, workouts, progress, dashboard, admin, api): create `__init__.py` defining the Blueprint object and `routes.py` with a placeholder route
  - [x] Register all blueprints in `create_app()` with correct url_prefixes: `/auth`, `/exercises`, `/workouts`, `/progress`, `/dashboard`, `/admin`, `/api`
  - [x] Verify app starts without import errors: `flask --app wsgi:app run` exits cleanly

## Dev Notes

### Architecture Requirements (MUST FOLLOW — no deviations)

**Application Factory Pattern:**
- `create_app()` MUST live in `app/__init__.py` — never in `wsgi.py` directly
- All extensions MUST be instantiated in `extensions.py` without the app object, then initialized via `ext.init_app(app)` in `create_app()`
- This pattern enables testing with `app.testing = True` without circular imports

**Blueprint Registration Pattern:**
```python
# app/__init__.py — exact pattern required
from app.blueprints.auth import auth_bp
from app.blueprints.exercises import exercises_bp
# ... etc

def create_app(config_name=None):
    app = Flask(__name__)
    # load config
    # init extensions
    app.register_blueprint(auth_bp)
    app.register_blueprint(exercises_bp)
    # ... register all blueprints
    return app
```

**Blueprint Definition Pattern:**
```python
# app/blueprints/auth/__init__.py — ONLY blueprint definition here
from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
from app.blueprints.auth import routes  # noqa: F401, E402
```

**Routes NEVER in `__init__.py`** — all routes go in `routes.py`

**Extensions Pattern:**
```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
```

### Naming Conventions (MANDATORY)
- Table names: plural snake_case (`users`, `workout_plans`)
- Column names: singular snake_case (`user_id`, `weight_kg`)
- Python functions: `snake_case` verbs
- Blueprint variables: `<name>_bp` (e.g., `auth_bp`, `workouts_bp`)
- URL prefixes: plural nouns where applicable (`/auth`, `/exercises`, `/workouts`, `/progress`, `/dashboard`, `/admin`, `/api`)
- CSS classes: BEM (`workout-card__title--active`)

### Config Pattern
```python
# config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-prod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///gymtrack_dev.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SENTRY_DSN = os.environ.get('SENTRY_DSN')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

### Error Handler Pattern
```python
# in create_app(), after blueprint registration
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "Resource not found"}), 404
    return render_template('errors/404.html'), 404
# Repeat for 400, 403, 500
```

### Flash Message Categories
ONLY these 4 are valid: `success`, `error`, `info`, `warning`
NEVER use: `ok`, `danger`, `primary`, `secondary` — these will break the CSS

### Sentry Initialization
```python
# in create_app(), only when SENTRY_DSN is set
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if app.config.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1
    )
```

### Testing Infrastructure
```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope='session')
def test_app():
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='function')
def test_db(test_app):
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()
```

### Project Structure Notes

- This story creates the entire skeleton. Subsequent stories ADD to it — never reorganize it
- `migrations/` is managed exclusively by `flask db init` / `flask db migrate` / `flask db upgrade` — never hand-edit
- `wsgi.py` is the Gunicorn entry point: `gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT`
- The `docs/deployment.md` stub should outline Railway setup steps (to be completed in Story 1.6)
- No model classes are created in this story — models come in Epic 1 Stories 1.2+ and Epic 2+

### References

- Architecture: Application Factory Pattern [Source: architecture.md#Starter Template Evaluation]
- Architecture: Blueprint structure [Source: architecture.md#Blueprint Internal Structure]
- Architecture: Config pattern [Source: architecture.md#Infrastructure & Deployment]
- Architecture: Error handler pattern [Source: architecture.md#API & Communication Patterns]
- Architecture: Flash message categories [Source: architecture.md#Format Patterns]
- Architecture: Testing structure [Source: architecture.md#Structure Patterns]
- PRD: NFR5 (bcrypt), NFR6 (HTTPS), NFR16 (no raw tracebacks) [Source: prd.md#Non-Functional Requirements]
- Epics: Story 1.1 AC [Source: epics.md#Story 1.1]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6 (GitHub Copilot CLI)

### Debug Log References

No issues encountered during implementation.

### Completion Notes List

- All 4 pytest tests pass: `test_app_creates_successfully`, `test_development_config_sets_debug`, `test_testing_config_uses_in_memory_sqlite`, `test_testing_config_disables_csrf`
- All 7 blueprints registered with correct url_prefixes
- Application Factory pattern implemented correctly with extensions.py pattern
- Error handlers for 400, 403, 404, 500 with JSON support for /api/* routes
- All dependencies installed in .venv

### File List

- gymtrack/config.py
- gymtrack/wsgi.py
- gymtrack/.env.example
- gymtrack/.gitignore
- gymtrack/requirements.txt
- gymtrack/requirements-dev.txt
- gymtrack/app/__init__.py
- gymtrack/app/extensions.py
- gymtrack/app/blueprints/__init__.py
- gymtrack/app/blueprints/auth/__init__.py
- gymtrack/app/blueprints/auth/routes.py
- gymtrack/app/blueprints/exercises/__init__.py
- gymtrack/app/blueprints/exercises/routes.py
- gymtrack/app/blueprints/workouts/__init__.py
- gymtrack/app/blueprints/workouts/routes.py
- gymtrack/app/blueprints/progress/__init__.py
- gymtrack/app/blueprints/progress/routes.py
- gymtrack/app/blueprints/dashboard/__init__.py
- gymtrack/app/blueprints/dashboard/routes.py
- gymtrack/app/blueprints/admin/__init__.py
- gymtrack/app/blueprints/admin/routes.py
- gymtrack/app/blueprints/api/__init__.py
- gymtrack/app/blueprints/api/routes.py
- gymtrack/app/models/__init__.py
- gymtrack/app/services/.gitkeep
- gymtrack/app/static/css/style.css
- gymtrack/app/static/js/set-logger.js
- gymtrack/app/static/js/charts.js
- gymtrack/app/static/manifest.json
- gymtrack/app/static/icons/.gitkeep
- gymtrack/app/templates/base.html
- gymtrack/app/templates/errors/400.html
- gymtrack/app/templates/errors/403.html
- gymtrack/app/templates/errors/404.html
- gymtrack/app/templates/errors/500.html
- gymtrack/app/templates/auth/.gitkeep
- gymtrack/app/templates/exercises/.gitkeep
- gymtrack/app/templates/workouts/.gitkeep
- gymtrack/app/templates/progress/.gitkeep
- gymtrack/app/templates/dashboard/.gitkeep
- gymtrack/app/templates/admin/.gitkeep
- gymtrack/docs/deployment.md
- gymtrack/migrations/.gitkeep
- gymtrack/tests/__init__.py
- gymtrack/tests/conftest.py
- gymtrack/tests/test_config.py

### Change Log

- 2026-05-04: Story created by bmad-create-story workflow
- 2026-05-05: Implementation completed by GitHub Copilot CLI — all tasks done, 4/4 tests passing, status → review
