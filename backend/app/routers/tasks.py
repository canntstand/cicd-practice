from fastapi import Depends, HTTPException, Response
from fastapi.routing import APIRouter
from ..database.database import get_db
from sqlalchemy.orm import Session
from ..validation import schemas
from ..services import tasks
from ..utils.dependencies import get_current_user


router = APIRouter(prefix="/api/tasks", tags=["Tasks", "API"])


@router.put("/{user_task_id}/status", status_code=200, response_model=schemas.TaskOut)
def complete_uncomplete_task(
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    resp = tasks.complete_uncomplete_task(user_task_id, user_id, db)

    if resp is None:
        raise HTTPException(404, detail="the task doesn't exist")

    return resp


@router.post("/", status_code=201, response_model=schemas.TaskOut)
def create_task(
    body: schemas.Task,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    body = schemas.TaskWithOwner(**body.model_dump(), owner=user_id)
    resp = tasks.create_task(body, db)
    return resp


@router.get("/", status_code=200, response_model=list[schemas.TaskOut])
def get_tasks(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    my_tasks = tasks.get_tasks(user_id, db)
    return my_tasks


@router.get("/{user_task_id}", status_code=200, response_model=schemas.TaskOut)
def get_task(
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    task = tasks.get_task(user_id, user_task_id, db)

    if task is None:
        raise HTTPException(404, detail="the task doesn't exist")

    return task


@router.put("/{user_task_id}", status_code=200, response_model=schemas.TaskOut)
def update_task(
    body: schemas.TaskUpdate,
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    body = schemas.TaskWithOwnerUpdate(**body.model_dump(), owner=user_id)
    updated_task = tasks.update_task(user_task_id, body, db)

    if updated_task is None:
        raise HTTPException(404, detail="the task doesn't exist")

    return updated_task


@router.delete("/{user_task_id}", status_code=204)
def delete_task(
    user_task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    if not tasks.delete_task(user_id, user_task_id, db):
        raise HTTPException(404, detail="the task doesn't exist")
    return Response(status_code=204)
