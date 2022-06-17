from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, Text, DateTime, Boolean

from db.database import Base


class DbAddress(Base):
    __tablename__ = 'addresses'
    id_address = Column('id_address', Integer, primary_key=True, index=True)
    zip_code = Column('zip_code', Integer)
    state = Column('state', String)
    city = Column('city', String)
    street = Column('street', String)
    ext_number = Column('ext_number', String)
    inner_number = Column('inner_number', String)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    clients = relationship("db.models.clients_db.DbClient", back_populates="address")
    branches = relationship("db.models.branches_db.DbBranch", back_populates="address")

