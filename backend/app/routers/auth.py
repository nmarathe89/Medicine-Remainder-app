"""Authentication: register, login, admin login, logout, session listing."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import SessionToken, User
from ..schemas import (
    LoginRequest,
    RegisterRequest,
    SessionOut,
    TokenResponse,
    UserOut,
)
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_session(db: Session, user: User) -> TokenResponse:
    token, jti, expires_at = create_access_token(user.id, user.role)
    db.add(SessionToken(user_id=user.id, token_id=jti, expires_at=expires_at))
    db.commit()
    return TokenResponse(access_token=token, role=user.role, username=user.username)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")
    return _issue_session(db, user)


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not an admin account")
    return _issue_session(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Revoke the most recent active session for this user. (Per-token revocation
    # is handled by matching the jti in a fuller implementation; here we revoke
    # the newest active session, which is the typical single-tab logout.)
    session = (
        db.query(SessionToken)
        .filter(SessionToken.user_id == user.id, SessionToken.revoked.is_(False))
        .order_by(SessionToken.created_at.desc())
        .first()
    )
    if session:
        session.revoked = True
        db.commit()
    return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List this user's sessions — demonstrates multi-session support."""
    now = datetime.now(timezone.utc)
    return (
        db.query(SessionToken)
        .filter(SessionToken.user_id == user.id, SessionToken.expires_at > now)
        .order_by(SessionToken.created_at.desc())
        .all()
    )
