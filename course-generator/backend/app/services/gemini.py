from google import genai
from google.genai import types
import os
import json
from dotenv import load_dotenv
from ..schemas.course import CourseInput, CourseOutput
from urllib.parse import quote
import uuid
from urllib.parse import unquote

# In-memory store for generated visuals (key -> raw SVG string)
VISUAL_STORE: dict = {}

load_dotenv()

# New google.genai SDK — uses a Client object
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.0-flash"


def build_prompt(user_input: CourseInput) -> str:
    constraints = []
    
    # Skill Level Constraints
    skill = user_input.skill_level.lower()
    if skill == "beginner":
        constraints.append("LEVEL: Absolute Beginner. Focus on core fundamentals, basic syntax, and foundational concepts. Explain everything simply as if for a novice.")
    elif skill == "intermediate":
        constraints.append("LEVEL: Intermediate. Assume basic proficiency. Focus on best practices, deeper concepts, optimization, and real-world application patterns.")
    elif skill == "advanced":
        constraints.append("LEVEL: Advanced. Skip basics. Focus on high-level architecture, expert techniques, edge cases, and performance tuning.")
    else:
        constraints.append(f"LEVEL: {skill.title()}. Tailor content appropriately for this experience level.")

    # Learning Style Constraints
    style = user_input.learning_style.lower()
    if "hands-on" in style or "project" in style:
        constraints.append("STYLE: Project-based / Hands-on. Ensure every module has a practical project. 80% of content should be exercise-driven. Use actionable, project-oriented language. The 'mini_project' field is mandatory for every module.")
    elif "theoretical" in style or "deep-dive" in style:
        constraints.append("STYLE: Theoretical / Deep-dive. Focus on the 'why', underlying principles, and academic foundations. Provide comprehensive explanations and refer to core theory and research papers.")
    elif "visual" in style or "interactive" in style:
        constraints.append("STYLE: Visual / Interactive. For every single module, you MUST provide a detailed description of a Visual Aid (e.g., 'A complex Mind Map showing the relationship between X and Y', 'A detailed Flowchart of the process Z') in the 'visual_aid' field. Emphasize diagrams, mental models, and visual metaphors.")
    else:
        constraints.append(f"STYLE: {style.title()}. Adapt the teaching method to this preference.")

    # Time constraints
    if user_input.hours_per_week < 10:
        constraints.append(f"TIME: Limited ({user_input.hours_per_week} hrs/week). Keep modules tight, focused, and high-impact. Prioritize the 20% of content that gives 80% of results.")
    elif user_input.hours_per_week > 20:
        constraints.append(f"TIME: Intensive ({user_input.hours_per_week} hrs/week). Provide deep, comprehensive coverage with extensive resources and complex projects.")

    constraints_text = "\n- ".join(constraints)

    prompt = f"""
    You are an expert AI curriculum designer and educational architect.
    Your mission is to design a high-quality, professional learning roadmap for: {user_input.topic}

    CRITICAL INSTRUCTIONS FOR PERSONALIZATION:
    - SKILL LEVEL IS {user_input.skill_level.upper()}. 
      If 'Beginner': Explain basics like I'm 5. 
      If 'Advanced': Skip basics entirely. Jump into advanced internals, architecture, and optimization. The user is already an expert, don't bore them with 'Introduction to...'.
    - LEARNING STYLE IS {user_input.learning_style.upper()}. 
      If 'Visual': You MUST populate the 'visual_aid' field with a descriptive text for a Mind Map or Diagram for EVERY module.
      If 'Hands-on': You MUST provide a 'mini_project' for EVERY module.

    User Profile:
    - Skill Level: {user_input.skill_level}
    - Available Time: {user_input.hours_per_week} hours/week
    - Learning Style: {user_input.learning_style}
    - Primary Goal: {user_input.goal}

    Specific Constraints for this request:
    - {constraints_text}
    - Output EXACTLY 5 MODULES.
    - Ensure ALL content (titles, topics, exercises) is 100% relevant to '{user_input.topic}'.
    - Do NOT include generic programming boilerplate unless the topic IS programming.
    - Structure the roadmap to move from foundational understanding to mastery/application.
    - Make the 'mini_project' description inspiring and practical.
    """
    return prompt


