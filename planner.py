import engine
import report
import store
from datetime import date

DB_PATH = "data/planner.sqlite"


# Open the engine's memory, seeding the sample data the first time.
def open_db():
    conn = store.init_db(DB_PATH)
    store.seed_sample(conn)
    return conn


# Show today's plan: capacity level, the served tokens with their reasons,
# the honest exam status lines, and the refill hint. No durations, ever.
def show_todays_plan(conn, today=None):
    plan = engine.build_plan(conn, today)
    names = store.fetch_subject_names(conn)

    print("\nToday's plan — " + plan["capacity"] + " capacity day")
    if not plan["items"]:
        print("All clear — nothing pending right now.")
    for index in range(len(plan["items"])):
        item = plan["items"][index]
        token = item["token"]
        subject = names[token["subject_id"]]
        print(str(index + 1) + ". " + token["title"] + " (" + subject + ")")
        print("   why: " + item["reason"])

    for line in engine.exam_report(conn, today):
        print(line)
    if plan["items"]:
        print("Finished everything? Choose refill for the next topic.")


# Show the college-covered topics still waiting, grouped by subject.
def show_backlog(conn):
    tokens = store.fetch_tokens(conn)
    names = store.fetch_subject_names(conn)

    for subject_id in sorted(names):
        print("\n" + names[subject_id] + ":")
        shown = False
        for token in tokens:
            if (token["subject_id"] == subject_id
                    and token["covered"] == 1
                    and token["state"] == "pending"):
                print("- " + token["title"])
                shown = True
        if not shown:
            print("- No backlog topics")


# Pick a pending topic and record how it felt: easy, medium, or hard.
def mark_done(conn, today=None):
    pending = [token for token in store.fetch_tokens(conn)
               if token["state"] == "pending"]
    if not pending:
        print("Everything is already completed.")
        return

    print("\nPending topics:")
    for index in range(len(pending)):
        print(str(index + 1) + ") " + pending[index]["title"])

    choice = input("Enter the topic number, or press Enter to cancel: ")
    if choice == "":
        print("No changes made.")
        return
    if not choice.isdigit():
        print("Please enter a number from the list.")
        return
    number = int(choice)
    if number < 1 or number > len(pending):
        print("Please enter a number from the list.")
        return

    print("How did it feel? 1) Easy  2) Medium  3) Hard")
    tap = input("Choose 1, 2, or 3: ")
    taps = {"1": "easy", "2": "medium", "3": "hard"}
    if tap not in taps:
        print("Please choose 1, 2, or 3. Nothing was saved.")
        return

    difficulty = taps[tap]
    engine.complete_token(conn, pending[number - 1]["id"], difficulty, today)
    print("Done: " + pending[number - 1]["title"]
          + " — back for review in " + str(engine.decay_days(difficulty))
          + " days.")


# Serve one more topic beyond today's list, if anything is left.
def do_refill(conn, today=None):
    plan = engine.build_plan(conn, today)
    item = engine.refill(conn, plan, today)
    if item is None:
        print("All clear — nothing left in the queue.")
        return
    names = store.fetch_subject_names(conn)
    token = item["token"]
    print("Next up: " + token["title"] + " (" + names[token["subject_id"]] + ")")
    print("why: " + item["reason"])


# Show syllabus progress and honest exam status lines.
def show_exams(conn, today=None):
    names = store.fetch_subject_names(conn)
    progress = engine.syllabus_progress(conn)
    for subject_id in sorted(progress):
        stats = progress[subject_id]
        print(names[subject_id] + ": taught " + str(stats["taught_pct"])
              + "%, completed " + str(stats["completed_pct"]) + "%")

    lines = engine.exam_report(conn, today)
    if not lines:
        print("No exams on the calendar yet.")
    for line in lines:
        print(line)


# --------------------- setup: your own syllabus --------------------------
# Numbered subject picker shared by the topic and exam prompts.
def choose_subject(conn):
    names = store.fetch_subject_names(conn)
    if not names:
        print("No subjects yet — add one with option 8 first.")
        return None
    print("\nYour subjects:")
    ids = sorted(names)
    for index in range(len(ids)):
        print(str(index + 1) + ") " + names[ids[index]])
    choice = input("Pick a subject number: ")
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(ids):
        print("Please enter a number from the list.")
        return None
    return ids[int(choice) - 1]


# 8) Add a subject (e.g. Maths 1, Applied Physics).
def add_subject_flow(conn):
    name = input("Subject name (e.g. Maths 1): ")
    try:
        store.add_subject(conn, name)
        print("Added subject: " + name.strip())
    except ValueError as err:
        print("Not added — " + str(err) + ".")


# 9) Add a topic to a subject. It goes straight into today's queue logic.
def add_topic_flow(conn):
    subject_id = choose_subject(conn)
    if subject_id is None:
        return
    title = input("Topic title (e.g. Limits and continuity): ")
    if not title.strip():
        print("A topic needs a title. Nothing was saved.")
        return

    covered_answer = input(
        "Has college covered it already? (y = yes, n = not yet, Enter = y): ")
    covered = 0 if covered_answer.strip().lower() == "n" else 1

    deadline_answer = input(
        "Deadline YYYY-MM-DD, or press Enter to skip: ").strip()
    deadline = None
    if deadline_answer:
        try:
            deadline = date.fromisoformat(deadline_answer).isoformat()
        except ValueError:
            print("That date isn't YYYY-MM-DD. Nothing was saved.")
            return

    store.add_topic(conn, subject_id, title, covered=covered,
                    deadline=deadline)
    print("Added topic: " + title.strip())


# 10) Add a named exam with its date — the engine plans backward from it.
def add_exam_flow(conn):
    subject_id = choose_subject(conn)
    if subject_id is None:
        return
    name = input("Exam name (e.g. Maths 1 Midterm): ")
    when = input("Date YYYY-MM-DD: ").strip()
    try:
        exam_date = date.fromisoformat(when)
    except ValueError:
        print("Please use the format YYYY-MM-DD. Nothing was saved.")
        return
    store.add_exam(conn, subject_id, name, exam_date)
    print("Added: " + name.strip() + " on " + when
          + " — today's plan counts down to it.")


# Keep showing the menu until the user chooses to quit.
def main():
    conn = open_db()
    while True:
        print("\nSchedule Planner")
        print("1) Show today's plan")
        print("2) Show backlog for each subject")
        print("3) Mark a topic done (with a tap)")
        print("4) Refill — next topic")
        print("5) Exams and syllabus progress")
        print("6) Write today.md")
        print("7) Quit")
        print("8) Add a subject")
        print("9) Add a topic")
        print("10) Add an exam")
        choice = input("Choose an option: ")

        if choice == "1":
            show_todays_plan(conn)
        elif choice == "2":
            show_backlog(conn)
        elif choice == "3":
            mark_done(conn)
        elif choice == "4":
            do_refill(conn)
        elif choice == "5":
            show_exams(conn)
        elif choice == "6":
            path = report.write_today_md(conn)
            print("Wrote " + path)
        elif choice == "7":
            print("Good luck with your studies!")
            break
        elif choice == "8":
            add_subject_flow(conn)
        elif choice == "9":
            add_topic_flow(conn)
        elif choice == "10":
            add_exam_flow(conn)
        else:
            print("Please choose a number from 1 to 10.")


if __name__ == "__main__":
    main()
