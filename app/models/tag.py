from app.db.meta import Base
from sqlalchemy import Column, Text


class Tag(Base):
    tag: str = Column(Text, nullable=False, unique=True)
