"""Local-only web interface for the Schedule Planner engine."""
from datetime import date
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import engine
import store
import auth_store
import problem_export

ROOT = Path(__file__).resolve().parent
WEB_PATH = ROOT / "web"

app = FastAPI(title="Schedule Planner", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_PATH), name="static")


class SubjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TopicInput(BaseModel):
    subject_id: int
    title: str = Field(min_length=1, max_length=200)
    covered: bool = True
    deadline: date | None = None


class ExamInput(BaseModel):
    subject_id: int
    name: str = Field(min_length=1, max_length=120)
    exam_date: date


class AssignmentInput(BaseModel):
    subject_id: int
    title: str = Field(min_length=1, max_length=200)
    due_date: date


class RevisionInput(BaseModel):
    exam_id: int
    token_id: int
    pass_number: Literal[1, 2]


class CompletionInput(BaseModel):
    difficulty: Literal["easy", "medium", "hard"]


class RefillInput(BaseModel):
    served_ids: list[int] = Field(default_factory=list, max_length=500)


class ScheduleInput(BaseModel):
    day_name: Literal[
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]
    kind: Literal["class", "transit", "holiday"]
    detail: str = Field(default="", max_length=200)


def current_user(request: Request):
    user = auth_store.session_user(request.cookies.get(auth_store.COOKIE_NAME))
    if user is None:
        raise HTTPException(401, "Sign in to access your planner.")
    return user


def open_db(request: Request):
    user = current_user(request)
    conn = store.init_db(str(auth_store.user_db_path(user["id"])))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def check_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Request origin did not match this planner.")


class AccountInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def subject_list(conn):
    return [
        {"id": subject_id, "name": name}
        for subject_id, name in store.fetch_subject_names(conn).items()
    ]


