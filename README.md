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

## Smarter Scheduling

The scheduler goes beyond a simple priority list. Here is what it does and why:

**Constraint-aware filtering**
Before any task is considered, `filter_tasks()` checks two conditions: the task must be due today (based on `frequency` and `last_completed` using `timedelta`), and it must fit the owner's current `time_windows` and `energy_level`. Tasks that fail either check are logged as `SKIP` with a reason — nothing is silently dropped.

**Priority + time-slot sorting**
`prioritize_tasks()` orders due tasks from high to medium to low priority. `sort_by_time()` then reorders the final plan by `scheduled_time` ("HH:MM") so the owner sees tasks in the natural order they should happen during the day.

**Greedy budget packing**
`generate_plan()` fills the owner's `daily_available_time` starting from the highest-priority tasks. If a task would exceed the remaining budget it is logged as `DROP` and skipped — lower-priority tasks that still fit are included. This guarantees the most important care always makes it into the plan.

**Per-pet and status filtering**
`filter_by(tasks, pet_name, completed)` lets callers slice the task list by pet, by completion status, or both. This powers views like "show me only Buddy's pending tasks" without touching the scheduler's internal state.

**Recurring task automation**
Calling `scheduler.mark_task_complete(task)` marks the task done, calculates `next_due` with `timedelta`, and automatically adds a fresh instance to the pet's task list. The new instance is not due until the frequency threshold passes again, so it will not appear in today's plan twice.

**Conflict detection**
`detect_conflicts(tasks)` scans the scheduled plan for any two tasks that share the same `scheduled_time`. Same-pet and cross-pet collisions are labelled separately and returned as warning strings. The planner never crashes — it warns and continues.

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
