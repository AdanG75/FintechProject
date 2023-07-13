from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean

from db.database import Base


class DbAccount(Base):
    __tablename__ = 'accounts'
    id_account = Column('id_account', Integer, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    alias_account = Column('alias_account', String)
    paypal_email = Column('paypal_email', String)
    paypal_id_client = Column('paypal_id_client', String)
    paypal_secret = Column('paypal_secret', String)
    type_owner = Column('type_owner', String)
    main_account = Column('main_account', Boolean)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    user = relationship(
        "db.models.users_db.DbUser",
        primaryjoin="and_(DbAccount.id_user==DbUser.id_user, "
                    "DbUser.dropped==False)",
        back_populates="accounts"
    )
