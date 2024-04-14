from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base, declared_attr


sa_meta = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)


class BaseMixin(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id: int = Column(Integer, autoincrement=True, primary_key=True)


Base = declarative_base(cls=BaseMixin, metadata=sa_meta)
