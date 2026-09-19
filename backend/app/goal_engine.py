from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re

class GoalAnalysisResult(BaseModel):
    goal_type: str = "learning"
    category: str = "Learning"
    subject: Optional[str] = None
    summary: str = ""
    priority: str = "medium"
    difficulty: str = "Beginner"
    deadline: str = ""
    estimated_effort: str = "30 minutes/day"
    daily_minutes: int = 30
    required_skills: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    learning_required: bool = True
    project_required: bool = False
    assessment_required: bool = True

def detect_learning_subject(text: str) -> Optional[str]:
    low = text.lower()
    # Check for DSA
    if re.search(r'\b(dsa|data\s*structures?|algorithms?|leetcode|competitive\s*programming)\b', low):
        return "DSA"
    # Check for Python
    if re.search(r'\b(python|py|django|flask|fastapi|pandas|numpy)\b', low):
        return "Python"
    return None

def analyze_goal_deterministic(title: str, deadline: str = "", level: str = "Beginner", minutes: int = 30, priority: str = "medium", category: str = "") -> GoalAnalysisResult:
    low = title.lower()
    subject = detect_learning_subject(title)
    
    if subject == "DSA":
        return GoalAnalysisResult(
            goal_type="learning",
            category="Learning",
            subject="DSA",
            summary=f"Master Data Structures and Algorithms with progressive problem solving and concept evaluations.",
            priority=priority or "high",
            difficulty=level or "Intermediate",
            deadline=deadline or "8 weeks",
            estimated_effort=f"{minutes} minutes/day",
            daily_minutes=minutes,
            required_skills=["DSA", "Problem Solving", "Algorithm Design", "Complexity Analysis"],
            success_criteria=[
                "Solve foundational and intermediate data structure problems",
                "Demonstrate mastery over search, sort, trees, and graphs",
                "Pass comprehensive DSA assessments and boss battle"
            ],
            learning_required=True,
            project_required=False,
            assessment_required=True
        )
    elif subject == "Python":
        return GoalAnalysisResult(
            goal_type="learning",
            category="Learning",
            subject="Python",
            summary=f"Build solid Python programming mastery from syntax to data structures, OOP, and real-world scripting.",
            priority=priority or "medium",
            difficulty=level or "Beginner",
            deadline=deadline or "6 weeks",
            estimated_effort=f"{minutes} minutes/day",
            daily_minutes=minutes,
            required_skills=["Python", "Object-Oriented Programming", "Data Structures", "Debugging"],
            success_criteria=[
                "Write clean, idiomatic Python code",
                "Master functions, data structures, and OOP principles",
                "Pass topic quizzes and complete the Python boss challenge"
            ],
            learning_required=True,
            project_required=True,
            assessment_required=True
        )
    else:
        # General goal classification
        is_habit = any(w in low for w in ['daily', 'every day', 'every morning', 'every', 'morning', 'evening', 'habit', 'routine', 'meditate', 'workout'])
        is_proj = any(w in low for w in ['build', 'develop', 'create', 'project', 'app', 'website', 'launch'])
        is_learn = any(w in low for w in ['learn', 'study', 'course', 'exam', 'read', 'master'])
        
        gtype = "habit" if is_habit else "project" if is_proj else "learning" if is_learn else "task"
        cat = category or ("Health" if any(w in low for w in ['fitness', 'gym', 'workout', 'run']) else "Learning" if is_learn else "Personal")
        
        return GoalAnalysisResult(
            goal_type=gtype,
            category=cat,
            subject=None,
            summary=f"{title} organized into a structured campaign.",
            priority=priority or "medium",
            difficulty=level or "Normal",
            deadline=deadline or "4 weeks",
            estimated_effort=f"{minutes} minutes/day",
            daily_minutes=minutes,
            required_skills=[cat, "Discipline"],
            success_criteria=[f"Complete all milestones for {title}"],
            learning_required=is_learn,
            project_required=is_proj,
            assessment_required=is_learn
        )

