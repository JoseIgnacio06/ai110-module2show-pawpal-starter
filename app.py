import streamlit as st
from pawpal_system import Pet, Owner, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# ------------------------------------------------------------------
# Steps 1 & 2 — Initialize Owner once, grab a local reference
# ------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(
        name="",
        daily_available_time=60,
        preferences=[],
        energy_level="medium",
        time_windows=["morning"],
    )

owner = st.session_state["owner"]

# ------------------------------------------------------------------
# Step 3 — Owner constraints form
# ------------------------------------------------------------------
st.subheader("Owner")

col1, col2 = st.columns(2)
with col1:
    new_name = st.text_input("Owner name", value=owner.name)
    if new_name != owner.name:
        owner.name = new_name

    new_time = st.number_input(
        "Daily available time (min)", min_value=5, max_value=480,
        value=owner.daily_available_time, step=5,
    )
    if new_time != owner.daily_available_time:
        owner.daily_available_time = int(new_time)

with col2:
    new_energy = st.selectbox(
        "Energy level", ["low", "medium", "high"],
        index=["low", "medium", "high"].index(owner.energy_level),
    )
    if new_energy != owner.energy_level:
        owner.energy_level = new_energy

    new_windows = st.multiselect(
        "Available time windows",
        ["morning", "afternoon", "evening"],
        default=owner.time_windows if owner.time_windows else ["morning"],
    )
    if new_windows != owner.time_windows:
        owner.time_windows = new_windows

st.divider()

# ------------------------------------------------------------------
# Step 4 — Add Pets and Tasks (stored inside the Owner)
# ------------------------------------------------------------------
st.subheader("Pets & Tasks")

with st.expander("Add a pet", expanded=not bool(owner.pets)):
    pet_name = st.text_input("Pet name", value="Mochi")
    species   = st.selectbox("Species", ["dog", "cat", "other"])
    notes     = st.text_input("Notes (optional)", value="")
    if st.button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species, notes=notes))
        st.success(f"{pet_name} added!")

if owner.pets:
    pet_names   = [p.name for p in owner.pets]
    target_name = st.selectbox("Add a task to which pet?", pet_names)
    target_pet  = next(p for p in owner.pets if p.name == target_name)

    with st.expander(f"Add a task to {target_name}", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        col4, col5 = st.columns(2)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
        with col5:
            time_constraint = st.selectbox(
                "Time window", ["any", "morning", "afternoon", "evening"]
            )

        if st.button("Add task"):
            task = Task(
                name=task_title,
                duration=int(duration),
                priority=priority,
                frequency=frequency,
                time_constraints=time_constraint,
                pet=target_pet,
            )
            target_pet.add_task(task)
            st.success(f"'{task_title}' added to {target_name}!")

    st.markdown("#### Current pets and tasks")
    for pet in owner.pets:
        tasks = pet.get_tasks()
        header = f"**{pet.name}** ({pet.species})"
        header += f" — {len(tasks)} task(s)" if tasks else " — no tasks yet"
        st.markdown(header)
        for task in tasks:
            status = "✅" if task.completed else "⬜"
            st.caption(f"  {status} {task.describe()}")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ------------------------------------------------------------------
# Step 5 — Generate Schedule using the real Scheduler
# ------------------------------------------------------------------
st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet with a task before generating a schedule.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.create_daily_plan()

        if plan["tasks"]:
            st.success(
                f"Scheduled **{len(plan['tasks'])} task(s)** "
                f"— {plan['total_duration']} / {owner.daily_available_time} min used"
            )
            for task in plan["tasks"]:
                st.markdown(f"- {task.describe()}")
        else:
            st.info("No tasks qualify for today given current constraints.")

        with st.expander("Scheduler decisions"):
            for line in plan["explanations"]:
                st.text(line)
