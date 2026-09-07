from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from ..utils.dependencies import refresh_access_token, get_current_user
from ..validation import schemas
from ..services import auth
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.database import get_db
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api", tags=["Auth", "API"])


@router.post("/register", status_code=201)
async def register(body: schemas.User, db: AsyncSession = Depends(get_db)):
    boolean = await auth.register(body, db)
    if boolean:
        return {"message": "Successfully registered"}
    raise HTTPException(500, detail="Registration failed")


@router.post("/login", status_code=200, response_model=schemas.TokenResp)
async def login(
    form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    return await auth.login(form, db)


@router.delete("/logout", status_code=204)
async def logout(
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    if not refresh_token:
        raise HTTPException(400, detail="Refresh token missing")

    if await auth.logout(refresh_token, db):
        response = Response(status_code=204)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    raise HTTPException(500, detail="something went wrong in logout function")


@router.post("/refresh", status_code=200, response_model=schemas.TokenResp)
async def refresh_token_pair(
    refresh_token: str = Cookie(None), db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(400, detail="Refresh token missing")
    return await refresh_access_token(refresh_token, db)
