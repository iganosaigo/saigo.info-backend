from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core import exceptions, security
from app.db.session import get_db_session as db_session

router = APIRouter()


@router.post("/login", response_model=schemas.TokenResponse)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_session),
) -> Any:
    user = await crud.user.authenticate(
        db,
        email=form_data.username.lower(),
        password=form_data.password,
    )
    if not user:
        raise exceptions.InvalidEmailOrPassword
    elif user.disabled:
        raise exceptions.DisabledUser

    token = security.create_access_token(user.email)
    result = {
        "access_token": token,
        "token_type": "bearer",
    }
    return result
