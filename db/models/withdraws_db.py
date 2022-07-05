from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import String, BigInteger

from db.database import Base


class DbWithdraw(Base):
    __tablename__ = 'withdraws'
    id_withdraw = Column('id_withdraw', String, primary_key=True, index=True)
    id_movement = Column('id_movement', BigInteger, ForeignKey("movements.id_movement"))
    type_withdraw = Column('type_withdraw', String)
