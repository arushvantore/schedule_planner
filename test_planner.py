from contextlib import redirect_stdout
from datetime import date
from io import StringIO

import planner
import store
from engine import complete_token

TODAY = date(2026, 10, 20)


# Fresh in-memory database with the sample data seeded for a fixed day.
def fresh():
    conn = store.init_db(":memory:")
    store.seed_sample(conn, TODAY)
    return conn


# The plan must show capacity, reasons, and never the word "minutes".
def check_plan_has_no_minutes():
    output = StringIO()
    with redirect_stdout(output):
        planner.show_todays_plan(fresh(), TODAY)
    result = output.getvalue()
    return ("capacity" in result
            and "deadline passed on" in result
            and "review due" in result
            and "minutes" not in result.lower())


# The backlog lists college-covered pending topics only.
def check_backlog_content():
    output = StringIO()
    with redirect_stdout(output):
        planner.show_backlog(fresh())
    result = output.getvalue()
    return ("Differentiation" in result
            and "Vectors" in result
            and "Integration" not in result
            and "Matrices" not in result)


# After completing the overdue token it disappears from the plan.
def check_completed_token_leaves_plan():
    conn = fresh()
    kinematics = [token for token in store.fetch_tokens(conn)
                  if token["title"] == "Kinematics"][0]
    complete_token(conn, kinematics["id"], "hard", TODAY)

    output = StringIO()
    with redirect_stdout(output):
        planner.show_todays_plan(conn, TODAY)
    return "deadline passed" not in output.getvalue()


# Refill surfaces the soon-deadline topic with an honest countdown.
def check_refill_output():
    output = StringIO()
    with redirect_stdout(output):
        planner.do_refill(fresh(), TODAY)
    result = output.getvalue()
    return ("Limits and continuity" in result
            and "deadline in 2 days" in result)


# Exams view shows syllabus percentages and the exam status line.
def check_exams_view():
    output = StringIO()
    with redirect_stdout(output):
        planner.show_exams(fresh(), TODAY)
    result = output.getvalue()
    return ("taught 75%" in result
            and "completed 25%" in result
            and "Maths 1 Midterm in 12 days" in result)


# Print a clear result so a beginner can see whether each check worked.
def print_result(name, passed):
    if passed:
        print("PASS: " + name)
    else:
        print("FAIL: " + name)


if __name__ == "__main__":
    print_result("plan has no minutes", check_plan_has_no_minutes())
    print_result("backlog content", check_backlog_content())
    print_result("completed token leaves plan", check_completed_token_leaves_plan())
    print_result("refill output", check_refill_output())
    print_result("exams view", check_exams_view())
