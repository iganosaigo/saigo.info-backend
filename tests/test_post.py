import pytest
from fastapi import status
from httpx import AsyncClient

from app import schemas
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
    async def api_create_post(
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

    @classmethod
    async def api_get_post(
        cls,
        manager: utils.ManagePost,
        post_id: str,
    ) -> schemas.PostResponse:
        request = await manager.get(post_id)
        assert request.status_code == status.HTTP_200_OK

        response = schemas.PostResponse(**request.json())
        assert response.post_id == post_id

        return response

    async def test_create_post(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
    ):
        manager = utils.ManagePost(client=client)
        manager.set_headers(admin_auth_header)

        post_ids = []
        total_posts = 3
        for post_num in range(1, total_posts + 1):
            post = self.create_post_template(f"post{post_num}")
            post_id = await self.api_create_post(manager, post)
            post_ids.append(post_id)

            if post_num == total_posts:
                manager.set_headers()

                request = await manager.create(
                    self.create_post_template(f"NOTPERMITTED")
                )
                assert request.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_delete_post(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
        create_post_crud: str,
    ):
        post_id = create_post_crud
        manager = utils.ManagePost(client=client)

        request = await manager.delete(post_id)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED

        manager.set_headers(admin_auth_header)
        request = await manager.delete(post_id)
        assert request.status_code == status.HTTP_200_OK

    async def test_update_post(
        self,
        client: AsyncClient,
        admin_auth_header: dict,
        create_post_crud: str,
    ):
        post_id = create_post_crud
        manager = utils.ManagePost(client=client)

        post_orig = await self.api_get_post(manager, post_id)

        post_modif = post_orig.model_copy()
        post_modif.title = post_orig.title + " modified"
        post_modif.content = post_orig.content + " modified"  # pyright: ignore

        post_new_data = schemas.UpdatePostRequest(**post_modif.model_dump())

        request = await manager.update(post_id, post_new_data)
        assert request.status_code == status.HTTP_401_UNAUTHORIZED

        manager.set_headers(admin_auth_header)
        request = await manager.update(post_id, post_new_data)
        assert request.status_code == status.HTTP_200_OK
        response = schemas.UpdatePostResponse(**request.json())
        assert post_id == response.post_id

        post_latest = await self.api_get_post(manager, post_id)
        assert post_latest != post_orig

        excluded = {"modified"}
        assert post_modif.model_dump(exclude=excluded) == post_latest.model_dump(
            exclude=excluded
        )
