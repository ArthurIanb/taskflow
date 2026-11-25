from app.database import Base
from sqlalchemy import String, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.users.models import User
from .schemas import Role, TaskStatus



class Blackboard(Base):
    __tablename__ = "blackboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(100))

    tasks: Mapped[list["Task"]] = relationship(back_populates="blackboard",cascade="all, delete-orphan")
    contestants: Mapped[list["BlackboardContestants"]] = relationship(back_populates="blackboard",cascade="all, delete-orphan")

class BlackboardContestants(Base):
    __tablename__ = "blackboard_contestants"

    blackboard_id: Mapped[int] = mapped_column(ForeignKey("blackboards.id"), primary_key=True)
    contestant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(default=Role.executor)

    blackboard: Mapped["Blackboard"] = relationship(back_populates="contestants")
    user: Mapped["User"] = relationship()

    @property
    def username(self) -> str:
        return self.user.username

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(1024))
    blackboard_id: Mapped[int] = mapped_column(ForeignKey("blackboards.id"))
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.draft)

    executors: Mapped[list["TaskExecutors"]] = relationship(back_populates="task",
                                                            cascade="all, delete-orphan")
    blackboard: Mapped["Blackboard"] = relationship(back_populates="tasks")

class TaskExecutors(Base):
    __tablename__ = "task_executor"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    executor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    task: Mapped["Task"] = relationship(back_populates="executors")
    user: Mapped["User"] = relationship()

    @property
    def username(self) -> str:
        return self.user.username
