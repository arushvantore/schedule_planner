from datetime import date, timedelta

# Capacity levels ordered from least to most serving power.
ORDER = ["low", "medium", "high"]

# How many tokens the engine serves on each kind of day.
SERVE_COUNT = {"low": 1, "medium": 2, "high": 3}


# Drop a capacity level by one step (low is the floor).
def downgrade(level):
    index = ORDER.index(level)
    return ORDER[max(index - 1, 0)]


# Classify a day from immutable facts only: class rows, transit rows,
# holidays in the schedule table, and pending deadlines within 2 days.
# Never uses minutes or elapsed time.
def classify_day(conn, today=None):
    if today is None:
        today = date.today()

    day_name = today.strftime("%A")
    kinds = [row["kind"] for row in conn.execute(
        "SELECT kind FROM schedule WHERE day_name = ?", (day_name,))]

    if "holiday" in kinds:
        level = "high"
    else:
        load = kinds.count("class") + (1 if "transit" in kinds else 0)
        if load <= 1:
            level = "high"
        elif load <= 3:
            level = "medium"
        else:
            level = "low"

    # Active deadlines steal energy: one-level downgrade.
    deadline_limit = (today + timedelta(days=2)).isoformat()
    soon = conn.execute(
        """SELECT COUNT(*) AS n FROM tokens
           WHERE state = 'pending' AND deadline IS NOT NULL AND deadline <= ?""",
        (deadline_limit,),
    ).fetchone()["n"]
    if soon:
        level = downgrade(level)

    return level
