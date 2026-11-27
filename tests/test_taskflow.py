from app.users.models import User
from app.users.schemas import Token
from app.users.router import create_access_token
from app.config import settings

from fastapi import status
import jwt

def test_create_user(client, db_session):
    response = client.post("/users", json={"username": "test", "email": "test@svoloch.ru", "password": "12345678"})
    assert response.status_code == status.HTTP_201_CREATED
    user = db_session.query(User).filter_by(username="test").first()
    assert user is not None

def test_usersunique(client):
    response1 = client.post("/users", json={"username": "test", "email": "test@svoloch.ru", "password": "12345678"})
    assert response1.status_code == status.HTTP_201_CREATED
    response2 = client.post("/users", json={"username": "test", "email": "different@svoloch.ru", "password": "12345678"})
    assert response2.status_code == 409
    response3 = client.post("/users", json={"username": "different", "email": "test@svoloch.ru", "password": "12345678"})
    assert response3.status_code == 409

def test_login(client):

    client.post("/users", json={"username": "test", "email": "test@svoloch.ru", "password": "12345678"})
    response = client.post("/users/token", data={"username": "test", "password": "12345678"})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    access_token = data["access_token"]
    token_type = data["token_type"]
    assert token_type == "bearer"
    assert "access_token" in data
    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    assert payload["sub"] == "test"
    assert "exp" in payload

