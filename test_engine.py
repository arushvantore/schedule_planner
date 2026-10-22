from datetime import date, timedelta

from capacity import SERVE_COUNT, classify_day
from store import fetch_tokens, init_db, seed_sample

TODAY = date(2026, 10, 20)


# Fresh in-memory database for an isolated test.
def fresh():
    return init_db(":memory:")


# Insert a bare token directly, for focused mini-setups.
def add_token(conn, subject_id, title, state="pending", covered=1, deadline=None,
              difficulty=None, prereq_id=None, origin_date=None,
              completed_at=None, next_review=None):
    return conn.execute(
        """INSERT INTO tokens
           (subject_id, title, state, covered, deadline, difficulty,
            prereq_id, origin_date, completed_at, next_review)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (subject_id, title, state, covered, deadline, difficulty,
         prereq_id, origin_date, completed_at, next_review),
    ).lastrowid


# Add schedule rows for a weekday in the test database.
def add_schedule(conn, day_name, kind):
    conn.execute(
        "INSERT INTO schedule (day_name, kind) VALUES (?, ?)", (day_name, kind))


# The schema must never contain minute or duration columns, ever.
def check_schema_has_no_minutes():
    conn = fresh()
    tables = ["subjects", "tokens", "exams", "schedule", "materials",
              "plan_history"]
    for table in tables:
        columns = [row["name"] for row in
                   conn.execute("PRAGMA table_info(" + table + ")")]
        for column in columns:
            if "minute" in column or "duration" in column or "elapsed" in column:
                return False

    expected = {
        "id", "subject_id", "title", "state", "covered", "deadline", "source",
        "difficulty", "priority", "prereq_id", "origin_date", "completed_at",
        "next_review",
    }
    token_columns = {row["name"] for row in
                     conn.execute("PRAGMA table_info(tokens)")}
    return token_columns == expected


# The sample seed must load 2 subjects, 8 tokens, the prerequisite chain,
# one overdue token, one review-due token, and relative deadlines.
def check_sample_seed():
    conn = fresh()
    seed_sample(conn, TODAY)
    tokens = fetch_tokens(conn)
    if len(tokens) != 8:
        return False

    subjects = conn.execute("SELECT COUNT(*) AS n FROM subjects").fetchone()["n"]
    if subjects != 2:
        return False

    by_title = {token["title"]: token for token in tokens}
    limits = by_title["Limits and continuity"]
    differentiation = by_title["Differentiation"]
    integration = by_title["Integration"]
    if differentiation["prereq_id"] != limits["id"]:
        return False
    if integration["prereq_id"] != differentiation["id"]:
        return False

    # Kinematics is the overdue demo token.
    if by_title["Kinematics"]["deadline"] >= TODAY.isoformat():
        return False

    # Limits is the upcoming-deadline demo token (in 2 days).
    if limits["deadline"] != (TODAY + timedelta(days=2)).isoformat():
        return False

    # Waves is the review-due demo token (hard, next_review already past).
    waves = by_title["Waves"]
    if waves["state"] != "completed" or waves["next_review"] >= TODAY.isoformat():
        return False

    # Every pending token gets today as its origin date.
    for token in tokens:
        if token["state"] == "pending" and token["origin_date"] != TODAY.isoformat():
            return False

    # Exactly one exam: Maths mid-term 12 days out.
    exams = conn.execute("SELECT * FROM exams").fetchall()
    if len(exams) != 1:
        return False
    if exams[0]["exam_date"] != (TODAY + timedelta(days=12)).isoformat():
        return False

    return True


# Capacity must follow the agreed rules: holiday > class load > deadline
# pressure downgrade.
def check_capacity_rules():
    day = TODAY.strftime("%A")

    # Empty schedule, no tokens: high.
    conn = fresh()
    if classify_day(conn, TODAY) != "high":
        return False

    # Three classes: medium.
    conn = fresh()
    for _ in range(3):
        add_schedule(conn, day, "class")
    if classify_day(conn, TODAY) != "medium":
        return False

    # Four classes: low.
    conn = fresh()
    for _ in range(4):
        add_schedule(conn, day, "class")
    if classify_day(conn, TODAY) != "low":
        return False

    # Holiday wins: high.
    conn = fresh()
    add_schedule(conn, day, "holiday")
    for _ in range(4):
        add_schedule(conn, day, "class")
    if classify_day(conn, TODAY) != "high":
        return False

    # One class + transit counts as load 2: medium.
    conn = fresh()
    add_schedule(conn, day, "class")
    add_schedule(conn, day, "transit")
    if classify_day(conn, TODAY) != "medium":
        return False

    # Deadline pressure downgrades medium to low.
    conn = fresh()
    for _ in range(3):
        add_schedule(conn, day, "class")
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('Physics')").lastrowid
    add_token(conn, subject_id, "Due soon",
              deadline=(TODAY + timedelta(days=1)).isoformat())
    if classify_day(conn, TODAY) != "low":
        return False

    # Deadline pressure never drops below low.
    conn = fresh()
    for _ in range(4):
        add_schedule(conn, day, "class")
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('Physics')").lastrowid
    add_token(conn, subject_id, "Due soon",
              deadline=(TODAY + timedelta(days=2)).isoformat())
    if classify_day(conn, TODAY) != "low":
        return False

    return True


# The agreed serve counts: low 1, medium 2, high 3.
def check_serve_counts():
    return SERVE_COUNT == {"low": 1, "medium": 2, "high": 3}


# Print a clear result so a beginner can see whether each check worked.
def print_result(name, passed):
    if passed:
        print("PASS: " + name)
    else:
        print("FAIL: " + name)


if __name__ == "__main__":
    print_result("schema has no minutes", check_schema_has_no_minutes())
    print_result("sample seed", check_sample_seed())
    print_result("capacity rules", check_capacity_rules())
    print_result("serve counts", check_serve_counts())
