from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

class UserCreateDTO(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3)
    password: str
    locale: str = "en"

class UserReadDTO(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    role: str
    locale: str
    is_active: bool

class UserUpdateDTO(BaseModel):
    username: str | None = None
    locale: str | None = None

class PasswordChangeDTO(BaseModel):
    password: str
