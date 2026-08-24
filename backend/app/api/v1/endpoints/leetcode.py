from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import urllib.request
import json

from app.db.database import get_db
from app.models.user import User
from app.models.leetcode import LeetCodeLog
from app.models.notification import Notification
from app.schemas.schemas import (
    LeetCodeLogCreate,
    LeetCodeLogOut,
    LeetCodeProfileOut,
    LeetCodeRecommendationOut,
    LeetCodeStudentSummary,
    UserUpdate,
)
from app.services.leetcode_reminder_service import send_daily_leetcode_reminders
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.tpo import scope_to_institution

router = APIRouter(prefix="/leetcode", tags=["leetcode"])

RECOMMENDED_PROBLEMS = [
    # Beginner / Warmup
    {
        "id": "1",
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "Easy",
        "topic": "Arrays & Hashing",
        "level": "Beginner",
        "description": "Find two numbers in an array that add up to a target value. Fundamental hash table technique.",
        "leetcode_url": "https://leetcode.com/problems/two-sum/",
        "tags": ["Array", "Hash Table"]
    },
    {
        "id": "242",
        "title": "Valid Anagram",
        "slug": "valid-anagram",
        "difficulty": "Easy",
        "topic": "Strings",
        "level": "Beginner",
        "description": "Determine if two strings are anagrams of each other using character frequency counting.",
        "leetcode_url": "https://leetcode.com/problems/valid-anagram/",
        "tags": ["String", "Hash Table", "Sorting"]
    },
    {
        "id": "217",
        "title": "Contains Duplicate",
        "slug": "contains-duplicate",
        "difficulty": "Easy",
        "topic": "Arrays & Hashing",
        "level": "Beginner",
        "description": "Check if an array contains any duplicate values using a set.",
        "leetcode_url": "https://leetcode.com/problems/contains-duplicate/",
        "tags": ["Array", "Hash Table"]
    },
    {
        "id": "121",
        "title": "Best Time to Buy and Sell Stock",
        "slug": "best-time-to-buy-and-sell-stock",
        "difficulty": "Easy",
        "topic": "Arrays & Greedy",
        "level": "Beginner",
        "description": "Maximize profit by choosing a single day to buy and a future day to sell. Single pass tracking min price.",
        "leetcode_url": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
        "tags": ["Array", "Dynamic Programming"]
    },
    {
        "id": "206",
        "title": "Reverse Linked List",
        "slug": "reverse-linked-list",
        "difficulty": "Easy",
        "topic": "Linked Lists",
        "level": "Beginner",
        "description": "Reverse a singly linked list iteratively or recursively.",
        "leetcode_url": "https://leetcode.com/problems/reverse-linked-list/",
        "tags": ["Linked List", "Recursion"]
    },

    # Intermediate / Placement Standard
    {
        "id": "15",
        "title": "3Sum",
        "slug": "3sum",
        "difficulty": "Medium",
        "topic": "Two Pointers",
        "level": "Intermediate",
        "description": "Find all unique triplets in the array that give the sum of zero. Essential two-pointer pattern.",
        "leetcode_url": "https://leetcode.com/problems/3sum/",
        "tags": ["Array", "Two Pointers", "Sorting"]
    },
    {
        "id": "49",
        "title": "Group Anagrams",
        "slug": "group-anagrams",
        "difficulty": "Medium",
        "topic": "Strings & Hashing",
        "level": "Intermediate",
        "description": "Group an array of strings into anagrams using sorted string keys or character counts.",
        "leetcode_url": "https://leetcode.com/problems/group-anagrams/",
        "tags": ["Array", "Hash Table", "String"]
    },
    {
        "id": "11",
        "title": "Container With Most Water",
        "slug": "container-with-most-water",
        "difficulty": "Medium",
        "topic": "Two Pointers",
        "level": "Intermediate",
        "description": "Compute the maximum area of water a container can store between vertical lines.",
        "leetcode_url": "https://leetcode.com/problems/container-with-most-water/",
        "tags": ["Array", "Two Pointers", "Greedy"]
    },
    {
        "id": "102",
        "title": "Binary Tree Level Order Traversal",
        "slug": "binary-tree-level-order-traversal",
        "difficulty": "Medium",
        "topic": "Trees & BFS",
        "level": "Intermediate",
        "description": "Return the level order traversal of nodes' values in a binary tree using BFS queue.",
        "leetcode_url": "https://leetcode.com/problems/binary-tree-level-order-traversal/",
        "tags": ["Tree", "Breadth-First Search", "Binary Tree"]
    },
    {
        "id": "322",
        "title": "Coin Change",
        "slug": "coin-change",
        "difficulty": "Medium",
        "topic": "Dynamic Programming",
        "level": "Intermediate",
        "description": "Find the fewest number of coins needed to make up a given amount. Classic DP problem.",
        "leetcode_url": "https://leetcode.com/problems/coin-change/",
        "tags": ["Array", "Dynamic Programming", "BFS"]
    },
    {
        "id": "207",
        "title": "Course Schedule",
        "slug": "course-schedule",
        "difficulty": "Medium",
        "topic": "Graphs & Topological Sort",
        "level": "Intermediate",
        "description": "Determine if you can finish all courses given prerequisite dependencies. Topological sort/Kahn's algorithm.",
        "leetcode_url": "https://leetcode.com/problems/course-schedule/",
        "tags": ["Depth-First Search", "Breadth-First Search", "Graph", "Topological Sort"]
    },

    # Advanced / Top Tier FAANG
    {
        "id": "42",
        "title": "Trapping Rain Water",
        "slug": "trapping-rain-water",
        "difficulty": "Hard",
        "topic": "Two Pointers & Monotonic Stack",
        "level": "Advanced",
        "description": "Compute how much water can be trapped after raining. Monotonic stack or two pointers technique.",
        "leetcode_url": "https://leetcode.com/problems/trapping-rain-water/",
        "tags": ["Array", "Two Pointers", "Dynamic Programming", "Stack"]
    },
    {
        "id": "146",
        "title": "LRU Cache",
        "slug": "lru-cache",
        "difficulty": "Medium",
        "topic": "Design & Data Structures",
        "level": "Advanced",
        "description": "Design a Least Recently Used (LRU) cache using a Hash Map and Doubly Linked List for O(1) operations.",
        "leetcode_url": "https://leetcode.com/problems/lru-cache/",
        "tags": ["Hash Table", "Linked List", "Design", "Doubly-Linked List"]
    },
    {
        "id": "23",
        "title": "Merge k Sorted Lists",
        "slug": "merge-k-sorted-lists",
        "difficulty": "Hard",
        "topic": "Heap & Linked Lists",
        "level": "Advanced",
        "description": "Merge k sorted linked lists into one sorted linked list using a Min-Heap / Priority Queue.",
        "leetcode_url": "https://leetcode.com/problems/merge-k-sorted-lists/",
        "tags": ["Linked List", "Divide and Conquer", "Heap (Priority Queue)", "Merge Sort"]
    },
    {
        "id": "212",
        "title": "Word Search II",
        "slug": "word-search-ii",
        "difficulty": "Hard",
        "topic": "Trie & Backtracking",
        "level": "Advanced",
        "description": "Find all words on a 2D board from a dictionary using a Trie and DFS Backtracking.",
        "leetcode_url": "https://leetcode.com/problems/word-search-ii/",
        "tags": ["Array", "String", "Backtracking", "Trie", "Matrix"]
    }
]


