"""PawPal+ Streamlit UI — connected to pawpal_system.py backend."""
import streamlit as st
from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

DATA_FILE = "data.json"

def autosave() -> None:
    """Write current owner state to data.json after every mutation."""
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)

def create_demo_owner() -> Owner:
    """Return a pre-populated Owner (Matthew) with Mr. Jasper for first-run demos."""
    owner = Owner("Matthew")
    today = date.today()
    jasper = Pet("Mr. Jasper", "cat", date(2021, 6, 10))
    jasper.add_task(Task("Morning feeding",    "07:30", 10, "high",   "daily",  due_date=today))
    jasper.add_task(Task("Morning playtime",   "09:00", 20, "medium", "daily",  due_date=today))
    jasper.add_task(Task("Midday feeding",     "12:30", 10, "high",   "daily",  due_date=today))
    jasper.add_task(Task("Afternoon nap check","15:00",  5, "low",    "daily",  due_date=today))
    jasper.add_task(Task("Evening feeding",    "18:00", 10, "high",   "daily",  due_date=today))
    jasper.add_task(Task("Medication",         "20:00",  5, "high",   "daily",  due_date=today))
    jasper.add_task(Task("Weekly grooming",    "11:00", 30, "low",    "weekly", due_date=today))
    jasper.add_task(Task("Vet checkup",        "10:00", 60, "medium", "once",   due_date=today + timedelta(days=30)))
    owner.add_pet(jasper)
    return owner

# ── Session state bootstrap ───────────────────────────────────────────────────
# Try to restore from data.json first; fall back to demo data on fresh install.
if "owner" not in st.session_state:
    loaded = Owner.load_from_json(DATA_FILE)
    if loaded:
        st.session_state.owner = loaded
    else:
        st.session_state.owner = create_demo_owner()
        autosave()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners.")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Owner Setup")

    with st.form("owner_form"):
        default_name = st.session_state.owner.name if st.session_state.owner else "Matthew"
        owner_name = st.text_input("Your name", value=default_name)
        if st.form_submit_button("Create / Reset Owner"):
            st.session_state.owner = Owner(owner_name)
            autosave()
            st.success(f"Owner '{owner_name}' ready!")

    if st.session_state.owner:
        st.divider()
        st.subheader("Block a time slot")
        with st.form("block_form"):
            blocked = st.text_input("Time (HH:MM)", placeholder="e.g. 09:00")
            if st.form_submit_button("Block time"):
                if blocked:
                    st.session_state.owner.block_time(blocked)
                    autosave()
                    st.success(f"{blocked} blocked.")
                else:
                    st.warning("Enter a time first.")

        if st.session_state.owner.blocked_times:
            st.caption("Blocked: " + ", ".join(st.session_state.owner.blocked_times))

