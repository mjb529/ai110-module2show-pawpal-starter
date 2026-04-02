# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Features

- **Owner management** — register an owner, block personal time slots that the scheduler respects
- **Multi-pet support** — add unlimited pets, each with their own task list
- **Task scheduling** — assign tasks with a description, time (HH:MM), duration, priority (low/medium/high), and frequency (once/daily/weekly)
- **Sorting by time** — the Scheduler automatically sorts all tasks chronologically using `sort_by_time()`
- **Filtering** — filter tasks by pet name or completion status with `filter_tasks()`
- **Conflict warnings** — `detect_conflicts()` scans for two tasks sharing the same time slot and returns a human-readable warning instead of crashing
- **Daily recurrence** — marking a daily or weekly task complete automatically creates the next occurrence (`timedelta`-based)
- **Plan reasoning** — `generate_schedule()` returns a reasoning list explaining why each task was placed, and flags any overlap with blocked owner slots

## Smarter Scheduling

Four algorithms make PawPal+ more intelligent than a plain task list:

| Algorithm | Method | How it works |
|---|---|---|
| Chronological sort | `Scheduler.sort_by_time()` | Uses `sorted()` with a lambda key on the `HH:MM` string — lexicographic order works correctly for zero-padded 24-hour times |
| Status/pet filter | `Scheduler.filter_tasks()` | Single-pass list comprehension; accepts optional `pet_name` and `completed` arguments independently |
| Conflict detection | `Scheduler.detect_conflicts()` | One-pass dictionary scan — O(n) — stores the first task seen at each time slot and emits a warning when a duplicate is found |
| Recurring rescheduling | `Scheduler.mark_task_complete()` + `Task.mark_complete()` | `Task.mark_complete()` returns the next `Task` instance (`due_date + timedelta`); the Scheduler adds it to the correct `Pet` |

## 📸 Demo

<img width="2840" height="1688" alt="image" src="https://github.com/user-attachments/assets/3c4d0735-8d3a-47b0-8d1f-23867834c3d0" />

## Data Persistence

PawPal+ automatically saves all owner, pet, and task data to `data.json` after every change. The next time the Streamlit app starts, it reloads from that file so your schedule is never lost.

**How it works (Agent Mode implementation):**

Serialization uses a custom dictionary conversion on each class rather than a third-party library like marshmallow:

- `Task.to_dict()` / `Task.from_dict()` — converts all fields; `due_date` stored as an ISO-8601 string (`YYYY-MM-DD`)
- `Pet.to_dict()` / `Pet.from_dict()` — nests its task list
- `Owner.to_dict()` / `Owner.from_dict()` — nests its pet list and blocked times
- `Owner.save_to_json(path)` — writes the full object graph to a file
- `Owner.load_from_json(path)` — reads it back, returns `None` safely if the file doesn't exist

In `app.py`, `Owner.load_from_json("data.json")` is called during session state initialisation so data persists across full app restarts. An `autosave()` helper is called after every mutation (add pet, add task, block time, mark complete).

## Running the CLI demo

```bash
python main.py
```

## Testing PawPal+

```bash
python -m pytest
```

The test suite (`tests/test_pawpal.py`) covers:

- **Task completion** — `mark_complete()` sets the flag and returns `None` for one-time tasks
- **Recurring tasks** — daily tasks reschedule to `today + 1 day`; weekly to `today + 7 days`
- **Pet task management** — `add_task()` increments count and tags `pet_name`
- **Sorting correctness** — out-of-order tasks come back in chronological order
- **Conflict detection** — same-time tasks produce warnings naming both tasks
- **Filtering** — tasks can be filtered by pet name or completion status
- **Edge cases** — owners with no pets, pets with no tasks, empty schedule generation

**Confidence level: ★★★★☆** — all 22 tests pass; the main untested edge is overlapping *duration* windows (e.g., a 60-minute task that bleeds into the next slot).
