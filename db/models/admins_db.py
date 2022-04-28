from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String

from db.database import Base


class DbAdmin(Base):
    __tablename__ = 'admins'
    id = Column('id_admin', Integer, primary_key=True, index=True)
    username = Column('username', String)
    email = Column('email', String)
    password = Column('password', String)
