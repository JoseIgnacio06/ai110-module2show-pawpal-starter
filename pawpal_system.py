from __future__ import annotations
from datetime import date
from typing import List, Dict, Optional, TypedDict


class DailyPlan(TypedDict):
    date: str
    tasks: List[Task]
    total_duration: int
    explanations: List[str]


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
    ):
        self.name = name
        self.duration = duration                      # minutes
        self.priority = priority                      # "high" | "medium" | "low"
        self.frequency = frequency                    # "daily" | "weekly" | "monthly"
        self.time_constraints = time_constraints      # "morning" | "evening" | "any"
        self.pet = pet
        self.last_completed: Optional[date] = last_completed
        self.completed: bool = False

    def mark_complete(self) -> None:
        """Mark the task as completed and record today as the completion date."""
        self.completed = True
        self.last_completed = date.today()

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
        )
