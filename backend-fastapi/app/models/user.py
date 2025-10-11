from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    full_name: str
