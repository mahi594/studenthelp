from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.schemas import UserOut, UserUpdate
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lets a student edit their own profile (branch, grad year, CGPA,
    college). Only fields explicitly present in the request body are
    touched - omitted fields are left as-is, so a partial PATCH from the
    frontend never blanks out other fields."""
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user
