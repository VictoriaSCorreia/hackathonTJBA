from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("guest_id", name="uq_users_guest_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    guest_id: str = Field(index=True)
