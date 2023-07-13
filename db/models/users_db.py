from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, Text, DateTime, Boolean

from db.database import Base


class DbUser(Base):
    __tablename__ = 'users'
    id_user = Column('id_user', Integer, primary_key=True, index=True)
    email = Column('email', String)
    name = Column('name', String)
    phone = Column('phone', String)
    password = Column('password', String)
    type_user = Column('type_user', String)
    public_key = Column('public_key', Text)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    accounts = relationship(
        "db.models.accounts_db.DbAccount",
        primaryjoin="and_(DbUser.id_user==DbAccount.id_user, "
                    "DbAccount.dropped==False)",
        back_populates="user"
    )
