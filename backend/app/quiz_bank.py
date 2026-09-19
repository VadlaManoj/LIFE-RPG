from typing import Dict, List, Any

QUIZ_BANK: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "DSA": {
        "Foundations": [
            {
                "id": "dsa_fnd_1",
                "question_type": "mcq",
                "question": "What is the worst-case time complexity of accessing an element by index in a standard static array?",
                "options": ["O(1)", "O(log N)", "O(N)", "O(N^2)"],
                "correct_answer": 0,
                "explanation": "Static arrays store elements in contiguous memory locations, allowing O(1) random access using pointer arithmetic.",
                "points": 10,
                "topic": "Foundations",
                "subtopic": "Time & Space Complexity",
                "difficulty": 1
            },
            {
                "id": "dsa_fnd_2",
                "question_type": "output_prediction",
                "question": "What is the time complexity of the following code snippet?\n\n```python\ni = 1\ncount = 0\nwhile i < n:\n    count += 1\n    i *= 2\n```\nProvide Big-O notation (e.g., O(log n), O(n), etc.).",
                "correct_answer": "O(log n)",
                "options": [],
                "explanation": "Since `i` doubles each iteration (1, 2, 4, 8, ...), the loop executes log2(n) times, resulting in O(log n) time complexity.",
                "points": 15,
                "topic": "Foundations",
                "subtopic": "Time & Space Complexity",
                "difficulty": 1
            }
        ],
        "Arrays": [
            {
                "id": "dsa_arr_1",
                "question_type": "output_prediction",
                "question": "What does the following two-pointer code return for nums = [1, 2, 3, 4, 5]?\n\n```python\ndef mystery(nums):\n    l, r = 0, len(nums) - 1\n    while l < r:\n        nums[l], nums[r] = nums[r], nums[l]\n        l += 1\n        r -= 1\n    return nums\n```",
                "correct_answer": "[5, 4, 3, 2, 1]",
                "options": [],
                "explanation": "The code swaps elements from both ends moving inward, reversing the array in O(N) time and O(1) auxiliary space.",
                "points": 15,
                "topic": "Arrays",
                "subtopic": "Two Pointers",
                "difficulty": 2
            },
            {
                "id": "dsa_arr_2",
                "question_type": "debugging",
                "question": "The following function is supposed to remove duplicates from a sorted array in-place and return the new length. However, it contains a bug. Identify the bug or provide the correct line for updating the unique pointer.\n\n```python\ndef remove_duplicates(nums):\n    if not nums: return 0\n    write_idx = 1\n    for i in range(1, len(nums)):\n        if nums[i] != nums[i - 1]:\n            nums[write_idx] = nums[i]\n            # missing step\n    return write_idx\n```",
                "correct_answer": "write_idx += 1",
                "options": [],
                "explanation": "After copying the unique element to nums[write_idx], write_idx must be incremented (`write_idx += 1`).",
                "points": 20,
                "topic": "Arrays",
                "subtopic": "Two Pointers",
                "difficulty": 2
            },
            {
                "id": "dsa_arr_3",
                "question_type": "short_answer",
                "question": "Explain why inserting an element at the beginning of an array of size N takes O(N) time.",
                "correct_answer": "All existing N elements must be shifted one position to the right to make room at index 0.",
                "keywords": ["shift", "contiguous", "position", "move", "index 0", "right"],
                "options": [],
                "explanation": "Because array elements must remain contiguous in memory, adding at index 0 requires shifting all N elements one slot to the right.",
                "points": 15,
                "topic": "Arrays",
                "subtopic": "Memory & Indexing",
                "difficulty": 1
            }
        ],
        "Strings": [
            {
                "id": "dsa_str_1",
                "question_type": "mcq",
                "question": "Which of the following techniques is most optimal for checking if two strings of length N are anagrams?",
                "options": [
                    "Sort both strings and compare (O(N log N) time, O(1) or O(N) space)",
                    "Character frequency count map (O(N) time, O(1) space if alphabet is fixed)",
                    "Generate all permutations of string 1 (O(N!) time)",
                    "Nested loops comparing each character (O(N^2) time)"
                ],
                "correct_answer": 1,
                "explanation": "Counting character frequencies using a hash map or 26-element array operates in linear O(N) time with constant O(1) extra space for standard alphabets.",
                "points": 15,
                "topic": "Strings",
                "subtopic": "Anagrams & Frequency",
                "difficulty": 2
            },
            {
                "id": "dsa_str_2",
                "question_type": "coding_problem",
                "question": "Write a function `is_palindrome(s: str) -> bool` that checks if a string is a palindrome considering only alphanumeric characters and ignoring cases. Provide the key return expression or two-pointer logic.",
                "correct_answer": "clean = [c.lower() for c in s if c.isalnum()]; return clean == clean[::-1]",
                "evaluation_criteria": {
                    "required_patterns": ["isalnum", "lower", "=="],
                    "sample_solution": "def is_palindrome(s):\n    c = [ch.lower() for ch in s if ch.isalnum()]\n    return c == c[::-1]"
                },
                "options": [],
                "explanation": "Filter non-alphanumeric characters, convert to lowercase, and check if the sequence reads identically forwards and backwards.",
                "points": 25,
                "topic": "Strings",
                "subtopic": "Two Pointers",
                "difficulty": 2
            }
        ],
        "Searching": [
            {
                "id": "dsa_srch_1",
                "question_type": "debugging",
                "question": "Find the bug causing an infinite loop in this binary search implementation when the target is not in the array:\n\n```python\ndef binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid\n        else:\n            high = mid\n    return -1\n```",
                "correct_answer": "low = mid + 1 and high = mid - 1",
                "options": [],
                "explanation": "When arr[mid] != target, we must advance past mid (`low = mid + 1` and `high = mid - 1`), otherwise the search window fails to shrink.",
                "points": 20,
                "topic": "Searching",
                "subtopic": "Binary Search",
                "difficulty": 2
            },
            {
                "id": "dsa_srch_2",
                "question_type": "mcq",
                "question": "In binary search on an array of 1,000,000 sorted elements, what is the maximum number of comparisons needed?",
                "options": ["20", "1000", "500,000", "1,000,000"],
                "correct_answer": 0,
                "explanation": "ceil(log2(1,000,000)) ≈ 20, because 2^20 = 1,048,576.",
                "points": 15,
                "topic": "Searching",
                "subtopic": "Binary Search",
                "difficulty": 2
            }
        ],
        "Sorting": [
            {
                "id": "dsa_sort_1",
                "question_type": "mcq",
                "question": "Which sorting algorithm is stable and guarantees O(N log N) worst-case time complexity?",
                "options": ["Quick Sort", "Merge Sort", "Heap Sort", "Selection Sort"],
                "correct_answer": 1,
                "explanation": "Merge Sort always guarantees O(N log N) time complexity across best, average, and worst cases, and preserves relative order of duplicate elements (stable).",
                "points": 15,
                "topic": "Sorting",
                "subtopic": "Merge & Quick Sort",
                "difficulty": 3
            },
            {
                "id": "dsa_sort_2",
                "question_type": "output_prediction",
                "question": "What is the worst-case time complexity of Quick Sort when the pivot is always chosen as the smallest or largest element?\nWrite in Big-O format (e.g. O(N^2), O(N log N)).",
                "correct_answer": "O(N^2)",
                "options": [],
                "explanation": "If the partition creates unbalanced subproblems of size 0 and N-1, the recursion tree height is N, yielding O(N^2) comparisons.",
                "points": 15,
                "topic": "Sorting",
                "subtopic": "Merge & Quick Sort",
                "difficulty": 3
            }
        ],
        "Linked Lists": [
            {
                "id": "dsa_ll_1",
                "question_type": "debugging",
                "question": "The following code tries to reverse a singly linked list. Find the missing pointer update inside the loop:\n\n```python\nprev = None\ncurr = head\nwhile curr:\n    nxt = curr.next\n    curr.next = prev\n    # missing assignments\n```",
                "correct_answer": "prev = curr; curr = nxt",
                "options": [],
                "explanation": "To advance, we set `prev = curr` and `curr = nxt` for the next iteration.",
                "points": 20,
                "topic": "Linked Lists",
                "subtopic": "Pointers & Traversal",
                "difficulty": 3
            },
            {
                "id": "dsa_ll_2",
                "question_type": "mcq",
                "question": "What algorithm detects a cycle in a linked list using O(1) memory?",
                "options": [
                    "Floyd's Tortoise and Hare (Slow/Fast Pointers)",
                    "Dijkstra's Shortest Path",
                    "Kruskal's Algorithm",
                    "Binary Search Traversal"
                ],
                "correct_answer": 0,
                "explanation": "Floyd's algorithm uses two pointers moving at different speeds (1 step vs 2 steps). If there is a cycle, they will meet in O(N) time and O(1) space.",
                "points": 15,
                "topic": "Linked Lists",
                "subtopic": "Cycle Detection",
                "difficulty": 3
            }
        ],
        "Stack": [
            {
                "id": "dsa_stk_1",
                "question_type": "output_prediction",
                "question": "What does this stack code output?\n\n```python\nstk = []\nfor c in \"({[]})\":\n    if c in \"({[\":\n        stk.append(c)\n    elif stk:\n        stk.pop()\nprint(len(stk))\n```",
                "correct_answer": "0",
                "options": [],
                "explanation": "All 3 opening brackets are pushed, then matched by 3 closing brackets which pop them all, leaving an empty stack with length 0.",
                "points": 15,
                "topic": "Stack",
                "subtopic": "Monotonic Stack & BFS Queue",
                "difficulty": 2
            }
        ],
        "Trees": [
            {
                "id": "dsa_tree_1",
                "question_type": "output_prediction",
                "question": "Given a Binary Search Tree with nodes inserted in order: [4, 2, 6, 1, 3, 5, 7]. What does the INORDER traversal produce? (Format: [1, 2, 3, 4, 5, 6, 7])",
                "correct_answer": "[1, 2, 3, 4, 5, 6, 7]",
                "options": [],
                "explanation": "Inorder traversal (Left, Root, Right) of any valid Binary Search Tree yields elements in strictly sorted ascending order.",
                "points": 20,
                "topic": "Trees",
                "subtopic": "BST Traversal & Invariant",
                "difficulty": 3
            }
        ],
        "Graphs": [
            {
                "id": "dsa_graph_1",
                "question_type": "mcq",
                "question": "Which data structure is typically used to implement Breadth-First Search (BFS) on a graph?",
                "options": ["Queue (FIFO)", "Stack (LIFO)", "Priority Queue / Min-Heap", "Binary Search Tree"],
                "correct_answer": 0,
                "explanation": "BFS explores vertices layer by layer using a First-In-First-Out (FIFO) queue.",
                "points": 15,
                "topic": "Graphs",
                "subtopic": "BFS & DFS Traversal",
                "difficulty": 3
            }
        ],
        "Dynamic Programming": [
            {
                "id": "dsa_dp_1",
                "question_type": "output_prediction",
                "question": "What is the value of fib(5) computed using dynamic programming where fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)?",
                "correct_answer": "5",
                "options": [],
                "explanation": "fib(0)=0, fib(1)=1, fib(2)=1, fib(3)=2, fib(4)=3, fib(5)=5.",
                "points": 15,
                "topic": "Dynamic Programming",
                "subtopic": "Memoization & Tabulation",
                "difficulty": 3
            }
        ]
    },
    "Python": {
        "Basics": [
            {
                "id": "py_bas_1",
                "question_type": "output_prediction",
                "question": "What is the output of the following Python code?\n\n```python\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(len(x))\n```",
                "correct_answer": "4",
                "options": [],
                "explanation": "`y = x` assigns a reference to the same list in memory. Mutating `y` also mutates `x`.",
                "points": 15,
                "topic": "Basics",
                "subtopic": "Types & Operators",
                "difficulty": 1
            },
            {
                "id": "py_bas_2",
                "question_type": "mcq",
                "question": "Which of the following Python data types is immutable?",
                "options": ["tuple", "list", "dict", "set"],
                "correct_answer": 0,
                "explanation": "Tuples cannot be modified after creation, making them immutable. Lists, dictionaries, and sets are mutable.",
                "points": 10,
                "topic": "Basics",
                "subtopic": "Types & Operators",
                "difficulty": 1
            }
        ],
        "Control Flow": [
            {
                "id": "py_cf_1",
                "question_type": "output_prediction",
                "question": "What is the output of this list comprehension?\n\n```python\nnums = [x * 2 for x in range(5) if x % 2 == 1]\nprint(nums)\n```",
                "correct_answer": "[2, 6]",
                "options": [],
                "explanation": "range(5) produces 0, 1, 2, 3, 4. The condition `x % 2 == 1` selects 1 and 3. Multiplying each by 2 yields [2, 6].",
                "points": 15,
                "topic": "Control Flow",
                "subtopic": "List Comprehensions & Loops",
                "difficulty": 2
            },
            {
                "id": "py_cf_2",
                "question_type": "debugging",
                "question": "What causes an unexpected result in the following loop, and how should it be fixed?\n\n```python\nitems = [1, 2, 3, 4, 5]\nfor x in items:\n    if x % 2 == 0:\n        items.remove(x)\n```",
                "correct_answer": "Mutating a list while iterating over it skips elements. Iterate over a copy: `for x in items[:]:`",
                "options": [],
                "explanation": "Modifying a list during iteration shifts subsequent elements forward, causing the loop iterator to skip items. Use `items[:]` or a list comprehension.",
                "points": 20,
                "topic": "Control Flow",
                "subtopic": "List Comprehensions & Loops",
                "difficulty": 2
            }
        ],
        "Functions": [
            {
                "id": "py_fn_1",
                "question_type": "output_prediction",
                "question": "What does this code print?\n\n```python\ndef append_to(val, target=[]):\n    target.append(val)\n    return target\n\nprint(append_to(1))\nprint(append_to(2))\n```\nProvide output for the second print statement.",
                "correct_answer": "[1, 2]",
                "options": [],
                "explanation": "Default argument expressions in Python are evaluated once at function definition time. The mutable list `target` is shared across calls.",
                "points": 20,
                "topic": "Functions",
                "subtopic": "Args, Kwargs & Closures",
                "difficulty": 2
            },
            {
                "id": "py_fn_2",
                "question_type": "mcq",
                "question": "In Python, what does `*args` unpack in a function signature?",
                "options": [
                    "Arbitrary positional arguments into a tuple",
                    "Arbitrary keyword arguments into a dictionary",
                    "Default parameters into a list",
                    "Global variables into local scope"
                ],
                "correct_answer": 0,
                "explanation": "`*args` collects extra positional arguments as a tuple, while `**kwargs` collects keyword arguments into a dict.",
                "points": 10,
                "topic": "Functions",
                "subtopic": "Args, Kwargs & Closures",
                "difficulty": 1
            }
        ],
        "Data Structures": [
            {
                "id": "py_ds_1",
                "question_type": "output_prediction",
                "question": "What does the following dictionary operation output?\n\n```python\nd = {'a': 1, 'b': 2}\nprint(d.get('c', 0) + d.get('a', 0))\n```",
                "correct_answer": "1",
                "options": [],
                "explanation": "d.get('c', 0) returns the default value 0 because 'c' is absent, and d.get('a', 0) returns 1. 0 + 1 = 1.",
                "points": 15,
                "topic": "Data Structures",
                "subtopic": "Dict Hashing & Set Operations",
                "difficulty": 2
            },
            {
                "id": "py_ds_2",
                "question_type": "debugging",
                "question": "Why does using an unhashable type as a dictionary key fail?\n\n```python\nd = {}\nd[[1, 2]] = 'val'\n```\nWhat exception is raised?",
                "correct_answer": "TypeError: unhashable type: 'list'",
                "options": [],
                "explanation": "Dictionary keys must be hashable and immutable so their hash value remains invariant. Lists are mutable and therefore unhashable.",
                "points": 15,
                "topic": "Data Structures",
                "subtopic": "Dict Hashing & Set Operations",
                "difficulty": 2
            }
        ],
        "OOP": [
            {
                "id": "py_oop_1",
                "question_type": "output_prediction",
                "question": "What is the output of this code?\n\n```python\nclass Hero:\n    species = 'Human'\n    def __init__(self, name):\n        self.name = name\n\nh1 = Hero('Arthur')\nh2 = Hero('Lancelot')\nHero.species = 'Legend'\nprint(f'{h1.species} & {h2.species}')\n```",
                "correct_answer": "Legend & Legend",
                "options": [],
                "explanation": "Both instances reference the class variable `species`. Changing `Hero.species` updates the attribute accessed across all instances without instance-level overrides.",
                "points": 20,
                "topic": "OOP",
                "subtopic": "Self, __init__ & Methods",
                "difficulty": 3
            },
            {
                "id": "py_oop_2",
                "question_type": "debugging",
                "question": "What is missing in `Child.__init__` to properly initialize the parent class `Parent`?\n\n```python\nclass Parent:\n    def __init__(self, val):\n        self.val = val\n\nclass Child(Parent):\n    def __init__(self, val, extra):\n        # missing call\n        self.extra = extra\n```",
                "correct_answer": "super().__init__(val)",
                "options": [],
                "explanation": "`super().__init__(val)` invokes the parent class initializer to set up inherited instance attributes.",
                "points": 20,
                "topic": "OOP",
                "subtopic": "Super, Inheritance & MRO",
                "difficulty": 3
            }
        ],
        "Exceptions": [
            {
                "id": "py_exc_1",
                "question_type": "output_prediction",
                "question": "What does this code print?\n\n```python\ndef test():\n    try:\n        return 1\n    finally:\n        return 2\nprint(test())\n```",
                "correct_answer": "2",
                "options": [],
                "explanation": "The `finally` block is guaranteed to execute before returning, so its return statement overrides the return from the `try` block.",
                "points": 20,
                "topic": "Exceptions",
                "subtopic": "Try-Except-Finally",
                "difficulty": 3
            }
        ],
        "Files": [
            {
                "id": "py_file_1",
                "question_type": "short_answer",
                "question": "What is the primary benefit of using a `with open(...)` context manager when working with files in Python?",
                "correct_answer": "It guarantees that the file will be automatically closed when exiting the block, even if an exception occurs.",
                "keywords": ["automatically", "close", "exception", "resource", "cleanup", "exit"],
                "options": [],
                "explanation": "Context managers implement `__enter__` and `__exit__`, ensuring deterministic file descriptor cleanup even during unexpected errors.",
                "points": 15,
                "topic": "Files",
                "subtopic": "With Statement & File I/O",
                "difficulty": 2
            }
        ],
        "Modules": [
            {
                "id": "py_mod_1",
                "question_type": "mcq",
                "question": "What is the purpose of the `if __name__ == '__main__':` boilerplate in Python scripts?",
                "options": [
                    "To allow code to run when executed directly, but not when imported as a module",
                    "To declare private classes",
                    "To enable multiprocessing threads",
                    "To benchmark script execution time"
                ],
                "correct_answer": 0,
                "explanation": "When a file is imported, `__name__` is set to the module's name. When run directly, `__name__` is `'__main__'`. This guard separates executable code from library imports.",
                "points": 10,
                "topic": "Modules",
                "subtopic": "Full Python Architecture",
                "difficulty": 2
            }
        ]
    }
}

