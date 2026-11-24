from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from typing import Annotated
from sqlalchemy.orm import Session

import jwt
from jwt.exceptions import InvalidTokenError

from .schemas import CreateUserRequest, CreateUserResponse, Token, BaseUserData
from .models import User
from . import service

from app.database import get_db
from app.security import create_access_token
from app.config import settings


SessionDep = Annotated[Session, Depends(get_db)]
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="users/token")

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_current_user(db:SessionDep, token: Annotated[str, Depends(oauth2_bearer)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credentials error",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = data.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    result = service.get_user_by_username(db=db, username=username)
    if result is None:
        raise credentials_exception
    return result


@router.post("/token", response_model=Token)
def login(db: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = service.authenticate_user(db=db, username=form_data.username, password=form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={
        "sub": form_data.username
    })
    return Token(access_token=token, token_type="bearer")

@router.get("/me", response_model=BaseUserData)
def read_authorised_user(user: Annotated[User,Depends(get_current_user)]):
    return BaseUserData(username=user.username, email=user.email)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user_data: CreateUserRequest, db: SessionDep) -> CreateUserResponse:
    try:
        user = service.create_user(user_data=user_data, db=db)
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return CreateUserResponse(username=user.username, email=user.email)
