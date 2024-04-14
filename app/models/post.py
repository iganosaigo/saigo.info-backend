from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from app.db.meta import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .user import Account


class Post(Base):
    account_id = Column(
        Integer,
        ForeignKey("account.id"),
        nullable=False,
        default=False,
        index=True,
    )
    post_id: str = Column(String(10), nullable=False, default=False, unique=True)
    post_json: Dict = Column(JSONB(astext_type=Text()))
    account: Account = relationship("Account", back_populates="post")

    # DATE YYYY-MM-DD HH24:MI

    # TODO: Do i need mutable changes in ORM session?
    # https://amercader.net/blog/beware-of-json-fields-in-sqlalchemy/
    # https://docs.sqlalchemy.org/en/14/orm/extensions/mutable.html#sqlalchemy.ext.mutable.MutableDict
    # post_json = Column(MutableDict.as_mutable(JSONB)) # noqa
