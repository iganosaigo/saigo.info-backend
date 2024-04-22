from dataclasses import dataclass
from typing import Literal

from httpx import AsyncClient, Response
from pydantic import Field

from app import schemas


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
        self._headers = {}
        self._body = {}
        self._url = "/"

    def set_headers(self, headers: dict = {}):
        self._headers = headers

    def set_body(self, body: dict = {}):
        self._body = body

    def set_url(self, path: str = "/"):
        self._url = path

    async def request(self, method: str) -> Response:

        params = {"headers": self._headers}

        if method in ["login"]:
            method = "post"
            params.update(
                {
                    "data": self._body,
                    "headers": {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                }
            )
        elif method in ["put", "post"]:
            params.update({"json": self._body})

        request_method = getattr(self.client, method)
        return await request_method(
            self._url,
            **params,
        )


class ManagePost(Manage):
    async def create(self, post: schemas.CreatePostRequest):
        self.set_url("/post/")
        self.set_body(post.model_dump())
        return await self.request("post")

    async def delete(self, post_id: str):
        self.set_url(f"/post/{post_id}")
        return await self.request("delete")

    async def get(self, post_id: str):
        self.set_url(f"/post/{post_id}")
        return await self.request("get")

    async def update(self, post_id: str, post: schemas.UpdatePostRequest):
        self.set_url(f"/post/{post_id}")
        self.set_body(post.model_dump())
        return await self.request("put")


class ManageUser(Manage):

    async def post(self, *, body: dict = {}, user: str | None = None):
        url = "/user/"
        if user:
            url = f"{url}{user}"
        self.set_url(url)
        if body:
            self.set_body(body)
        return await self.request("post")

    async def get(self, user: str | int | None = None):
        url = "/user/"
        if user:
            url = f"{url}{user}"
        self.set_url(url)
        return await self.request("get")

    async def login(self, body: dict = {}):
        url = "/auth/login"
        if body:
            self.set_body(body)
        self.set_url(url)
        return await self.request("login")

    async def me_change_pass(self):
        url = "/user/me/changepassword"
        self.set_url(url)
        return await self.request("post")

    async def disable(self, user: str):
        url = f"/user/{user}/disable"
        self.set_url(url)
        return await self.request("post")
