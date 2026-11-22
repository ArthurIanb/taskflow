from pydantic import BaseModel, ConfigDict
from enum import Enum
from app.users.schemas import BaseUserData


class Role(str, Enum):
    owner = "Owner"
    executor = "Executor"


class TaskStatus(str, Enum):
    draft = "Draft"
    opened =  "Opened"
    closed = "Closed"


class Contestant(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    role: Role

class TaskExecutorsScheme(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    username: str

class BaseTask(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    description: str
    status: TaskStatus
    blackboard_id: int
    executors: list[TaskExecutorsScheme]


class BaseBlackboard(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    title: str
    description: str
    contestants: list[Contestant] | None
    tasks: list[BaseTask]

class CreateBlackBoardRequest(BaseModel):
    title: str
    description: str


class CreateTaskRequest(BaseModel):
    title: str
    description: str
    task_status: TaskStatus
    executor_usernames: list[str]
    blackboard_id: int
