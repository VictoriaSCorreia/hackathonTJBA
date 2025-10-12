from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    guest_id: str


class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
