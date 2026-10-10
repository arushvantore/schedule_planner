from contextlib import redirect_stdout
from datetime import date
from io import StringIO

from planner import show_backlog, show_todays_plan
from sample_data import topics


# Check the starter list has two subjects with four correctly shaped topics each.
def check_starter_data():
    subjects = []
    for topic in topics:
        if topic["subject"] not in subjects:
            subjects.append(topic["subject"])

    if len(subjects) != 2:
        return False

    for subject in subjects:
        subject_topics = []
        for topic in topics:
            if topic["subject"] == subject:
                subject_topics.append(topic)
        if len(subject_topics) != 4:
            return False

    required_fields = [
        "subject",
        "name",
        "covered_in_college",
        "studied",
        "minutes_needed",
        "deadline",
    ]
    for topic in topics:
        for field in required_fields:
            if field not in topic:
                return False
    return True


# Check backlog output includes only college-covered topics that are not studied.
def check_backlog():
    output = StringIO()
    with redirect_stdout(output):
        show_backlog(topics)

    result = output.getvalue()
    return (
        "Limits and continuity" in result
        and "Differentiation" in result
        and "Vectors" in result
        and "Integration" not in result
        and "Matrices" not in result
    )


# Check the plan puts a deadline topic before backlog and explains each reason.
def check_todays_plan():
    test_topics = [
        {
            "subject": "Maths 1",
            "name": "Deadline topic",
            "covered_in_college": False,
            "studied": False,
            "minutes_needed": 30,
            "deadline": date.today().isoformat(),
        },
        {
            "subject": "Applied Physics",
            "name": "Backlog topic",
            "covered_in_college": True,
            "studied": False,
            "minutes_needed": 40,
            "deadline": None,
        },
    ]
    output = StringIO()
    with redirect_stdout(output):
        show_todays_plan(test_topics)

    result = output.getvalue()
    deadline_position = result.find("Deadline topic")
    backlog_position = result.find("Backlog topic")
    return (
        deadline_position >= 0
        and backlog_position > deadline_position
        and "deadline in 0 days" in result
        and "backlog from Applied Physics" in result
    )


# Check a studied topic with a current deadline does not appear in the plan.
def check_studied_topics_are_excluded_from_plan():
    studied_deadline_topic = {
        "subject": "Maths 1",
        "name": "Already studied deadline topic",
        "covered_in_college": True,
        "studied": True,
        "minutes_needed": 30,
        "deadline": date.today().isoformat(),
    }
    output = StringIO()
    with redirect_stdout(output):
        show_todays_plan([studied_deadline_topic])

    return "Already studied deadline topic" not in output.getvalue()


# Print a clear result so a beginner can see whether each check worked.
def print_result(name, passed):
    if passed:
        print("PASS: " + name)
    else:
        print("FAIL: " + name)


if __name__ == "__main__":
    print_result("starter data", check_starter_data())
    print_result("backlog display", check_backlog())
    print_result("today's plan", check_todays_plan())
    print_result(
        "studied topics are excluded from plan",
        check_studied_topics_are_excluded_from_plan(),
    )
