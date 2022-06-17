from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String

from db.database import Base


class DbDeposit(Base):
    __tablename__ = 'deposits'
    id_deposit = Column('id_deposit', String, primary_key=True, index=True)
    id_movement = Column('id_movement', Integer)
    id_destination_credit = Column('id_destination_credit', Integer)
    user_name = Column('user_name', String)
