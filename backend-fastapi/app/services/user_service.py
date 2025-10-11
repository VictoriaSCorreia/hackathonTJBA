from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_guest(self) -> User:
        # Generate a unique guest identifier
        guest_id = str(uuid4())
        user = User(guest_id=guest_id)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_guest_id(self, guest_id: str) -> User | None:
        stmt = select(User).where(User.guest_id == guest_id)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result
