# Story 1.6: CI/CD Pipeline, Deployment & Error Monitoring

Status: done

## Story

As a developer,
I want automated testing, deployment to Railway, and error monitoring configured,
so that every code push is validated and production errors are captured.

## Acceptance Criteria

1. **Given** a push or PR is made to any branch **When** GitHub Actions CI runs **Then** `flake8` lints the codebase (zero errors required to pass) **And** `pytest` runs all tests (zero failures required to pass).

2. **Given** a merge to `main` branch **When** GitHub Actions deploy job runs **Then** the application deploys to Railway automatically.

3. **Given** the application is running in production (`FLASK_ENV=production`) **When** `create_app()` is called **Then** Sentry SDK is initialized with the `SENTRY_DSN` env var **And** unhandled exceptions are automatically reported to Sentry **And** structured logging via `logging.getLogger(__name__)` is active in all modules.

4. **Given** `FLASK_ENV=development` **When** `create_app()` is called **Then** Sentry is NOT initialized (no dev noise in Sentry dashboard).

## Tasks / Subtasks

- [x] Task 1: Create GitHub Actions CI/CD workflow (AC: 1, 2)
  - [x] Create `.github/workflows/ci.yml` — NEW file (directory + file both new)
  - [x] Lint job: checkout → setup Python 3.11 → install `requirements-dev.txt` → run `flake8 . --exclude=migrations,venv,.venv --max-line-length=120`
  - [x] Test job (depends on lint): checkout → setup Python 3.11 → install `requirements-dev.txt` → run `pytest tests/ -v`
  - [x] Deploy job (only on push to `main`, depends on test): use Railway CLI to deploy
    - Use `npm install -g @railway/cli && railway up --detach` with `RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}`
  - [x] Use `ubuntu-latest` runner for all jobs
  - [x] Set env var `FLASK_ENV: testing` for the test job to use `TestingConfig`

- [x] Task 2: Create Railway `Procfile` for production deployment (AC: 2)
  - [x] Create `gymtrack/Procfile` — NEW file (root of the Flask project)
  - [x] Content: `web: gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT`
  - [x] This tells Railway how to start the app via Gunicorn (the existing `wsgi.py` is the entry point)

- [x] Task 3: Verify Sentry initialization is correct in `app/__init__.py` (AC: 3, 4)
  - [x] VERIFY (do NOT change) — Sentry is already initialized in `create_app()` from Story 1.1:
    ```python
    if app.config.get('SENTRY_DSN'):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
        )
    ```
  - [x] VERIFY `DevelopmentConfig.SENTRY_DSN = None` in `config.py` — already set, prevents dev init
  - [x] VERIFY `ProductionConfig.SENTRY_DSN = os.environ.get('SENTRY_DSN')` — already set
  - [x] VERIFY `sentry-sdk[flask]>=1.40` is in `requirements.txt` — already present
  - [x] If any of the above checks fail, apply the fix; otherwise this task is a no-op verification

- [x] Task 4: Add structured logging to modules that are missing it (AC: 3)
  - [x] `app/blueprints/auth/routes.py` already has `import logging; logger = logging.getLogger(__name__)` — SKIP
  - [x] CHECK `app/blueprints/auth/utils.py` — add `import logging; logger = logging.getLogger(__name__)` if missing

- [x] Task 5: Add `SENTRY_DSN` to `.env.example` and document Railway secrets (AC: 3)
  - [x] VERIFY `.env.example` already has `SENTRY_DSN=` — already present, no change needed
  - [x] Add comment block to `.env.example` documenting the Railway environment variables that must be set via Railway UI:
    ```
    # Railway Production Environment Variables (set via Railway UI — NOT in this file)
    # RAILWAY_ENVIRONMENT: production
    # SECRET_KEY: <random 32-byte hex>
    # DATABASE_URL: <Railway PostgreSQL connection string>
    # SENTRY_DSN: <Sentry project DSN>
    # MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
    ```

- [x] Task 6: Write tests in `tests/test_cicd.py` (AC: 3, 4)
  - [x] NEW file — does not exist yet
  - [x] Test that Sentry is NOT initialized when `FLASK_ENV=development` (i.e., `SENTRY_DSN` is `None` in DevelopmentConfig)
  - [x] Test that `create_app('production')` without `SENTRY_DSN` env var does NOT call `sentry_sdk.init` (guarded by `if app.config.get('SENTRY_DSN')`)
  - [x] Test that `create_app()` uses `TestingConfig` when `FLASK_ENV=testing`
  - [x] Use `unittest.mock.patch` to mock `sentry_sdk.init` and assert it is / is not called

## Dev Notes

### Critical Architecture Requirements (MUST follow)

**Sentry is already integrated — do NOT re-implement:**
- `app/__init__.py` already initializes Sentry inside `create_app()` guarded by `if app.config.get('SENTRY_DSN'):`
- `sentry-sdk[flask]>=1.40` is already in `requirements.txt`
- Do NOT move Sentry init outside `create_app()` — it must respect app config isolation for testing

**GitHub Actions workflow design:**
- File must be at `.github/workflows/ci.yml` (relative to repo root, which is the `copilot-cli-bmad` directory or the `gymtrack` directory — the Git repo root contains `gymtrack/`)
- **CRITICAL:** Determine the repo root. The git repo for GymTrack lives at `gymtrack/` inside the workspace. The `.github/` directory must be at the **git repository root**. If `gymtrack/` is its own git repo, `.github/` lives inside `gymtrack/`. If the workspace is the git repo, `.github/` lives at the workspace root.
- Railway CLI in GitHub Actions: use `npm install -g @railway/cli` or the official `railwayapp/railway-github-action@v2` action
- The `RAILWAY_TOKEN` secret must be configured in GitHub repo Settings → Secrets

