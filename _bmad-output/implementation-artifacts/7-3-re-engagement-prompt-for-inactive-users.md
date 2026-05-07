# Story 7.3: Re-Engagement Prompt for Inactive Users

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user returning after a long absence,
I want to see my last session and a prompt to get back on track,
so that I feel welcomed back rather than judged.

## Acceptance Criteria

1. **Given** my most recent completed session was ≥ 14 days ago
   **When** I log in and the dashboard loads
   **Then** I see a re-engagement card: "Welcome back! Your last workout was [date]. Pick up where you left off?" with a "Resume Routine" button linking to my most recent plan

2. **Given** my last session was fewer than 14 days ago
   **When** the dashboard loads
   **Then** the re-engagement card is NOT shown

3. **Given** I have never logged a session
   **When** the dashboard loads
   **Then** I see a getting-started prompt: "Ready to start? Create your first workout plan."

## Tasks / Subtasks

- [ ] Task 1: Add `get_re_engagement_data(user_id)` to `app/services/stats.py` (AC: 1, 2, 3)
  - [ ] Query `WorkoutSession` for user's most recent completed session (`is_complete == True`), ordered by `started_at` desc, limit 1
  - [ ] If no session exists → return `{'state': 'never_logged', 'last_session_date': None, 'last_plan_id': None}`
  - [ ] If last session < 14 days ago → return `{'state': 'active', 'last_session_date': None, 'last_plan_id': None}`
  - [ ] If last session ≥ 14 days ago → query `WorkoutPlan` for user's most recent plan (ordered by `created_at` desc, limit 1); return `{'state': 'inactive', 'last_session_date': <date>, 'last_plan_id': <id or None>}`
  - [ ] Pure function — accepts only `user_id: int`, uses `db.session` via `app.extensions`
  - [ ] All date comparisons use `datetime.date.today()` (UTC-safe for V1)

- [ ] Task 2: Extend `get_dashboard_stats(user_id)` to include re-engagement data (AC: 1, 2, 3)
  - [ ] Call `get_re_engagement_data(user_id)` inside `get_dashboard_stats`
  - [ ] Add `'re_engagement'` key to the returned dict: `{'state': ..., 'last_session_date': ..., 'last_plan_id': ...}`

- [ ] Task 3: Update dashboard route to pass re-engagement data to template (AC: 1, 2, 3)
  - [ ] In `gymtrack/app/blueprints/dashboard/routes.py`, extract `re_engagement` from `stats`
  - [ ] Pass `re_engagement=stats['re_engagement']` to `render_template`
  - [ ] Add logger line: `logger.info('Dashboard re_engagement: user=%d state=%s', current_user.id, stats['re_engagement']['state'])`

- [ ] Task 4: Add re-engagement card to dashboard template (AC: 1, 2, 3)
  - [ ] In `gymtrack/app/templates/dashboard/index.html`, add new section after the streak card
  - [ ] Section wrapper: `<section class="dashboard__section dashboard__re-engagement">`
  - [ ] **State `inactive`**: render card with text "Welcome back! Your last workout was {{ re_engagement.last_session_date | strftime('%b %d, %Y') }}. Pick up where you left off?" and a "Resume Routine" `<a>` button
    - If `re_engagement.last_plan_id` is not None: link href `/workouts/plans/{{ re_engagement.last_plan_id }}/`
    - If `last_plan_id` is None: link href `/workouts/plans/` (fallback to plans list)
  - [ ] **State `never_logged`**: render card with text "Ready to start? Create your first workout plan." and a "Create Plan" `<a>` button linking to `/workouts/plans/new`
  - [ ] **State `active`**: render nothing (section is hidden / not rendered)
  - [ ] CSS classes: `dashboard__re-engagement-card`, `dashboard__re-engagement-text`, `dashboard__re-engagement-btn`

- [ ] Task 5: Add integration tests in `gymtrack/tests/test_dashboard.py` (AC: 1, 2, 3)
  - [ ] `test_dashboard_re_engagement_shown_when_inactive_14_days` — user's last session is 15 days ago → response contains "Welcome back!" and "Resume Routine"
  - [ ] `test_dashboard_re_engagement_hidden_when_active` — user's last session is 7 days ago → "Welcome back!" NOT in response
  - [ ] `test_dashboard_re_engagement_getting_started_for_new_user` — user has no sessions → response contains "Ready to start?"
  - [ ] `test_dashboard_re_engagement_resume_routine_links_to_last_plan` — user inactive (15 days), has a plan → "Resume Routine" href contains `/workouts/plans/<plan_id>/`
  - [ ] `test_dashboard_re_engagement_resume_routine_fallback_no_plan` — user inactive (15 days), no plans → button href is `/workouts/plans/`
  - [ ] Use the existing `make_session`, `make_user` helpers and `_make_streak_user` pattern already in the file

## Dev Notes

### Context: Existing Dashboard State (from Stories 7.1 & 7.2)

The following files already exist and are stable:

