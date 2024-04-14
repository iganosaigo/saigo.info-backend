from typing import Any, cast, Dict, List, Optional

from app import schemas
from app.crud.crud_base import CRUDBase
from app.models import Account, Post
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func


class CRUDPost(CRUDBase[Post]):
    async def count_post_with_filters(
        self,
        db: AsyncSession,
        *,
        tags: Optional[List[str]] = None,
    ) -> Optional[int]:
        stmt = select(func.count()).select_from(self.model)
        if tags:
            stmt = stmt.filter(self.model.post_json["tags"].contains(tags))
        count = (await db.execute(stmt)).scalar_one_or_none()

        return count

    async def get_all_posts(
        self,
        db: AsyncSession,
        *,
        offset: int,
        limit: int,
        sort: str,
        order: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[schemas.PostFromDB]:
        columns = [
            Post.id,
            Post.post_id,
            Post.post_json["title"].astext.label("title"),
            func.left(Post.post_json["description"].astext, 250).label("description"),
            Post.post_json["created"].astext.label("created"),
            Post.post_json["modified"].astext.label("modified"),
            Post.post_json["tags"].label("tags"),
            Post.post_json["estimated"].astext.label("estimated"),
            Account.fullname.label("writer"),
            Account.id.label("writer_id"),
        ]

        stmt = select(columns).join(Account).offset(offset).limit(limit)

        # TODO: id is invalid sort field since post_id with uuid type added. Fix it.
        sort_models_dict: Dict[str, Any] = {
            "id": Post.id,
            "created": Post.post_json["created"],
        }
        sort_model = sort_models_dict[sort]

        # TODO: perhaps I should map string to SA operator asc() or desc()
        if order:
            if order == "asc":
                sort_model = sort_model.asc()
            elif order == "desc":
                sort_model = sort_model.desc()

        stmt = stmt.order_by(sort_model)

        if tags:
            stmt = stmt.filter(Post.post_json["tags"].contains(tags))

        rows = (await db.execute(stmt)).all()
        posts = [schemas.PostFromDB(**row._mapping) for row in rows]

        return posts

    async def get_post_id(
        self,
        db: AsyncSession,
        *,
        post_id: str,
    ) -> Optional[schemas.PostFromDB]:
        columns = [
            Post.id,
            Post.post_id,
            Post.post_json.label("data"),
            Account.id.label("writer_id"),
            Account.fullname.label("writer"),
        ]
        stmt = select(columns).join(Account).filter(Post.post_id == post_id)
        row = (await db.execute(stmt)).one_or_none()
        if row:
            # TODO: Make plain Dict without nested json 'data'.
            # Maybe it is better do this in DB?
            post_data: Dict = {}
            for key, value in row._mapping.items():
                if key == "data":
                    for k, v in value.items():  # type: ignore
                        post_data[k] = v
                else:
                    post_data[key] = value

            return schemas.PostFromDB(**post_data)

        return None

    async def create_post(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        obj_in: schemas.CreatePostInDB,
    ) -> str:
        new_post = Post(
            account_id=user_id,
            post_id=obj_in.post_id,
            post_json=obj_in.dict(
                exclude={"post_id"},
            ),
        )
        db.add(new_post)
        await db.commit()

        return new_post.post_id

    async def update_post(
        self,
        db: AsyncSession,
        *,
        post_id: str,
        obj_in: schemas.UpdatePostInDB,
    ) -> str:
        stmt = select(self.model).filter_by(post_id=post_id)
        post_in_db = cast(Post, (await db.execute(stmt)).scalar_one_or_none())
        new_post_data = post_in_db.post_json.copy()
        new_post_data.update(obj_in.dict())

        update_stmt = (
            update(self.model)
            .where(self.model.post_id == post_id)
            .values(post_json=new_post_data)
        )

        await db.execute(update_stmt)
        await db.commit()
        return post_id

    async def delete_by_post_id(
        self,
        db: AsyncSession,
        post_id: str,
    ) -> None:
        stmt = delete(self.model).filter(self.model.post_id == post_id)
        await db.execute(stmt)
        await db.commit()


post = CRUDPost(Post)