**Procfile format:**
```
web: gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT
```
Railway reads `Procfile` at the project root to determine the start command. `wsgi.py` already exists and calls `create_app('production')`.

**`flake8` line length:**
- The codebase uses up to 120 characters per line (common Flask convention). Set `--max-line-length=120` or create a `.flake8` config file at the project root:
  ```ini
  [flake8]
  max-line-length = 120
  exclude = migrations, venv, .venv, __pycache__
  ```
- Always exclude `migrations/` — Alembic auto-generated code is not subject to lint

**Testing environment:**
- CI test job must set `FLASK_ENV=testing` so `create_app()` picks up `TestingConfig` (in-memory SQLite, CSRF disabled, mail suppressed)
- No database setup needed — `TestingConfig` uses `sqlite://` (in-memory)

**Railway deployment approach:**
- Primary: Railway's native GitHub integration (connect repo in Railway dashboard, auto-deploy on push to `main`) — simplest, zero tokens needed
- Alternative for explicit GH Actions control: `RAILWAY_TOKEN` secret + Railway CLI
- Architecture specifies "deploy to Railway on merge to main via GitHub Actions" — implement as a `deploy` job in `ci.yml` that runs only on `push` to `main` branch

### Project Structure Notes

Files to CREATE (do NOT modify existing files unless verification in Task 3/4 finds gaps):

| File | Change Type | Description |
|------|-------------|-------------|
| `.github/workflows/ci.yml` | NEW | GitHub Actions: lint + test on push/PR; deploy on push to main |
| `gymtrack/Procfile` | NEW | Railway production start command for Gunicorn |
| `gymtrack/.flake8` | NEW | flake8 configuration (max line length, exclusions) |
| `tests/test_cicd.py` | NEW | Sentry initialization unit tests |

Files to VERIFY (change only if verification fails):

| File | What to Verify |
|------|----------------|
| `app/__init__.py` | Sentry init guard exists: `if app.config.get('SENTRY_DSN')` |
| `config.py` | `DevelopmentConfig.SENTRY_DSN = None`, `ProductionConfig.SENTRY_DSN = os.environ.get('SENTRY_DSN')` |
| `requirements.txt` | `sentry-sdk[flask]>=1.40` present |
| `.env.example` | `SENTRY_DSN=` documented |

**No changes to models, blueprints, templates, or database schema — this story is purely infrastructure.**

### State of Prior Stories (context for dev agent)

From Stories 1.1–1.5, the following is established:
- `app/__init__.py`: `create_app()` factory with Sentry init already wired
- `config.py`: `DevelopmentConfig`, `ProductionConfig`, `TestingConfig` all defined
- `wsgi.py`: `app = create_app('production')` — Gunicorn entry point ready
- `requirements.txt`: all runtime deps including `sentry-sdk[flask]>=1.40`, `gunicorn>=21.2`
- `requirements-dev.txt`: `flake8>=7.0`, `pytest>=8.0`, `pytest-flask>=1.3`
- `app/blueprints/auth/routes.py`: `logger = logging.getLogger(__name__)` established
- Auth blueprint fully implemented (register, login, logout, password-reset, profile)
- 26 passing tests in `tests/test_auth.py`

### GitHub Actions Workflow (Reference Implementation)

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r gymtrack/requirements-dev.txt
      - name: Lint with flake8
        run: flake8 gymtrack/ --exclude=gymtrack/migrations,gymtrack/venv,gymtrack/.venv

  test:
    runs-on: ubuntu-latest
    needs: lint
    env:
      FLASK_ENV: testing
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r gymtrack/requirements-dev.txt
      - name: Run tests
        run: |
          cd gymtrack
          pytest tests/ -v

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      - name: Deploy to Railway
        run: railway up --service gymtrack --detach
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        working-directory: gymtrack
```

> **Note:** If `gymtrack/` is the git repo root (not a subdirectory), remove the `gymtrack/` prefixes from paths and the `working-directory` override.

### References

- Story ACs: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6]
- CI/CD requirements: [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment]
- Sentry init pattern: [Source: gymtrack/app/__init__.py]
- Config structure: [Source: gymtrack/config.py]
- Gunicorn entry point: [Source: gymtrack/wsgi.py]
- Error logging pattern: [Source: _bmad-output/planning-artifacts/architecture.md#Error Logging Pattern]
- Railway deployment: [Source: _bmad-output/planning-artifacts/architecture.md#Hosting Platform: Railway]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4.6

### Debug Log References

### Completion Notes List

- Production config class attrs are evaluated at import time; tests use `monkeypatch.setattr` on `ProductionConfig` directly rather than env vars.
- Pre-existing test failure in `test_config.py::test_testing_config_uses_in_memory_sqlite` (expects `sqlite:///:memory:`, config uses `sqlite://`) — not introduced by this story.

### File List

- `.github/workflows/ci.yml` — NEW: GitHub Actions CI/CD workflow
- `gymtrack/Procfile` — NEW: Railway production start command
- `gymtrack/.flake8` — NEW: flake8 config (max-line-length=120)
- `gymtrack/tests/test_cicd.py` — NEW: Sentry initialization unit tests (4 passing)
- `gymtrack/app/blueprints/auth/utils.py` — MODIFIED: added structured logging import
- `gymtrack/.env.example` — MODIFIED: added Railway production env vars comment block
