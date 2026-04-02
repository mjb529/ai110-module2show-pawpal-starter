"""PawPal+ Streamlit UI — connected to pawpal_system.py backend."""
import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ── Session state bootstrap ───────────────────────────────────────────────────
# Streamlit reruns the script on every interaction; we persist the Owner object
# in st.session_state so data survives between button clicks.
if "owner" not in st.session_state:
    st.session_state.owner = None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners.")

# ── Sidebar: owner setup ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("Owner Setup")
    owner_name = st.text_input("Your name", value="Jordan", key="owner_name_input")

    if st.button("Create / Reset Owner"):
        st.session_state.owner = Owner(owner_name)
        st.success(f"Owner '{owner_name}' ready!")

    if st.session_state.owner:
        st.divider()
        st.subheader("Block a time slot")
        blocked = st.text_input(
            "Block time (HH:MM)", placeholder="e.g. 09:00", key="block_input"
        )
        if st.button("Block time"):
            if blocked:
                st.session_state.owner.block_time(blocked)
                st.success(f"{blocked} blocked.")

        if st.session_state.owner.blocked_times:
            st.caption("Blocked: " + ", ".join(st.session_state.owner.blocked_times))

# ── Guard: require owner ──────────────────────────────────────────────────────
if not st.session_state.owner:
    st.info('Use the sidebar to create an owner first, then come back here.')
    st.stop()

owner: Owner = st.session_state.owner

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_pets, tab_schedule = st.tabs(["🐶 Pets & Tasks", "📅 Today's Schedule"])

# ═════════════════════════════════════════════════════════════════════════════
# Tab 1: Pets & Tasks
# ═════════════════════════════════════════════════════════════════════════════
with tab_pets:

    # ── Add a pet ─────────────────────────────────────────────────────────────
    st.subheader("Add a Pet")
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", key="pet_name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"], key="species")
    with col3:
        dob = st.date_input("Date of birth", value=date(2020, 1, 1), key="dob")

    if st.button("Add Pet"):
        existing = [p.name for p in owner.pets]
        if not pet_name:
            st.warning("Please enter a pet name.")
        elif pet_name in existing:
            st.warning(f"'{pet_name}' is already registered.")
        else:
            owner.add_pet(Pet(pet_name, species, dob))
            st.success(f"{pet_name} added!")

    # ── Pet list & task assignment ─────────────────────────────────────────────
    if not owner.pets:
        st.info("No pets yet. Add one above.")
    else:
        st.divider()
        st.subheader("Schedule a Task")

        pet_options = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Choose a pet", pet_options, key="task_pet")

        col_a, col_b = st.columns(2)
        with col_a:
            task_desc = st.text_input("Task description", placeholder="e.g. Morning walk")
            task_time = st.text_input("Scheduled time (HH:MM)", placeholder="08:00")
            task_due = st.date_input("Due date", value=date.today(), key="task_due")
        with col_b:
            task_dur = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=20)
            task_pri = st.selectbox("Priority", ["high", "medium", "low"])
            task_freq = st.selectbox("Frequency", ["once", "daily", "weekly"])

        if st.button("Add Task"):
            if not task_desc or not task_time:
                st.warning("Please fill in the task description and time.")
            else:
                pet_obj = next(p for p in owner.pets if p.name == selected_pet_name)
                new_task = Task(
                    description=task_desc,
                    scheduled_time=task_time,
                    duration_minutes=int(task_dur),
                    priority=task_pri,
                    frequency=task_freq,
                    due_date=task_due,
                )
                pet_obj.add_task(new_task)
                st.success(f"Task '{task_desc}' added to {selected_pet_name}.")

        # ── Per-pet task tables ────────────────────────────────────────────────
        st.divider()
        st.subheader("Current Tasks")
        for pet in owner.pets:
            with st.expander(f"🐾 {pet.name} ({pet.species})", expanded=True):
                if not pet.tasks:
                    st.caption("No tasks yet.")
                else:
                    rows = [
                        {
                            "Time": t.scheduled_time,
                            "Task": t.description,
                            "Priority": t.priority.upper(),
                            "Duration": f"{t.duration_minutes} min",
                            "Freq": t.frequency,
                            "Due": str(t.due_date),
                            "Done": "✓" if t.is_complete else "○",
                        }
                        for t in pet.tasks
                    ]
                    st.table(rows)

# ═════════════════════════════════════════════════════════════════════════════
# Tab 2: Today's Schedule
# ═════════════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader(f"Schedule for {date.today().strftime('%A, %B %d %Y')}")

    if not owner.pets:
        st.info("Add pets and tasks in the first tab, then generate a schedule.")
    else:
        scheduler = Scheduler(owner)

        if st.button("Generate Schedule"):
            schedule = scheduler.generate_schedule()

            # ── Conflicts ─────────────────────────────────────────────────────
            if schedule["conflicts"]:
                for conflict in schedule["conflicts"]:
                    st.warning(f"⚠ {conflict}")
            else:
                st.success("No conflicts detected.")

            # ── Reasoning ─────────────────────────────────────────────────────
            st.subheader("Plan & Reasoning")
            if schedule["reasoning"]:
                for line in schedule["reasoning"]:
                    st.markdown(f"- {line}")
            else:
                st.info("No tasks due today.")

            # ── Task table ────────────────────────────────────────────────────
            if schedule["tasks"]:
                st.subheader("Today's Tasks (sorted by time)")
                rows = [
                    {
                        "Time": t.scheduled_time,
                        "Pet": t.pet_name,
                        "Task": t.description,
                        "Priority": t.priority.upper(),
                        "Duration": f"{t.duration_minutes} min",
                        "Done": "✓" if t.is_complete else "○",
                    }
                    for t in schedule["tasks"]
                ]
                st.table(rows)

        # ── Mark task complete ─────────────────────────────────────────────────
        all_tasks = owner.get_all_tasks()
        incomplete = [t for t in all_tasks if not t.is_complete]
        if incomplete:
            st.divider()
            st.subheader("Mark a Task Complete")
            task_labels = [
                f"{t.pet_name} — {t.description} @ {t.scheduled_time}" for t in incomplete
            ]
            chosen_label = st.selectbox("Select task", task_labels, key="complete_select")
            if st.button("Mark Complete"):
                idx = task_labels.index(chosen_label)
                scheduler.mark_task_complete(incomplete[idx])
                st.success(
                    f"'{incomplete[idx].description}' marked complete."
                    + (
                        " Next occurrence scheduled."
                        if incomplete[idx].frequency != "once"
                        else ""
                    )
                )
                st.rerun()
