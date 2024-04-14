from typing import Optional

from app.core.security import get_password_hash
from pydantic import BaseModel, EmailStr, Field, SecretStr, validator

from . import types


value_error = "{} must be less than {} characters"
EMAIL_MAX_LENGTH = 100


def check_email_len(email: str) -> str:
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValueError(value_error.format("email", EMAIL_MAX_LENGTH))
    return email.lower()


# ----> DB's schemas

# Get full info about user from DB with relations
class UserFromDB(BaseModel):
    id: int
    email: EmailStr
    fullname: str
    disabled: bool
    role_name: str
    role_id: int
    hashed_password: str


# Put user to DB
class UserToDB(BaseModel):
    email: EmailStr
    fullname: str
    disabled: bool
    role_id: int
    password: Optional[SecretStr] = Field(None, exclude=True)
    hashed_password: Optional[str] = None

    # Provide hash or it'll make it from plain password
    @validator("hashed_password", pre=True, always=True)
    def make_hashed_password(cls, hash, values):
        if hash:
            raise ValueError("You cant supply hash by yourself!")

        password = values["password"]
        if password:
            return get_password_hash(password.get_secret_value())

        return None


class UserAuth(BaseModel):
    disabled: bool
    email: EmailStr


# ----> HTTP Responses schemas

# Additional properties to return via API
class UserResponse(UserFromDB):
    pass

    class Config:
        fields = {
            "hashed_password": {"exclude": True},
            "role_id": {"exclude": True},
        }


# ----> HTTP Requests schemas


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., min_length=5, max_length=40)
    fullname: str = Field(..., min_length=4, max_length=30)
    role_name: str
    disabled: bool

    _email_ = validator("email", allow_reuse=True)(check_email_len)


class UpdateUserRequest(CreateUserRequest):
    password: SecretStr = Field(None, min_length=5, max_length=40)


# Admin change password mode
class ChangeUserPasswordRequest(BaseModel):
    new_password: SecretStr = Field(..., min_length=5, max_length=40)


# Usual user change password mode
class ChangeMePasswordRequest(ChangeUserPasswordRequest):
    old_password: SecretStr = Field(..., min_length=5, max_length=40)


class DisableUserRequest(BaseModel):
    disabled: bool