def dashboard_data(conn):
    plan = engine.build_plan(conn)
    names = store.fetch_subject_names(conn)
    items = []
    for item in plan["items"]:
        token = item["token"]
        items.append({
            "id": token["id"],
            "title": token["title"],
            "subject": names.get(token["subject_id"], "Unknown subject"),
            "reason": item["reason"],
        })
    progress = engine.syllabus_progress(conn)
    return {
        "today": date.today().isoformat(),
        "capacity": plan["capacity"],
        "items": items,
        "exams": engine.exam_report(conn),
        "assignments": store.fetch_assignments(conn, pending_only=True),
        "revisions": engine.revision_tasks(conn),
        "subjects": subject_list(conn),
        "progress": [
            {
                "subject": names.get(subject_id, "Unknown subject"),
                **values,
            }
            for subject_id, values in progress.items()
        ],
    }


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_PATH / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/signup", status_code=201)
def signup(payload: AccountInput, request: Request):
    check_origin(request)
    try:
        user = auth_store.create_account(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(409 if "already exists" in str(exc) else 422, str(exc)) from exc
    token, expires = auth_store.new_session(user["id"])
    response = JSONResponse(user)
    response.set_cookie(
        auth_store.COOKIE_NAME, token, httponly=True, secure=os.environ.get("PLANNER_COOKIE_SECURE") == "1",
        samesite="strict", expires=expires, path="/",
    )
    return response


@app.post("/api/auth/login")
def login(payload: AccountInput, request: Request):
    check_origin(request)
    user = auth_store.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(401, "Email or password is incorrect.")
    token, expires = auth_store.new_session(user["id"])
    response = JSONResponse(user)
    response.set_cookie(
        auth_store.COOKIE_NAME, token, httponly=True, secure=os.environ.get("PLANNER_COOKIE_SECURE") == "1",
        samesite="strict", expires=expires, path="/",
    )
    return response


@app.post("/api/auth/logout")
def logout(request: Request):
    check_origin(request)
    auth_store.revoke_session(request.cookies.get(auth_store.COOKIE_NAME))
    response = JSONResponse({"status": "signed out"})
    response.delete_cookie(auth_store.COOKIE_NAME, path="/", httponly=True, samesite="strict")
    return response


@app.get("/api/auth/me")
def me(request: Request):
    return current_user(request)


@app.get("/api/sources")
def sources(request: Request):
    conn = open_db(request)
    try:
        rows = conn.execute(
            """SELECT id, provider, source_name, external_ref, status,
                      last_attempt_at, last_success_at, last_error
               FROM source_connections ORDER BY provider, source_name"""
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.get("/api/today")
def today(request: Request):
    conn = open_db(request)
    try:
        return dashboard_data(conn)
    finally:
        conn.close()


@app.get("/api/exports/python-problems.pdf")
def export_python_problems(request: Request):
    conn = open_db(request)
    try:
        problems = problem_export.collect_python_problems(conn)
        if not problems:
            raise HTTPException(404, "No synced Python problem statements are available yet.")
        pdf = problem_export.make_python_problems_pdf(problems)
        return StreamingResponse(
            iter([pdf]), media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="Python_Problems.pdf"'},
        )
    finally:
        conn.close()


@app.post("/api/chat")
def chat(payload: ChatInput, request: Request):
    """Answer basic planner intents using only this account's planner data."""
    message = payload.message.strip()
    normalized = message.casefold()
    conn = open_db(request)
    try:
        if "python" in normalized and any(term in normalized for term in ("problem", "question", "exercise")):
            problems = problem_export.collect_python_problems(conn)
            if not problems:
                return {"reply": "I haven’t synced any Python problem statements from your course sources yet. I won’t fill the PDF with guesses. Once the Newton and selected Slack sources are connected, ask me again and I’ll collect the problems by subject and chapter.", "download_url": None}
            return {
                "reply": f"I found {len(problems)} Python problems, organized by subject and chapter. Here is the combined PDF.",
                "download_url": "/api/exports/python-problems.pdf",
            }
        data = dashboard_data(conn)
        if any(term in normalized for term in ("i finished", "i completed", "done with", "i studied")):
            tokens = store.fetch_tokens(conn)
            matched = next((token for token in sorted(tokens, key=lambda item: len(item["title"]), reverse=True)
                            if token["state"] == "pending" and token["title"].casefold() in normalized), None)
            if matched is None:
                reply = "I couldn’t match that to one of your pending topics yet. Your course data will appear here after source connections are added."
            else:
                next_review = engine.complete_token(conn, matched["id"], "medium")
                reply = f"Marked {matched['title']} complete. I’ll bring it back for review on {next_review.isoformat()}."
        elif any(term in normalized for term in ("what should", "what do i", "today", "study today", "plan for today")):
            if not data["items"]:
                reply = "I don’t have your course topics yet, so I can’t build a real study plan. Automatic Newton School, college, and Slack connections are still being built."
            else:
                reply = "Here’s what to study today:\n" + "\n".join(
                    f"• {item['title']} — {item['subject']} ({item['reason']})"
                    for item in data["items"]
                )
                reply += f"\n\nToday is a {data['capacity'].lower()} capacity day."
        elif any(term in normalized for term in ("assignment", "deadline", "due next")):
            assignments = data["assignments"]
            reply = ("Upcoming assignments:\n" + "\n".join(
                f"• {item['title']} — {item['subject']}, due {item['due_date']}"
                for item in assignments
            )) if assignments else "I don’t have assignment deadlines in your planner yet. Automatic source syncing is not connected yet."
        elif any(term in normalized for term in ("exam", "test", "revision")):
            exams = data["exams"]
            revisions = data["revisions"]
            parts = []
            if exams:
                parts.append("Exam outlook:\n" + "\n".join("• " + line for line in exams))
            if revisions:
                parts.append("Revision due:\n" + "\n".join(
                    f"• {item['topic']} — {item['subject']}, pass {item['pass_number']} for {item['exam']}"
                    for item in revisions
                ))
            reply = "\n\n".join(parts) or "I don’t have exam dates in your planner yet. Automatic college and course portal connections are still being built."
        elif any(term in normalized for term in ("more", "another", "finished", "done")):
            plan = engine.build_plan(conn)
            candidate = engine.refill(conn, plan)
            if candidate is None:
                reply = "There aren’t more eligible topics in your planner right now. Once your course sources are connected, I can use the full syllabus and progress to find the next task."
            else:
                token = candidate["token"]
                subject = store.fetch_subject_names(conn).get(token["subject_id"], "Unknown subject")
                reply = f"Do this next: {token['title']} — {subject}. {candidate['reason']}."
        elif any(term in normalized for term in ("less", "lighter", "too much", "reduce")):
            reply = "I can make lighter plans once your timetable and availability are connected. Those automatic college schedule connections are not in place yet."
        else:
            reply = "I can answer from the planner’s current study plan, exams, assignments, and revision data. Newton School, college, and Slack connections and the AI course tutor are still being built, so I can’t answer course questions from those sources yet."
        return {"reply": reply}
    finally:
        conn.close()


@app.post("/api/subjects", status_code=201)
def create_subject(payload: SubjectInput, request: Request):
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, "Enter a subject name.")
    conn = open_db(request)
    try:
        subject_id = store.add_subject(conn, name)
        return {"id": subject_id, "name": name}
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    finally:
        conn.close()


@app.post("/api/topics", status_code=201)
def create_topic(payload: TopicInput, request: Request):
    title = payload.title.strip()
    if not title:
        raise HTTPException(422, "Enter a topic title.")
    conn = open_db(request)
    try:
        if payload.subject_id not in store.fetch_subject_names(conn):
            raise HTTPException(404, "Subject not found.")
        topic_id = store.add_topic(
            conn,
            payload.subject_id,
            title,
            covered=int(payload.covered),
            deadline=payload.deadline.isoformat() if payload.deadline else None,
        )
        return {"id": topic_id, "title": title}
    finally:
        conn.close()


@app.post("/api/exams", status_code=201)
def create_exam(payload: ExamInput, request: Request):
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, "Enter an exam name.")
    conn = open_db(request)
    try:
        if payload.subject_id not in store.fetch_subject_names(conn):
            raise HTTPException(404, "Subject not found.")
        exam_id = store.add_exam(
            conn, payload.subject_id, name, payload.exam_date
        )
        return {"id": exam_id, "name": name}
    finally:
        conn.close()


