from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    role: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    username: str = Field(..., description="Username")
    password: str
    role_id: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = Field(None, description="Username")
    status: Optional[str] = None
    role_id: Optional[int] = None


class UserOut(BaseModel):
    id: int
    name: str
    username: str
    status: str
    role_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True