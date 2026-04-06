from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

def make_pet(name: str = "TestPet") -> Pet:
    return Pet(name=name, species="Dog")


def make_owner(minutes: int = 120) -> Owner:
    return Owner(
        name="Alex",
        daily_available_time=minutes,
        preferences=[],
        energy_level="medium",
        time_windows=["morning", "evening"],
    )


def make_task(
    pet: Pet,
    name: str = "Test Task",
    duration: int = 10,
    priority: str = "medium",
    frequency: str = "daily",
    time_constraints: str = "any",
    last_completed=None,
    scheduled_time=None,
) -> Task:
    return Task(
        name=name,
        duration=duration,
        priority=priority,
        frequency=frequency,
        time_constraints=time_constraints,
        pet=pet,
        last_completed=last_completed,
        scheduled_time=scheduled_time,
    )


def make_scheduler(minutes: int = 120) -> tuple:
    """Return (owner, scheduler) with no pets yet."""
    owner = make_owner(minutes)
    return owner, Scheduler(owner)


# ------------------------------------------------------------------
# Test 1 – Task Completion (existing)
# ------------------------------------------------------------------
def test_mark_complete_changes_status():
    """mark_complete() should set completed=True and record today's date."""
    pet = make_pet()
    task = make_task(pet)

    assert task.completed is False
    assert task.last_completed is None

    task.mark_complete()

    assert task.completed is True
    assert task.last_completed == date.today()


# ------------------------------------------------------------------
# Test 2 – Task Addition (existing)
# ------------------------------------------------------------------
def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task count by one per task added."""
    pet = make_pet()

    assert len(pet.get_tasks()) == 0

    pet.add_task(make_task(pet))
    assert len(pet.get_tasks()) == 1

    pet.add_task(make_task(pet, name="Another Task"))
    assert len(pet.get_tasks()) == 2


# ------------------------------------------------------------------
# Test 3 – Sorting Correctness (happy path)
# ------------------------------------------------------------------
def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should reorder tasks earliest-to-latest regardless of insertion order."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    t1 = make_task(pet, name="Late Task",    scheduled_time="19:00")
    t2 = make_task(pet, name="Early Task",   scheduled_time="07:30")
    t3 = make_task(pet, name="Midday Task",  scheduled_time="12:00")

    sorted_tasks = scheduler.sort_by_time([t1, t2, t3])

    assert [t.scheduled_time for t in sorted_tasks] == ["07:30", "12:00", "19:00"], \
        "Tasks should be ordered earliest to latest"


def test_sort_by_time_places_untimed_tasks_last():
    """Tasks with no scheduled_time should always appear after timed tasks."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    timed   = make_task(pet, name="Timed",   scheduled_time="08:00")
    untimed = make_task(pet, name="Untimed", scheduled_time=None)

    result = scheduler.sort_by_time([untimed, timed])

    assert result[0].name == "Timed",   "Timed task should come first"
    assert result[1].name == "Untimed", "Untimed task should be last"


def test_sort_by_time_all_untimed_no_crash():
    """sort_by_time() with all None scheduled_times should not raise."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    tasks = [make_task(pet, name=f"Task {i}") for i in range(3)]
    result = scheduler.sort_by_time(tasks)

    assert len(result) == 3, "All tasks should be returned even if none have a time"


# ------------------------------------------------------------------
# Test 4 – Recurrence Logic (happy path + edge cases)
# ------------------------------------------------------------------
def test_mark_task_complete_creates_recurring_instance():
    """mark_task_complete() should add a new task to the pet for daily tasks."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    task = make_task(pet, frequency="daily",
                     last_completed=date.today() - timedelta(days=1))
    pet.add_task(task)

    assert len(pet.get_tasks()) == 1

    next_task = scheduler.mark_task_complete(task)

    assert len(pet.get_tasks()) == 2,            "A new recurring instance should be added"
    assert next_task is not None,                "Should return the new Task"
    assert next_task.completed is False,         "New instance should not be completed"
    assert next_task.is_due_today() is False,    "New instance should not be due today"


def test_recurring_task_next_due_is_tomorrow_for_daily():
    """next_due on a completed daily task should be exactly today + 1 day."""
    pet = make_pet()
    task = make_task(pet, frequency="daily")

    task.mark_complete()

    assert task.next_due == date.today() + timedelta(days=1), \
        "Daily task next_due should be tomorrow"


def test_recurring_task_next_due_is_7_days_for_weekly():
    """next_due on a completed weekly task should be today + 7 days."""
    pet = make_pet()
    task = make_task(pet, frequency="weekly")

    task.mark_complete()

    assert task.next_due == date.today() + timedelta(days=7), \
        "Weekly task next_due should be 7 days from today"


