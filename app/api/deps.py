from app import crud, schemas
from app.core import exceptions
from app.core.config import settings
from app.core.security import verify_access_token
from app.db.session import get_db_session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_URL}/auth/login",
)


async def verify_user_token(
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(reusable_oauth2),
) -> schemas.UserFromDB:
    try:
        payload = verify_access_token(token)
        token_data = schemas.TokenPayload(**payload)
        user = await crud.user.get_user(db, email=token_data.sub)
        assert user

    except jwt.ExpiredSignatureError:
        raise exceptions.TokenExpired

    except (jwt.JWTError, ValidationError, AssertionError):
        raise exceptions.InvalidCredentials

    return user


class AuthCheck:
    def __init__(
        self,
        *,
        isdisabled: bool = False,
        isadmin: bool = False,
    ):
        self.isdisabled = isdisabled
        self.isadmin = isadmin

    def __call__(
        self,
        current_user: schemas.UserFromDB = Depends(verify_user_token),
    ) -> schemas.UserFromDB:
        if self.isadmin:
            if current_user.role_name != "admin":
                raise exceptions.PrivelegesError

        if self.isdisabled:
            if current_user.disabled:
                raise exceptions.DisabledUser

        return current_user
