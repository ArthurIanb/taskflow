from fastapi import APIRouter, Body, Depends
from typing import Annotated
from sqlalchemy.orm import Session

from .schemas import CreateUserRequest, CreateUserResponse
from .models import User
from app.database import get_db, SesionLocal
from app.security import hash_password

SessionDep = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/")
def create_user(ucr: CreateUserRequest, db: SessionDep) -> CreateUserResponse:
    hashed_pwd = hash_password(ucr.password)
    user = User(
        username = ucr.username,
        email = ucr.email,
        hashed_password = hashed_pwd
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return CreateUserResponse(username=user.username, email=user.email)