# Maps a diagnostic-quiz subject to the LeetCode topic keywords that best
# reinforce it, so a weak quiz score can drive a *relevant* recommendation
# instead of a generic one. Keys match the SUBJECTS list used on the quiz
# page (app/quiz/page.tsx) - keep the two in sync if either changes.
SUBJECT_TO_LEETCODE_TOPICS = {
    "DSA": ["Array", "Hash Table", "Two Pointers", "Tree", "Graph", "Dynamic Programming", "Linked List"],
    "DBMS": ["Array", "Hash Table"],          # no direct LeetCode equivalent - falls back to general DSA fundamentals
    "OS": ["Design", "Linked List"],           # process/memory concepts map loosely to design & pointer-heavy problems
    "CN": ["Graph", "Breadth-First Search"],   # networking maps loosely to graph/BFS problems
    "Aptitude": ["Array", "Greedy", "Two Pointers"],
    "OOP": ["Design"],
    "System Design": ["Design"],
}

WEAK_SUBJECT_THRESHOLD = 60  # score_percent below this counts as "weak" for recommendation purposes


def _today_str() -> str:
    return date.today().isoformat()


def recommend_for_subject(subject: str, limit: int = 5) -> list[dict]:
    """Pure helper (no DB/HTTP) so quiz.py can reuse the same recommendation
    logic right after grading a quiz, without importing this router."""
    topics = SUBJECT_TO_LEETCODE_TOPICS.get(subject, [])
    if not topics:
        return RECOMMENDED_PROBLEMS[:limit]

    matches = [
        p for p in RECOMMENDED_PROBLEMS
        if any(t.lower() in p["topic"].lower() or any(t.lower() in tag.lower() for tag in p.get("tags", [])) for t in topics)
    ]
    return (matches or RECOMMENDED_PROBLEMS)[:limit]


