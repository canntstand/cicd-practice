import datetime

from fastapi import HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..config import settings as ss
from ..database import models
from ..utils.dependencies import create_token_pair
from ..utils.exc import db_exc_check
from ..utils.hash import hash_pwd, verify_pwd
from ..validation import schemas
from . import users


@db_exc_check
def register(body: schemas.User, db: Session) -> bool:
    body.password = hash_pwd(body.password)
    user = users.create_user(body, db)
    db.commit()
    return bool(user)


@db_exc_check
def login(
    form: OAuth2PasswordRequestForm, db: Session, response: Response
) -> schemas.TokenResp:
    user = users.get_user_by_form(form, db)
    if not user or not verify_pwd(form.password, user.password):
        raise HTTPException(400, detail="Invalid credentials")

    db.execute(delete(models.RefreshToken).where(models.RefreshToken.owner == user.id))

    token_pair = create_token_pair(user.id)
    _save_refresh_token(db, user.id, token_pair.refresh_token)

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
    db.commit()
    return token_pair


def _save_refresh_token(db: Session, user_id: int, refresh_token: str):
    expires = datetime.datetime.fromtimestamp(
        jwt.decode(
            refresh_token,
            ss.REFRESH_SECRET_KEY,
            algorithms=[ss.REFRESH_ALGORITHM],
        )["exp"],
        tz=datetime.timezone.utc,
    )
    db.add(models.RefreshToken(token=refresh_token, owner=user_id, expires_at=expires))
    db.commit()


@db_exc_check
def logout(refresh_token: str, db: Session) -> bool:
    db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.token == refresh_token)
    )
    db.commit()
    return True
