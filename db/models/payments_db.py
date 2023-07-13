from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import String, BigInteger

from db.database import Base


class DbPayment(Base):
    __tablename__ = 'payments'
    id_payment = Column('id_payment', String, primary_key=True, index=True)
    id_movement = Column('id_movement', BigInteger, ForeignKey("movements.id_movement"))
    id_market = Column('id_market', String, ForeignKey("markets.id_market"))
    type_payment = Column('type_payment', String)
    paypal_id_order = Column('paypal_id_order', String)
