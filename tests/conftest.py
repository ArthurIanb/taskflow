import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.main import app
from app.database import Base, get_db

DB_PATH = "sqlite:///:memory:"

engine = create_engine(DB_PATH,
                       connect_args={"check_same_thread": False},
                       poolclass=StaticPool)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_test_settings(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "test_secret_keytest_secret_key22")
    monkeypatch.setattr(settings, "ALGORITHM", "HS256")


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()