from typing import Any, cast, Dict, List, Optional

from app import schemas
from app.core.security import get_password_hash, verify_password
from app.crud.crud_base import CRUDBase
from app.models import Account, Role
from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Specifying columns we prevent nested elements in Row from SA.
# Besides, it is right to select needed elements only.
# Moreover: lazy opts doesn't work with async right now
# and i dont like orm_mode=true work behaviour in pydantic.
user_common_select = select(
    Account.id,
    Account.role_id,
    Role.name.label("role_name"),
    Account.email,
    Account.fullname,
    Account.hashed_password,
    Account.disabled,
).join(Role)


class CRUDUser(CRUDBase[Account]):
    async def get_role_id_by_name(
        self,
        db: AsyncSession,
        *,
        role_name: str,
    ) -> Optional[int]:
        stmt = select(Role.id).where(Role.name == role_name)
        query = (await db.execute(stmt)).scalar_one_or_none()
        return query

    async def get_user(
        self,
        db: AsyncSession,
        *,
        email: Optional[str] = None,
        id: Optional[int] = None,
    ) -> Optional[schemas.UserFromDB]:

        stmt = user_common_select

        if email:
            stmt = stmt.where(Account.email == email)
        elif id:
            stmt = stmt.where(Account.id == id)
        else:
            # TODO: Make more clear
            return None

        user_in_db = (await db.execute(stmt)).one_or_none()
        if user_in_db:
            return schemas.UserFromDB.construct(**user_in_db._mapping)

        return None

    async def authenticate(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
    ) -> Optional[schemas.UserAuth]:
        stmt = select(
            Account.email,
            Account.hashed_password,
            Account.disabled,
        ).where(Account.email == email)

        user_in_db = (await db.execute(stmt)).one_or_none()

        if user_in_db and verify_password(
            password,
            user_in_db.hashed_password,
        ):
            return schemas.UserAuth(**user_in_db._mapping)
        return None

    async def get_all_users(
        self,
        db: AsyncSession,
    ) -> List[schemas.UserFromDB]:
        stmt = user_common_select.order_by(Account.id)
        rows = (await db.execute(stmt)).all()
        users = [schemas.UserFromDB.construct(**row._mapping) for row in rows]
        return users

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: schemas.UserToDB,
    ) -> schemas.UserFromDB:
        new_user = Account(**obj_in.dict())

        db.add(new_user)
        await db.commit()

        # Session.refresh() doesn't make eager load without `lazy=joinload`
        # param in table's class `Column` . Perhaps, it's not a best idea.
        # So let it be just separate select for new_user to return.
        # https://docs.sqlalchemy.org/en/14/orm/session_state_management.html#what-actually-loads
        refreshed_new_user = cast(
            schemas.UserFromDB,
            await self.get_user(db, email=obj_in.email),
        )
        return refreshed_new_user

    async def update_user(
        self,
        db: AsyncSession,
        *,
        db_obj: schemas.UserFromDB,
        obj_in: schemas.UserToDB,
    ) -> schemas.UserFromDB:
        stmt = (
            update(self.model)
            .where(self.model.email == db_obj.email)
            .values(**obj_in.dict(exclude_none=True))
            # .returning(self.model)
            # OR
            # .execution_options(synchronize_session="fetch")
        )

        await db.execute(stmt)
        await db.commit()

        updated_user = cast(
            schemas.UserFromDB,
            await self.get_user(db, email=obj_in.email),
        )

        return updated_user

    async def is_email_exists(
        self,
        db: AsyncSession,
        *,
        email: str,
    ) -> bool:
        stmt = select(exists(select(Account).where(Account.email == email)))
        email_exists = cast(bool, (await db.execute(stmt)).scalar())
        return email_exists

    async def disable_user(
        self,
        db: AsyncSession,
        *,
        id: int,
        disabled: bool,
    ) -> bool:
        stmt = update(self.model).where(self.model.id == id).values(disabled=disabled)
        await db.execute(stmt)
        await db.commit()
        return True

    async def change_password(
        self,
        db: AsyncSession,
        *,
        id: int,
        password_hash: str,
    ) -> bool:
        stmt = update(self.model).filter_by(id=id).values(hashed_password=password_hash)
        await db.execute(stmt)
        await db.commit()
        return True


user = CRUDUser(Account)
