from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String

from db.database import Base


class DbTransfer(Base):
    __tablename__ = 'transfers'
    id_transfer = Column('id_transfer', String, primary_key=True, index=True)
    id_movement = Column('id_movement', Integer)
    id_destination_credit = Column('id_destination_credit', Integer)
