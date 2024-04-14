from datetime import datetime
from typing import List, Optional, Union
import uuid

from pydantic import BaseModel, Field


def gen_post_id() -> str:
    return uuid.uuid4().hex[0:10]


def gen_post_date() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


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
    post_id: str = Field(default_factory=gen_post_id)
    created: str = Field(default_factory=gen_post_date)
    modified: None = None


class UpdatePostInDB(PostToDB):
    modified: str = Field(default_factory=gen_post_date)


# ----> HTTP Responses schemas


class TagsResponse(BaseModel):
    tags: List[str]


class PostResponse(PostFromDB):
    pass

    class Config:
        fields = {
            "writer_id": {"exclude": True},
            "id": {"exclude": True},
        }


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
