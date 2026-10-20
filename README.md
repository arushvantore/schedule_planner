# Schedule Planner — Autonomous Academic Execution Engine

> **What to study today — decided for you. No planning. No time-tracking. No syllabus worry.**
> You open it, see 2–3 topics, study at your own speed, tick them done, hit refill if you want more.
> The engine handles everything else — so exam eve arrives with: *"I'm already prepared."*

**Creator:** arush ([@arushvantore](https://github.com/arushvantore))
**Repo:** https://github.com/arushvantore/schedule_planner
**Status:** working prototype (CLI). Everything below is labeled honestly:
**works today** vs **planned** vs **vision**.

---

## 1. What this project IS

A self-hosted engine that takes the **entire cognitive load of academic planning
away from the student**. The student never looks at a calendar, never counts
minutes, never tracks a syllabus. Behind the scenes the system:

1. **Gathers** everything about the student's academic world (college portal,
   timetable, class Slack, uploaded PDFs, Codeforces) and remembers it —
   including *changes* (a professor moving a deadline is detected, not just
   new entries)
2. **Classifies** each day's capacity (Low / Medium / High) from real
   constraints — lecture hours, bus timings, holidays, missed classes —
   instead of ever tracking time
3. **Serves** 2–3 conceptual topic *tokens* per day, in the right order,
   with study materials attached — and a **refill button** when you finish
4. **Plans backward** from every upcoming exam, finishing all covered
   material by **exam − 5 days** (an invisible safety buffer), with spaced
   revision passes whose intervals adapt to how easy/hard you found each topic
5. **Never forgets** — unfinished tokens roll into tomorrow automatically,
   but a day is never buried under yesterday's failures

The promise is a **daily answer**, not a calendar: open → study → tick → live your day.

---

## 2. Core philosophy (the rules the engine believes)

- **Topics are tokens, not time-boxes.** The engine tracks state
  (pending / completed), priority, and prerequisites — **never minutes,
  never elapsed time.** Student-visible output contains no durations.
- **Capacity, not schedules.** A day is Low (1 core token), Medium
  (2–3), or High (3–4 + safety buffer) — computed from immutable external
  facts (classes, transit, active deadlines), not stopwatches.
- **Show the ceiling, not the wall.** Only 2–3 targets appear at once.
  Finish them → "Refill Queue" routes the next logical concept through the
  dependency graph. Cognitive load stays capped.
- **Backward chaining.** Exam on Day N → curriculum path must complete by
  Day N − 5. The buffer is invisible and uncompromised.
- **Qualitative memory.** Marking a token done asks one tap: **Easy /
  Medium / Hard.** Easy → revisited 7+ days out. Medium → ~5 days.
  Hard → back into the queue within 48 hours for a light pass.
- **Binary honesty.** Tokens are pending or completed; unfinished work rolls
  forward with an anti-overwhelm cap — a student who misses days gets a
  *reachable* plan, never a guilt wall.

---

## 3. What works TODAY (version 1)

A command-line app in this folder:

- **Menu** — show backlog · mark a topic studied · show today's plan · quit
- **Backlog view** — college-covered topics you haven't studied, by subject
- **Mark studied** — tick a topic; saved to `progress.json` between runs
- **Today's plan** — urgent deadlines first, then backlog, each line with its
  **reason**
- **Starter data** — Maths 1 + Applied Physics samples
- **Tests** — simple PASS/FAIL file (4 checks, all passing)

### What it is NOT (yet)

- The v1 code still plans with internal minutes — **Stage 1 rewrites it to
  the pure token/capacity model** described in §2
- Not connected to portal / Slack / PDFs / Codeforces (planned)
- No database (JSON file for now), no API, no extension, no web app
- No exams list, revision engine, or capacity classifier yet (all Stage 1)

---

## 4. A day in the target product

> **6:30 AM — one message:**
> *Today (Medium capacity — bus at 5:30):*
> *1. Implement Circular Queue in Python* 📎 *Lecture 14 recording*
> *2. Circular Queue — practice sheet* 📎 *from Slack*
> *3. Revise Vectors (Hard last time — second pass)*
> *Maths exam in 12 days — on pace.*

You study at your own speed. Tick done. All three gone? → tap **Refill** →
next logical token appears (or "All clear — free choice"). No times, no
minutes, no menus, no thinking.

---

## 5. Data feeds (how it becomes omniscient)

| Feed | Mechanism | Status |
|---|---|---|
| 🔌 **College portal** | Browser extension reads the portal in *your own logged-in browser* and sends data to the local engine — **zero credentials stored anywhere**; detects updates/deletions, not just new rows | Planned (Phase 1) |
| 🎥 **Recorded lectures** | Extension watches video progress (`onplay`/`timeupdate`); a half-watched lecture's remainder is re-queued as a token | Planned |
| 💬 **Slack** | Event listener via Slack **Socket Mode** (WebSockets — no public server needed) parses class channels for quiz / postponed / deadline-change signals; also receives posted assignments; daily plan flows back out | Planned |
| 📄 **PDFs you upload** | Exam notices, timetables, worksheets → dates extracted → **shown to you for one confirm tap** → enters the engine (never a silent wrong date) | Planned |
| 🏋️ **Codeforces** | Official User Status API — solved problems enter the re-solve queue; **WA/TLE submissions generate debug tokens** automatically | Planned |
| 📅 **Timetable / bus / notices** | Static vectors loaded once (manually or from PDF); define the capacity classifier's inputs | Planned |

Each feed logs its own health. If the portal feed dies, the engine keeps
working from the last good data and says so honestly.

---

## 6. Engine rules (the brain)

- **Capacity classifier:** `Capacity = f(lecture hours, transit buffers, active deadlines)`
  → Low / Medium / High → how many tokens are served today
- **Priority order:** carry-over from yesterday → overdue → revision due
  (decay schedule) → exam-urgent (next 2–3 exams) → backlog by prerequisite
  order → today's-taught review (new lecture recording today → review tonight)
- **Prerequisite graph:** tokens map to subject nodes; a concept is served
  only after its prerequisites are completed
- **Syllabus progress:** per subject — *taught %* and *completed %* shown on
  the dashboard and in every daily output
- **Readiness signal:** honest per-exam indicator (coverage × revisions done)
  — a signal, never a fake guarantee
- **Refill evaluation:** on request, the dependency graph is walked for the
  next reachable token within the day's capacity rules

---

## 7. Architecture & two-phase delivery

**Phase 1 (student-owned):**
```
[Browser extension] —reads→ your portal session (nothing stored)
        │ sends data
        ▼
[Local engine: FastAPI + SQLite] —the brain, runs on your machine
        │ serves
        ▼
[Checklist injected into the portal page] + [daily Slack message]
```

**Phase 2 (institution-owned):** once student outcomes are proven, the same
engine APIs plug into the college's official systems — portal link first,
native integration later. Faculty get an aggregate-only dashboard
(class syllabus %, who's behind) — the institution-facing product.

Code layout (from Stage 2): `/core` (engine) · `/connectors`
(portal, slack, pdf, codeforces) · `/models` (schemas) · SQLite with strict
integrity constraints.

---

## 8. What this product promises (design rules)

1. **The daily answer first** — open it, see today's targets in 2 seconds
2. **No time shown, ever** — no durations, no schedules, no stopwatches
3. **Never guilt-trip** — missed days rebalance; carry-over can't bury a day
4. **Always show why** — every token carries its reason
5. **Never show a wrong number** — extracted dates need your confirm tap
6. **Recall, don't re-read** — revision says "close the notes first"
7. **Works offline** — the brain is local; notifications are a bonus
8. **Privacy** — zero stored credentials · no ads · nothing sold ·
   faculty sees aggregates only
9. **Tests after every step** — no feature ships with a failing test

---

## 9. Build order

| Stage | What | Unlocks |
|---|---|---|
| **1** | **Rewrite the brain** — token model (no minutes) · capacity classifier · exam −5 backward chain · Easy/Hard decay · roll-forward with cap · prerequisites · syllabus % · `today.md` · daily auto-run — all tested | *It thinks correctly for me* |
| **2** | FastAPI shell (Pydantic added with approval) + portal connector | *It has a body* |
| **3** | Browser extension — injects the checklist, captures portal data locally, video-progress requeue | *It lives inside the portal* |
| **4** | Slack (Socket Mode) · PDF confirm flow · Codeforces (WA/TLE tokens) | *It listens to everything* |
| **5** | PWA screens (Today · Map · Progress · Add/Fix) + material library | *The sellable artifact* |
| **6** | Faculty dashboard + consent/roles | *Walk into the faculty office* |
| **7** | College pilot → portal link → official feed → campus license | *The deal* |

Gate before Stage 5+: **3-of-10 rule** — talk to 3–5 classmates first;
feature requests go to an idea bank, not into code.

---

## 10. Market note (honest)

Students pay $4–20/month for weaker planners (StudyTracker, Shovel,
StudyMap); Indian exam apps (Kalnehi, IsotopeAI) exist but require manual
entry. **The gap: nothing feeds itself from your own college's portal, and
nothing is sold *to the college* as a student-success tool** (the
institutional precedent is platforms like EAB Starfish). Free for students,
the institution pays — that is the path.

---

## 11. Install & run (today)

```bash
cd schedule_planner
python3 planner.py        # menu: backlog · mark studied · plan · quit
python3 test_planner.py   # expected: 4 × PASS
```

Requirements: Python 3.11+, nothing else. First run creates `progress.json`.

---

## 12. Layout (today)

```
schedule_planner/
├── planner.py        # CLI menu app (v1 — to be reworked into the token engine)
├── sample_data.py    # starter topics
├── test_planner.py   # PASS/FAIL checks
├── progress.json     # saved progress
├── README.md         # this file
├── .gitignore
└── .venv/
```

---

## 13. For AI assistants working on this repo

Working style: **plan → plain-language explanation → approval → build →
run tests after every step.** Locked design rules live in §8. The build
order in §9 is the source of truth — current step: **Stage 1** (rewrite the
brain to the token/capacity model). Never install packages (FastAPI/Pydantic
arrive at Stage 2, with explicit approval), never show per-topic times,
never add features without approval, never break the tests.
