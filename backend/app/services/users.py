from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from ..utils.exc import db_exc_check
from ..utils.hash import verify_pwd
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import models
from sqlalchemy import delete, select, update
from ..validation import schemas
import datetime
from fastapi import HTTPException

USER_FIELDS = [
    models.User.id,
    models.User.email,
    models.User.name,
    models.User.created_at,
]

USER_FIELDS_AND_PWD = USER_FIELDS.copy() + [models.User.password]


@db_exc_check
async def create_user(body: schemas.User, db: AsyncSession) -> schemas.UserOut:
    body = body.model_dump()
    user = (
        await db.execute(select(*USER_FIELDS).where(models.User.name == body["name"]))
        .mappings()
        .first()
    )

    if user:
        raise HTTPException(400, detail="Username is already in use")

    body["created_at"] = datetime.datetime.now(datetime.timezone.utc)
    user = models.User(**body)
    await db.add(user)
    await db.commit()
    await db.refresh(user)
    return schemas.UserOut.model_validate(user)


@db_exc_check
async def get_user(user_id: int, db: AsyncSession) -> Optional[schemas.UserOut]:
    user = (
        await db.execute(select(*USER_FIELDS).where(models.User.id == user_id))
        .mappings()
        .first()
    )

    if user:
        return schemas.UserOut.model_validate(user)

    return None


async def get_user_by_form(
    form: OAuth2PasswordRequestForm, db: AsyncSession
) -> Optional[schemas.UserOutByForm]:
    user = (
        await db.execute(
            select(*USER_FIELDS_AND_PWD).where(models.User.name == form.username)
        )
        .mappings()
        .first()
    )

    if not user:
        return None

    user = schemas.UserOutByForm.model_validate(user)

    if not verify_pwd(form.password, user.password):
        return None

    return user


@db_exc_check
async def update_user(
    user_id: int, body: schemas.UserUpdate, db: AsyncSession
) -> Optional[schemas.UserOut]:
    body = body.model_dump()
    body = {key: value for key, value in body.items() if value is not None}

    user = (
        await db.execute(
            update(models.User)
            .where(models.User.id == user_id)
            .returning(*USER_FIELDS)
            .values(**body)
        )
        .mappings()
        .first()
    )

    if user:
        await db.commit()
        return schemas.UserOut.model_validate(user)

    return None


@db_exc_check
async def delete_user(user_id: int, db: AsyncSession) -> bool:
    await db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.owner == user_id)
    )
    await db.execute(
        delete(models.RecurringTask).where(models.RecurringTask.owner == user_id)
    )
    await db.execute(delete(models.Task).where(models.Task.owner == user_id))

    deleted = await db.execute(delete(models.User).where(models.User.id == user_id))

    await db.commit()
    return deleted.rowcount > 0
