from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from .enum import Weekdays
from typing import Optional
from pydantic import field_validator


class MainModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Task(MainModel):
    name: str
    description: Optional[str] = None
    priority: int = 0


class TaskOut(Task):
    user_task_id: int
    is_completed: bool
    created_at: datetime


class RecurTask(Task):
    days: list[Weekdays]

    @field_validator("days")
    def check_days_not_empty(cls, v):
        if not v:
            raise ValueError("Days list cannot be empty")
        return v

class TaskUpdate(MainModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: int = 0

class RecurTaskUpdate(TaskUpdate):
    days: Optional[list[Weekdays]] = None

class RecurTaskOut(RecurTask):
    user_task_id: int
    is_completed: bool
    created_at: datetime


class TaskWithOwner(Task):
    owner: int

class TaskWithOwnerUpdate(TaskUpdate):
    owner: int

class RecurTaskWithOwner(RecurTask):
    owner: int

class RecurTaskWithOwnerUpdate(RecurTaskUpdate):
    owner: int


class User(MainModel):
    name: str
    email: Optional[EmailStr] = None
    password: str

class UserUpdate(MainModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserOut(MainModel):
    name: str
    email: Optional[EmailStr] = None
    created_at: datetime


class UserOutByForm(MainModel):
    id: int
    password: str
    email: Optional[EmailStr] = None
    name: str
    created_at: datetime


class Payload(MainModel):
    sub: str
    exp: float
    iat: float


class TokenResp(MainModel):
    access_token: str
    refresh_token: str
