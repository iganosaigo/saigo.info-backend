from sqlalchemy import Column, Text

from app.db.meta import Base


class Tag(Base):
    tag: str = Column(Text, nullable=False, unique=True)
