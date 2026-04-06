# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The scheduler goes beyond a simple priority list. Here is what it does and why:

**Constraint-aware filtering**: Before any task is considered, `filter_tasks()` checks two conditions: the task must be due today (based on `frequency` and `last_completed` using `timedelta`), and it must fit the owner's current `time_windows` and `energy_level`. Tasks that fail either check are logged as `SKIP` with a reason — nothing is silently dropped.

**Priority + time-slot sorting**: `prioritize_tasks()` orders due tasks from high to medium to low priority. `sort_by_time()` then reorders the final plan by `scheduled_time` ("HH:MM") so the owner sees tasks in the natural order they should happen during the day.

**Greedy budget packing**: `generate_plan()` fills the owner's `daily_available_time` starting from the highest-priority tasks. If a task would exceed the remaining budget it is logged as `DROP` and skipped — lower-priority tasks that still fit are included. This guarantees the most important care always makes it into the plan.

**Per-pet and status filtering**: `filter_by(tasks, pet_name, completed)` lets callers slice the task list by pet, by completion status, or both. This powers views like "show me only Buddy's pending tasks" without touching the scheduler's internal state.

**Recurring task automation**: Calling `scheduler.mark_task_complete(task)` marks the task done, calculates `next_due` with `timedelta`, and automatically adds a fresh instance to the pet's task list. The new instance is not due until the frequency threshold passes again, so it will not appear in today's plan twice.

**Conflict detection**: `detect_conflicts(tasks)` scans the scheduled plan for any two tasks that share the same `scheduled_time`. Same-pet and cross-pet collisions are labelled separately and returned as warning strings. The planner never crashes — it warns and continues.

## Testing PawPal+

### Running the tests

python -m pytest

### What the tests cover

The suite contains 17 tests across five areas:

1. Area: **Task completion** 2 Tests 
What is verified: `mark_complete()` sets `completed=True` and records today's date; `add_task()` increments pet task count.

2. Area: **Sorting** 3 Tests 
What is verified: Tasks sort chronologically by `scheduled_time`; untimed tasks sink to the end; all-`None` list does not crash.

3. Area: **Recurrence** 4 Tests  
What is verified: Completing a daily task creates a new non-due instance; `next_due` is exactly today + 1 day (daily) or + 7 days (weekly); unknown frequency returns `None` without crashing.

4. Area: **Conflict detection** 5 Tests 
What is verified: Cross-pet and same-pet collisions are labelled correctly; no collision returns empty list; untimed tasks are ignored; three tasks at one slot produce one warning, not two.

5. Area: **Budget packing** 3 Tests 
What is verified: Plan never exceeds `daily_available_time`; empty pet returns empty plan; owner with no pets returns empty plan.

### Confidence level (4 / 5)

The core scheduling pipeline (filtering, prioritizing, budget packing, recurrence, and conflict detection) is fully covered by unit tests, and all 17 pass. The one-star deduction reflects what is not yet tested: the Streamlit UI layer (`app.py`), `st.session_state` persistence across reruns, and integration between the UI inputs and the scheduler output. Those paths can only be verified with browser-level or end-to-end tests, which are not included in the current suite.

## Features

- **Constraint-aware daily planning**: The scheduler filters every task against the owner's available time budget, time-of-day windows (morning/afternoon/evening), and energy level before adding anything to the plan. Tasks that fail a constraint are logged as skipped with a reason, never silently dropped.
- **Priority-first budget packing**: Filtered tasks are sorted high → medium → low and greedily packed into the owner's daily minute budget. The most important care is always scheduled first; lower-priority tasks are dropped only when no time remains.
- **Sorting by scheduled time**: The final plan is reordered by each task's `scheduled_time` ("HH:MM") so the owner sees tasks in the natural order they should happen during the day. Tasks without a time slot are placed at the end.
- **Per-pet and status filtering**: Any task list can be sliced by pet name (case-insensitive) or completion status (pending/done) independently or in combination, powering views like "show me only Buddy's pending tasks."
- **Daily recurrence**: Marking a task complete automatically creates a fresh instance for the next occurrence. The new instance inherits all settings but is not due until the frequency threshold passes again (1 day for daily, 7 for weekly, 30 for monthly), preventing the same task from appearing twice in one day.
- **Accurate next-due calculation**: `next_due` is computed with Python's `timedelta` rather than calendar arithmetic, so daily, weekly, and monthly intervals are always exact regardless of month length or leap years.
- **Conflict detection**: Before displaying the schedule, the planner scans for tasks sharing the same `scheduled_time`. Same-pet and cross-pet collisions are labelled separately and surfaced as warnings in the UI so the owner can resolve them before the day starts.
- **Decision audit log**: Every scheduling decision (SKIP, OK, ADD, DROP, RECUR) is recorded with a plain-English reason and displayed in a colour-coded expandable log so the owner can understand exactly why each task was included or excluded.