import os
import sqlite3
from datetime import date, timedelta

# The engine's memory lives in one SQLite file. The schema holds tokens
# (topics), subjects, exams, weekly schedule, materials and plan history.
# There are intentionally NO minute or duration columns anywhere: the engine
# classifies capacity, it never tracks time.
SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    title TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
        CHECK (state IN ('pending', 'completed')),
    covered INTEGER NOT NULL DEFAULT 1,
    deadline TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    difficulty TEXT
        CHECK (difficulty IS NULL OR difficulty IN ('easy', 'medium', 'hard')),
    priority INTEGER NOT NULL DEFAULT 0,
    prereq_id INTEGER REFERENCES tokens(id),
    origin_date TEXT,
    completed_at TEXT,
    next_review TEXT
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    name TEXT NOT NULL,
    exam_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    state TEXT NOT NULL DEFAULT 'pending'
        CHECK (state IN ('pending', 'completed')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS revision_checks (
    id INTEGER PRIMARY KEY,
    exam_id INTEGER NOT NULL REFERENCES exams(id),
    token_id INTEGER NOT NULL REFERENCES tokens(id),
    pass_number INTEGER NOT NULL CHECK (pass_number IN (1, 2)),
    completed_at TEXT NOT NULL,
    UNIQUE (exam_id, token_id, pass_number)
);

CREATE TABLE IF NOT EXISTS source_connections (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    source_name TEXT NOT NULL,
    external_ref TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'needs_setup'
        CHECK (status IN ('needs_setup', 'connected', 'attention', 'disconnected')),
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_error TEXT,
    UNIQUE (provider, external_ref)
);

CREATE TABLE IF NOT EXISTS source_items (
    id INTEGER PRIMARY KEY,
    connection_id INTEGER NOT NULL REFERENCES source_connections(id),
    external_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    subject TEXT,
    chapter TEXT,
    language TEXT,
    event_date TEXT,
    due_date TEXT,
    url TEXT,
    content TEXT,
    content_hash TEXT NOT NULL,
    source_updated_at TEXT,
    last_seen_at TEXT NOT NULL,
    UNIQUE (connection_id, external_id)
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY,
    connection_id INTEGER NOT NULL REFERENCES source_connections(id),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    items_seen INTEGER NOT NULL DEFAULT 0,
    items_changed INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY,
    day_name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('class', 'transit', 'holiday')),
    detail TEXT
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    token_id INTEGER NOT NULL REFERENCES tokens(id),
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    uri TEXT,
    confirmed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS plan_history (
    id INTEGER PRIMARY KEY,
    day TEXT NOT NULL,
    token_id INTEGER NOT NULL REFERENCES tokens(id),
    capacity TEXT NOT NULL,
    reason TEXT NOT NULL
);
"""


# Open (or create) the database and make sure the tables exist.
def init_db(path):
    if path != ":memory:":
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Upgrade databases created before source chapter/language metadata existed.
    source_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(source_items)")
    }
    if "chapter" not in source_columns:
        conn.execute("ALTER TABLE source_items ADD COLUMN chapter TEXT")
    if "language" not in source_columns:
        conn.execute("ALTER TABLE source_items ADD COLUMN language TEXT")
    conn.commit()
    return conn


# Load the starter subjects and tokens. Deadlines are relative to today so
# the samples always demonstrate an upcoming deadline and an overdue one.
def seed_sample(conn, today=None):
    if today is None:
        today = date.today()

    existing = conn.execute("SELECT COUNT(*) AS n FROM subjects").fetchone()["n"]
    if existing:
        return

    maths_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('Maths 1')"
    ).lastrowid
    physics_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('Applied Physics')"
    ).lastrowid

    def add_token(subject_id, title, covered=1, deadline=None, prereq_id=None,
                  state="pending", difficulty=None, completed_at=None,
                  next_review=None):
        origin = None if state == "completed" else today.isoformat()
        return conn.execute(
            """INSERT INTO tokens
               (subject_id, title, state, covered, deadline, source,
                difficulty, prereq_id, origin_date, completed_at, next_review)
               VALUES (?, ?, ?, ?, ?, 'manual', ?, ?, ?, ?, ?)""",
            (subject_id, title, state, covered, deadline, difficulty,
             prereq_id, origin, completed_at, next_review),
        ).lastrowid

    limits = add_token(maths_id, "Limits and continuity",
                       deadline=(today + timedelta(days=2)).isoformat())
    differentiation = add_token(maths_id, "Differentiation", prereq_id=limits)
    add_token(maths_id, "Integration", covered=0, prereq_id=differentiation)
    add_token(maths_id, "Matrices", state="completed", difficulty="easy",
              completed_at=(today - timedelta(days=3)).isoformat(),
              next_review=(today + timedelta(days=4)).isoformat())

    add_token(physics_id, "Vectors")
    add_token(physics_id, "Kinematics",
              deadline=(today - timedelta(days=1)).isoformat())
    add_token(physics_id, "Work and energy", covered=0)
    add_token(physics_id, "Waves", state="completed", difficulty="hard",
              completed_at=(today - timedelta(days=6)).isoformat(),
              next_review=(today - timedelta(days=4)).isoformat())

    conn.execute(
        "INSERT INTO exams (subject_id, name, exam_date) VALUES (?, ?, ?)",
        (maths_id, "Maths 1 Midterm",
         (today + timedelta(days=12)).isoformat()),
    )

    conn.commit()


# --------------------- setup: the student's own data ---------------------
# Create a subject from the setup menu. Raises ValueError with a friendly
# message instead of letting the UNIQUE constraint crash the menu.
def add_subject(conn, name):
    name = name.strip()
    if not name:
        raise ValueError("a subject needs a name")
    existing = conn.execute(
        "SELECT id FROM subjects WHERE name = ?", (name,)
    ).fetchone()
    if existing:
        raise ValueError("you already have a subject called " + name)
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES (?)", (name,)
    ).lastrowid
    conn.commit()
    return subject_id


# Add one topic (token) to a subject. It starts pending with today as its
# origin date, so carry-over and priority treat it exactly like the seeded
# topics. covered=1 means college has taught it (it shows in the backlog).
def add_topic(conn, subject_id, title, today=None, covered=1, deadline=None):
    if today is None:
        today = date.today()
    title = title.strip()
    if not title:
        raise ValueError("a topic needs a title")
    token_id = conn.execute(
        """INSERT INTO tokens
           (subject_id, title, state, covered, deadline, source, origin_date)
           VALUES (?, ?, 'pending', ?, ?, 'manual', ?)""",
        (subject_id, title, covered, deadline, today.isoformat()),
    ).lastrowid
    conn.commit()
    return token_id


# Put a named exam on the calendar (e.g. "Maths 1 Midterm", 2026-11-04).
# The exam report counts down to this date and enforces the exam-minus-5
# buffer. exam_date may be a date or a YYYY-MM-DD string.
def add_exam(conn, subject_id, name, exam_date):
    name = name.strip()
    if not name:
        raise ValueError("an exam needs a name")
    if isinstance(exam_date, date):
        exam_date = exam_date.isoformat()
    exam_id = conn.execute(
        "INSERT INTO exams (subject_id, name, exam_date) VALUES (?, ?, ?)",
        (subject_id, name, exam_date),
    ).lastrowid
    conn.commit()
    return exam_id


def add_assignment(conn, subject_id, title, due_date, today=None):
    if today is None:
        today = date.today()
    title = title.strip()
    if not title:
        raise ValueError("an assignment needs a title")
    if isinstance(due_date, date):
        due_date = due_date.isoformat()
    assignment_id = conn.execute(
        """INSERT INTO assignments
           (subject_id, title, due_date, created_at)
           VALUES (?, ?, ?, ?)""",
        (subject_id, title, due_date, today.isoformat()),
    ).lastrowid
    conn.commit()
    return assignment_id


def fetch_assignments(conn, pending_only=False):
    query = (
        "SELECT a.*, s.name AS subject_name FROM assignments a "
        "JOIN subjects s ON s.id = a.subject_id"
    )
    if pending_only:
        query += " WHERE a.state = 'pending'"
    query += " ORDER BY a.due_date, a.id"
    return [dict(row) for row in conn.execute(query)]


def complete_assignment(conn, assignment_id):
    cursor = conn.execute(
        "UPDATE assignments SET state = 'completed' "
        "WHERE id = ? AND state = 'pending'", (assignment_id,)
    )
    conn.commit()
    return cursor.rowcount > 0


def complete_revision(conn, exam_id, token_id, pass_number, today=None):
    if today is None:
        today = date.today()
    conn.execute(
        """INSERT OR IGNORE INTO revision_checks
           (exam_id, token_id, pass_number, completed_at)
           VALUES (?, ?, ?, ?)""",
        (exam_id, token_id, pass_number, today.isoformat()),
    )
    conn.commit()


# Return every token as a plain dictionary, ordered by id.
def fetch_tokens(conn):
    return [dict(row) for row in conn.execute("SELECT * FROM tokens ORDER BY id")]


# Return {subject_id: subject_name} for readable reasons and displays.
def fetch_subject_names(conn):
    return {row["id"]: row["name"]
            for row in conn.execute("SELECT id, name FROM subjects")}


# Save a finished token: state, the tap feedback, and its review date.
def mark_completed(conn, token_id, difficulty, completed_at, next_review):
    conn.execute(
        """UPDATE tokens
           SET state = 'completed', difficulty = ?, completed_at = ?,
               next_review = ?
           WHERE id = ?""",
        (difficulty, completed_at.isoformat(), next_review.isoformat(), token_id),
    )
    conn.commit()


# Insert one row into the plan history so past plans can be audited later.
def log_plan(conn, day, token_id, capacity, reason):
    conn.execute(
        "INSERT INTO plan_history (day, token_id, capacity, reason) VALUES (?, ?, ?, ?)",
        (day.isoformat(), token_id, capacity, reason),
    )
    conn.commit()
