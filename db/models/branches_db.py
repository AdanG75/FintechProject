from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean

from db.database import Base


class DbBranch(Base):
    __tablename__ = 'branches'
    id_branch = Column('id_branch', String, primary_key=True, index=True)
    id_market = Column('id_market', String, ForeignKey("markets.id_market"))
    branch_name = Column('branch_name', String)
    service_hours = Column('service_hours', String)
    phone = Column('phone', String)
    password = Column('password', String)
    created_time = Column('created_time', DateTime(timezone=False))
    updated_time = Column('updated_time', DateTime(timezone=False))
    dropped = Column('dropped', Boolean)

    market = relationship("db.models.markets_db.DbMarket", back_populates="branches")
    address = relationship(
        "db.models.addresses_db.DbAddress",
        primaryjoin="and_(DbBranch.id_branch==DbAddress.id_branch, "
                    "DbAddress.dropped==False)",
        back_populates="branch",
        uselist=False
    )
