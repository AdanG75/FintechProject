from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import SmallInteger, String, Float

from db.database import Base


class DbCores(Base):
    __tablename__ = 'cores'
    id_core = Column('id_core', String, primary_key=True, index=True)
    id_fingerprint = Column('id_fingerprint', String, ForeignKey("fingerprints.id_fingerprint"))
    pos_x = Column('pos_x', SmallInteger)
    pos_y = Column('pos_y', SmallInteger)
    angle = Column('angle', Float)
    type_core = Column('type_core', String(length=1))
