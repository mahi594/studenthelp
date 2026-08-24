"""
Seed the database with an admin account, curated companies + rounds, and
approved quiz questions.

Run directly (no server needs to be running):
    cd backend && ./venv/bin/python scripts/seed_content.py

Idempotent - safe to re-run. Skips anything that already exists by name/email.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from passlib.context import CryptContext

from app.db.database import SessionLocal
from app.models.user import User
from app.models.company import Company, Round
from app.models.quiz_question import QuizQuestion

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_EMAIL = "admin@studenthelp.dev"
ADMIN_PASSWORD = "ChangeMe123!"  # change this after first login

COMPANIES = [
    {
        "name": "Google",
        "roles": ["SDE-1", "APM"],
        "tags": ["product-based", "faang"],
        "min_cgpa": "8.0",
        "preferred_branches": ["CSE", "IT", "ECE"],
        "resume_keywords": ["DSA", "System Design", "Python", "Java"],
        "apply_url": "https://careers.google.com/students/",
        "rounds": [
            {"order_index": 1, "round_type": "OA", "subjects_tested": ["DSA"], "difficulty": "Hard",
             "notes": "2 coding questions, 90 minutes, on Google's own platform."},
            {"order_index": 2, "round_type": "Technical", "subjects_tested": ["DSA", "System Design"], "difficulty": "Hard",
             "notes": "Two back-to-back technical rounds focused on algorithms and problem-solving approach."},
            {"order_index": 3, "round_type": "HR", "subjects_tested": ["Behavioral"], "difficulty": "Medium",
             "notes": "Googleyness and leadership questions."},
        ],
    },
    {
        "name": "Microsoft",
        "roles": ["SDE-1"],
        "tags": ["product-based", "faang-adjacent"],
        "min_cgpa": "7.5",
        "preferred_branches": ["CSE", "IT", "ECE"],
        "resume_keywords": ["DSA", "OOP", "C#", "Azure"],
        "apply_url": "https://careers.microsoft.com/students/",
        "rounds": [
            {"order_index": 1, "round_type": "OA", "subjects_tested": ["DSA", "Aptitude"], "difficulty": "Medium",
             "notes": "1 coding question + MCQs on CS fundamentals."},
            {"order_index": 2, "round_type": "Technical", "subjects_tested": ["DSA", "OOP"], "difficulty": "Medium",
             "notes": "Focus on clean code and edge cases, not just the correct approach."},
            {"order_index": 3, "round_type": "Technical", "subjects_tested": ["System Design", "DBMS"], "difficulty": "Hard"},
            {"order_index": 4, "round_type": "HR", "subjects_tested": ["Behavioral"], "difficulty": "Easy"},
        ],
    },
    {
        "name": "Amazon",
        "roles": ["SDE-1"],
        "tags": ["product-based", "faang"],
        "min_cgpa": "7.0",
        "preferred_branches": ["CSE", "IT", "ECE", "EEE"],
        "resume_keywords": ["DSA", "Leadership Principles", "AWS"],
        "apply_url": "https://www.amazon.jobs/en/teams/university",
        "rounds": [
            {"order_index": 1, "round_type": "OA", "subjects_tested": ["DSA"], "difficulty": "Medium",
             "notes": "2 coding questions + a work-style assessment (Leadership Principles)."},
            {"order_index": 2, "round_type": "Technical", "subjects_tested": ["DSA"], "difficulty": "Hard"},
            {"order_index": 3, "round_type": "Technical", "subjects_tested": ["DSA", "System Design"], "difficulty": "Hard",
             "notes": "Every technical round also probes Leadership Principles via 'tell me about a time...' questions."},
            {"order_index": 4, "round_type": "HR", "subjects_tested": ["Behavioral"], "difficulty": "Medium"},
        ],
    },
    {
        "name": "TCS",
        "roles": ["Ninja", "Digital"],
        "tags": ["service-based", "mass-recruiter"],
        "min_cgpa": "6.0",
        "preferred_branches": ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"],
        "resume_keywords": ["Aptitude", "Communication"],
        "apply_url": "https://www.tcs.com/careers",
        "rounds": [
            {"order_index": 1, "round_type": "OA", "subjects_tested": ["Aptitude", "DSA"], "difficulty": "Easy",
             "notes": "NQT: quantitative aptitude, reasoning, verbal, plus basic coding."},
            {"order_index": 2, "round_type": "Technical", "subjects_tested": ["DSA", "DBMS", "OOP"], "difficulty": "Easy"},
            {"order_index": 3, "round_type": "HR", "subjects_tested": ["Behavioral"], "difficulty": "Easy"},
        ],
    },
    {
        "name": "Infosys",
        "roles": ["SP", "Digital Specialist Engineer"],
        "tags": ["service-based", "mass-recruiter"],
        "min_cgpa": "6.5",
        "preferred_branches": ["CSE", "IT", "ECE", "EEE", "MECH"],
        "resume_keywords": ["Aptitude", "Communication"],
        "apply_url": "https://www.infosys.com/careers/",
        "rounds": [
            {"order_index": 1, "round_type": "OA", "subjects_tested": ["Aptitude"], "difficulty": "Easy",
             "notes": "InfyTQ-style aptitude + basic programming."},
            {"order_index": 2, "round_type": "Technical", "subjects_tested": ["DSA", "OOP"], "difficulty": "Easy"},
            {"order_index": 3, "round_type": "HR", "subjects_tested": ["Behavioral"], "difficulty": "Easy"},
        ],
    },
    {
        "name": "Razorpay",
        "roles": ["SDE-1"],
        "tags": ["product-based", "fintech", "startup"],
        "min_cgpa": "7.5",
        "preferred_branches": ["CSE", "IT"],
        "resume_keywords": ["DSA", "System Design", "Node.js", "Go"],
        "apply_url": "https://razorpay.com/jobs/",
        "rounds": [
            {"order_index": 1, "round_type": "OA", "subjects_tested": ["DSA"], "difficulty": "Medium"},
            {"order_index": 2, "round_type": "Technical", "subjects_tested": ["DSA", "System Design"], "difficulty": "Hard",
             "notes": "Strong emphasis on real-world system design given fintech scale."},
            {"order_index": 3, "round_type": "HR", "subjects_tested": ["Behavioral"], "difficulty": "Medium"},
        ],
    },
]

# (subject, question_text, options, correct_index, explanation, difficulty)
QUIZ_QUESTIONS = [
    ("DSA", "What is the time complexity of binary search on a sorted array of n elements?",
     ["O(n)", "O(log n)", "O(n log n)", "O(1)"], 1,
     "Binary search halves the search space each step, giving O(log n).", "Easy"),
    ("DSA", "Which data structure is best suited for implementing a LRU cache?",
     ["Array", "Stack", "HashMap + Doubly Linked List", "Binary Search Tree"], 2,
     "A hashmap gives O(1) lookup, a doubly linked list gives O(1) reordering/eviction.", "Medium"),
    ("DSA", "What is the worst-case time complexity of quicksort?",
     ["O(n log n)", "O(n^2)", "O(log n)", "O(n)"], 1,
     "Worst case occurs with a poor pivot choice (e.g. already-sorted input with a naive pivot).", "Medium"),
    ("DSA", "Which traversal of a binary search tree visits nodes in sorted order?",
     ["Pre-order", "Post-order", "In-order", "Level-order"], 2,
     "In-order traversal (left, root, right) visits BST nodes in ascending order.", "Easy"),
    ("DSA", "What does dynamic programming primarily optimize for?",
     ["Space only", "Recomputing overlapping subproblems", "Sorting speed", "Memory allocation"], 1,
     "DP avoids recomputation by storing (memoizing) results of overlapping subproblems.", "Medium"),
    ("DBMS", "Which normal form eliminates transitive dependency?",
     ["1NF", "2NF", "3NF", "BCNF"], 2,
     "3NF requires no non-key attribute to depend transitively on the primary key.", "Medium"),
    ("DBMS", "Which SQL clause is used to filter groups after aggregation?",
     ["WHERE", "HAVING", "GROUP BY", "ORDER BY"], 1,
     "HAVING filters aggregated results; WHERE filters rows before aggregation.", "Easy"),
    ("DBMS", "What does ACID stand for in database transactions?",
     ["Atomicity, Consistency, Isolation, Durability", "Access, Control, Integrity, Data",
      "Atomicity, Concurrency, Isolation, Data", "Availability, Consistency, Isolation, Durability"], 0,
     "ACID properties guarantee reliable transaction processing.", "Easy"),
    ("DBMS", "Which type of join returns only matching rows from both tables?",
     ["LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "FULL OUTER JOIN"], 2,
     "INNER JOIN returns only rows with matches in both tables.", "Easy"),
    ("OS", "What is a deadlock?",
     ["A process running forever", "Two or more processes waiting on each other's resources indefinitely",
      "A process using 100% CPU", "A memory leak"], 1,
     "Deadlock is a circular wait where each process holds a resource another needs.", "Medium"),
    ("OS", "Which scheduling algorithm can cause starvation?",
     ["Round Robin", "FCFS", "Priority Scheduling (without aging)", "SJF with no priority"], 2,
     "Without aging, low-priority processes can wait indefinitely under Priority Scheduling.", "Medium"),
    ("OS", "What is thrashing in the context of virtual memory?",
     ["Fast page access", "Excessive paging causing low CPU utilization", "CPU overheating",
      "Disk defragmentation"], 1,
     "Thrashing occurs when the system spends more time paging than executing.", "Medium"),
    ("OS", "Which of these is NOT one of the four necessary conditions for deadlock?",
     ["Mutual exclusion", "Hold and wait", "Preemption", "Circular wait"], 2,
     "The condition is 'no preemption', not 'preemption' - preemption prevents deadlock.", "Hard"),
    ("CN", "Which layer of the OSI model is responsible for routing?",
     ["Data Link", "Network", "Transport", "Session"], 1,
     "The Network layer (Layer 3) handles logical addressing and routing.", "Easy"),
    ("CN", "What is the primary difference between TCP and UDP?",
     ["TCP is connectionless, UDP is connection-oriented",
      "TCP is connection-oriented and reliable, UDP is connectionless and unreliable",
      "Both are identical in reliability", "UDP guarantees ordering, TCP does not"], 1,
     "TCP establishes a connection and guarantees delivery/order; UDP does not.", "Easy"),
    ("CN", "What does DNS primarily do?",
     ["Encrypts traffic", "Translates domain names to IP addresses", "Assigns MAC addresses",
      "Manages firewall rules"], 1,
     "DNS resolves human-readable domain names into IP addresses.", "Easy"),
    ("Aptitude", "A train 120m long is running at 60 km/hr. How long will it take to cross a platform 180m long?",
     ["10.2 sec", "18 sec", "20 sec", "12 sec"], 1,
     "Total distance = 300m, speed = 60*5/18 m/s ≈ 16.67 m/s, time = 300/16.67 ≈ 18 sec.", "Medium"),
    ("Aptitude", "If the ratio of two numbers is 3:5 and their sum is 128, what is the larger number?",
     ["48", "60", "80", "96"], 2,
     "3x+5x=128 → x=16, larger number = 5*16 = 80.", "Easy"),
    ("Aptitude", "What is the probability of getting a sum of 7 when two dice are rolled?",
     ["1/6", "1/12", "1/36", "7/36"], 0,
     "6 favorable outcomes out of 36 total → 6/36 = 1/6.", "Medium"),
    ("OOP", "Which OOP principle allows a subclass to provide a specific implementation of a method already defined in its superclass?",
     ["Encapsulation", "Abstraction", "Polymorphism (Overriding)", "Composition"], 2,
     "Method overriding is a form of runtime polymorphism.", "Easy"),
    ("OOP", "What is the main benefit of encapsulation?",
     ["Faster execution", "Bundling data and methods while restricting direct access to internals",
      "Multiple inheritance", "Automatic memory management"], 1,
     "Encapsulation hides internal state and exposes controlled access via methods.", "Easy"),
]


def get_or_create_admin(db) -> User:
    admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if admin:
        if admin.role != "admin":
            admin.role = "admin"
            db.commit()
        print(f"[skip] admin already exists: {ADMIN_EMAIL}")
        return admin

    admin = User(
        name="StudentHelp Admin",
        email=ADMIN_EMAIL,
        hashed_password=pwd_context.hash(ADMIN_PASSWORD),
        role="admin",
        # Same forced-reset flow as any admin created via /admin/create-admin -
        # this seed password is a known, checked-into-the-repo value, so it
        # must not be usable beyond one login.
        must_change_password=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"[created] admin user: {ADMIN_EMAIL} / {ADMIN_PASSWORD}  <-- must be changed on first login")
    return admin


def seed_companies(db):
    for c in COMPANIES:
        existing = db.query(Company).filter(Company.name == c["name"]).first()
        if existing:
            print(f"[skip] company already exists: {c['name']}")
            continue

        company = Company(
            name=c["name"],
            roles=c["roles"],
            tags=c["tags"],
            min_cgpa=c["min_cgpa"],
            preferred_branches=c["preferred_branches"],
            resume_keywords=c["resume_keywords"],
            apply_url=c["apply_url"],
            is_curated_verified=True,
        )
        db.add(company)
        db.flush()  # get company.id before inserting rounds

        for r in c["rounds"]:
            db.add(Round(company_id=company.id, **r))

        db.commit()
        print(f"[created] company: {c['name']} ({len(c['rounds'])} rounds)")


def seed_quiz_questions(db, admin: User):
    created = 0
    for subject, text, options, correct_idx, explanation, difficulty in QUIZ_QUESTIONS:
        existing = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.subject == subject, QuizQuestion.question_text == text)
            .first()
        )
        if existing:
            continue

        db.add(QuizQuestion(
            company_id=None,  # general/subject-only, not company-specific
            subject=subject,
            difficulty=difficulty,
            question_text=text,
            options=options,
            correct_option_index=correct_idx,
            explanation=explanation,
            status="approved",
            generated_by="admin",
            reviewed_by_user_id=admin.id,
        ))
        created += 1

    db.commit()
    print(f"[created] {created} new quiz questions ({len(QUIZ_QUESTIONS) - created} already existed)")


def main():
    db = SessionLocal()
    try:
        admin = get_or_create_admin(db)
        seed_companies(db)
        seed_quiz_questions(db, admin)
        print("\nDone. Log in with:")
        print(f"  email:    {ADMIN_EMAIL}")
        print(f"  password: {ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
