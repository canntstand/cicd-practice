from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from .enum import Weekdays


class MainModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Task(MainModel):
    name: str
    description: str | None = None
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
    name: str | None = None
    description: str | None = None
    priority: int = 0

class RecurTaskUpdate(TaskUpdate):
    days: list[Weekdays] | None = None

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
    email: EmailStr | None = None
    password: str

class UserUpdate(MainModel):
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None

class UserOut(MainModel):
    name: str
    email: EmailStr | None = None
    created_at: datetime


class UserOutByForm(MainModel):
    id: int
    password: str
    email: EmailStr | None = None
    name: str
    created_at: datetime


class Payload(MainModel):
    sub: str
    exp: float
    iat: float


class TokenResp(MainModel):
    access_token: str
    refresh_token: str
