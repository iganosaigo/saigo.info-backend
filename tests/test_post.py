from fastapi import status
import pytest

from app import schemas
from httpx import AsyncClient
from tests import utils


pytestmark = pytest.mark.anyio


class TestPost:
    @staticmethod
    def create_post_template(text: str):
        def repeat(text: str, num: int):
            return " ".join([text] * num)

        text = f"test-{text}"
        post = schemas.CreatePostRequest(
            title=repeat(text, 3),
            description=repeat(text, 5),
            content=repeat(text, 20),
            tags=["test", text],
            estimated=len(text),
        )
        return post

    @classmethod
    async def create_post(
        cls,
        manager: utils.ManagePost,
        content: schemas.CreatePostRequest,
    ):
        expected_post_id = schemas.post.gen_post_id(content.title)
        request = await manager.create(content)
        assert request.status_code == status.HTTP_200_OK
        response = schemas.CreatePostResponse(**request.json())
        assert response == schemas.post.CreatePostResponse(post_id=expected_post_id)
        return response.post_id

    async def test_create_post(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
    ):
        manager = utils.ManagePost(client=client)
        manager.set_header(admin_auth_header)

        post_ids = []
        total_posts = 3
        for post_num in range(1, total_posts + 1):
            post = self.create_post_template(f"post{post_num}")
            post_id = await self.create_post(manager, post)
            post_ids.append(post_id)

            if post_num == total_posts:
                manager.set_header()

                request = await manager.create(
                    self.create_post_template(f"NOTPERMITTED")
                )
                assert request.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_post(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
        post_id: str,
    ):
        manager = utils.ManagePost(client=client)

        request = await manager.delete(post_id)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED

        manager.set_header(admin_auth_header)
        request = await manager.delete(post_id)
        assert request.status_code == status.HTTP_200_OK