@app.post("/api/assignments", status_code=201)
def create_assignment(payload: AssignmentInput, request: Request):
    title = payload.title.strip()
    if not title:
        raise HTTPException(422, "Enter an assignment title.")
    conn = open_db(request)
    try:
        if payload.subject_id not in store.fetch_subject_names(conn):
            raise HTTPException(404, "Subject not found.")
        assignment_id = store.add_assignment(
            conn, payload.subject_id, title, payload.due_date
        )
        return {"id": assignment_id, "title": title}
    finally:
        conn.close()


@app.post("/api/assignments/{assignment_id}/complete")
def finish_assignment(assignment_id: int, request: Request):
    conn = open_db(request)
    try:
        if not store.complete_assignment(conn, assignment_id):
            raise HTTPException(404, "Pending assignment not found.")
        return {"id": assignment_id, "state": "completed"}
    finally:
        conn.close()


@app.post("/api/revisions/complete")
def finish_revision(payload: RevisionInput, request: Request):
    conn = open_db(request)
    try:
        exists = conn.execute(
            """SELECT 1 FROM exams e JOIN tokens t
               ON t.subject_id = e.subject_id
               WHERE e.id = ? AND t.id = ? AND t.covered = 1""",
            (payload.exam_id, payload.token_id),
        ).fetchone()
        if exists is None:
            raise HTTPException(404, "Exam topic not found.")
        store.complete_revision(
            conn, payload.exam_id, payload.token_id, payload.pass_number
        )
        return {"exam_id": payload.exam_id, "token_id": payload.token_id,
                "pass_number": payload.pass_number, "state": "completed"}
    finally:
        conn.close()


@app.post("/api/topics/{topic_id}/complete")
def complete_topic(topic_id: int, payload: CompletionInput, request: Request):
    conn = open_db(request)
    try:
        exists = conn.execute(
            "SELECT id FROM tokens WHERE id = ? AND state = 'pending'",
            (topic_id,),
        ).fetchone()
        if exists is None:
            raise HTTPException(404, "Pending topic not found.")
        next_review = engine.complete_token(
            conn, topic_id, payload.difficulty
        )
        return {"id": topic_id, "next_review": next_review.isoformat()}
    finally:
        conn.close()


@app.post("/api/refill")
def refill_plan(payload: RefillInput, request: Request):
    conn = open_db(request)
    try:
        plan = engine.build_plan(conn)
        already_shown = set(payload.served_ids)
        item = None
        while True:
            candidate = engine.refill(conn, plan)
            if candidate is None:
                break
            if candidate["token"]["id"] not in already_shown:
                item = candidate
                break
        if item is None:
            return {"item": None}
        token = item["token"]
        names = store.fetch_subject_names(conn)
        return {"item": {
            "id": token["id"],
            "title": token["title"],
            "subject": names.get(token["subject_id"], "Unknown subject"),
            "reason": item["reason"],
        }}
    finally:
        conn.close()


@app.get("/api/schedule")
def get_schedule(request: Request):
    conn = open_db(request)
    try:
        rows = conn.execute(
            "SELECT id, day_name, kind, detail FROM schedule ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.post("/api/schedule", status_code=201)
def add_schedule(payload: ScheduleInput, request: Request):
    conn = open_db(request)
    try:
        cursor = conn.execute(
            "INSERT INTO schedule (day_name, kind, detail) VALUES (?, ?, ?)",
            (payload.day_name, payload.kind, payload.detail.strip()),
        )
        conn.commit()
        return {"id": cursor.lastrowid}
    finally:
        conn.close()


@app.delete("/api/schedule/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, request: Request):
    conn = open_db(request)
    try:
        cursor = conn.execute(
            "DELETE FROM schedule WHERE id = ?", (schedule_id,)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Schedule item not found.")
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
