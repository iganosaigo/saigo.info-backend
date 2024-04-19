from app import schemas
from httpx import AsyncClient
import pytest


pytestmark = pytest.mark.anyio


class TestPost:

    async def test_post_creation(
        self,
        client: AsyncClient,
    ) -> None:
        pass
