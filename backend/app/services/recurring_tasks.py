from ..utils.exc import db_exc_check
from ..database import models
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
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
async def complete_uncomplete_recur_task(
    user_task_id: int, user_id: int, db: AsyncSession
) -> Optional[schemas.RecurTaskOut]:
    task = await db.execute(
        select(models.RecurringTask).where(
            models.RecurringTask.user_task_id == user_task_id,
            models.RecurringTask.owner == user_id,
        )
    ).scalar_one_or_none()

    if task is None:
        return None

    resp = (
        await db.execute(
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

    await db.commit()
    return schemas.RecurTaskOut.model_validate(resp)


@db_exc_check
async def create_recur_task(
    body: schemas.RecurTaskWithOwner, db: AsyncSession
) -> schemas.RecurTaskOut:
    body = body.model_dump()
    body["created_at"] = datetime.datetime.now(datetime.timezone.utc)
    last_task = await db.execute(
        select(models.RecurringTask.user_task_id)
        .where(models.RecurringTask.owner == body["owner"])
        .order_by(models.RecurringTask.user_task_id.desc())
        .limit(1)
    ).scalar_one_or_none()

    user_task_id = 1 if last_task is None else last_task + 1
    body["user_task_id"] = user_task_id

    task = models.RecurringTask(**body)
    await db.add(task)
    await db.commit()
    await db.refresh(task)
    return schemas.RecurTaskOut.model_validate(task)


@db_exc_check
async def get_recur_tasks(user_id: int, db: AsyncSession) -> list[schemas.RecurTaskOut]:
    tasks = (
        await db.execute(
            select(models.RecurringTask).where(models.RecurringTask.owner == user_id)
        )
        .scalars()
        .all()
    )
    return [schemas.RecurTaskOut.model_validate(task) for task in tasks]


@db_exc_check
async def get_recur_task(
    user_id: int, user_task_id: int, db: AsyncSession
) -> Optional[schemas.RecurTaskOut]:
    task = (
        await db.execute(
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
async def update_recur_task(
    user_task_id: int, body: schemas.RecurTaskWithOwnerUpdate, db: AsyncSession
) -> Optional[schemas.RecurTaskOut]:
    task = await db.execute(
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
        await db.execute(
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
        await db.commit()
        return schemas.RecurTaskOut.model_validate(task)

    return None


@db_exc_check
async def delete_recur_task(user_id: int, user_task_id: int, db: AsyncSession) -> bool:
    deleted = await db.execute(
        delete(models.RecurringTask).where(
            models.RecurringTask.user_task_id == user_task_id,
            models.RecurringTask.owner == user_id,
        )
    )
    await db.commit()
    return deleted.rowcount > 0
