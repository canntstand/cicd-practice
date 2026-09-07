from fastapi import Depends, HTTPException, Response
from fastapi.routing import APIRouter
from ..database.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from ..validation import schemas
from ..services import tasks
from ..utils.dependencies import get_current_user


router = APIRouter(prefix="/api/tasks", tags=["Tasks", "API"])


@router.patch("/{user_task_id}/status", status_code=200, response_model=schemas.TaskOut)
async def complete_uncomplete_task(
    user_task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    resp = await tasks.complete_uncomplete_task(user_task_id, user_id, db)

    if resp is None:
        raise HTTPException(404, detail="the task doesn't exist")

    return resp


@router.post("/", status_code=201, response_model=schemas.TaskOut)
async def create_task(
    body: schemas.Task,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    body = schemas.TaskWithOwner(**body.model_dump(), owner=user_id)
    resp = await tasks.create_task(body, db)
    return resp


@router.get("/", status_code=200, response_model=list[schemas.TaskOut])
async def get_tasks(
    db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user)
):
    my_tasks = await tasks.get_tasks(user_id, db)
    return my_tasks


@router.get("/{user_task_id}", status_code=200, response_model=schemas.TaskOut)
async def get_task(
    user_task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    task = await tasks.get_task(user_id, user_task_id, db)

    if task is None:
        raise HTTPException(404, detail="the task doesn't exist")

    return task


@router.patch("/{user_task_id}", status_code=200, response_model=schemas.TaskOut)
async def update_task(
    body: schemas.TaskUpdate,
    user_task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    body = schemas.TaskWithOwnerUpdate(**body.model_dump(), owner=user_id)
    updated_task = await tasks.update_task(user_task_id, body, db)

    if updated_task is None:
        raise HTTPException(404, detail="the task doesn't exist")

    return updated_task


@router.delete("/{user_task_id}", status_code=204)
async def delete_task(
    user_task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    if not await tasks.delete_task(user_id, user_task_id, db):
        raise HTTPException(404, detail="the task doesn't exist")
    return Response(status_code=204)