BOSS_QUIZZES: Dict[str, List[Dict[str, Any]]] = {
    "DSA": [
        {
            "id": "dsa_boss_r1",
            "round": 1,
            "round_name": "Round 1: Complexity & Invariants",
            "question_type": "mcq",
            "question": "Which of the following operations has O(1) amortized time complexity?",
            "options": [
                "Appending to a dynamic array (Python list)",
                "Inserting at index 0 of an array",
                "Finding an element in an unsorted array",
                "Reversing a singly linked list"
            ],
            "correct_answer": 0,
            "explanation": "Dynamic arrays double their capacity when full, spreading the cost of O(N) reallocation across N insertions for O(1) amortized append.",
            "points": 25,
            "topic": "Foundations",
            "subtopic": "Amortized Analysis",
            "difficulty": 4
        },
        {
            "id": "dsa_boss_r2",
            "round": 2,
            "round_name": "Round 2: Problem Solving & Binary Search",
            "question_type": "output_prediction",
            "question": "In rotated sorted array [4, 5, 6, 7, 0, 1, 2], which condition correctly decides whether the left half [low..mid] is strictly sorted?\nFormat: arr[low] <= arr[mid]",
            "correct_answer": "arr[low] <= arr[mid]",
            "options": [],
            "explanation": "If arr[low] <= arr[mid], the left portion contains no rotation inflection point and is strictly sorted.",
            "points": 25,
            "topic": "Searching",
            "subtopic": "Rotated Binary Search",
            "difficulty": 4
        },
        {
            "id": "dsa_boss_r3",
            "round": 3,
            "round_name": "Round 3: Debugging Data Structures",
            "question_type": "debugging",
            "question": "Identify the bug in this BFS queue traversal causing cycles to loop infinitely:\n\n```python\nqueue = [start]\nwhile queue:\n    node = queue.pop(0)\n    for neighbor in graph[node]:\n        queue.append(neighbor)\n```",
            "correct_answer": "Missing visited set to track already seen nodes",
            "options": [],
            "explanation": "Without maintaining a `visited` set or marking nodes when enqueued, cycles lead to infinite enqueuing.",
            "points": 25,
            "topic": "Graphs",
            "subtopic": "BFS Traversal",
            "difficulty": 4
        },
        {
            "id": "dsa_boss_r4",
            "round": 4,
            "round_name": "Round 4: Algorithmic Synthesis",
            "question_type": "short_answer",
            "question": "What two conditions must a problem satisfy to be solvable with Dynamic Programming?",
            "correct_answer": "Optimal substructure and overlapping subproblems.",
            "keywords": ["optimal substructure", "overlapping subproblems", "subproblems", "substructure", "memoization"],
            "options": [],
            "explanation": "Dynamic Programming applies when an optimal solution can be constructed from optimal solutions to subproblems (optimal substructure) and the same subproblems are solved repeatedly (overlapping subproblems).",
            "points": 25,
            "topic": "Dynamic Programming",
            "subtopic": "DP Principles",
            "difficulty": 5
        }
    ],
    "Python": [
        {
            "id": "py_boss_r1",
            "round": 1,
            "round_name": "Round 1: Language Semantics & Scoping",
            "question_type": "output_prediction",
            "question": "What is the output of this closure?\n\n```python\nfuncs = [lambda x, i=i: x + i for i in range(3)]\nprint([f(10) for f in funcs])\n```",
            "correct_answer": "[10, 11, 12]",
            "options": [],
            "explanation": "Using the default parameter `i=i` binds `i` to the current iteration value rather than capturing the late-binding loop variable.",
            "points": 25,
            "topic": "Functions",
            "subtopic": "Closures & Late Binding",
            "difficulty": 4
        },
        {
            "id": "py_boss_r2",
            "round": 2,
            "round_name": "Round 2: OOP & Method Resolution Order",
            "question_type": "output_prediction",
            "question": "What does `C.mro()` prioritize in multiple inheritance:\n\n```python\nclass A: pass\nclass B(A): pass\nclass C(B): pass\n```\nDoes B come before A in C's MRO? Answer 'yes' or 'no'.",
            "correct_answer": "yes",
            "options": [],
            "explanation": "Python's C3 Linearization ensures subclasses precede their parent classes in the MRO: [C, B, A, object].",
            "points": 25,
            "topic": "OOP",
            "subtopic": "MRO & C3 Linearization",
            "difficulty": 4
        },
        {
            "id": "py_boss_r3",
            "round": 3,
            "round_name": "Round 3: Advanced Debugging",
            "question_type": "debugging",
            "question": "Why does this context manager raise an unhandled exception despite having a try-except?\n\n```python\nclass SafeResource:\n    def __enter__(self):\n        return self\n    def __exit__(self, exc_type, exc_val, exc_tb):\n        return False\n```\nHow can `__exit__` suppress the handled exception?",
            "correct_answer": "Return True from __exit__",
            "options": [],
            "explanation": "If `__exit__` returns `True`, Python suppresses the active exception. Returning `False` (or None) allows the exception to propagate.",
            "points": 25,
            "topic": "Files",
            "subtopic": "Context Managers",
            "difficulty": 4
        },
        {
            "id": "py_boss_r4",
            "round": 4,
            "round_name": "Round 4: Architecture Synthesis",
            "question_type": "short_answer",
            "question": "What is the difference between `@staticmethod` and `@classmethod` in Python classes?",
            "correct_answer": "@classmethod receives the class (`cls`) as its first argument, while @staticmethod receives no implicit first argument.",
            "keywords": ["cls", "class", "implicit", "first argument", "self", "instance"],
            "options": [],
            "explanation": "@classmethod gets passed `cls` allowing factory methods or inheritance-aware operations; @staticmethod behaves like a regular function scoped inside the class namespace.",
            "points": 25,
            "topic": "OOP",
            "subtopic": "Decorators & Metaprogramming",
            "difficulty": 5
        }
    ]
}
