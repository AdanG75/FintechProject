from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, BigInteger, String, Float, Boolean, DateTime

from db.database import Base


class DbMovement(Base):
    __tablename__ = 'movements'
    id_movement = Column('id_movement', BigInteger, primary_key=True, index=True)
    id_credit = Column('id_credit', BigInteger, ForeignKey("credits.id_credit"))
    id_performer = Column('id_performer', Integer, ForeignKey("users.id_user"))
    id_requester = Column('id_requester', String, ForeignKey("clients.id_client"))
    type_movement = Column('type_movement', String)
    amount = Column('amount', Float)
    authorized = Column('authorized', Boolean)
    type_user = Column('type_user', String)
    in_process = Column('in_process', Boolean)
    successful = Column('successful', Boolean)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
