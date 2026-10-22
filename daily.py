from datetime import date

import report
import store

DB_PATH = "data/planner.sqlite"


# Build today's plan and write it to today.md. Run by hand, run_daily.sh,
# or the launchd job — same brain as the menu app.
def main():
    conn = store.init_db(DB_PATH)
    store.seed_sample(conn)
    path = report.write_today_md(conn, today=date.today())
    print("Wrote " + path)


if __name__ == "__main__":
    main()
