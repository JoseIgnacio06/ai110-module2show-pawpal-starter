# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
My initial UML design focused on supporting the three core actions a user should be able to perform in the app:

1. Create and manage pet care tasks
2. Set or update daily constraints and preferences
3. Generate and review a daily pet care plan with explanations

- What classes did you include, and what responsibilities did you assign to each?

Owner: represents the busy pet owner using the app. This class stores the owner’s preferences and daily constraints, such as available time, preferred time windows, or special instructions (i.e., “shorter walks today”). The Owner class acts as the central point that ties together pets, tasks, and scheduling needs.

Pet: represents an individual pet. It stores basic information such as name, species, and any special care notes. The Pet class helps the system understand which tasks belong to which pet and whether certain tasks have unique requirements (i.e., medication timing or grooming frequency).

Task: represents a single pet‑care task such as feeding, walking, grooming, or giving medication. Each Task includes attributes like duration, priority, frequency, and optional constraints (i.e., “must be done in the morning”). This class provides the raw material the Scheduler uses to build a daily plan.

Scheduler: the core logic engine of the system. The Scheduler takes the Owner’s constraints and the list of Tasks and selects which tasks fit into the day. It orders them, filters out tasks that don’t fit, and generates explanations for each decision. This class is responsible for producing the final daily plan.

**b. Design changes**

- Did your design change during implementation?
Yes, my design changed during implementation.

- If yes, describe at least one change and why you made it.
One major change was simplifying the Scheduler’s internal structure. At first, I planned to break the scheduling logic into multiple helper classes (i.e., a TaskSelector, a TaskPrioritizer, and an ExplanationGenerator). However, once I began coding, I realized this level of modularity made the system harder to follow and introduced unnecessary complexity. I merged these responsibilities into a single Scheduler class, which made the logic easier to test and reason about.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
Four, all sourced from the Owner and snapshotted into self.constraints at the start of each planning cycle: daily_available_time, time_windows, energy_level, and frequency + last_completed.

- How did you decide which constraints mattered most?
By impact on correctness first, then impact on the owner's day. daily_available_time is the hardest constraint, exceeding it is physically impossible, so it acts as an absolute cutoff. is_due_today comes next because scheduling a task that isn't due yet wastes budget that could go to something real. time_windows and energy_level are softer, they filter out tasks the owner could do but shouldn't be asked to, which protects quality of life rather than calendar correctness.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
The budget is filled greedily by priority, highest priority tasks are added first until the minutes run out. A lower-priority task is dropped even if it would fit perfectly in the remaining time after a high-priority task that barely fits.

Concrete example from the code: if "Vet Check-up" (high, 45 min) and "Evening Brush" (medium, 10 min) both pass filtering, but the budget only has 40 min left, the vet check-up is dropped and the evening brush is also lost because the greedy pass already tried and failed to place the vet check-up, and the dropped log entry ends the consideration of that slot.

- Why is that tradeoff reasonable for this scenario?
A pet care schedule should be predictable and safe to follow without second-guessing. A greedy priority sort guarantees that if anything gets dropped, it's always the least important thing, a pet owner never ends up skipping medication to fit in a grooming session. The alternative (trying every combination to find an optimal packing) would be more efficient on paper but harder to explain: the owner would see medium-priority tasks scheduled ahead of high-priority ones and lose trust in the plan. Transparency and safety take precedence over maximum task density for a daily care tool.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used AI at nearly every phase of the project, but with a different purpose at each stage. During design, I used it to translate the UML diagram into Python class skeletons so I could see the structure before writing any logic. During implementation, I used it to fill in method bodies once I understood what each method needed to do — for example, explaining what `timedelta` was and why it was safer than calendar arithmetic before letting it write `mark_complete`. During the later phases, I used it to suggest improvements (sorting, filtering, conflict detection, recurring tasks) and then reviewed each one before accepting it. I also used it to write the Streamlit UI layer, prompting it in steps rather than asking for the entire app at once.

- What kinds of prompts or questions were most helpful?

The most helpful prompts were specific and gave the AI enough context to make a real decision rather than a generic one. Prompts like "implement `filter_by` so it accepts `pet_name` and `completed` as optional parameters, and returns an empty list rather than crashing when both are None" produced much more useful code than "add a filter method." Asking the AI to review code and list bottlenecks before asking it to fix anything was also valuable — the review step forced me to understand the reasoning before changes were made. Questions about tradeoffs ("what's the downside of a greedy scheduler?") were more useful than questions asking for the best solution, because they gave me options to choose from.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

