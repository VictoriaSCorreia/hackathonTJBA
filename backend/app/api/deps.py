from collections.abc import Generator
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.user_service import UserService


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_guest(
    request: Request, db: Session = Depends(get_db)
):
    # Try header first, then cookie
    guest_id = request.headers.get("x-guest-id") or request.cookies.get("guest_id")
    if not guest_id:
        raise HTTPException(status_code=401, detail="Missing guest_id")

    user = UserService(db).get_by_guest_id(guest_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid guest_id")
    return user
