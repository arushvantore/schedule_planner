from datetime import date

import engine
import store

# Write today's plan as plain markdown. No durations anywhere.
def write_today_md(conn, path="today.md", today=None):
    if today is None:
        today = date.today()
    plan = engine.build_plan(conn, today)
    names = store.fetch_subject_names(conn)

    lines = ["# Today", "",
             "Capacity: " + plan["capacity"], ""]

    if not plan["items"]:
        lines.append("All clear — nothing pending right now.")
    for index in range(len(plan["items"])):
        item = plan["items"][index]
        token = item["token"]
        subject = names[token["subject_id"]]
        lines.append(str(index + 1) + ". " + token["title"]
                     + " (" + subject + ")")
        lines.append("   why: " + item["reason"])

    exam_lines = engine.exam_report(conn, today)
    if exam_lines:
        lines.append("")
        for exam_line in exam_lines:
            lines.append(exam_line)

    if plan["items"]:
        lines.append("")
        lines.append("Finished everything? Refill for the next topic.")

    with open(path, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    return path
