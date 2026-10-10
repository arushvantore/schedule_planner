import json
from datetime import date, timedelta

from sample_data import topics as starter_topics


# Load saved progress, or create the progress file with the starter topics.
def load_progress():
    try:
        progress_file = open("progress.json", "r")
    except FileNotFoundError:
        save_progress(starter_topics)
        return starter_topics

    with progress_file:
        return json.load(progress_file)


# Save the current topics so study progress is kept between program runs.
def save_progress(topics):
    progress_file = open("progress.json", "w")
    with progress_file:
        json.dump(topics, progress_file, indent=4)


# Show the college-covered topics that are still waiting to be studied.
def show_backlog(topics):
    subjects = []
    for topic in topics:
        if topic["subject"] not in subjects:
            subjects.append(topic["subject"])

    for subject in subjects:
        print("\n" + subject + ":")
        found_topic = False
        for topic in topics:
            if (
                topic["subject"] == subject
                and topic["covered_in_college"]
                and not topic["studied"]
            ):
                print("- " + topic["name"] + " (" + str(topic["minutes_needed"]) + " minutes)")
                found_topic = True
        if not found_topic:
            print("- No backlog topics")


# Let the user choose a topic and save it as studied.
def mark_topic_studied(topics):
    available_topics = []
    for topic in topics:
        if topic["covered_in_college"] and not topic["studied"]:
            available_topics.append(topic)

    if not available_topics:
        print("All topics are already marked as studied.")
        return

    print("\nTopics not yet studied:")
    for index in range(len(available_topics)):
        topic = available_topics[index]
        print(str(index + 1) + ") " + topic["subject"] + " - " + topic["name"])

    choice = input("Enter the topic number, or press Enter to cancel: ")
    if choice == "":
        print("No changes made.")
        return

    if not choice.isdigit():
        print("Please enter a number from the list.")
        return

    topic_number = int(choice)
    if topic_number < 1 or topic_number > len(available_topics):
        print("Please enter a number from the list.")
        return

    selected_topic = available_topics[topic_number - 1]
    selected_topic["studied"] = True
    save_progress(topics)
    print("Marked as studied: " + selected_topic["name"])


# Build today's plan by adding near deadlines first, then backlog in file order.
def show_todays_plan(topics):
    today = date.today()
    last_deadline_day = today + timedelta(days=2)
    minutes_left = 180 - 30
    planned_topics = []
    plan_reasons = []

    for topic in topics:
        if topic["studied"]:
            continue
        if topic["deadline"] is not None:
            deadline = date.fromisoformat(topic["deadline"])
            if today <= deadline <= last_deadline_day:
                if topic["minutes_needed"] <= minutes_left:
                    planned_topics.append(topic)
                    plan_reasons.append(
                        "deadline in " + str((deadline - today).days) + " days"
                    )
                    minutes_left = minutes_left - topic["minutes_needed"]

    for topic in topics:
        if topic["studied"]:
            continue
        is_backlog = topic["covered_in_college"]
        already_planned = topic in planned_topics
        if is_backlog and not already_planned:
            if topic["minutes_needed"] <= minutes_left:
                planned_topics.append(topic)
                plan_reasons.append("backlog from " + topic["subject"])
                minutes_left = minutes_left - topic["minutes_needed"]

    if not planned_topics:
        print("No topics fit into today's study time.")
        return

    print("\nToday's plan (up to 150 minutes, with a 30-minute buffer):")
    for index in range(len(planned_topics)):
        topic = planned_topics[index]
        print(
            "- "
            + topic["name"]
            + " ("
            + str(topic["minutes_needed"])
            + " minutes) — "
            + plan_reasons[index]
        )
    print("Study time left: " + str(minutes_left) + " minutes")


# Keep showing the menu until the user chooses to quit.
def main():
    topics = load_progress()
    while True:
        print("\nStudy Planner")
        print("1) Show backlog for each subject")
        print("2) Mark a topic as studied")
        print("3) Show today's plan")
        print("4) Quit")
        choice = input("Choose an option: ")

        if choice == "1":
            show_backlog(topics)
        elif choice == "2":
            mark_topic_studied(topics)
        elif choice == "3":
            show_todays_plan(topics)
        elif choice == "4":
            print("Good luck with your studies!")
            break
        else:
            print("Please choose 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
