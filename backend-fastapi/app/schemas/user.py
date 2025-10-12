from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
