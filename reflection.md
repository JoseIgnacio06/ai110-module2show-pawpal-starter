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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
