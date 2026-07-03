from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Session as SessionRow
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.services.security import (
    create_access_token,
    hash_password,
    new_jti,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, request: Request, db: AsyncSession = Depends(get_db)) -> TokenOut:
    existing = (await db.execute(select(User).where(User.username == body.username))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    existing_email = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _issue_token(db, user, request)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, request: Request, db: AsyncSession = Depends(get_db)) -> TokenOut:
    user = (await db.execute(select(User).where(User.username == body.username))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    user.last_login_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return await _issue_token(db, user, request)


@router.post("/admin/login", response_model=TokenOut)
async def admin_login(body: LoginIn, request: Request, db: AsyncSession = Depends(get_db)) -> TokenOut:
    user = (await db.execute(select(User).where(User.username == body.username))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin account")
    user.last_login_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return await _issue_token(db, user, request)


async def _issue_token(db: AsyncSession, user: User, request: Request) -> TokenOut:
    jti = new_jti()
    token, expires = create_access_token(user, jti)
    sess = SessionRow(
        id=jti,
        user_id=user.id,
        expires_at=expires,
        user_agent=(request.headers.get("user-agent") or "")[:255],
    )
    db.add(sess)
    await db.commit()
    return TokenOut(
        access_token=token,
        is_admin=user.is_admin,
        username=user.username,
        user_id=user.id,
    )