# ─── Curated topic library for reliable, subject-specific fallbacks ──────────
TOPIC_LIBRARY = {
    "dsa": {
        "course_title": "Complete DSA Mastery Roadmap",
        "overview": "A structured roadmap covering Data Structures & Algorithms from fundamentals to advanced problem-solving, with hands-on LeetCode practice and real project applications.",
        "modules": [
            {
                "module_number": 1,
                "title": "DSA Fundamentals & Complexity Analysis",
                "duration": "2 weeks",
                "objectives": [
                    "Understand Big-O, Big-Theta, and Big-Omega notation",
                    "Analyze time and space complexity of algorithms"
                ],
                "topics": [
                    "Big-O Notation & Complexity Analysis",
                    "Arrays & Strings",
                    "Recursion Basics",
                    "Linear & Binary Search"
                ],
                "resources": [
                    "Abdul Bari DSA YouTube Playlist",
                    "CS50 Algorithm Lectures — Harvard OpenCourseWare",
                    "GeeksForGeeks — Time Complexity Guide"
                ],
                "exercise": "Solve 10 LeetCode Easy problems on Arrays and Binary Search (Two Sum, Binary Search, Best Time to Buy Stock).",
                "mini_project": "Build a contact book app using binary search for fast name lookup.",
                "quiz_questions": [
                    "What is the time complexity of binary search?",
                    "Explain the difference between O(n) and O(n squared) with an example."
                ]
            },
            {
                "module_number": 2,
                "title": "Building Skills — Linked Lists, Stacks & Queues",
                "duration": "2 weeks",
                "objectives": [
                    "Implement singly and doubly linked lists from scratch",
                    "Understand stack and queue operations and their use cases"
                ],
                "topics": [
                    "Singly & Doubly Linked Lists",
                    "Stack (LIFO) & Real-world Applications",
                    "Queue, Deque & Circular Queue",
                    "Monotonic Stack Patterns"
                ],
                "resources": [
                    "NeetCode.io — Linked List & Stack Video Series",
                    "LeetCode Explore Card: Linked List",
                    "Visualgo.net — Interactive Data Structure Visualizations"
                ],
                "exercise": "Implement a Stack using two Queues. Solve on LeetCode: Valid Parentheses, Reverse Linked List, Middle of Linked List.",
                "mini_project": "Build a browser history simulator (back/forward navigation) using a Doubly Linked List.",
                "quiz_questions": [
                    "What is the difference between a stack and a queue?",
                    "How do you detect a cycle in a linked list?"
                ]
            },
            {
                "module_number": 3,
                "title": "Trees, Heaps & Hash Maps",
                "duration": "2 weeks",
                "objectives": [
                    "Traverse and manipulate Binary Trees and Binary Search Trees",
                    "Use Hash Maps and Heaps to solve real problems efficiently"
                ],
                "topics": [
                    "Binary Trees & Binary Search Trees (BST)",
                    "Tree Traversals: BFS, DFS, Inorder, Preorder, Postorder",
                    "Hash Maps & Hash Sets",
                    "Heaps & Priority Queues"
                ],
                "resources": [
                    "NeetCode — Trees & Heaps Full Playlist",
                    "MIT OpenCourseWare — Hashing Lecture (6.006)",
                    "LeetCode Explore Card: Binary Tree"
                ],
                "exercise": "Solve on LeetCode: Maximum Depth of Binary Tree, Level Order Traversal, Two Sum (HashMap), Top K Frequent Elements (Heap).",
                "mini_project": "Build a Student Grade Tracker using a Max-Heap to instantly fetch the top 5 performing students.",
                "quiz_questions": [
                    "What is the difference between BFS and DFS tree traversal?",
                    "When would you use a Heap over a sorted array?"
                ]
            },
            {
                "module_number": 4,
                "title": "Graphs & Dynamic Programming",
                "duration": "3 weeks",
                "objectives": [
                    "Implement graph algorithms: BFS, DFS, Dijkstra, and Union-Find",
                    "Solve DP problems using memoization and tabulation"
                ],
                "topics": [
                    "Graph Representation — Adjacency List & Matrix",
                    "BFS & DFS on Graphs",
                    "Shortest Path Algorithms: Dijkstra & Bellman-Ford",
                    "Dynamic Programming: 1D, 2D, Knapsack & LCS"
                ],
                "resources": [
                    "William Fiset — Graph Theory Algorithms (YouTube)",
                    "NeetCode — Dynamic Programming Full Playlist",
                    "LeetCode Explore Card: Graph Theory"
                ],
                "exercise": "Solve on LeetCode: Number of Islands, Clone Graph, Climbing Stairs, Coin Change, Longest Common Subsequence.",
                "mini_project": "Build a city route planner that finds the shortest path using Dijkstra's algorithm with a printed map output.",
                "quiz_questions": [
                    "What is the difference between Dijkstra and Bellman-Ford?",
                    "Explain memoization vs tabulation in dynamic programming."
                ]
            },
            {
                "module_number": 5,
                "title": "Advanced DSA & Interview Preparation",
                "duration": "3 weeks",
                "objectives": [
                    "Master Tries, Backtracking, and Greedy Algorithms",
                    "Solve 50+ LeetCode Medium problems with confidence"
                ],
                "topics": [
                    "Trie (Prefix Tree) — Design & Applications",
                    "Backtracking: Subsets, Permutations & N-Queens",
                    "Greedy Algorithms: Activity Selection, Huffman Coding",
                    "Sliding Window & Two Pointer Techniques"
                ],
                "resources": [
                    "Striver's DSA Sheet — takeUforward.org (Top 180 Questions)",
                    "NeetCode 150 Problem Set",
                    "Cracking the Coding Interview — Chapters 1 to 10"
                ],
                "exercise": "Complete Striver's Sheet Week 5 (Greedy + Backtracking). Solve on LeetCode: Word Search II, Subsets II, Jump Game.",
                "mini_project": "Build an autocomplete search engine using a Trie data structure with a simple web interface.",
                "quiz_questions": [
                    "How does a Trie differ from a HashMap for prefix lookups?",
                    "Explain the sliding window technique with a real example."
                ]
            }
        ]
    },
    "mathematics": {
        "course_title": "Complete Mathematics Mastery Roadmap",
        "overview": "A structured roadmap covering Mathematics from foundational arithmetic to advanced calculus and statistics, with real-world problem-solving practice.",
        "modules": [
            {
                "module_number": 1,
                "title": "Number Systems & Arithmetic Foundations",
                "duration": "2 weeks",
                "objectives": [
                    "Master number systems: natural, integers, rational, real",
                    "Perform arithmetic operations fluently including fractions and percentages"
                ],
                "topics": ["Number Systems & Place Value", "Fractions, Decimals & Percentages", "LCM, HCF & Prime Factorization", "Ratio, Proportion & Unitary Method"],
                "resources": ["Khan Academy — Arithmetic (free)", "NCERT Mathematics Class 6–8", "Professor Leonard — Pre-Algebra (YouTube)"],
                "exercise": "Solve 20 mixed arithmetic problems from Khan Academy. Complete a speed drill on fractions and percentages.",
                "mini_project": "Build a personal budget calculator using ratio and percentage concepts.",
                "quiz_questions": ["What is the difference between LCM and HCF?", "Convert 3/8 to a decimal and then to a percentage."]
            },
            {
                "module_number": 2,
                "title": "Algebra & Linear Equations",
                "duration": "2 weeks",
                "objectives": [
                    "Solve linear and quadratic equations confidently",
                    "Understand algebraic identities and factorization"
                ],
                "topics": ["Variables, Expressions & Equations", "Linear Equations in One & Two Variables", "Quadratic Equations & the Quadratic Formula", "Algebraic Identities & Factorization"],
                "resources": ["Khan Academy — Algebra 1 & 2", "Art of Problem Solving (AoPS)", "PatrickJMT — Algebra Fundamentals (YouTube)"],
                "exercise": "Solve 15 linear equation problems. Factorize 10 quadratic expressions. Complete Khan Academy Algebra 1 unit test.",
                "mini_project": "Write a simple equation solver that takes user input and solves linear/quadratic equations step by step.",
                "quiz_questions": ["Solve: 2x + 5 = 17. Show all steps.", "Factorize: x² - 5x + 6."]
            },
            {
                "module_number": 3,
                "title": "Geometry & Trigonometry",
                "duration": "2 weeks",
                "objectives": [
                    "Apply geometric theorems to solve problems involving shapes and angles",
                    "Use trigonometric ratios to solve right-angled triangle problems"
                ],
                "topics": ["Lines, Angles, Triangles & Quadrilaterals", "Circles, Area & Perimeter", "Trigonometric Ratios: sin, cos, tan", "Heights & Distances — Real-world Applications"],
                "resources": ["Khan Academy — Geometry & Trigonometry", "3Blue1Brown — Essence of Trigonometry (YouTube)", "NCERT Mathematics Class 9–10"],
                "exercise": "Solve 10 geometry proof problems. Calculate heights and distances using trigonometric ratios in 5 word problems.",
                "mini_project": "Create a triangle solver: input 3 values (sides/angles) and output all remaining measurements using trig.",
                "quiz_questions": ["State and prove the Pythagorean theorem.", "If sin θ = 3/5, find cos θ and tan θ."]
            },
            {
                "module_number": 4,
                "title": "Statistics, Probability & Combinatorics",
                "duration": "2 weeks",
                "objectives": [
                    "Calculate mean, median, mode, and standard deviation",
                    "Apply probability rules including permutations and combinations"
                ],
                "topics": ["Mean, Median, Mode & Standard Deviation", "Probability: Classical & Conditional", "Permutations & Combinations", "Data Representation: Histograms, Box Plots"],
                "resources": ["Khan Academy — Statistics & Probability", "StatQuest with Josh Starmer (YouTube)", "MIT OpenCourseWare — Introduction to Probability"],
                "exercise": "Analyze a real dataset (class marks). Calculate mean, median, variance. Solve 10 probability problems.",
                "mini_project": "Build a dice-roll simulator that tracks outcomes over 1000 rolls and compares frequency vs. theoretical probability.",
                "quiz_questions": ["What is the difference between permutation and combination?", "If a coin is tossed 3 times, what is P(exactly 2 heads)?"]
            },
            {
                "module_number": 5,
                "title": "Calculus — Limits, Derivatives & Integrals",
                "duration": "3 weeks",
                "objectives": [
                    "Understand limits and continuity of functions",
                    "Differentiate and integrate standard functions using core rules"
                ],
                "topics": ["Limits & Continuity", "Derivatives: Power, Chain, Product & Quotient Rules", "Applications of Derivatives: Maxima & Minima", "Integration: Definite & Indefinite Integrals"],
                "resources": ["3Blue1Brown — Essence of Calculus (YouTube)", "Professor Leonard — Calculus 1 Full Course (YouTube)", "Khan Academy — AP Calculus AB"],
                "exercise": "Differentiate 10 functions using all rules. Evaluate 10 definite integrals. Solve 5 optimization word problems.",
                "mini_project": "Build a graphing tool that plots f(x) and visually shows tangent lines and area under curve for user-defined functions.",
                "quiz_questions": ["What is the derivative of x³ + 2x² - 5x + 7?", "Find the area under y = x² from x=0 to x=3."]
            }
        ]
    },
    "python": {
        "course_title": "Python Programming — Zero to Proficient",
        "overview": "A hands-on Python roadmap from absolute basics to building real projects, covering syntax, OOP, file handling, APIs, and data manipulation.",
        "modules": [
            {
                "module_number": 1,
                "title": "Python Basics & Core Syntax",
                "duration": "2 weeks",
                "objectives": [
                    "Write and run Python programs using variables, loops, and conditions",
                    "Understand Python data types and basic I/O operations"
                ],
                "topics": ["Variables, Data Types & Type Casting", "Operators & Expressions", "Conditional Statements: if, elif, else", "Loops: for, while, break, continue"],
                "resources": ["Python.org Official Tutorial", "CS Dojo — Python for Beginners (YouTube)", "Automate the Boring Stuff with Python — Ch. 1–3 (free)"],
                "exercise": "Write 10 programs: FizzBuzz, prime checker, factorial, Fibonacci, simple calculator. Upload to GitHub.",
                "mini_project": "Build a number guessing game where the computer picks a random number and the user guesses with hints.",
                "quiz_questions": ["What is the difference between a list and a tuple in Python?", "How does Python handle integer division vs float division?"]
            },
            {
                "module_number": 2,
                "title": "Functions, Lists, Dicts & File Handling",
                "duration": "2 weeks",
                "objectives": [
                    "Write reusable functions with parameters and return values",
                    "Manipulate lists, dictionaries, and read/write files"
                ],
                "topics": ["Functions: args, kwargs, default params, lambda", "Lists, Tuples & Sets — Methods & Comprehensions", "Dictionaries & Nested Data Structures", "File Handling: open, read, write, CSV, JSON"],
                "resources": ["Real Python — realpython.com (Functions & Data Structures)", "Corey Schafer — Python Tutorials (YouTube)", "Automate the Boring Stuff — Ch. 8–9"],
                "exercise": "Build a contacts manager using a dictionary stored in a JSON file. Implement add, search, update, delete.",
                "mini_project": "Create a CSV-based expense tracker that reads/writes expenses and prints a monthly summary.",
                "quiz_questions": ["What is a lambda function? Give an example.", "How do you handle a KeyError when accessing a dictionary?"]
            },
            {
                "module_number": 3,
                "title": "Object-Oriented Programming in Python",
                "duration": "2 weeks",
                "objectives": [
                    "Design classes with attributes, methods, and constructors",
                    "Apply OOP principles: inheritance, polymorphism, encapsulation"
                ],
                "topics": ["Classes, Objects & __init__ Constructor", "Inheritance & Method Overriding", "Encapsulation: Private & Protected Members", "Dunder Methods: __str__, __repr__, __len__"],
                "resources": ["Corey Schafer — OOP Python Series (YouTube)", "Real Python — OOP in Python 3", "Python Crash Course — Chapter 9 (Eric Matthes)"],
                "exercise": "Model a Library system with Book, Member, and Library classes. Implement borrow/return logic.",
                "mini_project": "Build a bank account simulator with deposit, withdraw, and transfer using OOP with input validation.",
                "quiz_questions": ["What is the difference between __str__ and __repr__?", "Explain method resolution order (MRO) with an example."]
            },
            {
                "module_number": 4,
                "title": "Modules, APIs & Web Scraping",
                "duration": "2 weeks",
                "objectives": [
                    "Use Python's standard library and install third-party packages",
                    "Fetch data from REST APIs and scrape web pages"
                ],
                "topics": ["Python Standard Library: os, sys, datetime, math", "pip & Virtual Environments", "REST APIs with requests library", "Web Scraping with BeautifulSoup"],
                "resources": ["requests Docs — docs.python-requests.org", "Real Python — Web Scraping Tutorial", "Tech With Tim — API Projects (YouTube)"],
                "exercise": "Fetch weather data from OpenWeatherMap API. Parse and display temperature, humidity for 5 cities.",
                "mini_project": "Build a news headline scraper that pulls top 10 stories from a news site and saves them to a text file.",
                "quiz_questions": ["What is the difference between GET and POST requests?", "How do you find all anchor tags using BeautifulSoup?"]
            },
            {
                "module_number": 5,
                "title": "Python Projects & Best Practices",
                "duration": "3 weeks",
                "objectives": [
                    "Structure Python projects with proper packaging and testing",
                    "Build and deploy a complete Python application"
                ],
                "topics": ["Project Structure & Packaging", "Unit Testing with pytest", "Error Handling & Logging", "CLI Tools with argparse & Deployment Basics"],
                "resources": ["Real Python — Python Testing with pytest", "Corey Schafer — Unit Testing Python (YouTube)", "Hitchhiker's Guide to Python — docs.python-guide.org"],
                "exercise": "Add pytest unit tests to your expense tracker. Achieve 80%+ code coverage.",
                "mini_project": "Build a CLI To-Do app with add, complete, delete, list commands. Package it as an installable tool.",
                "quiz_questions": ["What is the purpose of a try/except/finally block?", "How does argparse help in building CLI tools?"]
            }
        ]
    },
    "c programming": {
        "course_title": "C Programming — From Scratch to Systems",
        "overview": "A comprehensive C programming roadmap from basic syntax to memory management, pointers, and systems-level programming with practical projects.",
        "modules": [
            {
                "module_number": 1,
                "title": "C Fundamentals & Program Structure",
                "duration": "2 weeks",
                "objectives": [
                    "Write, compile, and run basic C programs",
                    "Understand C data types, operators, and control flow"
                ],
                "topics": ["C Program Structure: main(), headers, compilation", "Data Types: int, float, char, double", "Operators: Arithmetic, Relational, Logical, Bitwise", "Control Flow: if-else, switch, for, while, do-while"],
                "resources": ["The C Programming Language — Kernighan & Ritchie (K&R)", "CS50 Week 1 — Harvard OpenCourseWare", "Jenny's Lectures CS IT — C Programming (YouTube)"],
                "exercise": "Write 10 C programs: even/odd, sum of digits, reverse a number, Fibonacci, star patterns. Compile with gcc.",
                "mini_project": "Build a command-line calculator supporting +, -, *, / with a loop to continue until user exits.",
                "quiz_questions": ["What is the difference between signed and unsigned integers in C?", "Explain the difference between while and do-while loops."]
            },
            {
                "module_number": 2,
                "title": "Functions, Arrays & Strings",
                "duration": "2 weeks",
                "objectives": [
                    "Write modular programs using functions with proper return types",
                    "Manipulate arrays and strings using standard library functions"
                ],
                "topics": ["Functions: Declaration, Definition, Call by Value", "Recursion in C", "Arrays: 1D, 2D, Multidimensional", "Strings & string.h: strcpy, strlen, strcmp, strcat"],
                "resources": ["GeeksForGeeks — C Functions & Arrays", "Neso Academy — C Programming (YouTube)", "CS50 — Arrays Lecture"],
                "exercise": "Implement bubble sort, selection sort, linear search, binary search on arrays. Write recursive factorial and Fibonacci.",
                "mini_project": "Build a student grade management system using 2D arrays to store and compute average marks per student.",
                "quiz_questions": ["What is the difference between call by value and call by reference?", "How are strings stored in C? What terminates a C string?"]
            },
            {
                "module_number": 3,
                "title": "Pointers & Memory Management",
                "duration": "2 weeks",
                "objectives": [
                    "Declare and dereference pointers; understand pointer arithmetic",
                    "Dynamically allocate and free memory using malloc/free"
                ],
                "topics": ["Pointers: Declaration, Dereference, Pointer Arithmetic", "Pointers and Arrays — Relationship & Differences", "Dynamic Memory: malloc, calloc, realloc, free", "Common Bugs: Dangling Pointers, Memory Leaks"],
                "resources": ["Understanding and Using C Pointers — Richard Reese (O'Reilly)", "Neso Academy — Pointers in C (YouTube)", "CS50 — Memory Lecture (Week 4)"],
                "exercise": "Implement a dynamic array using realloc. Write pointer-based swap and reverse-array functions.",
                "mini_project": "Build a dynamic stack using a pointer-based linked list with push, pop, and display operations.",
                "quiz_questions": ["What is a null pointer and why is it dangerous to dereference?", "What is the difference between malloc and calloc?"]
            },
            {
                "module_number": 4,
                "title": "Structures, Unions & File I/O",
                "duration": "2 weeks",
                "objectives": [
                    "Define and use structures and unions to model complex data",
                    "Read and write data to files using FILE pointers"
                ],
                "topics": ["Structures: Definition, Nesting, Array of Structs", "Unions & Bit Fields", "typedef and Enumerations", "File I/O: fopen, fread, fwrite, fclose, fprintf"],
                "resources": ["GeeksForGeeks — Structures in C", "Programiz — C File Handling Tutorial", "Jenny's Lectures — Structures & File I/O (YouTube)"],
                "exercise": "Create an Employee struct. Store 5 employees to a binary file and read them back.",
                "mini_project": "Build an inventory management system that stores product records in a binary file with add/search/display features.",
                "quiz_questions": ["What is the difference between a structure and a union in C?", "What is the difference between text mode and binary mode in file operations?"]
            },
            {
                "module_number": 5,
                "title": "Advanced C — Linked Lists, Preprocessor & Systems",
                "duration": "3 weeks",
                "objectives": [
                    "Implement linked lists, stacks, and queues using structs and pointers",
                    "Use preprocessor macros and understand compilation stages"
                ],
                "topics": ["Singly & Doubly Linked Lists in C", "Stacks & Queues using Linked Lists", "Preprocessor Directives: #define, #include, #ifdef", "Compilation Stages: Preprocessing, Compiling, Linking"],
                "resources": ["K&R C Book — Chapter 6 & 7", "GeeksForGeeks — Linked List in C", "Low Level Learning — C Systems Programming (YouTube)"],
                "exercise": "Implement a doubly linked list with insert, delete, search, and reverse. Write a Makefile for a multi-file C project.",
                "mini_project": "Build a text-based task manager using a linked list where tasks are stored persistently in a .txt file.",
                "quiz_questions": ["What are the advantages of a linked list over an array?", "What does the #define preprocessor directive do? Give an example."]
            }
        ]
    },
    "guitar basics": {
        "course_title": "Guitar Basics — From Zero to Playing Songs",
        "overview": "A beginner-friendly guitar roadmap covering posture, chords, strumming, scales, and song-playing — structured to get you making music from day one.",
        "modules": [
            {
                "module_number": 1,
                "title": "Guitar Setup, Posture & First Notes",
                "duration": "2 weeks",
                "objectives": [
                    "Hold the guitar correctly and adopt proper playing posture",
                    "Identify all parts of the guitar and tune it using a tuner"
                ],
                "topics": ["Parts of the Guitar: body, neck, frets, tuning pegs", "Proper Sitting & Standing Posture", "Tuning with a clip-on tuner & by ear", "Playing Single Notes on the High E and B strings"],
                "resources": ["Justin Guitar — Beginner Course (justinguitar.com — free)", "Marty Music — Guitar for Beginners (YouTube)", "Fender Play — First Week Lessons"],
                "exercise": "Tune your guitar daily. Practice picking single notes on strings 1–3 for 15 minutes. Learn to play a simple melody like 'Smoke on the Water'.",
                "mini_project": "Record a 30-second video of yourself playing a simple one-string melody cleanly from start to finish.",
                "quiz_questions": ["Name all 6 open strings of a standard-tuned guitar from low to high.", "What does 'fret' mean and how do you press a note correctly?"]
            },
            {
                "module_number": 2,
                "title": "Open Chords & Smooth Chord Changes",
                "duration": "2 weeks",
                "objectives": [
                    "Play the 8 essential open chords clearly without buzzing",
                    "Switch between chords smoothly within a beat"
                ],
                "topics": ["Open Chords: Em, Am, E, A, D, G, C, B7", "Finger Placement & Avoiding Buzz", "Chord Transitions: One-Minute Changes Exercise", "Reading Guitar Chord Diagrams"],
                "resources": ["Justin Guitar — Stage 1 & 2 (justinguitar.com)", "Paul Davids — Open Chords Masterclass (YouTube)", "Ultimate Guitar — Chord library (ultimate-guitar.com)"],
                "exercise": "Practice 'One-Minute Changes' between Em–Am, G–C, and D–A. Aim for 30+ clean changes per minute by end of week 2.",
                "mini_project": "Learn and perform the chord progression for 'Knockin' on Heaven's Door' (G–D–Am) cleanly.",
                "quiz_questions": ["What is the finger shape for an open G chord?", "Why do strings buzz when playing chords and how do you fix it?"]
            },
            {
                "module_number": 3,
                "title": "Strumming Patterns & Rhythm",
                "duration": "2 weeks",
                "objectives": [
                    "Strum in time using a metronome with down and up strokes",
                    "Play common strumming patterns used in pop and rock songs"
                ],
                "topics": ["Down Strums & Up Strums — Notation & Timing", "Common Patterns: D-DU-UDU, D-D-UDU", "Using a Metronome & Rhythm Practice", "Strumming Dynamics: Soft vs Loud"],
                "resources": ["Marty Music — Strumming Patterns for Beginners (YouTube)", "Justin Guitar — Strumming SOS Course", "Drumeo Metronome — free online metronome"],
                "exercise": "Practice 3 strumming patterns at 60 BPM, then 80 BPM over G–C–D–Em progression. Record and listen back.",
                "mini_project": "Learn to play 'Let Her Go' by Passenger using the correct strumming pattern all the way through.",
                "quiz_questions": ["What does 'BPM' mean and why is practicing with a metronome important?", "Write out the D-DU-UDU pattern using down/up arrows."]
            },
            {
                "module_number": 4,
                "title": "Barre Chords, Power Chords & the Fretboard",
                "duration": "2 weeks",
                "objectives": [
                    "Play F major and B minor barre chords cleanly",
                    "Use power chords to play rock riffs"
                ],
                "topics": ["F Major Barre Chord — E-shape & A-shape", "Power Chords (5 chords) for Rock", "CAGED System Introduction", "Fretboard Navigation: Notes on Strings 6 & 5"],
                "resources": ["Justin Guitar — Barre Chords Module (justinguitar.com)", "Paul Davids — How to Play Barre Chords (YouTube)", "GuitarTricks — CAGED System Lesson"],
                "exercise": "Practice F barre chord 10 minutes daily. Play a 12-bar blues using power chords at 70 BPM.",
                "mini_project": "Learn 'Smells Like Teen Spirit' by Nirvana intro and verse riff using power chords.",
                "quiz_questions": ["What is a barre chord and why is the F chord considered difficult for beginners?", "How do power chords differ from full open chords?"]
            },
            {
                "module_number": 5,
                "title": "Scales, Solos & Playing Complete Songs",
                "duration": "3 weeks",
                "objectives": [
                    "Play the pentatonic minor scale in position 1 across the fretboard",
                    "Perform 3 complete songs from start to finish"
                ],
                "topics": ["Pentatonic Minor Scale — Box Pattern 1", "Simple Lead Licks & Bending Techniques", "Fingerpicking Basics: Travis Picking Pattern", "Full Song Performance: Structure & Transitions"],
                "resources": ["Marty Music — Pentatonic Scale Lesson (YouTube)", "Justin Guitar — Lead Guitar Basics", "Rick Beato — Understanding the Pentatonic Scale (YouTube)"],
                "exercise": "Run the pentatonic scale up and down at 60 BPM. Improvise a 1-minute solo over a backing track in A minor.",
                "mini_project": "Record yourself performing 3 complete songs: one strumming, one power chords, one fingerpicked — and share the recording.",
                "quiz_questions": ["What are the 5 notes in the A minor pentatonic scale?", "What is the difference between lead guitar and rhythm guitar?"]
            }
        ]
    },
    "machine learning": {
        "course_title": "Machine Learning — Foundations to Real Projects",
        "overview": "A practical ML roadmap from mathematics foundations through supervised/unsupervised learning, neural networks, and deploying real models using Python and scikit-learn.",
        "modules": [
            {
                "module_number": 1,
                "title": "ML Foundations — Math & Python for ML",
                "duration": "2 weeks",
                "objectives": [
                    "Apply linear algebra and statistics concepts required for ML",
                    "Use NumPy, Pandas, and Matplotlib for data manipulation and visualization"
                ],
                "topics": ["Linear Algebra: Vectors, Matrices, Dot Products", "Statistics: Mean, Variance, Distributions, Correlation", "NumPy Arrays & Pandas DataFrames", "Data Visualization with Matplotlib & Seaborn"],
                "resources": ["3Blue1Brown — Essence of Linear Algebra (YouTube)", "Kaggle — Pandas & NumPy free micro-courses", "StatQuest with Josh Starmer — Stats for ML (YouTube)"],
                "exercise": "Load the Titanic dataset with Pandas. Compute summary statistics, plot distributions, and handle missing values.",
                "mini_project": "Build an EDA (Exploratory Data Analysis) report for the Iris dataset with 5+ charts and key statistical insights.",
                "quiz_questions": ["What is the difference between variance and standard deviation?", "How does a dot product relate to similarity between two vectors?"]
            },
            {
                "module_number": 2,
                "title": "Supervised Learning — Regression & Classification",
                "duration": "2 weeks",
                "objectives": [
                    "Implement Linear and Logistic Regression from scratch and with scikit-learn",
                    "Evaluate models using accuracy, precision, recall, F1, and ROC-AUC"
                ],
                "topics": ["Linear Regression: Cost Function & Gradient Descent", "Logistic Regression & Decision Boundary", "Decision Trees & Random Forests", "Model Evaluation: Train/Test Split, Cross-Validation, Confusion Matrix"],
                "resources": ["Andrew Ng — Machine Learning Specialization (Coursera)", "scikit-learn Documentation — sklearn.org", "Sentdex — ML with Python (YouTube)"],
                "exercise": "Train a Linear Regression model on the Boston Housing dataset. Train a Logistic Regression on Iris. Compare metrics.",
                "mini_project": "Build a House Price Predictor using Linear Regression on a Kaggle dataset. Deploy with a simple input form.",
                "quiz_questions": ["What is the difference between regression and classification?", "Explain precision vs recall. When would you prioritize one over the other?"]
            },
            {
                "module_number": 3,
                "title": "Unsupervised Learning & Feature Engineering",
                "duration": "2 weeks",
                "objectives": [
                    "Apply K-Means clustering and PCA to unlabeled data",
                    "Engineer and select features to improve model performance"
                ],
                "topics": ["K-Means Clustering & the Elbow Method", "Principal Component Analysis (PCA)", "Feature Scaling: Normalization & Standardization", "Feature Selection: Correlation, Importance, RFE"],
                "resources": ["StatQuest — PCA & Clustering (YouTube)", "Kaggle — Feature Engineering Micro-course", "Hands-On ML with Scikit-Learn & TensorFlow — Chapter 8 & 9 (Aurélien Géron)"],
                "exercise": "Apply K-Means on the Mall Customers dataset. Use PCA to reduce a high-dimensional dataset and visualize clusters in 2D.",
                "mini_project": "Build a customer segmentation system that groups users into personas using K-Means and visualizes them.",
                "quiz_questions": ["What problem does PCA solve and how does it work??", "What is the Elbow Method in K-Means clustering?"]
            },
            {
                "module_number": 4,
                "title": "Neural Networks & Deep Learning Basics",
                "duration": "3 weeks",
                "objectives": [
                    "Understand how artificial neural networks learn through backpropagation",
                    "Build and train basic neural networks using Keras/TensorFlow"
                ],
                "topics": ["Neurons, Layers, Activation Functions: ReLU, Sigmoid, Softmax", "Forward Pass & Backpropagation", "Building ANNs with Keras Sequential API", "Overfitting, Dropout & Regularization"],
                "resources": ["3Blue1Brown — Neural Networks series (YouTube)", "deeplearning.ai — Deep Learning Specialization (Coursera)", "François Chollet — Deep Learning with Python (book)"],
                "exercise": "Build a neural network to classify MNIST handwritten digits. Achieve 97%+ accuracy. Experiment with layers and dropout.",
                "mini_project": "Train a binary classifier neural network on a medical dataset (e.g., Breast Cancer Wisconsin) and evaluate with ROC-AUC.",
                "quiz_questions": ["What is the vanishing gradient problem and how does ReLU help?", "What is dropout and why does it prevent overfitting?"]
            },
            {
                "module_number": 5,
                "title": "ML Projects, Pipelines & Model Deployment",
                "duration": "3 weeks",
                "objectives": [
                    "Build end-to-end ML pipelines with preprocessing and model selection",
                    "Deploy a trained ML model as a REST API using Flask or FastAPI"
                ],
                "topics": ["sklearn Pipelines & ColumnTransformer", "Hyperparameter Tuning: GridSearchCV & RandomizedSearchCV", "Saving Models with joblib & pickle", "Model Deployment: Flask API + Docker basics"],
                "resources": ["Real Python — Deploying ML Models with Flask", "Krish Naik — ML Deployment Tutorial (YouTube)", "Made With ML — mlops.community"],
                "exercise": "Build a full pipeline (preprocess → train → tune → evaluate) for a Kaggle tabular dataset. Export as a .pkl model.",
                "mini_project": "Deploy your House Price Predictor model as a REST API using Flask. Create a simple HTML form to make predictions live.",
                "quiz_questions": ["What is the purpose of a scikit-learn Pipeline?", "What is the difference between GridSearchCV and RandomizedSearchCV?"]
            }
        ]
    }
}


