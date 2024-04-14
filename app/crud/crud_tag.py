from typing import List, Optional

from app import schemas
from app.crud.crud_base import CRUDBase
from app.models import Tag
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func


class CRUDPost(CRUDBase[Tag]):
    async def count_tags(
        self,
        db: AsyncSession,
    ) -> Optional[int]:

        stmt = select(func.count()).select_from(self.model)

        count = (await db.execute(stmt)).scalar_one_or_none()
        return count

    async def get_all_tags(
        self,
        db: AsyncSession,
    ) -> schemas.TagsResponse:
        stmt = select(self.model.tag)
        all_tags = (await db.execute(stmt)).scalars().all()
        return schemas.TagsResponse(tags=all_tags)

    async def add_tags(self, db: AsyncSession, *, tags: List[str]) -> bool:
        tags_insert = [{"tag": tag_name} for tag_name in tags]
        stmt = insert(self.model).values(tags_insert).on_conflict_do_nothing()
        await db.execute(stmt)
        await db.commit()
        return True


tag = CRUDPost(Tag)
