from datetime import date, timedelta

from capacity import SERVE_COUNT, classify_day
from engine import (build_plan, complete_token, decay_days, exam_report,
                    is_eligible, refill, syllabus_progress)
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


# On the seeded sample day the plan must serve overdue first, then the
# due review, each with an honest reason.
def check_plan_bucket_order():
    conn = fresh()
    seed_sample(conn, TODAY)
    plan = build_plan(conn, TODAY)
    if plan["capacity"] != "medium":
        return False
    if plan["served"] != 2:
        return False
    first = plan["items"][0]
    second = plan["items"][1]
    if first["token"]["title"] != "Kinematics":
        return False
    if "deadline passed on" not in first["reason"]:
        return False
    if second["token"]["title"] != "Waves":
        return False
    if "review due (was hard last time)" not in second["reason"]:
        return False
    return True


# A pending token whose prerequisite is still pending must not be served;
# completing the prerequisite makes it eligible.
def check_prereq_gating():
    conn = fresh()
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('OS')").lastrowid
    first = add_token(conn, subject_id, "Processes")
    add_token(conn, subject_id, "Threads", prereq_id=first)

    tokens = fetch_tokens(conn)
    by_id = {token["id"]: token for token in tokens}
    threads = [token for token in tokens if token["title"] == "Threads"][0]
    if is_eligible(threads, by_id, TODAY):
        return False

    plan = build_plan(conn, TODAY)
    titles = [item["token"]["title"] for item in plan["items"]]
    if titles != ["Processes"]:
        return False

    complete_token(conn, first, "medium", TODAY)
    plan = build_plan(conn, TODAY)
    titles = [item["token"]["title"] for item in plan["items"]]
    return titles == ["Threads"]


# Carry-over tokens go first; a token postponed 3+ days gets the loud flag.
def check_carryover_and_flag():
    conn = fresh()
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('DBMS')").lastrowid
    add_token(conn, subject_id, "Fresh backlog",
              origin_date=TODAY.isoformat())
    add_token(conn, subject_id, "Missed twice",
              origin_date=(TODAY - timedelta(days=3)).isoformat())

    plan = build_plan(conn, TODAY)
    first = plan["items"][0]
    second = plan["items"][1]
    if first["token"]["title"] != "Missed twice":
        return False
    if "3 days postponed, do this first" not in first["reason"]:
        return False
    if second["token"]["title"] != "Fresh backlog":
        return False
    if "postponed" in second["reason"]:
        return False
    return True


# Refill adds exactly one next token per tap, then reports empty.
def check_refill_adds_one():
    conn = fresh()
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('CN')").lastrowid
    for number in range(4):
        add_token(conn, subject_id, "Topic " + str(number + 1))

    plan = build_plan(conn, TODAY)
    if len(plan["items"]) != 3:
        return False

    item = refill(conn, plan, TODAY)
    if item is None or item["token"]["title"] != "Topic 4":
        return False
    if "backlog from CN" not in item["reason"]:
        return False

    return refill(conn, plan, TODAY) is None


# Decay: hard +2 days, medium +5, easy +7; the token becomes completed.
def check_decay():
    conn = fresh()
    subject_id = conn.execute(
        "INSERT INTO subjects (name) VALUES ('Maths')").lastrowid
    hard_id = add_token(conn, subject_id, "Hard topic")
    medium_id = add_token(conn, subject_id, "Medium topic")
    easy_id = add_token(conn, subject_id, "Easy topic")

    if decay_days("hard") != 2 or decay_days("medium") != 5 or decay_days("easy") != 7:
        return False

    complete_token(conn, hard_id, "hard", TODAY)
    complete_token(conn, medium_id, "medium", TODAY)
    complete_token(conn, easy_id, "easy", TODAY)

    by_id = {token["id"]: token for token in fetch_tokens(conn)}
    if by_id[hard_id]["next_review"] != (TODAY + timedelta(days=2)).isoformat():
        return False
    if by_id[medium_id]["next_review"] != (TODAY + timedelta(days=5)).isoformat():
        return False
    if by_id[easy_id]["next_review"] != (TODAY + timedelta(days=7)).isoformat():
        return False

    # A hard token completed 2 days ago is due for review today.
    conn2 = fresh()
    subject2 = conn2.execute(
        "INSERT INTO subjects (name) VALUES ('Maths')").lastrowid
    old_id = add_token(conn2, subject2, "Old hard topic", state="completed",
                       difficulty="hard",
                       completed_at=(TODAY - timedelta(days=2)).isoformat(),
                       next_review=TODAY.isoformat())
    plan = build_plan(conn2, TODAY)
    titles = [item["token"]["title"] for item in plan["items"]]
    return "Old hard topic" in titles


# On the sample data, refill after the first two serves the soon-deadline
# token with an honest countdown reason.
def check_soon_reason_via_refill():
    conn = fresh()
    seed_sample(conn, TODAY)
    plan = build_plan(conn, TODAY)
    item = refill(conn, plan, TODAY)
    if item is None:
        return False
    if item["token"]["title"] != "Limits and continuity":
        return False
    return item["reason"] == "deadline in 2 days"


# The Maths exam reports honest pace against the exam-minus-5 buffer.
def check_exam_report():
    conn = fresh()
    seed_sample(conn, TODAY)
    lines = exam_report(conn, TODAY)
    if len(lines) != 1:
        return False
    return ("Maths 1 Midterm in 12 days" in lines[0]
            and "on pace" in lines[0])


# Syllabus progress: taught % (college covered) and completed % per subject.
def check_syllabus_progress():
    conn = fresh()
    seed_sample(conn, TODAY)
    progress = syllabus_progress(conn)
    if len(progress) != 2:
        return False
    maths = list(progress.values())[0]
    physics = list(progress.values())[1]
    # Maths: 3 of 4 covered, 1 of 4 completed.
    if maths["taught_pct"] != 75 or maths["completed_pct"] != 25:
        return False
    # Physics: 3 of 4 covered, 1 of 4 completed.
    return physics["taught_pct"] == 75 and physics["completed_pct"] == 25


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
    print_result("plan bucket order", check_plan_bucket_order())
    print_result("prereq gating", check_prereq_gating())
    print_result("carry-over and flag", check_carryover_and_flag())
    print_result("refill adds one", check_refill_adds_one())
    print_result("decay rules", check_decay())
    print_result("soon reason via refill", check_soon_reason_via_refill())
    print_result("exam report", check_exam_report())
    print_result("syllabus progress", check_syllabus_progress())