def _normalize_topic(topic: str) -> str:
    """Normalize topic string for library lookup."""
    t = topic.lower().strip()
    aliases = {
        # DSA
        "data structures": "dsa",
        "data structures and algorithms": "dsa",
        "algorithms": "dsa",
        "dsa": "dsa",
        "data structure": "dsa",
        "ds and algo": "dsa",
        "ds&a": "dsa",
        # Mathematics
        "maths": "mathematics",
        "math": "mathematics",
        "mathematics": "mathematics",
        "basic maths": "mathematics",
        "applied mathematics": "mathematics",
        # Python
        "python": "python",
        "python programming": "python",
        "learn python": "python",
        "python basics": "python",
        # C Programming
        "c": "c programming",
        "c language": "c programming",
        "c programming": "c programming",
        "c program": "c programming",
        # Guitar
        "guitar": "guitar basics",
        "guitar basics": "guitar basics",
        "learn guitar": "guitar basics",
        "acoustic guitar": "guitar basics",
        "guitar for beginners": "guitar basics",
        # Machine Learning
        "ml": "machine learning",
        "machine learning": "machine learning",
        "ai": "machine learning",
        "artificial intelligence": "machine learning",
        "deep learning": "machine learning",
    }
    return aliases.get(t, t)


def _svg_data_url_for_topics(topics: list, title: str) -> str:
    """Create a compact SVG flowchart from topics and return as data URL."""
    # Simple stacked boxes SVG
    box_w = 300
    box_h = 44
    padding = 16
    spacing = 12
    width = box_w + padding * 2
    height = len(topics) * (box_h + spacing) + padding * 2

    # Escape text for XML
    def esc(t):
        return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    items = []
    for i, t in enumerate(topics):
        x = padding
        y = padding + i * (box_h + spacing)
        items.append(f'<rect x="{x}" y="{y}" rx="8" ry="8" width="{box_w}" height="{box_h}" fill="#ffffff" stroke="#94a3b8" stroke-width="1.2"/>')
        text = esc(t if len(t) <= 60 else t[:57] + '...')
        items.append(f'<text x="{x+12}" y="{y + box_h/2 + 5}" font-family="Inter, Arial, sans-serif" font-size="13" fill="#0f172a">{text}</text>')
        if i > 0:
            lx = x + box_w/2
            y1 = y - spacing/2
            y2 = y
            items.append(f'<line x1="{lx}" y1="{y1}" x2="{lx}" y2="{y2}" stroke="#cbd5e1" stroke-width="2"/>')

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    svg += ''.join(items)
    svg += '</svg>'

    data_url = 'data:image/svg+xml;utf8,' + quote(svg, safe='')
    return data_url


