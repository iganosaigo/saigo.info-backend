from typing import Any, AsyncGenerator, Dict

from app import crud, schemas
from app.core.config import get_settings
from app.db.meta import Base
from app.db.session import get_db_session
from app.main import app
from httpx import AsyncClient
from pydantic import EmailStr, SecretStr
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

settings = get_settings("test")
fastapi_uri = f"{settings.SERVER_HOST}:{settings.SERVER_PORT}{settings.API_URL}"
pg_uri = settings.PG_URI

engine = create_async_engine(pg_uri, echo=False)

session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)


async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_local() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db_session


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
        app=app,
        base_url=fastapi_uri,
        # headers={"Content-Type": "application/json"},
    ) as client:
        await start_db()
        yield client
        await engine.dispose()


@pytest.fixture
def admin_data() -> schemas.UserToDB:
    return schemas.UserToDB(
        email=EmailStr("test-admin@example.com"),
        fullname="test-admin",
        disabled=False,
        role_id=1,
        password=SecretStr("test-admin"),
    )


@pytest.fixture
async def create_admin(
    get_session: AsyncSession,
    admin_data: schemas.UserToDB,
) -> None:
    await crud.user.create(get_session, obj_in=admin_data)


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
