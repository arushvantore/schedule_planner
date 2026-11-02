"""Source-backed Python problem records for the first Newton problem book."""

PROBLEMS = [
    {
        "chapter": "Python Function, Scope, Variable Scopes",
        "title": "Check if a Number is a Palindrome (Function)",
        "difficulty": "Medium",
        "statement": (
            "Given a positive integer N, determine whether it is a palindrome. "
            "Note: A number is called a palindrome if it reads the same backwards and forwards."
        ),
    },
    {
        "chapter": "Python Function, Scope, Variable Scopes",
        "title": "Prime Numbers upto N (Function)",
        "difficulty": "Medium",
        "statement": (
            "Given an integer N, the task is to print all the prime numbers from 1 to N in ascending order. "
            "Note: Each prime number should be printed on the same line, separated by a space."
        ),
    },
    {
        "chapter": "Python Function, Scope, Variable Scopes",
        "title": "Find the Smallest and Largest Digit in a Number",
        "difficulty": "Medium",
        "statement": (
            "You are given a positive integer N. Your task is to find the smallest and largest digit in the given number."
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - Lecture Assignments",
        "title": "Movie Mania",
        "difficulty": "Easy",
        "statement": (
            "Four movies were released: Spiderman, Superman, Batman, and Aquaman in four distinct years "
            "given as four space-separated integers: year1, year2, year3, and year4 respectively. "
            "Spiderman was released in year1, Superman in year2, Batman in year3, and Aquaman in year4. "
            "Print the name of the movie that was released earliest of the four. Refer to the input section, "
            "output section, and example test cases. Use of built-in mathematical functions is strictly prohibited."
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - Lecture Assignments",
        "title": "Will Ramandeep Sir Fly? - 2",
        "difficulty": "Easy",
        "statement": (
            "Ramandeep Sir is known for his highly selective flying decisions after past flight troubles. "
            "He follows these rules: (1) If the trip is international, he will not fly, regardless of other "
            "conditions. (2) If the trip is domestic and the flight duration is less than or equal to 1.5 hours, "
            "he will fly. (3) If the trip is domestic and the duration is more than 1.5 hours, he will not fly "
            "if his seat is a middle seat or the airline is IngidoX. In all other cases, he will fly. Determine "
            "whether Ramandeep Sir will fly given the flight details."
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - Lecture Assignments",
        "title": "NST Bus Route Optimization",
        "difficulty": "Easy",
        "statement": (
            "A bus driver at NST Campus must pick up students from Hostel 1 and Hostel 2, then return to campus. "
            "Roads connect campus to Hostel 1 with length d1, campus to Hostel 2 with length d2, and Hostel 1 "
            "to Hostel 2 with length d3. The driver may travel on any road any number of times and in either "
            "direction. Find the minimum total distance for a route that starts at campus, visits both hostels, "
            "and returns to campus. Refer to the image on the source page for further clarity."
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - Lecture Assignments",
        "title": "Museum Ticket Booking System",
        "difficulty": "Easy",
        "statement": (
            "Implement calculateTicketPrice for a museum ticket booking system. The base price is $12. "
            "Visitors under 12 receive a $5 discount. Weekend visits add a $3 surcharge. A student card "
            "gives an additional $2 discount. The function accepts age (number), isWeekend (boolean), and "
            "hasStudentCard (boolean), and returns the final price after applicable discounts and surcharges."
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - Lecture Assignments",
        "title": "Greater of Four",
        "difficulty": "Easy",
        "statement": (
            "Given four integers a, b, c, and d, use the provided greater(x, y) function, which returns the "
            "greater of its two inputs, to find the greatest of the four numbers. You must use greater(); "
            "do not compare all four numbers directly."
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - In-class Quiz",
        "title": "Question 1 - Incorrect logical-operator syntax",
        "difficulty": "Quiz",
        "statement": (
            "Which of the following is the incorrect syntax for using logical operators in an if statement? "
            "A. if condition1 & condition2:  B. if condition1 or condition2:  "
            "C. if (condition1) and (condition2):  D. if condition1 and condition2:"
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - In-class Quiz",
        "title": "Question 2 - Output with not and and",
        "difficulty": "Quiz",
        "statement": (
            "What will be the output of this code?\n\n"
            "x = 20\ny = 10\nif not x > 15 and y > 15:\n    print(\"One condition is true \" )\n\n"
            "A. No output  B. One condition is true  C. Error  D. None of these"
        ),
    },
    {
        "chapter": "Python if-else and Logical Operators - In-class Quiz",
        "title": "Question 3 - Evaluate a logical expression",
        "difficulty": "Quiz",
        "statement": "What would be the output of the following code?\n\nprint(5 > 3 and 3 < 2)",
    },
    {
        "chapter": "Python if-else and Logical Operators - In-class Quiz",
        "title": "Question 4 - Nested condition output",
        "difficulty": "Quiz",
        "statement": (
            "What will be printed by this code?\n\n"
            "x = 4\ny = 10\nif x < 5:\n    if not (y < 10 and x == 4):\n        print(\"Yes\")\n    else:\n        print(\"Maybe\")\nelse:\n    print(\"No\")"
        ),
    },
]

SOURCE_URL = "https://my.newtonschool.co/course/zqngjr790187/assignment/479bjqe8kcg9"
COURSE_URL = "https://my.newtonschool.co/course/tjj12ybxo9tt/details?subTab=Assignments&tab=course&subject=zqngjr790187"
LECTURE_URL = "https://my.newtonschool.co/course/zqngjr790187/lecture/ztz8mhzw2sws?video_recording_hash=mxh4vsfgcb2q&lectureTab=assignment"
QUIZ_URL = "https://my.newtonschool.co/course/zqngjr790187/lecture/ztz8mhzw2sws?video_recording_hash=mxh4vsfgcb2q&lectureTab=classroom_quiz"
