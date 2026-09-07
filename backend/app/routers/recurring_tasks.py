from fastapi import Depends, HTTPException, Response
from fastapi.routing import APIRouter
from ..validation import schemas
from ..database.database import get_db
from sqlalchemy.orm import Session
from ..utils.exc import db_exc_check
from ..services import recurring_tasks as rt
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/recur-tasks", tags=["Recur-tasks", "API"])


@router.patch(
    "/{user_task_id}/status", status_code=200, response_model=schemas.RecurTaskOut
)
def complete_uncomplete_recur_task(
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    resp = rt.complete_uncomplete_recur_task(user_task_id, user_id, db)

    if resp is None:
        raise HTTPException(404, detail="the recurring task doesn't exist")
    return resp


@router.post("/", status_code=201, response_model=schemas.RecurTaskOut)
def create_recur_task(
    body: schemas.RecurTask,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    body = schemas.RecurTaskWithOwner(**body.model_dump(), owner=user_id)
    resp = rt.create_recur_task(body, db)
    return resp


@router.get("/", status_code=200, response_model=list[schemas.RecurTaskOut])
def get_recur_tasks(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user)
):
    tasks = rt.get_recur_tasks(user_id, db)
    return tasks


@router.get("/{user_task_id}", status_code=200, response_model=schemas.RecurTaskOut)
def get_recur_task(
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    task = rt.get_recur_task(user_id, user_task_id, db)

    if task is None:
        raise HTTPException(404, detail="the recurring task doesn't exist")

    return task


@router.patch("/{user_task_id}", status_code=200, response_model=schemas.RecurTaskOut)
def update_recur_task(
    body: schemas.RecurTaskUpdate,
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    body = schemas.RecurTaskWithOwnerUpdate(**body.model_dump(), owner=user_id)
    resp = rt.update_recur_task(user_task_id, body, db)

    if resp is None:
        raise HTTPException(404, detail="the recurring task doesn't exist")

    return resp


@router.delete("/{user_task_id}", status_code=204)
def delete_recur_task(
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    resp = rt.delete_recur_task(user_id, user_task_id, db)

    if not resp:
        raise HTTPException(404, detail="the recurring task doesn't exist")

    return Response(status_code=204)