# Curricula for dynamic campaigns
DSA_CURRICULUM = [
    {
        "milestone": "Foundations & Complexity",
        "description": "Understand time/space complexity, Big-O notation, and memory layouts.",
        "quests": [
            {"title": "Big-O Notation & Complexity", "topic": "Foundations", "subtopic": "Time & Space Complexity", "diff": 1, "obj": "Analyze time and space complexity using Big-O notation.", "type": "MCQ"},
            {"title": "Array Memory & Basic Operations", "topic": "Arrays", "subtopic": "Memory & Indexing", "diff": 1, "obj": "Understand how arrays are stored in memory and basic O(1) vs O(N) operations.", "type": "output_prediction"}
        ]
    },
    {
        "milestone": "Arrays & Strings",
        "description": "Master continuous data structures, two-pointer techniques, and sliding windows.",
        "quests": [
            {"title": "Two-Pointer Strategy", "topic": "Arrays", "subtopic": "Two Pointers", "diff": 2, "obj": "Apply the two-pointer technique to solve array search and inversion problems.", "type": "debugging"},
            {"title": "String Manipulation & Hashing", "topic": "Strings", "subtopic": "Anagrams & Frequency", "diff": 2, "obj": "Handle string indexing, frequency maps, and palindrome verification.", "type": "coding_problem"}
        ]
    },
    {
        "milestone": "Searching & Sorting",
        "description": "Implement binary search and compare fundamental sorting algorithms.",
        "quests": [
            {"title": "Binary Search Fundamentals", "topic": "Searching", "subtopic": "Binary Search", "diff": 2, "obj": "Implement binary search and identify boundary condition pitfalls.", "type": "debugging"},
            {"title": "Divide & Conquer Sorting", "topic": "Sorting", "subtopic": "Merge & Quick Sort", "diff": 3, "obj": "Trace merge sort and quick sort partition steps and analyze average/worst-case behavior.", "type": "output_prediction"}
        ]
    },
    {
        "milestone": "Linear Dynamic Structures",
        "description": "Deep dive into Linked Lists, Stacks, and Queues.",
        "quests": [
            {"title": "Singly & Doubly Linked Lists", "topic": "Linked Lists", "subtopic": "Pointers & Traversal", "diff": 3, "obj": "Implement node insertion, reversal, and cycle detection without memory leaks.", "type": "debugging"},
            {"title": "Stack & Queue Applications", "topic": "Stack", "subtopic": "Monotonic Stack & BFS Queue", "diff": 3, "obj": "Utilize stacks for parenthesis matching and queues for sequential processing.", "type": "coding_problem"}
        ]
    },
    {
        "milestone": "Trees & Graphs",
        "description": "Traverse hierarchical trees and solve graph connectivity problems.",
        "quests": [
            {"title": "Binary Search Tree Operations", "topic": "Trees", "subtopic": "BST Traversal & Invariant", "diff": 4, "obj": "Perform inorder, preorder, postorder traversals and validate BST invariants.", "type": "output_prediction"},
            {"title": "Graph Traversal (BFS & DFS)", "topic": "Graphs", "subtopic": "BFS & DFS Traversal", "diff": 4, "obj": "Traverse adjacency lists using Breadth-First and Depth-First search.", "type": "coding_problem"}
        ]
    },
    {
        "milestone": "DSA Boss: The Algorithm Trial",
        "description": "Face the multi-round DSA Boss testing complexity, data structures, and algorithmic optimization.",
        "is_boss": True,
        "quests": [
            {"title": "The Grand Algorithm Trial", "topic": "Dynamic Programming", "subtopic": "Comprehensive Evaluation", "diff": 5, "obj": "Synthesize data structures, binary search, and graph traversal under timed conditions.", "type": "mixed"}
        ]
    }
]

