from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.users.models import User
from app.users import service as UserServices

from .models import Blackboard, BlackboardContestants, Task, TaskExecutors
from .schemas import Contestant, Role, TaskStatus


def create_blackboard(db: Session, title: str, owner: User, description: str = "") -> Blackboard:
    blackboard = Blackboard(
        title=title,
        description=description,
        contestants=[BlackboardContestants(user=owner, role=Role.owner)]
    )

    db.add(blackboard)
    db.commit()
    db.refresh(blackboard)

    return blackboard

def get_blackboard_by_id(db: Session, bb_id: int) -> Blackboard | None:
    bb = db.get(Blackboard, bb_id)
    return bb

def get_blackboards_by_user(db: Session, user: User) -> list[Blackboard]:
    stmt = select(Blackboard).where(
        Blackboard.contestants.any(BlackboardContestants.contestant_id == user.id)
    ).options(
            selectinload(Blackboard.contestants).selectinload(BlackboardContestants.user),
            selectinload(Blackboard.tasks)
        )

    blackboards = db.scalars(stmt).all()
    return list(blackboards)


def create_task(db: Session, title: str, description: str, task_status: TaskStatus, blackboard: Blackboard, executors: list[User] | None=None) -> Task:
    task = Task(
        title=title,
        description=description,
        status=task_status
    )
    if executors:
        contestants_ids = [e.contestant_id for e in blackboard.contestants]
        for user in executors:
            if user.id not in contestants_ids:
                raise ValueError(f"Contester with id={user.id} is not assigned to this blackboard")
            te = TaskExecutors(user=user)
            task.executors.append(te)
        blackboard.tasks.append(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def assign_to_blackboard(db: Session, blackboard: Blackboard, new_user_username: str) -> Blackboard:
    user = UserServices.get_user_by_username(db=db, username=new_user_username)
    if not user:
        raise ValueError("User not found")
    if user.id in [c.contestant_id for c in blackboard.contestants]:
        raise ValueError("Already in")

    contestant = BlackboardContestants(
        user=user,
        blackboard=blackboard,
        role=Role.executor
    )
    db.add(contestant)
    db.commit()
    db.refresh(blackboard)
    return blackboard
