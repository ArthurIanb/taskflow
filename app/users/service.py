from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .schemas import CreateUserRequest
from .models import User

from app.security import hash_password, verify_password


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return db.scalar(stmt)


def create_user(db: Session, user_data: CreateUserRequest) -> User:
    user = User(
        username=user_data.username,
        email = user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("User already exists")
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db=db, username=username)

    if not user or not verify_password(password, user.hashed_password):
        return None
    return user