@router.get("/profile", response_model=LeetCodeProfileOut)
def get_leetcode_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = _today_str()
    solved_today = (current_user.leetcode_last_solved_date == today)

    # Fetch recent problem logs
    logs = (
        db.query(LeetCodeLog)
        .filter(LeetCodeLog.user_id == current_user.id)
        .order_by(LeetCodeLog.solved_at.desc())
        .limit(20)
        .all()
    )

    return LeetCodeProfileOut(
        username=current_user.leetcode_username,
        daily_goal=current_user.leetcode_daily_goal,
        total_solved=current_user.leetcode_total_solved,
        easy_solved=current_user.leetcode_easy_solved,
        medium_solved=current_user.leetcode_medium_solved,
        hard_solved=current_user.leetcode_hard_solved,
        streak=current_user.leetcode_streak,
        last_solved_date=current_user.leetcode_last_solved_date,
        solved_today=solved_today,
        recent_logs=[LeetCodeLogOut.model_validate(log) for log in logs],
    )


@router.post("/sync")
def sync_leetcode_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save handle and attempt sync with public LeetCode stats."""
    if payload.leetcode_username is not None:
        current_user.leetcode_username = payload.leetcode_username.strip()
    if payload.leetcode_daily_goal is not None:
        current_user.leetcode_daily_goal = max(1, payload.leetcode_daily_goal)

    username = current_user.leetcode_username
    if username:
        # Try fetching real LeetCode stats via public GraphQL API endpoint
        try:
            req_data = json.dumps({
                "query": """
                query userProblemsSolved($username: String!) {
                  matchedUser(username: $username) {
                    submitStatsGlobal {
                      acSubmissionNum {
                        difficulty
                        count
                      }
                    }
                  }
                }
                """,
                "variables": {"username": username}
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://leetcode.com/graphql",
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                res_body = json.loads(response.read().decode())
                matched = res_body.get("data", {}).get("matchedUser")
                if matched:
                    stats = matched.get("submitStatsGlobal", {}).get("acSubmissionNum", [])
                    for s in stats:
                        diff = s.get("difficulty")
                        cnt = s.get("count", 0)
                        if diff == "All":
                            current_user.leetcode_total_solved = max(current_user.leetcode_total_solved, cnt)
                        elif diff == "Easy":
                            current_user.leetcode_easy_solved = max(current_user.leetcode_easy_solved, cnt)
                        elif diff == "Medium":
                            current_user.leetcode_medium_solved = max(current_user.leetcode_medium_solved, cnt)
                        elif diff == "Hard":
                            current_user.leetcode_hard_solved = max(current_user.leetcode_hard_solved, cnt)
        except Exception:
            # Fallback gracefully if external API call times out or rate limits
            pass

    db.commit()
    db.refresh(current_user)
    return {"message": "LeetCode profile synced successfully.", "username": current_user.leetcode_username}


@router.post("/log", response_model=LeetCodeLogOut)
def log_solved_problem(
    payload: LeetCodeLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a problem solved by the student for practice."""
    today = _today_str()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # Calculate streak
    if current_user.leetcode_last_solved_date == today:
        # Already solved today, maintain streak
        pass
    elif current_user.leetcode_last_solved_date == yesterday:
        # Solved yesterday, increment streak
        current_user.leetcode_streak += 1
    else:
        # Streak broken or first problem
        current_user.leetcode_streak = 1

    current_user.leetcode_last_solved_date = today
    current_user.leetcode_total_solved += 1

    diff = payload.difficulty.capitalize()
    if diff == "Easy":
        current_user.leetcode_easy_solved += 1
    elif diff == "Medium":
        current_user.leetcode_medium_solved += 1
    elif diff == "Hard":
        current_user.leetcode_hard_solved += 1

    # Create problem log entry
    log_entry = LeetCodeLog(
        user_id=current_user.id,
        problem_title=payload.problem_title,
        problem_slug=payload.problem_slug or payload.problem_title.lower().replace(" ", "-"),
        difficulty=diff,
        topic=payload.topic or "General",
        notes=payload.notes,
        solved_at=datetime.utcnow()
    )
    db.add(log_entry)

    # 1) Notify platform admins (all institutions) and the student's OWN
    # institution's tpo_admin(s) only - this used to notify every tpo_admin
    # across every institution, leaking a student's name/activity to TPOs at
    # other colleges.
    admin_users = (
        db.query(User)
        .filter(
            User.role.in_(["admin", "tpo_admin"]),
            (User.role == "admin") | (User.institution_id == current_user.institution_id),
        )
        .all()
    )
    for admin in admin_users:
        if admin.id != current_user.id:
            notif = Notification(
                user_id=admin.id,
                type="leetcode_daily_solved",
                title=f"LeetCode Practice: {current_user.name}",
                body=f"{current_user.name} completed today's practice: {payload.problem_title} ({diff})! Streak: {current_user.leetcode_streak} days.",
                link="/admin/leetcode-tracker"
            )
            db.add(notif)

    # 2) Generate notification for Student
    student_notif = Notification(
        user_id=current_user.id,
        type="leetcode_streak_updated",
        title="Streak Maintained! 🔥",
        body=f"Awesome job! You logged '{payload.problem_title}' today. Current streak: {current_user.leetcode_streak} days!",
        link="/leetcode"
    )
    db.add(student_notif)

    db.commit()
    db.refresh(log_entry)
    db.refresh(current_user)
    return log_entry