def _svg_path_for_topics(topics: list, title: str) -> str:
    """Create an SVG from topics, store it in VISUAL_STORE and return a relative path."""
    # Reuse same generator logic as _svg_data_url_for_topics but keep raw svg
    box_w = 300
    box_h = 44
    padding = 16
    spacing = 12
    width = box_w + padding * 2
    height = len(topics) * (box_h + spacing) + padding * 2

    def esc(t):
        return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    items = []
    for i, t in enumerate(topics):
        x = padding
        y = padding + i * (box_h + spacing)
        items.append(f'<rect x="{x}" y="{y}" rx="8" ry="8" width="{box_w}" height="{box_h}" fill="#ffffff" stroke="#94a3b8" stroke-width="1.2"/>')
        text = esc(t if len(t) <= 60 else t[:57] + '...')
        items.append(f'<text x="{x+12}" y="{y + box_h/2 + 5}" font-family="Inter, Arial, sans-serif" font-size="13" fill="#0f172a">{text}</text>')
        if i > 0:
            lx = x + box_w/2
            y1 = y - spacing/2
            y2 = y
            items.append(f'<line x1="{lx}" y1="{y1}" x2="{lx}" y2="{y2}" stroke="#cbd5e1" stroke-width="2"/>')

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    svg += ''.join(items)
    svg += '</svg>'

    key = str(uuid.uuid4())
    VISUAL_STORE[key] = svg
    return f"/visual/temp/{key}"


