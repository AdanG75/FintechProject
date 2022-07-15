from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, DateTime

from db.database import Base


class DbSession(Base):
    __tablename__ = 'sessions'
    id_session = Column('id_session', Integer, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    session_start = Column('session_start', DateTime(timezone=False))
    session_finish = Column('session_finish', DateTime(timezone=False))
