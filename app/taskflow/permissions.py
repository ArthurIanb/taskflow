from sqlalchemy.orm import Session

from app.users.models import User

from .models import Task, Blackboard
from .service import get_blackboard_by_id, get_task_by_id
from .schemas import Role

def get_blackboard_with_access(
        db: Session, user: User,
        blackboard_id: int,
        required_role: Role | None = None
) -> Blackboard:
    blackboard = get_blackboard_by_id(db=db, bb_id=blackboard_id)
    if not blackboard:
        raise LookupError("Blackboard not found")

    contestants = [c for c in blackboard.contestants if c.contestant_id == user.id]
    if len(contestants) != 1:
        raise PermissionError("You dont have access")

    if required_role is not None and required_role != contestants[0].role:
        raise PermissionError("You dont have access")
    return blackboard


def get_task_with_access(
        db: Session, user: User,
        task_id: int,
        required_role: Role | None = None
) -> Task:
    task = get_task_by_id(db=db, task_id=task_id)
    if not task:
        raise LookupError("Task not found")

    contestants = [c for c in task.blackboard.contestants if c.contestant_id == user.id]
    if len(contestants) != 1:
        raise PermissionError("You dont have access")

    if required_role is not None and required_role != contestants[0].role:
        raise PermissionError("You dont have access")
    return task
