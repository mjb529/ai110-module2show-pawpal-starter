from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    scheduled_time: str          # "HH:MM" 24-hour format
    duration_minutes: int
    priority: str                # "low" | "medium" | "high"
    frequency: str               # "once" | "daily" | "weekly"
    pet_name: str = ""
    is_complete: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return the next occurrence for recurring tasks."""
        self.is_complete = True
        if self.frequency == "daily":
            return Task(
                description=self.description,
                scheduled_time=self.scheduled_time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                description=self.description,
                scheduled_time=self.scheduled_time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None


@dataclass
class Pet:
    """Stores pet details and owns a list of Tasks."""

    name: str
    species: str
    date_of_birth: date
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks belonging to this pet."""
        return self.tasks


class Owner:
    """Manages a collection of Pets and tracks blocked time slots."""

    def __init__(self, name: str) -> None:
        """Initialise an Owner with a name."""
        self.name: str = name
        self.pets: List[Pet] = []
        self.blocked_times: List[str] = []   # "HH:MM" strings

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def block_time(self, time_str: str) -> None:
        """Mark a time slot as unavailable (owner is busy)."""
        self.blocked_times.append(time_str)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all pets."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks


class Scheduler:
    """The scheduling brain: retrieves, sorts, filters, and analyses tasks."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        """Bind the Scheduler to an Owner."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Core retrieval
    # ------------------------------------------------------------------

    def get_todays_tasks(self) -> List[Task]:
        """Return incomplete tasks whose due_date is today."""
        today = date.today()
        return [
            t for t in self.owner.get_all_tasks()
            if t.due_date == today and not t.is_complete
        ]

    # ------------------------------------------------------------------
    # Sorting & filtering
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort a task list chronologically by scheduled_time (HH:MM)."""
        return sorted(tasks, key=lambda t: t.scheduled_time)

    def filter_tasks(
        self,
        tasks: List[Task],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Filter tasks by pet name and/or completion status."""
        result = tasks
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        if completed is not None:
            result = [t for t in result if t.is_complete == completed]
        return result

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Return warning strings for any two tasks sharing the same time slot."""
        seen: dict = {}
        warnings: List[str] = []
        for task in tasks:
            key = task.scheduled_time
            if key in seen:
                warnings.append(
                    f"Conflict at {key}: '{seen[key]}' and '{task.description}'"
                )
            else:
                seen[key] = task.description
        return warnings

    # ------------------------------------------------------------------
    # Recurring task management
    # ------------------------------------------------------------------

    def mark_task_complete(self, task: Task) -> None:
        """Complete a task and auto-schedule the next occurrence if recurring."""
        next_task = task.mark_complete()
        if next_task:
            for pet in self.owner.pets:
                if pet.name == task.pet_name:
                    pet.add_task(next_task)
                    break

    # ------------------------------------------------------------------
    # Schedule generation
    # ------------------------------------------------------------------

    def generate_schedule(self) -> dict:
        """Build a full daily schedule with sorted tasks, conflict warnings, and reasoning."""
        todays_tasks = self.get_todays_tasks()
        sorted_tasks = self.sort_by_time(todays_tasks)
        conflicts = self.detect_conflicts(sorted_tasks)

        reasoning: List[str] = []
        for task in sorted_tasks:
            if task.scheduled_time in self.owner.blocked_times:
                reasoning.append(
                    f"⚠  {task.description} overlaps a blocked owner slot at {task.scheduled_time}."
                )
            else:
                p = task.priority.capitalize()
                reasoning.append(
                    f"✓  [{task.scheduled_time}] {task.description} "
                    f"({p} priority, {task.duration_minutes} min) — {task.pet_name}"
                )

        return {
            "tasks": sorted_tasks,
            "conflicts": conflicts,
            "reasoning": reasoning,
        }
