from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy.sql.sqltypes import String, Integer, DateTime, Boolean

from db.database import Base


class DbOutstandingPayment(Base):
    __tablename__ = 'outstanding_payments'
    id_outstanding = Column('id_outstanding', Integer, primary_key=True, index=True)
    id_system = Column('id_system', Integer, ForeignKey("users.id_user"))
    id_market = Column('id_market', String, ForeignKey("markets.id_market"))
    amount = Column('amount', MONEY)
    past_amount = Column('past_amount', MONEY)
    in_process = Column('in_process', Boolean)
    last_cash_closing = Column('last_cash_closing', DateTime(timezone=False))
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)
