from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import SmallInteger, String, Float

from db.database import Base


class DbMinutiae(Base):
    __tablename__ = 'minutiae'
    id_minutia = Column('id_minutia', String, primary_key=True, index=True)
    id_fingerprint = Column('id_fingerprint', String, ForeignKey("fingerprints.id_fingerprint"))
    pos_x = Column('pos_x', SmallInteger)
    pos_y = Column('pos_y', SmallInteger)
    angle = Column('angle', Float)
    type_minutia = Column('type_minutia', String(length=1))
