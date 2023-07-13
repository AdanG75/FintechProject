from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer, DateTime, SmallInteger

from db.database import Base


class DbLoginAttempt(Base):
    __tablename__ = 'login_attempts'
    id_attempt = Column('id_attempt', Integer, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    email = Column('email', String)
    attempts = Column('attempts', SmallInteger)
    next_attempt_time = Column('next_attempt_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
