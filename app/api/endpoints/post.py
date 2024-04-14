import math
from typing import Any, Dict, List, Literal, Optional

from app import crud, schemas
from app.api import deps
from app.core import exceptions
from app.db.session import get_db_session as db_session
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.get("/tags", response_model=schemas.TagsResponse)
async def get_tags(db: AsyncSession = Depends(db_session)) -> Any:
    all_tags = await crud.tag.get_all_tags(db)
    return all_tags


@router.get("/", response_model=schemas.PageResponse)
async def get_pagination(
    db: AsyncSession = Depends(db_session),
    *,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=3, ge=1, le=100),
    sort: Literal["created"] = "created",
    order: Optional[Literal["asc", "desc"]] = None,
    tags: Optional[str] = None,
) -> Any:
    result: Dict = {}

    tags_array: List = []
    if tags:
        tags_array = tags.split(",")

    total_records = await crud.post.count_post_with_filters(db, tags=tags_array)
    if not total_records:
        raise exceptions.NotFound

    total_pages = int(math.ceil(total_records / page_size))
    if page > total_pages:
        raise exceptions.PageBadRequest

    # Calculate offset based on incoming page number.
    offset = (page - 1) * page_size
    all_posts = await crud.post.get_all_posts(
        db,
        offset=offset,
        limit=page_size,
        sort=sort,
        order=order,
        tags=tags_array,
    )

    result = {
        "current_page": page,
        "total_pages": total_pages,
        "page_size": page_size,
        "total_records": total_records,
        "filter_tags": tags_array,
        "data": all_posts,
    }
    return result


@router.get("/{post_id}", response_model=schemas.PostResponse)
async def get_specific_post(
    db: AsyncSession = Depends(db_session),
    *,
    post_id: str,
) -> Any:
    post = await crud.post.get_post_id(db, post_id=post_id)

    if not post:
        raise exceptions.NotFound

    return post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_class=Response,
)
async def delete_post(
    db: AsyncSession = Depends(db_session),
    *,
    post_id: str,
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    await crud.post.delete_by_post_id(db, post_id)


@router.put(
    "/{post_id}",
    response_model=schemas.UpdatePostResponse,
)
async def update_post(
    db: AsyncSession = Depends(db_session),
    *,
    post_id: str,
    body: schemas.UpdatePostRequest,
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(
            isadmin=True,
            isdisabled=True,
        ),
    ),
) -> Any:
    update_post = schemas.UpdatePostInDB.construct(**body.dict())

    result = await crud.post.update_post(
        db,
        post_id=post_id,
        obj_in=update_post,
    )

    if body.tags:
        await crud.tag.add_tags(db, tags=body.tags)

    return {"post_id": result}


@router.post("/", response_model=schemas.CreatePostResponse)
async def create_post(
    db: AsyncSession = Depends(db_session),
    *,
    body: schemas.CreatePostRequest,
    current_user: schemas.UserFromDB = Depends(
        deps.AuthCheck(isadmin=True, isdisabled=True),
    ),
) -> Any:
    new_post = schemas.CreatePostInDB(**body.dict())

    result = await crud.post.create_post(
        db,
        user_id=current_user.id,
        obj_in=new_post,
    )

    if body.tags:
        await crud.tag.add_tags(db, tags=body.tags)

    return {"post_id": result}
