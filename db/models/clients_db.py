from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, SmallInteger, String, Date, Boolean

from db.database import Base


class DbClient(Base):
    __tablename__ = 'clients'
    id_client = Column('id_client', String, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    last_name = Column('last_name', String)
    birth_date = Column('birth_date', Date)
    age = Column('age', SmallInteger)
    dropped = Column('dropped', Boolean)

    addresses = relationship(
        "db.models.addresses_db.DbAddress",
        primaryjoin="and_(DbClient.id_client==DbAddress.id_client, "
                    "DbAddress.dropped==False)",
        back_populates="client"
    )
    fingerprints = relationship(
        "db.models.fingerprints_db.DbFingerprint",
        primaryjoin="and_(DbClient.id_client==DbFingerprint.id_client, "
                    "DbFingerprint.dropped==False)",
        back_populates="client"
    )
