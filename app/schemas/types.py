from datetime import datetime
from typing import List, Optional, Union

from pydantic import EmailStr
from typing_extensions import TypedDict


# class TPostData(TypedDict):
#     title: str
#     content: str
#     tags: List[Optional[str]]
#     created: datetime
#     modified: Union[None, datetime]
#     estimated: int


class TUserGetOpts(TypedDict, total=False):
    id: int
    email: EmailStr
