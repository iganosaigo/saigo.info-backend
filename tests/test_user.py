from typing import Any, AsyncGenerator, Dict

from app import crud, schemas
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = pytest.mark.anyio


class TestCase:
    async def test_admin_login(
        self,
        client: AsyncClient,
        # get_session: AsyncSession,
        admin_data: schemas.UserToDB,
        create_admin: None,
    ) -> Any:
        body = {
            "username": admin_data.email,
            "password": admin_data.password.get_secret_value(),  # type: ignore
        }
        response = await client.post(
            "/auth/login",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        assert response.json()["access_token"]

    async def test_list_all_users(
        self,
        client: AsyncClient,
        admin_auth_header: Dict,
    ) -> Any:
        headers = admin_auth_header
        assert (await client.get("/user/", headers=headers)).status_code == 200
        assert (await client.get("/user/")).status_code == 401

    async def test_create_user(
        self,
        client: AsyncClient,
        admin_auth_header: Dict,
    ) -> Any:
        headers = admin_auth_header
        expected = {
            "id": 2,
            "email": "new-user@example.com",
            "fullname": "new-user",
            "role_name": "user",
            "disabled": False,
        }

        body = expected.copy()
        body.pop("id", None)
        body.update({"password": "test-password"})
        response = await client.post("/user/", json=body, headers=headers)
        assert response.status_code == 200
        assert expected == response.json()

        assert (await client.post("/user/", json=body)).status_code == 401
