# PRODUCT.md

Product vision and intended behavior for KAMLA. This document describes what KAMLA is for and how it should eventually behave. It is a product specification, not an implementation plan — nothing in this document is authorization to build anything. See `CLAUDE.md` for engineering rules and architecture boundaries.

KAMLA is an academic decision-making and planning platform for college students.

The core problem is not simply "students need a timetable."

Students constantly make interconnected academic decisions:

- Can I skip this lecture?
- How many lectures can I safely skip?
- Am I falling behind?
- What should I study first?
- Which topics matter most for my exams?
- How should I balance college with a startup, internship, hackathon, personal project, or other goal?
- Did a college announcement change my plan?
- What should I do today given everything else going on?

KAMLA should act as a contextual academic decision-making system rather than a generic productivity/timetable app.

## 1. Attendance intelligence

Students should be able to enter/maintain attendance for their courses.

KAMLA should answer questions such as:

- What is my current attendance?
- How many classes can I safely miss?
- What happens to my attendance if I miss the next 1/2/3 classes?
- How much attendance buffer do I have?
- Will I fall below the required threshold?
- Which courses are currently risky?

Attendance calculations must be deterministic backend logic, not LLM-generated calculations.

KAMLA should not moralize about attendance.

If a student explicitly chooses to accept attendance risk in exchange for another goal, the planning system should treat that as a user constraint/preference subject to institutional rules.

## 2. Academic state and decision support

KAMLA should help students answer:

- Am I on track?
- What am I falling behind on?
- What should I prioritize?
- What can safely be postponed?
- What is the highest-risk academic area right now?

It should reason over:

- syllabus/topics
- completion/progress
- exams
- deadlines
- attendance
- study time
- student priorities
- user-defined constraints
- PYQ importance/frequency

## 3. Dynamic scheduling

KAMLA should not generate a static timetable and forget about it.

The schedule should adapt when circumstances change.

Examples:

- an exam is postponed
- a deadline changes
- a student misses a study session
- attendance becomes risky
- the student adds a startup/internship/project commitment
- the student changes priorities
- a topic is identified as high priority through PYQ analysis

Plan changes should be represented as recommendations/pending changes where appropriate.

The student should remain in control of consequential changes.

## 4. Personal constraints and tradeoffs

Students should be able to tell KAMLA what they care about and what they are willing to sacrifice.

Example:

> "I want to spend 2 hours every day on my startup this semester."

KAMLA should create a schedule that attempts to satisfy:

- academic requirements
- attendance constraints
- exam preparation
- startup time
- available daily time
- student priorities

Students may explicitly state preferences such as:

- attendance is non-negotiable
- grades are the top priority
- startup time is important
- I am willing to accept lower attendance where institutionally permissible
- I want weekends mostly free

These become planning constraints/preferences.

The system should explain tradeoffs rather than pretending every goal can always be perfectly satisfied.

## 5. Considerate AI

KAMLA's AI should be contextual, useful and non-judgmental.

It should:

- understand the student's current situation
- explain why it recommends something
- surface tradeoffs
- ask for clarification when necessary
- propose plan changes
- allow the student to accept/reject consequential changes
- avoid generic motivational spam
- avoid pretending certainty where the underlying data is uncertain

The LLM is NOT the source of truth for calculations.

Deterministic engines calculate attendance, time, constraints and schedule validity.

The LLM interprets those results and communicates them naturally.

## 6. Example of desired behavior

If a college announcement says:

> "COOS CA-2 postponed. New date: 14 September."

KAMLA should eventually be able to:

1. identify the relevant academic event
2. update the academic calendar
3. determine how the change affects the student's plan
4. explain the impact
5. propose an updated study plan

Example:

> "COOS CA-2 was postponed to 14 September.
>
> You now have 6 additional days.
>
> I've adjusted your study plan accordingly.
>
> New priority: finish OS Unit 3 this week."

This is an example of the desired product behavior, not necessarily an MVP requirement.

## 7. PYQ analysis

KAMLA should eventually support uploading/processing previous-year question papers.

It should:

- extract questions
- identify topics
- determine topic frequency
- identify frequently asked topics
- compare PYQ topic frequency with the student's current academic progress
- identify frequently asked topics that remain incomplete
- use this information in prioritization

Example:

> "Synchronization has appeared frequently in previous-year papers.
>
> You have not completed this topic yet.
>
> Would you like me to raise its priority and adjust your study plan?"

PYQ topic mappings may initially be automatically generated.

Auto-mapped topics may be used for ranking, but KAMLA must clearly disclose that mappings are unconfirmed until the student reviews them.

## 8. Future information integrations

These are future roadmap items, NOT current MVP requirements.

Potential future integrations include:

- official college WhatsApp groups for relevant notices
- college announcements
- Unstop for hackathon/activity discovery
- personalized recommendations based on student interests

For WhatsApp, the intended future behavior is to process relevant official college-group announcements rather than indiscriminately ingest private conversations.

For Unstop, KAMLA may eventually recommend relevant hackathons/activities and redirect the student to Unstop for registration.

## 9. Notifications and proactive behavior

KAMLA should eventually be able to proactively surface useful academic information.

Examples:

- exam approaching
- study preparation should begin
- attendance approaching danger zone
- important topic still incomplete
- deadline approaching
- plan has become infeasible
- new college announcement affects the plan

Notifications should be useful and contextual rather than spammy.

## 10. MVP philosophy

The MVP should prove the core decision-making loop.

Prioritize:

1. secure student account
2. academic/course data
3. attendance tracking and deterministic attendance calculations
4. "can I skip this?" decision support
5. student goals and constraints
6. basic dynamic planning
7. academic progress/prioritization foundation

PYQ analysis and advanced AI behavior should be built after the core deterministic foundation is reliable.

Do not implement future integrations just because they are described here.

## 11. Product principles

KAMLA should:

- reduce cognitive load
- turn scattered academic information into decisions
- make tradeoffs visible
- preserve student agency
- adapt to changing circumstances
- avoid unnecessary notifications
- be transparent about uncertainty
- prefer explainable deterministic logic where possible
- use AI where contextual interpretation genuinely adds value

Do not implement anything from this document yet.
