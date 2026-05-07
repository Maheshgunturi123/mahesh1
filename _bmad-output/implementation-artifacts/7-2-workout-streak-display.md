# Story 7.2: Workout Streak Display

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a logged-in user,
I want to see my current workout streak on the dashboard,
so that I'm motivated to maintain my consistency.

## Acceptance Criteria

1. **Given** I have logged at least one session in the current week
   **When** the dashboard loads
   **Then** the streak shows the count of consecutive calendar weeks (ending with the current week) in which I logged ≥ 1 completed session
   **And** `calculate_streak(user_id)` in `app/services/streak.py` computes this as a pure function (no Flask context required)

2. **Given** I missed the previous week entirely
   **When** the dashboard loads
   **Then** my streak resets to 1 if I have logged a session this week, or 0 if I have not logged any session yet this week

3. **Given** I have a 5-week streak
   **When** the dashboard renders
   **Then** I see exactly: `🔥 5-week streak`

4. **Given** my streak is 0 (no sessions ever, or gap this week)
   **When** the dashboard renders
   **Then** I see `0 weeks` (no fire emoji)

## Tasks / Subtasks

- [x] Task 1: Verify `calculate_streak` implementation in `app/services/streak.py` (AC: 1, 2)
  - [x] **File already created by Story 7.1** — `gymtrack/app/services/streak.py`
  - [x] Confirm `calculate_streak(user_id: int) -> int` exists and passes all ACs
  - [x] A "week" = Monday–Sunday calendar week; streak = N consecutive weeks ending on the current week that each have ≥ 1 complete session
  - [x] If the current week has no session and prior week has sessions: streak = 0 (gap)
  - [x] If the current week has a session: streak counts from now backwards through each consecutive week
  - [x] Pure function — no Flask `current_user`, no `request` — only `user_id: int` arg; uses `db.session` via `app.extensions`
  - [x] See Dev Notes for exact reference implementation

- [x] Task 2: Verify dashboard template streak rendering (AC: 3, 4)
  - [x] **File already created by Story 7.1** — `gymtrack/app/templates/dashboard/index.html`
  - [x] Confirm streak section renders `🔥 {{ streak }}-week streak` when `streak > 0`
  - [x] Confirm streak section renders `0 weeks` (no emoji) when `streak == 0`
  - [x] Section must be wrapped in `<section class="dashboard__section dashboard__streak">` with `<h2>Workout Streak</h2>`
  - [x] Streak value in `<p class="dashboard__streak-value">` — color `#1d4ed8`, font-size `1.5rem`, font-weight `700`
  - [x] No changes needed if Story 7.1 is fully complete

- [x] Task 3: Add/verify streak display integration tests (AC: 1, 2, 3, 4)
  - [x] `gymtrack/tests/test_dashboard.py` — add streak-rendering tests if not already present:
    - [x] `test_dashboard_streak_shows_fire_emoji_for_active_streak` — user with sessions in last 2 consecutive weeks → response contains `🔥`
    - [x] `test_dashboard_streak_shows_zero_when_no_sessions` — no sessions → response contains `0 weeks` and does NOT contain `🔥`
    - [x] `test_dashboard_streak_shows_zero_when_gap_in_previous_week` — sessions 2 weeks ago but not last week nor this week → streak is 0 → `0 weeks` in response
    - [x] `test_dashboard_streak_single_week` — sessions only this week → response contains `🔥 1-week streak`
  - [x] `gymtrack/tests/test_streak.py` — verify these unit tests already exist (created in Story 7.1):
    - [x] `test_streak_zero_when_no_sessions`
    - [x] `test_streak_one_when_only_this_week`
    - [x] `test_streak_resets_when_week_missed`
    - [x] `test_streak_counts_consecutive_weeks`
  - [x] If tests are missing, add them using the fixture pattern from `conftest.py` (see Dev Notes)

## Dev Notes

### Context: What Story 7.1 Already Implemented

Story 7.1 (Personal Dashboard) is **done** and covers:
- `gymtrack/app/services/streak.py` — `calculate_streak(user_id)` pure function
- `gymtrack/app/services/stats.py` — `get_dashboard_stats(user_id)` calls `calculate_streak`
- `gymtrack/app/blueprints/dashboard/routes.py` — calls `get_dashboard_stats`, passes `streak` to template
- `gymtrack/app/templates/dashboard/index.html` — streak card with `🔥 N-week streak` / `0 weeks`
- `gymtrack/tests/test_streak.py` — unit tests for `calculate_streak`
- `gymtrack/tests/test_dashboard.py` — integration tests including `test_dashboard_shows_zero_streak_with_no_sessions`

**This story's job:** Verify the streak display fully satisfies AC 1–4 and add any display-level integration tests missing from `test_dashboard.py`. No new source files are expected unless verification finds gaps.

### Architecture Compliance

