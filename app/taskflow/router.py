from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy import select

from .models import Blackboard
from .schemas import CreateBlackBoardRequest, Role, CreateTaskRequest, BaseBlackboard, BaseTask
from . import service as TFService
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
    bb = TFService.create_blackboard(
        db=db,
        title=blackboard_data.title,
        description=blackboard_data.description,
        owner=creator
    )

    return bb

@router.get("/blackboards/{blackboard_id:int}")
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
    return TFService.get_blackboards_by_user(db=db, user=user)


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
        task = TFService.create_task(db=db, 
                                 title=task_data.title,
                                 description=task_data.description,
                                 task_status=task_data.task_status,
                                 blackboard=blackboard,
                                 executors=executors)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return task

@router.post("/blackboard/{blackboard_id:int}/assign", response_model=BaseBlackboard)
def assign_user_to_blackboard(db: SessionDep, blackboard_id: int, new_user_username: str, user:User= Depends(UserRoutes.get_current_user)) -> BaseBlackboard:
    try:
        blackboard = get_blackboard_with_access(db=db, user=user, blackboard_id=blackboard_id,required_role=Role.owner)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))

    try:
        res = TFService.assign_to_blackboard(db, blackboard, new_user_username)
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
