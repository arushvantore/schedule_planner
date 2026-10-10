# Planner

A personal study planner that reads my college syllabus progress
and shows what to study today and tomorrow.

## How it works

1. Run the program from this folder by typing `python3 planner.py`.
2. The first run creates `progress.json` with the starter topics.
3. Choose a menu option to see your backlog, mark a topic as studied, or
   see today's study plan.
4. When you mark a topic as studied, the planner saves that change in
   `progress.json` so it is still saved the next time you run the program.
5. The plan tries deadline topics due today or within the next two days
   first, then adds college-covered backlog topics in their listed order.
   It uses up to 150 minutes for study, leaving a 30-minute buffer from
   the 180-minute daily default.