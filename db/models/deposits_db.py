from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, String

from db.database import Base


class DbDeposit(Base):
    __tablename__ = 'deposits'
    id_deposit = Column('id_deposit', String, primary_key=True, index=True)
    id_movement = Column('id_movement', BigInteger, ForeignKey("movements.id_movement"))
    id_destination_credit = Column('id_destination_credit', BigInteger, ForeignKey("credits.id_credit"))
    depositor_name = Column('depositor_name', String)
    depositor_email = Column('depositor_email', String)
    type_deposit = Column('type_deposit', String)
    paypal_id_order = Column('paypal_id_order', String)
