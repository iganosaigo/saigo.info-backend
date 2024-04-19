from typing import Any, AsyncGenerator, Dict, Literal

from app import crud, schemas
from app.core.config import get_settings
from app.db.meta import Base
from app.db.session import get_db_session
from app.main import app as fastapi_app
from tests import utils
from dataclasses import asdict, dataclass
from httpx import AsyncClient, ASGITransport
from pydantic import SecretStr
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


settings = get_settings("test")
fastapi_uri = f"{settings.SERVER_HOST}:{settings.SERVER_PORT}{settings.API_URL}"
pg_uri = str(settings.PG_URI)

engine = create_async_engine(pg_uri, echo=False, poolclass=NullPool)

session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)


async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_local() as session:
        yield session


fastapi_app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_local() as session:
        yield session


async def start_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("INSERT INTO role (id, name) VALUES (:id, :name)"),
            [{"id": 1, "name": "admin"}, {"id": 2, "name": "user"}],
        )
        await conn.commit()
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url=fastapi_uri,
        # headers={"Content-Type": "application/json"},
    ) as client:
        await start_db()
        yield client
        await engine.dispose()


@pytest.fixture
def user_data_expected() -> utils.Users:

    def create_user(
        *,
        id: int,
        name: str,
        role: Literal["admin", "user"] = "admin",
        disabled: bool = False,
    ) -> utils.User:
        name = f"test-{name}"
        return utils.User(
            id=id,
            email=f"{name}@foobar.baz",
            fullname=name,
            password=name,
            role_name=role,
            disabled=disabled,
        )

    admin_initial = {"admin": create_user(id=1, name="admin")}
    admin_user = {"admin_user": create_user(id=2, name="admin-user")}
    readonly_user = {
        "user": create_user(
            id=3,
            name="user",
            role="user",
        )
    }
    disabled_user = {
        "disabled_user": create_user(
            id=4,
            name="disabled-user",
            role="user",
            disabled=True,
        )
    }
    all_users = utils.Users(
        users={
            **admin_initial,
            **admin_user,
            **readonly_user,
            **disabled_user,
        }
    )
    return all_users


@pytest.fixture
def admin_expected(
    user_data_expected: utils.Users,
) -> Dict:
    admin_data = user_data_expected["admin"]
    return admin_data.model_dump(exclude={"password"})


@pytest.fixture
def admin_data(
    user_data_expected: dict[str, utils.User],
) -> schemas.UserToDB:
    admin = user_data_expected.get("admin")
    if not admin:
        raise ValueError
    return schemas.UserToDB(
        **admin.model_dump(exclude={"id"}),
        role_id=1,
    )


@pytest.fixture
def other_users_data(user_data_expected: utils.Users) -> list[schemas.UserToDB]:
    result = []
    for name, data in user_data_expected.users.items():
        if not name == "admin":
            user = schemas.UserToDB(
                **data.model_dump(exclude={"id"}),
                role_id=utils.map_role_name_to_id(data.role_name),
            )
            result.append(user)
    return result


@pytest.fixture
async def create_admin(
    get_session: AsyncSession,
    admin_data: schemas.UserToDB,
) -> None:
    await crud.user.create(get_session, obj_in=admin_data)


@pytest.fixture
async def create_other_users(
    get_session: AsyncSession,
    other_users_data: list[schemas.UserToDB],
) -> None:
    for user in other_users_data:
        await crud.user.create(get_session, obj_in=user)


@pytest.fixture
async def admin_jwt(
    create_admin: None,
    admin_data: schemas.UserToDB,
    client: AsyncClient,
) -> str:
    body = {
        "username": admin_data.email,
        "password": admin_data.password.get_secret_value(),  # type: ignore
    }
    response = await client.post(
        "/auth/login",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response.json()["access_token"]


@pytest.fixture
async def admin_auth_header(admin_jwt: str) -> Dict:
    return {"Authorization": f"Bearer {admin_jwt}"}


@pytest.fixture
async def create_users(
    client: AsyncClient,
    admin_auth_header: dict,
    admin_expected: dict,
):
    pass
