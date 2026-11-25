from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import Task
from .schemas import CreateBlackBoardRequest, Role, CreateTaskRequest, BaseBlackboard, BaseTask
from .schemas import UpdateTask, TaskStatus
from . import service as tf_service
from .permissions import get_blackboard_with_access, get_task_with_access

from app.database import SessionDep
from app.users import router as UserRoutes
from app.users.models import User

router = APIRouter(
    prefix="/taskflow",
    tags=["TaskFlow"]
)


@router.post("/new_blackboard", response_model=BaseBlackboard)
def create_blackboard(blackboard_data: CreateBlackBoardRequest,
                      db: SessionDep, 
                      creator: User = Depends(UserRoutes.get_current_user)
                      ) -> BaseBlackboard:
    bb = tf_service.create_blackboard(
        db=db,
        title=blackboard_data.title,
        description=blackboard_data.description,
        owner=creator
    )

    return bb


@router.get("/blackboardss/{blackboard_id:int}")
def get_blackboard(blackboard_id: int, db: SessionDep, user: User=Depends(UserRoutes.get_current_user)) -> BaseBlackboard:
    try:
        blackboard = get_blackboard_with_access(db=db, user=user, blackboard_id=blackboard_id)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    return blackboard


@router.get("/my_blackboards")
def my_blackboards(db: SessionDep, user: User = Depends(UserRoutes.get_current_user)) -> list[BaseBlackboard]:
    return tf_service.get_blackboards_by_user(db=db, user=user)


@router.post("/task", response_model=BaseTask)
def create_task(db: SessionDep, task_data: CreateTaskRequest, user: User = Depends(UserRoutes.get_current_user)) -> BaseTask:
    try:
        blackboard = get_blackboard_with_access(db=db, user=user, blackboard_id=task_data.blackboard_id, required_role=Role.owner)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    unique_usernames = set(task_data.executor_usernames)
    executors = list(db.scalars(select(User).where(User.username.in_(unique_usernames))).all())
    if len(executors) != len(unique_usernames):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Some usernames are not valid")
    try:
        task = tf_service.create_task(db=db, 
                                 title=task_data.title,
                                 description=task_data.description,
                                 task_status=task_data.task_status,
                                 blackboard=blackboard,
                                 executors=executors)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return task


@router.post("/blackboards/{blackboard_id:int}/assign", response_model=BaseBlackboard)
def assign_user_to_blackboard(db: SessionDep, blackboard_id: int, new_user_username: str, user:User= Depends(UserRoutes.get_current_user)) -> BaseBlackboard:
    try:
        blackboard = get_blackboard_with_access(db=db, user=user, blackboard_id=blackboard_id,required_role=Role.owner)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))

    try:
        res = tf_service.assign_to_blackboard(db, blackboard, new_user_username)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="DONT KNOW")
    
    return res


@router.get("/tasks/{task_id}", response_model=BaseTask)
def get_task(db: SessionDep, task_id: int, user: User = Depends(UserRoutes.get_current_user)) -> BaseTask:
    try:
        task = get_task_with_access(db=db, user=user, task_id=task_id, required_role=None)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    return task


@router.post("/tasks/{task_id:int}/executors", response_model=BaseTask)
def assign_contestant_to_task(db: SessionDep,task_id: int, new_user_username: str, owner: User = Depends(UserRoutes.get_current_user)
                             ) -> BaseTask:

    try:
        task = get_task_with_access(db, owner, task_id, required_role=Role.owner)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    try:
        result =  tf_service.assign_to_task(db, task, new_user_username)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    return result


@router.delete("/tasks/{task_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(db: SessionDep, task_id: int, owner: User = Depends(UserRoutes.get_current_user)):
    try:
        task = get_task_with_access(db, owner, task_id, Role.owner)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    tf_service.delete_task(db, task)


@router.delete("/tasks/{task_id}/executors/{executor_username}", response_model=BaseTask)
def remove_executor_from_task(db: SessionDep, task_id: int, executor_username: str, owner: User = Depends(UserRoutes.get_current_user)):
    try:
        task = get_task_with_access(db, owner, task_id, Role.owner)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))

    try:
        task = tf_service.remove_executor(db, task, executor_username)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    
    return task 


@router.patch("/tasks/{task_id}", response_model=BaseTask)
def update_task(db: SessionDep, task_id: int, form_data: UpdateTask, owner: User = Depends(UserRoutes.get_current_user)) -> BaseTask:
    try:
        task = get_task_with_access(db, owner, task_id, Role.owner)
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))

    try:
        updated_task = tf_service.update_task(db, task, form_data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return updated_task

def change_task_status(new_status: TaskStatus, required_role: Role | None=None) -> Callable:

    def _dependency(db: SessionDep, task_id: int, user: User = Depends(UserRoutes.get_current_user)):
        try:
            task = get_task_with_access(db, user, task_id, required_role)
        except LookupError as e:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
        except PermissionError as e:
            raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))

        try:
            updated_task = tf_service.change_task_status(db, task, new_status)
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
        return updated_task
    return _dependency

@router.patch("/tasks/{task_id}/open", response_model=BaseTask)
def open_task(task: Task = Depends(change_task_status(TaskStatus.opened, Role.owner))) -> BaseTask:
    return task

@router.patch("/tasks/{task_id}/review", response_model=BaseTask)
def put_in_review(task: Task = Depends(change_task_status(TaskStatus.in_review))) -> BaseTask:
    return task

@router.patch("/tasks/{task_id}/close", response_model=BaseTask)
def close_task(task: Task = Depends(change_task_status(TaskStatus.closed, Role.owner))):
    return task

@router.patch("/tasks/{task_id}/reject", response_model=BaseTask)
def reject_task(task: Task = Depends(change_task_status(TaskStatus.opened, Role.owner))):
    return task