def test_mark_task_complete_unknown_frequency_returns_none():
    """mark_task_complete() should return None for tasks with unknown frequency."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    task = make_task(pet, frequency="never")
    pet.add_task(task)

    result = scheduler.mark_task_complete(task)

    assert result is None, "Unknown frequency should return None, not crash"


# ------------------------------------------------------------------
# Test 5 – Conflict Detection (happy path + edge cases)
# ------------------------------------------------------------------
def test_detect_conflicts_flags_cross_pet_collision():
    """Two tasks from different pets at the same time should produce a cross-pet warning."""
    _, scheduler = make_scheduler()

    buddy = make_pet("Buddy")
    luna  = make_pet("Luna")

    t1 = make_task(buddy, name="Walk",    scheduled_time="08:00")
    t2 = make_task(luna,  name="Feeding", scheduled_time="08:00")

    conflicts = scheduler.detect_conflicts([t1, t2])

    assert len(conflicts) == 1,              "Should detect exactly one conflict"
    assert "cross-pet conflict" in conflicts[0], "Should be labelled as cross-pet"
    assert "08:00" in conflicts[0],          "Should name the conflicting time slot"


def test_detect_conflicts_flags_same_pet_collision():
    """Two tasks from the same pet at the same time should produce a same-pet warning."""
    _, scheduler = make_scheduler()
    pet = make_pet("Buddy")

    t1 = make_task(pet, name="Brush",     scheduled_time="19:00")
    t2 = make_task(pet, name="Ear Clean", scheduled_time="19:00")

    conflicts = scheduler.detect_conflicts([t1, t2])

    assert len(conflicts) == 1,             "Should detect exactly one conflict"
    assert "same-pet conflict" in conflicts[0], "Should be labelled as same-pet"


def test_detect_conflicts_no_conflict_returns_empty_list():
    """Tasks at different times should return an empty list — no false positives."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    t1 = make_task(pet, name="Morning", scheduled_time="08:00")
    t2 = make_task(pet, name="Evening", scheduled_time="19:00")

    conflicts = scheduler.detect_conflicts([t1, t2])

    assert conflicts == [], "No conflict should return an empty list"


def test_detect_conflicts_ignores_untimed_tasks():
    """Tasks with no scheduled_time should never trigger a conflict warning."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    t1 = make_task(pet, name="A", scheduled_time=None)
    t2 = make_task(pet, name="B", scheduled_time=None)

    conflicts = scheduler.detect_conflicts([t1, t2])

    assert conflicts == [], "Untimed tasks should not generate conflict warnings"


def test_detect_conflicts_three_tasks_same_slot_one_warning():
    """Three tasks at the same slot should produce exactly one warning, not two."""
    _, scheduler = make_scheduler()
    pet = make_pet()

    tasks = [make_task(pet, name=f"Task {i}", scheduled_time="10:00") for i in range(3)]
    conflicts = scheduler.detect_conflicts(tasks)

    assert len(conflicts) == 1, "Three tasks at the same slot = one conflict warning"


# ------------------------------------------------------------------
# Test 6 – Budget packing edge cases
# ------------------------------------------------------------------
def test_generate_plan_respects_budget():
    """Tasks that would exceed the daily budget should be dropped."""
    owner = make_owner(minutes=20)
    pet = make_pet()
    owner.add_pet(pet)

    pet.add_task(make_task(pet, name="Big Task",   duration=15, priority="high"))
    pet.add_task(make_task(pet, name="Small Task", duration=10, priority="medium"))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    total = sum(t.duration for t in plan)
    assert total <= 20, f"Total duration {total} exceeds budget of 20 min"


def test_generate_plan_empty_when_no_tasks():
    """An owner with no pet tasks should produce an empty plan without crashing."""
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)   # pet has zero tasks

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    assert plan == [], "Plan should be empty when no tasks exist"


def test_generate_plan_empty_when_no_pets():
    """An owner with no pets at all should produce an empty plan without crashing."""
    owner = make_owner()
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    assert plan == [], "Plan should be empty when owner has no pets"


# ------------------------------------------------------------------
# Run directly: python tests/test_pawpal.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_mark_complete_changes_status,
        test_add_task_increases_pet_task_count,
        test_sort_by_time_returns_chronological_order,
        test_sort_by_time_places_untimed_tasks_last,
        test_sort_by_time_all_untimed_no_crash,
        test_mark_task_complete_creates_recurring_instance,
        test_recurring_task_next_due_is_tomorrow_for_daily,
        test_recurring_task_next_due_is_7_days_for_weekly,
        test_mark_task_complete_unknown_frequency_returns_none,
        test_detect_conflicts_flags_cross_pet_collision,
        test_detect_conflicts_flags_same_pet_collision,
        test_detect_conflicts_no_conflict_returns_empty_list,
        test_detect_conflicts_ignores_untimed_tasks,
        test_detect_conflicts_three_tasks_same_slot_one_warning,
        test_generate_plan_respects_budget,
        test_generate_plan_empty_when_no_tasks,
        test_generate_plan_empty_when_no_pets,
    ]
    for fn in tests:
        fn()
        print(f"PASS  {fn.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
