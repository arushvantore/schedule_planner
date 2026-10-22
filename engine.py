from datetime import date, timedelta

from capacity import SERVE_COUNT, classify_day
from store import fetch_subject_names, fetch_tokens, mark_completed

# How long until a token comes back for review, by tap feedback.
REVIEW_DELAY = {"easy": 7, "medium": 5, "hard": 2}


# Days until review for a difficulty tap (default: medium pace).
def decay_days(difficulty):
    return REVIEW_DELAY.get(difficulty, 5)


# Mark a token completed and set its next review date from the tap.
def complete_token(conn, token_id, difficulty, today=None):
    if today is None:
        today = date.today()
    next_review = today + timedelta(days=decay_days(difficulty))
    mark_completed(conn, token_id, difficulty, today, next_review)
    return next_review


def _parse(day_text):
    if day_text is None:
        return None
    return date.fromisoformat(day_text)


# A token can be served if it is pending with its prerequisite completed,
# or completed but due for review.
def is_eligible(token, by_id, today):
    if token["state"] == "pending":
        prereq_id = token["prereq_id"]
        if prereq_id is not None and by_id[prereq_id]["state"] != "completed":
            return False
        return True
    return _is_due_review(token, today)


def _is_due_review(token, today):
    if token["state"] != "completed":
        return False
    if token["difficulty"] is None or token["next_review"] is None:
        return False
    return _parse(token["next_review"]) <= today


def _reason_carry(token, today):
    origin = _parse(token["origin_date"])
    days = (today - origin).days
    text = "carried over from " + token["origin_date"]
    if days >= 3:
        text += " — " + str(days) + " days postponed, do this first"
    return text


# Fill `limit` slots from the ordered buckets. First match wins.
def _collect(conn, today, limit):
    tokens = fetch_tokens(conn)
    by_id = {token["id"]: token for token in tokens}
    names = fetch_subject_names(conn)

    candidates = [token for token in tokens if is_eligible(token, by_id, today)]

    carry = [token for token in candidates
             if token["state"] == "pending" and token["origin_date"]
             and _parse(token["origin_date"]) < today]
    overdue = [token for token in candidates
               if token["state"] == "pending" and token["deadline"]
               and _parse(token["deadline"]) < today]
    review = [token for token in candidates if _is_due_review(token, today)]
    soon = [token for token in candidates
            if token["state"] == "pending" and token["deadline"]
            and today <= _parse(token["deadline"]) <= today + timedelta(days=3)]
    backlog = [token for token in candidates
               if token["state"] == "pending" and token["covered"] == 1]

    items = []
    chosen = set()

    def take(bucket, reason_fn):
        for token in bucket:
            if len(items) >= limit:
                return
            if token["id"] in chosen:
                continue
            chosen.add(token["id"])
            items.append({"token": token, "reason": reason_fn(token)})

    take(carry, lambda token: _reason_carry(token, today))
    take(overdue, lambda token: "deadline passed on " + token["deadline"])
    take(review, lambda token: "review due (was " + token["difficulty"] + " last time)")
    take(soon, lambda token: "deadline in "
         + str((_parse(token["deadline"]) - today).days) + " days")
    take(backlog, lambda token: "backlog from " + names.get(token["subject_id"], "?"))

    return items


# Build today's plan: capacity level + up to that many tokens with reasons.
def build_plan(conn, today=None):
    if today is None:
        today = date.today()
    capacity = classify_day(conn, today)
    limit = SERVE_COUNT[capacity]
    items = _collect(conn, today, limit)
    return {"capacity": capacity, "served": limit, "items": items}


# One refill tap: the next eligible token beyond what the plan already
# served. None when the queue is empty. Appends the item to the plan.
def refill(conn, plan, today=None):
    if today is None:
        today = date.today()
    served = {item["token"]["id"] for item in plan["items"]}
    items = _collect(conn, today, plan["served"] + 1)
    for item in items:
        if item["token"]["id"] not in served:
            plan["items"].append(item)
            return item
    return None


# Honest per-exam lines: covered topics vs the exam-minus-5 buffer.
def exam_report(conn, today=None):
    if today is None:
        today = date.today()
    tokens = fetch_tokens(conn)
    exams = conn.execute(
        "SELECT e.*, s.name AS subject_name FROM exams e"
        " JOIN subjects s ON s.id = e.subject_id ORDER BY e.exam_date"
    ).fetchall()

    lines = []
    for row in exams:
        exam = dict(row)
        exam_date = _parse(exam["exam_date"])
        days_left = (exam_date - today).days
        finish_by = exam_date - timedelta(days=5)
        days_to_buffer = (finish_by - today).days
        subject_tokens = [token for token in tokens
                          if token["subject_id"] == exam["subject_id"]
                          and token["covered"] == 1]
        remaining = [token for token in subject_tokens
                     if token["state"] == "pending"]

        if not subject_tokens:
            status = "no topics mapped yet"
        elif not remaining:
            status = "all covered topics complete"
        elif days_to_buffer < 0:
            status = ("behind — " + str(len(remaining))
                      + " topics left and the buffer has passed")
        elif len(remaining) <= days_to_buffer:
            status = "on pace"
        else:
            status = ("behind — " + str(len(remaining)) + " topics with "
                      + str(days_to_buffer) + " days to the buffer")

        lines.append(exam["name"] + " in " + str(days_left)
                     + " days: " + status)
    return lines


# Per-subject syllabus progress: taught % (college covered) and
# completed % (state = completed). Plain honest numbers, no durations.
def syllabus_progress(conn):
    tokens = fetch_tokens(conn)
    names = fetch_subject_names(conn)
    result = {}
    for subject_id, name in names.items():
        subject_tokens = [token for token in tokens
                          if token["subject_id"] == subject_id]
        total = len(subject_tokens)
        if total == 0:
            result[subject_id] = {"taught_pct": 0, "completed_pct": 0}
            continue
        completed = len([token for token in subject_tokens
                         if token["state"] == "completed"])
        taught = len([token for token in subject_tokens
                      if token["covered"] == 1])
        result[subject_id] = {
            "taught_pct": round(taught * 100 / total),
            "completed_pct": round(completed * 100 / total),
        }
    return result
