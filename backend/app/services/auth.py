from fastapi import HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from ..database import models
from ..validation import schemas
from ..utils.hash import hash_pwd, verify_pwd
from ..utils.exc import db_exc_check
from ..utils.dependencies import create_token_pair
from . import users
import datetime
from jose import jwt
from ..config import settings as ss


@db_exc_check
async def register(body: schemas.User, db: AsyncSession) -> bool:
    body.password = hash_pwd(body.password)
    user = await users.create_user(body, db)
    await db.commit()
    if user:
        return True
    return False


@db_exc_check
async def login(
    form: OAuth2PasswordRequestForm, db: AsyncSession, response: Response = Response()
) -> schemas.TokenResp:
    user = await users.get_user_by_form(form, db)
    if not user or not verify_pwd(form.password, user.password):
        raise HTTPException(400, detail="Invalid credentials")

    await db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.owner == user.id)
    )

    token_pair = create_token_pair(user.id)
    await _save_refresh_token(db, user.id, token_pair.refresh_token)

    response.set_cookie(
        key="access_token",
        value=token_pair.access_token,
        httponly=True,
        secure=True,
        max_age=15 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=True,
        max_age=7 * 24 * 60 * 60,
    )
    await db.commit()
    return token_pair


async def _save_refresh_token(db: AsyncSession, user_id: int, refresh_token: str):
    expires = datetime.datetime.fromtimestamp(
        jwt.decode(
            refresh_token, ss.REFRESH_SECRET_KEY, algorithms=[ss.REFRESH_ALGORITHM]
        )["exp"]
    )
    await db.add(
        models.RefreshToken(token=refresh_token, owner=user_id, expires_at=expires)
    )
    await db.commit()


@db_exc_check
async def logout(refresh_token: str, db: AsyncSession) -> bool:
    await db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.token == refresh_token)
    )
    await db.commit()
    return True
