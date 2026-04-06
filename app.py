import streamlit as st
from pawpal_system import Pet, Owner, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# ------------------------------------------------------------------
# Session state — create Owner once, reuse across reruns
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
# Owner constraints
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
# Pets & Tasks
# ------------------------------------------------------------------
st.subheader("Pets & Tasks")

with st.expander("Add a pet", expanded=not bool(owner.pets)):
    pet_name = st.text_input("Pet name", value="Mochi")
    species  = st.selectbox("Species", ["dog", "cat", "other"])
    notes    = st.text_input("Notes (optional)", value="")
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

        col4, col5, col6 = st.columns(3)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
        with col5:
            time_constraint = st.selectbox(
                "Time window", ["any", "morning", "afternoon", "evening"]
            )
        with col6:
            scheduled_time = st.text_input(
                "Scheduled time (HH:MM)", value="", placeholder="e.g. 08:00"
            )

        if st.button("Add task"):
            target_pet.add_task(Task(
                name=task_title,
                duration=int(duration),
                priority=priority,
                frequency=frequency,
                time_constraints=time_constraint,
                pet=target_pet,
                scheduled_time=scheduled_time.strip() or None,
            ))
            st.success(f"'{task_title}' added to {target_name}!")

    # Current task roster — shown as a table per pet
    st.markdown("#### Current pets and tasks")
    for pet in owner.pets:
        tasks = pet.get_tasks()
        label = f"**{pet.name}** ({pet.species})"
        label += f" — {len(tasks)} task(s)" if tasks else " — no tasks yet"
        st.markdown(label)
        if tasks:
            st.dataframe(
                [
                    {
                        "Task":      t.name,
                        "Priority":  t.priority.upper(),
                        "Duration":  f"{t.duration} min",
                        "Frequency": t.frequency,
                        "Window":    t.time_constraints,
                        "Time":      t.scheduled_time or "—",
                        "Status":    "Done" if t.completed else "Pending",
                    }
                    for t in tasks
                ],
                use_container_width=True,
                hide_index=True,
            )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ------------------------------------------------------------------
# Today's Schedule
# ------------------------------------------------------------------
st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet with a task before generating a schedule.")
    else:
        scheduler  = Scheduler(owner)
        daily_plan = scheduler.create_daily_plan()
        plan       = daily_plan["tasks"]

        # 1. Conflict warnings — shown first so the owner can't miss them
        if daily_plan["conflicts"]:
            for conflict in daily_plan["conflicts"]:
                # Parse out the time slot for a human-readable lead line
                # e.g. "CONFLICT at 08:00 [cross-pet conflict]: 'Walk' (Buddy), 'Feed' (Luna)"
                st.warning(
                    f"**Scheduling conflict detected**\n\n"
                    f"{conflict}\n\n"
                    f"_Two tasks are set for the same time. "
                    f"Consider adjusting one of the scheduled times above._"
                )

        # 2. Budget summary
        if plan:
            budget_pct = int(daily_plan["total_duration"] / owner.daily_available_time * 100)
            st.success(
                f"Scheduled **{len(plan)} task(s)** "
                f"— {daily_plan['total_duration']} / {owner.daily_available_time} min used"
            )
            st.progress(min(budget_pct, 100))
        else:
            st.info("No tasks qualify for today given current constraints.")

        # 3. Sorted task table — sort_by_time() reorders by HH:MM
        if plan:
            sorted_plan = scheduler.sort_by_time(plan)
            st.markdown("#### Tasks in time order")
            st.dataframe(
                [
                    {
                        "Time":      t.scheduled_time or "—",
                        "Task":      t.name,
                        "Pet":       t.pet.name,
                        "Priority":  t.priority.upper(),
                        "Duration":  f"{t.duration} min",
                        "Window":    t.time_constraints,
                    }
                    for t in sorted_plan
                ],
                use_container_width=True,
                hide_index=True,
            )

        # 4. Per-pet filter — show pending tasks for one pet at a time
        if plan and len({t.pet.name for t in plan}) > 1:
            st.markdown("#### Filter by pet")
            filter_pet = st.selectbox(
                "Show pending tasks for:",
                ["All pets"] + list({t.pet.name for t in plan}),
            )
            if filter_pet != "All pets":
                filtered = scheduler.filter_by(plan, pet_name=filter_pet, completed=False)
                if filtered:
                    for t in scheduler.sort_by_time(filtered):
                        st.caption(
                            f"{t.scheduled_time or '—'}  {t.name} "
                            f"[{t.priority}] {t.duration} min"
                        )
                else:
                    st.info(f"No pending tasks for {filter_pet}.")

        # 5. Decisions audit log
        with st.expander("Scheduler decisions"):
            for line in daily_plan["explanations"]:
                if line.startswith("SKIP"):
                    st.caption(f":gray[{line}]")
                elif line.startswith("DROP"):
                    st.caption(f":orange[{line}]")
                elif line.startswith("ADD") or line.startswith("OK"):
                    st.caption(f":green[{line}]")
                else:
                    st.caption(line)
