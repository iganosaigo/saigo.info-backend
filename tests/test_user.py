import pytest

from app import schemas
from app.api.endpoints.user import get_user_helper
from app.core import exceptions
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests import utils

pytestmark = pytest.mark.anyio


class TestUser:

    async def test_get_user_helper(
        self,
        prepare_db: None,
        create_admin: None,
        get_session: AsyncSession,
        user_data_expected: utils.Users,
    ):
        session = get_session
        wrong_data = ["foo@barbaz.com", 111]
        for test in wrong_data:
            with pytest.raises(exceptions.NotFound):
                await get_user_helper(session, test)

        admin_data = user_data_expected["admin"]
        check_by_id = await get_user_helper(session, admin_data.id)
        check_by_email = await get_user_helper(session, admin_data.email)

        exclude = {"hashed_password", "role_id"}
        assert (
            check_by_id.model_dump(exclude=exclude)
            == check_by_email.model_dump(exclude=exclude)
            == admin_data.model_dump(exclude={"password"})
        )

    async def test_admin_login(
        self,
        client: AsyncClient,
        admin_data: schemas.UserToDB,
        create_admin: None,
    ) -> None:
        body = {
            "username": admin_data.email,
            "password": admin_data.password.get_secret_value(),  # type: ignore
        }
        manager = utils.ManageUser(client=client)
        manager.set_body(body)
        requrest = await manager.login()
        assert requrest.status_code == status.HTTP_200_OK
        assert requrest.json()["access_token"]

        body["password"] = "invalid-root-password"
        manager.set_body(body)
        requrest = await manager.login()
        assert requrest.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_admin_me(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
        admin_expected: dict,
    ) -> None:
        requrest = await client.get(
            "/user/me",
            headers=admin_auth_header,
        )
        assert requrest.status_code == status.HTTP_200_OK
        assert admin_expected == requrest.json()

        requrest = await client.get("/user/me")
        assert requrest.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_user(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
        admin_expected: dict,
        user_data_expected: utils.Users,
    ) -> None:
        manager = utils.ManageUser(client=client)
        manager.set_header(admin_auth_header)

        # Create all users
        for name, data in user_data_expected.users.items():
            # main admin already created
            if name == "admin":
                CHECK_STATUS = status.HTTP_401_UNAUTHORIZED
                requrest = await client.get("/user/")
            else:
                CHECK_STATUS = status.HTTP_200_OK
                body = data.model_dump(exclude={"id"})
                requrest = await manager.post(body=body)

            assert requrest.status_code == CHECK_STATUS
            if not name == "admin":
                assert data.model_dump(exclude={"password"}) == requrest.json()

            created_user_email = await manager.get(user=data.email)
            created_user_id = await manager.get(user=data.id)
            assert created_user_email.status_code == status.HTTP_200_OK
            assert created_user_id.status_code == status.HTTP_200_OK
            assert (
                created_user_email.json()
                == data.model_dump(exclude={"password"})
                == created_user_id.json()
            )

        get_users = await manager.get()
        assert get_users.status_code == status.HTTP_200_OK
        assert len(get_users.json()) == len(user_data_expected.users)

        expected_data = [
            v.model_dump(exclude={"password"})
            for v in user_data_expected.users.values()
        ]
        assert expected_data == get_users.json()

    async def test_disable_user(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
        user_data_expected: utils.Users,
        create_other_users: None,
    ) -> None:
        async def login_user():
            login_body = {
                "username": user.email,
                "password": user.password,
            }
            return await user_manager.login(login_body)

        async def test_case(disabled: bool):
            root_manager.set_body({"disabled": disabled})
            disable_requrest = await root_manager.disable(user.email)
            assert disable_requrest.status_code == status.HTTP_200_OK

            requrest = await login_user()
            if disabled:
                assert requrest.status_code == status.HTTP_403_FORBIDDEN
            else:
                assert requrest.status_code == status.HTTP_200_OK

        user = user_data_expected["admin_user"]

        root_manager = utils.ManageUser(client=client)
        root_manager.set_header(admin_auth_header)
        user_manager = utils.ManageUser(client=client)

        for disabled in [True, False]:
            await test_case(disabled)

    async def test_change_me_password(
        self,
        client,
        admin_auth_header: dict,
        user_data_expected: utils.Users,
        create_other_users: None,
    ):
        root_admin = user_data_expected["admin"]
        user_admin = user_data_expected["admin_user"]

        root_manager = utils.ManageUser(client=client)
        root_manager.set_header(admin_auth_header)
        new_root_pass = "new-root-pass"

        root_manager.set_body(
            {
                "old_password": root_admin.password,
                "new_password": new_root_pass,
            }
        )
        request = await root_manager.me_change_pass()
        assert request.status_code == status.HTTP_200_OK

        body = {
            "username": root_admin.email,
            "password": new_root_pass,
        }
        manager = utils.ManageUser(client=client)
        manager.set_body(
            {
                "username": root_admin.email,
                "password": new_root_pass,
            }
        )

        requrest = await manager.login()
        assert requrest.status_code == status.HTTP_200_OK
        token = requrest.json()["access_token"]
        assert token
