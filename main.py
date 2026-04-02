"""CLI demo script — verifies PawPal+ backend logic in the terminal."""
from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler


def print_divider(title: str = "") -> None:
    width = 60
    if title:
        print(f"\n{'─' * 4} {title} {'─' * (width - len(title) - 6)}")
    else:
        print("─" * width)


def main() -> None:
    # ── Owner setup ──────────────────────────────────────────────────
    owner = Owner("Jordan")
    owner.block_time("09:00")   # Jordan is busy at 9 AM

    # ── Pets ─────────────────────────────────────────────────────────
    mochi = Pet("Mochi", "cat", date(2020, 3, 15))
    buddy = Pet("Buddy", "dog", date(2019, 7, 4))

    # ── Tasks for Mochi ──────────────────────────────────────────────
    mochi.add_task(Task("Breakfast feeding", "07:00", 10, "high",   "daily"))
    mochi.add_task(Task("Medication",        "09:00",  5, "high",   "daily"))
    mochi.add_task(Task("Playtime",          "14:00", 20, "medium", "daily"))

    # ── Tasks for Buddy ──────────────────────────────────────────────
    buddy.add_task(Task("Morning walk",    "08:00", 30, "high",   "daily"))
    buddy.add_task(Task("Afternoon walk",  "17:00", 30, "high",   "daily"))
    buddy.add_task(Task("Dinner feeding",  "18:00", 10, "high",   "daily"))
    buddy.add_task(Task("Weekly grooming", "10:00", 45, "low",    "weekly"))

    owner.add_pet(mochi)
    owner.add_pet(buddy)

    scheduler = Scheduler(owner)

    # ── Today's schedule ─────────────────────────────────────────────
    schedule = scheduler.generate_schedule()

    print("=" * 60)
    print(f"  TODAY'S SCHEDULE  —  {date.today().strftime('%A, %B %d %Y')}")
    print(f"  Owner: {owner.name}")
    print("=" * 60)

    print_divider("Plan & Reasoning")
    for line in schedule["reasoning"]:
        print(f"  {line}")

    if schedule["conflicts"]:
        print_divider("Conflicts")
        for conflict in schedule["conflicts"]:
            print(f"  ⚠  {conflict}")

    print_divider("Full Task Table")
    header = f"  {'Time':6}  {'Pet':8}  {'Task':26}  {'Pri':6}  {'Min':>4}  {'Done'}"
    print(header)
    print("  " + "·" * 56)
    for task in schedule["tasks"]:
        done = "✓" if task.is_complete else "○"
        print(
            f"  {task.scheduled_time:6}  {task.pet_name:8}  "
            f"{task.description:26}  {task.priority.upper():6}  "
            f"{task.duration_minutes:>4}  {done}"
        )

    # ── Demo: conflict detection ──────────────────────────────────────
    print_divider("Conflict Detection Demo")
    buddy.add_task(Task("Vet appointment", "08:00", 60, "high", "once"))
    all_tasks = scheduler.sort_by_time(owner.get_all_tasks())
    conflicts = scheduler.detect_conflicts(all_tasks)
    if conflicts:
        for c in conflicts:
            print(f"  ⚠  {c}")
    else:
        print("  No conflicts found.")

    # ── Demo: filtering ───────────────────────────────────────────────
    print_divider("Filter: Mochi's tasks only")
    mochi_tasks = scheduler.filter_tasks(owner.get_all_tasks(), pet_name="Mochi")
    for t in mochi_tasks:
        print(f"  {t.scheduled_time}  {t.description}")

    # ── Demo: recurring task rescheduling ────────────────────────────
    print_divider("Recurring Task Demo")
    feed = mochi.tasks[0]
    print(f"  Completing '{feed.description}' (due {feed.due_date})")
    scheduler.mark_task_complete(feed)
    next_feed = mochi.tasks[-1]
    print(f"  Next occurrence auto-created for {next_feed.due_date}")

    print("\n" + "=" * 60)
    print("  Demo complete. All systems nominal.")
    print("=" * 60)


if __name__ == "__main__":
    main()