- Services are **pure functions** — no Flask `current_user`, no `request` context. Accept `user_id: int`. [Source: docs/architecture.md#Services Layer]
- All user-scoped queries filter by `user_id` — never by `current_user` inside a service. [Source: docs/architecture.md#Data Isolation]
- Blueprint: `app/blueprints/dashboard/` with `__init__.py` (Blueprint def) + `routes.py` (handlers). [Source: docs/architecture.md#Blueprint Internal Structure]
- CSS follows BEM naming convention; all new rules appended at end of `style.css`. [Source: docs/architecture.md#CSS Conventions]

### `calculate_streak(user_id)` — Reference Implementation

```python
# gymtrack/app/services/streak.py
import datetime
from app.extensions import db
from app.models.workout_session import WorkoutSession


def calculate_streak(user_id: int) -> int:
    """Return number of consecutive calendar weeks (Mon–Sun) ending
    with the current week in which the user logged ≥ 1 completed session."""
    rows = (
        db.session.query(WorkoutSession.started_at)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.is_complete == True,
        )
        .all()
    )
    if not rows:
        return 0

    today = datetime.date.today()
    current_monday = today - datetime.timedelta(days=today.weekday())

    weeks_with_sessions = set()
    for row in rows:
        d = row.started_at.date() if hasattr(row.started_at, 'date') else row.started_at
        week_start = d - datetime.timedelta(days=d.weekday())
        weeks_with_sessions.add(week_start)

    streak = 0
    check_week = current_monday
    while check_week in weeks_with_sessions:
        streak += 1
        check_week -= datetime.timedelta(weeks=1)

    return streak
```

### Template Streak Section — Reference Structure

```html
{# Inside gymtrack/app/templates/dashboard/index.html #}
<section class="dashboard__section dashboard__streak">
  <h2 class="dashboard__section-title">Workout Streak</h2>
  <p class="dashboard__streak-value">
    {% if streak == 0 %}
      0 weeks
    {% else %}
      🔥 {{ streak }}-week streak
    {% endif %}
  </p>
</section>
```

### Test Fixture Pattern (from `conftest.py`)

New test cases should follow the existing pattern — use the `test_client` and `logged_in_user` fixtures from `conftest.py`. Seed `WorkoutSession` rows with `is_complete=True` and controlled `started_at` dates to simulate streak scenarios.

```python
import datetime

def _monday_of_current_week():
    today = datetime.date.today()
    return today - datetime.timedelta(days=today.weekday())

def test_dashboard_streak_shows_fire_emoji_for_active_streak(client, logged_in_user, db_session):
    # Create sessions in current and previous week
    this_monday = _monday_of_current_week()
    last_monday = this_monday - datetime.timedelta(weeks=1)
    for week_start in [this_monday, last_monday]:
        session = WorkoutSession(
            user_id=logged_in_user.id,
            started_at=datetime.datetime.combine(week_start, datetime.time(10, 0)),
            is_complete=True
        )
        db_session.add(session)
    db_session.commit()

    response = client.get('/dashboard/')
    assert response.status_code == 200
    assert '🔥' in response.data.decode()
    assert '2-week streak' in response.data.decode()
```

### Project Structure Notes

- All streak logic lives in `gymtrack/app/services/streak.py` — do NOT duplicate in routes or templates
- `get_dashboard_stats(user_id)` in `stats.py` is the only caller of `calculate_streak` from the route layer
- `WorkoutSession` model is in `gymtrack/app/models/workout_session.py`
- `db` extension is from `gymtrack/app/extensions.py` (imported as `from app.extensions import db`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Services Layer]
- [Source: _bmad-output/planning-artifacts/architecture.md#Blueprint Internal Structure]
- [Source: _bmad-output/implementation-artifacts/7-1-personal-dashboard.md#Task 1]
- [Source: _bmad-output/implementation-artifacts/7-1-personal-dashboard.md#Task 8]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (claude-sonnet-4.6)

### Debug Log References

None — no implementation gaps found; all Story 7.1 artifacts were complete and correct.

### Completion Notes List

- Task 1: `gymtrack/app/services/streak.py` — `calculate_streak(user_id: int) -> int` verified. Pure function, correct Mon–Sun week logic, returns 0 on gap, counts consecutive weeks backwards from current. Matches reference implementation exactly.
- Task 2: `gymtrack/app/templates/dashboard/index.html` — streak section verified. `dashboard__section dashboard__streak`, `dashboard__streak-value` with `color: #1d4ed8; font-size: 1.5rem; font-weight: 700`. Renders `🔥 N-week streak` or `0 weeks` correctly.
- Task 3: Added 4 integration tests to `gymtrack/tests/test_dashboard.py`: `test_dashboard_streak_shows_fire_emoji_for_active_streak`, `test_dashboard_streak_shows_zero_when_no_sessions`, `test_dashboard_streak_shows_zero_when_gap_in_previous_week`, `test_dashboard_streak_single_week`. All 4 pass. Existing `test_streak.py` unit tests (4) verified present and passing.
- Full regression: 161 tests passed, 0 failures.

### File List

- VERIFIED `gymtrack/app/services/streak.py`
- VERIFIED `gymtrack/app/templates/dashboard/index.html`
- UPDATED `gymtrack/tests/test_dashboard.py` — added 4 streak display integration tests
- VERIFIED `gymtrack/tests/test_streak.py`

### Change Log

- 2026-05-05: Added streak display integration tests to `gymtrack/tests/test_dashboard.py` — AC 1–4 covered by `test_dashboard_streak_shows_fire_emoji_for_active_streak`, `test_dashboard_streak_shows_zero_when_no_sessions`, `test_dashboard_streak_shows_zero_when_gap_in_previous_week`, `test_dashboard_streak_single_week`.
