from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionDep
from app.users.router import get_current_user
from app.users.models import User

from .schemas import Role
from . import service as TFService
from .models import Task, Blackboard


class TaskPermissionChecker:
    def __init__(self, required_role: Role | None=None):
        self.required_role = required_role

    def __call__(self, db: SessionDep, task_id: int, user: User = Depends(get_current_user)) -> Task:
        task = TFService.get_task_by_id(db=db, task_id=task_id)
        if not task:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
        contestants = [c for c in task.blackboard.contestants if c.contestant_id == user.id]
        if len(contestants) != 1:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a contestant")
        contestant = contestants[0]

        if self.required_role is not None and self.required_role != contestant.role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not allowed to this task")
        return task


class BlackboardPermissionChecker:
    def __init__(self, required_role: Role | None=None):
        self.required_role = required_role

    def __call__(self, db: SessionDep, blackboard_id: int, user: User = Depends(get_current_user)) -> Blackboard:
        blackboard = TFService.get_blackboard_by_id(db=db, bb_id=blackboard_id)
        if not blackboard:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Blackboard not found")
        contestants = [c for c in blackboard.contestants if c.contestant_id == user.id]
        if len(contestants) != 1:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a contestant")
        contestant = contestants[0]

        if self.required_role is not None and self.required_role != contestant.role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not allowed to this blackboard")
        return blackboard



CurrentTaskMember = Annotated[Task, TaskPermissionChecker()]
CurrentTaskOwner = Annotated[Task, TaskPermissionChecker(required_role=Role.owner)]
