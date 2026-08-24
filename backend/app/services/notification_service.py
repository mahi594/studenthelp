import uuid
from sqlalchemy.orm import Session

from app.models.notification import Notification


def notify(
    db: Session,
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> Notification:
    """Creates a notification row. Caller is responsible for db.commit() -
    kept out of this helper so it can be batched with the triggering
    change (e.g. saving a QA answer) in a single transaction."""
    notification = Notification(user_id=user_id, type=type, title=title, body=body, link=link)
    db.add(notification)
    return notification
