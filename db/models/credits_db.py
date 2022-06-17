from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String, Float, DateTime, Boolean

from db.database import Base


class DbCredit(Base):
    __tablename__ = 'credits'
    id_credit = Column('id_credit', Integer, primary_key=True, index=True)
    id_client = Column('id_client', String)
    id_market = Column('id_market', String)
    id_account = Column('id_account', Integer)
    money = Column('money', Float)
    type_credit = Column('type_credit', String)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)
