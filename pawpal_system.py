from __future__ import annotations
from datetime import date, timedelta
from typing import List, Dict, Optional, TypedDict


class DailyPlan(TypedDict):
    date: str
    tasks: List[Task]
    total_duration: int
    explanations: List[str]
    conflicts: List[str]


# Maps priority labels to sort order (lower = scheduled first)
_PRIORITY_RANK: Dict[str, int] = {"high": 0, "medium": 1, "low": 2}
# Maps energy labels to a numeric level for comparison
_ENERGY_RANK: Dict[str, int] = {"low": 0, "medium": 1, "high": 2}
# Maps frequency labels to the minimum days before a task is due again
_FREQUENCY_DAYS: Dict[str, int] = {"daily": 1, "weekly": 7, "monthly": 30}


class Task:
    def __init__(
        self,
        name: str,
        duration: int,
        priority: str,
        frequency: str,
        time_constraints: str,
        pet: Pet,
        last_completed: Optional[date] = None,
        scheduled_time: Optional[str] = None,
    ):
        self.name = name
        self.duration = duration                      # minutes
        self.priority = priority                      # "high" | "medium" | "low"
        self.frequency = frequency                    # "daily" | "weekly" | "monthly"
        self.time_constraints = time_constraints      # "morning" | "evening" | "any"
        self.pet = pet
        self.last_completed: Optional[date] = last_completed
        self.scheduled_time: Optional[str] = scheduled_time  # "HH:MM", e.g. "08:00"
        self.completed: bool = False
        self.next_due: Optional[date] = None  # set by mark_complete()

    def mark_complete(self) -> None:
        """Mark the task done, record today, and calculate the next due date.

        next_due uses timedelta so the arithmetic is always exact:
            daily   → today + timedelta(days=1)
            weekly  → today + timedelta(days=7)
            monthly → today + timedelta(days=30)
        timedelta(days=N) adds exactly N * 24 h, avoiding any month-length
        or leap-year ambiguity that calendar arithmetic would introduce.
        """
        self.completed = True
        self.last_completed = date.today()
        days_ahead = _FREQUENCY_DAYS.get(self.frequency, 1)
        self.next_due = date.today() + timedelta(days=days_ahead)

    def recur(self) -> Task:
        """Return a fresh Task instance for the next occurrence.

        last_completed is set to today so is_due_today() correctly returns
        False until the frequency threshold has passed again.
        """
        return Task(
            name=self.name,
            duration=self.duration,
            priority=self.priority,
            frequency=self.frequency,
            time_constraints=self.time_constraints,
            pet=self.pet,
            last_completed=date.today(),
            scheduled_time=self.scheduled_time,
        )

    def is_due_today(self) -> bool:
        """Return True if enough time has passed since last completion per frequency."""
        if self.last_completed is None:
            return True
        days_since = (date.today() - self.last_completed).days
        threshold = _FREQUENCY_DAYS.get(self.frequency, 1)
        return days_since >= threshold

    def fits_constraints(self, owner_constraints: Dict) -> bool:
        """Return True if this task can be performed given the owner's current constraints."""
        # Time window: task must match one of the owner's available windows (unless "any")
        if self.time_constraints != "any":
            available_windows = owner_constraints.get("time_windows", [])
            if self.time_constraints not in available_windows:
                return False

        # Energy gate: high-priority tasks require at least medium energy
        owner_energy = _ENERGY_RANK.get(owner_constraints.get("energy_level", "medium"), 1)
        if self.priority == "high" and owner_energy < _ENERGY_RANK["medium"]:
            return False

        return True

    def describe(self) -> str:
        """Return a human-readable one-line summary of this task."""
        last = self.last_completed.isoformat() if self.last_completed else "never"
        return (
            f"[{self.priority.upper()}] {self.name} for {self.pet.name} "
            f"— {self.duration} min, {self.frequency}, {self.time_constraints} "
            f"(last done: {last})"
        )


