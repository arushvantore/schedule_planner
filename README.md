# Schedule Planner

**Know what to study next. Let the planner keep track of the rest.**

Schedule Planner is a student-focused academic planner and study assistant. It tracks each student’s syllabus, semester exams, assignments, study progress, results, and weak topics. A student can ask what to do today, study from their course materials, and ask for more work or a lighter plan as needed.

The goal is for students to arrive at exams prepared through steady, targeted work—without having to remember every syllabus topic, deadline, and revision date themselves.

Schedule Planner is intended for students with different schools, colleges, courses, subjects, and schedules. It is a separate product from Mentor Kit and must not depend on Mentor Kit or on one student’s personal setup.

## What a student can do

A student can ask the platform questions such as:

- “What should I work on today?”
- “I finished those. Give me more.”
- “Make today’s plan lighter.”
- “What assignments are due next?”
- “Which topics should I revise for my next exam?”
- “Show me all the questions for this subject from my connected course sources.”
- “Explain this part of the lecture.”
- “I got this question wrong. Help me understand it and practise the topic.”

The assistant should answer questions about the student’s own courses and materials, explain why work is recommended, and link answers to their sources when possible.

## How the planner organizes study

For every subject, Schedule Planner tracks the syllabus, course material, assignments, exams, revision, and backlog. It distinguishes between:

- **Covered:** the student has encountered the topic in class or course material.
- **Practised:** the student has attempted questions or exercises on it.
- **Understood:** available evidence suggests the student can answer questions on it.

A topic being listed in a syllabus or lecture does not, by itself, mean the student has learned it.

The planner combines current syllabus work with assignments, upcoming exams, revision, weak topics, and older backlog. It should keep old gaps visible without letting them bury current work.

When an exam is scheduled, the planner works backward from the date and aims to provide two revision passes plus a buffer before the exam. It uses syllabus progress, practice, and marks to recommend what to cover and revise. If an exam date changes or a student falls behind, it recalculates the plan and explains the change.

Exam and contest results can help identify weak concepts. The planner can return those concepts to the practice queue, offer explanations and targeted questions, and use later attempts to check for improvement.

## Daily workload and flexibility

The planner considers the student’s college timetable, commitments, and the time or study capacity the student has available on different days. It should be able to plan a lighter or fuller day accordingly.

Students can ask the planner to:

- Give them more work after they finish the plan.
- Make the plan lighter when they have less time or energy.
- Focus on an upcoming exam, assignment, or weak topic.
- Rebalance work after a missed day or a schedule change.
- Add a commitment or pause work on a subject.

The planner should keep the workload manageable, explain its recommendations, preserve exam revision where possible, and avoid guilt-based messages or streak pressure. Students can choose whether to receive reminders and adjust or pause them.

## Academic sources

Students should be able to start with manual setup or imports. Connections to outside sources are optional and can be added over time.

| Source | Information it may provide |
|---|---|
| Newton School or another learning portal | Course content, syllabus, assignments, questions, and lecture videos |
| College website | Semester exam calendar, notices, assignment information, and deadlines |
| College Slack | Course questions, announcements, deadline changes, and shared study material |
| College timetable | Classes and commitments that affect study availability on each day |
| Exam and contest results | Marks and performance that can reveal topics needing more practice |
| Student uploads | Syllabi, PDFs, question papers, timetables, and other study materials |

The planner should support a student’s full semester schedule, including all available exams and assignment deadlines—not only the next exam.

## Background syncing

A background sync service should check connected sources about every two minutes where the source supports that frequency. It should detect new or changed course content, questions, exam dates, assignment details, and deadlines, then update the student’s plan.

Use a supported API or event feed when available. Use page reading or scraping only when permitted by the source and the student’s authorized access. Actual update timing depends on the source’s integration and rate limits.

The app should show:

- When each source last synced.
- Whether the connection is working or needs attention.
- Which information changed and where it came from.
- When information could not be checked or may be out of date.

If sources disagree or an extracted date is uncertain, ask the student to confirm it before relying on it.

## Questions and PDF exports

A student should be able to ask for **all matching questions they can access** for a chosen subject from their connected portal and college Slack. Schedule Planner should organize those questions into one downloadable PDF, with source references where available.

The collection should be limited to material the student is authorized to access. Search results and exported PDFs must not include another student’s private data.