PYTHON_CURRICULUM = [
    {
        "milestone": "Python Basics & Syntax",
        "description": "Master Python syntax, dynamic typing, variables, and operators.",
        "quests": [
            {"title": "Python Syntax & Variable Types", "topic": "Basics", "subtopic": "Types & Operators", "diff": 1, "obj": "Understand dynamic typing, immutable vs mutable primitives, and type casting.", "type": "output_prediction"},
            {"title": "Conditional Branching & Logic", "topic": "Control Flow", "subtopic": "If-Else & Truthiness", "diff": 1, "obj": "Predict execution paths through conditional expressions and truthiness rules.", "type": "debugging"}
        ]
    },
    {
        "milestone": "Loops & Functions",
        "description": "Construct clean modular programs with loops, iterators, and functions.",
        "quests": [
            {"title": "Iterators & Comprehensions", "topic": "Control Flow", "subtopic": "List Comprehensions & Loops", "diff": 2, "obj": "Write efficient loops and concise list/dict comprehensions.", "type": "output_prediction"},
            {"title": "Function Scope & Arguments", "topic": "Functions", "subtopic": "Args, Kwargs & Closures", "diff": 2, "obj": "Define functions with default parameters, *args, **kwargs, and variable scoping.", "type": "coding_problem"}
        ]
    },
    {
        "milestone": "Python Data Structures",
        "description": "Master Python built-in structures: lists, tuples, sets, and dictionaries.",
        "quests": [
            {"title": "Lists, Dictionaries & Sets", "topic": "Data Structures", "subtopic": "Dict Hashing & Set Operations", "diff": 2, "obj": "Utilize dictionary hashing, set unions/intersections, and slice indexing.", "type": "debugging"},
            {"title": "Nested Data & Memory References", "topic": "Data Structures", "subtopic": "Shallow vs Deep Copy", "diff": 3, "obj": "Distinguish between reference assignment, shallow copies, and deep copies.", "type": "output_prediction"}
        ]
    },
    {
        "milestone": "Object-Oriented Python",
        "description": "Design modular systems using classes, inheritance, and dunder methods.",
        "quests": [
            {"title": "Classes, Instances & Methods", "topic": "OOP", "subtopic": "Self, __init__ & Methods", "diff": 3, "obj": "Construct classes with instance state and encapsulation.", "type": "coding_problem"},
            {"title": "Inheritance & Polymorphism", "topic": "OOP", "subtopic": "Super, Inheritance & MRO", "diff": 4, "obj": "Implement subclassing, super() calls, and method resolution order.", "type": "debugging"}
        ]
    },
    {
        "milestone": "Exceptions, Files & Modules",
        "description": "Handle runtime errors gracefully and structure multi-file modules.",
        "quests": [
            {"title": "Robust Exception Handling", "topic": "Exceptions", "subtopic": "Try-Except-Finally", "diff": 3, "obj": "Handle custom exceptions, catch specific errors, and manage resource cleanup.", "type": "debugging"},
            {"title": "File I/O & Context Managers", "topic": "Files", "subtopic": "With Statement & File I/O", "diff": 3, "obj": "Read/write files safely using context managers and serialize JSON data.", "type": "coding_problem"}
        ]
    },
    {
        "milestone": "Python Boss: The Master Developer Challenge",
        "description": "Defeat the Python Boss across OOP, data structures, and robust exception handling.",
        "is_boss": True,
        "quests": [
            {"title": "Python Architecture Boss Challenge", "topic": "Modules", "subtopic": "Full Python Architecture", "diff": 5, "obj": "Demonstrate end-to-end Python mastery with clean architecture and robust error handling.", "type": "mixed"}
        ]
    }
]

def get_curriculum_for_subject(subject: str) -> Optional[List[Dict[str, Any]]]:
    if subject == "DSA":
        return DSA_CURRICULUM
    elif subject == "Python":
        return PYTHON_CURRICULUM
    return None
