import uuid
from datetime import datetime, timedelta
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.schemas import (
    UserCreate,
    UserOut,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ChangePasswordRequest,
    VerifyEmailRequest,
    ResendVerificationResponse,
)
from app.services.email_service import send_password_reset_email, send_verification_email, is_email_configured
from app.services.institution_service import get_or_create_institution

router = APIRouter(prefix="/auth", tags=["auth"])

from passlib.handlers.bcrypt import _BcryptBackend
# Fix passlib compatibility with bcrypt >= 4.0 on Python 3.13
if not hasattr(_BcryptBackend, "_orig_calc_checksum"):
    _BcryptBackend._orig_calc_checksum = _BcryptBackend._calc_checksum
    def _safe_calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if isinstance(secret, bytes) and len(secret) > 72:
            secret = secret[:72]
        return self._orig_calc_checksum(secret)
    _BcryptBackend._calc_checksum = _safe_calc_checksum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def safe_password_str(password: str) -> str:
    if not password:
        return ""
    # bcrypt limits passwords to 72 bytes. Truncate UTF-8 bytes to <= 72.
    b = password.encode("utf-8")
    if len(b) > 72:
        b = b[:72]
    return b.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(safe_password_str(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(safe_password_str(plain_password), hashed_password)



PASSWORD_RESET_EXPIRE_MINUTES = 30
EMAIL_VERIFY_EXPIRE_MINUTES = 60 * 24  # 24 hours
PASSWORD_CHANGE_EXPIRE_MINUTES = 60  # restricted token issued at login when must_change_password is set


def generate_temp_password(length: int = 12) -> str:
    """Generates a random temp password with at least one letter, digit, and
    symbol, for freshly-created admin/tpo_admin accounts. Shown once in the
    /admin/create-admin response (and emailed if SMTP is configured) - never
    stored in plaintext, only its bcrypt hash."""
    alphabet = string.ascii_letters + string.digits
    symbols = "!@#$%*?"
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(symbols),
    ]
    password += [secrets.choice(alphabet) for _ in range(length - len(password))]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "scope": "access", "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_password_reset_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "scope": "password_reset", "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_password_change_token(subject: str) -> str:
    """Issued at login instead of a normal access token when
    user.must_change_password is True. Only valid for /auth/change-password
    (see get_current_user_for_password_change) - rejected by every other
    endpoint's get_current_user, which requires scope == 'access'."""
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_CHANGE_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "scope": "password_change", "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_email_verify_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EMAIL_VERIFY_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "scope": "email_verify", "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        # Reject tokens minted for another purpose (e.g. password reset, or
        # the restricted password-change token issued below) - without this
        # check, a reset/change token would also work as a full login token.
        if payload.get("scope") != "access":
            raise credentials_exception
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_user_for_password_change(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Guard for POST /auth/change-password only. Accepts EITHER a normal
    access token (a logged-in user voluntarily changing their password) OR
    the restricted 'password_change' scope token issued at login when
    must_change_password is set (a forced first-login reset, before the
    account has a full access token at all)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if payload.get("scope") not in ("access", "password_change"):
            raise credentials_exception
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Guard for admin-only endpoints (adding companies, approving quiz
    questions, etc). Raises 403 if the logged-in user isn't an admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def get_current_tpo_or_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Guard for the TPO dashboard - accessible to both content admins and
    dedicated placement-cell (TPO) accounts."""
    if current_user.role not in ("admin", "tpo_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TPO or admin access required")
    return current_user


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    institution_id = None
    college_name = payload.college_name.strip() if payload.college_name else None
    if college_name:
        institution = get_or_create_institution(db, college_name)
        institution_id = institution.id

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        branch=payload.branch,
        grad_year=payload.grad_year,
        college_name=college_name,
        institution_id=institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Best-effort: a failed verification email shouldn't block registration
    # itself - the student can still request a new one via /resend-verification.
    if is_email_configured():
        token = create_email_verify_token(subject=str(user.id))
        verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
        send_verification_email(user.email, verify_link)

    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if user.must_change_password:
        # Restricted token only - good for /auth/change-password and
        # nothing else. The frontend must send the student straight to the
        # change-password screen instead of the normal post-login flow.
        token = create_password_change_token(subject=str(user.id))
        return {
            "access_token": token,
            "token_type": "bearer",
            "must_change_password": True,
        }

    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer", "must_change_password": False}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_for_password_change),
):
    """Sets a new password and clears must_change_password. Accepts either a
    normal access token or the restricted password_change token issued at
    login (see get_current_user_for_password_change). Returns a full access
    token so the frontend can move straight into the app afterward."""
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    current_user.hashed_password = hash_password(payload.new_password)
    current_user.must_change_password = False
    db.commit()

    token = create_access_token(subject=str(current_user.id))
    return {"access_token": token, "token_type": "bearer", "message": "Password updated."}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the logged-in user's profile (including role), so the
    frontend can decide what to show without decoding the JWT itself."""
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Always returns a generic success message, whether or not the email is
    registered - this prevents using this endpoint to enumerate which emails
    have accounts. If SMTP isn't configured, the token is returned directly
    in the response for local development (never do this with real SMTP set
    up - see email_service.is_email_configured)."""
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        token = create_password_reset_token(subject=str(user.id))
        reset_link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"

        if is_email_configured():
            send_password_reset_email(user.email, reset_link)
            return ForgotPasswordResponse(message="If that email is registered, a reset link has been sent.")
        else:
            if settings.ENV == "production":
                raise HTTPException(status_code=500, detail="Email service is not configured in production.")
            return ForgotPasswordResponse(
                message="Email not configured (dev mode) - use dev_reset_token below to test the reset flow.",
                dev_reset_token=token,
            )

    # No user found - still return a generic success message (don't leak existence)
    return ForgotPasswordResponse(message="If that email is registered, a reset link has been sent.")


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("scope") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")
        user_id = decoded.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated. You can now log in with your new password."}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("scope") != "email_verify":
            raise HTTPException(status_code=400, detail="Invalid verification token")
        user_id = decoded.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    db.commit()
    return {"message": "Email verified."}


@router.post("/resend-verification", response_model=ResendVerificationResponse)
def resend_verification(current_user: User = Depends(get_current_user)):
    """Requires login (unlike forgot-password) since this is for someone who
    already has an account and just wants a fresh link - no need for the
    email-enumeration protection that forgot-password needs."""
    if current_user.email_verified:
        return ResendVerificationResponse(message="Your email is already verified.")

    token = create_email_verify_token(subject=str(current_user.id))
    verify_link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"

    if is_email_configured():
        send_verification_email(current_user.email, verify_link)
        return ResendVerificationResponse(message="Verification email sent.")
    else:
        if settings.ENV == "production":
            raise HTTPException(status_code=500, detail="Email service is not configured in production.")
        return ResendVerificationResponse(
            message="Email not configured (dev mode) - use dev_verify_token below to test the flow.",
            dev_verify_token=token,
        )
