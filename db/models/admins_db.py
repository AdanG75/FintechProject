from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, Boolean

from db.database import Base


class DbAdmin(Base):
    __tablename__ = 'admins'
    id_admin = Column('id_admin', String, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    full_name = Column('full_name', String)
    dropped = Column('dropped', Boolean)
