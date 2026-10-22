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
