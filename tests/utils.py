from app import schemas
from dataclasses import dataclass
from httpx import AsyncClient, Response
from typing import Literal


def map_role_name_to_id(role_name: Literal["admin", "user"]) -> int:
    if role_name == "admin":
        return 1
    elif role_name == "user":
        return 2


class User(schemas.CreateUserRequest):
    id: int
    role_name: Literal["admin", "user"]
    password: str


@dataclass
class Users:
    users: dict[str, User]

    def get(self, key, default=None):
        return self.users.get(key, default)

    def __getitem__(self, key):
        return self.users[key]


class Manage:
    def __init__(self, *, client: AsyncClient):
        self.client = client
        self.headers = self.set_header()
        self.body = self.set_body()

    def set_header(self, headers: dict = {}):
        self.headers = headers

    def set_body(self, body: dict = {}):
        self.body = body

    def url_path(self, path: str):
        self.url = path


class ManagePost(Manage):
    async def create(self):
        pass


class ManageUser(Manage):

    async def post(self, *, body: dict = {}, user: str | None = None):
        url = "/user/"
        if user:
            url = f"{url}{user}"

        return await self.client.post(url, json=body, headers=self.headers)

    async def get(self, user: str | int | None = None):
        url = "/user/"
        if user:
            url = f"{url}{user}"
        return await self.client.get(url, headers=self.headers)

    async def login(self, body: dict = {}):
        body_data = body if body else self.body
        url = "/auth/login"
        return await self.client.post(
            url,
            data=body_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    async def me_change_pass(self):
        url = "/user/me/changepassword"
        return await self.client.post(
            url,
            json=self.body,
            headers=self.headers,
        )

    async def disable(self, user: str) -> Response:
        url = f"/user/{user}/disable"
        return await self.client.post(
            url,
            json=self.body,
            headers=self.headers,
        )
