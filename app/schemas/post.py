from datetime import datetime, timezone
from typing import List, Optional, Union
import uuid

from pydantic import BaseModel, Field, ValidationInfo, field_validator


def gen_post_id(title: str) -> str:
    return uuid.uuid3(uuid.NAMESPACE_URL, title).hex[0:10]


def gen_post_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ----> DB's schemas


class PostFromDB(BaseModel):
    id: int
    post_id: str
    writer: str
    writer_id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    tags: List[Optional[str]]
    created: datetime
    modified: Union[None, datetime]
    estimated: int


class PostToDB(BaseModel):
    title: str
    description: str
    content: str
    tags: List[Optional[str]]
    estimated: int


class CreatePostInDB(PostToDB):
    post_id: str | None = Field(default=None, validate_default=True)
    created: str = Field(default_factory=gen_post_date)
    modified: None = None

    @field_validator("post_id", mode="after")
    @classmethod
    def make_post_id(cls, v: str | None, info: ValidationInfo) -> str:
        if v:
            return v
        title = info.data["title"]
        return gen_post_id(title)


class UpdatePostInDB(PostToDB):
    modified: str = Field(default_factory=gen_post_date)


# ----> HTTP Responses schemas


class TagsResponse(BaseModel):
    tags: List[str]


class PostResponse(PostFromDB):
    writer_id: int = Field(exclude=True)
    id: int = Field(exclude=True)


class PageResponse(BaseModel):
    current_page: int
    total_pages: int
    page_size: int
    total_records: int
    filter_tags: List[str]
    data: List[PostResponse]


class CreatePostResponse(BaseModel):
    post_id: str


class UpdatePostResponse(CreatePostResponse):
    pass


# ----> HTTP Requests schemas


class CreatePostRequest(BaseModel):
    title: str
    description: str
    content: str
    tags: Optional[List[str]] = []
    estimated: int


class UpdatePostRequest(CreatePostRequest):
    pass
