"""Automated test suite for PawPal+ scheduling system."""
import pytest
from datetime import date, timedelta
from typing import Optional

from pawpal_system import Owner, Pet, Task, Scheduler


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(
    description: str = "Walk",
    time: str = "09:00",
    duration: int = 30,
    priority: str = "medium",
    frequency: str = "once",
    due: Optional[date] = None,
) -> Task:
    return Task(
        description=description,
        scheduled_time=time,
        duration_minutes=duration,
        priority=priority,
        frequency=frequency,
        due_date=due or date.today(),
    )


def make_owner_with_pet(pet_name: str = "TestPet", species: str = "dog") -> tuple:  # type: ignore[type-arg]
    owner = Owner("TestOwner")
    pet = Pet(pet_name, species, date(2020, 1, 1))
    owner.add_pet(pet)
    return owner, pet


# ── Task completion ────────────────────────────────────────────────────────────

class TestTaskCompletion:
    def test_mark_complete_sets_flag(self):
        task = make_task()
        task.mark_complete()
        assert task.is_complete is True

    def test_once_task_returns_none(self):
        task = make_task(frequency="once")
        assert task.mark_complete() is None

    def test_daily_task_returns_next_day(self):
        today = date.today()
        task = make_task(frequency="daily", due=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert not next_task.is_complete

    def test_weekly_task_returns_next_week(self):
        today = date.today()
        task = make_task(frequency="weekly", due=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_next_occurrence_inherits_description(self):
        task = make_task(description="Medication", frequency="daily")
        next_task = task.mark_complete()
        assert next_task.description == "Medication"


# ── Pet task management ────────────────────────────────────────────────────────

class TestPetTaskManagement:
    def test_add_task_increases_count(self):
        _, pet = make_owner_with_pet()
        initial = len(pet.tasks)
        pet.add_task(make_task())
        assert len(pet.tasks) == initial + 1

    def test_add_task_tags_pet_name(self):
        _, pet = make_owner_with_pet("Mochi")
        task = make_task()
        pet.add_task(task)
        assert task.pet_name == "Mochi"

    def test_get_tasks_returns_all(self):
        _, pet = make_owner_with_pet()
        pet.add_task(make_task("Walk"))
        pet.add_task(make_task("Feed"))
        assert len(pet.get_tasks()) == 2


# ── Sorting correctness ────────────────────────────────────────────────────────

class TestSorting:
    def test_sort_by_time_chronological(self):
        owner, pet = make_owner_with_pet()
        pet.add_task(make_task("C", "14:00"))
        pet.add_task(make_task("A", "08:00"))
        pet.add_task(make_task("B", "11:30"))
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time(owner.get_all_tasks())
        times = [t.scheduled_time for t in sorted_tasks]
        assert times == ["08:00", "11:30", "14:00"]

    def test_already_sorted_unchanged(self):
        owner, pet = make_owner_with_pet()
        pet.add_task(make_task("A", "07:00"))
        pet.add_task(make_task("B", "12:00"))
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time(owner.get_all_tasks())
        assert sorted_tasks[0].scheduled_time == "07:00"


# ── Conflict detection ─────────────────────────────────────────────────────────

class TestConflictDetection:
    def test_no_conflicts_returns_empty(self):
        owner, pet = make_owner_with_pet()
        pet.add_task(make_task("Walk", "08:00"))
        pet.add_task(make_task("Feed", "09:00"))
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts(owner.get_all_tasks()) == []

    def test_same_time_yields_one_warning(self):
        owner, pet = make_owner_with_pet()
        pet.add_task(make_task("Walk", "08:00"))
        pet.add_task(make_task("Feed", "08:00"))
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
        assert len(conflicts) == 1
        assert "08:00" in conflicts[0]

    def test_conflict_message_names_both_tasks(self):
        owner, pet = make_owner_with_pet()
        pet.add_task(make_task("Walk", "10:00"))
        pet.add_task(make_task("Medication", "10:00"))
        scheduler = Scheduler(owner)
        msg = scheduler.detect_conflicts(owner.get_all_tasks())[0]
        assert "Walk" in msg and "Medication" in msg

    def test_three_tasks_two_conflicts(self):
        owner, pet = make_owner_with_pet()
        pet.add_task(make_task("A", "08:00"))
        pet.add_task(make_task("B", "08:00"))
        pet.add_task(make_task("C", "08:00"))
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts(owner.get_all_tasks())
        assert len(conflicts) == 2


# ── Recurring task rescheduling ────────────────────────────────────────────────

class TestRecurringTasks:
    def test_complete_daily_adds_next_to_pet(self):
        owner, pet = make_owner_with_pet()
        task = Task("Feed", "08:00", 10, "high", "daily", due_date=date.today())
        pet.add_task(task)
        scheduler = Scheduler(owner)
        initial = len(pet.tasks)
        scheduler.mark_task_complete(task)
        assert len(pet.tasks) == initial + 1

    def test_next_daily_due_tomorrow(self):
        owner, pet = make_owner_with_pet()
        task = Task("Walk", "07:00", 30, "high", "daily", due_date=date.today())
        pet.add_task(task)
        scheduler = Scheduler(owner)
        scheduler.mark_task_complete(task)
        assert pet.tasks[-1].due_date == date.today() + timedelta(days=1)

    def test_complete_once_does_not_add_task(self):
        owner, pet = make_owner_with_pet()
        task = Task("Vet visit", "10:00", 60, "high", "once", due_date=date.today())
        pet.add_task(task)
        scheduler = Scheduler(owner)
        initial = len(pet.tasks)
        scheduler.mark_task_complete(task)
        assert len(pet.tasks) == initial


# ── Filtering ──────────────────────────────────────────────────────────────────

class TestFiltering:
    def test_filter_by_pet_name(self):
        owner = Owner("Jordan")
        mochi = Pet("Mochi", "cat", date(2020, 1, 1))
        buddy = Pet("Buddy", "dog", date(2019, 1, 1))
        mochi.add_task(make_task("Feed Mochi", "07:00"))
        buddy.add_task(make_task("Walk Buddy", "08:00"))
        owner.add_pet(mochi)
        owner.add_pet(buddy)
        scheduler = Scheduler(owner)
        result = scheduler.filter_tasks(owner.get_all_tasks(), pet_name="Mochi")
        assert all(t.pet_name == "Mochi" for t in result)
        assert len(result) == 1

    def test_filter_incomplete_only(self):
        owner, pet = make_owner_with_pet()
        t1 = make_task("A", "08:00")
        t2 = make_task("B", "09:00")
        t1.is_complete = True
        pet.add_task(t1)
        pet.add_task(t2)
        scheduler = Scheduler(owner)
        result = scheduler.filter_tasks(owner.get_all_tasks(), completed=False)
        assert len(result) == 1
        assert result[0].description == "B"


# ── Edge cases ─────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_owner_with_no_pets(self):
        owner = Owner("Empty")
        scheduler = Scheduler(owner)
        assert scheduler.get_todays_tasks() == []
        assert scheduler.detect_conflicts([]) == []

    def test_pet_with_no_tasks(self):
        owner, _ = make_owner_with_pet()
        scheduler = Scheduler(owner)
        assert scheduler.get_todays_tasks() == []

    def test_generate_schedule_empty(self):
        owner = Owner("Empty")
        scheduler = Scheduler(owner)
        schedule = scheduler.generate_schedule()
        assert schedule["tasks"] == []
        assert schedule["conflicts"] == []
        assert schedule["reasoning"] == []
