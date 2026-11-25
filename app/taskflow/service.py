from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.users.models import User
from app.users import service as user_services

from .models import Blackboard, BlackboardContestants, Task, TaskExecutors
from .schemas import Contestant, Role, TaskStatus, UpdateTask

allowed_task_transitions: dict[TaskStatus, list[TaskStatus]] = {
    TaskStatus.draft: [TaskStatus.opened],
    TaskStatus.opened: [TaskStatus.in_review],
    TaskStatus.in_review: [TaskStatus.opened, TaskStatus.closed],
    TaskStatus.closed: [TaskStatus.draft, TaskStatus.opened]
}

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
                raise ValueError(f"Contester {user.username} is not assigned to this blackboard")
            te = TaskExecutors(user=user)
            task.executors.append(te)
    blackboard.tasks.append(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def assign_to_blackboard(db: Session, blackboard: Blackboard, new_user_username: str) -> Blackboard:
    user = user_services.get_user_by_username(db=db, username=new_user_username)
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


def get_task_by_id(db: Session, task_id: int) -> Task | None:
    task = db.get(Task, task_id)
    return task

def assign_to_task(db: Session, task: Task, new_user_username: str) -> Task:
    user = user_services.get_user_by_username(db, new_user_username)
    if not user:
        raise ValueError("User does not exists")
    if not any(user.id == c.contestant_id for c in task.blackboard.contestants):
            raise ValueError("User not a contestant, add him to blackboard")
    if any(user.id == c.executor_id for c in task.executors):
        raise ValueError("User already in executors")
    
    te = TaskExecutors(
        task_id=task.id,
        executor_id=user.id
    )
    try:
        db.add(te)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise LookupError("That exception is impossible, but something has happened, and i dk what")
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task):
    db.delete(task)
    db.commit()


def remove_executor(db: Session, task: Task, username: str) -> Task:
    user = user_services.get_user_by_username(db, username)
    if not user:
        raise LookupError("User not found")
    executor = next((ex for ex in task.executors if ex.executor_id == user.id), None)
    db.delete(executor)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, form_data: UpdateTask) -> Task:
    if form_data.title is not None:
        task.title = form_data.title
    if form_data.description is not None:
        task.description = form_data.description

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError("Invalid task data")
    db.refresh(task)
    return task


def change_task_status(db: Session, task: Task, new_status: TaskStatus) -> Task:
    if new_status not in allowed_task_transitions[task.status]:
        raise ValueError(f"Cant changes status from {task.status} to {new_status}")
    task.status = new_status
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise ValueError(f"Error while changing task status to {new_status}")
    db.refresh(task)
    return task