class Pet:
    def __init__(self, name: str, species: str, notes: str = ""):
        self.name = name
        self.species = species
        self.tasks: List[Task] = []
        self.notes = notes

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and enforce the bidirectional pet↔task link."""
        task.pet = self
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet if it exists."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        """Return a copy of the task list (safe for external iteration)."""
        return list(self.tasks)


class Owner:
    def __init__(
        self,
        name: str,
        daily_available_time: int,
        preferences: List[str],
        energy_level: str,
        time_windows: List[str],
    ):
        self.name = name
        self.pets: List[Pet] = []
        self.daily_available_time = daily_available_time  # minutes per day
        self.preferences = preferences
        self.energy_level = energy_level    # "low" | "medium" | "high"
        self.time_windows = time_windows    # e.g. ["morning", "evening"]

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner (no-op if already added)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Unregister a pet from this owner (no-op if not found)."""
        if pet in self.pets:
            self.pets.remove(pet)

    def update_constraints(
        self,
        time: int,
        preferences: List[str],
        energy_level: str,
    ) -> None:
        """Update the owner's availability and energy for the current planning cycle."""
        self.daily_available_time = time
        self.preferences = preferences
        self.energy_level = energy_level

    def get_all_tasks(self) -> List[Task]:
        """Flatten all tasks across every owned pet into a single list."""
        return [task for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: List[Task] = []
        self.constraints: Dict = self._build_constraints()
        self._decisions: List[str] = []   # audit log populated during planning

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_constraints(self) -> Dict:
        """Snapshot the owner's current constraints as a plain dict."""
        return {
            "daily_available_time": self.owner.daily_available_time,
            "preferences": self.owner.preferences,
            "energy_level": self.owner.energy_level,
            "time_windows": self.owner.time_windows,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_tasks(self) -> None:
        """Refresh both the task list and constraints from the owner.

        Always call this before filtering or planning so stale data
        (e.g. after remove_pet or update_constraints) is discarded.
        """
        self.constraints = self._build_constraints()
        self.tasks = self.owner.get_all_tasks()
        self._decisions = []

    def filter_tasks(self) -> List[Task]:
        """Return only tasks that are due today AND fit the owner's constraints."""
        filtered: List[Task] = []
        for task in self.tasks:
            if not task.is_due_today():
                self._decisions.append(
                    f"SKIP  '{task.name}' ({task.pet.name}): not due today "
                    f"[{task.frequency}, last={task.last_completed}]"
                )
                continue
            if not task.fits_constraints(self.constraints):
                self._decisions.append(
                    f"SKIP  '{task.name}' ({task.pet.name}): constraint mismatch "
                    f"[window={task.time_constraints}, energy={self.constraints['energy_level']}]"
                )
                continue
            self._decisions.append(
                f"OK    '{task.name}' ({task.pet.name}): due today and fits constraints"
            )
            filtered.append(task)
        return filtered

    def prioritize_tasks(self) -> List[Task]:
        """Sort filtered tasks: high → medium → low priority."""
        return sorted(
            self.filter_tasks(),
            key=lambda t: _PRIORITY_RANK.get(t.priority, 1),
        )

    def generate_plan(self) -> List[Task]:
        """Build the final ordered task list that fits within the daily time budget.

        Collects and refreshes all state first, then greedily fills the
        budget starting from the highest-priority tasks.
        """
        self.collect_tasks()
        budget: int = self.constraints["daily_available_time"]
        time_used: int = 0
        plan: List[Task] = []

        for task in self.prioritize_tasks():
            if time_used + task.duration <= budget:
                plan.append(task)
                time_used += task.duration
                self._decisions.append(
                    f"ADD   '{task.name}': {task.duration} min "
                    f"(used {time_used}/{budget} min)"
                )
            else:
                self._decisions.append(
                    f"DROP  '{task.name}': {task.duration} min would exceed budget "
                    f"({time_used + task.duration}/{budget} min)"
                )

        return plan

    def filter_by(
        self,
        tasks: List[Task],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Filter a task list by pet name, completion status, or both.

        Args:
            tasks:      The list to filter (e.g. from generate_plan or get_all_tasks).
            pet_name:   Keep only tasks belonging to this pet (case-insensitive).
                        Pass None to skip this filter.
            completed:  Pass True for completed tasks, False for pending,
                        None to skip this filter.

        Examples:
            # All pending tasks across every pet
            scheduler.filter_by(all_tasks, completed=False)

            # Completed tasks for Buddy only
            scheduler.filter_by(all_tasks, pet_name="Buddy", completed=True)
        """
        result = tasks
        if pet_name is not None:
            result = [t for t in result if t.pet.name.lower() == pet_name.lower()]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        return result

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by scheduled_time in ascending order ("HH:MM").

        Tasks without a scheduled_time are placed at the end.

        How the lambda works:
          sorted() calls the key function once per item to get a
          comparison value. "HH:MM" strings are zero-padded, so they
          sort correctly as plain strings ("08:00" < "14:30" < "23:00").
          Tasks missing a time get "99:99" so they always sink to the end.

        Example:
            tasks = [task_at_14h, task_at_08h, task_no_time]
            sort_by_time(tasks)
            → [task_at_08h, task_at_14h, task_no_time]
        """
        return sorted(
            tasks,
            key=lambda t: t.scheduled_time if t.scheduled_time is not None else "99:99",
        )

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Return a warning string for every pair of tasks that share a scheduled_time.

        Strategy (lightweight — warns, never raises):
          - Only tasks that have a scheduled_time are checked.
          - Tasks without a time are silently ignored; no crash, no false positives.
          - Each unique time slot is grouped; any slot with 2+ tasks is a conflict.
          - Same-pet and cross-pet collisions are both caught and labelled differently.

        Returns an empty list when there are no conflicts.
        """
        warnings: List[str] = []

        # Group tasks by their scheduled_time, skipping any that have no time set
        slots: Dict[str, List[Task]] = {}
        for task in tasks:
            if task.scheduled_time is None:
                continue
            slots.setdefault(task.scheduled_time, []).append(task)

        for time_slot, slot_tasks in sorted(slots.items()):
            if len(slot_tasks) < 2:
                continue  # no conflict at this slot

            names = ", ".join(f"'{t.name}' ({t.pet.name})" for t in slot_tasks)
            pets  = {t.pet.name for t in slot_tasks}

            if len(pets) == 1:
                label = "same-pet conflict"
            else:
                label = "cross-pet conflict"

            warnings.append(
                f"CONFLICT at {time_slot} [{label}]: {names}"
            )

        return warnings

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete and auto-create the next occurrence for recurring tasks.

        For daily/weekly/monthly tasks a new Task instance is added to the
        same pet immediately, with last_completed=today so it won't appear
        in today's plan again.  The next_due date on the completed task shows
        exactly when the new instance will become due.

        Returns the new Task instance, or None for non-recurring tasks.
        """
        task.mark_complete()

        if task.frequency not in _FREQUENCY_DAYS:
            return None

        next_task = task.recur()
        task.pet.add_task(next_task)
        self._decisions.append(
            f"RECUR '{task.name}' ({task.pet.name}): "
            f"next due {task.next_due} [{task.frequency}]"
        )
        return next_task

    def explain_decisions(self) -> List[str]:
        """Return the audit log from the most recent generate_plan call."""
        return list(self._decisions)

    def create_daily_plan(self) -> DailyPlan:
        """Run the full planning pipeline and return a structured daily plan."""
        plan = self.generate_plan()
        return DailyPlan(
            date=date.today().isoformat(),
            tasks=plan,
            total_duration=sum(t.duration for t in plan),
            explanations=self.explain_decisions(),
            conflicts=self.detect_conflicts(plan),
        )
