from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str

class BaseUserData(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=255)


class CreateUserRequest(BaseUserData):
    password: str = Field(min_length=8, max_length=100)


class CreateUserResponse(BaseUserData):
    ...
