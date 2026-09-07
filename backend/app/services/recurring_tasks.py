from ..utils.exc import db_exc_check
from ..database import models
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from typing import Optional
from ..validation import schemas
import datetime

TASK_FIELDS = [
    models.RecurringTask.user_task_id,
    models.RecurringTask.name,
    models.RecurringTask.description,
    models.RecurringTask.priority,
    models.RecurringTask.days,
    models.RecurringTask.is_completed,
    models.RecurringTask.created_at,
]


@db_exc_check
def complete_uncomplete_recur_task(
    user_task_id: int, user_id: int, db: Session
) -> Optional[schemas.RecurTaskOut]:
    task = db.execute(
        select(models.RecurringTask).where(
            models.RecurringTask.user_task_id == user_task_id,
            models.RecurringTask.owner == user_id,
        )
    ).scalar_one_or_none()

    if task is None:
        return None

    resp = (
        db.execute(
            update(models.RecurringTask)
            .where(
                models.RecurringTask.user_task_id == user_task_id,
                models.RecurringTask.owner == user_id,
            )
            .returning(*TASK_FIELDS)
            .values(is_completed=not task.is_completed)
        )
        .mappings()
        .first()
    )

    db.commit()
    return schemas.RecurTaskOut.model_validate(resp)


@db_exc_check
def create_recur_task(
    body: schemas.RecurTaskWithOwner, db: Session
) -> schemas.RecurTaskOut:
    body = body.model_dump()
    body["created_at"] = datetime.datetime.now(datetime.timezone.utc)
    last_task = db.execute(
        select(models.RecurringTask.user_task_id)
        .where(models.RecurringTask.owner == body["owner"])
        .order_by(models.RecurringTask.user_task_id.desc())
        .limit(1)
    ).scalar_one_or_none()

    user_task_id = 1 if last_task is None else last_task + 1
    body["user_task_id"] = user_task_id

    task = models.RecurringTask(**body)
    db.add(task)
    db.commit()
    db.refresh(task)
    return schemas.RecurTaskOut.model_validate(task)


@db_exc_check
def get_recur_tasks(user_id: int, db: Session) -> list[schemas.RecurTaskOut]:
    tasks = (
        db.execute(
            select(models.RecurringTask).where(models.RecurringTask.owner == user_id)
        )
        .scalars()
        .all()
    )
    return [schemas.RecurTaskOut.model_validate(task) for task in tasks]


@db_exc_check
def get_recur_task(
    user_id: int, user_task_id: int, db: Session
) -> Optional[schemas.RecurTaskOut]:
    task = (
        db.execute(
            select(*TASK_FIELDS).where(
                models.RecurringTask.user_task_id == user_task_id,
                models.RecurringTask.owner == user_id,
            )
        )
        .mappings()
        .first()
    )

    if task:
        return schemas.RecurTaskOut.model_validate(task)

    return None


@db_exc_check
def update_recur_task(
    user_task_id: int, body: schemas.RecurTaskWithOwnerUpdate, db: Session
) -> Optional[schemas.RecurTaskOut]:
    task = db.execute(
        select(models.RecurringTask).where(
            models.RecurringTask.user_task_id == user_task_id,
            models.RecurringTask.owner == body.owner,
        )
    ).scalar_one_or_none()

    if not task:
        return None

    body = body.model_dump()
    body = {key: value for key, value in body.items() if value is not None}
        
    
    task = (
        db.execute(
            update(models.RecurringTask)
            .where(
                models.RecurringTask.user_task_id == user_task_id,
                models.RecurringTask.owner == body["owner"],
            )
            .returning(*TASK_FIELDS)
            .values(**body)
        )
        .mappings()
        .first()
    )

    if task:
        db.commit()
        return schemas.RecurTaskOut.model_validate(task)

    return None


@db_exc_check
def delete_recur_task(user_id: int, user_task_id: int, db: Session) -> bool:
    deleted = db.execute(
        delete(models.RecurringTask).where(
            models.RecurringTask.user_task_id == user_task_id,
            models.RecurringTask.owner == user_id,
        )
    ).rowcount
    db.commit()
    return deleted > 0
