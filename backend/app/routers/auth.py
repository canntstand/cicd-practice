from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database.database import get_db
from ..services import auth
from ..utils.dependencies import get_current_user, refresh_access_token
from ..validation import schemas

router = APIRouter(prefix="/api", tags=["Auth", "API"])


@router.post("/register", status_code=201)
def register(body: schemas.User, db: Session = Depends(get_db)):
    bool = auth.register(body, db)
    if bool:
        return {"message": "Successfully registered"}
    raise HTTPException(500, detail="Registration failed")


@router.post("/login", status_code=200, response_model=schemas.TokenResp)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return auth.login(form, db)


@router.delete("/logout", status_code=204)
def logout(
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    if not refresh_token:
        raise HTTPException(400, detail="Refresh token missing")

    if auth.logout(refresh_token, db):
        response = Response(status_code=204)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    raise HTTPException(500, detail="something went wrong in logout function")


@router.post("/refresh", status_code=200, response_model=schemas.TokenResp)
def refresh_token_pair(
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(400, detail="Refresh token missing")
    return refresh_access_token(refresh_token, db)
