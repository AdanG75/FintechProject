from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String

from db.database import Base


class DbPayment(Base):
    __tablename__ = 'payments'
    id_payment = Column('id_payment', String, primary_key=True, index=True)
    id_movement = Column('id_movement', Integer)
    id_market = Column('id_market', String)
