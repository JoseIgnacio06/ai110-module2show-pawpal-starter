from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------
owner = Owner(
    name="Alex",
    daily_available_time=120,
    preferences=[],
    energy_level="medium",
    time_windows=["morning", "evening"],
)

buddy = Pet(name="Buddy", species="Dog")
luna  = Pet(name="Luna",  species="Cat")
owner.add_pet(buddy)
owner.add_pet(luna)

# ------------------------------------------------------------------
# Tasks — intentional conflicts baked in
#
#   08:00  Buddy: Morning Walk   ┐ same time, different pets  → cross-pet conflict
#   08:00  Luna:  Morning Feed   ┘
#
#   19:00  Buddy: Evening Brush  ┐ same time, same pet        → same-pet conflict
#   19:00  Buddy: Ear Cleaning   ┘
#
#   10:00  Luna:  Vet Check-up     no collision at this slot
# ------------------------------------------------------------------

buddy.add_task(Task(
    name="Morning Walk",
    duration=20,
    priority="high",
    frequency="daily",
    time_constraints="morning",
    pet=buddy,
    last_completed=date.today() - timedelta(days=1),
    scheduled_time="08:00",            # CONFLICT: cross-pet with Luna's feed
))

luna.add_task(Task(
    name="Morning Feeding",
    duration=5,
    priority="high",
    frequency="daily",
    time_constraints="morning",
    pet=luna,
    last_completed=None,
    scheduled_time="08:00",            # CONFLICT: cross-pet with Buddy's walk
))

buddy.add_task(Task(
    name="Evening Brush",
    duration=10,
    priority="medium",
    frequency="daily",
    time_constraints="evening",
    pet=buddy,
    last_completed=date.today() - timedelta(days=1),
    scheduled_time="19:00",            # CONFLICT: same-pet with Ear Cleaning
))

buddy.add_task(Task(
    name="Ear Cleaning",
    duration=10,
    priority="medium",
    frequency="weekly",
    time_constraints="evening",
    pet=buddy,
    last_completed=date.today() - timedelta(days=8),
    scheduled_time="19:00",            # CONFLICT: same-pet with Evening Brush
))

luna.add_task(Task(
    name="Vet Check-up",
    duration=30,
    priority="high",
    frequency="monthly",
    time_constraints="morning",
    pet=luna,
    last_completed=date.today() - timedelta(days=35),
    scheduled_time="10:00",            # no conflict
))

# ------------------------------------------------------------------
# Run the planner
# ------------------------------------------------------------------
scheduler  = Scheduler(owner)
daily_plan = scheduler.create_daily_plan()

# ------------------------------------------------------------------
# Print: Today's Schedule
# ------------------------------------------------------------------
print("=" * 58)
print("  PAWPAL+ — TODAY'S SCHEDULE")
print(f"  {daily_plan['date']}  |  Owner: {owner.name}")
print("=" * 58)
for i, task in enumerate(scheduler.sort_by_time(daily_plan["tasks"]), start=1):
    time_label = task.scheduled_time or "??:??"
    print(f"  {i}. {time_label}  {task.describe()}")
print("-" * 58)
print(f"  Total: {daily_plan['total_duration']} / {owner.daily_available_time} min")

# ------------------------------------------------------------------
# Print: Conflict warnings
# ------------------------------------------------------------------
print("\n" + "=" * 58)
print("  CONFLICT DETECTION")
print("=" * 58)
if daily_plan["conflicts"]:
    for warning in daily_plan["conflicts"]:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts detected.")

# ------------------------------------------------------------------
# Print: Scheduler decisions
# ------------------------------------------------------------------
print("\n--- Scheduler Decisions ---")
for line in daily_plan["explanations"]:
    print(" ", line)
