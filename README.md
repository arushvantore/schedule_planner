# Schedule Planner — Autonomous Academic Execution Engine

> **What to study today — decided for you. No planning. No time-tracking. No syllabus worry.**
> You open it, see 2–3 topics, study at your own speed, tick them done, hit refill if you want more.
> The engine handles everything else — so exam eve arrives with: *"I'm already prepared."*

**Creator:** arush ([@arushvantore](https://github.com/arushvantore))
**Repo:** https://github.com/arushvantore/schedule_planner
**Status:** working CLI prototype + Stage 1 rewrite in progress.
Everything below is labeled honestly: **works today** vs **planned** vs **vision**.

---

## ⏸️ HANDOFF STATUS (read this first if you are an AI continuing the project)

**Last updated:** 20 Oct 2026. Creator is away after exams; resume here.

**Where exactly we stopped:**
- **Stage 1 (rewrite the brain) is COMPLETE** — all steps done, all 17 tests pass.
- The engine is built, tested, and running: `store.py` (SQLite, zero minutes) · `capacity.py` (Low/Medium/High) · `engine.py` (5-bucket priority, decay, exam−5, syllabus%) · `planner.py` (CLI v2, no minutes) · `report.py` + `daily.py` + `run_daily.sh` + launchd template.
- **Next step: Stage 2** — FastAPI shell (Pydantic, with approval) + portal connector.
- **Do not:** add minute/duration columns, show per-topic times, install packages without approval, commit without approval, or skip running tests after every step. Full rules in §9 and §14.

---

## 1. What this project IS

A self-hosted engine that takes the **entire cognitive load of academic
planning away from the student**. The student never looks at a calendar,
never counts minutes, never tracks a syllabus. Behind the scenes the system:

1. **Gathers** everything about the student's academic world (college
   portal, timetable, class Slack, uploaded PDFs, Codeforces) and remembers
   it — including *changes* (a professor moving a deadline is detected,
   not just new entries)
2. **Classifies** each day's capacity (Low / Medium / High) from real
   constraints — lecture hours, bus timings, holidays, missed classes —
   instead of ever tracking time
3. **Serves** 2–3 conceptual topic *tokens* per day, in the right order,
   with study materials attached — and a **refill button** when you finish
4. **Plans backward** from every upcoming exam, finishing all covered
   material by **exam − 5 days** (an invisible safety buffer), with spaced
   revision passes whose intervals adapt to how easy/hard you found each
   topic
5. **Never forgets** — unfinished tokens roll into tomorrow automatically,
   but a day is never buried under yesterday's failures

The promise is a **daily answer**, not a calendar: open → study → tick →
live your day.

---

## 2. Core philosophy (the rules the engine believes)

- **Topics are tokens, not time-boxes.** The engine tracks state
  (pending / completed), priority, and prerequisites — **never minutes,
  never elapsed time.** Student-visible output contains no durations.
- **Capacity, not schedules.** A day is Low (1 core token), Medium (2), or
  High (3) — computed from immutable external facts (classes, transit,
  active deadlines), not stopwatches.
- **Show the ceiling, not the wall.** Only 2–3 targets appear at once.
  Finish them → "Refill Queue" routes the next logical concept through the
  dependency graph. Cognitive load stays capped.
- **Backward chaining.** Exam on Day N → curriculum path must complete by
  Day N − 5. The buffer is invisible and uncompromised.
- **Qualitative memory.** Marking a token done asks one tap: **Easy /
  Medium / Hard.** Easy → revisited 7+ days out. Medium → ~5 days.
  Hard → back into the queue within 48 hours for a light pass.
- **Binary honesty.** Tokens are pending or completed; unfinished work
  rolls forward with an anti-overwhelm cap — a student who misses days
  gets a *reachable* plan, never a guilt wall.

---

## 3. What works TODAY (verified 20 Oct 2026 — Stage 1 COMPLETE)

| Piece | State |
|---|---|
| **Memory layer** (`store.py`) | ✅ SQLite schema (tokens, subjects, exams, schedule, materials, plan history) with **zero minute columns**; seeds 8 tokens + 1 exam, with a prerequisite chain, one overdue token (Kinematics), one review-due token (Waves) |
| **Capacity classifier** (`capacity.py`) | ✅ holiday → High; class load ≤1 High / ≤3 Medium / ≥4 Low; deadline pressure (≤2 days) downgrades one level. Serves 1 / 2 / 3 tokens |
| **Planning engine** (`engine.py`) | ✅ 5-bucket order (carry-over with 3-day postponed flag → overdue → review-due → deadline-soon → backlog) · prerequisite gating · decay Easy+7d / Medium+5d / Hard+2d · exam−5 pace report · syllabus taught%/completed% |
| **CLI v2** (`planner.py`) | ✅ today's plan (capacity + reasons + exam lines) · backlog · mark-done with Easy/Medium/Hard tap · refill · exams & syllabus view · writes `today.md` · persists to `data/planner.sqlite` — **no minutes anywhere** |
| **Report & auto-run** (`report.py`, `daily.py`, `run_daily.sh`, `launchd/`) | ✅ `today.md` writer · daily runner (smoke-tested) · launchd 6:30 AM template (**not installed** — activate by hand per comments in the plist) |
| **Test suites** | ✅ `test_engine.py` 12/12 PASS + `test_planner.py` 5/5 PASS = **17/17** |
| **README** | ✅ this document |
| FastAPI shell, portal connector, extension, Slack, PDF, Codeforces feeds | ❌ not started (Stages 2–4) |

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

## 6. Engine spec (agreed design — implement exactly this)

### 6.1 Day capacity classifier — ✅ implemented in `capacity.py`
- Inputs from the `schedule` table for the weekday: rows of kind
  `class`, `transit`, or `holiday`; plus pending tokens with a deadline
  within 2 days ("deadline pressure").
- `load = (number of class rows) + (1 if any transit row)`
- Rules, in order:
  - `holiday` present → **High**
  - else `load ≤ 1` → High · `load ≤ 3` → Medium · `load ≥ 4` → Low
  - If any pending deadline ≤ today+2 exists → downgrade one level
    (High→Medium, Medium→Low, Low stays Low)
- Serve counts: **Low = 1 token, Medium = 2, High = 3** (per day)

### 6.2 Daily plan builder — ✅ implemented in `engine.py`
- A token is **eligible** if: pending AND its prerequisite (single
  `prereq_id` chain) is completed; OR completed but due for review
  (difficulty set and `next_review` ≤ today).
- Serve order — fill the day's slots from these buckets, first-come:
  1. **Carry-over** — pending, `origin_date` < today (reason:
     `carried over from {date}`; if ≥3 days postponed append
     ` — {n} days postponed, do this first`)
  2. **Overdue** — pending, deadline < today (reason: `deadline passed on {date}`)
  3. **Review due** — completed tokens whose `next_review` ≤ today
     (reason: `review due (was {difficulty} last time)`)
  4. **Deadline soon** — pending, deadline ≤ today+3
     (reason: `deadline in {n} days`)
  5. **Backlog** — pending, covered by college, prerequisite done
     (reason: `backlog from {subject}`)
- Anti-overwhelm: carry-over is allowed to fill the whole day's capacity;
  the day is never bigger than its capacity.
- **Refill:** each tap adds the next eligible unserved token (1 per tap,
  no artificial total limit — the student pulls, the system never pushes).

### 6.3 Decay rule (asymmetric feedback) — ✅ implemented in `engine.py`
- Tap on completion: Easy / Medium / Hard.
- `next_review = completed_at + 7 days` (Easy) / `+5` (Medium) / `+2` (Hard).
- A due review token re-enters the serve buckets (see 6.2 bucket 3).

### 6.4 Backward chain with exams — ✅ implemented in `engine.py` (`exam_report`)
- Table `exams(subject_id, name, exam_date)`.
- Target: all exam-relevant completed by **exam_date − 5 days**; revision
  passes scheduled inside that window using the decay rule. If the plan
  cannot fit (too many tokens vs days left), report honestly
  (`{subject}: behind for {exam}`) — never fake a green.

### 6.5 Syllabus progress — ✅ implemented in `engine.py` (`syllabus_progress`)
- Per subject: taught % (tokens with any activity) and completed %
  (completed / total). Shown in dashboard and daily output.

### 6.6 Output → `today.md` — ✅ implemented in `report.py`
- Plain markdown, no durations anywhere: capacity level, numbered token
  list with reasons + attached materials, exam status line, refill hint.

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

**Phase 2 (institution-owned):** once student outcomes are proven, the
same engine APIs plug into the college's official systems — portal link
first, native integration later. Faculty get an aggregate-only dashboard
(class syllabus %, who's behind) — the institution-facing product.

Code layout (from Stage 2 on): `/core` (engine) · `/connectors`
(portal, slack, pdf, codeforces) · `/models` (Pydantic schemas) · SQLite
with strict integrity constraints. **FastAPI + Pydantic are added only at
Stage 2, with explicit approval.**

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

## 9. Build order (with exact current position)

| Stage | What | Unlocks | Status |
|---|---|---|---|
| **1** | **Rewrite the brain** — see sub-steps below | *It thinks correctly for me* | ✅ COMPLETE (20 Oct 2026) |
| **2** | FastAPI shell (Pydantic, with approval) + portal connector | *It has a body* | ❌ NEXT |
| **3** | Browser extension — injects checklist, captures portal data locally, video-progress requeue | *It lives inside the portal* | ❌ |
| **4** | Slack (Socket Mode) · PDF confirm flow · Codeforces (WA/TLE tokens) | *It listens to everything* | ❌ |
| **5** | PWA screens (Today · Map · Progress · Add/Fix) + material library | *The sellable artifact* | ❌ |
| **6** | Faculty dashboard + consent/roles | *Walk into the faculty office* | ❌ |
| **7** | College pilot → portal link → official feed → campus license | *The deal* | ❌ |

**Gate before Stage 5+:** 3-of-10 rule — talk to 3–5 classmates first;
feature requests go to an idea bank, not into code.

### Stage 1 sub-steps — ALL DONE ✅ (20 Oct 2026)

- ✅ **Step 0** — baseline: old tests 4/4 PASS, old code read
- ✅ **Step 1** — `store.py`: schema + `init_db` + `seed_sample` + CRUD. **No minute columns.**
- ✅ **Step 2** — `test_engine.py` (incl. the permanent "no minutes in schema" check) + `capacity.py` per §6.1
- ✅ **Step 3** — `engine.py` per §6.2 + §6.3 (eligibility, `build_plan` with reasons, `refill`, `complete_token` with decay)
- ✅ **Step 4** — exam−5 pace report (§6.4) + syllabus % (§6.5) + tests
- ✅ **Step 5** — CLI v2 rewired (`planner.py`), old minutes-based v1 and `sample_data.py` retired, tests rewritten
- ✅ **Step 6** — `today.md` (`report.py`) + `daily.py` + `run_daily.sh` + launchd template (not installed)
- ✅ **Step 7** — README updated to reflect reality + committed & pushed

**Rule going forward:** after each step run `python3 test_planner.py` AND
`python3 test_engine.py` — both must be all-PASS (17 checks) before moving
on. One step per approval; explain in plain words before editing.

---

## 10. Market note (honest)

Students pay $4–20/month for weaker planners (StudyTracker $4/mo, Shovel
$19.99/mo with LMS sync, StudyMap with SM-2); Indian exam apps (Kalnehi,
IsotopeAI) exist but require manual entry. Spaced retrieval is proven
strong (g≈0.74, Latimier 2020); uniform ≈ expanding intervals (g≈0.034).
**The gap: nothing feeds itself from your own college's portal, and
nothing is sold *to the college* as a student-success tool**
(institutional precedent: EAB Starfish). Free for students, the
institution pays — that is the path.

---

## 11. Install & run (today)

```bash
cd schedule_planner
python3 planner.py        # menu: today's plan · backlog · mark done · refill · exams · today.md · quit
python3 daily.py          # writes today.md once (for launchd/cron/manual)
python3 test_engine.py    # expected: 12 × PASS
python3 test_planner.py   # expected: 5 × PASS
```

Requirements: Python 3.11+, nothing else (stdlib only — SQLite via
`sqlite3` is stdlib). First run creates `data/planner.sqlite` (gitignored)
and seeds the sample data. `launchd/com.arush.planner.daily.plist` is a
6:30 AM template — **not installed**; activate by hand per the comments
inside it.

---

## 12. Layout (today)

```
schedule_planner/
├── store.py          # SQLite schema + seed + CRUD (zero minute columns)
├── capacity.py       # Low/Medium/High day classifier
├── engine.py         # plan builder (5 buckets), decay, exam−5, syllabus %
├── planner.py        # CLI v2 — menu over the engine (no minutes)
├── report.py         # writes today.md (plain markdown, no durations)
├── daily.py          # one-shot: seed db + write today.md (for launchd)
├── run_daily.sh      # wrapper for daily.py
├── test_engine.py    # 12 PASS/FAIL checks (schema, seed, capacity, engine)
├── test_planner.py   # 5 PASS/FAIL checks (CLI v2 outputs)
├── launchd/
│   └── com.arush.planner.daily.plist   # 6:30 AM template — NOT installed
├── data/             # planner.sqlite lives here (gitignored)
├── today.md          # generated output (gitignored)
├── README.md         # this document (the handoff source of truth)
├── .gitignore        # ignores __pycache__/, progress.json, .venv/, data/, today.md
└── .venv/
```

### Module APIs (for the next AI)

**`store.py`**
- `init_db(path)` → connection with schema applied (`:memory:` allowed)
- `seed_sample(conn, today=None)` — idempotent; 2 subjects, 8 tokens
  (prereq chain, relative deadlines, one overdue, one review-due), 1 exam
- `fetch_tokens(conn)` · `fetch_subject_names(conn)` · `mark_completed(conn, token_id, difficulty, completed_at, next_review)` · `log_plan(conn, day, token_id, capacity, reason)`
- Tables: `subjects`, `tokens(id, subject_id, title, state, covered, deadline, source, difficulty, priority, prereq_id, origin_date, completed_at, next_review)`, `exams`, `schedule(day_name, kind, detail)`, `materials`, `plan_history`

**`capacity.py`**
- `classify_day(conn, today=None)` → `"low" | "medium" | "high"`
- `SERVE_COUNT = {"low": 1, "medium": 2, "high": 3}` · `downgrade(level)`

**`engine.py`**
- `build_plan(conn, today=None)` → `{"capacity", "served", "items": [{"token", "reason"}]}`
- `refill(conn, plan, today=None)` → next item or `None` (appends to `plan`)
- `complete_token(conn, token_id, difficulty, today=None)` → sets state + `next_review` via decay
- `decay_days(difficulty)` → 7 / 5 / 2 · `is_eligible(token, by_id, today)`
- `exam_report(conn, today=None)` → honest pace lines (exam − 5 buffer)
- `syllabus_progress(conn)` → `{subject_id: {"taught_pct", "completed_pct"}}`

**`report.py`** — `write_today_md(conn, path="today.md", today=None)`
**`planner.py`** — `open_db()`, `show_todays_plan`, `show_backlog`, `mark_done`, `do_refill`, `show_exams` (all accept `today=` for tests); `main()` menu

---

## 13. Pitch one-pager (for mentors / demo day)

> "I built a study engine that thinks for me. It quietly watches everything
> my college throws at me — portal, timetable, class Slack, PDFs, my
> Codeforces submissions — and every morning hands me exactly 2–3 topics
> to study, sized to what my day can actually hold, with revisions timed
> so I never re-learn from scratch. I never open a calendar, never count
> minutes, never check the syllabus. The plan is already done.
> Every student I know does this planning by hand, badly, at 1 AM.
> It's free for students; colleges pay for the class-level readiness
> dashboard — the Starfish-style student-success tool they already budget for."

Demo script (3 min): show `today.md` output → mark a token Hard → refill →
show exam −5 status line. Then say: "and here it is inside the portal" (Stage 3).

---

## 14. Locked decisions log (do not reverse without explicit approval)

1. **No minutes/durations anywhere** — not in schema, not in output.
   Capacity + token counts instead. (Killed in final merge; the v1 CLI's
   internal 150-min budget is legacy, removed in Step 5.)
2. **Brain before shell** — engine + tests first (Stage 1); FastAPI +
   Pydantic only at Stage 2; browser extension only at Stage 3.
3. **Single prerequisite chain per token** (`prereq_id`), not full DAG —
   simple now; upgrade only if a real need appears.
4. **Serve counts:** Low=1, Medium=2, High=3; refill adds 1 per tap.
5. **Decay:** Easy +7d · Medium +5d · Hard +2d. Exam buffer: finish by
   exam − 5 days.
6. **PDF/portal-extracted dates always require a confirm tap** — never
   silently trust an extraction.
7. **Zero stored credentials** — extension uses the student's own logged-in
   browser session; no state.json passwords anywhere.
8. **No silent fallbacks** — a dead feed logs honestly and shows a health
   badge; never fabricate data.
9. **No guilt mechanics** — no streak-shaming, no wall of overdue tasks,
   no gamification of any kind, no ads, no notifications beyond the one
   daily plan message.
10. **Faculty view = aggregates only** (class syllabus %, who's behind);
    per-student data stays private until the student shares it.
11. **std-lib only until Stage 2** (FastAPI/Pydantic need explicit approval
    before install).
12. **3-of-10 gate** before building Stage 5+ (talk to 3–5 classmates).
13. **Never commit/push without creator's approval** — but a handoff save
    requested by the creator counts as approval.
14. **No per-topic clock times ever** in student-visible output.
15. **Banned: fake precision and fake guarantees** — "readiness signal",
    never "100% prepared guarantee".

---

## 15. For AI assistants working on this repo

Read §HANDOFF STATUS first, then §9 (current step), then §6 (engine spec —
now **implemented** in `capacity.py` / `engine.py` / `report.py`), then
§12 (module APIs), then §14 (locked decisions). Working style: **plan →
plain-language explanation → approval → build → run tests after every step**
(`python3 test_engine.py` = 12 checks AND `python3 test_planner.py` = 5
checks — both must stay all-PASS). Never install packages without approval
(Stage 2's FastAPI/Pydantic is the first install, and it needs explicit
yes). Never show per-topic times. Never add features without approval.
Never break existing tests. When finished with a step: report what changed,
test results, and what's next — then stop and wait for the creator.
