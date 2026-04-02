# PawPal+ Project Reflection

## 1. System Design

**Three core actions a user should be able to perform:**

1. **Add a pet** — the owner should be able to register a pet (name, species, date of birth) so the system knows whose tasks it is managing.
2. **Schedule a task** — the owner should be able to assign a care activity (e.g., morning walk, medication, feeding) to a specific pet with a time, duration, priority, and recurrence frequency.
3. **View today's schedule** — the owner should be able to see all tasks for the current day sorted by time, with conflict warnings and reasoning about why each task was placed where it was.

---

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design centered on four classes with clearly separated responsibilities:

- **Owner** — stores the owner's name and a list of their pets. Also holds any blocked time slots (times the owner is unavailable), which the Scheduler uses as a constraint when building the daily plan.
- **Pet** — stores the pet's name, species, and date of birth, and owns a list of Task objects assigned to that pet.
- **Task** — a dataclass representing a single care activity (e.g., walk, feeding, medication). Attributes include description, scheduled time, duration in minutes, priority level (low/medium/high), frequency (once/daily/weekly), and a completion status flag.
- **Scheduler** — the core "brain." It takes an Owner, collects all tasks across all pets, filters by date/status, sorts by priority and time, detects conflicts (two tasks scheduled at the same time), handles recurring task rescheduling, and produces a readable daily plan with reasoning.

The key relationship is: Owner → has many Pets → each Pet has many Tasks → Scheduler reads all Tasks through the Owner to build the plan.

**b. Design changes**

Yes — two notable changes happened during implementation.

1. **`Task` gained a `due_date` field.** The initial sketch treated tasks as purely time-of-day items ("08:00 walk"). Once recurring tasks were added it became clear I needed a calendar date as well, otherwise there was no way to distinguish today's walk from tomorrow's auto-generated one. Adding `due_date` (defaulting to `date.today()`) solved this cleanly without breaking the rest of the design.

2. **`mark_complete()` was moved onto `Task` (not `Scheduler`).** Early on I put the recurrence logic in `Scheduler.mark_task_complete()`. Copilot pointed out that a `Task` already knows its own frequency and the `timedelta` math is self-contained, so having `Task.mark_complete()` return the next occurrence is more cohesive. The `Scheduler` method became a thin wrapper that just calls `task.mark_complete()` and re-attaches the result to the right `Pet`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: **time** (tasks are sorted by `scheduled_time` in HH:MM format), **priority** (high/medium/low, surfaced in the reasoning output), and **owner availability** (blocked time slots set by the owner on the sidebar). I decided time was the primary sort key because a daily schedule is fundamentally chronological — the owner needs to know what to do *next*, not just what matters most. Priority is included in the reasoning text so the owner can choose to re-order manually if needed. Blocked slots act as a soft warning rather than hard removal, which keeps the system flexible.

**b. Tradeoffs**

The conflict detector only flags tasks that share the **exact same HH:MM start time** — it does not check whether a 60-minute task overlaps the start of the next task. For example, a task at 08:00 that lasts 90 minutes would not conflict with one at 09:00 even though they overlap in real life. This is a deliberate simplification: implementing duration-aware overlap detection would require converting times to minutes-since-midnight and doing interval arithmetic, adding significant complexity for a feature most users will notice only in edge cases. For a basic daily pet-care schedule, exact-time collision detection catches the most common mistake (accidentally double-booking the same slot) with minimal code.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase, but in different modes:

- **Design brainstorming (Phase 1):** Asked Copilot Chat to generate a Mermaid.js class diagram from a plain-English description of the four classes. This was the fastest way to see whether the relationships made sense visually before writing any code.
- **Scaffolding (Phase 1–2):** Used Agent Mode to generate the class skeleton and initial docstrings from the UML, which saved time on boilerplate. The instruction "use Python dataclasses for Task and Pet" kept the output clean.
- **Algorithmic help (Phase 4):** Inline Chat on `sort_by_time()` to learn the `sorted(..., key=lambda t: t.scheduled_time)` pattern. Also asked Chat to explain `timedelta` for recurring task rescheduling.
- **Test generation (Phase 5):** Asked Chat "what are the most important edge cases for a scheduler with sorting and recurring tasks?" to get a test plan, then used the Generate Tests smart action to scaffold the test file.

The most effective prompt style was **specific and scoped**: asking about one method at a time with the file attached (`#file:pawpal_system.py`) rather than asking broad questions like "how do I build a scheduler?".

**b. Judgment and verification**

When I asked Copilot to implement conflict detection, it initially suggested comparing `task.scheduled_time` strings using `<=` and `>=` comparisons to detect *overlapping duration windows*. While technically correct, the code used `datetime.strptime` on every comparison, added 15+ lines, and was hard to follow at a glance. I rejected this in favour of the simpler exact-match dictionary approach. My reasoning: duration-overlap detection is a future enhancement, not a minimum requirement, and the simpler version is easier to test and explain. I verified the simpler version manually by adding two tasks at the same time in `main.py` and confirming the warning printed correctly.

---

## 4. Testing and Verification

**a. What you tested**

The 22-test suite (`tests/test_pawpal.py`) covers:

- **Task completion** — `mark_complete()` sets `is_complete = True` and returns `None` for one-time tasks
- **Recurring rescheduling** — daily tasks create a next occurrence for `today + 1 day`; weekly for `today + 7 days`; the next task starts incomplete
- **Pet task management** — `add_task()` increments the pet's task count and tags the task with the pet's name
- **Sorting correctness** — tasks added out of order come back in chronological `HH:MM` order
- **Conflict detection** — same-time tasks produce a warning naming both; three tasks at the same slot produce two warnings; different slots produce none
- **Filtering** — filter by pet name returns only that pet's tasks; filter by `completed=False` excludes finished tasks
- **Edge cases** — owner with no pets, pet with no tasks, and `generate_schedule()` on an empty owner all return gracefully without errors

These tests matter because the scheduler's value is entirely in its correctness: a pet owner relying on it to give medications on time can't afford silent failures in sorting or rescheduling.

**b. Confidence**

**★★★★☆** — all 22 tests pass and the CLI demo runs cleanly. The main gap is duration-aware overlap detection: two tasks that don't share an exact start time but overlap in duration would not be flagged. I'd add that next, along with a test for tasks that span midnight (e.g., a late-night feeding followed by an early-morning one).

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was the most satisfying part. Having `main.py` as a testbed before touching the Streamlit UI meant I could confirm every algorithm — sorting, conflict detection, recurring rescheduling — worked in isolation. When I then wired up `app.py`, there were zero surprises from the backend. The separation also made the tests straightforward to write because the logic had no UI dependencies at all.

**b. What you would improve**

I'd redesign the conflict detector to be duration-aware. Right now it only catches exact start-time collisions, which misses the case where an 08:00/90-minute task bleeds into a 09:00 task. The fix would be converting each task to a `(start_minutes, end_minutes)` interval and checking for intersection. I'd also add data persistence (save/load to JSON) so the schedule isn't wiped every time the Streamlit app restarts.

**c. Key takeaway**

AI is most useful when you already know what you want. Vague prompts ("build me a scheduler") produced generic, over-engineered output. Scoped prompts tied to a specific method and file (`#file:pawpal_system.py — how should sort_by_time work for HH:MM strings?`) produced clean, immediately usable suggestions. Being the "lead architect" meant my job was not to delegate thinking to the AI, but to decompose the problem clearly enough that AI could help with the implementation details without creating unnecessary complexity.
