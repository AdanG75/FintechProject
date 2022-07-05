from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, BigInteger, DateTime, Boolean

from db.database import Base


class DbAddress(Base):
    __tablename__ = 'addresses'
    id_address = Column('id_address', BigInteger, primary_key=True, index=True)
    id_branch = Column('id_branch', String, ForeignKey("branches.id_branch"))
    id_client = Column('id_client', String, ForeignKey("clients.id_client"))
    type_owner = Column('type_owner', String)
    is_main = Column('is_main', Boolean)
    zip_code = Column('zip_code', Integer)
    state = Column('state', String)
    city = Column('city', String)
    neighborhood = Column('neighborhood', String)
    street = Column('street', String)
    ext_number = Column('ext_number', String)
    inner_number = Column('inner_number', String)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    client = relationship("db.models.clients_db.DbClient", back_populates="address")
    branch = relationship("db.models.branches_db.DbBranch", back_populates="address")
