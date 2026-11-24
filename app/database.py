from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings
from typing import Annotated
from fastapi import Depends


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    with SessionLocal() as session:
        yield session

class Base(DeclarativeBase):
    ... 

SessionDep = Annotated[Session, Depends(get_db)]
