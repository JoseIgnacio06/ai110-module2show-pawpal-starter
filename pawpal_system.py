from __future__ import annotations
from typing import List, Dict


class Task:
    def __init__(
        self,
        name: str,
        duration: int,
        priority: str,
        frequency: str,
        time_constraints: str,
        pet: Pet,
    ):
        self.name = name
        self.duration = duration          # minutes
        self.priority = priority          # e.g. "high", "medium", "low"
        self.frequency = frequency        # e.g. "daily", "weekly"
        self.time_constraints = time_constraints  # e.g. "morning", "any"
        self.pet = pet

    def is_due_today(self) -> bool:
        pass

    def fits_constraints(self, owner_constraints) -> bool:
        pass

    def describe(self) -> str:
        pass


class Pet:
    def __init__(self, name: str, species: str, notes: str = ""):
        self.name = name
        self.species = species
        self.tasks: List[Task] = []
        self.notes = notes

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> List[Task]:
        pass


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
        self.daily_available_time = daily_available_time  # minutes
        self.preferences = preferences
        self.energy_level = energy_level   # e.g. "low", "medium", "high"
        self.time_windows = time_windows   # e.g. ["morning", "evening"]

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def update_constraints(
        self,
        time: int,
        preferences: List[str],
        energy_level: str,
    ) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: List[Task] = []
        self.constraints: Dict = {}

    def collect_tasks(self) -> None:
        pass

    def filter_tasks(self) -> List[Task]:
        pass

    def prioritize_tasks(self) -> List[Task]:
        pass

    def generate_plan(self) -> List[Task]:
        pass

    def explain_decisions(self) -> List[str]:
        pass

    def create_daily_plan(self) -> Dict:
        pass
