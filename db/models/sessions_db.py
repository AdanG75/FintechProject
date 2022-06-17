from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String, DateTime

from db.database import Base


class DbSession(Base):
    __tablename__ = 'sessions'
    id_session = Column('id_session', String, primary_key=True, index=True)
    id_user = Column('id_user', Integer)
    session_start = Column('session_start', DateTime)
    session_finish = Column('session_finish', DateTime)
