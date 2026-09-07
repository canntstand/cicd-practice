from fastapi import APIRouter, Depends, Response, HTTPException
from ..validation import schemas
from ..database.database import get_db
from ..database import models
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..services import users
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile", "API"])


@router.delete("/", status_code=204)
async def delete_profile(
    user_id: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.owner == user_id)
    )
    await db.commit()

    deleted = await users.delete_user(user_id, db)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)


@router.patch("/", status_code=200, response_model=schemas.UserOut)
async def update_profile(
    body: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    updated_user = await users.update_user(user_id, body, db)
    if not updated_user:
        raise HTTPException(404, detail="User not found")
    return updated_user


@router.get("/", status_code=200, response_model=schemas.UserOut)
async def get_profile(
    db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)
):
    user = await users.get_user(user_id, db)

    return user
