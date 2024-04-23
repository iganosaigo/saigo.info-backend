from pydantic import EmailStr
from typing_extensions import TypedDict


class TUserGetOpts(TypedDict, total=False):
    id: int
    email: EmailStr
