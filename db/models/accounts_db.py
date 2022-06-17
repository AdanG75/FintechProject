from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean

from db.database import Base


class DbAccount(Base):
    __tablename__ = 'accounts'
    id_account = Column('id_account', Integer, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    paypal_email = Column('paypal_email', String)
    type_owner = Column('type_owner', String)
    main_account = Column('main_account', Boolean)
    system_account = Column('system_account', Boolean)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    user = relationship("db.models.users_db.DbUser", back_populates="accounts")


