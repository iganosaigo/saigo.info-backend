from typing import Any, Dict, List, Union

from app import crud, schemas
from app.api import deps
from app.core import exceptions
from app.core.security import get_password_hash, verify_password
from app.db.session import get_db_session as db_session
from app.schemas import types
from fastapi import APIRouter, Depends, Response, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


async def get_user_helper(
    db: AsyncSession,
    user: Union[int, EmailStr],
) -> schemas.UserFromDB:
    crud_params: types.TUserGetOpts = {}

    if isinstance(user, int):
        crud_params["id"] = user
    elif isinstance(user, str):
        crud_params["email"] = user

    user_in_db = await crud.user.get_user(db, **crud_params)
    if not user_in_db:
        raise exceptions.NotFound

    return user_in_db


@router.get("/", response_model=List[schemas.UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(db_session),
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    all_users = await crud.user.get_all_users(db)
    return all_users


@router.post("/", response_model=schemas.UserResponse)
async def create_user(
    *,
    db: AsyncSession = Depends(db_session),
    body: schemas.CreateUserRequest,
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:

    if await crud.user.is_email_exists(db, email=body.email):
        raise exceptions.EmailExists

    role_id = await crud.user.get_role_id_by_name(db, role_name=body.role_name)
    if not role_id:
        raise exceptions.RoleInvalid

    new_user = schemas.UserToDB(**body.dict(), role_id=role_id)

    result = await crud.user.create(db, obj_in=new_user)
    return result


@router.get("/me", response_model=schemas.UserResponse)
async def test_token(
    current_user: schemas.UserFromDB = Depends(deps.AuthCheck()),
) -> Any:
    return current_user


@router.post(
    "/me/changepassword",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
async def change_me_password(
    *,
    db: AsyncSession = Depends(db_session),
    body: schemas.ChangeMePasswordRequest,
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isdisabled=True),
    ),
) -> Any:
    check_password = verify_password(
        body.old_password.get_secret_value(),
        current_user.hashed_password,
    )
    if not check_password:
        raise exceptions.InvalidCredentials

    new_password_hash = get_password_hash(body.new_password.get_secret_value())

    await crud.user.change_password(
        db,
        id=current_user.id,
        password_hash=new_password_hash,
    )


@router.get("/{some_user}", response_model=schemas.UserResponse)
async def read_user(
    *,
    db: AsyncSession = Depends(db_session),
    some_user: Union[int, EmailStr],
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    return await get_user_helper(db, some_user)


@router.put("/{some_user}", response_model=schemas.UserResponse)
async def update_specific_user(
    *,
    db: AsyncSession = Depends(db_session),
    some_user: Union[int, EmailStr],
    body: schemas.UpdateUserRequest,
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    user_in_db = await get_user_helper(db, some_user)

    if user_in_db.email != body.email:
        if await crud.user.is_email_exists(db, email=body.email):
            raise exceptions.EmailExists

    opts: Dict[str, Any] = {}
    role_id: int
    if user_in_db.role_name != body.role_name:
        new_role_id = await crud.user.get_role_id_by_name(
            db,
            role_name=body.role_name,
        )
        if not new_role_id:
            raise exceptions.RoleInvalid
        role_id = new_role_id
    else:
        role_id = user_in_db.role_id

    opts.update({"role_id": role_id})
    updated_user = schemas.UserToDB(**body.dict(), **opts)

    result = await crud.user.update_user(
        db,
        db_obj=user_in_db,
        obj_in=updated_user,
    )

    return result


@router.delete(
    "/{some_user}",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
async def delete_specific_user(
    *,
    db: AsyncSession = Depends(db_session),
    some_user: Union[int, EmailStr],
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    user_in_db = await get_user_helper(db, some_user)
    await crud.user.delete_by_id(db, user_in_db.id)


@router.post(
    "/{some_user}/disable",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
async def disable_specific_user(
    db: AsyncSession = Depends(db_session),
    *,
    body: schemas.DisableUserRequest,
    some_user: Union[int, EmailStr],
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    user_in_db = await get_user_helper(db, some_user)

    await crud.user.disable_user(
        db,
        id=user_in_db.id,
        disabled=body.disabled,
    )


@router.post(
    "/{some_user}/changepassword",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
async def change_user_password(
    *,
    db: AsyncSession = Depends(db_session),
    body: schemas.ChangeUserPasswordRequest,
    some_user: Union[int, EmailStr],
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    user_in_db = await get_user_helper(db, some_user)
    new_password_hash = get_password_hash(body.new_password.get_secret_value())
    await crud.user.change_password(
        db,
        id=user_in_db.id,
        password_hash=new_password_hash,
    )
