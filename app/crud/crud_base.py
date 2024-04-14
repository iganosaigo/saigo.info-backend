from typing import Any, Dict, Generic, Optional, Type, TypeVar

from app.db.meta import Base
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession


ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        stmt = select(self.model).filter(self.model.id == id)
        return (await db.execute(stmt)).scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        *,
        obj_in: Dict[str, Any],
    ) -> Optional[ModelType]:
        pass

    async def delete_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> None:
        stmt = delete(self.model).filter(self.model.id == id)
        await db.execute(stmt)
        await db.commit()

    async def get_count(
        self,
        db: AsyncSession,
    ) -> Optional[int]:
        stmt = select(func.count()).select_from(self.model)
        count = (await db.execute(stmt)).scalar_one_or_none()
        return count
