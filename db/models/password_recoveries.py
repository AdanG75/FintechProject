from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, Boolean, DateTime, SmallInteger

from db.database import Base


class DbPasswordRecovery(Base):
    __tablename__ = 'password_recoveries'
    id_recover = Column('id_recover', Integer, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    code = Column('code', Integer)
    expiration_time = Column('expiration_time', DateTime(timezone=False))
    attempts = Column('attempts', SmallInteger)
    is_valid = Column('is_valid', Boolean)
    updated_time = Column('updated_time', DateTime(timezone=False))

