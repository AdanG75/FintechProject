from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, BigInteger, String, Float, DateTime, Boolean

from db.database import Base


class DbCredit(Base):
    __tablename__ = 'credits'
    id_credit = Column('id_credit', BigInteger, primary_key=True, index=True)
    id_client = Column('id_client', String, ForeignKey("clients.id_client"))
    id_market = Column('id_market', String, ForeignKey("markets.id_market"))
    id_account = Column('id_account', Integer, ForeignKey("accounts.id_account"))
    alias_credit = Column('alias_credit', String)
    type_credit = Column('type_credit', String)
    amount = Column('amount', Float)
    past_amount = Column('past_amount', Float)
    is_approved = Column('is_approved', Boolean)
    in_process = Column('in_process', Boolean)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)
