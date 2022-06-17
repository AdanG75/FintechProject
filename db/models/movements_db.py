from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String, Float, Boolean, DateTime

from db.database import Base


class DbMovement(Base):
    __tablename__ = 'movements'
    id_movement = Column('id_movement', Integer, primary_key=True, index=True)
    id_credit = Column('id_credit', Integer)
    id_user = Column('id_user', Integer)
    type_movement = Column('type_movement', String)
    amount = Column('amount', Float)
    type_user = Column('type_user', String)
    created_time = Column('created_time', DateTime(timezone=False))
    successful = Column('succesful', Boolean)