@router.get("/recommendations", response_model=List[LeetCodeRecommendationOut])
def get_recommendations(
    level: Optional[str] = None,
    topic: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Return LeetCode problem recommendations tailored to student's level & preparation."""
    results = RECOMMENDED_PROBLEMS

    if level:
        level_clean = level.capitalize()
        results = [p for p in results if p["level"].capitalize() == level_clean]

    if topic and topic.lower() != "all":
        results = [p for p in results if topic.lower() in p["topic"].lower() or any(topic.lower() in t.lower() for t in p.get("tags", []))]

    return [LeetCodeRecommendationOut(**p) for p in results]


@router.get("/recommendations/for-me", response_model=List[LeetCodeRecommendationOut])
def get_my_weak_subject_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """LeetCode problems picked from the student's actual weak subjects -
    the most recent quiz attempt per subject, filtered to scores below
    WEAK_SUBJECT_THRESHOLD, mapped through SUBJECT_TO_LEETCODE_TOPICS. This
    is the same logic quiz.py runs right after grading; exposed here too so
    the dashboard/leetcode page can show it without retaking a quiz."""
    from app.models.user import QuizResult  # local import to avoid a top-level circular import with quiz.py

    latest_by_subject: dict[str, QuizResult] = {}
    results = (
        db.query(QuizResult)
        .filter(QuizResult.user_id == current_user.id)
        .order_by(QuizResult.taken_at.desc())
        .all()
    )
    for r in results:
        if r.subject not in latest_by_subject:
            latest_by_subject[r.subject] = r

    weak_subjects = [s for s, r in latest_by_subject.items() if r.score_percent < WEAK_SUBJECT_THRESHOLD]
    if not weak_subjects:
        return []

    seen_ids = set()
    recommendations = []
    for subject in weak_subjects:
        for p in recommend_for_subject(subject, limit=3):
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                recommendations.append(p)

    return [LeetCodeRecommendationOut(**p) for p in recommendations]


@router.get("/admin/students", response_model=List[LeetCodeStudentSummary])
def get_admin_leetcode_tracker(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin endpoint to track all students' LeetCode progress, daily practice status, and streaks."""
    if current_user.role not in ["admin", "tpo_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")

    query = db.query(User).filter(User.role == "student")
    # institution_id (not the free-text college_name) is the actual tenant
    # boundary - see tpo.py. The old college_name-string match here would
    # silently show every institution's students to a tpo_admin whose
    # college_name happened to be blank.
    query = scope_to_institution(query, User, current_user)

    students = query.order_by(User.leetcode_streak.desc(), User.name.asc()).all()
    today = _today_str()

    summaries = []
    for s in students:
        latest_log = (
            db.query(LeetCodeLog)
            .filter(LeetCodeLog.user_id == s.id)
            .order_by(LeetCodeLog.solved_at.desc())
            .first()
        )
        latest_title = latest_log.problem_title if latest_log else None

        summaries.append(
            LeetCodeStudentSummary(
                user_id=s.id,
                name=s.name,
                email=s.email,
                leetcode_username=s.leetcode_username,
                total_solved=s.leetcode_total_solved,
                streak=s.leetcode_streak,
                solved_today=(s.leetcode_last_solved_date == today),
                last_solved_date=s.leetcode_last_solved_date,
                latest_problem=latest_title,
            )
        )

    return summaries