When the AI first generated the `generate_plan` method, it called `collect_tasks`, then `filter_tasks`, then `prioritize_tasks` as three separate sequential calls. I noticed that `prioritize_tasks` internally called `filter_tasks` again, which meant the audit log could record duplicate SKIP entries if the methods were ever called independently. I pushed back and asked for a design where `filter_tasks` is only called once per planning cycle, with `collect_tasks` owning the reset. The final design reflects that change — `prioritize_tasks` delegates to `filter_tasks` exactly once inside `generate_plan`.

- How did you evaluate or verify what the AI suggested?

I ran the code and read the terminal output carefully. For the scheduler, I checked the decisions log line by line to confirm that each SKIP, ADD, and DROP matched what I expected given the inputs. For the recurring task logic, I printed `next_due`, `last_completed`, and `is_due_today()` immediately after calling `mark_task_complete` to confirm the state was consistent. For conflict detection, I deliberately created tasks at the same time slot and verified the correct label (same-pet vs cross-pet) appeared. I also ran the full pytest suite after every significant change to catch regressions.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

The test suite covers 17 behaviors across five areas: task completion (mark_complete sets the right fields), task addition (add_task increments the pet's count), sorting (sort_by_time returns chronological order, handles None scheduled_time without crashing), recurrence (mark_task_complete creates a non-due instance, next_due is exactly today + frequency days, unknown frequency returns None), conflict detection (cross-pet and same-pet labels, no false positives for untimed tasks, three tasks at one slot produce one warning), and budget packing (plan never exceeds daily_available_time, empty state returns an empty plan without crashing).

- Why were these tests important?

These tests matter because the scheduler's output directly affects what a pet owner does with their day. A bug in `is_due_today` could mean a medication task gets skipped. A bug in recurrence could mean the same task shows up twice or never reappears. A crash on an empty task list would break the app for any new user before they add anything. The tests lock in the correct behavior so that adding new features (like conflict detection or sorting) cannot silently break existing logic.

**b. Confidence**

- How confident are you that your scheduler works correctly?

4 out of 5. All 17 unit tests pass and cover the core scheduling pipeline end to end. The one point of uncertainty is the Streamlit UI layer `st.session_state`, persistence across reruns, the interaction between form inputs and the stored Owner object, and what happens if a user navigates away mid-session are not covered by any automated test. Those paths can only be verified through manual browser testing.

- What edge cases would you test next if you had more time?

The most important untested edge case is calling `generate_plan` twice in a row without changing any data, the second call should produce the same result, but because `collect_tasks` rebuilds the task list from scratch, a bug where `recur` adds tasks to the pet on each call could cause the list to grow. I would also test what happens when `daily_available_time` is set to zero (should return an empty plan immediately), and what happens when all tasks share the same priority (the sort should be stable and preserve insertion order). Finally, I would test the `scheduled_time` validation path, currently the UI accepts any string as a time, so "8am" or "morning" could be passed in and would sort to an unexpected position.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The decision audit log. Every scheduling decision such as: SKIP, OK, ADD, DROP and RECUR are recorded with a plain-English reason and surfaced in the UI. This was not in the original UML and emerged naturally during implementation. It made debugging much faster because I could see exactly why the scheduler dropped a task instead of guessing. It also makes the app genuinely more useful to a pet owner, who can read the log and understand the plan rather than just following it blindly. It is a small addition to the code but has a large impact on trust and transparency.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would redesign how `scheduled_time` is handled. Right now it is a free-text "HH:MM" string with no validation, the UI accepts anything, and if a user types "8am" or leaves it blank after partial input, it silently sorts to an unexpected position. I would replace it with a `datetime.time` field validated on input, with a Streamlit `st.time_input` widget that forces the correct format. I would also redesign the greedy budget packing to do a second pass after the first, if high-priority tasks leave a gap that is too small for the next task but large enough for a lower-priority one, the current algorithm wastes that time. A two-pass approach would fill those gaps without changing the priority ordering that makes the plan trustworthy.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most valuable thing I learned is that AI is most useful when you already have a mental model of what you want. When I gave the AI a vague instruction like "implement the scheduler," the output was technically correct but required significant revision because it made assumptions I had not thought through. When I gave it a specific instruction like "implement `generate_plan` so it calls `collect_tasks` once, then fills the budget greedily by priority, and logs every ADD and DROP decision," the output matched my intent closely and needed much less correction. The quality of AI output is a direct reflection of the clarity of your own thinking, the AI accelerates what you already understand but cannot substitute for understanding itself.