| File | Current State | This Story's Change |
|------|--------------|---------------------|
| `gymtrack/app/services/streak.py` | `calculate_streak(user_id)` pure fn | No change |
| `gymtrack/app/services/stats.py` | `get_dashboard_stats(user_id)` returning `streak`, `recent_prs`, `freq_chart`, `has_freq_data` | ADD `get_re_engagement_data(user_id)` + extend return dict |
| `gymtrack/app/blueprints/dashboard/routes.py` | Passes `streak`, `recent_prs`, `freq_chart_json`, `has_freq_data` to template | ADD `re_engagement` kwarg to `render_template` call |
| `gymtrack/app/templates/dashboard/index.html` | Streak card + Recent PRs card + Frequency chart | ADD re-engagement section after streak card |
| `gymtrack/tests/test_dashboard.py` | Story 7.1/7.2 tests; uses `make_session(db, user_id, is_complete, days_ago)` | ADD 5 new AC tests |

**DO NOT** modify `streak.py`, `pr_detection.py`, or any model files.

### Architecture Compliance

- Services are **pure functions** — `get_re_engagement_data(user_id: int)` must accept only `user_id: int`. No Flask `current_user`, no `request` inside the function. [Source: docs/architecture.md#Services Layer]
- All user-scoped queries **must** filter by `user_id` — never query without it. [Source: docs/architecture.md#Data Isolation]
- Date/time: Store UTC `datetime` in DB; compare using `datetime.date.today()` for inactivity threshold calculation. [Source: docs/architecture.md#Date/Time Handling]
- Template date formatting: use Jinja2 filter `{{ value | strftime('%b %d, %Y') }}` — NEVER pass raw datetime to template expecting a string. [Source: docs/architecture.md#Format Patterns]
- CSS: BEM convention `block__element--modifier`, all new rules appended at end of `style.css`. [Source: docs/architecture.md#CSS Conventions]
- Blueprint structure: routes in `routes.py` only, never `__init__.py`. [Source: docs/architecture.md#Blueprint Internal Structure]

### `get_re_engagement_data` — Reference Implementation

```python
# In gymtrack/app/services/stats.py  (add below existing imports)
import datetime

from app.models.workout_plan import WorkoutPlan
from app.models.workout_session import WorkoutSession

INACTIVITY_THRESHOLD_DAYS = 14


def get_re_engagement_data(user_id: int) -> dict:
    """Return re-engagement state for the dashboard.

    States:
      'never_logged' – user has no completed sessions ever
      'active'       – last session < 14 days ago (no card shown)
      'inactive'     – last session ≥ 14 days ago (show welcome-back card)
    """
    last_session = (
        WorkoutSession.query
        .filter_by(user_id=user_id, is_complete=True)
        .order_by(WorkoutSession.started_at.desc())
        .first()
    )

    if last_session is None:
        return {'state': 'never_logged', 'last_session_date': None, 'last_plan_id': None}

    last_date = (
        last_session.started_at.date()
        if hasattr(last_session.started_at, 'date')
        else last_session.started_at
    )
    days_since = (datetime.date.today() - last_date).days

    if days_since < INACTIVITY_THRESHOLD_DAYS:
        return {'state': 'active', 'last_session_date': None, 'last_plan_id': None}

    # Inactive — find most recent plan
    last_plan = (
        WorkoutPlan.query
        .filter_by(user_id=user_id)
        .order_by(WorkoutPlan.created_at.desc())
        .first()
    )
    return {
        'state': 'inactive',
        'last_session_date': last_date,
        'last_plan_id': last_plan.id if last_plan else None,
    }
```

### Extending `get_dashboard_stats` — Reference Diff

```python
# At the top of get_dashboard_stats, after streak:
re_engagement = get_re_engagement_data(user_id)

# In the returned dict, add:
return {
    'streak': streak,
    'recent_prs': pr_list,
    'freq_chart': freq_chart,
    'has_freq_data': any(w['count'] > 0 for w in freq_chart),
    're_engagement': re_engagement,   # <-- ADD THIS
}
```

### Dashboard Route — Reference Diff

```python
# routes.py – add re_engagement to render_template call
return render_template(
    'dashboard/index.html',
    streak=stats['streak'],
    recent_prs=stats['recent_prs'],
    freq_chart_json=json.dumps(stats['freq_chart']),
    has_freq_data=stats['has_freq_data'],
    re_engagement=stats['re_engagement'],    # <-- ADD THIS
)
# And add log line:
logger.info(
    'Dashboard loaded: user=%d streak=%d re_engagement=%s',
    current_user.id, stats['streak'], stats['re_engagement']['state']
)
```

### Template Re-Engagement Section — Reference Structure

```html
{# Place after the Streak card section, before Recent PRs section #}
{% if re_engagement.state in ('inactive', 'never_logged') %}
<section class="dashboard__section dashboard__re-engagement">
  {% if re_engagement.state == 'inactive' %}
    <div class="dashboard__re-engagement-card">
      <p class="dashboard__re-engagement-text">
        Welcome back! Your last workout was {{ re_engagement.last_session_date | strftime('%b %d, %Y') }}.
        Pick up where you left off?
      </p>
      <a href="{{ url_for('workouts.plan_detail', id=re_engagement.last_plan_id) if re_engagement.last_plan_id else url_for('workouts.plans') }}"
         class="dashboard__re-engagement-btn">
        Resume Routine
      </a>
    </div>
  {% elif re_engagement.state == 'never_logged' %}
    <div class="dashboard__re-engagement-card">
      <p class="dashboard__re-engagement-text">
        Ready to start? Create your first workout plan.
      </p>
      <a href="{{ url_for('workouts.new_plan') }}"
         class="dashboard__re-engagement-btn">
        Create Plan
      </a>
    </div>
  {% endif %}
</section>
{% endif %}
```

> **⚠️ Workouts blueprint URL verification required:** Before writing the template `url_for` calls, check `gymtrack/app/blueprints/workouts/routes.py` for the exact endpoint names. Common patterns: `workouts.plan_detail` with kwarg `id`, `workouts.plans` or `workouts.plan_list` for the list, `workouts.new_plan` for create. If endpoint names differ, use the actual names. Do NOT guess.

### CSS Additions (append to end of `app/static/css/style.css`)

```css
/* ── Dashboard: Re-Engagement Card ── */
.dashboard__re-engagement-card {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.dashboard__re-engagement-text {
  margin: 0 0 0.75rem;
  color: #1e40af;
  font-size: 0.95rem;
}

.dashboard__re-engagement-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: #1d4ed8;
  color: #fff;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 600;
}

.dashboard__re-engagement-btn:hover {
  background: #1e40af;
}
```

### Test Helper Pattern

Extend the existing test file. Re-use the helpers already present:

```python
# Helper already in test_dashboard.py — use as-is
def make_session(db, user_id, is_complete=True, days_ago=0):
    started = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)
    ws = WorkoutSession(user_id=user_id, started_at=started, is_complete=is_complete)
    db.session.add(ws)
    db.session.commit()
    return ws

# New helper needed for plans
from app.models.workout_plan import WorkoutPlan

def make_plan(db, user_id, name='My Plan'):
    plan = WorkoutPlan(user_id=user_id, name=name)
    db.session.add(plan)
    db.session.commit()
    return plan
```

Example test structure:

```python
def test_dashboard_re_engagement_shown_when_inactive_14_days(app):
    """AC1: last session 15 days ago → welcome-back card shown."""
    with app.app_context():
        user, c = _make_streak_user(app, email='re_engage_inactive@example.com')
        make_session(_db, user.id, is_complete=True, days_ago=15)
        resp = c.get('/dashboard/')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8')
        assert 'Welcome back!' in body
        assert 'Resume Routine' in body

def test_dashboard_re_engagement_hidden_when_active(app):
    """AC2: last session 7 days ago → no re-engagement card."""
    with app.app_context():
        user, c = _make_streak_user(app, email='re_engage_active@example.com')
        make_session(_db, user.id, is_complete=True, days_ago=7)
        resp = c.get('/dashboard/')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8')
        assert 'Welcome back!' not in body
        assert 'Ready to start?' not in body

def test_dashboard_re_engagement_getting_started_for_new_user(app):
    """AC3: no sessions → getting-started prompt."""
    with app.app_context():
        user, c = _make_streak_user(app, email='re_engage_new@example.com')
        resp = c.get('/dashboard/')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8')
        assert 'Ready to start?' in body
        assert 'Create Plan' in body
```

### Behaviour at the 14-Day Boundary

- `days_since = 13`: active → no card
- `days_since = 14`: inactive → card shown
- `days_since = 0` (session today): active → no card

The threshold check is strictly `< 14`, meaning 14 is the first day the card appears.

### Project Structure Notes

- `get_re_engagement_data` lives in `gymtrack/app/services/stats.py` alongside the existing aggregation helpers (NOT in a new file).
- `WorkoutPlan` model is in `gymtrack/app/models/workout_plan.py` — import it in `stats.py`.
- `WorkoutSession.plan_id` exists (nullable FK to `workout_plans.id`) but is NOT used for this feature — instead, query `WorkoutPlan` directly for the most recent plan the user created, which gives a safer fallback than relying on `plan_id` on the last session.
- No new blueprint or migration is required; this is purely a service + template + test change.
- No new model columns or migrations needed.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Services Layer]
- [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint Internal Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#CSS Conventions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Date/Time Handling]
- [Source: _bmad-output/implementation-artifacts/7-2-workout-streak-display.md#Dev Notes]
- [Source: gymtrack/app/services/stats.py]
- [Source: gymtrack/app/blueprints/dashboard/routes.py]
- [Source: gymtrack/app/templates/dashboard/index.html]
- [Source: gymtrack/tests/test_dashboard.py]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (claude-sonnet-4.6)

### Debug Log References

### Completion Notes List

### File List
