from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, Date

from db.database import Base


class DbClient(Base):
    __tablename__ = 'clients'
    id_client = Column('id_client', String, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    id_address = Column('id_address', Integer, ForeignKey("addresses.id_address"))
    last_name = Column('last_name', String)
    birth_date = Column('birth_date', Date)
    phone = Column('phone', String)
    age = Column('age', Integer)

    address = relationship("db.models.addresses_db.DbAddress", back_populates="clients")
    fingerprints = relationship("db.models.fingerprints_db.DbFingerprint", back_populates="client")
