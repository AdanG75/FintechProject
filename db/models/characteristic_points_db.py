from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, Float

from db.database import Base


class DbCharacteristicPoint(Base):
    __tablename__ = 'characteristic_points'
    id_characteristic = Column('id_characteristic', String, primary_key=True, index=True)
    id_fingerprint = Column('id_fingerprint', String, ForeignKey("fingerprints.id_fingerprint"))
    pos_x = Column('pos_x', Integer)
    pos_y = Column('pos_y', Integer)
    angle = Column('angle', Float)
    type = Column('type', String(length=1))
