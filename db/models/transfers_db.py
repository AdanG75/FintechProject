from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, String

from db.database import Base


class DbTransfer(Base):
    __tablename__ = 'transfers'
    id_transfer = Column('id_transfer', String, primary_key=True, index=True)
    id_movement = Column('id_movement', BigInteger, ForeignKey("movements.id_movement"))
    id_destination_credit = Column('id_destination_credit', BigInteger, ForeignKey("credits.id_credit"))
    type_transfer = Column('type_transfer', String)
    paypal_id_order = Column('paypal_id_order', String)