# ── Guard ─────────────────────────────────────────────────────────────────────
if not st.session_state.owner:
    st.info("Use the sidebar to create an owner first.")
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
    with st.form("add_pet_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_pet_name = st.text_input("Pet name")
        with col2:
            new_species = st.selectbox("Species", ["cat", "dog", "rabbit", "other"])
        with col3:
            new_dob = st.date_input("Date of birth", value=date(2020, 1, 1))
        if st.form_submit_button("Add Pet"):
            existing = [p.name for p in owner.pets]
            if not new_pet_name:
                st.warning("Please enter a pet name.")
            elif new_pet_name in existing:
                st.warning(f"'{new_pet_name}' is already registered.")
            else:
                owner.add_pet(Pet(new_pet_name, new_species, new_dob))
                autosave()
                st.success(f"{new_pet_name} added!")

    # ── Existing pets ─────────────────────────────────────────────────────────
    if not owner.pets:
        st.info("No pets yet. Add one above.")
    else:
        st.divider()

        for pet_idx, pet in enumerate(owner.pets):
            header_col, del_col = st.columns([5, 1])
            with header_col:
                st.subheader(f"🐾 {pet.name}  ({pet.species})")
            with del_col:
                if st.button("Delete pet", key=f"del_pet_{pet_idx}", type="secondary"):
                    owner.pets.pop(pet_idx)
                    autosave()
                    st.rerun()

            # ── Add task to this pet ───────────────────────────────────────────
            with st.expander(f"Add task for {pet.name}"):
                with st.form(f"add_task_{pet.name}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        task_desc = st.text_input("Description", placeholder="e.g. Morning walk")
                        task_time = st.text_input("Time (HH:MM)", placeholder="08:00")
                        task_due  = st.date_input("Due date", value=date.today())
                    with col_b:
                        task_dur  = st.number_input("Duration (min)", min_value=1, max_value=480, value=20)
                        task_pri  = st.selectbox("Priority", ["high", "medium", "low"])
                        task_freq = st.selectbox("Frequency", ["daily", "once", "weekly"])
                    if st.form_submit_button("Add Task"):
                        if not task_desc or not task_time:
                            st.warning("Fill in description and time.")
                        else:
                            pet.add_task(Task(
                                description=task_desc,
                                scheduled_time=task_time,
                                duration_minutes=int(task_dur),
                                priority=task_pri,
                                frequency=task_freq,
                                due_date=task_due,
                            ))
                            autosave()
                            st.success(f"Task added to {pet.name}.")

            # ── Task list with delete buttons ──────────────────────────────────
            if not pet.tasks:
                st.caption("No tasks yet.")
            else:
                hdr = st.columns([1, 3, 1, 1, 1, 0.6])
                for col, label in zip(hdr, ["Time", "Task", "Priority", "Duration", "Freq", ""]):
                    col.markdown(f"**{label}**")
                st.divider()
                for task_idx, task in enumerate(pet.tasks):
                    row = st.columns([1, 3, 1, 1, 1, 0.6])
                    row[0].write(task.scheduled_time)
                    row[1].write(task.description)
                    row[2].write(task.priority.upper())
                    row[3].write(f"{task.duration_minutes} min")
                    row[4].write(task.frequency)
                    if row[5].button("🗑", key=f"del_task_{pet.name}_{task_idx}"):
                        pet.tasks.pop(task_idx)
                        autosave()
                        st.rerun()

            st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# Tab 2: Today's Schedule
# ═════════════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.subheader(f"Schedule for {date.today().strftime('%A, %B %d %Y')}")
    st.caption(f"Owner: {owner.name}")

    if not owner.pets:
        st.info("Add pets and tasks in the Pets & Tasks tab first.")
    else:
        scheduler = Scheduler(owner)
        schedule  = scheduler.generate_schedule()

        # ── Conflicts ─────────────────────────────────────────────────────────
        if schedule["conflicts"]:
            for conflict in schedule["conflicts"]:
                st.warning(f"⚠ {conflict}")
        else:
            st.success("No scheduling conflicts.")

        # ── Task table ────────────────────────────────────────────────────────
        if not schedule["tasks"]:
            st.info("No tasks due today.")
        else:
            st.subheader("Today's Tasks")
            hdr = st.columns([1, 2, 3, 1, 1, 0.6])
            for col, label in zip(hdr, ["Time", "Pet", "Task", "Priority", "Duration", "Done"]):
                col.markdown(f"**{label}**")
            st.divider()
            for task in schedule["tasks"]:
                row = st.columns([1, 2, 3, 1, 1, 0.6])
                row[0].write(task.scheduled_time)
                row[1].write(task.pet_name)
                row[2].write(task.description)
                row[3].write(task.priority.upper())
                row[4].write(f"{task.duration_minutes} min")
                row[5].write("✓" if task.is_complete else "○")

            # ── Reasoning ─────────────────────────────────────────────────────
            with st.expander("Plan reasoning"):
                for line in schedule["reasoning"]:
                    st.markdown(f"- {line}")

        # ── Mark task complete ─────────────────────────────────────────────────
        all_tasks  = owner.get_all_tasks()
        incomplete = [t for t in all_tasks if not t.is_complete]
        if incomplete:
            st.divider()
            st.subheader("Mark a Task Complete")
            with st.form("complete_form"):
                task_labels  = [f"{t.pet_name} — {t.description} @ {t.scheduled_time}" for t in incomplete]
                chosen_label = st.selectbox("Select task", task_labels)
                if st.form_submit_button("Mark Complete"):
                    idx = task_labels.index(chosen_label)
                    scheduler.mark_task_complete(incomplete[idx])
                    autosave()
                    msg = f"'{incomplete[idx].description}' marked complete."
                    if incomplete[idx].frequency != "once":
                        msg += " Next occurrence scheduled."
                    st.success(msg)
                    st.rerun()
