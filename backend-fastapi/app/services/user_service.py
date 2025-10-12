from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, payload: UserCreate) -> User:
        user = User(email=payload.email, full_name=payload.full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)