## Lecture videos and explanations

Students should be able to watch supported lecture videos within the platform and ask for:

- An explanation of the lecture or a selected section.
- A summary of key ideas.
- Help understanding a specific timestamp or confusing concept.
- Practice questions based on the lecture.

When possible, explanations should point to the relevant course material or video timestamp. The platform should make clear which source material was used.

## Privacy and student ownership

Each student’s information must remain private to that student.

- Every request must be checked on the server to ensure the student can access only their own account, courses, messages, marks, schedule, and study history.
- Student data must be isolated between accounts. One student’s information must never appear in another student’s plan, chat, search results, PDF, or reports.
- Each student connects their own authorized sources and can see and disconnect those connections.
- Students should be able to export or delete their data.
- The planner should request only the source access needed for its features.
- Portal passwords must not be stored by Schedule Planner.
- College staff should not see an individual student’s private study history by default.
- Any future college reporting must be clearly disclosed, appropriately aggregated, and governed by student consent and college policy.

Data isolation and access controls must be in place before the product hosts information for multiple students.

## AI usage

The planner’s core scheduling, syllabus tracking, deadline tracking, progress updates, and study queues should work without an AI model for every action. AI is useful for tutoring, explanations, searching course materials, and answering student questions.

The student experience should feel open-ended, without an arbitrary small question allowance where possible. However, AI models and hosting have finite processing capacity and cost, so Schedule Planner cannot honestly promise literally unlimited AI use at no cost. Any practical usage limits should be fair, transparent, and separate from the planner’s basic organization features.

## Product principles

1. **The student asks what to do next.** The planner handles organizing the syllabus and deadlines.
2. **Use the student’s actual academic information.** Keep source links and sync status visible.
3. **Be clear about uncertainty.** Confirm uncertain dates and explain missing or stale information.
4. **Track learning, not just coverage.** Use practice and results to find weak topics.
5. **Keep plans adjustable.** Recalculate as availability, results, and deadlines change.
6. **Keep students in control.** Connections, reminders, exports, and deletion should be understandable and adjustable.
7. **Protect each student’s data.** Enforce account isolation on the server.
8. **Work without integrations.** Manual setup and imports should provide a useful starting point.
9. **Support phones and computers.** Build a responsive student-facing web app with chat, daily plan, progress, and study materials.
10. **Build for extension.** Add new sources and learning features over time without rebuilding the planner’s core.

## Current project status

The repository currently contains a command-line prototype and the planning engine that forms the product’s foundation. The web app, student accounts, source syncing, PDF question collection, and lecture assistant remain planned work.

Existing local changes should be preserved as development continues. New work should be added in reviewable stages, with current project instructions followed.

## Roadmap

### Stage 1 — Planning engine

Maintain the core planner for subjects, syllabus topics, assignments, exams, completion, revision, weak-topic practice, daily capacity, and backlog.

### Stage 2 — Generic setup and application interface

Let students set up their own subjects, syllabus, semester exam calendar, assignment deadlines, timetable, and daily availability. Add the API needed by the web app and future source connections.

### Stage 3 — Student web app

Build a responsive app for phones and computers with a daily plan, progress views, semester calendar, assignments, materials, and a chat-style way to ask what to do or ask about course information.

### Stage 4 — Secure student identity and data separation

Establish account access, data export and deletion, and server-side isolation so each student can access only their own information. Complete this foundation before offering a shared hosted service.

### Stage 5 — Source connections and background sync

Add supported connections for Newton School, college websites, Slack, timetables, and student uploads. Implement background syncing, source health, change detection, and confirmation for uncertain information.

### Stage 6 — Questions, PDFs, and lecture help

Add subject-based question search across a student’s connected sources, combined PDF exports, in-platform video viewing, explanations, summaries, and practice based on course materials.

### Stage 7 — Student pilot and college integration

Pilot with students, measure whether plans are accurate and manageable, and improve the product based on feedback. Once the privacy and access model is ready, work with college IT teams to connect approved portal and campus systems.

## Long-term direction

Schedule Planner begins as a tool students can set up for their own courses and schedules. It can grow to support more schools, colleges, learning platforms, and study features over time.

The longer-term goal is to work with college IT teams to connect Schedule Planner to official college portals, so students can receive an up-to-date, personalized study plan while keeping control of their own academic information.
