from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from ..config import settings as ss
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from ..validation.schemas import Payload, TokenResp
from fastapi import Depends, HTTPException
from ..database.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import exists, select, delete
from ..database import models

SECRET_KEY = ss.SECRET_KEY
TOKEN_EXPIRE_MINUTES = ss.TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = ss.REFRESH_TOKEN_EXPIRE_MINUTES
ALGORITHM = ss.ALGORITHM
REFRESH_ALGORITHM = ss.REFRESH_ALGORITHM
REFRESH_SECRET_KEY = ss.REFRESH_SECRET_KEY
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", scheme_name="JWT")


def create_token(subject_id: int, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=TOKEN_EXPIRE_MINUTES
        )

    if not subject_id:
        raise ValueError("Subject must be non-empty string")

    to_encode = {
        "sub": str(subject_id),
        "exp": expires_delta.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject_id: int, expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

    if not subject_id:
        raise ValueError("Subject must be non-empty string")

    to_encode = {
        "sub": str(subject_id),
        "exp": expires_delta.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, REFRESH_ALGORITHM)
    return encoded_jwt


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        token_data = Payload(**payload)

        if datetime.fromtimestamp(token_data.exp, timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return int(token_data.sub)

    except JWTError as e:
        raise HTTPException(
            status_code=403, detail=f"Invalid token: {str(e)}"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=403,
            detail=f"Token validation failed: {str(e)}",
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    user_id = verify_token(token)

    if not db.scalar(select(exists().where(models.User.id == user_id))):
        raise HTTPException(
            status_code=404, detail="User not found"
        )

    return user_id


def create_token_pair(subject_id: int) -> TokenResp:
    access_token = create_token(subject_id)
    refresh_token = create_refresh_token(subject_id)
    return TokenResp(access_token=access_token, refresh_token=refresh_token)


def verify_refresh_token(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(
            token, key=REFRESH_SECRET_KEY, algorithms=REFRESH_ALGORITHM
        )
        token_data = Payload(**payload)
        user_id = int(token_data.sub)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=401,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_exists = db.execute(
            select(exists().where(models.RefreshToken.token == token))
        ).scalar()

        if not token_exists:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        return user_id

    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )


def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    user_id = verify_refresh_token(refresh_token, db)

    new_access_token = create_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.token == refresh_token)
    )

    db.add(
        models.RefreshToken(
            token=new_refresh_token,
            owner=user_id,
            expires_at=datetime.fromtimestamp(
                jwt.decode(
                    new_refresh_token,
                    REFRESH_SECRET_KEY,
                    algorithms=[REFRESH_ALGORITHM],
                )["exp"]
            ),
        )
    )
    db.commit()

    return TokenResp(access_token=new_access_token, refresh_token=new_refresh_token)
