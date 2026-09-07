from sqlalchemy import Column, DateTime, Integer, String, ARRAY, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, unique=True)
    user_task_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    __table_args__ = (CheckConstraint('priority >= 0', name='priority_positive'),)

class RecurringTask(Base):
    __tablename__ = "recur_tasks"
    id = Column(Integer, primary_key=True, unique=True)
    user_task_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    days = Column(ARRAY(String), nullable=False)
    __table_args__ = (CheckConstraint('priority >= 0', name='priority_positive'),)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    owner = Column(Integer, ForeignKey("users.id"), index=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())