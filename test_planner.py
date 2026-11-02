from contextlib import redirect_stdout
from datetime import date
from io import StringIO
import builtins

import planner
import store
from engine import complete_token

TODAY = date(2026, 10, 20)


# Run a menu flow with scripted answers instead of a real keyboard.
def with_answers(answers, fn, *args):
    queue = list(answers)
    original = builtins.input
    builtins.input = lambda prompt="": queue.pop(0)
    output = StringIO()
    try:
        with redirect_stdout(output):
            fn(*args)
    finally:
        builtins.input = original
    return output.getvalue()


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


# Setup menu: a new subject and topic appear in the backlog.
def check_setup_adds_subject_and_topic():
    conn = fresh()
    added_subject = with_answers(["Chemistry"], planner.add_subject_flow, conn)
    added_topic = with_answers(["1", "Organic chemistry", "y", ""],
                               planner.add_topic_flow, conn)
    output = StringIO()
    with redirect_stdout(output):
        planner.show_backlog(conn)
    backlog = output.getvalue()
    return ("Added subject: Chemistry" in added_subject
            and "Added topic: Organic chemistry" in added_topic
            and "Chemistry:" in backlog
            and "- Organic chemistry" in backlog)


# Setup menu: a new exam gets a real countdown on the exams view.
def check_setup_adds_exam_countdown():
    conn = fresh()
    added = with_answers(["1", "Chemistry Final", "2026-10-30"],
                         planner.add_exam_flow, conn)
    output = StringIO()
    with redirect_stdout(output):
        planner.show_exams(conn, TODAY)
    exams = output.getvalue()
    return ("today's plan counts down to it" in added
            and "Chemistry Final in 10 days" in exams)


# Setup menu: duplicate subjects and bad dates are refused, nothing saved.
def check_setup_rejects_bad_input():
    conn = fresh()
    duplicate = with_answers(["Maths 1"], planner.add_subject_flow, conn)
    bad_date = with_answers(["1", "Chemistry Final", "tomorrow"],
                            planner.add_exam_flow, conn)
    output = StringIO()
    with redirect_stdout(output):
        planner.show_exams(conn, TODAY)
    exams = output.getvalue()
    return ("you already have a subject called Maths 1" in duplicate
            and "Nothing was saved" in bad_date
            and "Chemistry Final" not in exams)


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
    print_result("setup adds subject and topic",
                 check_setup_adds_subject_and_topic())
    print_result("setup adds exam countdown",
                 check_setup_adds_exam_countdown())
    print_result("setup rejects bad input",
                 check_setup_rejects_bad_input())
