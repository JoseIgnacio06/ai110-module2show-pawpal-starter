from datetime import date
from pawpal_system import Pet, Task


def make_task(pet: Pet) -> Task:
    """Helper: return a basic daily Task attached to the given pet."""
    return Task(
        name="Test Task",
        duration=10,
        priority="medium",
        frequency="daily",
        time_constraints="any",
        pet=pet,
    )


def make_pet() -> Pet:
    """Helper: return a bare Pet with no tasks."""
    return Pet(name="TestPet", species="Dog")


# ------------------------------------------------------------------
# Test 1 – Task Completion
# ------------------------------------------------------------------
def test_mark_complete_changes_status():
    """mark_complete() should set completed=True and record today's date."""
    pet = make_pet()
    task = make_task(pet)

    assert task.completed is False, "Task should start as not completed"
    assert task.last_completed is None, "last_completed should start as None"

    task.mark_complete()

    assert task.completed is True, "completed should be True after mark_complete()"
    assert task.last_completed == date.today(), "last_completed should be set to today"


# ------------------------------------------------------------------
# Test 2 – Task Addition
# ------------------------------------------------------------------
def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task count by one per task added."""
    pet = make_pet()

    assert len(pet.get_tasks()) == 0, "Pet should start with zero tasks"

    task_a = make_task(pet)
    pet.add_task(task_a)
    assert len(pet.get_tasks()) == 1, "Pet should have 1 task after first add"

    task_b = make_task(pet)
    pet.add_task(task_b)
    assert len(pet.get_tasks()) == 2, "Pet should have 2 tasks after second add"


# ------------------------------------------------------------------
# Run directly: python tests/test_pawpal.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    test_mark_complete_changes_status()
    print("PASS  test_mark_complete_changes_status")

    test_add_task_increases_pet_task_count()
    print("PASS  test_add_task_increases_pet_task_count")

    print("\nAll tests passed.")
