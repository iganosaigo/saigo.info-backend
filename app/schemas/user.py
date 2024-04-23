from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    ValidationInfo,
    field_validator,
)

from app.core.security import get_password_hash

value_error = "{} must be less than {} characters"
EMAIL_MAX_LENGTH = 100


def check_email_len(email: str) -> str:
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValueError(value_error.format("email", EMAIL_MAX_LENGTH))
    return email.lower()


# ----> HTTP Responses schemas


# Additional properties to return via API
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    fullname: str
    disabled: bool
    role_name: str


# ----> HTTP Requests schemas


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., min_length=5, max_length=40)
    fullname: str = Field(..., min_length=4, max_length=30)
    role_name: str
    disabled: bool

    _email_validation = field_validator("email")(check_email_len)


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


# ----> DB's schemas


# Get full info about user from DB with relations
class UserFromDB(UserResponse):
    role_id: int
    hashed_password: str


# Put user to DB
class UserToDB(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    email: EmailStr
    fullname: str
    disabled: bool
    role_id: int
    password: Optional[SecretStr] = Field(None, exclude=True)
    hashed_password: Optional[str] = Field(None, validate_default=True)

    @field_validator("hashed_password", mode="after")
    @classmethod
    def make_hashed_password(cls, v: str, info: ValidationInfo) -> str | None:
        if v:
            raise ValueError("You cant supply hash by yourself!")

        password = info.data["password"]
        if password:
            return get_password_hash(password.get_secret_value())

        return None


class UserAuth(BaseModel):
    disabled: bool
    email: EmailStr
