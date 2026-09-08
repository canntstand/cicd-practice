from fastapi import APIRouter, Depends, Response, HTTPException
from ..validation import schemas
from ..database.database import get_db
from ..database import models
from sqlalchemy import delete
from sqlalchemy.orm import Session
from ..services import users
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile", "API"])


@router.delete("/", status_code=204)
def delete_profile(
    user_id: int = Depends(get_current_user), db: Session = Depends(get_db)
):
    db.execute(delete(models.RefreshToken).where(models.RefreshToken.owner == user_id))
    db.commit()

    deleted = users.delete_user(user_id, db)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)


@router.put("/", status_code=200, response_model=schemas.UserOut)
def update_profile(
    body: schemas.UserUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    updated_user = users.update_user(user_id, body, db)
    if not updated_user:
        raise HTTPException(404, detail="User not found")
    return updated_user


@router.get("/", status_code=200, response_model=schemas.UserOut)
def get_profile(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user)
):
    user = users.get_user(user_id, db)

    return user
