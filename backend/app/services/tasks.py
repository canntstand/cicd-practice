from ..utils.exc import db_exc_check
from ..database import models
from sqlalchemy import delete, select, update
from typing import Optional
from sqlalchemy.orm import Session
from ..validation import schemas
import datetime

TASK_FIELDS = [
    models.Task.user_task_id,
    models.Task.name,
    models.Task.description,
    models.Task.priority,
    models.Task.is_completed,
    models.Task.created_at,
]


@db_exc_check
def complete_uncomplete_task(
    user_task_id: int, user_id: int, db: Session
) -> Optional[schemas.TaskOut]:
    task = (
        db.execute(
            select(models.Task).where(
                models.Task.user_task_id == user_task_id, models.Task.owner == user_id
            )
        )
        .scalar_one_or_none()
    )

    if task is None:
        return None

    resp = (
        db.execute(
            update(models.Task)
            .where(
                models.Task.user_task_id == user_task_id, models.Task.owner == user_id
            )
            .returning(*TASK_FIELDS)
            .values(is_completed=not task.is_completed)
        )
        .mappings()
        .first()
    )

    db.commit()
    return schemas.TaskOut.model_validate(resp)


@db_exc_check
def create_task(body: schemas.TaskWithOwner, db: Session) -> schemas.TaskOut:
    body = body.model_dump()
    body["created_at"] = datetime.datetime.now(datetime.timezone.utc)

    # Get the last task for this user
    last_task = db.execute(
        select(models.Task.user_task_id)
        .where(models.Task.owner == body["owner"])
        .order_by(models.Task.user_task_id.desc())
        .limit(1)
    ).scalar_one_or_none()

    user_task_id = 1 if last_task is None else last_task + 1
    body["user_task_id"] = user_task_id

    task = models.Task(**body)
    db.add(task)
    db.commit()
    db.refresh(task)
    return schemas.TaskOut.model_validate(task)


@db_exc_check
def get_tasks(user_id: int, db: Session) -> list[schemas.TaskOut]:
    tasks = (
        db.execute(select(models.Task).where(models.Task.owner == user_id))
        .scalars()
        .all()
    )
    return [schemas.TaskOut.model_validate(task) for task in tasks]


@db_exc_check
def get_task(user_id: int, user_task_id: int, db: Session) -> Optional[schemas.TaskOut]:
    task = (
        db.execute(
            select(*TASK_FIELDS).where(
                models.Task.user_task_id == user_task_id, models.Task.owner == user_id
            )
        )
        .mappings()
        .first()
    )

    if task:
        return schemas.TaskOut.model_validate(task)

    return None


@db_exc_check
def update_task(
    user_task_id: int, body: schemas.TaskWithOwnerUpdate, db: Session
) -> Optional[schemas.TaskOut]:
    task = db.execute(
        select(models.Task).where(
            models.Task.user_task_id == user_task_id,
            models.Task.owner == body.owner,
        )
    ).scalar_one_or_none()

    body = body.model_dump()
    body = {key: value for key, value in body.items() if value is not None}

    task = (
        db.execute(
            update(models.Task)
            .where(
                models.Task.user_task_id == user_task_id,
                models.Task.owner == body["owner"],
            )
            .returning(*TASK_FIELDS)
            .values(**body)
        )
        .mappings()
        .first()
    )

    if task:
        db.commit()
        return schemas.TaskOut.model_validate(task)

    return None


@db_exc_check
def delete_task(user_id: int, user_task_id: int, db: Session) -> bool:
    deleted = db.execute(
        delete(models.Task).where(
            models.Task.user_task_id == user_task_id,
            models.Task.owner == user_id,
        )
    ).rowcount
    db.commit()
    return deleted > 0
