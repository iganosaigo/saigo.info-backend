from __future__ import annotations

from typing import TYPE_CHECKING

from app.db.meta import Base
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .post import Post


class Role(Base):
    id = Column(SmallInteger, autoincrement=False, primary_key=True)
    name = Column(String(30), nullable=False, unique=True)
    account: Account = relationship("Account", back_populates="role")


class Account(Base):
    fullname = Column(String(30), nullable=False)
    email: str = Column(Text, nullable=False, unique=True)
    hashed_password: str = Column(Text, nullable=False)
    disabled: bool = Column(Boolean(), default=False, nullable=False)
    role_id = Column(
        Integer,
        ForeignKey("role.id"),
        nullable=False,
        server_default="1",
    )
    role: Role = relationship(Role, back_populates="account")
    post: Post = relationship("Post", back_populates="account")
