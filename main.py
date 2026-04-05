from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ------------------------------------------------------------------
# 1. Create Owner
# ------------------------------------------------------------------
owner = Owner(
    name="Alex",
    daily_available_time=60,          # 60 minutes available today
    preferences=["morning walks", "short sessions"],
    energy_level="medium",
    time_windows=["morning", "evening"],
)

# ------------------------------------------------------------------
# 2. Create Pets
# ------------------------------------------------------------------
buddy = Pet(name="Buddy", species="Dog", notes="Loves fetch, needs daily walks")
luna  = Pet(name="Luna",  species="Cat", notes="Indoor cat, shy but playful")

owner.add_pet(buddy)
owner.add_pet(luna)

# ------------------------------------------------------------------
# 3. Add Tasks (mix of priorities, windows, and completion history)
# ------------------------------------------------------------------

# Buddy – morning walk: high priority, due daily, not done today
buddy.add_task(Task(
    name="Morning Walk",
    duration=20,
    priority="high",
    frequency="daily",
    time_constraints="morning",
    pet=buddy,
    last_completed=date.today() - timedelta(days=1),   # done yesterday → due today
))

# Buddy – brush teeth: medium priority, due weekly, done 8 days ago
buddy.add_task(Task(
    name="Brush Teeth",
    duration=10,
    priority="medium",
    frequency="weekly",
    time_constraints="evening",
    pet=buddy,
    last_completed=date.today() - timedelta(days=8),   # overdue → due today
))

# Buddy – flea treatment: low priority, due monthly, done 2 days ago → NOT due today
buddy.add_task(Task(
    name="Flea Treatment",
    duration=15,
    priority="low",
    frequency="monthly",
    time_constraints="any",
    pet=buddy,
    last_completed=date.today() - timedelta(days=2),   # recently done → skipped
))

# Luna – feeding: high priority, due daily, never done before
luna.add_task(Task(
    name="Morning Feeding",
    duration=5,
    priority="high",
    frequency="daily",
    time_constraints="morning",
    pet=luna,
    last_completed=None,                               # never done → always due
))

# Luna – playtime: medium priority, due daily, done today already → NOT due today
luna.add_task(Task(
    name="Playtime",
    duration=15,
    priority="medium",
    frequency="daily",
    time_constraints="evening",
    pet=luna,
    last_completed=date.today(),                       # done today → skipped
))

# Luna – vet check: high priority, due monthly, overdue by 35 days
luna.add_task(Task(
    name="Vet Check-up",
    duration=60,
    priority="high",
    frequency="monthly",
    time_constraints="morning",
    pet=luna,
    last_completed=date.today() - timedelta(days=35),  # overdue → due, but may exceed budget
))

# ------------------------------------------------------------------
# 4. Run the Scheduler and print Today's Schedule
# ------------------------------------------------------------------
scheduler = Scheduler(owner)
daily_plan = scheduler.create_daily_plan()

print("=" * 54)
print("        PAWPAL+ — TODAY'S SCHEDULE")
print(f"        {daily_plan['date']}  |  Owner: {owner.name}")
print("=" * 54)

if daily_plan["tasks"]:
    for i, task in enumerate(daily_plan["tasks"], start=1):
        print(f"  {i}. {task.describe()}")
else:
    print("  No tasks scheduled for today.")

print("-" * 54)
print(f"  Total time: {daily_plan['total_duration']} / {owner.daily_available_time} min")
print("=" * 54)

print("\n--- Scheduler Decisions ---")
for line in daily_plan["explanations"]:
    print(" ", line)
