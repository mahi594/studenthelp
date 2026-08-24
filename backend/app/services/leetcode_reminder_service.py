"""
Daily LeetCode reminder job.

Runs once a day (see scheduler wiring in main.py) and notifies any student
who has opted into LeetCode tracking (i.e. has set leetcode_username) but
hasn't logged a solved problem yet today. Deliberately conservative:
- Only nudges students who've explicitly set a username (opt-in signal),
  not every student - unsolicited daily notifications for a feature someone
  never engaged with would just train people to ignore notifications.
- Checks for an existing reminder notification created today before sending
  a new one, so re-running the job (e.g. after a restart) never double-sends.

This is APScheduler running in-process (see main.py), which is only safe for
a SINGLE backend instance/worker. If StudentHelp ever moves to multiple
Railway replicas or workers, every replica would independently fire this job
and each student would get one notification per replica. At that point,
migrate to a Railway Cron Job hitting a protected endpoint instead (a single
external trigger, not N in-process schedulers), or add a distributed lock.
"""
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.notification import Notification


def send_daily_leetcode_reminders(db: Session) -> int:
    """Sends a reminder notification to every opted-in student who hasn't
    solved a problem yet today. Returns the count of reminders sent (useful
    for logging/testing)."""
    today = date.today().isoformat()

    students = (
        db.query(User)
        .filter(User.role == "student")
        .filter(User.leetcode_username.isnot(None))
        .filter(User.leetcode_username != "")
        .all()
    )

    sent = 0
    for student in students:
        if student.leetcode_last_solved_date == today:
            continue  # already solved today - no nudge needed

        already_reminded_today = (
            db.query(Notification)
            .filter(
                Notification.user_id == student.id,
                Notification.type == "leetcode_reminder",
                Notification.created_at >= datetime.combine(date.today(), datetime.min.time()),
            )
            .first()
        )
        if already_reminded_today:
            continue  # avoid double-sending if the job runs more than once today

        streak = student.leetcode_streak or 0
        streak_msg = (
            f" Don't break your {streak}-day streak!" if streak > 0 else " Start a streak today!"
        )
        db.add(
            Notification(
                user_id=student.id,
                type="leetcode_reminder",
                title="Haven't solved today's problem yet?",
                body=f"You haven't logged a LeetCode problem today.{streak_msg}",
                link="/leetcode",
            )
        )
        sent += 1

    db.commit()
    return sent