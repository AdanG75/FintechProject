from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String, Float, Boolean, DateTime

from db.database import Base


class DbFingerprint(Base):
    __tablename__ = 'fingerprints'
    id_fingerprint = Column('id_fingerprint', String, primary_key=True, index=True)
    id_client = Column('id_client', String, ForeignKey("clients.id_client"))
    alias_fingerprint = Column('alias_fingerprint', String)
    url_fingerprint = Column('url_fingerprint', String)
    fingerprint_type = Column('fingerprint_type', String)
    quality = Column('quality', String)
    spectral_index = Column('spectral_index', Float)
    spatial_index = Column('spatial_index', Float)
    main_fingerprint = Column('main_fingerprint', Boolean)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    client = relationship("db.models.clients_db.DbClient", back_populates="fingerprints")