def _build_fallback_modules(topic: str, goal: str, skill_level: str = "beginner", hours_per_week: int = 10, learning_style: str = "hands-on") -> tuple:
    """
    Returns (modules, course_title, overview, is_curated, is_generic).
    Priority: TOPIC_LIBRARY → Gemini plain-text → generic labeled fallback.
    """
    key = _normalize_topic(topic)
    style = learning_style.lower()
    skill = skill_level.lower()

    # 1. Check curated library first
    if key in TOPIC_LIBRARY:
        lib = json.loads(json.dumps(TOPIC_LIBRARY[key])) # Deep copy to avoid mutating the original library
        
        is_hands_on = "hands-on" in style or "project" in style
        is_theoretical = "theoretical" in style or "deep-dive" in style
        is_visual = "visual" in style or "interactive" in style

        lib["course_title"] = f"{lib['course_title']} — {skill_level.title()} {learning_style.title()}"
        lib["overview"] = (
            f"A {learning_style} oriented roadmap for {skill_level} learners. "
            f"{lib['overview']} Goal: {goal}."
        )
        
        # Skill-level adaptation
        if skill == "advanced":
            for i, mod in enumerate(lib["modules"]):
                if mod["module_number"] == 1:
                    mod["title"] = f"Advanced {topic.title()} Architecture & Internals"
                    mod["topics"] = [f"{topic.title()} system design", "Performance optimization patterns", "Edge-case handling"]
                    mod["objectives"] = [
                        f"Analyze advanced {topic} architecture and performance tradeoffs",
                        "Identify high-impact optimizations and scalability patterns"
                    ]
                    mod["exercise"] = f"Review a professional {topic} case study and identify three architectural improvements."
                    mod["mini_project"] = f"Design a high-performance {topic} prototype focusing on latency and scalability."
                elif mod["module_number"] == 2:
                    mod["title"] = f"Advanced {topic.title()} Patterns & Best Practices"
                    mod["topics"] = ["Robust design patterns", "Production-grade reliability", "Security and maintainability"]
                elif mod["module_number"] == 5:
                    mod["title"] = f"Expert Mastery & Innovation in {topic.title()}"
                    mod["topics"] = ["Advanced research trends", "Automation and tooling", "Leadership and mentorship"]
        elif skill == "intermediate":
            for mod in lib["modules"]:
                if mod["module_number"] == 1:
                    mod["title"] = f"Intermediate {topic.title()} Foundations"
                    mod["topics"] = [f"Core {topic} concepts", "Common patterns", "Hands-on application"]
                    mod["exercise"] = f"Complete an intermediate {topic} task that reinforces key concepts."
                elif mod["module_number"] == 3:
                    mod["title"] = f"Applied {topic.title()} Skills"
                    mod["topics"] = ["Practical workflows", "Best practices", "Real-world examples"]
        elif skill == "beginner":
            for mod in lib["modules"]:
                if mod["module_number"] == 1:
                    mod["title"] = f"{topic.title()} Basics & Getting Started"
                    mod["topics"] = [f"What is {topic}?", "Core terminology", "First practical examples"]
                    mod["exercise"] = f"Follow a guided beginner tutorial to apply the first {topic} concept step-by-step."
                elif mod["module_number"] == 5:
                    mod["title"] = f"Beginner {topic.title()} Capstone"
                    mod["topics"] = ["Review core concepts", "Build a simple complete project", "Plan the next learning step"]
                    mod["exercise"] = f"Assemble the skills from prior modules into a beginner-friendly project."
        
        # Learning Style adaptation
        for mod in lib["modules"]:
            if is_hands_on:
                if "practical" not in mod["title"].lower():
                    mod["title"] = f"Practical: {mod['title']}"
                mod["exercise"] = f"Build a working {topic} example that applies {mod['topics'][0]}."
                mod["mini_project"] = mod.get("mini_project") or f"Create a practical {topic} project based on {mod['topics'][0]}."
                mod["resources"].append(f"Project-based {topic} tutorial")
            elif is_theoretical:
                if "theoretical" not in mod["title"].lower():
                    mod["title"] = f"Theoretical: {mod['title']}"
                mod["exercise"] = f"Write a short analysis explaining why {mod['topics'][0]} works and how it relates to underlying theory."
                mod["resources"].append(f"Research article or academic paper on {mod['topics'][0]}")
                if not mod.get("mini_project"):
                    mod["mini_project"] = f"Prepare a documented theory review on {mod['topics'][0]}."
            elif is_visual:
                if "visualized" not in mod["title"].lower():
                    mod["title"] = f"Visualized: {mod['title']}"
                # Generate an inline SVG data-URL for the visual aid so frontend can render it as an image
                mod["visual_aid"] = _svg_path_for_topics(mod.get("topics", []), mod.get("title", topic))
                mod["exercise"] = f"Sketch or map out {mod['topics'][0]} visually and explain the relationship between the key elements."
                mod["resources"].append(f"Interactive {topic} visualization")
        
        return lib["modules"], lib["course_title"], lib["overview"], True, False

    # 2. Ask Gemini with a simpler plain-text prompt (no schema enforcement)
    try:
        fallback_prompt = f"""
        You are an expert curriculum designer. Create a 5-module learning roadmap for '{topic}'.
        
        User Profile:
        - Skill Level: {skill_level}
        - Learning Style: {learning_style}
        - Goal: {goal}
        
        Tailor the modules specifically for a {skill_level} learner with a {learning_style} preference.
        
        For each module provide:
        1. A concise, specific stage title (max 6 words)
        2. Exactly 3 specific subtopics relevant only to '{topic}'
        3. One hands-on exercise sentence
        4. One mini-project idea (write null for modules 2 and 4)
        5. One recommended resource (book, website, or YouTube channel)
        6. A descriptive 'visual_aid' (e.g. 'Concept Mind Map', 'Flowchart')

        Output ONLY a valid JSON array of objects, no markdown blocks, no explanation:
        [
          {{
            "title": "...",
            "topics": ["...", "...", "..."],
            "exercise": "...",
            "mini_project": "..." or null,
            "resource": "...",
            "visual_aid": "..."
          }}
        ]
        """
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=fallback_prompt
        )
        text = resp.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        stages = json.loads(text.strip())
        is_generic = False
    except Exception as fallback_err:
        print(f"Gemini plain-text fallback failed: {fallback_err}")
        is_generic = True
        is_hands_on = "hands-on" in style or "project" in style
        is_theoretical = "theoretical" in style or "deep-dive" in style
        is_visual = "visual" in style or "interactive" in style

        def formatted_resource(base):
            if is_theoretical:
                return f"Research paper or article on {base}"
            if is_visual:
                return f"Interactive visualization or diagram for {base}"
            return f"Project-based guide for {base}"

        def formatted_exercise(base):
            if is_theoretical:
                return f"Write a short summary explaining why {base} works and its key principles."
            if is_visual:
                return f"Sketch or diagram the main ideas behind {base} and label the relationships."
            return f"Build a practical {base} example and test it end-to-end."

        def formatted_mini_project(base, fallback=None):
            if is_hands_on:
                return fallback or f"Create a working {base} project that applies the concepts."
            if is_theoretical:
                return fallback or f"Prepare a documented theory review of {base}."
            if is_visual:
                return fallback or f"Design a visual roadmap or diagram for {base}."
            return fallback

        stages = [
            {
                "title": f"{topic.title()} Foundations",
                "topics": [f"Introduction to {topic}", "Core concepts", "First applications"],
                "exercise": formatted_exercise(f"{topic} foundations"),
                "mini_project": formatted_mini_project(f"{topic} foundations", f"Build a simple {topic} starter project."),
                "resource": formatted_resource(f"{topic} basics"),
                "visual_aid": f"Diagram showing the basics of {topic}."
            },
            {
                "title": f"Applied {topic.title()} Skills",
                "topics": ["Key techniques", "Common tools", "Practice workflows"],
                "exercise": formatted_exercise(f"applied {topic} skills"),
                "mini_project": formatted_mini_project(f"applied {topic} skills", None),
                "resource": formatted_resource(f"practical {topic}"),
                "visual_aid": f"Flowchart of the {topic} workflow."
            },
            {
                "title": f"{topic.title()} Theory & Strategy",
                "topics": ["Underlying principles", "Best practices", "Decision criteria"],
                "exercise": formatted_exercise(f"{topic} theory"),
                "mini_project": formatted_mini_project(f"{topic} theory", f"Create a documented strategy guide for {topic}."),
                "resource": formatted_resource(f"{topic} theory"),
                "visual_aid": f"Concept map connecting {topic} principles."
            },
            {
                "title": f"Real-World {topic.title()} Applications",
                "topics": ["Case studies", "Project examples", "Optimization"],
                "exercise": formatted_exercise(f"real-world {topic}"),
                "mini_project": formatted_mini_project(f"real-world {topic}"),
                "resource": formatted_resource(f"{topic} applications"),
                "visual_aid": f"Diagram of a real-world {topic} system."
            },
            {
                "title": f"Mastering {topic.title()}",
                "topics": ["Advanced techniques", "Review & reflection", "Next steps"],
                "exercise": formatted_exercise(f"mastering {topic}"),
                "mini_project": formatted_mini_project(f"mastering {topic}", f"Build a complete {topic} capstone project."),
                "resource": formatted_resource(f"advanced {topic}"),
                "visual_aid": f"Mind map of {topic} mastery." 
            },
        ]

    durations = ["2 weeks", "2 weeks", "2 weeks", "3 weeks", "3 weeks"]
    modules = []
    for i, stage in enumerate(stages[:5]):
        title = stage.get("title", f"Module {i+1}: {topic}")
        topics = stage.get("topics", [f"{topic} topic {i+1}"])
        exercise = stage.get("exercise", f"Practice {topics[0] if topics else topic} daily.")
        mini_project = stage.get("mini_project", None)
        # Prefer generated SVG data-url for visual learners
        if is_visual:
            visual_aid = _svg_path_for_topics(topics, title)
        else:
            visual_aid = stage.get("visual_aid", f"Diagram for {topics[0]}")
        resource = stage.get("resource", f"{topic} learning resources")
        modules.append({
            "module_number": i + 1,
            "title": title,
            "duration": durations[i],
            "objectives": [
                f"Understand and apply {topics[0] if topics else topic}",
                f"Build confidence through {title.lower()}"
            ],
            "topics": topics,
            "resources": [resource, "Community forums & study groups"],
            "exercise": exercise,
            "mini_project": mini_project,
            "visual_aid": visual_aid,
            "quiz_questions": [f"What are the key aspects of {topics[0] if topics else topic}?"]
        })

    course_title = f"Complete {skill_level.title()} Guide to {topic}"
    overview = (
        f"A personalized {skill_level} roadmap for '{topic}', "
        f"designed for {hours_per_week} hours/week. Goal: {goal}."
    )
    return modules, course_title, overview, False, is_generic


def generate_course_json(user_input: CourseInput) -> tuple[CourseOutput, any]:
    prompt = build_prompt(user_input)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CourseOutput,
                temperature=0.5
            )
        )
        result_dict = json.loads(response.text)
        return CourseOutput(**result_dict), False
    except Exception as e:
        print(f"Gemini structured API failed: {e}. Using fallback.")
        modules, course_title, overview, is_curated, is_generic = _build_fallback_modules(
            user_input.topic,
            user_input.goal,
            user_input.skill_level,
            user_input.hours_per_week,
            user_input.learning_style
        )
        mock_data = {
            "course_title": course_title,
            "overview": overview,
            "estimated_duration": "10 Weeks",
            "modules": modules
        }
        
        # We'll use a trick to pass these flags back without breaking the schema if possible, 
        # or just handle it in the route.
        return CourseOutput(**mock_data), (is_curated, is_generic)
